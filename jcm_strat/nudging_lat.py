"""Latitude-dependent top of the ERA5 tropospheric nudging (Phase 23).

JCM's ``nudging.min_pressure_hpa`` is one pressure for the whole globe, applied per level at the
level's reference pressure (``jcm.runners._nudging_inv_tau``). A global value cannot follow the
tropopause: 150 hPa nudges the extratropical lowermost stratosphere, 400 hPa (13c, 21a) stops
nudging the tropical upper troposphere and loses the shallow branch. This term puts the top of the
nudged region at ``p_trop_hpa`` inside |lat| <= ``lat_full_deg`` and at ``p_pole_hpa`` poleward of
``lat_zero_deg``, blended in log p with a cos^2 in latitude across the subtropical tropopause break
(the same window shape as QboNudging). Below the top the weight ramps from 0 to 1 over
``taper_decades`` of log10 p instead of JCM's hard step.

The weight multiplies the tendency of JCM's own NudgingTerm (winds, temperature and, where nudged, humidity), so tau,
``pbl_levels``, ``nudge_temperature`` and the ERA5 target are unchanged. JCM's per-level mask still applies on top:
``min_pressure_hpa`` must be at or above the smallest top (``p_trop_hpa``), else it is the binding cut.

Config (``nudging.lat_top`` absent or null: JCM's global cut alone, as before Phase 23)::

    nudging:
      min_pressure_hpa: 100.0   # <= p_trop_hpa; the latitude profile below is the real cut
      lat_top:
        p_trop_hpa: 150.0
        p_pole_hpa: 400.0
        lat_full_deg: 20.0
        lat_zero_deg: 35.0
        taper_decades: 0.1
"""
from __future__ import annotations

import logging

import jax.numpy as jnp
import numpy as np
from flax import nnx

import jcm.nudging as _jcm_nudging
from jcm.physics.coords_util import column_lat_lon
from jcm.physics_interface import PhysicsTendency

P0_PA = 101325.0


def top_hpa(lat_deg, p_trop_hpa, p_pole_hpa, lat_full_deg, lat_zero_deg):
    """Top of the nudged region (hPa) at each latitude; log-p blend, cos^2 in latitude."""
    a = np.abs(np.asarray(lat_deg, dtype=np.float64))
    w_trop = np.where(a <= lat_full_deg, 1.0, np.where(a >= lat_zero_deg, 0.0,
                      np.cos(0.5 * np.pi * (a - lat_full_deg) / (lat_zero_deg - lat_full_deg)) ** 2))
    return np.exp(w_trop * np.log(p_trop_hpa) + (1.0 - w_trop) * np.log(p_pole_hpa))


def weights(p_ref_hpa, lat_deg, *, p_trop_hpa=150.0, p_pole_hpa=400.0, lat_full_deg=20.0,
            lat_zero_deg=35.0, taper_decades=0.1):
    """(nlev, n) weight: 0 above the top, rising linearly in log10 p to 1 ``taper_decades`` below it."""
    top = top_hpa(lat_deg, p_trop_hpa, p_pole_hpa, lat_full_deg, lat_zero_deg)
    d = np.log10(np.asarray(p_ref_hpa, dtype=np.float64))[:, None] - np.log10(top)[None, :]
    if taper_decades <= 0:
        return (d >= 0).astype(np.float64)
    return np.clip(d / taper_decades, 0.0, 1.0)


class LatTopNudgingTerm(_jcm_nudging.NudgingTerm):
    """JCM's NudgingTerm with its tendency multiplied by a (level, latitude) weight."""

    def __init__(self, config, **lat_top):
        super().__init__(config)
        self.lat_top = dict(lat_top)

    def cache_coords(self, coords) -> None:
        super().cache_coords(coords)
        vertical = coords.vertical
        if hasattr(vertical, "a_centers"):          # same reference pressure as jcm.runners
            p_ref = (np.asarray(vertical.a_centers) + np.asarray(vertical.b_centers) * P0_PA) / 100.0
        else:
            p_ref = np.asarray(vertical.centers) * P0_PA / 100.0
        lat_cols, _ = column_lat_lon(coords.horizontal)               # radians, column order
        self._w = nnx.Variable(jnp.asarray(weights(p_ref, np.rad2deg(np.asarray(lat_cols)), **self.lat_top),
                                           jnp.float32))              # (nlev, ncols)

    def __call__(self, state, diagnostics, forcing, terrain):
        tend, diagnostics = super().__call__(state, diagnostics, forcing, terrain)
        # (nlev, ncols) on the column-vectorized path; the row-major reshape back to
        # (nlev, nlon, nlat) is the one ComposablePhysics uses, so either host works.
        w = self._w.get_value().reshape(state.u_wind.shape)
        return PhysicsTendency(
            u_wind=w * tend.u_wind, v_wind=w * tend.v_wind, temperature=w * tend.temperature,
            specific_humidity=w * tend.specific_humidity, tracers=tend.tracers,
        ), diagnostics


def install_lat_top(lat_top: dict | None) -> None:
    """Make jcm's ``with_nudging`` build a LatTopNudgingTerm (``nudging.lat_top`` mapping; None: no-op).

    ``jcm.runners.maybe_add_nudging`` imports ``with_nudging`` from ``jcm.nudging`` at call time, so
    patching the module attribute is enough (same style as the install_* hooks in main.py).
    """
    if not lat_top:
        return
    lat_top = dict(lat_top)

    def with_nudging(physics, config):
        return physics + LatTopNudgingTerm(config, **lat_top)

    _jcm_nudging.with_nudging = with_nudging
    logging.getLogger("jcm_strat").info("jcm_strat: nudging top by latitude %s", lat_top)
