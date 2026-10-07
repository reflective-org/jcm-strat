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
