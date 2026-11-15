#!/usr/bin/env bash
# Phase 31 (Susanne 2026-11-09): AL7h validation. Step 1: extend the AL7h chain (p22_teq + AL7h correction, QBO tau 1 d)
# from its end-of-2010 state through 2019, so it can be judged on years the T_e correction was not fitted to
# (the correction was fitted on 2005-04..2008-01). Same prefix as Phase 25, so 2011+ continue the existing chain.
#   tmux new-session -d -s strat_p31_extend 'GPU=2 bash scripts/phase31_extend.sh'     restartable; log runs/p31_run.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
LOG="$REPO/runs/p31_run.log"; GPU="${GPU:-2}"
CORR="$REPO/docs/outputs/25_al7_half/corrections/AL7h.nc"
EXTRA="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total"
step() { echo "[p31] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
step "start, commit $(git rev-parse --short HEAD)"
while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
step "extend AL7h 2011-2019 on GPU $GPU"; t1=$(date +%s)
EXPERIMENT=p22_teq PREFIX=p25_AL7h SCHEME=calendar YEARS=1990-2019 AGG=p31_AL7h_1990_2019 SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$EXTRA" \
  bash scripts/chain_segments.sh > runs/p31_AL7h_chain_stdout.log 2>&1; rc=$?
bad=$(grep -l 'atmosphere unhealthy' runs/p25_AL7h_20[01][0-9]0101/log.txt 2>/dev/null | tr '\n' ' ')
step "AL7h extension exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED (runs/p25_AL7h_chain.log)"; exit 1; fi
touch runs/p31_AL7h_extend.done
step "finished"
