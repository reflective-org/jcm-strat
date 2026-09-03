#!/usr/bin/env bash
# Phase 4: run 2005-2009 as five chained one-year segments on GPU 0, then link the segment
# outputs into runs/p4_5yr/ with cumulative day numbers so every analysis script sees one run.
#
#   tmux new-session -d -s strat_p4_chain 'bash scripts/chain_years.sh'
#   EXPERIMENT=p6_pk PREFIX=p6 tmux new-session -d -s strat_p6_chain 'bash scripts/chain_years.sh'
#
# EXPERIMENT (default p4_5yr) is the hydra experiment; PREFIX (default p4) names the runs
# runs/<PREFIX>_<year> and the aggregate runs/<PREFIX>_5yr.
# Restartable: a finished segment (exit=0 in its log) is skipped. Progress: runs/<PREFIX>_chain.log
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
EXPERIMENT="${EXPERIMENT:-p4_5yr}"; PREFIX="${PREFIX:-p4}"
LOG="$REPO/runs/${PREFIX}_chain.log"; mkdir -p "$REPO/runs"
step() { echo "[chain] $(date -Is) $*" | tee -a "$LOG"; }
if nvidia-smi -i 0 --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then
  step "refusing: GPU 0 is busy"; exit 1
fi

YEARS=(2005 2006 2007 2008 2009)
prev=""
for y in "${YEARS[@]}"; do
  name="${PREFIX}_$y"; rundir="$REPO/runs/$name"
  days=$(python3 -c "import datetime as d; print((d.date($y+1,1,1)-d.date($y,1,1)).days)")
  if grep -q '\[launch\].*exit=0' "$rundir/log.txt" 2>/dev/null; then step "skip $name (done)"; prev="$rundir"; continue; fi
  mkdir -p "$rundir"
  init=()
  if [ -n "$prev" ]; then init=(init=from_state "init.file=$prev/checkpoint.ckpt"); fi
  step "run $name: $days days ${init[*]:-init=era5}"
  ( cd "$rundir" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$EXPERIMENT" ++run.checkpoint_path=checkpoint.ckpt \
      "run.start_date=$y-01-01" "run.total_time=$days" "${init[@]}" hydra.run.dir="$rundir" ) >> "$rundir/log.txt" 2>&1
  rc=$?; echo "[launch] $(date -Is) exit=$rc" >> "$rundir/log.txt"
  step "done $name exit=$rc"
  [ $rc -eq 0 ] || { step "segment $name FAILED - stopping"; exit 1; }
  prev="$rundir"
done

# one virtual run with cumulative day numbers
agg="$REPO/runs/${PREFIX}_5yr"; mkdir -p "$agg"; rm -f "$agg"/longrun_day*.nc
offset=0
for y in "${YEARS[@]}"; do
  for f in "$REPO/runs/${PREFIX}_$y"/longrun_day*.nc; do
    d=$(basename "$f" | sed -E 's/longrun_day([0-9]+)\.nc/\1/')
    ln -s "$f" "$agg/longrun_day$((offset + d)).nc"
  done
  offset=$((offset + $(python3 -c "import datetime as d; print((d.date($y+1,1,1)-d.date($y,1,1)).days)")))
done
cp "$REPO/runs/${PREFIX}_2005/.hydra" -r "$agg/" 2>/dev/null
cat "$REPO"/runs/${PREFIX}_20??/log.txt > "$agg/log.txt"
step "linked $(ls "$agg"/longrun_day*.nc | wc -l) chunk files into runs/p4_5yr ($offset days)"
step "chain finished"
