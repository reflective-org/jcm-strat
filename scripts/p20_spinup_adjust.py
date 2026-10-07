"""Phase 20: was a one-month spin-up enough? Daily global relative angular momentum and 300 hPa zonal wind through the
spin-up month and the first month after it, for several chains side by side.

    python scripts/p20_spinup_adjust.py --out <dir> --tag <tag> \
        "runs/p19jhn400_spinup_19891201,runs/p19jhn400_19900101:no SSO (19d)" \
        "runs/p20jhsso_spinup_19891201,runs/p20jhsso_19900101:fixed Lott-Miller (20)" [--days-after 31]

Each run is "<spin-up dir>,<first segment dir>:<label>". Daily means of the 6-hourly frames (all four phases, so no tidal
aliasing). Quantities:
  M      global relative angular momentum  int u a cos(phi) dp/g dA  [1e25 kg m2/s]  (dp from the hybrid coefficients and ps)
  u300   zonal-mean u at the model level nearest 300 hPa, 25-50N (the band of the Tibetan Plateau / Rockies / Alps) [m/s]
  u300s  the same, 25-50S
The orographic drag's re-adjustment (the colleague: ~4 weeks) shows up as a drift of M and u300 relative to the no-SSO chain;
"enough" = the difference has levelled off before day 31. Writes <tag>_spinup_adjust.png and <tag>_spinup_adjust.md.
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

A = 6.371e6
G = 9.80616
P0 = 101325.0
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#8a5cd6"]


def files(d):
    return sorted(glob.glob(os.path.join(d, "longrun_day*.nc")), key=lambda f: int(re.search(r"day(\d+)\.nc", f).group(1)))


def daily(dirs, days_after):
    out = {"t": [], "M": [], "u300": [], "u300s": []}
    t0 = None
    for k, d in enumerate(dirs):
        for f in files(d):
            with xr.open_dataset(f) as ds:
                times = ds.time.values
                if t0 is None:
                    t0 = times[0]
                el = (times - t0) / np.timedelta64(1, "D")
                if k == 1 and el[0] > 31 + days_after:
                    break
                ps = ds.normalized_surface_pressure.values.astype(np.float64) * P0                 # (t, lon, lat)
                ah = ds.hybrid_a_half.values; bh = ds.hybrid_b_half.values                          # (nlev+1), surface first?
                dp = np.abs(np.diff(ah)[None, :, None, None] + np.diff(bh)[None, :, None, None] * ps[:, None])   # (t, lev, lon, lat)
                u = ds.u_wind.values.astype(np.float64)
                lat = np.deg2rad(ds.lat.values); coslat = np.cos(lat)
                w = coslat / coslat.sum()                                                            # area weights per lat row
                # M = sum u a cos(phi) dp/g * dA, dA = 4 pi a^2 * w / nlon per cell
                nlon = ds.sizes["lon"]
                M = (u * dp / G * A * coslat[None, None, None, :] * (4 * np.pi * A**2 * w / nlon)[None, None, None, :]).sum((1, 2, 3))
                pf = ds.hybrid_a_full.values / 100.0 + ds.hybrid_b_full.values * 1013.25
                k300 = int(np.argmin(np.abs(pf - 300.0)))
                zm = u[:, k300].mean(1)                                                              # (t, lat)
                nb = (ds.lat.values >= 25) & (ds.lat.values <= 50); sb = (ds.lat.values <= -25) & (ds.lat.values >= -50)
                out["t"].append(el); out["M"].append(M / 1e25)
                out["u300"].append((zm[:, nb] * coslat[nb]).sum(1) / coslat[nb].sum())
                out["u300s"].append((zm[:, sb] * coslat[sb]).sum(1) / coslat[sb].sum())
    r = {k: np.concatenate(v) for k, v in out.items()}
    day = np.floor(r["t"] - 1e-6).astype(int)                                                       # frame at 06..24 h -> day 0
    keep = day <= 31 + days_after
    res = {"day": np.unique(day[keep])}
    for k in ("M", "u300", "u300s"):
        res[k] = np.array([r[k][keep][day[keep] == dd].mean() for dd in res["day"]])
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True); ap.add_argument("--tag", default="p20")
    ap.add_argument("--days-after", type=int, default=31)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = []
    for spec in a.runs:
        paths, label = spec.split(":", 1)
        data.append((label, daily(paths.split(","), a.days_after)))
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 9), sharex=True, constrained_layout=True)
    names = (("M", "global relative angular momentum [1e25 kg m$^2$ s$^{-1}$]"),
             ("u300", "zonal-mean u, ~300 hPa, 25-50N [m/s]"), ("u300s", "zonal-mean u, ~300 hPa, 25-50S [m/s]"))
    for (label, d), c in zip(data, COLORS):
        for ax, (k, _) in zip(axes, names):
            ax.plot(d["day"], d[k], color=c, lw=2, label=label)
    for ax, (_, yl) in zip(axes, names):
        ax.axvline(31, color="#444", lw=1, ls="--"); ax.set_ylabel(yl, fontsize=8.5); ax.grid(alpha=0.25)
    axes[0].text(31.5, axes[0].get_ylim()[1], " 1990-01-01: tracers start,\n spin-up discarded", va="top", fontsize=8)
    axes[0].legend(frameon=False, fontsize=9)
    axes[-1].set_xlabel("days since 1989-12-01 (daily means of the 6-hourly frames)")
    axes[0].set_title(f"Spin-up adjustment ({a.tag})", fontsize=10)
    png = os.path.join(a.out, f"{a.tag}_spinup_adjust.png"); fig.savefig(png, dpi=130)

    lines = [f"# Spin-up adjustment: {a.tag}", "", "Daily means; day 0 = 1989-12-01, day 31 = 1990-01-01 (first diagnosed day).", "",
             "| run | quantity | day 0 | day 7 | day 15 | day 23 | day 30 | day 45 | last day | trend days 21-30 [/day] | trend days 31-last [/day] |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, d in data:
        for k, _ in names:
            def at(dd):
                i = np.where(d["day"] == dd)[0]
                return f"{d[k][i[0]]:.3f}" if i.size else "-"
            def trend(lo, hi):
                m = (d["day"] >= lo) & (d["day"] <= hi)
                return f"{np.polyfit(d['day'][m], d[k][m], 1)[0]:+.4f}" if m.sum() > 2 else "-"
            lines.append(f"| {label} | {k} | {at(0)} | {at(7)} | {at(15)} | {at(23)} | {at(30)} | {at(45)} | {d[k][-1]:.3f} | "
                         f"{trend(21, 30)} | {trend(31, int(d['day'][-1]))} |")
    if len(data) > 1:
        lines += ["", f"Difference {data[1][0]} minus {data[0][0]} (the drag's effect):", "",
                  "| quantity | day 7 | day 15 | day 23 | day 30 | day 45 | last day |", "|---|---|---|---|---|---|---|"]
        d0, d1 = data[0][1], data[1][1]
        common = np.intersect1d(d0["day"], d1["day"])
        for k, _ in names:
            diff = {dd: d1[k][d1["day"] == dd][0] - d0[k][d0["day"] == dd][0] for dd in common}
            lines.append(f"| {k} | " + " | ".join(f"{diff[dd]:+.3f}" if dd in diff else "-" for dd in (7, 15, 23, 30, 45)) +
                         f" | {diff[common[-1]]:+.3f} |")
    lines += ["", f"![spin-up]({os.path.basename(png)})", ""]
    open(os.path.join(a.out, f"{a.tag}_spinup_adjust.md"), "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
