#!/usr/bin/env bash
# Phase 10: diagnostics of the 1990-2019 chain once it has finished (tmux p10_analysis30, CPU).
# Waits for "chain exit=0" in runs/p10_run30.log, then pulse/steady/clock/omega diagnostics and the
# tracer budget on the aggregate (every 30 days), throughput rows for every year, into
# docs/outputs/10_production/. Log: runs/p10_analysis30.log.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"; export JAX_PLATFORMS=cpu
LOG="$REPO/runs/p10_analysis30.log"
step() { echo "[analysis30] $(date -Is) $*" | tee -a "$LOG"; }
until grep -q "chain exit=" runs/p10_run30.log; do sleep 300; done
grep -q "chain exit=0" runs/p10_run30.log || { step "chain did not exit 0; not analysing"; exit 1; }
step "chain finished; waiting for the last compaction"
while pgrep -f "compact_run.py" >/dev/null; do sleep 60; done
OUT="$REPO/docs/outputs/10_production"
step "pulse diagnostics"
python scripts/pulse_diagnostics.py runs/p10_30yr "$OUT" --label "P10 1990-2019 (strat63, tau 1 d)" --stride 120 --injection once >> "$LOG" 2>&1
step "tracer budget"
python scripts/tracer_budget.py runs/p10_30yr "$OUT" --label "P10 1990-2019" --stride 120 >> "$LOG" 2>&1
step "throughput rows"
for y in $(seq 1990 2019); do python scripts/throughput.py "runs/p10_${y}0101" --label "P10 $y" --grid T63L63 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"; done
du -sh runs/p10_30yr/ runs/p10_19900101 >> "$LOG" 2>&1; du -shc runs/p10_????0101 2>/dev/null | tail -1 >> "$LOG"
step "ANALYSIS30_DONE"
