#!/usr/bin/env bash
# Phase 23 diagnostics, second pass (2026-10-22). strat_circulation reads EVERY file of the aggregate whatever --years says,
# so on the 18-year aggregates it ran for hours and, four at a time, was OOM-killed (L0, LAL7: exit 137); the node reboot at
# 09:44 PDT then killed AL7's. Here: 2006-2007-only aggregates runs/p23d_<run>_0607, strat_circulation for all four (P20b's
# earlier one used all 18 years for the TEM part, so it is redone for consistency), plus AL7's missing vortex/seasonal.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
PY="$REPO/.venv/bin/python"; OUT="$REPO/docs/outputs/23_lat_nudging"; LOG="$REPO/runs/p23_diag.log"
step() { echo "[p23 diag2] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
circ() { "$PY" scripts/strat_circulation.py "runs/p23d_$1_0607" "$OUT/$1" --years 2006-2007 --label "$1" --age-var aoa_sfc > "runs/p23_diag_$1_circ.log" 2>&1; step "$1 strat_circulation exit=$?"; }
step "start"
( "$PY" scripts/vortex_jets.py runs/p23d_AL7_0607 "$OUT/AL7" --years 2006-2007 --label AL7 > runs/p23_diag_AL7_vortex.log 2>&1; step "AL7 vortex_jets exit=$?"
  "$PY" scripts/seasonal_age_winds.py runs/p23d_AL7_0607 "$OUT/AL7" --years 2006-2007 --label AL7 > runs/p23_diag_AL7_seasonal.log 2>&1; step "AL7 seasonal exit=$?" ) &
circ P20b & circ AL7 & circ L0 & circ LAL7 & wait
step "finished"
