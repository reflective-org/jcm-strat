#!/usr/bin/env bash
# Phase 15 (Susanne, 2026-09-24): hyperparameter sweep of the dry model's stratospheric configuration toward CLaMS / ERA5-like
# dynamics, unattended on GPU 0 (tmux strat_p15_sweep, log runs/p15_sweep.log), hard budget BUDGET_H (46 h; "nothing longer than 48 h").
#   0. GPU visible and idle; inputs (QBO targets, strat81 ERA5 windows 1990-1994); pytest; 5-day smokes with the plausibility gate
#   1. base = the Phase 13b p13_jucker segments 1990-1992 linked (scripts/link_segments.py) and scored (scripts/sweep_score.py)
#   2. stage 1: every line of scripts/phase15_matrix.txt as a 3-year chain 1990-1992 (p15_base + physics group + overrides),
#      scored, leaderboard + record updated and committed after EACH run (scripts/sweep_leaderboard.py)
#   3. stage 2: scripts/sweep_plan.py combines the family winners -> scripts/phase15_matrix_stage2.txt -> same loop
#   4. stage 3: the best run of all stages continues its chain to 1990-1994 (segments 1990-1992 are reused), scored on
#      1993-1994, and gets the standard Phase 12/13 diagnostics against p13jucker_5yr and p12echam_5yr
# Before every run the remaining budget is checked against the measured minutes per simulated year; a run that would not
# finish (with the stage-3 reserve kept) is skipped and logged. Restartable: finished segments/scores are skipped.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
GPU="${GPU:-0}"; BUDGET_H="${BUDGET_H:-46}"; YEARS1="${YEARS1:-1990-1992}"; YEARS3="${YEARS3:-1990-1994}"
MPY="${MPY:-20}"                      # first estimate of end-to-end minutes per simulated year; replaced by the measured value
P13="${P13:-/data/JCM_stripped/jcm-strat-phase13/runs}"; P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/15_sweep"; SCORES="$OUT/scores"; mkdir -p "$OUT" "$SCORES" "$REPO/runs"
LOG="$REPO/runs/p15_sweep.log"; MATRIX="$REPO/scripts/phase15_matrix.txt"; MATRIX2="$REPO/scripts/phase15_matrix_stage2.txt"
T0=$(date +%s); DEADLINE=$((T0 + BUDGET_H * 3600))
export JAX_PLATFORMS_SAVE="${JAX_PLATFORMS:-}"

step() { echo "[p15] $(date -Is) $*" | tee -a "$LOG"; }
runlog() { echo "- $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M PDT') — $*" >> "$OUT/output.md"; }
remaining_min() { echo $(( (DEADLINE - $(date +%s)) / 60 )); }
gpu_visible() { CUDA_VISIBLE_DEVICES="$GPU" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$GPU" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
commit_record() {  # <message>
  git add -A "$OUT" PROGRESS.md scripts/phase15_matrix_stage2.txt >/dev/null 2>&1
  if git commit -q -m "Phase 15 sweep: $1" >/dev/null 2>&1; then step "committed: $1"; else step "nothing new to commit ($1)"; fi
}
leaderboard() { JAX_PLATFORMS=cpu python scripts/sweep_leaderboard.py "$OUT" --scores "$SCORES" 2>&1 | tail -1 | tee -a "$LOG"; }
step "start, commit $(git rev-parse --short HEAD), GPU $GPU, budget $BUDGET_H h (deadline $(date -d @"$DEADLINE" -Is)), stage-1 years $YEARS1, final $YEARS3"
runlog "pipeline started (commit $(git rev-parse --short HEAD), GPU $GPU, budget $BUDGET_H h)"

# ---- 0. GPU, inputs, tests
n=0; until gpu_visible; do [ $((n % 6)) -eq 0 ] && step "waiting for a JAX-visible GPU $GPU"; n=$((n + 1)); sleep 300; done
gpu_busy && { step "FAIL: GPU $GPU busy"; exit 1; }
step "GPU $GPU visible and idle"
y0="${YEARS3%-*}"; y1="${YEARS3#*-}"
win() { local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"; }
for y in $(seq "$y0" "$y1"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  [ -s "$(win l81_3af87627 "$y")" ] || { step "FAIL: no strat81 ERA5 window for $y"; exit 1; }
done
[ -s "$REPO/cache/era5/wb2_192x96_l81_3af87627_1989-12-31_1990-01-08_6h_u-v-T.nc" ] || { step "FAIL: no strat81 smoke window"; exit 1; }
for d in p13jucker_19900101 p13jucker_19910101 p13jucker_19920101 p13jucker_5yr p13jucker_19940101; do [ -d "$P13/$d" ] || { step "FAIL: $P13/$d missing"; exit 1; }; done
for d in p12echam_5yr p12echam_19940101; do [ -d "$P12/$d" ] || { step "FAIL: $P12/$d missing"; exit 1; }; done
step "inputs present"
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p15_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p15_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- smokes (5 days, GPU) with the plausibility gate: base, and one of each drag term
smoke() {  # <name> <physics> <overrides> <expected log line>
  local name=$1 phys=$2 ov=$3 expect=$4; local rundir="$REPO/runs/p15_smoke_$name"; mkdir -p "$rundir"
  local extra=(); [ "$ov" != "-" ] && read -r -a extra <<< "$ov"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$GPU python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p15_base "physics=$phys" "${extra[@]}" \
      run.start_date="1990-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true \
      physics.terms.held_suarez.qbo.year=1990 hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?; local nf; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke $name ran on the CPU"; return 1; }
  grep -q "JuckerColumns: JFV2013 table" "$rundir/log.txt" || { step "FAIL: smoke $name has no JuckerColumns line"; return 1; }
  grep -q "$expect" "$rundir/log.txt" || { step "FAIL: smoke $name lacks '$expect'"; return 1; }
  grep -q "save_interval: 0.25" "$rundir/log.txt" || { step "FAIL: smoke $name is not 6-hourly output"; return 1; }
  step "smoke $name exit=$rc ($nf files, $(grep -c 'Wall:' "$rundir/log.txt") chunks, $(grep 'Wall:' "$rundir/log.txt" | tail -1 | sed 's/.*(\(.*\))/\1/'))"
  [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || return 1
  JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
u = ds.u_wind.isel(time=-1).values; T = ds.temperature.isel(time=-1).values
want = {"u_wind", "v_wind", "temperature", "omega", "normalized_surface_pressure", "aoa150", "aoa_sfc", "aoa500"}
ok = np.isfinite(u).all() and np.isfinite(T).all() and 150 < T.min() and T.max() < 330 and np.abs(u).max() < 150 and set(ds.data_vars) == want and ds.sizes["time"] == 20
print(f"[smoke {d.split('/')[-1]}] levels {ds.sizes['level']}, vars {sorted(ds.data_vars)}, frames {ds.sizes['time']}; T {T.min():.0f}..{T.max():.0f} K, |u| max {np.abs(u).max():.0f} m/s -> {'GATE OK' if ok else 'GATE FAILED'}")
sys.exit(0 if ok else 2)
PY
  local g=$?; [ $g -eq 0 ] || { step "FAIL: smoke $name plausibility gate"; return 1; }
}
smoke base    strat15_jucker       -                                          "tau_scale 1, tau_max_days None"        || exit 1
smoke ray10   strat15_jucker_ray   physics.terms.rayleigh_drag.tau_days=10    "RayleighDragProfile: L81, drag 30 hPa -> 1 hPa, tau 10 d" || exit 1
smoke hines05 strat15_jucker_hines physics.terms.hines_gwd.rms_launch_wind=0.5 "HinesGwdLaunch: L81, launch 634 hPa -> launch_level 10" || exit 1
smoke lm      strat15_jucker_lm    -                                          "JuckerColumns" || exit 1
step "smokes passed"
runlog "pytest and the four 5-day smokes (base, ray10, hines05, lm) passed; the sweep starts"

# ---- 1. base: linked and scored on the CPU in the background while the first chain uses the GPU
base_pid=""
if [ ! -s "$SCORES/base.json" ]; then
  python scripts/link_segments.py runs/p15_base_3yr "$P13/p13jucker_19900101" "$P13/p13jucker_19910101" "$P13/p13jucker_19920101" >> "$LOG" 2>&1
  ( JAX_PLATFORMS=cpu python scripts/sweep_score.py runs/p15_base_3yr --name base --stage 1 \
      --desc "p13_jucker segments 1990-1992 (Phase 13b): strat81, JFV relaxation, no drag - THE BASE" --out "$SCORES" > "$REPO/runs/p15_score_base.log" 2>&1
    echo "[p15] $(date -Is) base scored exit=$? ($(tail -1 "$REPO/runs/p15_score_base.log" | cut -c1-300))" >> "$LOG" ) &
  base_pid=$!
  step "base scoring started in the background (pid $base_pid)"
fi
wait_base() { if [ -n "$base_pid" ]; then wait "$base_pid" 2>/dev/null; base_pid=""; fi; }

# ---- the sweep loop
run_entry() {  # <name> <physics> <overrides> <desc> <years> <stage>
  local name=$1 phys=$2 ov=$3 desc=$4 years=$5 stage=$6
  local prefix="p15_${name//+/_}"; local ny; ny=$(( ${years#*-} - ${years%-*} + 1 )); local agg="${prefix}_${ny}yr"
  local sname="$name"; [ "$stage" = 3 ] && sname="${name}_5yr"        # the winner keeps its 3-yr score; the 5-yr run is a new row
  if [ -s "$SCORES/$sname.json" ]; then step "skip $sname (scored)"; return 0; fi
  local need=$(( ny * MPY + 20 )); local reserve=$(( 2 * MPY + 120 ))
  [ "$stage" = 3 ] && reserve=0
  if [ $(( $(remaining_min) - reserve )) -lt $need ]; then
    step "SKIP $name for budget: needs ~$need min (+$reserve reserve), $(remaining_min) min left"; runlog "**skipped for budget**: $name ($desc)"; return 2
  fi
  local extra="physics=$phys"; [ "$ov" != "-" ] && extra="$extra $ov"
  step "run $name (stage $stage): $years, $extra"
  local t1; t1=$(date +%s)
  EXPERIMENT=p15_base PREFIX="$prefix" SCHEME=calendar YEARS="$years" AGG="$agg" SAVE_INTERVAL=0.25 GPU="$GPU" EXTRA="$extra" \
    bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/${prefix}_chain_stdout.log" 2>&1; local rc=$?
  local mins=$(( ($(date +%s) - t1) / 60 ))
  step "chain $name exit=$rc after $mins min (runs/${prefix}_chain.log)"
  if [ $rc -ne 0 ]; then runlog "**FAILED** chain $name after $mins min (see runs/${prefix}_chain.log)"; commit_record "$name failed"; return 1; fi
  local segs_run; segs_run=$(grep -c '\[chain\].*done .*exit=0' "$REPO/runs/${prefix}_chain.log")
  if [ "$segs_run" -gt 0 ] && [ "$stage" != 3 ] && [ "$mins" -gt $(( 5 * segs_run )) ]; then MPY=$(( (mins + segs_run - 1) / segs_run )); step "measured $MPY min/yr end-to-end"; fi
  local win=2; [ "$stage" = 3 ] && win=2
  JAX_PLATFORMS=cpu python scripts/sweep_score.py "runs/$agg" --name "$sname" --stage "$stage" --desc "$desc" --window-years $win --out "$SCORES" \
    > "$REPO/runs/p15_score_${sname//+/_}.log" 2>&1; local sc=$?
  local line; line=$(tail -1 "$REPO/runs/p15_score_${sname//+/_}.log" | cut -c1-400)
  step "score $sname exit=$sc: $line"
  runlog "stage $stage **$sname** ($desc): ${mins} min for $ny yr; $line"
  wait_base; leaderboard; commit_record "stage $stage $name"
  return 0
}
run_matrix() {  # <matrix file> <years> <stage>
  local f=$1 years=$2 stage=$3 name phys ov desc
  while IFS='|' read -r name phys ov desc; do
    name=$(echo "$name" | xargs); phys=$(echo "$phys" | xargs); ov=$(echo "$ov" | xargs); desc=$(echo "$desc" | xargs)
    [ -z "$name" ] || [[ "$name" == \#* ]] && continue
    run_entry "$name" "$phys" "$ov" "$desc" "$years" "$stage"
  done < "$f"
}

# ---- 2. stage 1
step "stage 1: $(grep -vc '^\s*#\|^\s*$' "$MATRIX") runs of $YEARS1"
run_matrix "$MATRIX" "$YEARS1" 1
wait_base; step "stage 1 finished; $(remaining_min) min left"

# ---- 3. stage 2 (planned from the scores)
JAX_PLATFORMS=cpu python scripts/sweep_plan.py --scores "$SCORES" --matrix "$MATRIX" --stage2 "$MATRIX2" > "$REPO/runs/p15_plan.log" 2>&1
step "stage 2 plan: $(grep -vc '^\s*#\|^\s*$' "$MATRIX2") run(s) ($(grep '^#   ' "$MATRIX2" | sed 's/^#   //' | tr '\n' ';'))"
runlog "stage 2 planned: $(grep '^#   ' "$MATRIX2" | sed 's/^#   //' | tr '\n' ';') -> $(grep -v '^#' "$MATRIX2" | cut -d'|' -f1 | xargs | tr ' ' ',')"
commit_record "stage 2 plan"
run_matrix "$MATRIX2" "$YEARS1" 2
step "stage 2 finished; $(remaining_min) min left"

# ---- 4. stage 3: the two best changed runs to five years + the standard diagnostics (budget permitting)
best=$(JAX_PLATFORMS=cpu python scripts/sweep_plan.py --scores "$SCORES" --best 2>/dev/null)
mapfile -t TOP < <(JAX_PLATFORMS=cpu python scripts/sweep_plan.py --scores "$SCORES" --top 2 2>/dev/null)
if [ "$best" = "base" ]; then
  step "the base is still the best scored configuration; stage 3 extends the two best CHANGED runs to document how close they come: ${TOP[*]}"
  runlog "stage 3: the base stays the best; the best changed runs (${TOP[*]}) are extended to $YEARS3 to document how close they come"
else
  step "stage 3: best run $best; extending ${TOP[*]} to $YEARS3"; runlog "stage 3: best run **$best**; ${TOP[*]} extended to $YEARS3"
fi
final_diag() {  # <name>
  local name=$1 prefix="p15_${1//+/_}"; local agg="runs/${prefix}_5yr"; local final="$OUT/final_${1//+/_}"; mkdir -p "$final"
  export JAX_PLATFORMS=cpu
  step "final diagnostics on $agg (phase12_compare x2 in parallel, aoa_vs_clams x3, mesosphere) -> $final"
  python scripts/phase12_compare.py --before "$P13/p13jucker_5yr" --after "$agg" --tag "vs_jucker" --stride 1 --last-days 60 \
    --label "Phase 15 $name vs the Phase 13b base (Jucker, no drag), 1990-1994" --before-label "p13_jucker (base)" --after-label "$name" \
    --clocks aoa_sfc aoa500 aoa150 --out "$final" > "$REPO/runs/p15_compare_${prefix}_vs_jucker.log" 2>&1 &
  python scripts/phase12_compare.py --before "$P12/p12echam_5yr" --after "$agg" --tag "vs_echam" --stride 1 --last-days 60 \
    --label "Phase 15 $name vs JCM full physics (p12_echam), 1990-1994" --before-label "full ECHAM" --after-label "$name" \
    --clocks aoa_sfc aoa500 aoa150 --out "$final" > "$REPO/runs/p15_compare_${prefix}_vs_echam.log" 2>&1 &
  local v
  for v in aoa150 aoa_sfc aoa500; do
    python scripts/aoa_vs_clams.py "$agg" "$final" --years 2005-2009 --last-saves 240 --var "$v" --second-run "$P13/p13jucker_5yr" --second-label "base (p13_jucker)" \
      --label "P15 $name 1990-1994 [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p15_aoa_${prefix}_${v}.log" 2>&1 &
  done
  wait
  python scripts/mesosphere_wstar.py "$P13/p13jucker_19940101:base Jucker (1994)" "runs/${prefix}_19940101:$name (1994)" \
    --reference "$P12/p12echam_19940101:full ECHAM (1994)" --stride 1 --last-saves 240 --out "$final" --tag p15 > "$REPO/runs/p15_mesosphere_${prefix}.log" 2>&1
  step "final diagnostics of $name exit=$?"
  runlog "final diagnostics of **$name** (1990-1994) in \`final_${1//+/_}/\`: \`vs_jucker_*\`, \`vs_echam_*\` (w*, ages, metrics.md), \`*_aoa_*\` (vs CLaMS/WACCM, base alongside), \`p15_mesosphere.md\`"
  unset JAX_PLATFORMS
}
for cand in "${TOP[@]}"; do
  [ -n "$cand" ] || continue
  row=$(awk -F'|' -v n="$cand" '!/^[[:space:]]*#/ { k=$1; gsub(/^[[:space:]]+|[[:space:]]+$/, "", k); if (k == n) { print; exit } }' "$MATRIX" "$MATRIX2" 2>/dev/null)
  [ -n "$row" ] || { step "no matrix row for $cand - skipped"; continue; }
  IFS='|' read -r name phys ov desc <<< "$row"
  phys=$(echo "$phys" | xargs); ov=$(echo "$ov" | xargs); desc=$(echo "$desc" | xargs)
  if [ $(remaining_min) -lt 150 ]; then step "SKIP the final diagnostics budget for $cand ($(remaining_min) min left)"; runlog "**skipped for budget**: stage 3 for $cand"; continue; fi
  run_entry "$cand" "$phys" "$ov" "$desc (five years)" "$YEARS3" 3; rc3=$?
  [ $rc3 -eq 0 ] && [ $(remaining_min) -gt 90 ] && final_diag "$cand"
done
leaderboard
sed -i 's/| \*\*running\*\* (unattended sweep on GPU 0)/| **done** (see the leaderboard in the record)/' PROGRESS.md
runlog "pipeline finished ($(( ($(date +%s) - T0) / 3600 )) h $(( (($(date +%s) - T0) % 3600) / 60 )) min); best run: $(JAX_PLATFORMS=cpu python scripts/sweep_plan.py --scores "$SCORES" --best 2>/dev/null)"
commit_record "finished"
step "finished"
