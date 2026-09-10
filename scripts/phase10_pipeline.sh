#!/usr/bin/env bash
# Phase 10 unattended pipeline (tmux strat_p10_pipeline): wait for the ERA5 prefetch, run the unit
# tests, a 5-day and a 30-day GPU smoke of p10_prod, then the 2005-2009 chain (chain_segments.sh).
# Each step is gated on the previous one. Progress: runs/p10_pipeline.log; step logs beside it.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
LOG="$REPO/runs/p10_pipeline.log"; mkdir -p "$REPO/runs"
step() { echo "[p10] $(date -Is) $*" | tee -a "$LOG"; }
FILT='cuda\|CUDA\|plugin\|jaxlib\|^\s*File\|\^$\|Traceback\|RuntimeError\|_check_cuda\|for d in'

step "pipeline start, commit $(git rev-parse --short HEAD), GPU ${CUDA_VISIBLE_DEVICES:-0}"
while tmux has-session -t p10_prefetch 2>/dev/null; do sleep 60; done
for f in wb2_192x96_l63_35c39d41_2007-12-31_2009-01-03_6h_u-v-T.nc wb2_192x96_l63_35c39d41_2004-12-31_2005-02-02_6h_u-v-T.nc; do
  [ -s "$REPO/cache/era5/$f" ] || { step "FAIL: ERA5 window $f missing after prefetch"; exit 1; }
done
step "ERA5 windows present"

JAX_PLATFORMS=cpu python -m pytest tests -q 2>&1 | grep -v "$FILT" > runs/p10_tests.log; rc=${PIPESTATUS[0]}
step "unit tests exit=$rc: $(tail -1 runs/p10_tests.log)"
[ $rc -eq 0 ] || { step "FAIL: tests"; exit 1; }

smoke() {  # name days chunk
  local name=$1 days=$2 chunk=$3 rundir="$REPO/runs/$1"; mkdir -p "$rundir"
  step "smoke $name: $days d"
  ( cd "$rundir" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p10_prod \
      run.start_date=2005-01-01 "run.total_time=$days" "run.chunk_days=$chunk" \
      physics.terms.held_suarez.qbo.year=2005 physics.terms.production_tracers.first_segment=true \
      hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?
  step "smoke $name exit=$rc; files: $(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l), $(du -sh "$rundir" 2>/dev/null | cut -f1)"
  grep -i "resource_exhausted\|nan" "$rundir/log.txt" | head -3 | tee -a "$LOG"
  return $rc
}
smoke p10_smoke5 5 5 || { step "FAIL: 5-day smoke"; exit 1; }
smoke p10_smoke30 30 10 || { step "FAIL: 30-day smoke"; exit 1; }

step "launching the 2005-2009 chain"
EXPERIMENT=p10_prod PREFIX=p10 SCHEME=calendar YEARS=2005-2009 AGG=p10_5yr SAVE_INTERVAL=0.25 GPU="${CUDA_VISIBLE_DEVICES:-0}" \
  bash "$REPO/scripts/chain_segments.sh"; rc=$?
step "chain exit=$rc"
step "pipeline finished"
