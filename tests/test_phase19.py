"""Phases 19-21: the reruns on jcm 3 (CPU, hydra compose only).

19d p19_jh_n400 = 13c run 2 (Jucker + Hines, strat81, nudging < 400 hPa) on the new jcm; 20 p20_jh_sso_n400 = 19d + the
fixed Lott-Miller; 21a p21_echam_n400 = p12_echam with nudging < 400 hPa; 21b p21_free = p14_free. All carry jcm 3's
defaults stated explicitly: ECHAM sponge on the top level only, no target_T_K, cubic SL vertical interpolation.
"""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

from jcm_strat.prefetch_era5 import compose_run_config

EXPS = ("p13_jucker_hines_n400", "p13_jucker_gwd_n400", "p12_echam", "p14_free",
        "p19_jh_n400", "p20_jh_sso_n400", "p21_echam_n400", "p21_free")


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in EXPS}


@pytest.mark.parametrize("e", ["p19_jh_n400", "p20_jh_sso_n400", "p21_echam_n400", "p21_free"])
def test_jcm3_defaults_are_stated(cfgs, e):
    c = cfgs[e]
    assert c.run.sponge.levels == 1 and c.run.sponge.timescale_h is None and c.run.sponge.enspodi is None
    assert "target_T_K" not in c.run.sponge
    # every Phase 19-21 run uses jcm 3's cubic SL vertical interpolation on the full L95 grid (cubic blew up only on strat81)
    assert c.dycore.sl_vertical_interpolation is None and c.grid.layers == 95 and c.level_table is None
    assert "start_date" not in c.run and c.run.monthly_means is False and c.run.save_chunks is True
    assert c.run.save_interval == 0.25 and c.run.output_averages is False and c.calendar == "gregorian"
    assert {"aoa", "aoa150", "aoa_sfc", "aoa500", "n2o", "cfc11"} <= set(c.sl_mass_fixer_exclude)


def test_p19_is_13c_run2_on_the_new_jcm_and_l95(cfgs):
    old, new = cfgs["p13_jucker_hines_n400"], cfgs["p19_jh_n400"]
    # same physics and nudging as 13c run 2; the grid is the full L95 (Susanne 2026-10-07), 13c ran on strat81
    assert new.physics == old.physics and new.nudging == old.nudging
    assert new.nudging.min_pressure_hpa == 400.0 and new.grid.layers == 95 and new.level_table is None
    assert "lott_miller_sso" not in new.physics.terms and "hines_gwd" in new.physics.terms
    assert new.output_drop == old.output_drop


def test_p20_adds_only_lott_miller(cfgs):
    p19, p20 = cfgs["p19_jh_n400"], cfgs["p20_jh_sso_n400"]
    assert list(p20.physics.terms) == ["moist_air_state", "held_suarez", "hines_gwd", "lott_miller_sso", "production_tracers", "omega_diagnostic"]
    assert p20.physics.terms.lott_miller_sso._target_ == "jcm.physics.gravity_waves.sso.LottMillerSso"
    for k in p19.physics.terms:
        assert p20.physics.terms[k] == p19.physics.terms[k], k
    for k in ("grid", "run", "nudging", "output_drop", "sl_mass_fixer_exclude", "dycore", "terrain", "level_table"):
        assert p20[k] == p19[k], k
    assert p20.terrain.file == "hf://bundles/t63/terrain.nc"


def test_p21a_is_p12_echam_with_the_400_hpa_cutoff(cfgs):
    old, new = cfgs["p12_echam"], cfgs["p21_echam_n400"]
    assert new.nudging.min_pressure_hpa == 400.0 and old.nudging.min_pressure_hpa == 150.0 and new.nudging.freq == "12h"
    assert new.physics == old.physics and new.grid.layers == 95 and new.level_table is None
    assert {"qbo_nudging", "hines_gwd", "lott_miller_sso", "echam_surface_exchange"} <= set(new.physics.terms)


def test_p21b_is_free_running(cfgs):
    c = cfgs["p21_free"]
    assert c.nudging.enabled is False and "qbo_nudging" not in c.physics.terms
    assert {"hines_gwd", "lott_miller_sso", "echam_surface_exchange"} <= set(c.physics.terms)
    assert c.physics == cfgs["p14_free"].physics and c.grid.layers == 95


def test_chain_initialises_tracers_for_phase_20_and_21_experiments():
    """chain_segments.sh adds first_segment=true on the first real segment for p10_*/p1x/p2x experiments (Phase 19 fix:
    the old pattern p1[1-9]* missed p20_*/p21_*, whose tracers would never have been initialised)."""
    import re
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(here, "scripts", "chain_segments.sh")).read()
    pat = re.search(r'case "\$EXPERIMENT" in ([^)]*)\) FIRST_SEG_EXTRA="physics.terms.production_tracers.first_segment=true"', src).group(1)
    import fnmatch
    for e in ("p19_jh_n400", "p20_jh_sso_n400", "p21_echam_n400", "p21_free"):
        assert any(fnmatch.fnmatch(e, g) for g in pat.split("|")), e


def test_p20_ignores_only_the_humidity_health_criterion(cfgs, monkeypatch):
    assert cfgs["p20_jh_sso_n400"].health_ignore_q_max is True
    assert not cfgs["p19_jh_n400"].get("health_ignore_q_max", False)
    import jcm.diagnostics as diag
    from jcm_strat.main import install_health_policy
    fake = {"q": (False, {"ok": False, "reasons": ["q_max=104.7 g/kg (> 100)"]}),
            "qT": (False, {"ok": False, "reasons": ["q_max=150.0 g/kg (> 100)", "T_min=84K (< 100K)"]})}
    monkeypatch.setattr(diag, "check_health", lambda ds, i, d: fake[ds])
    install_health_policy(True)
    ok, rep = diag.check_health("q", 0, 60.0)
    assert ok and rep["ok"] and rep["reasons"] == []
    ok, rep = diag.check_health("qT", 0, 60.0)
    assert not ok and rep["reasons"] == ["T_min=84K (< 100K)"]
