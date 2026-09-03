"""PassiveTracers: one physics step and one short model run on the small Held-Suarez grid."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np

from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.held_suarez.utils import get_held_suarez_coords
from jcm.physics_interface import compute_physics_step_gridpoint

from jcm_strat.held_suarez_columns import HeldSuarezColumns
from jcm_strat.tracers import DAY, PassiveTracers


def _model(time_step=10):
    coords = get_held_suarez_coords()
    physics = ComposablePhysics(terms=[HeldSuarezColumns(), PassiveTracers()],
                                checkpoint_terms=False, vectorize_columns=True)
    return Model(coords=coords, time_step=time_step, physics=physics)


def test_one_step_tendencies():
    model = _model()
    dycore_state = model._prepare_initial_dycore_state()
    state = model.dycore.to_physics_state(dycore_state)
    assert set(state.tracers) >= {"aoa", "unity", "sai", "e90"}
    assert float(jnp.max(jnp.abs(state.tracers["unity"] - 1.0))) < 1e-6
    tend, _ = compute_physics_step_gridpoint(
        state, forcing=None, terrain=None,
        physics_state_carry=model._build_initial_physics_carry(),
        physics=model.physics, time_step=10 * 60)
    term = [t for t in model.physics.terms if isinstance(t, PassiveTracers)][0]
    nlev = state.temperature.shape[0]
    p = np.asarray(term._pressure(state.normalized_surface_pressure.reshape(-1))).reshape(state.temperature.shape)
    assert not bool(jnp.any(jnp.isnan(tend.temperature)))      # Held-Suarez columns variant works
    d_aoa = np.asarray(tend.tracers["aoa"])
    assert np.allclose(d_aoa[p <= 700e2], term._per_s / DAY)   # clock ticks above 700 hPa
    assert np.all(d_aoa[p > 700e2] <= 0.0)                    # reset below
    assert np.all(np.asarray(tend.tracers["unity"]) == 0.0)
    d_sai = np.asarray(tend.tracers["sai"])
    assert d_sai.max() > 0 and d_sai.min() == 0.0
    d_e90 = np.asarray(tend.tracers["e90"])
    assert d_e90.max() > 0                                     # surface source active


def test_short_run_keeps_tracers_sane():
    model = _model()
    # save_interval must not exceed total_time, or Model.run saves nothing and
    # _final_dycore_state stays at the initial condition (a vacuous test)
    ds = model.run(total_time=1, save_interval=1).to_xarray()   # one day on T31L8, one snapshot
    for k in ("aoa", "unity", "sai", "e90"):
        assert k in ds and not bool(np.any(np.isnan(ds[k].values)))
    u = ds["unity"].values                                     # raw units: stays 1 everywhere
    assert abs(u.mean() - 1.0) < 1e-2 and u.std() < 1e-2
    assert ds["aoa"].values.min() >= -1e-6
    assert ds["aoa"].values.max() > 0.5                        # the clock ticks (1 d expected)
    assert ds["sai"].values.max() > 0 and ds["e90"].values.max() > 50
