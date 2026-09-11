# Features

What works today. Updated with every PR.

| Feature | Since | How |
|---|---|---|
| Reproducible environment from pinned submodules (jax-gcm `849893b`, dinosaur SL `bd99e39b`), Python 3.11, CUDA JAX, all under the repo | Phase 0 | `scripts/bootstrap_env.sh`, `scripts/check_env.sh`, `env/requirements.lock` |
| One-command tmux launch on GPU 0 with run isolation (`runs/<session>/`) | Phase 0 | `scripts/launch.sh` |
| Year chains on a chosen GPU (`GPU=<n>`, default 0; refuses a busy card) | Phase 8 | `scripts/chain_years.sh` |
| Mean-preserving month-centre target for the QBO nudging (linear interpolation reproduces ERA5's monthly means) | Phase 8 | `qbo_nudging.mean_preserving_nodes`, `qbo.mean_preserving`, `tests/test_qbo_nudging.py` |
| Throughput measurement and bar chart from a run's per-chunk wall-time attributes | Phase 0 | `scripts/throughput.py`, `scripts/plot_throughput.py`, `docs/outputs/throughput.csv` |
| Zonal-mean T/u sanity plot for any jcm output file | Phase 0 | `scripts/plot_zonal_mean.py` |
| Passive tracers (age of air, unity, idealised injection, e90) as one PhysicsTerm, advected semi-Lagrangian with the global mass fixer | Phase 3 | `jcm_strat/tracers.py`, `physics/strat_passive.yaml`, `+experiment=p3_tracers`, `tests/test_tracers.py` |
| Tracer budget and transport diagnostics (mass-weighted burdens with exact hybrid layer masses, sai vs analytic expectation, pull-up check, age of air at 20 hPa) | Phase 3 | `scripts/tracer_budget.py` |
| Multi-year nudged runs as chained calendar-year segments (init=from_state from the previous checkpoint), per-year ERA5 windows sliced from one prefetch, aggregate run directory with cumulative day numbers | Phase 4 | `scripts/chain_years.sh`, `scripts/slice_era5_years.py`, `+experiment=p4_5yr` |
| Age-of-air comparison against CLaMS v3.1/ERA5 and WACCM6 REF-D1; polar-vortex u(60°, 10 hPa) time series with ERA5 SSW dates | Phase 4 | `scripts/aoa_vs_clams.py`, `scripts/vortex_series.py` |
| PDF report of all phase records | Phase 4 | `scripts/make_report.py` → `docs/outputs/jcm-strat_phases_0-4.pdf` |
| PARADIS rollout circulation comparison (zonal means of u, v, T, omega cached from the raw state.zarr; climatology and vortex panels against the model) | Phase 4 | `scripts/paradis_zonal.py`, `scripts/paradis_circulation.py`, `scripts/vortex_series.py --paradis` |
| Offline age-of-air clocks carried by a PARADIS rollout's winds (semi-Lagrangian on the rollout's grid, JAX/GPU, surface and 150 hPa resets); fourth and fifth sources in the age-of-air comparison | Phase 4 | `scripts/paradis_offline_clock.py`, `scripts/aoa_vs_clams.py --paradis-clock` |
| QBO nudging of the tropical stratospheric zonal-mean wind towards ERA5 monthly means, inside the Polvani-Kushner term; per-segment year via `EXTRA_PER_YEAR` | Phase 8 | `jcm_strat/qbo_nudging.py`, `physics/strat_pk_qbo.yaml`, `+experiment=p8_qbo`, `tests/test_qbo_nudging.py` |
| Before/after comparison of the equatorial wind (time-height, amplitude profiles, confinement of the change, error in the QBO layer and above it) | Phase 8 | `scripts/qbo_compare.py`; `aoa_vs_clams.py --second-run` |
| Phase 8 PDF (relaxation table, both window tops, all figures) | Phase 8 | `scripts/make_phase8_report.py` -> `docs/outputs/jcm-strat_phase8_qbo.pdf` |
| Tracked PDFs marked binary so `git diff` (and JCM's provenance probe, which decodes the diff as UTF-8) never dumps them | Phase 8 | `.gitattributes` |
