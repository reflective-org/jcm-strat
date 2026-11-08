#!/usr/bin/env python3
"""Daily ERA5 zonal means for the Phase 28 variability scores (CPU + network, Copernicus CDS).

The first Phase 28 reference used the L95 nudging windows, which are WeatherBench2 data and stop at 50 hPa (every
level above is a copy of 50 hPa). This replaces them with ERA5 from the CDS (reanalysis-era5-pressure-levels,
6-hourly 00/06/12/18 UTC, 2.5 deg grid), reduced to the same daily-zonal-mean npz that scripts/daily_zm.py writes:

  days (datetime64[D]), p_hpa (lev, ascending), lat (ascending, 90S-90N), and u, v, T, th, vth as (day, lev, lat)

with th = T (1000/p)^kappa and vth = the zonal covariance v'theta' formed in each 6-hourly snapshot, then averaged
over the four snapshots of the calendar day.

  full YEAR0 YEAR1   17 levels 1-250 hPa, one request per half-month -> OUT/full/era5_<Y>.npz (D1-D7)
  long YEAR0 YEAR1   10, 50, 100 hPa only, one request per quarter -> OUT/long/era5_<Y>.npz (the 1990-2022 context:
                     u at 10 hPa, T at 50 hPa, heat flux at 100 hPa). A year already fetched in full is subset.

OUT = cache/variability_cds. Run with the AIDE download env (cdsapi; credentials in ~/.cdsapirc):
  /data/AIDE-atmosphere_validation/AIDE-atmosphere/era5_env/bin/python scripts/fetch_era5_daily_zm.py full 2006 2010
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
OUT = os.path.join(REPO, "cache", "variability_cds")
KAPPA = 0.2857
FULL = ["1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125", "150", "175", "200", "225", "250"]
LONG = ["10", "50", "100"]
_nc_lock = threading.Lock()      # netCDF4/HDF5 is not thread safe (fetch_era5_strat_ref.py crashed silently)


def log(s):
    print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)


def members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                yield netCDF4.Dataset(n, memory=z.read(n))
    else:
        yield netCDF4.Dataset(path)


def reduce_raw(raw):
    """CDS netcdf -> dict of daily zonal means (complete days only)."""
    x, lat, lev, tt = {}, None, None, None
    with _nc_lock:
        for ds in members(raw):
            for k in ("u", "v", "t"):
                if k in ds.variables:
                    x[k] = np.asarray(ds.variables[k][:], dtype="f4")              # (time, lev, lat, lon)
                    lat = np.asarray(ds.variables["latitude"][:], dtype="f8")
                    lev = np.asarray(ds.variables["pressure_level"][:], dtype="f8")
                    tn = "valid_time" if "valid_time" in ds.variables else "time"
                    tt = netCDF4.num2date(ds.variables[tn][:], ds.variables[tn].units, only_use_cftime_datetimes=False)
            ds.close()
    fac = ((1000.0 / lev) ** KAPPA).astype("f4")[None, :, None]
    zm = {}
    zm["u"] = x["u"].mean(-1)
    vb = x["v"].mean(-1, keepdims=True); tb = x["t"].mean(-1, keepdims=True)
    zm["v"] = vb[..., 0]; zm["T"] = tb[..., 0]; zm["th"] = zm["T"] * fac
    zm["vth"] = ((x["v"] - vb) * (x["t"] - tb)).mean(-1) * fac
    del x
    days = np.array([np.datetime64(t.strftime("%Y-%m-%d")) for t in tt])
    ud, cnt = np.unique(days, return_counts=True); ud = ud[cnt == 4]
    out = {k: np.stack([v[days == d].mean(0) for d in ud]) for k, v in zm.items()}
    if lat[0] > lat[-1]:
        lat = lat[::-1]; out = {k: v[..., ::-1] for k, v in out.items()}
    if lev[0] > lev[-1]:
        lev = lev[::-1]; out = {k: v[:, ::-1] for k, v in out.items()}
    return dict(days=ud, p_hpa=lev, lat=lat, **{k: v.astype("f4") for k, v in out.items()})


def retrieve(raw, levels, year, months, days):
    cdsapi.Client(quiet=True, progress=False).retrieve(
        "reanalysis-era5-pressure-levels",
        {"product_type": ["reanalysis"], "variable": ["u_component_of_wind", "v_component_of_wind", "temperature"],
         "pressure_level": levels, "year": [str(year)], "month": months, "day": days,
         "time": ["00:00", "06:00", "12:00", "18:00"], "grid": [2.5, 2.5],
         "data_format": "netcdf", "download_format": "unarchived"}, raw + ".part")
    os.replace(raw + ".part", raw)


def concat(parts):
    zs = [dict(np.load(p)) for p in parts]
    return {k: (np.concatenate([z[k] for z in zs]) if k not in ("p_hpa", "lat") else zs[0][k]) for k in zs[0]}


def fetch_part(tag, levels, year, months, d0, d1):
    """One CDS request (days d0..d1 of the given months) -> reduced part npz. The CDS refuses requests above a few
    thousand fields ("cost limits exceeded": 3 x 17 levels x 31 days x 4 times was refused, x 16 days accepted), and
    each request waits in the queue for minutes, so the full levels go by half-month and the long levels by quarter."""
    month = months[0]
    d = os.path.join(OUT, "parts"); os.makedirs(d, exist_ok=True)
    name = f"{tag}_{year}{month:02d}_{d0:02d}"
    part, raw = os.path.join(d, name + ".npz"), os.path.join(d, name + ".nc")
    if os.path.exists(part):
        return part
    for attempt in range(5):
        try:
            if not os.path.exists(raw):
                retrieve(raw, levels, year, [f"{m:02d}" for m in months], [f"{i:02d}" for i in range(d0, d1 + 1)])
            np.savez(part, **reduce_raw(raw)); os.remove(raw); log(f"{name}: reduced")
            return part
        except Exception as e:                                        # CDS hiccups: retry, never leave a half file
            log(f"{name}: attempt {attempt + 1} failed: {e}")
            if os.path.exists(raw):
                os.remove(raw)
            time.sleep(300)
    raise RuntimeError(f"{name} failed")


def chunks(year, half):
    if half:                                                          # full: half-months
        for m in range(1, 13):
            yield [m], 1, 15
            yield [m], 16, calendar.monthrange(year, m)[1]
    else:                                                             # long: quarters (the CDS skips 30/31 Feb etc.)
        for q in range(4):
            yield [3 * q + 1, 3 * q + 2, 3 * q + 3], 1, 31


def full_year(year):
    out = os.path.join(OUT, "full", f"era5_{year}.npz")
    if os.path.exists(out):
        log(f"{year} full present"); return
    with ThreadPoolExecutor(max_workers=4) as ex:
        parts = list(ex.map(lambda c: fetch_part("full", FULL, year, *c), chunks(year, True)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez(out, **concat(parts))
    for p in parts:
        os.remove(p)
    log(f"{year}: wrote {out}")


def long_year(year):
    out = os.path.join(OUT, "long", f"era5_{year}.npz"); os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        return
    full = os.path.join(OUT, "full", f"era5_{year}.npz")
    if os.path.exists(full):
        z = dict(np.load(full)); k = np.isin(z["p_hpa"], [float(l) for l in LONG])
        np.savez(out, **{n: (v[:, k] if v.ndim == 3 else v[k] if n == "p_hpa" else v) for n, v in z.items()})
        log(f"{year} long: subset of full"); return
    parts = [fetch_part("long", LONG, year, *c) for c in chunks(year, False)]
    np.savez(out, **concat(parts))
    for p in parts:
        os.remove(p)
    log(f"{year} long: wrote {out}")


if __name__ == "__main__":
    mode, y0, y1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if mode == "full":
        for y in range(y0, y1 + 1):
            full_year(y)
    elif mode == "long":
        with ThreadPoolExecutor(max_workers=2) as ex:
            list(ex.map(long_year, range(y0, y1 + 1)))     # 2 at a time: the full levels go first
    else:
        sys.exit("mode: full | long")
    log("done")
