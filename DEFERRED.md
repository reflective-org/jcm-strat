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
| [#6](https://github.com/reflective-org/jcm-strat/issues/6) | QBO nudging of tropical stratospheric wind | feature | **Done in Phase 8** (`docs/outputs/08_qbo`); close when the branch is merged. Cheaper zonal-mean reduction: #44. |
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
| [#25](https://github.com/reflective-org/jcm-strat/issues/25) | Reference the age-of-air clock to the tropopause (reset below ~150 hPa, or entry age) | research | Part of the tropical age excess is tropospheric transit in a non-convecting model. |
| [#26](https://github.com/reflective-org/jcm-strat/issues/26) | Stream the ERA5 nudging target instead of holding it on the GPU | upstream | Limits nudged runs to ~1 year per segment at L95; chained segments are the workaround. |

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

## Found in Phase 8

| Item | Label | Notes |
|---|---|---|
| QBO amplitude 80 % of ERA5, westerly phases +5-10 m/s where ERA5 has +10-20: the 10-day relaxation, not the window (the 1 hPa top changed nothing inside the QBO layer) | research | **tau 5 d tested over 2005-2009 (`p8c_5yr`, record addendum 2026-09-10): amplitude 80 -> 86 %, nothing else moves; consistent with a ~40 d model restoring time.** Still open: 2 d (~95 %) and 6 h (prescribed, like the troposphere), and the decision which becomes the default. Watch the thermal-wind temperature anomalies against the 15-day Polvani-Kushner relaxation. |
| Daily instead of monthly QBO target | feature | `scripts/fetch_era5_strat_ref.py` already pulls 6-hourly 10 hPa u from CDS; extend to all 25 levels and u + T, and replace the month-centre interpolation in `qbo_nudging.py` by day centres. Only pays off with a tau well below 10 d. |
| SAO at 1 hPa still 30 % of ERA5 (9.5 vs 30.7 m/s) | research | The weight is 0 at 1 hPa by construction (the target's top level). A top below 1 hPa with the target clamped to its 1 hPa value, or a one-sided taper, would hold 1 hPa itself. |
| JCM's provenance probe crashed a segment (`UnicodeDecodeError` decoding `git diff HEAD`) when a tracked PDF was modified in the working tree | bug | Worked around with `.gitattributes` (`*.pdf binary`); the probe in `external/jax-gcm/jcm/provenance.py` should decode with `errors="replace"`. Upstream issue to file. |


## Found in Phase 9

| Item | Label | Notes |
|---|---|---|
| JCM truncates `save_interval / time_step` and `total_time / save_interval` silently (`model.py`), and the chunk loop labels a tail chunk shorter than a save without integrating it (`runners.py`), so a 7-min step or a 91-day segment loses time with no error; the 366-day 2008 segments of every chain so far integrated 365 days | bug | `jcm_strat/segments.py` and `chain_segments.sh` refuse both cases; upstream should raise. Upstream issue to file. |
| ERA5 prefetch (`jcm.data.era5.dataset_on_model_grid`) is single-threaded and holds ~5-7x the output window in RAM (a 20 GB T63L63 year peaks near 140 GB); the whole Phase 9 matrix (2 TB) takes ~10 h in three parallel streams and is CPU-, not network-bound | perf | Chunk the window in time inside `_to_model_grid`, or regrid per level in float32. Upstream issue to file. |
| Native terrain exists only for T63 and T106; T85 and T119 run on the interpolated T63 file (fine for the dry model, wrong once Lott-Miller SSO is on) | feature | The GMTED2010 builder in `jcm/data/mirror` runs on Glade; add t85 / t119 bundles there. |
| `tracer_budget.py`'s analytic sai target depends on the vertical table: the source-box mass fraction comes out 0.00811 on L95/strat63 and 0.00768 on strat47 (the model burdens agree to 0.5 % across the three, unity error 3e-4), so strat47 reads "+3.5 % vs analytic" where L95 reads -0.8 % | bug | The budget masks the box on nominal sigma x p_s per column while the model masks on a + b p_s (identical for pure-pressure layers); find the layer that flips between the two and mask on the file's own `hybrid_a_full/hybrid_b_full` instead. Diagnostic only. |
