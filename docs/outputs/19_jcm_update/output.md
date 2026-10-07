# Phase 19 — jcm update (PR #1027 fixes), precision check, 19d baseline (13d physics, nudged < 400 hPa, new jcm)

Status: **running** (pipeline `scripts/phase19_run.sh`, tmux `strat_p19_run`, GPU 4, launched 2026-10-07 12:02 PDT).
Sections 19a-19c and the precision gate are written by the set-up session; the 19d Results are filled in by the
pipeline's write-up agent. Every decision with its options: [decisions.md](decisions.md).

## Why

A colleague found that jax-gcm PR #1027 (merged 2026-10-05, 1d444197) fixed Lott-Miller SSO (`nktopg=1` made the
"low-level" state a whole-column mean; drag ~100x too strong), removed its land-fraction factor, and replaced the upper
sponge (10 levels, full wind, T relaxed to `target_T_K` 250 K) with ECHAM's `uspnge` (top level, 3 h, m != 0 only). Our
pin 849893be had all of it; Phases 12 run 4, 13 (GWD) and 14 used the broken Lott-Miller. Updating jcm drags in
dinosaur >= 1.5.0, whose bf16 GPU dots are miscompiled by our jaxlib 0.10.2 (NH -> SH mass drift) unless jcm #892's
override is active. Phase 19 updates jcm, checks the precision explicitly, ports jcm-strat, and reruns the 13d physics
with nudging below 400 hPa (= Phase 13c run 2 on the old jcm) to measure the update's effect alone (19d).

## 19a — environment

| item | old (Phases 1-18) | new (Phase 19) |
|---|---|---|
| jax-gcm | 849893be (2.1.0b0) | **35dc1997** (origin/dev 2026-10-06, 3.0.0rc1; contains 1d444197 #1027 and 4dbe734d #892) |
| dinosaur | shoyer/dinosaur@semi-lagrangian bd99e39 (git submodule, 1.4.0) | **1.5.0 from PyPI**, exact pin (submodule removed) |
| jax / jaxlib | 0.10.2 | 0.10.2 (pinned; jcm caps < 0.11) |
| venv | main checkout `.venv` (shared by the old worktrees) | own `.venv` in `/data/JCM_stripped/jcm-strat-phase19` |

`scripts/bootstrap_env.sh` and `scripts/check_env.sh` updated; check_env: all PASS on GPU (2026-10-07 11:05 PDT).

## 19b — precision check (jcm #892)

1. **Where the algorithms live** (`grep -n DOT_ALGORITHM` in the installed dinosaur 1.5.0, [p19b_grep_dot_algorithm.txt](p19b_grep_dot_algorithm.txt)):
   `jax_numpy_utils.py:36 FLOAT32_DOT_ALGORITHM = lax.DotAlgorithmPreset.BF16_BF16_F32_X6`, used at `:120`;
   `spherical_harmonic.py:47 FAST_TRANSFORM_DOT_ALGORITHM = jax.lax.DotAlgorithmPreset.BF16_BF16_F32_X3`, used at `:429`.
2. **In our entry point**: `jcm_strat/main.py` imports `jcm.main` (and with it `jcm.dycore.dinosaur`, which applies the
   override) before any jcm_strat term, calls `apply_dot_precision_workaround()` once more (idempotent), and prints both
   values before the model build and again after `jcm.runners.build_model` returns; it refuses to run if either is not
   `Precision.HIGHEST` on an affected jaxlib. Every log of Phases 19-21 carries, twice:
   `jcm_strat: dinosaur dot precision FLOAT32_DOT_ALGORITHM=HIGHEST FAST_TRANSFORM_DOT_ALGORITHM=HIGHEST (jaxlib 0.10.2, affected by the bf16 miscompile: True)`.
3. **jcm's `dot_precision_test.py` on GPU 0**: 7 passed, including the GPU-only single-level inverse-transform regression
   test ([p19b_dot_precision_test.log](p19b_dot_precision_test.log)).
4. **30-day gate** on the 19d spin-up month (1989-12-01 + 31 d, the 19d configuration exactly): change of the NH-SH
   area-mean surface pressure and of the global mean from the first 6-hourly sample. **PASS**: max |dNH-SH| 2.17 hPa
   (end -1.21), max |dglobal| 0.07 hPa (end +0.04); the old jcm with the same physics (January 1990) swings by 2.16 /
   0.13 hPa. The bug's signature is -116 hPa in 30 days. Details: [p19_ps_gate.md](p19_ps_gate.md).

   ![ps gate](p19_ps_gate.png)

## 19c — port to jcm 3

pytest 99 passed after the port (82/89 passed before it). What broke and how it was fixed (details and options in
decisions.md):

- `run.start_date` -> `run.start_time` — **silent** in jcm 3 (an unknown key; the run would have started on 2000-01-01).
  `jcm_strat.main` now refuses `run.start_date` and `run.sponge.target_T_K`.
- One Gregorian clock in jcm 3; `calendar: gregorian` is kept as a checked key (anything else refused).
- `run=longrun` writes calendar-month means only; the base experiments set `monthly_means: false, save_chunks: true` so
  the 6-hourly `longrun_day<N>.nc` chunks every diagnostic reads are written as before.
- Sponge: jcm 3's `UpperSponge` is ECHAM's `uspnge`; all experiments use `run.sponge.levels: 1` with ECHAM's 3 h and
  enspodi 1; the old remapped strat63/strat81 sponge (4 levels, enspodi 6.73, full wind, T -> 250 K) is gone.
  `dycore.sl_vertical_interpolation: null` (= cubic, jcm 3's default; was linear). Both echoed in every run header.
- `forcing.ozone_file: auto` now fails for the strat tables (no on-grid bundle); `analytic`, what jcm 2 used silently.
- jcm 3's ECHAM package gained `echam_surface_exchange`; added to our full-physics term lists (Phase 21).
- Unchanged: the tracer mass-fixer policy wrapper, Hines/Lott-Miller import paths, the L95 table (so the ERA5 window
  hashes and the cached 1990-1999 windows are reused), `jcm.data.era5`.
- Also new in jcm 3 and part of "the update's effect": dinosaur 1.5's hybrid-coordinate temperature equation, virtual
  temperature in the hybrid dynamics (the dry runs carry ERA5's initial humidity passively), a mass fixer on specific
  humidity, the nodal-tracer fixer factor clipped to [2/3, 1.5].

**Spin-up** (Susanne's request): every chain starts 1989-12-01 from ERA5 and runs 31 days (`runs/<prefix>_spinup_19891201`,
QBO target year 1989, not linked into the aggregate, so excluded from every diagnostic); the 1990 segment starts from its
checkpoint with `first_segment=true`, which now also restarts the clocks, sources and `sai` at 0 on the first step (the
identity without a spin-up). Verified: smoke restart and the real 1990 segments read 0.250 d on the clocks at 06 UTC
1 January. Smokes (5 d) of all four Phase 19-21 configurations passed on 2026-10-07.

## 19d — Results

*(to be written by the pipeline's write-up agent from update_metrics.md, vs13d_metrics.md, p19_mesosphere.md, scores/)*
