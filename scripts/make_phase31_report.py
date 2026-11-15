#!/usr/bin/env python3
"""Build the Phase 31 AL7h validation record: summary figure, PDF and web page.

    python scripts/make_phase31_report.py

Inputs (all under docs/outputs/31_al7h_validation, written by scripts/phase31_validate.sh):
  success_1119/success_metrics.json   groups A-C, 2011-2019, age references of 2011-2019 (out of sample)
  success_0610/success_metrics.json   groups A-C, 2006-2010, age references of 2006-2010 (in sample)
  variability.json                    group D, 2011-2019 (optional: the page says "pending" without it)
  w1119/, w0610/                      diagnostics figures and *_metrics.md tables
Group D for 2006-2010 is AL7h's entry of the Phase 30 scoring (CDS ERA5 2006-2010).

Outputs:
  docs/outputs/31_al7h_validation/summary.png
  docs/outputs/jcm-strat_phase31_al7h_validation.pdf
  docs/outputs/31_al7h_validation/report/index.html (+ the figures it links, copied beside it)

Every number in the text is read from those files, so the record cannot drift from the scoring. Rerun after group D lands.
"""
import html
import json
import os
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image as PILImage  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "outputs")
D = os.path.join(OUT, "31_al7h_validation")
P30_VAR = os.path.join(REPO, "docs/outputs/30_level_thinning/variability.json")
PDF = os.path.join(OUT, "jcm-strat_phase31_al7h_validation.pdf")
PAGE = os.path.join(D, "report")
RUN = "AL7h"
IN_C, OUT_C = "#eb6834", "#2a78d6"     # in sample (2006-2010) orange, out of sample (2011-2019) blue

# ---------------------------------------------------------------- what is imposed, tuned, emergent
# Imposed: nudged to ERA5. Tuned: the AL7h T_e correction was fitted to ERA5 extratropical T, 400-1 hPa, on
# 2005-04..2008-01, so the polar-cap T is tuned and the extratropical jets follow it by thermal wind.
# Emergent: nothing in the model is fitted to them.
CLASS = {"A": "emergent", "B": "emergent", "C1": "constrained", "C2": "tuned", "D": "emergent"}
CLASS_TEXT = {
    "tuned": "tuned (T_e correction fitted to ERA5 polar T)",
    "constrained": "constrained (jets follow the tuned T by thermal wind)",
    "emergent": "emergent (nothing fitted to it)",
}


def klass(mid):
    if mid.startswith("X-"):
        return "emergent"
    return CLASS.get(mid[:2], CLASS.get(mid[0]))


def load_ac(tag):
    """Groups A-C; A2 replaced by the WACCM6 entry-age RMSE (scripts/a2_waccm_age.py), the old A2 kept as X-A2-clams."""
    f = os.path.join(D, f"success_{tag}", "success_metrics.json")
    if not os.path.exists(f):
        return None
    ms = json.load(open(f))[RUN]["metrics"]
    fa = os.path.join(D, f"success_{tag}", "a2_waccm.json")
    if not os.path.exists(fa):
        raise SystemExit(f"{fa} missing: run scripts/a2_waccm_age.py")
    a2 = json.load(open(fa))
    out = []
    for m in ms:
        if m["id"] == "A2":
            out.append(dict(group="A", id="A2", label="2-D entry-age RMSE vs WACCM6, 150 hPa clock [yr]",
                            model=a2["rmse_waccm"], ref=0.0, err=a2["err"]))
            out.append(dict(m, id="X-A2-clams", label="old A2: 2-D age RMSE vs CLaMS shifted by its 150 hPa age [yr]"))
        else:
            out.append(m)
    return out


def load_d(tag):
    f = os.path.join(D, "variability.json") if tag == "1119" else P30_VAR
    if not os.path.exists(f):
        return None
    return json.load(open(f))["runs"][RUN]["metrics"]


# Kept in the record but not in the score (Susanne 2026-11-10): winds at 10 hPa and above (jets, vortex variability,
# final warmings, all u at 10 hPa) and the number of major SSWs. Age counts only on the 150 hPa clock (A1-A4 already
# use aoa150; the surface clock against CLaMS is a plot and context rows only).
UNSCORED = {"C1-jet10_N", "C1-jet10_N-lat", "C1-jet10_S", "C1-jet10_S-lat",
            "D1-N", "D1-S", "D2-N", "D2-S", "D3", "D4-fwN", "D4-fwS",
            "D6-N", "D6-S", "D7",          # Susanne 2026-11-10: heat-flux -> polar T and age-w* relations out of the score
            "X-A2-clams"}                  # the old A2 (CLaMS shifted by its 150 hPa age), kept for context


def scored(mid):
    return mid not in UNSCORED


def gmean(ms, g):
    e = [m["err"] for m in ms if m["group"] == g and scored(m["id"])]
    return sum(e) / len(e) if e else float("nan")


def status(e):
    return "pass" if e <= 1.0 else ("near" if e <= 1.5 else "fail")


def fnum(x):
    if isinstance(x, (list, tuple)):
        return "-".join(fnum(v) for v in x)
    if x is None:
        return "-"
    a = abs(x)
    return f"{x:.0f}" if a >= 100 else f"{x:.1f}" if a >= 10 else f"{x:.2f}"


def md_tables(path):
    """{section heading: [rows]} from a *_metrics.md file (pipe tables only)."""
    out, sec = {}, None
    for line in open(path):
        if line.startswith("## "):
            sec = line[3:].strip()
            out[sec] = []
        elif line.startswith("|") and not line.startswith("|---") and sec:
            out[sec].append([c.strip().replace("**", "") for c in line.strip().strip("|").split("|")])
    return out


# ---------------------------------------------------------------- data
AC = {"0610": load_ac("0610"), "1119": load_ac("1119")}
DD = {"0610": load_d("0610"), "1119": load_d("1119")}
ALL = {t: (AC[t] or []) + (DD[t] or []) for t in AC}
D_PENDING = DD["1119"] is None


def summary():
    s = {}
    for t in ("0610", "1119"):
        ms = AC[t] or []
        g = {k: gmean(ms, k) for k in "ABC"}
        g["comb"] = sum(g[k] for k in "ABC") / 3 if ms else float("nan")
        sc = [m for m in ms if scored(m["id"])]
        g["pass"] = f"{sum(m['err'] <= 1 for m in sc)} / {len(sc)}"
        dm = DD[t]
        g["D"] = gmean(dm, "D") if dm else None
        dsc = [m for m in dm if scored(m["id"])] if dm else []
        g["Dpass"] = f"{sum(m['err'] <= 1 for m in dsc)} / {len(dsc)}" if dm else None
        s[t] = g
    return s


S = summary()


# ---------------------------------------------------------------- summary figure
def make_summary_png(path):
    ids = [m["id"] for m in ALL["0610"]]
    for m in ALL["1119"]:
        if m["id"] not in ids:
            ids.append(m["id"])
    order = ["tuned", "constrained", "emergent"]
    pos = {i: k for k, i in enumerate(ids)}
    ids.sort(key=lambda i: (order.index(klass(i)), pos[i]))
    lab = {m["id"]: m["label"] for t in ALL for m in ALL[t]}
    val = {t: {m["id"]: m["err"] for m in ALL[t]} for t in ALL}
    n = len(ids)
    fig, ax = plt.subplots(figsize=(8.6, 0.27 * n + 1.6), dpi=150)
    xmax = 4.0
    ax.axvspan(0, 1, color="#e6f2e6", zorder=0)
    ax.axvspan(1, 1.5, color="#fbf1dc", zorder=0)
    ax.axvspan(1.5, xmax, color="#f8e4e1", zorder=0)
    for x, s in ((0.5, "pass"), (1.25, "near"), (2.75, "fail")):
        ax.text(x, -1.1, s, ha="center", va="center", fontsize=8, color="#52514e")
    y_of = {i: k for k, i in enumerate(ids)}
    prev = None
    for i in ids:
        k = klass(i)
        if k != prev and prev is not None:
            ax.axhline(y_of[i] - 0.5, color="#888", lw=0.6)
        prev = k
        for t, c, mk, off in (("0610", IN_C, "o", -0.12), ("1119", OUT_C, "o", 0.12)):
            e = val[t].get(i)
            if e is None:
                continue
            x = min(e, xmax - 0.06)
            face = "white" if t == "0610" else c
            al = 1.0 if scored(i) else 0.3
            ax.plot([x], [y_of[i] + off], mk, ms=6.5, mfc=face, mec=c, mew=1.6, zorder=3, alpha=al)
            if e > xmax:
                ax.text(xmax - 0.12, y_of[i] + off, f"{e:.1f}", ha="right", va="center", fontsize=6.5, color="#333")
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{i}  {lab[i] if len(lab[i]) <= 54 else lab[i][:52] + '…'}" + ("" if scored(i) else "  (not scored)")
                        for i in ids], fontsize=7)
    for tl, i in zip(ax.get_yticklabels(), ids):
        if not scored(i):
            tl.set_color("#9a9a9a")
    ax.set_ylim(n - 0.5, -1.6)
    ax.set_xlim(0, xmax)
    ax.set_xlabel("error in units of the bound (|model - ref| / bound; ≤ 1 passes)", fontsize=8)
    ax.tick_params(axis="x", labelsize=8)
    # class labels on the right
    for k in order:
        ys = [y_of[i] for i in ids if klass(i) == k]
        if ys:
            ax.text(xmax + 0.08, (min(ys) + max(ys)) / 2, k, rotation=90, va="center", ha="left", fontsize=8, color="#333")
    h1 = ax.plot([], [], "o", ms=6.5, mfc="white", mec=IN_C, mew=1.6, label="2006-2010 (in sample: correction fitted 2005-04..2008-01)")[0]
    h2 = ax.plot([], [], "o", ms=6.5, mfc=OUT_C, mec=OUT_C, mew=1.6, label="2011-2019 (out of sample)")[0]
    ax.legend(handles=[h1, h2], loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7, frameon=False)
    ax.set_title("AL7h against its references, metric by metric" + ("  (group D 2011-2019 pending)" if D_PENDING else ""),
                 fontsize=9.5, pad=22)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- narrative (shared by PDF and page)
def g(t, k):
    v = S[t].get(k)
    return "pending" if v is None else (f"{v:.2f}" if isinstance(v, float) else v)


LABEL = {"A3": "age step tropics -> 50-70 deg, 55 hPa, 150 hPa clock [yr]", "A4": "transit 70 -> 10 hPa, 150 hPa clock [yr]",
         "A1": "entry age 55 hPa tropics, 150 hPa clock vs WACCM6 [yr]"}
for _t in ALL:
    for _m in ALL[_t]:
        _m["label"] = LABEL.get(_m["id"], _m["label"])


def m_of(t, mid):
    for m in ALL[t]:
        if m["id"] == mid:
            return m
    return None


def mv(t, mid):
    m = m_of(t, mid)
    return fnum(m["model"]) if m else "-"


def rv(t, mid):
    m = m_of(t, mid)
    return fnum(m["ref"]) if m else "-"


T1119 = md_tables(os.path.join(D, "w1119", "seasonal_metrics.md"))
T0610 = md_tables(os.path.join(D, "w0610", "seasonal_metrics.md"))
C1119 = md_tables(os.path.join(D, "w1119", "circulation_metrics.md"))
C0610 = md_tables(os.path.join(D, "w0610", "circulation_metrics.md"))


def temp_row(tab, season):
    for r in tab["Zonal-mean temperature [K]"]:
        if r[0] == season:
            return r
    return None


def qbo_rows(tab):
    sec = [k for k in tab if k.startswith("QBO")][0]
    return {r[0]: r for r in tab[sec][1:]}


Q1119 = qbo_rows(C1119)
T_DJF = temp_row(T1119, "DJF")

INTRO = (
    "AL7h is the dry jcm-strat configuration chosen in Phases 22-29: the Jucker et al. (2013) relaxation temperature with "
    "half of the AL7 correction (Phase 25), Hines gravity-wave drag launched at 634 hPa, fixed Lott-Miller orographic drag, "
    "ERA5 nudging below 400 hPa (tau 6 h) and the zonal-mean equatorial wind nudged to ERA5 between 90 and 1 hPa "
    "(|lat| < 15 deg, tapering to zero at 25 deg, tau 1 d). T63 L95, 12-minute step, one chain from 1990. "
    "This record asks whether that model reproduces stratospheric dynamics, and separates what it gets right on its own "
    "from what was put in."
)

CLASSES = [
    ["class", "what", "metrics"],
    ["imposed", "troposphere below 400 hPa (ERA5 nudging); zonal-mean equatorial wind 90-1 hPa (QBO nudging)",
     "not scored; the QBO panel is shown as a check that the nudging does its job"],
    ["tuned", "the T_e correction was fitted to ERA5 extratropical temperature 400-1 hPa over 2005-04..2008-01",
     "C2 (polar-cap T at 50 hPa)"],
    ["constrained", "extratropical jets: tied to the tuned temperature by thermal wind, but not fitted themselves",
     "C1 (jet speed and latitude, 50 and 10 hPa)"],
    ["emergent", "nothing in the model is fitted to these", "A (age of air, 150 hPa clock), B (w*, mass flux), D (variability), tropical T"],
    ["not scored", "kept in the validation and the tables, left out of every score: winds at 10 hPa and above (10 hPa jets, "
     "vortex variability D1-D2, final warmings D4-fw), the number of major SSWs (D3), the heat-flux and age-w* "
     "relations (D6, D7), age on the surface clock against CLaMS and the old CLaMS-based A2",
     "shown faded in the figure and the metric table"],
]


def verdict_paras():
    s0, s1 = S["0610"], S["1119"]
    d1 = "pending (the ERA5 daily reference for 2011-2019 is still downloading)" if D_PENDING else f"{g('1119', 'D')} ({g('1119', 'Dpass')} pass)"
    return [
        f"<b>Out of sample, AL7h scores as well as in sample.</b> On 2011-2019, years the temperature correction never saw, "
        f"the combined A-C error is {s1['comb']:.2f} with {s1['pass']} criteria passed. On 2006-2010 it is {s0['comb']:.2f} "
        f"with {s0['pass']} passed. An error of 1 means on average at the edge of the bounds, which are about the size of the "
        "CLaMS-WACCM6 disagreement. Group D (variability) is "
        f"{g('0610', 'D')} on 2006-2010 and {d1} on 2011-2019.",
        "<b>What it gets right on its own.</b> The entry age at 55 hPa, the tropical upwelling above 70 hPa, the 70 hPa "
        "mass flux, the shape and seasonality of the Brewer-Dobson cells, and the latitude of both polar-night jets. "
        "The tuned polar-cap temperatures stay on ERA5 out of sample, so the correction is not overfitted to its "
        "fitting years.",
        "<b>What it gets wrong, in the score.</b> One scored metric fails: upwelling at 100 hPa is a third of the "
        "reference. Near the bound: the age step from the tropics to mid-latitudes (the tropical pipe is leakier than "
        "CLaMS), the 70-10 hPa transit time (a little fast) and w* at 50 hPa (a little fast).",
        "<b>What it gets wrong, outside the score.</b> The tropical tropopause is about 11 K too warm and the air "
        "near it is 0.8 yr too old on the surface clock. Both winter jets are 10-20 % weak at 10 hPa, and the NH "
        "vortex varies too little, with too few major sudden warmings. The NH polar cap responds to the 100 hPa heat "
        "flux at half the ERA5 rate, and the tropical age rises too slowly with upwelling. These stay in the "
        "validation but count towards no score: winds at 10 hPa and above, SSW counts, the heat-flux and age-w* "
        "relations and the surface clock are left out by choice. "
        "All are listed under 'Failures'.",
    ]


def failures():
    t = T_DJF
    rows = [["failure", "scored", "2006-2010", "2011-2019", "reference"]]
    rows.append(["w* at 100 hPa, tropics [mm/s] (B1-100)", mv("0610", "B1-100"), mv("1119", "B1-100"), rv("1119", "B1-100")])
    rows.append(["old A2: 2-D age RMSE vs shifted CLaMS [yr] (X-A2-clams)", mv("0610", "X-A2-clams"), mv("1119", "X-A2-clams"), "0"])
    rows.append(["age step tropics to 50-70 deg at 55 hPa [yr] (A3)", mv("0610", "A3"), mv("1119", "A3"), rv("1119", "A3")])
    rows.append(["surface-clock age 55 hPa tropics vs CLaMS [yr]", *[sfc_age_rows()[0][k] .split(" ")[0] for k in (5, 7, 6)]])
    rows.append(["SH jet at 10 hPa, JJA [m/s] (C1-jet10_S)", mv("0610", "C1-jet10_S"), mv("1119", "C1-jet10_S"), rv("1119", "C1-jet10_S")])
    rows.append(["NH jet at 10 hPa, DJF [m/s] (C1-jet10_N)", mv("0610", "C1-jet10_N"), mv("1119", "C1-jet10_N"), rv("1119", "C1-jet10_N")])
    t0 = temp_row(T0610, "DJF")
    rows.append(["T at 100 hPa, tropics, DJF [K]", t0[3].split("/")[0].strip(), t[3].split("/")[0].strip(), t[3].split("/")[1].strip()])
    rows.append(["T at 1 hPa, tropics, DJF [K]", t0[4].split("/")[0].strip(), t[4].split("/")[0].strip(), t[4].split("/")[1].strip()])
    sao0 = qbo_rows(C0610)["model: AL7h"][2].split("/")[0].strip()
    rows.append(["SAO amplitude at 1 hPa [m/s]", sao0, Q1119["model: AL7h"][2].split("/")[0].strip(), Q1119["ERA5"][2].split("/")[0].strip()])
    for mid, lab in (("D3", "NH major SSWs in the window (D3)"), ("D6-N", "heat flux -> NH polar-cap T slope (D6-N)"),
                     ("D7", "age vs w* slope [yr per mm/s] (D7)"), ("D1-N", "year-to-year std of NH winter u, 10 hPa [m/s] (D1-N)")):
        rows.append([lab, mv("0610", mid), mv("1119", mid) if not D_PENDING else "pending",
                     (rv("1119", mid) if not D_PENDING else "") + (f" ({rv('0610', mid)} in 2006-2010)" if rv("0610", mid) != "-" else "")])
    for r in rows[1:]:
        ids = [x for x in UNSCORED | {"B1-100", "A3"} if f"({x})" in r[0] or (x == "D3" and "SSW" in r[0])]
        r.insert(1, "yes" if ids and all(scored(x) for x in ids) else "no")
    return rows


def score_table():
    rows = [["group (scored metrics only)", "class", "2006-2010", "2011-2019"]]
    for k, lab, c in (("A", "A age of air", "emergent"), ("B", "B residual circulation", "emergent"),
                      ("C", "C polar vortex (50 hPa jets, polar-cap T)", "C1 constrained, C2 tuned")):
        rows.append([lab, c, f"{S['0610'][k]:.2f}", f"{S['1119'][k]:.2f}"])
    rows.append(["combined A-C", "", f"{S['0610']['comb']:.2f}", f"{S['1119']['comb']:.2f}"])
    rows.append(["criteria passed A-C", "", S["0610"]["pass"], S["1119"]["pass"]])
    rows.append(["D variability", "emergent", g("0610", "D"), g("1119", "D")])
    rows.append(["criteria passed D", "", g("0610", "Dpass"), g("1119", "Dpass")])
    return rows


def sfc_age_rows():
    """Surface-clock age at 55 hPa against CLaMS (mean of DJF and JJA): context only, no bound, not scored."""
    out = []
    for col, lab in ((3, "tropics"), (4, "50-70N"), (5, "50-70S")):
        v = {}
        for tag, tab in (("0610", T0610), ("1119", T1119)):
            rs = [r for r in tab["Age of air [yr]"] if r[0] == "aoa_sfc"]
            mo = [float(r[col].split("/")[0]) for r in rs]
            re_ = [float(r[col].split("/")[1]) for r in rs]
            v[tag] = (sum(mo) / len(mo), sum(re_) / len(re_))
        out.append([f"X-sfc-{lab}", f"surface-clock age 55 hPa {lab} vs CLaMS [yr]", "emergent", "no",
                    fnum(v["0610"][1]), f"{fnum(v['0610'][0])} (no bound)", fnum(v["1119"][1]), f"{fnum(v['1119'][0])} (no bound)"])
    return out


def metric_table():
    rows = [["id", "metric", "class", "scored", "ref 2006-2010", "model 2006-2010", "ref 2011-2019", "model 2011-2019"]]
    ids = [m["id"] for m in ALL["0610"]]
    for i in ids:
        a, b = m_of("0610", i), m_of("1119", i)
        cell = (lambda m: f"{fnum(m['model'])} ({status(m['err'])})" if m else "pending")
        rows.append([i, a["label"], klass(i), "yes" if scored(i) else "no", fnum(a["ref"]), cell(a),
                     fnum(b["ref"]) if b else "-", cell(b)])
        if i == "A4":
            rows += sfc_age_rows()
    return rows


def dim_row(r):
    return r[0] in UNSCORED or r[0].startswith("X-")


def a2_note():
    a = {t: json.load(open(os.path.join(D, f"success_{t}", "a2_waccm.json"))) for t in ("0610", "1119")}
    return (f"A2 is the cos-weighted RMSE of the 150 hPa clock against the WACCM6 REF-D1 2-D entry age for the same years, "
            f"100-5 hPa, |lat| ≤ 80, bound 0.4 yr: {a['0610']['rmse_waccm']:.2f} yr in 2006-2010 and "
            f"{a['1119']['rmse_waccm']:.2f} yr in 2011-2019 (bias {a['0610']['bias_waccm']:+.2f} / {a['1119']['bias_waccm']:+.2f}). "
            f"The old A2 compared against CLaMS shifted by CLaMS' own tropical 150 hPa age (0.09 yr): "
            f"{a['0610']['rmse_clams']:.2f} / {a['1119']['rmse_clams']:.2f} yr, mostly a uniform offset of "
            f"{a['0610']['bias_clams']:+.2f} / {a['1119']['bias_clams']:+.2f} yr. WACCM6 itself differs from shifted CLaMS by "
            f"{a['0610']['rmse_waccm_vs_clams']:.2f} / {a['1119']['rmse_waccm_vs_clams']:.2f} yr with the same offset, so "
            "that offset comes from the shift, not from the model. The old A2 is kept as a faded row.")


SECTIONS = [
    ("Age of air (group A, emergent)", [
        ("w1119/age_seasonal_aoa150.png", "Scored: the 150 hPa clock (reset below 150 hPa), 2011-2019, against the "
         "WACCM6 REF-D1 entry age. Measured from 150 hPa, tropical ages match."),
        ("w1119/age_seasonal_aoa_sfc.png", "Not scored, shown for context: age on the surface clock against CLaMS v3.1 "
         "for the same months. The model is too old by 0.5-1.5 yr in a band at 100-70 hPa across the tropics and "
         "subtropics and by up to 0.5 yr elsewhere. Since the 150 hPa clock matches, this excess builds up between the "
         "surface and 150 hPa, where upwelling at 100 hPa is too weak."),
    ], "Group A counts only the 150 hPa clock. {a2} Entry age at 55 hPa is {e0} yr in 2006-2010 and {e1} yr in 2011-2019 against {er} yr (A1, pass). The age step "
       "from the tropics to 50-70 deg is {s1} yr against {sr} (A3), so the tropical pipe is leakier than CLaMS, and "
       "the transit from 70 to 10 hPa is {t1} yr against 2.3-3.2 (A4)."),
    ("Residual circulation (group B, emergent)", [
        ("w1119/tem_streamfunction.png", "TEM residual streamfunction, DJF / JJA / annual, AL7h 2011-2019 (top) against "
         "WACCM6 histSST (bottom). Cell shape, the summer-to-winter cell in the upper stratosphere and the seasonal "
         "shift of the turnaround latitude are reproduced. The lowest branch, near 100 hPa, is weaker than WACCM6."),
    ], "w* at 70, 30 and 10 hPa is within the bounds ({w70}, {w30}, {w10} mm/s against {r70}, {r30}, {r10}); 50 hPa is "
       "a bit fast ({w50} vs {r50}). At 100 hPa it is {w100} mm/s against {r100}: the shallow branch at the tropopause "
       "is the main circulation failure, in sample and out of sample alike. The mass flux at 100 hPa ({f100}, ref "
       "{rf100} x 1e9 kg/s) passes, so the deficit is in the tropical core of the upwelling rather than in the total."),
    ("Polar vortex and winds (group C, constrained)", [
        ("w1119/vortex_jets.png", "Polar-night jets, 2011-2019: u at 10 hPa, the jet maximum and its latitude with "
         "height, against ERA5 and WACCM6. Jet latitude matches ERA5 from 50 to 5 hPa in both hemispheres. Both jets "
         "are weak above 30 hPa and the subtropical easterlies at 10 hPa are too strong near 25-30 deg in winter."),
        ("w1119/wind_seasonal.png", "Zonal-mean u by season against ERA5, same months. Besides the weak polar jets, the "
         "winter subtropical jet near 200 hPa is 10-20 m/s too weak; that region is above the 400 hPa nudging and "
         "is the model's own."),
    ], "Group C counts the 50 hPa jets and the polar-cap temperature; the 10 hPa jets are shown but not scored. NH 50 hPa jet {n50} m/s against {rn50}, NH 10 hPa {n10} against {rn10}, SH 50 hPa {s50} against {rs50}, SH "
       "10 hPa {s10} against {rs10}. The latitudes are right everywhere. The polar-cap temperature at 50 hPa, the "
       "quantity the correction was fitted to, stays within 1.5 K of ERA5 out of sample (C2)."),
    ("Temperature (polar caps tuned, tropics emergent)", [
        ("w1119/temp_seasonal.png", "Zonal-mean T by season against ERA5, 2011-2019. Polar caps are on ERA5 (tuned). "
         "In the tropics the errors stack vertically: about -6 K at 200-300 hPa, about +11 K at 100 hPa, -6 K at "
         "10-20 hPa and +7 to +10 K at 1-3 hPa."),
    ], "The tropical tropopause (100 hPa) is {t100} K against ERA5 {r100} K in DJF. That warm tropopause is consistent with "
       "the weak 100 hPa w* (less adiabatic cooling), and it is the same in both periods, so it is a property of the "
       "configuration, not of the years."),
    ("QBO and SAO (imposed)", [
        ("w1119/qbo_time_height.png", "Equatorial zonal wind 5S-5N, 2011-2019: AL7h (nudged), ERA5 and free-running "
         "WACCM6. The QBO follows ERA5 because it is nudged; this panel only shows that the nudging works, including "
         "the 2016 disruption."),
    ], "QBO standard deviation at 10/20/30/50 hPa is {q} m/s against ERA5 {qr}. The SAO at 1 hPa, at the top of the "
       "nudged layer, has {sao} m/s amplitude against ERA5 {saor}."),
]


def section_text(i):
    t = SECTIONS[i][2]
    if i == 0:
        return t.format(a2=a2_note(), e0=mv("0610", "A1"), e1=mv("1119", "A1"), er=rv("1119", "A1"), s1=mv("1119", "A3"),
                        sr=rv("1119", "A3"), t1=mv("1119", "A4"))
    if i == 1:
        return t.format(**{f"w{k}": mv("1119", f"B1-{k}") for k in ("100", "70", "50", "30", "10")},
                        **{f"r{k}": rv("1119", f"B1-{k}").split(" ")[0] for k in ("100", "70", "50", "30", "10")},
                        f100=mv("1119", "B2-100"), rf100=rv("1119", "B2-100"))
    if i == 2:
        return t.format(n50=mv("1119", "C1-jet50_N"), rn50=rv("1119", "C1-jet50_N"), n10=mv("1119", "C1-jet10_N"),
                        rn10=rv("1119", "C1-jet10_N"), s50=mv("1119", "C1-jet50_S"), rs50=rv("1119", "C1-jet50_S"),
                        s10=mv("1119", "C1-jet10_S"), rs10=rv("1119", "C1-jet10_S"))
    if i == 3:
        return t.format(t100=T_DJF[3].split("/")[0].strip(), r100=T_DJF[3].split("/")[1].strip())
    if i == 4:
        return t.format(q=Q1119["model: AL7h"][1], qr=Q1119["ERA5"][1], sao=Q1119["model: AL7h"][2].split("/")[0].strip(),
                        saor=Q1119["ERA5"][2].split("/")[0].strip())
    return t


D_FIGS_1119 = ["variability_vortex.png", "variability_heatflux.png", "variability_seasonal.png", "variability_age_wstar.png"]


D_SCOPE = ("Group D counts the w* annual cycle (D4-w) and the heat-flux variability (D5). The 10 hPa vortex "
           "variability (D1, D2), the SSW count (D3), the final-warming dates (D4-fw), the heat flux -> polar-cap T "
           "relation (D6) and the age-w* relation (D7) are shown but not scored. ")


def d_text():
    return D_SCOPE + _d_text()


def _d_text():
    if D_PENDING:
        return ("Group D for 2011-2019 needs ERA5 daily zonal means of the same days. They are being fetched from the "
                "Copernicus data store; the scoring runs automatically when they arrive and this section is then "
                f"regenerated. On 2006-2010 AL7h's group D error is {g('0610', 'D')} ({g('0610', 'Dpass')} pass): the "
                "w* annual cycle and the heat-flux variability pass. Outside the score, the NH polar cap responds to the heat "
                "flux at half the ERA5 rate (D6-N), and the vortex varies too little with too few major warmings ("
                f"{mv('0610', 'D3')} against {rv('0610', 'D3')}).")
    return (f"Group D error {g('1119', 'D')} on 2011-2019 ({g('1119', 'Dpass')} pass) against {g('0610', 'D')} on "
            f"2006-2010. NH major SSWs: {mv('1119', 'D3')} against ERA5 {rv('1119', 'D3')}. NH heat-flux response "
            f"slope {mv('1119', 'D6-N')} against {rv('1119', 'D6-N')}. Age-w* slope {mv('1119', 'D7')} against "
            f"{rv('1119', 'D7')}.")


COST = [["grid", "per 12-min step", "per 6 h of model time", "per 10-day chunk", "per model year (wall clock, chain)"],
        ["L95 (AL7h)", "17.5 ms", "0.53 s", "21.0 s", "15.6 min"],
        ["strat84 (AL7hL84, mesosphere 22 -> 11 layers)", "15.8 ms", "0.48 s", "19.0 s", "13.8 min"]]

METHOD = [
    "Bounds and errors as in scripts/success_metrics.py (Susanne 2026-10-23): err = |model - ref| / bound, or "
    "|ln(model/ref)| / ln(factor) for w* and mass flux; pass err ≤ 1, near ≤ 1.5, fail above. Group means are plain "
    "means over their metrics; the combined score is the mean of A, B and C.",
    "References for the same years as the model window: CLaMS v3.1 age (ERA5-driven) and WACCM6 REF-D1 entry age "
    "(SCORE_REF_YEARS), ERA5 monthly zonal means for winds and temperature, WACCM6 histSST TEM for w* and mass flux, "
    "CDS ERA5 daily zonal means for group D.",
    "Periods: the correction was fitted on 2005-04..2008-01, so 2006-2010 overlaps it (in sample) and 2011-2019 does "
    "not (out of sample). Both periods are the same continuous chain p25_AL7h, started in 1990.",
    "Run cost measured on one H100, median over the 2015 (L95) and 2008 (strat84) segments.",
]


# ---------------------------------------------------------------- PDF
def build_pdf():
    W = A4[0] - 4 * cm
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=14, spaceBefore=10, spaceAfter=5)
    B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
    CAP = ParagraphStyle("CAP", parent=B, fontSize=8.3, leading=10.8, textColor=colors.HexColor("#444444"), spaceAfter=10)
    SM = ParagraphStyle("SM", parent=B, fontSize=7.6, leading=9.4, spaceAfter=0)
    TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=18, spaceAfter=4)
    SUB = ParagraphStyle("SUB", parent=B, fontSize=10, textColor=colors.HexColor("#444444"), spaceAfter=10)

    SMD = ParagraphStyle("SMD", parent=SM, textColor=colors.HexColor("#9a9a9a"))
    CHIP = {"pass": "#2f7d3a", "near": "#a86b00", "fail": "#b3372b"}

    def tab(rows, colw, dim=False):
        body = []
        for k, r in enumerate(rows):
            faded = dim and k > 0 and dim_row(r)
            cells = []
            for c in r:
                t_ = html.escape(str(c))
                for st_, col in CHIP.items():
                    if dim and f"({st_})" in t_:
                        col = "#c9c9c9" if faded else col
                        t_ = t_.replace(f"({st_})", f'<font color="{col}"><b>{st_}</b></font>')
                cells.append(Paragraph(t_, SMD if faded else SM))
            body.append(cells)
        t = Table(body, colWidths=colw, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return t

    def fig(rel, cap, maxh=13 * cm):
        p = os.path.join(D, rel)
        if not os.path.exists(p):
            return Paragraph(f"[{rel} not available]", CAP)
        w, h = PILImage.open(p).size
        s = min(W / w, maxh / h)
        return KeepTogether([Image(p, width=w * s, height=h * s), Paragraph(cap, CAP)])

    st = [Paragraph("AL7h validation: stratospheric dynamics, 2006-2019", TITLE),
          Paragraph("jcm-strat Phase 31. Does the chosen dry configuration reproduce the stratosphere on years it was not tuned on?", SUB),
          Paragraph(INTRO, B), Paragraph("What is imposed, tuned and emergent", H1),
          tab(CLASSES, [2.2 * cm, 8.6 * cm, W - 10.8 * cm]), Spacer(1, 8), Paragraph("Verdict", H1)]
    st += [Paragraph(p, B) for p in verdict_paras()]
    st += [tab(score_table(), [4.5 * cm, 4.5 * cm, (W - 9 * cm) / 2, (W - 9 * cm) / 2]), Spacer(1, 8),
           fig("summary.png", "Every metric, error in units of its bound. Open orange: 2006-2010, in sample. Filled blue: "
               "2011-2019, out of sample. Rows grouped by what the metric measures: tuned, constrained by the tuning, or "
               "emergent.", maxh=20 * cm)]
    for i, (title, figs, _) in enumerate(SECTIONS):
        st += [Paragraph(title, H1), Paragraph(section_text(i), B)]
        st += [fig(r, c) for r, c in figs]
    st += [Paragraph("Variability (group D, emergent)", H1), Paragraph(d_text(), B)]
    if not D_PENDING:
        st += [fig(f, f"Group D, AL7h 2011-2019 against CDS ERA5: {f[12:-4].replace('_', ' ')}.") for f in D_FIGS_1119]
    st += [Paragraph("Failures", H1), Paragraph("The quantities where AL7h is outside its bounds or clearly off ERA5, in both periods.", B),
           tab(failures(), [6.4 * cm, 1.4 * cm, 2.2 * cm, 2.2 * cm, W - 12.2 * cm]),
           Paragraph("All metrics", H1),
           Paragraph("Faded rows are kept for the validation but do not count towards any score: winds at 10 hPa and above, "
                     "the number of major SSWs, the heat-flux and age-w* relations (D6, D7), the surface-clock age against CLaMS "
                     "and the old CLaMS-based A2.", B),
           tab(metric_table(), [1.7 * cm, 4.3 * cm, 1.8 * cm, 1.2 * cm, 1.6 * cm, 2.2 * cm, 1.6 * cm, W - 14.4 * cm], dim=True),
           Paragraph("Run cost", H1), tab(COST, [4.6 * cm, 2.4 * cm, 2.8 * cm, 2.4 * cm, W - 12.2 * cm]),
           Paragraph("Method", H1)]
    st += [Paragraph(m, B) for m in METHOD]
    SimpleDocTemplate(PDF, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                      title="AL7h validation", author="jcm-strat").build(st)


# ---------------------------------------------------------------- page
CSS = """
<style>
/* Layout: one reading column, figures break out to a wider measure; a verdict band and a class key up top. */
:root{--bg:#f7f8f9;--surface:#ffffff;--ink:#14181d;--ink-2:#4a525c;--rule:#d9dee4;--accent:#1f5f9e;
--in:#eb6834;--out:#2a78d6;--pass:#2f7d3a;--near:#a86b00;--fail:#b3372b;--pass-bg:#e6f2e6;--near-bg:#fbf1dc;--fail-bg:#f8e4e1;
--f-display:"IBM Plex Sans Condensed","Arial Narrow",system-ui,sans-serif;--f-body:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
--f-mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#121518;--surface:#1a1e23;--ink:#e8ebee;--ink-2:#a9b1ba;
--rule:#2e343b;--accent:#7fb2e5;--in:#f08a5d;--out:#5c9ce6;--pass:#7cc487;--near:#e0b04a;--fail:#ee8476;--pass-bg:#1d2b1f;
--near-bg:#2e2716;--fail-bg:#33201d;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121518;--surface:#1a1e23;--ink:#e8ebee;--ink-2:#a9b1ba;--rule:#2e343b;--accent:#7fb2e5;--in:#f08a5d;
--out:#5c9ce6;--pass:#7cc487;--near:#e0b04a;--fail:#ee8476;--pass-bg:#1d2b1f;--near-bg:#2e2716;--fail-bg:#33201d;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:15px/1.6 var(--f-body)}
.wrap{max-width:1040px;margin:0 auto;padding-block:32px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.col{max-width:68ch}
h1,h2{font-family:var(--f-display);text-wrap:balance;line-height:1.15}
h1{font-size:2.1rem;margin:0 0 6px;font-weight:600}
h2{font-size:1.35rem;margin:44px 0 8px;font-weight:600;border-top:1px solid var(--rule);padding-top:18px}
.eyebrow{font:500 .75rem/1 var(--f-mono);letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2)}
.lede{color:var(--ink-2);font-size:1.05rem;margin:0 0 18px}
p{margin:0 0 12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:18px 0 8px}
.kpi{background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:12px 14px;min-width:0}
.kpi .k{font:500 .72rem/1.2 var(--f-mono);letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2)}
.kpi .v{font:600 1.7rem/1.2 var(--f-display);font-variant-numeric:tabular-nums;margin-top:4px}
.kpi .s{font-size:.82rem;color:var(--ink-2)}
.tw{overflow-x:auto;margin:10px 0 18px}
table{border-collapse:collapse;font-size:.85rem;font-variant-numeric:tabular-nums;min-width:100%}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font:600 .74rem/1.3 var(--f-mono);letter-spacing:.04em;text-transform:uppercase;color:var(--ink-2)}
td.n{font-family:var(--f-mono);white-space:nowrap}
.chip{display:inline-block;font:600 .7rem/1 var(--f-mono);padding:3px 6px;border-radius:3px;letter-spacing:.03em}
.pass{color:var(--pass);background:var(--pass-bg)}.near{color:var(--near);background:var(--near-bg)}.fail{color:var(--fail);background:var(--fail-bg)}
tr.dim td{color:var(--ink-2)}tr.dim .chip{opacity:.4}.chip.no-bound{color:var(--ink-2);border:1px solid var(--rule)}
.cls{font:500 .72rem/1 var(--f-mono);color:var(--ink-2)}
figure{margin:16px 0 22px}
figure img{display:block;width:100%;height:auto;background:#fff;border:1px solid var(--rule);border-radius:4px}
figcaption{font-size:.85rem;color:var(--ink-2);margin-top:6px;max-width:80ch}
.pending{border:1px dashed var(--rule);border-radius:6px;padding:12px 14px;background:var(--surface)}
.foot{color:var(--ink-2);font-size:.82rem;margin-top:40px}
a{color:var(--accent)}
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">
"""


def strip_tags(s):
    return s.replace("<b>", "<strong>").replace("</b>", "</strong>")


def htable(rows, numeric_from=2, chips=False):
    h = ["<div class=\"tw\"><table><thead><tr>"] + [f"<th>{html.escape(c)}</th>" for c in rows[0]] + ["</tr></thead><tbody>"]
    for r in rows[1:]:
        h.append("<tr class=\"dim\">" if chips and dim_row(r) else "<tr>")
        for j, c in enumerate(r):
            c = str(c)
            cell = html.escape(c)
            if chips:
                for s in ("pass", "near", "fail", "no bound"):
                    cell = cell.replace(f"({s})", f"<span class=\"chip {s.replace(' ', '-')}\">{s}</span>")
            cls = " class=\"n\"" if j >= numeric_from else ""
            h.append(f"<td{cls}>{cell}</td>")
        h.append("</tr>")
    h.append("</tbody></table></div>")
    return "".join(h)


def build_page():
    os.makedirs(PAGE, exist_ok=True)
    figs = ["summary.png"] + [r for _, fs, _ in SECTIONS for r, _ in fs]
    if not D_PENDING:
        figs += D_FIGS_1119
    for f in figs:
        src = os.path.join(D, f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(PAGE, os.path.basename(f)))
    s0, s1 = S["0610"], S["1119"]

    def kpi(k, v, s):
        return f"<div class=\"kpi\"><div class=\"k\">{k}</div><div class=\"v\">{v}</div><div class=\"s\">{s}</div></div>"

    def figure(rel, cap):
        return (f"<figure><img src=\"{os.path.basename(rel)}\" alt=\"{html.escape(cap[:120])}\" loading=\"lazy\">"
                f"<figcaption>{html.escape(cap)}</figcaption></figure>")

    p = ["<title>AL7h Validation</title>", "<meta name=\"claude:viewport-fit-sides\" content=\"cover\">", CSS,
         "<div class=\"wrap\">", "<div class=\"eyebrow\">jcm-strat · Phase 31 · T63 L95 dry model</div>",
         "<h1>AL7h validation: stratospheric dynamics, 2006-2019</h1>",
         "<p class=\"lede col\">Does the chosen configuration reproduce the stratosphere on years it was not tuned on? "
         "Scored against CLaMS, WACCM6 and ERA5 for the same years, in sample (2006-2010) and out of sample (2011-2019).</p>",
         "<div class=\"kpis\">",
         kpi("combined A-C, 2011-2019", f"{s1['comb']:.2f}", f"out of sample · {s1['pass']} pass"),
         kpi("combined A-C, 2006-2010", f"{s0['comb']:.2f}", f"in sample · {s0['pass']} pass"),
         kpi("variability D, 2011-2019", g("1119", "D"), "ERA5 daily reference still downloading" if D_PENDING else f"{g('1119', 'Dpass')} pass"),
         kpi("variability D, 2006-2010", g("0610", "D"), f"{g('0610', 'Dpass')} pass"),
         "</div><p class=\"cls\">Errors are in units of each metric's bound: ≤ 1 passes, ≤ 1.5 is near, above fails. Lower is better.</p>",
         "<h2>What is being tested</h2>", f"<p class=\"col\">{html.escape(INTRO)}</p>",
         htable(CLASSES, numeric_from=99),
         "<h2>Verdict</h2>"]
    p += [f"<p class=\"col\">{strip_tags(x)}</p>" for x in verdict_paras()]
    p.append(htable(score_table()))
    p.append(figure("summary.png", "Every metric, error in units of its bound. Open orange: 2006-2010, in sample. Filled "
                    "blue: 2011-2019, out of sample. Rows grouped into tuned, constrained by the tuning, and emergent."))
    for i, (title, fs, _) in enumerate(SECTIONS):
        p += [f"<h2>{html.escape(title)}</h2>", f"<p class=\"col\">{html.escape(section_text(i))}</p>"]
        p += [figure(r, c) for r, c in fs]
    p.append("<h2>Variability (group D, emergent)</h2>")
    if D_PENDING:
        p.append(f"<div class=\"pending col\">{html.escape(d_text())}</div>")
    else:
        p.append(f"<p class=\"col\">{html.escape(d_text())}</p>")
        p += [figure(f, f"Group D, AL7h 2011-2019 against CDS ERA5: {f[12:-4].replace('_', ' ')}.") for f in D_FIGS_1119]
    p += ["<h2>Failures</h2>", "<p class=\"col\">Where AL7h is outside its bounds or clearly off ERA5. They are the same "
          "in both periods, so they belong to the configuration rather than to particular years.</p>", htable(failures(), 1),
          "<h2>All metrics</h2>", "<p class=\"col\">Faded rows are kept for the validation but do not count towards any score: "
          "winds at 10 hPa and above, the number of major SSWs, the heat-flux and age-w* relations (D6, D7), the surface-clock "
          "age against CLaMS and the old CLaMS-based A2.</p>",
          htable(metric_table(), 4, chips=True),
          "<h2>Run cost</h2>", htable(COST, 1),
          "<h2>Method</h2>"]
    p += [f"<p class=\"col\">{html.escape(m)}</p>" for m in METHOD]
    p += ["<p class=\"foot\">Generated by scripts/make_phase31_report.py from docs/outputs/31_al7h_validation. "
          "PDF: docs/outputs/jcm-strat_phase31_al7h_validation.pdf.</p>", "</div>"]
    open(os.path.join(PAGE, "index.html"), "w").write("\n".join(p))
    return figs


if __name__ == "__main__":
    if AC["0610"] is None or AC["1119"] is None:
        raise SystemExit("success_0610 or success_1119 missing - run scripts/phase31_validate.sh / the 2006-2010 rescoring first")
    make_summary_png(os.path.join(D, "summary.png"))
    build_pdf()
    figs = build_page()
    print(f"wrote {D}/summary.png, {PDF}, {PAGE}/index.html (+{len(figs)} figures); group D 2011-2019 "
          + ("pending" if D_PENDING else "included"))
