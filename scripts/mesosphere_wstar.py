#!/usr/bin/env python3
"""Phase 13: is the mesosphere ventilated? The residual circulation above 10 hPa of one or more runs, side by side.

    python scripts/mesosphere_wstar.py --out docs/outputs/13_gwd --tag meso \
        runs/p12ctl_19940101:"dry control" runs/p13gwd_19940101:"+ GWD" runs/p13gwdl77_19940101:"+ GWD, strat77" \
        [--stride 4] [--clock aoa150] [--reference runs/p12echam_19940101:"full ECHAM"]

Reproduces the table of the Phase 12 addendum (docs/outputs/12_circulation/output.md, 2026-09-22): the TEM residual
vertical velocity w* (scripts/strat_circulation.py: Psi* from v* = [v] - d/dp([v'th']/d[th]/dp), w* = -H omega*/p) from
every ``--stride``-th frame of the given run directories (one calendar-year segment each, e.g. the 1994 segment),
annual mean, cos-weighted over the tropics 15S-15N and the polar caps 60-90 (NH, SH), at 10 / 5 / 2 / 1 / 0.5 / 0.3 hPa,
mm/s, upward positive; and the latitude standard deviation of the entry-age clock (``--clock``, default aoa150) at 3
and 1.5 hPa over the last 60 days (a flat age in latitude just below the 1 hPa tracer lid means lid-valued air is
being pushed DOWN into the stratosphere instead of the stratosphere being ventilated upward; the clocks themselves
are relaxed to WACCM above the lid and cannot measure the mesosphere - the dynamics have to).

Writes <out>/<tag>_mesosphere.md (the table) and <out>/<tag>_mesosphere.png (tropical w* profile 100-0.1 hPa per run,
and each run's annual w*(lat, p) above 30 hPa).
"""
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
import strat_circulation as circ  # noqa: E402

LEVELS_HPA = (10.0, 5.0, 2.0, 1.0, 0.5, 0.3)
BANDS = {"tropics 15S-15N": (-15.0, 15.0), "NH 60-90": (60.0, 90.0), "SH 60-90": (-90.0, -60.0)}
P0_HPA = 1013.25


def band_mean(w_row, lat, lo, hi):
    m = (lat >= lo) & (lat <= hi) & np.isfinite(w_row)
    wgt = np.cos(np.deg2rad(lat[m]))
    return float(np.sum(w_row[m] * wgt) / np.sum(wgt)) if m.any() else np.nan


def annual_wstar(rundir, stride):
    V, VTH, TH = circ.model_tem_fields(rundir, stride=stride)
    p, vstar, psi = circ.tem_streamfunction(V.mean("time").values, VTH.mean("time").values, TH.mean("time").values,
                                            V.level.values, V.lat.values)
    return p, V.lat.values, circ.residual_w(p, psi, V.lat.values)


def clock_lat_std(rundir, var, last_saves):
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))
    frames, n = [], 0
    for f in reversed(files):
        d = xr.open_dataset(f, decode_times=False)
        if var not in d:
            return {}
        frames.insert(0, d[var].mean("lon")); n += d.sizes["time"]
        if n >= last_saves:
            break
    a = xr.concat(frames, "time").isel(time=slice(-last_saves, None)).mean("time") / 365.25   # (level, lat), yr
    p = a.level.values * P0_HPA
    out = {}
    for ph in (3.0, 1.5):
        i = int(np.argmin(np.abs(p - ph)))
        row = a.isel(level=i).values; m = np.abs(a.lat.values) <= 88
        out[ph] = float(np.std(row[m]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="rundir[:label] (one calendar-year segment or an aggregate)")
    ap.add_argument("--reference", default=None, help="rundir[:label] drawn as a reference (e.g. the full-physics segment)")
    ap.add_argument("--out", required=True); ap.add_argument("--tag", default="meso")
    ap.add_argument("--stride", type=int, default=4, help="every n-th 6-hourly frame (4 = daily)")
    ap.add_argument("--clock", default="aoa150"); ap.add_argument("--last-saves", type=int, default=240)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)

    specs = [(s.split(":", 1)[0], s.split(":", 1)[1] if ":" in s else os.path.basename(s.rstrip("/"))) for s in a.runs]
    ref = None
    if a.reference:
        ref = (a.reference.split(":", 1)[0], a.reference.split(":", 1)[1] if ":" in a.reference else "reference")
    results = []
    for rundir, label in specs + ([ref] if ref else []):
        print(f"[meso] {label}: {rundir} (stride {a.stride})", flush=True)
        p, lat, w = annual_wstar(rundir, a.stride)
        std = clock_lat_std(rundir, a.clock, a.last_saves)
        results.append((rundir, label, p, lat, w, std))

    lines = [f"# Mesosphere check ({a.tag}): annual-mean TEM w* above 10 hPa, mm/s, upward positive", "",
             f"Every {a.stride}th 6-hourly frame of each run directory; bands cos-weighted; `{a.clock}` latitude std over the last "
             f"{a.last_saves} frames (|lat| <= 88). Cells: tropics / NH cap / SH cap.", "",
             "| run | " + " | ".join(f"{lv:g} hPa" for lv in LEVELS_HPA) + f" | `{a.clock}` lat std at 3 / 1.5 hPa [yr] |",
             "|---|" + "---|" * (len(LEVELS_HPA) + 1)]
    for rundir, label, p, lat, w, std in results:
        cells = []
        for lv in LEVELS_HPA:
            i = int(np.argmin(np.abs(p / 100.0 - lv)))
            cells.append(" / ".join(f"{band_mean(w[i], lat, *BANDS[b]):+.2f}" for b in BANDS))
        s = f"{std.get(3.0, np.nan):.2f} / {std.get(1.5, np.nan):.2f}" if std else "-"
        lines.append(f"| {label} (`{os.path.basename(rundir.rstrip('/'))}`) | " + " | ".join(cells) + f" | {s} |")
    md = os.path.join(a.out, f"{a.tag}_mesosphere.md"); open(md, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); print("wrote", md)

    n = len(results)
    fig = plt.figure(figsize=(5.5 + 4.2 * n, 5.5), layout="constrained")
    gs = fig.add_gridspec(1, n + 1, width_ratios=[1.3] + [1] * n)
    ax = fig.add_subplot(gs[0, 0])
    for k, (rundir, label, p, lat, w, _) in enumerate(results):
        prof = np.array([band_mean(w[i], lat, *BANDS["tropics 15S-15N"]) for i in range(p.size)])
        ax.plot(prof, p / 100.0, ("k--" if ref and k == n - 1 else f"C{k}-"), label=label)
    ax.axvline(0, color="grey", lw=0.8); ax.set_yscale("log"); ax.set_ylim(100, 0.1); ax.set_xlim(-2.5, 2.5)
    ax.set_xlabel("tropical w* 15S-15N [mm/s]"); ax.set_ylabel("pressure [hPa]"); ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8)
    ax.set_title("annual mean, tropics")
    lv = np.array([-3, -2, -1, -0.5, -0.2, -0.1, 0.1, 0.2, 0.5, 1, 2, 3])
    for k, (rundir, label, p, lat, w, _) in enumerate(results):
        axk = fig.add_subplot(gs[0, k + 1])
        cf = axk.contourf(lat, p / 100.0, np.clip(w, lv[0], lv[-1]), levels=lv, cmap="RdBu_r", extend="both")
        axk.contour(lat, p / 100.0, w, levels=[0], colors="k", linewidths=0.6)
        axk.set_yscale("log"); axk.set_ylim(30, 0.1); axk.set_title(label, fontsize=10); axk.set_xlabel("latitude")
        if k: axk.set_yticklabels([])
    fig.colorbar(cf, ax=fig.axes[1:], shrink=0.8, pad=0.02, label="w* [mm/s]")
    fig.suptitle(f"{a.tag}: residual vertical velocity above 30 hPa (annual mean)")
    f = os.path.join(a.out, f"{a.tag}_mesosphere.png"); fig.savefig(f, dpi=120); plt.close(fig); print("wrote", f)


if __name__ == "__main__":
    main()
