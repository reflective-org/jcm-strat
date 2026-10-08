#!/usr/bin/env python3
"""DJF and JJA age of air and zonal-mean zonal wind of one run, against CLaMS / WACCM6 (age) and ERA5 (wind), over the
same calendar years (Susanne 2026-10-08, for the Phase 20 extension).

    JAX_PLATFORMS=cpu python scripts/seasonal_age_winds.py runs/<aggregate> OUTDIR --years 2005-2009 [--label TEXT]

Writes to OUTDIR:
  age_seasonal_<clock>.png   rows DJF / JJA; columns model, reference, model - reference (300-1 hPa).
                             aoa150 (reset below 150 hPa, entry age) is compared with WACCM6 REF-D1 AOA (also an
                             age relative to the tropopause region); aoa_sfc (surface reset) with CLaMS v3.1 (ERA5).
  wind_seasonal.png          rows DJF / JJA; columns model, ERA5 (same months), model - ERA5 (1000-1 hPa).
  seasonal_metrics.md        ages at 55 / 12 hPa (tropics 10S-10N, 50-70 N and S) and u at 10 hPa 60N/60S per season.
Seasons are monthly-mean seasons of the selected years: DJF = Dec, Jan, Feb of those years (calendar months, so the
December of the last year belongs to that year's DJF, as in strat_compare.py). Model fields: every 6-hourly frame in the
window, zonal mean. WACCM6 h0 files stamp each monthly mean with the first day of the NEXT month (19700201 = January).
"""
from __future__ import annotations

import argparse, glob, io, os, re, sys, zipfile
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAMS_ZIP = "/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip"
WACCM = "/data/CESM2_REFD1_AOA/AoA_waccm6_refd1.04_AOA1mf_1970-2019_ba_0_100.0_ck_0_50.0.nc"
ERA5_DIR = os.path.join(REPO, "cache", "era5_ref")
P0_HPA = 1013.25
SEASONS = {"DJF": (12, 1, 2), "JJA": (6, 7, 8)}
CLOCKS = {"aoa150": "WACCM6 REF-D1", "aoa_sfc": "CLaMS v3.1"}
P_OUT = np.geomspace(1000.0, 1.0, 60)


def files(rundir):
    fs = glob.glob(os.path.join(rundir, "longrun_day*.nc"))
    return sorted(fs, key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))


def model_seasonal(rundir, years):
    """Season -> dict(var -> (level, lat) zonal mean) over every frame of the selected years; level in hPa (ascending p)."""
    want = ["u_wind"] + list(CLOCKS)
    acc = {s: {v: 0.0 for v in want} for s in SEASONS}; cnt = {s: 0 for s in SEASONS}
    p_hpa = lat = None
    for f in files(rundir):
        with xr.open_dataset(f, decode_times=True) as d:
            yr = d.time.dt.year.values; mo = d.time.dt.month.values
            for s, months in SEASONS.items():
                k = np.isin(yr, years) & np.isin(mo, months)
                if not k.any():
                    continue
                sub = d.isel(time=np.where(k)[0])
                for v in want:
                    if v in sub:
                        acc[s][v] = acc[s][v] + sub[v].mean("lon").sum("time").values
                cnt[s] += int(k.sum())
                p_hpa = sub.level.values * P0_HPA; lat = sub.lat.values
    if not all(cnt.values()):
        raise SystemExit(f"no model frames for some season in {years}: {cnt}")
    out = {s: {v: (acc[s][v] / cnt[s]) for v in want if not np.isscalar(acc[s][v])} for s in SEASONS}
    for s in out:                                                 # clocks in days -> years
        for c in CLOCKS:
            if c in out[s]:
                out[s][c] = out[s][c] / 365.25
    return out, p_hpa, lat, cnt


def clams_seasonal(years):
    out = {}
    with zipfile.ZipFile(CLAMS_ZIP) as z:
        per = []
        for y in years:
            n = [x for x in z.namelist() if x.endswith(f"_press_{y}.nc")]
            if n:
                per.append(xr.open_dataset(io.BytesIO(z.read(n[0])), decode_times=False)["AGE"].load())
    if not per:
        return None
    a = xr.concat(per, "year"); a = a.where(a > -1e20)
    for s, months in SEASONS.items():
        out[s] = a.sel(month=list(map(float, months))).mean(("year", "month"))
    return {s: (np.asarray(v.press), np.asarray(v.lat), v.values) for s, v in out.items()}


def waccm_seasonal(years):
    w = xr.open_dataset(WACCM, decode_times=False)
    d = w.date.values.astype(int)
    stamp_y, stamp_m = d // 10000, (d // 100) % 100
    mon = np.where(stamp_m == 1, 12, stamp_m - 1); yr = np.where(stamp_m == 1, stamp_y - 1, stamp_y)   # stamp = next month
    out = {}
    for s, months in SEASONS.items():
        k = np.isin(yr, years) & np.isin(mon, months)
        if not k.any():
            return None
        a = w.AOA.isel(time=np.where(k)[0]).mean("time"); a = a.where(a >= 0)
        out[s] = (np.asarray(w.lev), np.asarray(w.lat), a.values)
    return out


def era5_seasonal_u(years, lat_out):
    fs = [os.path.join(ERA5_DIR, f"era5_zm_monthly_{y}.nc") for y in years]
    fs = [f for f in fs if os.path.exists(f)]
    if not fs:
        return None
    ds = xr.open_mfdataset(fs, combine="by_coords")
    tname = [c for c in ds.coords if c.startswith("time") or c == "valid_time"][0]
    u = ds["uzm"].rename({tname: "time"}).interp(lat=lat_out).load()
    return {s: (np.asarray(u.level, float), lat_out, u.where(u.time.dt.month.isin(list(m)), drop=True).mean("time").values)
            for s, m in SEASONS.items()}


def on_grid(p_src, lat_src, f, lat_dst, p_dst=P_OUT):
    """Bilinear in (log p, lat) onto (p_dst, lat_dst); NaN outside the source range."""
    o = np.argsort(p_src); p_src = np.asarray(p_src)[o]; f = np.asarray(f)[o]
    lo = np.argsort(lat_src); lat_src = np.asarray(lat_src)[lo]; f = f[:, lo]
    tmp = np.array([np.interp(lat_dst, lat_src, row, left=np.nan, right=np.nan) for row in f])          # (p_src, lat_dst)
    out = np.array([np.interp(np.log(p_dst), np.log(p_src), tmp[:, j], left=np.nan, right=np.nan) for j in range(len(lat_dst))]).T
    return out


def band(lat, row, lo, hi):
    m = (lat >= lo) & (lat <= hi) & np.isfinite(row); w = np.cos(np.deg2rad(lat[m]))
    return float(np.sum(row[m] * w) / np.sum(w)) if m.any() else np.nan


def panel(ax, lat, p, f, levels, cmap, title, ptop, pbot):
    c = ax.contourf(lat, p, f, levels=levels, cmap=cmap, extend="both")
    ax.set_yscale("log"); ax.set_ylim(pbot, ptop); ax.set_xlim(-90, 90); ax.set_title(title, fontsize=9)
    return c


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("rundir"); ap.add_argument("outdir")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--label", default="model")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = (int(v) for v in a.years.split("-")); years = list(range(y0, y1 + 1))
    m, p_hpa, lat, cnt = model_seasonal(a.rundir, years)
    print(f"[seasonal] {a.rundir} {a.years}: frames {cnt}", flush=True)
    lat_g = np.linspace(-89, 89, 90)
    refs = {"aoa150": waccm_seasonal(years), "aoa_sfc": clams_seasonal(years)}
    lines = [f"# Seasonal age of air and winds: {a.label}, {a.years}\n", f"Run `{a.rundir}`; 6-hourly frames per season: {cnt}.\n",
             "## Age of air [yr]\n", "| clock | reference | season | 55 hPa tropics model / ref | 55 hPa 50-70N | 55 hPa 50-70S | 12 hPa tropics |",
             "|---|---|---|---|---|---|---|"]
    age_lv = np.arange(0, 7.01, 0.5); diff_lv = np.arange(-2, 2.01, 0.25)
    for clock, refname in CLOCKS.items():
        if clock not in m["DJF"]:
            continue
        ref = refs[clock]
        fig, axs = plt.subplots(2, 3, figsize=(15, 8), sharey=True)
        for i, s in enumerate(SEASONS):
            mg = on_grid(p_hpa, lat, m[s][clock], lat_g)
            c0 = panel(axs[i, 0], lat_g, P_OUT, mg, age_lv, "viridis", f"{a.label} {clock}, {s}", 1, 300)
            row = [clock, refname, s]
            if ref is not None:
                rg = on_grid(ref[s][0], ref[s][1], ref[s][2], lat_g)
                panel(axs[i, 1], lat_g, P_OUT, rg, age_lv, "viridis", f"{refname}, {s}", 1, 300)
                c2 = panel(axs[i, 2], lat_g, P_OUT, mg - rg, diff_lv, "RdBu_r", f"model - {refname}, {s}", 1, 300)
                k55, k12 = np.argmin(abs(P_OUT - 55)), np.argmin(abs(P_OUT - 12))
                f = lambda g, k, lo, hi: band(lat_g, g[k], lo, hi)
                row += [f"{f(mg, k55, -10, 10):.2f} / {f(rg, k55, -10, 10):.2f}", f"{f(mg, k55, 50, 70):.2f} / {f(rg, k55, 50, 70):.2f}",
                        f"{f(mg, k55, -70, -50):.2f} / {f(rg, k55, -70, -50):.2f}", f"{f(mg, k12, -10, 10):.2f} / {f(rg, k12, -10, 10):.2f}"]
            lines.append("| " + " | ".join(row) + " |")
            for ax in axs[i]:
                ax.set_ylabel("hPa") if ax is axs[i, 0] else None
        fig.colorbar(c0, ax=axs[:, :2], label="age [yr]", pad=0.01)
        if ref is not None:
            fig.colorbar(c2, ax=axs[:, 2], label="model - ref [yr]", pad=0.01)
        fig.suptitle(f"Age of air ({clock}) by season, {a.years}: {a.label} vs {refname}")
        fig.savefig(os.path.join(a.outdir, f"age_seasonal_{clock}.png"), dpi=110); plt.close(fig)

    e = era5_seasonal_u(years, lat_g)
    u_lv = np.arange(-60, 61, 5); du_lv = np.arange(-20, 21, 2.5)
    fig, axs = plt.subplots(2, 3, figsize=(15, 8), sharey=True)
    lines += ["\n## Zonal-mean zonal wind [m/s]\n", "| season | u 10 hPa 60N model / ERA5 | u 10 hPa 60S | u 30 hPa equator |", "|---|---|---|---|"]
    for i, s in enumerate(SEASONS):
        mg = on_grid(p_hpa, lat, m[s]["u_wind"], lat_g)
        c0 = panel(axs[i, 0], lat_g, P_OUT, mg, u_lv, "RdBu_r", f"{a.label} u, {s}", 1, 1000)
        if e is not None:
            eg = on_grid(e[s][0], e[s][1], e[s][2], lat_g)
            panel(axs[i, 1], lat_g, P_OUT, eg, u_lv, "RdBu_r", f"ERA5 u, {s}", 1, 1000)
            c2 = panel(axs[i, 2], lat_g, P_OUT, mg - eg, du_lv, "PuOr_r", f"model - ERA5, {s}", 1, 1000)
            k10, k30 = np.argmin(abs(P_OUT - 10)), np.argmin(abs(P_OUT - 30))
            g = lambda F, k, la: float(np.interp(la, lat_g, F[k]))
            lines.append(f"| {s} | {g(mg, k10, 60):.0f} / {g(eg, k10, 60):.0f} | {g(mg, k10, -60):.0f} / {g(eg, k10, -60):.0f} | "
                         f"{g(mg, k30, 0):.0f} / {g(eg, k30, 0):.0f} |")
        for ax in axs[i]:
            ax.contour(lat_g, P_OUT, mg if ax is axs[i, 0] else (eg if (e is not None and ax is axs[i, 1]) else mg * np.nan),
                       levels=[0], colors="k", linewidths=0.6)
        axs[i, 0].set_ylabel("hPa")
    fig.colorbar(c0, ax=axs[:, :2], label="u [m/s]", pad=0.01)
    if e is not None:
        fig.colorbar(c2, ax=axs[:, 2], label="model - ERA5 [m/s]", pad=0.01)
    fig.suptitle(f"Zonal-mean zonal wind by season, {a.years}: {a.label} vs ERA5 (same months)")
    fig.savefig(os.path.join(a.outdir, "wind_seasonal.png"), dpi=110); plt.close(fig)
    open(os.path.join(a.outdir, "seasonal_metrics.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
