#!/usr/bin/env bash
# Phase 26b (Susanne 2026-10-28): score on 2006-2010 instead of 2005-2009, so the first year after the restart from
# P20b is left out. Every run needs 2010: the five restart runs are extended by one year from their 2009 checkpoints,
# and P20b gets its own 2010 as runs/p26_P20b_* (1990-2009 linked to p20bt; the 50-year p20bt chain on GPU 0 will
# reach 2010 only after its ERA5 prefetch). Two queues on GPUs 1 and 2 (GPU 0 is the p20bt chain's). Scoring runs one
# job at a time at a 60G cap, so it fits beside that prefetch (192G) in the shared 256G slice.
#
#   bash scripts/phase26_2010.sh      restartable
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
OUT="$REPO/docs/outputs/26_5yr_scoring"; LOG="$REPO/runs/p26b_run.log"
W=/data/JCM_stripped
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p26b] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
corr() { echo "++physics.terms.held_suarez.te_correction_file=$1 ++physics.terms.held_suarez.te_correction_mode=total"; }

# name prefix experiment extra (as in each run's runs/<prefix>_chain.log)
declare -A RUN=(
  [AL7]="p22_AL7|p22_teq|$(corr $W/jcm-strat-phase19/docs/outputs/22_teq_vortex/corrections/AL7.nc)"
  [AL7h]="p25_AL7h|p22_teq|$(corr $W/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc)"
  [AL7t]="p24_AL7t|p22_teq|$(corr $W/jcm-strat-phase24/docs/outputs/24_al7_taper/corrections/AL7t35_50.nc)"
  [LAL7]="p23_LAL7|p23_lattop|$(corr $W/jcm-strat-phase23/docs/outputs/22_teq_vortex/corrections/AL7.nc)"
  [L0]="p23_L0|p23_lattop|"
  [P20b]="p26_P20b|p20b_ext|"
)
for y in $(seq 1990 2009); do [ -e "runs/p26_P20b_${y}0101" ] || ln -s "$REPO/runs/p20bt_${y}0101" "runs/p26_P20b_${y}0101"; done

extend() {  # <gpu> <name>...: extend each run to 2010 on one GPU; marker runs/p26b_<name>.done / .failed
  local gpu="$1"; shift
  for name in "$@"; do
    IFS='|' read -r pre exp extra <<< "${RUN[$name]}"
    if [ ! -s "runs/${pre}_20100101/checkpoint.ckpt" ]; then
      while nvidia-smi -i "$gpu" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $gpu busy"; sleep 300; done
      step "extend $name to 2010 on GPU $gpu ($exp)"; local t1; t1=$(date +%s)
      EXPERIMENT="$exp" PREFIX="$pre" SCHEME=calendar YEARS=1990-2010 AGG="${pre}_agg" SAVE_INTERVAL=0.25 GPU="$gpu" EXTRA="$extra" \
        bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout_p26b.log" 2>&1; local rc=$?
      local bad; bad=$(grep -l 'atmosphere unhealthy' "runs/${pre}_20100101/log.txt" 2>/dev/null)
      step "$name chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP}"
      if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $name (runs/${pre}_chain.log), not scored"; touch "runs/p26b_$name.failed"; continue; fi
    fi
    touch "runs/p26b_$name.done"
  done
}

score() {  # <name> <prefix>: 2006-2010 aggregate, diagnostics, raw success scores
  local n="$1" pre="$2" a="runs/p26_$1_0610"
  [ -e "$a/log.txt" ] || py scripts/link_segments.py "$a" $(for y in 2006 2007 2008 2009 2010; do echo "$REPO/runs/${pre}_${y}0101"; done) >> "$LOG" 2>&1
  mkdir -p "$OUT/w0610/$n"
  py scripts/vortex_jets.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" > "runs/p26b_vortex_$n.log" 2>&1; step "$n vortex_jets exit=$?"
  py scripts/seasonal_age_winds.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" > "runs/p26b_seasonal_$n.log" 2>&1; step "$n seasonal exit=$?"
  py scripts/strat_circulation.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" --age-var aoa_sfc > "runs/p26b_circ_$n.log" 2>&1; step "$n strat_circulation exit=$?"
  py scripts/success_metrics.py "$OUT/success_0610" "$n=$a" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > "runs/p26b_success_$n.log" 2>&1
  step "$n success 2006-2010 exit=$?"
}

ORDER=(P20b AL7 AL7h AL7t L0 LAL7)
step "start, commit $(git rev-parse --short HEAD)"
rm -f runs/p26b_*.done runs/p26b_*.failed
extend 1 AL7 AL7t L0 &
extend 2 AL7h LAL7 P20b &
for n in "${ORDER[@]}"; do
  until [ -e "runs/p26b_$n.done" ] || [ -e "runs/p26b_$n.failed" ]; do sleep 60; done
  [ -e "runs/p26b_$n.done" ] && score "$n" "${RUN[$n]%%|*}"
done
wait
ALL=()
for n in "${ORDER[@]}"; do [ -e "$OUT/success_0610/raw/sweep/$n.json" ] && ALL+=("$n=runs/p26_${n}_0610"); done
py scripts/success_metrics.py "$OUT/success_0610" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > runs/p26b_success.log 2>&1
step "success table 2006-2010 exit=$? (${#ALL[@]} runs)"
git add "$OUT" && git commit -q -m "Phase 26: all six runs extended to 2010 and scored on 2006-2010

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && step "committed"
step "finished"
