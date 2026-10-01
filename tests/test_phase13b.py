"""Phase 13b: the Jucker et al. (2013) relaxation term and its two experiments (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import jax.numpy as jnp
import numpy as np
import pytest
from flax import nnx

from jcm_strat.jucker import DEFAULT_DATA, JuckerColumns, load_jfv_table
from jcm_strat.prefetch_era5 import compose_run_config

PK = dict(gamma_k_per_km=4.0, p_tropopause_hpa=100.0, p_vortex_top_hpa=3.0, tau_strat_days=15.0, season_offset=0.5)


def _term(lats_deg, p_hpa, **kw):
    term = JuckerColumns(qbo=None, **PK, **kw)
    term._sigma = nnx.Variable(jnp.asarray(np.asarray(p_hpa) / 1013.25))
    term._lat = nnx.Variable(jnp.deg2rad(jnp.asarray(np.asarray(lats_deg, float))))
    term._coords_cached = True
    parent = type(term).__mro__[1]; orig = parent.cache_coords
    parent.cache_coords = lambda self, coords: None                       # sigma/lat are hand-set above
    try:
        term.cache_coords(object())
    finally:
        parent.cache_coords = orig
    return term


def _te_k(term, tyear):
    n = term._lat.get_value().shape[0]
    return np.asarray(term._equilibrium_temperature(jnp.ones((n,)), tyear)) / term._k_per_nondim


def _tau_days(term, tyear):
    return 1.0 / (np.asarray(term._kt_jucker(tyear)) / term._k_per_inv_second) / 86400.0


def test_data_file_is_the_jfv_table():
    days, p, lat, te, tau = load_jfv_table(DEFAULT_DATA)
    assert te.shape == tau.shape == (12, 40, 64) and np.all(np.diff(p) > 0) and np.all(np.diff(lat) > 0)
    assert days[0] == 15.5 and days[-1] == 349.5
    assert 130 <= te.min() and te.max() <= 345 and 3.4 <= tau.min() / 86400 <= 3.6 and 41 <= tau.max() / 86400 <= 43


def test_winter_pole_cold_summer_stratopause_hot_and_seasons_swap():
    term = _term([-85.0, 0.0, 85.0], [1.0, 10.0, 100.0])
    jan, jul = _te_k(term, 15.5 / 365), _te_k(term, 196.5 / 365)          # exactly mid-January / mid-July
    assert 295 < jan[0, 0] < 310 and 200 < jan[0, 2] < 212                 # 1 hPa: SH summer stratopause, NH winter pole
    assert 295 < jul[0, 2] < 315 and 165 < jul[0, 0] < 175                 # swapped in July
    assert 180 < jan[2, 2] < 192 and 225 < jan[2, 0] < 235                 # 100 hPa: cold winter pole, warmer summer pole
    assert 265 < jan[0, 1] < 285 and 265 < jul[0, 1] < 285                 # tropics: little seasonal cycle


def test_tau_is_radiative_above_100_hpa_and_held_suarez_below():
    term = _term([-60.0, 0.0, 60.0], [0.3, 1.0, 10.0, 100.0, 300.0, 500.0])
    tau = _tau_days(term, 15.5 / 365)
    assert np.all((4.0 <= tau[:2]) & (tau[:2] <= 6.5))                     # 1-0.3 hPa: 4.5-6 d
    assert np.all((5.0 <= tau[2]) & (tau[2] <= 10.0))                      # 10 hPa
    assert np.all((11.0 <= tau[3]) & (tau[3] <= 41.0))                     # 100 hPa: 12-40 d (tropics longest)
    assert np.allclose(tau[4:], 40.0)                                      # Held-Suarez k_a below 250 hPa


def test_blend_region_is_linear_between_250_and_100_hpa():
    term = _term([0.0], [100.0, 175.0, 250.0])
    beta = np.asarray(term._beta.get_value())[:, 0]
    assert np.allclose(beta, [1.0, 0.5, 0.0])                              # JFV at 100 hPa, Held-Suarez at 250, half-half at 175
    te = _te_k(term, 0.3)[:, 0]
    jfv = np.asarray(term._jfv(term._te_tab.get_value(), 0.3))[:, 0] / term._k_per_nondim
    hs = np.asarray(type(term).__mro__[1]._equilibrium_temperature(term, jnp.ones((1,)), 0.3))[:, 0] / term._k_per_nondim
    assert abs(te[0] - jfv[0]) < 1e-3 and abs(te[2] - hs[2]) < 1e-3
    assert abs(te[1] - 0.5 * (jfv[1] + hs[1])) < 1e-3                     # the two profiles mixed at the SAME level


def test_month_interpolation_is_periodic_and_hits_the_nodes():
    term = _term([45.0], [10.0])
    m0, m1, w = term._month_weights(jnp.asarray(15.5 / 365)); assert (int(m0), int(m1), round(float(w), 6)) == (0, 1, 0.0)
    m0, m1, w = term._month_weights(jnp.asarray(0.0)); assert (int(m0), int(m1)) == (11, 0) and 0.45 < float(w) < 0.55
    a, b = _te_k(term, 0.0)[0, 0], _te_k(term, 0.999999)[0, 0]
    assert abs(a - b) < 0.05                                               # continuous across New Year


def test_p_bd_cannot_exceed_the_tropopause():
    with pytest.raises(ValueError):
        JuckerColumns(qbo=None, p_bd_hpa=150.0, **PK)


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p12_l81", "p13_gwd", "p13_jucker", "p13_jucker_gwd")}


def test_jucker_is_p12_l81_with_the_relaxation_swapped(cfgs):
    l81, j = cfgs["p12_l81"], cfgs["p13_jucker"]
    assert list(j.physics.terms) == ["held_suarez", "production_tracers", "omega_diagnostic"]
    hs = j.physics.terms.held_suarez
    assert hs._target_ == "jcm_strat.jucker.JuckerColumns" and hs.p_bd_hpa == 100.0 and hs.p_hs_hpa == 250.0
    for k in ("gamma_k_per_km", "p_tropopause_hpa", "phi0_deg", "delta_phi_deg", "epsilon_k", "season_offset", "p_vortex_top_hpa", "tau_strat_days"):
        assert hs[k] == l81.physics.terms.held_suarez[k]
    assert hs.qbo == l81.physics.terms.held_suarez.qbo                     # QBO nudging unchanged, inside the term
    assert j.physics.terms.production_tracers == l81.physics.terms.production_tracers and j.physics.terms.production_tracers.lid_p_hpa == 1.0
    for k in ("grid", "run", "nudging", "output_drop", "sl_mass_fixer_exclude", "calendar", "level_table", "terrain"):
        assert j[k] == l81[k], k
    assert j.grid.layers == 81


def test_jucker_gwd_adds_exactly_the_phase13_drag_terms(cfgs):
    j, jg, g = cfgs["p13_jucker"], cfgs["p13_jucker_gwd"], cfgs["p13_gwd"]
    assert list(jg.physics.terms) == ["moist_air_state", "held_suarez", "hines_gwd", "lott_miller_sso", "production_tracers", "omega_diagnostic"]
    for k in ("moist_air_state", "hines_gwd", "lott_miller_sso"):
        assert jg.physics.terms[k] == g.physics.terms[k]
    assert jg.physics.terms.held_suarez == j.physics.terms.held_suarez
    for k in ("grid", "run", "nudging", "output_drop", "sl_mass_fixer_exclude", "calendar", "level_table"):
        assert jg[k] == j[k], k


def test_jucker_gwd_terms_compose_in_a_valid_order(cfgs):
    import hydra
    from jcm.physics.composable_physics import ComposablePhysics
    from jcm_strat import levels
    levels.install("strat")
    terms = [hydra.utils.instantiate(v) for v in cfgs["p13_jucker_gwd"].physics.terms.values()]
    cp = ComposablePhysics(terms)
    assert [t.name for t in cp.terms][:4] == ["moist_air_column_state", "held_suarez", "hines_gwd", "lott_miller_sso"]
    assert type(terms[1]).__name__ == "JuckerColumns" and terms[1].qbo is not None
