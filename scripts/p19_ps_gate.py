"""Phase 19b precision gate: hemispheric surface-pressure asymmetry and global-mean ps drift over ~30 days.

jcm #892: with dinosaur 1.5's bf16 dots miscompiled (jaxlib < 0.11.2) the single-level inverse transform of
log ps carries a fixed error pattern every step, which integrates into a NH -> SH mass drift (-116 hPa NH-SH in
30 d on HS T63L47; +0.03 hPa with the HIGHEST override). With terrain and ERA5 nudging the NH-SH area-mean ps
is not zero (orography, season), so the gate is on its CHANGE from the first sample, and on the change of the
global mean. Thresholds: |dA| < 5 hPa (old jcm, p13jhn400 January 1990: max |dA| 2.2 hPa of natural NH-SH mass exchange; the bug is ~20-50x
that), |d global| < 0.5 hPa.

    python scripts/p19_ps_gate.py <new_run_dir> [--ref <old_run_dir>] [--days 31] --out <dir> --tag <tag>

Writes <out>/<tag>_ps_gate.png and <tag>_ps_gate.md; exit status 0 = PASS, 1 = FAIL.
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

P0_PA = 101325.0
LIM_ASYM_HPA = 5.0
LIM_GLOBAL_HPA = 0.5


def series(run_dir: str, days: float):
    files = sorted(glob.glob(os.path.join(run_dir, "longrun_day*.nc")),
                   key=lambda f: int(re.search(r"day(\d+)\.nc", f).group(1)))
    if not files:
        raise FileNotFoundError(f"no longrun_day*.nc in {run_dir}")
    t, nh, sh, gl = [], [], [], []
    t0 = None
    for f in files:
        with xr.open_dataset(f) as ds:
            ps = ds["normalized_surface_pressure"].astype("float64") * P0_PA / 100.0      # hPa, (time, lon, lat)
            w = np.cos(np.deg2rad(ds["lat"]))
            zm = ps.mean("lon")
            n = (zm.where(ds.lat > 0) * w).sum("lat") / w.where(ds.lat > 0).sum()
            s = (zm.where(ds.lat < 0) * w).sum("lat") / w.where(ds.lat < 0).sum()
            g = (zm * w).sum("lat") / w.sum()
            times = ds["time"].values
            if t0 is None:
                t0 = times[0]
            el = (times - t0) / np.timedelta64(1, "D")
            t.append(el); nh.append(n.values); sh.append(s.values); gl.append(g.values)
            if el[-1] >= days:
                break
    t, nh, sh, gl = (np.concatenate(x) for x in (t, nh, sh, gl))
    keep = t <= days
    return t[keep], nh[keep], sh[keep], gl[keep]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run")
    ap.add_argument("--ref", default=None, help="old-jcm run of the same physics for context (not gated)")
    ap.add_argument("--days", type=float, default=31.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="p19")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)

    runs = [("new jcm (35dc1997, dinosaur 1.5.0)", a.run)]
    if a.ref:
        runs.append(("old jcm (849893be, dinosaur SL bd99e39)", a.ref))
    res = {}
    for label, d in runs:
        t, n, s, g = series(d, a.days)
        asym = n - s
        res[label] = dict(t=t, dA=asym - asym[0], dG=g - g[0], A0=asym[0], G0=g[0])

    new = res[runs[0][0]]
    max_dA = float(np.max(np.abs(new["dA"]))); end_dA = float(new["dA"][-1])
    max_dG = float(np.max(np.abs(new["dG"]))); end_dG = float(new["dG"][-1])
    ok = max_dA < LIM_ASYM_HPA and max_dG < LIM_GLOBAL_HPA

    fig, axes = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True, constrained_layout=True)
    colors = ["#2a6fdb", "#9a9a9a"]
    for (label, _), c in zip(runs, colors):
        r = res[label]
        axes[0].plot(r["t"], r["dA"], color=c, lw=2, label=label)
        axes[1].plot(r["t"], r["dG"], color=c, lw=2, label=label)
    for ax, lim, name in ((axes[0], LIM_ASYM_HPA, "change of NH - SH area-mean ps [hPa]"),
                          (axes[1], LIM_GLOBAL_HPA, "change of global-mean ps [hPa]")):
        ax.axhline(0, color="#444", lw=0.8)
        for sgn in (1, -1):
            ax.axhline(sgn * lim, color="#c0392b", lw=1, ls="--")
        ax.set_ylabel(name)
        ax.grid(alpha=0.25)
    axes[0].legend(frameon=False, fontsize=9, loc="best")
    axes[0].set_title(f"Phase 19b precision gate ({a.tag}): {'PASS' if ok else 'FAIL'}  "
                      f"(dashed: gate; jcm #892 bug = -116 hPa NH-SH in 30 d)", fontsize=10)
    axes[1].set_xlabel("days since the first 6-hourly sample")
    png = os.path.join(a.out, f"{a.tag}_ps_gate.png")
    fig.savefig(png, dpi=130)

    lines = [f"# Phase 19b precision gate: {a.tag}", "",
             f"Run: `{a.run}`" + (f"; reference (old jcm, context only): `{a.ref}`" if a.ref else ""), "",
             f"Gate: max |change of NH-SH area-mean ps| < {LIM_ASYM_HPA} hPa and max |change of global-mean ps| < {LIM_GLOBAL_HPA} hPa "
             f"over the first {a.days:g} days (jcm #892: buggy -116 hPa NH-SH in 30 d, fixed +0.03 hPa on HS T63L47).", "",
             "| run | NH-SH at start [hPa] | max abs dA | dA at end | global mean at start | max abs dG | dG at end |",
             "|---|---|---|---|---|---|---|"]
    for label, _ in runs:
        r = res[label]
        lines.append(f"| {label} | {r['A0']:.2f} | {np.max(np.abs(r['dA'])):.3f} | {r['dA'][-1]:+.3f} | {r['G0']:.2f} | "
                     f"{np.max(np.abs(r['dG'])):.4f} | {r['dG'][-1]:+.4f} |")
    lines += ["", f"**Result: {'PASS' if ok else 'FAIL'}** (new jcm: max |dA| {max_dA:.3f} hPa, end {end_dA:+.3f}; "
              f"max |dG| {max_dG:.4f} hPa, end {end_dG:+.4f}).", "", f"![ps gate]({os.path.basename(png)})", ""]
    with open(os.path.join(a.out, f"{a.tag}_ps_gate.md"), "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
