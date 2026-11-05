#!/usr/bin/env bash
# p20bt continued to 50 years (Susanne 2026-10-28): 2010-2039 on from p20bt_20090101's checkpoint, same experiment
# (p20b_ext), same chain. The WB2 ERA5 nudging store ends 2023-01-10, so 2010-2022 are nudged to the real years and
# model years 2023-2039 to ERA5 1991-2007 (ERA5_RECYCLE="2023 32": a multiple of 4, so the leap years agree; Susanne
# chose "real to 2022, then recycle"). The tracers see only the fraction of the year, so their clocks and pulses run on
# across the switch. 1990-2009 are finished and skipped; runs/p20bt_20yr is left as it is, the new aggregate is
# runs/p20bt_50yr. A health stop ends the chain (no rescue). Log runs/p20bt_50yr.log, chain log runs/p20bt_chain.log.
#   tmux new-session -d -s train_p20bt_50yr 'GPU=1 bash scripts/p20bt_50yr.sh'
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${GPU:-1}"; PREFIX=p20bt; AGG=p20bt_50yr; MIN_FREE_GB="${MIN_FREE_GB:-6000}"
LOG="$REPO/runs/p20bt_50yr.log"
say() { echo "[p20bt-50yr] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
free=$(df -BG --output=avail /data | tail -1 | tr -dc 0-9)
[ "$free" -ge "$MIN_FREE_GB" ] || { say "FAIL: only ${free} GB free on /data"; exit 1; }
# the main checkout's QBO reference (era5_glob) must have the real years 2021-2022 as well
for y in 2021 2022; do
  ls /data/JCM_stripped/jcm-strat/cache/era5_ref/era5_zm_monthly_$y.nc >/dev/null 2>&1 || { say "FAIL: no jcm-strat/cache/era5_ref/era5_zm_monthly_$y.nc"; exit 1; }
done
# 2012-2022 nudging windows are prefetched on the CPU (tmux preproc_p20bt_era5win); a segment whose window is missing would
# build it itself, far slower, and could race the prefetch on the same file - so wait for the prefetch to end first
PF="$REPO/runs/p20bt_prefetch_2012-2022.log"
until grep -q '^PREFETCH_EXIT=' "$PF" 2>/dev/null; do sleep 60; done
grep -q '^PREFETCH_EXIT=0$' "$PF" || { say "FAIL: window prefetch failed ($PF)"; exit 1; }
say "start: $PREFIX 2010-2039 on GPU $GPU (ERA5 recycled from 2023: 1991-2007), commit $(git rev-parse --short HEAD), free ${free} GB"
SPINUP="1989-12-01 31" EXPERIMENT=p20b_ext PREFIX=$PREFIX SCHEME=calendar YEARS=1990-2039 AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" \
  ERA5_RECYCLE="2023 32" bash scripts/chain_segments.sh >> runs/${PREFIX}_chain_stdout.log 2>&1
rc=$?; bad=$(grep -l 'atmosphere unhealthy' runs/${PREFIX}_*0101/log.txt 2>/dev/null | tr '\n' ' ')
[ $rc -eq 0 ] && [ -z "$bad" ] || { say "FAIL: chain exit=$rc, health stops: ${bad:-none} (runs/${PREFIX}_chain.log)"; exit 1; }
say "finished -> runs/$AGG"
