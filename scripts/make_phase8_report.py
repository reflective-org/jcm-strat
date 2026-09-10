#!/usr/bin/env python3
"""Build the Phase 8 (QBO nudging) PDF from the Phase 8 record and its figures.

    python scripts/make_phase8_report.py [docs/outputs/jcm-strat_phase8_qbo.pdf]

The narrative lives here, plain language first; the figures are the tracked PNGs under
docs/outputs/08_qbo/. Numbers are copied from docs/outputs/08_qbo/output.md and the metric
tables beside the figures - those records are canonical; regenerate the PDF whenever they change.
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
D = os.path.join(REPO, "docs", "outputs", "08_qbo")
W = A4[0] - 4 * cm
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=8, spaceAfter=5)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
BL = ParagraphStyle("BL", parent=B, leftIndent=12, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=10)
SM = ParagraphStyle("SM", parent=B, fontSize=8.3, leading=10.5)
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


def table(rows, colw, hl=None):
    cells = [[Paragraph(str(c), SM) for c in r] for r in rows]
    t = Table(cells, colWidths=colw, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    for r in (hl or []):
        st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3ecdc")))
    t.setStyle(TableStyle(st))
    return t


def build(out_pdf):
    today = dt.date.today().strftime("%-d %B %Y")
    s = [P("jcm-strat Phase 8: giving the model a QBO", TITLE),
         P("Nudging the tropical stratospheric wind towards ERA5 on the Phase 6 configuration (Polvani-Kushner stratosphere, "
           "ERA5-nudged troposphere, four passive tracers, T63L95, 12 minute step). Two versions: the nudging window reaching up to "
           "4 hPa, run for 2005 and for the 2005 to 2009 chain, and then the same runs with the window top raised to 1 hPa; then a "
           "sweep of the relaxation time (10, 5, 2, 1 days) over the same five years, after which 1 day became the default, and a "
           "mean-preserving interpolation of the monthly target. "
           f"Record as of {today}, branch phase8-qbo-nudging.", SUB)]

    # ------------------------------------------------------------------ 1
    s += [P("1. The problem", H1),
          P("The stripped model has no quasi-biennial oscillation. Its equatorial stratosphere sits in steady easterlies of 12 to 14 m/s "
            "with a year-to-year variability of 4 m/s where ERA5 has 17 (Phase 6 record). It cannot grow one: the QBO is driven by "
            "tropical waves launched by convection, which the dry model does not have, and by gravity-wave drag, which is off, and it "
            "needs about 500 to 700 m vertical spacing in the tropical lower stratosphere, where the L95 grid has about 1 km. "
            "For aerosol transport the QBO matters directly. It modulates the tropical upwelling and the subtropical mixing barrier, so "
            "an injected layer's residence time in the tropics and its leak to mid-latitudes differ by tens of percent between the "
            "easterly and the westerly phase; Pinatubo showed it and every injection study reports it. Under specified dynamics the "
            "standard remedy is to relax the tropical wind towards the observed one, as WACCM does in its QBO-nudged configurations. "
            "That is what Phase 8 adds, and it measures what changes.")]

    # ------------------------------------------------------------------ 2
    s += [P("2. Everything the model is relaxed towards, in one table", H1),
          P("A relaxation adds a tendency -(x - target)/tau to a field x: the field is pulled towards the target with e-folding time tau. "
            "The stripped model is held together by the six relaxations in the table, acting on different fields in different layers. The QBO nudging "
            "of this phase is one of them; the others are unchanged from Phase 6. 'Target cadence' says how often the target itself "
            "carries new information; between samples every target is interpolated linearly in time to the 12 minute step."),
          table([["field", "where", "target", "tau", "target cadence"],
                 ["u, v, T (full fields)", "troposphere: pressure above 150 hPa, except the two lowest model levels",
                  "ERA5 (WeatherBench2 6-hourly, regridded to the model grid and levels)", "6 h", "6-hourly samples"],
                 ["T (full field)", "stratosphere: pressure below 100 hPa, all latitudes",
                  "Polvani-Kushner (2002) seasonal equilibrium: US standard atmosphere outside the winter polar cap, a vortex profile cooling at "
                  "4 K/km inside it (cap edge 50 deg, width 10 deg), the cooling faded out above 3 hPa", "15 d", "analytic; follows the calendar"],
                 ["T (full field)", "troposphere, underneath the ERA5 nudging",
                  "Held-Suarez equilibrium, floored by the standard atmosphere", "40 d in the free troposphere, 4 d in the boundary layer (sigma above 0.7)",
                  "analytic (the 6 h nudging dominates)"],
                 ["u, v (Rayleigh friction)", "boundary layer, sigma above 0.7", "zero", "1 d at the surface, weakening linearly to none at sigma 0.7", "-"],
                 ["zonal-mean u only", "tropics: full weight within 15 deg of the equator, cos-squared taper to zero at 25 deg; pressure 90 hPa up to the window top "
                  "(4 hPa in the first version, 1 hPa in the second), full weight from 40 hPa to about 9 hPa (2.2 hPa in the second version), log-linear tapers",
                  "ERA5 monthly-mean zonal-mean zonal wind (CDS pressure-level product, 25 levels 1000 to 1 hPa, 2005 to 2009)", "10 d in the first version; 1 d since section 7",
                  "monthly means, interpolated between month centres (mean-preserving nodes since section 8)"],
                 ["u, v to zero; T to its zonal mean and to 250 K (sponge)", "the top 10 model levels, 0.01 to 0.15 hPa (above about 65 km)",
                  "zero wind; zonal-mean T and 250 K", "1.5 h at the top level, doubling with each level downward (32 d at the tenth)", "-"]],
                [2.6 * cm, 4.3 * cm, 4.9 * cm, 2.9 * cm, 2.3 * cm], hl=[5]),
          Spacer(1, 4),
          P("In altitude (7 km scale height): 150 hPa is about 13 km, 90 hPa 17 km, 40 hPa 22.5 km, 9 hPa 33 km, 4 hPa 39 km, 2.2 hPa 43 km, "
            "1 hPa 48 km. The model lid is 0.01 hPa, about 80 km. In its first version the QBO nudging was the slowest data-driven relaxation in the "
            "model (10 days against 6 hours in the troposphere) and the one with the coarsest target (monthly against 6-hourly); sections 7 "
            "and 8 change the first and keep the second on purpose.", CAP)]

    # ------------------------------------------------------------------ 3
    s += [P("3. The recipe, and why each choice", H1),
          *bullets([
              "<b>Target: ERA5 monthly zonal means from the Copernicus Climate Data Store.</b> ERA5's tropical stratospheric winds are "
              "observation-constrained (the Singapore and tropical radiosonde network, GNSS radio occultation) and its QBO is right. The "
              "CDS monthly product reaches 1 hPa, whereas the WeatherBench2 store that feeds the tropospheric nudging has nothing usable above "
              "about 60 hPa, which is why the QBO could not simply be included in that nudging. ERA5 is also what the troposphere follows, so "
              "one reanalysis constrains the whole column, and the years line up with the CLaMS age-of-air reference. A WACCM target would have "
              "imposed a modelled, weaker QBO; a climatological or idealised one would have lost the real 2005 to 2009 phase sequence.",
              "<b>What is relaxed: only the zonal mean of the zonal wind.</b> At every longitude of a latitude row the same tendency, "
              "-(u_bar_model - u_bar_ERA5)/tau, is applied. The waves that do the transport are left alone; only the mean flow they propagate "
              "through is corrected. Relaxing the full wind field would damp the eddies too.",
              "<b>Where: the QBO's own domain.</b> Full weight within 15 degrees of the equator, fading to zero at 25; full weight between "
              "40 and 9 hPa, fading to zero at 90 hPa (clear of the 150 hPa tropospheric nudging) and at 4 hPa (below the semiannual "
              "oscillation region). Section 6 raises the top to 1 hPa.",
              "<b>How fast: tau = 10 days,</b> WACCM's choice. Slow enough not to fight the resolved waves step by step, fast enough to hold "
              "the observed phase. It also means the model is <i>guided</i>, not prescribed: its own dynamics can and do pull back, which is "
              "why the amplitude comes out at 80 percent of the target (section 5) and why a shorter tau is the obvious next knob (section 7).",
              "<b>Implementation.</b> jcm_strat/qbo_nudging.py; the term runs on the column path, the zonal mean is a segment mean over "
              "the columns of each latitude row, the fraction of year comes from the same clock the seasonal Polvani-Kushner term uses, and "
              "the calendar year is a configuration argument that the segment chain passes per year. The QBO tendency is computed inside "
              "the Polvani-Kushner term (PolvaniKushnerQbo, one term instead of two); three CPU tests check the weights, that the tendency "
              "equals -k w (u_bar - target) exactly, and that the combined term equals the two-term sum. Configuration: "
              "physics/strat_pk_qbo.yaml, experiment p8_qbo.",
              "<b>One hazard.</b> The first three attempts died with RESOURCE_EXHAUSTED allocating 29 GiB. JAX preallocates 75 percent of the "
              "card by default; the compiled step holds the 29 GB one-year nudging target and at times a second copy of it, so the Phase 6 "
              "configuration sat just below that ceiling and any additional term tipped it over. scripts/env.sh now sets "
              "XLA_PYTHON_CLIENT_MEM_FRACTION=0.92. Nothing about the physics changed.",
          ])]

    # ------------------------------------------------------------------ 4
    s += [P("4. The runs", H1),
          table([["run", "window top", "length", "purpose", "compared with"],
                 ["p8_qbo_2005_oom, _oom2", "4 hPa", "0", "GPU out of memory under the default 75 percent preallocation", "-"],
                 ["p8_qbo_2005", "4 hPa", "1 year (2005)", "first year with QBO nudging", "p6_pk_g4_t15_s05_top3 (Phase 6, same year)"],
                 ["p8_2005 to p8_2009, aggregate p8_5yr", "4 hPa", "5 years", "the chain with tracers (chain_years.sh, 82 min on GPU 0)", "p6_5yr (Phase 6 chain)"],
                 ["p8b_2005 to p8b_2009, aggregate p8b_5yr", "1 hPa", "5 years", "the same chain with the window top raised to 1 hPa (section 6)", "p8_5yr and p8_qbo_2005"]],
                [4.2 * cm, 1.8 * cm, 2.2 * cm, 5.0 * cm, 3.8 * cm]),
          Spacer(1, 4),
          P("All runs: T63L95, 12 minute step, ERA5-nudged troposphere below 150 hPa, Polvani-Kushner stratosphere as chosen in Phase 6, "
            "four passive tracers, GPU 0. The chains are five one-year segments, each restarted from the previous checkpoint.", CAP)]

    # ------------------------------------------------------------------ 5
    s += [P("5. Results with the window top at 4 hPa", H1),
          P("Acceptance checks proposed before the runs, all on the 2005 to 2009 chain unless stated:"),
          table([["check", "threshold", "result"],
                 ["equatorial (5S-5N) monthly u vs ERA5, 10-70 hPa", "RMS below 5 m/s (Phase 6: 16)", "<b>pass</b>: 3.9 m/s (2005 alone 4.2; Phase 6 chain 16.3)"],
                 ["QBO amplitude: deseasonalised std at 20 and 30 hPa", "within 30 percent of ERA5", "<b>pass</b>: 14.1 / 12.4 m/s vs ERA5 17.5 / 15.2 (81, 82 percent); 10 hPa 78 percent, 50 hPa 73 percent. Phase 6: 3.9 / 3.7"],
                 ["the change is confined to the tropics", "RMS change in time-mean u outside 30 deg, 1-100 hPa, below 2 m/s; troposphere unchanged", "<b>pass</b>: 0.5 m/s outside, 0.0 in the troposphere, 3.3 inside the window"],
                 ["polar vortex, sudden warmings", "unchanged within noise", "<b>pass</b>: DJF u(60N, 10 hPa) 32 m/s (Phase 6: 32, ERA5 28); the January 2009 warming moves 5 days closer to ERA5, a spurious March 2005 reversal disappears; 2006 and 2007 still missed (issue 33)"],
                 ["stratospheric climatology vs ERA5, 100-1 hPa", "not worse than Phase 6", "<b>pass on T</b>: 6.3 K (6.4); <b>u 6.4 m/s (5.6)</b>: the extra error is the tropical upper stratosphere, see below"],
                 ["tracer conservation", "Phase 3 levels", "<b>pass</b>: unity max deviation 2.6e-4, sai burden -0.8 percent vs analytic, minima at or above 0, top-level polar sai 8 percent of the column"],
                 ["age of air", "reported", "tropics 2.16 yr at 55 hPa (Phase 6: 2.29; CLaMS 1.33); contrast to 50-70 deg 1.63 (1.56; 2.79); at 12 hPa 3.61 (3.70; 3.68)"],
                 ["throughput", "within 5 percent of Phase 6", "<b>fail, -13 percent</b>: 3880 vs 4445 days/hr stepping (8 vs 7 ms per step); the zonal-mean reduction costs about 1 ms, issue 44"]],
                [4.6 * cm, 4.4 * cm, 8.0 * cm]),
          Spacer(1, 6),
          fig("5yr/qbo_time_height_before_after.png",
              "Figure 1. Equatorial (5S to 5N) zonal-mean zonal wind, monthly, 2005 to 2009, 100 to 1 hPa. Top: the Phase 6 chain, steady "
              "easterlies. Middle: the QBO-nudged chain. Bottom: ERA5. Dotted lines mark the nudging window (90 to 4 hPa). The descending "
              "easterly and westerly shear zones are reproduced in phase. Two shortfalls are visible: the westerly phases are weaker than "
              "ERA5's (+5 to +10 m/s where ERA5 has +10 to +20), and above the window the model is more easterly than ERA5 and misses the "
              "semiannual oscillation at 1 to 3 hPa entirely.", maxh=12 * cm)]
    s += [fig("5yr/qbo_profiles.png",
              "Figure 2. Left: time-mean equatorial wind. Middle: its deseasonalised standard deviation, the QBO amplitude, 80 percent of "
              "ERA5's inside the window. Right: the change in time-mean zonal-mean wind, nudged minus Phase 6, with the window dotted: the "
              "change is confined to the tropics, apart from the easterly anomaly above the window at 1 to 3 hPa (10 to 15 m/s more "
              "easterly than before; -24 m/s at 3 hPa against ERA5's -8). Momentum is carried upward out of the nudged layer and nothing "
              "above opposes it, which is the whole of the 0.8 m/s global wind-error increase in the acceptance table."),
          fig("1yr/qbo_time_height_before_after.png",
              "Figure 3. The single year 2005 (Phase 6 run, nudged run, ERA5). After 30 days the wind at 10 / 20 / 30 hPa reads "
              "-29 / -21 / -6 m/s against ERA5's -31 / -26 / -6 (Phase 6: +2 / +5 / +6). The nudging locks on within a month.", maxh=11 * cm)]
    s += [PageBreak(), P("What the rest of the stratosphere and the tracers did", H2),
          P("The five-year mean transport moves a little, in the right direction, and not much: the QBO mainly redistributes transport "
            "between its phases, and a five-year mean averages over two cycles. Tropical age of air at 20 km drops from 2.29 to 2.16 years, "
            "the tropics-to-extratropics contrast rises from 1.56 to 1.63 years (CLaMS 2.79), and the Brewer-Dobson upwelling at 70 hPa "
            "strengthens by 7 percent (7.2 to 7.7 x 10^9 kg/s; WACCM6 6.1). The 0.9 year tropical excess that remains is the Phase 4 "
            "diagnosis unchanged: slow transit through the unmixed troposphere and lower stratosphere (issue 25), not the tropical wind. "
            "The QBO's value for aerosol is in phase-dependent statements (residence time in the easterly against the westerly phase, "
            "subtropical leakage), which this configuration can now make and the Phase 6 one could not."),
          fig("5yr/p8_5yr_aoa_profiles.png",
              "Figure 4. Mean age of air at about 20 km (left) and 30 km (middle), and the tropical profile (right): nudged chain (blue), "
              "Phase 6 chain (orange dashed), CLaMS (green), WACCM6 entry age (red), and the offline clock carried by PARADIS winds (violet). "
              "The QBO nudging changes the age by 0.1 year in the tropics and nothing elsewhere.", maxh=8 * cm),
          fig("5yr/strat/vortex_series.png",
              "Figure 5. Polar-vortex wind at 60N (top) and 60S (bottom), 10 hPa: nudged chain (orange), Phase 6 chain (blue), ERA5 (black), "
              "WACCM6 envelope (grey), ERA5 major warmings dashed red. The two model curves lie on top of each other outside the tropics: "
              "the nudging does what it says, the tropical mean flow and nothing else.", maxh=9 * cm)]
    s += [fig("5yr/circulation/qbo_time_height.png",
              "Figure 6. The same equatorial section as Figure 1 with WACCM6 histSST (free-running, same years) as the third panel instead of "
              "the Phase 6 chain. WACCM's own QBO is weaker than ERA5's and out of phase with the real one, which is why WACCM was not used "
              "as the target; its semiannual oscillation at 1 to 3 hPa, however, is present, and ours is not.", maxh=12 * cm)]

    # ------------------------------------------------------------------ 6
    s += [PageBreak(), P("6. Raising the window top to 1 hPa", H1),
          P("Two defects of the first version point at the top of the window. The westerly phase of the QBO first appears at 5 to 10 hPa "
            "and descends from there; with the taper ending at 4 hPa that onset layer was only partly nudged (weight 0.3 at 5 hPa, 0.7 at "
            "7 hPa). And above the window the mean flow had become 10 to 15 m/s more easterly than ERA5 (Figure 2), a reservoir of easterly "
            "momentum sitting directly on top of the onset layer. Both argue for extending the window upward. The ERA5 monthly target "
            "already reaches 1 hPa and the model lid is 0.01 hPa, so this is one configuration key: p_top_hpa 4 becomes 1. With the "
            "existing taper the weight is then 1 from 40 hPa up to 2.2 hPa and falls to zero at 1 hPa; the semiannual oscillation at "
            "1 to 3 hPa, whose monthly means ERA5 resolves, is nudged in with it. Nothing else changed: same tau, same latitude window, "
            "same target, same years. Runs p8b_2005 to p8b_2009, aggregate p8b_5yr, compared against the 4 hPa runs. One segment died once in "
            "JCM's provenance probe, which decodes the working-tree git diff as UTF-8 and met a modified tracked PDF; .gitattributes now marks PDFs "
            "binary and the segment was rerun."),
          P("The single year first", H2),
          table([["2005", "std 10 / 20 / 30 / 50 hPa [m/s]", "mean u 20 / 30 hPa", "RMS vs ERA5, 10-70 hPa", "RMS vs ERA5, 1-7 hPa"],
                 ["window top 4 hPa (p8_qbo_2005)", "15.5 / 8.2 / 8.8 / 7.8", "-23.0 / -18.7", "4.2", "17.5"],
                 ["window top 1 hPa (p8b_2005)", "15.8 / 8.2 / 8.8 / 7.8", "-23.1 / -18.7", "4.2", "10.6"],
                 ["ERA5 (monthly, CDS)", "19.7 / 9.7 / 10.5 / 10.3", "-27.3 / -22.0", "-", "-"]],
                [4.6 * cm, 4.0 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm], hl=[2]),
          Spacer(1, 4),
          P("Single year, so the standard deviation is the plain one, not deseasonalised. RMS change in the time-mean zonal-mean wind, 1 hPa minus "
            "4 hPa version: 2.7 m/s inside the window, 0.5 outside it in the stratosphere, 0.0 in the troposphere.", CAP),
          fig("1hpa_top/1yr/qbo_time_height_before_after.png",
              "Figure 7. 2005 with the window top at 4 hPa (top), at 1 hPa (middle), and ERA5 (bottom). Inside the QBO layer the two runs are the "
              "same (RMS 4.2 m/s in both). Above 5 hPa the 1 hPa version follows ERA5: the error over 1 to 7 hPa falls from 17.5 to 10.6 m/s, "
              "the westerly onset of late 2005 at 5 to 10 hPa is stronger (+10 m/s where the 4 hPa run had +5), and the April semiannual "
              "westerlies at 1 to 2 hPa appear, at a fifth of ERA5's amplitude. The remaining upper-level error is what a 10-day relaxation "
              "leaves of a semiannual signal that the model's own dynamics pull against.", maxh=12 * cm),
          fig("1hpa_top/1yr/qbo_profiles.png",
              "Figure 8. 2005 profiles. The time-mean wind at 1 to 3 hPa moves from -16 m/s to -10 (ERA5 -6); the variability above 5 hPa "
              "doubles; the change (right) is a single patch centred at 2 to 3 hPa, +10 m/s, and nothing elsewhere.", maxh=7 * cm)]
    s += RESULTS_1HPA

    # ------------------------------------------------------------------ 7
    s += [PageBreak(), P("7. A shorter relaxation time: the tau sweep, 10 to 1 days", H1),
          P("Raising the window top left the QBO layer exactly as it was, so the 80 percent amplitude is the relaxation, not the "
            "geometry. Two springs act on the tropical zonal-mean wind: the nudging, pulling toward ERA5 with time constant tau, and the "
            "model's own dynamics, pulling toward the model's own easterly state (tropical upwelling lifting slow-spinning air, and the "
            "15-day Polvani-Kushner temperature relaxation eroding the warm and cold layers a westerly jet needs). The wind settles at the "
            "weighted mean, so the swings shrink by the factor tau_model / (tau + tau_model). Eighty percent at tau 10 days implies a model "
            "restoring time of about 40 days and predicts 89 percent at 5 days, 95 at 2 days, 99 at 6 hours. The monthly target is kept: "
            "the QBO descends about 1 km a month, so a monthly target interpolated between month centres resolves its transitions to within "
            "a week, and a daily one would only add sub-monthly wind changes that are not QBO. One key: tau_days 5. Runs p8c_2005 to "
            "p8c_2009 (aggregate p8c_5yr) on GPU 2 while Phase 9 occupied GPU 0; before-state p8b_5yr (tau 10 days, window top 1 hPa)."),
          table([["2005-2009", "deseasonalised std 10 / 20 / 30 / 50 hPa [m/s]", "RMS vs ERA5, 10-70 hPa", "RMS vs ERA5, 1-7 hPa", "SAO amplitude 1 / 2 / 3 hPa"],
                 ["tau 10 d (p8b_5yr)", "13.7 / 14.1 / 12.4 / 7.8", "4.0", "12.5", "9.5 / 15.8 / 13.8"],
                 ["tau 5 d (p8c_5yr)", "14.6 / 15.1 / 13.2 / 8.5", "3.1", "10.9", "12.2 / 17.3 / 13.9"],
                 ["ERA5 (monthly, CDS)", "17.5 / 17.5 / 15.2 / 10.7", "-", "-", "30.7 / 20.7 / 15.6"]],
                [3.6 * cm, 4.4 * cm, 2.9 * cm, 2.9 * cm, 3.2 * cm], hl=[2]),
          Spacer(1, 4),
          P("Amplitude at 20 hPa as a fraction of ERA5: 81 to 86 percent (prediction 89). Change in the time-mean zonal-mean wind, tau 5 minus "
            "tau 10: 0.7 m/s inside the window, 0.2 outside it in the stratosphere, 0.0 in the troposphere.", CAP),
          table([["check", "tau 10 d", "tau 5 d", "reference"],
                 ["stratospheric climatology vs ERA5, 100-1 hPa, annual", "T 6.3 K, u 4.9 m/s", "T 6.2 K, u 4.8 m/s", "Phase 6: 6.4 K, 5.6 m/s"],
                 ["polar vortex, DJF u(60N, 10 hPa) / JJA u(60S, 10 hPa)", "31 / 64 m/s", "30 / 64 m/s", "ERA5 28 / 72"],
                 ["SSW-like reversals", "2008-03-26, 2009-01-31, 2009-12-07", "2006-02-15, 2008-03-21, 2009-01-31, 2009-12-07", "ERA5 majors 2006-01/02, 2007-02, 2008-02, 2009-01"],
                 ["Brewer-Dobson upward mass flux at 70 hPa, DJF / JJA / annual", "9.4 / 6.6 / 7.7", "9.4 / 6.8 / 7.9", "WACCM6 8.6 / 5.4 / 6.1 (x 10^9 kg/s)"],
                 ["age of air at 20 km, tropics / 50-70 deg / contrast", "2.16 / 3.81 / 1.64 yr", "2.15 / 3.80 / 1.65 yr", "CLaMS 1.33 / 4.12 / 2.79"],
                 ["tracer conservation: unity max deviation, sai vs analytic, polar top-level sai", "2.7e-4, -0.8 percent, 7.6 percent", "2.8e-4, -0.8 percent, 7.3 percent", "Phase 3 levels"],
                 ["throughput, stepping", "3890-3930 days per hour, 8 ms per step", "3910-3940 days per hour, 8 ms per step", "Phase 6: 4445"]],
                [5.2 * cm, 3.7 * cm, 3.7 * cm, 4.4 * cm]),
          Spacer(1, 6),
          fig("tau5/5yr/qbo_time_height_before_after.png",
              "Figure 15. Equatorial wind 2005 to 2009 at tau 10 days (top), tau 5 days (middle) and ERA5 (bottom). The westerly phases at 5 to "
              "20 hPa are broader and about 5 m/s stronger and the semiannual westerlies at 1 to 3 hPa more distinct; the picture is otherwise "
              "the same.", maxh=12 * cm),
          fig("tau5/5yr/qbo_profiles.png",
              "Figure 16. Left: the time-mean equatorial wind is unchanged. Middle: the QBO amplitude rises at every level by 6 to 9 percent. "
              "Right: the change in the time-mean zonal-mean wind is below 2 m/s everywhere.", maxh=7 * cm),
          fig("tau5/5yr/strat/vortex_series.png",
              "Figure 17. Polar-vortex wind at 10 hPa, tau 10 (blue) and tau 5 (orange) days. The one visible difference is a reversal in "
              "February 2006, a few days after ERA5's warming, which the tau 10 day chain did not produce; a single event far outside the "
              "window, read as internal variability.", maxh=8 * cm),
          fig("tau5/5yr/p8c_5yr_aoa_profiles.png",
              "Figure 18. Age of air at tau 5 days (blue) against tau 10 days (orange dashed): identical to a hundredth of a year.", maxh=7 * cm),
          P("Halving tau closed about a quarter of the remaining amplitude gap at every level, as the two-spring estimate predicts, and "
            "nothing else in the model moved. The sweep was then completed with 2 days (runs p8d_*) and 1 day (p8e_*), same protocol."),
          P("The whole sweep", H2),
          table([["tau", "std 10 / 20 / 30 / 50 hPa [m/s]", "percent of ERA5 at 20 hPa (two-spring prediction)", "RMS vs ERA5, 10-70 hPa", "RMS, 1-7 hPa", "SAO 1 / 2 / 3 hPa", "u RMSE 100-1 hPa"],
                 ["10 d", "13.7 / 14.1 / 12.4 / 7.8", "81 (80)", "4.0", "12.5", "9.5 / 15.8 / 13.8", "4.9 m/s"],
                 ["5 d", "14.6 / 15.1 / 13.2 / 8.5", "86 (89)", "3.1", "10.9", "12.2 / 17.3 / 13.9", "4.8"],
                 ["2 d", "15.4 / 15.8 / 13.9 / 9.0", "90 (95)", "2.5", "8.9", "14.9 / 18.1 / 13.7", "4.6"],
                 ["1 d", "15.7 / 16.1 / 14.2 / 9.3", "92 (98)", "2.3", "7.7", "17.2 / 18.2 / 13.7", "4.4"],
                 ["ERA5", "17.5 / 17.5 / 15.2 / 10.7", "100", "-", "-", "30.7 / 20.7 / 15.6", "-"]],
                [1.3 * cm, 3.6 * cm, 3.1 * cm, 2.4 * cm, 1.9 * cm, 2.9 * cm, 1.8 * cm], hl=[4]),
          Spacer(1, 4),
          P("Unchanged across the sweep: T RMSE 100-1 hPa 6.3 to 6.2 K; jets 31 / 64 to 30 / 64 m/s; Brewer-Dobson 70 hPa 7.7 to 8.2 x 10^9 kg/s; age of air "
            "at 20 km 2.16 to 2.13 yr in the tropics, contrast 1.64 to 1.65; tracer conservation and throughput identical. Time-mean wind change "
            "against tau 10 days: 0.7 / 1.4 / 1.8 m/s inside the window, at most 0.5 outside it, 0.0 in the troposphere. Vortex reversals: a "
            "February 2006 reversal (ERA5 warming 11 February) appears at 5, 2 and 1 days and never at 10; the 2009 date wanders and the March 2008 "
            "reversal is missing at 1 day. Plausibly a Holton-Tan-type re-timing of wave events, but three chains cannot separate it from "
            "internal variability.", CAP),
          fig("tau1/5yr/qbo_time_height_before_after.png",
              "Figure 19. Equatorial wind 2005 to 2009 at tau 10 days (top), tau 1 day (middle) and ERA5 (bottom). At 1 day the westerly phases "
              "have ERA5's width and strength to within a few m/s, the onsets at 5 to 10 hPa are in place, and the semiannual oscillation at 1 to "
              "3 hPa is distinct.", maxh=12 * cm),
          fig("tau1/5yr/qbo_profiles.png",
              "Figure 20. Left: the time-mean equatorial wind at tau 1 day (orange) lies on ERA5 (green) from 40 hPa to 1.5 hPa. Middle: the QBO "
              "amplitude at 90 to 93 percent of ERA5 at every level. Right: the change against tau 10 days stays inside the window.", maxh=7 * cm),
          fig("tau1/5yr/strat/vortex_series.png",
              "Figure 21. Polar-vortex wind at 10 hPa at tau 10 (blue) and 1 day (orange). The February 2006 reversal, and otherwise two curves "
              "on top of each other.", maxh=8 * cm),
          P("Reading the sweep", H2),
          P("The amplitude follows the two-spring law down to 2 days and then flattens: 80, 86, 90, 92 percent against the predicted 80, 89, 95, "
            "98. From 2 to 1 day the gain is 2 percent, so the last 8 percent is not the relaxation any more but the target itself. Above the QBO "
            "layer the gain does not flatten (12.5 to 7.7 m/s), because the semiannual signal is fast enough for tau to still matter. Nothing "
            "outside the window moves at any tau, and the global stratospheric wind error improves monotonically, all of it in the tropics."),
          P("Decision (KEY_DECISIONS 27): tau 1 day is the default. It is the value at which the relaxation stops being the limit; the model "
            "still sets its own temperature, since the thermal-wind adjustment takes about a day and the wind therefore does not run ahead of "
            "it as it would at 6 hours; and it sits in the range specified-dynamics models use (SD-WACCM: 50 hours). The daily-versus-monthly "
            "target question is settled the other way: the term already interpolates the monthly means to every 12-minute step, a daily target "
            "would impose sub-monthly changes that are not QBO, and what the target needs is the right shape, which is section 8.")]
    s += [PageBreak(), P("8. The target's shape: mean-preserving interpolation", H1),
          P("The target is ERA5's monthly-mean zonal wind, and the amplitude is scored against those same monthly means. The term "
            "interpolates linearly between month-centre values. A straight line between the centres of two neighbouring months cuts the "
            "corner of every peak, so the interpolant's own monthly means are smaller than the values it was drawn through: for a sinusoid "
            "of period P months by the factor (6 + 2 cos(2 pi / P)) / 8, which is 0.6 percent for the QBO's 28-month period and 12.5 percent "
            "for the 6-month semiannual oscillation. The AMIP boundary-condition method (Taylor et al. 2000) fixes this by solving for "
            "month-centre node values whose piecewise-linear interpolant reproduces the monthly means exactly; with equal months that is the "
            "tridiagonal system (v[k-1] + 6 v[k] + v[k+1]) / 8 = m[k], ends clamped. Implemented as qbo.mean_preserving (default on, "
            "mean_preserving_nodes in qbo_nudging.py, unit-tested to 1e-3 m/s); runs p8f_2005 to p8f_2009 at tau 1 day against the tau 1 day "
            "chain with plain interpolation, p8e_5yr. The cadence stays monthly; only the shape changes.")]
    s += INTERP_RESULTS()
    s += [PageBreak(), P("9. Reading and what comes next", H1), *READING]

    s += [P("10. Where things are", H2),
          P("Runs under runs/p8_* (window top 4 hPa), runs/p8b_* (1 hPa), runs/p8c_*, p8d_*, p8e_* (1 hPa, tau 5 / 2 / 1 days) and runs/p8f_* (tau 1 day, "
            "mean-preserving target); record docs/outputs/08_qbo/output.md with the figures beside it (5yr/, 1yr/, 1hpa_top/, tau5/, tau2/, tau1/, interp/); the term jcm_strat/qbo_nudging.py with tests/test_qbo_nudging.py; configuration "
            "jcm_strat/config/physics/strat_pk_qbo.yaml and experiment p8_qbo; the comparison script scripts/qbo_compare.py; the ERA5 "
            "target fetch scripts/fetch_era5_strat_ref.py (cache/era5_ref/). Decisions 23, 24 and 26 in KEY_DECISIONS.md; open items: "
            "issue 44 (cheaper zonal mean), issue 6 (close on merge).")]

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="jcm-strat Phase 8: QBO nudging", author="Susanne Baur")

    def footer(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"jcm-strat Phase 8  |  page {d.page}"); c.restoreState()
    doc.build(s, onFirstPage=footer, onLaterPages=footer); print("wrote", out_pdf)


def _md_table_rows(path):
    """Rows of the first markdown table in a metrics file, as lists of cell strings (header first)."""
    rows = []
    for line in open(path):
        if line.startswith("|") and not line.startswith("|---"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def INTERP_RESULTS():
    """Section 8 results, read from the mean-preserving run's metrics if they exist (the chain runs after this
    file was written), otherwise a pending note. Regenerate the PDF once docs/outputs/08_qbo/interp/5yr/ is there."""
    base = os.path.join(D, "interp", "5yr")
    qm = os.path.join(base, "qbo_metrics.md")
    if not os.path.exists(qm):
        return [P("Results pending: the p8f chain and its analysis run unattended after this build; rerun "
                  "scripts/make_phase8_report.py when docs/outputs/08_qbo/interp/5yr/ exists.", CAP)]
    rows = _md_table_rows(qm)
    out = [P("Results, 2005 to 2009", H2),
           table([["2005-2009"] + rows[0][1:]] + [[r[0]] + r[1:] for r in rows[1:]],
                 [4.0 * cm, 4.2 * cm, 2.6 * cm, 3.4 * cm, 2.8 * cm], hl=[2])]
    sm = os.path.join(base, "strat", "strat_metrics.md")
    if os.path.exists(sm):
        srows = [r for r in _md_table_rows(sm) if len(r) > 2 and r[2] == "annual" and r[1] == "ERA5"]
        if srows:
            out.append(P("Stratospheric climatology vs ERA5, 100-1 hPa, annual: " + "; ".join(
                f"{r[0]}: T RMSE {r[3]} K, u RMSE {r[4]} m/s, jets {r[5]} / {r[6]}" for r in srows) + ".", CAP))
    out += [fig("interp/5yr/qbo_time_height_before_after.png",
                "Figure 22. Equatorial wind 2005 to 2009: tau 1 day with plain interpolation (top), with mean-preserving nodes (middle), ERA5 (bottom).",
                maxh=12 * cm),
            fig("interp/5yr/qbo_profiles.png",
                "Figure 23. Time-mean equatorial wind, QBO amplitude and the change in the time-mean zonal-mean wind, mean-preserving minus plain.",
                maxh=7 * cm),
            fig("interp/5yr/strat/vortex_series.png", "Figure 24. Polar-vortex wind at 10 hPa, both versions.", maxh=8 * cm),
            fig("interp/5yr/p8f_5yr_aoa_profiles.png", "Figure 25. Age of air, mean-preserving (blue) against plain interpolation (orange dashed).", maxh=7 * cm)]
    return out


# Filled in from the 1 hPa runs' metric tables (docs/outputs/08_qbo/1hpa_top/).
RESULTS_1HPA = [
    P("The five-year chain", H2),
    table([["2005-2009", "deseasonalised std 10 / 20 / 30 / 50 hPa [m/s]", "mean u 20 / 30 hPa", "RMS vs ERA5, 10-70 hPa", "RMS vs ERA5, 1-7 hPa", "SAO amplitude 1 / 2 / 3 hPa"],
           ["window top 4 hPa (p8_5yr)", "13.6 / 14.1 / 12.4 / 7.8", "-11.9 / -7.5", "3.9", "22.7", "4.7 / 5.6 / 5.5"],
           ["window top 1 hPa (p8b_5yr)", "13.7 / 14.1 / 12.4 / 7.8", "-11.9 / -7.5", "4.0", "12.5", "9.5 / 15.8 / 13.8"],
           ["ERA5 (monthly, CDS)", "17.5 / 17.5 / 15.2 / 10.7", "-12.9 / -8.0", "-", "-", "30.7 / 20.7 / 15.6"]],
          [3.6 * cm, 3.6 * cm, 2.4 * cm, 2.3 * cm, 2.3 * cm, 2.8 * cm], hl=[2]),
    Spacer(1, 4),
    P("Time-mean equatorial wind at 3 hPa: -24 m/s with the 4 hPa top, -9 with the 1 hPa top, ERA5 -6. RMS change in the time-mean zonal-mean "
      "wind, 1 hPa minus 4 hPa version: 5.0 m/s inside the window (one patch at 2 to 3 hPa), 0.5 outside it in the stratosphere, 0.0 in the "
      "troposphere. SAO: amplitude of the semiannual harmonic of the equatorial wind (strat_circulation.py).", CAP),
    table([["check", "window top 4 hPa", "window top 1 hPa", "reference"],
           ["stratospheric climatology vs ERA5, 100-1 hPa, annual", "T 6.3 K, u 6.4 m/s", "T 6.3 K, <b>u 4.9 m/s</b>", "Phase 6: 6.4 K, 5.6 m/s"],
           ["polar vortex, DJF u(60N, 10 hPa) / JJA u(60S, 10 hPa)", "32 / 65 m/s", "31 / 64 m/s", "ERA5 28 / 72"],
           ["SSW-like reversals", "2008-03-21, 2009-01-31, 2009-12-07", "2008-03-26, 2009-01-31, 2009-12-07", "ERA5 majors 2006-01, 2007-02, 2008-02, 2009-01"],
           ["Brewer-Dobson upward mass flux at 70 hPa, DJF / JJA / annual", "9.2 / 6.7 / 7.7", "9.4 / 6.6 / 7.7", "WACCM6 8.6 / 5.4 / 6.1 (x 10^9 kg/s)"],
           ["age of air at 20 km, tropics / 50-70 deg / contrast", "2.16 / 3.79 / 1.63 yr", "2.16 / 3.81 / 1.64 yr", "CLaMS 1.33 / 4.12 / 2.79"],
           ["age of air at 30 km, tropics", "3.61 yr", "3.68 yr", "CLaMS 3.68"],
           ["tracer conservation: unity max deviation, sai vs analytic, polar top-level sai", "2.6e-4, -0.8 percent, 8 percent", "2.7e-4, -0.8 percent, 7.6 percent", "Phase 3 levels"],
           ["throughput, stepping / end-to-end", "3820-3960 / 2120-2190 days per hour", "3890-3930 / 1870-1900 days per hour", "Phase 6: 4445 / 2090"]],
          [5.2 * cm, 3.7 * cm, 3.7 * cm, 4.4 * cm]),
    Spacer(1, 4),
    P("End-to-end throughput of the 1 hPa chain is lower only because of compile and output time in a busier session; the stepping rate, "
      "8 ms per step, is the same.", CAP),
    fig("1hpa_top/5yr/qbo_time_height_before_after.png",
        "Figure 9. Equatorial wind 2005 to 2009: window top 4 hPa (top), 1 hPa (middle), ERA5 (bottom); the dotted lines are now 90 and 1 hPa. "
        "Below 5 hPa the two model panels are the same picture. Above it the 1 hPa version follows ERA5: the easterly reservoir at 1 to 4 hPa "
        "is gone and the alternating semiannual westerlies and easterlies at 1 to 3 hPa appear, at roughly three quarters of ERA5's amplitude "
        "at 2 to 3 hPa and a third at 1 hPa, where the taper reaches zero.", maxh=12 * cm),
    fig("1hpa_top/5yr/qbo_profiles.png",
        "Figure 10. Left: time-mean equatorial wind; the 1 hPa version (orange) sits on ERA5 (green) from 40 hPa to 2 hPa, the 4 hPa version "
        "(blue dashed) departs above 5 hPa. Middle: QBO amplitude, identical below 5 hPa, doubled above. Right: the change in time-mean "
        "zonal-mean wind is one patch at 2 to 3 hPa over the equator, +15 m/s, and nothing anywhere else.", maxh=7 * cm),
    fig("1hpa_top/5yr/circulation/qbo_time_height.png",
        "Figure 11. The 1 hPa chain against ERA5 and WACCM6. Compare with Figure 6: the semiannual oscillation that was missing is now present; "
        "it is weaker than WACCM's at 1 hPa and comparable at 2 to 3 hPa.", maxh=12 * cm),
    fig("1hpa_top/5yr/strat/strat_climatology_panel.png",
        "Figure 12. Zonal-mean temperature and wind, DJF and JJA, 300 to 1 hPa: 4 hPa version, 1 hPa version, ERA5, WACCM6. The only visible "
        "difference between the two model rows is the equatorial wind above 5 hPa in DJF, where the 1 hPa version has ERA5's weak "
        "westerlies instead of easterlies. Everything poleward of 25 degrees is identical.", maxh=15 * cm),
    fig("1hpa_top/5yr/strat/vortex_series.png",
        "Figure 13. Polar-vortex wind at 10 hPa, 60N and 60S, both versions against ERA5 and WACCM6. The two curves lie on top of each other.", maxh=8 * cm),
    fig("1hpa_top/5yr/p8b_5yr_aoa_profiles.png",
        "Figure 14. Age of air, 1 hPa version (blue) against the 4 hPa version (orange dashed), CLaMS, WACCM6 and the PARADIS offline clock. "
        "Indistinguishable: the tropical age at 20 km is 2.16 years in both.", maxh=7 * cm),
]
READING = bullets([
    "<b>The model now has ERA5's QBO, in phase, at 80 percent amplitude, and with the window top at 1 hPa also ERA5's semiannual oscillation "
    "above it.</b> The equatorial wind error against ERA5 fell from 16 m/s (Phase 6) to 4 in the QBO layer and, with the 1 hPa top, from 23 to "
    "12 above it. The global stratospheric wind error, 5.6 m/s in Phase 6, is 4.9 with the 1 hPa top: the nudging no longer costs anything in "
    "the climatology.",
    "<b>The rest of the stratosphere is untouched.</b> Polar-night jets, sudden warmings, polar-cap temperatures, the Brewer-Dobson flux and the "
    "tracer budgets are the Phase 6 ones within noise, in both versions. The nudging does what it says: the tropical mean flow and nothing else.",
    "<b>Age of air moves a little, in the right direction, and not much.</b> Tropical age at 20 km 2.29 to 2.16 years; contrast to the "
    "extratropics 1.56 to 1.63 (CLaMS 2.79). A five-year mean averages over two QBO cycles; the QBO's value for aerosol is in phase-dependent "
    "statements (residence time in the easterly against the westerly phase, subtropical leakage), which the model can now make. The remaining "
    "0.9 year tropical excess is the Phase 4 diagnosis unchanged (issue 25).",
    "<b>The window top was not what limits the westerly phases; tau was, and then the target's shape.</b> Raising the top to 1 hPa left "
    "the QBO layer exactly as it was. The tau sweep 10, 5, 2, 1 days gave 80, 86, 90, 92 percent of ERA5's amplitude with nothing else "
    "moving, following the two-spring estimate (model restoring time about 40 days) down to 2 days and flattening below, where the "
    "linear interpolation cutting the peaks of the monthly target becomes the limit. Above the QBO layer the gain continued to 1 day and "
    "the semiannual oscillation at 2 hPa reached ERA5. No artefact appeared at the window edges from the stiff wind spring against the "
    "15-day Polvani-Kushner relaxation; the age of air moved by 0.03 years over the whole sweep.",
    "<b>Cadence versus shape.</b> The term already interpolates the monthly target to every 12-minute step, so a daily target would not "
    "change the cadence the model sees; it would only add sub-monthly zonal-mean wind changes that are not QBO. What the target needed "
    "was the right shape, mean-preserving nodes, which is a property of how the monthly means are interpolated, not of their cadence.",
    "<b>Decisions.</b> Window top 1 hPa (KEY_DECISIONS 26) and tau 1 day with the mean-preserving target (KEY_DECISIONS 27) are the "
    "defaults. The 4 hPa chain and the tau 10, 5, 2 day chains stay on disk as before-states. Open: whether the February 2006 vortex "
    "reversal that appears at every short tau is a Holton-Tan-type response (DEFERRED.md).",
    "<b>Cost.</b> The zonal-mean reduction adds about 1 ms to a 7 ms step, minus 13 percent stepping throughput, the same for both window tops; "
    "a cheaper reduction on the dycore grid is issue 44. A five-year chain takes 70 to 80 minutes on one GPU.",
])


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "docs", "outputs", "jcm-strat_phase8_qbo.pdf"))
