#!/usr/bin/env python3
"""Phase 15: leaderboard + figures from the per-run score files, written into the living record.

    python scripts/sweep_leaderboard.py docs/outputs/15_sweep [--scores docs/outputs/15_sweep/scores]

Reads every ``<scores>/*.json`` written by scripts/sweep_score.py and writes, in the output directory:
  leaderboard.md            all runs sorted by the composite (lower = closer to CLaMS / ERA5 / WACCM6), with the parts,
                            the Phase 12/13 table numbers and the cost
  sweep_wstar_profiles.png  tropical w* profiles 200-1 hPa of every run vs WACCM6
  sweep_age_profiles.png    entry-age clock at 55 and 12 hPa and the tropical profile vs CLaMS (entry age = AGE - 0.09 yr)
  sweep_scores.png          the composite and its four parts per run
and replaces the block between ``<!-- leaderboard:start -->`` and ``<!-- leaderboard:end -->`` in ``output.md`` (if present)
with the table and a factual summary of the best run against the base, so the record updates itself after every run.
"""
from __future__ import annotations

import argparse, glob, json, os, datetime as dt
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

W_LEVELS = (100.0, 70.0, 50.0, 30.0, 10.0)


def load(scores_dir):
    runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(scores_dir, "*.json")))]
    return sorted(runs, key=lambda r: r["composite"])


def fmt(x, nd=2, plus=False):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:+.{nd}f}" if plus else f"{x:.{nd}f}"


def table(runs):
    base = next((r for r in runs if r["name"] == "base"), None)
    ref = runs[0]
    head = ["rank", "run", "stage", "composite", "age RMSE `aoa150` vs CLaMS-entry [yr]", "age bias", "w* log-err", "u RMSE [m/s]", "T RMSE [K]",
            "w* 100/70/50/30/10 hPa [mm/s]", "`aoa150` 55 hPa trop / 50-70", "`aoa150` 12 hPa trop / 50-70", "`aoa_sfc` RMSE vs CLaMS", "w* 1 hPa trop / NH / SH", "min/yr", "what"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for i, r in enumerate(runs, 1):
        w = "/".join(fmt(r.get(f"wstar_annual_{lv:g}"), 2) for lv in W_LEVELS)
        lines.append("| " + " | ".join([
            str(i), f"**{r['name']}**" if r is ref else r["name"], str(r.get("stage", "")), fmt(r["composite"], 3),
            fmt(r.get("age_rmse_aoa150")), fmt(r.get("age_bias_aoa150"), 2, True), fmt(r.get("w_logerr")), fmt(r.get("u_rmse"), 1), fmt(r.get("T_rmse"), 1),
            w, f"{fmt(r.get('age_aoa150_55_tropics'))} / {fmt(r.get('age_aoa150_55_5070'))}", f"{fmt(r.get('age_aoa150_12_tropics'))} / {fmt(r.get('age_aoa150_12_5070'))}",
            fmt(r.get("age_rmse_aoa_sfc")), f"{fmt(r.get('meso_1_tropics'))} / {fmt(r.get('meso_1_nh'))} / {fmt(r.get('meso_1_sh'))}",
            fmt(r.get("minutes_per_year"), 0), r.get("desc", "")]) + " |")
    r = ref
    refrow = ("| | *references* | | | CLaMS entry age (AGE − {:.2f}) | | WACCM6 | ERA5 | ERA5 | {} | CLaMS {} / {} (WACCM entry {} / {}) | CLaMS {} / {} (WACCM {} / {}) | | full ECHAM 1994: +0.96 / −1.29 / −3.19 | | |"
              .format(r.get("clams_offset_150", 0.09), "/".join(fmt(r.get(f"wstar_waccm_annual_{lv:g}")) for lv in W_LEVELS),
                      fmt(r.get("age_clams_55_tropics") - r.get("clams_offset_150", 0.09) if r.get("age_clams_55_tropics") is not None else None),
                      fmt(r.get("age_clams_55_5070") - r.get("clams_offset_150", 0.09) if r.get("age_clams_55_5070") is not None else None),
                      fmt(r.get("age_waccm_55_tropics")), fmt(r.get("age_waccm_55_5070")),
                      fmt(r.get("age_clams_12_tropics") - r.get("clams_offset_150", 0.09) if r.get("age_clams_12_tropics") is not None else None),
                      fmt(r.get("age_clams_12_5070") - r.get("clams_offset_150", 0.09) if r.get("age_clams_12_5070") is not None else None),
                      fmt(r.get("age_waccm_12_tropics")), fmt(r.get("age_waccm_12_5070"))))
    lines.append(refrow)
    return "\n".join(lines), base, ref


def summary(runs, base, ref):
    if not runs:
        return "_no scored runs yet_"
    n = len(runs); now = dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=-7))).strftime("%Y-%m-%d %H:%M PDT")
    s = [f"{n} scored run(s) as of {now}. Composite = mean(age RMSE/0.5 yr, w* log-error/ln 1.5, u RMSE/5 m/s, T RMSE/5 K); lower is closer; "
         "the age term is the entry-age clock against CLaMS (AGE minus CLaMS' own 0.09 yr at 150 hPa), w* against WACCM6, u and T against ERA5 (same months)."]
    if base is not None and ref is not base:
        d = lambda k, nd=2: f"{fmt(ref.get(k), nd)} (base {fmt(base.get(k), nd)})"
        s.append(f"**Best so far: `{ref['name']}`** — {ref.get('desc', '')}: composite {d('composite', 3)}; age RMSE {d('age_rmse_aoa150')} yr, "
                 f"bias {fmt(ref.get('age_bias_aoa150'), 2, True)} (base {fmt(base.get('age_bias_aoa150'), 2, True)}); tropical w* 100/70/50/30/10 hPa "
                 + "/".join(fmt(ref.get(f'wstar_annual_{lv:g}')) for lv in W_LEVELS) + " (base " + "/".join(fmt(base.get(f'wstar_annual_{lv:g}')) for lv in W_LEVELS)
                 + ", WACCM6 " + "/".join(fmt(ref.get(f'wstar_waccm_annual_{lv:g}')) for lv in W_LEVELS) + f"); u RMSE {d('u_rmse', 1)} m/s, T RMSE {d('T_rmse', 1)} K; "
                 f"`aoa150` 55 hPa tropics {d('age_aoa150_55_tropics')} / 50-70 {d('age_aoa150_55_5070')}, 12 hPa tropics {d('age_aoa150_12_tropics')} yr; cost {d('minutes_per_year', 0)} min/yr.")
        better = [r["name"] for r in runs if r["composite"] < base["composite"] - 1e-9 and r is not base]
        worse = [r["name"] for r in runs if r["composite"] > base["composite"] + 1e-9 and r is not base]
        s.append(f"Closer than the base ({fmt(base['composite'], 3)}): {', '.join(better) or 'none'}. Further from it: {', '.join(worse) or 'none'}.")
    elif base is not None:
        s.append(f"**The base is still the best** (composite {fmt(base['composite'], 3)}); no change has improved on it yet.")
    return "\n\n".join(s)


def figures(runs, out):
    if not runs:
        return
    cmap = plt.get_cmap("tab20"); colors = {r["name"]: cmap(i % 20) for i, r in enumerate(runs)}
    # --- w* profiles
    fig, ax = plt.subplots(figsize=(6.5, 7))
    for r in runs:
        if "profile_p" in r:
            ax.plot(r["profile_wstar_tropics"], r["profile_p"], color=colors[r["name"]], lw=2.2 if r["name"] == "base" else 1.2, label=f"{r['name']} ({r['composite']:.2f})")
    r0 = runs[0]
    if "profile_waccm_p" in r0:
        ax.plot(r0["profile_waccm_wstar_tropics"], r0["profile_waccm_p"], "k--", lw=2, label="WACCM6 1996-2014")
    ax.axvline(0, color="k", lw=0.5); ax.set_yscale("log"); ax.set_ylim(200, 0.3); ax.set_xlim(-0.6, 1.6)
    ax.set_xlabel("tropical (15S-15N) w* [mm/s], annual mean of the scoring window"); ax.set_ylabel("pressure [hPa]")
    ax.set_title("Phase 15 sweep: tropical residual ascent (composite in brackets)"); ax.grid(alpha=.3); ax.legend(fontsize=7, ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(out, "sweep_wstar_profiles.png"), dpi=130); plt.close(fig)
    # --- age profiles
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for r in runs:
        if "profile_lat" not in r:
            continue
        kw = dict(color=colors[r["name"]], lw=2.2 if r["name"] == "base" else 1.2, label=r["name"])
        axes[0].plot(r["profile_lat"], r["profile_age150_55"], **kw); axes[1].plot(r["profile_lat"], r["profile_age150_12"], **kw)
        axes[2].plot(r["profile_age150_tropics"], r["profile_age_p"], **kw)
    if "profile_clams_lat" in r0:
        axes[0].plot(r0["profile_clams_lat"], r0["profile_clams_entry_55"], "k--", lw=2, label="CLaMS entry age")
        axes[1].plot(r0["profile_clams_lat"], r0["profile_clams_entry_12"], "k--", lw=2, label="CLaMS entry age")
        axes[2].plot(r0["profile_clams_entry_tropics"], r0["profile_clams_p"], "k--", lw=2, label="CLaMS entry age")
    axes[0].set_title("entry-age clock aoa150 at ~55 hPa"); axes[1].set_title("aoa150 at ~12 hPa"); axes[2].set_title("tropical (10S-10N) aoa150 profile")
    for ax in axes[:2]:
        ax.set_xlabel("latitude"); ax.set_ylabel("yr"); ax.grid(alpha=.3)
    axes[2].set_yscale("log"); axes[2].set_ylim(200, 1); axes[2].set_xlabel("yr"); axes[2].set_ylabel("hPa"); axes[2].grid(alpha=.3); axes[2].legend(fontsize=7, ncol=2)
    fig.suptitle("Phase 15 sweep: age of air (last 60 d of each run) vs CLaMS v3.1/ERA5 2005-2009 (AGE − 0.09 yr)"); fig.tight_layout()
    fig.savefig(os.path.join(out, "sweep_age_profiles.png"), dpi=130); plt.close(fig)
    # --- scores
    fig, ax = plt.subplots(figsize=(max(6, 0.8 * len(runs) + 2), 4.5))
    x = np.arange(len(runs)); wdt = 0.18
    for j, (k, lab) in enumerate((("score_age", "age vs CLaMS"), ("score_w", "w* vs WACCM6"), ("score_u", "u vs ERA5"), ("score_T", "T vs ERA5"))):
        ax.bar(x + (j - 1.5) * wdt, [r.get(k, np.nan) for r in runs], wdt, label=lab)
    ax.plot(x, [r["composite"] for r in runs], "k.-", label="composite")
    ax.set_xticks(x); ax.set_xticklabels([r["name"] for r in runs], rotation=45, ha="right"); ax.set_ylabel("normalised error (1 = acceptance edge)")
    ax.set_title("Phase 15 sweep: score parts (lower is closer)"); ax.grid(alpha=.3, axis="y"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(out, "sweep_scores.png"), dpi=130); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--scores", default=None)
    a = ap.parse_args(); scores = a.scores or os.path.join(a.out, "scores")
    runs = load(scores)
    tab, base, ref = table(runs) if runs else ("_no scored runs yet_", None, None)
    summ = summary(runs, base, ref)
    open(os.path.join(a.out, "leaderboard.md"), "w").write(f"# Phase 15 sweep leaderboard\n\n{summ}\n\n{tab}\n")
    figures(runs, a.out)
    rec = os.path.join(a.out, "output.md")
    if os.path.exists(rec):
        txt = open(rec).read(); s, e = "<!-- leaderboard:start -->", "<!-- leaderboard:end -->"
        if s in txt and e in txt:
            block = f"{s}\n{summ}\n\n{tab}\n\n![scores](sweep_scores.png)\n![w*](sweep_wstar_profiles.png)\n![age](sweep_age_profiles.png)\n{e}"
            txt = txt[:txt.index(s)] + block + txt[txt.index(e) + len(e):]
            open(rec, "w").write(txt)
    print(summ.split("\n\n")[1] if "\n\n" in summ else summ)


if __name__ == "__main__":
    main()
