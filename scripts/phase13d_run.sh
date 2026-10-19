#!/usr/bin/env bash
# Phase 13d (Susanne, 2026-09-25): ONE run, Jucker relaxation + Hines only, ERA5 nudging < 150 hPa, strat81, 1990-1994, GPU 1
# (tmux phase13d-jucker-hines, log runs/p13d_run.log). Steps: GPU -> inputs -> pytest -> smoke with the plausibility gate ->
# chain -> diagnostics (compare pairs in parallel, aoa_vs_clams, mesosphere table) -> docs/outputs/13d_jucker_hines/.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU="${GPU:-1}"; P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/13d_jucker_hines"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p13d_run.log"
step() { echo "[p13d] $(date -Is) $*" | tee -a "$LOG"; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPU $GPU"
n=0; until gpu_visible "$GPU"; do [ $((n % 6)) -eq 0 ] && step "waiting for a visible GPU"; n=$((n + 1)); sleep 300; done
gpu_busy "$GPU" && { step "FAIL: GPU $GPU busy"; exit 1; }
y0="${YEARS%-*}"; y1="${YEARS#*-}"
win() { local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"; }
for y in $(seq "$y0" "$y1"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  [ -s "$(win l81_3af87627 "$y")" ] || { step "FAIL: no strat81 ERA5 window for $y"; exit 1; }
done
for d in runs/p13jucker_5yr runs/p13juckergwd_5yr runs/p13jucker_19940101 runs/p13juckergwd_19940101 "$P12/p12echam_5yr" "$P12/p12echam_19940101" "$P12/p12l81_19940101"; do
  [ -d "$d" ] || { step "FAIL: $d missing"; exit 1; }; done
step "inputs present"
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p13d_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p13d_tests.log"))"; [ $rc -eq 0 ] || exit 1
e=p13_jucker_hines; rundir="$REPO/runs/p13juckerhines_smoke5"; mkdir -p "$rundir"
( cd "$rundir" && CUDA_VISIBLE_DEVICES=$GPU python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$e" \
    run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true \
    physics.terms.held_suarez.qbo.year="$y0" hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1; rc=$?
nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke ran on the CPU"; exit 1; }
grep -q "JuckerColumns: JFV2013 table" "$rundir/log.txt" || { step "FAIL: smoke has no JuckerColumns line"; exit 1; }
grep -q "HinesGwdLaunch: L81, launch 634 hPa -> launch_level 10" "$rundir/log.txt" || { step "FAIL: smoke has no L81 launch line"; exit 1; }
step "smoke $e exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || exit 1
JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY' || { step "FAIL: smoke plausibility gate"; exit 1; }
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
u = ds.u_wind.isel(time=-1).values; T = ds.temperature.isel(time=-1).values
ok = np.isfinite(u).all() and np.isfinite(T).all() and 150 < T.min() and T.max() < 330 and np.abs(u).max() < 150
print(f"[smoke] levels {ds.sizes['level']}, vars {len(ds.data_vars)}; T {T.min():.0f}..{T.max():.0f} K, |u| max {np.abs(u).max():.0f} m/s -> {'GATE OK' if ok else 'GATE FAILED'}")
sys.exit(0 if ok else 2)
PY
step "launching chain p13jh (GPU $GPU)"
EXPERIMENT=p13_jucker_hines PREFIX=p13jh SCHEME=calendar YEARS="$YEARS" AGG=p13jh_5yr SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p13jh_chain_stdout.log" 2>&1; rc=$?; step "chain p13jh exit=$rc"
[ $rc -eq 0 ] || { step "FAIL: chain (runs/p13jh_chain.log)"; exit 1; }
export JAX_PLATFORMS=cpu
for y in $(seq "$y0" "$y1"); do python scripts/throughput.py "runs/p13jh_${y}0101" --label "P13d jh $y" --grid T63L81 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"; done
cmp() { local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "$REPO/runs/p13d_compare_$tag.log" 2>&1; step "compare $tag exit=$?"; }
step "phase12_compare x3 in parallel"
cmp hines        runs/p13jucker_5yr    runs/p13jh_5yr "Hines only added under the Jucker relaxation (strat81, nudged < 150 hPa, $YEARS)" "Jucker, no drag" "Jucker + Hines" &
cmp lm_off       runs/p13juckergwd_5yr runs/p13jh_5yr "Lott-Miller off: Jucker + Hines + LM -> Jucker + Hines (strat81, nudged < 150 hPa, $YEARS)" "Hines + Lott-Miller" "Hines only" &
cmp jh_vs_echam  "$P12/p12echam_5yr"   runs/p13jh_5yr "JCM full physics vs dry Jucker + Hines ($YEARS)" "full ECHAM" "Jucker + Hines" &
wait
for v in aoa150 aoa_sfc aoa500; do python scripts/aoa_vs_clams.py runs/p13jh_5yr "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
  --label "P13d Jucker + Hines $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p13jh_aoa_${v}.log" 2>&1 & done; wait; step "aoa_vs_clams done"
python scripts/mesosphere_wstar.py "$P12/p12l81_19940101:strat81 PK" "runs/p13jucker_19940101:Jucker" "runs/p13juckergwd_19940101:Jucker + Hines + LM" \
  "runs/p13jh_19940101:Jucker + Hines" --reference "$P12/p12echam_19940101:full ECHAM" --out "$OUT" --tag p13d > "$REPO/runs/p13d_mesosphere.log" 2>&1; step "mesosphere exit=$?"
step "finished"
