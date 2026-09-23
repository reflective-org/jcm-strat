"""Phase 13: gravity-wave drag on the dry column path, the strat77 table and the 400 hPa nudging cutoff (CPU)."""
import os

os.environ.setdefault("JAX_PLATFORMS", "cpu")

import numpy as np
import pytest

from jcm_strat import gwd, levels
from jcm_strat.prefetch_era5 import compose_run_config


@pytest.fixture(scope="module")
def cfgs():
    return {e: compose_run_config([f"+experiment={e}"]) for e in ("p12_ctl", "p12_l81", "p13_gwd", "p13_gwd_l77", "p13_l81_n400")}


def test_gwd_is_the_control_plus_the_drag_terms_only(cfgs):
    ctl, g = cfgs["p12_ctl"], cfgs["p13_gwd"]
    assert list(g.physics.terms) == ["moist_air_state", "held_suarez", "hines_gwd", "lott_miller_sso", "production_tracers", "omega_diagnostic"]
    assert g.physics.terms.hines_gwd._target_ == "jcm_strat.gwd.HinesGwdLaunch"
    assert g.physics.terms.hines_gwd.launch_p_hpa == 634.0 and g.physics.terms.hines_gwd.rms_launch_wind == 1.0
    assert g.physics.terms.lott_miller_sso._target_ == "jcm.physics.gravity_waves.sso.LottMillerSso"
    assert g.physics.terms.moist_air_state._target_.endswith("MoistAirColumnState")
    for k in ("held_suarez", "production_tracers", "omega_diagnostic"):
        assert g.physics.terms[k] == ctl.physics.terms[k]
    assert g.physics.terms.production_tracers.lid_p_hpa == 1.0           # the clocks stay relaxed to WACCM above 1 hPa
    for k in ("grid", "run", "nudging", "output_drop", "sl_mass_fixer_exclude", "calendar", "level_table", "terrain"):
        assert g[k] == ctl[k], k


def test_gwd_terms_compose_in_a_valid_order(cfgs):
    import hydra
    from jcm.physics.composable_physics import ComposablePhysics
    levels.install("strat")
    terms = [hydra.utils.instantiate(v) for v in cfgs["p13_gwd"].physics.terms.values()]
    cp = ComposablePhysics(terms)                                         # validates requires/provides
    assert [t.name for t in cp.terms][:4] == ["moist_air_column_state", "held_suarez", "hines_gwd", "lott_miller_sso"]


def test_gwd_l77_is_gwd_on_strat77_with_the_l95_sponge(cfgs):
    g, l77 = cfgs["p13_gwd"], cfgs["p13_gwd_l77"]
    assert l77.grid.layers == 77 and l77.level_table == "strat"
    assert (l77.run.sponge.levels, l77.run.sponge.enspodi) == levels.sponge_for(77) == (10, 2.0)
    assert l77.physics == g.physics and l77.nudging == g.nudging
    rest = {k: v for k, v in l77.run.items() if k != "sponge"}
    assert rest == {k: v for k, v in g.run.items() if k != "sponge"}


def test_l81_n400_is_p12_l81_with_the_cutoff_at_400(cfgs):
    l81, n4 = cfgs["p12_l81"], cfgs["p13_l81_n400"]
    assert n4.nudging.min_pressure_hpa == 400.0 and l81.nudging.min_pressure_hpa == 150.0
    assert {k: v for k, v in n4.nudging.items() if k != "min_pressure_hpa"} == {k: v for k, v in l81.nudging.items() if k != "min_pressure_hpa"}
    assert n4.physics == l81.physics and n4.grid == l81.grid and n4.run == l81.run
    assert "hines_gwd" not in n4.physics.terms                          # no drag in run 3


@pytest.mark.parametrize("n, level, p_hpa", [(95, 10, 634), (81, 10, 634), (63, 3, 589), (77, 3, 589)])
def test_launch_level_resolves_to_the_same_pressure_on_every_table(n, level, p_hpa):
    from jcm.physics.echam import echam_levels as el
    levels.install("strat")
    lev, p = gwd.launch_level_for(el.get_echam_levels(n), 634.0)
    assert lev == level and round(p) == p_hpa
    # 10 levels above the surface - JCM's fixed default - would be the stratosphere on the 8-layer tropospheres
    p_full = 0.5 * (levels.pressures_hpa(n)[:-1] + levels.pressures_hpa(n)[1:])
    assert (p_full[n - 10 - 1] < 160) == (n in (63, 77))


def test_hines_launch_term_drags_a_stratospheric_jet_from_the_resolved_level():
    """A strat63 column with a westerly jet peaking at 1 hPa: finite tendencies, none below the launch level."""
    import jax.numpy as jnp
    from jcm.physics.echam import echam_levels as el
    from jcm.physics_interface import PhysicsState

    levels.install("strat")
    vert = el.get_echam_levels(63)
    term = gwd.HinesGwdLaunch(launch_p_hpa=634.0, rms_launch_wind=1.0)
    term.cache_coords(type("C", (), {"vertical": vert})())
    assert term.launch_level == 3
    ph = np.asarray(vert.a_boundaries) + np.asarray(vert.b_boundaries) * 101325.0
    pf = 0.5 * (ph[:-1] + ph[1:]); nlev = pf.size; ncol = 2
    T = 220.0 + 60.0 * np.clip(np.log(pf / 100.0) / np.log(1000.0), 0, 1)
    u = 60.0 * np.exp(-0.5 * (np.log(pf / 100.0) / 1.5) ** 2)             # jet centred on 1 hPa
    z_half = 7000.0 * np.log(101325.0 / np.maximum(ph, 1e-3))
    rho = pf / (287.0 * T)
    col = lambda a: jnp.asarray(np.repeat(a[:, None], ncol, axis=1))
    diags = {"pressure_full": col(pf), "pressure_half": col(ph), "height_half": col(z_half), "air_density": col(rho)}
    state = PhysicsState(u_wind=col(u), v_wind=col(np.zeros(nlev)), temperature=col(T), specific_humidity=col(np.zeros(nlev)),
                         geopotential=col(9.81 * 0.5 * (z_half[:-1] + z_half[1:])), normalized_surface_pressure=jnp.ones((ncol,)), tracers={})
    tend, _ = term(state, diags, None, None)
    du = np.asarray(tend.u_wind)
    assert du.shape == (nlev, ncol) and np.all(np.isfinite(du))
    launch_idx = nlev - term.launch_level - 1
    assert np.allclose(du[launch_idx + 1:], 0.0)                          # nothing below the launch level
    assert np.abs(du[pf < 500.0]).max() > 0.0                             # drag somewhere above it
