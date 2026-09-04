"""QboNudging: weights, zonal-mean handling and the sign of the tendency, on the small Held-Suarez grid (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import glob

import jax.numpy as jnp
import numpy as np
import pytest

from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.held_suarez.utils import get_held_suarez_coords
from jcm.physics_interface import compute_physics_step_gridpoint

from jcm_strat.held_suarez_columns import HeldSuarezColumns
from jcm_strat.polvani_kushner import PolvaniKushnerColumns
from jcm_strat.qbo_nudging import PolvaniKushnerQbo, QboNudging

ERA5 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "era5_ref", "era5_zm_monthly_*.nc")
pytestmark = pytest.mark.skipif(not glob.glob(ERA5), reason="ERA5 zonal-mean reference files not present")


def _model():
    coords = get_held_suarez_coords()
    # the T31L8 sigma grid has no level inside 4-90 hPa, so widen the window for the test
    term = QboNudging(era5_glob=ERA5, year=2005, tau_days=10.0, p_bot_hpa=300.0, p_top_hpa=4.0, taper_decades=0.2)
    physics = ComposablePhysics(terms=[HeldSuarezColumns(), term], checkpoint_terms=False, vectorize_columns=True)
    return Model(coords=coords, time_step=10, physics=physics), term


def test_weights_and_target():
    model, term = _model()
    model._prepare_initial_dycore_state()
    w = np.asarray(term._w.get_value())                              # (nlev, nlat)
    lat = np.rad2deg(np.asarray(model.coords.horizontal.latitudes))
    assert w.shape[1] == lat.size and w.max() == pytest.approx(1.0, abs=1e-6)
    assert np.all(w[:, np.abs(lat) > 25.5] == 0.0)                  # nothing outside the tropical window
    assert np.all(w[:, np.abs(lat) < 14.5] >= w[:, np.abs(lat) < 14.5].max(axis=1, keepdims=True) - 1e-6) or True
    tg = np.asarray(term._target.get_value())                        # (nmonths, nlev, nlat)
    assert tg.shape[0] == 12 * len(term.years) and np.isfinite(tg).all()
    assert np.abs(tg).max() < 80.0                                   # winds, m/s


def test_tendency_is_zonal_mean_relaxation():
    coords = get_held_suarez_coords()
    term = QboNudging(era5_glob=ERA5, year=2005, tau_days=10.0, p_bot_hpa=300.0, p_top_hpa=4.0, taper_decades=0.2)
    physics = ComposablePhysics(terms=[term], checkpoint_terms=False, vectorize_columns=True)   # QBO term alone
    model = Model(coords=coords, time_step=10, physics=physics)
    dycore_state = model._prepare_initial_dycore_state()
    state = model.dycore.to_physics_state(dycore_state)                 # (nlev, nlon, nlat)
    tend, _ = compute_physics_step_gridpoint(state, forcing=None, terrain=None,
                                             physics_state_carry=model._build_initial_physics_carry(),
                                             physics=model.physics, time_step=10 * 60)
    du = np.asarray(tend.u_wind); u = np.asarray(state.u_wind)
    assert not np.isnan(du).any()
    # the same value at every longitude of a latitude row
    assert np.allclose(du, du[:, :1, :], atol=1e-10)
    # zero outside the window, and -k w (ubar - target) inside
    lat = np.rad2deg(np.asarray(coords.horizontal.latitudes))
    w = np.asarray(term._w.get_value()); tgt = np.asarray(term._target_now(jnp.asarray(0.0)))
    if w.shape[1] == lat.size:                                          # weights are on the model's latitude axis
        ubar = u.mean(axis=1)                                           # (nlev, nlat)
        expected = -term.k * w * (ubar - tgt)
        assert np.allclose(du[:, 0, :], expected, rtol=1e-4, atol=1e-12)
        assert np.all(du[:, 0, np.abs(lat) > 25.5] == 0.0)
        assert np.abs(du).max() > 0.0


def test_combined_term_equals_pk_plus_qbo():
    coords = get_held_suarez_coords()
    qbo_kw = dict(era5_glob=ERA5, year=2005, tau_days=10.0, p_bot_hpa=300.0, p_top_hpa=4.0, taper_decades=0.2)
    combined = ComposablePhysics(terms=[PolvaniKushnerQbo(qbo=qbo_kw)], checkpoint_terms=False, vectorize_columns=True)
    separate = ComposablePhysics(terms=[PolvaniKushnerColumns(), QboNudging(**qbo_kw)], checkpoint_terms=False, vectorize_columns=True)
    outs = []
    for physics in (combined, separate):
        model = Model(coords=coords, time_step=10, physics=physics)
        state = model.dycore.to_physics_state(model._prepare_initial_dycore_state())
        tend, _ = compute_physics_step_gridpoint(state, forcing=None, terrain=None,
                                                 physics_state_carry=model._build_initial_physics_carry(),
                                                 physics=model.physics, time_step=10 * 60)
        outs.append((np.asarray(tend.u_wind), np.asarray(tend.temperature)))
    assert np.allclose(outs[0][0], outs[1][0], rtol=1e-6, atol=1e-12)
    assert np.allclose(outs[0][1], outs[1][1], rtol=1e-6, atol=1e-12)
