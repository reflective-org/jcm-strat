"""The clock tracer must not be rescaled by the global mass fixer (jcm_strat.main policy)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np

from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.held_suarez.utils import get_held_suarez_coords

from jcm_strat.held_suarez_columns import HeldSuarezColumns
from jcm_strat.main import install_mass_fixer_policy
from jcm_strat.tracers import PassiveTracers


def test_excluded_clock_ticks_one_day_per_day():
    install_mass_fixer_policy(enabled=True, exclude=("aoa",))
    coords = get_held_suarez_coords()
    physics = ComposablePhysics(terms=[HeldSuarezColumns(), PassiveTracers()],
                                checkpoint_terms=False, vectorize_columns=True)
    model = Model(coords=coords, time_step=10, physics=physics)
    ds = model.run(total_time=1, save_interval=1).to_xarray()   # one day on T31L8, one snapshot
    aoa = ds["aoa"].values
    # instantaneous snapshot: air that never touched p > 700 hPa has aged exactly 1 day
    assert abs(aoa.max() - 1.0) < 0.02, aoa.max()
    assert not bool(np.any(np.isnan(ds["unity"].values)))


def test_sl_departure_iterations_reaches_the_dycore():
    from jcm_strat.main import install_sl_options
    from jcm.dycore.dinosaur import dycore as dy
    install_sl_options({"departure_iterations": 2})
    coords = get_held_suarez_coords()
    physics = ComposablePhysics(terms=[HeldSuarezColumns()], checkpoint_terms=False, vectorize_columns=True)
    model = Model(coords=coords, time_step=10, physics=physics)
    assert int(model.dycore._sl_options.get("departure_iterations")) == 2
    dy.DinosaurDycore.__init__ = dy.DinosaurDycore.__init__  # leave the patched init in place; other tests do not read it
