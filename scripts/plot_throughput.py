#!/usr/bin/env python3
"""Bar chart of simulated days per hour across the project's configurations.

    python scripts/plot_throughput.py docs/outputs/throughput.csv docs/outputs/00_phase0/throughput.png

Reads the CSV that scripts/throughput.py --csv appends to. Every phase adds a bar.
"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main(csv_path: str, out_png: str) -> None:
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("no rows")
    labels = [f"{r['label']}\n{r['grid']} dt={float(r['dt_min']):g} min" for r in rows]
    vals = [float(r["days_per_hr"]) for r in rows]
    fig, ax = plt.subplots(figsize=(max(5, 1.8 * len(rows) + 2), 4.2))
    bars = ax.bar(range(len(rows)), vals, color="#4C78A8")
    for b, v, r in zip(bars, vals, rows):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f} d/hr\n{float(r['ms_per_step']):.0f} ms/step",
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("simulated days per wall-clock hour (1x H100)")
    ax.set_ylim(0, max(vals) * 1.3)
    ax.axhline(52, color="grey", ls="--", lw=0.8)
    ax.text(len(rows) - 0.5, 52, " JCM T63L95 full physics, A100 (design doc)", va="bottom",
            ha="right", fontsize=7, color="grey")
    ax.set_title("jcm-strat throughput by configuration")
    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    print("wrote", out_png)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
