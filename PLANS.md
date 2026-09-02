# Plan: `jcm-strat` — Approach A, a stripped-down stratosphere model on JCM / Dinosaur-SL

Supersedes `/data/JCM_stripped/jcm-strat_APPROACH_A_PLAN.md` (the earlier, denser draft). This
version is deliberately streamlined: **Part 1** is the shortest path to a running, validated,
timed model with passive tracers; **Part 2** is everything else, filed as GitHub issues on day one.

## Context

We want to know how fast the *simplest possible physics solve* for stratospheric tracer
transport can be, before deciding whether the ML emulator (Approach B) is worth building. The
2026-08-31 meeting split the work: Approach A (this repo) runs the physics dycore with
tropospheric physics stripped out and the troposphere nudged to ERA5; Approach B retrains
PARADIS. You own Approach A only.

Approach A also fixes two known problems of the current AIDE-SAI-link setup: the fixed 150 hPa
domain boundary becomes a dynamical tropopause, and the polar pull-up problem goes away because
vertical motion comes from mass continuity in a real dycore.

**Vehicle:** JCM (`climate-analytics-lab/jax-gcm`, branch `dev`, v2.1.0b0) on the Dinosaur
semi-Lagrangian dycore (`shoyer/dinosaur@semi-lagrangian`, open PR neuralgcm/dinosaur#135,
dinosaur 1.4.0). Verified against the live `dev` tree (SHA `849893b`, 2026-09-01):

- Semi-Lagrangian transport is unconditional in JCM's dinosaur backend
  (`jcm/dycore/dinosaur/dycore.py: _require_semi_lagrangian`), tracers are stored on the grid
  ("nodal") and a **global proportional mass fixer already exists and is on by default**
  (`_fix_nodal_tracer_mass`, Diamantakis & Flemming 2014). No conservation code is needed in
  Phase 1.
- The ECHAM physics is a flat YAML list of 12 terms (`jcm/config/physics/echam.yaml`); a
  stripped physics is a YAML made by deletion. `physics=held_suarez` is a single term that is
  already hybrid-grid aware.
- `nudging=era5` exists (`jcm/config/nudging/era5.yaml`: `tau_hours`, `pbl_levels`,
  `nudge_temperature`, `min_pressure_hpa`, `freq`) and is appended to *any* physics by the
  runner (`jcm/runners.py: maybe_add_nudging`). ERA5 comes from WeatherBench2 (6-hourly,
  1959–2023, 13 levels 50–1000 hPa, clamped above 50 hPa → no usable target above ~60 hPa).
- `grid=echam_t63_l95_hybrid` (ECHAM6 middle-atmosphere grid, lid ~0.01 hPa) exists and is
  validated with full physics (52 days/hr on one A100 with radiation on).
- No age-of-air tracer exists anywhere in JCM. A tracer is declared by a `PhysicsTerm` via
  `required_tracers() -> (TracerSpec(...),)` (`jcm/physics/physics_term.py:27`); this is the
  only new physics code in Part 1.

**Environment facts that shape the plan**

- Only the semi-Lagrangian Dinosaur on this machine is inside a colleague's venv under
  `/home/ubuntu/noah/` — off limits. `/data/jax-gcm-fork` is a stale June 2026 `main`
  snapshot without SL, L95, nudging or ERA5. **We build our own environment from `dev`.**
- System Python is 3.10; JCM needs ≥ 3.11. `uv` is available but we install our own.
- Root disk `/` is 97 % full (15 GB free); `/data` has 42 TB free. **Everything** (repo, venv,
  uv/HF/ERA5/JAX caches, runs) lives under `/data/JCM_stripped/jcm-strat/`; nothing in `$HOME`.
- 8× H100, no scheduler, shared machine. **This project uses GPU 0 only; GPUs 1–7 stay free.**
  `launch.sh` hard-codes `CUDA_VISIBLE_DEVICES=0` and refuses to start if a `strat_*` tmux
  session is already running, so runs are strictly sequential. Every run is a detached tmux
  session (`/data/CLAUDE.md` convention; new prefix `strat_*`).
- `gh` is authenticated as `susannebaur`; AIDE-SAI-link lives in `reflective-org`.

## Decisions taken (with you, 2026-09-02)

| Decision | Choice |
|---|---|
| Repo name | **`jcm-strat`**, package `jcm_strat` (alternatives considered: `strat-sd`, `jcm-strat-transport`, `fast-strat`) |
| Location | GitHub `reflective-org/jcm-strat`; disk `/data/JCM_stripped/jcm-strat` (venv, caches and runs inside it) |
| GPUs | **GPU 0 only**; GPUs 1–7 remain free; all runs sequential |
| Per-step record | every phase ships a tracked `docs/outputs/<NN_phase>/output.md` with its plots |
| Phase-1 grid | **T63L95** (existing, validated); a ~30-level grid is a Part-2 issue |
| Stratospheric temperature with radiation off | **Held-Suarez relaxation as-is**; RRTMGP option filed as an issue |
| Tropospheric nudging | **winds + temperature**, τ = 6 h |
| Nudging cutoff | **150 hPa hard cutoff for now** (`min_pressure_hpa: 150`, one YAML line, easy to change); issue filed: must become a dynamical tropopause, not a hard cutoff |
| ERA5 period | **2005–2009** (quiet volcanically, overlaps CLaMS 2004–2023, three observed SSWs) |
| Age-of-air source region | **whole troposphere, p > 700 hPa** (comparable to `/data/CLaMS`, `/data/CESM2_REFD1_AOA`) |

House rules applied throughout: each phase is one PR for your review; subtasks are
commit-sized; commit/PR text does not mention Claude; the seven docs (README, ARCHITECTURE,
PROGRESS, PLANS, KEY_DECISIONS, DEFERRED, FEATURES) are kept current in every PR.

**Per-step output record.** Every phase writes `docs/outputs/<NN_phase>/output.md` — what was
run (exact CLI, SHA, GPU, wall-clock), what came out (numbers against the acceptance
thresholds), the plots (PNG files beside it, tracked in git via a `!docs/outputs/**` exception
to the `*.png` ignore rule), and what was decided as a result. `runs/` stays gitignored; the
scripts copy the final figures from `runs/<session>/` into `docs/outputs/`.

---

# Part 1 — The simplest possible path (6 PRs)

Goal of Part 1, "the Phase-1 number":

> The stripped JCM on Dinosaur-SL, ERA5-nudged below 150 hPa, runs **N simulated years/day on
> one H100**, with passive-tracer mass closing to **< 0.5 %/yr**, exact non-negativity, and a
> 5-year age-of-air field whose latitude/height pattern matches CLaMS.

Launch convention for every run below:

```bash
scripts/launch.sh <session> <hydra overrides...>
# refuses if any strat_* tmux session exists (one run at a time), then
# = tmux new-session -d -s strat_<session> 'source scripts/env.sh && CUDA_VISIBLE_DEVICES=0 \
#     python -m jcm.main --config-dir /data/JCM_stripped/jcm-strat/jcm_strat/config <overrides> \
#     hydra.run.dir=/data/JCM_stripped/jcm-strat/runs/<session> 2>&1 | tee runs/<session>/log.txt'
```

## PR 1 — Phase 0: repository, environment, reproduce the known-good (no model code)

Commits:

1. **Repo skeleton.** `git init` at `/data/JCM_stripped/jcm-strat`, layout below,
   `pyproject.toml` for `jcm_strat`, `.gitignore` (`runs/`, `cache/`, `scratch/`, `.venv/`,
   `*.nc`, `*.npz`, `*.png`, with `!docs/outputs/**` so the per-step plots are tracked), the
   seven doc files with one paragraph each, `docs/outputs/00_phase0/output.md` started,
   `LICENSE` (Apache-2.0, same as JCM). Create the GitHub repo in `reflective-org` with
   `gh repo create`. Move the two existing documents in `/data/JCM_stripped/` (handover,
   earlier draft plan) into `docs/background/` so the folder holds only the repo.
2. **Pinned upstreams as submodules.** `external/jax-gcm` @ `849893b` (dev), `external/dinosaur`
   @ `bd99e39b` (semi-lagrangian branch head, 2026-08-24). Why: JCM's `requirements.txt`
   tracks the Dinosaur *branch by name*, so an unpinned install is not reproducible (a
   colleague's env resolved `f7a44f68`; the head has since moved).
3. **`scripts/bootstrap_env.sh`** (~60 lines): install `uv` to `~/.local/bin` (58 MB, the
   only thing on the root disk); export `UV_CACHE_DIR=$REPO/cache/uv`,
   `UV_PYTHON_INSTALL_DIR=$REPO/cache/uv-python` with `REPO=/data/JCM_stripped/jcm-strat`;
   `uv python install 3.11`; `uv venv $REPO/.venv`; install in this order:
   `-e external/dinosaur`, then `-e "external/jax-gcm[era5]"` with the dinosaur requirement
   overridden onto the submodule (`--override overrides.txt`; fallback `--no-deps` + explicit
   requirements minus the dinosaur line), then `jax[cuda12]` (JCM does not pin `jax`, so pip
   would otherwise install the CPU wheel), then `-e .`. Freeze to `env/requirements.lock`.
4. **`scripts/env.sh` + `scripts/launch.sh` + `scripts/check_env.sh`.** `env.sh` activates the
   venv and exports `HF_HOME=$REPO/cache/huggingface`, `JCM_ERA5_CACHE=$REPO/cache/era5`,
   `SCRATCH=$REPO/scratch` (JCM puts its JAX compilation cache in `$SCRATCH/jcm-jax-cache`),
   and `CUDA_VISIBLE_DEVICES=0`. `launch.sh` has no GPU argument; it exits with an error if
   `tmux ls` shows any `strat_*` session or if `nvidia-smi` shows a process on GPU 0.
   `check_env.sh` asserts: exactly one `CudaDevice` visible under `env.sh`;
   `jcm.dycore.dinosaur.dycore.semi_lagrangian_available()` is True;
   `dinosaur.__version__ == 1.4.0` and its `direct_url.json` points at the submodule;
   `jcm.__version__ == 2.1.0b0`; `df /` unchanged after bootstrap.
5. **Smoke runs (stock JCM, nothing of ours).**
   `physics=held_suarez grid=held_suarez_t31_l8 run=smoke` and
   `physics=echam grid=echam_t63_l95_hybrid run=smoke terrain=from_file forcing=from_file`
   with the `hf://bundles/t63/...` boundary files (exact HF paths confirmed here and recorded
   in KEY_DECISIONS). This warms the HF cache.
6. **Baseline timing + issues.** 10-day `physics=echam grid=echam_t63_l95_hybrid run=longrun`
   on GPU 0 → `scripts/throughput.py` (~40 lines) parses the log and appends a
   `simulated days/hr` row to `PROGRESS.md`. Then file all Part-2 GitHub issues with labels.

Acceptance: `check_env.sh` passes; both smoke runs finish; resolved configs (`--cfg job`)
committed under `docs/resolved_configs/`; one throughput row (expect ≥ 52 days/hr, the A100
number; an H100 should be faster — lower means the environment is wrong, e.g. CPU JAX).
Plot: a throughput bar chart that every later phase adds a bar to.

## PR 2 — Phase 1: strip the physics — dry Held-Suarez on the L95 high-top grid

Commits:

1. **Overlay config dir** `jcm_strat/config/` with `physics/strat_dry.yaml` (Held-Suarez only,
   a copy of JCM's `held_suarez.yaml` so it is ours to extend) and
   `experiment/p1_dry.yaml` (`# @package _global_`; sets `grid: echam_t63_l95_hybrid`,
   `run: longrun`, `init: jw`, `terrain: from_file` + HF path, `nudging: none`). How the overlay
   works: Hydra's `--config-dir` adds our directory to the config search path, so
   `physics=strat_dry` and `+experiment=p1_dry` resolve from our tree while every other group
   comes from the installed `jcm.config`. **JCM source is never edited**; a JCM upgrade is a
   submodule SHA bump.
2. **30-day run.** If `ComposablePhysics._validate_ordering` raises a missing `requires` key,
   add the minimal provider term and record why in KEY_DECISIONS. Note: Held-Suarez has never
   been run on 95 levels to 0.01 hPa in JCM; the `run=longrun` sponge (10 levels,
   `target_T_K=250`) is what keeps the top alive.
3. **`scripts/plot_zonal_mean.py`** (~120 lines): zonal-mean u and T (lat × log-p,
   1000 → 0.01 hPa) for the model and for the ERA5 monthly tape at
   `/home/susanne/docs/AIDE-atmosphere_validation/AIDE-atmosphere/output/era5_monthly_tape.nc`,
   plus a difference panel; time series of global-mean surface pressure and kinetic energy.
4. **Gravity-wave drag A/B.** `physics/strat_dry_gwd.yaml` = Held-Suarez + `hines_gwd` +
   `lott_miller_sso` (+ `moist_air_state` if their `requires` demand it). The handover is
   explicit: without GWD a coarse stratosphere has a too-strong polar-night jet and a cold
   pole, both of which change the Brewer-Dobson circulation and hence aerosol lifetime. Run
   both for one year, one after the other on GPU 0; keep whichever is closer to ERA5 as the
   default and say why in KEY_DECISIONS and `docs/outputs/01_dry/output.md`.
5. **Throughput row** for the bare stripped model — the upper bound on Approach A's speed and
   the honest answer to "how much does stripping buy".

Acceptance: 365 days, no NaN; global-mean p_s drift < 0.1 hPa; subtropical jets present;
top-level zonal-mean |dT/dt| over the last 60 days < 0.5 K/day; throughput ≥ 2× the PR-1
baseline.
Plots: DJF/JJA zonal-mean u and T (model / ERA5 / diff), GWD-on vs GWD-off side by side; p_s
and KE time series.

## PR 3 — Phase 2: specified dynamics — nudge the troposphere to ERA5

Commits:

1. **Prefetch ERA5 2005** in tmux (`preproc_era5_2005`):
   `python -m jcm.data.era5 --grid echam_t63_l95_hybrid --start 2004-12-31 --end 2006-01-02 --init`.
   Record cache size (expect > 15 GB/yr at L95; the target stays resident in RAM — fine with
   1 TB, but note it).
2. **`experiment/p2_sd.yaml`**: `init: era5`, `nudging: era5` with `tau_hours: 6`,
   `pbl_levels: 2`, `nudge_temperature: true`, **`min_pressure_hpa: 150`**, `freq: 6h`,
   `run.start_date: 2005-01-01`. The cutoff is one YAML key by design; a comment points at the
   dynamical-tropopause issue.
3. **90-day check run, then 1-year run** (2005). The winds-only comparison
   (`nudging.nudge_temperature=false`) is filed as issue 15 rather than run now, so GPU 0 stays
   on the main line.
4. **`scripts/plot_nudging_check.py`** (~100 lines): RMSE(u, T) vs ERA5 per level (should be
   small below 150 hPa, unconstrained above); WMO lapse-rate tropopause pressure vs latitude
   from the model's own T vs ERA5 — this is the replacement for the fixed 150 hPa cutoff;
   polar-vortex u(60°N, 10 hPa) daily vs ERA5, reusing the diagnostics in
   `/home/susanne/docs/AIDE-atmosphere_validation`.
5. **Throughput row** (nudging is I/O, expect within 10 % of Phase 1).

Acceptance: 365 days stable; 500 hPa zonal-mean u RMSE vs ERA5 < 3 m/s and T < 3 K; no kink
in the zonal mean at 150 hPa; tropopause pressure vs latitude within ±30 hPa of ERA5; the
2006 January SSW visible as a vortex weakening.
Plots: RMSE-by-level profile; zonal-mean u DJF model/ERA5; tropopause pressure vs latitude;
u(60°N, 10 hPa) time series.

## PR 4 — Phase 3: passive tracers (the only new physics code)

Commits:

1. **`jcm_strat/tracers.py`: `PassiveTracers(PhysicsTerm)`** (~100 lines), modelled on
   `jcm/physics/held_suarez/held_suarez_physics.py`. `required_tracers()` declares four
   `TracerSpec`s (all `nondimensionalize=False`):
   - `aoa` — clock tracer, units s: tendency +1 s/s everywhere, relaxed to 0 on a short
     timescale where p > 700 hPa (physics terms return tendencies, so "reset" is a strong
     relaxation, τ ≈ one time step).
   - `unity` — constant 1, no tendency: exposes any local non-conservation of the SL scheme
     that the global mass fixer hides.
   - `pulse` — initial box 15°S–15°N, 20–25 km, value 1, no source: an SAI-like plume.
   - `e90` — surface source, 90-day e-folding sink (Prather et al. 2011): a tropopause marker.
   Check how `PhysicsTendency` converts tracer tendencies with `nondimensionalize=False`
   before trusting units (one unit test does this).
2. **`physics/strat_passive.yaml`** = the chosen Phase-1 physics + `passive_tracers` term;
   `experiment/p3_tracers.yaml` = `p2_sd` + this physics.
3. **`tests/test_tracers.py`** (~50 lines, CPU): one step gives `aoa = dt` above the reset
   layer and ≈ 0 below; `unity` unchanged; `e90` decays at the right rate.
4. **`scripts/tracer_budget.py`** (~80 lines): global mass-weighted burden time series for all
   four tracers; min/max of `unity`; polar-cap top-level column of `pulse` (the pull-up check).
5. **1-year run (2005)** with 5-day saves on GPU 0; throughput row.

Acceptance: `unity` within 1 ± 1e-3 everywhere after 1 yr; `pulse` global burden drift
< 0.5 %/yr; cell minimum of every tracer exactly ≥ 0; `aoa` ≈ 1 yr in the lowest
stratosphere with the tropical-pipe minimum visible; `e90` 90-ppb contour tracks the
dynamical tropopause from PR 3; no polar-cap maximum of `pulse` at the top level.
Plots: burden time series (4 tracers); zonal-mean `aoa` and `pulse` at month 12; `unity`
deviation map at 10 hPa.

## PR 5 — Phase 4: the 5-year run and the Phase-1 number

Commits:

1. **Prefetch ERA5 2006–2009**, one tmux job per year.
2. **`experiment/p4_5yr.yaml`** (`run.checkpoint_path`, `chunk_days: 30`, `total_time`
   1826 days); launch 2005–2009 on GPU 0. The time-step comparison is issue 3, run after this
   finishes.
3. **`scripts/aoa_vs_clams.py`** (~120 lines): zonal-mean mean age at year 5 vs CLaMS
   (`/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip`, same years) and WACCM6 REF-D1
   (`/data/CESM2_REFD1_AOA`); latitude profiles at 20 and 30 km; tropical vertical profile.
   Five years is not equilibrated (mean age needs ~10 yr) — this is a *pattern* check, stated
   as such.
4. **Vortex / SSW diagnostics** for 2005–2009: do the ERA5 SSWs (Jan 2006, Feb 2008, Jan 2009)
   appear in the free stratosphere driven only by the nudged troposphere?
5. **Headline table** in README and PROGRESS: simulated years/day, GPU-hours per 30 years,
   tracer drift over 5 yr, AoA bias, vortex statistics; throughput chart PR 1 → PR 5.

Acceptance: 5 years complete; tracer drift per PR-4 thresholds; AoA latitude gradient has
the right sign and the tropical/extratropical contrast is within 50 % of CLaMS; at least 2
of the 3 ERA5 SSW winters show a weakened vortex.
Plots: AoA zonal-mean triptych (model / CLaMS / WACCM); AoA at 20 km vs latitude; u(60°N,
10 hPa) for five winters vs ERA5; throughput bars.

## PR 6 — Phase 5: consolidate and hand off (docs only)

1. KEY_DECISIONS complete (every choice above with its reason), DEFERRED = Part 2 with issue
   links, FEATURES, ARCHITECTURE (overlay diagram), PLANS (this document, updated).
2. Reproducibility check: fresh clone into a scratch path + `bootstrap_env.sh` + `launch.sh`
   of `p3_tracers` for 10 days reproduces the PR-4 burden series to float tolerance.
3. Update `/data/CLAUDE.md` tmux prefix table with `strat_*` (separate tiny PR there).

Acceptance: a second person can reproduce a 10-day run from the README alone.

Expected pace: PR 1–2 in week 1, PR 3–4 in week 2, the 5-year run in the background of
week 3.

---

# Part 2 — Add complexity later (GitHub issues, filed in PR 1)

Ordered by value. Each is one issue; none is started before PR 5 is merged.

| # | Issue | Label | Notes |
|---|---|---|---|
| 1 | **Dynamical nudging cutoff** *(you asked for this)* | `feature` | Replace the hard `min_pressure_hpa` mask with a mask that follows the model's own WMO tropopause (lat- and time-dependent) plus a smooth taper; needs a per-column `inv_tau` instead of JCM's `(nlev,)` profile (`jcm/nudging.py: NudgingConfig`, `jcm/runners.py: _nudging_inv_tau`), ~120 lines. Interim step: per-level tanh taper 200 → 100 hPa. |
| 2 | **RRTMGP radiation with prescribed trace gases** *(you asked for this)* | `feature` | Add `rrtmgp_radiation` + `simple_chemistry` + `echam_boundary_conditions` (+ what their `requires` need) back into the stripped YAML; O3/CO2/CH4 are prescribed already. Gives the stratosphere its own radiative equilibrium so Held-Suarez no longer stands in for radiative damping. Radiation is the dominant cost, so measure both. |
| 3 | Time-step sweep 12 → 30 → 60 → 120 min on the PR-4 config | `research` | Report years/day vs AoA and vortex degradation. The SL PR reports a knee near 30 min. |
| 4 | Reduced ~30–44-level grid | `feature` | New level table in `jcm/physics/echam/echam_levels.py` (hardcoded 40/47/95) and a `(63, N)` entry in `jcm/diffusion.py: _ECHAM_LMIDATM_ORDERS` (unlisted counts silently fall back to uniform diffusion). Aim ≥ 20 levels over 150–1 hPa; sweep L30/L44 vs L95 on AoA. |
| 5 | Polvani-Kushner 2002 stratosphere | `feature` | Extend `HeldSuarez` with a winter polar-vortex equilibrium (~150 lines); a polar-night jet without radiation. |
| 6 | QBO nudging of tropical stratospheric u | `blocked` | Needs ERA5 above 60 hPa (WeatherBench2 stops at 50 hPa): CDS 37-level ingest (`~/.cdsapirc` exists) or a SPARC QBO tape. |
| 7 | Segment-parallel 30-year runs across 8 GPUs | `research` | Under specified dynamics, segments with 1–2 yr spin-up overlap are nearly independent; the only route to "hours". Needs a 2-segment overlap test first. |
| 8 | Local mass consistency (air-mass tracer, `tracer_filter` hook) | `research` | Only if PR-4's `unity` deviations are large; the global fixer is already on. Also expose `mass_fixer=False` on the CLI to record the unfixed drift. |
| 9 | MAM4 aerosol + SO2 injection | `feature` | `pip install 'jcm[mam4]'` (GPL extra, `mam4-jax==0.4.0`); strip the cloud-borne chain. |
| 10 | TOMAS from AIDE-SAI-link as a `PhysicsTerm` | `feature` | Fidelity check on size-distribution details. |
| 11 | Pinatubo 1991–1995 validation | `research` | Burden, AOD, e-folding vs SAGE/HIRS; thresholds agreed before the runs. |
| 12 | Shared benchmark vs AIDE-SAI-link (and later PARADIS) | `research` | Same 1-year injection, same diagnostics; AIDE reference is 34.9 s/step full physics (`/data/AIDE-SAI-link/MANIFEST.md`, 2026-08-28). |
| 13 | Upstream JCM PRs | `upstream` | `PassiveTracers` term, per-column nudging profile, new level tables. |
| 14 | Pin dinosaur to a release once PR #135 merges (JCM v2.1) | `upstream` | Drop the submodule + override for a version floor. |
| 15 | Winds-only vs winds+temperature nudging A/B | `research` | One extra 1-year run of the PR-3 config with `nudging.nudge_temperature=false`; deferred so GPU 0 stays on the main line. |

---

# Repository layout

```
jcm-strat/                         /data/JCM_stripped/jcm-strat, GitHub reflective-org/jcm-strat
  README.md  ARCHITECTURE.md  PROGRESS.md  PLANS.md  KEY_DECISIONS.md  DEFERRED.md  FEATURES.md
  LICENSE  pyproject.toml  .gitmodules  .gitignore  overrides.txt
  env/requirements.lock            uv pip freeze of the accepted environment (committed)
  docs/outputs/                    TRACKED per-step records: <NN_phase>/output.md + *.png
    00_phase0/  01_dry/  02_nudged/  03_tracers/  04_5yr/
  docs/background/                 handover + earlier draft plan (moved from /data/JCM_stripped)
  external/jax-gcm                 submodule @ 849893b (dev)
  external/dinosaur                submodule @ bd99e39b (semi-lagrangian)
  jcm_strat/
    __init__.py
    tracers.py                     PassiveTracers PhysicsTerm (PR 4)
    config/                        Hydra overlay, used via --config-dir
      physics/{strat_dry,strat_dry_gwd,strat_passive}.yaml
      experiment/{p1_dry,p2_sd,p3_tracers,p4_5yr}.yaml
  scripts/
    bootstrap_env.sh  env.sh  launch.sh  check_env.sh
    throughput.py  plot_zonal_mean.py  plot_nudging_check.py  tracer_budget.py  aoa_vs_clams.py
  tests/test_tracers.py
  docs/resolved_configs/           `--cfg job` output per experiment
  .venv/  cache/{uv,uv-python,huggingface,era5}/  scratch/  runs/     gitignored, all inside the repo dir
```

Not a fork of JCM: a config overlay plus one small installable package. JCM is under active
development on `dev`; following it must stay a one-line SHA bump.

---

# Verification (end-to-end)

| PR | Check | Pass |
|---|---|---|
| 1 | `scripts/check_env.sh`; two smoke runs; 10-day L95 full-physics timing | 8 CUDA devices, SL available, pinned SHAs; ≥ 52 days/hr; `df /` unchanged |
| 2 | 1-yr dry run, GWD A/B | no NaN; p_s drift < 0.1 hPa; top |dT/dt| < 0.5 K/day; ≥ 2× PR-1 throughput; zonal-mean plots vs ERA5 |
| 3 | 1-yr nudged run | 500 hPa u RMSE < 3 m/s, T < 3 K; no kink at 150 hPa; tropopause within ±30 hPa of ERA5; Jan-2006 SSW visible |
| 4 | `pytest tests/`; 1-yr tracer run | tests pass; `unity` 1 ± 1e-3; `pulse` drift < 0.5 %/yr; min ≥ 0; no polar top-level `pulse` maximum |
| 5 | 5-yr run | AoA pattern vs CLaMS; 2/3 SSW winters; headline table filled |
| 6 | fresh-clone reproduction | 10-day burden series reproduced |

Every run: `tmux ls` shows exactly one `strat_<session>`; `nvidia-smi` shows our process on
GPU 0 and nothing of ours on GPUs 1–7; log and `.hydra/` config saved in `runs/<session>/`;
the phase's `docs/outputs/<NN_phase>/output.md` is updated before the PR is opened.

# Open questions (do not block PR 1)

1. Segment-parallel execution across 8 GPUs (issue 7): scientifically acceptable, and with
   what spin-up overlap? This decides whether "30 years in hours" is the goal or "one GPU for
   about a day" is fine.
2. Minimum acceptable Δz in the 18–30 km aerosol layer, needed before issue 4 starts.
3. What counts as "realistic enough": one agreed number on age of air and one on vortex
   strength, before PR 5's run so the result is decided, not argued.
