You are the write-up agent for jcm-strat Phase 19 (jcm update + precision check + 19d baseline). The
pipeline scripts/phase19_run.sh has just finished its runs and diagnostics. Work in the worktree
/data/JCM_stripped/jcm-strat-phase19 (branch phase19-jcm-update).

Read: docs/outputs/19_jcm_update/decisions.md; runs/p19_run.log; docs/outputs/19_jcm_update/*.md
(metrics: p19_ps_gate.md, update_metrics.md, vs13d_metrics.md, p19_mesosphere.md, scores/*.json),
and look at the PNGs there. Old-jcm reference records: /data/JCM_stripped/jcm-strat-phase13/docs/outputs/13c_jucker_n400/
and 13d_jucker_hines/ (10yr/ subdir is stride 1).

Then:
1. Write docs/outputs/19_jcm_update/output.md (create it if absent; keep anything already there). Sections:
   what was run (exact commands from the log, commit SHAs, wall-clock, GPU), 19a environment (jcm SHA,
   dinosaur version and how installed), 19b precision check - all four items explicitly
   (1 grep hits, 2 the echoed values before/after build from runs/p19jhn400_19900101/log.txt, 3 the
   dot_precision_test result runs/p19b_dot_precision_test.log, 4 the 30-day ps gate table + plot),
   19c port summary (from decisions.md), 19d Results vs OLD p13jhn400 first 5 yr (same physics, old jcm)
   and p13jh (13d) for context: tropical w* 100/70/50/30/10 hPa vs WACCM (stride 1), mass flux,
   aoa150 entry age vs WACCM, surface clock vs CLaMS, mesosphere, u/T scores - with the figures
   embedded; an acceptance-style table; "What changed and why" (jcm update alone: dinosaur 1.5 hybrid
   T equation, moist Tv, ECHAM sponge, cubic SL, mass fixers); Open questions / follow-ups.
2. Add a Phase 19 row to PROGRESS.md (same style as the existing rows).
3. Commit (git add docs/outputs/19_jcm_update PROGRESS.md; message "Phase 19: record ..."). No push.
4. Update the memory: create/refresh memory file phase19-jcm-update.md (frontmatter name/description/
   metadata type project; body with the key numbers and where things are; link [[jcm-pr1027-sso-bug]],
   [[phase13c-n400]], [[phase13d-jucker-hines]]) and make sure MEMORY.md has exactly one line for it.
5. Append a STATUS.md entry and refresh its top block.
