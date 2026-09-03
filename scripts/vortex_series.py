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

    fig, ax = plt.subplots(figsize=(13, 4.2))
    ax.plot(dates, un, label=f"u({lat[jn]:.0f}N, {p[k]:.0f} hPa)")
    ax.plot(dates, us, label=f"u({lat[js]:.0f}S, {p[k]:.0f} hPa)", alpha=.7)
    ax.axhline(0, color="k", lw=.6)
    for s in SSW:
        d = dt.date.fromisoformat(s)
        if dates[0] <= d <= dates[-1]:
            ax.axvline(d, color="r", ls="--", lw=.8); ax.text(d, ax.get_ylim()[1] * 0.9, " ERA5 SSW", color="r", fontsize=7)
    ax.set_ylabel("m/s"); ax.set_title(f"{os.path.basename(a.rundir)}: zonal-mean zonal wind at 10 hPa (5-day means)"); ax.legend(fontsize=8); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(a.out_png, dpi=130); print("wrote", a.out_png)

    print("winter   DJF-mean u(60N,10hPa) [m/s]   5-day means with u<0 (Nov-Mar)")
    years = sorted({d.year for d in dates})
    for y in years[:-1]:
        djf = [(d.year == y and d.month == 12) or (d.year == y + 1 and d.month in (1, 2)) for d in dates]
        nm = [(d.year == y and d.month >= 11) or (d.year == y + 1 and d.month <= 3) for d in dates]
        if sum(djf) < 10:
            continue
        print(f"{y}/{y+1}   {np.mean(un[np.array(djf)]):8.1f}                   {int((un[np.array(nm)] < 0).sum()):3d}")


if __name__ == "__main__":
    main()
