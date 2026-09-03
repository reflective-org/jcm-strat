# Deferred

Consciously not done yet. Each item is a GitHub issue (filed 2026-09-02); none starts before Part 1
of [PLANS.md](PLANS.md) is complete. Ordered by value.

| # | Item | Label | Notes |
|---|---|---|---|
| [#1](https://github.com/reflective-org/jcm-strat/issues/1) | Dynamical nudging cutoff (follow the model's own tropopause, with a taper) instead of the 150 hPa hard mask | feature | Needs per-column `inv_tau` (JCM's `NudgingConfig` is per-level only). Interim: tanh taper 200→100 hPa. |
| [#2](https://github.com/reflective-org/jcm-strat/issues/2) | RRTMGP radiation with prescribed O3/CO2/CH4 in the stripped configuration | feature | Gives the stratosphere its own radiative equilibrium; radiation is the dominant cost — measure both. |
| [#3](https://github.com/reflective-org/jcm-strat/issues/3) | Time-step sweep 12→30→60→120 min | research | SL PR reports an accuracy knee near 30 min. |
| [#4](https://github.com/reflective-org/jcm-strat/issues/4) | Reduced ~30–44-level grid | feature | New table in `echam_levels.py` + `(63, N)` diffusion orders; ≥ 20 levels over 150–1 hPa. |
| [#5](https://github.com/reflective-org/jcm-strat/issues/5) | Polvani-Kushner 2002 stratosphere (polar-night jet without radiation) | feature | ~150 lines extending `HeldSuarez`. |
| [#6](https://github.com/reflective-org/jcm-strat/issues/6) | QBO nudging of tropical stratospheric wind | blocked | Needs ERA5 above 60 hPa (CDS 37-level or SPARC QBO tape). |
| [#7](https://github.com/reflective-org/jcm-strat/issues/7) | Segment-parallel 30-year runs | research | Only if the project ever needs more than GPU 0. |
| [#8](https://github.com/reflective-org/jcm-strat/issues/8) | Local mass consistency / expose `mass_fixer=False` on the CLI | research | Only if Phase-3 `unity` deviations are large. |
| [#9](https://github.com/reflective-org/jcm-strat/issues/9) | MAM4 aerosol + SO2 injection (`jcm[mam4]`, GPL) | feature | |
| [#10](https://github.com/reflective-org/jcm-strat/issues/10) | TOMAS from AIDE-SAI-link as a PhysicsTerm | feature | |
| [#11](https://github.com/reflective-org/jcm-strat/issues/11) | Pinatubo 1991–1995 validation | research | Thresholds agreed before the runs. |
| [#12](https://github.com/reflective-org/jcm-strat/issues/12) | Shared benchmark vs AIDE-SAI-link (34.9 s/step full physics, 2026-08-28) and PARADIS | research | |
| [#13](https://github.com/reflective-org/jcm-strat/issues/13) | Upstream JCM PRs: PassiveTracers term, per-column nudging, level tables | upstream | |
| [#14](https://github.com/reflective-org/jcm-strat/issues/14) | Pin dinosaur to a release once neuralgcm/dinosaur#135 merges (JCM v2.1) | upstream | Drops `external/dinosaur` and `env/overrides.txt`. |
| [#15](https://github.com/reflective-org/jcm-strat/issues/15) | Winds-only vs winds+temperature nudging A/B | research | One extra 1-year run of the Phase-2 config. |
| [#17](https://github.com/reflective-org/jcm-strat/issues/17) | Nudging-check diagnostics for Phase 2 acceptance (RMSE vs ERA5 below 150 hPa, tropopause, SSW) | feature | Needed to close the Phase-2 acceptance table. |
| [#18](https://github.com/reflective-org/jcm-strat/issues/18) | Global-mean p_s differs between dry and full-physics runs (998.6 vs 985.6 hPa) | research | Understand before comparing tracer burdens across configurations. |
| [#19](https://github.com/reflective-org/jcm-strat/issues/19) | Output volume / per-chunk overhead dominates the dry model's wall time | feature | Kernel 6000 d/hr vs end-to-end ~1000-2500 d/hr. |
| [#20](https://github.com/reflective-org/jcm-strat/issues/20) | Gravity-wave drag in the stripped model (needs a column-vectorized Held-Suarez) | feature | Phase-1 GWD A/B dropped; `strat_dry_gwd.yaml` removed until this is solved. |

## Found in Phase 6 (issues #31-#36, filed 2026-09-03)

| Item | Label | Notes |
|---|---|---|
| [#31](https://github.com/reflective-org/jcm-strat/issues/31) Tropical tropopause in the PK equilibrium: latitude-dependent `T_US` floor (~195 K at the equator, 217 K poleward) | feature | The stripped model is ~10 K warm at 70-150 hPa in the tropics; affects the tropical pipe and age of air. |
| [#32](https://github.com/reflective-org/jcm-strat/issues/32) Upper-stratosphere cold bias, 1-3 hPa, ~9 K year-round at tau 15 | research | Dynamical; check with Hines drag (#20) and with RRTMGP (#2). |
| [#34](https://github.com/reflective-org/jcm-strat/issues/34) Spin-up of the upper stratosphere from the ERA5 initial state (no information above 50 hPa) | feature | Start comparisons after a 1-2 month spin-up, or initialise the stratosphere from the PK equilibrium. |
| [#33](https://github.com/reflective-org/jcm-strat/issues/33) Internal variability vs relaxation time: SSW frequency at tau 15 vs 25 over 2005-2009 | research | Needs the 5-year chains; decides whether tau 15 is too stiff for the wave-driven variability. |
| [#32](https://github.com/reflective-org/jcm-strat/issues/32) Winter pole above 10 hPa 20-30 K too warm with the 3 hPa taper | feature | The taper hands the cap back to the standard atmosphere, whose 1-3 hPa values are summer ones; a colder winter stratopause target (or a taper to a winter profile) is needed. |
| [#35](https://github.com/reflective-org/jcm-strat/issues/35) Full-ECHAM specified-dynamics year has no Arctic vortex (u(60N,10hPa) ~4 m/s all year) and a half-strength Antarctic one | research | Check Hines/SSO drag strength and the radiation + nudging balance in the stock package before using it as the reference stratosphere; rerun with a 6 h target once memory allows. |
| [#36](https://github.com/reflective-org/jcm-strat/issues/36) tracer_budget pull-up check 192x too large before 2026-09-03 | bug | Fixed on phase6-stratosphere; Phase 3/4 numbers to correct (verdicts unchanged). |

## Found in Phase 7

| Item | Label | Notes |
|---|---|---|
| Semi-implicit off-centering vs time step: is `sl_off_centering` (0.2) what limits the step to < 60 min? | research | Two departure iterations did not help at 30 min and only delayed the blow-up at 60/90; sweep off-centering 0.2-0.5 at 45 and 60 min. |
| Antarctic jet weakening with the step (66 -> 54 m/s at 30 min) | research | Accuracy signature of the fast winter jet; check whether it is the dycore or the 6-hourly nudging interpolation, and whether the 5-year age of air changes at 30 min. |
