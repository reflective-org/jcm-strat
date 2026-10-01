#!/usr/bin/env bash
# Phase 12, run 4 (tmux strat_p12_echam, log runs/p12_echam.log): JCM's FULL ECHAM physics with the clocks
# (experiment p12_echam: T63L95, ERA5-nudged troposphere, QBO nudging, Phase 12 tracers, 6-hourly output of the
# dynamics + clocks only), 1990-1994 as one chain on GPU 0, then the before/after diagnostics against the Phase 12
# control (p12ctl_5yr). Susanne, 2026-09-18: "Do the full physics 5 year run with the clocks".
# Steps: wait for the T63L95 ERA5 windows (tmux preproc_p12_l95_prefetch) -> pytest -> 5-day GPU smoke -> chain
# (~2.6 h per year: the full package stepped 140 d/hr in Phase 6; 12-hourly nudging target like that reference, the
# 6-hourly one OOMed at chunk 2 on the H200) -> phase12_compare (tag echam), aoa_vs_clams,
# throughput rows.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; GPU="${GPU:-0}"
OUT="$REPO/docs/outputs/12_circulation"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p12_echam.log"
step() { echo "[p12-echam] $(date -Is) $*" | tee -a "$LOG"; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
y0="${YEARS%-*}"; y1="${YEARS#*-}"
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPU $GPU"
CUDA_VISIBLE_DEVICES="$GPU" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1 || { step "FAIL: no GPU visible (scripts/restore_nvidia_dev.sh)"; exit 1; }
gpu_busy "$GPU" && { step "FAIL: GPU $GPU busy"; exit 1; }

# ---- inputs
win() { local y=$1 n; n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  echo "$REPO/cache/era5/wb2_192x96_l95_c39313fe_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_12h_u-v-T.nc"; }
n=0
while :; do
  missing=0; for y in $(seq "$y0" "$y1"); do [ -s "$(win "$y")" ] || missing=1; done
  [ -s "$REPO/cache/era5/wb2_192x96_l95_c39313fe_${y0}-01-01_${y0}-01-01_6h_u-v-T-q-z.nc" ] || missing=1    # the initial state is a 6h slice
  [ -s "$REPO/cache/era5/wb2_192x96_l95_c39313fe_$((y0-1))-12-31_${y0}-01-08_12h_u-v-T.nc" ] || missing=1
  [ $missing -eq 0 ] && break
  if ! tmux has-session -t preproc_p12_l95_prefetch 2>/dev/null; then
    step "windows missing and the prefetch session is gone - running the prefetch here"
    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --days 5 --years "$y0" --no-init -- +experiment=p12_echam >> "$REPO/runs/p12_prefetch_l95.log" 2>&1
    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme calendar --years "$YEARS" --save-interval 0.25 -- +experiment=p12_echam >> "$REPO/runs/p12_prefetch_l95.log" 2>&1 \
      || { step "FAIL: prefetch"; exit 1; }
    continue
  fi
  [ $((n % 10)) -eq 0 ] && step "waiting for the T63L95 ERA5 windows (tmux preproc_p12_l95_prefetch)"
  n=$((n + 1)); sleep 120
done
for y in $(seq "$y0" "$y1"); do [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }; done
step "inputs present"

# ---- unit tests
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p12_echam_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p12_echam_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- GPU smoke, 5 days
rundir="$REPO/runs/p12echam_smoke5"; mkdir -p "$rundir"
( cd "$rundir" && CUDA_VISIBLE_DEVICES=$GPU python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p12_echam \
    run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.qbo_nudging.year="$y0" \
    physics.terms.production_tracers.first_segment=true hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
rc=$?; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke ran on the CPU"; exit 1; }
step "smoke p12echam_smoke5 exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || { step "FAIL: smoke (runs/p12echam_smoke5/log.txt)"; exit 1; }
JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
p = np.asarray(ds.level) * 1013.25
a5 = ds["aoa500"].isel(time=-1).values / 365.25; a7 = ds["aoa"].isel(time=-1).values / 365.25
print(f"[smoke p12echam_smoke5] levels {ds.sizes['level']}, vars {sorted(ds.data_vars)}; day 5: aoa500 max below 1 hPa {a5[p >= 1].max():.4f} yr, "
      f"aoa {a7[p >= 1].max():.4f}; 500-700 hPa band mean aoa {a7[(p > 500) & (p <= 700)].mean() * 365.25:.2f} d vs aoa500 {a5[(p > 500) & (p <= 700)].mean() * 365.25:.2f} d; "
      f"T range {float(ds.temperature.min()):.0f}..{float(ds.temperature.max()):.0f} K, u range {float(ds.u_wind.min()):.0f}..{float(ds.u_wind.max()):.0f} m/s")
PY
grep -h "days/hr\|steady" "$rundir/log.txt" | tail -2 >> "$LOG" || true

# ---- chain
step "launching chain p12echam (GPU $GPU)"
EXTRA_PER_SEG="physics.terms.qbo_nudging.year={year}" EXPERIMENT=p12_echam PREFIX=p12echam SCHEME=calendar YEARS="$YEARS" AGG=p12echam_5yr SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p12echam_chain_stdout.log" 2>&1; rc=$?
step "chain exit=$rc"; [ $rc -eq 0 ] || { step "FAIL: chain (runs/p12echam_chain.log)"; exit 1; }

# ---- diagnostics (CPU)
export JAX_PLATFORMS=cpu
for y in $(seq "$y0" "$y1"); do
  python scripts/throughput.py "runs/p12echam_${y}0101" --label "P12 echam $y" --grid T63L95 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done
step "phase12_compare: echam vs ctl"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12echam_5yr --tag echam --label "full ECHAM physics (T63L95) vs the dry Polvani-Kushner control (strat63), QBO on, $YEARS" \
  --before-label "ctl: dry PK, strat63" --after-label "full ECHAM, L95" --out "$OUT" > "$REPO/runs/p12_compare_echam.log" 2>&1; step "compare echam exit=$?"
for v in aoa_sfc aoa500; do
  python scripts/aoa_vs_clams.py runs/p12echam_5yr "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P12 echam $YEARS [$v]: age after 5 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p12echam_aoa_${v}.log" 2>&1; step "aoa_vs_clams $v exit=$?"
done
step "finished"
