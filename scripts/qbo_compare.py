#!/usr/bin/env python3
"""Phase 27: how the QBO nudging settings change the QBO and the tropical upwelling, AL7h against QBO30 / QBO10d.

    python scripts/qbo_compare.py OUTDIR NAME=AGGREGATE:SWEEP_JSON:P_BOT:TAPER:TAU [...] [--years 2006-2010]

AGGREGATE is a run directory of longrun_day*.nc covering the years (scripts/link_segments.py), SWEEP_JSON the run's
success_metrics raw json (tropical w* and entry-age profiles), and P_BOT [hPa] / TAPER [decades] / TAU [days] the
run's qbo nudging settings (p_top is 1 hPa in all of them). Equatorial (5S-5N) zonal-mean u is read on the model's own
levels and averaged to months; ERA5 is the monthly zonal mean the nudging uses. Writes OUTDIR/qbo_nudging.png
(nudging rate, QBO amplitude, correlation with ERA5, 50 hPa wind) and OUTDIR/qbo_upwelling.png (w*, entry age).
"""
from __future__ import annotations

import argparse, glob, json, os, re, sys

import netCDF4
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import report_figures as rf  # noqa: E402  (style, colours, reference line styles)
import strat_compare as sc  # noqa: E402
import xarray as xr  # noqa: E402

plt = rf.plt
P_TOP = 1.0


def eq_monthly_model(rundir, t0_year):
    """Equatorial (5S-5N, cos-weighted) zonal-mean u as monthly means: (months, nlev) array, p [hPa], year, month."""
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))
    rows, times = [], []
    for f in files:
        with netCDF4.Dataset(f) as d:
            lat = np.asarray(d.variables["lat"][:]); m = np.abs(lat) <= 5; w = np.cos(np.deg2rad(lat[m]))
            u = np.asarray(d.variables["u_wind"][:, :, :, m]).mean(2)                       # (t, lev, lat); dims time, level, lon, lat
            rows.append((u * w).sum(-1) / w.sum())
            tv = d.variables["time"]; times.append(netCDF4.num2date(tv[:], tv.units, getattr(tv, "calendar", "standard")))
            p = np.asarray(d.variables["level"][:]) * sc.P0_HPA
    u = np.concatenate(rows); t = np.concatenate(times)
    ym = np.array([(x.year, x.month) for x in t]); keys = sorted({tuple(k) for k in ym})
    out = np.array([u[(ym[:, 0] == y) & (ym[:, 1] == mo)].mean(0) for y, mo in keys])
    return out, p, np.array([k[0] for k in keys]), np.array([k[1] for k in keys])


def eq_monthly_era5(years):
    files = [os.path.join(sc.ERA5_DIR, f"era5_zm_monthly_{y}.nc") for y in years]
    ds = xr.open_mfdataset([f for f in files if os.path.exists(f)], combine="by_coords")
    tname = [c for c in ds.coords if c.startswith("time") or c == "valid_time"][0]
    u = ds["uzm"].sel(lat=slice(-5, 5)) if ds.lat[0] < ds.lat[-1] else ds["uzm"].sel(lat=slice(5, -5))
    w = np.cos(np.deg2rad(u.lat)); u = ((u * w).sum("lat") / w.sum()).load()
    t = u[tname].dt
    return u.values, ds.level.values.astype(float), t.year.values, t.month.values


def deseason(u, month):
    a = u.copy()
    for mo in range(1, 13):
        k = month == mo; a[k] -= u[k].mean(0)
    return a


def weight(p, p_bot, taper):
    l10 = np.log10(p); lo, hi = np.log10(P_TOP), np.log10(p_bot)
    w = np.clip(np.minimum((l10 - lo) / taper, (hi - l10) / taper), 0.0, 1.0)
    return np.where((p < P_TOP) | (p > p_bot), 0.0, w)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("outdir"); ap.add_argument("runs", nargs="+")
    ap.add_argument("--years", default="2006-2010")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = map(int, a.years.split("-")); years = list(range(y0, y1 + 1))
    ue, pe, ye, me = eq_monthly_era5(years)
    ae = deseason(ue, me); tdec_e = ye + (me - 0.5) / 12
    runs = {}
    for arg in a.runs:
        name, rest = arg.split("=", 1); agg, sw, pb, tp, tau = rest.split(":")
        u, p, yy, mm = eq_monthly_model(agg, y0); k = (yy >= y0) & (yy <= y1)
        runs[name] = dict(u=u[k], p=p, y=yy[k], m=mm[k], sw=json.load(open(sw)), p_bot=float(pb), taper=float(tp), tau=float(tau))
        print(f"{name}: {k.sum()} months, {p.size} levels", flush=True)

    # ---- figure 1: nudging, QBO amplitude, phase agreement, 50 hPa wind
    fig = plt.figure(figsize=(12, 8.4))
    gs = fig.add_gridspec(2, 3, height_ratios=(1.15, 1)); ax = [fig.add_subplot(gs[0, i]) for i in range(3)]
    ts = fig.add_subplot(gs[1, :])
    pp = np.geomspace(0.5, 120, 400)
    for n, r in runs.items():
        c, mk = rf.STYLE[n]
        ax[0].plot(weight(pp, r["p_bot"], r["taper"]) / r["tau"], pp, color=c, lw=2.2, label=f"{n}: {r['p_bot']:g} hPa, {r['tau']:g} d")
        an = deseason(r["u"], r["m"]); sd = an.std(0); kk = (r["p"] >= 1) & (r["p"] <= 100)
        rf.run_line(ax[1], n, sd[kk], r["p"][kk], every=4)
        # correlation of the monthly anomalies with ERA5 at each model level (ERA5 interpolated in ln p)
        ei = np.array([np.interp(np.log(r["p"]), np.log(pe), row) for row in ae])
        cor = np.array([np.corrcoef(an[:, j], ei[:, j])[0, 1] for j in range(r["p"].size)])
        rf.run_line(ax[2], n, cor[kk], r["p"][kk], every=4)
        j50 = int(np.argmin(np.abs(r["p"] - 50)))
        ts.plot(r["y"] + (r["m"] - 0.5) / 12, r["u"][:, j50], color=c, lw=2, marker=mk, ms=4, markevery=3, label=f"{n} ({r['p'][j50]:.0f} hPa)")
    ke = (pe >= 1) & (pe <= 100)
    ax[1].plot(ae.std(0)[ke], pe[ke], label="ERA5", **rf.REF["ERA5"])
    ts.plot(tdec_e, ue[:, int(np.argmin(np.abs(pe - 50)))], label="ERA5 (50 hPa)", **rf.REF["ERA5"])
    rf.log_p(ax[0], 1, 100); ax[0].set_xlabel("nudging rate, weight / tau [1/day]")
    ax[0].set_title("a  QBO nudging window, 5S-5N", color=rf.INK, fontsize=11, loc="left"); ax[0].legend(loc="lower right", fontsize=8)
    rf.log_p(ax[1], 1, 100); ax[1].set_xlabel("QBO amplitude: std of monthly anomalies [m/s]"); ax[1].set_xlim(left=0)
    ax[1].set_title("b  QBO amplitude", color=rf.INK, fontsize=11, loc="left"); ax[1].legend(loc="lower right", fontsize=8)
    rf.log_p(ax[2], 1, 100); ax[2].set_xlabel("correlation with ERA5, monthly anomalies"); ax[2].set_xlim(0, 1.02)
    ax[2].set_title("c  QBO phase agreement", color=rf.INK, fontsize=11, loc="left"); ax[2].legend(loc="lower left", fontsize=8)
    for x in ax[1:]: x.set_ylabel("")
    ts.axhline(0, color=rf.MUTED, lw=0.8); ts.set_xlim(y0, y1 + 1); ts.set_ylabel("u, 5S-5N [m/s]"); ts.set_xlabel("year")
    ts.set_title("d  Equatorial wind at 50 hPa, monthly means", color=rf.INK, fontsize=11, loc="left"); ts.legend(ncol=4, fontsize=8.5, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(a.outdir, "qbo_nudging.png"), dpi=150); plt.close(fig)

    # ---- figure 2: tropical w* and entry age
    first = next(iter(runs.values()))["sw"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.6))
    for n, r in runs.items():
        s = r["sw"]
        p = np.asarray(s["profile_p"]); w = np.asarray(s["profile_wstar_tropics"]); k = (p >= 5) & (p <= 120)
        rf.run_line(ax[0], n, w[k], p[k], every=5)
        p = np.asarray(s["profile_age_p"]); g = np.asarray(s["profile_age150_tropics"]); k = (p >= 1) & (p <= 100)
        rf.run_line(ax[1], n, g[k], p[k], every=6)
    p = np.asarray(first["profile_waccm_p"]); w = np.asarray(first["profile_waccm_wstar_tropics"]); k = (p >= 5) & (p <= 120)
    ax[0].plot(w[k], p[k], label="WACCM6", **rf.REF["WACCM6"])
    pc = np.asarray(first["profile_clams_p"]); ac = np.asarray(first["profile_clams_entry_tropics"]); k = (pc >= 1) & (pc <= 100)
    ax[1].plot(ac[k], pc[k], label="CLaMS (ERA5)", **rf.REF["CLaMS (ERA5)"])
    rf.log_p(ax[0], 5, 120); ax[0].set_xlabel("residual vertical velocity w*, 15S-15N [mm/s]"); ax[0].set_xlim(left=0)
    ax[0].set_title("a  Tropical upwelling", color=rf.INK, fontsize=11, loc="left"); ax[0].legend(loc="lower right", fontsize=9)
    rf.log_p(ax[1], 1, 100); ax[1].set_xlabel("entry age of air, 10S-10N [years]"); ax[1].set_xlim(left=0); ax[1].set_ylabel("")
    ax[1].set_title("b  Tropical entry age", color=rf.INK, fontsize=11, loc="left"); ax[1].legend(loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(a.outdir, "qbo_upwelling.png"), dpi=150); plt.close(fig)
    print("wrote", a.outdir)


if __name__ == "__main__":
    main()
