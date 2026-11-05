#!/usr/bin/env bash
# Phase 25 (Susanne 2026-10-27): AL7 with the T_eq correction at HALF amplitude (AL7h), everywhere else as AL7 -
# does a weaker correction keep most of the vortex while the age of air recovers? Same protocol as AL7 (Phase 22):
# P20b physics and nudging (p22_teq, global top 400 hPa), 2005-2007 from P20b's end-of-2004 state. Then the Phase 23
# diagnostics and the success metrics on 2006-2007, every CPU step under scripts/memcap.sh.
#
#   bash scripts/phase24_run.sh [GPU]      restartable
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${1:-0}"; NAME=AL7h; PRE=p25_AL7h; BASE=p20bt
OUT="$REPO/docs/outputs/25_al7_half"; LOG="$REPO/runs/p25_run.log"
CORR="$OUT/corrections/AL7h.nc"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 96G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p25] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }

step "start, commit $(git rev-parse --short HEAD)"
if [ ! -s "runs/${PRE}_20070101/checkpoint.ckpt" ]; then
  for y in $(seq 1990 2004); do [ -e "runs/${PRE}_${y}0101" ] || ln -s "$REPO/runs/${BASE}_${y}0101" "runs/${PRE}_${y}0101"; done
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
  step "run $NAME on GPU $GPU (2005-2007 from P20b 2004), correction ${CORR##*/}"; t1=$(date +%s)
  EXPERIMENT=p22_teq PREFIX="$PRE" SCHEME=calendar YEARS=1990-2007 AGG="${PRE}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" \
    EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total" \
    bash scripts/chain_segments.sh > "runs/${PRE}_chain_stdout.log" 2>&1; rc=$?
  bad=$(grep -l 'atmosphere unhealthy' runs/${PRE}_200[5-7]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  { [ $rc -eq 0 ] && [ -z "$bad" ]; } || { step "FAILED (runs/${PRE}_chain.log)"; exit 1; }
fi
A="runs/p23d_${NAME}_0607"
[ -e "$A/log.txt" ] || py scripts/link_segments.py "$A" "$REPO/runs/${PRE}_20060101" "$REPO/runs/${PRE}_20070101" >> "$LOG" 2>&1
mkdir -p "$OUT/$NAME"
py scripts/vortex_jets.py "$A" "$OUT/$NAME" --years 2006-2007 --label "$NAME" > "runs/p25_vortex.log" 2>&1; step "vortex_jets exit=$?"
py scripts/seasonal_age_winds.py "$A" "$OUT/$NAME" --years 2006-2007 --label "$NAME" > "runs/p25_seasonal.log" 2>&1; step "seasonal exit=$?"
py scripts/strat_circulation.py "$A" "$OUT/$NAME" --years 2006-2007 --label "$NAME" --age-var aoa_sfc > "runs/p25_circ.log" 2>&1; step "strat_circulation exit=$?"
# success metrics: earlier raw scores are reused (copied), only AL7h is scored new
S="$OUT/success"; mkdir -p "$S/raw/sweep" "$S/raw/teq"
for d in 23_lat_nudging 24_al7_taper; do cp -n "$REPO/docs/outputs/$d/success/raw/sweep/"*.json "$S/raw/sweep/"; cp -n "$REPO/docs/outputs/$d/success/raw/teq/"*.json "$S/raw/teq/"; done
py scripts/success_metrics.py "$S" P20b=runs/p23d_P20b_0607 AL7=runs/p23d_AL7_0607 L0=runs/p23d_L0_0607 LAL7=runs/p23d_LAL7_0607 AL7t=runs/p23d_AL7t_0607 "$NAME=$A" \
  > runs/p25_success.log 2>&1; step "success_metrics exit=$?"
git add "$OUT" && git commit -q -m "Phase 25: AL7h (AL7 correction at half amplitude) - diagnostics and success metrics" && step "committed"
step "finished"
