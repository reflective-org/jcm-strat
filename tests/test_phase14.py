"""Phase 14: the free-running full-physics experiment is p12_echam minus the two relaxations (CPU, hydra compose only)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import pytest

from jcm_strat.prefetch_era5 import compose_run_config


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p12_echam", "p14_free")}


def test_free_is_echam_without_nudging_and_without_the_qbo_term(cfgs):
    ec, fr = cfgs["p12_echam"], cfgs["p14_free"]
    # no ERA5 relaxation: jcm.runners.maybe_add_nudging / _maybe_attach_nudging_target look only at this flag
    assert fr.nudging.enabled is False and ec.nudging.enabled is True
    # no QBO relaxation, every other term in the same order
    assert "qbo_nudging" not in fr.physics.terms and "held_suarez" not in fr.physics.terms
    assert list(fr.physics.terms) == [t for t in ec.physics.terms if t != "qbo_nudging"]
    for t in fr.physics.terms:
        assert fr.physics.terms[t] == ec.physics.terms[t], t
    assert fr.physics.vectorize_columns == ec.physics.vectorize_columns and fr.physics.checkpoint_terms == ec.physics.checkpoint_terms


def test_free_keeps_every_other_p12_echam_choice(cfgs):
    ec, fr = cfgs["p12_echam"], cfgs["p14_free"]
    assert fr.grid == ec.grid and fr.grid.layers == 95 and fr.level_table is None
    assert fr.run == ec.run and fr.run.save_interval == 0.25 and fr.run.chunk_days == 5 and fr.run.time_step == 12
    assert fr.calendar == "gregorian" and fr.init.kind == "era5" and fr.forcing == ec.forcing and fr.terrain == ec.terrain
    assert fr.sl_mass_fixer is True and set(fr.sl_mass_fixer_exclude) == set(ec.sl_mass_fixer_exclude)
    assert list(fr.output_keep) == list(ec.output_keep)
