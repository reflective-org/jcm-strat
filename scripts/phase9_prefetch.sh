#!/usr/bin/env bash
# Phase 9: prefetch the ERA5 nudging windows (per segment) and initial states for the run matrix,
# on the CPU, writing cache/era5/.p9_<prefix>.done after each configuration so phase9_queue.sh
# can start a chain as soon as its data is there.
#
#   tmux new-session -d -s p9_prefetch 'bash scripts/phase9_prefetch.sh'            # whole matrix
#   bash scripts/phase9_prefetch.sh p9_t85l95 p9_t119l95                              # some rows
#   SMOKE=1 bash scripts/phase9_prefetch.sh                                           # 5-day windows only
# Log: runs/p9_prefetch.log. Restartable: cached windows are skipped by jcm.data.era5 itself.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"; source "$REPO/scripts/phase9_lib.sh"
export JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES=""
LOG="$REPO/runs/p9_prefetch.log"; mkdir -p "$REPO/runs"
step() { echo "[prefetch] $(date -Is) $*" | tee -a "$LOG"; }
SMOKE="${SMOKE:-}"
matrix_rows "$@" | while read -r row; do
  parse_row "$row" || continue
  scheme="$SCHEME"; marker="$P9_MARKER_DIR/.p9_${PREFIX}.done"
  if [ -n "$SMOKE" ]; then scheme=smoke; marker="$P9_MARKER_DIR/.p9_${PREFIX}.smoke.done"; fi
  if [ -e "$marker" ]; then step "skip $PREFIX ($scheme, marker present)"; continue; fi
  step "start $PREFIX scheme=$scheme +experiment=$EXPERIMENT $EXTRA"
  # shellcheck disable=SC2086
  python -m jcm_strat.prefetch_era5 --scheme "$scheme" --years 2005-2009 -- "+experiment=$EXPERIMENT" $EXTRA 2>&1 \
    | grep -v -i 'warning' | tee -a "$LOG"
  rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then touch "$marker"; step "done $PREFIX"; else step "FAILED $PREFIX exit=$rc"; fi
done
step "prefetch finished"
