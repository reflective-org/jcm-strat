"""ProductionTracers (Phase 10, revised Phase 11): tendencies by region and date, the tracer lid, and a short run with 6-hourly snapshots."""
import os
import types

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import jax_datetime as jdt
import numpy as np
import pytest

from jcm.forcing import SolarGeometry
from jcm.model import Model
from jcm.physics.composable_physics import ComposablePhysics
from jcm.physics.diagnostics.omega import OmegaDiagnostic
from jcm.physics.held_suarez.utils import get_held_suarez_coords

from jcm_strat.advection_tracers import CLOCKS, DAY, DEFAULT_PULSES, DEFAULT_SOURCES, STEADY, ProductionTracers, site_of
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


PULSE_NAMES = ProductionTracers._pulse_names
SOURCE_NAMES = ProductionTracers._source_names


def test_declared_tracers_and_shapes():
    model = _model()
    state, term = _state_and_term(model)
    names = set(state.tracers)
    assert set(CLOCKS) | {"sai"} | set(STEADY) <= names
    assert set(PULSE_NAMES) <= names and set(SOURCE_NAMES) <= names
    assert len(PULSE_NAMES) == 2 * len(DEFAULT_PULSES) and len(SOURCE_NAMES) == 2 * len(DEFAULT_SOURCES)
    assert not ({"unity", "e90"} & names)
    assert site_of("pulse_3_box") == ("pulse", 2, "_box") and site_of("src_1") == ("src", 0, "")
    targets = np.asarray(term._targets.get_value()); srcs = np.asarray(term._sources.get_value())
    for arr in (targets, srcs):
        assert arr.min() >= 0.0 and arr.max() <= 1.0001                     # unit amplitude everywhere
    for i, name in enumerate(PULSE_NAMES):
        kind, j, suffix = site_of(name)
        if suffix == "_box":
            assert set(np.unique(targets[i])) <= {0.0, 1.0}                 # sharp edges: 0 or 1, nothing else
            if targets[i].max() > 0:
                assert targets[i - 1].max() > 0.3                           # its Gaussian twin is resolved at the same site
                # the box holds the cells where the Gaussian exceeds exp(-1/2) in both factors (cap radius sigma, slab +-sigma)
                assert np.all(targets[i - 1][targets[i] == 1.0] >= np.exp(-1.0) * 0.999)
    assert targets[0].max() > 0.3 and targets[1].max() == 1.0              # the 30 hPa site is resolved on T31L8; higher sites are above its top
    q0 = np.asarray(term._q0.get_value()); k = np.asarray(term._k.get_value())
    assert q0.min() >= 0 and q0.max() <= 1.2 and k.min() >= 0
    p = np.asarray(term._pressure(state.normalized_surface_pressure))
    assert np.all(q0[:, p > 700e2] > 0.9)                        # WACCM: ~1 in the troposphere
    assert q0[0][p < 50e2].mean() < q0[0][p > 700e2].mean()      # and depleted in the stratosphere (T31L8 top ~25 hPa)
    a_ref = np.asarray(term._aoa_ref.get_value())
    assert a_ref.min() >= 0 and 2.5 * 365 < a_ref[p < 50e2].mean() < 5.5 * 365   # WACCM age at the T31L8 top: a few years


def test_tendencies_by_region_and_date():
    # Phase 10 sinks on, lid off: the injection / absorption / steady-tracer logic on its own
    model = _model(first_segment=True, injection="quarterly", surface_sink=True, lid_p_hpa=None)
    state, term = _state_and_term(model)
    p = np.asarray(term._pressure(state.normalized_surface_pressure))
    sfc = np.asarray(term._sfc_mask.get_value())[:, None] & np.ones_like(p, bool)
    # 1 January 00:00 of the first segment: injection of every pulse and the WACCM initial state
    d = _tend(term, state, _forcing(0.0))
    targets = np.asarray(term._targets.get_value()); q0 = np.asarray(term._q0.get_value())
    for i, name in enumerate(PULSE_NAMES):
        assert np.allclose(d[name] * DT, targets[i], atol=1e-6)
    for i, sp in enumerate(STEADY):
        assert np.allclose(d[sp] * DT, q0[i] - 1.0, atol=1e-6)
    # mid-February: no injection; pulses only absorbed at the surface, steady tracers source/sink
    d = _tend(term, state, _forcing(45.0 / 365.0))
    for name in PULSE_NAMES:
        assert np.all(d[name][~sfc] == 0.0)                      # pure advection between injections
    state2 = state.replace(tracers={**state.tracers, "pulse_1": jnp.ones_like(state.temperature), "pulse_1_box": jnp.ones_like(state.temperature)})
    d2 = _tend(term, state2, _forcing(45.0 / 365.0))
    for name in ("pulse_1", "pulse_1_box"):
        assert np.allclose(d2[name][sfc] * DT, -1.0) and np.all(d2[name][~sfc] == 0.0)
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
    # continuous sources: emission S / 90 d everywhere but the absorbing layers, at any date
    srcs = np.asarray(term._sources.get_value())
    for i, name in enumerate(SOURCE_NAMES):
        e = d[name]
        assert np.allclose(e[~sfc], (srcs[i] / (90.0 * DAY))[~sfc]) and np.all(e[sfc] <= 0.0)
    # without first_segment the steady tracers are not overwritten on 1 January
    state_b, term_b = _state_and_term(_model(first_segment=False, injection="quarterly", surface_sink=True, lid_p_hpa=None))
    d_b = _tend(term_b, state_b, _forcing(0.0))
    assert np.all(d_b["n2o"][p > 700e2] == 0.0)


def test_no_sinks_and_lid():
    """Phase 11 defaults: no surface sink; above the lid the clocks and steady tracers relax to WACCM (A) and,
    with lid_sink_injections, the pulses, sources and sai relax to zero (B). T31L8's top layer is ~25 hPa, so the
    lid is put at 100 hPa here to have cells above it."""
    for sink_inj in (False, True):
        state, term = _state_and_term(_model(first_segment=False, lid_p_hpa=100.0, lid_sink_injections=sink_inj))
        p = np.asarray(term._pressure(state.normalized_surface_pressure))
        lid = p < 100e2; assert lid.any() and (~lid).any()
        sfc = np.asarray(term._sfc_mask.get_value())[:, None] & np.ones_like(p, bool)
        ones = jnp.ones_like(state.temperature)
        state = state.replace(tracers={**state.tracers, **{n: ones for n in PULSE_NAMES + SOURCE_NAMES + ("sai",)},
                                       **{n: 2000.0 * ones for n in CLOCKS}})
        d = _tend(term, state, _forcing(0.5))
        tau = term.lid_tau_s; a_ref = np.asarray(term._aoa_ref.get_value()); off = term.lid_clock_offset_s / DAY
        # no surface sink: pulses untouched below the lid, sources emit everywhere below the lid
        srcs = np.asarray(term._sources.get_value())
        for name in PULSE_NAMES:
            assert np.all(d[name][~lid] == 0.0)
        for i, name in enumerate(SOURCE_NAMES):
            assert np.allclose(d[name][~lid], (srcs[i] / (90.0 * DAY))[~lid])
        # above the lid
        for name in PULSE_NAMES + SOURCE_NAMES + ("sai",):
            if sink_inj:
                assert np.allclose(d[name][lid], -1.0 / tau)
            elif name.startswith("pulse"):
                assert np.all(d[name][lid] == 0.0)
        assert np.allclose(d["aoa150"][lid], (a_ref[lid] - 2000.0) / tau)
        for name in ("aoa", "aoa_sfc"):
            assert np.allclose(d[name][lid], (a_ref[lid] + off - 2000.0) / tau)
        assert np.allclose(d["aoa"][(~lid) & (p <= 700e2)], 1.0 / DAY)         # normal ageing below the lid
        q0 = np.asarray(term._q0.get_value())
        for i, sp in enumerate(STEADY):
            assert np.allclose(d[sp][lid], (q0[i][lid] - 1.0) / tau)
            assert np.all(d[sp][(~lid) & (p > 700e2)] == 0.0)
    # lid off: the clocks age everywhere above their reset region
    state, term = _state_and_term(_model(lid_p_hpa=None))
    p = np.asarray(term._pressure(state.normalized_surface_pressure))
    d = _tend(term, state, _forcing(0.5))
    assert np.allclose(d["aoa"][p <= 700e2], 1.0 / DAY)
    assert not hasattr(term, "_aoa_ref")


def test_single_injection_mode():
    """Production setting: the pulses are set once, on the first step of the first segment, never again."""
    state, term = _state_and_term(_model(first_segment=True, lid_p_hpa=None))    # injection="once" is the default
    targets = np.asarray(term._targets.get_value())
    d0 = _tend(term, state, _forcing(0.0))
    for i, name in enumerate(PULSE_NAMES):
        assert np.allclose(d0[name] * DT, targets[i], atol=1e-6)
    for x in (91.25 / 365.0 + 0.5 * DT / DAY / 365.0, 0.5, 0.999):     # quarterly dates and any other time: nothing (no surface sink)
        d = _tend(term, state, _forcing(x))
        assert np.all(d["pulse_1"] == 0.0) and np.all(d["pulse_1_box"] == 0.0)
    state_b, term_b = _state_and_term(_model(first_segment=False, lid_p_hpa=None))    # later segments: never
    assert np.all(_tend(term_b, state_b, _forcing(0.0))["pulse_1"] == 0.0)
    with pytest.raises(ValueError):
        ProductionTracers(injection="monthly")
    with pytest.raises(ValueError):
        ProductionTracers(pulses=DEFAULT_PULSES[:-1])


def test_short_run_six_hourly_snapshots():
    model = _model(first_segment=True, lid_p_hpa=100.0)
    ds = model.run(total_time=1, save_interval=0.25, output_averages=False).to_xarray()
    assert ds.sizes["time"] == 4
    for k in CLOCKS + ("sai", "n2o", "cfc11", "pulse_1", "pulse_1_box", "src_1", "src_1_box", "omega", "u_wind"):
        assert k in ds and not bool(np.any(np.isnan(ds[k].values))), k
    assert "unity" not in ds and "e90" not in ds
    assert ds["omega"].shape == ds["temperature"].shape and float(np.abs(ds["omega"].values).max()) > 0
    assert ds["aoa"].values.min() >= -1e-6 and ds["aoa"].values.max() > 0.5
    for k in ("pulse_1", "pulse_1_box"):
        assert ds[k].values.max() > 0.5 and ds[k].values.min() >= -1e-6
    assert ds["src_1"].values.max() > 0 and ds["src_1"].values.min() >= -1e-6
    # the global mass fixer rescales the whole field by one factor per step; on T31L8 with the sharp
    # WACCM gradient that is ~0.5 percent (unity saw 2.6e-4 at T63 in Phases 4-8)
    assert ds["n2o"].values.max() <= 1.02 and ds["n2o"].values.min() >= 0.0
    a, a150, asf = (ds[k].isel(time=-1).values for k in CLOCKS)
    assert (a150 <= a + 1e-3).mean() > 0.99 and (a <= asf + 1e-3).mean() > 0.99
    # the lid pulls the top layer's clock towards WACCM's age within the day (tau 1 d): well above one day of ageing
    top = ds["aoa"].isel(time=-1).values[np.argmin(np.asarray(ds.level))] if float(ds.level[0]) > float(ds.level[-1]) else ds["aoa"].isel(time=-1).values[0]
    assert top.mean() > 100.0
