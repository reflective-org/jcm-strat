#!/usr/bin/env python3
"""Multi-decade drift of a chunked jcm-strat run: annual-mean age of air, polar vortex and polar-cap T, year by year.

    python scripts/long_run_series.py runs/<session> <outdir> --start 1990-01-01 [--label TEXT] [--recycle-from 2023]

Per output file (10 days of 6-hourly frames) only the few levels used are read: zonal-mean ``aoa_sfc`` (surface clock,
CLaMS convention) and ``aoa150`` (reset below 150 hPa) at ~100, ~55 and ~12 hPa in the tropics (10S-10N) and at 50-70N/S;
zonal-mean u at 60N/60S, 10 hPa; 60-90N/S area-weighted T at 50 hPa. Annual means are plotted against the year with
CLaMS (ERA5-driven, surface clock) for every year it covers, so the model's age trend can be read against CLaMS' own.
``--recycle-from`` marks the year from which the run is nudged to recycled ERA5. Writes <outdir>/<run>_series.png,
<outdir>/<run>_series.csv and prints the per-decade means.
"""
from __future__ import annotations

import argparse, datetime as dt, glob, io, os, re, sys, zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from aoa_vs_clams import CLAMS_ZIP  # noqa: E402

P0 = 1013.25
LEVELS = {"100": 100.0, "55": 55.0, "12": 12.0}
BANDS = {"tropics": (-10, 10), "50-70N": (50, 70), "50-70S": (-70, -50)}


def band(lat, f, lo, hi):
    m = (lat >= lo) & (lat <= hi); w = np.cos(np.deg2rad(lat[m]))
    return float((f[..., m] * w).sum(-1) / w.sum())


def read_file(path, kk, k10, k50, lat):
    """Time-mean diagnostics of one output file."""
    out = {}
    with netCDF4.Dataset(path) as d:
        for v in ("aoa_sfc", "aoa150"):
            a = d.variables[v][:, kk, :, :].mean(axis=(0, 2)) / 365.25            # (lev, lat), years
            for i, key in enumerate(LEVELS):
                for b, (lo, hi) in BANDS.items():
                    out[f"{v}_{key}_{b}"] = band(lat, a[i], lo, hi)
        u = d.variables["u_wind"][:, k10, :, :].mean(axis=(0, 1))                 # (lat,)
        out["u10_60N"] = float(np.interp(60, lat, u)); out["u10_60S"] = float(np.interp(-60, lat, u))
        t = d.variables["temperature"][:, k50, :, :].mean(axis=(0, 1))
        out["T50_cap_N"] = band(lat, t, 60, 90); out["T50_cap_S"] = band(lat, t, -90, -60)
        out["n"] = d.dimensions["time"].size
    return out


def clams_series():
    """CLaMS annual-mean AGE at the same levels and bands, {year: {key: value}}."""
    res = {}
    with zipfile.ZipFile(CLAMS_ZIP) as z:
        for name in z.namelist():
            m = re.search(r"_press_(\d{4})\.nc$", name)
            if not m:
                continue
            import xarray as xr
            ds = xr.open_dataset(io.BytesIO(z.read(name)), decode_times=False)
            a = ds["AGE"].where(ds["AGE"] > -1e20).mean("month")
            p = np.asarray(a.press); lat = np.asarray(a.lat); r = {}
            for key, pp in LEVELS.items():
                row = a.isel(press=int(np.argmin(np.abs(p - pp)))).values
                for b, (lo, hi) in BANDS.items():
                    msk = (lat >= lo) & (lat <= hi) & np.isfinite(row); w = np.cos(np.deg2rad(lat[msk]))
                    r[f"{key}_{b}"] = float((row[msk] * w).sum() / w.sum())
            res[int(m.group(1))] = r
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir")
    ap.add_argument("--start", default="1990-01-01"); ap.add_argument("--label", default=None)
    ap.add_argument("--recycle-from", type=int, default=None)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    run = os.path.basename(a.rundir.rstrip("/")); label = a.label or run
    files = sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]; starts = [0] + ends[:-1]
    with netCDF4.Dataset(files[0]) as d:
        p = np.asarray(d.variables["level"][:]) * P0; lat = np.asarray(d.variables["lat"][:])
    kk = [int(np.argmin(np.abs(p - v))) for v in LEVELS.values()]
    k10 = int(np.argmin(np.abs(p - 10))); k50 = int(np.argmin(np.abs(p - 50)))
    print(f"{len(files)} files; levels {[round(float(p[k]), 1) for k in kk]} hPa, u at {p[k10]:.1f}, T at {p[k50]:.1f} hPa", flush=True)

    t0 = dt.date.fromisoformat(a.start); rows = []
    for i, (f, s0, s1) in enumerate(zip(files, starts, ends)):
        r = read_file(f, kk, k10, k50, lat)
        r["year"] = (t0 + dt.timedelta(days=(s0 + s1) / 2)).year; rows.append(r)
        if i % 100 == 0:
            print(f"  {i}/{len(files)} {r['year']}", flush=True)
    keys = [k for k in rows[0] if k not in ("year", "n")]
    years = sorted({r["year"] for r in rows})
    ann = {y: {k: np.average([r[k] for r in rows if r["year"] == y], weights=[r["n"] for r in rows if r["year"] == y]) for k in keys}
           for y in years}
    with open(os.path.join(a.outdir, f"{run}_series.csv"), "w") as fh:
        fh.write("year," + ",".join(keys) + "\n")
        for y in years:
            fh.write(f"{y}," + ",".join(f"{ann[y][k]:.4f}" for k in keys) + "\n")
    cl = clams_series(); cy = sorted(cl)

    Y = np.array(years)
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.5), constrained_layout=True)
    for j, b in enumerate(BANDS):
        x = ax[0, j]
        for key, c in zip(LEVELS, ("C2", "C0", "C3")):
            x.plot(Y, [ann[y][f"aoa_sfc_{key}_{b}"] for y in years], color=c, lw=2, label=f"model {key} hPa")
            x.plot(Y, [ann[y][f"aoa150_{key}_{b}"] for y in years], color=c, lw=1, ls=":", label=f"model {key} hPa, 150 hPa clock")
            x.plot(cy, [cl[y][f"{key}_{b}"] for y in cy], color=c, lw=1.4, ls="--", label=f"CLaMS {key} hPa")
        x.set_title(f"age of air, {b}"); x.set_ylabel("years")
    ax[0, 0].legend(fontsize=7, ncol=3, loc="upper left")
    x = ax[1, 0]
    x.plot(Y, [ann[y]["u10_60N"] for y in years], label="60N"); x.plot(Y, [ann[y]["u10_60S"] for y in years], label="60S")
    x.set_title("annual-mean zonal-mean u, 10 hPa"); x.set_ylabel("m/s"); x.legend(fontsize=8)
    x = ax[1, 1]
    x.plot(Y, [ann[y]["T50_cap_N"] for y in years], label="60-90N"); x.plot(Y, [ann[y]["T50_cap_S"] for y in years], label="60-90S")
    x.set_title("annual-mean polar-cap T, 50 hPa"); x.set_ylabel("K"); x.legend(fontsize=8)
    x = ax[1, 2]
    for b, c in zip(BANDS, ("k", "C0", "C3")):
        x.plot(Y, [ann[y][f"aoa_sfc_55_{b}"] - ann[y][f"aoa150_55_{b}"] for y in years], color=c, label=b)
    x.set_title("surface clock minus 150 hPa clock, 55 hPa"); x.set_ylabel("years"); x.legend(fontsize=8)
    for x in ax.flat:
        x.grid(alpha=.3)
        if a.recycle_from:
            x.axvline(a.recycle_from, color="grey", lw=1, ls="-.")
    if a.recycle_from:
        ax[1, 0].text(a.recycle_from + 0.3, ax[1, 0].get_ylim()[1], " recycled ERA5 ->", va="top", fontsize=8, color="grey")
    fig.suptitle(f"{label}: annual means {years[0]}-{years[-1]}")
    fig.savefig(os.path.join(a.outdir, f"{run}_series.png"), dpi=120)

    print("\ndecade means:")
    show = ["aoa_sfc_55_tropics", "aoa_sfc_55_50-70N", "aoa_sfc_12_tropics", "aoa_sfc_12_50-70N", "aoa150_55_tropics", "u10_60N", "u10_60S",
            "T50_cap_N", "T50_cap_S"]
    print("years      " + " ".join(f"{k:>18}" for k in show))
    for d0 in range(years[0], years[-1] + 1, 10):
        ys = [y for y in years if d0 <= y < d0 + 10]
        print(f"{ys[0]}-{ys[-1]}  " + " ".join(f"{np.mean([ann[y][k] for y in ys]):18.2f}" for k in show))
    print("CLaMS 55 hPa tropics/50-70N, 12 hPa tropics/50-70N, first/last years:",
          [(y, round(cl[y]['55_tropics'], 2), round(cl[y]['55_50-70N'], 2), round(cl[y]['12_tropics'], 2), round(cl[y]['12_50-70N'], 2)) for y in (cy[0], cy[-1])])


if __name__ == "__main__":
    main()
