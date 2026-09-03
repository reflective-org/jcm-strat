#!/usr/bin/env bash
# Phase 7 second wave: when a GPU's first sweep run ends, launch its follow-up on the same GPU.
#   GPU 0: p7_dt30  -> p7_dt90
#   GPU 1: p7_dt60  -> p7_dt60_it2   (two departure iterations)
#   GPU 2: p7_dt120 -> p7_dt120_it2
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
step() { echo "[p7q] $(date -Is) $*"; }
wait_session_gone() { while tmux ls 2>/dev/null | grep -q "^$1:"; do sleep 20; done; }
follow() {  # gpu session_to_wait name overrides...
  local gpu="$1" wait="$2" name="$3"; shift 3
  wait_session_gone "$wait"; sleep 10
  step "launch $name on GPU $gpu: $*"
  if [ "$gpu" = 0 ]; then scripts/launch.sh "$name" +experiment=p6_pk "$@"; else scripts/launch_gpu.sh "$gpu" "$name" +experiment=p6_pk "$@"; fi
}
follow 0 strat_p7_dt30   p7_dt90      run.time_step=90 &
follow 1 strat1_p7_dt60  p7_dt60_it2  run.time_step=60  ++sl_departure_iterations=2 &
follow 2 strat2_p7_dt120 p7_dt120_it2 run.time_step=120 ++sl_departure_iterations=2 &
wait; step "second wave launched"
