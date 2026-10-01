#!/usr/bin/env bash
# Phase 11 diagnostics of the two 5-year review runs, A and B in parallel (CPU only; tmux eval_p11_diag,
# log runs/p11_diag.log). Time series every 20th frame (= every 5 days): the 6-hourly stride-4 default of
# pulse_diagnostics walked 654 GB for 4 h without finishing on 2026-09-15.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
export JAX_PLATFORMS=cpu
OUT="$REPO/docs/outputs/11_lid_tracers"; mkdir -p "$OUT"; LOG="$REPO/runs/p11_diag.log"
step() { echo "[p11-diag] $(date -Is) $*" | tee -a "$LOG"; }
one() {
  e=$1; run="$REPO/runs/p11${e}_5yr"; lab="P11$e 1990-1994 (strat63, lid 1 hPa, $([ "$e" = a ] && echo 'no sink' || echo 'lid sink'))"
  python scripts/aoa_vs_clams.py "$run" "$OUT" --years 2005-2009 --last-saves 240 \
      --label "$lab: age after 5 yr (last 60 d of 1994) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p11${e}_aoa.log" 2>&1; step "aoa_vs_clams $e exit=$?"
  python scripts/pulse_diagnostics.py "$run" "$OUT" --label "$lab" --stride 20 > "$REPO/runs/p11${e}_pulse_diag.log" 2>&1; step "pulse_diagnostics $e exit=$?"
  python scripts/tracer_budget.py "$run" "$OUT" --label "$lab" --stride 20 > "$REPO/runs/p11${e}_budget.log" 2>&1; step "tracer_budget $e exit=$?"
  python scripts/pulse_evolution.py "$run" "$OUT" --label "$lab" --stages panels vertical mass --nproc 12 > "$REPO/runs/p11${e}_evolution.log" 2>&1; step "pulse_evolution $e exit=$?"
}
step "start"
one a & pa=$!; one b & pb=$!
wait $pa; wait $pb
step "finished"
