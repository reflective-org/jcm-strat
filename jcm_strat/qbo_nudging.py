"""QBO nudging: relax the tropical stratospheric zonal-mean zonal wind towards ERA5 (issue #6).

The stripped model has no QBO (Phase 6 record: steady equatorial easterlies of 12-14 m/s, a
deseasonalised variability of 4 m/s where ERA5 has 17). It cannot grow one: the QBO is driven by
tropical waves launched by convection, which the dry model does not have, and by gravity-wave drag
that is off, and it needs ~500-700 m vertical spacing in the tropical lower stratosphere. The
standard remedy in specified-dynamics and SAI studies (e.g. WACCM's QBO nudging) is to relax the
zonal-mean tropical wind towards the observed one. That is what this term does.

What is nudged, towards what:

* Target: ERA5 monthly-mean zonal-mean zonal wind from the Copernicus Climate Data Store
  (``cache/era5_ref/era5_zm_monthly_<year>.nc``, 25 pressure levels 1-1000 hPa, 0.25 deg latitude,
  2005-2009), interpolated to the model's latitudes and to its reference pressures in ln p, and
  linearly in time between month centres. ERA5 is the reanalysis the troposphere is already nudged
  to, and its QBO is observed, not modelled. Monthly means suffice because the QBO evolves over
  months (it descends ~1 km per month).
* What: only the ZONAL MEAN of the model's zonal wind is relaxed. The tendency at every longitude
  of a latitude row is the same, ``-(ubar_model - ubar_ERA5)/tau``, so eddies (the waves that do
  the transport) are left alone; only the mean flow they propagate through is corrected.
* Where: a tropical window, weight 1 for |lat| <= 15 deg falling smoothly (cos^2) to 0 at 25 deg,
  and a pressure window with full weight between ~2.2 and ~40 hPa falling to 0 at 1 and 90 hPa
  (linear in log p). It stays clear of the 150 hPa tropospheric nudging cutoff below; the top is
  the top of the ERA5 target. The first Phase 8 runs stopped at 4 hPa (full weight to ~9 hPa), the
  QBO's own domain: that left the 1-4 hPa layer 10-15 m/s too easterly, because momentum carried
  up out of the nudged layer met nothing there (no SAO forcing). Raising the top to 1 hPa removed
  that bias and nudged in ERA5's semiannual oscillation at 2-3 hPa; inside the QBO layer nothing
  changed (docs/outputs/08_qbo, 1hpa_top/).
* How fast: tau = 1 day. The first Phase 8 runs used WACCM's 10 days and reached 80 percent of
  ERA5's QBO amplitude; a sweep over 2005-2009 (10 / 5 / 2 / 1 d -> 80 / 86 / 90 / 92 percent,
  nothing else in the model moving) showed the deficit is this relaxation working against the
  model's own easterly tendency (a restoring time of ~40 d), not the window. At 1 day the gain per
  halving had flattened to ~2 percent, so the rest is the target's shape (below). KEY_DECISIONS #27.
* Target shape: ``mean_preserving=True`` adjusts the month-centre values so that the piecewise-
  linear interpolation reproduces ERA5's monthly means exactly (the AMIP mid-month "bcs" method,
  Taylor et al. 2000): with equal months the mean over month k of the interpolant is
  (v[k-1] + 6 v[k] + v[k+1]) / 8, so the node values v solve that tridiagonal system with the
  monthly means m on the right-hand side (ends clamped: v[-1] = v[0]). Plain linear interpolation
  through the means cuts every peak: for a sinusoid of period P months the interpolant's monthly means
  are (6 + 2 cos(2 pi/P))/8 of the nodes, so the means understate the nodes by 0.6 percent for the
  QBO (P ~ 28) and 12.5 percent for the SAO (P = 6); the correction is the inverse.

The term runs on the column-vectorized physics path like the other jcm_strat terms. The zonal mean
is a segment-sum over the columns of each latitude row; the term reads the fraction of year from
``forcing.solar.tyear`` (as PolvaniKushnerColumns does) and the calendar year from its ``year``
argument, which the segment chain passes per year (``EXTRA_PER_YEAR``). Per-second rates are
converted to the dycore's nondimensional time exactly as in ``tracers.py`` and ``HeldSuarez``.
"""
from __future__ import annotations

import glob
import logging
from typing import ClassVar

import jax
import jax.numpy as jnp
import numpy as np
import xarray as xr
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics.coords_util import column_lat_lon
from jcm.physics.physics_term import PhysicsTerm
from jcm.physics_interface import PhysicsState, PhysicsTendency

from jcm_strat.polvani_kushner import PolvaniKushnerColumns

P0_PA = 101325.0
DAY = 86400.0


def mean_preserving_nodes(monthly_means: np.ndarray) -> np.ndarray:
    """Month-centre node values whose piecewise-linear interpolant has the given monthly means.

    ``monthly_means`` has time first, (nmonths, ...). With equal-length months (the term's time
    coordinate is a uniform 1/12 year per month) the mean of the interpolant over month k is
    (v[k-1] + 6 v[k] + v[k+1]) / 8; the ends are clamped (v[-1] = v[0], v[n] = v[n-1]), matching
    the clamping of the interpolation itself. Solves the tridiagonal system exactly.
    """
    m = np.asarray(monthly_means, dtype=np.float64)
    n = m.shape[0]
    if n < 2:
        return m.copy()
    A = np.zeros((n, n))
    idx = np.arange(n)
    A[idx, idx] = 6.0
    A[idx[1:], idx[1:] - 1] = 1.0
    A[idx[:-1], idx[:-1] + 1] = 1.0
    A[0, 0] += 1.0; A[-1, -1] += 1.0                       # clamped ends
    A /= 8.0
    v = np.linalg.solve(A, m.reshape(n, -1))
    return v.reshape(m.shape)


class QboNudging(PhysicsTerm):
    name: ClassVar[str] = "qbo_nudging"
    category: ClassVar[str] = "nudging_qbo"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        era5_glob: str = "cache/era5_ref/era5_zm_monthly_*.nc",
        year: int = 2005,
        tau_days: float = 1.0,
        lat_full_deg: float = 15.0,
        lat_zero_deg: float = 25.0,
        p_bot_hpa: float = 90.0,
        p_top_hpa: float = 1.0,
        taper_decades: float = 0.35,
        use_calendar: bool = True,
        mean_preserving: bool = True,
    ) -> None:
        self.use_calendar = bool(use_calendar)   # False: fixed target (first month); only for tests
        self.mean_preserving = bool(mean_preserving)
        files = sorted(glob.glob(era5_glob), key=lambda f: int(xr.open_dataset(f, decode_times=False).attrs.get("year", 0)))
        if not files:
            raise FileNotFoundError(f"QboNudging: no ERA5 zonal-mean files match {era5_glob}")
        dss = [xr.open_dataset(f, decode_times=False) for f in files]
        years = [int(d.attrs["year"]) for d in dss]
        self.year = int(year)
        # _target_now indexes the concatenated record by (year - year0) * 12, so the record must be
        # contiguous from its first year to the one in use: keep the contiguous block of files that
        # contains `year` (files being downloaded for other years may leave gaps elsewhere), and refuse
        # a missing year instead of silently clamping onto a frozen month (Phase 10).
        anchor = self.year if self.use_calendar else years[0]
        if anchor not in years:
            raise FileNotFoundError(f"QboNudging: no ERA5 zonal-mean file for {anchor} in {era5_glob} "
                                    f"(have {years}; scripts/fetch_era5_strat_ref.py)")
        i = years.index(anchor); lo = hi = i
        while lo > 0 and years[lo - 1] == years[lo] - 1: lo -= 1
        while hi < len(years) - 1 and years[hi + 1] == years[hi] + 1: hi += 1
        dss = dss[lo:hi + 1]; self.years = years[lo:hi + 1]
        if self.use_calendar and self.year + 1 not in self.years:
            logging.getLogger("jcm_strat").warning("QboNudging: no ERA5 file for %d; the second half of December %d "
                                                   "holds the December mean instead of interpolating", self.year + 1, self.year)
        self._u_raw = np.concatenate([d.uzm.values for d in dss], axis=0).astype(np.float64)   # (nmonths, 25, 721)
        self._p_raw = dss[0].level.values.astype(np.float64)                                     # hPa, ascending
        self._lat_raw = dss[0].lat.values.astype(np.float64)                                     # deg, ascending
        self.year0 = self.years[0]; self.nmonths = self._u_raw.shape[0]
        self.tau_days = float(tau_days)
        self.lat_full = float(lat_full_deg); self.lat_zero = float(lat_zero_deg)
        self.p_bot = float(p_bot_hpa); self.p_top = float(p_top_hpa); self.taper = float(taper_decades)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        per_s = float(specs.nondimensionalize(1.0 / units.second))
        self.k = per_s / (self.tau_days * DAY)                      # relaxation rate in nondimensional time
        self._coords_cached = False

    # ------------------------------------------------------------------ setup
    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(P0_PA)
        p_ref = np.asarray(sigma, dtype=np.float64) * P0_PA / 100.0                             # hPa, (nlev,)
        lat_cols, _ = column_lat_lon(coords.horizontal)
        lat_cols = np.asarray(lat_cols, dtype=np.float64)                                        # radians, (ncols,)
        lats, lat_idx, counts = np.unique(np.round(lat_cols, 10), return_inverse=True, return_counts=True)
        lat_deg = np.rad2deg(lats)
        # ERA5 target on (nmonths, nlev, nlat): latitude first, then ln p
        tgt = np.empty((self.nmonths, p_ref.size, lats.size))
        lp_raw = np.log(self._p_raw); lp_ref = np.log(p_ref)
        for m in range(self.nmonths):
            on_lat = np.stack([np.interp(lat_deg, self._lat_raw, self._u_raw[m, k]) for k in range(self._p_raw.size)])   # (25, nlat)
            for j in range(lats.size):
                tgt[m, :, j] = np.interp(lp_ref, lp_raw, on_lat[:, j])
        # weights: latitude window x pressure window
        a = np.abs(lat_deg)
        w_lat = np.where(a <= self.lat_full, 1.0, np.where(a >= self.lat_zero, 0.0,
                         np.cos(0.5 * np.pi * (a - self.lat_full) / (self.lat_zero - self.lat_full)) ** 2))
        l10 = np.log10(p_ref); lo, hi = np.log10(self.p_top), np.log10(self.p_bot)
        w_p = np.clip(np.minimum((l10 - lo) / self.taper, (hi - l10) / self.taper), 0.0, 1.0)
        w_p = np.where((p_ref < self.p_top) | (p_ref > self.p_bot), 0.0, w_p)
        self._w = nnx.Variable(jnp.asarray(w_p[:, None] * w_lat[None, :], jnp.float32))         # (nlev, nlat)
        self._target = nnx.Variable(jnp.asarray(tgt, jnp.float32))                              # (nmonths, nlev, nlat)
        self._lat_idx = nnx.Variable(jnp.asarray(lat_idx, jnp.int32))                            # (ncols,)
        self._counts = nnx.Variable(jnp.asarray(counts, jnp.float32))                            # (nlat,)
        self.nlat = int(lats.size)
        self._coords_cached = True

    # ------------------------------------------------------------------ step
    def _target_now(self, tyear):
        """Linear interpolation between month centres; clamped at the record's ends."""
        t = (self.year - self.year0) * 12.0 + tyear * 12.0 - 0.5
        t = jnp.clip(t, 0.0, self.nmonths - 1.0)
        i0 = jnp.clip(jnp.floor(t).astype(jnp.int32), 0, self.nmonths - 2); f = t - i0
        tg = self._target.get_value()
        return (1.0 - f) * tg[i0] + f * tg[i0 + 1]                                              # (nlev, nlat)

    def zonal_mean(self, field):
        """(nlev, ncols) -> (nlev, nlat) mean over the columns of each latitude row."""
        idx = self._lat_idx.get_value()
        s = jax.ops.segment_sum(field.T, idx, num_segments=self.nlat)                            # (nlat, nlev)
        return (s / self._counts.get_value()[:, None]).T

    def tendency(self, u_cols, tyear):
        """QBO-nudging tendency of u (nondimensional rate x m/s) for column-vectorized u (nlev, ncols)."""
        ubar = self.zonal_mean(u_cols)                                                           # (nlev, nlat), m/s
        tend_lat = -self.k * self._w.get_value() * (ubar - self._target_now(tyear))             # (nlev, nlat)
        return tend_lat[:, self._lat_idx.get_value()]                                            # (nlev, ncols)

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        solar = getattr(forcing, "solar", None) if self.use_calendar else None
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        tend = self.tendency(state.u_wind, tyear)
        zeros = jnp.zeros_like(state.temperature)
        return PhysicsTendency(u_wind=tend, v_wind=zeros, temperature=zeros, specific_humidity=zeros), diagnostics


class PolvaniKushnerQbo(PolvaniKushnerColumns):
    """Polvani-Kushner relaxation plus QBO nudging in ONE term.

    Functionally identical to running ``PolvaniKushnerColumns`` and ``QboNudging`` as two terms
    (a unit test asserts it). It was written while chasing a GPU out-of-memory in the first
    Phase 8 runs; the actual cause turned out to be JAX's default 75 percent preallocation
    (60 of 80 GB) with two copies of the 29 GB one-year nudging target in flight inside the
    compiled step - the Phase 6 configuration sat just below that ceiling and any extra term
    pushed it over. The fix is ``XLA_PYTHON_CLIENT_MEM_FRACTION=0.92`` in ``scripts/env.sh``. The
    one-term form is kept because it is marginally cheaper and reads the fraction of year once.
    Configure the QBO part through the ``qbo`` mapping (QboNudging's arguments).
    """

    def __init__(self, qbo: dict | None = None, **pk_kwargs) -> None:
        super().__init__(**pk_kwargs)
        self.qbo = QboNudging(**dict(qbo or {}))

    def cache_coords(self, coords) -> None:
        super().cache_coords(coords)
        self.qbo.cache_coords(coords)

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        tend, diagnostics = super().__call__(state, diagnostics, forcing, terrain)
        solar = getattr(forcing, "solar", None) if self.qbo.use_calendar else None
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        du = self.qbo.tendency(state.u_wind, tyear)
        return PhysicsTendency(u_wind=tend.u_wind + du, v_wind=tend.v_wind, temperature=tend.temperature,
                               specific_humidity=tend.specific_humidity), diagnostics
