#!/usr/bin/env bash
# Phase 26 (Susanne 2026-10-27): score on 5 years instead of 2 - more robust, and a restart may drift after a couple
# of years. The five restart runs (AL7, AL7h, AL7t, LAL7, L0; 2005-2007 from P20b's end-of-2004 state) are extended
# to 2009 on GPU 0, each with the settings its own chain was launched with. All six runs (P20b = p20bt 2005-2009) are
# then scored on 2005-2009, the years of the CLaMS and WACCM6 age references, and on 2008-2009 as a drift check
# against the Phase 23-25 scores of 2006-2007. Scoring runs one job at a time beside the chains; every CPU step is under
# scripts/memcap.sh.
#
#   bash scripts/phase26_run.sh [GPU]      restartable
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${1:-0}"; OUT="$REPO/docs/outputs/26_5yr_scoring"; LOG="$REPO/runs/p26_run.log"
W=/data/JCM_stripped
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 96G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p26] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
corr() { echo "++physics.terms.held_suarez.te_correction_file=$1 ++physics.terms.held_suarez.te_correction_mode=total"; }

# name prefix experiment extra (as in each run's runs/<prefix>_chain.log)
RUNS=(
  "AL7|p22_AL7|p22_teq|$(corr $W/jcm-strat-phase19/docs/outputs/22_teq_vortex/corrections/AL7.nc)"
  "AL7h|p25_AL7h|p22_teq|$(corr $W/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc)"
  "AL7t|p24_AL7t|p22_teq|$(corr $W/jcm-strat-phase24/docs/outputs/24_al7_taper/corrections/AL7t35_50.nc)"
  "LAL7|p23_LAL7|p23_lattop|$(corr $W/jcm-strat-phase23/docs/outputs/22_teq_vortex/corrections/AL7.nc)"
  "L0|p23_L0|p23_lattop|"
)

score() {  # <name> <prefix>: aggregates, diagnostics and raw success scores for 2005-2009 and 2008-2009
  local n="$1" pre="$2" a5="runs/p26_$1_0509" a2="runs/p26_$1_0809"
  [ -e "$a5/log.txt" ] || py scripts/link_segments.py "$a5" $(for y in 2005 2006 2007 2008 2009; do echo "$REPO/runs/${pre}_${y}0101"; done) >> "$LOG" 2>&1
  [ -e "$a2/log.txt" ] || py scripts/link_segments.py "$a2" "$REPO/runs/${pre}_20080101" "$REPO/runs/${pre}_20090101" >> "$LOG" 2>&1
  mkdir -p "$OUT/$n"
  py scripts/vortex_jets.py "$a5" "$OUT/$n" --years 2005-2009 --label "$n" > "runs/p26_vortex_$n.log" 2>&1; step "$n vortex_jets exit=$?"
  py scripts/seasonal_age_winds.py "$a5" "$OUT/$n" --years 2005-2009 --label "$n" > "runs/p26_seasonal_$n.log" 2>&1; step "$n seasonal exit=$?"
  py scripts/strat_circulation.py "$a5" "$OUT/$n" --years 2005-2009 --label "$n" --age-var aoa_sfc > "runs/p26_circ_$n.log" 2>&1; step "$n strat_circulation exit=$?"
  py scripts/success_metrics.py "$OUT/success" "$n=$a5" --t0 2005-01-01 --t1 2010-01-01 --window-years 5 > "runs/p26_success_$n.log" 2>&1
  step "$n success 2005-2009 exit=$?"
  py scripts/success_metrics.py "$OUT/success_0809" "$n=$a2" --t0 2008-01-01 --t1 2010-01-01 --window-years 2 > "runs/p26_success0809_$n.log" 2>&1
  step "$n success 2008-2009 exit=$?"
}

scorer() {  # scores P20b, then each run as soon as its chain has finished (marker runs/p26_<name>.done / .failed)
  score P20b p20bt
  for r in "${RUNS[@]}"; do
    local name="${r%%|*}" pre; pre=$(echo "$r" | cut -d'|' -f2)
    until [ -e "runs/p26_$name.done" ] || [ -e "runs/p26_$name.failed" ]; do sleep 60; done
    [ -e "runs/p26_$name.done" ] && score "$name" "$pre"
  done
}

step "start, commit $(git rev-parse --short HEAD)"
rm -f runs/p26_*.done runs/p26_*.failed
scorer &
for r in "${RUNS[@]}"; do
  IFS='|' read -r name pre exp extra <<< "$r"
  if [ ! -s "runs/${pre}_20090101/checkpoint.ckpt" ]; then
    while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
    step "extend $name to 2009 on GPU $GPU ($exp)"; t1=$(date +%s)
    EXPERIMENT="$exp" PREFIX="$pre" SCHEME=calendar YEARS=1990-2009 AGG="${pre}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$extra" \
      bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout_p26.log" 2>&1; rc=$?
    bad=$(grep -l 'atmosphere unhealthy' runs/${pre}_200[89]0101/log.txt 2>/dev/null | tr '\n' ' ')
    step "$name chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
    if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $name (runs/${pre}_chain.log), not scored"; touch "runs/p26_$name.failed"; continue; fi
  fi
  touch "runs/p26_$name.done"
done
wait
ALL5=(); ALL2=()
for n in P20b AL7 AL7h AL7t L0 LAL7; do
  [ -e "$OUT/success/raw/sweep/$n.json" ] && ALL5+=("$n=runs/p26_${n}_0509")
  [ -e "$OUT/success_0809/raw/sweep/$n.json" ] && ALL2+=("$n=runs/p26_${n}_0809")
done
py scripts/success_metrics.py "$OUT/success" "${ALL5[@]}" --t0 2005-01-01 --t1 2010-01-01 --window-years 5 > runs/p26_success.log 2>&1
step "success table 2005-2009 exit=$? (${#ALL5[@]} runs)"
py scripts/success_metrics.py "$OUT/success_0809" "${ALL2[@]}" --t0 2008-01-01 --t1 2010-01-01 --window-years 2 > runs/p26_success0809.log 2>&1
step "success table 2008-2009 exit=$? (${#ALL2[@]} runs)"
git add "$OUT" && git commit -q -m "Phase 26: all six runs scored on 2005-2009, and on 2008-2009 as a drift check" && step "committed"
step "finished"
