#!/usr/bin/env bash
# Phase 7 third wave: GPU 0 p7_dt90 -> p7_dt90_it2; GPU 1 p7_dt60_it2 -> p7_dt45_it2.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
step() { echo "[p7q2] $(date -Is) $*"; }
wait_session_gone() { while tmux ls 2>/dev/null | grep -q "^$1:"; do sleep 20; done; }
follow() { local gpu="$1" wait="$2" name="$3"; shift 3; wait_session_gone "$wait"; sleep 10; step "launch $name on GPU $gpu: $*"
  if [ "$gpu" = 0 ]; then scripts/launch.sh "$name" +experiment=p6_pk "$@"; else scripts/launch_gpu.sh "$gpu" "$name" +experiment=p6_pk "$@"; fi; }
follow 0 strat_p7_dt90      p7_dt90_it2 run.time_step=90 ++sl_departure_iterations=2 &
follow 1 strat1_p7_dt60_it2 p7_dt45_it2 run.time_step=45 ++sl_departure_iterations=2 &
wait; step "third wave launched"
