#!/usr/bin/env bash
# Phase 9: the standard diagnostics for every finished run of the resolution sweep, then the
# cross-run comparison and the summary table/figure. CPU only (JAX_PLATFORMS=cpu).
#
#   tmux new-session -d -s p9_analysis 'bash scripts/phase9_analysis.sh 2>&1 | tee runs/p9_analysis.log'
#   bash scripts/phase9_analysis.sh T85L95            # one label only (per-run part), then the summary
#
# Runs: docs/outputs/09_resolution/runs.txt, one "LABEL rundir" per line (the T63L95 baseline is the
# Phase 8b chain). Per run -> docs/outputs/09_resolution/<LABEL>/: run_summary, tracer_budget,
# aoa_vs_clams (last 73 saves = final year), strat_circulation (-> circulation/), qbo_compare against
# the baseline, throughput row (grid label = LABEL). Then strat_compare over all runs (-> strat/) and
# resolution_metrics.py (-> resolution_metrics.md, resolution_sweep.png).
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
OUT="$REPO/docs/outputs/09_resolution"; RUNS="$OUT/runs.txt"; YEARS=2005-2009
BASE=$(awk '$1=="T63L95"{print $2}' "$RUNS")
step() { echo "[analysis] $(date -Is) $*"; }

grep -v '^\s*#' "$RUNS" | grep -v '^\s*$' | while read -r label rundir; do
  if [ $# -gt 0 ]; then keep=0; for w in "$@"; do [ "$w" = "$label" ] && keep=1; done; [ $keep = 1 ] || continue; fi
  [ -d "$REPO/$rundir" ] || { step "skip $label: $rundir missing"; continue; }
  grep -q 'chain finished' "$REPO/runs/$(basename "$rundir" | sed 's/_5yr$//')_chain.log" 2>/dev/null || { step "skip $label: chain not finished"; continue; }
  d="$OUT/$label"; mkdir -p "$d/circulation"
  step "$label <- $rundir"
  python scripts/run_summary.py "$REPO/$rundir" "$d/${label}_summary.png" > "$d/run_summary.txt" 2>&1
  python scripts/tracer_budget.py "$REPO/$rundir" "$d" --label "$label" > "$d/tracer_budget.txt" 2>&1
  python scripts/aoa_vs_clams.py "$REPO/$rundir" "$d" --years $YEARS --label "Phase 9 $label" --last-saves 73 > "$d/aoa.txt" 2>&1
  python scripts/strat_circulation.py "$REPO/$rundir" "$d/circulation" --years $YEARS --label "$label" > "$d/circulation/log.txt" 2>&1
  if [ "$label" != "T63L95" ] && [ -n "$BASE" ]; then
    python scripts/qbo_compare.py "$d" --before "$REPO/$BASE" --after "$REPO/$rundir" --years $YEARS \
      --label-before "before: T63L95 (Phase 8b)" --label-after "after: $label" > "$d/qbo.txt" 2>&1
  elif [ -d "$REPO/runs/p8_5yr" ]; then   # the baseline itself: its own before-state is the 4 hPa Phase 8 chain
    python scripts/qbo_compare.py "$d" --before "$REPO/runs/p8_5yr" --after "$REPO/$rundir" --years $YEARS \
      --label-before "before: QBO window top 4 hPa (Phase 8)" --label-after "after: $label (Phase 8b)" > "$d/qbo.txt" 2>&1
  fi
  python scripts/throughput.py "$REPO/$rundir" --label "P9 $label" --grid "$label" --csv "$REPO/docs/outputs/throughput.csv" > "$d/throughput.txt" 2>&1
  step "$label done"
done

runs_args=(); while read -r label rundir; do
  case "$label" in \#*|"") continue;; esac
  grep -q 'chain finished' "$REPO/runs/$(basename "$rundir" | sed 's/_5yr$//')_chain.log" 2>/dev/null && runs_args+=(--run "$label=$REPO/$rundir")
done < "$RUNS"
nruns=$(( ${#runs_args[@]} / 2 ))
if [ "$nruns" -ge 2 ]; then
  step "strat_compare over $nruns runs"; mkdir -p "$OUT/strat"
  python scripts/strat_compare.py "$OUT/strat" "${runs_args[@]}" --years $YEARS --panel > "$OUT/strat/log.txt" 2>&1 || step "strat_compare failed"
  step "resolution_metrics"
  python scripts/resolution_metrics.py "$OUT" "${runs_args[@]}" --years $YEARS --last-saves 73 --throughput "$REPO/docs/outputs/throughput.csv" 2>&1 | tail -20
fi
step "analysis finished"
