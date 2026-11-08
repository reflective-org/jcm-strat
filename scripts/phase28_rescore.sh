#!/usr/bin/env bash
# Phase 28 rescore with a real ERA5 reference (Susanne 2026-11-07). The first reference (L95 nudging windows) is
# WeatherBench2 data, constant above 50 hPa, so D1-D4 and the ERA5 w* in D4-w/D7 were wrong. CPU + network only, no GPU.
# tmux strat_p28_rescore, log runs/p28_rescore.log.
#   1. CDS ERA5 daily zonal means (scripts/fetch_era5_daily_zm.py): full 1-250 hPa 2006-2010, 10/50/100 hPa 1990-2022
#   2. check u 60N 10 hPa against the independent cache/era5_ref/era5_u10hPa_daily_2006-2009 files
#   3. variability_score.py and success_metrics.py --variability (model npz in cache/variability are reused)
#   4. commit (not pushed)
set -uo pipefail
cd "$(dirname "$0")/.."
ENV=/data/AIDE-atmosphere_validation/AIDE-atmosphere/era5_env/bin/python
fetch() { bash scripts/memcap.sh -m 32G -- $ENV scripts/fetch_era5_daily_zm.py "$@"; }
py() { bash scripts/memcap.sh -m 64G -- .venv/bin/python "$@"; }
log() { echo "[p28r] $(TZ=America/Los_Angeles date '+%Y-%m-%d %H:%M %Z') $*"; }
C=cache/variability_cds; Z=cache/variability; OUT=docs/outputs/28_variability
RUNS=(P20b AL7 AL7h AL7t L0 LAL7 QBO30 QBO10d)

log "start, commit $(git rev-parse --short HEAD)"
fetch full 2006 2010 > runs/p28_fetch_full.log 2>&1 & P1=$!
fetch long 1990 2005 > runs/p28_fetch_long1.log 2>&1 & P2=$!
fetch long 2011 2022 > runs/p28_fetch_long2.log 2>&1 & P3=$!
wait $P1 || log "full fetch FAILED (runs/p28_fetch_full.log)"
log "full done ($(ls $C/full/era5_*.npz 2>/dev/null | wc -l)/5)"
wait $P2 || log "long 1990-2005 FAILED"; wait $P3 || log "long 2011-2022 FAILED"
fetch long 2006 2010 >> runs/p28_fetch_long1.log 2>&1 || log "long 2006-2010 FAILED"
log "long done ($(ls $C/long/era5_*.npz 2>/dev/null | wc -l)/33)"
[ "$(ls $C/full/era5_*.npz 2>/dev/null | wc -l)" -eq 5 ] || { log "missing full years, stop"; exit 1; }

py - <<'PY'
import glob, numpy as np, netCDF4
z = [dict(np.load(f"cache/variability_cds/full/era5_{y}.npz")) for y in range(2006, 2010)]
d = np.concatenate([x["days"] for x in z]); i10 = list(z[0]["p_hpa"]).index(10.0); j = list(z[0]["lat"]).index(60.0)
u = np.concatenate([x["u"][:, i10, j] for x in z])
r = []
for y in range(2006, 2010):
    with netCDF4.Dataset(f"cache/era5_ref/era5_u10hPa_daily_{y}.nc") as ds:
        lat = ds["lat"][:]; v = [k for k in ds.variables if k.startswith("uzm")][0]; x = np.asarray(ds[v][:]).squeeze()
        r.append(x[:, int(np.argmin(abs(lat - 60.0)))])
r = np.concatenate(r); n = min(r.size, u.size)
print(f"[p28r] check u 60N 10 hPa vs era5_u10hPa_daily 2006-2009: n {n}, r {np.corrcoef(u[:n], r[:n])[0,1]:.3f}, "
      f"std {u[:n].std():.1f} vs {r[:n].std():.1f}, mean diff {np.mean(u[:n] - r[:n]):+.2f} m/s", flush=True)
PY

ARGS=(); for n in "${RUNS[@]}"; do ARGS+=("$n=$Z/${n}_0610.npz"); done
LONG=(); [ "$(ls $C/long/era5_*.npz 2>/dev/null | wc -l)" -eq 33 ] && LONG=(--long-dir "$C/long" --long 1990-2022) || log "no full 1990-2022 context, scoring without it"
JAX_PLATFORMS=cpu py scripts/variability_score.py "$OUT" "${ARGS[@]}" --era5-dir "$C/full" "${LONG[@]}" \
  --t0 2006-01-01 --t1 2011-01-01 > runs/p28_variability.log 2>&1 \
  || { log "variability_score FAILED (runs/p28_variability.log)"; exit 1; }
S="$OUT/success_0610"
ALL=(); for n in "${RUNS[@]}"; do ALL+=("$n=runs/p26_${n}_0610"); done
JAX_PLATFORMS=cpu py scripts/success_metrics.py "$S" "${ALL[@]}" --t0 2006-01-01 --t1 2011-01-01 --window-years 5 \
  --variability "$OUT/variability.json" > runs/p28_success.log 2>&1 || { log "success_metrics FAILED (runs/p28_success.log)"; exit 1; }
cat "$OUT/variability_table.md"
git add scripts/fetch_era5_daily_zm.py scripts/variability_score.py scripts/daily_zm.py scripts/phase28_rescore.sh \
  "$OUT"/variability* "$OUT"/success_0610
git commit -q -m "Phase 28: group D rescored against CDS ERA5 (the L95 nudging windows are constant above 50 hPa)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && log "committed $(git rev-parse --short HEAD)"
log "finished"
