# Progress

Newest first. Each row links to the per-phase record in `docs/outputs/`.

| Date | Phase | State | Record |
|---|---|---|---|
| 2026-09-02 | 0 — environment, baseline | in progress: repo + pinned submodules + bootstrap written; env build running | [docs/outputs/00_phase0/output.md](docs/outputs/00_phase0/output.md) |

## Throughput table

Simulated days per wall-clock hour, one H100 (GPU 0), `run=longrun` unless stated.

| Phase | Configuration | Grid | dt [min] | days/hr | ms/step | run | date |
|---|---|---|---|---|---|---|---|
| 0 | JCM full ECHAM physics (reference) | T63L95 | 12 | — | — | — | — |

Reference from upstream (A100-40GB, `docs/source/design/dinosaur_sl_jam_configuration.md` in
JCM): T63L47 full science 115 days/hr at dt=15 min; T63L95 full science 52 days/hr.
