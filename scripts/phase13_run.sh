#!/usr/bin/env bash
# Phase 13: gravity-wave drag for the dry model, the L95 mesosphere, and a lower nudging cutoff (Susanne, 2026-09-23),
# unattended (tmux strat_p13_run, log runs/p13_run.log). Three 5-year chains 1990-1994, 6-hourly output like Phase 12:
#   gwd       p13_gwd       GPU_A  Phase 12 control + Hines (launch 634 hPa) + Lott-Miller drag, strat63
#   gwd_l77   p13_gwd_l77   GPU_B  the same on strat77 = strat63 + all 22 L95 mesospheric layers (own ERA5 windows, L95 sponge)
#   l81_n400  p13_l81_n400  GPU_C  Phase 12 strat81 run (no drag) with the ERA5 nudging cut off at 400 hPa instead of 150
# GPU 0 belongs to Phase 14 (p14_free). Steps: GPUs visible and idle -> inputs (QBO targets; strat63/strat81 windows from
# Phases 11/12; strat77 smoke window now, the 5 calendar-year strat77 windows in tmux preproc_p13_l77_prefetch) -> pytest
# -> 5-day GPU smokes of all three -> chains gwd + l81_n400 at once, gwd_l77 when its windows exist -> diagnostics
# (scripts/phase12_compare.py before/after pairs, scripts/aoa_vs_clams.py per clock, scripts/mesosphere_wstar.py on the
# 1994 segments) into docs/outputs/13_gwd/.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU_A="${GPU_A:-1}"; GPU_B="${GPU_B:-2}"; GPU_C="${GPU_C:-3}"
P12="${P12:-/data/JCM_stripped/jcm-strat-phase12/runs}"
OUT="$REPO/docs/outputs/13_gwd"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p13_run.log"
step() { echo "[p13] $(date -Is) $*" | tee -a "$LOG"; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPUs $GPU_A/$GPU_B/$GPU_C, Phase 12 runs $P12"

# ---- 0. GPUs
n=0
until gpu_visible "$GPU_A"; do
  [ $((n % 6)) -eq 0 ] && step "waiting for a visible GPU (CUDA_ERROR_NO_DEVICE? run: sudo bash scripts/restore_nvidia_dev.sh)"
  n=$((n + 1)); sleep 300
done
for g in "$GPU_A" "$GPU_B" "$GPU_C"; do gpu_busy "$g" && { step "FAIL: GPU $g busy"; exit 1; }; done
step "GPUs $GPU_A/$GPU_B/$GPU_C visible and idle"

# ---- 1. inputs
y0="${YEARS%-*}"; y1="${YEARS#*-}"
win() {  # <table-tag> <year> -> window file name for one calendar-year segment
  local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"
}
L77=l77_9fc7126b
for y in $(seq "$y0" "$y1"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  [ -s "$(win l63_35c39d41 "$y")" ] || { step "FAIL: no strat63 ERA5 window for $y"; exit 1; }
  [ -s "$(win l81_3af87627 "$y")" ] || { step "FAIL: no strat81 ERA5 window for $y"; exit 1; }
done
for d in p12ctl_5yr p12l81_5yr p12echam_5yr p12ctl_19940101 p12l81_19940101 p12echam_19940101; do
  [ -d "$P12/$d" ] || { step "FAIL: Phase 12 run $P12/$d missing"; exit 1; }
done
# strat77: the 5-day smoke window (+ initial state) now, the five calendar years in their own tmux session
JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --days 5 --years "$y0" -- +experiment=p13_gwd_l77 > "$REPO/runs/p13_prefetch_l77_smoke.log" 2>&1 \
  || { step "FAIL: strat77 smoke window (runs/p13_prefetch_l77_smoke.log)"; exit 1; }
l77_missing() { local y; for y in $(seq "$y0" "$y1"); do [ -s "$(win $L77 "$y")" ] || return 0; done; return 1; }   # true (0) while any window is missing
if ! l77_missing; then step "strat77 5-year windows already present"
elif ! tmux has-session -t preproc_p13_l77_prefetch 2>/dev/null; then
  tmux new-session -d -s preproc_p13_l77_prefetch "cd '$REPO' && source scripts/env.sh && JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme calendar --years '$YEARS' --save-interval 0.25 -- +experiment=p13_gwd_l77 >> '$REPO/runs/p13_prefetch_l77.log' 2>&1"
  step "strat77 5-year windows: prefetch launched (tmux preproc_p13_l77_prefetch, runs/p13_prefetch_l77.log, ~6 min/yr)"
fi
step "inputs present (strat77 chain windows pending if the prefetch is running)"

# ---- 2. unit tests (rerun after ANY config change - Phase 12 lesson)
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p13_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p13_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- 3. GPU smokes (5 days), in parallel
smoke() {  # <experiment> <gpu> <per-seg overrides...>
  local e=$1 g=$2; shift 2; local rundir="$REPO/runs/${e//_/}_smoke5"; mkdir -p "$rundir"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$g python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$e" \
      run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true \
      physics.terms.held_suarez.qbo.year="$y0" "$@" hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?; local nf; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke $e ran on the CPU"; return 1; }
  step "smoke $e exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ]
}
smoke p13_gwd "$GPU_A" & sa=$!
sleep 45; smoke p13_l81_n400 "$GPU_C" & sc=$!
sleep 45; smoke p13_gwd_l77 "$GPU_B" & sb=$!
wait $sa; ra=$?; wait $sc; rc3=$?; wait $sb; rb=$?
[ $ra -eq 0 ] && [ $rb -eq 0 ] && [ $rc3 -eq 0 ] || { step "FAIL: a smoke failed (runs/p13*_smoke5/log.txt)"; exit 1; }
grep -q "HinesGwdLaunch: L63, launch 634 hPa -> launch_level 3" "$REPO/runs/p13gwd_smoke5/log.txt" || { step "FAIL: gwd smoke log has no 'launch_level 3' line"; exit 1; }
grep -q "HinesGwdLaunch: L77, launch 634 hPa -> launch_level 3" "$REPO/runs/p13gwdl77_smoke5/log.txt" || { step "FAIL: gwd_l77 smoke log has no L77 launch line"; exit 1; }
JAX_PLATFORMS=cpu python - "$REPO/runs/p13gwd_smoke5" "$REPO/runs/p13gwdl77_smoke5" "$REPO/runs/p13l81n400_smoke5" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
for d in sys.argv[1:]:
    ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
    p = np.asarray(ds.level) * 1013.25
    a5 = ds["aoa500"].isel(time=-1).values / 365.25
    u = ds.u_wind.isel(time=-1).values; T = ds.temperature.isel(time=-1).values
    print(f"[smoke {d.split('/')[-1]}] levels {ds.sizes['level']}, vars {len(ds.data_vars)}; day 5: aoa500 max below 1 hPa {a5[p >= 1].max():.4f} yr; "
          f"u range {u.min():.0f}..{u.max():.0f} m/s, T range {T.min():.0f}..{T.max():.0f} K, finite: {np.isfinite(u).all() and np.isfinite(T).all()}")
PY

# ---- 4. chains
step "launching chains gwd (GPU $GPU_A) and l81_n400 (GPU $GPU_C)"
EXPERIMENT=p13_gwd PREFIX=p13gwd SCHEME=calendar YEARS="$YEARS" AGG=p13gwd_5yr SAVE_INTERVAL=0.25 GPU="$GPU_A" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p13gwd_chain_stdout.log" 2>&1 & pa=$!
sleep 90
EXPERIMENT=p13_l81_n400 PREFIX=p13l81n400 SCHEME=calendar YEARS="$YEARS" AGG=p13l81n400_5yr SAVE_INTERVAL=0.25 GPU="$GPU_C" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p13l81n400_chain_stdout.log" 2>&1 & pc=$!
n=0
while l77_missing; do
  if ! tmux has-session -t preproc_p13_l77_prefetch 2>/dev/null; then
    step "strat77 windows missing and the prefetch session is gone - running the prefetch here"
    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme calendar --years "$YEARS" --save-interval 0.25 -- +experiment=p13_gwd_l77 >> "$REPO/runs/p13_prefetch_l77.log" 2>&1 \
      || { step "FAIL: strat77 prefetch"; break; }
    continue
  fi
  [ $((n % 10)) -eq 0 ] && step "waiting for the strat77 ERA5 windows (tmux preproc_p13_l77_prefetch)"
  n=$((n + 1)); sleep 120
done
if l77_missing; then step "FAIL: no strat77 windows - gwd_l77 chain not started"; rb=1; pb=""
else
  step "launching chain gwd_l77 (GPU $GPU_B)"
  EXPERIMENT=p13_gwd_l77 PREFIX=p13gwdl77 SCHEME=calendar YEARS="$YEARS" AGG=p13gwdl77_5yr SAVE_INTERVAL=0.25 GPU="$GPU_B" \
    bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p13gwdl77_chain_stdout.log" 2>&1 & pb=$!
fi
wait $pa; ra=$?; step "chain gwd exit=$ra"
wait $pc; rc3=$?; step "chain l81_n400 exit=$rc3"
[ -n "${pb:-}" ] && { wait $pb; rb=$?; step "chain gwd_l77 exit=$rb"; }
[ $ra -eq 0 ] && [ $rb -eq 0 ] && [ $rc3 -eq 0 ] || step "WARNING: a chain failed (runs/p13*_chain.log); diagnostics run for what exists"

# ---- 5. diagnostics (CPU)
export JAX_PLATFORMS=cpu
step "throughput rows"
for pre in p13gwd p13gwdl77 p13l81n400; do for y in $(seq "$y0" "$y1"); do
  [ -d "runs/${pre}_${y}0101" ] || continue
  grid=T63L63; [ $pre = p13gwdl77 ] && grid=T63L77; [ $pre = p13l81n400 ] && grid=T63L81
  python scripts/throughput.py "runs/${pre}_${y}0101" --label "P13 ${pre#p13} $y" --grid "$grid" --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done; done
cmp() {  # <tag> <before> <after> <label> <before-label> <after-label> [extra...]
  local tag=$1 b=$2 a=$3 l=$4 bl=$5 al=$6; shift 6
  [ -d "$b" ] && [ -d "$a" ] || { step "compare $tag skipped ($b / $a missing)"; return; }
  step "phase12_compare: $tag"
  python scripts/phase12_compare.py --before "$b" --after "$a" --tag "$tag" --label "$l" --before-label "$bl" --after-label "$al" \
    --clocks aoa_sfc aoa500 aoa150 --out "$OUT" "$@" > "$REPO/runs/p13_compare_$tag.log" 2>&1; step "compare $tag exit=$?"
}
cmp gwd        "$P12/p12ctl_5yr"    runs/p13gwd_5yr      "Hines + Lott-Miller drag added to the dry model (strat63, $YEARS)" "ctl: no drag" "+ GWD"
cmp gwd_l77    runs/p13gwd_5yr      runs/p13gwdl77_5yr   "drag on: strat63 -> strat77 (all L95 mesospheric layers, $YEARS)" "GWD strat63" "GWD strat77"
cmp gwd_l77_vs_ctl "$P12/p12ctl_5yr" runs/p13gwdl77_5yr  "drag + L95 mesosphere vs the dry control ($YEARS)" "ctl" "+ GWD, strat77"
cmp l81_n400   "$P12/p12l81_5yr"    runs/p13l81n400_5yr  "strat81: ERA5 nudging cutoff 150 -> 400 hPa ($YEARS)" "nudged < 150 hPa" "nudged < 400 hPa"
cmp gwd_vs_echam "$P12/p12echam_5yr" runs/p13gwd_5yr     "dry + GWD against JCM full physics ($YEARS)" "full ECHAM" "dry + GWD"
for pre in p13gwd p13gwdl77 p13l81n400; do [ -d "runs/${pre}_5yr" ] || continue; for v in aoa150 aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/${pre}_5yr" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P13 ${pre#p13} $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/${pre}_aoa_${v}.log" 2>&1; step "aoa_vs_clams $pre $v exit=$?"
done; done
step "mesosphere w* (1994 segments)"
segs=("$P12/p12ctl_19940101:dry control" "$P12/p12l81_19940101:strat81")
for pre in p13gwd p13gwdl77 p13l81n400; do [ -d "runs/${pre}_19940101" ] && segs+=("runs/${pre}_19940101:${pre#p13}"); done
python scripts/mesosphere_wstar.py "${segs[@]}" --reference "$P12/p12echam_19940101:full ECHAM" --out "$OUT" --tag p13 > "$REPO/runs/p13_mesosphere.log" 2>&1; step "mesosphere exit=$?"
step "finished"
