#!/usr/bin/env bash
# Phase 26: once phase26_2010.sh has scored all six runs on 2006-2010, rebuild the scorecard figures and page into
# docs/outputs/26_5yr_scoring/report and commit. The findings block is a placeholder until it is rewritten by hand;
# publishing the page to its artifact URL is done from a session.
#
#   bash scripts/phase26_report.sh
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
OUT="$REPO/docs/outputs/26_5yr_scoring"; S="$OUT/success_0610"; R="$OUT/report"; LOG="$REPO/runs/p26b_run.log"
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p26r] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }

while tmux has-session -t strat_p26b_run 2>/dev/null; do sleep 120; done
NAMES=(); for n in P20b AL7 AL7h AL7t L0 LAL7; do [ -e "$S/raw/sweep/$n.json" ] && NAMES+=("$n"); done
step "scoring finished, ${#NAMES[@]} runs scored: ${NAMES[*]}"
mkdir -p "$R"
py scripts/report_figures.py "$R" $(for n in "${NAMES[@]}"; do echo "$n=$S/raw/sweep/$n.json:$OUT/w0610/$n"; done) > runs/p26r_figures.log 2>&1
step "report_figures exit=$?"
[ -e "$R/notes.html" ] || cp "$REPO/docs/outputs/25_al7_half/report/notes.html" "$R/"
[ -e "$R/findings.html" ] || echo '<p><b>Scored on 2006&ndash;2010.</b> Findings for the five-year window are being written up.</p>' > "$R/findings.html"
WINDOW=2006-2010 py scripts/build_scorecard.py "$S/success_metrics.json" "$R" "$R/findings.html" \
  $(for n in "${NAMES[@]}"; do echo "$n=$OUT/w0610/$n"; done) > runs/p26r_build.log 2>&1
step "build_scorecard exit=$?"
git add "$R" && git commit -q -m "Phase 26: scorecard figures and page for 2006-2010 (findings pending)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && step "report committed"
