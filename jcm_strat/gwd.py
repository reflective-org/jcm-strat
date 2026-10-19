"""Gravity-wave drag for the dry (Held-Suarez / Polvani-Kushner) column physics — Phase 13.

JCM's :class:`~jcm.physics.gravity_waves.hines.HinesGwd` launches its wave spectrum from a level
counted from the SURFACE (``launch_level`` = 10 levels above the surface, ECHAM's ``emiss_lev``),
which is 634 hPa on L95 but 126 hPa — in the stratosphere — on the strat63 table with its
8 tropospheric layers. :class:`HinesGwdLaunch` therefore takes the launch level as a PRESSURE and
resolves the level index from the run's vertical coordinate in :meth:`cache_coords` (nearest full
level at the reference surface pressure 1013.25 hPa), so the same yaml means the same thing on
every level table. The default 634 hPa is what the Phase 12 full-physics reference (L95, JCM's
default launch level) used. The tunable :class:`~jcm.physics.gravity_waves.hines.HinesParameters`
are exposed as plain keyword arguments so the yaml can set them (``rms_launch_wind`` is the
amplitude knob; PLANS Phase 13: retune it once if the drag over-drives the circulation as the
full-physics run did).

The term requires the moist-air diagnostics (``pressure_full``, ``pressure_half``, ``height_half``,
``air_density``) that :class:`~jcm.physics.diagnostics.moist_air_state.MoistAirColumnState`
provides, so that prepare term must precede it in the physics list (composable_physics validates
the ordering at construction). Lott-Miller orographic drag (:class:`jcm.physics.gravity_waves.sso.LottMillerSso`)
needs no such adaptation and is used as it is; its sub-grid orography fields come from the T63
terrain file the dry runs already load (``hf://bundles/t63/terrain.nc`` carries orostd/orosig/
orogam/orothe/oropic/oroval).
"""
from __future__ import annotations

import logging

import jax
import jax.numpy as jnp
import numpy as np
from jcm import constants as _physical_constants
from jcm.physics.gravity_waves.hines.hines import HinesGwd, HinesParameters, hines_gwd
from jcm.physics_interface import PhysicsTendency

_log = logging.getLogger("jcm_strat")
_P_SURFACE_REF_PA = 101325.0


def launch_level_for(vertical, launch_p_hpa: float) -> tuple[int, float]:
    """(launch_level, p_full_hpa): ``hines_gwd``'s 1-based count of levels above the surface whose
    full level (at 1013.25 hPa surface pressure) is nearest ``launch_p_hpa``, and that level's pressure."""
    if hasattr(vertical, "a_centers"):
        p_full = np.asarray(vertical.a_centers) + np.asarray(vertical.b_centers) * _P_SURFACE_REF_PA
    else:
        p_full = np.asarray(vertical.centers) * _P_SURFACE_REF_PA
    nlev = p_full.size
    idx = int(np.argmin(np.abs(p_full / 100.0 - float(launch_p_hpa))))
    level = nlev - idx - 1                       # hines_gwd: launch_idx = nlev - launch_level - 1
    if level < 1:
        raise ValueError(f"launch pressure {launch_p_hpa} hPa resolves to the lowest level; hines_gwd needs launch_level >= 1")
    return level, float(p_full[idx] / 100.0)


class HinesGwdLaunch(HinesGwd):
    """:class:`HinesGwd` with the launch level given as a pressure (resolved per level table)."""

    def __init__(self, launch_p_hpa: float = 634.0, rms_launch_wind: float = 1.0, **hines_params) -> None:
        super().__init__(HinesParameters.default(rms_launch_wind=float(rms_launch_wind), **hines_params))
        self.launch_p_hpa = float(launch_p_hpa)
        self.rms_launch_wind = float(rms_launch_wind)
        self.launch_level: int | None = None     # set by cache_coords
        self.launch_p_resolved_hpa: float | None = None

    def cache_coords(self, coords) -> None:
        super().cache_coords(coords)
        self.launch_level, self.launch_p_resolved_hpa = launch_level_for(coords.vertical, self.launch_p_hpa)
        nlev = int(np.asarray(coords.vertical.a_centers if hasattr(coords.vertical, "a_centers") else coords.vertical.centers).size)
        _log.info("HinesGwdLaunch: L%d, launch %g hPa -> launch_level %d (full level %.0f hPa), rms_launch_wind %g m/s",
                  nlev, self.launch_p_hpa, self.launch_level, self.launch_p_resolved_hpa, self.rms_launch_wind)

    def __call__(self, state, diagnostics, forcing, terrain):
        if self.launch_level is None:
            raise RuntimeError("HinesGwdLaunch.cache_coords was not called before the first step")
        params = self.params.get_value()
        pressure_full = diagnostics["pressure_full"]
        pressure_half = diagnostics["pressure_half"]
        height_half = diagnostics["height_half"]
        air_density = diagnostics["air_density"]
        layer_mass = (pressure_half[1:, :] - pressure_half[:-1, :]) / _physical_constants.grav
        launch_level = int(self.launch_level)
        tend, _state = jax.vmap(
            lambda *a: hines_gwd(*a, params, launch_level=launch_level),
            in_axes=(1, 1, 1, 1, 1, 1, 1, 1), out_axes=(0, 0),
        )(pressure_half, pressure_full, height_half, air_density, layer_mass,
          state.temperature, state.u_wind, state.v_wind)
        dt_temperature = tend.dissip / _physical_constants.cpd
        return PhysicsTendency(u_wind=tend.dudt.T, v_wind=tend.dvdt.T, temperature=dt_temperature.T,
                               specific_humidity=jnp.zeros_like(state.specific_humidity), tracers={}), diagnostics
