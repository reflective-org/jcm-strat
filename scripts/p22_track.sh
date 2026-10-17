#!/usr/bin/env bash
# Phase 22 (Susanne 2026-10-16): iterate the equilibrium-temperature correction of the Phase 20b setup toward ERA5 so the lower and
# middle stratosphere - above all the polar vortex at ~50 hPa - matches ERA5. One TRACK = one recipe, iterated:
#
#   iteration i of track T: runs/p22_<T><i>_YYYY0101 for 1990-2004 are links to P20b's (p20bt) segments, so the chain runs
#   2005-2007 only, from P20b's end-of-2004 state (clocks 15 years old), with correction corrections/<T><i>.nc; scored on
#   2005-04..2007-12 against ERA5 for the same months (scripts/teq_score.py); the next correction comes from that window
#   (scripts/teq_update.py, cumulative). Iteration 0 is P20b itself unless the track changes the physics (OVR, e.g. the polar-cap
#   tau), in which case <T>0 is run with the overrides and no correction.
#
#   bash scripts/p22_track.sh T GPU [KEY=VALUE ...]     keys (defaults):
#     MODE=zonal|chang3d  LAT="25 35"  PR="1 100"  SMOOTH=1  ALPHA=  CMODE=jfv|total  OVR="hydra overrides"  NITER=8
#     DESC="text"
#   Stops at NITER, or when u_ls_ext gains < 0.1 m/s twice in a row, or on the Phase 22 deadline (runs/p22_deadline, epoch s).
#   Restartable: finished segments, corrections and scores are skipped.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
T="${1:?track name}"; GPU="${2:?gpu}"; shift 2
MODE=zonal; LAT="25 35"; PR="1 100"; SMOOTH=1; ALPHA=""; CMODE=jfv; OVR=""; NITER=8; DESC="$T"
for kv in "$@"; do eval "${kv%%=*}=\"\${kv#*=}\""; done
OUT="$REPO/docs/outputs/22_teq_vortex"; SC="$OUT/scores"; CO="$OUT/corrections"; mkdir -p "$SC" "$CO"
LOG="$REPO/runs/p22_$T.log"; LOCK="$REPO/runs/.p22_git.lock"; BASE=p20bt; T0W=2005-04-01; T1W=2008-01-01
DEADLINE=$(cat "$REPO/runs/p22_deadline")
PY="$REPO/.venv/bin/python"
step() { echo "[p22 $T] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*" | tee -a "$LOG"; }
note() { flock "$LOCK" bash -c "echo '- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') - **$T** $*' >> '$OUT/runlog.md'"; }
left_min() { echo $(( (DEADLINE - $(date +%s)) / 60 )); }
record() {
  flock "$LOCK" bash -c "cd '$REPO' && JAX_PLATFORMS=cpu '$PY' scripts/p22_leaderboard.py '$OUT' > /dev/null 2>&1; \
    git add '$OUT' >/dev/null 2>&1; git add -f '$CO'/*.nc '$SC'/*.json >/dev/null 2>&1; \
    git commit -q -m 'Phase 22: $1' >/dev/null 2>&1 && echo committed || echo 'nothing to commit'" >> "$LOG"
}
score() {  # <name> <agg> <desc>
  [ -s "$SC/$1.json" ] && return 0
  JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" "$PY" scripts/teq_score.py "runs/$2" --t0 $T0W --t1 $T1W --name "$1" --desc "$3" --out "$SC" \
    > "runs/p22_score_$1.log" 2>&1 || { step "score $1 FAILED (runs/p22_score_$1.log)"; return 1; }
  local line; line=$(grep '^\[score\]' "runs/p22_score_$1.log" | tail -1 | cut -c1-600); step "$line"; note "$line"; record "$1 scored"
}
metric() { python3 -c "import json; print(json.load(open('$SC/$1.json'))['u_ls_ext'])"; }
update() {  # <from agg> <out> [prev]
  [ -s "$2" ] && return 0
  local sm=""; [ "$SMOOTH" = 1 ] && sm="--smooth"; local al=""; [ -n "$ALPHA" ] && al="--alpha $ALPHA"
  local pv=""; [ -n "${3:-}" ] && pv="--prev $3"
  # shellcheck disable=SC2086
  JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES="" "$PY" scripts/teq_update.py "runs/$1" --t0 $T0W --t1 $T1W --mode "$MODE" --lat-mask $LAT --p-range $PR \
    $sm $al $pv --out "$2" 2>&1 | grep '^\[teq\]' | tee -a "$LOG"
  [ -s "$2" ] || { step "update FAILED -> $2"; return 1; }
}
run_iter() {  # <i> <correction file or empty>
  local name="$T$1"; local pre="p22_$name"
  for y in $(seq 1990 2004); do [ -e "runs/${pre}_${y}0101" ] || ln -s "$REPO/runs/${BASE}_${y}0101" "runs/${pre}_${y}0101"; done
  local extra="$OVR"; [ -n "$2" ] && extra="$extra ++physics.terms.held_suarez.te_correction_file=$2 ++physics.terms.held_suarez.te_correction_mode=$CMODE"
  [ "$(left_min)" -gt 75 ] || { step "SKIP $name: deadline"; note "skipped $name for the deadline"; return 2; }
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do step "GPU $GPU busy"; sleep 300; done
  step "run $name (2005-2007 from P20b 2004; ${2##*/}) overrides: ${extra:-none}"; local t1; t1=$(date +%s)
  EXPERIMENT=p22_teq PREFIX="$pre" SCHEME=calendar YEARS=1990-2007 AGG="${pre}_agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$extra" \
    bash scripts/chain_segments.sh > "runs/${pre}_chain_stdout.log" 2>&1; local rc=$?
  local bad; bad=$(grep -l 'atmosphere unhealthy' runs/${pre}_200[5-7]0101/log.txt 2>/dev/null | tr '\n' ' ')
  step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min ${bad:+HEALTH STOP: $bad}"
  if [ $rc -ne 0 ] || [ -n "$bad" ]; then note "**FAILED** $name (exit $rc ${bad:+health stop}; runs/${pre}_chain.log)"; record "$name failed"; return 1; fi
  score "$name" "${pre}_agg" "$DESC, iteration $1"
}

[ -s "$REPO/runs/p22_deadline" ] || { echo "no runs/p22_deadline"; exit 1; }
printf "MODE=%q\nLAT=%q\nPR=%q\nSMOOTH=%q\nALPHA=%q\nCMODE=%q\nOVR=%q\nDESC=%q\n" "$MODE" "$LAT" "$PR" "$SMOOTH" "$ALPHA" "$CMODE" "$OVR" "$DESC" > "$REPO/runs/p22_track_$T.env"
step "start: $DESC | MODE=$MODE LAT=$LAT PR=$PR SMOOTH=$SMOOTH ALPHA=${ALPHA:-default} CMODE=$CMODE OVR=${OVR:-none} NITER=$NITER GPU=$GPU commit $(git rev-parse --short HEAD), $(left_min) min to deadline"
note "started: $DESC (MODE=$MODE LAT=$LAT PR=$PR SMOOTH=$SMOOTH ALPHA=${ALPHA:-default} CMODE=$CMODE OVR=${OVR:-none}; GPU $GPU)"
# iteration 0
if [ -n "$OVR" ]; then run_iter 0 "" || exit 1; src0="p22_${T}0_agg"; score0="${T}0"
else src0="p20bt_20yr"; score0="P20b_base"; [ -s "$SC/P20b_base.json" ] || score P20b_base p20bt_20yr "P20b (p20bt) itself, no correction"; fi
prev_m=$(metric "$score0"); prev_corr=""; prev_src="$src0"; flat=0
for i in $(seq 1 "$NITER"); do
  corr="$CO/$T$i.nc"
  update "$prev_src" "$corr" "$prev_corr" || exit 1
  run_iter "$i" "$corr"; rc=$?; [ $rc -eq 2 ] && break; [ $rc -eq 0 ] || exit 1
  m=$(metric "$T$i")
  if python3 -c "import sys; sys.exit(0 if $prev_m - $m < 0.1 else 1)"; then flat=$((flat + 1)); else flat=0; fi
  step "u_ls_ext $prev_m -> $m m/s (flat count $flat)"
  prev_m=$m; prev_corr="$corr"; prev_src="p22_$T${i}_agg"
  [ $flat -ge 2 ] && { step "converged (two iterations gaining < 0.1 m/s)"; note "converged after iteration $i"; break; }
done
record "track $T finished"; step "track finished, $(left_min) min to deadline"; note "finished"
