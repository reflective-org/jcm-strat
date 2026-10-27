#!/usr/bin/env python3
"""Comparison figures for the transport scorecard (Phase 24): all runs on one axis against CLaMS / WACCM6 / ERA5.

    JAX_PLATFORMS=cpu python scripts/report_figures.py OUTDIR NAME=SWEEP_JSON:DIAG_DIR [...]

SWEEP_JSON is a success-metrics raw score (sweep_score.py, window 2006-2007, clocks averaged over the window); DIAG_DIR holds
that run's vortex_jets.md. Writes OUTDIR/{age_profile,age_latitude,wstar_profile,jets}.png.
Run colours: a brand-derived set validated for separation (OKLab dE x100: normal >= 16.3, deutan/protan >= 10.8), plus a
marker per run; references in grey with their own dash patterns.
"""
from __future__ import annotations

import json, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sweep_score as ss  # noqa: E402
import strat_circulation as circ  # noqa: E402

STYLE = {"P20b": ("#242729", "o"), "AL7": ("#6f382a", "s"), "AL7h": ("#b18e63", "P"), "AL7t": ("#5e7227", "v"),
         "L0": ("#25a3b2", "^"), "LAL7": ("#6f6194", "D")}
REF = {"CLaMS (ERA5)": dict(color="#5f6264", ls="--", lw=2.4), "WACCM6": dict(color="#8B8D8E", ls=":", lw=2.4),
       "ERA5": dict(color="#5f6264", ls="--", lw=2.4)}
INK, MUTED, GRID = "#282C2E", "#5f6264", "#E4E1DD"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "legend.frameon": False})


def run_line(ax, name, x, y, every=None):
    c, m = STYLE[name]
    ax.plot(x, y, color=c, lw=2, marker=m, ms=5, markevery=every, label=name)


def log_p(ax, top, bottom):
    ax.set_yscale("log"); ax.set_ylim(bottom, top)
    ticks = [t for t in (1, 2, 5, 10, 20, 50, 100, 200) if top <= t <= bottom]
    ax.set_yticks(ticks); ax.set_yticklabels([str(t) for t in ticks]); ax.minorticks_off(); ax.set_ylabel("pressure [hPa]")


def jets_table(md):
    """vortex_jets.md -> {season: {source: (p list, umax list, lat list)}}."""
    out, season = {}, None
    for line in open(md):
        if line.startswith("## DJF"): season = "DJF"
        elif line.startswith("## JJA"): season = "JJA"
        elif season and re.match(r"^\| \d", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            p = float(cells[0])
            for k, cell in zip(("model", "ERA5", "WACCM6"), cells[1:4]):
                mm = re.match(r"([-\d.]+) @ ([-\d.]+)", cell)
                if mm:
                    out.setdefault(season, {}).setdefault(k, ([], [], []))
                    out[season][k][0].append(p); out[season][k][1].append(float(mm.group(1))); out[season][k][2].append(float(mm.group(2)))
    return out


def main():
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    runs = {}
    for arg in sys.argv[2:]:
        name, rest = arg.split("=", 1); sw, dd = rest.split(":", 1)
        runs[name] = (json.load(open(sw)), dd)
    first = next(iter(runs.values()))[0]
    pw, latw, aw = ss.waccm_age_ref()

    # 1. tropical entry-age profile
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    for n, (s, _) in runs.items():
        p = np.asarray(s["profile_age_p"]); a = np.asarray(s["profile_age150_tropics"]); k = (p >= 1) & (p <= 100)
        run_line(ax, n, a[k], p[k], every=6)
    pc = np.asarray(first["profile_clams_p"]); ac = np.asarray(first["profile_clams_entry_tropics"]); k = (pc >= 1) & (pc <= 100)
    ax.plot(ac[k], pc[k], label="CLaMS (ERA5)", **REF["CLaMS (ERA5)"])
    tm = np.abs(latw) <= 10; aw_t = np.nanmean(aw[:, tm], axis=1); k = (pw >= 1) & (pw <= 100)
    ax.plot(aw_t[k], pw[k], label="WACCM6", **REF["WACCM6"])
    log_p(ax, 1, 100); ax.set_xlabel("entry age of air, 10S-10N [years]"); ax.set_xlim(left=0)
    ax.legend(loc="upper left", fontsize=9); fig.tight_layout(); fig.savefig(os.path.join(outdir, "age_profile.png"), dpi=150); plt.close(fig)

    # 2. entry age against latitude at 55 and 12 hPa
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=False)
    for ax, lv in zip(axes, (55, 12)):
        for n, (s, _) in runs.items():
            run_line(ax, n, s["profile_lat"], s[f"profile_age150_{lv}"], every=8)
        ax.plot(first["profile_clams_lat"], first[f"profile_clams_entry_{lv}"], label="CLaMS (ERA5)", **REF["CLaMS (ERA5)"])
        kk = int(np.argmin(np.abs(pw - lv))); ax.plot(latw, aw[kk], label="WACCM6", **REF["WACCM6"])
        ax.set_title(f"{lv} hPa", color=INK, fontsize=11, loc="left"); ax.set_xlabel("latitude"); ax.set_xlim(-90, 90)
        ax.set_xticks([-90, -60, -30, 0, 30, 60, 90]); ax.set_ylim(bottom=0)
    axes[0].set_ylabel("entry age of air [years]"); axes[1].legend(loc="lower center", ncol=4, fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "age_latitude.png"), dpi=150); plt.close(fig)

    # 3. tropical w* profile
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    for n, (s, _) in runs.items():
        p = np.asarray(s["profile_p"]); w = np.asarray(s["profile_wstar_tropics"]); k = (p >= 5) & (p <= 120)
        run_line(ax, n, w[k], p[k], every=5)
    p = np.asarray(first["profile_waccm_p"]); w = np.asarray(first["profile_waccm_wstar_tropics"]); k = (p >= 5) & (p <= 120)
    ax.plot(w[k], p[k], label="WACCM6", **REF["WACCM6"])
    e = ss.era5_wstar(list(range(1996, 2002)))
    if e is not None:
        pe, lae, _, we = e["annual"]; t = np.abs(lae) <= 15; wg = np.cos(np.deg2rad(lae[t]))
        prof = np.array([np.nansum(we[i, t] * wg) / wg.sum() for i in range(pe.size)]); k = (pe >= 5) & (pe <= 120)
        ax.plot(prof[k], pe[k], label="ERA5 (1996-2001)", **REF["ERA5"])
    log_p(ax, 5, 120); ax.set_xlabel("residual vertical velocity w*, 15S-15N [mm/s]"); ax.set_xlim(left=0)
    ax.legend(loc="lower right", fontsize=9); fig.tight_layout(); fig.savefig(os.path.join(outdir, "wstar_profile.png"), dpi=150); plt.close(fig)

    # 4. winter jet maximum against height
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
    refs_done = False
    for n, (_, dd) in runs.items():
        tab = jets_table(os.path.join(dd, "vortex_jets.md"))
        for ax, season in zip(axes, ("DJF", "JJA")):
            pp, uu, _ = tab[season]["model"]; c, m = STYLE[n]
            ax.plot(uu, pp, color=c, marker=m, ms=5, lw=2, label=n)
            if not refs_done:
                pe_, ue, _ = tab[season]["ERA5"]; ax.plot(ue, pe_, label="ERA5", **REF["ERA5"])
                pw_, uw, _ = tab[season]["WACCM6"]; ax.plot(uw, pw_, label="WACCM6", **REF["WACCM6"])
        refs_done = True
    for ax, title in zip(axes, ("DJF, northern winter (30-90N)", "JJA, southern winter (30-90S)")):
        log_p(ax, 1, 50); ax.set_title(title, color=INK, fontsize=11, loc="left"); ax.set_xlabel("jet maximum, zonal-mean u [m/s]")
    axes[1].set_ylabel("")
    h, l = axes[1].get_legend_handles_labels(); order = [i for i, x in enumerate(l) if x in STYLE] + [i for i, x in enumerate(l) if x not in STYLE]
    axes[1].legend([h[i] for i in order], [l[i] for i in order], loc="lower right", fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "jets.png"), dpi=150); plt.close(fig)
    print("wrote", outdir)


if __name__ == "__main__":
    main()
