#!/usr/bin/env python3
"""Passive-tracer budget and transport diagnostics of a chunked jcm-strat run (Phase 3).

    python scripts/tracer_budget.py runs/<session> <outdir> [--label TEXT]

Reads every longrun_day*.nc (5-day means) and writes
  <outdir>/<run>_tracer_budget.png    burden time series: unity (relative drift), sai (vs the
                                      expected linear growth from its known source), e90, and the
                                      unity min/max envelope
  <outdir>/<run>_tracer_zonal.png     zonal means at the last save: age of air (years), sai, e90
                                      with its 90 contour (the tropopause marker), unity - 1
and prints the acceptance numbers: unity max |deviation|, sai burden drift vs expected, cell
minimum of every tracer, polar-cap top-level sai vs its global-mean column (the pull-up check),
tropical vs extratropical age of air at 20 hPa.

Mass weights are exact: the ECHAM L95 hybrid coefficients (jcm.physics.echam.echam_levels) give
dp per layer from the file's normalized surface pressure, and the Gaussian quadrature weights
of the T63 grid replace cos(lat). Burdens are in kg of tracer per kg... i.e. sum(q dp w)/sum(dp w)
(a mass-weighted global mean mixing ratio), which is what "conservation" means for a mixing ratio
in a model whose total air mass itself moves a little.
"""
from __future__ import annotations

import argparse
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

P0 = 101325.0
TRACERS = ("aoa", "unity", "sai", "e90")


def gauss_weights(lat_deg: np.ndarray) -> np.ndarray:
    nodes, w = np.polynomial.legendre.leggauss(lat_deg.size)
    order_file = np.argsort(np.sin(np.deg2rad(lat_deg)))
    out = np.empty_like(w)
    out[order_file] = w[np.argsort(nodes)]
    return out / out.sum()


def layer_dp(nlev: int, nsp: np.ndarray) -> np.ndarray:
    """dp (Pa) per output layer, surface-first, shape (nlev, lon, lat); nsp = p_s / P0."""
    try:
        os.environ.setdefault("JAX_PLATFORMS", "cpu")
        from jcm.physics.echam.echam_levels import get_echam_levels
        v = get_echam_levels(nlev)
        a = np.asarray(v.a_boundaries, dtype=np.float64)
        b = np.asarray(v.b_boundaries, dtype=np.float64)
        da, db = np.diff(a), np.diff(b)                      # top-first
        dp = da[:, None, None] + db[:, None, None] * (nsp[None] * P0)
        return dp[::-1]                                       # -> surface-first like the file
    except Exception as e:  # noqa: BLE001
        print("WARNING: hybrid table unavailable (%s); using nominal-sigma thickness" % e)
        raise


def load(rundir: str) -> xr.Dataset:
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")),
                   key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not files:
        raise SystemExit("no longrun_day*.nc in " + rundir)
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False,
                           data_vars=[*TRACERS, "normalized_surface_pressure"])
    # each file is one chunk holding several window means; reconstruct the day at the END of
    # every window from the chunk-end day in the filename and the number of saves per file
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]
    starts = [0] + ends[:-1]
    days = []
    for f, s0, s1 in zip(files, starts, ends):
        with xr.open_dataset(f, decode_times=False) as d:
            n = d.sizes["time"]
        step = (s1 - s0) / n
        days.extend(s0 + step * (j + 1) for j in range(n))
    return ds, np.asarray(days, dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir"); ap.add_argument("--label", default="")
    a = ap.parse_args()
    run = os.path.basename(a.rundir.rstrip("/"))
    os.makedirs(a.outdir, exist_ok=True)
    ds, day = load(a.rundir)                                 # day = end of each averaging window
    lat = np.asarray(ds.lat); w = gauss_weights(lat)
    p_nom = np.asarray(ds.level) * P0 / 100.0                # nominal hPa, surface-first
    nt = ds.sizes["time"]
    interval = float(np.median(np.diff(day))) if nt > 1 else float(day[0])
    nsp = np.asarray(ds.normalized_surface_pressure)          # (t, lon, lat)

    burden = {k: np.zeros(nt) for k in TRACERS}
    umin = np.zeros(nt); umax = np.zeros(nt); cellmin = {k: np.inf for k in TRACERS}
    sai_expected = np.zeros(nt)
    box_mass_frac = np.zeros(nt)
    for i in range(nt):
        dp = layer_dp(ds.sizes["level"], nsp[i])               # (lev, lon, lat)
        wgt = dp * w[None, None, :]
        M = wgt.sum()
        for k in TRACERS:
            q = np.asarray(ds[k].isel(time=i))
            burden[k][i] = (q * wgt).sum() / M
            cellmin[k] = min(cellmin[k], float(q.min()))
        u = np.asarray(ds["unity"].isel(time=i)); umin[i], umax[i] = u.min(), u.max()
        # sai source box (jcm_strat.tracers defaults): |lat|<=15, 25<=p<=55 hPa
        p3 = np.broadcast_to(p_nom[:, None, None], dp.shape) * nsp[i][None]
        box = (np.abs(lat)[None, None, :] <= 15.0) & (p3 >= 25.0) & (p3 <= 55.0)
        box_mass_frac[i] = (wgt * box).sum() / M
    # expected sai global-mean mixing ratio: rate * box mass fraction * time (mid-window mean)
    rate = 1e-6 * 86400.0                                    # per day
    t_mid = day - 0.5 * interval                             # the file holds a window mean
    sai_expected = rate * box_mass_frac.mean() * t_mid

    unity_dev = max(abs(umin - 1).max(), abs(umax - 1).max())
    unity_drift = burden["unity"][-1] / burden["unity"][0] - 1
    sai_err = burden["sai"][-1] / sai_expected[-1] - 1
    # pull-up: sai at the top model level over the polar caps vs its global-mean column
    sai_last = np.asarray(ds["sai"].isel(time=-1))            # (lev, lon, lat)
    # the top level is the one with the smallest reference pressure; do not assume a level order
    # (the chained-run aggregates come out top-first and the single runs surface-first)
    top = sai_last[int(np.argmin(np.asarray(ds["level"])))]
    cap = np.abs(lat) > 70
    # zonal mean first: the earlier version summed over longitude without dividing by nlon, so
    # every pull-up number printed before 2026-09-03 was 192x too large (the verdicts still held)
    polar_top = float((top[:, cap].mean(axis=0) * w[cap]).sum() / w[cap].sum())
    global_col = float(burden["sai"][-1])
    aoa_last = np.asarray(ds["aoa"].isel(time=-1)).mean(axis=1) / 365.25   # zonal mean, years (lev, lat)
    k20 = int(np.argmin(np.abs(p_nom - 20.0)))
    trop = np.abs(lat) <= 10; extra = (np.abs(lat) >= 50) & (np.abs(lat) <= 70)
    aoa_trop = float((aoa_last[k20, trop] * w[trop]).sum() / w[trop].sum())
    aoa_extra = float((aoa_last[k20, extra] * w[extra]).sum() / w[extra].sum())

    print(f"run:                      {run}  ({nt} saves, day {day[-1]:.0f})")
    print(f"unity max |q-1| (any cell, any save): {unity_dev:.2e}")
    print(f"unity global burden drift:            {unity_drift:+.2e}")
    print(f"sai burden vs expected (source*box mass*t): {sai_err:+.2%}  (expected {sai_expected[-1]:.3e}, got {burden['sai'][-1]:.3e})")
    print("cell minimum: " + ", ".join(f"{k} {cellmin[k]:.2e}" for k in TRACERS))
    print(f"pull-up check: sai at top level, |lat|>70: {polar_top:.3e} vs global-mean column {global_col:.3e} (ratio {polar_top/global_col if global_col else float('nan'):.3f})")
    print(f"age of air at ~20 hPa, last save: tropics(|lat|<=10) {aoa_trop:.2f} yr, 50-70deg {aoa_extra:.2f} yr, max {aoa_last.max():.2f} yr")

    # --- plot 1: budgets
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    ax = axes[0, 0]; ax.plot(day, (burden["unity"] - 1) * 1e6); ax.set_title("unity: global burden - 1 (ppm)"); ax.set_xlabel("day")
    ax = axes[0, 1]; ax.plot(day, (umax - 1) * 1e3, label="max"); ax.plot(day, (umin - 1) * 1e3, label="min"); ax.legend()
    ax.set_title("unity: cell extremes - 1 (x1e-3)"); ax.set_xlabel("day")
    ax = axes[1, 0]; ax.plot(day, burden["sai"], label="model"); ax.plot(day, sai_expected, "--", label="expected: source x box mass x t")
    ax.legend(); ax.set_title("sai: global-mean mixing ratio"); ax.set_xlabel("day")
    ax = axes[1, 1]; ax.plot(day, burden["e90"]); ax.set_title("e90: global-mean mixing ratio"); ax.set_xlabel("day")
    fig.suptitle(f"{a.label or run}: tracer budgets"); fig.tight_layout()
    f1 = os.path.join(a.outdir, f"{run}_tracer_budget.png"); fig.savefig(f1, dpi=130); print("wrote", f1)

    # --- plot 2: zonal means at the last save
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    def zm(k): return np.asarray(ds[k].isel(time=-1)).mean(axis=1)
    cf = axes[0, 0].contourf(lat, p_nom, aoa_last, levels=np.linspace(0, max(0.5, aoa_last.max()), 11), cmap="viridis")
    fig.colorbar(cf, ax=axes[0, 0], label="yr"); axes[0, 0].set_title("age of air (clock, reset below 700 hPa)")
    s = zm("sai"); cf = axes[0, 1].contourf(lat, p_nom, s, levels=np.linspace(0, max(s.max(), 1e-9), 11), cmap="magma_r")
    fig.colorbar(cf, ax=axes[0, 1]); axes[0, 1].set_title("sai (source 15S-15N, 25-55 hPa)")
    e = zm("e90"); cf = axes[1, 0].contourf(lat, p_nom, e, levels=np.linspace(0, 100, 11), cmap="Blues")
    axes[1, 0].contour(lat, p_nom, e, levels=[90], colors="r", linewidths=1.0)
    fig.colorbar(cf, ax=axes[1, 0]); axes[1, 0].set_title("e90 (red: 90 contour = tropopause marker)")
    d = (zm("unity") - 1) * 1e3; lim = max(1e-3, np.abs(d).max())
    cf = axes[1, 1].contourf(lat, p_nom, d, levels=np.linspace(-lim, lim, 13), cmap="RdBu_r")
    fig.colorbar(cf, ax=axes[1, 1], label="x1e-3"); axes[1, 1].set_title("unity - 1 (local transport error)")
    for ax in axes.ravel():
        ax.set_yscale("log"); ax.set_ylim(1000, 0.01); ax.axhline(150, color="grey", ls=":", lw=0.8)
    for ax in axes[1]: ax.set_xlabel("latitude")
    for ax in axes[:, 0]: ax.set_ylabel("nominal pressure (hPa)")
    fig.suptitle(f"{a.label or run}: zonal means, day {day[-1]:.0f} (5-day mean)"); fig.tight_layout()
    f2 = os.path.join(a.outdir, f"{run}_tracer_zonal.png"); fig.savefig(f2, dpi=130); print("wrote", f2)


if __name__ == "__main__":
    main()
