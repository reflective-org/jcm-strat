#!/usr/bin/env bash
# Phase 23 diagnostics (CPU): the four runs over the same years, 2006-2007 (2005 is the restart's adjustment year;
# sweep_score's window is the last two years of each archive, so P20b gets an aggregate that also ends in 2007).
#   P20b = p20bt 1990-2007 (runs/p23_P20bref_agg), AL7 = runs/p22_AL7_agg, L0 = runs/p23_L0_agg, LAL7 = runs/p23_LAL7_agg
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
py() { bash "$REPO/scripts/memcap.sh" -m 96G -- "$REPO/.venv/bin/python" "$@"; }   # memory-capped (scripts/memcap.sh)
OUT="$REPO/docs/outputs/23_lat_nudging"; LOG="$REPO/runs/p23_diag.log"
step() { echo "[p23 diag] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
[ -e runs/p23_P20bref_agg/log.txt ] || py scripts/link_segments.py runs/p23_P20bref_agg $(for y in $(seq 1990 2007); do echo "$REPO/runs/p20bt_${y}0101"; done) >> "$LOG" 2>&1
diag() {  # <name> <agg>
  local n="$1" a="runs/$2" d="$OUT/$1"; mkdir -p "$d"
  py scripts/sweep_score.py "$a" --name "$n" --out "$OUT/sweep" --desc "Phase 23 $n, 2006-2007" > "runs/p23_diag_${n}_sweep.log" 2>&1; step "$n sweep_score exit=$?"
  py scripts/strat_circulation.py "$a" "$d" --years 2006-2007 --label "$n" > "runs/p23_diag_${n}_circ.log" 2>&1; step "$n strat_circulation exit=$?"
  py scripts/vortex_jets.py "$a" "$d" --years 2006-2007 --label "$n" > "runs/p23_diag_${n}_vortex.log" 2>&1; step "$n vortex_jets exit=$?"
  py scripts/seasonal_age_winds.py "$a" "$d" --years 2006-2007 --label "$n" > "runs/p23_diag_${n}_seasonal.log" 2>&1; step "$n seasonal exit=$?"
}
step "start"
diag P20b p23_P20bref_agg & diag AL7 p22_AL7_agg & diag L0 p23_L0_agg & diag LAL7 p23_LAL7_agg & wait
step "finished"
