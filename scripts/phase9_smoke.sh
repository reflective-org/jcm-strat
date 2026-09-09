#!/usr/bin/env bash
# Phase 9: 5-day smoke test of every matrix row on one GPU, sequentially (3-8 min each). Checks
# memory (no RESOURCE_EXHAUSTED), that the ERA5 window is a cache hit, that the ECHAM lmidatm
# diffusion profile is used (no "uniform SPEEDY" warning), no NaN, and records the chunk wall time.
#
#   GPU=0 tmux new-session -d -s strat_p9_smoke 'bash scripts/phase9_smoke.sh'
#   bash scripts/phase9_smoke.sh p9_t119l95            # one row
# Needs the smoke windows: SMOKE=1 bash scripts/phase9_prefetch.sh. Runs land in runs/p9smoke_<prefix>.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"; source "$REPO/scripts/phase9_lib.sh"
GPU="${GPU:-0}"; export CUDA_VISIBLE_DEVICES="$GPU"
LOG="$REPO/runs/p9_smoke.log"; mkdir -p "$REPO/runs"
step() { echo "[smoke] $(date -Is) $*" | tee -a "$LOG"; }
if nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then step "refusing: GPU $GPU busy"; exit 1; fi
matrix_rows "$@" | while read -r row; do
  parse_row "$row" || continue
  name="p9smoke_${PREFIX}"; rundir="$REPO/runs/$name"; mkdir -p "$rundir"
  step "run $name: +experiment=$EXPERIMENT $EXTRA (5 days, GPU $GPU)"
  t0=$(date +%s)
  # shellcheck disable=SC2086
  ( cd "$rundir" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$EXPERIMENT" $EXTRA \
      run.start_date=2005-01-01 run.total_time=5 run.chunk_days=5 physics.terms.held_suarez.qbo.year=2005 hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  rc=$?; echo "[launch] $(date -Is) exit=$rc" >> "$rundir/log.txt"
  oom=$(grep -c 'RESOURCE_EXHAUSTED' "$rundir/log.txt"); hit=$(grep -c 'era5: cache hit' "$rundir/log.txt")
  uni=$(grep -c 'uniform' "$rundir/log.txt"); nan=$(grep -c -i 'nan' "$rundir/log.txt")
  wall=$(grep -o 'chunk.*wall[^,]*' "$rundir/log.txt" | tail -1)
  step "done $name exit=$rc in $(( $(date +%s) - t0 )) s: oom=$oom cache_hits=$hit uniform_diffusion_warnings=$uni nan_lines=$nan ${wall:-}"
  nvidia-smi -i "$GPU" --query-gpu=memory.used --format=csv,noheader | sed 's/^/[smoke]   gpu memory after: /' | tee -a "$LOG"
done
step "smoke finished"
