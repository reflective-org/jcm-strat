#!/usr/bin/env bash
# Phase 9: run 2005-2009 as chained segments whose length fits the GPU-resident ERA5 nudging
# target at the run's resolution (jcm_strat/segments.py: year | half | quarter | bimonth), then
# link the segment outputs into runs/<PREFIX>_5yr with cumulative day numbers so every analysis
# script sees one run. Generalises chain_years.sh (which stays as it is).
#
#   PREFIX=p9_t85l95 SCHEME=half EXTRA="grid=echam_t85_l95_hybrid run.time_step=9" \
#     tmux new-session -d -s strat_p9_t85l95 'bash scripts/chain_segments.sh'
#
# Environment:
#   EXPERIMENT     hydra experiment (default p9_res; p9_l63 / p9_l47 for the vertical axis)
#   PREFIX         run names: runs/<PREFIX>_<YYYYMMDD> per segment, runs/<PREFIX>_5yr aggregate
#   SCHEME         year | half | quarter | bimonth (default year)
#   YEARS          default 2005-2009
#   GPU            default 0 (project rule: 0, then 1, then 2)
#   EXTRA          constant hydra overrides for every segment (grid=..., run.time_step=...)
#   EXTRA_PER_SEG  per-segment overrides, {year} replaced by the segment's calendar year
#                  (default: the QBO target year, as chain_years.sh passes it)
# Restartable: a finished segment (exit=0 in its log) is skipped; a crashed one resumes from its
# checkpoint.ckpt. Progress: runs/<PREFIX>_chain.log.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
EXPERIMENT="${EXPERIMENT:-p9_res}"; PREFIX="${PREFIX:?PREFIX is required}"
SCHEME="${SCHEME:-year}"; YEARS="${YEARS:-2005-2009}"; GPU="${GPU:-0}"
EXTRA="${EXTRA:-}"; EXTRA_PER_SEG="${EXTRA_PER_SEG:-physics.terms.held_suarez.qbo.year={year}}"
export CUDA_VISIBLE_DEVICES="$GPU"
LOG="$REPO/runs/${PREFIX}_chain.log"; mkdir -p "$REPO/runs"
step() { echo "[chain] $(date -Is) $*" | tee -a "$LOG"; }

if nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then
  step "refusing: GPU $GPU is busy"; exit 1
fi
# the time step must divide the 5-day save interval (JCM truncates silently); default 12 min
dt_min=$(printf '%s\n' $EXTRA | sed -n 's/^run\.time_step=//p' | tail -1); dt_min="${dt_min:-12}"
if [ $(( 7200 % dt_min )) -ne 0 ]; then step "refusing: run.time_step=$dt_min does not divide 7200 min"; exit 1; fi

read -r -a extra <<< "$EXTRA"
mapfile -t SEGS < <(JAX_PLATFORMS=cpu python -m jcm_strat.segments "$SCHEME" "$YEARS") || { step "segments failed"; exit 1; }
step "chain $PREFIX: experiment=$EXPERIMENT scheme=$SCHEME (${#SEGS[@]} segments) GPU=$GPU extra: ${extra[*]:-none} per-seg: $EXTRA_PER_SEG"

prev=""
for seg in "${SEGS[@]}"; do
  read -r d days y <<< "$seg"
  name="${PREFIX}_${d//-/}"; rundir="$REPO/runs/$name"
  if grep -q '\[launch\].*exit=0' "$rundir/log.txt" 2>/dev/null; then step "skip $name (done)"; prev="$rundir"; continue; fi
  mkdir -p "$rundir"
  init=(); if [ -n "$prev" ]; then init=(init=from_state "init.file=$prev/checkpoint.ckpt"); fi
  per=(); if [ -n "$EXTRA_PER_SEG" ]; then read -r -a per <<< "${EXTRA_PER_SEG//\{year\}/$y}"; fi
  step "run $name: $d +$days d ${init[*]:-init=era5} ${per[*]}"
  echo "[launch] $(date -Is) jcm-strat $(git -C "$REPO" rev-parse --short HEAD) chain=$PREFIX GPU=$GPU" >> "$rundir/log.txt"
  ( cd "$rundir" && python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$EXPERIMENT" ++run.checkpoint_path=checkpoint.ckpt \
      "run.start_date=$d" "run.total_time=$days" "${extra[@]}" "${per[@]}" "${init[@]}" hydra.run.dir="$rundir" ) >> "$rundir/log.txt" 2>&1
  rc=$?; echo "[launch] $(date -Is) exit=$rc" >> "$rundir/log.txt"
  step "done $name exit=$rc"
  [ $rc -eq 0 ] || { step "segment $name FAILED - stopping"; exit 1; }
  prev="$rundir"
done

# one virtual run with cumulative day numbers (calendar offsets, so dates match chain_years.sh)
agg="$REPO/runs/${PREFIX}_5yr"; mkdir -p "$agg"; rm -f "$agg"/longrun_day*.nc "$agg/segments.txt"
year_offset=0; cur_year=""; seg_offset=0; first=""
for seg in "${SEGS[@]}"; do
  read -r d days y <<< "$seg"
  if [ "$y" != "$cur_year" ]; then
    if [ -n "$cur_year" ]; then year_offset=$(( year_offset + $(python3 -c "import datetime as d; print((d.date($cur_year+1,1,1)-d.date($cur_year,1,1)).days)") )); fi
    cur_year="$y"; seg_offset=0
  fi
  rundir="$REPO/runs/${PREFIX}_${d//-/}"; [ -n "$first" ] || first="$rundir"
  for f in "$rundir"/longrun_day*.nc; do
    n=$(basename "$f" | sed -E 's/longrun_day([0-9]+)\.nc/\1/')
    ln -s "$f" "$agg/longrun_day$((year_offset + seg_offset + n)).nc"
  done
  echo "$d $days $rundir" >> "$agg/segments.txt"
  seg_offset=$(( seg_offset + days ))
done
cp -r "$first/.hydra" "$agg/" 2>/dev/null
cat "$REPO"/runs/${PREFIX}_20??????/log.txt > "$agg/log.txt"
step "linked $(ls "$agg"/longrun_day*.nc | wc -l) chunk files into runs/${PREFIX}_5yr"
step "chain finished"
