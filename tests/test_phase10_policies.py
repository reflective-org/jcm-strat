"""jcm_strat.main hooks added in Phase 10 (calendar, output drop), the QBO target-year check, calendar segments."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import glob

import numpy as np
import pytest

import jcm.model as _model
import jcm.predictions as _predictions
from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.held_suarez.utils import get_held_suarez_coords

from jcm_strat import main as strat_main
from jcm_strat import segments
from jcm_strat.held_suarez_columns import HeldSuarezColumns
from jcm_strat.qbo_nudging import QboNudging

ERA5_GLOB = "/data/JCM_stripped/jcm-strat/cache/era5_ref/era5_zm_monthly_*.nc"


@pytest.fixture
def restore_patches():
    yield
    _model.Model.__init__ = strat_main._ORIG_MODEL_INIT
    _predictions.ModelPredictions.to_xarray = strat_main._ORIG_TO_XARRAY


def _model_hs():
    physics = ComposablePhysics(terms=[HeldSuarezColumns()], checkpoint_terms=False, vectorize_columns=True)
    return Model(coords=get_held_suarez_coords(), time_step=10, physics=physics)


def test_calendar_hook(restore_patches):
    assert _model_hs().calendar == "365_day"                     # JCM's default, the Phase 6-9 state
    strat_main.install_calendar("gregorian")
    assert _model_hs().calendar == "gregorian"
    with pytest.raises(ValueError):
        strat_main.install_calendar("julian")


def test_output_drop_hook(restore_patches):
    strat_main.install_output_policy(["geopotential", "not_a_variable"])
    ds = _model_hs().run(total_time=1, save_interval=1).to_xarray()
    assert "geopotential" not in ds and "temperature" in ds   # the hook itself; p10_prod writes geopotential


@pytest.mark.skipif(not glob.glob(ERA5_GLOB), reason="ERA5 zonal-mean reference not on this machine")
def test_qbo_target_year_must_exist():
    QboNudging(era5_glob=ERA5_GLOB, year=2005)                  # cached
    with pytest.raises(FileNotFoundError):
        QboNudging(era5_glob=ERA5_GLOB, year=1999)
    QboNudging(era5_glob=ERA5_GLOB, year=1999, use_calendar=False)   # tests with a frozen target still work


def test_calendar_segments():
    segs = segments.segments("calendar", [2007, 2008], 0.25)
    assert [(s.isoformat(), d) for s, d, _ in segs] == [("2007-01-01", 365), ("2008-01-01", 366)]
    with pytest.raises(ValueError):
        segments.segments("calendar", [2008], 5)                 # a 5-day interval cannot tile 366 days
    segments.check_time_step(12, 0.25)
    with pytest.raises(ValueError):
        segments.check_time_step(7, 0.25)
    assert segments.segments("year", [2008])[0][1] == 365        # the Phase 9 behaviour is unchanged
