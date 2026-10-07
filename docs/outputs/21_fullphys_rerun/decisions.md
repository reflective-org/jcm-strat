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
