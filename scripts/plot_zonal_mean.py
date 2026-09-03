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
    ap.add_argument("--era5-tape", default=None,
                    help="zonal-mean ERA5 monthly tape (Uzm, Tzm on level x lat; 7-70 hPa) for a "
                         "stratospheric comparison row; the model is interpolated to its levels")
    ap.add_argument("--months", default="1,2,12", help="months of the tape to average (default DJF)")
    a = ap.parse_args()
    ds = xr.open_dataset(a.ncfile, decode_times=False)
    p_hpa = np.asarray(ds["level"]) * 1013.25
    lat = np.asarray(ds["lat"])
    T = zonal_mean(ds, "temperature").transpose("level", "lat")
    U = zonal_mean(ds, "u_wind").transpose("level", "lat")

    nrows = 2 if a.era5_tape else 1
    fig, axes_all = plt.subplots(nrows, 2, figsize=(12, 5 * nrows), squeeze=False)
    axes = axes_all[0]
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
    if a.era5_tape:
        era = xr.open_dataset(a.era5_tape)
        months = [int(m) for m in a.months.split(",")]
        sel = np.isin(era["month"].values, months)
        Ue = era["Uzm"].isel(time=np.where(sel)[0]).mean("time")
        Te = era["Tzm"].isel(time=np.where(sel)[0]).mean("time")
        plev = era["level"].values
        # model -> the tape's pressure levels (log-p interpolation) and latitudes
        logp = np.log(p_hpa)
        order = np.argsort(logp)
        def to_levels(F):
            out = np.empty((plev.size, lat.size))
            for j in range(lat.size):
                out[:, j] = np.interp(np.log(plev), logp[order], np.asarray(F)[order, j])
            return xr.DataArray(out, dims=("level", "lat"), coords={"level": plev, "lat": lat}).interp(lat=era["lat"])
        dU = to_levels(U) - Ue
        dT = to_levels(T) - Te
        ax2 = axes_all[1]
        cf = ax2[0].contourf(era["lat"], plev, dT, levels=np.arange(-30, 31, 5), cmap="RdBu_r", extend="both")
        fig.colorbar(cf, ax=ax2[0], label="K")
        ax2[0].set_title(f"model - ERA5 zonal-mean T, months {a.months} (tape {era.attrs.get('years','')})")
        cf = ax2[1].contourf(era["lat"], plev, dU, levels=np.arange(-40, 41, 5), cmap="RdBu_r", extend="both")
        ax2[1].contour(era["lat"], plev, Ue, levels=np.arange(-80, 81, 20), colors="k", linewidths=0.5)
        fig.colorbar(cf, ax=ax2[1], label="m/s")
        ax2[1].set_title("model - ERA5 zonal-mean u (contours: ERA5 u)")
        for ax in ax2:
            ax.set_yscale("log"); ax.set_ylim(plev.max(), plev.min()); ax.set_xlabel("latitude")
        ax2[0].set_ylabel("pressure (hPa)")
        rms_T = float(np.sqrt(np.nanmean(dT.values ** 2))); rms_U = float(np.sqrt(np.nanmean(dU.values ** 2)))
        print(f"model - ERA5 over {plev.min():g}-{plev.max():g} hPa: RMS dT = {rms_T:.1f} K, RMS du = {rms_U:.1f} m/s")
    fig.suptitle(a.title or a.ncfile)
    fig.tight_layout()
    fig.savefig(a.out_png, dpi=130)
    print("wrote", a.out_png)


if __name__ == "__main__":
    main()
