#!/usr/bin/env bash
# Phase 14 (tmux strat_p14_run, log runs/p14_run.log): JCM's FULL ECHAM physics FREE-RUNNING - no ERA5 nudging, no QBO
# nudging - with the Phase 12 clocks (experiment p14_free = p12_echam minus the two relaxations), 1990-1999 as one
# ten-segment chain on GPU 0, then the Phase 12 diagnostics against the nudged full-physics run p12echam_5yr (and the
# dry control p12ctl_5yr). Susanne, 2026-09-22: "a new phase that runs JCM full physics with no nudging ... 10 years
# ... the same plots as in phase 12".
# Steps: inputs (the ERA5 initial state of 1990-01-01 is the only reanalysis input) -> pytest -> 5-day GPU smoke, whose
# log must show nudging disabled and no qbo_nudging term -> chain (~2.3-3 h per year at Phase 12 run-4 rates, less
# without the nudging target) -> a second aggregate of the first five years (p14free_5yr, same spin-up as the 5-yr
# references; chain_segments.sh skips finished segments and only links) -> phase12_compare tags free10 / free5 /
# free10_vs_ctl, aoa_vs_clams for the three clocks, throughput rows.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1999}"; GPU="${GPU:-0}"; PREFIX=p14free; AGG="${PREFIX}_10yr"; AGG5="${PREFIX}_5yr"
OUT="$REPO/docs/outputs/14_free_physics"; mkdir -p "$OUT" "$REPO/runs"; LOG="$REPO/runs/p14_run.log"
step() { echo "[p14] $(date -Is) $*" | tee -a "$LOG"; }
gpu_busy() { nvidia-smi -i "$1" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; }
y0="${YEARS%-*}"; y1="${YEARS#*-}"
step "start, commit $(git rev-parse --short HEAD), years $YEARS, GPU $GPU"
CUDA_VISIBLE_DEVICES="$GPU" python -c "import jax; assert any(d.platform == 'gpu' for d in jax.devices())" >/dev/null 2>&1 || { step "FAIL: no GPU visible (scripts/restore_nvidia_dev.sh)"; exit 1; }
gpu_busy "$GPU" && { step "FAIL: GPU $GPU busy"; exit 1; }

# ---- inputs: the initial state (grid hash of T63L95) and, for chain_segments.sh's up-front check, the QBO reference years
init="$REPO/cache/era5/wb2_192x96_l95_c39313fe_${y0}-01-01_${y0}-01-01_6h_u-v-T-q-z.nc"
if [ ! -s "$init" ]; then
  step "initial state missing - prefetching it"
  JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --days 5 --years "$y0" -- +experiment=p12_echam >> "$REPO/runs/p14_prefetch_init.log" 2>&1 || { step "FAIL: prefetch of the initial state"; exit 1; }
fi
[ -s "$init" ] || { step "FAIL: no initial state $init"; exit 1; }
for y in $(seq "$y0" "$y1"); do [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: chain_segments.sh wants cache/era5_ref/era5_zm_monthly_$y.nc"; exit 1; }; done
for r in p12echam_5yr p12ctl_5yr; do [ -d "$REPO/runs/$r" ] || step "WARNING: runs/$r missing - the comparison against it will fail"; done
step "inputs present"

# ---- unit tests (config composition included: tests/test_phase14.py)
JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p14_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p14_tests.log"))"; [ $rc -eq 0 ] || exit 1

# ---- GPU smoke, 5 days
rundir="$REPO/runs/${PREFIX}_smoke5"; mkdir -p "$rundir"
( cd "$rundir" && CUDA_VISIBLE_DEVICES=$GPU python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p14_free \
    run.start_date="$y0-01-01" run.total_time=5 run.chunk_days=5 physics.terms.production_tracers.first_segment=true hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
rc=$?; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
grep -q "1xcpu" "$rundir/log.txt" && { step "FAIL: smoke ran on the CPU"; exit 1; }
step "smoke ${PREFIX}_smoke5 exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || { step "FAIL: smoke (runs/${PREFIX}_smoke5/log.txt)"; exit 1; }
# the resolved config is echoed at the top of the log: nudging must be disabled and no qbo_nudging term present
sed -n '/^nudging:/,/^[a-z]/p' "$rundir/log.txt" | grep -q "enabled: false" || { step "FAIL: smoke log does not show nudging.enabled: false"; exit 1; }
grep -q "qbo_nudging\|NudgingTerm\|QBO nudging" "$rundir/log.txt" && { step "FAIL: smoke log mentions a nudging term"; exit 1; }
step "smoke config: nudging disabled, no QBO term"
JAX_PLATFORMS=cpu python - "$rundir" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
d = sys.argv[1]; ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
p = np.asarray(ds.level) * 1013.25
a5 = ds["aoa500"].isel(time=-1).values / 365.25; a7 = ds["aoa"].isel(time=-1).values / 365.25
print(f"[smoke p14free_smoke5] levels {ds.sizes['level']}, vars {sorted(ds.data_vars)}; day 5: aoa500 max below 1 hPa {a5[p >= 1].max():.4f} yr, "
      f"aoa {a7[p >= 1].max():.4f}; T range {float(ds.temperature.min()):.0f}..{float(ds.temperature.max()):.0f} K, u range {float(ds.u_wind.min()):.0f}..{float(ds.u_wind.max()):.0f} m/s")
PY
grep -h "days/hr" "$rundir/log.txt" | tail -1 >> "$LOG" || true

# ---- chain, ten calendar years; no per-segment override (no QBO term), WACCM tracer initial state on segment 1
step "launching chain $PREFIX $YEARS (GPU $GPU)"
EXTRA_PER_SEG="" FIRST_SEG_EXTRA="physics.terms.production_tracers.first_segment=true" EXPERIMENT=p14_free PREFIX=$PREFIX SCHEME=calendar \
  YEARS="$YEARS" AGG=$AGG SAVE_INTERVAL=0.25 GPU="$GPU" bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/${PREFIX}_chain_stdout.log" 2>&1; rc=$?
step "chain exit=$rc"; [ $rc -eq 0 ] || { step "FAIL: chain (runs/${PREFIX}_chain.log)"; exit 1; }
# the first five years as their own aggregate (finished segments are skipped, only the links are made)
EXTRA_PER_SEG="" FIRST_SEG_EXTRA="" COMPACT=0 EXPERIMENT=p14_free PREFIX=$PREFIX SCHEME=calendar YEARS="$y0-$((y0 + 4))" AGG=$AGG5 SAVE_INTERVAL=0.25 GPU="$GPU" \
  bash "$REPO/scripts/chain_segments.sh" >> "$REPO/runs/${PREFIX}_chain_stdout.log" 2>&1; step "5-yr aggregate $AGG5 exit=$?"

# ---- diagnostics (CPU): the Phase 12 set, before = nudged full physics, after = free-running
export JAX_PLATFORMS=cpu
for y in $(seq "$y0" "$y1"); do
  python scripts/throughput.py "runs/${PREFIX}_${y}0101" --label "P14 free $y" --grid T63L95 --csv docs/outputs/throughput.csv 2>/dev/null | grep "throughput\|end-to-end" >> "$LOG"
done
CLOCKS="aoa_sfc aoa500 aoa150"
step "phase12_compare: free 10 yr vs nudged full physics"
python scripts/phase12_compare.py --before runs/p12echam_5yr --after "runs/$AGG" --tag free10 --clocks $CLOCKS \
  --label "free-running full physics 1990-1999 vs the nudged full physics 1990-1994 (both T63L95)" \
  --before-label "nudged (p12echam, 5 yr)" --after-label "free (p14free, 10 yr)" --out "$OUT" > "$REPO/runs/p14_compare_free10.log" 2>&1; step "compare free10 exit=$?"
step "phase12_compare: free first 5 yr vs nudged full physics (same spin-up)"
python scripts/phase12_compare.py --before runs/p12echam_5yr --after "runs/$AGG5" --tag free5 --clocks $CLOCKS \
  --label "free-running full physics, first 5 yr (1990-1994) vs the nudged full physics 1990-1994 (both T63L95)" \
  --before-label "nudged (p12echam, 5 yr)" --after-label "free (p14free, first 5 yr)" --out "$OUT" > "$REPO/runs/p14_compare_free5.log" 2>&1; step "compare free5 exit=$?"
step "phase12_compare: free 10 yr vs the dry control"
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after "runs/$AGG" --tag free10_vs_ctl --clocks $CLOCKS \
  --label "free-running full physics 1990-1999 (T63L95) vs the dry Polvani-Kushner control 1990-1994 (strat63)" \
  --before-label "ctl: dry PK, nudged" --after-label "free (p14free, 10 yr)" --out "$OUT" > "$REPO/runs/p14_compare_free10_vs_ctl.log" 2>&1; step "compare free10_vs_ctl exit=$?"
for v in $CLOCKS; do
  python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var "$v" \
    --label "P14 free $YEARS [$v]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p14_aoa_${v}.log" 2>&1; step "aoa_vs_clams $v exit=$?"
done
python scripts/aoa_vs_clams.py "runs/$AGG" "$OUT" --years 2005-2009 --last-saves 240 --var aoa_sfc --mark-levels 500,55,30 --pmax 1000 \
  --label "P14 free $YEARS [aoa_sfc]: age after 10 yr (last 60 d) vs CLaMS/WACCM 2005-2009" > "$REPO/runs/p14_aoa_aoa_sfc_levels.log" 2>&1; step "aoa_vs_clams aoa_sfc levels exit=$?"
step "finished"
