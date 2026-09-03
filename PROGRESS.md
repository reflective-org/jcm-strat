# Progress

Newest first. Each row links to the per-phase record in `docs/outputs/`.

| Date | Phase | State | Record |
|---|---|---|---|
| 2026-09-03 | 6 — stratosphere without radiation (Polvani-Kushner, seasonal) | A/B of 8 configurations done, choice fixed as `strat_pk` defaults; **done**: 5-year chain (6.4 K / 5.6 m/s vs ERA5, 2 of 3 SSW winters, AoA pattern vs CLaMS); full-ECHAM reference year: better T (4.3 K) but no Arctic vortex and 9.7 m/s | [docs/outputs/06_stratosphere/output.md](docs/outputs/06_stratosphere/output.md) |
| 2026-09-03 | 3 — passive tracers | **done**: aoa/unity/sai/e90 term, 1-yr run 2005, all acceptance checks pass; mass-fixer/clock interaction found and fixed | [docs/outputs/03_tracers/output.md](docs/outputs/03_tracers/output.md) |
| 2026-09-03 | 2 — specified dynamics | runs done (90 d check, 1-yr 2005), PR open | [docs/outputs/02_nudged/output.md](docs/outputs/02_nudged/output.md) |
| 2026-09-02 | 1 — stripped dry model | run done (1-yr HS), PR open | [docs/outputs/01_dry/output.md](docs/outputs/01_dry/output.md) |
| 2026-09-02 | 0 — environment, baseline | **done**: env built and accepted, two smoke runs, 10-day baseline timed at dt 12 and 15, issues #1–#15 filed | [docs/outputs/00_phase0/output.md](docs/outputs/00_phase0/output.md) |

## Throughput table

Simulated days per wall-clock hour, one H100 (GPU 0), `run=longrun` unless stated.

| Phase | Configuration | Grid | dt [min] | days/hr | ms/step | run | date |
|---|---|---|---|---|---|---|---|
| 0 | JCM full ECHAM physics (reference) | T63L95 | 12 | 51.6 | 582 | `base_echam_l95_10d` | 2026-09-02 |
| 0 | JCM full ECHAM physics (reference) | T63L95 | 15 | 51.9 | 723 | `base_echam_l95_10d_dt15` | 2026-09-02 |
| 1 | P1 dry HS | T63L95 | 12 | 6000.0 (e2e 991) | 5 | `p1_dry_30d` | 2026-09-02 |
| 1 | P1 dry HS | T63L95 | 12 | 5786.9 (e2e 2368) | 5 | `p1_dry_1yr` | 2026-09-02 |
| 2 | P2 SD | T63L95 | 12 | 5454.5 (e2e 2326) | 6 | `p2_sd_1yr` | 2026-09-03 |
| 3 | P3 SD + passive tracers (aoa, unity, sai, e90) | T63L95 | 12 | 4458.4 (e2e 2082) | 7 | `p3_tracers_1yr` | 2026-09-03 |
| 6 | P6 SD + tracers + Polvani-Kushner stratosphere | T63L95 | 12 | 4445.3 (e2e 2012) | 7 | `p6_pk_g4_t15_s05_top3` | 2026-09-03 |
| 6 | reference: full ECHAM physics + SD nudging (12 h target), GPU 1 | T63L95 | 12 | 139.9 (e2e 131) | 214 | `ref_echam_sd_2005` | 2026-09-03 |

(e2e = end-to-end incl. compile and output writing.) Reference from upstream (A100-40GB, `docs/source/design/dinosaur_sl_jam_configuration.md` in
JCM): T63L47 full science 115 days/hr at dt=15 min; T63L95 full science 52 days/hr.
