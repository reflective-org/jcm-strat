#!/usr/bin/env python3
"""ERA5 stratospheric reference for the Polvani-Kushner and time-step phases (CPU + network).

Two products from the Copernicus Climate Data Store (credentials in ~/.cdsapirc), reduced to
small zonal-mean files under $JCM_STRAT_REPO/cache/era5_ref/:

  era5_zm_monthly_<Y>.nc   zonal-mean u and T, monthly means, 25 levels 1000-1 hPa
                            (reanalysis-era5-pressure-levels-monthly-means)
  era5_u10hPa_daily_<Y>.nc  zonal-mean u at 10 hPa, 6-hourly -> daily mean, 90S-90N
                            (reanalysis-era5-pressure-levels, one request per month)

Needed because the WeatherBench2 store used for nudging stops at 50 hPa, and the existing
AIDE tape covers 1989-1994 on six levels only. Run in tmux with the AIDE download env:
  tmux new-session -d -s preproc_era5_ref \
    '/home/susanne/docs/AIDE-atmosphere_validation/AIDE-atmosphere/era5_env/bin/python \
     scripts/fetch_era5_strat_ref.py 2005 2009 2>&1 | tee runs/preproc_era5_ref.log'
"""
import os, sys, time, zipfile, io
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import netCDF4
import cdsapi

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "cache", "era5_ref"); os.makedirs(OUT, exist_ok=True)
LEVELS = ["1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125", "150", "175", "200",
          "225", "250", "300", "400", "500", "600", "700", "850", "925", "1000"]

def log(s): print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)

def members(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                yield netCDF4.Dataset(n, memory=z.read(n))
    else:
        yield netCDF4.Dataset(path)

def zonal_mean_file(raw, out, vars_, extra_attrs):
    found, lat, lev, tvals, tunits = {}, None, None, None, None
    for ds in members(raw):
        for v in vars_:
            if v in ds.variables:
                x = np.asarray(ds.variables[v][:], dtype="f8")
                found[v] = x.mean(axis=-1)                       # over longitude
                lat = np.asarray(ds.variables["latitude"][:], dtype="f8")
                lev = np.asarray(ds.variables["pressure_level"][:], dtype="f8")
                tname = "valid_time" if "valid_time" in ds.variables else "time"
                tvals = np.asarray(ds.variables[tname][:], dtype="f8"); tunits = ds.variables[tname].units
        ds.close()
    if lat[0] > lat[-1]:
        lat = lat[::-1]; found = {k: v[..., ::-1] for k, v in found.items()}
    if lev[0] > lev[-1]:
        lev = lev[::-1]; found = {k: v[:, ::-1, :] for k, v in found.items()}
    with netCDF4.Dataset(out, "w") as o:
        o.createDimension("time", len(tvals)); o.createDimension("level", len(lev)); o.createDimension("lat", len(lat))
        t = o.createVariable("time", "f8", ("time",)); t[:] = tvals; t.units = tunits
        l = o.createVariable("level", "f8", ("level",)); l[:] = lev; l.units = "hPa"
        a = o.createVariable("lat", "f8", ("lat",)); a[:] = lat; a.units = "degrees_north"
        for v, arr in found.items():
            x = o.createVariable(v + "zm", "f4", ("time", "level", "lat")); x[:] = arr
        o.source = "ERA5 via CDS"; o.note = "zonal means; latitude and pressure ascending"
        for k, val in extra_attrs.items(): setattr(o, k, val)

def fetch_monthly(year):
    out = os.path.join(OUT, f"era5_zm_monthly_{year}.nc")
    if os.path.exists(out): log(f"{year} monthly present"); return
    raw = os.path.join(OUT, f"raw_monthly_{year}.nc")
    if not os.path.exists(raw):
        log(f"{year} monthly: submitting")
        cdsapi.Client(quiet=True, progress=False).retrieve(
            "reanalysis-era5-pressure-levels-monthly-means",
            {"product_type": ["monthly_averaged_reanalysis"], "variable": ["u_component_of_wind", "temperature"],
             "pressure_level": LEVELS, "year": [str(year)], "month": [f"{m:02d}" for m in range(1, 13)],
             "time": ["00:00"], "data_format": "netcdf", "download_format": "unarchived"}, raw)
    zonal_mean_file(raw, out, ["u", "t"], {"product": "reanalysis-era5-pressure-levels-monthly-means", "year": str(year)})
    os.remove(raw); log(f"{year} monthly: wrote {out}")

def fetch_daily_u10(year):
    out = os.path.join(OUT, f"era5_u10hPa_daily_{year}.nc")
    if os.path.exists(out): log(f"{year} daily present"); return
    import calendar
    parts = []
    for m in range(1, 13):
        raw = os.path.join(OUT, f"raw_u10_{year}{m:02d}.nc")
        if not os.path.exists(raw):
            ndays = calendar.monthrange(year, m)[1]
            log(f"{year}-{m:02d} u10: submitting")
            cdsapi.Client(quiet=True, progress=False).retrieve(
                "reanalysis-era5-pressure-levels",
                {"product_type": ["reanalysis"], "variable": ["u_component_of_wind"], "pressure_level": ["10"],
                 "year": [str(year)], "month": [f"{m:02d}"], "day": [f"{d:02d}" for d in range(1, ndays + 1)],
                 "time": ["00:00", "06:00", "12:00", "18:00"], "grid": [1.0, 1.0],
                 "data_format": "netcdf", "download_format": "unarchived"}, raw)
        parts.append(raw)
    # daily mean of the 6-hourly zonal mean
    days, vals, lat = [], [], None
    for raw in parts:
        for ds in members(raw):
            u = np.asarray(ds.variables["u"][:], dtype="f8")            # (time, [level,] lat, lon)
            if u.ndim == 4: u = u[:, 0]
            tname = "valid_time" if "valid_time" in ds.variables else "time"
            tt = netCDF4.num2date(ds.variables[tname][:], ds.variables[tname].units)
            lat = np.asarray(ds.variables["latitude"][:], dtype="f8")
            uz = u.mean(axis=-1)
            for d in sorted({t.date() for t in tt}):
                sel = np.array([t.date() == d for t in tt]); days.append(d); vals.append(uz[sel].mean(axis=0))
            ds.close()
    vals = np.array(vals)
    if lat[0] > lat[-1]: lat = lat[::-1]; vals = vals[:, ::-1]
    with netCDF4.Dataset(out, "w") as o:
        o.createDimension("time", len(days)); o.createDimension("lat", len(lat))
        t = o.createVariable("time", "f8", ("time",)); t.units = "days since 1900-01-01"
        t[:] = netCDF4.date2num([__import__("datetime").datetime(d.year, d.month, d.day) for d in days], t.units)
        a = o.createVariable("lat", "f8", ("lat",)); a[:] = lat
        x = o.createVariable("uzm_10hPa", "f4", ("time", "lat")); x[:] = vals; x.units = "m s-1"
        o.source = "ERA5 via CDS, reanalysis-era5-pressure-levels, 6-hourly -> daily mean, 1x1 deg"
    for raw in parts: os.remove(raw)
    log(f"{year} daily u10: wrote {out} ({len(days)} days)")

if __name__ == "__main__":
    y0, y1 = int(sys.argv[1]), int(sys.argv[2])
    years = list(range(y0, y1 + 1))
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(fetch_monthly, years))
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(fetch_daily_u10, years))
    log("done")
