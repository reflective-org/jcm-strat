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
