#!/usr/bin/env python3
"""Build the Phase 12 (circulation tests) PDF from the Phase 12 record and its figures.

    python scripts/make_phase12_report.py [docs/outputs/jcm-strat_phase12_circulation.pdf]

The narrative lives here, plain language first; the figures are the tracked PNGs under
docs/outputs/12_circulation/ and every number is read from the <tag>_metrics.md files there, so the
tables cannot drift from the record. Regenerate the PDF whenever the record changes.
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
D = os.path.join(REPO, "docs", "outputs", "12_circulation")
W = A4[0] - 4 * cm
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=8, spaceAfter=5)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
BL = ParagraphStyle("BL", parent=B, leftIndent=12, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=10)
SM = ParagraphStyle("SM", parent=B, fontSize=7.8, leading=9.8)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=19, spaceAfter=4)
SUB = ParagraphStyle("SUB", parent=B, fontSize=10.5, textColor=colors.HexColor("#444444"), spaceAfter=12)


def P(t, s=B):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(f"• {t}", BL) for t in items]


def fig(rel, caption, width=W, maxh=14.5 * cm):
    path = os.path.join(D, rel)
    if not os.path.exists(path):
        return P(f"[figure {rel} not yet available]", CAP)
    w, h = PILImage.open(path).size
    scale = min(width / w, maxh / h)
    return KeepTogether([Image(path, width=w * scale, height=h * scale), Paragraph(caption, CAP)])


def table(rows, colw, hl=None, style=SM):
    cells = [[Paragraph(str(c), style) for c in r] for r in rows]
    t = Table(cells, colWidths=colw, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    for r in (hl or []):
        st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3ecdc")))
    t.setStyle(TableStyle(st))
    return t


def metrics(tag):
    """{(quantity, season): (before, after, diff, ref)} and {(clock, level, region): (before, after, diff, clams)} of <tag>_metrics.md."""
    circ, age = {}, {}
    section = None
    for line in open(os.path.join(D, f"{tag}_metrics.md")):
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


def build(out_pdf):
    today = dt.date.today().strftime("%-d %B %Y")
    m = {t: metrics(t) for t in ("noqbo", "l81", "echam", "ctl_vs_p11a")}
    ctl = m["noqbo"]  # its "before" column is the control

    def circ_row(q, seas, fmt):
        b = ctl[0][(q, seas)]
        return [fmt(b[0]), fmt(m["noqbo"][0][(q, seas)][1]), fmt(m["l81"][0][(q, seas)][1]), fmt(m["echam"][0][(q, seas)][1]), fmt(b[3])]

    def age_row(clock, lev, reg):
        b = ctl[1][(clock, lev, reg)]
        return [b[0], m["noqbo"][1][(clock, lev, reg)][1], m["l81"][1][(clock, lev, reg)][1], m["echam"][1][(clock, lev, reg)][1], b[3]]

    f2 = lambda x: x
    hdr = ["quantity (annual mean, 1990-1994)", "control (Phase 11 A)", "QBO nudging off", "strat81", "full ECHAM physics", "reference"]
    circ_rows = [hdr]
    for ph in (100, 70, 30, 10):
        circ_rows.append([f"tropical upward mass flux {ph} hPa [10^9 kg/s]"] + circ_row(f"upward mass flux {ph} hPa [1e9 kg/s]", "annual", f2))
    for ph in (100, 70, 50, 30, 10):
        circ_rows.append([f"tropical w* 15S-15N {ph} hPa [mm/s]"] + circ_row(f"tropical w* 15S-15N {ph} hPa [mm/s]", "annual", f2))
    circ_rows.append(["tropical w* 10 hPa, DJF [mm/s]"] + circ_row("tropical w* 15S-15N 10 hPa [mm/s]", "DJF", f2))
    age_rows = [["age of air after 5 years [yr]", "control", "QBO off", "strat81", "full ECHAM", "CLaMS (surface clock)"]]
    for clock, lab in (("aoa_sfc", "surface clock"), ("aoa500", "500 hPa clock")):
        for lev in ("55 hPa", "12 hPa"):
            for reg, rl in (("tropics 10S-10N", "tropics"), ("50-70 deg", "50-70 deg")):
                age_rows.append([f"{lab}, {lev}, {rl}"] + age_row(clock, lev, reg))
    cw = [c * (W / 100) for c in (34, 13, 13, 13, 14, 13)]

    s = [P("jcm-strat Phase 12: why is the stratospheric circulation too weak?", TITLE),
         P("Four 5-year runs, 1990-1994, of the Phase 11 transport model with one change each: the QBO nudging switched off, the full L95 "
           "troposphere restored (strat81), and JCM's complete ECHAM physics in place of the dry Polvani-Kushner stratosphere - against a "
           "control that is Phase 11 run A. Measured by the TEM residual vertical velocity w* and the age of air with two clocks (zero at the "
           f"surface and zero at 500 hPa), against WACCM6 and CLaMS. Record as of {today}, branch phase12-circulation.", SUB)]

    s += [P("1. The question", H1),
          P("After Phase 11 the model's stratosphere looked too weakly ventilated: above ~20 hPa the age of air was whatever the 1 hPa tracer lid "
            "prescribed, the tropical lower stratosphere at 55 hPa read 2.7 years against CLaMS' 1.3 and was still ageing, and N2O and CFC-11 sat "
            "6 km too low. Susanne asked (16 September) for two tests of the dry model - the QBO nudging off, and the tropospheric layers that "
            "the Phase 9 strat63 grid had thinned put back - each with before/after plots of w* and of the age of air for a surface clock and a "
            "500 hPa clock, and then (18 September) for the same five years with JCM's full physics and the clocks: is the age too old in JCM's own "
            "physics too, or only in the stripped model?"),
          P("2. The four runs, exactly", H1),
          P("Everything below is read from the runs' resolved configurations. Rows not listed are identical in all runs: T63, 12-minute step, "
            "Gregorian calendar, one calendar year per chained segment, 6-hourly instantaneous output, terrain from file, the Phase 11 tracer term "
            "(1 hPa lid, no sinks, unit pulses), global mass fixer on with the clocks and n2o/cfc11 excluded, and the same ERA5 initial state."),
          table([["item", "control (= Phase 11 A + aoa500)", "QBO nudging off", "strat81", "full ECHAM physics"],
                 ["vertical grid", "strat63: 8 mesosphere + 47 stratosphere (the L95 levels 1.08-159 hPa) + 8 troposphere", "same",
                  "strat81: same 8 + 47, plus all 26 L95 tropospheric layers", "JCM's native L95 (22 + 47 + 26)"],
                 ["upper sponge", "4 levels, factor 6.73 per level (remapped to L95's damping profile in pressure)", "same", "same",
                  "L95 native: 10 levels, factor 2 per level (the profile the strat tables reproduce)"],
                 ["physics", "dry: Held-Suarez troposphere, Polvani-Kushner relaxation above (gamma 4 K/km, tau 15 d, seasonal winter hemisphere, "
                  "vortex cooling faded above 3 hPa). No radiation, convection, clouds, moisture physics or gravity-wave drag", "same", "same",
                  "full ECHAM: RRTMGP radiation with a prescribed monthly ozone climatology, MACv2-SP aerosol, simple chemistry, Sundqvist cloud "
                  "fraction, 1-moment microphysics, TTE/TKE vertical diffusion, ECHAM surface, Tiedtke convection, Hines gravity-wave drag, "
                  "Lott-Miller orographic drag"],
                 ["surface boundary conditions", "none needed", "none", "none", "SST, sea ice, land temperature, soil moisture, snow, albedo from JCM's "
                  "present-day climatology file"],
                 ["ERA5 nudging", "u, v, T wherever p > 150 hPa; tau 6 h; lowest 2 levels free; target 6-hourly", "same", "same",
                  "same, target sampled 12-hourly (the 6-hourly one-year target did not fit in GPU memory beside RRTMGP; JCM interpolates between samples)"],
                 ["QBO nudging", "tropical zonal-mean u to ERA5 monthly means, tau 1 d, |lat| < 25 deg, 90-1 hPa, mean-preserving target; inside the "
                  "Polvani-Kushner term", "<b>off</b> (qbo: null)", "same as control", "same parameters, as its own term (unit-tested to be the same maths)"],
                 ["clocks", "aoa (700 hPa), aoa150, aoa_sfc (lowest 2 layers), aoa500", "same", "same", "same"],
                 ["written output", "13 fields: u, v, T, q, p_s, geopotential, omega, 4 clocks, n2o, cfc11 (the 19 injection tracers are integrated "
                  "but not written; Phase 11 A wrote all 31)", "same", "same", "same 13 (the ~120 ECHAM diagnostics not written)"],
                 ["chunk length", "10 days", "10 days", "10 days", "5 days (GPU memory)"],
                 ["GPU and cost", "GPU 1, 27-30 min per year", "GPU 3, 27-30 min", "GPU 2, 27-30 min", "GPU 0, 3.1-3.4 h per year (11x)"]],
                [c * (W / 100) for c in (14, 26, 14, 18, 28)]),
          Spacer(1, 4),
          P("The control repeats Phase 11 A with the extra clock, because that run had no 500 hPa clock and the comparison needed the same clock "
            "definitions before and after. Its dynamics are Phase 11 A's: w* agrees to 0.005 mm/s, the up-flux to 0.1 x 10^9 kg/s, the age to "
            "0.01 year - the noise floor of a 5-year mean of a chaotic run (ctl_vs_p11a_metrics.md). Differences below that in the other runs are not "
            "differences. Between the control and strat81 the only physics change is the 18 extra tropospheric layers; between strat81 and the full "
            "physics the intended change is the physics package (and the surface forcing file it needs), the unavoidable side changes are the native "
            "L95 table with its native sponge, the 12-hourly target and the shorter chunks.", CAP)]

    s += [Spacer(1, 6), P("3. Method", H1),
          *bullets([
              "<b>w*</b> is the TEM residual vertical velocity in log-pressure coordinates: v* = [v] - d/dp([v'theta'] / d[theta]/dp), the residual "
              "mass streamfunction Psi* from v*, then omega* from dPsi*/dphi and w* = -H omega*/p with H = 7 km. The eddy covariance is formed in every "
              "daily snapshot of the 6-hourly archive and averaged over the whole run (annual) and over DJF and JJA. WACCM6 histSST 1996-2014 "
              "(its daily zonal-mean TEM tape, the same formula) is the reference; the model years 1990-1994 are not in that tape.",
              "<b>Age of air</b> is the zonal mean of each clock over the last 60 days of 1994, converted to years: aoa_sfc (zero in the lowest two model "
              "layers, the CLaMS convention) and the new aoa500 (zero wherever p > 500 hPa). CLaMS v3.1 driven by ERA5, 2005-2009 mean, is the "
              "reference (CLaMS starts in 2004). A 5-year clock has not converged (Phase 11: +0.15 yr per year at 55 hPa in the tropics), so the "
              "age plots compare the same stage of spin-up; differences are meaningful, absolute values are lower bounds.",
              "<b>Tropical upward mass flux</b> is max minus min of Psi* over |lat| <= 60 deg at a level, the standard Brewer-Dobson strength metric "
              "(WACCM6 gives 6.1 x 10^9 kg/s at 70 hPa; the ERA5-era literature 6 to 8).",
          ]),
          P("4. Results: the circulation", H1),
          table(circ_rows, cw, hl=[]), Spacer(1, 4),
          P("Table 1. Annual means over 1990-1994 (WACCM6 1996-2014 for the reference column). Read from noqbo_metrics.md, l81_metrics.md, "
            "echam_metrics.md; the control column is the 'before' of each.", CAP),
          fig("noqbo_wstar_tropics.png",
              "Figure 1. QBO nudging off (red) against the control (blue): tropical (15S-15N) w* profile with the Eulerian [w] dotted, and the "
              "monthly w* at 70 and 30 hPa with WACCM6's climatological cycle dashed. Without the nudging the lower-branch upwelling falls by "
              "~0.1 mm/s; nothing changes at 10 hPa.", maxh=6.2 * cm),
          fig("l81_wstar_tropics.png",
              "Figure 2. strat81 (red) against the control: the deep branch at 10 hPa doubles, the lower branch weakens like in the QBO-off run and "
              "the ascent stalls between 50 and 20 hPa.", maxh=6.2 * cm)]

    s += [PageBreak(),
          fig("echam_wstar_tropics.png",
              "Figure 3. Full ECHAM physics (red) against the dry control: the tropical profile follows WACCM6 (dashed) from 50 to 20 hPa and "
              "overshoots it below 70 hPa and above 20 hPa; the 50-20 hPa stall of the dry model is gone.", maxh=6.2 * cm),
          fig("echam_wstar.png",
              "Figure 4. w* in latitude and pressure: control, full physics, their difference and WACCM6, for the annual mean, DJF and JJA. "
              "The dry model's tropical pipe is narrow and patchy with weak, diffuse extratropical descent; the full physics has WACCM6's broad "
              "pipe and a deeper polar descent, both stronger than WACCM6's.", maxh=15 * cm)]

    s += [PageBreak(), P("5. Results: the age of air", H1),
          table(age_rows, cw), Spacer(1, 4),
          P("Table 2. Mean age at the end of 1994 (last 60 days), zonal means over 10S-10N and 50-70 deg (both hemispheres, cos-weighted), for the "
            "surface clock and the 500 hPa clock. CLaMS is a surface clock. Read from the same metrics files.", CAP),
          fig("echam_age_profiles.png",
              "Figure 5. Age of air, control (blue), full physics (red) and CLaMS (dashed): latitude profiles at 55 and 12 hPa and the tropical "
              "vertical profile, for the surface clock (top) and the 500 hPa clock (bottom). The full-physics tropical profile lies on CLaMS from "
              "the tropopause to 5 hPa; its extratropical lower stratosphere is 1.4 years too young.", maxh=12.5 * cm)]
    s += [PageBreak(),
          fig("l81_age_profiles.png",
              "Figure 6. The same for strat81 against the control: the surface clock gets older everywhere, the 500 hPa clock does not move. The "
              "difference between the two clocks - the surface-to-500 hPa transit of the dry troposphere - grows from 0.35 to 0.78 years.", maxh=12.5 * cm),
          fig("noqbo_age_aoa500.png",
              "Figure 7. 500 hPa clock, control / QBO off / difference / CLaMS: without the nudging the tropical lower stratosphere is 0.3 years older.",
              maxh=5.5 * cm)]

    s += [PageBreak(), P("6. Reading", H1),
          *bullets([
              "<b>The control reproduces Phase 11 A.</b> Every circulation and age number agrees to the noise floor, so the Phase 12 code (the "
              "strat81 table, the clock subclass, the QBO-off switch) left the default configuration untouched, and the comparisons below are clean.",
              "<b>QBO nudging off: the lower branch weakens, the age gets older.</b> The change is confined to |lat| < 30 deg and 100-5 hPa with the "
              "tilted dipole of the QBO's secondary meridional circulation. w* at 70 hPa 0.33 to 0.25 mm/s, at 50 hPa 0.26 to 0.16; nothing at "
              "10 hPa; 55 hPa tropical age +0.26 (surface clock) / +0.28 years (500 hPa clock). The imposed ERA5 shear zones add ~0.1 mm/s of "
              "lower-stratospheric upwelling, as theory says they should, and do nothing to the deep branch. The QBO nudging is not what makes "
              "the stratosphere old; it slightly helps. Without it the model has no QBO at all (weak steady easterlies, -16 m/s at 20 hPa).",
              "<b>strat81: the deep branch doubles, the stratospheric age does not move.</b> Tropical w* at 10 hPa 0.13 to 0.31 mm/s (DJF 0.41 to 0.59, "
              "WACCM6 0.64), polar descent above 10 hPa deeper - the deep branch does respond to how the troposphere is resolved, so the wave "
              "source is part of the story. But the lower branch weakens like in the QBO-off run and the 50-20 hPa stall gets worse (30 hPa w* "
              "0.09 to 0.02). The age splits by clock: the surface clock reads 0.33 years older at 55 hPa, the 500 hPa clock 0.10 years younger. "
              "With 26 instead of 8 tropospheric layers the resolved vertical transport of the dry troposphere (no convection, no boundary-layer "
              "mixing) is slower, and the surface clock carries that transit (0.35 to 0.78 years) into every stratospheric comparison. The 500 hPa "
              "clock is the fairer one against CLaMS, whose surface-to-tropopause transit is weeks, and it says: strat81's stratosphere is as old as "
              "strat63's. At 6-hourly output strat81 costs nothing end to end (the run is output-bound).",
              "<b>Full physics: the age is not too old.</b> With RRTMGP, convection and gravity-wave drag, under the same nudging, the tropical age "
              "lies on CLaMS from the tropopause to 5 hPa: 1.33 years at 55 hPa (CLaMS 1.33), 3.64 at 12 hPa (3.68). The 20-1 hPa layer, flat at the "
              "lid value in every dry run, has latitude structure. The surface-to-500 hPa transit is 0.26 years: convection mixes the troposphere. "
              "So the old age of Phases 4-11 belongs to the dry Polvani-Kushner configuration, not to the dycore, the semi-Lagrangian transport "
              "(Phase 9 had already shown resolution changes nothing) or the tracer scheme.",
              "<b>Full physics: what is wrong has flipped sign.</b> The circulation is too strong, above all its shallow branch: tropical w* 1.46 mm/s "
              "at 100 hPa (WACCM6 0.40), 0.60 at 70 hPa (0.21), up-flux 28.7 x 10^9 kg/s at 100 hPa (10.9) and 11.3 at 70 hPa (6.1); at 50 and 30 hPa "
              "it matches WACCM6, at 10 hPa it is twice WACCM6 (0.87 vs 0.47). The extratropical lower stratosphere is too young (55 hPa at 50-70 deg "
              "2.73 vs 4.12; contrast 1.4 vs 2.8 years). The 100 hPa numbers sit at the top of the nudged layer inside the convective outflow, so "
              "part of the excess there is convection, but 70 hPa is above both and still 3x WACCM6. This is the same physics whose Phase 6 "
              "reference year had no Arctic vortex and a half-strength Antarctic one (issue 35): an over-driven Brewer-Dobson circulation and a weak "
              "vortex are two faces of too much wave forcing, or too little wave filtering, of the extratropical stratosphere - the gravity-wave "
              "drag settings are the first suspect.",
              "<b>Where the dry model's deficit sits.</b> Its lower branch is already stronger than WACCM6's (70 hPa 0.33 vs 0.21); the age excess "
              "(2.3-2.4 years at 55 hPa with the 500 hPa clock, 4.4 at 12 hPa) comes from the near-zero ascent between 50 and 20 hPa, which no "
              "dry-model change repaired, from the lid-filled upper stratosphere, and from the tropospheric transit of the surface clock. The full "
              "physics has no 50-20 hPa stall. It adds three things at once - radiative heating (with ozone), gravity-wave drag and convection - and "
              "this phase does not separate them. On the physics: the residual circulation is wave-driven, and Newtonian relaxation to an equilibrium "
              "temperature supplies whatever heating the ascent demands, so the absence of an explicit ozone heating term is unlikely to be the "
              "leading cause on its own; what the relaxation gets wrong is the radiative time scale (one 15-day value at all heights against a "
              "few days near the stratopause) and the equilibrium temperature's structure and seasonality, which set the zonal winds that filter "
              "the waves. The dry model also has no gravity-wave drag at all, and its mesosphere does not circulate (Phase 10). The cheapest next "
              "tests, in order: the dry model plus Hines gravity-wave drag; the dry model plus RRTMGP with the prescribed ozone; both.",
          ]),
          P("7. Where things are", H2),
          P("Runs under runs/p12{ctl,noqbo,l81,echam}_&lt;YYYYMMDD&gt; and the aggregates runs/p12*_5yr in the phase12 worktree; the record "
            "docs/outputs/12_circulation/output.md with &lt;tag&gt;_metrics.md and the figures &lt;tag&gt;_wstar*.png, &lt;tag&gt;_age_*.png for "
            "tags noqbo, l81, echam, ctl_vs_p11a and the aoa_vs_clams triptychs per run and clock; the strat81 table in jcm_strat/levels.py; the "
            "clock subclass ProductionTracersAoa500 in jcm_strat/advection_tracers.py; the QBO-off switch (qbo: null) in jcm_strat/qbo_nudging.py; "
            "experiments p12_ctl, p12_noqbo, p12_l81, p12_echam and physics presets strat_pk_qbo_prod12, strat_pk_prod12_noqbo, echam_prod12 under "
            "jcm_strat/config; the comparison script scripts/phase12_compare.py (w* from Psi* in scripts/strat_circulation.py); the pipelines "
            "scripts/phase12_run.sh, phase12_finish.sh, phase12_echam.sh. Decisions 41 and 42 in KEY_DECISIONS.md; open questions at the end of "
            "the record.")]

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="jcm-strat Phase 12: circulation tests", author="Susanne Baur")

    def footer(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"jcm-strat Phase 12  |  page {d.page}"); c.restoreState()
    doc.build(s, onFirstPage=footer, onLaterPages=footer); print("wrote", out_pdf)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "docs", "outputs", "jcm-strat_phase12_circulation.pdf"))
