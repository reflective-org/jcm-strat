"""strat47 / strat63: subsets of L95 with the stratosphere intact, consistent diffusion orders and sponge (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import pytest

from jcm_strat import levels

L95 = levels.pressures_hpa(95)


@pytest.mark.parametrize("n", levels.TABLES)
def test_table_is_a_monotone_subset_of_l95(n):
    p = levels.pressures_hpa(n)
    assert p.size == n + 1
    assert np.all(np.diff(p) > 0)
    assert p[0] == L95[0] and p[-1] == L95[-1]
    # every interface is an L95 interface
    assert all(np.any(np.isclose(v, L95)) for v in p)


def test_strat63_keeps_the_stratosphere_and_thins_the_rest():
    p = levels.pressures_hpa(63)
    strat = L95[(L95 >= 1.0) & (L95 <= 160.0)]          # L95 interfaces 1.08 .. 159 hPa
    assert strat.size == 48
    assert all(np.any(np.isclose(v, p)) for v in strat)   # all 47 layers intact
    assert np.sum(p < 1.0) == 8 and np.sum(p > 160.0) == 8


def test_strat47_keeps_the_lower_stratosphere_at_l95_spacing():
    p = levels.pressures_hpa(47)
    lower = L95[(L95 >= 29.0) & (L95 <= 160.0)]          # 30 .. 159 hPa
    assert lower.size == 18
    assert all(np.any(np.isclose(v, p)) for v in lower)
    upper = p[(p >= 1.0) & (p < 29.0)]
    assert upper.size == 15                              # every other L95 interface
    assert np.sum(p < 1.0) == 7 and np.sum(p > 160.0) == 8


@pytest.mark.parametrize("n", levels.TABLES)
@pytest.mark.parametrize("trunc", (63, 127))
def test_orders_have_one_entry_per_level_and_grade_downward(n, trunc):
    orders = levels.level_orders(trunc, n)
    assert len(orders) == n
    assert orders[0] == 1                                # del2 at the top
    assert np.all(np.diff(orders) >= 0)                  # never a lower order below a higher one
    assert orders[-1] == (4 if trunc == 63 else 3)       # L95's bottom order
    assert sum(c for c, _ in levels.order_runs(trunc, n)) == n


def test_sponge_matches_the_experiment_yamls():
    import yaml
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for n, name in ((63, "p9_l63"), (47, "p9_l47")):
        cfg = yaml.safe_load(open(os.path.join(here, "jcm_strat", "config", "experiment", f"{name}.yaml")))
        lev, ensp = levels.sponge_for(n)
        assert cfg["run"]["sponge"]["levels"] == lev
        assert cfg["run"]["sponge"]["enspodi"] == pytest.approx(ensp, abs=0.01)
        # the sponge bottom sits within one L95 interface of L95's own (interface 10, 0.165 hPa)
        p = levels.pressures_hpa(n)
        assert 0.13 <= p[lev] <= 0.21


def test_install_patches_jcm_and_leaves_echam_l47_alone_until_asked():
    import jcm.diffusion as jd
    import jcm.physics.echam.echam_levels as el
    import jcm.runners as jr
    echam47 = np.asarray(el.get_echam_levels(47).a_boundaries)
    levels.install(None)                                  # no-op
    assert np.array_equal(np.asarray(el.get_echam_levels(47).a_boundaries), echam47)
    levels.install("strat")
    ours = np.asarray(el.get_echam_levels(47).a_boundaries)
    assert ours.size == 48 and not np.array_equal(ours, echam47)
    assert np.asarray(el.get_echam_levels(63).a_boundaries).size == 64
    assert np.asarray(el.get_echam_levels(95).a_boundaries).size == 96     # untouched
    assert {47, 63} <= set(jd.ECHAM_LMIDATM_LAYERS) and jr.ECHAM_LMIDATM_LAYERS is jd.ECHAM_LMIDATM_LAYERS
    assert jd.echam_lmidatm_orders(85, 63).size == 63 and jd.echam_lmidatm_orders(119, 47).size == 47
    with pytest.raises(ValueError):
        levels.install("other")
