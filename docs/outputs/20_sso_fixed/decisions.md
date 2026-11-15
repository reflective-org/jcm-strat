# Phase 20 (dry 13d + fixed Lott-Miller) decision log

Append-only, times in PDT. The set-up decisions shared by Phases 19-21 (jcm pin, dinosaur, spin-up, tracer
re-initialisation, sponge, GPUs, pipelines, diagnostics) are in the Phase 19 log:
/data/JCM_stripped/jcm-strat-phase19/docs/outputs/19_jcm_update/decisions.md (branch phase19-jcm-update).

### 2026-10-07 11:58 PDT - Where this phase's runs and record live
- Options: own venv + runs in this worktree / run from the phase19 worktree.
- Chosen: the runs are made by /data/JCM_stripped/jcm-strat-phase19/scripts/phase20_run.sh from the phase19
  worktree (the only new-jcm venv) into its runs/; this worktree's `runs` and `.venv` are symlinks to it, and
  only the record (docs/outputs/20_sso_fixed/) is committed here, on a branch stacked on phase19-jcm-update.
- Why: one venv, one runs/ directory; the code is identical (branched at 3b5768c).

### 2026-10-07 13:27 PDT - Failure agent: chain p20jhsso stopped at 1996 (RELAUNCHED=0) - NOT relaunched
- Proximate error: segment p20jhsso_19960101 exited 1 with FileNotFoundError: runs/p20jhsso_19950101/checkpoint.ckpt
  does not exist.
- Real cause (scientific, not mechanical): **the model blows up in every segment**, and the chain did not notice.
  The runner's bail_on_unhealthy stops a segment at the first unhealthy 10-day chunk, keeps the last healthy
  checkpoint and still exits 0, so chain_segments.sh counted each truncated segment as finished and started the
  next "year" from whatever state survived:
  | segment | stopped at | reason |
  |---|---|---|
  | 1990 | day 130 | T NaN 100 % (day 120 still OK: T 173-311 K) |
  | 1991 | day 20 | q_max 131.5 g/kg |
  | 1992 | day 140 | T NaN 100 % |
  | 1993 | day 210 | T NaN 100 % |
  | 1994 | day 70 | q_max 197.5 g/kg |
  | 1995 | day 10 | T_min 84 K (T 84-396 K); no checkpoint ever written -> the 1996 error |
  Every p20jhsso 1990-1995 output is therefore invalid (partial years, each started from a state up to ~7
  months older than its date; tracers/QBO calendars inconsistent). The spin-up (31 d) was healthy.
- **The Phase 19 baseline does the same:** p19jhn400 (no SSO, same new jcm) went NaN at day 140 (1990), 230 (1991)
  and 160 (1992) and its chain is still running on GPU 4 producing the same kind of truncated segments. So the
  instability is NOT (only) the fixed Lott-Miller term: it comes with the new jcm port (jcm 35dc1997 + dinosaur
  1.5.0, ECHAM sponge levels=1, start_time clock etc.). 5-day smokes and the 31-day 19b gate were too short to see it.
- Options: (a) relaunch as is (would repeat the same blow-ups, and the 1995 checkpoint does not exist);
  (b) patch chain_segments.sh to fail on "atmosphere unhealthy" and relaunch (still no valid run, only a cleaner stop);
  (c) change physics/time step/sponge to stabilise (forbidden for this agent, and a science decision);
  (d) do not relaunch; record and hand to Susanne.
- Chosen: (d). Why: a NaN/blow-up is explicitly a non-mechanical failure; nothing I may change fixes it.
- For Susanne to decide:
  1. Stop strat_p19_run (GPU 4) - its 1990-1992 segments are equally truncated and its write-up agent will
     otherwise analyse invalid output. (Left running by me: not this pipeline's session.)
  2. Find the blow-up: rerun the 1990 segment from the spin-up checkpoint with daily output around days 110-130
     (which level/latitude goes first - sponge top with levels=1 is the first suspect, then the cubic SL/time
     step under dinosaur 1.5.0, then the 1d444197 Lott-Miller change for p20 only).
  3. Fix chain_segments.sh so a segment whose log contains "atmosphere unhealthy" (or that ran short of
     total_time) counts as FAILED, not done - otherwise any future chain can silently splice partial years.
  4. Delete/quarantine runs/p20jhsso_19{90..96}0101 before any relaunch (the chain's skip test would reuse them).

### 2026-10-07 15:14 PDT - Resolution of the 13:27 failure (set-up session)
- Cause: jcm 3's cubic SL vertical interpolation in the dry strat81 mesosphere (not the fixed Lott-Miller, not the
  sponge geometry): see the Phase 19 decisions.md entries 13:40-14:15 (test runs p19t_linear / p19t_sponge4).
- Chosen: p19_jh_n400 (and so p20_jh_sso_n400) use `dycore.sl_vertical_interpolation: linear`; chain_segments.sh
  fails a segment on a health stop; the 13:27 output moved to runs/invalid_cubic_20261007/; Phase 20 relaunched from
  scratch at 14:30 PDT (tmux strat_p20_run, GPU 1). The comparison with 19d stays clean: both use linear.

### 2026-10-07 19:04 PDT - Failure agent: L95 + cubic run stopped at 1990 day 60 (q_max 104.7 g/kg)
- What failed: pipeline `phase20_run.sh` (relaunched 18:16 PDT, commit ca392cf, GPU 1, RELAUNCHED=0). Smoke PASS,
  spin-up p20jhsso_spinup_19891201 healthy (q_max 22 -> 7 g/kg, the same as 19d's spin-up), 19b gate PASS, then segment
  p20jhsso_19900101 stopped on jcm's health check at day 60 (`q_max=104.7 g/kg (> 100)`), exit 3, chain stopped
  correctly (the chain health-stop fix worked; no partial year spliced). Checkpoint stays at day 50.
- Diagnosis: no NaN, T 193-331 K, |u| < 150 m/s - a local moisture spike, not a general blow-up. Chunk q_max:
  6.3, 22.6, 6.7, 21.8, 79.8, 104.7 g/kg (days 10-60). In the 6-h output the maximum is on the LOWEST model level
  (sigma 0.983) at the southeastern edge of the Tibetan plateau / Himalaya: 89.7 g/kg at 99.4E 25.2N (day 50 file),
  173 g/kg at 97.5E 28.9N (day 60 file). The 19d baseline (identical config WITHOUT lott_miller_sso, same jcm, L95
  cubic) is at q_max 3.6-5.8 g/kg through day 110 of 1990. The only difference is the fixed Lott-Miller SSO term, so
  the cause is the SSO drag (with the fixed 100x factor) over the steepest orography interacting with the
  near-surface moisture (likely a grid-point convergence / dry-model water positivity issue at the surface). This is
  scientific, not mechanical.
- Options: (a) relaunch unchanged (deterministic: it would fail again at day 60); (b) loosen the q_max health
  threshold (forbidden: changing a threshold to make it pass); (c) change SSO settings / time step / humidity
  handling (forbidden for this agent: physics/config science); (d) do not relaunch, record, hand to Susanne.
- Chosen: (d). Why: a reproducible physical instability tied to the one physics term this phase tests; nothing I
  may change fixes it, and a relaunch would only burn GPU 1 for an hour to fail again.
- For Susanne to decide:
  1. Whether the fixed Lott-Miller is unstable on L95 at this time step over the Himalaya, or whether humidity in the
     dry configuration just needs a cap/sink (in a dry run q is near-passive; a 100 g/kg surface value may not
     matter for the strat circulation, but the health check is binding). Suggested test: rerun 1990 from the
     spin-up checkpoint with daily output for days 30-60 and look at SSO u/v tendencies and omega at 95-100E,
     25-30N; compare with the old-jcm 13c/13d runs that had the (unfixed) Lott-Miller.
  2. Options then: smaller SSO time-step/implicit limiter, SSO tendency cap, orography smoothing, or keep SSO off
     (13d/19d) and drop Phase 20.
  3. Before any relaunch move runs/p20jhsso_19900101 aside (it is incomplete; the spin-up can be reused).
  GPU 1 is now idle. strat_p19_run (19d, GPU 4) and Phase 21 are unaffected and keep running.

### 2026-10-07 19:25 PDT - Susanne: treat humidity as unimportant for now; relaunch (supervising session)
- Susanne chose option "treat humidity as unimportant" from the 19:04 list, with a GitHub issue to come back to it:
  reflective-org/jcm-strat#62.
- Implementation: `health_ignore_q_max: true` in p20_jh_sso_n400.yaml; `jcm_strat/main.py::install_health_policy` wraps
  `jcm.diagnostics.check_health`: q_max > 100 g/kg is printed per chunk ("health_ignore_q_max: not fatal") and every
  temperature check stays fatal. Echoed in the run header. 19d/21 unaffected (flag false). Test in tests/test_phase19.py.
- Options not taken: cap q or add a q sink (changes the model state); tune SSO / smooth orography (science change).
- Relaunch: failed segment moved to runs/failed_q_20261007/p20jhsso_19900101; smoke, spin-up and 19b gate reused.
- Watch for: q growing without bound -> a later T NaN (would still stop the run).

### 2026-10-07 23:52 PDT - Failure agent: 1997 segment blew up near the surface east of the Tibetan Plateau (T 58-746 K)
- What failed: pipeline `phase20_run.sh` (relaunched 19:20 PDT, commit 1d8e4a7, GPU 1, RELAUNCHED=0). Segments 1990-1996
  finished healthy (exit 0, compacted). Segment p20jhsso_19970101 stopped on jcm's health check at day 360
  (`T_min=58K (< 100K)`, `T_max=746K (> 500K)`), exit 3, 23:50 PDT; chain stopped correctly. Its checkpoint stays at
  day 350 (1997-12-17); 1998-1999 not run; the 10-yr diagnostics and write-up did not run.
- Diagnosis (6-h output, longrun_day340/350/360.nc): no NaN. Up to 1997-12-19 18Z everything is normal (T_max 330-355 K
  on the lowest level over Arctic land, T_min a slow drift 180 -> 154 K at the Antarctic surface, within what 19d also
  shows; 19d and earlier p20 years reach T 147-150 / 357-392 K too). Then from 1997-12-20 00Z a local runaway at
  sigma 0.98 (lowest levels), 106.9E 30.8N (Sichuan Basin, east flank of the Tibetan Plateau): T_max 406 -> 639 K in
  24 h, peaking 780 K; a cold partner two grid points east at 114.4E 30.8N falls to 25 K. A one-to-two-point
  hot/cold dipole that grows for a week = a grid-scale numerical instability, not a meteorological event. It sits in
  the same SE-Tibet sector as the issue #62 humidity spikes. Humidity was NOT large at the time (chunk q_max 2.4 g/kg;
  1997 max 19 g/kg), but the exempted q spikes recurred in every year 1990-1996 (q_max 105, 149, 58, 33, 162, 39,
  110 g/kg; 19d without SSO: <= 6 g/kg). 19d (same config, no Lott-Miller) ran 1990-1994 with no such event.
  So the fixed Lott-Miller SSO over the steep SE-Tibet orography is again the prime suspect; the temperature checks
  that the #62 exemption left fatal caught it, as intended.
- Options: (a) relaunch unchanged (the model is deterministic from the 1996 checkpoint: it would fail again at the
  same day after ~30 min of GPU 1); (b) loosen the temperature thresholds (forbidden, and the state is unphysical);
  (c) SSO limiter / orography smoothing / shorter time step / restart with a perturbation (science or config change -
  not mine to make); (d) do not relaunch, record, hand to Susanne.
- Chosen: (d). Why: a reproducible physical/numerical instability tied to the term this phase tests; RELAUNCHED=0 only
  covers mechanical causes. Nothing moved or deleted; runs/p20jhsso_19970101 left in place as evidence.
- For Susanne to decide:
  1. Whether to use what exists: 1990-1996 are complete and healthy. THE comparison of this phase (sso5_vs_19d, 5 yr)
     needs only 1990-1994, so the 5-yr aggregate + diagnostics + write-up could run unchanged in scope; only the
     10-yr / ERA5 1998-99 score part is lost. That needs a go and a pipeline variant that stops the chain at 1996 (or
     1994) - not done here.
  2. Whether the fixed Lott-Miller needs a stabiliser before production use (tendency cap, implicit/limited drag,
     orography smoothing over SE Tibet, smaller dt) - with #62 this is now the second symptom in the same place.
     Suggested diagnostic: rerun 1997-12-07 .. 12-21 from runs/p20jhsso_19970101/checkpoint.ckpt (day 350) with 6-h
     SSO u/v/T tendencies at 100-115E, 25-35N.
  3. Before any relaunch of the chain, move runs/p20jhsso_19970101 aside (it is incomplete).
  GPU 1 is idle. Phase 21 (strat_p21_run, GPUs 2/3) is unaffected.

### 2026-10-15 16:47 PDT (recorded 2026-10-20) - Phase 20b: nudge the bottom two levels as well
- Why: 19d (dry, no Lott-Miller) and 21a/21b (full physics with Lott-Miller) all run through Dec 1997; only the dry config with
  Lott-Miller fails, and only the dry config leaves the bottom two levels (jcm's default `pbl_levels: 2`) to the dynamics and
  the drag alone, with no boundary layer. Test: `p20b_sso_pbl0` = Phase 20 with `nudging.pbl_levels: 0`, nothing else changed
  (commit 82096e4), clean from the 1989-12 spin-up, GPU 0.
- Result 18:50 PDT: passes Dec 1997 (east-Tibet bottom levels 259-291 K), no humidity exemption needed 1990-1997.
- Susanne asked for 20 years: the 1999-2009 extension of p20b was replaced by `p20bt` (all output variables, fresh 1990-2009
  from the spin-up, so the 1990 tracer pulses are written from their release; commit ac5f341). Done 2026-10-16 02:41 PDT, healthy.
