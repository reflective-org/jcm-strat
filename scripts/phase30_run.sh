#!/usr/bin/env bash
# Phase 30 (Susanne 2026-11-08): QBO10d on the thinned strat76 grid (jcm_strat/levels.py: L95 with the mesosphere 22 -> 11
# layers and the ERA5-nudged troposphere below 402 hPa 16 -> 8; 1.08-402 hPa = L95 exactly). Same physics as QBO10d
# (p22_teq + AL7h correction + QBO tau 10 d), 2005-2010 from P20b's end-of-2004 state merged onto strat76
# (scripts/remap_checkpoint_levels.py, runs/p30_L76_20040101), scored on 2006-2010 beside the eight Phase 28 runs, A-D.
#   0. ERA5 nudging windows on strat76 for 2005-2010 (CPU, memcap)
#   1. chain 2005-2010 on the first free GPU of 0, 1, 2
#   2. 2006-2010 aggregate, diagnostics, raw success score (CPU, memcap)
#   3. daily zonal means (same GPU), group D for all nine runs against CDS ERA5, success table A-D
# Run 2 (Susanne 2026-11-09): AL7h on strat84 (mesosphere cut only, L95 below 1.08 hPa):
#   NLEV=84 N=AL7hL84 QBO_TAU= bash scripts/phase30_run.sh
# QBO30 is left out of the scoring (Susanne 2026-11-09: its QBO is unacceptable).
#   tmux new-session -d -s strat_p30_run 'bash scripts/phase30_run.sh'      restartable; log runs/p30_run.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
OUT="$REPO/docs/outputs/30_level_thinning"; P28="$REPO/docs/outputs/28_variability"; LOG="$REPO/runs/p30_run.log"; 
CORR=/data/JCM_stripped/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc
Q=physics.terms.held_suarez.qbo
NLEV="${NLEV:-76}"; N="${N:-QBO10dL76}"; QBO_TAU="${QBO_TAU-10.0}"     # QBO_TAU empty = the default 1 d (AL7h)
PRE="p30_${N}"; [ "$N" = QBO10dL76 ] && PRE=p30_L76                       # run 1 kept its original prefix
GRIDX="grid=strat_t63_l${NLEV}_hybrid level_table=strat"
EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total ${QBO_TAU:+++$Q.tau_days=$QBO_TAU} $GRIDX"
RUNS=(P20b AL7 AL7h AL7t L0 LAL7 QBO10d QBO10dL76); [ "$N" = QBO10dL76 ] || RUNS+=("$N")
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p30] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
gpu_free() { ! nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
mkdir -p "$OUT"
step "start, commit $(git rev-parse --short HEAD)"
[ -s "runs/${PRE}_20040101/checkpoint.ckpt" ] || { step "missing runs/${PRE}_20040101/checkpoint.ckpt (remap_checkpoint_levels.py)"; exit 1; }

# 0. nudging windows
# shellcheck disable=SC2086
JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash scripts/memcap.sh -m 200G -- .venv/bin/python -m jcm_strat.prefetch_era5 --scheme calendar --save-interval 0.25 --years 2005-2010 --no-init -- +experiment=p22_teq $GRIDX \
  >> "$LOG" 2>&1 || { step "prefetch FAILED"; exit 1; }
step "prefetch done"

# 1. run
GPU=""
if [ ! -e "runs/p30_$N.done" ]; then
  until [ -n "$GPU" ]; do for g in 0 1 2; do gpu_free "$g" && { GPU=$g; break; }; done; [ -n "$GPU" ] || { step "GPUs 0-2 busy"; sleep 300; }; done
  step "run $N on GPU $GPU: p22_teq $EXTRA"; t1=$(date +%s)
  EXPERIMENT=p22_teq PREFIX="$PRE" SCHEME=calendar YEARS=2004-2010 AGG="${PRE}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$EXTRA" \
    bash scripts/chain_segments.sh > "runs/${PRE}_chain_stdout.log" 2>&1; rc=$?
  bad=$(grep -l 'atmosphere unhealthy' runs/${PRE}_20[01][0-9]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "$N chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $N (runs/${PRE}_chain.log)"; exit 1; fi
  touch "runs/p30_$N.done"
fi

# 2. groups A-C
A="runs/p26_${N}_0610"; S="$OUT/success_0610"; mkdir -p "$S/raw" "$OUT/w0610/$N"
cp -rn "$P28/success_0610/raw/." "$S/raw/"
[ -e "$A/log.txt" ] || py scripts/link_segments.py "$A" $(for y in 2006 2007 2008 2009 2010; do echo "$REPO/runs/${PRE}_${y}0101"; done) >> "$LOG" 2>&1
py scripts/vortex_jets.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" > runs/p30_vortex_$N.log 2>&1; step "vortex_jets exit=$?"
py scripts/seasonal_age_winds.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" > runs/p30_seasonal_$N.log 2>&1; step "seasonal exit=$?"
py scripts/strat_circulation.py "$A" "$OUT/w0610/$N" --years 2006-2010 --label "$N" --age-var aoa_sfc > runs/p30_circ_$N.log 2>&1; step "strat_circulation exit=$?"
py scripts/success_metrics.py "$S" "$N=$A" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > runs/p30_success_$N.log 2>&1; step "success $N exit=$?"

# 3. group D
Z=cache/variability; C=cache/variability_cds
if [ ! -s "$Z/${N}_0610.npz" ]; then
  if [ -z "$GPU" ]; then until [ -n "$GPU" ]; do for g in 0 1 2; do gpu_free "$g" && { GPU=$g; break; }; done; [ -n "$GPU" ] || sleep 300; done; fi
  CUDA_VISIBLE_DEVICES=$GPU XLA_PYTHON_CLIENT_PREALLOCATE=false JAX_PLATFORMS=cuda bash scripts/memcap.sh -m 64G -- .venv/bin/python \
    scripts/daily_zm.py "$Z/${N}_0610.npz" --run "$A" --t0 2006-01-01 --t1 2011-01-01 > runs/p30_zm_$N.log 2>&1; step "daily_zm exit=$?"
fi
V=(); for n in "${RUNS[@]}"; do V+=("$n=$Z/${n}_0610.npz"); done
py scripts/variability_score.py "$OUT" "${V[@]}" --era5-dir "$C/full" --long-dir "$C/long" --long 1990-2022 \
  --t0 2006-01-01 --t1 2011-01-01 > runs/p30_variability.log 2>&1 || { step "variability_score FAILED (runs/p30_variability.log)"; exit 1; }
ALL=(); for n in "${RUNS[@]}"; do ALL+=("$n=runs/p26_${n}_0610"); done
py scripts/success_metrics.py "$S" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 --variability "$OUT/variability.json" \
  > runs/p30_success.log 2>&1 || { step "success_metrics FAILED (runs/p30_success.log)"; exit 1; }
step "success table: $(grep -E 'combined score|D variability' "$S/success_table.md" | tr -s ' ' | cut -c1-300 | tr '\n' ' ')"
grep -h "Run completed\|Model starting" runs/${PRE}_2007*/main.log > runs/p30_timing_$N.txt 2>/dev/null
step "finished"
