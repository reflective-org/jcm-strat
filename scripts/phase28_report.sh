#!/usr/bin/env bash
# Phase 28: scorecard v7 = the Phase 27 page plus group D (variability and relations), into docs/outputs/28_variability/report.
# The A-C figures are Phase 27's (unchanged runs and scores); findings.html is written by hand.
#
#   bash scripts/phase28_report.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
OUT="$REPO/docs/outputs/28_variability"; S="$OUT/success_0610"; R="$OUT/report"; R27="$REPO/docs/outputs/27_qbo_nudging/report"
W26="$REPO/../jcm-strat-phase26/docs/outputs/26_5yr_scoring/w0610"; W27="$REPO/docs/outputs/27_qbo_nudging/w0610"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 16G -- "$REPO/.venv/bin/python" "$@"; }
diag() { case "$1" in QBO30|QBO10d) echo "$W27/$1";; *) echo "$W26/$1";; esac; }
NAMES=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d)
mkdir -p "$R"
cp "$R27"/*.png "$R/"; cp "$OUT"/variability_*.png "$R/"
[ -e "$R/notes.html" ] || cp "$R27/notes.html" "$R/"
[ -e "$R/findings.html" ] || cp "$R27/findings.html" "$R/"
WINDOW=2006-2010 py scripts/build_scorecard.py "$S/success_metrics.json" "$R" "$R/findings.html" \
  $(for n in "${NAMES[@]}"; do echo "$n=$(diag $n)"; done)
