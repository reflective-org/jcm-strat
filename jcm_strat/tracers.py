"""Passive tracers for the stripped stratosphere model (Phase 3).

One PhysicsTerm that declares four tracers and their sources/sinks. Transport is the
dycore's job (semi-Lagrangian, nodal tracers, global mass fixer); this term only adds the
local tendencies. It runs on jcm's column-vectorized path (``vectorize_columns: true``,
fields are ``(nlev, ncols)``), with pressure from the hybrid coordinate and one latitude per
column — the 3-D path cannot accumulate tracer tendencies (see ``held_suarez_columns.py``).

Units. All four tracers use ``nondimensionalize=False``: the state bridge passes their
values through untouched in both directions, so what the physics sees, what the dycore
carries and what lands in the netCDF are the same numbers. The price is that the dycore
integrates tendencies over its *nondimensional* time step, so every per-second tendency
here is multiplied by ``_per_s`` — the same conversion ``HeldSuarez`` applies to its
relaxation rates via ``physics_specs_from_constants``.

Tracers:

``aoa``    age of air in days. Tendency +1 day/day everywhere; relaxed to zero on one time
           step wherever p > 700 hPa (the whole troposphere is the clock's source region,
           KEY_DECISIONS #10). Mean age in the stratosphere is the primary transport metric.
``unity``  starts at 1 everywhere, no tendency. Any departure from 1 is transport error the
           global mass fixer does not remove locally.
``sai``    continuous source of 1e-6 per second in the box 15S-15N, 25-55 hPa (~20-25 km),
           no sink: an idealised stratospheric injection. Its global burden must grow
           linearly at the known source rate — a conservation check with a known answer.
``e90``    Prather et al. (2011) tropopause marker: held at 100 in the lowest two model
           layers, 90-day e-folding sink everywhere. The 90 contour marks the tropopause.
"""
from __future__ import annotations

from typing import ClassVar

import jax.numpy as jnp
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics.coords_util import column_lat_lon
from jcm.physics.physics_term import PhysicsTerm, TracerSpec
from jcm.physics_interface import PhysicsState, PhysicsTendency

P0_PA = 101325.0
DAY = 86400.0


class PassiveTracers(PhysicsTerm):
    name: ClassVar[str] = "passive_tracers"
    category: ClassVar[str] = "tracers"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()
    output_attrs: ClassVar = {
        "aoa": {"units": "day", "long_name": "age of air (clock tracer, reset below 700 hPa)"},
        "unity": {"units": "1", "long_name": "uniform tracer, initial value 1, no sources"},
        "sai": {"units": "1", "long_name": "idealised stratospheric injection tracer"},
        "e90": {"units": "1", "long_name": "e90 tropopause tracer (surface = 100, 90-day sink)"},
    }

    def __init__(
        self,
        aoa_reset_pressure_hpa: float = 700.0,
        sai_source_per_s: float = 1e-6,
        sai_lat_deg: float = 15.0,
        sai_p_top_hpa: float = 25.0,
        sai_p_bot_hpa: float = 55.0,
        e90_surface_value: float = 100.0,
        e90_surface_layers: int = 2,
        e90_lifetime_days: float = 90.0,
    ) -> None:
        self.aoa_reset_pressure_pa = float(aoa_reset_pressure_hpa) * 100.0
        self.sai_source_per_s = float(sai_source_per_s)
        self.sai_lat = float(jnp.deg2rad(sai_lat_deg))
        self.sai_p_top_pa = float(sai_p_top_hpa) * 100.0
        self.sai_p_bot_pa = float(sai_p_bot_hpa) * 100.0
        self.e90_surface_value = float(e90_surface_value)
        self.e90_surface_layers = int(e90_surface_layers)
        self.e90_rate = 1.0 / (float(e90_lifetime_days) * DAY)
        # per-second -> per nondimensional dycore time (read from the live constants,
        # as HeldSuarez does, so a constants override is honoured)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._per_s = float(specs.nondimensionalize(1.0 / units.second))
        self._coords_cached = False

    @classmethod
    def required_tracers(cls) -> tuple[TracerSpec, ...]:
        return (
            TracerSpec("aoa", units="day", initial_value=0.0, nondimensionalize=False),
            TracerSpec("unity", units="1", initial_value=1.0, nondimensionalize=False),
            TracerSpec("sai", units="1", initial_value=0.0, nondimensionalize=False),
            TracerSpec("e90", units="1", initial_value=0.0, nondimensionalize=False),
        )

    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        if hasattr(vertical, "centers"):          # sigma coordinate
            sigma = vertical.centers
        else:                                     # hybrid: sigma-equivalent at p_s = P0
            sigma = vertical.get_sigma_centers(P0_PA)
        sigma = jnp.asarray(sigma)
        self._sigma = nnx.Variable(sigma)
        lat, _ = column_lat_lon(coords.horizontal)
        self._lat = nnx.Variable(lat)                                    # (ncols,), radians
        # index 0 is the surface if sigma decreases upward, else the last index is
        surf_first = bool(sigma[0] > sigma[-1])
        n = sigma.shape[0]
        idx = jnp.arange(n)
        self._surface_mask = nnx.Variable(
            (idx < self.e90_surface_layers) if surf_first else (idx >= n - self.e90_surface_layers)
        )
        self._coords_cached = True

    def _pressure(self, normalized_surface_pressure):
        # (nlev, 1) * (ncols,) -> (nlev, ncols), in Pa
        return self._sigma.get_value()[:, jnp.newaxis] * normalized_surface_pressure * P0_PA

    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        dt = diagnostics["_dt_seconds"]
        p = self._pressure(state.normalized_surface_pressure)
        lat = self._lat.get_value()                      # (nlat,) broadcasts on the last axis
        zeros = jnp.zeros_like(state.temperature)

        aoa = state.tracers["aoa"]
        d_aoa = jnp.where(p > self.aoa_reset_pressure_pa, -aoa / dt, 1.0 / DAY)

        sai_box = (jnp.abs(lat) <= self.sai_lat) & (p >= self.sai_p_top_pa) & (p <= self.sai_p_bot_pa)
        d_sai = jnp.where(sai_box, self.sai_source_per_s, 0.0)

        e90 = state.tracers["e90"]
        surf = self._surface_mask.get_value()[:, jnp.newaxis]
        d_e90 = jnp.where(surf, (self.e90_surface_value - e90) / dt, -self.e90_rate * e90)

        k = self._per_s  # per-second tendencies -> per nondimensional time (see module doc)
        tendencies = PhysicsTendency(
            u_wind=zeros, v_wind=zeros, temperature=zeros, specific_humidity=zeros,
            tracers={"aoa": k * d_aoa, "unity": zeros, "sai": k * d_sai, "e90": k * d_e90},
        )
        return tendencies, diagnostics
