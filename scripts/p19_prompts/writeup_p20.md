You are the write-up agent for jcm-strat Phase 20 (dry 13d physics + FIXED Lott-Miller SSO, strat81,
nudging < 400 hPa, new jcm, 10 yr 1990-1999 after a one-month spin-up). The pipeline
/data/JCM_stripped/jcm-strat-phase19/scripts/phase20_run.sh has just finished. Runs live in
/data/JCM_stripped/jcm-strat-phase19/runs (p20jhsso_*); the record lives in the worktree
/data/JCM_stripped/jcm-strat-phase20 (branch phase20-sso-fixed): docs/outputs/20_sso_fixed/.

Read: docs/outputs/20_sso_fixed/decisions.md (if any) and the Phase 19 one
(/data/JCM_stripped/jcm-strat-phase19/docs/outputs/19_jcm_update/decisions.md); runs/p20_run.log;
the metrics in docs/outputs/20_sso_fixed/ (sso5_vs_19d_metrics.md = THE comparison: same code, with vs
without SSO; sso10_vs_13c1/13c2/13d_metrics.md vs the old-jcm runs; scores/*.json with ERA5 1998-99 w*
and mass flux for the 10-yr run; p20_mesosphere.md; p20_spinup_adjust.md) and look at every PNG.
If the Phase 19 record output.md exists, read its Results for the 19d numbers.

Then:
1. Write docs/outputs/20_sso_fixed/output.md: what was run (commands, SHAs, wall-clock, GPU), Results at
   5 and 10 yr: tropical w* 100/70/50/30/10 hPa vs WACCM (stride 1), upward mass flux vs ERA5 (1998-99)
   and WACCM, aoa150 entry age vs WACCM, surface clock vs CLaMS, mesosphere check, and the angular-momentum
   / 300 hPa u adjustment through the spin-up month (was one month enough? answer from the trend columns).
   Include this note: the colleague's "25 % weak 100/70 hPa w*" is the stride-4 reading; at stride 1 13d
   had 100 hPa 0.35 vs WACCM 0.40 but 70 hPa 0.30 vs 0.21. Verdict on whether the fixed Lott-Miller helps
   the dry config (compared with 19d), Open questions / follow-ups (just list them).
2. PROGRESS.md row for Phase 20. 3. Commit in /data/JCM_stripped/jcm-strat-phase20 (no push).
4. Memory file phase20-sso-fixed.md (+ one MEMORY.md line), linked to [[jcm-pr1027-sso-bug]] and
   [[phase19-jcm-update]]. 5. STATUS.md entry and top block.
