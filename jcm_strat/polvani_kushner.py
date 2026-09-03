"""Polvani-Kushner (2002) stratospheric equilibrium with a seasonal cycle, on the column path.

Held-Suarez clamps its equilibrium temperature at 200 K, so above the tropopause the model
relaxes toward an isothermal stratosphere: no polar-night jet, no seasons (Phases 1-4, the
21 K RMS cold bias against ERA5). Polvani & Kushner (2002, GRL, "Tropospheric response to
stratospheric perturbations in a relatively simple general circulation model") replace the
clamp above ``p_T`` = 100 hPa with

    T_eq^strat(phi, p) = [1 - W(phi)] T_US(p) + W(phi) T_PV(p)

where ``T_US`` is the US Standard Atmosphere 1976 profile, ``T_PV(p) = T_US(p_T)
(p/p_T)^(R gamma / g)`` is a polar-vortex profile cooling at ``gamma`` K/km above the
tropopause, and ``W(phi) = 1/2 [1 + tanh((phi - phi_0)/delta_phi)]`` confines the cooling to
the winter polar cap (``phi_0`` = 50 deg, ``delta_phi`` = 10 deg). Below ``p_T`` the
Held-Suarez tropospheric equilibrium is kept, with the 200 K floor replaced by ``T_US(p)`` and
a hemispheric asymmetry ``- epsilon sin(phi)`` that cools the winter troposphere (PK02 eq. A1).

PK02 is a perpetual-solstice setup. Here the winter hemisphere follows the calendar: with
``s(t) = cos(2 pi (tyear - t_peak))`` and ``t_peak`` = mid-January, the northern cap uses
amplitude ``A_N = clip((s + c) / (1 + c), 0, 1)`` and the southern cap the same with ``-s``,
where ``c = season_offset``. ``c = 0`` gives ``max(0, s)``: each vortex exists for half the
year and is at full strength only briefly around the solstice (the first Phase-6 run: cooling
arrived two months late in autumn and the vortices were too weak). ``c = 0.5`` starts the
cooling at the autumn equinox, holds it near full strength through the three winter months and
ends it after the spring equinox, which is when the real polar night, and the radiative cooling
it stands in for, exist. ``epsilon(t) = epsilon_0 s(t)`` in the troposphere either way. The
fraction of year comes from ``forcing.solar.tyear`` (populated by ``ForcingData.select`` from the
run calendar), the same field the SPEEDY shortwave scheme reads.

The stratospheric relaxation time ``tau_strat_days`` is a separate knob (default 40 d = PK02 =
Held-Suarez ``k_a``). Duncan's handover argues for the real radiative damping time, 5-20 days,
once aerosol heating is switched on; the Phase 6 A/B tests 40 vs 15 d.

Everything else (Rayleigh friction, tropospheric relaxation rates, per-column layout) is
inherited from ``HeldSuarezColumns``. Note that ``gamma = 0`` is not Held-Suarez: the winter
cap then relaxes toward an isothermal ``T_US(p_T)`` = 216.65 K, and everywhere the ``T_US``
floor replaces the 200 K clamp (a warmer high-latitude troposphere than Held-Suarez, as in
PK02; irrelevant under ERA5 nudging below 150 hPa).
"""
from __future__ import annotations

from typing import ClassVar

import jax.numpy as jnp
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics_interface import PhysicsState, PhysicsTendency

from jcm_strat.held_suarez_columns import HeldSuarezColumns

P0_PA = 101325.0
# US Standard Atmosphere 1976: layer base pressure [Pa], base temperature [K], lapse dT/dz [K/m].
_USSA = (
    (101325.0, 288.15, -6.5e-3),   # 0-11 km
    (22632.1, 216.65, 0.0),        # 11-20 km
    (5474.89, 216.65, 1.0e-3),     # 20-32 km
    (868.019, 228.65, 2.8e-3),     # 32-47 km
    (110.906, 270.65, 0.0),        # 47-51 km
    (66.9389, 270.65, -2.8e-3),    # 51-71 km
    (3.95642, 214.65, -2.0e-3),    # 71-85 km
)
R_DRY = 287.05
GRAVITY = 9.80665


def standard_atmosphere_temperature(p_pa):
    """T_US(p) [K] for pressure in Pa (any array); hydrostatic within each USSA layer."""
    t = jnp.full_like(p_pa, _USSA[0][1])
    for p_b, t_b, lapse in _USSA:
        in_layer = p_pa <= p_b
        if lapse == 0.0:
            t_layer = jnp.full_like(p_pa, t_b)
        else:
            t_layer = t_b * (p_pa / p_b) ** (-R_DRY * lapse / GRAVITY)
        t = jnp.where(in_layer, t_layer, t)
    return t


class PolvaniKushnerColumns(HeldSuarezColumns):
    """Held-Suarez troposphere + PK02 stratosphere with a calendar-driven winter hemisphere."""

    name: ClassVar[str] = "held_suarez"       # same slot as Held-Suarez: one relaxation term per run
    category: ClassVar[str] = "held_suarez"

    def __init__(
        self,
        gamma_k_per_km: float = 4.0,
        p_tropopause_hpa: float = 100.0,
        phi0_deg: float = 50.0,
        delta_phi_deg: float = 10.0,
        epsilon_k: float = 10.0,
        t_peak_year_fraction: float = 0.04,   # ~15 January: NH vortex at full strength
        season_offset: float = 0.0,           # 0: half-year cosine; 0.5: equinox-to-equinox plateau
        tau_strat_days: float = 40.0,
        **held_suarez_kwargs,
    ) -> None:
        super().__init__(**held_suarez_kwargs)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._k_per_nondim = float(specs.nondimensionalize(1.0 * units.degK))   # K -> model T units
        self.gamma = float(gamma_k_per_km) * 1e-3                                # K/m
        self.p_t_pa = float(p_tropopause_hpa) * 100.0
        self.phi0 = float(jnp.deg2rad(phi0_deg))
        self.delta_phi = float(jnp.deg2rad(delta_phi_deg))
        self.epsilon = float(epsilon_k) * self._k_per_nondim
        self.t_peak = float(t_peak_year_fraction)
        self.season_offset = float(season_offset)
        self.k_strat = nnx.Variable(jnp.asarray(specs.nondimensionalize(1.0 / (float(tau_strat_days) * units.day))))

    # --- equilibrium -------------------------------------------------------------------
    def _season(self, tyear):
        s = jnp.cos(2.0 * jnp.pi * (tyear - self.t_peak))
        c = self.season_offset
        a_n = jnp.clip((s + c) / (1.0 + c), 0.0, 1.0)
        a_s = jnp.clip((-s + c) / (1.0 + c), 0.0, 1.0)
        return a_n, a_s, s                                        # A_N, A_S, s

    def _equilibrium_temperature(self, normalized_surface_pressure, tyear=0.0):
        sigma = self._sigma.get_value()[:, jnp.newaxis]           # (nlev, 1)
        lat = self._lat.get_value()                               # (ncols,)
        p_over_p0 = sigma * normalized_surface_pressure           # (nlev, ncols)
        p_pa = p_over_p0 * P0_PA
        a_n, a_s, s = self._season(tyear)

        t_us = standard_atmosphere_temperature(p_pa) * self._k_per_nondim
        # troposphere: Held-Suarez with the winter-hemisphere asymmetry, floored by T_US (PK02 A1)
        t_trop = p_over_p0 ** self._kappa * (
            self.maxT.get_value()
            - self.dTy.get_value() * jnp.sin(lat) ** 2
            - self.epsilon * s * jnp.sin(lat)
            - self.dThz.get_value() * jnp.log(p_over_p0) * jnp.cos(lat) ** 2
        )
        t_trop = jnp.maximum(t_us, t_trop)
        # stratosphere: polar-vortex cooling in the winter cap (PK02 A2-A3), seasonal weights
        t_pv = standard_atmosphere_temperature(jnp.asarray(self.p_t_pa)) * self._k_per_nondim \
            * (p_pa / self.p_t_pa) ** (R_DRY * self.gamma / GRAVITY)
        w_n = 0.5 * (1.0 + jnp.tanh((lat - self.phi0) / self.delta_phi))
        w_s = 0.5 * (1.0 - jnp.tanh((lat + self.phi0) / self.delta_phi))
        w = a_n * w_n + a_s * w_s                                 # (ncols,), in [0, 1]
        t_strat = (1.0 - w) * t_us + w * t_pv
        return jnp.where(p_pa < self.p_t_pa, t_strat, t_trop)

    def _kt(self):
        kt = super()._kt()                                        # (nlev, ncols) or (nlev, 1)
        p_ref = self._sigma.get_value()[:, jnp.newaxis] * P0_PA
        return jnp.where(p_ref < self.p_t_pa, self.k_strat.get_value(), kt)

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain) -> tuple[PhysicsTendency, dict]:
        # Held-Suarez's __call__ with the fraction of year threaded into the equilibrium
        # (kept as an argument, not stored on the module, so nothing traced leaks out of jit).
        solar = getattr(forcing, "solar", None)
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        teq = self._equilibrium_temperature(state.normalized_surface_pressure, tyear)
        zeros = jnp.zeros_like(state.temperature)
        tendencies = PhysicsTendency(
            u_wind=-self._kv() * state.u_wind,
            v_wind=-self._kv() * state.v_wind,
            temperature=-self._kt() * (state.temperature - teq),
            specific_humidity=zeros,
        )
        return tendencies, diagnostics
