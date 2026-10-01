"""Jucker, Fueglistaler & Vallis (2013) stratospheric relaxation on the column path — Phase 13b.

Polvani-Kushner relaxes the stratosphere toward the US standard atmosphere (plus a winter-cap cooling
that is faded out above 3 hPa) with one 15-day timescale. JFV2013 ("Maintenance of the stratospheric
structure in an idealized general circulation model", JAS 70, 3341) instead prescribe the equilibrium
temperature T_e(month, p, lat) and the relaxation time tau(month, p, lat) from a radiative calculation
with ozone and a seasonal cycle: a ~300 K summer stratopause, a 190-205 K winter polar upper
stratosphere, tau of 25-40 d in the lower stratosphere, 5-10 d at 10 hPa and 4.5-6 d at 1-0.1 hPa.
Their data (`github.com/mjucker/JFV-strat`, `temp_monthly_L10_full.nc` / `tau_monthly_L10_full.nc`,
zonally uniform) is stored as `jcm_strat/data/jfv2013_te_tau_zm.nc`: 12 mid-month days of a 365-day
year x 40 pressure levels (0.007-945 hPa) x 64 Gaussian latitudes.

:class:`JuckerColumns` subclasses :class:`~jcm_strat.qbo_nudging.PolvaniKushnerQbo` so the QBO nudging,
the Held-Suarez boundary-layer friction and the tropospheric equilibrium are unchanged:

* above ``p_bd`` (100 hPa) T_e and 1/tau are the JFV fields, interpolated in log-pressure and latitude
  onto the run's levels and columns once in :meth:`cache_coords`, and linearly (periodic) in the
  fraction of year between mid-months at every step;
* below ``p_hs`` (250 hPa) the parent's troposphere: Held-Suarez T_eq with the PK winter asymmetry,
  Held-Suarez k_T;
* between the two a linear blend in pressure — JFV's own ``hs_forcing.f90`` defaults
  (``p_hs = 250e2, p_bd = 100e2``). The parent's PK stratosphere never enters because ``p_bd`` must not
  exceed the parent's tropopause pressure (asserted).

Under the ERA5 nudging of u, v, T below 150 hPa the troposphere and the blend region are held to ERA5
anyway; the change acts from 150 hPa up. The reference surface pressure 1013.25 hPa fixes the level
pressures of the table and of the blend (as ``PolvaniKushnerColumns._kt`` does).
"""
from __future__ import annotations

import logging
import os

import jax.numpy as jnp
import numpy as np
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics_interface import PhysicsState, PhysicsTendency

from jcm_strat.held_suarez_columns import HeldSuarezColumns
from jcm_strat.polvani_kushner import P0_PA
from jcm_strat.qbo_nudging import PolvaniKushnerQbo

_log = logging.getLogger("jcm_strat")
DEFAULT_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jfv2013_te_tau_zm.nc")
DAYS_PER_YEAR = 365.0


def load_jfv_table(path: str = DEFAULT_DATA):
    """(day_of_year[12], p_hpa[np] ascending, lat_deg[nlat] ascending, te[12, np, nlat] K, tau[12, np, nlat] s)."""
    import xarray as xr
    with xr.open_dataset(path, decode_times=False) as d:
        d = d.sortby("pfull").sortby("lat")
        return (np.asarray(d.day_of_year.values, float), np.asarray(d.pfull.values, float), np.asarray(d.lat.values, float),
                np.asarray(d.te.values, float), np.asarray(d.tau.values, float))


def interpolate_table(field, p_hpa, lat_deg, p_out_hpa, lat_out_deg):
    """Bilinear (log-p, lat) interpolation of ``field[12, np, nlat]`` onto ``(12, nlev, ncols)``; clamped at the edges."""
    lp, lpo = np.log(p_hpa), np.log(np.asarray(p_out_hpa, float))
    lat_out = np.asarray(lat_out_deg, float)
    out = np.empty((field.shape[0], lpo.size, lat_out.size))
    for m in range(field.shape[0]):
        on_lat = np.stack([np.interp(lat_out, lat_deg, field[m, k, :]) for k in range(lp.size)])      # (np, ncols)
        out[m] = np.stack([np.interp(lpo, lp, on_lat[:, j]) for j in range(lat_out.size)], axis=1)      # (nlev, ncols)
    return out


class JuckerColumns(PolvaniKushnerQbo):
    """PolvaniKushnerQbo with the JFV2013 equilibrium temperature and relaxation time above ``p_bd_hpa``."""

    def __init__(self, data_file: str = DEFAULT_DATA, p_bd_hpa: float = 100.0, p_hs_hpa: float = 250.0, **pk_kwargs) -> None:
        super().__init__(**pk_kwargs)
        if float(p_bd_hpa) > self.p_t_pa / 100.0:
            raise ValueError(f"p_bd_hpa={p_bd_hpa} must not exceed the tropopause pressure {self.p_t_pa / 100.0} hPa "
                             "(the Polvani-Kushner stratosphere would show through the blend)")
        if not float(p_hs_hpa) > float(p_bd_hpa):
            raise ValueError("p_hs_hpa must be larger (lower in the atmosphere) than p_bd_hpa")
        self.data_file = str(data_file)
        self.p_bd_pa = float(p_bd_hpa) * 100.0
        self.p_hs_pa = float(p_hs_hpa) * 100.0
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(self.data_file)
        # (the table itself is loaded in cache_coords: nnx forbids array data in plain attributes)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._k_per_inv_second = float(specs.nondimensionalize(1.0 / units.second))

    # --- coordinate-dependent tables -----------------------------------------------------
    def cache_coords(self, coords) -> None:
        super().cache_coords(coords)
        days, p_hpa, lat_deg, te, tau = load_jfv_table(self.data_file)
        month_nodes = np.concatenate([[days[-1] / DAYS_PER_YEAR - 1.0], days / DAYS_PER_YEAR, [days[0] / DAYS_PER_YEAR + 1.0]])
        p_ref_hpa = np.asarray(self._sigma.get_value()) * P0_PA / 100.0          # (nlev,)
        lat_cols = np.rad2deg(np.asarray(self._lat.get_value()))                   # (ncols,)
        te_tab = interpolate_table(te, p_hpa, lat_deg, p_ref_hpa, lat_cols) * self._k_per_nondim
        k_tab = self._k_per_inv_second / interpolate_table(tau, p_hpa, lat_deg, p_ref_hpa, lat_cols)
        self._te_tab = nnx.Variable(jnp.asarray(te_tab))                           # (12, nlev, ncols), model T units
        self._k_tab = nnx.Variable(jnp.asarray(k_tab))                             # (12, nlev, ncols), model 1/time units
        self._nodes = nnx.Variable(jnp.asarray(month_nodes))                       # (14,) fractions of year, periodic ends
        p_ref = np.asarray(self._sigma.get_value()) * P0_PA
        beta = np.clip((self.p_hs_pa - p_ref) / (self.p_hs_pa - self.p_bd_pa), 0.0, 1.0)   # 1 above p_bd, 0 below p_hs
        self._beta = nnx.Variable(jnp.asarray(beta)[:, jnp.newaxis])               # (nlev, 1)
        top = int(np.argmin(p_ref_hpa)); j_eq = int(np.argmin(np.abs(lat_cols)))
        tau_days = 1.0 / (k_tab / self._k_per_inv_second) / 86400.0
        _log.info("JuckerColumns: JFV2013 table (%s) on L%d x %d columns; JFV above %.0f hPa, Held-Suarez below %.0f hPa; "
                  "T_e at the top level (%.3f hPa) Jan: equator %.0f K, min %.0f, max %.0f K; tau range above p_bd %.1f-%.1f d",
                  os.path.basename(self.data_file), p_ref_hpa.size, lat_cols.size, self.p_bd_pa / 100, self.p_hs_pa / 100,
                  p_ref_hpa[top], te_tab[0, top, j_eq] / self._k_per_nondim, te_tab[0, top].min() / self._k_per_nondim,
                  te_tab[0, top].max() / self._k_per_nondim, tau_days[:, beta >= 1.0].min(), tau_days[:, beta >= 1.0].max())

    # --- time interpolation --------------------------------------------------------------
    def _month_weights(self, tyear):
        nodes = self._nodes.get_value()
        t = jnp.mod(jnp.asarray(tyear), 1.0)
        idx = jnp.clip(jnp.searchsorted(nodes, t, side="right") - 1, 0, nodes.size - 2)     # node[idx] <= t < node[idx+1]
        w = (t - nodes[idx]) / (nodes[idx + 1] - nodes[idx])
        return (idx - 1) % 12, idx % 12, w

    def _jfv(self, table, tyear):
        m0, m1, w = self._month_weights(tyear)
        return (1.0 - w) * table[m0] + w * table[m1]                               # (nlev, ncols)

    # --- equilibrium and rate --------------------------------------------------------------
    def _equilibrium_temperature(self, normalized_surface_pressure, tyear=0.0):
        t_hs = super()._equilibrium_temperature(normalized_surface_pressure, tyear)   # PK: Held-Suarez where p >= p_T
        beta = self._beta.get_value()
        return beta * self._jfv(self._te_tab.get_value(), tyear) + (1.0 - beta) * t_hs

    def _kt_jucker(self, tyear):
        k_hs = HeldSuarezColumns._kt(self)                                         # (nlev, ncols)
        beta = self._beta.get_value()
        return beta * self._jfv(self._k_tab.get_value(), tyear) + (1.0 - beta) * k_hs

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        solar = getattr(forcing, "solar", None)
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        teq = self._equilibrium_temperature(state.normalized_surface_pressure, tyear)
        zeros = jnp.zeros_like(state.temperature)
        du = -self._kv() * state.u_wind
        if self.qbo is not None:
            qbo_solar = solar if self.qbo.use_calendar else None
            du = du + self.qbo.tendency(state.u_wind, qbo_solar.tyear if qbo_solar is not None else jnp.asarray(0.0))
        return PhysicsTendency(u_wind=du, v_wind=-self._kv() * state.v_wind,
                               temperature=-self._kt_jucker(tyear) * (state.temperature - teq),
                               specific_humidity=zeros), diagnostics
