#!/usr/bin/env python3
"""Success metrics for stratospheric tracer transport (Susanne 2026-10-23): one table, fixed bounds, any set of runs.

    JAX_PLATFORMS=cpu python scripts/success_metrics.py OUTDIR NAME=runs/<agg> [NAME=runs/<agg> ...] [--t0 2006-01-01 --t1 2008-01-01]
        [--window-years 2]

--window-years must match t0..t1 (Phase 26 scores 2005-2009: --t0 2005-01-01 --t1 2010-01-01 --window-years 5).

The aggregates should hold only the window's years (scripts/sweep_score.py scores the LAST two years of an archive;
strat_circulation-style readers load every file). Raw scores come from sweep_score.py (w*, mass flux, ages; clocks
averaged over the whole window) and teq_score.py (jets and polar-cap T against ERA5 for the same months), written to
OUTDIR/raw/. Writes OUTDIR/success_metrics.md and OUTDIR/success_metrics.json.

Metrics and bounds ("moderate": about the size of the CLaMS - WACCM6 disagreement). err = |model - ref| / bound, or
|ln(model/ref)| / ln(factor) for w* and mass flux; pass err <= 1, near 1 < err <= 1.5, fail > 1.5.

  A1  tropical (10S-10N) entry age aoa150 at 55 hPa vs WACCM6 REF-D1 entry age             +- 0.25 yr
  A2  aoa150 vs CLaMS (ERA5) minus CLaMS' own tropical 150 hPa age, RMSE 100-5 hPa, |lat|<=80   < 0.4 yr
  A3  age step tropics -> 50-70 deg at 55 hPa, aoa150 vs the same step in CLaMS                +- 0.5 yr
  A4  tropical transit time 70 -> 10 hPa (aoa150 at 10 hPa minus at 70 hPa)                   2.3-3.2 yr (CLaMS 3.0, WACCM6 2.5)
  B1  tropical (15S-15N) annual w* at 100 / 70 / 50 / 30 / 10 hPa vs WACCM6                   factor 1.35 each
  B2  annual upward mass flux at 100 and 70 hPa vs WACCM6                                     +- 20 %
  C1  winter jet maximum at 50 and 10 hPa (DJF 30-90N, JJA 30-90S) vs ERA5: strength / latitude  +- 5 m/s / +- 4 deg
  C2  winter polar-cap (60-90) T bias at 50 hPa vs ERA5, DJF N / JJA S                          +- 2 K

Combined score: mean err within each group (A, B, C), then the mean of the three groups - lower is better, <= 1 means
"on average inside the bounds". ERA5 TEM w* (1996-2001, the years on disk) is shown for context, not scored.
"""
from __future__ import annotations

import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sweep_score as ss  # noqa: E402

B = dict(A1=0.25, A2=0.4, A3=0.5, A4=(2.3, 3.2), B1=1.35, B2=0.20, C1u=5.0, C1lat=4.0, C2=2.0)
W_LEV = (100, 70, 50, 30, 10)


def raw_scores(name, agg, outdir, t0, t1, years):
    raw = os.path.join(outdir, "raw"); os.makedirs(raw, exist_ok=True)
    sw, tq = os.path.join(raw, "sweep", f"{name}.json"), os.path.join(raw, "teq", f"{name}.json")
    if not os.path.exists(sw):
        subprocess.run([sys.executable, os.path.join(HERE, "sweep_score.py"), agg, "--name", name, "--out", os.path.dirname(sw),
                        "--window-years", f"{years:g}", "--age-days", f"{round(years * 365.25):d}", "--desc", f"success metrics {name}"], check=True)
    if not os.path.exists(tq):
        subprocess.run([sys.executable, os.path.join(HERE, "teq_score.py"), agg, "--t0", t0, "--t1", t1, "--name", name,
                        "--out", os.path.dirname(tq), "--desc", f"success metrics {name}"], check=True)
    return json.load(open(sw)), json.load(open(tq))


def status(e):
    return "✅" if e <= 1.0 else ("⚠️" if e <= 1.5 else "❌")


def metrics(s, t):
    """-> list of (group, id, label, model, ref, err)."""
    m = []
    a1, r1 = s["age_aoa150_55_tropics"], s["age_waccm_55_tropics"]
    m.append(("A", "A1", "entry age 55 hPa tropics [yr]", a1, r1, abs(a1 - r1) / B["A1"]))
    m.append(("A", "A2", "2-D age RMSE vs CLaMS [yr]", s["age_rmse_aoa150"], 0.0, s["age_rmse_aoa150"] / B["A2"]))
    st = s["age_aoa150_55_5070"] - s["age_aoa150_55_tropics"]; sc = s["age_clams_55_5070"] - s["age_clams_55_tropics"]
    m.append(("A", "A3", "age step tropics -> 50-70 deg, 55 hPa [yr]", st, sc, abs(st - sc) / B["A3"]))
    prof = np.asarray(s["profile_age150_tropics"]); pp = np.asarray(s["profile_age_p"]); o = np.argsort(pp)
    at = lambda lv: float(np.interp(np.log(lv), np.log(pp[o]), prof[o]))
    tr = at(10.0) - at(70.0); lo, hi = B["A4"]
    e4 = abs(tr - (lo + hi) / 2) / ((hi - lo) / 2)                  # <= 1 inside the range
    m.append(("A", "A4", "transit 70 -> 10 hPa [yr]", tr, (lo, hi), e4))
    for lv in W_LEV:
        a, r = s[f"wstar_annual_{lv}"], s[f"wstar_waccm_annual_{lv}"]
        m.append(("B", f"B1-{lv}", f"w* {lv} hPa [mm/s]", a, r, abs(np.log(max(a, 0.02) / r)) / np.log(B["B1"])))
    for lv in (100, 70):
        a, r = s[f"flux_annual_{lv}"], s[f"flux_waccm_annual_{lv}"]
        m.append(("B", f"B2-{lv}", f"mass flux {lv} hPa [1e9 kg/s]", a, r, abs(np.log(a / r)) / np.log(1 + B["B2"])))
    for key, lab in (("jet50_N", "NH 50 hPa"), ("jet10_N", "NH 10 hPa"), ("jet50_S", "SH 50 hPa"), ("jet10_S", "SH 10 hPa")):
        u, la, ue, lae = t[key]
        m.append(("C", f"C1-{key}", f"jet {lab} [m/s]", u, ue, abs(u - ue) / B["C1u"]))
        m.append(("C", f"C1-{key}-lat", f"jet {lab} latitude [deg]", la, lae, abs(abs(la) - abs(lae)) / B["C1lat"]))
    for h in ("N", "S"):
        m.append(("C", f"C2-{h}", f"polar-cap T bias 50 hPa {h} [K]", t[f"T50_cap_{h}"], 0.0, abs(t[f"T50_cap_{h}"]) / B["C2"]))
    return m


def combined(ms):
    g = {k: np.mean([e for (gg, *_, e) in ms if gg == k]) for k in "ABC"}
    return g, float(np.mean(list(g.values())))


def fmt(x):
    if isinstance(x, tuple):
        return f"{x[0]:g}-{x[1]:g}"
    if x == 0:
        return "0"
    return f"{x:.2f}" if abs(x) < 10 else f"{x:.1f}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("outdir"); ap.add_argument("runs", nargs="+")
    ap.add_argument("--t0", default="2006-01-01"); ap.add_argument("--t1", default="2008-01-01")
    ap.add_argument("--window-years", type=float, default=2.0)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    runs = [r.split("=", 1) for r in a.runs]
    res = {n: metrics(*raw_scores(n, p, a.outdir, a.t0, a.t1, a.window_years)) for n, p in runs}
    era5 = ss.era5_wstar(list(range(1996, 2002)))
    w_era5 = {}
    if era5 is not None:
        import strat_circulation as circ
        pe, lae, psie, we = era5["annual"]
        w_era5 = {lv: circ.tropical_wstar(pe * 100.0, we, lae, lv) for lv in W_LEV}
        w_era5.update({f"flux{lv}": circ.upward_mass_flux(pe * 100.0, psie, lv, lae) / 1e9 for lv in (100, 70)})
    names = [n for n, _ in runs]
    first = res[names[0]]
    L = ["| metric | reference | " + " | ".join(names) + " |", "|---|---|" + "---|" * len(names)]
    for i, (g, mid, lab, _, ref, _) in enumerate(first):
        extra = ""
        if mid.startswith("B1-") and w_era5:
            extra = f" (ERA5 {w_era5[int(mid[3:])]:.2f})"
        if mid.startswith("B2-") and w_era5:
            extra = f" (ERA5 {w_era5['flux' + mid[3:]]:.1f})"
        cells = [f"{status(res[n][i][5])} {fmt(res[n][i][3])}" for n in names]
        L.append(f"| **{mid}** {lab} | {fmt(ref)}{extra} | " + " | ".join(cells) + " |")
    summ = {n: combined(res[n]) for n in names}
    L += ["", "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for k, lab in (("A", "A age of air"), ("B", "B residual circulation"), ("C", "C polar vortex")):
        L.append(f"| {lab}, mean err | " + " | ".join(f"{summ[n][0][k]:.2f}" for n in names) + " |")
    L.append("| **combined score** | " + " | ".join(f"**{summ[n][1]:.2f}**" for n in names) + " |")
    L.append("| passed (✅) / total | " + " | ".join(f"{sum(e <= 1 for *_, e in res[n])} / {len(res[n])}" for n in names) + " |")
    open(os.path.join(a.outdir, "success_table.md"), "w").write("\n".join(L) + "\n")
    json.dump({n: {"metrics": [dict(group=g, id=i, label=l, model=mo, ref=r, err=e) for g, i, l, mo, r, e in res[n]],
                   "groups": summ[n][0], "combined": summ[n][1]} for n in names},
              open(os.path.join(a.outdir, "success_metrics.json"), "w"), indent=1, default=float)
    print("\n".join(L))


if __name__ == "__main__":
    main()
