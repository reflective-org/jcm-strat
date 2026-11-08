#!/usr/bin/env python3
"""Group D of the success metrics (Phase 28): variability and two relations, model runs against ERA5 for the same days.

    python scripts/variability_score.py OUTDIR NAME=<daily_zm.npz> [NAME=...] --era5-dir DIR --t0 2006-01-01 --t1 2011-01-01
        [--long 1990-2022 --long-dir LDIR]

Inputs are daily zonal means: one npz per run over the window (scripts/daily_zm.py) and one per ERA5 year
(DIR/era5_<year>.npz from scripts/fetch_era5_daily_zm.py: CDS ERA5, 2.5 deg, 1-250 hPa; LDIR holds the 10/50/100 hPa
years for --long). NOT the L95 nudging windows: they are WeatherBench2 data and constant above 50 hPa.
The age reference is CLaMS v3.1 (ERA5-driven), monthly. Every anomaly is taken against the dataset's OWN day-of-year
(or monthly) climatology over the window, so the seasonal cycle is removed separately from the model and from ERA5.

Metrics. err = |ln(model/ref)| / ln(factor) for spreads and slopes, |model - ref| / bound otherwise. Pass err <= 1,
near <= 1.5, as A-C.

  D1  year-to-year spread: std over winters of the winter-mean u at 10 hPa, cos-weighted over 55-65 deg
      (DJF N, JJA S)                                                                                  factor 1.5
  D2  daily spread: std of daily u anomalies at 60 deg, 10 hPa within winter (DJF N, JJA S)            factor 1.35
  D3  NH major SSWs (Charlton-Polvani, u 60N 10 hPa, strat_compare.ssw_dates): number in the window       +- 1 event
  D4  seasonal cycle: final-warming date (first easterly crossing of 5-day-smoothed u 60 deg 10 hPa after
      which u stays below 5 m/s, Black & McDaniel; Mar-Jul N / Sep-Jan S), mean over the springs                                           +- 10 days
      and the annual-cycle amplitude (max - min of the monthly climatology) of tropical w* at 70 hPa    factor 1.35
  D5  daily variability of the wave forcing: std of daily anomalies of the 45-75 deg eddy heat flux v'T'
      at 100 hPa (DJF N, JJA S)                                                                       factor 1.35
  D6  heat flux -> vortex relation (Newman et al. 2001, pooled daily): regression slope of the 50 hPa
      polar-cap (60-90) T anomaly on the trailing 40-day mean 100 hPa 45-75 heat-flux anomaly
      (poleward positive), days Jan-Mar N / Jul-Oct S                                                  factor 1.35
  D7  age vs w* relation: regression slope of the monthly tropical (10S-10N) age anomaly at 55 hPa
      (deseasonalised, detrended; model aoa150, CLaMS AGE) on the trailing 3-month tropical (15S-15N)
      70 hPa w* anomaly                                                                               factor 1.5
      A slope of the wrong sign fails (err 3).

D is reported as its own group; the combined score stays the mean of A, B and C so earlier scores stay comparable.
With --long, the same quantities from ERA5 over those years are written as context (how much five years scatter).
Writes OUTDIR/variability.json, OUTDIR/variability_table.md and the figures OUTDIR/variability_*.png.
"""
from __future__ import annotations

import argparse, io, json, os, sys, zipfile
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import strat_circulation as circ                   # noqa: E402
from strat_compare import ssw_dates                # noqa: E402

CLAMS_ZIP = "/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip"
KAPPA = 0.2857
F = dict(D1=1.5, D2=1.35, D3=1.0, D4d=10.0, D4w=1.35, D5=1.35, D6=1.35, D7=1.5)
HEMI = {"N": dict(lat=60.0, band=(55, 65), djf=(12, 1, 2), rel=(1, 2, 3), hf=(45, 75), cap=(60, 90), sign=1.0),
        "S": dict(lat=-60.0, band=(-65, -55), djf=(6, 7, 8), rel=(7, 8, 9, 10), hf=(-75, -45), cap=(-90, -60), sign=-1.0)}


# ----------------------------------------------------------------------------- data
class Z:
    """Daily zonal means (day, lev, lat) of one source."""
    def __init__(self, d):
        self.days = d["days"].astype("datetime64[D]"); self.p = d["p_hpa"]; self.lat = d["lat"]
        self.f = {k: d[k] for k in d if k not in ("days", "p_hpa", "lat")}

    @classmethod
    def load(cls, files, t0=None, t1=None):
        ds = [dict(np.load(f)) for f in files]
        d = {k: np.concatenate([x[k] for x in ds]) if k in ("days", "u", "v", "T", "th", "vth", "aoa150", "aoa_sfc") else ds[0][k]
             for k in ds[0] if all(k in x for x in ds)}
        z = cls(d)
        if t0 is not None:
            m = (z.days >= np.datetime64(t0)) & (z.days < np.datetime64(t1))
            z.days = z.days[m]; z.f = {k: v[m] for k, v in z.f.items()}
        return z

    def ilev(self, p):
        return int(np.argmin(np.abs(np.log(self.p / p))))

    def band(self, var, p, lo, hi):
        x = self.f[var][:, self.ilev(p)]
        m = (self.lat >= lo) & (self.lat <= hi); w = np.cos(np.deg2rad(self.lat[m]))
        return (x[:, m] * w).sum(1) / w.sum()

    def at_lat(self, var, p, lat):
        x = self.f[var][:, self.ilev(p)]
        return np.array([np.interp(lat, self.lat, row) for row in x])

    def vT(self, p, lo, hi):          # v'T' from v'theta'
        return self.band("vth", p, lo, hi) / (1000.0 / self.p[self.ilev(p)]) ** KAPPA

    def months(self):
        y = self.days.astype("datetime64[Y]").astype(int) + 1970
        m = self.days.astype("datetime64[M]").astype(int) % 12 + 1
        return y, m


def doy(days):
    d = (days - days.astype("datetime64[Y]")).astype(int)            # 0..365
    leap = ((days.astype("datetime64[Y]").astype(int) + 1970) % 4 == 0)
    return np.where(leap & (d >= 59), d - 1, d).clip(0, 364)


def anomaly(x, days, smooth=31):
    k = doy(days); clim = np.array([np.nanmean(x[k == i]) if np.any(k == i) else np.nan for i in range(365)])
    clim = np.where(np.isnan(clim), np.nanmean(clim), clim)
    ker = np.ones(smooth) / smooth; pad = np.concatenate([clim[-smooth:], clim, clim[:smooth]])
    clim = np.convolve(pad, ker, "same")[smooth:-smooth]
    return x - clim[k]


def month_of(days):
    return days.astype("datetime64[M]").astype(int) % 12 + 1


def monthly_tem_wstar(z, plev=70.0):
    """Monthly tropical w* (15S-15N) from monthly means of the daily vbar, v'theta', thetabar (as strat_circulation)."""
    ym = z.days.astype("datetime64[M]"); out_t, out_w = [], []
    for m in np.unique(ym):
        k = ym == m
        if k.sum() < 25:
            continue
        p, _, psi = circ.tem_streamfunction(z.f["v"][k].mean(0), z.f["vth"][k].mean(0), z.f["th"][k].mean(0), z.p * 100.0, z.lat)
        w = circ.residual_w(p, psi, z.lat)
        out_t.append(m); out_w.append(circ.tropical_wstar(p, w, z.lat, plev))
    return np.array(out_t), np.array(out_w)


def deseason_detrend(t_month, x):
    m = t_month.astype(int) % 12
    clim = np.array([x[m == i].mean() for i in range(12)])
    a = x - clim[m]; tt = np.arange(a.size)
    return a - np.polyval(np.polyfit(tt, a, 1), tt)


def clams_monthly_age(years, plev=55.0):
    t, a = [], []
    with zipfile.ZipFile(CLAMS_ZIP) as zf:
        for y in years:
            ds = xr.open_dataset(io.BytesIO(zf.read(f"clams_v3.1_era5_zm_lat_press_{y}.nc")), decode_times=False)
            A = ds["AGE"].where(ds["AGE"] > -1e20)
            lp = np.log(ds.press.values); o = np.argsort(lp)
            for mi in range(12):
                prof = A.isel(month=mi).values                         # (press, lat)
                row = np.array([np.interp(np.log(plev), lp[o], prof[o, j]) for j in range(prof.shape[1])])
                lat = ds.lat.values; m = np.abs(lat) <= 10; w = np.cos(np.deg2rad(lat[m]))
                t.append(np.datetime64(f"{y}-{mi + 1:02d}")); a.append(np.nansum(row[m] * w) / np.nansum(w * np.isfinite(row[m])))
    return np.array(t), np.array(a)


# ----------------------------------------------------------------------------- quantities
def quantities(z, age=None):
    """All D quantities of one source (z = daily zonal means; age = (months, tropical 55 hPa age) or None -> aoa150)."""
    q = {}; y, mo = z.months()
    for h, H in HEMI.items():
        u = z.at_lat("u", 10.0, H["lat"])
        # D1: winter means (DJF labelled by its Jan year; complete winters only)
        wy = np.where(mo == 12, y + 1, y) if h == "N" else y
        win = np.isin(mo, H["djf"]); vals = []; ub = z.band("u", 10.0, *H["band"])
        for yy in np.unique(wy[win]):
            k = win & (wy == yy)
            if k.sum() >= 85:
                vals.append(ub[k].mean())
        q[f"D1-{h}"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else np.nan; q[f"winters-{h}"] = len(vals)
        q[f"winter_u-{h}"] = [float(v) for v in vals]
        # D2: daily spread in winter
        ua = anomaly(u, z.days); q[f"D2-{h}"] = float(np.std(ua[win]))
        # D5: heat-flux daily variability
        hf = H["sign"] * z.vT(100.0, *H["hf"]); hfa = anomaly(hf, z.days)
        q[f"D5-{h}"] = float(np.std(hfa[win])); q[f"hf_mean-{h}"] = float(hf[win].mean())
        # D6: trailing 40-day heat flux vs 50 hPa polar-cap T
        T = z.band("T", 50.0, *H["cap"]); Ta = anomaly(T, z.days)
        c = np.concatenate([[0.0], np.cumsum(hfa)]); n = 40
        x = np.full(hfa.size, np.nan); x[n - 1:] = (c[n:] - c[:-n]) / n
        k = np.isin(mo, H["rel"]) & np.isfinite(x)
        sl = np.polyfit(x[k], Ta[k], 1)[0]; r = np.corrcoef(x[k], Ta[k])[0, 1]
        q[f"D6-{h}"] = float(sl); q[f"D6r-{h}"] = float(r); q[f"D6pts-{h}"] = (x[k][::3].tolist(), Ta[k][::3].tolist())
        if h == "N":                                                   # D3
            q["SSW-N"] = [str(e) for e in ssw_dates(u, z.days)]
        # D4: final warming
        us = np.full(u.size, np.nan); us[2:-2] = np.convolve(u, np.ones(5) / 5, "valid"); fw = []   # NaN at the ends
        for yy in np.unique(y):
            if h == "N":
                k = (z.days >= np.datetime64(f"{yy}-03-01")) & (z.days < np.datetime64(f"{yy}-08-01"))
            else:
                k = (z.days >= np.datetime64(f"{yy}-09-01")) & (z.days < np.datetime64(f"{yy + 1}-02-01"))
            if k.sum() < 120:
                continue
            s, dd = us[k], z.days[k]; ok = np.isfinite(s); s, dd = s[ok], dd[ok]
            # Black & McDaniel: the first easterly crossing after which u never returns above 5 m/s
            cross = [c for c in np.where((s[:-1] >= 0) & (s[1:] < 0))[0] if np.all(s[c + 1:] < 5.0)]
            if cross:
                start = np.datetime64(f"{yy}-03-01") if h == "N" else np.datetime64(f"{yy}-09-01")
                fw.append((int(yy), int((dd[cross[0] + 1] - start).astype(int))))
        q[f"D4d-{h}"] = float(np.mean([d for _, d in fw])) if fw else np.nan; q[f"fw-{h}"] = fw
        q[f"u10-{h}"] = u.tolist()
    # D4w: annual cycle of tropical w* 70 hPa;  D7 age vs w*
    tm, w = monthly_tem_wstar(z, 70.0)
    mi = tm.astype(int) % 12; clim = np.array([w[mi == i].mean() for i in range(12)])
    q["D4w"] = float(clim.max() - clim.min()); q["w70_clim"] = clim.tolist()
    wa = deseason_detrend(tm, w); w3 = np.convolve(wa, np.ones(3) / 3, "full")[:wa.size]; w3[:2] = np.nan
    if age is None:
        ym = z.days.astype("datetime64[M]"); a55 = z.band("aoa150", 55.0, -10, 10) / 365.25
        at = np.array([m for m in tm]); av = np.array([a55[ym == m].mean() for m in tm])
    else:
        at, av = age; keep = np.isin(at, tm); at, av = at[keep], av[keep]
    aa = deseason_detrend(at, av); ww = np.array([w3[np.where(tm == m)[0][0]] for m in at])
    k = np.isfinite(ww)
    q["D7"] = float(np.polyfit(ww[k], aa[k], 1)[0]); q["D7r"] = float(np.corrcoef(ww[k], aa[k])[0, 1])
    q["D7pts"] = (ww[k].tolist(), aa[k].tolist())
    q["days"] = [str(d) for d in z.days]
    return q


def errors(m, r):
    """-> list of (id, label, model, ref, err)."""
    out = []
    lg = lambda a, b, f: abs(np.log(a / b)) / np.log(f) if (a > 0 and b > 0) else 3.0
    for h in "NS":
        out.append((f"D1-{h}", f"year-to-year std of winter u 55-65{h} 10 hPa [m/s]", m[f"D1-{h}"], r[f"D1-{h}"], lg(m[f"D1-{h}"], r[f"D1-{h}"], F["D1"])))
    for h in "NS":
        out.append((f"D2-{h}", f"daily std of winter u 60{h} 10 hPa [m/s]", m[f"D2-{h}"], r[f"D2-{h}"], lg(m[f"D2-{h}"], r[f"D2-{h}"], F["D2"])))
    nm, nr = len(m["SSW-N"]), len(r["SSW-N"])
    out.append(("D3", "NH major SSWs in the window [number]", nm, nr, abs(nm - nr) / F["D3"]))
    for h in "NS":
        dm, dr = dict(map(tuple, m[f"fw-{h}"])), dict(map(tuple, r[f"fw-{h}"])); yy = sorted(set(dm) & set(dr))   # common springs
        a = float(np.mean([dm[y] for y in yy])) if yy else np.nan; b = float(np.mean([dr[y] for y in yy])) if yy else np.nan
        e = abs(a - b) / F["D4d"] if yy else 3.0
        out.append((f"D4-fw{h}", f"final warming {h}, days after {'1 Mar' if h == 'N' else '1 Sep'}", a, b, e))
    out.append(("D4-w", "annual-cycle amplitude of tropical w* 70 hPa [mm/s]", m["D4w"], r["D4w"], lg(m["D4w"], r["D4w"], F["D4w"])))
    for h in "NS":
        out.append((f"D5-{h}", f"daily std of 100 hPa heat flux {h} [K m/s]", m[f"D5-{h}"], r[f"D5-{h}"], lg(m[f"D5-{h}"], r[f"D5-{h}"], F["D5"])))
    for h in "NS":
        out.append((f"D6-{h}", f"heat flux -> polar-cap T slope {h} [K per K m/s]", m[f"D6-{h}"], r[f"D6-{h}"], lg(m[f"D6-{h}"], r[f"D6-{h}"], F["D6"])))
    out.append(("D7", "age vs w* slope [yr per mm/s]", m["D7"], r["D7"], lg(-m["D7"], -r["D7"], F["D7"])))
    return out


# ----------------------------------------------------------------------------- figures
COL = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22"]


def figures(outdir, Q, ref):
    names = list(Q)
    days = np.array(ref["days"], dtype="datetime64[D]")
    fig, ax = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    for i, h in enumerate("NS"):
        ax[i].plot(days, ref[f"u10-{h}"], "k", lw=1.6, label="ERA5")
        for c, n in zip(COL, names):
            ax[i].plot(np.array(Q[n]["days"], dtype="datetime64[D]"), Q[n][f"u10-{h}"], color=c, lw=0.7, label=n)
        ax[i].axhline(0, color="0.5", lw=0.5); ax[i].set_ylabel(f"u 60{h} 10 hPa [m/s]")
        if h == "N":
            for e in ref["SSW-N"]:
                ax[i].axvline(np.datetime64(e), color="k", ls=":", lw=1)
    ax[0].legend(ncol=5, fontsize=8); ax[0].set_title("Polar vortex at 10 hPa (dotted: ERA5 major SSWs)")
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "variability_vortex.png"), dpi=110); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    for i, h in enumerate("NS"):
        for c, n in zip(COL, names):
            x, y = map(np.asarray, Q[n][f"D6pts-{h}"]); ax[i].scatter(x, y, s=3, color=c, alpha=0.3)
            xx = np.linspace(x.min(), x.max(), 2); ax[i].plot(xx, Q[n][f"D6-{h}"] * xx, color=c, lw=1, label=f"{n} {Q[n][f'D6-{h}']:.2f}")
        x, y = map(np.asarray, ref[f"D6pts-{h}"]); ax[i].scatter(x, y, s=4, color="k", alpha=0.4)
        xx = np.linspace(x.min(), x.max(), 2); ax[i].plot(xx, ref[f"D6-{h}"] * xx, "k", lw=2.2, label=f"ERA5 {ref[f'D6-{h}']:.2f}")
        ax[i].set_xlabel("40-day mean heat-flux anomaly, 100 hPa 45-75 [K m/s]"); ax[i].set_ylabel("polar-cap T anomaly, 50 hPa [K]")
        ax[i].set_title(f"{h}H: {'Jan-Mar' if h == 'N' else 'Jul-Oct'}"); ax[i].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "variability_heatflux.png"), dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5))
    for c, n in zip(COL, names):
        x, y = map(np.asarray, Q[n]["D7pts"]); ax.scatter(x, y, s=8, color=c, alpha=0.5)
        xx = np.linspace(x.min(), x.max(), 2); ax.plot(xx, Q[n]["D7"] * xx, color=c, lw=1, label=f"{n} {Q[n]['D7']:.2f} (r {Q[n]['D7r']:.2f})")
    x, y = map(np.asarray, ref["D7pts"]); ax.scatter(x, y, s=10, color="k")
    xx = np.linspace(x.min(), x.max(), 2); ax.plot(xx, ref["D7"] * xx, "k", lw=2.2, label=f"CLaMS/ERA5 {ref['D7']:.2f} (r {ref['D7r']:.2f})")
    ax.set_xlabel("3-month w* anomaly, 70 hPa 15S-15N [mm/s]"); ax.set_ylabel("age anomaly, 55 hPa 10S-10N [yr]")
    ax.legend(fontsize=7); ax.set_title("Age vs tropical upwelling (monthly anomalies)")
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "variability_age_wstar.png"), dpi=110); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5)); mm = np.arange(1, 13)
    ax.plot(mm, ref["w70_clim"], "k", lw=2.2, label="ERA5")
    for c, n in zip(COL, names):
        ax.plot(mm, Q[n]["w70_clim"], color=c, lw=1, label=n)
    ax.set_xticks(mm); ax.set_xlabel("month"); ax.set_ylabel("w* 70 hPa, 15S-15N [mm/s]"); ax.legend(fontsize=7, ncol=3)
    ax.set_title("Seasonal cycle of tropical upwelling")
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "variability_seasonal.png"), dpi=110); plt.close(fig)


# ----------------------------------------------------------------------------- main
def fmt(x):
    if isinstance(x, (int, np.integer)):
        return str(x)
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.2f}" if abs(x) < 10 else f"{x:.1f}"


def status(e):
    return "✅" if e <= 1.0 else ("⚠️" if e <= 1.5 else "❌")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("outdir"); ap.add_argument("runs", nargs="+")
    ap.add_argument("--era5-dir", required=True); ap.add_argument("--t0", default="2006-01-01"); ap.add_argument("--t1", default="2011-01-01")
    ap.add_argument("--long", default=None); ap.add_argument("--long-dir", default=None)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = int(a.t0[:4]), int(a.t1[:4])
    yrs = list(range(y0, y1))
    ez = Z.load([os.path.join(a.era5_dir, f"era5_{y}.npz") for y in yrs])
    ref = quantities(ez, age=clams_monthly_age(yrs))
    Q = {}
    for spec in a.runs:
        n, f = spec.split("=", 1)
        Q[n] = quantities(Z.load([f], a.t0, a.t1)); print(f"[D] {n} done", flush=True)
    E = {n: errors(Q[n], ref) for n in Q}
    long = None
    if a.long:
        l0, l1 = map(int, a.long.split("-"))
        lz = Z.load([os.path.join(a.long_dir or a.era5_dir, f"era5_{y}.npz") for y in range(l0, l1 + 1)])
        lq = {}   # long ERA5 context: D1, D2, D5, D6, SSWs (no D7: CLaMS starts 2004)
        y, mo = lz.months()
        for h, H in HEMI.items():
            u = lz.at_lat("u", 10.0, H["lat"]); win = np.isin(mo, H["djf"])
            wy = np.where(mo == 12, y + 1, y) if h == "N" else y
            ub = lz.band("u", 10.0, *H["band"])
            vals = [ub[win & (wy == yy)].mean() for yy in np.unique(wy[win]) if (win & (wy == yy)).sum() >= 85]
            lq[f"D1-{h}"] = float(np.std(vals, ddof=1))
            sd5 = [np.std(vals[i:i + 5], ddof=1) for i in range(len(vals) - 4)] or [np.nan]   # every 5-winter window
            lq[f"D1_5yr_range-{h}"] = [float(np.min(sd5)), float(np.max(sd5))]
            lq[f"D2-{h}"] = float(np.std(anomaly(u, lz.days)[win]))
            hf = H["sign"] * lz.vT(100.0, *H["hf"]); hfa = anomaly(hf, lz.days); lq[f"D5-{h}"] = float(np.std(hfa[win]))
            Ta = anomaly(lz.band("T", 50.0, *H["cap"]), lz.days)
            c = np.concatenate([[0.0], np.cumsum(hfa)]); x = np.full(hfa.size, np.nan); x[39:] = (c[40:] - c[:-40]) / 40
            k = np.isin(mo, H["rel"]) & np.isfinite(x)
            lq[f"D6-{h}"] = float(np.polyfit(x[k], Ta[k], 1)[0])
            if h == "N":
                ev = ssw_dates(u, lz.days); lq["SSW-N"] = [str(e) for e in ev]; lq["SSW_per_winter-N"] = len(ev) / (l1 - l0 + 1)
        long = dict(years=a.long, **lq)

    names = list(Q)
    L = ["| metric | ERA5 / CLaMS (same days) | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for i, (mid, lab, _, rv, _) in enumerate(E[names[0]]):
        L.append(f"| **{mid}** {lab} | {fmt(rv)} | " + " | ".join(f"{status(E[n][i][4])} {fmt(E[n][i][2])}" for n in names) + " |")
    L += ["", "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    L.append("| **D variability, mean err** | " + " | ".join(f"**{np.mean([e[4] for e in E[n]]):.2f}**" for n in names) + " |")
    L.append("| passed (✅) / total | " + " | ".join(f"{sum(e[4] <= 1 for e in E[n])} / {len(E[n])}" for n in names) + " |")
    L.append("Relation correlations r: D6-N/S, D7: ERA5 " + f"{ref['D6r-N']:.2f} / {ref['D6r-S']:.2f}, {ref['D7r']:.2f}; " +
             "; ".join(f"{n} {Q[n]['D6r-N']:.2f} / {Q[n]['D6r-S']:.2f}, {Q[n]['D7r']:.2f}" for n in names))
    if long:
        L += ["", f"ERA5 {long['years']} for context: D1 {long['D1-N']:.1f} / {long['D1-S']:.1f} m/s (5-winter windows "
              f"{long['D1_5yr_range-N'][0]:.1f}-{long['D1_5yr_range-N'][1]:.1f} N, {long['D1_5yr_range-S'][0]:.1f}-{long['D1_5yr_range-S'][1]:.1f} S), "
              f"D2 {long['D2-N']:.1f} / {long['D2-S']:.1f}, D5 {long['D5-N']:.1f} / {long['D5-S']:.1f}, D6 {long['D6-N']:.2f} / {long['D6-S']:.2f}, "
              f"NH SSWs {len(long['SSW-N'])} ({long['SSW_per_winter-N']:.2f} per winter)"]
    open(os.path.join(a.outdir, "variability_table.md"), "w").write("\n".join(L) + "\n")
    strip = lambda q: {k: v for k, v in q.items() if not (k.startswith("u10") or k.endswith("pts") or "pts-" in k or k == "days")}
    json.dump({"ref": strip(ref), "long": long,
               "runs": {n: {"q": strip(Q[n]), "metrics": [dict(group="D", id=i, label=l, model=m, ref=r, err=e) for i, l, m, r, e in E[n]],
                            "D": float(np.mean([e[4] for e in E[n]]))} for n in names}},
              open(os.path.join(a.outdir, "variability.json"), "w"), indent=1, default=float)
    figures(a.outdir, Q, ref)
    print("\n".join(L))


if __name__ == "__main__":
    main()
