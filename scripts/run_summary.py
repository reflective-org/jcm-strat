#!/usr/bin/env python3
"""Stability summary of a chunked jcm run: the Phase-1 acceptance numbers and a 4-panel plot.

    python scripts/run_summary.py runs/<session> out.png [--last-days 60]

Reads every longrun_day*.nc (5-day means, one row per save) and reports
  * global-mean surface pressure and its drift over the run (hPa),
  * global mass-weighted kinetic energy (J/kg),
  * zonal-mean temperature of the top model level: mean over the last N days and its
    linear trend (K/day) -- the "does the top run away" check,
  * global min/max temperature per save.
Global means use cos(lat) weights on the regular-in-longitude Gaussian grid (the exact
quadrature weights are not in the file; cos(lat) is within ~1e-3 of them at T63).
"""
import argparse
import glob
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def load(rundir):
    files = sorted(glob.glob(f"{rundir}/longrun_day*.nc"),
                   key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not files:
        raise SystemExit(f"no longrun_day*.nc in {rundir}")
    dss = [xr.open_dataset(f, decode_times=False) for f in files]
    return files, dss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir")
    ap.add_argument("out_png")
    ap.add_argument("--last-days", type=float, default=60.0)
    a = ap.parse_args()
    files, dss = load(a.rundir)
    day, ps, ke, ttop, tmin, tmax = [], [], [], [], [], []
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]
    top_idx = -1 if float(dss[0].level[-1]) < float(dss[0].level[0]) else 0  # smallest sigma = model top
    for k, ds in enumerate(dss):
        prev, end = (ends[k - 1] if k else 0), ends[k]
        nt = ds.sizes["time"]
        w = np.cos(np.deg2rad(ds.lat.values)); w = w / w.sum()
        for it in range(nt):
            d = ds.isel(time=it)
            dp = d["pressure_thickness"]
            colw = dp / dp.sum("level")
            ps.append(float((d["surface_pressure"].mean("lon") * w).sum()) / 100.0)
            ke_col = (0.5 * (d["u_wind"] ** 2 + d["v_wind"] ** 2) * colw).sum("level")
            ke.append(float((ke_col.mean("lon") * w).sum()))
            T = d["temperature"]
            ttop.append(float((T.isel(level=top_idx).mean("lon") * w).sum()))
            tmin.append(float(T.min())); tmax.append(float(T.max()))
            day.append(prev + (it + 1) * (end - prev) / nt)
    day = np.array(day); ps = np.array(ps); ke = np.array(ke); ttop = np.array(ttop)

    sel = day >= day.max() - a.last_days
    trend = np.polyfit(day[sel], ttop[sel], 1)[0] if sel.sum() >= 2 else float("nan")
    print(f"run:                    {a.rundir}  ({len(files)} chunk files, {len(day)} saves, day {day.min():.0f}-{day.max():.0f})")
    print(f"global-mean ps:         {ps[0]:.3f} -> {ps[-1]:.3f} hPa   drift {ps[-1]-ps[0]:+.4f} hPa")
    print(f"global KE (J/kg):       {ke[0]:.1f} -> {ke[-1]:.1f}")
    print(f"top-level zonal-mean T: mean(last {a.last_days:.0f} d) {ttop[sel].mean():.1f} K, trend {trend:+.3f} K/day")
    print(f"T range:                min {min(tmin):.1f} K  max {max(tmax):.1f} K")

    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(day, ps); ax[0, 0].set_title("global-mean surface pressure [hPa]")
    ax[0, 1].plot(day, ke); ax[0, 1].set_title("global mass-weighted KE [J/kg]")
    ax[1, 0].plot(day, ttop); ax[1, 0].set_title(f"top-level zonal-mean T [K]  (trend last {a.last_days:.0f} d: {trend:+.3f} K/day)")
    ax[1, 1].plot(day, tmin, label="min"); ax[1, 1].plot(day, tmax, label="max"); ax[1, 1].legend(); ax[1, 1].set_title("global T min / max [K]")
    for x in ax.ravel():
        x.set_xlabel("day"); x.grid(alpha=0.3)
    fig.suptitle(a.rundir)
    fig.tight_layout(); fig.savefig(a.out_png, dpi=130)
    print("wrote", a.out_png)


if __name__ == "__main__":
    main()
