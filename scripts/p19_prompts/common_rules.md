## Rules (Susanne's, all binding)
- You run headless; nobody will answer questions. Decide, and log every decision in the phase's
  `decisions.md` (question, all options, choice, why; timestamped PDT, append-only).
- Quote all times in Pacific time (PDT). Get it with `TZ=America/Los_Angeles date`.
- Commit locally only: NEVER push, never open PRs or issues. Commit messages must NOT mention Claude
  or AI and must carry NO Co-Authored-By line.
- Do not start new model runs, do not change model code or configs. Do not touch the main checkout
  /data/JCM_stripped/jcm-strat working tree (except the files named below under scratch/p19_agent/), its
  runs/, or other worktrees' runs/. GPUs: never 5-7.
- Never edit a running bash script in place (`tmux ls` shows what runs).
- The CLAUDE.md files under /data and /data/JCM_stripped describe OTHER projects; they do not apply here.
- Memory directory: /home/susanne/.claude/projects/-data-JCM-stripped/memory/ (index MEMORY.md, one
  line per memory). Read MEMORY.md and the memories it names for this phase first.
- Background: /data/JCM_stripped/jcm-strat/scratch/p19_agent/brief.md (the plan), memory
  jcm-pr1027-sso-bug.md, /data/JCM_stripped/jcm-strat-phase19/docs/outputs/19_jcm_update/decisions.md
  (how Phase 19 was set up: jcm 35dc1997 + dinosaur 1.5.0, one-month spin-up from 1989-12-01 discarded,
  tracers re-initialised 1990-01-01, ECHAM sponge levels=1, cubic SL, nudging < 400 hPa, stride 1).
- Status file: /data/JCM_stripped/jcm-strat/scratch/p19_agent/STATUS.md - keep the short human-readable
  status block at the top current (what runs where, ETA, next step) and append a timestamped entry.
