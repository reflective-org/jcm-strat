#!/usr/bin/env bash
# Phase 10 production: the 1990-2019 chain, unattended (tmux strat_p10_30yr). Waits for the four
# ERA5 prefetch streams (runs/p10_prefetch_{a,b,c,d}.log) and the CDS QBO target (cache/era5_ref,
# 1989-2020), runs a 5-day GPU smoke of p10_prod, then scripts/chain_segments.sh for 1990-2019 into
# runs/p10_<YYYY>0101 and the aggregate runs/p10_30yr. Progress: runs/p10_run30.log.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
LOG="$REPO/runs/p10_run30.log"; mkdir -p "$REPO/runs"
step() { echo "[p10-30yr] $(date -Is) $*" | tee -a "$LOG"; }
step "start, commit $(git rev-parse --short HEAD), GPU ${CUDA_VISIBLE_DEVICES:-0}"

until [ "$(grep -l PREFETCH_DONE runs/p10_prefetch_?.log 2>/dev/null | wc -l)" -ge 4 ]; do sleep 120; done
step "ERA5 prefetch streams finished"
for y in $(seq 1989 2020); do
  until [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ]; do sleep 120; done
done
step "CDS QBO target 1989-2020 present"
missing=0
for y in $(seq 1990 2019); do
  n=$(( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) )); n=$(( n / 86400 ))
  end=$(date -d "$y-01-01 + $((n+2)) days" +%F); start=$(date -d "$y-01-01 - 1 day" +%F)
  f="$REPO/cache/era5/wb2_192x96_l63_35c39d41_${start}_${end}_6h_u-v-T.nc"
  [ -s "$f" ] || { step "MISSING ERA5 window for $y: $f"; missing=1; }
done
[ $missing -eq 0 ] || { step "FAIL: ERA5 windows missing"; exit 1; }
step "all 30 ERA5 windows present"

rundir="$REPO/runs/p10_smoke5_v2"; mkdir -p "$rundir"
( cd "$rundir" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p10_prod \
    run.start_date=2005-01-01 run.total_time=5 run.chunk_days=5 physics.terms.held_suarez.qbo.year=2005 \
    physics.terms.production_tracers.first_segment=true hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
rc=$?; step "smoke p10_smoke5_v2 exit=$rc ($(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l) files)"
[ $rc -eq 0 ] || { step "FAIL: smoke"; exit 1; }

step "launching the 1990-2019 chain"
EXPERIMENT=p10_prod PREFIX=p10 SCHEME=calendar YEARS=1990-2019 AGG=p10_30yr SAVE_INTERVAL=0.25 GPU="${CUDA_VISIBLE_DEVICES:-0}" \
  bash "$REPO/scripts/chain_segments.sh"; rc=$?
step "chain exit=$rc"
step "finished"
