"""Phase 12 experiments compose to what their headers say (CPU, hydra compose only, no model)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

from jcm_strat.advection_tracers import CLOCKS
from jcm_strat.prefetch_era5 import compose_run_config


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p11a_prod", "p12_ctl", "p12_noqbo", "p12_l81")}


def test_ctl_is_p11a_plus_aoa500_and_trimmed_output(cfgs):
    p11, ctl = cfgs["p11a_prod"], cfgs["p12_ctl"]
    assert ctl.physics.terms.production_tracers._target_.endswith("ProductionTracersAoa500")
    assert ctl.physics.terms.production_tracers.aoa500_reset_pressure_hpa == 500.0
    assert set(ctl.sl_mass_fixer_exclude) == set(p11.sl_mass_fixer_exclude) | {"aoa500"}
    drop = set(ctl.output_drop)
    assert not drop & (set(CLOCKS) | {"aoa500", "n2o", "cfc11", "omega", "u_wind", "v_wind", "temperature"})
    assert {"sai", "pulse_1", "pulse_5_box", "src_4_box"} <= drop and len(drop) == 19
    # the dynamics-side configuration is p11a's
    for key in ("gamma_k_per_km", "tau_strat_days", "p_vortex_top_hpa"):
        assert ctl.physics.terms.held_suarez[key] == p11.physics.terms.held_suarez[key]
    assert ctl.physics.terms.held_suarez.qbo.tau_days == p11.physics.terms.held_suarez.qbo.tau_days == 1.0
    assert ctl.grid.layers == 63 and ctl.level_table == "strat" and ctl.run.save_interval == 0.25 and ctl.calendar == "gregorian"


def test_noqbo_has_no_qbo_term_and_the_same_polvani_kushner(cfgs):
    ctl, nq = cfgs["p12_ctl"], cfgs["p12_noqbo"]
    hs = nq.physics.terms.held_suarez
    # p10_prod merges qbo.tau_days onto the group; the experiment body must have set the mapping back to null
    assert hs._target_ == "jcm_strat.qbo_nudging.PolvaniKushnerQbo" and hs.qbo is None
    for key in ("gamma_k_per_km", "p_tropopause_hpa", "phi0_deg", "delta_phi_deg", "epsilon_k", "season_offset", "p_vortex_top_hpa", "tau_strat_days"):
        assert hs[key] == ctl.physics.terms.held_suarez[key]
    assert nq.physics.terms.production_tracers == ctl.physics.terms.production_tracers
    assert nq.grid.layers == 63 and nq.nudging.min_pressure_hpa == ctl.nudging.min_pressure_hpa == 150.0


def test_l81_changes_only_the_grid(cfgs):
    ctl, l81 = cfgs["p12_ctl"], cfgs["p12_l81"]
    assert l81.grid.layers == 81 and l81.grid.spectral_truncation == 63 and l81.level_table == "strat"
    assert l81.physics == ctl.physics and l81.nudging == ctl.nudging
    assert l81.run.sponge.levels == ctl.run.sponge.levels == 4 and l81.run.sponge.enspodi == ctl.run.sponge.enspodi
    assert l81.run.time_step == ctl.run.time_step == 12
