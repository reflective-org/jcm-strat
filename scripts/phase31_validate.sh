#!/usr/bin/env bash
# Phase 31 (Susanne 2026-11-09): AL7h validation on years its T_e correction was not fitted to (fit: 2005-04..2008-01).
# Waits for scripts/phase31_extend.sh (AL7h 2011-2019) and for the CDS daily ERA5 fetch (2011-2019), then
#   1. aggregates p31_AL7h_1119 (2011-2019); diagnostics vs ERA5 / CLaMS / WACCM6 for 2011-2019 and 2006-2010
#   2. success metrics A-C on 2011-2019 with the age references of the same years (SCORE_REF_YEARS)
#   3. daily zonal means (GPU) and group D on 2011-2019 against CDS ERA5 of the same days
# Everything CPU runs under scripts/memcap.sh. The document (PDF + page) is written afterwards from these outputs.
#   tmux new-session -d -s strat_p31_validate 'bash scripts/phase31_validate.sh'     restartable; log runs/p31_run.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
OUT="$REPO/docs/outputs/31_al7h_validation"; LOG="$REPO/runs/p31_run.log"; N=AL7h
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m "${MEM:-60G}" -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p31] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
gpu_free() { ! nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
mkdir -p "$OUT"
step "validate: start, commit $(git rev-parse --short HEAD)"
until [ -e runs/p31_AL7h_extend.done ]; do
  grep -q "FAILED" "$LOG" 2>/dev/null && grep "FAILED" "$LOG" | tail -1 | grep -q "p31_AL7h_chain\|p25_AL7h_chain" && { step "extension failed - stopping"; exit 1; }
  sleep 300
done
step "extension done"

# 1. aggregates and diagnostics
A=runs/p31_AL7h_1119; A0=runs/p26_AL7h_0610
[ -e "$A/log.txt" ] || py scripts/link_segments.py "$A" $(for y in $(seq 2011 2019); do echo "$REPO/runs/p25_AL7h_${y}0101"; done) >> "$LOG" 2>&1
for w in 1119:2011-2019:$A 0610:2006-2010:$A0; do
  IFS=: read -r tag yrs agg <<< "$w"; d="$OUT/w$tag"; mkdir -p "$d"
  [ -s "$d/vortex_jets.png" ] || { py scripts/vortex_jets.py "$agg" "$d" --years "$yrs" --label "$N" > "runs/p31_vortex_$tag.log" 2>&1; step "vortex_jets $yrs exit=$?"; }
  [ -s "$d/temp_seasonal.png" ] || { py scripts/seasonal_age_winds.py "$agg" "$d" --years "$yrs" --label "$N" > "runs/p31_seasonal_$tag.log" 2>&1; step "seasonal $yrs exit=$?"; }
  [ -s "$d/tem_streamfunction.png" ] || { MEM=96G py scripts/strat_circulation.py "$agg" "$d" --years "$yrs" --label "$N" --age-var aoa_sfc > "runs/p31_circ_$tag.log" 2>&1; step "strat_circulation $yrs exit=$?"; }
done

# 2. A-C on 2011-2019, age references of the same years
S="$OUT/success_1119"; mkdir -p "$S"
SCORE_REF_YEARS=2011-2019 py scripts/success_metrics.py "$S" "$N=$A" --t0 2011-01-01 --t1 2020-01-01 --window-years 9 \
  > runs/p31_success_AC.log 2>&1; step "success A-C 2011-2019 exit=$?"

# 3. group D
Z=cache/variability; C=cache/variability_cds
if [ ! -s "$Z/${N}_1119.npz" ]; then
  G=""; until [ -n "$G" ]; do for g in 0 1 2; do gpu_free "$g" && { G=$g; break; }; done; [ -n "$G" ] || sleep 300; done
  CUDA_VISIBLE_DEVICES=$G XLA_PYTHON_CLIENT_PREALLOCATE=false JAX_PLATFORMS=cuda bash scripts/memcap.sh -m 64G -- .venv/bin/python \
    scripts/daily_zm.py "$Z/${N}_1119.npz" --run "$A" --t0 2011-01-01 --t1 2020-01-01 > runs/p31_zm.log 2>&1; step "daily_zm (GPU $G) exit=$?"
fi
until grep -q "^exit=" runs/p31_era5_fetch.log 2>/dev/null; do sleep 600; done
for y in $(seq 2011 2019); do [ -s "$C/full/era5_$y.npz" ] || { step "CDS ERA5 $y missing (runs/p31_era5_fetch.log) - group D not scored"; exit 1; }; done
step "CDS ERA5 2011-2019 on disk"
py scripts/variability_score.py "$OUT" "$N=$Z/${N}_1119.npz" --era5-dir "$C/full" --long-dir "$C/long" --long 1990-2022 \
  --t0 2011-01-01 --t1 2020-01-01 > runs/p31_variability.log 2>&1 || { step "variability_score FAILED (runs/p31_variability.log)"; exit 1; }
SCORE_REF_YEARS=2011-2019 py scripts/success_metrics.py "$S" "$N=$A" --t0 2011-01-01 --t1 2020-01-01 --window-years 9 \
  --variability "$OUT/variability.json" > runs/p31_success.log 2>&1 || { step "success_metrics FAILED (runs/p31_success.log)"; exit 1; }
step "success table: $(grep -E 'combined score|D variability' "$S/success_table.md" | tr -s ' ' | tr '\n' ' ')"
step "validate finished"
