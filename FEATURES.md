# Features

What works today. Updated with every PR.

| Feature | Since | How |
|---|---|---|
| Reproducible environment from pinned submodules (jax-gcm `849893b`, dinosaur SL `bd99e39b`), Python 3.11, CUDA JAX, all under the repo | Phase 0 | `scripts/bootstrap_env.sh`, `scripts/check_env.sh`, `env/requirements.lock` |
| One-command tmux launch on GPU 0 with run isolation (`runs/<session>/`) | Phase 0 | `scripts/launch.sh` |
| Throughput measurement and bar chart from a run's per-chunk wall-time attributes | Phase 0 | `scripts/throughput.py`, `scripts/plot_throughput.py`, `docs/outputs/throughput.csv` |
| Zonal-mean T/u sanity plot for any jcm output file | Phase 0 | `scripts/plot_zonal_mean.py` |
| Passive tracers (age of air, unity, idealised injection, e90) as one PhysicsTerm, advected semi-Lagrangian with the global mass fixer | Phase 3 | `jcm_strat/tracers.py`, `physics/strat_passive.yaml`, `+experiment=p3_tracers`, `tests/test_tracers.py` |
| Tracer budget and transport diagnostics (mass-weighted burdens with exact hybrid layer masses, sai vs analytic expectation, pull-up check, age of air at 20 hPa) | Phase 3 | `scripts/tracer_budget.py` |
