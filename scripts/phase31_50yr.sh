#!/usr/bin/env bash
# AL7h for 50 years, AL7h throughout (Susanne 2026-11-13): a NEW chain p31_AL7h50, 1990-2039, every segment (spin-up included)
# with the AL7h T_e correction - unlike the p25_AL7h chain, whose 1990-2004 are links to P20b (p20bt). It is p20bt_50yr with
# the correction added and nothing else changed, so the two 50-yr runs compare year for year and variable for variable:
#   - experiment p20b_ext = p20b_sso_pbl0 physics/nudging/tracers (= p22_teq's) with every tracer written (Susanne chose
#     "all tracers, like p20bt"; ~180 GB/yr); production tracers injected on 1990-01-01 (chain_segments FIRST_SEG_EXTRA default)
#   - 31-day spin-up from ERA5 on 1989-12-01 (AL7h on), QBO tau 1 d, QBO target year = ERA5 year
#   - ERA5: real years to 2022, model 2023-2039 nudged to ERA5 1991-2007 (ERA5_RECYCLE="2023 32", multiple of 4 -> leap years
#     agree; WB2 store ends 2023-01-10); tracer clocks run on
# A health stop ends the chain (no rescue). Restartable (finished segments are skipped).
# The earlier p25_AL7h 2020-2039 extension (P20b 1990-2004 underneath) was stopped during 2029; its 2020-2028 are kept.
#   tmux new-session -d -s train_p31_al7h50 'GPU=2 bash scripts/phase31_50yr.sh'     log runs/p31_AL7h50.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
LOG="$REPO/runs/p31_AL7h50.log"; GPU="${GPU:-2}"; MIN_FREE_GB="${MIN_FREE_GB:-12000}"
PREFIX=p31_AL7h50; AGG=p31_AL7h50_1990_2039
CORR="$REPO/docs/outputs/25_al7_half/corrections/AL7h.nc"
EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total"
step() { echo "[p31-AL7h50] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
[ "$free" -ge "$MIN_FREE_GB" ] || { step "FAIL: only ${free} GB free on /data"; exit 1; }
[ -f "$CORR" ] || { step "FAIL: no correction file $CORR"; exit 1; }
step "start, commit $(git rev-parse --short HEAD) (+ working tree), free ${free} GB"
while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
step "$PREFIX 1990-2039 (spin-up 1989-12), AL7h on every segment, all tracers, GPU $GPU, ERA5 recycled from 2023 (1991-2007)"; t1=$(date +%s)
SPINUP="1989-12-01 31" EXPERIMENT=p20b_ext PREFIX=$PREFIX SCHEME=calendar YEARS=1990-2039 AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  EXTRA="$EXTRA" ERA5_RECYCLE="2023 32" bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1; rc=$?
bad=$(grep -l 'atmosphere unhealthy' runs/${PREFIX}_*/log.txt 2>/dev/null | tr '\n' ' ')
step "chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED (runs/${PREFIX}_chain.log)"; exit 1; fi
touch runs/${PREFIX}.done
step "finished -> runs/$AGG"
