#!/usr/bin/env bash
# p20bt 1990-2039 (50 years; ERA5 recycled from 2023, see scripts/p20bt_50yr.sh): year-by-year drift of age, vortex and
# polar-cap T, the age at the end (2035-2039) and in 2005-2009 against CLaMS/WACCM, and the 10 hPa vortex series.
# One job at a time under scripts/memcap.sh. Log runs/p20bt_50yr_plots.log.
#   tmux new-session -d -s eval_p20bt_50yr 'bash scripts/p20bt_50yr_plots.sh'
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
OUT="$REPO/docs/outputs/p20bt_50yr"; A=runs/p20bt_50yr; LOG="$REPO/runs/p20bt_50yr_plots.log"; mkdir -p "$OUT"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 96G -- "$REPO/.venv/bin/python" "$@"; }
say() { echo "[p20bt-50] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
say "start, commit $(git rev-parse --short HEAD)"
for v in aoa_sfc aoa150; do
  py scripts/aoa_vs_clams.py "$A" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P20b 1990-2039 [$v]: age over 2035-2039 vs CLaMS/WACCM 2005-2009" > "runs/p20bt_50yr_aoa_$v.log" 2>&1
  say "end-state age $v exit=$?"
done
py scripts/vortex_series.py "$A" "$OUT/p20bt_50yr_vortex_series.png" --start 1990-01-01 > runs/p20bt_50yr_vortex.log 2>&1
say "vortex series exit=$?"
py scripts/long_run_series.py "$A" "$OUT" --start 1990-01-01 --recycle-from 2023 \
  --label "P20b 1990-2039 (ERA5 nudging recycled 1991-2007 from 2023)" > "$OUT/p20bt_50yr_series.txt" 2>&1
say "long-run series exit=$?"
say "finished"
