"""Phase 13c: Jucker + drag with the 400 hPa cutoff, with and without Lott-Miller (CPU, hydra compose only)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

from jcm_strat.prefetch_era5 import compose_run_config

MOIST = {"air_density", "height_full", "height_half", "layer_thickness", "pressure_full", "pressure_half", "pressure_thickness", "relative_humidity", "surface_pressure"}


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p13_jucker_gwd", "p13_jucker_gwd_n400", "p13_jucker_hines_n400")}


def test_gwd_n400_is_jucker_gwd_with_the_cutoff_and_the_moist_diagnostics_dropped(cfgs):
    jg, n4 = cfgs["p13_jucker_gwd"], cfgs["p13_jucker_gwd_n400"]
    assert n4.nudging.min_pressure_hpa == 400.0 and jg.nudging.min_pressure_hpa == 150.0
    assert {k: v for k, v in n4.nudging.items() if k != "min_pressure_hpa"} == {k: v for k, v in jg.nudging.items() if k != "min_pressure_hpa"}
    assert n4.physics == jg.physics and n4.grid == jg.grid and n4.run == jg.run and n4.grid.layers == 81
    assert set(n4.output_drop) == set(jg.output_drop) | MOIST and len(n4.output_drop) == 28
    for k in ("u_wind", "v_wind", "temperature", "omega", "aoa", "aoa150", "aoa_sfc", "aoa500", "n2o", "cfc11"):
        assert k not in n4.output_drop


def test_hines_n400_drops_only_lott_miller(cfgs):
    n4, h4 = cfgs["p13_jucker_gwd_n400"], cfgs["p13_jucker_hines_n400"]
    assert list(h4.physics.terms) == ["moist_air_state", "held_suarez", "hines_gwd", "production_tracers", "omega_diagnostic"]
    for k in h4.physics.terms:
        assert h4.physics.terms[k] == n4.physics.terms[k], k
    assert h4.physics.terms.held_suarez._target_ == "jcm_strat.jucker.JuckerColumns"
    for k in ("grid", "run", "nudging", "output_drop", "sl_mass_fixer_exclude", "calendar", "level_table"):
        assert h4[k] == n4[k], k


def test_hines_only_list_composes(cfgs):
    import hydra
    from jcm.physics.composable_physics import ComposablePhysics
    from jcm_strat import levels
    levels.install("strat")
    terms = [hydra.utils.instantiate(v) for v in cfgs["p13_jucker_hines_n400"].physics.terms.values()]
    assert [t.name for t in ComposablePhysics(terms).terms] == ["moist_air_column_state", "held_suarez", "hines_gwd", "production_tracers", "omega_diagnostic"]
