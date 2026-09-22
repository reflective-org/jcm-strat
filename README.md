# jcm-strat

**A stratosphere-only configuration of JCM on the Dinosaur semi-Lagrangian dycore, for fast
stratospheric tracer transport.** This is *Approach A* from the 2026-08-31 planning meeting:
run the physics dycore with tropospheric physics stripped out, nudge the troposphere to ERA5,
leave the stratosphere free, and measure how fast the simplest possible physics solve can be.
That number is the baseline against which the ML-emulator route (Approach B, PARADIS) is judged.

Status (2026-09-16): **Phases 0–10 done and merged into `dev`; Phase 11 chosen and being extended;
Phase 12 running.** The speed question is answered: one simulated year in 4–5 minutes of stepping
on one H100 at T63 (Phase 4: 10.4 min end-to-end with 5-day means, 30 yr ≈ 5.2 GPU-h; Phase 10: ~26–30
min end-to-end with 6-hourly instantaneous output, 30 yr ≈ 15 h). The stratosphere without
radiation is defensible (Polvani-Kushner target + QBO nudging: T RMSE ~6 K, u ~4.4 m/s vs ERA5,
polar-night jets, most sudden warmings, ERA5's QBO at 93 % amplitude). The open problem is
transport in the upper stratosphere: the dry model has no gravity-wave drag above the sponge, so
the mesosphere is never ventilated and the age-of-air clock grows without bound (23 yr after the
30-year Phase 10 run). Phase 11 bounds it with a tracer lid above 1 hPa; Phase 12 tests whether
the QBO nudging or the thinned troposphere is holding the deep branch back. Resolution is *not*
the cause (Phase 9: nine grids, same age of air). See [PROGRESS.md](PROGRESS.md), the phase
table below and the summary PDF
[docs/outputs/jcm-strat_phases_0-12_summary.pdf](docs/outputs/jcm-strat_phases_0-12_summary.pdf).

## What this repo is, and is not

- It is a **Hydra config overlay** on the installed `jcm` package plus a few small physics terms
  (passive/production tracers, Polvani-Kushner stratosphere, QBO nudging, reduced level tables).
  JCM's source is never edited; upgrading JCM is a submodule SHA bump.
- It is **not** a fork of JCM and **not** an aerosol model (yet). Aerosol microphysics and
  radiation are deferred, deliberately, so the transport and throughput question is answered
  first. See [DEFERRED.md](DEFERRED.md).
- Upstreams are pinned as submodules under `external/` because JCM's own requirement on the
  semi-Lagrangian Dinosaur is a *branch name*, not a commit, and the branch head moves.

## Quick start

```bash
git clone --recurse-submodules git@github.com:reflective-org/jcm-strat.git /data/JCM_stripped/jcm-strat
cd /data/JCM_stripped/jcm-strat
scripts/bootstrap_env.sh        # uv-managed Python 3.11 venv, everything under ./cache and ./.venv
scripts/check_env.sh            # must print only PASS lines
source scripts/env.sh           # activates the venv, pins GPU 0, points every cache into the repo

# a stock JCM smoke test (nothing of ours yet)
scripts/launch.sh smoke_hs physics=held_suarez grid=held_suarez_t31_l8 run=smoke
tmux attach -t strat_smoke_hs   # C-b d to detach
```

Every model run goes through `scripts/launch.sh`: it runs in a detached tmux session named
`strat_<session>`, on **GPU 0** by default (other cards only when released for a phase), writing
to `runs/<session>/`. Multi-year runs are chains of one-calendar-year segments
(`scripts/chain_segments.sh`, restart from the previous segment's checkpoint; the whole ERA5
nudging target for one year sits on the GPU, so one long run does not fit). Before any launch,
`python -c "import jax; print(jax.devices())"` must show a `CudaDevice`: this node loses its
`/dev/nvidia*` device nodes at every reboot and JAX then falls back to the CPU silently
(`scripts/restore_nvidia_dev.sh` on the Phase 12 branch recreates them; `chain_segments.sh`
refuses to start without a GPU).

## Unattended pipelines

Each phase runs unattended in tmux from a `scripts/phase<N>_*.sh` pipeline (runs, diagnostics,
output records, commits, PRs) so the session that started it can be closed. Check on one with:

```bash
tmux ls                                  # strat_<name> present = still running
tail -f runs/<name>.log                  # one line per step
tmux attach -t strat_<name>              # live console (C-b d to detach)
gh pr list --repo reflective-org/jcm-strat
```

The chain scripts skip segments whose logs show a clean exit, so after an interruption just
start the pipeline again (never reuse a run prefix for a different configuration, KEY_DECISIONS #38).

## Documents

| File | What it is |
|---|---|
| [PLANS.md](PLANS.md) | The plan: Part 1 (six PRs to the Phase-1 number) and Part 2 (deferred, as issues) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How the overlay, the environment and the run convention fit together |
| [PROGRESS.md](PROGRESS.md) | Where we are; the throughput table |
| [KEY_DECISIONS.md](KEY_DECISIONS.md) | Every default and *why* |
| [DEFERRED.md](DEFERRED.md) | What is consciously not done yet, with issue links |
| [FEATURES.md](FEATURES.md) | What works today |
| `docs/outputs/<NN_phase>/output.md` | Per-phase record: exact commands, numbers, plots, decisions |
| [docs/outputs/jcm-strat_phases_0-12_summary.pdf](docs/outputs/jcm-strat_phases_0-12_summary.pdf) | **Summary of all phases so far**: findings, what was tried, what is open (`scripts/make_summary_report.py`) |
| `docs/outputs/jcm-strat_phase*.pdf` | Per-phase PDFs (Phases 0–4, 6, 7, 8, 9) |
| [docs/PHYSICS_EXPLAINER.md](docs/PHYSICS_EXPLAINER.md) | Held-Suarez, Polvani-Kushner, QBO nudging and full physics explained in simple words, with what each cost us |
| `docs/background/` | The handover document this work started from |

## Phases

| Phase | What was done | Headline finding | Record |
|---|---|---|---|
| 0 | Environment, run tooling, stock JCM baseline | Full ECHAM physics at T63L95: 52 simulated days/hr | [00](docs/outputs/00_phase0/output.md) |
| 1 | Strip the physics: dry Held-Suarez on T63L95 | 5,800 days/hr stepping, 112× the full model | [01](docs/outputs/01_dry/output.md) |
| 2 | Nudge u, v, T to ERA5 below 150 hPa (tau 6 h), stratosphere free | Stable for a year, −6 % throughput | [02](docs/outputs/02_nudged/output.md) |
| 3 | Passive tracers: age-of-air clock, unity, idealised injection, e90 | Clock must be exempt from JCM's global mass fixer (0.44 day/day otherwise) | [03](docs/outputs/03_tracers/output.md) |
| 4 | Five chained years 2005–2009: the Phase-1 number | 10.4 min per year end-to-end; mass closed to 0.02 %; age of air pattern right but tropics 1.5 yr too old, no polar-night jet | [04](docs/outputs/04_5yr/output.md) |
| 6 | Stratosphere without radiation: seasonal Polvani-Kushner (8 A/B runs, 5-yr chain, full-ECHAM reference year) | tau 15 d, equinox-to-equinox season, vortex cooling faded above 3 hPa: T RMSE 6.4 K, u 5.6 m/s vs ERA5, 2 of 3 SSW winters; full ECHAM under the same nudging gets 4.3 K but no Arctic vortex | [06](docs/outputs/06_stratosphere/output.md) |
| 7 | Time-step sweep 12–120 min | Knee at 30 min (2.35× stepping, Antarctic jet −18 %); ≥ 60 min unusable; 12 min kept | [07](docs/outputs/07_timestep/output.md) |
| 8 | QBO nudging of the tropical zonal-mean wind to ERA5 monthly means (window top 4 → 1 hPa; tau 10 → 5 → 2 → 1 d; mean-preserving target) | Equatorial u error 16 → 2.2 m/s, QBO amplitude 93 % of ERA5, SAO appears; nothing outside the window moves; age of air 0.1 yr younger only | [08](docs/outputs/08_qbo/output.md) |
| 9 | Resolution sweep T63/T85/T119 × L95/strat63/strat47, nine 5-yr chains | Age of air identical at every grid (RMSE 0.73–0.75 yr): the bias is not resolution; **strat63** adopted (L95 within 0.02 yr at 1.4× the speed); T119 improves climatology only at 3.5× cost | [09](docs/outputs/09_resolution/output.md) |
| 10 | Production tracer set (3 clocks, pulses, sources, N2O/CFC-11-like), 6-hourly instantaneous output, Gregorian calendar; 2005–2009 review then **1990–2019** | 30 years in ~15 h, 2.3 TB; pulses gone in 2–3 yr, sources equilibrate in < 1 yr; value-imposing tracers must leave the mass fixer; **the mesosphere is never ventilated**: age 23 yr and flat in latitude above 1 hPa, stratosphere 3–5× too old and still growing, N2O isopleths ~6 km too low | [10](docs/outputs/10_production/output.md) |
| 11 | Tracer lid above 1 hPa (relax to WACCM age/state), unit amplitudes, sharp-edged twins, no surface sink; A (no sink) vs B (lid sink) 1990–1994 | Clocks bounded (max 5.4 yr) but 20–1 hPa fills from the lid, tropical 55 hPa age 2.7 yr vs CLaMS 1.3 and creeping; N2O/CFC-11 depletion unchanged, so it is made inside the stratosphere; **A chosen**, extension 1995–2009 running | branch `phase11-lid-tracers` |
| 12 | Circulation tests vs a control: QBO nudging off; strat81 (full L95 troposphere); w* and age (surface and 500 hPa clocks) before/after | running (three 5-yr chains 1990–1994) | branch `phase12-circulation` |

Phase 5 of the plan (consolidate and hand off, docs only) has no run of its own: its content is the per-phase records, the PDFs and this file.

## Headline table

Simulated days per wall-clock hour on one H100 (GPU 0), stepping / end-to-end (end-to-end includes JIT
compile and output writing). The running version with every run is the throughput table in
[PROGRESS.md](PROGRESS.md).

| Configuration | Grid | dt | simulated days / hour (1× H100) | notes |
|---|---|---|---|---|
| JCM full ECHAM physics (reference) | T63L95 | 12 min | 51.6 (582 ms/step) | Phase 0 baseline; 51.9 at dt = 15 min |
| stripped, dry Held-Suarez | T63L95 | 12 min | 5,787 / 2,368 | Phase 1 |
| + ERA5 nudging below 150 hPa | T63L95 | 12 min | 5,454 / 2,326 | Phase 2 |
| + passive tracers (age of air etc.) | T63L95 | 12 min | 4,458 / 2,082 | Phase 3; clock excluded from the mass fixer |
| same, 5 years 2005–2009 (five chained segments) | T63L95 | 12 min | 4,315 / 1,768 | Phase 4; 10.4 min per year, 30 yr ≈ 5.2 GPU-h |
| + Polvani-Kushner stratosphere (seasonal, tau 15 d) | T63L95 | 12 min | 4,445 / 2,012 | Phase 6 chosen configuration |
| reference: full ECHAM physics + the same nudging | T63L95 | 12 min | 140 / 131 | Phase 6 reference year (GPU 1, 12-hourly target) |
| Phase 6 configuration at dt 30 min | T63L95 | 30 min | 10,432 / 1,891 | Phase 7; Antarctic jet 18 % weaker, not adopted |
| + QBO nudging to ERA5 (window to 1 hPa) | T63L95 | 12 min | 3,890–3,930 / 1,872–1,904 | Phase 8b; −13 % for the zonal-mean reduction; tau 1 d costs nothing more |
| same on **strat63** (63 levels, stratosphere = L95) | T63 strat63 | 12 min | 5,374 / 1,750 | Phase 9, recommended grid; 5-yr chain in 65 min |
| same on strat47 | T63 strat47 | 12 min | 6,228 / 1,948 | Phase 9 throughput option; costs QBO amplitude and 0.1 yr aloft |
| same at T85L95 (dt 9) / T119L95 (dt 6, the 1° grid) | T85 / T119 | 9 / 6 min | 1,636 / 847 and 557 / 403 | Phase 9; no change in transport |
| production: 15 tracers, omega, 6-hourly instantaneous output | T63 strat63 | 12 min | 4,760 / 860 | Phase 10; output-bound, ~26–30 min per year, 30 yr in ~15 h and 2.3 TB compressed |
| production + tracer lid, 24 tracers, two chains sharing the CPU output path | T63 strat63 | 12 min | 4,180 / 750 | Phase 11; 31 min per year per chain |

## Upstreams

- JCM: https://github.com/climate-analytics-lab/jax-gcm (branch `dev`), docs
  https://jax-gcm.readthedocs.io/en/development/
- Dinosaur semi-Lagrangian: https://github.com/neuralgcm/dinosaur/pull/135 (shoyer fork,
  branch `semi-lagrangian`)
- Reference coupler this is measured against: https://github.com/reflective-org/AIDE-SAI-link

License: Apache-2.0 (same as JCM and Dinosaur).
