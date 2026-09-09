#!/usr/bin/env bash
# Phase 9: run the matrix as chained 2005-2009 segments, one configuration after another on one
# GPU. Each chain waits for its prefetch marker (cache/era5/.p9_<prefix>.done, written by
# phase9_prefetch.sh) and is skipped if its aggregate run already exists.
#
#   GPU=0 tmux new-session -d -s strat_p9_queue 'bash scripts/phase9_queue.sh'                 # all rows
#   GPU=0 tmux new-session -d -s strat_p9_queue 'bash scripts/phase9_queue.sh p9_t63l63 p9_t63l47 p9_t85l95 p9_t119l95'
# Log: runs/p9_queue.log (per-chain detail in runs/<prefix>_chain.log).
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"; source "$REPO/scripts/phase9_lib.sh"
GPU="${GPU:-0}"
LOG="$REPO/runs/p9_queue.log"; mkdir -p "$REPO/runs"
step() { echo "[queue] $(date -Is) $*" | tee -a "$LOG"; }
matrix_rows "$@" | while read -r row; do
  parse_row "$row" || continue
  if grep -q 'chain finished' "$REPO/runs/${PREFIX}_chain.log" 2>/dev/null; then step "skip $PREFIX (chain finished)"; continue; fi
  marker="$P9_MARKER_DIR/.p9_${PREFIX}.done"
  until [ -e "$marker" ]; do step "waiting for prefetch of $PREFIX"; sleep 600; done
  step "start chain $PREFIX (GPU $GPU): scheme=$SCHEME +experiment=$EXPERIMENT $EXTRA"
  PREFIX="$PREFIX" SCHEME="$SCHEME" EXPERIMENT="$EXPERIMENT" EXTRA="$EXTRA" GPU="$GPU" bash "$REPO/scripts/chain_segments.sh"
  step "chain $PREFIX exit=$?"
done
step "queue finished"
