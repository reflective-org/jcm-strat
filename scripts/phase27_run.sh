#!/usr/bin/env bash
# Phase 27 (Susanne 2026-10-29): AL7h with lighter QBO nudging - does freeing the lower stratosphere from the 1-day QBO
# nudging improve its dynamics? Two runs, everything else as AL7h (p22_teq, AL7h correction, 2005-2010 from P20b's
# end-of-2004 state), scored on 2006-2010 beside the six Phase 26 runs:
#   QBO30  QBO window raised: zero at 50 hPa, full weight from 30 hPa up (p_bot 90 -> 50 hPa, taper 0.35 -> 0.22 decades;
#          the narrower taper also moves full weight at the top from 2.2 to 1.7 hPa)
#   QBO10d QBO relaxation time 1 -> 10 days (WACCM's), window unchanged
# Runs in parallel on GPUs 0 and 1; scoring one job at a time under scripts/memcap.sh at 60G.
#
#   bash scripts/phase27_run.sh      restartable
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
OUT="$REPO/docs/outputs/27_qbo_nudging"; P26="$REPO/docs/outputs/26_5yr_scoring"; LOG="$REPO/runs/p27_run.log"
CORR=/data/JCM_stripped/jcm-strat-phase25/docs/outputs/25_al7_half/corrections/AL7h.nc
Q=physics.terms.held_suarez.qbo
BASEX="++physics.terms.held_suarez.te_correction_file=$CORR ++physics.terms.held_suarez.te_correction_mode=total"
declare -A RUN=(
  [QBO30]="p27_QBO30|1|$BASEX ++$Q.p_bot_hpa=50.0 ++$Q.taper_decades=0.22"
  [QBO10d]="p27_QBO10d|0|$BASEX ++$Q.tau_days=10.0"
)
py() { JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" bash "$REPO/scripts/memcap.sh" -m 60G -- "$REPO/.venv/bin/python" "$@"; }
step() { echo "[p27] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }

run() {  # <name>: 2005-2010 from P20b 2004; marker runs/p27_<name>.done / .failed
  local name="$1" pre gpu extra; IFS='|' read -r pre gpu extra <<< "${RUN[$name]}"
  for y in $(seq 1990 2004); do [ -e "runs/${pre}_${y}0101" ] || ln -s "$REPO/runs/p20bt_${y}0101" "runs/${pre}_${y}0101"; done
  while nvidia-smi -i "$gpu" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $gpu busy"; sleep 300; done
  step "run $name on GPU $gpu: $extra"; local t1; t1=$(date +%s)
  EXPERIMENT=p22_teq PREFIX="$pre" SCHEME=calendar YEARS=1990-2010 AGG="${pre}_agg" SAVE_INTERVAL=0.25 GPU="$gpu" EXTRA="$extra" \
    bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout.log" 2>&1; local rc=$?
  local bad; bad=$(grep -l 'atmosphere unhealthy' runs/${pre}_20[01][0-9]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "$name chain exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  if [ $rc -ne 0 ] || [ -n "$bad" ]; then step "FAILED $name (runs/${pre}_chain.log)"; touch "runs/p27_$name.failed"; else touch "runs/p27_$name.done"; fi
}

score() {  # <name>: 2006-2010 aggregate, diagnostics, raw success score
  local n="$1" pre; pre="${RUN[$n]%%|*}"; local a="runs/p26_${n}_0610"
  [ -e "$a/log.txt" ] || py scripts/link_segments.py "$a" $(for y in 2006 2007 2008 2009 2010; do echo "$REPO/runs/${pre}_${y}0101"; done) >> "$LOG" 2>&1
  mkdir -p "$OUT/w0610/$n"
  py scripts/vortex_jets.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" > "runs/p27_vortex_$n.log" 2>&1; step "$n vortex_jets exit=$?"
  py scripts/seasonal_age_winds.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" > "runs/p27_seasonal_$n.log" 2>&1; step "$n seasonal exit=$?"
  py scripts/strat_circulation.py "$a" "$OUT/w0610/$n" --years 2006-2010 --label "$n" --age-var aoa_sfc > "runs/p27_circ_$n.log" 2>&1; step "$n strat_circulation exit=$?"
  py scripts/success_metrics.py "$OUT/success_0610" "$n=$a" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > "runs/p27_success_$n.log" 2>&1
  step "$n success 2006-2010 exit=$?"
}

step "start, commit $(git rev-parse --short HEAD)"
rm -f runs/p27_*.done runs/p27_*.failed
run QBO30 & sleep 60; run QBO10d &
S="$OUT/success_0610"; mkdir -p "$S/raw/sweep" "$S/raw/teq"
cp -n "$P26/success_0610/raw/sweep/"*.json "$S/raw/sweep/"; cp -n "$P26/success_0610/raw/teq/"*.json "$S/raw/teq/"
for n in QBO30 QBO10d; do
  until [ -e "runs/p27_$n.done" ] || [ -e "runs/p27_$n.failed" ]; do sleep 60; done
  [ -e "runs/p27_$n.done" ] && score "$n"
done
wait
ALL=(); for n in P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d; do [ -e "$S/raw/sweep/$n.json" ] && ALL+=("$n=runs/p26_${n}_0610"); done
py scripts/success_metrics.py "$S" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 > runs/p27_success.log 2>&1
step "success table 2006-2010 exit=$? (${#ALL[@]} runs)"
git add "$OUT" && git commit -q -m "Phase 27: AL7h with lighter QBO nudging (QBO30, QBO10d) scored on 2006-2010

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && step "committed"
step "finished"
