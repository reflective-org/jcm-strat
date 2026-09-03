#!/usr/bin/env bash
# Second Phase 6 queue, on GPU 2: the wider-season (season_offset 0.5) variants, sequential.
#   tmux new-session -d -s chain_p6_ab2 'bash scripts/phase6_ab_gpu2.sh 2>&1 | tee runs/p6_ab_gpu2_chain.log'
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
step() { echo "[p6_ab2] $(date -Is) $*"; }
wait_free() { while tmux ls 2>/dev/null | grep -q '^strat2_'; do sleep 20; done; }
done_ok() { grep -q '\[launch\].*exit=0' "$REPO/runs/$1/log.txt" 2>/dev/null; }
declare -a NAMES=(p6_pk_g4_t40_s05 p6_pk_g4_t15_s05)
declare -A OVR=(
  [p6_pk_g4_t40_s05]="physics.terms.held_suarez.season_offset=0.5"
  [p6_pk_g4_t15_s05]="physics.terms.held_suarez.season_offset=0.5 physics.terms.held_suarez.tau_strat_days=15"
)
for n in "${NAMES[@]}"; do
  wait_free
  if done_ok "$n"; then step "skip $n (done)"; continue; fi
  step "launch $n ${OVR[$n]}"
  # shellcheck disable=SC2086
  scripts/launch_gpu.sh 2 "$n" +experiment=p6_pk ${OVR[$n]} || { step "launch of $n refused"; exit 1; }
  sleep 30; wait_free
  if done_ok "$n"; then step "done $n"; else step "$n FAILED"; fi
done
step "chain finished"
