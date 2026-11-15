#!/usr/bin/env bash
# Phase 30 runtime benchmark: the QBO10d configuration (p22_teq + AL7h correction + QBO tau 10 d) for 30 days from
# 2007-01-01 (ERA5 initial state) on L95 and the thinned L95 subsets strat84 / strat87 / strat76 (jcm_strat/levels.py).
# Timing only: 30 days do not test stability or the circulation. One GPU, sequential.
#   GPU=0 bash scripts/phase30_bench.sh        (in tmux strat_p30_bench; log runs/p30_bench.log)
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
source scripts/env.sh
export CUDA_VISIBLE_DEVICES="${GPU:-0}"
LOG="$REPO/runs/p30_bench.log"
DAYS=30; START=2007-01-01
CORR=/data/JCM_stripped/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc
step() { echo "[p30] $(TZ=America/Los_Angeles date '+%F %H:%M %Z') $*" | tee -a "$LOG"; }
py_cpu() { bash scripts/memcap.sh -m 96G -- env JAX_PLATFORMS=cpu python "$@"; }

COMMON=(+experiment=p22_teq
  ++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total
  ++physics.terms.held_suarez.qbo.tau_days=10.0 physics.terms.held_suarez.qbo.year=2007
  physics.terms.production_tracers.first_segment=true)

for n in ${TABLES:-95 84 87 76}; do
  if [ "$n" = 95 ]; then GRIDO=(); else GRIDO=(grid=strat_t63_l${n}_hybrid level_table=strat); fi
  step "prefetch L$n"
  py_cpu -m jcm_strat.prefetch_era5 --days $DAYS --start $START --years 2007 -- "${COMMON[@]}" "${GRIDO[@]}" >> "$LOG" 2>&1 \
    || { step "prefetch L$n FAILED"; continue; }
  rd="$REPO/runs/p30_bench_l$n"; mkdir -p "$rd"
  step "run L$n -> $rd"
  t0=$(date +%s)
  ( cd "$rd" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "${COMMON[@]}" "${GRIDO[@]}" \
      run.start_time=$START run.total_time=$DAYS ++run.checkpoint_path=checkpoint.ckpt > stdout.log 2>&1 )
  rc=$?
  step "L$n exit=$rc wall=$(( $(date +%s) - t0 )) s"
done
step "bench finished"
