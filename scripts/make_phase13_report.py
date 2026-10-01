#!/usr/bin/env python3
"""Build the Phase 13 PDF (gravity-wave drag and the radiative relaxation for the dry model: steps 13, 13b, 13c, 13d).

    python scripts/make_phase13_report.py [docs/outputs/jcm-strat_phase13_drag_relaxation.pdf]

The narrative lives here, plain language first; the figures are the tracked PNGs under docs/outputs/13*_*/. The Phase 13d
tables are read from docs/outputs/13d_jucker_hines/{hines,lm_off,jh_vs_echam}_metrics.md and p13d_mesosphere.md, so they cannot
drift from the record; the earlier steps' acceptance numbers are the ones their output.md records state. Regenerate the PDF
whenever a record changes.
"""
import datetime as dt
import os
import sys

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "outputs")
D13, D13B, D13C, D13D = (os.path.join(OUT, d) for d in ("13_gwd", "13b_jucker", "13c_jucker_n400", "13d_jucker_hines"))
W = A4[0] - 4 * cm
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=8, spaceAfter=5)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
BL = ParagraphStyle("BL", parent=B, leftIndent=12, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=10)
SM = ParagraphStyle("SM", parent=B, fontSize=7.8, leading=9.8)
XS = ParagraphStyle("XS", parent=B, fontSize=7.0, leading=8.6)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=19, spaceAfter=4)
SUB = ParagraphStyle("SUB", parent=B, fontSize=10.5, textColor=colors.HexColor("#444444"), spaceAfter=12)


def P(t, s=B):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(f"• {t}", BL) for t in items]


def fig(d, rel, caption, width=W, maxh=14.5 * cm):
    path = os.path.join(d, rel)
    if not os.path.exists(path):
        return P(f"[figure {rel} not available]", CAP)
    w, h = PILImage.open(path).size
    scale = min(width / w, maxh / h)
    return KeepTogether([Image(path, width=w * scale, height=h * scale), Paragraph(caption, CAP)])


def table(rows, colw, hl=None, style=SM, bold_col=None):
    cells = [[Paragraph(str(c), style) for c in r] for r in rows]
    t = Table(cells, colWidths=colw, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    for r in (hl or []):
        st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3ecdc")))
    if bold_col is not None:
        st.append(("BACKGROUND", (bold_col, 1), (bold_col, -1), colors.HexColor("#eef5e8")))
    t.setStyle(TableStyle(st))
    return t


def metrics(d, tag):
    """{(quantity, season): (before, after, diff, ref)} and {(clock, level, region): (before, after, diff, clams)}."""
    circ, age = {}, {}
    section = None
    for line in open(os.path.join(d, f"{tag}_metrics.md")):
        if line.startswith("## "):
            section = "circ" if "circulation" in line else "age"
            continue
        if not line.startswith("| ") or line.startswith("|---") or "before" in line:
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if section == "circ":
            circ[(c[0], c[1])] = c[2:]
        elif section == "age":
            age[(c[0], c[1], c[2])] = c[3:]
    return circ, age


def mesosphere(d, name):
    """{run label: [10, 5, 2, 1, 0.5, 0.3 hPa cells 'trop / NH / SH', lat std]} of <name>."""
    rows = {}
    for line in open(os.path.join(d, name)):
        if not line.startswith("| ") or line.startswith("|---") or line.startswith("| run"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows[c[0].split(" (")[0].strip("*")] = c[1:]
    return rows


def build(out_pdf):
    today = dt.date.today().strftime("%-d %B %Y")
    hines = metrics(D13D, "hines")          # before = p13jucker_5yr, after = p13jh_5yr
    lm = metrics(D13D, "lm_off")            # before = p13juckergwd_5yr
    ech = metrics(D13D, "jh_vs_echam")      # before = p12echam_5yr
    meso = mesosphere(D13D, "p13d_mesosphere.md")
    D10 = os.path.join(D13D, "10yr")
    s1 = metrics(D10, "hines_s1")           # the 5-yr Hines pair at stride 1
    t10 = metrics(D10, "jh10_vs_5")         # before = 5 yr, after = 10 yr (stride 1)
    meso10 = mesosphere(D10, "p13d10_mesosphere.md")

    def w(m, ph, seas="annual", col=1):
        return m[0][(f"tropical w* 15S-15N {ph} hPa [mm/s]", seas)][col]

    def mf(m, ph, seas="annual", col=1):
        return m[0][(f"upward mass flux {ph} hPa [1e9 kg/s]", seas)][col]

    def age(m, clock, lev, reg, col=1):
        return m[1][(clock, lev, reg)][col]

    # ---- the cross-phase acceptance table: 13d read from its files, the rest as their records state
    jh_meso = meso["Jucker + Hines"]
    r2 = lambda x: f"{float(x):.2f}"
    jh = {"w100": r2(w(hines, 100)), "w30": r2(w(hines, 30)), "w10": r2(w(hines, 10)),
          "a12": age(hines, "aoa150", "12 hPa", "tropics 10S-10N"), "a55": age(hines, "aoa150", "55 hPa", "tropics 10S-10N"),
          "a55x": age(hines, "aoa150", "55 hPa", "50-70 deg"),
          "meso": " / ".join(x.split(" / ")[0] for x in jh_meso[3:6]), "polar": " / ".join(jh_meso[4].split(" / ")[1:]), "cost": "30–32"}
    acc = [["quantity", "target", "strat81 control (PK, Phase 12)", "13: PK + Hines + LM (strat63)", "13b: Jucker", "13b: Jucker + Hines + LM",
            "13c: Jucker + Hines + LM, nudged &lt; 400 hPa (10 yr)", "13c: Jucker + Hines, nudged &lt; 400 hPa (10 yr)", "13d: Jucker + Hines",
            "full ECHAM (Phase 12)"],
           ["tropical w* 100 hPa [mm/s]", "0.40", "0.35", "1.05", "0.29", "0.99", "0.06", "0.10", jh["w100"], "1.46"],
           ["tropical w* 30 hPa [mm/s] (stride-4 sampled)", "0.26", "0.02", "0.19", "0.03", "0.06", "−0.07", "0.01", jh["w30"], "0.28"],
           ["tropical w* 10 hPa [mm/s]", "0.47", "0.31", "0.02", "0.41", "0.25", "0.36", "0.58", jh["w10"], "0.87"],
           ["tropical entry age 12 hPa [yr]", "2.90 ± 0.4", "3.80", "3.55", "3.67", "3.65", "5.02", "4.21", jh["a12"], "3.33"],
           ["tropical entry age 55 hPa [yr]", "1.19", "1.31", "1.10", "1.56", "1.12", "2.91", "2.26", jh["a55"], "0.96"],
           ["50–70° entry age 55 hPa [yr]", "≥ 3.6", "3.64", "2.47", "3.62", "2.06", "3.65", "3.96", jh["a55x"], "2.41"],
           ["tropical w* 1 / 0.5 / 0.3 hPa, 1994 [mm/s]", "upward", "−0.75 / −0.98 / −0.12", "−0.39 / −0.73 / −0.64", "+0.32 / +0.08 / +0.23",
            "+0.15 / +0.31 / +0.90", "+0.05 / +0.44 / +1.63", "+0.26 / +0.78 / +1.89", jh["meso"], "+0.96 / +1.31 / +1.92"],
           ["polar descent 0.5 hPa NH / SH, 1994 [mm/s]", "≈ ECHAM", "−0.07 / −0.51", "−0.42 / −0.66", "−1.76 / −2.92", "−2.97 / −4.60",
            "−2.61 / −3.71", "−2.99 / −4.86", jh["polar"], "−2.82 / −5.27"],
           ["cost [min per simulated year]", "≤ 35", "26–27", "31–33", "26–28", "41", "41", "36", jh["cost"], "181–206"]]
    acc_w = [c * (W / 100) for c in (19, 7, 9.5, 9.5, 8, 9.5, 9.5, 9.5, 9, 9)]

    # ---- Phase 13d tables from the metrics files
    hdr = ["quantity (annual mean, 1990–1994)", "Jucker, no drag", "Jucker + Hines + LM", "<b>Jucker + Hines</b>", "full ECHAM", "WACCM6"]
    circ_rows = [hdr]
    for ph in (100, 70, 30, 10):
        q = f"upward mass flux {ph} hPa [1e9 kg/s]"
        circ_rows.append([f"tropical upward mass flux {ph} hPa [10^9 kg/s]", mf(hines, ph, col=0), mf(lm, ph, col=0), mf(hines, ph), mf(ech, ph, col=0),
                          hines[0][(q, "annual")][3]])
    for ph in (100, 70, 50, 30, 10):
        q = f"tropical w* 15S-15N {ph} hPa [mm/s]"
        circ_rows.append([f"tropical w* {ph} hPa [mm/s]", w(hines, ph, col=0), w(lm, ph, col=0), w(hines, ph), w(ech, ph, col=0), hines[0][(q, "annual")][3]])
    for seas in ("DJF", "JJA"):
        q = "tropical w* 15S-15N 10 hPa [mm/s]"
        circ_rows.append([f"tropical w* 10 hPa, {seas} [mm/s]", w(hines, 10, seas, 0), w(lm, 10, seas, 0), w(hines, 10, seas), w(ech, 10, seas, 0),
                          hines[0][(q, seas)][3]])
    age_rows = [["age after 5 years [yr]", "Jucker, no drag", "Jucker + Hines + LM", "<b>Jucker + Hines</b>", "full ECHAM", "CLaMS (surface clock)"]]
    for clock, lab in (("aoa150", "entry-age clock (zero below 150 hPa)"), ("aoa_sfc", "surface clock")):
        for lev in ("55 hPa", "12 hPa"):
            for reg, rl in (("tropics 10S-10N", "tropics"), ("50-70 deg", "50–70°")):
                age_rows.append([f"{lab}, {lev}, {rl}", age(hines, clock, lev, reg, 0), age(lm, clock, lev, reg, 0), age(hines, clock, lev, reg),
                                 age(ech, clock, lev, reg, 0), hines[1][(clock, lev, reg)][3]])
    cw = [c * (W / 100) for c in (34, 13, 14, 13, 13, 13)]
    meso_rows = [["run (1994 segment, annual mean; tropics / NH cap / SH cap, mm/s)", "10 hPa", "5 hPa", "2 hPa", "1 hPa", "0.5 hPa", "0.3 hPa",
                  "entry-age latitude std 3 / 1.5 hPa [yr]"]]
    for k in ("strat81 PK", "Jucker", "Jucker + Hines + LM", "Jucker + Hines", "full ECHAM"):
        meso_rows.append([k] + meso[k])
    for k, lab in (("Jucker + Hines 1994", "Jucker + Hines 1994, stride 1"), ("Jucker + Hines 1999", "Jucker + Hines 1999, stride 1"),
                   ("full ECHAM 1994", "full ECHAM 1994, stride 1")):
        meso_rows.append([lab] + meso10[k])
    meso_w = [c * (W / 100) for c in (22, 11, 11, 11, 11, 11, 11, 12)]

    s = [P("jcm-strat Phase 13: wave drag and the radiative relaxation for the dry stratosphere", TITLE),
         P("Eight chained runs in four steps, 23–25 September 2026, on the Phase 12 transport model (T63, dry column physics, ERA5-nudged "
           "troposphere, QBO nudging, four age clocks): gravity-wave drag added to the Polvani–Kushner model (13), the Jucker et al. (2013) "
           "radiative relaxation in place of Polvani–Kushner without and with drag (13b), the same with the nudging cut off at 400 hPa and "
           "Lott–Miller on/off over ten years (13c), and Jucker + Hines only under the 150 hPa nudging (13d). Measured by the TEM residual "
           f"vertical velocity w*, the age of air and the mesospheric circulation against WACCM6, CLaMS and JCM's full physics. Record as of {today}, "
           "branch phase13-gwd.", SUB)]

    s += [P("1. The question", H1),
          P("Phase 12 ended with two findings. The old stratospheric age of air of Phases 4–11 belongs to the dry Polvani–Kushner configuration: "
            "under the same nudging JCM's full ECHAM physics puts the tropical age on CLaMS. And the dry model's mesosphere does not circulate: "
            "above ~1.5 hPa the tropical residual motion is downward, there is no polar descent, and the age between 20 and 1 hPa is flat in "
            "latitude because lid-valued air is pushed down. Two ingredients of the full physics were the suspects: the gravity-wave drag, which "
            "ventilates the mesosphere in the atmosphere and in the full-physics run and by downward control sets the deep branch; and the "
            "radiative heating, which the dry model replaces by a relaxation toward an equilibrium temperature that is flat above 3 hPa with a "
            "single 15-day timescale. Phase 13 tests both, one change at a time, on 5-year chains 1990–1994 (13c: 10 years)."),
          P("2. The eight runs", H1),
          P("Common to all: T63, 12-minute step, Gregorian calendar, one calendar year per chained segment, ERA5 nudging of u, v and T with a "
            "6-hour timescale below the stated cutoff, QBO nudging of the tropical zonal-mean wind to ERA5 monthly means (90–1 hPa, tau 1 d), "
            "Held–Suarez troposphere, upper sponge, the four clocks with the 1 hPa tracer lid, 6-hourly output, same ERA5 initial state."),
          table([["step", "experiment", "vertical grid", "stratospheric relaxation", "gravity-wave drag", "nudging cutoff", "years", "cost [min/yr]"],
                 ["13", "p13_gwd", "strat63", "Polvani–Kushner", "Hines (launch 634 hPa) + Lott–Miller, JCM defaults", "150 hPa", "1990–94", "31–33"],
                 ["13", "p13_gwd_l95", "native L95", "Polvani–Kushner", "Hines + Lott–Miller", "150 hPa", "1990–94", "51–54"],
                 ["13", "p13_l81_n400", "strat81", "Polvani–Kushner", "none", "400 hPa", "1990–94", "26–27"],
                 ["13b", "p13_jucker", "strat81", "Jucker et al. 2013 above 100 hPa", "none", "150 hPa", "1990–94", "26–28"],
                 ["13b", "p13_jucker_gwd", "strat81", "Jucker 2013", "Hines + Lott–Miller", "150 hPa", "1990–94", "41"],
                 ["13c", "p13_jucker_gwd_n400", "strat81", "Jucker 2013", "Hines + Lott–Miller", "400 hPa", "1990–99", "41"],
                 ["13c", "p13_jucker_hines_n400", "strat81", "Jucker 2013", "Hines only", "400 hPa", "1990–99", "36"],
                 ["<b>13d</b>", "<b>p13_jucker_hines</b>", "strat81", "Jucker 2013", "<b>Hines only</b>", "150 hPa", "1990–94", "30–32"]],
                [c * (W / 100) for c in (6, 17, 10, 17, 22, 9, 9, 10)], hl=[8]),
          Spacer(1, 4),
          P("strat63 = 8 mesosphere + the 47 L95 levels of 1–159 hPa + 8 troposphere; strat81 = the same with all 26 L95 tropospheric layers "
            "(Phase 12). The Jucker relaxation uses the equilibrium temperature and relaxation time that Jucker, Fueglistaler and Vallis (2013) "
            "computed radiatively with ozone: a ~300 K summer stratopause, a 190–205 K winter polar upper stratosphere, 4–6 day timescales near "
            "the stratopause and 12–39 days at 100 hPa, applied above 100 hPa with a linear blend to Held–Suarez below 250 hPa. Hines is JCM's "
            "non-orographic scheme launched at 634 hPa with a 1 m/s rms wind; Lott–Miller is the orographic scheme. Costs are end-to-end on one "
            "H100 at 6-hourly output.", CAP)]

    s += [P("3. Method", H1),
          *bullets([
              "<b>w*</b> is the TEM residual vertical velocity in log-pressure coordinates from the residual streamfunction, the eddy covariance "
              "formed in every 4th 6-hourly frame and averaged over the run (annual, DJF, JJA). WACCM6 histSST 1996–2014 is the reference. "
              "Caveat found by Phase 15: one daily phase is tide-biased in the middle stratosphere (a 30 hPa value can differ by 0.3 mm/s "
              "between the 06 UTC frames and all frames), so the 30 hPa numbers in this report are indicative only; 100 and 10 hPa and the "
              "mesosphere are not affected in their conclusions.",
              "<b>Age of air</b> is the zonal mean of each clock over the last 60 days of the chain. The entry-age clock (zero wherever p > 150 hPa) "
              "is compared with WACCM6's entry age (1.19 yr at 55 hPa in the tropics, 2.90 at 12 hPa, ~3.7 at 55 hPa and 50–70°); the surface "
              "clock with CLaMS v3.1/ERA5 2005–2009 (1.33 / 3.68 / 4.12). A 5-year clock is a lower bound where air is old (10-year chains are "
              "0.3–0.4 yr older in the extratropics), so runs are compared at equal chain length.",
              "<b>Mesosphere</b>: annual-mean w* above 10 hPa in the 1994 segment for the tropics (15S–15N) and the polar caps, plus the latitude "
              "standard deviation of the entry age at 3 and 1.5 hPa (zero when the lid value fills the layer). The criterion is qualitative: "
              "upward in the tropics at 1–0.3 hPa, polar descent of at least 1 mm/s, with full ECHAM as the scale.",
              "<b>Acceptance</b> (PLANS Phase 13): tropical w* at 30 / 10 hPa within 1.5× of 0.26 / 0.47 mm/s; tropical entry age at 12 hPa within "
              "0.4 yr of 2.90 and at 55 hPa not worse than the control's; extratropical entry age at 55 hPa ≥ 3.6 yr; mesosphere as above; "
              "cost ≤ 1.3× the control.",
          ])]

    s += [PageBreak(), P("4. All eight runs against the criteria", H1),
          table(acc, acc_w, style=XS, bold_col=8), Spacer(1, 4),
          P("Table 1. The Phase 13 acceptance table across the four steps. The 13d column is read from hines_metrics.md and p13d_mesosphere.md; "
            "the other columns are the values their records state (13_gwd, 13b_jucker, 13c_jucker_n400/output.md). 13c ran ten years, so its "
            "ages are not directly comparable with the 5-year columns. Bold-headed column: the run that comes closest.", CAP),
          P("5. What each step found", H1),
          P("<b>13 — drag under Polvani–Kushner closes the tropical age gap, but by the wrong mechanism.</b> Hines + Lott–Miller at JCM defaults "
            "deposit their momentum in the lower stratosphere: the shallow branch becomes 2.6× WACCM6 (100 hPa w* 1.05 vs 0.40), the tropical "
            "surface-clock age at 55 hPa falls from 2.74 to 1.35 yr (CLaMS 1.33) but the extratropical lower stratosphere becomes 1.4 yr too young "
            "(2.71 vs 4.12) — the full-physics failure, which uses the same two schemes. The deep branch collapses (10 hPa 0.13 → 0.02) and the "
            "mesosphere is still downward: the drag is exhausted below the stratopause. Native L95 changes hundredths of a mm/s; cutting the "
            "nudging at 400 hPa weakens the shallow branch and ages everything by 0.3–0.6 yr."),
          fig(D13, "gwd_wstar_tropics.png",
              "Figure 1 (Phase 13). Tropical w* with Hines + Lott–Miller added to the Polvani–Kushner model (red) against the control (blue) and "
              "WACCM6 (dashed): the profile below 50 hPa doubles and more, the 10 hPa ascent disappears.", maxh=6.2 * cm),
          P("<b>13b — the Jucker relaxation alone ventilates the mesosphere.</b> With no drag at all the tropical residual motion at 1–0.3 hPa "
            "turns upward and the polar descent becomes 1.7–4.9 mm/s (control < 1, full physics 1.3–7): the relaxation itself supplies the "
            "summer-to-winter cell, because its 4–6 day timescale toward a 300 K summer and 200 K winter stratopause makes the meridional "
            "temperature gradient above 5 hPa an order of magnitude larger than under the flat Polvani–Kushner target. The deep branch improves "
            "(10 hPa 0.31 → 0.41) and the extratropical age stays right (3.62); the tropical lower stratosphere gets 0.25 yr older (weaker "
            "100–70 hPa upwelling under the longer JFV timescale there). Hines + Lott–Miller on top repeat the Phase 13 damage.")]

    s += [fig(D13B, "jucker_wstar.png",
              "Figure 2 (Phase 13b). w* in latitude and pressure, Polvani–Kushner control / Jucker relaxation / difference / WACCM6, for the "
              "annual mean, DJF and JJA. Above ~5 hPa the Jucker run has a coherent solstice cell — DJF ascent over the southern hemisphere and "
              "descent over the northern cap, JJA the mirror image — where the control has a patchwork. Below 10 hPa the two are alike.",
              maxh=12.5 * cm),
          P("<b>13c — the 400 hPa cutoff removes the shallow branch; Lott–Miller off is better everywhere.</b> With the ERA5 forcing stopped at "
            "~7 km the dry Held–Suarez troposphere (no convection, no moist baroclinic waves) supplies far less wave flux into the lower "
            "stratosphere than ERA5's upper troposphere: 100 hPa w* 0.06 / 0.10 (WACCM6 0.40), tropical entry age at 55 hPa 2.9 / 2.3 yr. The "
            "deep branch and the mesosphere are fine. The clean ten-year pair with Lott–Miller on and off shows the orographic scheme weakening "
            "both branches and ageing the tropics by 0.7–0.8 yr. So the shallow branch of the dry model is ERA5's to give, and the next run "
            "followed directly: Jucker + Hines only, nudged below 150 hPa.")]

    s += [PageBreak(), P("6. Phase 13d: Jucker + Hines only, nudged below 150 hPa", H1),
          P("One run, p13jh_5yr, 1990–1994 on strat81 (pipeline 25 September 10:12–14:08 PDT, GPU 1). Three comparisons at equal chain length: "
            "Hines added to the no-drag Jucker run, Lott–Miller removed from the Jucker + both-schemes run, and the run against JCM's full physics."),
          table(circ_rows, cw), Spacer(1, 4),
          P("Table 2. Circulation, annual means 1990–1994 (WACCM6 1996–2014). Read from hines_metrics.md (before = Jucker no drag, after = Jucker + "
            "Hines), lm_off_metrics.md (before = Jucker + Hines + Lott–Miller) and jh_vs_echam_metrics.md (before = full ECHAM).", CAP),
          table(age_rows, cw), Spacer(1, 4),
          P("Table 3. Age of air at the end of 1994, zonal means over 10S–10N and 50–70° (both hemispheres), entry-age clock and surface clock. "
            "CLaMS is a surface clock; WACCM6's entry age is 1.19 / 2.90 yr in the tropics at 55 / 12 hPa and ~3.7 at 50–70°, 55 hPa.", CAP)]

    s += [fig(D13D, "hines_wstar_tropics.png",
              "Figure 3. Hines added under the Jucker relaxation (red) against the no-drag run (blue): annual tropical w* profile with WACCM6 "
              "dashed, and monthly w* at 70 and 30 hPa. The shallow branch rises 13 % to 0.33 mm/s at 100 hPa, the deep branch 19 % to 0.49 at "
              "10 hPa (WACCM6 0.40 / 0.47); the 50–20 hPa layer does not move, and the 30 hPa series still sits below WACCM6's cycle.",
              maxh=6.2 * cm),
          fig(D13D, "lm_off_wstar.png",
              "Figure 4. Lott–Miller removed: w* with both schemes / Hines only / difference / WACCM6, annual, DJF, JJA. The orographic scheme's "
              "signature — a 2.5× tropical pipe at 100 hPa and broad extratropical descent through the whole lower stratosphere in both winters — "
              "is gone; the Hines-only maps have WACCM6's shape with a deeper winter polar descent above 10 hPa.", maxh=11 * cm)]

    s += [PageBreak(),
          fig(D13D, "hines_age_profiles.png",
              "Figure 5. Age of air, Jucker no drag (blue), Jucker + Hines (red), CLaMS (dashed): latitude profiles at 55 and 12 hPa and the "
              "tropical vertical profile, for the surface clock (top), the 500 hPa clock (middle) and the entry-age clock (bottom). The entry-age "
              "clock lies on CLaMS's shape from the tropopause to 5 hPa and 0.1–0.2 yr younger than without drag; the surface clock's 1.8 yr "
              "offset in the tropics is the dry troposphere's transit, not a stratospheric difference.", maxh=12.5 * cm),
          fig(D13D, "p13jh_5yr_aoa150_aoa_triptych.png",
              "Figure 6. Entry-age clock after five years (left) against CLaMS's surface clock (middle) and WACCM6's entry age (right). The tropical "
              "pipe has WACCM6's width and contour spacing up to ~10 hPa; above 20 hPa the run is still bounded by the lid value.", maxh=6.5 * cm)]

    s1_rows = [["tropical w* [mm/s], 1990-1994", "Jucker no drag, stride 4", "Jucker + Hines, stride 4", "Jucker no drag, stride 1",
                "<b>Jucker + Hines, stride 1</b>", "WACCM6"]]
    for ph in (100, 70, 50, 30, 10):
        q = f"tropical w* 15S-15N {ph} hPa [mm/s]"
        s1_rows.append([f"{ph} hPa", hines[0][(q, "annual")][0], hines[0][(q, "annual")][1], s1[0][(q, "annual")][0], s1[0][(q, "annual")][1],
                        s1[0][(q, "annual")][3]])
    t10_rows = [["entry-age clock [yr]", "after 5 yr", "<b>after 10 yr</b>", "change", "target"]]
    for lev, reg, rl, tgt in (("55 hPa", "tropics 10S-10N", "55 hPa, tropics", "WACCM6 1.19 (control 1.31)"),
                              ("55 hPa", "50-70 deg", "55 hPa, 50-70 deg", "≥ 3.6"),
                              ("12 hPa", "tropics 10S-10N", "12 hPa, tropics", "2.90 ± 0.4"),
                              ("12 hPa", "50-70 deg", "12 hPa, 50-70 deg", "CLaMS 4.56, WACCM6 4.18")):
        b, a, d = t10[1][("aoa150", lev, reg)][:3]
        t10_rows.append([rl, b, a, d, tgt])
    for lev, reg, rl, tgt in (("55 hPa", "tropics 10S-10N", "surface clock, 55 hPa, tropics", "CLaMS 1.33"),
                              ("55 hPa", "50-70 deg", "surface clock, 55 hPa, 50-70 deg", "CLaMS 4.12")):
        b, a, d = t10[1][("aoa_sfc", lev, reg)][:3]
        t10_rows.append([rl, b, a, d, tgt])
    s += [PageBreak(), P("Ten years, and every frame: the stride-1 diagnostics", H2),
          P("The chain was continued from its 1994 checkpoint to 1999 (25 September, GPU 1, 29-30 min per year) and every comparison "
            "was recomputed from all 6-hourly frames instead of one daily phase, after Phase 15 found that phase tide-biased."),
          table(s1_rows, [c * (W / 100) for c in (22, 15, 15, 15, 18, 15)]), Spacer(1, 4),
          P("Table 5. The same five years, sampled two ways (hines_metrics.md vs 10yr/hines_s1_metrics.md). The 50-20 hPa 'stall' of every "
            "Phase 12-13 table was the 06 UTC tidal phase: from all frames the dry model's ascent between 70 and 30 hPa is 40-70 % above "
            "WACCM6, on it at 100 and 10 hPa. The 30 hPa criterion (within 1.5x of 0.26) is met.", CAP),
          table(t10_rows, [c * (W / 100) for c in (34, 14, 14, 12, 26)]), Spacer(1, 4),
          P("Table 6. The clocks after five and after ten years (10yr/jh10_vs_5_metrics.md; the circulation itself is identical to 0.01 mm/s). "
            "The extratropical entry age reaches the criterion and is still rising; the tropical 12 hPa value is converged and stays 0.17 "
            "outside its tolerance; the tropical 55 hPa entry age was not converged at five years and is now 0.43 yr older than WACCM6 "
            "despite ascent on WACCM6 - old extratropical air mixed into the pipe, not slow ascent. The surface clock keeps drifting with "
            "the dry troposphere's transit.", CAP),
          fig(D10, "hines_s1_wstar_tropics.png",
              "Figure 8. The Phase 13d pair at stride 1: annual tropical w* (WACCM6 dashed) and monthly w* at 70 and 30 hPa. The model sits "
              "above WACCM6's cycle in most months with the seasonal phase right; compare Figure 3, the same runs from the 06 UTC frames.",
              maxh=6.2 * cm),
          fig(D10, "jh10_vs_5_age_profiles.png",
              "Figure 9. Age of air after five (blue) and ten (red) years, CLaMS dashed: surface clock, 500 hPa clock and entry-age clock "
              "(rows). The entry-age clock moves 0.1-0.2 yr at 55 hPa (0.6 over the Antarctic) and is converged at 12 hPa in the tropics; "
              "the two lower clocks rise 0.3-0.5 yr everywhere.", maxh=11 * cm)]
    s += [PageBreak(), P("Mesosphere", H2),
          table(meso_rows, meso_w, hl=[4], style=XS), Spacer(1, 4),
          P("Table 4. Annual-mean w* above 10 hPa in the 1994 segment, tropics / NH cap / SH cap, and the latitude standard deviation of the "
            "entry age at 3 / 1.5 hPa. Rows 1-5 from p13d_mesosphere.md (every 4th frame), the last three from 10yr/p13d10_mesosphere.md "
            "(every frame): at stride 1 the tropical ascent at 1 hPa is +1.0 to +1.1 mm/s where the daily phase read +0.04, and the 1999 "
            "segment repeats 1994 to 0.1-0.3 mm/s.", CAP),
          fig(D13D, "p13d_mesosphere.png",
              "Figure 7. Annual-mean w* above 30 hPa in 1994: the tropical profile for the five runs (left) and the latitude–pressure maps. The "
              "Hines-only run (fourth panel) has the full-physics cell above 1 hPa — tropical ascent of 2 mm/s at 0.3 hPa, polar descent of "
              "4–7 mm/s — with the deep branch below it intact.", maxh=5.5 * cm)]

    s += [P("7. Reading", H1),
          *bullets([
              "<b>Lott–Miller was the damage.</b> Removing it, with everything else fixed, takes the 100 hPa w* from 0.99 to 0.33 (WACCM6 0.40), "
              "doubles the deep branch (0.25 → 0.49) and restores the extratropical entry age (2.06 → 3.47). Under the 150 hPa nudging this is "
              "the same verdict Phase 13c reached under the 400 hPa cutoff, now without the cutoff's confound. The orographic drag as JCM "
              "configures it deposits its momentum below 50 hPa, where the residual circulation does not want it.",
              "<b>Hines alone does what the drag was supposed to do.</b> Under the Jucker relaxation it adds 13 % to the shallow branch, 19 % to "
              "the deep branch (now on WACCM6) and completes the mesospheric cell to full-physics strength at 0.5–0.3 hPa in all three bands. "
              "Every entry-age number moves toward its target by 0.13–0.23 yr, the tropics slightly more, so the age contrast is kept.",
              "<b>Closer to WACCM6 than JCM's own physics.</b> On every circulation number except 30 hPa the dry Jucker + Hines run is nearer "
              "WACCM6 than the full ECHAM run (100 hPa 0.33 vs 1.46; 70 hPa 0.19 vs 0.60; 10 hPa 0.49 vs 0.87), and its extratropical age is right "
              "where the full physics is 1.7 yr too young. The tropical entry age at 55 hPa, 1.41 vs ECHAM's 0.96, brackets WACCM6's 1.19.",
              "<b>Verdict.</b> Met: mesosphere, 10 hPa w*, 100 hPa w* without overshoot, cost (31 min/yr, 1.15×). Missed narrowly: tropical "
              "entry age 12 hPa 3.45 (0.15 outside 2.90 ± 0.4), 55 hPa 1.41 (0.10 worse than the control's 1.31), 50–70° 3.47 (0.13 short of 3.6); "
              "and 30 hPa 0.04 vs 0.26, which is a stride-4 number. None of the Phase 13/13b failures remains. p13_jucker_hines replaces "
              "p13_jucker as the candidate production dry configuration, subject to the stride-1 w* check and Susanne's decision. The Hines "
              "amplitude knob reserved for a shallow-branch overshoot is not needed: the shallow branch is 17 % under WACCM6.",
              "<b>What is left.</b> A ten-year extension (segments 1990–1994 reused, strat81 ERA5 windows exist to 1999) to settle the two age "
              "criteria that a 5-year clock cannot; a stride-1 recomputation of w* to see whether a 50–20 hPa deficit remains at all; if it does, "
              "the Rayleigh-drag family of the Phase 15 sweep (30 → 1 hPa), whose leaderboard already ranks ray30 + a 100 hPa nudging cutoff "
              "first with an entry-age RMSE of 0.45 yr vs CLaMS — Hines + Rayleigh together has not been run; the JFV blend boundary (p_bd 70 hPa) "
              "or a 15-day cap on its timescale for the slow 100–70 hPa upwelling; the per-term drag-tendency diagnostic.",
          ]),
          P("8. Where things are", H2),
          P("Worktree /data/JCM_stripped/jcm-strat-phase13, branch phase13-gwd (not pushed). Runs under runs/p13*_&lt;YYYYMMDD&gt; with the "
            "aggregates runs/p13gwd_5yr, p13gwdl95_5yr, p13l81n400_5yr, p13jucker_5yr, p13juckergwd_5yr, p13jgn400_10yr, p13jhn400_10yr, "
            "p13jh_5yr, p13jh_10yr. Records docs/outputs/13_gwd, 13b_jucker, 13c_jucker_n400, 13d_jucker_hines (output.md, &lt;tag&gt;_metrics.md, "
            "figures, p13*_mesosphere.md; the ten-year, stride-1 diagnostics under 13d_jucker_hines/10yr). Code: jcm_strat/gwd.py (Hines launch level as a pressure), jcm_strat/jucker.py (JuckerColumns) with the table "
            "jcm_strat/data/jfv2013_te_tau_zm.nc, experiments p13_* and physics presets strat_pk_gwd_prod13, strat_jucker_qbo_prod13, "
            "strat_jucker_gwd_prod13, strat_jucker_hines_prod13; pipelines scripts/phase13_run.sh, phase13b_run.sh, phase13c_run.sh, "
            "phase13d_run.sh, phase13d_extend10.sh; analysis scripts/phase12_compare.py, aoa_vs_clams.py, mesosphere_wstar.py. Decision 43 in KEY_DECISIONS.md; "
            "PLANS.md Phase 13–13d; the PROGRESS.md throughput rows.")]

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="jcm-strat Phase 13: wave drag and the radiative relaxation", author="Susanne Baur")

    def footer(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"jcm-strat Phase 13  |  page {d.page}"); c.restoreState()
    doc.build(s, onFirstPage=footer, onLaterPages=footer); print("wrote", out_pdf)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "docs", "outputs", "jcm-strat_phase13_drag_relaxation.pdf"))
