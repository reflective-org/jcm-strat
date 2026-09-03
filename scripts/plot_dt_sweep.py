#!/usr/bin/env python3
"""Phase 7: metrics vs time step from strat_compare's strat_metrics.md and throughput.csv.

    python scripts/plot_dt_sweep.py docs/outputs/07_timestep/strat_metrics.md docs/outputs/throughput.csv OUT.png

Run labels must be of the form ``dt<minutes>[_it2]``. Four panels: T RMSE, u RMSE (100-1 hPa, annual,
vs ERA5), the two polar-night jets (DJF 60N, JJA 60S) with the ERA5 values as dashed lines, and
simulated days per hour (stepping and end-to-end). ``_it2`` runs (two departure iterations) are open markers.
"""
import re, sys, csv
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

metrics_md, csv_path, out = sys.argv[1:4]
rows = {}
for line in open(metrics_md):
    if not line.startswith("| dt"): continue
    c = [x.strip() for x in line.strip("|\n").split("|")]
    if c[1] != "ERA5" or c[2] != "annual": continue
    m = re.match(r"dt(\d+)(_it2)?", c[0]); dt = int(m.group(1)); it2 = bool(m.group(2))
    un = re.match(r"(-?\d+) \(ref (-?\d+)\)", c[5]); us = re.match(r"(-?\d+) \(ref (-?\d+)\)", c[6])
    rows[(dt, it2)] = dict(T=float(c[3]), u=float(c[4]), un=float(un.group(1)), un_ref=float(un.group(2)),
                           us=float(us.group(1)), us_ref=float(us.group(2)))
# DJF/JJA jets come from the seasonal rows
for line in open(metrics_md):
    if not line.startswith("| dt"): continue
    c = [x.strip() for x in line.strip("|\n").split("|")]
    if c[1] != "ERA5": continue
    m = re.match(r"dt(\d+)(_it2)?", c[0]); key = (int(m.group(1)), bool(m.group(2)))
    if c[2] == "DJF": rows[key]["jetN"] = float(re.match(r"(-?\d+)", c[5]).group(1)); rows[key]["jetN_ref"] = float(re.search(r"ref (-?\d+)", c[5]).group(1))
    if c[2] == "JJA": rows[key]["jetS"] = float(re.match(r"(-?\d+)", c[6]).group(1)); rows[key]["jetS_ref"] = float(re.search(r"ref (-?\d+)", c[6]).group(1))
thr = {}
for r in csv.DictReader(open(csv_path)):
    m = re.match(r"p7_dt(\d+)(_it2)?", r["run"]) or (re.match(r"p6_pk_g4_t15_s05_top3", r["run"]) and re.match(r"(12)()", "12"))
    if m: thr[(int(m.group(1)), bool(m.group(2)))] = (float(r["days_per_hr"]), float(r["e2e_days_per_hr"]))
C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7", "muted": "#52514e", "grid": "#e6e5e2"}
fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
def series(key_fn, ax, color, label, it2, ls="-"):
    ks = sorted(k for k in rows if k[1] == it2); xs = [k[0] for k in ks]; ys = [key_fn(rows[k]) for k in ks]
    ax.plot(xs, ys, ls, color=color, lw=2, marker="o" if not it2 else "s", mfc=color if not it2 else "white", label=label)
for ax in axes.flat: ax.grid(True, color=C["grid"]); ax.set_axisbelow(True); ax.set_xscale("log", base=2); ax.set_xticks([12, 30, 60, 90, 120]); ax.set_xticklabels(["12", "30", "60", "90", "120"]); ax.set_xlabel("time step [min]")
ax = axes[0, 0]; series(lambda r: r["T"], ax, C["blue"], "1 departure iteration", False); series(lambda r: r["T"], ax, C["blue"], "2 iterations", True, "--"); ax.set_ylabel("T RMSE 100-1 hPa vs ERA5 [K]"); ax.legend(frameon=False, fontsize=8)
ax = axes[0, 1]; series(lambda r: r["u"], ax, C["orange"], "1 iteration", False); series(lambda r: r["u"], ax, C["orange"], "2 iterations", True, "--"); ax.set_ylabel("u RMSE 100-1 hPa vs ERA5 [m/s]")
ax = axes[1, 0]
series(lambda r: r["jetN"], ax, C["aqua"], "u 60N DJF", False); series(lambda r: r["jetS"], ax, C["violet"], "u 60S JJA", False)
series(lambda r: r["jetN"], ax, C["aqua"], None, True, "--"); series(lambda r: r["jetS"], ax, C["violet"], None, True, "--")
k0 = sorted(rows)[0]; ax.axhline(rows[k0]["jetN_ref"], color=C["aqua"], ls=":", lw=1); ax.axhline(rows[k0]["jetS_ref"], color=C["violet"], ls=":", lw=1)
ax.set_ylabel("polar-night jet at 10 hPa [m/s]  (dotted: ERA5)"); ax.legend(frameon=False, fontsize=8)
ax = axes[1, 1]
for it2, ls, lab in ((False, "-", "1 iteration"), (True, "--", "2 iterations")):
    ks = sorted(k for k in thr if k[1] == it2)
    if ks:
        ax.plot([k[0] for k in ks], [thr[k][0] for k in ks], ls, color=C["blue"], lw=2, marker="o", mfc=C["blue"] if not it2 else "white", label=f"stepping, {lab}")
        ax.plot([k[0] for k in ks], [thr[k][1] for k in ks], ls, color=C["orange"], lw=2, marker="o", mfc=C["orange"] if not it2 else "white", label=f"end-to-end, {lab}")
ax.set_yscale("log"); ax.set_ylabel("simulated days per hour (1 H100)"); ax.legend(frameon=False, fontsize=8)
fig.suptitle("Phase 7: time-step sweep on the Phase 6 configuration, 2005"); fig.tight_layout(); fig.savefig(out, dpi=130); print("wrote", out)
