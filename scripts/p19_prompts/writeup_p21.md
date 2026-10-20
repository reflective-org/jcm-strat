You are the write-up agent for jcm-strat Phase 21 (full-physics references redone on the new jcm with the
fixed Lott-Miller SSO): 21a p21echam = Phase 12 run 4 (full ECHAM, T63L95, QBO term, ERA5 nudging now
< 400 hPa) 1990-1994; 21b p21free = Phase 14 (free-running, no nudging, no QBO) 1990-1999; both after a
discarded one-month spin-up. The pipeline /data/JCM_stripped/jcm-strat-phase19/scripts/phase21_run.sh has
just finished. Runs: /data/JCM_stripped/jcm-strat-phase19/runs (p21echam_*, p21free_*); record: worktree
/data/JCM_stripped/jcm-strat-phase21 (branch phase21-fullphys-rerun), docs/outputs/21_fullphys_rerun/.

Read: the Phase 19 decisions.md, runs/p21_run.log, the metrics in docs/outputs/21_fullphys_rerun/
(echam_rerun_metrics.md vs old p12echam_5yr; free_rerun10/free_rerun5_metrics.md vs old p14free;
echam_vs_p20 / free_vs_p20 = Phase 20 alongside; scores/*.json; p21_mesosphere.md) and every PNG. Old
records: /data/JCM_stripped/jcm-strat-phase12/docs/outputs/12_circulation/output.md (run 4) and
/data/JCM_stripped/jcm-strat-phase14/docs/outputs/14_free_physics/output.md.

Then:
1. Write docs/outputs/21_fullphys_rerun/output.md: what was run, Results for 21a and 21b against the old
   runs (same phase12_compare diagnostics, stride 1), with Phase 20 alongside, and answer explicitly:
   (i) does "nudging puts tropical age on CLaMS" (Phase 12 run 4) survive the fixed drag? (note 21a also
   moved the nudging cutoff 150 -> 400 hPa, so separate the two causes as far as the data allow and say
   where they cannot be separated); (ii) does "free-running lower-stratospheric tropical w* is downward"
   (Phase 14) survive? Open questions / follow-ups.
2. PROGRESS.md row. 3. Commit in /data/JCM_stripped/jcm-strat-phase21 (no push).
4. Memory file phase21-fullphys-rerun.md (+ one MEMORY.md line), linked to [[jcm-pr1027-sso-bug]],
   [[phase12-circulation]], [[phase14-free-physics]], [[phase20-sso-fixed]].
5. STATUS.md entry and top block; if Phases 19 and 20 are recorded too, say in STATUS.md that the
   Phase 19-21 plan is complete.
