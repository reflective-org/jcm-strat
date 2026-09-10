"""ProductionTracers (Phase 10): tendencies by region and date, and a short run with 6-hourly snapshots."""
import os
import types

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import jax_datetime as jdt
import numpy as np

from jcm.forcing import SolarGeometry
from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.diagnostics.omega import OmegaDiagnostic
from jcm.physics.held_suarez.utils import get_held_suarez_coords

from jcm_strat.advection_tracers import DAY, DEFAULT_PULSES, STEADY, ProductionTracers
from jcm_strat.held_suarez_columns import HeldSuarezColumns

DT = 600.0


def _model(**kw):
    coords = get_held_suarez_coords()
    physics = ComposablePhysics(terms=[HeldSuarezColumns(), ProductionTracers(**kw), OmegaDiagnostic()],
                                checkpoint_terms=False, vectorize_columns=True)
    # as the production chain: a 1 January start on the Gregorian calendar, so the fraction of year
    # is exactly 0 at the first step (JCM's 365_day default would put 2005-01-01 at day 9)
    return Model(coords=coords, time_step=DT / 60, physics=physics,
                 start_date=jdt.to_datetime("2005-01-01"), calendar="gregorian")


def _state_and_term(model):
    state = model.dycore.to_physics_state(model._prepare_initial_dycore_state())
    term = [t for t in model.physics.terms if isinstance(t, ProductionTracers)][0]
    nlev, nlon, nlat = state.temperature.shape
    cols = state.replace(**{f: getattr(state, f).reshape(nlev, -1) for f in
                            ("u_wind", "v_wind", "temperature", "specific_humidity")},
                         normalized_surface_pressure=state.normalized_surface_pressure.reshape(-1),
                         tracers={k: v.reshape(nlev, -1) for k, v in state.tracers.items()})
    return cols, term


def _forcing(tyear):
    t = jnp.asarray(tyear, jnp.float32)
    return types.SimpleNamespace(solar=SolarGeometry(tyear=t, orbital_phase=2 * jnp.pi * t, synodic_phase=jnp.asarray(0.0)))


def _tend(term, state, forcing):
    tend, _ = term(state, {"_dt_seconds": DT}, forcing, None)
    return {k: np.asarray(v) / term._per_s for k, v in tend.tracers.items()}      # per second


def test_declared_tracers_and_targets():
    model = _model()
    state, term = _state_and_term(model)
    names = set(state.tracers)
    assert {"aoa", "aoa150", "aoa_sfc", "sai", "n2o", "cfc11"} <= names
    assert {f"pulse_{i + 1}" for i in range(len(DEFAULT_PULSES))} <= names
    assert not ({"unity", "e90"} & names)
    targets = np.asarray(term._targets.get_value())
    for i, (_, _, _, amp) in enumerate(DEFAULT_PULSES):
        assert 0.0 <= targets[i].min() and targets[i].max() <= amp * 1.0001
        if i == 0: assert targets[i].max() > 0.3 * amp              # the 30 hPa blob is resolved on T31L8; the higher ones are above its top
    q0 = np.asarray(term._q0.get_value()); k = np.asarray(term._k.get_value())
    assert q0.min() >= 0 and q0.max() <= 1.2 and k.min() >= 0
    p = np.asarray(term._pressure(state.normalized_surface_pressure))
    assert np.all(q0[:, p > 700e2] > 0.9)                        # WACCM: ~1 in the troposphere
    assert q0[0][p < 50e2].mean() < q0[0][p > 700e2].mean()      # and depleted in the stratosphere (T31L8 top ~25 hPa)


def test_tendencies_by_region_and_date():
    model = _model(first_segment=True)
    state, term = _state_and_term(model)
    p = np.asarray(term._pressure(state.normalized_surface_pressure))
    sfc = np.asarray(term._sfc_mask.get_value())[:, None] & np.ones_like(p, bool)
    # 1 January 00:00 of the first segment: injection of every pulse and the WACCM initial state
    d = _tend(term, state, _forcing(0.0))
    targets = np.asarray(term._targets.get_value()); q0 = np.asarray(term._q0.get_value())
    for i in range(len(DEFAULT_PULSES)):
        assert np.allclose(d[f"pulse_{i + 1}"] * DT, targets[i], atol=1e-6)
    for i, sp in enumerate(STEADY):
        assert np.allclose(d[sp] * DT, q0[i] - 1.0, atol=1e-6)
    # mid-February: no injection; pulses only absorbed at the surface, steady tracers source/sink
    d = _tend(term, state, _forcing(45.0 / 365.0))
    for i in range(len(DEFAULT_PULSES)):
        assert np.all(d[f"pulse_{i + 1}"][~sfc] == 0.0)          # pure advection between injections
    state2 = state.replace(tracers={**state.tracers, "pulse_1": jnp.ones_like(state.temperature)})
    d2 = _tend(term, state2, _forcing(45.0 / 365.0))
    assert np.allclose(d2["pulse_1"][sfc] * DT, -1.0) and np.all(d2["pulse_1"][~sfc] == 0.0)
    for sp in STEADY:                                            # q = 1 everywhere initially
        assert np.all(d[sp][p > 700e2] == 0.0) and np.all(d[sp][p <= 700e2] <= 0.0)
        assert d[sp][p < 50e2].min() < 0.0                       # loss active in the stratosphere
    # the quarterly injection date (day 91.25) fires once: the step containing it
    x_fire = 91.25 / 365.0 + 0.5 * DT / DAY / 365.0
    assert np.allclose(_tend(term, state, _forcing(x_fire))["pulse_1"] * DT, targets[0], atol=1e-6)
    assert np.all(_tend(term, state, _forcing(x_fire + 2 * DT / DAY / 365.0))["pulse_1"][~sfc] == 0.0)
    # clocks
    assert np.allclose(d["aoa"][p <= 700e2], 1.0 / DAY) and np.all(d["aoa"][p > 700e2] <= 0.0)
    assert np.allclose(d["aoa150"][p <= 150e2], 1.0 / DAY) and np.all(d["aoa150"][p > 150e2] <= 0.0)
    assert np.allclose(d["aoa_sfc"][~sfc], 1.0 / DAY) and np.all(d["aoa_sfc"][sfc] <= 0.0)
    assert d["sai"].max() > 0 and d["sai"].min() == 0.0
    # without first_segment the steady tracers are not overwritten on 1 January
    state_b, term_b = _state_and_term(_model(first_segment=False))
    d_b = _tend(term_b, state_b, _forcing(0.0))
    assert np.all(d_b["n2o"][p > 700e2] == 0.0)


def test_short_run_six_hourly_snapshots():
    model = _model(first_segment=True)
    ds = model.run(total_time=1, save_interval=0.25, output_averages=False).to_xarray()
    assert ds.sizes["time"] == 4
    for k in ("aoa", "aoa150", "aoa_sfc", "sai", "n2o", "cfc11", "pulse_1", "omega", "u_wind"):
        assert k in ds and not bool(np.any(np.isnan(ds[k].values))), k
    assert "unity" not in ds and "e90" not in ds
    assert ds["omega"].shape == ds["temperature"].shape and float(np.abs(ds["omega"].values).max()) > 0
    assert ds["aoa"].values.min() >= -1e-6 and ds["aoa"].values.max() > 0.5
    assert ds["pulse_1"].values.max() > 0.5 and ds["pulse_1"].values.min() >= -1e-6
    # the global mass fixer rescales the whole field by one factor per step; on T31L8 with the sharp
    # WACCM gradient that is ~0.5 percent (unity saw 2.6e-4 at T63 in Phases 4-8)
    assert ds["n2o"].values.max() <= 1.02 and ds["n2o"].values.min() >= 0.0
    a, a150, asf = (ds[k].isel(time=-1).values for k in ("aoa", "aoa150", "aoa_sfc"))
    assert (a150 <= a + 1e-3).mean() > 0.99 and (a <= asf + 1e-3).mean() > 0.99
