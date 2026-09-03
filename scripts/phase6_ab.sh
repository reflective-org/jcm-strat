#!/usr/bin/env bash
# Phase 6 A/B queue on GPU 0, strictly sequential: waits for any running strat_* session, then
# launches each configuration with scripts/launch.sh and waits for it, then runs the comparison.
#   tmux new-session -d -s chain_p6_ab 'bash scripts/phase6_ab.sh 2>&1 | tee runs/p6_ab_chain.log'
# Restartable: a run whose log ends in exit=0 is skipped.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
step() { echo "[p6_ab] $(date -Is) $*"; }
wait_free() { while tmux ls 2>/dev/null | grep -q '^strat_'; do sleep 20; done; }
done_ok() { grep -q '\[launch\].*exit=0' "$REPO/runs/$1/log.txt" 2>/dev/null; }

declare -a NAMES=(p6_pk_g4_t40 p6_pk_g4_t15 p6_pk_g2_t40)
declare -A OVR=(
  [p6_pk_g4_t40]=""
  [p6_pk_g4_t15]="physics.terms.held_suarez.tau_strat_days=15"
  [p6_pk_g2_t40]="physics.terms.held_suarez.gamma_k_per_km=2"
)
for n in "${NAMES[@]}"; do
  wait_free
  if done_ok "$n"; then step "skip $n (done)"; continue; fi
  step "launch $n ${OVR[$n]}"
  # shellcheck disable=SC2086
  scripts/launch.sh "$n" +experiment=p6_pk ${OVR[$n]} || { step "launch of $n refused"; exit 1; }
  sleep 30; wait_free
  if done_ok "$n"; then step "done $n"; else step "$n FAILED (see runs/$n/log.txt)"; fi
done

step "comparison"
source scripts/env.sh
args=(--run P3_HS=/data/JCM_stripped/jcm-strat/runs/p3_tracers_1yr)
for n in "${NAMES[@]}"; do done_ok "$n" && args+=(--run "$n=runs/$n"); done
done_ok ref_echam_sd_2005 && args+=(--run ECHAM_SD=runs/ref_echam_sd_2005)
mkdir -p docs/outputs/06_stratosphere
JAX_PLATFORMS=cpu python scripts/strat_compare.py docs/outputs/06_stratosphere "${args[@]}" --years 2005-2005
step "chain finished"
