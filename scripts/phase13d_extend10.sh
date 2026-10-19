#!/usr/bin/env bash
# Phase 13d, ten-year extension (Susanne, 2026-09-25 "lets do a 10year extension"): continue the p13jh chain (Jucker + Hines only,
# ERA5 nudging < 150 hPa, strat81) from its 1994 checkpoint to 1999, aggregate p13jh_10yr, then the diagnostics at STRIDE 1 (every
# 6-hourly frame; Phase 15 found the daily-phase sampling of Phases 12-13d tide-biased) into docs/outputs/13d_jucker_hines/10yr/:
#   jh10_vs_5      p13jh_5yr -> p13jh_10yr          clock convergence, 5 vs 10 years
#   jh10_vs_n400   p13jhn400_10yr -> p13jh_10yr     the clean 10-year pair: nudging cutoff 400 -> 150 hPa, same physics
#   jh10_vs_echam  p12echam_5yr -> p13jh_10yr       the standard full-physics comparison
#   hines_s1       p13jucker_5yr -> p13jh_5yr       the Phase 13d pair again at stride 1 (the 30 hPa question)
#   aoa_vs_clams on p13jh_10yr (5-yr run alongside); mesosphere table for the 1999 segments at stride 1.
# GPU 1 (Susanne 2026-09-25), tmux phase13d-extend10, log runs/p13d_ext_run.log. Restartable: finished segments are skipped.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1999}"; GPU="${GPU:-1}"; P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/13d_jucker_hines/10yr"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p13d_ext_run.log"
step() { echo "[p13d-ext] $(date -Is) $*" | tee -a "$LOG"; }
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
for d in runs/p13jh_5yr runs/p13jh_19940101 runs/p13jucker_5yr runs/p13jhn400_10yr "runs/p13jhn400_${y1}0101" "$P12/p12echam_5yr" "$P12/p12echam_19940101"; do
  [ -d "$d" ] || { step "FAIL: $d missing"; exit 1; }; done
grep -q '\[launch\].*exit=0' runs/p13jh_19940101/log.txt || { step "FAIL: segment 1994 not finished cleanly"; exit 1; }
step "inputs present; segments $y0-1994 will be skipped, 1995-$y1 run from runs/p13jh_19940101/checkpoint.ckpt"
step "launching chain p13jh (GPU $GPU)"
EXPERIMENT=p13_jucker_hines PREFIX=p13jh SCHEME=calendar YEARS="$YEARS" AGG=p13jh_10yr SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p13jh_chain10_stdout.log" 2>&1; rc=$?; step "chain p13jh exit=$rc"
[ $rc -eq 0 ] || { step "FAIL: chain (runs/p13jh_chain.log)"; exit 1; }
export JAX_PLATFORMS=cpu
for y in $(seq 1995 "$y1"); do python scripts/throughput.py "runs/p13jh_${y}0101" --label "P13d jh $y" --grid T63L81 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"; done
cmp() { local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" --stride 1 \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" > "$REPO/runs/p13d_ext_compare_$tag.log" 2>&1; step "compare $tag exit=$?"; }
step "phase12_compare x4 in parallel, stride 1"
cmp jh10_vs_5     runs/p13jh_5yr        runs/p13jh_10yr "Jucker + Hines: 5 -> 10 years (strat81, nudged < 150 hPa, 1990-1994 -> 1990-1999; stride 1)" "5 yr (1990-1994)" "10 yr (1990-1999)" &
cmp jh10_vs_n400  runs/p13jhn400_10yr   runs/p13jh_10yr "Jucker + Hines, ten years: ERA5 nudging cutoff 400 -> 150 hPa (strat81, 1990-1999; stride 1)" "nudged < 400 hPa" "nudged < 150 hPa" &
cmp jh10_vs_echam "$P12/p12echam_5yr"   runs/p13jh_10yr "JCM full physics (5 yr) vs dry Jucker + Hines (10 yr; stride 1)" "full ECHAM 1990-1994" "Jucker + Hines 1990-1999" &
cmp hines_s1      runs/p13jucker_5yr    runs/p13jh_5yr  "Hines only added under the Jucker relaxation (strat81, nudged < 150 hPa, 1990-1994) at STRIDE 1" "Jucker, no drag" "Jucker + Hines" &
wait
for v in aoa150 aoa_sfc aoa500; do python scripts/aoa_vs_clams.py runs/p13jh_10yr "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
  --second-run runs/p13jh_5yr --second-label "after 5 yr" \
  --label "P13d Jucker + Hines 1990-1999 [$v]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p13jh10_aoa_${v}.log" 2>&1 & done; wait; step "aoa_vs_clams done"
python scripts/mesosphere_wstar.py "runs/p13jhn400_${y1}0101:Jucker + Hines, nudged < 400 hPa" "runs/p13jh_19940101:Jucker + Hines 1994" \
  "runs/p13jh_${y1}0101:Jucker + Hines $y1" --reference "$P12/p12echam_19940101:full ECHAM 1994" --stride 1 --out "$OUT" --tag p13d10 \
  > "$REPO/runs/p13d_ext_mesosphere.log" 2>&1; step "mesosphere exit=$?"
step "finished"
