"""Idealised upper-stratospheric Rayleigh drag — Phase 15 sweep, the stand-in for the missing wave drag.

Phases 13/13b: the dry model's one remaining circulation defect is the 50-20 hPa stall of the tropical
ascent (w* 0.03 vs WACCM6 0.26 mm/s at 30 hPa). By downward control that ascent is set by the wave drag
above ~30 hPa, which the dry model lacks entirely between the resolved waves and the sponge in the top
four levels; Hines + Lott-Miller at JCM defaults deposit their momentum below 50 hPa instead. The
fallback the Phase 13 plan named is a prescribed Rayleigh drag profile confined to the upper
stratosphere/mesosphere (Holton 1982; the mechanistic models of Shepherd & Shaw 2004), one tunable
number per run:

    du/dt = -k(p) u,   dv/dt = -k(p) v,
    k(p)  = (1 / tau_days) * clip( ln(p_bot / p) / ln(p_bot / p_top), 0, 1 ) ** power

i.e. zero at and below ``p_bot_hpa`` (30 hPa), rising in log-pressure to ``1 / tau_days`` at
``p_top_hpa`` (1 hPa) and constant above it up to the sponge (which then dominates). ``power`` = 1 is
the linear ramp; 2 concentrates the drag near the top of the range. ``zonal_mean_only`` restricts the
drag to the zonal-mean wind (segment sum over the columns of each latitude row, as the QBO nudging
does), leaving the eddies alone; the default drags the full wind as a sponge does.

The term drags the QBO-nudged tropical wind too (tau 1 d nudging against a 10-100 d drag: negligible).
Rayleigh drag is a known idealisation - it does not conserve angular momentum locally and its
"downward control" is spurious in the sense of Shepherd & Shaw 2004 - so it is a sweep knob to locate
how much drag, and where, the circulation needs, not a production component.
"""
from __future__ import annotations

import logging
from typing import ClassVar

import jax
import jax.numpy as jnp
import numpy as np
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics.coords_util import column_lat_lon
from jcm.physics.physics_term import PhysicsTerm
from jcm.physics_interface import PhysicsState, PhysicsTendency

_log = logging.getLogger("jcm_strat")
P0_PA = 101325.0
DAY = 86400.0


def drag_profile(p_hpa, p_bot_hpa: float, p_top_hpa: float, tau_days: float, power: float = 1.0):
    """k(p) in 1/s on the given pressures (hPa): 0 below p_bot, 1/tau at and above p_top, log-p ramp between."""
    p = np.asarray(p_hpa, float)
    x = np.clip(np.log(p_bot_hpa / p) / np.log(p_bot_hpa / p_top_hpa), 0.0, 1.0)
    return (x ** float(power)) / (float(tau_days) * DAY)


class RayleighDragProfile(PhysicsTerm):
    """Rayleigh drag on (u, v) with a prescribed log-pressure profile between ``p_bot_hpa`` and ``p_top_hpa``."""

    name: ClassVar[str] = "rayleigh_drag"
    category: ClassVar[str] = "rayleigh_drag"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()

    def __init__(self, p_bot_hpa: float = 30.0, p_top_hpa: float = 1.0, tau_days: float = 10.0, power: float = 1.0,
                 zonal_mean_only: bool = False) -> None:
        if not float(p_top_hpa) < float(p_bot_hpa):
            raise ValueError("p_top_hpa must be smaller (higher up) than p_bot_hpa")
        if not float(tau_days) > 0.0:
            raise ValueError("tau_days must be positive")
        self.p_bot_hpa = float(p_bot_hpa)
        self.p_top_hpa = float(p_top_hpa)
        self.tau_days = float(tau_days)
        self.power = float(power)
        self.zonal_mean_only = bool(zonal_mean_only)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._per_inv_second = float(specs.nondimensionalize(1.0 / units.second))
        self._coords_cached = False

    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(P0_PA)
        p_ref_hpa = np.asarray(sigma) * P0_PA / 100.0
        k = drag_profile(p_ref_hpa, self.p_bot_hpa, self.p_top_hpa, self.tau_days, self.power) * self._per_inv_second
        self._k = nnx.Variable(jnp.asarray(k)[:, jnp.newaxis])          # (nlev, 1), model 1/time units
        lat, _ = column_lat_lon(coords.horizontal)
        lat = np.asarray(lat)
        # latitude-row index of every column, for the zonal mean (rows = distinct latitudes)
        rows, inverse = np.unique(np.round(lat, 10), return_inverse=True)
        self._row = nnx.Variable(jnp.asarray(inverse.astype(np.int32)))
        self._ncols_per_row = nnx.Variable(jnp.asarray(np.bincount(inverse).astype(float)))
        self._nrows = int(rows.size)
        active = k > 0
        _log.info("RayleighDragProfile: L%d, drag %g hPa -> %g hPa, tau %g d at the top (power %g, %s); %d active levels, "
                  "tau at the first active level (%.2f hPa) %.0f d, at the top level (%.3f hPa) %.1f d",
                  p_ref_hpa.size, self.p_bot_hpa, self.p_top_hpa, self.tau_days, self.power,
                  "zonal mean only" if self.zonal_mean_only else "full wind", int(active.sum()),
                  p_ref_hpa[active].max() if active.any() else float("nan"),
                  1.0 / (k[active].max() / self._per_inv_second) / DAY if active.any() else float("nan"),
                  p_ref_hpa.min(), 1.0 / (k[np.argmin(p_ref_hpa)] / self._per_inv_second) / DAY)
        self._coords_cached = True

    def _zonal_mean(self, field):
        """(nlev, ncols) -> (nlev, ncols) with every column replaced by its latitude row's mean."""
        row = self._row.get_value(); n = self._ncols_per_row.get_value()
        sums = jax.vmap(lambda f: jax.ops.segment_sum(f, row, num_segments=self._nrows))(field)   # (nlev, nrows)
        return (sums / n)[:, row]

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        if not self._coords_cached:
            raise RuntimeError("RayleighDragProfile.cache_coords was not called before the first step")
        k = self._k.get_value()
        u, v = state.u_wind, state.v_wind
        if self.zonal_mean_only:
            u, v = self._zonal_mean(u), self._zonal_mean(v)
        zeros = jnp.zeros_like(state.temperature)
        return PhysicsTendency(u_wind=-k * u, v_wind=-k * v, temperature=zeros,
                               specific_humidity=jnp.zeros_like(state.specific_humidity), tracers={}), diagnostics
