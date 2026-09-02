#!/usr/bin/env python3
"""Zonal-mean temperature and zonal wind (latitude x log-pressure) from a jcm output file.

    python scripts/plot_zonal_mean.py runs/<session>/longrun_day10.nc out.png [--title TEXT]

Phase-0 version: model only, last time slice, the full column from the surface to the lid.
Pressure on the y axis is the level's reference pressure (sigma-like coordinate x 1013.25 hPa),
which is exact where the hybrid coordinate is pure pressure (the stratosphere) and approximate
near the surface — good enough for a sanity check of the vertical structure. ERA5 comparison
panels are added in Phase 1.
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr


def zonal_mean(ds: xr.Dataset, var: str) -> xr.DataArray:
    da = ds[var]
    if "time" in da.dims:
        da = da.isel(time=-1)
    return da.mean("lon")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ncfile")
    ap.add_argument("out_png")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    ds = xr.open_dataset(a.ncfile, decode_times=False)
    p_hpa = np.asarray(ds["level"]) * 1013.25
    lat = np.asarray(ds["lat"])
    T = zonal_mean(ds, "temperature").transpose("level", "lat")
    U = zonal_mean(ds, "u_wind").transpose("level", "lat")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    cf = axes[0].contourf(lat, p_hpa, T, levels=np.arange(180, 321, 10), cmap="RdYlBu_r", extend="both")
    fig.colorbar(cf, ax=axes[0], label="K")
    axes[0].set_title("zonal-mean temperature")
    lev = np.arange(-80, 81, 10)
    cf = axes[1].contourf(lat, p_hpa, U, levels=lev, cmap="RdBu_r", extend="both")
    axes[1].contour(lat, p_hpa, U, levels=[0], colors="k", linewidths=0.6)
    fig.colorbar(cf, ax=axes[1], label="m/s")
    axes[1].set_title("zonal-mean zonal wind")
    for ax in axes:
        ax.set_yscale("log")
        ax.set_ylim(p_hpa.max(), max(p_hpa.min(), 1e-2))
        ax.set_xlabel("latitude")
        ax.axhline(150, color="grey", ls=":", lw=0.8)  # the AIDE-SAI-link domain boundary
    axes[0].set_ylabel("reference pressure (hPa)")
    fig.suptitle(a.title or a.ncfile)
    fig.tight_layout()
    fig.savefig(a.out_png, dpi=130)
    print("wrote", a.out_png)


if __name__ == "__main__":
    main()
