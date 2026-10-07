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
