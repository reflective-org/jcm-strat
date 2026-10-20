"""Phase 23 latitude-dependent nudging top: weights, and the term = JCM's NudgingTerm x weight (CPU, small HS grid)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

from types import SimpleNamespace

import jax.numpy as jnp
import numpy as np
import pytest

import jcm.nudging as jn
from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.held_suarez.utils import get_held_suarez_coords

from jcm_strat import nudging_lat
from jcm_strat.nudging_lat import LatTopNudgingTerm, top_hpa, weights

KW = dict(p_trop_hpa=150.0, p_pole_hpa=400.0, lat_full_deg=20.0, lat_zero_deg=35.0, taper_decades=0.1)


def test_top_and_weights():
    assert top_hpa(0.0, 150, 400, 20, 35) == pytest.approx(150.0)
    assert top_hpa(-20.0, 150, 400, 20, 35) == pytest.approx(150.0)
    assert top_hpa(35.0, 150, 400, 20, 35) == pytest.approx(400.0)
    assert top_hpa(-80.0, 150, 400, 20, 35) == pytest.approx(400.0)
    mid = top_hpa(27.5, 150, 400, 20, 35)
    assert mid == pytest.approx(np.sqrt(150.0 * 400.0))           # half way in log p
    p = np.geomspace(1.0, 1000.0, 400)
    lat = np.linspace(-90, 90, 73)
    w = weights(p, lat, **KW)
    top = top_hpa(lat, 150, 400, 20, 35)
    assert np.all(w[p[:, None] < top[None, :]] == 0.0)              # nothing above the top, anywhere
    assert np.all(w[p[:, None] > top[None, :] * 10 ** 0.1 * 1.0001] == 1.0)
    assert np.all(np.diff(w, axis=0) >= 0)                          # monotone downwards
    hard = weights(p, lat, **{**KW, "taper_decades": 0.0})
    assert set(np.unique(hard)) <= {0.0, 1.0}


def _state_and_term(lat_top):
    coords = get_held_suarez_coords()
    nlev = coords.vertical.centers.size
    cfg = jn.NudgingConfig(inv_tau_wind=jnp.full(nlev, 1 / 21600.0), inv_tau_temperature=jnp.full(nlev, 1 / 21600.0))
    terms = {"base": jn.NudgingTerm(cfg), "lat": LatTopNudgingTerm(cfg, **lat_top)}
    model = Model(coords=coords, time_step=10, physics=ComposablePhysics(terms=[terms["lat"]], checkpoint_terms=False))
    state = model.dycore.to_physics_state(model._prepare_initial_dycore_state())   # (nlev, nlon, nlat)
    for t in terms.values():
        t.cache_coords(coords)
    target = jn.NudgingTarget(u_wind=state.u_wind + 10.0, v_wind=state.v_wind - 5.0, temperature=state.temperature + 3.0)
    return coords, state, terms, SimpleNamespace(nudging_target=target)


def test_term_is_base_times_weight():
    # the T31L8 sigma grid has 8 levels; put the tops where several of them fall either side
    lat_top = {**KW, "p_trop_hpa": 300.0, "p_pole_hpa": 600.0}
    coords, state, terms, forcing = _state_and_term(lat_top)
    base, _ = terms["base"](state, {}, forcing, None)
    out, _ = terms["lat"](state, {}, forcing, None)
    p = np.asarray(coords.vertical.centers) * 1013.25
    lat = np.rad2deg(np.asarray(coords.horizontal.latitudes))
    w = weights(p, lat, **lat_top)                                  # (nlev, nlat)
    for name in ("u_wind", "v_wind", "temperature"):
        b = np.asarray(getattr(base, name)); o = np.asarray(getattr(out, name))
        np.testing.assert_allclose(o, b * w[:, None, :], rtol=1e-5, atol=1e-12)
    o = np.asarray(out.u_wind)
    assert np.any(o != 0.0) and np.any(w == 0.0) and np.all(o[w[:, None, :].repeat(o.shape[1], 1) == 0.0] == 0.0)


def test_install_swaps_with_nudging(monkeypatch):
    monkeypatch.setattr(jn, "with_nudging", jn.with_nudging)          # restored after the test
    nudging_lat.install_lat_top(None)
    assert jn.with_nudging is not None and jn.with_nudging.__module__ == "jcm.nudging"
    nudging_lat.install_lat_top(KW)
    cfg = jn.NudgingConfig(inv_tau_wind=jnp.ones(8), inv_tau_temperature=jnp.ones(8))
    physics = jn.with_nudging(ComposablePhysics(terms=[], checkpoint_terms=False), cfg)
    assert isinstance(physics.terms[-1], LatTopNudgingTerm)
