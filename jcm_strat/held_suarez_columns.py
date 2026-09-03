"""Held-Suarez forcing for the column-vectorized physics path.

jcm's ``HeldSuarez`` works on the full ``(nlev, nlon, nlat)`` field and takes latitude from
the 1-D grid axis, so it cannot be composed with column-vectorized terms (the gravity-wave
schemes, issue #20) — and jcm's 3-D physics path cannot accumulate tracer tendencies at all
(``PhysicsTendency`` trees with different tracer dicts do not add), which Phase 3 needs.

This subclass changes only the coordinate cache: latitude becomes one value per physics
column via ``jcm.physics.coords_util.column_lat_lon`` (the same helper the radiation and
aerosol schemes use), and sigma broadcasts as ``(nlev, 1)`` against ``(nlev, ncols)``
fields. The forcing itself (Held & Suarez 1994 equilibrium temperature, Newtonian relaxation,
Rayleigh friction) is inherited unchanged. Use with ``vectorize_columns: true``.
"""
from __future__ import annotations

from typing import ClassVar

import jax.numpy as jnp
from flax import nnx

from jcm.physics.coords_util import column_lat_lon
from jcm.physics.held_suarez.held_suarez_physics import HeldSuarez


class HeldSuarezColumns(HeldSuarez):
    name: ClassVar[str] = "held_suarez"
    category: ClassVar[str] = "held_suarez"

    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(101325.0)
        self._sigma = nnx.Variable(jnp.asarray(sigma))
        lat, _ = column_lat_lon(coords.horizontal)
        self._lat = nnx.Variable(lat)                     # (ncols,), radians
        self._coords_cached = True

    def _equilibrium_temperature(self, normalized_surface_pressure):
        sigma = self._sigma.get_value()[:, jnp.newaxis]   # (nlev, 1)
        lat = self._lat.get_value()                       # (ncols,)
        p_over_p0 = sigma * normalized_surface_pressure   # (nlev, ncols)
        temperature = p_over_p0 ** self._kappa * (
            self.maxT.get_value()
            - self.dTy.get_value() * jnp.sin(lat) ** 2
            - self.dThz.get_value() * jnp.log(p_over_p0) * jnp.cos(lat) ** 2
        )
        return jnp.maximum(self.minT.get_value(), temperature)

    def _kv(self):
        sigma = self._sigma.get_value()
        kv = self.kf.get_value() * jnp.maximum(0.0, (sigma - self.sigma_b.get_value()) / (1.0 - self.sigma_b.get_value()))
        return kv[:, jnp.newaxis]

    def _kt(self):
        sigma = self._sigma.get_value()
        lat = self._lat.get_value()
        cutoff = jnp.maximum(0.0, (sigma - self.sigma_b.get_value()) / (1.0 - self.sigma_b.get_value()))
        return self.ka.get_value() + (self.ks.get_value() - self.ka.get_value()) * (
            cutoff[:, jnp.newaxis] * jnp.cos(lat) ** 4
        )
