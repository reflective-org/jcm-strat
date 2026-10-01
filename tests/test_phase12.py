"""Phase 12 experiments compose to what their headers say (CPU, hydra compose only, no model)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

from jcm_strat.advection_tracers import CLOCKS
from jcm_strat.prefetch_era5 import compose_run_config


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p11a_prod", "p12_ctl", "p12_noqbo", "p12_l81", "p12_echam")}


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


def test_echam_is_the_full_package_plus_the_phase12_terms(cfgs):
    ctl, ec = cfgs["p12_ctl"], cfgs["p12_echam"]
    terms = list(ec.physics.terms)
    assert terms[:12] == ["moist_air_state", "echam_boundary_conditions", "macv2_sp_aerosol", "simple_chemistry", "sundqvist_cloud_fraction",
                          "rrtmgp_radiation", "tte_tke_vertical_diffusion", "echam_surface", "tiedtke_convection", "echam_1m_microphysics",
                          "hines_gwd", "lott_miller_sso"]
    assert terms[12:] == ["qbo_nudging", "production_tracers", "omega_diagnostic"]
    assert "held_suarez" not in ec.physics.terms
    q = ec.physics.terms.qbo_nudging; cq = ctl.physics.terms.held_suarez.qbo
    assert q._target_ == "jcm_strat.qbo_nudging.QboNudging"
    for k in ("tau_days", "mean_preserving", "lat_full_deg", "lat_zero_deg", "p_bot_hpa", "p_top_hpa", "era5_glob"):
        assert q[k] == cq[k]
    assert ec.physics.terms.production_tracers == ctl.physics.terms.production_tracers
    assert ec.grid.layers == 95 and ec.level_table is None
    # 12-hourly target and 5-day chunks: the 6-hourly one OOMed beside RRTMGP at chunk 2 (2026-09-18), as in Phase 6
    assert ec.nudging.min_pressure_hpa == 150.0 and ec.nudging.tau_hours == 6.0 and ec.nudging.freq == "12h"
    assert ec.run.save_interval == 0.25 and ec.run.chunk_days == 5 and ec.calendar == "gregorian" and ec.run.time_step == 12
    assert set(ec.sl_mass_fixer_exclude) == set(ctl.sl_mass_fixer_exclude)
    assert set(ec.output_keep) >= {"u_wind", "v_wind", "temperature", "omega", "aoa_sfc", "aoa500", "n2o", "cfc11"}
    assert ec.forcing.kind == "from_file" and ec.init.kind == "era5"
