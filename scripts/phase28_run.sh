#!/usr/bin/env bash
# Phase 28: group D of the success metrics (variability, SSWs, seasonal cycle, heat-flux and age-w* relations).
# Unattended, GPU 0 (Susanne 2026-11-05). tmux strat_p28_run, log runs/p28_run.log.
#   1. daily zonal means (scripts/daily_zm.py, jax on GPU 0): ERA5 1990-2022 and the eight scorecard runs, 2006-2010
#   2. scripts/variability_score.py -> docs/outputs/28_variability/  (group D table, json, figures)
#   3. scripts/success_metrics.py with --variability on the Phase 27 raw scores -> docs/outputs/28_variability/success_0610
#   4. commit (not pushed)
set -uo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh >/dev/null 2>&1
export CUDA_VISIBLE_DEVICES=0 XLA_PYTHON_CLIENT_PREALLOCATE=false JAX_PLATFORMS=cuda
py() { bash scripts/memcap.sh -m 64G -- .venv/bin/python "$@"; }
log() { echo "[p28] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*"; }
Z=cache/variability; OUT=docs/outputs/28_variability; mkdir -p "$Z" "$OUT"
RUNS=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d)

log "start, commit $(git rev-parse --short HEAD)"
for y in $(seq 1990 2022); do
  [ -s "$Z/era5_$y.npz" ] && continue
  py scripts/daily_zm.py "$Z/era5_$y.npz" --era5 "$y" 2>&1 | grep '^\[daily_zm\] .*npz' || log "ERA5 $y FAILED"
done
log "ERA5 done ($(ls $Z/era5_*.npz | wc -l) years)"
for n in "${RUNS[@]}"; do
  [ -s "$Z/${n}_0610.npz" ] && continue
  log "run $n"
  py scripts/daily_zm.py "$Z/${n}_0610.npz" --run "runs/p26_${n}_0610" --t0 2006-01-01 --t1 2011-01-01 > "runs/p28_zm_$n.log" 2>&1 \
    || log "run $n FAILED (runs/p28_zm_$n.log)"
done
ARGS=(); for n in "${RUNS[@]}"; do [ -s "$Z/${n}_0610.npz" ] && ARGS+=("$n=$Z/${n}_0610.npz"); done
log "scoring ${#ARGS[@]} runs"
JAX_PLATFORMS=cpu py scripts/variability_score.py "$OUT" "${ARGS[@]}" --era5-dir "$Z" --t0 2006-01-01 --t1 2011-01-01 --long 1990-2022 \
  > runs/p28_variability.log 2>&1 || { log "variability_score FAILED (runs/p28_variability.log)"; exit 1; }
S="$OUT/success_0610"; mkdir -p "$S/raw"; cp -rn docs/outputs/27_qbo_nudging/success_0610/raw/. "$S/raw/"
ALL=(); for n in "${RUNS[@]}"; do ALL+=("$n=runs/p26_${n}_0610"); done
JAX_PLATFORMS=cpu py scripts/success_metrics.py "$S" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 \
  --variability "$OUT/variability.json" > runs/p28_success.log 2>&1 || { log "success_metrics FAILED (runs/p28_success.log)"; exit 1; }
git add scripts/daily_zm.py scripts/variability_score.py scripts/success_metrics.py scripts/phase28_run.sh "$OUT"
git commit -q -m "Phase 28: success-metrics group D (variability, SSWs, seasonal cycle, heat-flux and age-w* relations), 2006-2010

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && log "committed $(git rev-parse --short HEAD)"
log "finished"
