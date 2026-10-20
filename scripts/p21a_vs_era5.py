#!/usr/bin/env python3
"""Phase 21a first check (Susanne 2026-10-08): the rerun of Phase 12 run 4 (full ECHAM physics, new jcm, fixed Lott-Miller,
ERA5 nudging below 400 hPa) against ERA5 only.

    JAX_PLATFORMS=cpu python scripts/p21a_vs_era5.py runs/p21echam_5yr OUTDIR [--years 1990-1994]

Writes to OUTDIR:
  eq_u_qbo.png         equatorial (5S-5N) monthly zonal-mean u, 100-1 hPa: model, ERA5 (same months), model - ERA5
  wstar_tropics.png    tropical (15S-15N) TEM w* profiles 100-1 hPa, annual / DJF / JJA: model vs ERA5
  wstar_sections.png   annual TEM w* latitude-pressure sections, model vs ERA5
  era5_check.md        the numbers behind the plots
ERA5 TEM inputs (cache/era5_ref/era5_tem_monthly_*.nc) exist only for 1996-2001, so the ERA5 w* is that period's
climatology, not the run's years; u is compared month by month for the run's own years. Model TEM w* at stride 1
(every 6-hourly frame), as in every Phase 15+ record.
"""
from __future__ import annotations

import argparse, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_score as ss              # noqa: E402
import strat_compare as sc            # noqa: E402

ERA5_TEM_YEARS = list(range(1996, 2002))
P_PROFILE = np.array([100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1], float)


def band_mean(field, lat, lo, hi):
    """Area-weighted mean over lo..hi deg of the LAST axis."""
    m = (lat >= lo) & (lat <= hi); w = np.cos(np.deg2rad(lat[m]))
    return np.sum(field[..., m] * w, axis=-1) / np.sum(w)


def to_levels(prof, p_src, p_dst):
    """Interpolate along the first axis in log p (p_src any order)."""
    o = np.argsort(p_src)
    return np.array([np.interp(np.log(p_dst), np.log(p_src[o]), prof[o, k]) for k in range(prof.shape[1])]).T \
        if prof.ndim == 2 else np.interp(np.log(p_dst), np.log(p_src[o]), prof[o])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("rundir"); ap.add_argument("outdir"); ap.add_argument("--years", default="1990-1994")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = (int(v) for v in a.years.split("-")); years = list(range(y0, y1 + 1))
    nyr = y1 - y0 + 1
    print(f"[21a] loading {a.rundir} ({nyr} yr, all frames)", flush=True)
    fields, _, p_hpa, lat, (t0, t1, nt) = ss.load_model(a.rundir, window_years=nyr + 0.1, age_days=1)
    print(f"[21a] model {t0}..{t1}, {nt} frames", flush=True)
    lines = [f"# Phase 21a vs ERA5 (first check)\n", f"Run `{a.rundir}`, {t0} .. {t1}, {nt} frames (stride 1).\n"]

    # ---- equatorial u, month by month
    u_m = fields["u"].resample(time="1MS").mean()
    u_eq = band_mean(u_m.values, lat, -5, 5)                    # (month, level)
    era, _ = sc.load_era5(years, lat)
    plev = era.plev.values                                      # strat_compare puts ERA5 on its P_LEVELS ("plev")
    e_eq = band_mean(era["u"].transpose("time", "plev", "lat").values, lat, -5, 5)
    m_eq = np.array([to_levels(r, p_hpa, plev) for r in u_eq])
    n = min(len(m_eq), len(e_eq)); m_eq, e_eq = m_eq[:n], e_eq[:n]
    tt = np.arange(n) / 12.0 + y0
    sel = (plev <= 100) & (plev >= 1)
    fig, axs = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    for ax, d, ttl, cm, lim in ((axs[0], m_eq, "21a model", "RdBu_r", 40), (axs[1], e_eq, "ERA5", "RdBu_r", 40),
                                (axs[2], m_eq - e_eq, "model - ERA5", "PuOr_r", 20)):
        c = ax.contourf(tt, plev[sel], d[:, sel].T, levels=np.linspace(-lim, lim, 21), cmap=cm, extend="both")
        ax.contour(tt, plev[sel], d[:, sel].T, levels=[0], colors="k", linewidths=0.6)
        ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylabel("hPa"); ax.set_title(f"{ttl}: zonal-mean u, 5S-5N [m/s]")
        plt.colorbar(c, ax=ax, pad=0.01)
    axs[-1].set_xlabel("year"); fig.tight_layout(); fig.savefig(os.path.join(a.outdir, "eq_u_qbo.png"), dpi=110); plt.close(fig)
    rms = np.sqrt(np.mean((m_eq - e_eq)[:, sel] ** 2, axis=0)); corr = [np.corrcoef(m_eq[:, k], e_eq[:, k])[0, 1] for k in np.where(sel)[0]]
    lines += ["\n## Equatorial u (5S-5N), monthly, model vs ERA5 same months\n", "| hPa | RMSE [m/s] | correlation | std model / ERA5 [m/s] |", "|---|---|---|---|"]
    for k, (r, c) in zip(np.where(sel)[0], zip(rms, corr)):
        lines.append(f"| {plev[k]:g} | {r:.1f} | {c:.2f} | {m_eq[:, k].std():.1f} / {e_eq[:, k].std():.1f} |")

    # ---- TEM w*
    e_w = ss.era5_wstar(ERA5_TEM_YEARS)
    lines += [f"\n## Tropical (15S-15N) TEM w* [mm/s]: model {y0}-{y1} vs ERA5 {ERA5_TEM_YEARS[0]}-{ERA5_TEM_YEARS[-1]} climatology\n",
              "| hPa | " + " | ".join(f"{s} model / ERA5" for s in ss.SEASONS) + " |", "|---|" + "---|" * len(ss.SEASONS)]
    prof = {}
    for s, months in ss.SEASONS.items():
        pm, lm, _, wm = ss.wstar_fields(fields, months)
        pe, le, _, we = e_w[s]
        prof[s] = (to_levels(band_mean(wm, lm, -15, 15), pm, P_PROFILE) * 1e3, to_levels(band_mean(we, le, -15, 15), pe, P_PROFILE) * 1e3,
                   (pm, lm, wm, pe, le, we))
    for i, p in enumerate(P_PROFILE):
        lines.append(f"| {p:g} | " + " | ".join(f"{prof[s][0][i]:.2f} / {prof[s][1][i]:.2f}" for s in ss.SEASONS) + " |")
    fig, axs = plt.subplots(1, 3, figsize=(12, 5), sharey=True)
    for ax, s in zip(axs, ss.SEASONS):
        ax.plot(prof[s][0], P_PROFILE, "o-", label=f"21a model {y0}-{y1}")
        ax.plot(prof[s][1], P_PROFILE, "s--k", label=f"ERA5 {ERA5_TEM_YEARS[0]}-{ERA5_TEM_YEARS[-1]}")
        ax.axvline(0, color="grey", lw=0.5); ax.set_xscale("symlog", linthresh=0.1); ax.set_title(f"tropical w* 15S-15N, {s}")
        ax.set_xlabel("mm/s")
    axs[0].set_yscale("log"); axs[0].invert_yaxis(); axs[0].set_ylabel("hPa"); axs[0].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(a.outdir, "wstar_tropics.png"), dpi=110); plt.close(fig)

    pm, lm, wm, pe, le, we = prof["annual"][2]
    fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    lv = np.array([-3, -2, -1, -0.5, -0.2, -0.1, 0, 0.1, 0.2, 0.5, 1, 2, 3])
    for ax, (p, la, w, ttl) in zip(axs, ((pm, lm, wm, f"21a model {y0}-{y1}"), (pe, le, we, f"ERA5 {ERA5_TEM_YEARS[0]}-{ERA5_TEM_YEARS[-1]}"))):
        k = (p <= 100) & (p >= 1)
        c = ax.contourf(la, p[k], w[k] * 1e3, levels=lv, cmap="RdBu_r", extend="both")
        ax.set_yscale("log"); ax.set_xlim(-80, 80); ax.set_title(f"{ttl}: annual TEM w* [mm/s]"); ax.set_xlabel("latitude")
    axs[0].invert_yaxis(); axs[0].set_ylabel("hPa"); plt.colorbar(c, ax=axs, pad=0.01)
    fig.savefig(os.path.join(a.outdir, "wstar_sections.png"), dpi=110); plt.close(fig)
    open(os.path.join(a.outdir, "era5_check.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
