"""Polvani-Kushner equilibrium: standard atmosphere, winter-cap cooling, seasonal swap."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np

from jcm_strat.polvani_kushner import (PolvaniKushnerColumns, standard_atmosphere_temperature,
                                       P0_PA, R_DRY, GRAVITY)


def test_standard_atmosphere_anchor_points():
    p = jnp.array([101325.0, 22632.1, 5474.89, 868.019, 110.906, 1000.0])
    t = np.asarray(standard_atmosphere_temperature(p))
    assert abs(t[0] - 288.15) < 1e-6 and abs(t[1] - 216.65) < 1e-3
    assert abs(t[2] - 216.65) < 1e-3 and abs(t[3] - 228.65) < 1e-2 and abs(t[4] - 270.65) < 1e-2
    # 10 hPa is at ~31 km, in the +1 K/km layer: 216.65 + 11.1 ~ 227.7 K
    assert 226.0 < t[5] < 230.0, t[5]


class _Fake(PolvaniKushnerColumns):
    """Bypass coords: hand-set sigma levels and latitudes."""

    def __init__(self, lats_deg, sigmas, **kw):
        super().__init__(**kw)
        from flax import nnx
        self._sigma = nnx.Variable(jnp.asarray(sigmas))
        self._lat = nnx.Variable(jnp.deg2rad(jnp.asarray(lats_deg)))
        self._coords_cached = True


def _teq_kelvin(term, tyear, ps=1.0):
    ncols = term._lat.get_value().shape[0]
    return np.asarray(term._equilibrium_temperature(jnp.full((ncols,), ps), tyear)) / term._k_per_nondim


def test_winter_pole_is_cold_and_summer_pole_is_standard():
    lats = [-80.0, 0.0, 80.0]
    sig = [10.0 / 1013.25]                       # one level at 10 hPa
    term = _Fake(lats, sig, gamma_k_per_km=4.0)
    t = _teq_kelvin(term, 0.04)[0]               # mid-January: NH winter
    t_us = float(standard_atmosphere_temperature(jnp.asarray(1000.0)))
    # NH pole: T_PV = T_US(100 hPa) * (10/100)^(R*gamma/g) ~ 216.65 * 0.1^0.117 ~ 165 K
    expect = 216.65 * (0.1) ** (R_DRY * 4e-3 / GRAVITY)
    assert abs(t[2] - expect) < 3.0, (t[2], expect)
    assert abs(t[1] - t_us) < 1.0 and abs(t[0] - t_us) < 1.0, t
    # mid-July: hemispheres swap
    t2 = _teq_kelvin(term, 0.54)[0]
    assert abs(t2[0] - expect) < 3.0 and abs(t2[2] - t_us) < 1.0, t2


def test_gamma_zero_gives_isothermal_winter_cap_and_standard_summer():
    term = _Fake([-85.0, 85.0], [5.0 / 1013.25], gamma_k_per_km=0.0)
    t = _teq_kelvin(term, 0.04)[0]               # NH winter
    t_us = float(standard_atmosphere_temperature(jnp.asarray(500.0)))
    assert abs(t[1] - 216.65) < 0.5 and abs(t[0] - t_us) < 0.5, (t, t_us)


def test_troposphere_matches_held_suarez_where_warm():
    from jcm_strat.held_suarez_columns import HeldSuarezColumns
    from flax import nnx
    lats = [-30.0, 0.0, 30.0]
    sig = [0.9, 0.5]
    pk = _Fake(lats, sig, epsilon_k=0.0)
    hs = HeldSuarezColumns()
    hs._sigma = nnx.Variable(jnp.asarray(sig)); hs._lat = nnx.Variable(jnp.deg2rad(jnp.asarray(lats)))
    ps = jnp.ones((3,))
    a = np.asarray(pk._equilibrium_temperature(ps, 0.0)); b = np.asarray(hs._equilibrium_temperature(ps))
    t_us = np.asarray(standard_atmosphere_temperature(jnp.asarray(sig)[:, None] * P0_PA)) * pk._k_per_nondim
    warm = b > t_us                                  # where Held-Suarez sits above the T_US floor
    assert warm.any() and np.allclose(a[warm], b[warm], rtol=1e-6), (a, b)
    assert np.all(a >= b - 1e-6)                     # PK02's floor is T_US, never colder than HS


def test_season_offset_widens_the_winter():
    lats = [85.0]; sig = [10.0 / 1013.25]
    narrow = _Fake(lats, sig, gamma_k_per_km=4.0, season_offset=0.0)
    wide = _Fake(lats, sig, gamma_k_per_km=4.0, season_offset=0.5)
    t_us = float(standard_atmosphere_temperature(jnp.asarray(1000.0)))
    # mid-October (tyear 0.79): the narrow cosine has barely started cooling, the wide one has
    assert abs(_teq_kelvin(narrow, 0.79)[0, 0] - t_us) < 4.0
    assert _teq_kelvin(wide, 0.79)[0, 0] < t_us - 15.0
    # mid-January both are at full strength and identical
    assert abs(_teq_kelvin(wide, 0.04)[0, 0] - _teq_kelvin(narrow, 0.04)[0, 0]) < 0.5
    # mid-July neither cools the north
    assert abs(_teq_kelvin(wide, 0.54)[0, 0] - t_us) < 0.5
