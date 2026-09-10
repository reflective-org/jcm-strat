#!/usr/bin/env python3
"""Phase 10 production-tracer diagnostics of a 6-hourly run: pulses, steady tracers, clocks, omega.

    python scripts/pulse_diagnostics.py runs/<run> <outdir> [--label TEXT] [--stride 4]

Reads every longrun_day*.nc (instantaneous frames, 6-hourly) and writes
  <outdir>/<run>_pulse_burdens.png   mass-weighted global mean of every pulse tracer vs time (log),
                                     with the injections visible as jumps; cell min/max envelope
  <outdir>/<run>_pulse_evolution.png pulse_1 at 30 hPa and its zonal mean at 0, 5, 20, 60 d after
                                     the first injection: the advected shape the ML model is to learn
  <outdir>/<run>_steady_clocks.png   n2o / cfc11 zonal means (last frame) against the WACCM initial
                                     state, the three clocks' zonal means, burden time series
  <outdir>/<run>_omega.png           omega: level-wise global mean and std (last frame), 30 hPa map
  <outdir>/<run>_pulse_metrics.md    the numbers: first-frame RMSE of each pulse vs its analytic
                                     target, burden after each injection, monotone decay check,
                                     range, steady-tracer drift, clock ordering, omega sanity
Time series use every ``--stride``-th frame (default 4 = daily); maps use single frames. Mass
weights are the hybrid layer thickness and the Gaussian quadrature weights (scripts/tracer_budget.py).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tracer_budget import P0, gauss_weights, install_level_table, layer_dp  # noqa: E402

PULSES = tuple(f"pulse_{i}" for i in range(1, 6))
REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jcm_strat", "data", "waccm_tracer_ref.nc")


def frames(rundir):
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not files:
        raise SystemExit("no longrun_day*.nc in " + rundir)
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]; starts = [0] + ends[:-1]
    days = []
    for f, s0, s1 in zip(files, starts, ends):
        with xr.open_dataset(f, decode_times=False) as d:
            n = d.sizes["time"]
        days.extend(s0 + (s1 - s0) / n * (j + 1) for j in range(n))
    return files, np.asarray(days)


def analytic_target(name, lat, lon, p_hpa, term):
    """The blob the term injects, on the file's (lev, lon, lat) grid, from the term's own parameters."""
    i = int(name.split("_")[1]) - 1
    lat0, lon0, p0, amp = term.pulses[i]
    la, lo = np.deg2rad(lat), np.deg2rad(lon)
    LA, LO = np.meshgrid(la, lo)                                              # (lon, lat)
    cosang = np.sin(LA) * np.sin(np.deg2rad(lat0)) + np.cos(LA) * np.cos(np.deg2rad(lat0)) * np.cos(LO - np.deg2rad(lon0))
    theta = np.arccos(np.clip(cosang, -1, 1))
    zeta = np.log10(p_hpa / 1000.0)
    return amp * np.exp(-0.5 * (theta / term.sigma_h) ** 2)[None] * np.exp(-0.5 * ((zeta - np.log10(p0 / 1000.0)) / term.sigma_z) ** 2)[:, None, None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir"); ap.add_argument("--label", default=""); ap.add_argument("--stride", type=int, default=4)
    a = ap.parse_args()
    run = os.path.basename(a.rundir.rstrip("/")); os.makedirs(a.outdir, exist_ok=True)
    install_level_table(a.rundir)
    os.environ.setdefault("JAX_PLATFORMS", "cpu")
    from jcm_strat.advection_tracers import ProductionTracers
    term = ProductionTracers()
    files, day = frames(a.rundir)
    ds = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False)
    names = [k for k in PULSES if k in ds]; steady = [k for k in ("n2o", "cfc11") if k in ds]; clocks = [k for k in ("aoa", "aoa150", "aoa_sfc") if k in ds]
    lat = np.asarray(ds.lat); lon = np.asarray(ds.lon); w = gauss_weights(lat)
    p_nom = np.asarray(ds.level) * P0 / 100.0                                  # hPa, file order
    k30 = int(np.argmin(np.abs(p_nom - 30.0)))
    sel = np.arange(a.stride - 1, ds.sizes["time"], a.stride); tday = day[sel]
    lines = [f"# {a.label or run}: production-tracer metrics", "", f"frames: {ds.sizes['time']} (every {np.median(np.diff(day)) * 24:.0f} h), day {day[-1]:.1f}; time series every {a.stride} frames", ""]

    # ---- burdens (mass-weighted global mean mixing ratio) and extremes
    burden = {k: np.zeros(sel.size) for k in names + steady + clocks}; qmin = {k: np.zeros(sel.size) for k in names}; qmax = {k: np.zeros(sel.size) for k in names}
    for j, i in enumerate(sel):
        nsp = np.asarray(ds.normalized_surface_pressure.isel(time=i)); wgt = layer_dp(ds.sizes["level"], nsp) * w[None, None, :]; M = wgt.sum()
        for k in burden:
            q = np.asarray(ds[k].isel(time=i)); burden[k][j] = (q * wgt).sum() / M
            if k in names: qmin[k][j], qmax[k][j] = q.min(), q.max()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for k in names:
        axes[0].plot(tday, burden[k], label=k); axes[1].plot(tday, qmax[k], label=f"{k} max"); axes[1].plot(tday, qmin[k], ":", label=f"{k} min")
    axes[0].set_yscale("log"); axes[0].set_title("pulse tracers: global-mean mixing ratio (jumps = injections)"); axes[0].legend(fontsize=7)
    axes[1].set_yscale("symlog", linthresh=1e-6); axes[1].set_title("pulse tracers: cell extremes"); axes[1].legend(fontsize=6, ncol=2)
    for ax in axes: ax.set_xlabel("day")
    fig.suptitle(a.label or run); fig.tight_layout(); f = os.path.join(a.outdir, f"{run}_pulse_burdens.png"); fig.savefig(f, dpi=130); print("wrote", f)
    lines += ["## pulses", "", "| tracer | amplitude | first-frame RMSE vs target / amp | burden after 1st injection | min over run | max over run | decay monotone between injections |", "|---|---|---|---|---|---|---|"]
    nsp0 = np.asarray(ds.normalized_surface_pressure.isel(time=0))
    for k in names:
        amp = term.pulses[int(k.split("_")[1]) - 1][3]
        q0 = np.asarray(ds[k].isel(time=0)); tgt = analytic_target(k, lat, lon, p_nom * nsp0.mean(), term)
        rmse = float(np.sqrt(np.mean((q0 - tgt) ** 2))) / amp
        b = burden[k]; jumps = np.where(np.diff(b) > 0.2 * b[:-1].max())[0]
        seg_ok = all(np.all(np.diff(b[s + 1:e + 1]) <= 1e-9 * b.max()) for s, e in zip([-1, *jumps], [*jumps, b.size - 1]))
        lines.append(f"| {k} | {amp} | {rmse:.3f} | {b[0]:.3e} | {qmin[k].min():.2e} | {qmax[k].max():.3f} | {'yes' if seg_ok else 'NO'} ({jumps.size} injections seen) |")
    # ---- pulse_1 evolution
    if "pulse_1" in ds:
        offs = [0, 5, 20, 60]; fig, axes = plt.subplots(2, len(offs), figsize=(4.2 * len(offs), 7))
        for c, off in enumerate(offs):
            i = int(np.argmin(np.abs(day - (day[0] + off)))); q = np.asarray(ds["pulse_1"].isel(time=i))
            m = axes[0, c].pcolormesh(lon, lat, q[k30].T, vmin=0, vmax=max(q[k30].max(), 1e-3), cmap="magma_r", shading="auto"); fig.colorbar(m, ax=axes[0, c])
            axes[0, c].set_title(f"pulse_1 at {p_nom[k30]:.0f} hPa, day {day[i]:.2f}")
            z = q.mean(axis=1); m = axes[1, c].contourf(lat, p_nom, z, levels=np.linspace(0, max(z.max(), 1e-3), 11), cmap="magma_r"); fig.colorbar(m, ax=axes[1, c])
            axes[1, c].set_yscale("log"); axes[1, c].set_ylim(1000, 0.01); axes[1, c].set_title("zonal mean")
        fig.suptitle(f"{a.label or run}: advection of pulse_1 after the first injection"); fig.tight_layout()
        f = os.path.join(a.outdir, f"{run}_pulse_evolution.png"); fig.savefig(f, dpi=120); print("wrote", f)
    # ---- steady tracers and clocks
    fig, axes = plt.subplots(2, 3, figsize=(15, 8)); ref = xr.open_dataset(REF) if os.path.exists(REF) else None
    for c, k in enumerate(steady[:2]):
        z = np.asarray(ds[k].isel(time=-1)).mean(axis=1); lv = np.linspace(0, 1, 11)
        m = axes[0, c].contourf(lat, p_nom, z, levels=lv, cmap="Blues"); fig.colorbar(m, ax=axes[0, c])
        if ref is not None: axes[0, c].contour(ref.lat, ref.lev, ref[f"{k}_q0"].T if ref[f"{k}_q0"].dims[0] == "lat" else ref[f"{k}_q0"], levels=lv[1:-1], colors="r", linewidths=0.6)
        axes[0, c].set_title(f"{k} zonal mean, day {day[-1]:.0f} (red: WACCM initial state)")
        lines.append(f"\n{k}: burden first/last {burden[k][0]:.4f} / {burden[k][-1]:.4f}; last-frame min/max {float(ds[k].isel(time=-1).min()):.2e} / {float(ds[k].isel(time=-1).max()):.4f}")
    ax = axes[0, 2]
    for k in steady: ax.plot(tday, burden[k], label=k)
    ax.set_title("steady tracers: global-mean mixing ratio"); ax.legend(); ax.set_xlabel("day")
    for c, k in enumerate(clocks[:3]):
        z = np.asarray(ds[k].isel(time=-1)).mean(axis=1) / 365.25
        m = axes[1, c].contourf(lat, p_nom, z, levels=np.linspace(0, max(0.5, z.max()), 11), cmap="viridis"); fig.colorbar(m, ax=axes[1, c], label="yr")
        axes[1, c].set_title(f"{k} zonal mean (yr), day {day[-1]:.0f}")
    for ax in list(axes[0, :2]) + list(axes[1]): ax.set_yscale("log"); ax.set_ylim(1000, 0.01); ax.axhline(150, color="grey", ls=":", lw=0.8)
    fig.suptitle(a.label or run); fig.tight_layout(); f = os.path.join(a.outdir, f"{run}_steady_clocks.png"); fig.savefig(f, dpi=120); print("wrote", f)
    if {"aoa", "aoa150", "aoa_sfc"} <= set(clocks):
        A, A150, ASF = (np.asarray(ds[k].isel(time=-1)) for k in ("aoa", "aoa150", "aoa_sfc"))
        lines.append(f"\nclocks (last frame): aoa150 <= aoa in {(A150 <= A + 1e-3).mean():.1%} of cells, aoa <= aoa_sfc in {(A <= ASF + 1e-3).mean():.1%}; "
                     f"global means {burden['aoa'][-1] / 365.25:.2f} / {burden['aoa150'][-1] / 365.25:.2f} / {burden['aoa_sfc'][-1] / 365.25:.2f} yr (aoa / aoa150 / aoa_sfc)")
    # ---- omega
    if "omega" in ds:
        om = np.asarray(ds["omega"].isel(time=-1)); mean = (om.mean(axis=1) * w).sum(axis=1); std = np.sqrt(((om ** 2).mean(axis=1) * w).sum(axis=1))
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        axes[0].plot(mean, p_nom, label="global mean"); axes[0].plot(std, p_nom, label="rms"); axes[0].set_yscale("log"); axes[0].set_ylim(1000, 0.01); axes[0].set_xscale("symlog", linthresh=1e-4); axes[0].legend(); axes[0].set_xlabel("Pa/s")
        lim = np.percentile(np.abs(om[k30]), 99); m = axes[1].pcolormesh(lon, lat, om[k30].T, vmin=-lim, vmax=lim, cmap="RdBu_r", shading="auto"); fig.colorbar(m, ax=axes[1], label="Pa/s")
        axes[1].set_title(f"omega at {p_nom[k30]:.0f} hPa, day {day[-1]:.1f}"); fig.suptitle(a.label or run); fig.tight_layout()
        f = os.path.join(a.outdir, f"{run}_omega.png"); fig.savefig(f, dpi=120); print("wrote", f)
        lines.append(f"\nomega (last frame): max |level-mean| / rms = {np.max(np.abs(mean) / np.maximum(std, 1e-12)):.3f}; rms at {p_nom[k30]:.0f} hPa {std[k30]:.2e} Pa/s")
    f = os.path.join(a.outdir, f"{run}_pulse_metrics.md"); open(f, "w").write("\n".join(lines) + "\n"); print("wrote", f); print("\n".join(lines))


if __name__ == "__main__":
    main()
