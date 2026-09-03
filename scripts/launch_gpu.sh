#!/usr/bin/env bash
# Launch one jcm run in a detached tmux session on a GPU other than 0 (GPUs 1 and 2 were released
# to this project on 2026-09-03; GPUs 3-7 stay off limits).
#
#   scripts/launch_gpu.sh <gpu> <session> <hydra overrides...>
#
# Same contract as launch.sh (runs/<session>/, log.txt, .hydra/) but the tmux session is named
# strat<gpu>_<session> so launch.sh's strat_* guard for GPU 0 is not triggered, and the busy check
# is per GPU: it refuses if that GPU already has a process or a strat<gpu>_* session.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ $# -ge 2 ] || { echo "usage: $0 <gpu 1|2> <session> <hydra overrides...>"; exit 2; }
gpu="$1"; name="$2"; shift 2
case "$gpu" in 1|2) ;; *) echo "refusing: only GPUs 1 and 2 are released to this project"; exit 1;; esac
session="strat${gpu}_${name}"
if tmux ls 2>/dev/null | grep -q "^strat${gpu}_"; then
  echo "refusing: a strat${gpu}_* session is running:"; tmux ls | grep "^strat${gpu}_"; exit 1
fi
if nvidia-smi -i "$gpu" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then
  echo "refusing: GPU $gpu is busy:"; nvidia-smi -i "$gpu" --query-compute-apps=pid,process_name,used_memory --format=csv; exit 1
fi
rundir="$REPO/runs/$name"; mkdir -p "$rundir"
overrides=""; for a in "$@"; do overrides+=" $(printf '%q' "$a")"; done
cmd="source $REPO/scripts/env.sh && export CUDA_VISIBLE_DEVICES=$gpu && cd $rundir && \
echo \"[launch] \$(date -Is) jcm-strat \$(git -C $REPO rev-parse --short HEAD) session=$session GPU=$gpu\" && \
python -m jcm_strat.main --config-dir $REPO/jcm_strat/config$overrides hydra.run.dir=$rundir; rc=\$?; \
echo \"[launch] \$(date -Is) exit=\$rc\""
tmux new-session -d -s "$session" "bash -c $(printf '%q' "$cmd") 2>&1 | tee -a $rundir/log.txt"
echo "launched $session (GPU $gpu) -> $rundir/log.txt"
