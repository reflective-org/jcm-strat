#!/usr/bin/env python3
"""Polar-vortex time series from a chunked jcm-strat run: zonal-mean u at 60N and 60S, 10 hPa.

    python scripts/vortex_series.py runs/<session> out.png [--start 2005-01-01]

Uses the 5-day means as saved. Marks the ERA5 major sudden stratospheric warmings inside
2005-2009 (central dates: 2006-01-21, 2008-02-22, 2009-01-24) so the question "does the free
stratosphere, driven only by the nudged troposphere, weaken its vortex in those winters?" can be
read off. Also prints DJF-mean u(60N, 10 hPa) per winter and the number of 5-day means with
u < 0 (the SSW reversal criterion) per winter.
"""
import argparse
import datetime as dt
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

SSW = ["2006-01-21", "2008-02-22", "2009-01-24"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("out_png"); ap.add_argument("--start", default="2005-01-01")
    ap.add_argument("--paradis", default=None, help="zonal_means.nc from scripts/paradis_zonal.py: adds a second panel with the PARADIS rollout's u(60N/60S, 10 hPa)")
    ap.add_argument("--era5-u10", default=None, help="glob of era5_u10hPa_daily_<year>.nc (uzm_10hPa on time x lat): overlays ERA5 on the model panel and tabulates its winters")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")),
                   key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False, data_vars=["u_wind"])
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]; starts = [0] + ends[:-1]
    days = []
    for f, s0, s1 in zip(files, starts, ends):
        with xr.open_dataset(f, decode_times=False) as d:
            n = d.sizes["time"]
        days.extend(s0 + (s1 - s0) / n * (j + 0.5) for j in range(n))     # window centres
    t0 = dt.date.fromisoformat(a.start)
    dates = np.array([t0 + dt.timedelta(days=float(d)) for d in days])
    p = np.asarray(ds.level) * 1013.25; k = int(np.argmin(np.abs(p - 10)))
    lat = np.asarray(ds.lat)
    u = ds.u_wind.isel(level=k).mean("lon")                                   # (time, lat)
    jn = int(np.argmin(np.abs(lat - 60))); js = int(np.argmin(np.abs(lat + 60)))
    un = u.isel(lat=jn).values; us = u.isel(lat=js).values

    nrows = 2 if a.paradis else 1
    fig, axes = plt.subplots(nrows, 1, figsize=(13, 4.2 * nrows), squeeze=False); ax = axes[0, 0]
    ax.plot(dates, un, label=f"u({lat[jn]:.0f}N, {p[k]:.0f} hPa)")
    ax.plot(dates, us, label=f"u({lat[js]:.0f}S, {p[k]:.0f} hPa)", alpha=.7)
    ax.axhline(0, color="k", lw=.6)
    era = None
    if a.era5_u10:
        import glob as _glob, pandas as pd
        era = xr.open_mfdataset(sorted(_glob.glob(a.era5_u10)), combine="nested", concat_dim="time")
        el = np.asarray(era.lat); en = int(np.argmin(np.abs(el - 60))); es = int(np.argmin(np.abs(el + 60)))
        et = pd.to_datetime(era.time.values); eun = era.uzm_10hPa.isel(lat=en).values; eus = era.uzm_10hPa.isel(lat=es).values
        ax.plot(et, eun, color="k", lw=.7, alpha=.8, label="ERA5 u(60N, 10 hPa), daily")
        ax.plot(et, eus, color="grey", lw=.7, alpha=.8, label="ERA5 u(60S, 10 hPa), daily")
    for s in SSW:
        d = dt.date.fromisoformat(s)
        if dates[0] <= d <= dates[-1]:
            ax.axvline(d, color="r", ls="--", lw=.8); ax.text(d, ax.get_ylim()[1] * 0.9, " ERA5 SSW", color="r", fontsize=7)
    ax.set_ylabel("m/s"); ax.set_title(f"{os.path.basename(a.rundir)}: zonal-mean zonal wind at 10 hPa (5-day means)"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    if a.paradis:
        pz = xr.open_dataset(a.paradis); k10 = int(np.argmin(np.abs(pz.level.values - 10)))
        pj = int(np.argmin(np.abs(pz.lat.values - 60.5))); ps_ = int(np.argmin(np.abs(pz.lat.values + 60.5)))
        ax2 = axes[1, 0]; pt = pz.time.values
        ax2.plot(pt, pz.u.isel(level=k10, lat=pj).values, label="PARADIS u(60.5N, 10 hPa)")
        ax2.plot(pt, pz.u.isel(level=k10, lat=ps_).values, label="PARADIS u(60.5S, 10 hPa)", alpha=.7)
        ax2.axhline(0, color="k", lw=.6); ax2.set_ylabel("m/s"); ax2.grid(alpha=.3); ax2.legend(fontsize=8)
        ax2.set_title("PARADIS v2 stage 3d rollout 1995_12_06_5y1m (daily after the first month): the same diagnostic, different years", fontsize=9)
        lo = min(ax.get_ylim()[0], ax2.get_ylim()[0]); hi = max(ax.get_ylim()[1], ax2.get_ylim()[1]); ax.set_ylim(lo, hi); ax2.set_ylim(lo, hi)
    fig.tight_layout(); fig.savefig(a.out_png, dpi=130); print("wrote", a.out_png)

    print("winter   DJF-mean u(60N,10hPa) [m/s]   5-day means with u<0 (Nov-Mar)")
    years = sorted({d.year for d in dates})
    for y in years[:-1]:
        djf = [(d.year == y and d.month == 12) or (d.year == y + 1 and d.month in (1, 2)) for d in dates]
        nm = [(d.year == y and d.month >= 11) or (d.year == y + 1 and d.month <= 3) for d in dates]
        if sum(djf) < 10:
            continue
        print(f"{y}/{y+1}   {np.mean(un[np.array(djf)]):8.1f}                   {int((un[np.array(nm)] < 0).sum()):3d}")
    if era is not None:
        print("ERA5     DJF-mean u(60N,10hPa) [m/s]   days with u<0 (Nov-Mar)   DJF-mean u(60S)")
        ey = np.array([d.year for d in et]); em = np.array([d.month for d in et])
        for y in sorted(set(ey))[:-1]:
            djf = ((ey == y) & (em == 12)) | ((ey == y + 1) & (em <= 2)); nm = ((ey == y) & (em >= 11)) | ((ey == y + 1) & (em <= 3))
            if djf.sum() < 20: continue
            print(f"{y}/{y+1}   {eun[djf].mean():8.1f}                   {int((eun[nm] < 0).sum()):3d}                  {eus[djf].mean():6.1f}")


if __name__ == "__main__":
    main()
