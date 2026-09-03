# jcm-strat

**A stratosphere-only configuration of JCM on the Dinosaur semi-Lagrangian dycore, for fast
stratospheric tracer transport.** This is *Approach A* from the 2026-08-31 planning meeting:
run the physics dycore with tropospheric physics stripped out, nudge the troposphere to ERA5,
leave the stratosphere free, and measure how fast the simplest possible physics solve can be.
That number is the baseline against which the ML-emulator route (Approach B, PARADIS) is judged.

Status: **Phases 0–4 done.** The Phase-1 number is in: one simulated year in 10.4 minutes on one H100 at T63L95 (30 years ≈ 5.2 GPU-hours), passive-tracer mass closed to 0.02 % over five years; age-of-air pattern right but the tropics 1.5 yr too old and no polar-night jet with Held-Suarez in place of radiation. Next: the stratospheric forcing (issues #5 Polvani-Kushner, #2 RRTMGP). See [PROGRESS.md](PROGRESS.md) and [docs/outputs/04_5yr/output.md](docs/outputs/04_5yr/output.md).

## What this repo is, and is not

- It is a **Hydra config overlay** on the installed `jcm` package plus one small physics term
  (passive tracers). JCM's source is never edited; upgrading JCM is a submodule SHA bump.
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
`strat_<session>`, on **GPU 0 only**, one at a time, writing to `runs/<session>/`.

## Unattended pipeline

`scripts/pipeline.sh` runs the remaining plan steps (runs, plots, output records, commits, PRs)
one after another in the tmux session `strat_pipeline`, so the session that started it can be
closed. Check on it with:

```bash
tmux ls                                  # strat_pipeline present = still running
tail -f runs/pipeline.log                # one line per step
tmux attach -t strat_pipeline            # live console (C-b d to detach)
gh pr list --repo reflective-org/jcm-strat
```

It skips steps whose outputs exist, so after an interruption just start it again.

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
| `docs/background/` | The handover document this work started from |

## Headline table

Filled in as phases complete (see PROGRESS.md for the running version).

| Configuration | Grid | dt | simulated days / hour (1× H100) | notes |
|---|---|---|---|---|
| JCM full ECHAM physics (reference) | T63L95 | 12 min | 51.6 (582 ms/step) | Phase 0 baseline; 51.9 at dt = 15 min |
| stripped, dry Held-Suarez | T63L95 | 12 min | — | Phase 1 |
| + ERA5 nudging below 150 hPa | T63L95 | 12 min | — | Phase 2 |
| + passive tracers (age of air etc.) | T63L95 | 12 min | 4458 stepping, 2082 end-to-end | Phase 3; clock excluded from the mass fixer |
| same, 5 years 2005–2009 (five chained segments) | T63L95 | 12 min | 4315 stepping, 1768 end-to-end | Phase 4; 10.4 min per year, 30 yr ≈ 5.2 GPU-h |

## Upstreams

- JCM: https://github.com/climate-analytics-lab/jax-gcm (branch `dev`), docs
  https://jax-gcm.readthedocs.io/en/development/
- Dinosaur semi-Lagrangian: https://github.com/neuralgcm/dinosaur/pull/135 (shoyer fork,
  branch `semi-lagrangian`)
- Reference coupler this is measured against: https://github.com/reflective-org/AIDE-SAI-link

License: Apache-2.0 (same as JCM and Dinosaur).
