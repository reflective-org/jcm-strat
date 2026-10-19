#!/usr/bin/env bash
# Phase 13c (Susanne, 2026-09-24): two TEN-year runs 1990-1999 on strat81 with the Jucker relaxation, gravity-wave drag and
# the ERA5 nudging cut off at 400 hPa, in parallel on two GPUs (tmux phase13c-n400, log runs/p13c_run.log):
#   jgn400  p13_jucker_gwd_n400    GPU_A  Hines + Lott-Miller
#   jhn400  p13_jucker_hines_n400  GPU_B  Hines only
# Steps: GPUs visible and idle -> inputs (QBO targets 1990-1999; strat81 windows, 1995-1999 from tmux preproc_p13c_l81_prefetch)
# -> pytest -> 5-day smokes with the plausibility gate -> both chains -> diagnostics (compare pairs in parallel; aoa_vs_clams;
# mesosphere table on the 1994 and 1999 segments) -> docs/outputs/13c_jucker_n400/. Budget: ~40 min/yr -> ~7 h chains + 1 h.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1999}"; GPU_A="${GPU_A:-1}"; GPU_B="${GPU_B:-2}"
P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/13c_jucker_n400"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p13c_run.log"
step() { echo "[p13c] $(date -Is) $*" | tee -a "$LOG"; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPUs $GPU_A/$GPU_B"

n=0
until gpu_visible "$GPU_A"; do [ $((n % 6)) -eq 0 ] && step "waiting for a visible GPU"; n=$((n + 1)); sleep 300; done
for g in "$GPU_A" "$GPU_B"; do gpu_busy "$g" && { step "FAIL: GPU $g busy"; exit 1; }; done
step "GPUs $GPU_A/$GPU_B visible and idle"

# ---- 1. inputs
y0="${YEARS%-*}"; y1="${YEARS#*-}"
win() {  # <table-tag> <year> -> window file name for one calendar-year segment
  local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"
}
for y in $(seq "$y0" "$y1"); do [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }; done
[ -s "$REPO/cache/era5/wb2_192x96_l81_3af87627_1989-12-31_1990-01-08_6h_u-v-T.nc" ] || { step "FAIL: no strat81 smoke window"; exit 1; }
l81_missing() { local y; for y in $(seq "$y0" "$y1"); do [ -s "$(win l81_3af87627 "$y")" ] || return 0; done; return 1; }
n=0
while l81_missing; do
  if ! tmux has-session -t preproc_p13c_l81_prefetch 2>/dev/null; then
    step "strat81 windows missing and the prefetch session is gone - running the prefetch here"
    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme calendar --years "$YEARS" --save-interval 0.25 -- +experiment=p12_l81 >> "$REPO/runs/p13c_prefetch_l81.log" 2>&1 \
      || { step "FAIL: strat81 prefetch"; exit 1; }
    continue
  fi
  [ $((n % 10)) -eq 0 ] && step "waiting for the strat81 ERA5 windows 1995-1999 (tmux preproc_p13c_l81_prefetch, runs/p13c_prefetch_l81.log)"
  n=$((n + 1)); sleep 120
done
for d in p12echam_5yr p12echam_19940101 p12l81_5yr p12l81_19940101; do [ -d "$P12/$d" ] || { step "FAIL: $P12/$d missing"; exit 1; }; done
step "inputs present"

# ---- 2. unit tests
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p13c_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p13c_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- 3. smokes, in parallel on the two GPUs, with the plausibility gate
smoke() {  # <experiment> <gpu>
  local e=$1 g=$2; local rundir="$REPO/runs/${e//_/}_smoke5"; mkdir -p "$rundir"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$g python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$e" \
      run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true \
      physics.terms.held_suarez.qbo.year="$y0" hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?; local nf; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke $e ran on the CPU"; return 1; }
  grep -q "JuckerColumns: JFV2013 table" "$rundir/log.txt" || { step "FAIL: smoke $e has no JuckerColumns line"; return 1; }
  grep -q "HinesGwdLaunch: L81, launch 634 hPa -> launch_level 10" "$rundir/log.txt" || { step "FAIL: smoke $e has no L81 launch_level 10 line"; return 1; }
  step "smoke $e exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || return 1
  JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
u = ds.u_wind.isel(time=-1).values; T = ds.temperature.isel(time=-1).values
ok = np.isfinite(u).all() and np.isfinite(T).all() and 150 < T.min() and T.max() < 330 and np.abs(u).max() < 150
print(f"[smoke {d.split('/')[-1]}] levels {ds.sizes['level']}, vars {len(ds.data_vars)} (moist diagnostics dropped: {'pressure_full' not in ds}); "
      f"T {T.min():.0f}..{T.max():.0f} K, |u| max {np.abs(u).max():.0f} m/s -> {'GATE OK' if ok else 'GATE FAILED'}")
sys.exit(0 if ok else 2)
PY
  local g2=$?; [ $g2 -eq 0 ] || { step "FAIL: smoke $e plausibility gate"; return 1; }
}
smoke p13_jucker_gwd_n400 "$GPU_A" & sa=$!
sleep 45; smoke p13_jucker_hines_n400 "$GPU_B" & sb=$!
wait $sa; ra=$?; wait $sb; rb=$?
[ $ra -eq 0 ] && [ $rb -eq 0 ] || { step "FAIL: a smoke failed"; exit 1; }

# ---- 4. chains, both at once
chain() {  # <experiment> <prefix> <gpu>
  step "launching chain $2 (GPU $3)"
  EXPERIMENT=$1 PREFIX=$2 SCHEME=calendar YEARS="$YEARS" AGG=${2}_10yr SAVE_INTERVAL=0.25 GPU="$3" \
    bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/${2}_chain_stdout.log" 2>&1; local rc=$?
  step "chain $2 exit=$rc"; return $rc
}
chain p13_jucker_gwd_n400 p13jgn400 "$GPU_A" & pa=$!
sleep 90
chain p13_jucker_hines_n400 p13jhn400 "$GPU_B" & pb=$!
wait $pa; ra=$?; wait $pb; rb=$?
[ $ra -eq 0 ] && [ $rb -eq 0 ] || step "WARNING: a chain failed (runs/p13j*n400_chain.log); diagnostics run for what exists"

# ---- 5. diagnostics (CPU)
export JAX_PLATFORMS=cpu
step "throughput rows"
for pre in p13jgn400 p13jhn400; do for y in $(seq "$y0" "$y1"); do
  [ -d "runs/${pre}_${y}0101" ] || continue
  python scripts/throughput.py "runs/${pre}_${y}0101" --label "P13c ${pre#p13} $y" --grid T63L81 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done; done
cmp() {  # <tag> <before> <after> <label> <before-label> <after-label>
  local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  [ -d "$b" ] && [ -d "$a" ] || { step "compare $tag skipped ($b / $a missing)"; return; }
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "$REPO/runs/p13c_compare_$tag.log" 2>&1; step "compare $tag exit=$?"
}
step "phase12_compare x4 in parallel"
cmp hines_vs_lm     runs/p13jgn400_10yr   runs/p13jhn400_10yr "Lott-Miller off: Hines + LM -> Hines only (Jucker, strat81, nudged < 400 hPa, $YEARS)" "Hines + Lott-Miller" "Hines only" &
cmp n400            runs/p13juckergwd_5yr runs/p13jgn400_10yr "Jucker + GWD: nudging cutoff 150 -> 400 hPa (and 5 -> 10 yr)" "nudged < 150 hPa (5 yr)" "nudged < 400 hPa (10 yr)" &
cmp jgn400_vs_echam "$P12/p12echam_5yr"   runs/p13jgn400_10yr "JCM full physics vs dry Jucker + GWD, nudged < 400 hPa" "full ECHAM (5 yr)" "Jucker + GWD n400 (10 yr)" &
cmp jhn400_vs_jucker runs/p13jucker_5yr   runs/p13jhn400_10yr "Jucker no drag (5 yr, < 150 hPa) -> Jucker + Hines only, nudged < 400 hPa (10 yr)" "Jucker, no drag" "Jucker + Hines, n400" &
wait
for pre in p13jgn400 p13jhn400; do [ -d "runs/${pre}_10yr" ] || continue; for v in aoa150 aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/${pre}_10yr" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P13c ${pre#p13} $YEARS [$v]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/${pre}_aoa_${v}.log" 2>&1 &
done; done; wait; step "aoa_vs_clams done"
step "mesosphere w* (1994 and 1999 segments)"
segs=("$P12/p12l81_19940101:strat81 PK (1994)" "runs/p13jucker_19940101:Jucker (1994)" "runs/p13juckergwd_19940101:Jucker + GWD (1994)")
for pre in p13jgn400 p13jhn400; do for y in 1994 1999; do [ -d "runs/${pre}_${y}0101" ] && segs+=("runs/${pre}_${y}0101:${pre#p13} ($y)"); done; done
python scripts/mesosphere_wstar.py "${segs[@]}" --reference "$P12/p12echam_19940101:full ECHAM (1994)" --out "$OUT" --tag p13c > "$REPO/runs/p13c_mesosphere.log" 2>&1; step "mesosphere exit=$?"
step "finished"
