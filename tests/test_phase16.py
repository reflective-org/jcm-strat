"""Phase 16: the tropospheric tracer mixing term, its physics groups and the two base experiments (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np
import pytest

import jcm_strat.tracer_mixing as tm
from jcm_strat.prefetch_era5 import compose_run_config
from jcm_strat.tracer_mixing import TropoTracerMixing, mixing_profile


def _term(p_hpa, lats_deg, **kw):
    class V:
        centers = np.asarray(p_hpa, float) / 1013.25
    class H:
        pass
    lat = np.deg2rad(np.asarray(lats_deg, float))
    tm.column_lat_lon = lambda h: (jnp.asarray(lat), jnp.zeros_like(jnp.asarray(lat)))
    coords = type("C", (), {"vertical": V(), "horizontal": H()})()
    t = TropoTracerMixing(**kw); t.cache_coords(coords)
    return t


def test_profile_is_zero_above_p_top_and_one_below_p_full():
    assert np.allclose(mixing_profile([50, 100, 150, 200, 500], 100, 200), [0, 0, 0.5, 1, 1])


def test_tendency_conserves_column_mass_and_vanishes_in_the_stratosphere():
    p = np.array([10.0, 50.0, 100.0, 150.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0])
    t = _term(p, [0.0, 45.0], k_m2_s=20.0)
    k = np.asarray(t._k.get_value()); assert np.all(k[:3] == 0) and np.all(k[4:] == 20.0) and 0 < k[3, 0] < 20
    state = type("S", (), {})()
    state.normalized_surface_pressure = jnp.ones((2,)); state.temperature = jnp.full((p.size, 2), 250.0 * t._k_per_nondim)
    state.specific_humidity = jnp.zeros((p.size, 2))
    c = np.tile(np.linspace(0.0, 1000.0, p.size)[:, None], (1, 2))          # a clock increasing downward, days
    state.tracers = {"aoa_sfc": jnp.asarray(c)}
    tend, _ = t(state, {}, None, None)
    dcdt = np.asarray(tend.tracers["aoa_sfc"]) / t._per_s                     # 1/s
    assert np.allclose(dcdt[:2], 0.0)                                          # nothing above 100 hPa
    assert np.any(dcdt[4:] != 0)
    # column mass (dp-weighted) conserved: sum_k dcdt_k * dp_k = 0 with the same half-level thicknesses the term uses
    p_pa = p * 100.0; dp = np.diff(p_pa); p_half = np.concatenate([[p_pa[0] - 0.5 * dp[0]], 0.5 * (p_pa[1:] + p_pa[:-1]), [p_pa[-1] + 0.5 * dp[-1]]])
    thick = np.diff(p_half)
    assert abs(np.sum(dcdt[:, 0] * thick)) < 1e-5 * np.sum(np.abs(dcdt[:, 0]) * thick)     # float32
    # a well-mixed column has no tendency; a gradient is reduced (downgradient): young air moves down, old air moves up
    state.tracers = {"x": jnp.ones((p.size, 2))}
    assert np.allclose(np.asarray(t(state, {}, None, None)[0].tracers["x"]), 0.0)
    assert dcdt[-1, 0] < 0 and dcdt[5, 0] > 0
    assert np.allclose(np.asarray(tend.u_wind), 0.0) and np.allclose(np.asarray(tend.temperature), 0.0)


def test_implicit_step_is_stable_conservative_and_matches_explicit_for_small_dt():
    p = np.array([10.0, 50.0, 100.0, 150.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 950.0, 980.0, 1000.0])
    t = _term(p, [0.0], k_m2_s=30.0)
    state = type("S", (), {})()
    state.normalized_surface_pressure = jnp.ones((1,)); state.temperature = jnp.full((p.size, 1), 250.0 * t._k_per_nondim)
    state.specific_humidity = jnp.zeros((p.size, 1)); c = np.linspace(0.0, 1000.0, p.size)[:, None]; state.tracers = {"aoa_sfc": jnp.asarray(c)}
    p_pa = p * 100.0; dp = np.diff(p_pa); thick = np.diff(np.concatenate([[p_pa[0] - 0.5 * dp[0]], 0.5 * (p_pa[1:] + p_pa[:-1]), [p_pa[-1] + 0.5 * dp[-1]]]))
    ex = np.asarray(t(state, {}, None, None)[0].tracers["aoa_sfc"]) / t._per_s
    im_small = np.asarray(t(state, {"_dt_seconds": 1.0}, None, None)[0].tracers["aoa_sfc"]) / t._per_s
    # dt -> 0: implicit = explicit (float32: (C_new - C)/dt with C ~ 1000 leaves ~1e-3 of the largest tendency as roundoff)
    assert np.allclose(im_small, ex, rtol=2e-2, atol=3e-3 * np.abs(ex).max())
    dt = 720.0
    im = np.asarray(t(state, {"_dt_seconds": dt}, None, None)[0].tracers["aoa_sfc"]) / t._per_s
    c_new = c[:, 0] + dt * im[:, 0]
    assert np.all(np.isfinite(c_new)) and c_new.min() >= c.min() - 1e-3 and c_new.max() <= c.max() + 1e-3   # monotone: no over/undershoot
    assert abs(np.sum(im[:, 0] * thick)) < 1e-5 * np.sum(np.abs(im[:, 0]) * thick)      # mass conserved
    # explicit would be unstable here (thin 20 hPa layers ~170 m, |K dt / dz^2| > 1); the implicit step reduces the bottom
    # value and stays bounded (a local gradient CAN steepen where the diffusivity ramps, so only the ends are checked)
    assert c_new[-1] < c[-1, 0] and c_new[4] > c[4, 0]


def test_all_tracers_solved_at_once_equal_one_by_one():
    p = np.array([10.0, 100.0, 200.0, 400.0, 600.0, 800.0, 1000.0])
    t = _term(p, [0.0, 30.0], k_m2_s=20.0)
    state = type("S", (), {})()
    state.normalized_surface_pressure = jnp.ones((2,)); state.temperature = jnp.full((p.size, 2), 250.0 * t._k_per_nondim)
    state.specific_humidity = jnp.zeros((p.size, 2))
    rng = np.random.default_rng(1)
    state.tracers = {n: jnp.asarray(rng.uniform(0, 1000, (p.size, 2))) for n in ("aoa", "n2o", "sai", "pulse_1")}
    tend = t(state, {"_dt_seconds": 720.0}, None, None)[0].tracers
    p_pa = np.asarray(t._sigma.get_value()) * 101325.0 * np.ones((1, 2)); t_k = np.full((p.size, 2), 250.0); k = np.asarray(t._k.get_value())
    for n, c in state.tracers.items():
        one = np.asarray(t.implicit_tendency_per_second(c, jnp.asarray(p_pa), jnp.asarray(t_k), jnp.asarray(k), 720.0)) * t._per_s
        assert np.allclose(np.asarray(tend[n]), one, rtol=1e-5, atol=1e-6 * np.abs(one).max()), n


def test_tropical_confinement_and_validation():
    p = np.array([100.0, 300.0, 500.0, 900.0])
    t = _term(p, [0.0, 20.0, 40.0, 60.0], k_m2_s=10.0, lat_max_deg=40.0)
    k = np.asarray(t._k.get_value())[-1]
    assert k[0] == pytest.approx(10.0) and 0 < k[1] < 10 and k[2] == pytest.approx(0.0, abs=1e-9) and k[3] == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(ValueError):
        TropoTracerMixing(k_m2_s=-1.0)
    with pytest.raises(ValueError):
        TropoTracerMixing(p_top_hpa=300.0, p_full_hpa=200.0)


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p15_base", "p16_base", "p16_n100", "p16_base_mix", "p16_n100_mix")}


def test_p16_base_is_the_phase15_winner(cfgs):
    b, p15 = cfgs["p16_base"], cfgs["p15_base"]
    assert list(b.physics.terms) == ["held_suarez", "rayleigh_drag", "production_tracers", "omega_diagnostic"]
    assert b.physics.terms.rayleigh_drag.tau_days == 30.0 and b.physics.terms.rayleigh_drag.p_bot_hpa == 30.0 and b.physics.terms.rayleigh_drag.p_top_hpa == 1.0
    assert b.nudging.min_pressure_hpa == 100.0 and p15.nudging.min_pressure_hpa == 150.0
    assert {k: v for k, v in b.nudging.items() if k != "min_pressure_hpa"} == {k: v for k, v in p15.nudging.items() if k != "min_pressure_hpa"}
    for k in ("held_suarez", "production_tracers", "omega_diagnostic"):
        assert b.physics.terms[k] == p15.physics.terms[k]
    assert b.run == p15.run and list(b.output_keep) == list(p15.output_keep) and b.grid == p15.grid
    n = cfgs["p16_n100"]
    assert list(n.physics.terms) == ["held_suarez", "production_tracers", "omega_diagnostic"] and n.nudging.min_pressure_hpa == 100.0


def test_mixing_groups_add_exactly_the_mixing_term(cfgs):
    for base, mix in (("p16_base", "p16_base_mix"), ("p16_n100", "p16_n100_mix")):
        b, m = cfgs[base], cfgs[mix]
        assert [k for k in m.physics.terms if k != "tropo_tracer_mixing"] == list(b.physics.terms)
        for k in b.physics.terms:
            assert m.physics.terms[k] == b.physics.terms[k], (mix, k)
        t = m.physics.terms.tropo_tracer_mixing
        assert t._target_ == "jcm_strat.tracer_mixing.TropoTracerMixing" and t.k_m2_s == 10.0 and t.p_top_hpa == 100.0 and t.p_full_hpa == 200.0 and t.lat_max_deg is None
        assert m.nudging == b.nudging and m.run == b.run


def test_mixing_list_instantiates_in_order(cfgs):
    import hydra
    from jcm.physics.composable_physics import ComposablePhysics
    from jcm_strat import levels
    levels.install("strat")
    terms = [hydra.utils.instantiate(v) for v in cfgs["p16_base_mix"].physics.terms.values()]
    assert [t.name for t in ComposablePhysics(terms).terms] == ["held_suarez", "rayleigh_drag", "tropo_tracer_mixing", "production_tracers", "omega_diagnostic"]
