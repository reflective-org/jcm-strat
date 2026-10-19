#!/usr/bin/env python3
"""ERA5 TEM inputs for the Phase 17 upwelling target (CPU + network).

Up to Phase 16 every tropical w* was compared with WACCM6 only; the WeatherBench2 store used for the
nudging stops at 50 hPa and the cached ERA5 zonal means are monthly means (no eddy fluxes). This script
pulls 6-hourly v and T on the stratospheric pressure levels from the Copernicus Climate Data Store
(reanalysis-era5-pressure-levels, 2.5 deg grid, one request per month) and reduces each month at once
to the three zonal-mean fields the TEM residual circulation needs:

  vzm    [v]                       monthly mean of the zonal mean, m/s
  tzm    [T]                       K
  vtzm   [v'T'] (zonal deviations) monthly mean of the zonal covariance at each 6-hourly time, K m/s

written to $JCM_STRAT_REPO/cache/era5_ref/era5_tem_monthly_<Y>.nc (time, level, lat; ascending). The TEM
formula is linear in [v] and [v'theta'] once theta is a function of p alone at a pressure level, so the
monthly means are enough: theta = T (1000/p)^kappa, [v'theta'] = (1000/p)^kappa [v'T'].

  tmux new-session -d -s preproc_era5_tem \
    '/data/AIDE-atmosphere_validation/AIDE-atmosphere/era5_env/bin/python scripts/fetch_era5_tem.py 1998 1999 2>&1 | tee runs/preproc_era5_tem.log'
"""
import calendar
import os
import sys
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import cdsapi
import netCDF4
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "cache", "era5_ref"); os.makedirs(OUT, exist_ok=True)
LEVELS = ["1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125", "150", "175", "200", "225", "250"]
_nc_lock = threading.Lock()      # netCDF4/HDF5 reads from several threads crashed fetch_era5_strat_ref.py silently


def log(s):
    print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)


def members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                yield netCDF4.Dataset(n, memory=z.read(n))
    else:
        yield netCDF4.Dataset(path)


def reduce_month(raw):
    """-> lat (asc), lev (asc), [v], [T], [v'T'] monthly means (level, lat)."""
    v = t = lat = lev = None
    for ds in members(raw):
        for name in ds.variables:
            if name == "v": v = np.asarray(ds.variables["v"][:], dtype="f8")
            if name == "t": t = np.asarray(ds.variables["t"][:], dtype="f8")
        if "latitude" in ds.variables:
            lat = np.asarray(ds.variables["latitude"][:], dtype="f8"); lev = np.asarray(ds.variables["pressure_level"][:], dtype="f8")
        ds.close()
    vz, tz = v.mean(-1, keepdims=True), t.mean(-1, keepdims=True)              # (time, lev, lat, 1)
    vt = ((v - vz) * (t - tz)).mean(-1)
    out = [vz[..., 0].mean(0), tz[..., 0].mean(0), vt.mean(0)]                    # (lev, lat)
    if lat[0] > lat[-1]: lat = lat[::-1]; out = [o[:, ::-1] for o in out]
    if lev[0] > lev[-1]: lev = lev[::-1]; out = [o[::-1] for o in out]
    return lat, lev, out


def fetch_month(year, month):
    part = os.path.join(OUT, f"tem_part_{year}{month:02d}.npz")
    if os.path.exists(part):
        return part
    raw = os.path.join(OUT, f"raw_tem_{year}{month:02d}.nc")
    if not os.path.exists(raw):
        log(f"{year}-{month:02d}: submitting")
        ndays = calendar.monthrange(year, month)[1]
        cdsapi.Client(quiet=True, progress=False).retrieve(
            "reanalysis-era5-pressure-levels",
            {"product_type": ["reanalysis"], "variable": ["v_component_of_wind", "temperature"], "pressure_level": LEVELS,
             "year": [str(year)], "month": [f"{month:02d}"], "day": [f"{d:02d}" for d in range(1, ndays + 1)],
             "time": ["00:00", "06:00", "12:00", "18:00"], "grid": [2.5, 2.5],
             "data_format": "netcdf", "download_format": "unarchived"}, raw + ".part")
        os.replace(raw + ".part", raw)
    with _nc_lock:
        lat, lev, (vz, tz, vt) = reduce_month(raw)
    np.savez(part, lat=lat, lev=lev, vzm=vz, tzm=tz, vtzm=vt)
    os.remove(raw); log(f"{year}-{month:02d}: reduced")
    return part


def write_year(year, parts):
    out = os.path.join(OUT, f"era5_tem_monthly_{year}.nc")
    zs = [np.load(p) for p in parts]
    with netCDF4.Dataset(out, "w") as o:
        o.createDimension("time", 12); o.createDimension("level", zs[0]["lev"].size); o.createDimension("lat", zs[0]["lat"].size)
        t = o.createVariable("time", "f8", ("time",)); t.units = "days since 1900-01-01"
        t[:] = netCDF4.date2num([__import__("datetime").datetime(year, m, 15) for m in range(1, 13)], t.units)
        l = o.createVariable("level", "f8", ("level",)); l[:] = zs[0]["lev"]; l.units = "hPa"
        a = o.createVariable("lat", "f8", ("lat",)); a[:] = zs[0]["lat"]; a.units = "degrees_north"
        for k, u in (("vzm", "m s-1"), ("tzm", "K"), ("vtzm", "K m s-1")):
            x = o.createVariable(k, "f4", ("time", "level", "lat")); x[:] = np.stack([z[k] for z in zs]); x.units = u
        o.source = "ERA5 via CDS, reanalysis-era5-pressure-levels, 6-hourly, 2.5 deg"
        o.note = "monthly means of zonal means; vtzm = monthly mean of the zonal covariance [v'T'] at each time"
    for p in parts: os.remove(p)
    log(f"{year}: wrote {out}")


if __name__ == "__main__":
    y0, y1 = int(sys.argv[1]), int(sys.argv[2])
    for year in range(y0, y1 + 1):
        if os.path.exists(os.path.join(OUT, f"era5_tem_monthly_{year}.nc")):
            log(f"{year} present"); continue
        with ThreadPoolExecutor(max_workers=4) as ex:
            parts = list(ex.map(lambda m: fetch_month(year, m), range(1, 13)))
        write_year(year, parts)
    log("done")
