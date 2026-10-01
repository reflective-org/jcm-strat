#!/usr/bin/env bash
# Phase 13b: the Jucker, Fueglistaler & Vallis (2013) relaxation in the dry model (Susanne, 2026-09-23: "Go but do it with
# L81"), unattended on ONE GPU (tmux phase13b-jucker, log runs/p13b_run.log). Two 5-year chains 1990-1994, sequential:
#   jucker      p13_jucker      strat81, PK relaxation -> JFV2013 T_e/tau above 100 hPa, no drag     (vs p12l81_5yr)
#   jucker_gwd  p13_jucker_gwd  the same + Hines (launch 634 hPa) + Lott-Miller = option (c)          (vs jucker, p13gwd_5yr, p12echam_5yr)
# Steps: GPU visible and idle -> inputs (QBO targets, strat81 windows) -> pytest -> 5-day smokes (sequential, same GPU) with
# a physical-plausibility gate -> chain 1 -> chain 2 -> diagnostics on the CPU with the compare pairs IN PARALLEL (Phase 13:
# 40 min each in series) -> mesosphere table over every Phase 12/13 run -> docs/outputs/13b_jucker/. Budget ~7 h; the tmux
# command wraps this script in `timeout 13h`.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU="${GPU:-1}"
P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/13b_jucker"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p13b_run.log"
step() { echo "[p13b] $(date -Is) $*" | tee -a "$LOG"; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPU $GPU, Phase 12 runs $P12"

# ---- 0. the one GPU
n=0
until gpu_visible "$GPU"; do
  [ $((n % 6)) -eq 0 ] && step "waiting for a visible GPU (CUDA_ERROR_NO_DEVICE? run: sudo bash scripts/restore_nvidia_dev.sh)"
  n=$((n + 1)); sleep 300
done
n=0
while gpu_busy "$GPU"; do [ $((n % 10)) -eq 0 ] && step "GPU $GPU busy - waiting (one GPU only, no other is taken)"; n=$((n + 1)); sleep 120; done
step "GPU $GPU visible and idle"

# ---- 1. inputs
y0="${YEARS%-*}"; y1="${YEARS#*-}"
win() {  # <table-tag> <year> -> window file name for one calendar-year segment
  local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"
}
for y in $(seq "$y0" "$y1"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  [ -s "$(win l81_3af87627 "$y")" ] || { step "FAIL: no strat81 ERA5 window for $y"; exit 1; }
done
[ -s "$REPO/cache/era5/wb2_192x96_l81_3af87627_1989-12-31_1990-01-08_6h_u-v-T.nc" ] || { step "FAIL: no strat81 smoke window"; exit 1; }
[ -s "$REPO/jcm_strat/data/jfv2013_te_tau_zm.nc" ] || { step "FAIL: JFV table missing"; exit 1; }
for d in p12ctl_5yr p12l81_5yr p12echam_5yr p12ctl_19940101 p12l81_19940101 p12echam_19940101; do
  [ -d "$P12/$d" ] || { step "FAIL: Phase 12 run $P12/$d missing"; exit 1; }
done
for d in p13gwd_5yr p13gwd_19940101 p13gwdl95_19940101 p13l81n400_19940101; do [ -d "runs/$d" ] || { step "FAIL: Phase 13 run runs/$d missing"; exit 1; }; done
step "inputs present"

# ---- 2. unit tests
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p13b_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p13b_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- 3. GPU smokes (5 days), one after the other, with a plausibility gate
smoke() {  # <experiment>
  local e=$1; local rundir="$REPO/runs/${e//_/}_smoke5"; mkdir -p "$rundir"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$GPU python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$e" \
      run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true \
      physics.terms.held_suarez.qbo.year="$y0" hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?; local nf; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke $e ran on the CPU"; return 1; }
  grep -q "JuckerColumns: JFV2013 table" "$rundir/log.txt" || { step "FAIL: smoke $e log has no JuckerColumns table line"; return 1; }
  step "smoke $e exit=$rc ($nf files): $(grep -o 'JuckerColumns: JFV2013 table.*' "$rundir/log.txt" | head -1 | cut -c1-200)"
  [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || return 1
  JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
u = ds.u_wind.isel(time=-1).values; T = ds.temperature.isel(time=-1).values; p = np.asarray(ds.level) * 1013.25
a5 = ds["aoa500"].isel(time=-1).values / 365.25
ok = np.isfinite(u).all() and np.isfinite(T).all() and 150 < T.min() and T.max() < 330 and np.abs(u).max() < 150
print(f"[smoke {d.split('/')[-1]}] levels {ds.sizes['level']}, vars {len(ds.data_vars)}; day 5: T {T.min():.0f}..{T.max():.0f} K, |u| max {np.abs(u).max():.0f} m/s, "
      f"aoa500 max below 1 hPa {a5[p >= 1].max():.3f} yr -> {'GATE OK' if ok else 'GATE FAILED'}")
sys.exit(0 if ok else 2)
PY
  local g=$?; [ $g -eq 0 ] || { step "FAIL: smoke $e plausibility gate"; return 1; }
}
smoke p13_jucker || exit 1
smoke p13_jucker_gwd || exit 1

# ---- 4. chains, one GPU, one after the other
chain() {  # <experiment> <prefix>
  step "launching chain $2 (GPU $GPU)"
  EXPERIMENT=$1 PREFIX=$2 SCHEME=calendar YEARS="$YEARS" AGG=${2}_5yr SAVE_INTERVAL=0.25 GPU="$GPU" \
    bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/${2}_chain_stdout.log" 2>&1; local rc=$?
  step "chain $2 exit=$rc"; return $rc
}
chain p13_jucker p13jucker; r1=$?
chain p13_jucker_gwd p13juckergwd; r2=$?
[ $r1 -eq 0 ] && [ $r2 -eq 0 ] || step "WARNING: a chain failed (runs/p13jucker*_chain.log); diagnostics run for what exists"

# ---- 5. diagnostics (CPU), compare pairs in parallel
export JAX_PLATFORMS=cpu
step "throughput rows"
for pre in p13jucker p13juckergwd; do for y in $(seq "$y0" "$y1"); do
  [ -d "runs/${pre}_${y}0101" ] || continue
  python scripts/throughput.py "runs/${pre}_${y}0101" --label "P13b ${pre#p13} $y" --grid T63L81 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done; done
cmp() {  # <tag> <before> <after> <label> <before-label> <after-label>
  local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  [ -d "$b" ] && [ -d "$a" ] || { step "compare $tag skipped ($b / $a missing)"; return; }
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "$REPO/runs/p13b_compare_$tag.log" 2>&1; step "compare $tag exit=$?"
}
step "phase12_compare x4 in parallel"
cmp jucker            "$P12/p12l81_5yr"   runs/p13jucker_5yr    "Jucker et al. relaxation in place of Polvani-Kushner (strat81, no drag, $YEARS)" "PK relaxation" "JFV relaxation" &
cmp jucker_gwd        runs/p13jucker_5yr  runs/p13juckergwd_5yr "Hines + Lott-Miller drag added under the Jucker relaxation (strat81, $YEARS)" "JFV, no drag" "JFV + GWD" &
cmp jucker_gwd_vs_gwd runs/p13gwd_5yr     runs/p13juckergwd_5yr "drag runs: PK relaxation (strat63) -> Jucker relaxation (strat81), $YEARS" "PK + GWD" "JFV + GWD" &
cmp jucker_gwd_vs_echam "$P12/p12echam_5yr" runs/p13juckergwd_5yr "JCM full physics vs dry Jucker + GWD ($YEARS)" "full ECHAM" "JFV + GWD" &
wait
for pre in p13jucker p13juckergwd; do [ -d "runs/${pre}_5yr" ] || continue; for v in aoa150 aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/${pre}_5yr" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P13b ${pre#p13} $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/${pre}_aoa_${v}.log" 2>&1 &
done; done; wait; step "aoa_vs_clams done"
step "mesosphere w* (1994 segments, all Phase 12/13 runs)"
segs=("$P12/p12ctl_19940101:dry control" "$P12/p12l81_19940101:strat81" "runs/p13gwd_19940101:PK + GWD" "runs/p13gwdl95_19940101:PK + GWD, L95" "runs/p13l81n400_19940101:strat81 n400")
for pre in p13jucker p13juckergwd; do [ -d "runs/${pre}_19940101" ] && segs+=("runs/${pre}_19940101:${pre#p13}"); done
python scripts/mesosphere_wstar.py "${segs[@]}" --reference "$P12/p12echam_19940101:full ECHAM" --out "$OUT" --tag p13b > "$REPO/runs/p13b_mesosphere.log" 2>&1; step "mesosphere exit=$?"
step "finished"
