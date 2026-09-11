"""Production tracer set for the long runs (Phase 10): transport-learning tracers plus the clocks.

One PhysicsTerm that replaces ``PassiveTracers`` in the production physics. Transport is the
dycore's job (semi-Lagrangian, nodal tracers, global mass fixer); this term only adds the local
tendencies, on jcm's column-vectorized path (``vectorize_columns: true``, fields ``(nlev, ncols)``).
Units and the per-second -> nondimensional conversion (``_per_s``) are exactly as in ``tracers.py``.

Tracers (all ``nondimensionalize=False``, so state, dycore and netCDF carry the same numbers):

``aoa``       age of air in days, reset to zero on one step wherever p > 700 hPa (as in Phases 3-9).
``aoa150``    the same clock reset wherever p > 150 hPa: "entry age" into the stratosphere
              (KEY_DECISIONS #22).
``aoa_sfc``   the same clock reset only in the lowest ``sfc_layers`` model layers: the CLaMS/WACCM
              surface boundary condition.
``sai``       continuous source of 1e-6 per second in the box 15S-15N, 25-55 hPa, no sink (as before).
``pulse_<i>`` single injections: on the first step of the run (``injection: once``, the production
              setting; ``first_segment=true`` marks that segment) the field is SET to a Gaussian blob
              G_i(lat, lon, p) of amplitude A_i centred at (lat_i, lon_i, p_i) with widths
              ``pulse_sigma_deg`` (great-circle) and ``pulse_sigma_decades`` (log10 p), and never
              again. Afterwards the only process besides transport is absorption in the lowest
              ``absorb_layers`` layers (relaxed to zero on one step): the field is pure advection of a
              known initial shape until it has mixed out and drained through the surface. With
              ``injection: quarterly`` (the 2005-2009 review run) the blob is re-set on 1 January and
              every 365/``n_pulses_per_year`` days of each year.
``src_<i>``   continuous sources: every step adds A_i G_i / ``source_timescale_days`` (the blob alone
              would reach A_i in that time) at a fourth set of sites; the same surface absorption is
              the only sink. Source and sink balance after a few years, leaving steady plumes with
              permanent 3-D gradients that breathe with the seasons and the QBO.
``n2o``,      steady tracers with a tropospheric source and a stratospheric photochemical sink:
``cfc11``     held at 1 wherever p > ``n2o_source_pressure_hpa``, loss  -k(lat, p) q  elsewhere with
              WACCM's zonal-mean loss-frequency climatology, and initialised (first step of the
              first segment, ``first_segment=true``) from WACCM's zonal-mean January distribution
              normalised to 1 at the surface. Both come from ``jcm_strat/data/waccm_tracer_ref.nc``
              (scripts/make_waccm_tracer_ref.py). Their steady state is set by the model's own
              transport against a realistic sink, so they carry permanent, latitude- and
              height-dependent gradients spanning 1 to ~1e-2 (N2O) and 1 to ~1e-4 (CFC-11).

Time. A term sees no clock; like ``QboNudging`` this one reads the fraction of year from
``forcing.solar.tyear``, which is exactly 0 at 00:00 on 1 January of every chained segment under
``calendar: gregorian`` (jcm_strat/main.py). The injection fires on the step whose interval contains
an injection date; with a 12-min step that is one step, at most two in a leap year.

Mass fixer. The dycore applies the fixer after the physics, with the post-physics mass as the target,
so neither the injections nor the surface absorption are fought by it; the pulses and the steady
tracers stay under the fixer. The three clocks are not conserved quantities and must be listed in
``sl_mass_fixer_exclude`` (KEY_DECISIONS #19).
"""
from __future__ import annotations

import os
from typing import ClassVar, Sequence

import jax.numpy as jnp
import numpy as np
import xarray as xr
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics.coords_util import column_lat_lon
from jcm.physics.physics_term import PhysicsTerm, TracerSpec
from jcm.physics_interface import PhysicsState, PhysicsTendency

P0_PA = 101325.0
DAY = 86400.0
DEFAULT_REF = os.path.join(os.path.dirname(__file__), "data", "waccm_tracer_ref.nc")

# (lat deg, lon deg E, p hPa, amplitude): different heights, hemispheres, longitudes and concentrations
DEFAULT_PULSES = (
    (0.0, 0.0, 30.0, 1.0),        # tropical middle stratosphere
    (45.0, 120.0, 70.0, 0.5),     # NH lower stratosphere
    (-60.0, 240.0, 10.0, 0.2),    # SH polar middle stratosphere
    (30.0, 300.0, 3.0, 0.1),      # upper stratosphere
    (-15.0, 60.0, 300.0, 0.05),   # tropical upper troposphere, crosses the tropopause
)
# continuous sources (lat deg, lon deg E, p hPa, amplitude): sites distinct from the pulses
DEFAULT_SOURCES = (
    (0.0, 180.0, 20.0, 1.0),      # tropical middle stratosphere
    (30.0, 60.0, 100.0, 0.5),     # NH subtropical lowermost stratosphere
    (-60.0, 300.0, 5.0, 0.2),     # SH polar upper stratosphere
    (-30.0, 240.0, 55.0, 0.3),    # SH subtropical lower stratosphere (Susanne, 2026-09-11)
)
STEADY = ("n2o", "cfc11")


class ProductionTracers(PhysicsTerm):
    name: ClassVar[str] = "production_tracers"
    category: ClassVar[str] = "tracers"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()
    output_attrs: ClassVar = {
        "aoa": {"units": "day", "long_name": "age of air (clock tracer, reset below 700 hPa)"},
        "aoa150": {"units": "day", "long_name": "age of air, clock reset below 150 hPa (stratospheric entry age)"},
        "aoa_sfc": {"units": "day", "long_name": "age of air, clock reset in the lowest two model layers (surface boundary condition)"},
        "sai": {"units": "1", "long_name": "idealised stratospheric injection tracer (source 15S-15N, 25-55 hPa)"},
        "n2o": {"units": "1", "long_name": "N2O-like tracer: 1 below 700 hPa, WACCM loss frequency above, WACCM zonal-mean initial state"},
        "cfc11": {"units": "1", "long_name": "CFC-11-like tracer: 1 below 700 hPa, WACCM loss frequency above, WACCM zonal-mean initial state"},
    }
    _pulse_names: tuple[str, ...] = tuple(f"pulse_{i + 1}" for i in range(len(DEFAULT_PULSES)))
    _source_names: tuple[str, ...] = tuple(f"src_{i + 1}" for i in range(len(DEFAULT_SOURCES)))

    def __init__(
        self,
        pulses: Sequence[Sequence[float]] = DEFAULT_PULSES,
        injection: str = "once",
        n_pulses_per_year: int = 4,
        sources: Sequence[Sequence[float]] = DEFAULT_SOURCES,
        source_timescale_days: float = 90.0,
        pulse_sigma_deg: float = 12.0,
        pulse_sigma_decades: float = 0.25,
        absorb_layers: int = 2,
        sfc_layers: int = 2,
        aoa_reset_pressure_hpa: float = 700.0,
        aoa150_reset_pressure_hpa: float = 150.0,
        sai_source_per_s: float = 1e-6,
        sai_lat_deg: float = 15.0,
        sai_p_top_hpa: float = 25.0,
        sai_p_bot_hpa: float = 55.0,
        ref_file: str = DEFAULT_REF,
        n2o_source_pressure_hpa: float = 700.0,
        first_segment: bool = False,
    ) -> None:
        self.pulses = tuple(tuple(float(v) for v in p) for p in pulses)
        if len(self.pulses) != len(DEFAULT_PULSES):
            raise ValueError(f"ProductionTracers declares {len(DEFAULT_PULSES)} pulse tracers; got {len(self.pulses)} centres")
        if injection not in ("once", "quarterly"):
            raise ValueError(f"injection={injection!r}; expected 'once' or 'quarterly'")
        self.injection = injection
        self.n_pulses = int(n_pulses_per_year)
        self.sources = tuple(tuple(float(v) for v in p) for p in sources)
        if len(self.sources) != len(DEFAULT_SOURCES):
            raise ValueError(f"ProductionTracers declares {len(DEFAULT_SOURCES)} source tracers; got {len(self.sources)} sites")
        self.source_rate = 1.0 / (float(source_timescale_days) * DAY)      # per second, times A_i G_i
        self.sigma_h = float(np.deg2rad(pulse_sigma_deg))
        self.sigma_z = float(pulse_sigma_decades)
        self.absorb_layers = int(absorb_layers)
        self.sfc_layers = int(sfc_layers)
        self.aoa_reset_pa = float(aoa_reset_pressure_hpa) * 100.0
        self.aoa150_reset_pa = float(aoa150_reset_pressure_hpa) * 100.0
        self.sai_source_per_s = float(sai_source_per_s)
        self.sai_lat = float(np.deg2rad(sai_lat_deg))
        self.sai_p_top_pa = float(sai_p_top_hpa) * 100.0
        self.sai_p_bot_pa = float(sai_p_bot_hpa) * 100.0
        self.ref_file = str(ref_file)
        self.steady_source_pa = float(n2o_source_pressure_hpa) * 100.0
        self.first_segment = bool(first_segment)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._per_s = float(specs.nondimensionalize(1.0 / units.second))
        self._coords_cached = False

    @classmethod
    def required_tracers(cls) -> tuple[TracerSpec, ...]:
        clocks = tuple(TracerSpec(n, units="day", initial_value=0.0, nondimensionalize=False)
                       for n in ("aoa", "aoa150", "aoa_sfc"))
        pulses = tuple(TracerSpec(n, units="1", initial_value=0.0, nondimensionalize=False) for n in cls._pulse_names)
        sources = tuple(TracerSpec(n, units="1", initial_value=0.0, nondimensionalize=False) for n in cls._source_names)
        steady = tuple(TracerSpec(n, units="1", initial_value=1.0, nondimensionalize=False) for n in STEADY)
        return clocks + (TracerSpec("sai", units="1", initial_value=0.0, nondimensionalize=False),) + pulses + sources + steady

    # ------------------------------------------------------------------ setup
    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(P0_PA)
        sigma = np.asarray(sigma, dtype=np.float64)
        lat, lon = column_lat_lon(coords.horizontal)
        lat = np.asarray(lat, dtype=np.float64); lon = np.asarray(lon, dtype=np.float64)      # radians, (ncols,)
        n = sigma.shape[0]; idx = np.arange(n)
        surf_first = bool(sigma[0] > sigma[-1])
        def lowest(k):
            return (idx < k) if surf_first else (idx >= n - k)
        self._sigma = nnx.Variable(jnp.asarray(sigma))
        self._lat = nnx.Variable(jnp.asarray(lat))
        self._absorb_mask = nnx.Variable(jnp.asarray(lowest(self.absorb_layers)))
        self._sfc_mask = nnx.Variable(jnp.asarray(lowest(self.sfc_layers)))
        # blobs on the reference pressure (sigma * P0): pulses (npulse, nlev, ncols), sources (nsrc, nlev, ncols)
        zeta = np.log10(sigma * P0_PA / 1000e2)                                                # log10(p / 1000 hPa)
        def blob(lat0, lon0, p0, amp):
            la0, lo0 = np.deg2rad(lat0), np.deg2rad(lon0)
            cosang = np.sin(lat) * np.sin(la0) + np.cos(lat) * np.cos(la0) * np.cos(lon - lo0)
            theta = np.arccos(np.clip(cosang, -1.0, 1.0))                                      # (ncols,)
            z0 = np.log10(p0 / 1000.0)
            return amp * np.exp(-0.5 * (theta / self.sigma_h) ** 2)[None, :] * np.exp(-0.5 * ((zeta - z0) / self.sigma_z) ** 2)[:, None]
        self._targets = nnx.Variable(jnp.asarray(np.stack([blob(*c) for c in self.pulses]), jnp.float32))
        self._sources = nnx.Variable(jnp.asarray(np.stack([blob(*c) for c in self.sources]), jnp.float32))
        # WACCM reference: (lev, lat) -> model (nlev, ncols), latitude first then ln p
        ref = xr.open_dataset(self.ref_file)
        lat_deg = np.rad2deg(lat)
        lp_ref = np.log(ref.lev.values.astype(np.float64)); lp_mod = np.log(sigma * P0_PA / 100.0)
        order = np.argsort(lp_ref); lp_ref = lp_ref[order]
        fields = {}
        for sp in STEADY:
            for kind in ("q0", "k"):
                src = ref[f"{sp}_{kind}"].values.astype(np.float64)[order]                    # (lev, lat), lev ascending in p
                on_lat = np.stack([np.interp(lat_deg, ref.lat.values, src[k]) for k in range(src.shape[0])])   # (lev, ncols)
                fields[f"{sp}_{kind}"] = np.stack([np.interp(lp_mod, lp_ref, on_lat[:, j]) for j in range(on_lat.shape[1])], axis=1)
        self._q0 = nnx.Variable(jnp.asarray(np.stack([fields[f"{sp}_q0"] for sp in STEADY]), jnp.float32))   # (2, nlev, ncols)
        self._k = nnx.Variable(jnp.asarray(np.stack([fields[f"{sp}_k"] for sp in STEADY]), jnp.float32))     # (2, nlev, ncols), 1/s
        self._coords_cached = True

    def _pressure(self, normalized_surface_pressure):
        return self._sigma.get_value()[:, jnp.newaxis] * normalized_surface_pressure * P0_PA

    # ------------------------------------------------------------------ step
    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        dt = diagnostics["_dt_seconds"]
        p = self._pressure(state.normalized_surface_pressure)
        lat = self._lat.get_value()
        solar = getattr(forcing, "solar", None)
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        x = tyear * 365.0                                     # model-days into the year
        period = 365.0 / self.n_pulses
        first = jnp.logical_and(self.first_segment, x < dt / DAY)             # very first step of the run
        if self.injection == "once":
            fire = first
        else:
            fire = jnp.floor(x / period) != jnp.floor((x - dt / DAY) / period)  # an injection date lies in this step
        absorb = self._absorb_mask.get_value()[:, jnp.newaxis]
        sfc = self._sfc_mask.get_value()[:, jnp.newaxis]
        tr = state.tracers
        d = {}
        d["aoa"] = jnp.where(p > self.aoa_reset_pa, -tr["aoa"] / dt, 1.0 / DAY)
        d["aoa150"] = jnp.where(p > self.aoa150_reset_pa, -tr["aoa150"] / dt, 1.0 / DAY)
        d["aoa_sfc"] = jnp.where(sfc, -tr["aoa_sfc"] / dt, 1.0 / DAY)
        sai_box = (jnp.abs(lat) <= self.sai_lat) & (p >= self.sai_p_top_pa) & (p <= self.sai_p_bot_pa)
        d["sai"] = jnp.where(sai_box, self.sai_source_per_s, 0.0)
        targets = self._targets.get_value()
        for i, name in enumerate(self._pulse_names):
            q = tr[name]
            d[name] = jnp.where(fire, (targets[i] - q) / dt, jnp.where(absorb, -q / dt, 0.0))
        srcs = self._sources.get_value()
        for i, name in enumerate(self._source_names):
            q = tr[name]
            d[name] = jnp.where(absorb, -q / dt, self.source_rate * srcs[i])
        q0 = self._q0.get_value(); kk = self._k.get_value()
        for i, name in enumerate(STEADY):
            q = tr[name]
            k_safe = jnp.minimum(kk[i], 0.25 / dt)            # forward-Euler safety for the fastest loss
            steady = jnp.where(p > self.steady_source_pa, (1.0 - q) / dt, -k_safe * q)
            d[name] = jnp.where(first, (q0[i] - q) / dt, steady)
        k = self._per_s                                       # per-second -> per nondimensional time
        zeros = jnp.zeros_like(state.temperature)
        return PhysicsTendency(u_wind=zeros, v_wind=zeros, temperature=zeros, specific_humidity=zeros,
                               tracers={n: k * v for n, v in d.items()}), diagnostics


for _i, (_lat, _lon, _p, _amp) in enumerate(DEFAULT_PULSES):
    ProductionTracers.output_attrs[f"pulse_{_i + 1}"] = {
        "units": "1",
        "long_name": (f"pulse tracer {_i + 1}: Gaussian blob (amplitude {_amp}, centre {_lat} deg lat, {_lon} deg E, "
                      f"{_p} hPa; sigma 12 deg, 0.25 decades) injected once at the start of the run, absorbed in the lowest two layers"),
    }
for _i, (_lat, _lon, _p, _amp) in enumerate(DEFAULT_SOURCES):
    ProductionTracers.output_attrs[f"src_{_i + 1}"] = {
        "units": "1",
        "long_name": (f"continuous-source tracer {_i + 1}: Gaussian blob source (amplitude {_amp} per 90 d, centre {_lat} deg lat, "
                      f"{_lon} deg E, {_p} hPa; sigma 12 deg, 0.25 decades) every step, absorbed in the lowest two layers"),
    }
