#!/usr/bin/env bash
# Phase 17 (Susanne 2026-10-01: "you can use GPU 0, 1 and 2. I need age of air to look like that of CLaMS, and the tropical upwelling
# needs to match ERA5 better too"): damped fixed-point iterations of the JFV T_e correction toward the ERA5 temperature climatology
# (scripts/teq_correction.py), one track per GPU, then a ten-year confirmation run of the track's last correction.
#
#   bash scripts/phase17_run.sh A      # GPU 0: Phase 16 mix10trop (Jucker, Rayleigh 30 d above 30 hPa, nudged < 100 hPa, tropical tracer mixing)
#   bash scripts/phase17_run.sh B      # GPU 1: the same without the Rayleigh drag (does a right T_e replace the drag?)
#   bash scripts/phase17_run.sh B0     # GPU 2: B with no correction (the drag removal alone, for attribution)
#
# Iteration i of track T: runs/p17_T<i>_YYYY0101 for 1990-1997 are directory links to Phase 16's mix10trop segments, so the chain
# runs 1998-1999 only, from mix10trop's 1997 checkpoint (clocks eight years old), with correction docs/outputs/17_teq/corrections/
# T<i>.nc; aggregate runs/p17_T<i>_10yr, scored on 1998-1999 (scripts/sweep_score.py; w* vs ERA5 once cache/era5_ref has the TEM
# files). The next correction comes from that run (alpha 0.7, cumulative). Stops after NITER iterations or when the T RMSE gains
# < 0.2 K. Then T_final: 1990-1999 from ERA5 initial conditions with the last correction (ages comparable with Phase 16's).
# Restartable: finished segments, corrections and scores are skipped. Budget BUDGET_H hours (default 24).
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
T="${1:?track A, B or B0}"; BUDGET_H="${BUDGET_H:-24}"; NITER="${NITER:-4}"; ALPHA="${ALPHA:-0.7}"
P16="${P16:-/data/JCM_stripped/jcm-strat-phase16/runs}"; START="p16_mix10trop"
MIX="physics.terms.tropo_tracer_mixing.k_m2_s=10 physics.terms.tropo_tracer_mixing.lat_max_deg=30"
case "$T" in
  A)  GPU=0; EXP=p16_base_mix; DESC="mix10trop (Jucker + Rayleigh 30 d + tropical tracer mixing)";;
  B)  GPU=1; EXP=p16_n100_mix; DESC="mix10trop without the Rayleigh drag";;
  B0) GPU=2; EXP=p16_n100_mix; DESC="mix10trop without the Rayleigh drag, NO T_e correction"; NITER=0;;
  *)  echo "track must be A, B or B0"; exit 1;;
esac
OUT="$REPO/docs/outputs/17_teq"; SCORES="$OUT/scores"; CORR="$OUT/corrections"; mkdir -p "$SCORES" "$CORR" "$REPO/runs"
LOG="$REPO/runs/p17_$T.log"; LOCK="$REPO/runs/.p17_git.lock"
T0=$(date +%s); DEADLINE=$((T0 + BUDGET_H * 3600))
step() { echo "[p17$T] $(date -Is) $*" | tee -a "$LOG"; }
runlog() { flock "$LOCK" bash -c "echo '- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M PDT') — track $T: $*' >> '$OUT/output.md'"; }
remaining_min() { echo $(( (DEADLINE - $(date +%s)) / 60 )); }
record() {
  flock "$LOCK" bash -c "cd '$REPO' && JAX_PLATFORMS=cpu python scripts/sweep_leaderboard.py '$OUT' --scores '$SCORES' 2>&1 | tail -1; \
    git add -A '$OUT' >/dev/null 2>&1; git add -f '$CORR'/*.nc >/dev/null 2>&1; \
    git commit -q -m 'Phase 17: $1' >/dev/null 2>&1 && echo committed || echo 'nothing to commit'" | tee -a "$LOG"
}
score_run() {  # <name> <agg> <desc>
  local name=$1 agg=$2 desc=$3
  [ -s "$SCORES/$name.json" ] && { step "skip score $name"; return 0; }
  JAX_PLATFORMS=cpu python scripts/sweep_score.py "runs/$agg" --name "$name" --stage "$T" --desc "$desc" --window-years 2 --out "$SCORES" \
    > "runs/p17_score_$name.log" 2>&1
  local line; line=$(tail -1 "runs/p17_score_$name.log" | cut -c1-500)
  step "score $name: $line"; runlog "**$name** ($desc): $line"; record "$name scored"
}
t_rmse() { python3 -c "import json,sys; print(json.load(open('$SCORES/$1.json'))['T_rmse'])"; }
chain() {  # <prefix> <years> <extra overrides>
  EXPERIMENT="$EXP" PREFIX="$1" SCHEME=calendar YEARS="$2" AGG="$1_10yr" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$3" \
    bash "$REPO/scripts/chain_segments.sh" > "runs/$1_chain_stdout.log" 2>&1
}
wait_gpu() {
  local n=0
  while nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; do
    [ $((n % 6)) -eq 0 ] && step "GPU $GPU busy - waiting"; n=$((n + 1)); sleep 300
    [ "$(remaining_min)" -gt 100 ] || return 1
  done
}

step "start track $T ($DESC): commit $(git rev-parse --short HEAD), GPU $GPU, NITER $NITER, alpha $ALPHA, budget $BUDGET_H h"
runlog "started ($DESC; GPU $GPU, commit $(git rev-parse --short HEAD), $NITER iterations, alpha $ALPHA)"

iterate() {  # <i>: one 1998-1999 run with correction <T><i> (none for i=0)
  local i=$1 name="${T}$1"; local prefix="p17_$name"; local corr="$CORR/$name.nc"
  [ -s "$SCORES/$name.json" ] && { step "skip $name (scored)"; return 0; }
  local extra="$MIX"
  if [ "$i" -gt 0 ]; then
    if [ ! -s "$corr" ]; then
      if [ "$i" -eq 1 ]; then cp "$CORR/p17_iter1.nc" "$corr"                      # from mix10trop itself
      else JAX_PLATFORMS=cpu python scripts/teq_correction.py "runs/p17_${T}$((i - 1))_10yr" --prev "$CORR/${T}$((i - 1)).nc" \
             --alpha "$ALPHA" --out "$corr" 2>&1 | grep '^\[teq\]' | tee -a "$LOG"
      fi
    fi
    extra="$extra physics.terms.held_suarez.te_correction_file=$corr"
  fi
  for y in 1990 1991 1992 1993 1994 1995 1996 1997; do
    [ -e "runs/${prefix}_${y}0101" ] || ln -s "$P16/${START}_${y}0101" "runs/${prefix}_${y}0101"
  done
  [ "$(remaining_min)" -gt 120 ] || { step "SKIP $name for budget"; runlog "**skipped for budget**: $name"; return 2; }
  wait_gpu || { step "SKIP $name: GPU never free"; return 2; }
  step "run $name: 1998-1999 from $START 1997 (correction: ${corr##*/})"; local t1; t1=$(date +%s)
  chain "$prefix" 1990-1999 "$extra"; local rc=$?
  step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min"
  [ $rc -eq 0 ] || { runlog "**FAILED** $name (runs/${prefix}_chain.log)"; record "$name failed"; return 1; }
  score_run "$name" "${prefix}_10yr" "$DESC, iteration $i (1998-1999 from mix10trop 1997)"
}

last=0
for i in $(seq 0 "$NITER"); do
  [ "$T" != B0 ] && [ "$i" -eq 0 ] && continue          # A's iteration 0 is mix10trop itself (scored as p16_mix10trop); B's is B0
  iterate "$i" || break
  last=$i
  if [ "$i" -ge 2 ]; then
    prev=$(t_rmse "${T}$((i - 1))"); cur=$(t_rmse "${T}$i")
    if python3 -c "import sys; sys.exit(0 if $prev - $cur < 0.2 else 1)"; then step "T RMSE $prev -> $cur K: converged"; break; fi
  fi
done

# ---- ten-year confirmation from ERA5 initial conditions with the last correction
if [ "$T" != B0 ] && [ "$last" -ge 1 ]; then
  name="${T}_final"; prefix="p17_$name"; corr="$CORR/${T}${last}.nc"
  if [ -s "$SCORES/$name.json" ]; then step "skip $name (scored)"
  elif [ "$(remaining_min)" -lt $((10 * 36 + 30)) ]; then step "SKIP $name for budget ($(remaining_min) min left)"; runlog "**ten-year run skipped for budget** ($(remaining_min) min left)"
  else
    wait_gpu && { step "run $name: 1990-1999 from ERA5 with ${corr##*/}"; t1=$(date +%s)
      chain "$prefix" 1990-1999 "$MIX physics.terms.held_suarez.te_correction_file=$corr"; rc=$?
      step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min"
      if [ $rc -eq 0 ]; then
        score_run "$name" "${prefix}_10yr" "$DESC with correction ${T}${last}, ten years 1990-1999 from ERA5"
        JAX_PLATFORMS=cpu python scripts/aoa_vs_clams.py "runs/${prefix}_10yr" "$OUT/final" --years 2005-2009 --last-saves 240 --var aoa150 \
          --second-run "$P16/p16_mix10trop_10yr" --second-label "Phase 16 mix10trop (10 yr)" \
          --label "P17 $name 1990-1999 [aoa150]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "runs/p17_aoa_$name.log" 2>&1
        JAX_PLATFORMS=cpu python scripts/phase12_compare.py --before "$P16/p16_mix10trop_10yr" --after "runs/${prefix}_10yr" --tag "${name}_vs_mix10trop" \
          --stride 1 --last-days 60 --label "Phase 17 $name vs Phase 16 mix10trop, 1990-1999" --before-label mix10trop --after-label "$name" \
          --clocks aoa_sfc aoa500 aoa150 --out "$OUT/final" > "runs/p17_compare_$name.log" 2>&1
        runlog "final diagnostics for $name in \`final/\`"; record "$name diagnostics"
      else runlog "**FAILED** $name"; record "$name failed"; fi; }
  fi
fi
step "track $T finished; $(remaining_min) min left"; runlog "finished"
