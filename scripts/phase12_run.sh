#!/usr/bin/env bash
# Phase 12: circulation tests (Susanne, 2026-09-16: "the circulation in the Phase 11 runs looks too weak"), unattended
# (tmux strat_p12_run, log runs/p12_run.log). Three 5-year chains 1990-1994, 6-hourly output like Phase 11:
#   noqbo  p12_noqbo  GPU_A  QBO nudging OFF (qbo: null), strat63
#   l81    p12_l81    GPU_B  QBO on, strat81 = strat63 + all 26 L95 tropospheric layers (own ERA5 windows)
#   ctl    p12_ctl    GPU_A  after noqbo: Phase 11 run A + the aoa500 clock = the "before" of both comparisons
# GPU 0 is left to the p11a 1990-2009 extension (memory: GPU rule 0, then 1, then 2).
# Steps: wait until JAX sees a GPU (the host loses /dev/nvidia* on reboot: scripts/restore_nvidia_dev.sh) ->
# inputs (QBO targets, strat63 windows, the strat81 windows from tmux preproc_p12_l81_prefetch) -> pytest ->
# 5-day GPU smokes of noqbo and l81 -> chains -> diagnostics (scripts/phase12_compare.py: w* and age of air
# before/after; aoa_vs_clams for aoa_sfc and aoa500; throughput rows) into docs/outputs/12_circulation/.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU_A="${GPU_A:-1}"; GPU_B="${GPU_B:-2}"
P11A="${P11A:-/data/JCM_stripped/jcm-strat-phase11/runs/p11a_5yr}"
OUT="$REPO/docs/outputs/12_circulation"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p12_run.log"
step() { echo "[p12] $(date -Is) $*" | tee -a "$LOG"; }
gpu_visible() { CUDA_VISIBLE_DEVICES="$1" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPUs $GPU_A/$GPU_B, before-run $P11A"

# ---- 0. a GPU the process can actually open (nvidia-smi lists the cards even when /dev/nvidia* is missing)
n=0
until gpu_visible "$GPU_A"; do
  [ $((n % 6)) -eq 0 ] && step "waiting for a visible GPU (CUDA_ERROR_NO_DEVICE? run: sudo bash scripts/restore_nvidia_dev.sh)"
  n=$((n + 1)); sleep 300
done
step "GPU $GPU_A visible to JAX"
for g in "$GPU_A" "$GPU_B"; do gpu_busy "$g" && { step "FAIL: GPU $g busy"; exit 1; }; done

# ---- 1. inputs
y0="${YEARS%-*}"; y1="${YEARS#*-}"
win() {  # <table-tag> <year> -> window file name for one calendar-year segment
  local tag=$1 y=$2 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_${tag}_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"
}
for y in $(seq "$y0" "$y1"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  [ -s "$(win l63_35c39d41 "$y")" ] || { step "FAIL: no strat63 ERA5 window for $y"; exit 1; }
done
n=0
while :; do
  missing=0; for y in $(seq "$y0" "$y1"); do [ -s "$(win l81_3af87627 "$y")" ] || missing=1; done
  [ -s "$REPO/cache/era5/wb2_192x96_l81_3af87627_${y0}-01-01_${y0}-01-01_6h_u-v-T-q-z.nc" ] || missing=1
  [ $missing -eq 0 ] && break
  if ! tmux has-session -t preproc_p12_l81_prefetch 2>/dev/null; then
    step "strat81 windows missing and the prefetch session is gone - running the prefetch here"
    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme calendar --years "$YEARS" --save-interval 0.25 -- +experiment=p12_l81 >> "$REPO/runs/p12_prefetch_l81.log" 2>&1 \
      || { step "FAIL: strat81 prefetch"; exit 1; }
    continue
  fi
  [ $((n % 10)) -eq 0 ] && step "waiting for the strat81 ERA5 windows (tmux preproc_p12_l81_prefetch, runs/p12_prefetch_l81.log)"
  n=$((n + 1)); sleep 120
done
step "inputs present"
# the 5-day smoke window of strat81 (strat63's exists from Phase 11)
JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --days 5 --years "$y0" --no-init -- +experiment=p12_l81 >> "$REPO/runs/p12_prefetch_l81.log" 2>&1 || { step "FAIL: strat81 smoke window"; exit 1; }

# ---- 2. unit tests
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p12_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p12_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- 3. GPU smokes (5 days), in parallel
smoke() {  # <experiment> <gpu> <per-seg overrides...>
  local e=$1 g=$2; shift 2; local rundir="$REPO/runs/${e/_/}_smoke5"; mkdir -p "$rundir"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$g python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" "+experiment=$e" \
      run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true "$@" hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  local rc=$?; local nf; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke $e ran on the CPU"; return 1; }
  step "smoke $e exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ]
}
smoke p12_noqbo "$GPU_A" & sa=$!
sleep 60
smoke p12_l81 "$GPU_B" physics.terms.held_suarez.qbo.year="$y0" & sb=$!
wait $sa; ra=$?; wait $sb; rb=$?
[ $ra -eq 0 ] && [ $rb -eq 0 ] || { step "FAIL: a smoke failed"; exit 1; }
grep -q "QBO nudging OFF" "$REPO/runs/p12noqbo_smoke5/log.txt" || { step "FAIL: noqbo smoke log has no 'QBO nudging OFF' line"; exit 1; }
JAX_PLATFORMS=cpu python - "$REPO/runs/p12noqbo_smoke5" "$REPO/runs/p12l81_smoke5" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
for d in sys.argv[1:]:
    ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
    p = np.asarray(ds.level) * 1013.25
    a5 = ds["aoa500"].isel(time=-1).values / 365.25; a7 = ds["aoa"].isel(time=-1).values / 365.25
    print(f"[smoke {d.split('/')[-1]}] levels {ds.sizes['level']}, vars {len(ds.data_vars)} (pulses written: {any(k.startswith('pulse') for k in ds.data_vars)}); "
          f"day 5: aoa500 max below 1 hPa {a5[p >= 1].max():.4f} yr, aoa (700) max {a7[p >= 1].max():.4f} yr; "
          f"aoa500 zero where p>500 hPa: {np.allclose(a5[p > 500], 0)}; u range {float(ds.u_wind.min()):.0f}..{float(ds.u_wind.max()):.0f} m/s")
PY

# ---- 4. chains
step "launching chains noqbo (GPU $GPU_A) and l81 (GPU $GPU_B)"
EXTRA_PER_SEG="" EXPERIMENT=p12_noqbo PREFIX=p12noqbo SCHEME=calendar YEARS="$YEARS" AGG=p12noqbo_5yr SAVE_INTERVAL=0.25 GPU="$GPU_A" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p12noqbo_chain_stdout.log" 2>&1 & pa=$!
sleep 90
EXPERIMENT=p12_l81 PREFIX=p12l81 SCHEME=calendar YEARS="$YEARS" AGG=p12l81_5yr SAVE_INTERVAL=0.25 GPU="$GPU_B" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p12l81_chain_stdout.log" 2>&1 & pb=$!
wait $pa; ra=$?; step "chain noqbo exit=$ra"
[ $ra -eq 0 ] || { step "FAIL: chain noqbo (runs/p12noqbo_chain.log); l81 continues"; }
step "launching chain ctl (GPU $GPU_A)"
EXPERIMENT=p12_ctl PREFIX=p12ctl SCHEME=calendar YEARS="$YEARS" AGG=p12ctl_5yr SAVE_INTERVAL=0.25 GPU="$GPU_A" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p12ctl_chain_stdout.log" 2>&1 & pc=$!
wait $pb; rb=$?; step "chain l81 exit=$rb"
wait $pc; rc=$?; step "chain ctl exit=$rc"
[ $ra -eq 0 ] && [ $rb -eq 0 ] && [ $rc -eq 0 ] || { step "FAIL: a chain failed; see runs/p12*_chain.log"; exit 1; }

# ---- 5. diagnostics (CPU)
export JAX_PLATFORMS=cpu
step "throughput rows"
for pre in p12noqbo p12l81 p12ctl; do for y in $(seq "$y0" "$y1"); do
  python scripts/throughput.py "runs/${pre}_${y}0101" --label "P12 ${pre#p12} $y" --grid "$([ $pre = p12l81 ] && echo T63L81 || echo T63L63)" --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done; done
step "phase12_compare: noqbo vs ctl"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12noqbo_5yr --tag noqbo --label "QBO nudging off (strat63, $YEARS)" \
  --before-label "ctl: QBO on" --after-label "QBO off" --out "$OUT" > "$REPO/runs/p12_compare_noqbo.log" 2>&1; step "compare noqbo exit=$?"
step "phase12_compare: l81 vs ctl"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12l81_5yr --tag l81 --label "full L95 troposphere: strat63 -> strat81 (QBO on, $YEARS)" \
  --before-label "ctl: strat63" --after-label "strat81" --out "$OUT" > "$REPO/runs/p12_compare_l81.log" 2>&1; step "compare l81 exit=$?"
step "phase12_compare: ctl vs p11a (reproduction check: identical dynamics expected)"
python scripts/phase12_compare.py --before "$P11A" --after runs/p12ctl_5yr --tag ctl_vs_p11a --label "Phase 12 control vs Phase 11 A (same dynamics)" \
  --before-label "p11a_5yr" --after-label "p12ctl_5yr" --clocks aoa_sfc aoa --no-waccm --out "$OUT" > "$REPO/runs/p12_compare_ctl.log" 2>&1; step "compare ctl exit=$?"
for pre in p12ctl p12noqbo p12l81; do for v in aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py "runs/${pre}_5yr" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P12 ${pre#p12} $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/${pre}_aoa_${v}.log" 2>&1; step "aoa_vs_clams $pre $v exit=$?"
done; done
step "finished"
