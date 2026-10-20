#!/usr/bin/env python3
"""Phase 22: one iteration of the equilibrium-temperature correction toward ERA5, on the model's own levels.

    python scripts/teq_update.py runs/<agg> --t0 2005-04-01 --t1 2008-01-01 --out corr.nc [--prev prev.nc]
        [--mode zonal|chang3d] [--alpha A] [--lat-mask 25 35] [--p-range 1 100] [--smooth] [--cap 40]

The model's monthly-mean temperature over [t0, t1) (every 6-hourly frame, calendar months) is compared with ERA5 for the
SAME months, and the cumulative additive correction to T_eq becomes

    dT(new) = clip( dT(prev) - alpha * W * S[T_model - T_ERA5], -cap, cap )

* ``--mode zonal`` (Phase 17 on p20b): zonal means; ERA5 = cache/era5_ref/era5_zm_monthly_<year>.nc interpolated in log p onto the
  model's reference levels; S = Phase 17's 1-2-1 smoothing (twice in latitude, once periodic in month) with ``--smooth``.
* ``--mode chang3d`` (Chang 2006, as used by Wu & Reichler 2018 and Mooring & Linz): the full 3-D monthly mean T(month, lev, lat,
  lon) against ERA5's 3-D monthly mean (CDS monthly means 1-500 hPa, cache/era5_ref/era5_t3d_monthly_<y>.nc), pointwise, no
  smoothing; Chang/Wu-Reichler's step is alpha = 2/3.

W is the region mask on the INCREMENT (the previous correction is kept everywhere): 1 for p_ref in ``--p-range`` (hPa) and
|lat| >= ``--lat-mask``[1], 0 for |lat| <= ``--lat-mask``[0] (sin^2 taper; ``--lat-mask 0 0`` = all latitudes); above the
p-range top the increment tapers to zero at a tenth of that pressure (ERA5 has nothing above 1 hPa), below its bottom to zero
at 1.25 x the bottom pressure. The file holds dte(month, pfull, lat[, lon]) in K on the model's reference pressures, the format
``JuckerColumns(te_correction_file=..., te_correction_mode=jfv|total)`` reads ("jfv": added to the JFV T_e above 100 hPa and
faded out by the 100-250 hPa blend; "total": added to the blended T_eq on every level - needed for a p-range below 100 hPa).
"""
from __future__ import annotations

import argparse, glob, os, re, sys
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_compare as sc        # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERA5_ZM = "/data/JCM_stripped/jcm-strat/cache/era5_ref/era5_zm_monthly_{y}.nc"


def run_files(rundir):
    fs = glob.glob(os.path.join(rundir, "longrun_day*.nc"))
    return sorted(fs, key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))


def model_monthly(rundir, t0, t1, three_d):
    """Monthly means over [t0, t1) of T (zonal: (ym, lev, lat); 3-D: (ym, lev, lat, lon)), keyed by (year, month)."""
    sums, cnt = {}, {}
    p_ref = lat = lon = None
    for f in run_files(rundir):
        d = xr.open_dataset(f, decode_times=True)
        tt = d.time.values
        if tt[-1] < t0 or tt[0] >= t1:
            d.close(); continue
        k = np.where((tt >= t0) & (tt < t1))[0]
        if k.size == 0:
            d.close(); continue
        T = d.temperature.isel(time=k)
        T = T.transpose("time", "level", "lat", "lon") if three_d else T.mean("lon").transpose("time", "level", "lat")
        vals = T.values.astype("f8"); ym = [(int(str(x)[:4]), int(str(x)[5:7])) for x in tt[k]]
        for i, key in enumerate(ym):
            if key not in sums:
                sums[key] = np.zeros(vals.shape[1:]); cnt[key] = 0
            sums[key] += vals[i]; cnt[key] += 1
        p_ref = d.level.values * sc.P0_HPA; lat = d.lat.values; lon = d.lon.values
        d.close()
    keys = sorted(sums)
    return {k: sums[k] / cnt[k] for k in keys}, p_ref, lat, lon


def era5_zonal(keys, p_ref, lat):
    """ERA5 monthly zonal-mean T for each (year, month) in keys on (lev = p_ref, lat)."""
    out = {}
    for y in sorted({k[0] for k in keys}):
        ds = xr.open_dataset(ERA5_ZM.format(y=y), decode_times=True)
        tname = [c for c in ds.coords if c.startswith("time") or c == "valid_time"][0]
        t = ds["tzm"].rename({tname: "time"}).interp(lat=lat)
        lp = np.log(ds.level.values.astype(float)); o = np.argsort(lp)
        for m in range(1, 13):
            if (y, m) not in keys:
                continue
            prof = t.sel(time=t.time.dt.month == m).mean("time").values[o]      # (nlev_era, nlat)
            lpo = np.log(np.clip(p_ref, np.exp(lp[o][0]), np.exp(lp[o][-1])))
            out[(y, m)] = np.stack([np.interp(lpo, lp[o], prof[:, j]) for j in range(lat.size)], axis=1)   # (lev, lat)
        ds.close()
    return out


ERA5_T3D = os.path.join(REPO, "cache", "era5_ref", "era5_t3d_monthly_{y}.nc")


def era5_3d(keys, p_ref, lat, lon):
    """ERA5 monthly-mean 3-D T on the model grid and reference levels, (lev surface-first, lat, lon) per key, from the CDS monthly
    means 1-500 hPa (scripts/fetch_era5_t3d_monthly.py; the WeatherBench2 nudging cache cannot be used: 13 levels, clamped above
    50 hPa). Bilinear in lat/lon, linear in log p, clamped outside 1-500 hPa (the update mask is zero there)."""
    out = {}
    for y in sorted({k[0] for k in keys}):
        f = ERA5_T3D.format(y=y)
        if not os.path.exists(f):
            raise SystemExit(f"missing {f} (scripts/fetch_era5_t3d_monthly.py)")
        ds = xr.open_dataset(f, decode_times=True)
        ren = {c: n for c, n in (("valid_time", "time"), ("pressure_level", "plev"), ("latitude", "lat"), ("longitude", "lon")) if c in ds.dims or c in ds.coords}
        ds = ds.rename(ren).sortby("lat").sortby("plev")
        t = ds["t"] if "t" in ds else ds["temperature"]
        t = xr.concat([t, t.isel(lon=0).assign_coords(lon=360.0)], "lon")                # periodic edge for interpolation
        t = t.interp(lat=lat, lon=lon)
        lp = np.log(ds.plev.values.astype(float)); lpo = np.log(np.clip(p_ref, np.exp(lp[0]), np.exp(lp[-1])))
        for m in range(1, 13):
            if (y, m) not in keys:
                continue
            a = t.sel(time=t.time.dt.month == m).isel(time=0).transpose("plev", "lat", "lon").values.astype("f8")
            j = np.clip(np.searchsorted(lp, lpo) - 1, 0, lp.size - 2); w = np.clip((lpo - lp[j]) / (lp[j + 1] - lp[j]), 0, 1)
            out[(y, m)] = (1 - w)[:, None, None] * a[j] + w[:, None, None] * a[j + 1]       # (lev, lat, lon)
        ds.close()
    return out


def smooth121(x, axis, periodic=False):
    x = np.moveaxis(x, axis, -1)
    if periodic:
        y = 0.25 * np.roll(x, 1, -1) + 0.5 * x + 0.25 * np.roll(x, -1, -1)
    else:
        xp = np.concatenate([x[..., :1], x, x[..., -1:]], -1)
        y = 0.25 * xp[..., :-2] + 0.5 * xp[..., 1:-1] + 0.25 * xp[..., 2:]
    return np.moveaxis(y, -1, axis)


def region_mask(p_ref, lat, lat_mask, p_range):
    al = np.abs(lat); a0, a1 = lat_mask
    if a1 <= 0:
        ml = np.ones_like(al)
    else:
        ml = np.where(al >= a1, 1.0, np.where(al <= a0, 0.0, np.sin(0.5 * np.pi * (al - a0) / (a1 - a0)) ** 2))
    ptop, pbot = p_range; lp = np.log(p_ref)
    up = np.clip((lp - np.log(ptop / 10.0)) / np.log(10.0), 0.0, 1.0)                 # 1 at ptop, 0 at ptop/10
    dn = np.clip((np.log(1.25 * pbot) - lp) / np.log(1.25), 0.0, 1.0)                  # 1 at pbot, 0 at 1.25 pbot
    mp = np.where(p_ref < ptop, np.sin(0.5 * np.pi * up) ** 2, np.where(p_ref > pbot, np.sin(0.5 * np.pi * dn) ** 2, 1.0))
    return mp[:, None] * ml[None, :]                                                   # (lev, lat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("--t0", required=True); ap.add_argument("--t1", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--prev", default=None)
    ap.add_argument("--mode", choices=("zonal", "chang3d"), default="zonal"); ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--lat-mask", type=float, nargs=2, default=(0.0, 0.0)); ap.add_argument("--p-range", type=float, nargs=2, default=(1.0, 100.0))
    ap.add_argument("--smooth", action="store_true"); ap.add_argument("--cap", type=float, default=40.0)
    a = ap.parse_args()
    three = a.mode == "chang3d"
    alpha = a.alpha if a.alpha is not None else (2.0 / 3.0 if three else 0.7)
    t0, t1 = np.datetime64(a.t0), np.datetime64(a.t1)
    mm, p_ref, lat, lon = model_monthly(a.rundir, t0, t1, three)
    keys = list(mm)
    ref = era5_3d(keys, p_ref, lat, lon) if three else era5_zonal(keys, p_ref, lat)
    # calendar-month means of the error over the window
    shp = mm[keys[0]].shape
    err = np.zeros((12,) + shp); n = np.zeros(12)
    for k in keys:
        err[k[1] - 1] += mm[k] - ref[k]; n[k[1] - 1] += 1
    if (n == 0).any():
        raise SystemExit(f"window lacks calendar months {np.where(n == 0)[0] + 1}")
    err /= n.reshape((12,) + (1,) * len(shp))
    if a.smooth:
        err = smooth121(smooth121(err, 2), 2); err = smooth121(err, 0, periodic=True)
    W = region_mask(p_ref, lat, a.lat_mask, a.p_range)                                   # (lev, lat)
    Wx = W[None, :, :, None] if three else W[None]
    prev = 0.0
    if a.prev:
        with xr.open_dataset(a.prev) as d:
            prev = d.dte.values
        if prev.shape != err.shape:
            raise SystemExit(f"--prev {a.prev} has shape {prev.shape}, this update {err.shape}")
    inc = -alpha * Wx * err
    tot = np.clip(prev + inc, -a.cap, a.cap)
    dims = ("month", "pfull", "lat", "lon") if three else ("month", "pfull", "lat")
    coords = {"month": np.arange(1, 13), "pfull": p_ref, "lat": lat}
    if three:
        coords["lon"] = lon
    if three:     # model output is (lev, lat, lon) already
        pass
    ds = xr.Dataset({"dte": (dims, tot.astype("f8"))}, coords=coords)
    ds.dte.attrs.update(units="K", long_name="additive correction to the equilibrium temperature (Phase 22)")
    # scores of the error the update was made from (cos-weighted over the masked region and 100-10 hPa extratropics)
    wlat = np.cos(np.deg2rad(lat))
    ez = err.mean(-1) if three else err                                                  # (12, lev, lat) zonal error
    sel = (p_ref >= 10) & (p_ref <= 100)
    ext = np.abs(lat) >= 30
    rms_ls = float(np.sqrt((ez[:, sel][:, :, ext] ** 2 * wlat[ext]).sum() / (12 * sel.sum() * wlat[ext].sum())))
    ds.attrs.update(source_run=os.path.abspath(a.rundir), window=f"{a.t0}..{a.t1}", mode=a.mode, alpha=alpha, cap=a.cap,
                    lat_mask=str(tuple(a.lat_mask)), p_range=str(tuple(a.p_range)), smooth=int(a.smooth), prev=str(a.prev),
                    zonal_T_rmse_100_10hPa_extratropics_before=rms_ls)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ds.to_netcdf(a.out)
    ann = tot.mean(0); ann = ann.mean(-1) if three else ann
    print(f"[teq] {a.rundir} {a.t0}..{a.t1} mode {a.mode} alpha {alpha:.3f}: zonal T RMSE 100-10 hPa |lat|>=30 {rms_ls:.2f} K; "
          f"increment {inc.min():+.1f}..{inc.max():+.1f} K, total {tot.min():+.1f}..{tot.max():+.1f} K -> {a.out}")
    for pl in (300, 100, 50, 30, 10, 1):
        k = int(np.argmin(np.abs(p_ref - pl)))
        print(f"[teq]   annual zonal dT at {pl:>3} hPa, lat -80/-60/-30/0/30/60/80: " +
              " ".join(f"{np.interp(l, lat, ann[k]):+5.1f}" for l in (-80, -60, -30, 0, 30, 60, 80)))


if __name__ == "__main__":
    main()
