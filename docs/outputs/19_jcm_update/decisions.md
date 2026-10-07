# Phase 19 decision log

Every question that came up while carrying out the Phase 19-21 brief
(`scratch/p19_agent/brief.md`, approved by Susanne 2026-10-07), with all options seen, the
choice and the reason. Append-only, times in PDT.

---

### 2026-10-07 10:45 PDT - Worktree layout for Phases 19-21
- Options: (a) one worktree per phase (jcm-strat-phase19/20/21, stacked branches); (b) everything
  in the phase19 worktree on one branch.
- Chosen: (a) branches `phase19-jcm-update` (off `phase18-heating` 292d458), `phase20-sso-fixed`,
  `phase21-fullphys-rerun`, BUT all three phases' runs launched from and living in the
  **phase19 worktree** (`runs/`), which owns the only new-jcm venv. The phase20/21 worktrees are
  created for their records/commits only and symlink `.venv` and `runs/` from phase19.
- Why: the new venv cannot be shared with older worktrees, building three new venvs (one per
  worktree) costs ~15 GB and three identical environments; Phase 20/21 code changes are configs
  only. Stacked branches keep the per-phase records reviewable as the brief asks.

### 2026-10-07 10:50 PDT - jax-gcm pin
- Options: origin/dev head 35dc1997 (2026-10-06 13:27 PDT); merge 1d444197 itself.
- Chosen: **35dc19974670044eb7ab8a3a8944a6143eae54eb** (jcm 3.0.0rc1). Contains 1d444197 (#1027)
  and 4dbe734d (#892) - checked with `git merge-base --is-ancestor`.
- Why: the brief says current origin/dev; 119 commits after our old pin 849893be.

### 2026-10-07 10:50 PDT - dinosaur: submodule or PyPI
- Options: (a) keep a submodule `external/dinosaur` re-pointed at the neuralgcm v1.5.0 tag;
  (b) PyPI `dinosaur==1.5.0` exact; (c) PyPI `dinosaur>=1.5.0` floating.
- Chosen: (b), exact `dinosaur==1.5.0` (the newest release), forced through `env/overrides.txt`;
  the `external/dinosaur` submodule is removed on this branch (older branches keep theirs).
- Why: the semi-Lagrangian core is upstream since 1.4.0, so the only reason for the git-branch
  submodule (a moving branch name) is gone; an exact PyPI pin is as reproducible as a SHA and
  needs no clone. Floating (c) would let a 1.5.1/1.6 change results silently.

### 2026-10-07 10:50 PDT - jax version
- Options: let the resolver choose; pin `jax[cuda12]==0.10.2`.
- Chosen: pin 0.10.2 (jax, jaxlib, cuda plugin) - jcm caps jax<0.11 and validates 0.10.2; our old
  env had 0.10.2, so the only dycore change is jcm + dinosaur. jaxlib 0.10.2 IS affected by the
  bf16 miscompile -> #892 override must be active (checked in check_env.sh and in every run header).

### 2026-10-07 11:15 PDT - 19b item 1: where DOT_ALGORITHM lives in dinosaur 1.5.0
- `grep -n DOT_ALGORITHM` on the installed package:
  `jax_numpy_utils.py:36 FLOAT32_DOT_ALGORITHM = lax.DotAlgorithmPreset.BF16_BF16_F32_X6`,
  `jax_numpy_utils.py:120 precision = FLOAT32_DOT_ALGORITHM`,
  `spherical_harmonic.py:47 FAST_TRANSFORM_DOT_ALGORITHM = jax.lax.DotAlgorithmPreset.BF16_BF16_F32_X3`,
  `spherical_harmonic.py:429 ... float32_algorithm=FAST_TRANSFORM_DOT_ALGORITHM`.
- No decision needed; recorded for output.md.

### 2026-10-07 11:15 PDT - 19b item 2: import order / where to echo the precision
- Options: (a) rely on `import jcm` (jcm.dycore.dinosaur applies the override at import);
  (b) also call `apply_dot_precision_workaround()` explicitly in jcm_strat.main; (c) (b) plus a hard
  refusal if either value is not HIGHEST on an affected jaxlib.
- Chosen: (c). `jcm_strat/main.py` imports `jcm.main` (-> jcm.dycore.dinosaur) before any jcm_strat
  term module, so (a) already holds; the explicit call is idempotent and guards a future import
  reorder. `log_dot_precision()` prints both values before the build AND after `build_model`
  (jcm.runners.build_model wrapped), and raises if either is not `Precision.HIGHEST` while
  `jaxlib_is_affected()`. scripts/check_env.sh asserts the same after `import jcm, jcm_strat`.
- Why: the brief wants the values in every log, after the model is built; a refusal is cheaper
  than a silent hemispheric mass drift.

### 2026-10-07 11:15 PDT - 19b item 3: jcm's dot_precision_test.py on GPU
- `pytest jcm/dycore/dinosaur/dot_precision_test.py` on GPU 0: 7 passed (incl. the GPU-only
  `SingleLevelTransformGpuTest::test_single_level_inverse_transform`). Log runs/p19b_dot_precision_test.log.

### 2026-10-07 11:15 PDT - API breakage found when porting to jcm 3.0.0rc1 (119 commits)
pytest on the unported tree: 82 passed, 7 failed. Breakage and fixes:
1. `Model(start_date=..., calendar=...)` -> `Model(start_time=...)`; jcm 3 has ONE proleptic
   Gregorian clock with 1 January at phase 0 (exactly what our `calendar: gregorian` patch did).
   Options: drop the `calendar` key from the configs / keep it as a checked no-op. Chosen: keep it,
   `install_calendar` now only refuses anything but `gregorian` - the configs keep stating it.
2. **`run.start_date` -> `run.start_time` (silent!)**: jcm 3 no longer reads `start_date`, so an
   unported config would have started every segment on 2000-01-01 against the wrong ERA5 window
   without an error. Renamed in p2_sd/p3_tracers/ref_echam_sd (+ comments) and chain_segments.sh;
   `jcm_strat.main.check_jcm3_run_keys` now refuses `run.start_date` and `run.sponge.target_T_K`.
   The OLD phase scripts (phase9..18 *_run.sh) still say start_date: they are historical records
   of runs on the old jcm and are not run again; left unchanged.
3. `run=longrun` now writes calendar-month means only (`monthly_means: true, save_chunks: false`,
   `save_interval: 1`). Every jcm-strat diagnostic reads the per-chunk `longrun_day<N>.nc`, so
   p3_tracers and ref_echam_sd (the two bases of every experiment) set `monthly_means: false,
   save_chunks: true`; the experiments already set save_interval 0.25, output_averages false.
4. jcm's ECHAM term list gained `echam_surface_exchange` (EchamSurfaceExchange, the
   surface-exchange contract). Options: leave our explicit lists (echam_prod12/echam_free14) as
   they were / add the term as jcm's physics/echam.yaml does. Chosen: add it, same position - the
   brief asks for Phase 12/14 "on the new jcm", which means jcm 3's ECHAM package.
5. Things that did NOT break: the mass-fixer wrapper (`_fix_nodal_tracer_mass` keeps its
   signature; jcm 3 now clips the factor to [2/3, 1.5]), `column_lat_lon`,
   `physics_specs_from_constants`, `PhysicsTerm`/`TracerSpec`, `HinesGwd`, `LottMillerSso`
   (now a package `jcm.physics.gravity_waves.sso`, same import path), `get_echam_levels`
   (L95 table unchanged -> the ERA5 window hashes are unchanged: strat81 3af87627, L95 c39313fe,
   so the 1990-1999 windows on disk are reused), `jcm.data.era5` (byte-identical).

### 2026-10-07 11:15 PDT - Old strat81 sponge -> jcm 3 ECHAM sponge
- Old: p9_l63 (inherited by strat81) set `run.sponge.levels 4, enspodi 6.73` on top of jcm 2's
  longrun sponge (tau 1.5 h at the top, FULL u, v damped, T relaxed to target_T_K 250 K) -
  the remapped strat63 equivalent of L95's 10-level sponge (levels.sponge_for).
- Options: (a) keep 4 levels/enspodi 6.73 with the new scheme (m != 0 only, no T target);
  (b) ECHAM's own: 1 level, 3 h, enspodi 1 (`timescale_h`/`enspodi` null); (c) map tau(p) of the
  old sponge onto the new one.
- Chosen: (b), as the brief prescribes (`run.sponge.levels=1`), set in p9_l63 (so the whole
  strat63/strat81 chain gets it) and repeated in the p19/p20/p21 experiments so the config dump
  states it. The remap has no meaning any more: the new sponge touches neither the zonal mean nor
  T's mean, which is what the old 4-level remap was tuned for. p9_l47 and p13_gwd_l95 (not run
  again) keep their old numbers. strat81's top level is L95's top level (0.01 hPa), so "ECHAM's
  top level" is the same level as in L95.

### 2026-10-07 11:20 PDT - How to do the one-month spin-up
- Options: (a) start 1989-12-01 from ERA5, run 31 days, restart 1990-01-01 from that checkpoint
  with the tracers initialised then (brief's first choice); (b) fallback: January 1990 as spin-up,
  restart 1990-01-01 with that dynamic state (dynamics then hold "future" January 1990 at the
  1990-01-01 restart - a 31-day phase jump in the nudging target and season);
  (c) one segment 1989-12-01..1990-12-31 with a re-initialisation at 1990-01-01.
- Chosen: (a). It needs only ERA5 for December 1989: the QBO target year 1989 is on disk
  (cache/era5_ref/era5_zm_monthly_1989.nc); nudging windows 1989-11-30..1990-01-03 for strat81
  (6 h, 2.5 GB) and L95 (12 h, 1.4 GB) plus the 1989-12-01 initial states are prefetched
  (tmux strat_p19_prefetch). (c) would break the one-calendar-year segment layout every
  diagnostic and the chain's QBO year override rely on.
- Implementation: `scripts/chain_segments.sh SPINUP="1989-12-01 31"` runs
  `runs/<PREFIX>_spinup_19891201` (init ERA5, QBO year 1989, first_segment FALSE), then the
  1990 segment from its checkpoint with `first_segment=true`. Not linked into the aggregate, so
  every diagnostic excludes it by construction.

### 2026-10-07 11:20 PDT - How to re-initialise the tracers on 1990-01-01 after the spin-up
- Problem: old runs started 1990-01-01 from ERA5 with every tracer at its initial value (clocks,
  sources, sai 0; n2o/cfc11 1) and `first_segment=true` then SET the pulses to their shapes and
  n2o/cfc11 to WACCM's state on step 1. After a spin-up the checkpoint carries a month of clock
  ageing and source/sai accumulation, which `first_segment` did not touch.
- Options: (a) drop the tracers from the checkpoint before the restart (needs a checkpoint
  surgery script, and jcm 3 checkpoints are schema-stamped and refuse a changed composition);
  (b) a separate "reset" flag; (c) extend `first_segment=true` so that on the first step every
  tracer is treated as holding its initial value: tendency = usual tendency evaluated at q = 0,
  plus -q/dt.
- Chosen: (c). On a run without spin-up the tracers already hold 0 on that step, so it is the
  identity (old behaviour unchanged, test_first_step_reinitialises_after_spinup); after the
  spin-up the 1 January state of all 26 tracers equals the old runs' (pulses and n2o/cfc11 were
  already set, not incremented). Dynamics (u, v, T, ps, q) are carried over from the spin-up.

### 2026-10-07 11:20 PDT - Humidity in the dry configurations
- jcm 3 makes the hybrid-level dynamics moist (virtual temperature) and adds a mass fixer on the
  modal specific humidity. The dry runs carry the ERA5 initial humidity passively (no moist
  physics), so Tv now differs from T by up to ~1-2 K in the warm, moist lower troposphere at the
  start (q decays only by transport/diffusion). Options: zero q at init / keep jcm 3's behaviour.
- Chosen: keep jcm 3's behaviour; it is part of "the effect of the jcm update alone" that 19d
  measures, and changing the initial state would be a side experiment. Recorded as a
  difference to old runs in output.md.

### 2026-10-07 11:57 PDT - Smokes: what failed and how it was fixed
- First round (commit 6d3ba46): the full-physics smokes (p21_echam_n400 GPU 2, p21_free GPU 3) ran; the two dry ones
  (p19/p20) died at build: jcm 3's `forcing.ozone_file: auto` now fetches an on-grid ozone bundle eagerly and
  hf://bundles/t63_l81/ozone_pd.nc does not exist (jcm 2 fell back to the analytic profile silently - the old run
  provenance says "ozone_source: analytic (auto found no packaged match)"). Options: (a) build an L81 ozone file;
  (b) `forcing.ozone_file: analytic`, i.e. exactly what the old runs used; the dry physics never reads ozone.
  Chosen (b), in p9_l63 (inherited by every strat63/strat81 experiment).
- My smoke checker's thresholds were too tight (ps up to 1102 hPa occurs in the old p12echam smoke too; the
  1 hPa tracer lid's values reach ~2-3 hPa within 5 days in old and new runs alike). Loosened to ps < 1120 hPa
  and the clock check below 10 hPa. All four smokes PASS; restart smoke (p19 from the p19 smoke checkpoint,
  first_segment=true): the 06 UTC clock is 0.250 d below 10 hPa -> re-initialisation works.
- Observation (not acted on): with jcm 3's ECHAM sponge (top level only, m != 0 only) the full-physics
  mesospheric winds are stronger: max |u| ~150 m/s at 0.03-0.04 hPa after 5 days vs ~90 m/s on the old jcm
  (its 10-level full-wind sponge). This is jcm's documented effect of the sponge change ("the stratospheric
  and mesospheric zonal-mean winds strengthen"); the brief prescribes levels=1. Watched by jcm's per-chunk
  health check; listed under follow-ups.
- Old vs new 5-day DJF tropical w* in the full-physics smoke (stride 1, 5 days, noisy): 100 hPa 1.43 -> 0.45
  mm/s - a first hint of the fixed Lott-Miller's effect; the chains will tell.

### 2026-10-07 11:57 PDT - GPU assignment
- GPU 0 has been held since ~10:50 PDT by another of Susanne's jobs (/home/susanne/cesm_jax/validation/
  phase6_multiyear.py, 10 GB, 99 %). Options: wait for GPU 0 / use the spare GPU 4 for 19d.
- Chosen: 19d on GPU 4 (the brief: "GPU 4 is spare: use it only if one of the above must be restarted while its
  GPU is busy" - 19d cannot start on its GPU, which is the same situation). 20 on GPU 1, 21a on GPU 2, 21b on
  GPU 3, as planned. Every pipeline waits (wait_gpu) rather than fails if its GPU is busy.

### 2026-10-07 11:57 PDT - Precision gate (19b item 4): which 30-day run, which thresholds
- Options for the run: (a) a separate 30-day 19d run; (b) the 19d spin-up month itself (31 days of exactly the
  19d config, 1989-12-01 from ERA5). Chosen (b): same config and length, no extra GPU time, and the gate then
  sits before the 5-year chain (chain_segments.sh SPINUP_ONLY=1, gate, then the chain). Phases 20/21 run their
  own spin-ups and then wait for runs/p19b_gate.PASS (or stop on .FAIL).
- Metric: with terrain and nudging the NH-SH area-mean ps is not zero (orography, season), so the gate is on
  its CHANGE from the first 6-hourly sample, plus the change of the global mean. Thresholds |dA| < 5 hPa,
  |dG| < 0.5 hPa. Why 5: the OLD jcm (p13jhn400, same physics, January 1990) swings by up to 2.2 hPa
  (global mean +0.13 hPa) - natural NH-SH mass exchange; the bug is -116 hPa in 30 d. The old run is
  drawn alongside for context (a different month, so not a difference).

### 2026-10-07 11:57 PDT - Diagnostics and comparisons chosen
- All TEM diagnostics at stride 1 (phase12_compare.py --stride 1, mesosphere_wstar.py --stride 1,
  sweep_score.py uses every frame). Ages over the last 60 days (240 frames), as before.
- 19d: `update` = old p13jhn400 first 5 yr (links day <= 1826 of p13jhn400_10yr into runs/old_p13jhn400_5yr)
  -> p19jhn400_5yr; `vs13d` = p13jh_5yr -> 19d; aoa_vs_clams (3 clocks, old alongside); mesosphere 1994;
  sweep_score of both (u/T vs ERA5; w* vs WACCM because ERA5 TEM exists only for 1996-2001 on disk).
- 20: THE comparison `sso5_vs_19d` (p19jhn400_5yr -> p20jhsso_5yr, same code); 10 yr vs the old 13c run 1
  (broken LM), 13c run 2 (no LM), 13d; sweep_score of the 10-yr runs over 1998-99 = ERA5 TEM w* and upward
  mass flux ("mass flux vs ERA5"); spin-up adjustment = scripts/p20_spinup_adjust.py (daily global
  relative angular momentum and 300 hPa zonal-mean u at 25-50N/S, 19d vs 20, through December 1989 and
  January 1990).
- 21: `echam_rerun` (old p12echam_5yr -> 21a), `free_rerun10`/`free_rerun5` (old p14free -> 21b), and with
  Phase 20 alongside `echam_vs_p20`, `free_vs_p20`; aoa_vs_clams; sweep_score; mesosphere.
- Not done (keep it simple): no PDF reports (not in the brief), no new reference fetches.

### 2026-10-07 11:57 PDT - Pipelines and agents
- scripts/phase19_run.sh (tmux strat_p19_run, GPU 4), phase20_run.sh (strat_p20_run, GPU 1),
  phase21_run.sh (strat_p21_run, GPUs 2+3; 21a and 21b chains in parallel, each followed by its own
  diagnostics). Shared helpers scripts/p19_lib.sh. Each: pytest -> smoke (skipped if passed) -> spin-up ->
  gate -> chain -> diagnostics -> commit metrics/plots -> headless write-up agent
  (scripts/p19_prompts/writeup_pNN.md + common_rules.md, copied to runs/pNN_writeup_prompt.md). Any failure
  -> failure agent (scripts/p19_prompts/failure.md): diagnose, fix if clearly mechanical, relaunch ONCE with
  RELAUNCHED=1, otherwise record and stop. A failed precision gate is a science stop (no relaunch).
- chain_segments.sh gained LINK_ONLY=1 (aggregate relinking without the GPU checks; Phase 14's watcher
  failed on exactly that) for the 5-yr aggregates of the 10-yr chains.

### 2026-10-07 12:15 PDT - Bug caught at launch: tracer initialisation flag for p20_*/p21_*
- chain_segments.sh adds `first_segment=true` to the first segment only for experiments matching
  `p10_*|p1[1-9]*` (Phase 10-18 naming). p20_jh_sso_n400, p21_echam_n400 and p21_free do not match, so their
  1990 segments would have run with first_segment=false: no pulses, no WACCM n2o/cfc11 state, and the clocks
  would have kept the spin-up month's age. Seen in the chain headers ("first-seg: none") right after launch.
- Options: (a) stop the pipelines and relaunch with FIRST_SEG_EXTRA set explicitly; (b) widen the pattern to
  `p2[0-9]*` with an atomic replace of the script (mv of a new file: the running spin-up chains keep the old
  inode, never an in-place edit), before any 1990 segment starts.
- Chosen (b), done 12:14 PDT; the Phase 19b gate passed one minute later and both 1990 segments (p19jhn400,
  p20jhsso) started with `physics.terms.production_tracers.first_segment=true` (checked in their chain logs).
  21a/21b were still in their spin-ups and will read the fixed script for 1990. Regression test added
  (tests/test_phase19.py::test_chain_initialises_tracers_for_phase_20_and_21_experiments).

### 2026-10-07 12:15 PDT - 19b gate result
- PASS: new jcm max |change NH-SH ps| 2.17 hPa (end -1.21), global mean max 0.07 hPa (end +0.04) over the
  31-day spin-up; the old jcm (same physics, January 1990): 2.16 / 0.13 hPa. Same natural swing, no drift.
  docs/outputs/19_jcm_update/p19_ps_gate.md/.png.

### 2026-10-07 13:39 PDT - INCIDENT: the dry chains (19d, 20) blow up on the new jcm; the chains spliced partial years
- Found by the Phase 20 failure agent (13:27 PDT; its log in jcm-strat-phase20 docs/outputs/20_sso_fixed/decisions.md):
  every p19jhn400 / p20jhsso segment hit jcm's health stop ("atmosphere unhealthy", T NaN or q/T limits) after
  10-230 days; `bail_on_unhealthy` ends the run with exit 0, so chain_segments.sh counted it as a finished year
  and started the next from the last healthy checkpoint. All p19jhn400_1990-1994 and p20jhsso_1990-1995 output is
  invalid. The 31-day spin-ups and the 19b gate were healthy (the blow-up comes later; the gate stands).
- Where: 19d 1990, frame by frame (longrun_day140): fine until 1990-05-18; then |u| 190-230 m/s and T collapsing
  (Tmin 73 K, then 4 K) at 0.09-0.4 hPa, Tmax 350-420 K at 0.155 hPa, NaN on 1990-05-21 - an upper-mesospheric
  instability in the sponge region. The full-physics runs (21a/21b, same sponge) are healthy through day 165.
- Reading: the old 4-level full-wind sponge (+ T -> 250 K) held the dry strat81 mesosphere; jcm 3's ECHAM uspnge
  (top level only, m != 0 only, 3 h) does not. ECHAM's own config relies on Hines (full spectrum) for the
  mesospheric jets; the dry config's mesosphere is the Jucker relaxation + Hines launched at 634 hPa only.
- Actions now: (1) stopped strat_p19_run (it was computing diagnostics on invalid output; nothing committed from
  it); (2) chain_segments.sh now counts a health stop as a FAILED segment (rc 3) and a segment with one in its log
  as not done (atomic replace); (3) the running Phase 21 chains still use the old script in memory, so a watchdog
  (tmux strat_p21_watch, runs/p21_watchdog.sh) stops Phase 21 if any p21 segment reports a health stop;
  (4) two 1990 test runs from the 19d spin-up checkpoint to find the cause (tmux strat_p19_test, GPUs 1 and 4):
  p19t_sponge4 = jcm 3's sponge over the old geometry (4 levels, enspodi 6.73, 1.5 h; still m != 0 only, no
  T target), p19t_linear = levels 1 with linear SL vertical interpolation (the old default).
