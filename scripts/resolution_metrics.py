#!/usr/bin/env python3
"""Phase 9: one table and one figure for the resolution sweep.

    python scripts/resolution_metrics.py docs/outputs/09_resolution --run T63L95=runs/p8b_5yr \\
        --run T63L63=runs/p9_t63l63_5yr ... [--years 2005-2009] [--last-saves 73] \\
        [--throughput docs/outputs/throughput.csv]

Computes the age-of-air fidelity directly (model zonal-mean ``aoa`` over the last ``--last-saves``
5-day means against the CLaMS v3.1/ERA5 annual mean: RMSE and bias over (lat, ln p) 100-5 hPa
after interpolating the model in ln p onto CLaMS' pressure levels and linearly onto its
latitudes, cos-lat weighted; tropical (10S-10N) and 50-70 deg age at ~55 and ~12 hPa and their
contrast) and collects the rest from the per-run metric tables the existing scripts write:
``<outdir>/<LABEL>/circulation/circulation_metrics.md`` (strat_circulation.py: 70 hPa annual
up-flux, QBO deseasonalised std, 70->10 hPa transit), ``<outdir>/strat/strat_metrics.md``
(strat_compare.py: T and u RMSE 100-1 hPa vs ERA5, polar-night jets), ``<outdir>/<LABEL>/qbo_metrics.md``
(qbo_compare.py: RMS vs ERA5 equatorial monthly u 10-70 hPa) and ``throughput.csv`` (stepping and
end-to-end days per hour; median over the chain's segments). Grid, dt and column count come from
the run's ``.hydra/config.yaml``; the chain wall time from ``runs/<prefix>_chain.log``.

Writes ``<outdir>/resolution_metrics.md`` (metrics with reference rows, then per-metric ranks and
the mean rank - no weights are invented) and ``<outdir>/resolution_sweep.png`` (each metric
against the number of columns, one marker per vertical grid, references as dotted lines).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aoa_vs_clams as avc  # noqa: E402

# categorical slots 1-3 of the reference palette (fixed order: L95, L63, L47), text in ink tokens
C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "ink": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e2"}
VERT_STYLE = {95: ("L95", C["blue"], "o"), 63: ("L63", C["orange"], "s"), 47: ("L47", C["aqua"], "^")}
NODAL = {21: (64, 32), 31: (96, 48), 42: (128, 64), 63: (192, 96), 85: (256, 128), 106: (320, 160), 119: (360, 180), 170: (512, 256)}
WACCM_UPFLUX_70 = 6.1   # 10^9 kg/s, WACCM6 histSST 2005-2009, same method (circulation_metrics.md)


def interp_logp(field, p_src, p_dst):
    """(lev, lat) -> (len(p_dst), lat), linear in ln p, NaN outside the source range."""
    lp_s, lp_d = np.log(p_src), np.log(p_dst)
    order = np.argsort(lp_s)
    out = np.full((p_dst.size, field.shape[1]), np.nan)
    for j in range(field.shape[1]):
        col = field[order, j]
        ok = np.isfinite(col)
        if ok.sum() < 2:
            continue
        out[:, j] = np.interp(lp_d, lp_s[order][ok], col[ok], left=np.nan, right=np.nan)
    return out


def aoa_metrics(rundir, last_saves, clams, pmin=5.0, pmax=100.0):
    pm, latm, am, _ = avc.model_age(rundir, last_saves)
    pc, latc, ac = clams
    sel = (pc >= pmin) & (pc <= pmax)
    on_p = interp_logp(am, pm, pc[sel])                                  # (nsel, latm)
    on_lat = np.stack([np.interp(latc, latm[np.argsort(latm)], on_p[k][np.argsort(latm)]) for k in range(on_p.shape[0])])
    ref = ac[sel]
    d = on_lat - ref
    w = np.cos(np.deg2rad(latc))[None, :] * np.isfinite(d)
    rmse = float(np.sqrt(np.nansum(w * d ** 2) / np.sum(w)))
    bias = float(np.nansum(w * d) / np.sum(w))
    out = {"aoa_rmse": rmse, "aoa_bias": bias}
    for ptarget, tag in ((55.0, "55"), (12.0, "12")):
        k = int(np.argmin(np.abs(pm - ptarget))); prof = am[k]
        out[f"trop{tag}"] = avc.band(latm, prof, 0, 10)
        out[f"extra{tag}"] = avc.band(latm, prof, 50, 70)
        out[f"contrast{tag}"] = out[f"extra{tag}"] - out[f"trop{tag}"]
    return out


def clams_bands(clams):
    pc, latc, ac = clams
    out = {}
    for ptarget, tag in ((55.0, "55"), (12.0, "12")):
        k = int(np.argmin(np.abs(pc - ptarget))); prof = ac[k]
        out[f"trop{tag}"] = avc.band(latc, prof, 0, 10); out[f"extra{tag}"] = avc.band(latc, prof, 50, 70)
        out[f"contrast{tag}"] = out[f"extra{tag}"] - out[f"trop{tag}"]
    return out


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_circulation(path):
    """annual 70/100 hPa up-flux, QBO std at 10/20/30/50, transit 70->10 for the model row."""
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        if not line.startswith("| model"):
            continue
        c = _cells(line)
        if len(c) == 6 and c[1] == "annual":
            out["upflux70"], out["upflux100"] = float(c[2]), float(c[3])
        elif len(c) == 4 and "/" in c[1] and "/" in c[2] and "." in c[3] and len(c[1].split("/")) == 4:
            out["qbo_std"] = [float(v) for v in c[1].split("/")]
        elif len(c) == 4 and len(c[1].split("/")) == 5:
            out["transit"] = float(c[2])
    return out


def parse_strat(path):
    """{label: {T, u, jetN, jetN_ref, jetS, jetS_ref}} from the ERA5 annual/DJF/JJA rows."""
    rows = {}
    if not os.path.exists(path):
        return rows
    for line in open(path):
        if not line.startswith("|") or line.startswith("| run") or line.startswith("|---"):
            continue
        c = _cells(line)
        if len(c) < 7 or c[1] != "ERA5":
            continue
        r = rows.setdefault(c[0], {})
        val = lambda s: float(re.match(r"(-?\d+(?:\.\d+)?)", s).group(1))
        ref = lambda s: float(re.search(r"ref (-?\d+)", s).group(1))
        if c[2] == "annual":
            r["T"], r["u"] = float(c[3]), float(c[4])
        elif c[2] == "DJF":
            r["jetN"], r["jetN_ref"] = val(c[5]), ref(c[5])
        elif c[2] == "JJA":
            r["jetS"], r["jetS_ref"] = val(c[6]), ref(c[6])
    return rows


def parse_qbo(path):
    if not os.path.exists(path):
        return {}
    for line in open(path):
        if line.startswith("| after"):
            c = _cells(line)
            return {"qbo_rms": float(c[3].split()[0])}
    return {}


def parse_throughput(path, prefix):
    rows = [r for r in csv.DictReader(open(path)) if r["run"] == prefix or r["run"].startswith(prefix + "_")] if os.path.exists(path) else []
    if not rows:
        return {}
    med = lambda k: float(np.median([float(r[k]) for r in rows if r.get(k) not in (None, "", "0")] or [np.nan]))
    return {"days_per_hr": med("days_per_hr"), "ms_per_step": med("ms_per_step"), "e2e_days_per_hr": med("e2e_days_per_hr")}


def chain_hours(rundir):
    """Wall hours of the whole chain from runs/<prefix>_chain.log (first 'run' to 'chain finished')."""
    prefix = os.path.basename(rundir.rstrip("/")).replace("_5yr", "")
    log = os.path.join(os.path.dirname(rundir.rstrip("/")), f"{prefix}_chain.log")
    if not os.path.exists(log):
        return np.nan
    t0 = t1 = None
    for line in open(log):
        m = re.match(r"\[chain\] (\S+) (.*)", line)
        if not m:
            continue
        ts = dt.datetime.fromisoformat(m.group(1))
        if t0 is None and m.group(2).startswith("run "):
            t0 = ts
        if "chain finished" in m.group(2):
            t1 = ts
    return (t1 - t0).total_seconds() / 3600.0 if t0 and t1 else np.nan


def grid_info(rundir):
    cfg = yaml.safe_load(open(os.path.join(rundir, ".hydra", "config.yaml")))
    g = cfg["grid"]; trunc = int(g["spectral_truncation"]); layers = int(g["layers"])
    nlon, nlat = NODAL[trunc]
    return {"trunc": trunc, "layers": layers, "columns": nlon * nlat, "dt": float(cfg["run"]["time_step"]),
            "level_table": cfg.get("level_table") or "echam"}


def fmt(v, nd=2):
    return "-" if v is None or (isinstance(v, float) and not np.isfinite(v)) else f"{v:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir"); ap.add_argument("--run", action="append", required=True, help="LABEL=rundir")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--last-saves", type=int, default=73)
    ap.add_argument("--throughput", default=None)
    a = ap.parse_args()
    years = list(range(*[int(s) + i for i, s in enumerate(a.years.split("-"))]))
    runs = [tuple(r.split("=", 1)) for r in a.run]
    clams = avc.clams_age(years)
    cref = clams_bands(clams)
    strat = parse_strat(os.path.join(a.outdir, "strat", "strat_metrics.md"))

    R = {}
    for label, rundir in runs:
        m = grid_info(rundir)
        m.update(aoa_metrics(rundir, a.last_saves, clams))
        m.update(parse_circulation(os.path.join(a.outdir, label, "circulation", "circulation_metrics.md")))
        m.update(parse_qbo(os.path.join(a.outdir, label, "qbo_metrics.md")))
        m.update(strat.get(label, {}))
        if a.throughput:
            m.update(parse_throughput(a.throughput, os.path.basename(rundir.rstrip("/")).replace("_5yr", "")))
        m["hours"] = chain_hours(rundir)
        R[label] = m
        print(label, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items() if k != "qbo_std"})

    # ---- table
    hdr = ["run", "grid", "columns", "dt [min]", "AoA RMSE vs CLaMS 100-5 hPa [yr]", "AoA bias [yr]",
           "age 55 hPa tropics / 50-70 / contrast [yr]", "age 12 hPa tropics / 50-70 / contrast [yr]",
           "transit 70->10 hPa [yr]", "up-flux 70 hPa annual [1e9 kg/s]", "T RMSE 100-1 hPa vs ERA5 [K]",
           "u RMSE [m/s]", "u(60N,10hPa) DJF / u(60S) JJA [m/s]", "QBO RMS vs ERA5 10-70 hPa [m/s]",
           "stepping [d/hr]", "ms/step", "chain wall [h]"]
    lines = [f"# Resolution sweep: {a.years}, age of air from the last {a.last_saves} saves", "",
             "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for label, m in R.items():
        lines.append("| " + " | ".join([
            label, f"T{m['trunc']} L{m['layers']} ({m['level_table']})", f"{m['columns']}", f"{m['dt']:g}",
            fmt(m.get("aoa_rmse")), fmt(m.get("aoa_bias")),
            f"{fmt(m['trop55'])} / {fmt(m['extra55'])} / {fmt(m['contrast55'])}",
            f"{fmt(m['trop12'])} / {fmt(m['extra12'])} / {fmt(m['contrast12'])}",
            fmt(m.get("transit")), fmt(m.get("upflux70"), 1), fmt(m.get("T"), 1), fmt(m.get("u"), 1),
            f"{fmt(m.get('jetN'), 0)} / {fmt(m.get('jetS'), 0)}", fmt(m.get("qbo_rms"), 1),
            fmt(m.get("days_per_hr"), 0), fmt(m.get("ms_per_step"), 0), fmt(m.get("hours"), 1)]) + " |")
    ref_jets = next((f"{fmt(m['jetN_ref'], 0)} / {fmt(m['jetS_ref'], 0)}" for m in R.values() if "jetN_ref" in m), "-")
    lines.append("| " + " | ".join(["CLaMS v3.1 / ERA5", "1 deg, 39 levels", "-", "-", "0", "0",
                                    f"{fmt(cref['trop55'])} / {fmt(cref['extra55'])} / {fmt(cref['contrast55'])}",
                                    f"{fmt(cref['trop12'])} / {fmt(cref['extra12'])} / {fmt(cref['contrast12'])}",
                                    "2.94", "-", "-", "-", "-", "-", "-", "-", "-"]) + " |")
    lines.append("| " + " | ".join(["ERA5 / WACCM6 histSST", "-", "-", "-", "-", "-", "-", "-", "-", f"{WACCM_UPFLUX_70} (WACCM6)",
                                    "0", "0", ref_jets + " (ERA5)", "0", "-", "-", "-"]) + " |")
    # ---- ranks (lower is better for every error metric; contrast and up-flux as |model - reference|)
    rank_defs = [("AoA RMSE", lambda m: m.get("aoa_rmse")),
                 ("|age 55 hPa tropics - CLaMS|", lambda m: abs(m["trop55"] - cref["trop55"])),
                 ("|contrast 55 hPa - CLaMS|", lambda m: abs(m["contrast55"] - cref["contrast55"])),
                 ("|transit - CLaMS|", lambda m: abs(m["transit"] - 2.94) if "transit" in m else None),
                 ("|up-flux 70 - WACCM6|", lambda m: abs(m["upflux70"] - WACCM_UPFLUX_70) if "upflux70" in m else None),
                 ("T RMSE vs ERA5", lambda m: m.get("T")), ("u RMSE vs ERA5", lambda m: m.get("u")),
                 ("QBO RMS vs ERA5", lambda m: m.get("qbo_rms"))]
    labels = list(R)
    ranks = {l: [] for l in labels}
    lines += ["", "## Ranks (1 = closest to the reference; mean rank is unweighted)", "",
              "| run | " + " | ".join(n for n, _ in rank_defs) + " | mean rank |", "|" + "---|" * (len(rank_defs) + 2)]
    table = {l: {} for l in labels}
    for name, fn in rank_defs:
        vals = {l: fn(R[l]) for l in labels}
        have = [l for l in labels if vals[l] is not None and np.isfinite(vals[l])]
        order = sorted(have, key=lambda l: vals[l])
        for i, l in enumerate(order):
            table[l][name] = i + 1; ranks[l].append(i + 1)
    for l in labels:
        lines.append("| " + l + " | " + " | ".join(str(table[l].get(n, "-")) for n, _ in rank_defs)
                     + f" | {np.mean(ranks[l]):.2f} |" if ranks[l] else f"| {l} | " + " | ".join("-" for _ in rank_defs) + " | - |")
    lines += ["", "Ranks compare model runs only; the reference rows are the targets. Cost is reported, not ranked."]
    os.makedirs(a.outdir, exist_ok=True)
    md = os.path.join(a.outdir, "resolution_metrics.md")
    open(md, "w").write("\n".join(lines) + "\n"); print("wrote", md)

    # ---- figure: each metric against columns; marker/colour = vertical grid; references dotted
    panels = [("AoA RMSE vs CLaMS, 100-5 hPa [yr]", "aoa_rmse", None),
              ("tropical age at 55 hPa [yr]", "trop55", cref["trop55"]),
              ("age contrast 50-70 minus tropics, 55 hPa [yr]", "contrast55", cref["contrast55"]),
              ("tropical up-flux 70 hPa, annual [1e9 kg/s]", "upflux70", WACCM_UPFLUX_70),
              ("T RMSE 100-1 hPa vs ERA5 [K]", "T", None), ("u RMSE 100-1 hPa vs ERA5 [m/s]", "u", None),
              ("equatorial u RMS vs ERA5, 10-70 hPa [m/s]", "qbo_rms", None),
              ("stepping, simulated days per hour", "days_per_hr", None), ("chain wall time, 5 years [h]", "hours", None)]
    fig, axes = plt.subplots(3, 3, figsize=(13, 10.5))
    cols = sorted({m["columns"] for m in R.values()})
    truncs = {m["columns"]: m["trunc"] for m in R.values()}
    for ax, (title, key, ref) in zip(axes.ravel(), panels):
        for lay, (name, color, marker) in VERT_STYLE.items():
            pts = sorted((m["columns"], m.get(key)) for m in R.values() if m["layers"] == lay and m.get(key) is not None and np.isfinite(m.get(key)))
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=color, lw=2, marker=marker, ms=8, mfc=color, mec="white", mew=1, label=name)
        if ref is not None:
            ax.axhline(ref, color=C["muted"], ls=":", lw=1.2)
            ax.text(cols[0], ref, " reference", color=C["muted"], fontsize=8, va="bottom")
        ax.set_xscale("log", base=2); ax.set_xticks(cols); ax.set_xticklabels([f"T{truncs[c]}\n{c}" for c in cols], fontsize=8)
        ax.set_title(title, fontsize=9.5, color=C["ink"]); ax.grid(True, color=C["grid"]); ax.set_axisbelow(True)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        if key == "days_per_hr":
            ax.set_yscale("log")
        else:
            ax.set_ylim(bottom=0)          # errors and ages from zero, so a flat line reads as flat
            ax.set_ylim(top=ax.get_ylim()[1] * 1.08)
    axes[2, 0].set_xlabel("horizontal truncation / number of columns"); axes[2, 1].set_xlabel("horizontal truncation / number of columns")
    axes[0, 0].legend(frameon=False, fontsize=9, title="vertical grid", title_fontsize=9)
    fig.suptitle(f"Phase 9 resolution sweep, {a.years}: transport fidelity and cost against resolution", fontsize=12, color=C["ink"])
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    png = os.path.join(a.outdir, "resolution_sweep.png"); fig.savefig(png, dpi=130); print("wrote", png)


if __name__ == "__main__":
    main()
