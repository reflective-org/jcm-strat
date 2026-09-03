#!/usr/bin/env python3
"""Circulation drivers of age of air: jcm-strat vs a PARADIS long-range rollout.

    python scripts/paradis_circulation.py runs/<session> runs/paradis_<member>/zonal_means.nc <outdir>

PARADIS carries no tracer, so it cannot enter the age-of-air comparison directly. What it does
carry is the circulation that sets the age of air: the zonal-mean temperature and zonal wind
(polar-night jet, QBO) and the zonal-mean vertical velocity (tropical upwelling, the Brewer-
Dobson proxy). This script compares those on PARADIS's 17 pressure levels:

  <run>_vs_paradis_climatology.png  T and u: model (last 12 months), PARADIS (all kept months),
                                    model minus PARADIS
  paradis_upwelling.png             PARADIS zonal-mean omega converted to w = -omega*H/p (mm/s),
                                    annual mean; tropical values printed at 100/70/50/30/20 hPa

and prints the tropical upwelling numbers with the ERA5-based literature range for orientation.
The model has no omega in its output (dycore.compute_omega is off), so the upwelling panel is
PARADIS-only; the model's upwelling is what its age-of-air gradient measures indirectly.
"""
import argparse
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

H_SCALE = 7000.0  # m, for w = -omega * H / p


def model_climatology(rundir: str, last_n: int = 73):
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False, data_vars=["temperature", "u_wind"])
    ds = ds.isel(time=slice(-last_n, None))
    p = np.asarray(ds.level) * 1013.25
    T = ds.temperature.mean(("time", "lon")).values; U = ds.u_wind.mean(("time", "lon")).values
    return p, np.asarray(ds.lat), T, U


def to_levels(field, p_from, p_to):
    """log-p interpolate (nlev, nlat) from surface-first p_from to p_to."""
    order = np.argsort(p_from); lp = np.log(p_from[order]); f = field[order]
    out = np.empty((len(p_to), field.shape[1]))
    for j in range(field.shape[1]):
        out[:, j] = np.interp(np.log(p_to), lp, f[:, j])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("paradis_nc"); ap.add_argument("outdir")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    run = os.path.basename(a.rundir.rstrip("/"))
    pz = xr.open_dataset(a.paradis_nc)
    plev = pz.level.values.astype(float); plat = pz.lat.values
    Tp = pz["T"].mean("time").values; Up = pz["u"].mean("time").values; Wp = pz["omega"].mean("time").values
    t0, t1 = np.datetime_as_string(pz.time.values[0], "D"), np.datetime_as_string(pz.time.values[-1], "D")

    pm, mlat, Tm, Um = model_climatology(a.rundir)
    Tm_i = to_levels(Tm, pm, plev); Um_i = to_levels(Um, pm, plev)
    Tp_i = np.stack([np.interp(mlat, plat, Tp[k]) for k in range(len(plev))]); Up_i = np.stack([np.interp(mlat, plat, Up[k]) for k in range(len(plev))])

    fig, ax = plt.subplots(2, 3, figsize=(15, 8), sharey=True)
    lv_T = np.arange(180, 321, 10); lv_u = np.arange(-60, 61, 10); lv_d = np.arange(-30, 31, 5)
    for i, (F, lv, cmap, lab, title) in enumerate([
            (Tm_i, lv_T, "RdYlBu_r", "K", f"model {run}: zonal-mean T, last 12 months"),
            (Tp_i, lv_T, "RdYlBu_r", "K", f"PARADIS: zonal-mean T, {t0}..{t1}"),
            (Tm_i - Tp_i, lv_d, "RdBu_r", "K", "model minus PARADIS, T")]):
        cf = ax[0, i].contourf(mlat, plev, F, levels=lv, cmap=cmap, extend="both"); fig.colorbar(cf, ax=ax[0, i], label=lab); ax[0, i].set_title(title, fontsize=9)
    for i, (F, lv, cmap, lab, title) in enumerate([
            (Um_i, lv_u, "RdBu_r", "m/s", "model: zonal-mean u"),
            (Up_i, lv_u, "RdBu_r", "m/s", "PARADIS: zonal-mean u"),
            (Um_i - Up_i, lv_d, "RdBu_r", "m/s", "model minus PARADIS, u")]):
        cf = ax[1, i].contourf(mlat, plev, F, levels=lv, cmap=cmap, extend="both"); fig.colorbar(cf, ax=ax[1, i], label=lab); ax[1, i].set_title(title, fontsize=9)
        ax[1, i].contour(mlat, plev, F, levels=[0], colors="k", linewidths=.5)
    for axx in ax.ravel():
        axx.set_yscale("log"); axx.set_ylim(1000, 1); axx.axhline(150, color="grey", ls=":", lw=.8)
    for axx in ax[1]: axx.set_xlabel("latitude")
    for axx in ax[:, 0]: axx.set_ylabel("pressure (hPa)")
    fig.suptitle("Circulation drivers of age of air: jcm-strat (Held-Suarez stratosphere, 2009) vs PARADIS rollout (1996-2000), on PARADIS's 17 levels")
    fig.tight_layout(); f1 = os.path.join(a.outdir, f"{run}_vs_paradis_climatology.png"); fig.savefig(f1, dpi=130); print("wrote", f1)

    # upwelling
    w_mm = -Wp * H_SCALE / (plev[:, None] * 100.0) * 1000.0          # mm/s
    fig, ax = plt.subplots(figsize=(7, 4.5))
    cf = ax.contourf(plat, plev, w_mm, levels=np.linspace(-1.5, 1.5, 16), cmap="RdBu_r", extend="both")
    ax.contour(plat, plev, w_mm, levels=[0], colors="k", linewidths=.5); fig.colorbar(cf, ax=ax, label="mm/s")
    ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_xlabel("latitude"); ax.set_ylabel("pressure (hPa)")
    ax.set_title(f"PARADIS: zonal-mean vertical velocity w = -omega*H/p, {t0}..{t1} mean", fontsize=9)
    fig.tight_layout(); f2 = os.path.join(a.outdir, "paradis_upwelling.png"); fig.savefig(f2, dpi=130); print("wrote", f2)

    trop = np.abs(plat) <= 10
    print("PARADIS tropical (10S-10N) zonal-mean upwelling, all-time mean; ERA5-era literature w* ~0.2-0.4 mm/s at 70 hPa, ~0.3-0.5 at 30 hPa")
    for pp in (100, 70, 50, 30, 20):
        k = int(np.argmin(np.abs(plev - pp))); print(f"  {plev[k]:5.0f} hPa: w = {w_mm[k, trop].mean():+.3f} mm/s  (omega {Wp[k, trop].mean()*1e3:+.3f} mPa/s)")
    jn = int(np.argmin(np.abs(plat - 60.5))); js = int(np.argmin(np.abs(plat + 60.5))); k10 = int(np.argmin(np.abs(plev - 10)))
    u60 = pz["u"].isel(level=k10, lat=jn); u60s = pz["u"].isel(level=k10, lat=js)
    print("PARADIS u(60.5N, 10 hPa): DJF means and days with u<0 (Nov-Mar), per winter")
    tt = pz.time.values.astype("datetime64[D]"); yrs = np.array([int(str(x)[:4]) for x in tt]); mos = np.array([int(str(x)[5:7]) for x in tt])
    for y in range(yrs.min(), yrs.max()):
        djf = ((yrs == y) & (mos == 12)) | ((yrs == y + 1) & (mos <= 2)); nm = ((yrs == y) & (mos >= 11)) | ((yrs == y + 1) & (mos <= 3))
        if djf.sum() < 20: continue
        print(f"  {y}/{y+1}: DJF mean {float(u60.values[djf].mean()):6.1f} m/s   days u<0: {int((u60.values[nm] < 0).sum()):3d}   (60S DJF {float(u60s.values[djf].mean()):5.1f})")
    print(f"PARADIS annual-mean u(60.5N,10hPa) {float(u60.mean()):.1f} m/s; model annual-mean at 60N/10hPa {float(Um_i[k10, int(np.argmin(np.abs(mlat-60)))]):.1f} m/s")


if __name__ == "__main__":
    main()
