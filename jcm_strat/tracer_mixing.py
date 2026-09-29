"""Tropospheric vertical tracer mixing — Phase 16, the stand-in for convective tracer transport in the dry model.

Phase 12 addendum: the dry model's troposphere has no convection and no boundary-layer turbulence, so a tracer takes
~1.7 yr from 500 to 100 hPa in the tropics (ECHAM 0.16 yr) and the SURFACE clock (CLaMS' own clock) reads 2 yr too old
at 55 hPa (3.3 vs 1.3 yr) even where the stratospheric ENTRY age is right. Under the ERA5 nudging the tropospheric
temperature is already ERA5's, so a dry convective adjustment would have nothing to adjust and would move no tracer;
what is missing is the tracer transport itself. This term mixes every tracer vertically in the troposphere:

    dC/dt = g^2 d/dp ( rho^2 K(p) dC/dp ),     rho = p / (R_d T)

i.e. a vertical diffusion with coefficient ``k_m2_s`` [m^2/s] (Fickian in height, written in pressure), applied
where p > ``p_top_hpa`` (100 hPa: zero at and above it) with full strength below ``p_full_hpa`` (200 hPa) and a
linear ramp between, so the stratosphere and the tropopause layer are untouched. A diffusivity of 10-30 m^2/s over
an 8 km deep troposphere gives an exchange time H^2/K of 0.7-0.2 yr, the order of ECHAM's convective transit.
Optionally confined to the tropics (``lat_max_deg``, cos^2 taper) since deep convection is; the default mixes at every
latitude (the dry model has no boundary-layer mixing anywhere).

The update is IMPLICIT (backward Euler, one tridiagonal solve per column and tracer, ``jax.lax.linalg.tridiagonal_solve``)
and the tendency handed back is (C_new - C) / dt with the model step from ``diagnostics["_dt_seconds"]``: the strat81
levels are ~100 m thick near the surface, where an explicit update is unstable for any K above ~5 m^2/s at the 12-minute
step (the first smoke test produced NaN clocks at K 30). Flux form with zero flux through the top and bottom interfaces:
the column mass of every tracer is conserved to roundoff (unit-tested; the implicit step conserves it exactly too since
the operator telescopes). Without ``_dt_seconds`` in the diagnostics (unit tests) the explicit tendency is returned.
Winds and temperature are not touched.
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
R_DRY = 287.05
GRAVITY = 9.80665


def mixing_profile(p_hpa, p_top_hpa: float, p_full_hpa: float):
    """0 at and above p_top, 1 at and below p_full, linear in p between (on the given pressures, hPa)."""
    p = np.asarray(p_hpa, float)
    return np.clip((p - p_top_hpa) / (p_full_hpa - p_top_hpa), 0.0, 1.0)


class TropoTracerMixing(PhysicsTerm):
    """Vertical diffusion of every tracer below ``p_top_hpa`` with diffusivity ``k_m2_s`` (m^2/s)."""

    name: ClassVar[str] = "tropo_tracer_mixing"
    category: ClassVar[str] = "tropo_tracer_mixing"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()

    def __init__(self, k_m2_s: float = 10.0, p_top_hpa: float = 100.0, p_full_hpa: float = 200.0,
                 lat_max_deg: float | None = None) -> None:
        if not float(k_m2_s) >= 0.0:
            raise ValueError("k_m2_s must be >= 0")
        if not float(p_full_hpa) > float(p_top_hpa):
            raise ValueError("p_full_hpa must be larger (lower in the atmosphere) than p_top_hpa")
        self.k_m2_s = float(k_m2_s)
        self.p_top_hpa = float(p_top_hpa)
        self.p_full_hpa = float(p_full_hpa)
        self.lat_max_deg = None if lat_max_deg is None else float(lat_max_deg)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._per_s = float(specs.nondimensionalize(1.0 / units.second))       # per-second rate -> model time units
        self._k_per_nondim = float(specs.nondimensionalize(1.0 * units.degK))  # K -> model temperature units
        self._coords_cached = False

    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = np.asarray(vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(P0_PA))
        self._sigma = nnx.Variable(jnp.asarray(sigma)[:, jnp.newaxis])                        # (nlev, 1)
        prof = mixing_profile(sigma * P0_PA / 100.0, self.p_top_hpa, self.p_full_hpa)
        lat, _ = column_lat_lon(coords.horizontal)
        lat = np.asarray(lat)
        if self.lat_max_deg is not None:
            x = np.clip(np.abs(np.rad2deg(lat)) / self.lat_max_deg, 0.0, 1.0)
            latw = np.cos(0.5 * np.pi * x) ** 2
        else:
            latw = np.ones_like(lat)
        self._k = nnx.Variable(jnp.asarray(self.k_m2_s * prof[:, None] * latw[None, :]))      # (nlev, ncols), m^2/s
        active = prof > 0
        p_hpa = sigma * P0_PA / 100.0
        dz_min = float(np.min(np.abs(np.diff(np.log(p_hpa[active]))) * 7000.0)) if active.sum() > 1 else float("nan")
        _log.info("TropoTracerMixing: L%d, K %g m^2/s below %g hPa (full below %g hPa)%s; %d active levels (%.0f-%.0f hPa), "
                  "thinnest active layer ~%.0f m (explicit K dt/dz^2 would be %.2f at dt 12 min; the update is implicit)",
                  sigma.size, self.k_m2_s, self.p_top_hpa, self.p_full_hpa,
                  f", |lat| < {self.lat_max_deg:g}" if self.lat_max_deg is not None else "", int(active.sum()),
                  p_hpa[active].min() if active.any() else float("nan"), p_hpa[active].max() if active.any() else float("nan"),
                  dz_min, self.k_m2_s * 720.0 / dz_min ** 2 if dz_min == dz_min else float("nan"))
        self._coords_cached = True

    @staticmethod
    def _operator(p_pa, t_k, k):
        """Tridiagonal coefficients (a, b, c) of the flux-form operator L on (nlev, ncols): (L C)_k = a_k C_{k-1} + b_k C_k + c_k C_{k+1}
        [1/s]; zero flux through the top and bottom interfaces (levels in any monotonic order)."""
        rho = p_pa / (R_DRY * t_k)
        dp = p_pa[1:] - p_pa[:-1]                                          # (nlev-1, ncols), between full levels
        d_int = GRAVITY ** 2 * (0.5 * (rho[1:] + rho[:-1])) ** 2 * 0.5 * (k[1:] + k[:-1])   # D at the interfaces
        p_half = jnp.concatenate([p_pa[:1] - 0.5 * dp[:1], 0.5 * (p_pa[1:] + p_pa[:-1]), p_pa[-1:] + 0.5 * dp[-1:]], axis=0)
        thick = p_half[1:] - p_half[:-1]                                   # (nlev, ncols)
        g = d_int / dp                                                     # (nlev-1, ncols): flux per unit concentration difference
        zeros = jnp.zeros_like(g[:1])
        c = jnp.concatenate([g, zeros], axis=0) / thick                    # coupling to the level below (index k+1)
        a = jnp.concatenate([zeros, g], axis=0) / thick                    # coupling to the level above (index k-1)
        return a, -(a + c), c

    def tendency_per_second(self, tracer, p_pa, t_k, k):
        """Explicit dC/dt [1/s] on (nlev, ncols) (used when the step length is not available, e.g. in unit tests)."""
        a, b, c = self._operator(p_pa, t_k, k)
        up = jnp.concatenate([jnp.zeros_like(tracer[:1]), tracer[:-1]], axis=0)
        dn = jnp.concatenate([tracer[1:], jnp.zeros_like(tracer[:1])], axis=0)
        return a * up + b * tracer + c * dn

    def implicit_tendency_per_second(self, tracer, p_pa, t_k, k, dt_s):
        """(C_new - C) / dt [1/s] with C_new the backward-Euler solution of (I - dt L) C_new = C, column by column."""
        a, b, c = self._operator(p_pa, t_k, k)
        dl, d, du = (-dt_s * a).T, (1.0 - dt_s * b).T, (-dt_s * c).T      # (ncols, nlev); dl[:, 0] = du[:, -1] = 0 by construction
        rhs = tracer.T[..., jnp.newaxis]                                   # (ncols, nlev, 1)
        c_new = jax.lax.linalg.tridiagonal_solve(dl, d, du, rhs)[..., 0].T
        return (c_new - tracer) / dt_s

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        if not self._coords_cached:
            raise RuntimeError("TropoTracerMixing.cache_coords was not called before the first step")
        k = self._k.get_value()
        p_pa = self._sigma.get_value() * state.normalized_surface_pressure[jnp.newaxis, :] * P0_PA
        t_k = state.temperature / self._k_per_nondim
        dt_s = diagnostics.get("_dt_seconds") if isinstance(diagnostics, dict) else None
        if dt_s is None:
            tend = {name: self.tendency_per_second(c, p_pa, t_k, k) * self._per_s for name, c in state.tracers.items()}
        else:
            tend = {name: self.implicit_tendency_per_second(c, p_pa, t_k, k, dt_s) * self._per_s for name, c in state.tracers.items()}
        zeros = jnp.zeros_like(state.temperature)
        return PhysicsTendency(u_wind=zeros, v_wind=zeros, temperature=zeros,
                               specific_humidity=jnp.zeros_like(state.specific_humidity), tracers=tend), diagnostics
