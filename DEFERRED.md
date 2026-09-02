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
