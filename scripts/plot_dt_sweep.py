#!/usr/bin/env python3
"""Phase 7: one figure for the time-step sweep.

    python scripts/plot_dt_sweep.py METRICS.md THROUGHPUT.csv OUT.png \
        --status "dt60:1:blew up, chunk 2 (T 42 K)" --status "dt120:1:NaN in chunk 1" ...

Reads strat_compare's ``strat_metrics.md`` (run labels ``dt<min>`` or ``dt<min>_it2``) and
``throughput.csv`` (runs ``p7_dt<min>[_it2]``; the 12-min Phase 6 run ``p6_pk_g4_t15_s05_top3``).

Four panels against the time step: T RMSE and u RMSE (100-1 hPa, annual, vs ERA5), the two
polar-night jets with the ERA5 values as dotted lines, and simulated days per hour. Filled
circles: one departure iteration; open squares: two. A run whose u RMSE exceeds 30 m/s is
"unphysical" and is drawn as a red cross at the top of each panel instead of a value; runs that
never produced a year (NaN, health-check stop) are given with ``--status`` and drawn the same way.
A status strip under the panels spells out every run's fate.
"""
import argparse, csv, re
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

C = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "violet": "#4a3aa7", "red": "#e34948",
     "ink": "#0b0b0b", "muted": "#52514e", "grid": "#e6e5e2"}
UNPHYSICAL_U = 30.0


def parse_metrics(path):
    rows = {}
    for line in open(path):
        if not line.startswith("| dt"):
            continue
        c = [x.strip() for x in line.strip("|\n").split("|")]
        if c[1] != "ERA5":
            continue
        m = re.match(r"dt(\d+)(_it2)?$", c[0])
        if not m:
            continue
        key = (int(m.group(1)), 2 if m.group(2) else 1)
        r = rows.setdefault(key, {})
        val = lambda s: float(re.match(r"(-?\d+(?:\.\d+)?)", s).group(1))
        ref = lambda s: float(re.search(r"ref (-?\d+)", s).group(1))
        if c[2] == "annual":
            r["T"], r["u"] = float(c[3]), float(c[4])
        if c[2] == "DJF":
            r["jetN"], r["jetN_ref"] = val(c[5]), ref(c[5])
        if c[2] == "JJA":
            r["jetS"], r["jetS_ref"] = val(c[6]), ref(c[6])
    return rows


def parse_throughput(path):
    thr = {}
    for r in csv.DictReader(open(path)):
        if r["run"] == "p6_pk_g4_t15_s05_top3":
            key = (12, 1)
        else:
            m = re.match(r"p7_dt(\d+)(_it2)?$", r["run"])
            if not m:
                continue
            key = (int(m.group(1)), 2 if m.group(2) else 1)
        thr[key] = (float(r["days_per_hr"]), float(r["e2e_days_per_hr"]))
    return thr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics"); ap.add_argument("throughput"); ap.add_argument("out")
    ap.add_argument("--status", action="append", default=[], help="dt<min>:<iterations>:<text> for runs without a year")
    a = ap.parse_args()
    rows, thr = parse_metrics(a.metrics), parse_throughput(a.throughput)
    failed = {}
    for s in a.status:
        lab, it, text = s.split(":", 2)
        failed[(int(lab.replace("dt", "")), int(it))] = text
    unphysical = {k: f"finite but unphysical (u RMSE {v['u']:.0f} m/s)" for k, v in rows.items() if v.get("u", 0) > UNPHYSICAL_U}
    good = {k: v for k, v in rows.items() if k not in unphysical}
    bad = {**failed, **unphysical}
    dts = sorted({k[0] for k in list(rows) + list(failed) + list(thr)})

    fig = plt.figure(figsize=(12, 9.5))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.55], hspace=0.45, wspace=0.28)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    strip = fig.add_subplot(gs[2, :]); strip.set_axis_off()

    def style(ax, ylabel):
        ax.grid(True, color=C["grid"]); ax.set_axisbelow(True)
        ax.set_xscale("log", base=2); ax.set_xticks(dts); ax.set_xticklabels([str(d) for d in dts])
        ax.set_xlabel("time step [min]"); ax.set_ylabel(ylabel)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)

    def line(ax, keyfn, color, it, label):
        ks = sorted(k for k in good if k[1] == it and keyfn(good[k]) is not None)
        if not ks: return
        ax.plot([k[0] for k in ks], [keyfn(good[k]) for k in ks], "-" if it == 1 else "--", color=color, lw=2,
                marker="o" if it == 1 else "s", ms=7, mfc=color if it == 1 else "white", label=label)

    def crosses(ax, floor=0.0):
        ymin, ymax = ax.get_ylim(); ymin = min(ymin, floor); ymax = max(ymax, ymin + 1.4 * (ymax - ymin) if ymax > ymin else 1.0)
        ax.set_ylim(ymin, ymax); y = ymax - 0.06 * (ymax - ymin)
        for (dt, it) in sorted(bad):
            ax.plot(dt * (1.0 if it == 1 else 1.06), y, "x", color=C["red"], ms=9, mew=2)
        ax.set_ylim(ymin, ymax + 0.08 * (ymax - ymin))

    ax = axes[0]; style(ax, "T RMSE 100-1 hPa vs ERA5 [K]")
    line(ax, lambda r: r.get("T"), C["blue"], 1, "1 departure iteration"); line(ax, lambda r: r.get("T"), C["blue"], 2, "2 iterations")
    ax.legend(frameon=False, fontsize=8, loc="upper left"); crosses(ax)
    ax = axes[1]; style(ax, "u RMSE 100-1 hPa vs ERA5 [m/s]")
    line(ax, lambda r: r.get("u"), C["orange"], 1, None); line(ax, lambda r: r.get("u"), C["orange"], 2, None); crosses(ax)
    ax = axes[2]; style(ax, "polar-night jet at 10 hPa [m/s]")
    line(ax, lambda r: r.get("jetN"), C["aqua"], 1, "u 60N, DJF"); line(ax, lambda r: r.get("jetS"), C["violet"], 1, "u 60S, JJA")
    line(ax, lambda r: r.get("jetN"), C["aqua"], 2, None); line(ax, lambda r: r.get("jetS"), C["violet"], 2, None)
    if good:
        k0 = sorted(good)[0]
        ax.axhline(good[k0]["jetN_ref"], color=C["aqua"], ls=":", lw=1.2); ax.axhline(good[k0]["jetS_ref"], color=C["violet"], ls=":", lw=1.2)
        ax.text(dts[0], good[k0]["jetS_ref"] + 1.5, "ERA5", color=C["violet"], fontsize=8)
        ax.text(dts[0], good[k0]["jetN_ref"] + 1.5, "ERA5", color=C["aqua"], fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower left"); crosses(ax)
    ax = axes[3]; style(ax, "simulated days per hour, one H100"); ax.set_yscale("log")
    for it, ls, lab in ((1, "-", "1 iteration"), (2, "--", "2 iterations")):
        ks = sorted(k for k in thr if k[1] == it and k not in bad)
        if ks:
            ax.plot([k[0] for k in ks], [thr[k][0] for k in ks], ls, color=C["blue"], lw=2, marker="o" if it == 1 else "s", mfc=C["blue"] if it == 1 else "white", label=f"stepping only, {lab}")
            ax.plot([k[0] for k in ks], [thr[k][1] for k in ks], ls, color=C["orange"], lw=2, marker="o" if it == 1 else "s", mfc=C["orange"] if it == 1 else "white", label=f"end-to-end, {lab}")
    ax.legend(frameon=False, fontsize=8, loc="upper left")

    # status strip
    allkeys = sorted(set(rows) | set(failed) | set(thr))
    lines = []
    for k in allkeys:
        dt, it = k
        tag = f"dt {dt:>3} min, {it} iteration{'s' if it > 1 else ''}:"
        if k in bad:
            lines.append((tag, bad[k], C["red"]))
        else:
            r = good[k]
            lines.append((tag, f"stable — T RMSE {r['T']:.1f} K, u RMSE {r['u']:.1f} m/s, jets {r.get('jetN', float('nan')):.0f} / {r.get('jetS', float('nan')):.0f} m/s"
                          + (f", {thr[k][0]:.0f} days/hr" if k in thr else ""), C["ink"]))
    y = 0.95
    strip.text(0.0, y, "Run status (red crosses in the panels mark the runs that produced no usable year)", fontsize=9.5, color=C["ink"], weight="bold", transform=strip.transAxes, va="top")
    for tag, text, col in lines:
        y -= 0.16
        strip.text(0.0, y, tag, fontsize=8.8, color=C["muted"], transform=strip.transAxes, va="top", family="monospace")
        strip.text(0.27, y, text, fontsize=8.8, color=col, transform=strip.transAxes, va="top")
    fig.suptitle("Phase 7: time-step sweep on the Phase 6 configuration, 2005 (ERA5 as the yardstick)", fontsize=12)
    fig.savefig(a.out, dpi=130, bbox_inches="tight"); print("wrote", a.out)


if __name__ == "__main__":
    main()
