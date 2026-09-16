#!/usr/bin/env bash
# Third Phase 6 queue, GPU 0: the vortex-top taper on the best relaxation settings so far.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
step() { echo "[p6_ab0b] $(date -Is) $*"; }
wait_free() { while tmux ls 2>/dev/null | grep -q '^strat_'; do sleep 20; done; }
done_ok() { grep -q '\[launch\].*exit=0' "$REPO/runs/$1/log.txt" 2>/dev/null; }
declare -a NAMES=(p6_pk_g4_t15_s05_top10)
declare -A OVR=(
  [p6_pk_g4_t15_s05_top10]="physics.terms.held_suarez.season_offset=0.5 physics.terms.held_suarez.tau_strat_days=15 physics.terms.held_suarez.p_vortex_top_hpa=10"
)
for n in "${NAMES[@]}"; do
  wait_free
  if done_ok "$n"; then step "skip $n (done)"; continue; fi
  step "launch $n ${OVR[$n]}"
  # shellcheck disable=SC2086
  scripts/launch.sh "$n" +experiment=p6_pk ${OVR[$n]} || { step "launch of $n refused"; exit 1; }
  sleep 30; wait_free
  if done_ok "$n"; then step "done $n"; else step "$n FAILED"; fi
done
step "chain finished"
