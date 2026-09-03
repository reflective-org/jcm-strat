#!/usr/bin/env python3
"""Age of air: model vs CLaMS (ERA5-driven) and WACCM6 REF-D1, zonal means and profiles.

    python scripts/aoa_vs_clams.py runs/<session> <outdir> --years 2005-2009 [--label TEXT]

Model: zonal-mean ``aoa`` (days -> years) averaged over the last 12 saves (the final year).
CLaMS: /data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip, ``AGE`` (years) on month x press x lat,
       annual mean over the requested years. CLaMS' clock increases linearly at the Earth's
       surface, so it is the like-for-like reference for our clock (reset below 700 hPa).
WACCM: /data/CESM2_REFD1_AOA/...AOA1mf...nc, ``AOA`` (years) relative to a base point at
       0.47 deg N, 103 hPa — a *stratospheric entry* age, so it reads ~0.3-0.5 yr younger than a
       surface clock everywhere; shown for the pattern, not the level. Values below the base
       point are negative and masked.

Writes <outdir>/<run>_aoa_triptych.png (three zonal-mean panels, one colour scale) and
<outdir>/<run>_aoa_profiles.png (latitude profiles at ~55 hPa (20 km) and ~12 hPa (30 km),
tropical vertical profile), and prints the numbers used in the acceptance table.
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

CLAMS_ZIP = "/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip"
WACCM = "/data/CESM2_REFD1_AOA/AoA_waccm6_refd1.04_AOA1mf_1970-2019_ba_0_100.0_ck_0_50.0.nc"
P0 = 1013.25


def model_age(rundir: str, last_saves: int = 12):
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")),
                   key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False, data_vars=["aoa"])
    n = min(last_saves, ds.sizes["time"])
    age = ds["aoa"].isel(time=slice(-n, None)).mean(("time", "lon")).values / 365.25   # (lev, lat), years
    return np.asarray(ds.level) * P0, np.asarray(ds.lat), age, int(re.search(r"_day(\d+)", files[-1]).group(1))


def clams_age(years):
    ages = []
    with zipfile.ZipFile(CLAMS_ZIP) as z:
        for y in years:
            name = [n for n in z.namelist() if n.endswith(f"_press_{y}.nc")]
            if not name:
                continue
            ds = xr.open_dataset(io.BytesIO(z.read(name[0])), decode_times=False)
            a = ds["AGE"].where(ds["AGE"] > -1e20).mean("month")
            ages.append(a)
    a = xr.concat(ages, "year").mean("year")
    return np.asarray(a.press), np.asarray(a.lat), a.values          # (press, lat)


def waccm_age(years):
    w = xr.open_dataset(WACCM, decode_times=False)
    d = w.date.values
    sel = (d >= years[0] * 10000 + 101) & (d < (years[-1] + 1) * 10000 + 101)
    a = w.AOA.isel(time=np.where(sel)[0]).mean("time")
    a = a.where(a >= 0)
    return np.asarray(w.lev), np.asarray(w.lat), a.values             # (lev, lat)


def band(lat, field_1d, lo, hi):
    m = (np.abs(lat) >= lo) & (np.abs(lat) <= hi)
    wgt = np.cos(np.deg2rad(lat[m]))
    return float(np.nansum(field_1d[m] * wgt) / np.nansum(wgt * ~np.isnan(field_1d[m])))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--label", default="")
    a = ap.parse_args()
    y0, y1 = (int(s) for s in a.years.split("-")); years = list(range(y0, y1 + 1))
    run = os.path.basename(a.rundir.rstrip("/")); os.makedirs(a.outdir, exist_ok=True)

    pm, latm, am, last_day = model_age(a.rundir)
    pc, latc, ac = clams_age(years)
    pw, latw, aw = waccm_age(years)
    vmax = max(1.0, np.ceil(np.nanmax(ac) * 2) / 2)
    levels = np.linspace(0, vmax, int(vmax * 4) + 1)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    for ax, (p, lat, age, title) in zip(axes, [
        (pm, latm, am, f"model {run} (last 12 saves, ends day {last_day})"),
        (pc, latc, ac, f"CLaMS v3.1 / ERA5, {a.years} mean (surface clock)"),
        (pw, latw, aw, f"WACCM6 REF-D1, {a.years} mean (entry age, base 103 hPa)"),
    ]):
        cf = ax.contourf(lat, p, age, levels=levels, cmap="viridis", extend="max")
        ax.contour(lat, p, age, levels=levels[::4], colors="w", linewidths=0.5)
        ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_title(title, fontsize=9); ax.set_xlabel("latitude")
    axes[0].set_ylabel("pressure (hPa)")
    fig.colorbar(cf, ax=axes, label="mean age (yr)", shrink=0.9)
    fig.suptitle(f"{a.label or 'Phase 4'}: age of air, zonal mean")
    f1 = os.path.join(a.outdir, f"{run}_aoa_triptych.png"); fig.savefig(f1, dpi=130, bbox_inches="tight"); print("wrote", f1)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    rows = []
    for ax, ptarget, label in zip(axes[:2], (55.0, 12.0), ("~55 hPa (~20 km)", "~12 hPa (~30 km)")):
        for p, lat, age, name, ls in ((pm, latm, am, "model", "-"), (pc, latc, ac, "CLaMS", "--"), (pw, latw, aw, "WACCM (entry age)", ":")):
            k = int(np.argmin(np.abs(p - ptarget))); prof = age[k]
            ax.plot(lat, prof, ls, label=name)
            rows.append((label, name, band(lat, prof, 0, 10), band(lat, prof, 50, 70)))
        ax.set_title(f"mean age at {label}"); ax.set_xlabel("latitude"); ax.set_ylabel("yr"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax = axes[2]
    for p, lat, age, name, ls in ((pm, latm, am, "model", "-"), (pc, latc, ac, "CLaMS", "--"), (pw, latw, aw, "WACCM (entry age)", ":")):
        m = np.abs(lat) <= 10; prof = np.nanmean(age[:, m], axis=1); ax.plot(prof, p, ls, label=name)
    ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_xlabel("yr"); ax.set_ylabel("pressure (hPa)"); ax.set_title("tropical (10S-10N) profile"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.suptitle(f"{a.label or 'Phase 4'}: age-of-air profiles"); fig.tight_layout()
    f2 = os.path.join(a.outdir, f"{run}_aoa_profiles.png"); fig.savefig(f2, dpi=130); print("wrote", f2)

    print(f"{'level':16s} {'source':20s} {'tropics 10S-10N':>16s} {'50-70 deg':>10s} {'contrast':>9s}")
    for label, name, t, e in rows:
        print(f"{label:16s} {name:20s} {t:16.2f} {e:10.2f} {e - t:9.2f}")


if __name__ == "__main__":
    main()
