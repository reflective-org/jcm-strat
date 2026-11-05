#!/usr/bin/env bash
# Phase 27: scorecard figures and page for all eight runs on 2006-2010, plus the QBO nudging comparison
# (AL7h / QBO30 / QBO10d), into docs/outputs/27_qbo_nudging/report. findings.html is written by hand.
#
#   bash scripts/phase27_report.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
OUT="$REPO/docs/outputs/27_qbo_nudging"; S="$OUT/success_0610"; R="$OUT/report"
W26="$REPO/../jcm-strat-phase26/docs/outputs/26_5yr_scoring/w0610"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
diag() { case "$1" in QBO30|QBO10d) echo "$OUT/w0610/$1";; *) echo "$W26/$1";; esac; }
NAMES=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d)
mkdir -p "$R"
py scripts/report_figures.py "$R" $(for n in "${NAMES[@]}"; do echo "$n=$S/raw/sweep/$n.json:$(diag $n)"; done)
py scripts/qbo_compare.py "$R" --years 2006-2010 \
  AL7h=runs/p26_AL7h_0610:$S/raw/sweep/AL7h.json:90:0.35:1 \
  QBO30=runs/p26_QBO30_0610:$S/raw/sweep/QBO30.json:50:0.22:1 \
  QBO10d=runs/p26_QBO10d_0610:$S/raw/sweep/QBO10d.json:90:0.35:10
[ -e "$R/notes.html" ] || cp "$REPO/../jcm-strat-phase26/docs/outputs/26_5yr_scoring/report/notes.html" "$R/"
[ -e "$R/findings.html" ] || cp "$REPO/../jcm-strat-phase26/docs/outputs/26_5yr_scoring/report/findings.html" "$R/"
WINDOW=2006-2010 py scripts/build_scorecard.py "$S/success_metrics.json" "$R" "$R/findings.html" \
  $(for n in "${NAMES[@]}"; do echo "$n=$(diag $n)"; done)
