#!/usr/bin/env bash
# Launch one jcm run in a detached tmux session on GPU 0.
#
#   scripts/launch.sh <session> <hydra overrides...>
#   e.g. scripts/launch.sh p1_dry physics=strat_dry +experiment=p1_dry
#
# Project policy: GPU 0 only, one run at a time. This script refuses to start if a
# strat_* tmux session already exists or if GPU 0 has a process on it.
# Output goes to runs/<session>/ (log.txt, .hydra/, netCDF), never into the tree.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ $# -ge 1 ] || { echo "usage: $0 <session> <hydra overrides...>"; exit 2; }
name="$1"; shift
session="strat_${name}"

if tmux ls 2>/dev/null | grep -q '^strat_'; then
  echo "refusing: a strat_* tmux session is already running:"; tmux ls | grep '^strat_'; exit 1
fi
if nvidia-smi -i 0 --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then
  echo "refusing: GPU 0 is busy:"; nvidia-smi -i 0 --query-compute-apps=pid,process_name,used_memory --format=csv; exit 1
fi

rundir="$REPO/runs/$name"
mkdir -p "$rundir"
overrides=""
for a in "$@"; do overrides+=" $(printf '%q' "$a")"; done
cmd="source $REPO/scripts/env.sh && cd $rundir && \
echo \"[launch] \$(date -Is) jcm-strat \$(git -C $REPO rev-parse --short HEAD) session=$session\" && \
python -m jcm_strat.main --config-dir $REPO/jcm_strat/config$overrides hydra.run.dir=$rundir; rc=\$?; \
echo \"[launch] \$(date -Is) exit=\$rc\""
tmux new-session -d -s "$session" "bash -c $(printf '%q' "$cmd") 2>&1 | tee -a $rundir/log.txt"
echo "launched $session -> $rundir/log.txt   (attach: tmux attach -t $session ; detach: C-b d)"
