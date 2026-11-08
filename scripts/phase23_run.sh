#!/usr/bin/env bash
# Phase 23 (Susanne 2026-10-20): latitude-dependent top of the ERA5 nudging (150 hPa tropics -> 400 hPa extratropics,
# experiment p23_lattop, jcm_strat/nudging_lat.py), on Phase 22's protocol so the scores sit next to P20b's and AL7's:
# 1990-2004 are links to P20b's (p20bt) segments, the chain runs 2005-2007 from P20b's end-of-2004 state, and
# 2005-04..2007-12 is scored against ERA5 for the same months (scripts/teq_score.py).
#
#   L0    P20b + lat top                  (compare P20b_base: the nudging top is the only change)
#   LAL7  P20b + AL7 T_eq correction + lat top (compare AL7: the best Phase 22 vortex config)
#
#   bash scripts/phase23_run.sh [GPU]      (default 0); restartable: finished chains and scores are skipped
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${1:-0}"; BASE=p20bt; T0W=2005-04-01; T1W=2008-01-01
OUT="$REPO/docs/outputs/23_lat_nudging"; SC="$OUT/scores"; mkdir -p "$SC"
LOG="$REPO/runs/p23_run.log"; PY="$REPO/.venv/bin/python"
AL7="$REPO/docs/outputs/22_teq_vortex/corrections/AL7.nc"
step() { echo "[p23] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }

run() {  # <name> <desc> [hydra overrides]
  local name="$1" desc="$2" extra="${3:-}" pre="p23_$1"
  if [ -s "$SC/$name.json" ]; then step "$name already scored"; return 0; fi
  for y in $(seq 1990 2004); do [ -e "runs/${pre}_${y}0101" ] || ln -s "$REPO/runs/${BASE}_${y}0101" "runs/${pre}_${y}0101"; done
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
  step "run $name on GPU $GPU (2005-2007 from P20b 2004) overrides: ${extra:-none}"; local t1; t1=$(date +%s)
  EXPERIMENT=p23_lattop PREFIX="$pre" SCHEME=calendar YEARS=1990-2007 AGG="${pre}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$extra" \
    bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout.log" 2>&1; local rc=$?
  local bad; bad=$(grep -l 'atmosphere unhealthy' runs/${pre}_200[5-7]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $name (runs/${pre}_chain.log)"; return 1; fi
  JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" "$PY" scripts/teq_score.py "runs/${pre}_agg" --t0 $T0W --t1 $T1W --name "$name" --desc "$desc" \
    --out "$SC" > "runs/p23_score_$name.log" 2>&1 || { step "score $name FAILED (runs/p23_score_$name.log)"; return 1; }
  step "$(grep '^\[score\]' "runs/p23_score_$name.log" | tail -1 | cut -c1-600)"
  git add "$SC/$name.json" && git commit -q -m "Phase 23: $name scored" && step "committed $name score"
}

step "start, commit $(git rev-parse --short HEAD)"
run L0 "P20b + latitude-dependent nudging top (150 hPa tropics, 400 hPa extratropics)" || exit 1
run LAL7 "AL7 + latitude-dependent nudging top" \
  "++physics.terms.held_suarez.te_correction_file=$AL7 ++physics.terms.held_suarez.te_correction_mode=total" || exit 1
step "finished"
