# Phase 21 (full-physics references rerun) decision log

Append-only, times in PDT. The set-up decisions shared by Phases 19-21 (jcm pin, dinosaur, spin-up, tracer
re-initialisation, sponge, GPUs, pipelines, diagnostics) are in the Phase 19 log:
/data/JCM_stripped/jcm-strat-phase19/docs/outputs/19_jcm_update/decisions.md (branch phase19-jcm-update).

### 2026-10-07 11:58 PDT - Where this phase's runs and record live
- Options: own venv + runs in this worktree / run from the phase19 worktree.
- Chosen: the runs are made by /data/JCM_stripped/jcm-strat-phase19/scripts/phase21_run.sh from the phase19
  worktree (the only new-jcm venv) into its runs/; this worktree's `runs` and `.venv` are symlinks to it, and
  only the record (docs/outputs/21_fullphys_rerun/) is committed here, on a branch stacked on phase19-jcm-update.
- Why: one venv, one runs/ directory; the code is identical (branched at 3b5768c).

### 2026-10-08 12:03 PDT - Failure agent: free_vs_p20 and the mesosphere check failed (no Phase 20 10-yr data)
- What failed: the pipeline stopped at 12:02 PDT with "a diagnostics step failed or was skipped". Both chains are
  complete and healthy, and echam_rerun, free_rerun10, free_rerun5 and echam_vs_p20 ran (exit 0). Two steps failed:
  `compare free_vs_p20` (runs/p21_compare_free_vs_p20.log) and `mesosphere_wstar.py` (runs/p21_mesosphere.log). Both
  failed with `ValueError: need at least one array to concatenate` in strat_circulation.model_tem_fields. The cause was
  missing input: runs/p20jhsso_10yr and runs/p20jhsso_19990101 do not exist, because Phase 20 stopped on the 1997 health
  stop (Oct 7 23:50 PDT) and was not relaunched. Only the 5-yr aggregate runs/p20jhsso_5yr was linked (by Susanne's
  p20_5yr_diag.sh, Oct 8). The pipeline's guard only checked that the 5-yr aggregate existed, then used the 10-yr one.
- Options: (a) record the failure only and leave the two Phase 20 comparisons out; (b) rerun both by hand on the
  common healthy window: free_vs_p20 as 1990-1994 (p20jhsso_5yr vs p21free_5yr), and the mesosphere check with Phase 20
  1994 instead of 1999; (c) build a 7-yr 1990-1996 Phase 20 aggregate and compare that.
- Chosen: (b). Mechanical, with no physics, config or threshold change. Rerun by hand on CPU (tmux eval_p21_p20diag,
  script runs/p21_p20diag_rerun.sh, logs runs/p21_compare_free_vs_p20_5yr.log and runs/p21_mesosphere_rerun.log).
  The new tag is `free_vs_p20_5yr`, so it is never mistaken for the planned 10-yr comparison. The mesosphere table
  keeps 21a 1994 and 21b 1999 as planned, and adds 21b 1994 so that one row matches the year of the Phase 20 1994 row.
  The pipeline was not relaunched (as instructed).
- Why: 1990-1994 is the window Susanne already chose for Phase 20's own diagnostics after the 1997 blow-up. Both
  aggregates exist for it, and free_rerun5 already uses p21free_5yr. Option (c) would need a new aggregate over a
  window no other comparison uses. A 1990-1999 Phase 20 vs 21b comparison is impossible until Phase 20 is resolved.
- For Susanne: free_vs_p20 is a 5-yr comparison, not the planned 10-yr one. If Phase 20 is ever rerun to 1999 (after an
  SSO stabiliser decision), the 10-yr comparison can be made with the cmp line in scripts/phase21_run.sh.

### 2026-10-08 13:00 PDT - Failure agent: outcome of the hand rerun
- Question: were the hand reruns from 12:03 clean, and can the write-up use them?
- Options: use them / discard them and report the failure only.
- Chosen: use them. `free_vs_p20_5yr` exit 0 (free_vs_p20_5yr_metrics.md + 6 plots) and mesosphere exit 0
  (p21_mesosphere.md/.png: 21a 1994, 21b 1999, 21b 1994, 20 1994, reference Phase 12 run 4 1994). Neither log has a traceback.
- Why: same scripts and settings as the pipeline. Only the Phase 20 window changed (1990-1994) because of the 1997 stop.
  The pipeline's stale failed log runs/p21_compare_free_vs_p20.log and runs/p21_mesosphere.log are superseded by
  runs/p21_compare_free_vs_p20_5yr.log and runs/p21_mesosphere_rerun.log. The write-up should cite free_vs_p20_5yr and
  say it is 5 yr.

### 2026-10-08 13:06 PDT - Write-up agent: choices made in output.md
- **Phase 14's "downward w*" against the stride-1 rerun.** Question: the Phase 14 record says −0.05/−0.22/−0.28 mm/s at
  100/70/50 hPa, but free_rerun10 reads the same p14free_10yr as +0.17/+0.10/+0.01. Options: (a) quote only the stride-1
  numbers; (b) quote both and say the original was stride 4; (c) treat the difference as a script change and not comment.
  Chosen: (b). Phase 14's free10_metrics.md says "every 4th 6-hourly frame", and Phase 15 found stride 4 tide-biased, so the
  discrepancy is explained and is itself part of the answer to question (ii). The age-based part of the Phase 14 finding
  (equatorial age maximum) does not depend on sampling and is kept as real.
- **Separating cutoff vs code for question (i).** No 2×2 exists (only old/150 and new/400 nudged runs). Options: (a) say
  "cannot be separated" and stop; (b) use the free pair (code change only, no nudging) as the code effect and attribute the
  residual to the cutoff, labelled as an estimate that assumes additivity; (c) use Phase 13c (dry, cutoff only, old jcm) as
  the cutoff effect. Chosen: (b) with (c) as supporting evidence, and state explicitly which quantities stay ambiguous
  (12 hPa tropical age, extratropical 55 hPa age). Why: it uses only runs that exist and makes the assumption visible.
- **era5_check/.** Susanne's own 21a-vs-ERA5 check (tmux eval_p21a_era5) was still running at write-up time; its first two
  PNGs were already committed by the pipeline. Options: interpret it fully / mention it descriptively / ignore it. Chosen:
  describe what the committed PNGs show (weak vortices, equatorial u near 1 hPa) and leave the interpretation to her. Its
  in-progress outputs are not committed by me.
- **"Phase 19-21 plan complete" in STATUS.md.** Phase 20 has no output.md (stopped in 1997, awaiting Susanne's decisions),
  so the plan is NOT reported complete; Phases 19 and 21 are.
