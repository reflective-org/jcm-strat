#!/usr/bin/env bash
# Phase 20b, 20 years with every tracer written (Susanne 2026-10-15/16): runs/p20b (1990-1998) wrote only the age clocks,
# n2o and cfc11, and the pulses/SAI/sources are injected once on 1990-01-01 - writing them from 1999 on would miss their
# first 9 years. So the whole run is redone as p20bt with experiment p20b_ext (all tracers written 6-hourly) from the same
# 1989-12-01 spin-up, 1990-2009 -> runs/p20bt_20yr.
# A health stop ends the chain (no rescue; Phase 20b needs none so far). Then DJF/JJA age + winds, strat_compare and
# age vs CLaMS/WACCM for 2005-2009. Log runs/p20b_ext.log.
#   tmux new-session -d -s strat_p20bt 'GPU=0 bash scripts/p20b_extend.sh'
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${GPU:-0}"; PREFIX=p20bt; AGG=p20bt_20yr; MIN_FREE_GB="${MIN_FREE_GB:-5000}"
OUT=/data/JCM_stripped/jcm-strat-phase20/docs/outputs/20_sso_fixed/p20b_extension
LOG="$REPO/runs/p20b_ext.log"; mkdir -p "$OUT"
say() { echo "[p20b-ext] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
[ "$free" -ge "$MIN_FREE_GB" ] || { say "FAIL: only ${free} GB free on /data"; exit 1; }
say "start: $PREFIX 1990-2009 on GPU $GPU, experiment p20b_ext, commit $(git rev-parse --short HEAD), free ${free} GB"
SPINUP="1989-12-01 31" EXPERIMENT=p20b_ext PREFIX=$PREFIX SCHEME=calendar YEARS=1990-2009 AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1
rc=$?; bad=$(grep -l 'atmosphere unhealthy' runs/${PREFIX}_*0101/log.txt 2>/dev/null | tr '\n' ' ')
[ $rc -eq 0 ] && [ -z "$bad" ] || { say "FAIL: chain exit=$rc, health stops: ${bad:-none} (runs/${PREFIX}_chain.log)"; exit 1; }
say "chain done -> runs/$AGG"
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
python scripts/seasonal_age_winds.py "runs/$AGG" "$OUT" --years 2005-2009 --label "P20b fixed Lott-Miller, bottom levels nudged" > runs/p20b_ext_seasonal.log 2>&1
say "seasonal age + winds 2005-2009 exit=$?"
python scripts/strat_compare.py "$OUT" --run "P20b=runs/$AGG" --years 2005-2009 > runs/p20b_ext_strat_compare.log 2>&1
say "strat_compare 2005-2009 exit=$?"
for v in aoa150 aoa_sfc; do
  python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P20b 1990-2009 [$v]: age at the end vs CLaMS/WACCM" > "runs/p20b_ext_aoa_$v.log" 2>&1
  say "aoa $v exit=$?"
done
say "finished"
