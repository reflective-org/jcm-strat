#!/usr/bin/env bash
# Phase 18 (Susanne 2026-10-01: "can you set this up what you just laid out and run it? Use GPU 0"): the JFV T_e correction with
# ERA5's diabatic HEATING as the target in the tropical lower stratosphere (|lat| < 30, 100-30 hPa, cos^2 tapers to 40 deg and
# 15 hPa) and Phase 17's ERA5-temperature target everywhere else (scripts/teq_correction.py --heating-target). The heating is the
# CLaMS v3 ERA5 THETA_DOT_TOT climatology 2000-2014 - the vertical velocity CLaMS itself is driven by.
#
#   tmux new-session -d -s strat_p18 'bash scripts/phase18_run.sh'
#
# Iteration i: runs/p18_H<i>_YYYY0101 for 1990-1997 are directory links to Phase 16's mix10trop segments, the chain runs 1998-1999
# from mix10trop's 1997 checkpoint (as Phase 17) with correction docs/outputs/18_heating/corrections/H<i>.nc. H1 = Phase 17's
# converged A4 outside the mask + the first heating step inside, from mix10trop itself; H<i+1> from run H<i> (alpha 0.7,
# cumulative). Score = sweep_score.py --w-metric full (w* annual/DJF/JJA + upward mass flux 100/70/30/10 hPa vs ERA5). After
# NITER iterations the best-scoring correction runs ten years 1990-1999 from ERA5 (H_final), with aoa_vs_clams and phase12_compare
# against mix10trop. GPU 0 only. Restartable (finished segments, corrections, scores are skipped). Budget BUDGET_H (default 20 h).
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
BUDGET_H="${BUDGET_H:-20}"; NITER="${NITER:-4}"; ALPHA="${ALPHA:-0.7}"; GPU=0
P16="${P16:-/data/JCM_stripped/jcm-strat-phase16/runs}"; START="p16_mix10trop"
A4="${A4:-/data/JCM_stripped/jcm-strat-phase17/docs/outputs/17_teq/corrections/A4.nc}"
EXP=p16_base_mix
MIX="physics.terms.tropo_tracer_mixing.k_m2_s=10 physics.terms.tropo_tracer_mixing.lat_max_deg=30"
DESC="mix10trop + T_e correction: ERA5 heating target in the tropical lower stratosphere, ERA5 T elsewhere"
OUT="$REPO/docs/outputs/18_heating"; SCORES="$OUT/scores"; CORR="$OUT/corrections"; mkdir -p "$SCORES" "$CORR" "$REPO/runs"
LOG="$REPO/runs/p18.log"; LOCK="$REPO/runs/.p18_git.lock"
T0=$(date +%s); DEADLINE=$((T0 + BUDGET_H * 3600))
step() { echo "[p18] $(date -Is) $*" | tee -a "$LOG"; }
runlog() { flock "$LOCK" bash -c "echo '- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M PDT') — $*' >> '$OUT/output.md'"; }
remaining_min() { echo $(( (DEADLINE - $(date +%s)) / 60 )); }
gitretry() { local i; for i in 1 2 3 4 5 6; do git "$@" 2>/dev/null && return 0; sleep 5; done; return 1; }   # a poller holds index.lock briefly
record() {
  flock "$LOCK" bash -c "cd '$REPO' && JAX_PLATFORMS=cpu python scripts/sweep_leaderboard.py '$OUT' --scores '$SCORES' 2>&1 | tail -1" | tee -a "$LOG"
  gitretry add -A "$OUT"; gitretry add -f "$CORR"/*.nc
  gitretry commit -q -m "Phase 18: $1" && step "committed: $1" || step "nothing committed ($1)"
}
score_run() {  # <name> <agg> <desc>
  local name=$1 agg=$2 desc=$3
  [ -s "$SCORES/$name.json" ] && { step "skip score $name"; return 0; }
  JAX_PLATFORMS=cpu python scripts/sweep_score.py "runs/$agg" --name "$name" --stage H --desc "$desc" --window-years 2 --w-metric full \
    --out "$SCORES" > "runs/p18_score_$name.log" 2>&1
  local line; line=$(tail -1 "runs/p18_score_$name.log" | cut -c1-500)
  step "score $name: $line"; runlog "**$name** ($desc): $line"; record "$name scored"
}
composite() { python3 -c "import json; print(json.load(open('$SCORES/$1.json'))['composite'])"; }
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

step "start: commit $(git rev-parse --short HEAD), GPU $GPU, NITER $NITER, alpha $ALPHA, budget $BUDGET_H h"
runlog "started (GPU $GPU, commit $(git rev-parse --short HEAD), $NITER iterations, alpha $ALPHA)"

for i in $(seq 1 "$NITER"); do
  name="H$i"; prefix="p18_$name"; corr="$CORR/$name.nc"
  [ -s "$SCORES/$name.json" ] && { step "skip $name (scored)"; continue; }
  if [ ! -s "$corr" ]; then
    if [ "$i" -eq 1 ]; then
      JAX_PLATFORMS=cpu python scripts/teq_correction.py "$P16/${START}_10yr" --heating-target --outer-from "$A4" --alpha "$ALPHA" \
        --out "$corr" 2>&1 | grep '^\[teq\]' | tee -a "$LOG"
    else
      JAX_PLATFORMS=cpu python scripts/teq_correction.py "runs/p18_H$((i - 1))_10yr" --heating-target --prev "$CORR/H$((i - 1)).nc" \
        --alpha "$ALPHA" --out "$corr" 2>&1 | grep '^\[teq\]' | tee -a "$LOG"
    fi
    [ -s "$corr" ] || { step "correction $name FAILED"; runlog "**FAILED** correction $name"; exit 1; }
  fi
  for y in 1990 1991 1992 1993 1994 1995 1996 1997; do
    [ -e "runs/${prefix}_${y}0101" ] || ln -s "$P16/${START}_${y}0101" "runs/${prefix}_${y}0101"
  done
  [ "$(remaining_min)" -gt 120 ] || { step "SKIP $name for budget"; runlog "**skipped for budget**: $name"; break; }
  wait_gpu || { step "SKIP $name: GPU 0 never free"; break; }
  step "run $name: 1998-1999 from $START 1997 (correction ${corr##*/})"; t1=$(date +%s)
  chain "$prefix" 1990-1999 "$MIX physics.terms.held_suarez.te_correction_file=$corr"; rc=$?
  step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min"
  [ $rc -eq 0 ] || { runlog "**FAILED** $name (runs/${prefix}_chain.log)"; record "$name failed"; exit 1; }
  score_run "$name" "${prefix}_10yr" "$DESC, iteration $i (1998-1999 from mix10trop 1997)"
done

# ---- ten years from ERA5 with the best iteration's correction
best=""; bestc=99
for i in $(seq 1 "$NITER"); do
  [ -s "$SCORES/H$i.json" ] || continue
  c=$(composite "H$i"); python3 -c "import sys; sys.exit(0 if $c < $bestc else 1)" && { best="H$i"; bestc=$c; }
done
if [ -n "$best" ]; then
  name="H_final"; prefix="p18_$name"; corr="$CORR/$best.nc"
  if [ -s "$SCORES/$name.json" ]; then step "skip $name (scored)"
  elif [ "$(remaining_min)" -lt $((10 * 36 + 30)) ]; then step "SKIP $name for budget ($(remaining_min) min left)"; runlog "**ten-year run skipped for budget**"
  elif wait_gpu; then
    step "run $name: 1990-1999 from ERA5 with $best (composite $bestc)"; runlog "best iteration $best (composite $bestc) -> ten years from ERA5"
    t1=$(date +%s); chain "$prefix" 1990-1999 "$MIX physics.terms.held_suarez.te_correction_file=$corr"; rc=$?
    step "chain $name exit=$rc after $(( ($(date +%s) - t1) / 60 )) min"
    if [ $rc -eq 0 ]; then
      score_run "$name" "${prefix}_10yr" "$DESC, correction $best, ten years 1990-1999 from ERA5"
      JAX_PLATFORMS=cpu python scripts/aoa_vs_clams.py "runs/${prefix}_10yr" "$OUT/final" --years 2005-2009 --last-saves 240 --var aoa150 \
        --second-run "$P16/p16_mix10trop_10yr" --second-label "Phase 16 mix10trop (10 yr)" \
        --label "P18 $name 1990-1999 [aoa150]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "runs/p18_aoa_$name.log" 2>&1
      JAX_PLATFORMS=cpu python scripts/phase12_compare.py --before "$P16/p16_mix10trop_10yr" --after "runs/${prefix}_10yr" --tag "${name}_vs_mix10trop" \
        --stride 1 --last-days 60 --label "Phase 18 $name vs Phase 16 mix10trop, 1990-1999" --before-label mix10trop --after-label "$name" \
        --clocks aoa_sfc aoa500 aoa150 --out "$OUT/final" > "runs/p18_compare_$name.log" 2>&1
      runlog "final diagnostics for $name in \`final/\`"; record "$name diagnostics"
    else runlog "**FAILED** $name"; record "$name failed"; fi
  fi
fi
step "finished; $(remaining_min) min left"; runlog "finished"
