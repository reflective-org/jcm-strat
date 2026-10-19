#!/usr/bin/env python3
"""Free-running full physics (Phase 14) vs the best dry dycore (Phase 16 mix10trop) vs CLaMS / ERA5 — three figures.

    python scripts/compare_free_dry_clams.py --out docs/outputs/comparisons/free_dry_clams \
        [--free /data/JCM_stripped/jcm-strat-phase14/runs/p14free_10yr] [--dry /data/JCM_stripped/jcm-strat-phase16/runs/p16_mix10trop_10yr]

Both runs are 1990-1999 from ERA5; the window is their last two years (1998-1999, every 6-hourly frame), the ages the last 60 days.

  aoa500_triptych.png   the 500 hPa clock (reset below 500 hPa) as latitude-pressure sections: CLaMS v3.1/ERA5 2005-2009 mean age
                        minus CLaMS' own tropical (0-10 deg) age at 500 hPa (the same clock definition), the dry model, the free
                        model; below them the latitude profiles at 55 and 12 hPa
  wstar.png             TEM residual vertical velocity (annual mean): the 15S-15N profile 100-1 hPa and latitude sections at 70
                        and 30 hPa, against ERA5 TEM w* of the same years (scripts/fetch_era5_tem.py) and WACCM6 1996-2014
  temperature.png       zonal-mean temperature against latitude at 100 / 50 / 10 / 1 hPa, DJF and JJA, against ERA5 monthly
                        zonal means of the same years (ERA5 is also the reanalysis that drives CLaMS)
"""
from __future__ import annotations

import argparse, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_score as ss          # noqa: E402
import strat_compare as sc        # noqa: E402

# reference palette (dataviz skill, categorical slots 1-3 in fixed order); references in ink
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dc"
C_DRY, C_FREE, C_WACCM = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]

plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "legend.frameon": False, "lines.linewidth": 2.0})


def band(lat, row, lo, hi):
    return ss.band(np.asarray(lat), np.asarray(row), lo, hi)


def tropical_profile(p, lat, w):
    m = np.abs(lat) <= 15; wg = np.cos(np.deg2rad(lat[m]))
    return np.array([np.nansum(w[k, m] * wg) / np.sum(wg * np.isfinite(w[k, m])) for k in range(p.size)])


def label_end(ax, x, y, text, color, dx=0, dy=0):
    ax.annotate(text, (x, y), xytext=(4 + dx, dy), textcoords="offset points", color=INK, fontsize=9, va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=color, lw=1.2))


def fig_triptych(out, runs, clams):
    pc, latc, ac = clams
    off = band(latc, ac[int(np.argmin(np.abs(pc - 500.0)))], 0, 10)
    panels = [("CLaMS v3.1 / ERA5 2005-2009\n(AGE − its tropical 500 hPa age, %.2f yr)" % off, pc, latc, ac - off)]
    for name, r in runs.items():
        panels.append((f"{name}\n1998-1999, last 60 days", r["p"], r["lat"], r["age"]["aoa500"]))
    levels = np.arange(0.0, 6.01, 0.5)
    fig = plt.figure(figsize=(15, 9.2), constrained_layout=True)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1.0])
    for j, (title, p, lat, a) in enumerate(panels):
        ax = fig.add_subplot(gs[0, j]); ax.grid(False)
        o = np.argsort(p); P, A = p[o], a[o]
        keep = (P >= 0.9) & (P <= 320)
        # yellow -> green -> blue: lightness falls monotonically with age (still a sequential scale, not a rainbow), and the
        # hue change keeps neighbouring half-year bands apart, which twelve steps of one blue did not
        cmap = plt.get_cmap("YlGnBu", len(levels) - 1)
        cf = ax.contourf(lat, P[keep], A[keep], levels=levels, cmap=cmap, extend="max")
        ax.contour(lat, P[keep], A[keep], levels=levels[1::2], colors=INK, linewidths=0.4, alpha=0.6)        # half years
        cs = ax.contour(lat, P[keep], A[keep], levels=levels[::2][1:], colors=INK, linewidths=1.0)           # whole years
        for t in ax.clabel(cs, fmt="%.0f yr", fontsize=8, colors=INK, inline_spacing=2):
            t.set_bbox(dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))              # readable on the dark blues
        for pl in (55, 12):
            ax.axhline(pl, color="#e34948", lw=1.0, ls=(0, (4, 3)))
        ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_xlim(-85, 85)
        ax.set_yticks([300, 100, 55, 30, 12, 5, 1]); ax.set_yticklabels(["300", "100", "55", "30", "12", "5", "1"])
        ax.set_xlabel("latitude"); ax.set_title(title, fontsize=10, color=INK)
        if j == 0:
            ax.set_ylabel("pressure [hPa]")
    fig.colorbar(cf, ax=fig.axes[:3], label="age, 500 hPa clock [yr]", shrink=0.9)
    for j, pl in enumerate((55, 12)):
        ax = fig.add_subplot(gs[1, j])
        rows = [("CLaMS", latc, ss.at_level(pc, ac, pl) - off, INK, "-")]
        rows += [(n, r["lat"], ss.at_level(r["p"], r["age"]["aoa500"], pl), c, "-") for (n, r), c in zip(runs.items(), (C_DRY, C_FREE))]
        for n, la, row, c, ls in rows:
            m = np.abs(la) <= 85
            ax.plot(la[m], row[m], color=c, ls=ls)
            label_end(ax, la[m][-1], row[m][-1], n.split(" (")[0], c)
        ax.set_xlim(-85, 100); ax.set_xlabel("latitude"); ax.set_ylabel("age [yr]")
        ax.set_title(f"{pl} hPa (red dashed line above)", fontsize=10, color=INK)
    ax = fig.add_subplot(gs[1, 2]); ax.axis("off")
    txt = ["Tropical (0-10°) / 50-70° age [yr]", ""]
    for pl in (55, 12):
        txt.append(f"{pl} hPa")
        txt.append(f"  CLaMS         {band(latc, ss.at_level(pc, ac, pl), 0, 10) - off:4.2f} / {band(latc, ss.at_level(pc, ac, pl), 50, 70) - off:4.2f}")
        for n, r in runs.items():
            row = ss.at_level(r["p"], r["age"]["aoa500"], pl)
            txt.append(f"  {n.split(' (')[0]:<13} {band(r['lat'], row, 0, 10):4.2f} / {band(r['lat'], row, 50, 70):4.2f}")
        txt.append("")
    ax.text(0.0, 1.0, "\n".join(txt), va="top", family="monospace", fontsize=10, color=INK)
    fig.suptitle("Age of air, 500 hPa clock: free-running full physics vs dry dycore vs CLaMS", color=INK, fontsize=12)
    fig.savefig(os.path.join(out, "aoa500_triptych.png"), dpi=130); plt.close(fig)


def fig_wstar(out, runs, era5, waccm):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.2), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1.25, 1.25]})
    refs = [("ERA5 1998-99", era5, INK, "-"), ("WACCM6 1996-2014", waccm, C_WACCM, (0, (5, 3)))]
    ax = axes[0]
    for n, (p, lat, w), c, ls in refs + [(n, (r["wp"], r["wlat"], r["w"]), c, "-") for (n, r), c in zip(runs.items(), (C_DRY, C_FREE))]:
        prof = tropical_profile(p, lat, w); k = (p >= (2 if n.startswith("ERA5") else 1)) & (p <= 100)   # ERA5's 1 hPa is its top level: one-sided derivative
        ax.plot(prof[k], p[k], color=c, ls=ls, label=n.split(" (")[0])
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_yscale("log"); ax.set_ylim(100, 1); ax.set_yticks([100, 70, 50, 30, 10, 5, 1]); ax.set_yticklabels(["100", "70", "50", "30", "10", "5", "1"])
    ax.set_xlabel("w* [mm/s], 15S-15N, annual"); ax.set_ylabel("pressure [hPa]"); ax.set_title("tropical profile", fontsize=10, color=INK)
    ax.legend(loc="lower right", fontsize=9)
    for ax, pl in zip(axes[1:], (70, 30)):
        for n, (p, lat, w), c, ls in refs + [(n, (r["wp"], r["wlat"], r["w"]), c, "-") for (n, r), c in zip(runs.items(), (C_DRY, C_FREE))]:
            row = ss.at_level(p, w, pl); m = np.abs(lat) <= 80
            ax.plot(lat[m], row[m], color=c, ls=ls, label=n.split(" (")[0])
        ax.axhline(0, color=MUTED, lw=0.8); ax.set_xlim(-80, 80)
        ax.set_xlabel("latitude"); ax.set_ylabel("w* [mm/s], annual"); ax.set_title(f"{pl} hPa: where the air rises (width of the upwelling)", fontsize=10, color=INK)
        ax.legend(loc="lower center", fontsize=9, ncol=2)
    fig.suptitle("TEM residual vertical velocity w* (all 6-hourly frames, 1998-1999)", color=INK, fontsize=12)
    fig.savefig(os.path.join(out, "wstar.png"), dpi=130); plt.close(fig)


def fig_temperature(out, runs, era5_T):
    levels = (100, 50, 10, 1)
    fig, axes = plt.subplots(len(levels), 2, figsize=(12, 12.6), layout="constrained", sharex=True)
    for j, s in enumerate(("DJF", "JJA")):
        ref = era5_T[s]
        for i, pl in enumerate(levels):
            ax = axes[i, j]
            ax.plot(ref.lat, ref.sel(plev=pl), color=INK, label="ERA5 1998-99")
            for (n, r), c in zip(runs.items(), (C_DRY, C_FREE)):
                ax.plot(r["Tseas"][s].lat, r["Tseas"][s].sel(plev=pl), color=c, label=n.split(" (")[0])
            ax.set_xlim(-90, 90); ax.set_title(f"{s}, {pl} hPa", fontsize=10, color=INK)
            if j == 0:
                ax.set_ylabel("T [K]")
            if i == len(levels) - 1:
                ax.set_xlabel("latitude")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="outside lower center", ncol=3, fontsize=10)
    fig.suptitle("Zonal-mean temperature vs latitude, 1998-1999 (ERA5 = the reanalysis that drives CLaMS)", color=INK, fontsize=12)
    fig.savefig(os.path.join(out, "temperature.png"), dpi=130); plt.close(fig)


def load_run(rundir, era5_years):
    fields, age, p, lat, span = ss.load_model(rundir, 2.0, 60.0)
    wp, wlat, _, w = ss.wstar_fields(fields, ss.SEASONS["annual"])
    t = fields["T"].time; Tseas = {}
    import xarray as xr
    for s, months in (("DJF", (12, 1, 2)), ("JJA", (6, 7, 8))):
        tm = fields["T"].where(t.dt.month.isin(list(months)), drop=True).mean("time")
        tm = xr.Dataset({"T": tm}).rename(level="lev")
        Tseas[s] = sc._interp_logp(tm, tm.lev.values, sc.P_LEVELS, "lev")["T"]
    return dict(p=p, lat=lat, age=age, wp=wp, wlat=wlat, w=w, Tseas=Tseas, span=span)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--free", default="/data/JCM_stripped/jcm-strat-phase14/runs/p14free_10yr")
    ap.add_argument("--dry", default="/data/JCM_stripped/jcm-strat-phase16/runs/p16_mix10trop_10yr")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    import pickle
    cache = os.path.join(a.out, ".cache.pkl")          # the archives take ~15 min to reduce; figures re-render from this
    if os.path.exists(cache):
        runs = pickle.load(open(cache, "rb"))
    else:
        runs = {"Dry dycore (Phase 16 mix10trop)": load_run(a.dry, None), "Full physics, free (Phase 14)": load_run(a.free, None)}
        pickle.dump(runs, open(cache, "wb"))
    for n, r in runs.items():
        print(f"[cmp] {n}: window {r['span'][0]}..{r['span'][1]}, {r['span'][2]} frames, {r['p'].size} levels", flush=True)
    years = sorted({int(s[:4]) for r in runs.values() for s in (r["span"][1],)})
    years = [1998, 1999]
    e = ss.era5_wstar(years); wa = ss.waccm_wstar()
    era5 = (e["annual"][0], e["annual"][1], e["annual"][3]); waccm = (wa["annual"][0], wa["annual"][1], wa["annual"][3])
    lat0 = next(iter(runs.values()))["lat"]
    zm, _ = sc.load_era5(years, lat0)
    era5_T = {s: zm["T"].where(zm.time.dt.month.isin(list(m)), drop=True).mean("time") for s, m in (("DJF", (12, 1, 2)), ("JJA", (6, 7, 8)))}
    fig_triptych(a.out, runs, ss.clams_ref())
    fig_wstar(a.out, runs, era5, waccm)
    fig_temperature(a.out, runs, era5_T)
    # numbers for the record
    for n, r in runs.items():
        prof = tropical_profile(r["wp"], r["wlat"], r["w"])
        print(f"[cmp] {n}: tropical w* 100/70/50/30/10 = " + "/".join(f"{np.interp(np.log(pl), np.log(r['wp']), prof):.2f}" for pl in (100, 70, 50, 30, 10)))
    pe, le, we = era5
    prof = tropical_profile(pe, le, we)
    print("[cmp] ERA5 1998-99: tropical w* 100/70/50/30/10 = " + "/".join(f"{np.interp(np.log(pl), np.log(pe), prof):.2f}" for pl in (100, 70, 50, 30, 10)))
    print(f"[cmp] wrote {a.out}/aoa500_triptych.png, wstar.png, temperature.png")


if __name__ == "__main__":
    main()
