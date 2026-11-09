#!/usr/bin/env bash
# Phase 29 (Susanne 2026-11-09): LQBO10d = QBO10d (AL7h correction, 10-day QBO nudging) with L0's latitude-dependent
# ERA5 nudging top (150 hPa tropics -> 400 hPa extratropics, experiment p23_lattop). 2005-2010 from P20b's end-of-2004
# state on GPU 0, scored on 2006-2010 beside the eight Phase 28 runs, groups A-C and D.
#   1. chain 2005-2010 (GPU 0)
#   2. 2006-2010 aggregate, diagnostics, raw success score (CPU, memcap)
#   3. daily zonal means (GPU 0), group D for all nine runs against CDS ERA5, success table A-D
#   4. scorecard figures and page (findings.html written by hand afterwards), commit (not pushed)
#
#   tmux new-session -d -s strat_p29_run 'bash scripts/phase29_run.sh'      restartable; log runs/p29_run.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
OUT="$REPO/docs/outputs/29_lqbo10d"; P28="$REPO/docs/outputs/28_variability"; LOG="$REPO/runs/p29_run.log"
CORR=/data/JCM_stripped/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc
Q=physics.terms.held_suarez.qbo
N=LQBO10d; PRE=p29_LQBO10d; GPU=0
EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total ++$Q.tau_days=10.0"
RUNS=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d LQBO10d)
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p29] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
mkdir -p "$OUT"
step "start, commit $(git rev-parse --short HEAD)"

# 1. run
if [ ! -e "runs/p29_$N.done" ]; then
  for y in $(seq 1990 2004); do [ -e "runs/${PRE}_${y}0101" ] || ln -s "$REPO/runs/p20bt_${y}0101" "runs/${PRE}_${y}0101"; done
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
  step "run $N on GPU $GPU: p23_lattop $EXTRA"; t1=$(date +%s)
  EXPERIMENT=p23_lattop PREFIX="$PRE" SCHEME=calendar YEARS=1990-2010 AGG="${PRE}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$EXTRA" \
    bash scripts/chain_segments.sh > "runs/${PRE}_chain_stdout.log" 2>&1; rc=$?
  bad=$(grep -l 'atmosphere unhealthy' runs/${PRE}_20[01][0-9]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "$N chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $N (runs/${PRE}_chain.log)"; exit 1; fi
  touch "runs/p29_$N.done"
fi

# 2. groups A-C
A="runs/p26_${N}_0610"; S="$OUT/success_0610"; mkdir -p "$S/raw" "$OUT/w0610/$N"
cp -rn "$P28/success_0610/raw/." "$S/raw/"
[ -e "$A/log.txt" ] || py scripts/link_segments.py "$A" $(for y in 2006 2007 2008 2009 2010; do echo "$REPO/runs/${PRE}_${y}0101"; done) >> "$LOG" 2>&1
py scripts/vortex_jets.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" > runs/p29_vortex.log 2>&1; step "vortex_jets exit=$?"
py scripts/seasonal_age_winds.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" > runs/p29_seasonal.log 2>&1; step "seasonal exit=$?"
py scripts/strat_circulation.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" --age-var aoa_sfc > runs/p29_circ.log 2>&1; step "strat_circulation exit=$?"
py scripts/success_metrics.py "$S" "$N=$A" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > runs/p29_success_$N.log 2>&1; step "success $N exit=$?"

# 3. group D
Z=cache/variability; C=cache/variability_cds
if [ ! -s "$Z/${N}_0610.npz" ]; then
  CUDA_VISIBLE_DEVICES=$GPU XLA_PYTHON_CLIENT_PREALLOCATE=false JAX_PLATFORMS=cuda bash scripts/memcap.sh -m 64G -- .venv/bin/python \
    scripts/daily_zm.py "$Z/${N}_0610.npz" --run "$A" --t0 2006-01-01 --t1 2011-01-01 > runs/p29_zm.log 2>&1; step "daily_zm exit=$?"
fi
V=(); for n in "${RUNS[@]}"; do V+=("$n=$Z/${n}_0610.npz"); done
py scripts/variability_score.py "$OUT" "${V[@]}" --era5-dir "$C/full" --long-dir "$C/long" --long 1990-2022 \
  --t0 2006-01-01 --t1 2011-01-01 > runs/p29_variability.log 2>&1 || { step "variability_score FAILED (runs/p29_variability.log)"; exit 1; }
ALL=(); for n in "${RUNS[@]}"; do ALL+=("$n=runs/p26_${n}_0610"); done
py scripts/success_metrics.py "$S" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 --variability "$OUT/variability.json" \
  > runs/p29_success.log 2>&1 || { step "success_metrics FAILED (runs/p29_success.log)"; exit 1; }
step "success table: $(grep -E 'combined score|D variability' "$S/success_table.md" | tr -s ' ' | cut -c1-300 | tr '\n' ' ')"

# 4. scorecard (A-C figures redrawn with nine runs; Phase 27's QBO comparison figures reused)
bash scripts/phase29_report.sh >> "$LOG" 2>&1; step "report exit=$?"
git add scripts/phase29_run.sh scripts/phase29_report.sh scripts/build_scorecard.py scripts/report_figures.py "$OUT"
git commit -q -m "Phase 29: LQBO10d (QBO10d + 150 hPa tropical nudging) scored on 2006-2010, groups A-D

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019WwiRRbaS2W66QyD9NYJXd" && step "committed $(git rev-parse --short HEAD)"
step "finished"
