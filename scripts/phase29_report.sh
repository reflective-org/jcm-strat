#!/usr/bin/env bash
# Phase 29: scorecard v8 = nine runs (adds LQBO10d), groups A-D, into docs/outputs/29_lqbo10d/report.
# A-C comparison figures redrawn with nine runs; Phase 27's QBO nudging figures reused; findings.html written by hand.
#
#   bash scripts/phase29_report.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
OUT="$REPO/docs/outputs/29_lqbo10d"; S="$OUT/success_0610"; R="$OUT/report"
R27="$REPO/docs/outputs/27_qbo_nudging/report"; R28="$REPO/docs/outputs/28_variability/report"
W26="$REPO/../jcm-strat-phase26/docs/outputs/26_5yr_scoring/w0610"; W27="$REPO/docs/outputs/27_qbo_nudging/w0610"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
diag() { case "$1" in QBO30|QBO10d) echo "$W27/$1";; LQBO10d) echo "$OUT/w0610/$1";; *) echo "$W26/$1";; esac; }
NAMES=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d LQBO10d)
mkdir -p "$R"
py scripts/report_figures.py "$R" $(for n in "${NAMES[@]}"; do echo "$n=$S/raw/sweep/$n.json:$(diag $n)"; done)
cp "$R27"/qbo_nudging.png "$R27"/qbo_upwelling.png "$R/"; cp "$OUT"/variability_*.png "$R/"
[ -e "$R/notes.html" ] || cp "$R28/notes.html" "$R/"
[ -e "$R/findings.html" ] || cp "$R28/findings.html" "$R/"
WINDOW=2006-2010 py scripts/build_scorecard.py "$S/success_metrics.json" "$R" "$R/findings.html" \
  $(for n in "${NAMES[@]}"; do echo "$n=$(diag $n)"; done)
