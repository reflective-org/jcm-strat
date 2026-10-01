"""Phase 15: the sweep's base experiment, physics groups, the two new knobs of the Jucker term and the Rayleigh drag term (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np
import pytest
from flax import nnx

from jcm_strat.jucker import JuckerColumns
from jcm_strat.prefetch_era5 import compose_run_config
from jcm_strat.rayleigh import RayleighDragProfile, drag_profile

PK = dict(gamma_k_per_km=4.0, p_tropopause_hpa=100.0, p_vortex_top_hpa=3.0, tau_strat_days=15.0, season_offset=0.5)
KEEP = ["u_wind", "v_wind", "temperature", "omega", "normalized_surface_pressure", "aoa150", "aoa_sfc", "aoa500"]
GROUPS = ["strat15_jucker", "strat15_jucker_hines", "strat15_jucker_lm", "strat15_jucker_ray", "strat15_jucker_hines_ray",
          "strat15_jucker_hines_lm", "strat15_jucker_lm_ray", "strat15_jucker_hines_lm_ray"]


def _jucker(lats_deg, p_hpa, **kw):
    term = JuckerColumns(qbo=None, **PK, **kw)
    term._sigma = nnx.Variable(jnp.asarray(np.asarray(p_hpa) / 1013.25))
    term._lat = nnx.Variable(jnp.deg2rad(jnp.asarray(np.asarray(lats_deg, float))))
    term._coords_cached = True
    parent = type(term).__mro__[1]; orig = parent.cache_coords
    parent.cache_coords = lambda self, coords: None
    try:
        term.cache_coords(object())
    finally:
        parent.cache_coords = orig
    return term


def _tau_days(term, tyear=15.5 / 365):
    return 1.0 / (np.asarray(term._kt_jucker(tyear)) / term._k_per_inv_second) / 86400.0


# ----------------------------------------------------------------------------------------------- Jucker knobs
def test_tau_scale_halves_the_radiative_time_and_leaves_held_suarez_alone():
    ref = _tau_days(_jucker([0.0, 60.0], [1.0, 10.0, 50.0, 500.0]))
    half = _tau_days(_jucker([0.0, 60.0], [1.0, 10.0, 50.0, 500.0], tau_scale=0.5))
    assert np.allclose(half[:3], 0.5 * ref[:3], rtol=1e-6) and np.allclose(half[3], ref[3])


def test_tau_max_caps_only_where_jfv_is_slower():
    p = [1.0, 10.0, 100.0]
    ref = _tau_days(_jucker([0.0, 60.0], p)); capped = _tau_days(_jucker([0.0, 60.0], p, tau_max_days=15.0))
    assert np.all(ref[2] > 11.0) and np.all(capped[2] <= 15.0 + 1e-9)          # 100 hPa: 12-40 d -> <= 15 d
    assert np.allclose(capped[:2], ref[:2])                                    # 1 and 10 hPa (4-10 d) untouched


def test_knob_validation():
    with pytest.raises(ValueError):
        JuckerColumns(qbo=None, tau_scale=0.0, **PK)
    with pytest.raises(ValueError):
        JuckerColumns(qbo=None, tau_max_days=-1.0, **PK)


# ----------------------------------------------------------------------------------------------- Rayleigh drag
def test_drag_profile_is_zero_below_ramp_and_saturates_above():
    p = np.array([100.0, 30.0, 10.0, 5.477, 1.0, 0.3])
    k = drag_profile(p, 30.0, 1.0, 10.0)
    assert k[0] == 0.0 and k[1] == 0.0 and k[4] == pytest.approx(1 / (10 * 86400)) and k[5] == pytest.approx(1 / (10 * 86400))
    assert k[3] == pytest.approx(0.5 / (10 * 86400), rel=1e-3)                 # geometric mid-point of 30 and 1 hPa: half
    assert k[2] < k[3] < k[4]
    assert drag_profile(np.array([5.477]), 30.0, 1.0, 10.0, power=2.0)[0] == pytest.approx(0.25 / (10 * 86400), rel=1e-3)


def test_rayleigh_term_tendency_and_zonal_mean_option():
    class V:                    # a tiny vertical/horizontal coordinate stand-in
        centers = np.array([0.5, 10.0, 100.0]) / 1013.25
    class H:
        pass
    import jcm_strat.rayleigh as ray
    lat = np.deg2rad(np.array([0.0, 0.0, 45.0, 45.0])); lon = np.zeros(4)
    ray.column_lat_lon = lambda h: (jnp.asarray(lat), jnp.asarray(lon))
    coords = type("C", (), {"vertical": V(), "horizontal": H()})()
    term = RayleighDragProfile(p_bot_hpa=30.0, p_top_hpa=1.0, tau_days=10.0); term.cache_coords(coords)
    k = np.asarray(term._k.get_value())[:, 0] / term._per_inv_second
    assert k[0] == pytest.approx(1 / (10 * 86400)) and k[2] == 0.0 and 0 < k[1] < k[0]
    state = type("S", (), {})(); state.u_wind = jnp.asarray([[10.0, -10.0, 4.0, 8.0]] * 3); state.v_wind = jnp.zeros((3, 4))
    state.temperature = jnp.zeros((3, 4)); state.specific_humidity = jnp.zeros((3, 4))
    tend, _ = term(state, {}, None, None)
    assert np.allclose(np.asarray(tend.u_wind)[2], 0.0) and np.allclose(np.asarray(tend.u_wind)[0], -k[0] * term._per_inv_second * np.array([10.0, -10.0, 4.0, 8.0]))
    assert np.allclose(np.asarray(tend.temperature), 0.0)
    zm = RayleighDragProfile(p_bot_hpa=30.0, p_top_hpa=1.0, tau_days=10.0, zonal_mean_only=True); zm.cache_coords(coords)
    tz, _ = zm(state, {}, None, None)
    assert np.allclose(np.asarray(tz.u_wind)[0], -k[0] * term._per_inv_second * np.array([0.0, 0.0, 6.0, 6.0]))   # row means 0 and 6
    with pytest.raises(ValueError):
        RayleighDragProfile(p_bot_hpa=1.0, p_top_hpa=30.0)


# ----------------------------------------------------------------------------------------------- configs
@pytest.fixture(scope="module")
def cfgs():
    out = {"p13_jucker": compose_run_config(["+experiment=p13_jucker"]), "p15_base": compose_run_config(["+experiment=p15_base"])}
    for g in GROUPS:
        out[g] = compose_run_config(["+experiment=p15_base", f"physics={g}"])
    return out


def test_base_is_p13_jucker_with_whitelisted_output_only(cfgs):
    j, b = cfgs["p13_jucker"], cfgs["p15_base"]
    assert b.run.save_interval == 0.25 == j.run.save_interval          # 6-hourly: the TEM w* needs all four daily phases
    assert list(b.output_keep) == KEEP and list(b.output_drop) == []
    assert b.run == j.run
    for k in ("grid", "nudging", "sl_mass_fixer_exclude", "calendar", "level_table", "terrain"):
        assert b[k] == j[k], k
    hs_b = {k: v for k, v in b.physics.terms.held_suarez.items() if k not in ("tau_scale", "tau_max_days", "te_correction_file")}
    assert hs_b == dict(j.physics.terms.held_suarez) and b.physics.terms.held_suarez.tau_scale == 1.0 and b.physics.terms.held_suarez.tau_max_days is None \
        and b.physics.terms.held_suarez.te_correction_file is None          # Phase 17 knob, off by default
    assert b.physics.terms.production_tracers == j.physics.terms.production_tracers and b.physics.terms.production_tracers.lid_p_hpa == 1.0
    assert list(b.physics.terms) == ["held_suarez", "production_tracers", "omega_diagnostic"]


def test_physics_groups_differ_only_by_their_drag_terms(cfgs):
    base = cfgs["strat15_jucker"].physics.terms
    for g in GROUPS:
        t = cfgs[g].physics.terms
        drag = [k for k in t if k in ("hines_gwd", "lott_miller_sso", "rayleigh_drag")]
        assert ("hines_gwd" in drag) == ("hines" in g) and ("lott_miller_sso" in drag) == ("_lm" in g) and ("rayleigh_drag" in drag) == ("ray" in g), g
        assert ("moist_air_state" in t) == ("hines" in g or "_lm" in g), g
        for k in ("held_suarez", "production_tracers", "omega_diagnostic"):
            assert t[k] == base[k], (g, k)
        if "hines_gwd" in t:
            assert t.hines_gwd.launch_p_hpa == 634.0 and t.hines_gwd.rms_launch_wind == 1.0
        if "rayleigh_drag" in t:
            assert t.rayleigh_drag.p_bot_hpa == 30.0 and t.rayleigh_drag.p_top_hpa == 1.0 and t.rayleigh_drag.tau_days == 10.0 and t.rayleigh_drag.zonal_mean_only is False


def test_every_matrix_line_composes_and_instantiates():
    import hydra
    from jcm.physics.composable_physics import ComposablePhysics
    from jcm_strat import levels
    levels.install("strat")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = [l for l in open(os.path.join(here, "scripts", "phase15_matrix.txt")) if l.strip() and not l.startswith("#")]
    assert len(rows) >= 8
    seen = set()
    for l in rows:
        name, phys, ov, desc = [c.strip() for c in l.split("|", 3)]
        assert name not in seen; seen.add(name)
        extra = [] if ov == "-" else ov.split()
        c = compose_run_config(["+experiment=p15_base", f"physics={phys}", *extra])
        assert c.run.save_interval == 0.25 and list(c.output_keep) == KEEP
        terms = [hydra.utils.instantiate(v) for v in c.physics.terms.values()]
        names = [t.name for t in ComposablePhysics(terms).terms]
        assert names[0] in ("held_suarez", "moist_air_column_state") and names[-1] == "omega_diagnostic"
