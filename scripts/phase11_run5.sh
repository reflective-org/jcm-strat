#!/usr/bin/env bash
# Phase 11: two 5-year review chains (1990-1994) of the revised production tracers, unattended
# (tmux strat_p11_run5, log runs/p11_run5.log):
#   A  p11a_prod  GPU 0  no sink anywhere for the pulses, sources and sai
#   B  p11b_prod  GPU 1  the same, plus relaxation to zero above the 1 hPa tracer lid
# Both: unit amplitudes, Gaussian + sharp-edged twins, no surface absorption, clocks and n2o/cfc11 relaxed
# to WACCM above the lid. Steps: unit tests -> 5-day GPU smoke of each experiment -> both chains in parallel
# (scripts/chain_segments.sh, runs/p11{a,b}_<YYYY>0101, aggregates runs/p11{a,b}_5yr) -> diagnostics into
# docs/outputs/11_lid_tracers/. To extend the chosen run to 2019 later: same PREFIX, YEARS=1990-2019 (finished
# segments are skipped, the chain continues from the 1994 checkpoint).
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$REPO"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
YEARS="${YEARS:-1990-1994}"; OUT="$REPO/docs/outputs/11_lid_tracers"; mkdir -p "$OUT" "$REPO/runs"
LOG="$REPO/runs/p11_run5.log"
step() { echo "[p11-5yr] $(date -Is) $*" | tee -a "$LOG"; }
step "start, commit $(git rev-parse --short HEAD), years $YEARS"

for g in 0 1; do
  if nvidia-smi -i "$g" --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -q .; then step "FAIL: GPU $g busy"; exit 1; fi
done
for y in $(seq "${YEARS%-*}" "${YEARS#*-}"); do
  [ -s "$REPO/cache/era5_ref/era5_zm_monthly_$y.nc" ] || { step "FAIL: no QBO target for $y"; exit 1; }
  n=$(( ( $(date -d "$((y+1))-01-01" +%s) - $(date -d "$y-01-01" +%s) ) / 86400 ))
  f="$REPO/cache/era5/wb2_192x96_l63_35c39d41_$(date -d "$y-01-01 - 1 day" +%F)_$(date -d "$y-01-01 + $((n+2)) days" +%F)_6h_u-v-T.nc"
  [ -s "$f" ] || { step "FAIL: no ERA5 window for $y ($f)"; exit 1; }
done
step "inputs present"

JAX_PLATFORMS=cpu python -m pytest tests -x -q > "$REPO/runs/p11_tests.log" 2>&1; rc=$?
step "pytest exit=$rc ($(tail -1 "$REPO/runs/p11_tests.log"))"; [ $rc -eq 0 ] || exit 1

for e in a b; do
  gpu=0; [ "$e" = b ] && gpu=1
  rundir="$REPO/runs/p11${e}_smoke5"; mkdir -p "$rundir"
  ( cd "$rundir" && CUDA_VISIBLE_DEVICES=$gpu python -m jcm_strat.main --config-dir "$REPO/jcm_strat/config" +experiment=p11${e}_prod \
      run.start_date=1990-01-01 run.total_time=5 run.chunk_days=5 physics.terms.held_suarez.qbo.year=1990 \
      physics.terms.production_tracers.first_segment=true hydra.run.dir="$rundir" ) > "$rundir/log.txt" 2>&1
  rc=$?; nf=$(ls "$rundir"/longrun_day*.nc 2>/dev/null | wc -l)
  step "smoke p11${e}_smoke5 exit=$rc ($nf files)"; [ $rc -eq 0 ] && [ "$nf" -ge 1 ] || { step "FAIL: smoke $e"; exit 1; }
done
JAX_PLATFORMS=cpu python - "$REPO/runs/p11a_smoke5" "$REPO/runs/p11b_smoke5" >> "$LOG" 2>&1 <<'PY'
import sys, glob, numpy as np, xarray as xr
for d in sys.argv[1:]:
    ds = xr.open_dataset(sorted(glob.glob(d + "/longrun_day*.nc"))[-1], decode_times=False)
    p = np.asarray(ds.level) * 1013.25; lid = p < 1.0
    a = ds["aoa"].isel(time=-1).values / 365.25; n = ds["n2o"].isel(time=-1).values; b = ds["pulse_1_box"].isel(time=-1).values
    print(f"[smoke {d.split('/')[-1]}] day5: aoa above lid mean {a[lid].mean():.2f} yr (WACCM ~4.5 + 0.3), below {a[~lid].max():.3f} yr max; "
          f"n2o min/max {n.min():.2e}/{n.max():.4f}; pulse_1_box min/max {b.min():.2e}/{b.max():.3f}; "
          f"tracers {sum(k.startswith(('pulse', 'src')) for k in ds.data_vars)} pulse/src fields")
PY

step "launching chains A (GPU 0) and B (GPU 1)"
EXPERIMENT=p11a_prod PREFIX=p11a SCHEME=calendar YEARS="$YEARS" AGG=p11a_5yr SAVE_INTERVAL=0.25 GPU=0 \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p11a_chain_stdout.log" 2>&1 & pa=$!
sleep 90     # let A claim its GPU and compile before B starts
EXPERIMENT=p11b_prod PREFIX=p11b SCHEME=calendar YEARS="$YEARS" AGG=p11b_5yr SAVE_INTERVAL=0.25 GPU=1 \
  bash "$REPO/scripts/chain_segments.sh" > "$REPO/runs/p11b_chain_stdout.log" 2>&1 & pb=$!
wait $pa; ra=$?; step "chain A exit=$ra"
wait $pb; rb=$?; step "chain B exit=$rb"
[ $ra -eq 0 ] && [ $rb -eq 0 ] || { step "FAIL: a chain failed; see runs/p11{a,b}_chain.log"; exit 1; }

for e in a b; do
  run="$REPO/runs/p11${e}_5yr"; lab="P11$e $YEARS (strat63, lid 1 hPa, $([ $e = a ] && echo 'no sink' || echo 'lid sink'))"
  step "diagnostics $e"
  JAX_PLATFORMS=cpu python scripts/pulse_diagnostics.py "$run" "$OUT" --label "$lab" > "$REPO/runs/p11${e}_pulse_diag.log" 2>&1; step "pulse_diagnostics $e exit=$?"
  JAX_PLATFORMS=cpu python scripts/tracer_budget.py "$run" "$OUT" --label "$lab" > "$REPO/runs/p11${e}_budget.log" 2>&1; step "tracer_budget $e exit=$?"
  JAX_PLATFORMS=cpu python scripts/aoa_vs_clams.py "$run" "$OUT" --years 2005-2009 --last-saves 240 \
      --label "$lab: age of air after 5 yr (last 60 d of 1994) vs CLaMS/WACCM 2005-2009 climatology" > "$REPO/runs/p11${e}_aoa.log" 2>&1; step "aoa_vs_clams $e exit=$?"
  JAX_PLATFORMS=cpu python scripts/pulse_evolution.py "$run" "$OUT" --label "$lab" --stages panels vertical mass > "$REPO/runs/p11${e}_evolution.log" 2>&1; step "pulse_evolution $e exit=$?"
done
step "finished"
