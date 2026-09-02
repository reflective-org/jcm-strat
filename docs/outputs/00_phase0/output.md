# Phase 0 — environment and baseline

Status: in progress (2026-09-02).

## What was done

1. Repository created at `/data/JCM_stripped/jcm-strat` (GitHub: `reflective-org/jcm-strat`).
2. Upstreams pinned as submodules:
   - `external/jax-gcm` @ `849893b` — climate-analytics-lab/jax-gcm, branch `dev`, 2026-09-01
   - `external/dinosaur` @ `bd99e39b` — shoyer/dinosaur, branch `semi-lagrangian`, 2026-08-24
3. `uv` 0.12.9 installed to `~/.local/bin` (the only file this project puts on the root disk).
4. `scripts/bootstrap_env.sh` run; log in `bootstrap_env.log` beside this file.

## Environment acceptance (`scripts/check_env.sh`)

_pending_

## Smoke runs

_pending_

## Baseline throughput (stock JCM, full ECHAM physics, T63L95, 10 days)

_pending_

## Decisions taken in this phase

See KEY_DECISIONS.md rows 1–4, 11, 12.
