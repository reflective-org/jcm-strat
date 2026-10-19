#!/usr/bin/env python3
"""Difference between two runs of the same tracer set (Phase 11 A/B): zonal means and B - A at the last
frame for the tracers that differ, and the global-burden ratio B/A over time for all injected tracers.

    python scripts/ab_diff.py runs/<A> runs/<B> <outdir> [--label TEXT] [--stride 40] [--tracers ...]

Writes <outdir>/<A>_vs_<B>_zonal.png (rows = the --tracers given, else every tracer whose field differs by
more than 1e-3 of its maximum; columns A, B, B - A; keep it to a handful of rows) and <outdir>/<A>_vs_<B>_burden_ratio.png (mass-weighted global mean of
B over A, every --stride frames; tracers within 1e-3 of 1 throughout are drawn in grey).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tracer_budget import P0, gauss_weights, install_level_table, layer_dp  # noqa: E402

INJECTED = tuple(f"pulse_{i}{s}" for i in range(1, 6) for s in ("", "_box")) + tuple(f"src_{i}{s}" for i in range(1, 5) for s in ("", "_box")) + ("sai",)


def files(rundir):
    fs = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not fs:
        raise SystemExit("no longrun_day*.nc in " + rundir)
    return fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_a"); ap.add_argument("run_b"); ap.add_argument("outdir"); ap.add_argument("--label", default="")
    ap.add_argument("--stride", type=int, default=40, help="frames between burden samples (40 = every 10 days of 6-hourly output)")
    ap.add_argument("--tracers", nargs="*", default=None)
    ap.add_argument("--skip-burden", action="store_true", help="only the zonal-mean figure of the last frame")
    a = ap.parse_args()
    na, nb = (os.path.basename(r.rstrip("/")) for r in (a.run_a, a.run_b)); os.makedirs(a.outdir, exist_ok=True)
    install_level_table(a.run_a)
    fa, fb = files(a.run_a), files(a.run_b)
    if len(fa) != len(fb):
        raise SystemExit(f"{na} has {len(fa)} files, {nb} {len(fb)}")
    da = xr.open_mfdataset(fa, combine="nested", concat_dim="time", decode_times=False)
    db = xr.open_mfdataset(fb, combine="nested", concat_dim="time", decode_times=False)
    tracers = [k for k in (a.tracers or INJECTED) if k in da and k in db]
    lat = np.asarray(da.lat); w = gauss_weights(lat); p_nom = np.asarray(da.level) * P0 / 100.0
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in fa]; starts = [0] + ends[:-1]
    day = np.concatenate([s0 + (s1 - s0) / 4 / (s1 - s0) * np.arange(1, 4 * (s1 - s0) + 1) for s0, s1 in zip(starts, ends)])
    # ---- burden ratio over time
    sel = np.arange(a.stride - 1, da.sizes["time"], a.stride); ratio = {k: np.zeros(sel.size) for k in tracers}
    for j, i in enumerate(sel if not a.skip_burden else []):
        wa = layer_dp(da.sizes["level"], np.asarray(da.normalized_surface_pressure.isel(time=i))) * w[None, None, :]
        wb = layer_dp(db.sizes["level"], np.asarray(db.normalized_surface_pressure.isel(time=i))) * w[None, None, :]
        for k in tracers:
            ma = (np.asarray(da[k].isel(time=i)) * wa).sum(); mb = (np.asarray(db[k].isel(time=i)) * wb).sum()
            ratio[k][j] = mb / ma if ma > 0 else np.nan
        if j % 20 == 0: print(f"  burden sample {j + 1}/{sel.size}", flush=True)
    changed = [k for k in tracers if np.nanmax(np.abs(ratio[k] - 1)) > 1e-3]
    if a.skip_burden: changed = []
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for k in tracers:
        if k in changed: ax.plot(day[sel], ratio[k], label=f"{k} (last {ratio[k][-1]:.3f})")
        else: ax.plot(day[sel], ratio[k], color="0.75", lw=0.8)
    ax.axhline(1, color="k", lw=0.6); ax.set_xlabel("day"); ax.set_ylabel(f"global mass {nb} / {na}")
    ax.set_title(f"{a.label or na + ' vs ' + nb}: mass ratio of every injected tracer (grey: within 1e-3 of 1 throughout)", fontsize=10); ax.legend(fontsize=8)
    fig.tight_layout(); f = os.path.join(a.outdir, f"{na}_vs_{nb}_burden_ratio.png")
    if not a.skip_burden: fig.savefig(f, dpi=130); print("wrote", f)
    plt.close(fig)
    # ---- zonal means at the last frame for the tracers whose fields differ
    za = {k: np.asarray(da[k].isel(time=-1)).mean(axis=1) for k in tracers}; zb = {k: np.asarray(db[k].isel(time=-1)).mean(axis=1) for k in tracers}
    rows = [k for k in tracers if a.tracers or np.abs(zb[k] - za[k]).max() > 1e-3 * max(za[k].max(), 1e-30)]
    if not rows:
        print("no tracer's zonal mean differs by more than 1e-3 of its maximum"); return
    fig, axes = plt.subplots(len(rows), 3, figsize=(15, 3.6 * len(rows)), squeeze=False)
    for r, k in enumerate(rows):
        vmax = max(za[k].max(), zb[k].max()); norm = mcolors.LogNorm(vmin=vmax * 1e-4, vmax=vmax)
        for c, (z, name) in enumerate(((za[k], na), (zb[k], nb))):
            m = axes[r, c].pcolormesh(lat, p_nom, np.maximum(z, norm.vmin), norm=norm, cmap="magma_r", shading="auto"); fig.colorbar(m, ax=axes[r, c])
            axes[r, c].set_title(f"{k}: {name}, day {day[-1]:.0f} (log)", fontsize=9)
        d = zb[k] - za[k]; lim = np.abs(d).max()
        m = axes[r, 2].pcolormesh(lat, p_nom, d, vmin=-lim, vmax=lim, cmap="RdBu_r", shading="auto"); fig.colorbar(m, ax=axes[r, 2])
        axes[r, 2].set_title(f"{k}: {nb} - {na} (max |diff| {lim:.2e} = {lim / vmax:.1%} of max)", fontsize=9)
        for ax in axes[r]: ax.set_yscale("log"); ax.set_ylim(1000, 0.01); ax.axhline(1.0, color="c", ls="--", lw=0.8)
    axes[-1, 1].set_xlabel("latitude"); axes[0, 0].set_ylabel("pressure (hPa)")
    fig.suptitle(f"{a.label or na + ' vs ' + nb}: zonal means of the tracers that differ (dashed: the 1 hPa lid)", fontsize=11); fig.tight_layout(rect=(0, 0, 1, 0.985))
    f = os.path.join(a.outdir, f"{na}_vs_{nb}_zonal.png"); fig.savefig(f, dpi=120); print("wrote", f)
    print("tracers differing at the last frame:", rows); print("burden ratio at the end:", {k: round(float(ratio[k][-1]), 4) for k in changed})


if __name__ == "__main__":
    main()
