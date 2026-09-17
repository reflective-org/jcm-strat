#!/usr/bin/env python3
"""Build the cross-phase summary PDF: what jcm-strat has tried so far, what was found, what is open.

    python scripts/make_summary_report.py [docs/outputs/jcm-strat_phases_0-12_summary.pdf] \
        [--figure-roots <repo checkout> ...]

The narrative lives here, plain language first. Figures are the tracked PNGs under docs/outputs/;
each is looked up in every root given with --figure-roots (default: this checkout), so a phase whose
branch is not merged yet can be included from its worktree. A missing figure is stated in the PDF,
never silently dropped. Numbers are copied from the per-phase output.md records; regenerate the PDF
whenever those change.
"""
import argparse
import datetime as dt
import os

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = A4[0] - 4 * cm

# DejaVu (bundled with matplotlib) so that the record's symbols (arrows, degrees, minus) render.
_FONTS = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(_FONTS, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(_FONTS, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", os.path.join(_FONTS, "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-BoldOblique", os.path.join(_FONTS, "DejaVuSans-BoldOblique.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="DejaVu-Bold", fontSize=14.5, spaceBefore=10, spaceAfter=5)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="DejaVu-Bold", fontSize=11.5, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="DejaVu", fontSize=9.2, leading=12.6, spaceAfter=5)
BL = ParagraphStyle("BL", parent=B, leftIndent=12, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.2, leading=10.5, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=10)
SM = ParagraphStyle("SM", parent=B, fontSize=7.4, leading=9.3, spaceAfter=0)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontName="DejaVu-Bold", fontSize=18, spaceAfter=4)
SUB = ParagraphStyle("SUB", parent=B, fontSize=10, textColor=colors.HexColor("#444444"), spaceAfter=12)

FIGURE_ROOTS = [REPO]


def P(t, s=B):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(f"• {t}", BL) for t in items]


def find_fig(rel):
    for root in FIGURE_ROOTS:
        path = os.path.join(root, "docs", "outputs", rel)
        if os.path.exists(path):
            return path
    return None


def fig(rel, caption, width=W, maxh=13.5 * cm):
    path = find_fig(rel)
    if path is None:
        return P(f"[figure docs/outputs/{rel} is not in any of the checkouts this PDF was built from]", CAP)
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


def build(out):
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="jcm-strat: Phases 0-12, what was tried and what was found", author="jcm-strat")
    s = []

    # ------------------------------------------------------------------ title
    s.append(P("jcm-strat: Phases 0–12", TITLE))
    s.append(P("What has been tried, what was found, and what is open in the stratosphere-only JCM configuration for fast tracer transport "
               f"(Approach A). Repository <b>reflective-org/jcm-strat</b>, branch <b>dev</b>. Built {dt.date.today().isoformat()} from the per-phase records in "
               "<b>docs/outputs/&lt;NN&gt;/output.md</b>, KEY_DECISIONS.md and PROGRESS.md; Phases 11 and 12 from their branches "
               "(phase11-lid-tracers, phase12-circulation), which were not yet merged when this was written.", SUB))

    s.append(P("The one-paragraph version", H1))
    s.append(P("The question Approach A was set up to answer, <i>how fast can the simplest physics solve of stratospheric tracer transport be</i>, "
               "is answered: with the tropospheric physics stripped out and the troposphere nudged to ERA5, JCM on the semi-Lagrangian Dinosaur dycore "
               "steps one simulated year at T63 in 4–5 minutes on one H100 (Phase 4: 10.4 min end-to-end with 5-day means, 30 years in about 5 GPU-hours; "
               "Phase 10: 26–30 min end-to-end when every 6-hourly instantaneous field is written, 30 years in about 15 hours and 2.3 TB). Along the way the "
               "model was given a defensible stratosphere without radiation (a seasonal Polvani-Kushner temperature target plus QBO nudging to ERA5, "
               "Phases 6 and 8), its time step and grid were bounded (Phases 7 and 9: 12 minutes, T63 with 63 levels), and a production tracer set was run "
               "for 1990–2019 (Phase 10). The unsolved problem is transport in the upper stratosphere: the dry model has no gravity-wave drag above its "
               "sponge, so the mesosphere is never ventilated, the age-of-air clock grows without bound (23 years after the 30-year run) and the "
               "stratosphere below it ends up 3–5 times too old with N2O and CFC-11 isopleths about 6 km too low. Phase 9 showed this is not a "
               "resolution problem. Phase 11 caps the tracers above 1 hPa with WACCM's mesospheric age and state, which bounds the clock but leaves "
               "the 20–1 hPa layer filled from the lid; its run A is being extended to 2009. Phase 12, running now, tests whether the QBO nudging or "
               "the thinned troposphere is what holds the deep branch back."))

    # ------------------------------------------------------------------ the model
    s.append(P("The model as it stands", H1))
    s.append(P("Everything is a Hydra configuration overlay on the installed <b>jcm</b> package plus a few small physics terms; JCM's source is never edited. "
               "The current production configuration (Phase 11, <b>p11a_prod</b>) is:"))
    s.extend(bullets([
        "<b>Dycore</b>: JCM on Dinosaur's semi-Lagrangian branch, T63 (192×96 columns), <b>strat63</b> vertical table (8 mesospheric + the 47 L95 levels "
        "between 1.08 and 159 hPa intact + 8 tropospheric), lid 0.01 hPa, dt 12 min, Rayleigh sponge in the top four levels above 0.2 hPa.",
        "<b>Troposphere</b>: u, v, T relaxed to ERA5 (6-hourly, WeatherBench2 store) below 150 hPa with tau 6 h; no convection, clouds, boundary layer "
        "or radiation. The nudging cutoff is a hard 150 hPa mask (issue #1: should become a dynamical tropopause).",
        "<b>Stratosphere</b>: temperature relaxed with tau 15 d towards a seasonal Polvani-Kushner (2002) equilibrium (gamma 4 K/km, equinox-to-equinox "
        "cooling season, vortex cooling faded out above 3 hPa); the tropical zonal-mean zonal wind relaxed with tau 1 d towards ERA5 monthly means "
        "(mean-preserving interpolation) between 90 and 1 hPa, |lat| &lt; 25°.",
        "<b>Tracers</b> (24, semi-Lagrangian, quasi-monotone limiter): three age-of-air clocks (reset below 700 hPa, below 150 hPa, at the surface), "
        "the box source <b>sai</b>, five once-injected pulses and four continuous sources with a sharp-edged twin each, N2O- and CFC-11-like species "
        "held at 1 below 700 hPa with WACCM loss frequencies. Clocks and the value-imposing species are exempt from JCM's global mass fixer. "
        "Above 1 hPa the clocks and species are relaxed (tau 1 d) to WACCM6's mesospheric age and state (the Phase 11 lid).",
        "<b>Output</b>: instantaneous every 6 h, with omega; Gregorian calendar; one-calendar-year segments chained through checkpoints because JCM keeps "
        "the whole ERA5 target of a segment on the GPU (~21 GB at strat63).",
    ]))

    # ------------------------------------------------------------------ phase table
    s.append(P("The phases at a glance", H1))
    rows = [["Phase", "What was run", "What it showed", "Decision"],
            ["0", "Environment, tooling, stock JCM baseline (T63L95, full ECHAM physics, 10 days)",
             "52 simulated days per hour; 582 ms per step", "Pin JCM 849893b and Dinosaur bd99e39b as submodules; everything under the repo"],
            ["1", "Dry Held-Suarez on T63L95, one year", "5,800 days/hr stepping (112× full physics); stable",
             "Held-Suarez holds the stratosphere for now; gravity-wave drag dropped (issue #20)"],
            ["2", "ERA5 nudging of u, v, T below 150 hPa, tau 6 h; 90 d and one year", "Stable; −6 % throughput", "Winds + temperature nudging; hard 150 hPa cutoff"],
            ["3", "Passive tracers: clock, unity, sai injection, e90; one year", "Clock slowed to 0.44 day/day under the global mass fixer",
             "Clock excluded from the fixer (KEY_DECISIONS #19); tracer tendencies verified analytically"],
            ["4", "Five chained years 2005–2009", "10.4 min/yr end-to-end; mass closed to 0.02 %; age of air pattern right, tropics 1.5 yr too old, no polar-night jet",
             "The Phase-1 number is in; fidelity gap attributed to the Held-Suarez stratosphere, not tuned away"],
            ["4 (follow-ups)", "PARADIS rollout 1995_12_06_5y1m as a circulation reference; two offline clocks carried by its winds",
             "PARADIS-driven stratosphere too young everywhere (the opposite failure)", "Shown as bounds only; carry surface and entry-age clocks from now on (#22)"],
            ["6", "Seasonal Polvani-Kushner stratosphere: 8 A/B years, 5-yr chain, full-ECHAM reference year",
             "T RMSE 6.4 K, u 5.6 m/s vs ERA5 (Held-Suarez: 35 K); jets right; 2 of 3 SSW winters; full ECHAM under the same nudging: 4.3 K but no Arctic vortex",
             "tau 15 d, wide season, taper above 3 hPa = strat_pk defaults"],
            ["7", "Time step 12–120 min, 1–2 departure iterations", "30 min stable at 2.35× (Antarctic jet −18 %); 45 min degrades winds; ≥ 60 min blows up or drifts",
             "12 min kept; 30 min as a fast mode for sensitivity work (issue #51)"],
            ["8", "QBO nudging to ERA5: window top 4 → 1 hPa; tau 10/5/2/1 d; mean-preserving target",
             "Equatorial u error 16 → 2.2 m/s; amplitude 80 → 93 % of ERA5; SAO appears; nothing outside the window moves; age of air −0.1 yr only",
             "Window to 1 hPa, tau 1 d, mean-preserving (KEY_DECISIONS #26, #32)"],
            ["9", "T63/T85/T119 × L95/strat63/strat47, nine 5-yr chains", "Age of air vs CLaMS identical at every grid (RMSE 0.73–0.75 yr); T119 improves climatology at 3.5× cost",
             "T63 strat63 adopted; strat47 as throughput option (KEY_DECISIONS #31)"],
            ["10", "Production tracers, 6-hourly output, Gregorian calendar; 2005–2009 review then 1990–2019",
             "30 yr in ~15 h; pulses gone in 2–3 yr, sources equilibrate &lt; 1 yr; n2o grew to 1.07 under the fixer; mesosphere never ventilated, clocks unbounded",
             "n2o/cfc11 out of the fixer; pulses injected once; a fix for the top needed → Phase 11"],
            ["11", "Tracer lid above 1 hPa (WACCM age/state), unit amplitudes, box twins, no surface sink; A (no sink) vs B (lid sink), 1990–1994",
             "Clocks bounded (max 5.4 yr) but 20–1 hPa fills from the lid; 55 hPa tropics 2.7 yr vs CLaMS 1.3; N2O/CFC-11 depletion unchanged",
             "A chosen (mass conserved exactly); extension 1995–2009 running on GPU 0"],
            ["12", "Control vs QBO nudging off vs strat81 (full L95 troposphere), 1990–1994; w* and age (surface, 500 hPa clocks)",
             "running", "pending"]]
    s.append(table(rows, [1.4 * cm, 5.4 * cm, 6.0 * cm, 4.2 * cm], hl=[12, 13]))
    s.append(P("Phase 5 of the plan was a documentation hand-off with no run of its own. Every phase has a record under docs/outputs and a PR into dev; "
               "Phases 6–9 have their own PDFs beside this one.", CAP))

    # ------------------------------------------------------------------ throughput
    s.append(PageBreak())
    s.append(P("1. Speed: the Phase-1 number and what each addition cost", H1))
    s.append(P("Simulated days per wall-clock hour on one H100, stepping (kernel only) and end-to-end (with JIT compile and output writing). "
               "One simulated year is 365 days; six simulated hours is what one emulator step covers."))
    rows = [["Configuration", "Grid, dt", "days/hr stepping / e2e", "one year e2e", "note"],
            ["Phase 0: stock JCM, full ECHAM physics", "T63L95, 12 min", "52 / 47", "7.8 h", "reference"],
            ["Phase 1: dry Held-Suarez", "T63L95, 12", "5,787 / 2,368", "9.2 min", "112× stepping"],
            ["Phase 2: + ERA5 nudging below 150 hPa", "T63L95, 12", "5,454 / 2,326", "9.4 min", ""],
            ["Phase 3: + four passive tracers", "T63L95, 12", "4,458 / 2,082", "10.5 min", ""],
            ["Phase 4: five chained years", "T63L95, 12", "4,315 / 1,768", "10.4 min", "30 yr ≈ 5.2 GPU-h"],
            ["Phase 6: + Polvani-Kushner stratosphere", "T63L95, 12", "4,445 / 2,012", "10.9 min", ""],
            ["Phase 6 reference: full ECHAM + the same nudging", "T63L95, 12", "140 / 131", "2.8 h", "GPU 1, 12-hourly target"],
            ["Phase 7: Phase 6 at dt 30 min", "T63L95, 30", "10,432 / 1,891", "11.6 min", "output-bound already; jet −18 %"],
            ["Phase 8b: + QBO nudging", "T63L95, 12", "3,900 / 1,890", "11.6 min", "−13 % for the zonal-mean reduction"],
            ["Phase 9: same on strat63", "T63 strat63, 12", "5,374 / 1,750", "12.5 min", "recommended grid"],
            ["Phase 9: same on strat47", "T63 strat47, 12", "6,228 / 1,948", "11.2 min", ""],
            ["Phase 9: T85L95 / T119L95", "9 / 6 min", "1,636 / 847 and 557 / 403", "26 / 54 min", "no change in transport"],
            ["Phase 10: production, 6-hourly instantaneous output", "T63 strat63, 12", "4,760 / 860", "26–30 min", "output-bound; 30 yr ≈ 15 h, 2.3 TB"],
            ["Phase 11: + lid, 24 tracers, two chains at once", "T63 strat63, 12", "4,180 / 750", "31 min", "per chain, CPU output path shared"]]
    s.append(table(rows, [5.6 * cm, 2.6 * cm, 3.6 * cm, 2.0 * cm, 3.2 * cm], hl=[5, 13]))
    s.append(Spacer(1, 6))
    s.append(P("Reading. Stripping the physics bought a factor ~90 in stepping and ~40 end-to-end. From Phase 3 on the end-to-end time is dominated by "
               "output conversion and writing and per-segment setup, not by the dycore (issue #19): at 6-hourly instantaneous output (Phase 10) 13 s of "
               "stepping per 10-day chunk waits on ~30 s of netCDF writing, so the production run is output-bound and a longer time step would not help "
               "it. Compression runs afterwards on the CPU (108 → 75 GB per year). The GPU memory limit is the ERA5 nudging target JCM keeps resident "
               "(one year ≈ 21–31 GB), which is why every multi-year run is a chain of one-year segments (issue #26) and why the JAX preallocation "
               "fraction had to be raised to 0.92 when the QBO term was added."))

    # ------------------------------------------------------------------ stratosphere without radiation
    s.append(P("2. A stratosphere without radiation (Phases 6 and 8)", H1))
    s.append(P("<b>The problem.</b> With Held-Suarez in place of radiation the stratosphere is isothermal: no meridional temperature gradient, no "
               "polar-night jet, u ≈ 0 above 100 hPa, no sudden warmings, and the tropical age of air 1.5 yr too old (Phase 4). Radiation "
               "(RRTMGP, issue #2) would fix it at the cost that dominated the full model."))
    s.append(P("<b>What was tried.</b> Phase 6 replaced the Held-Suarez equilibrium above 100 hPa by Polvani and Kushner's (2002) analytic winter-pole "
               "cooling, made seasonal through the calendar, and swept its knobs over 2005: gamma 2 vs 4 K/km, relaxation time 40 / 25 / 15 d, the "
               "season shape, and where the cooling is faded out aloft (none / 10 / 5 / 3 hPa). tau was the dominant knob (RMSE vs ERA5 8.9 → 6.7 K, "
               "jets from ~55 to ~90 % of ERA5); the wide season fixed the autumn onset; PK02's unbounded cooling had to be capped (143 K at 3 hPa "
               "otherwise). The chosen run was then chained over 2005–2009 and compared with a full-ECHAM year under the same nudging."))
    s.append(P("<b>What it showed.</b> Over 2005–2009: T RMSE 100–1 hPa 6.4 K and u RMSE 5.6 m/s against ERA5 (Held-Suarez chain: 35.7 K, 11.9 m/s), "
               "DJF u(60°N, 10 hPa) 32 vs ERA5 28 m/s, JJA u(60°S) 65 vs 72, two of the three observed SSW winters reversed. The full-ECHAM reference "
               "year gets a better temperature (4.3 K) but no Arctic vortex at all (u ≈ 4 m/s all winter) and a worse wind (9.7 m/s), at 30× the cost. "
               "Remaining biases: the winter pole above 10 hPa 20–30 K too warm where the cooling is faded (issue #32), a 1–3 hPa cold bias, and a "
               "tropical tropopause that is too warm because the US-Standard floor has no latitude dependence (issue #31)."))
    s.append(fig("06_stratosphere/strat_climatology_panel.png",
                 "Phase 6: zonal-mean T and u climatology of full ECHAM physics under specified dynamics, Held-Suarez, the chosen Polvani-Kushner run, ERA5 "
                 "and WACCM6 (docs/outputs/06_stratosphere/strat_climatology_panel.png).", maxh=12 * cm))
    s.append(P("<b>The QBO (Phase 8).</b> The dry model cannot grow a QBO (no convective wave source, ~1 km levels): equatorial wind in steady easterlies "
               "with 4 m/s of variability where ERA5 has 17. Following WACCM's specified-dynamics practice, only the <i>zonal mean</i> of the tropical zonal "
               "wind is relaxed towards ERA5 monthly means, so the transporting waves are left alone. Tried in sequence: window top 4 hPa (left a 10–15 m/s "
               "easterly bias at 1–3 hPa and no SAO) → 1 hPa (bias gone, SAO appears, global u RMSE 6.4 → 4.9 m/s); tau 10 → 5 → 2 → 1 d "
               "(QBO amplitude 80 → 86 → 90 → 92 % of ERA5; the model's own easterly tendency restores in ~40 d, so a slow nudge loses the westerly "
               "peaks); and a mean-preserving interpolation of the monthly nodes (93 %; the SAO at 2–3 hPa now equals ERA5's). A daily target was "
               "considered and dropped: the term already interpolates to every step, and a daily target would impose sub-monthly variability that is not "
               "the QBO. Cost: about 1 ms on a 7 ms step. Everything outside the window is unchanged to 0.5 m/s; the five-year-mean age of air moves "
               "0.1 yr younger in the tropics, i.e. the QBO's transport effect is phase-dependent and averages out over two cycles, as expected."))
    s.append(fig("08_qbo/5yr/qbo_time_height_before_after.png",
                 "Phase 8: equatorial zonal-mean zonal wind 2005–2009 without QBO nudging (Phase 6 chain), with the nudging as first implemented (window "
                 "top 4 hPa, tau 10 d) and ERA5 (docs/outputs/08_qbo/5yr/qbo_time_height_before_after.png). The later steps (top 1 hPa, tau 1 d, "
                 "mean-preserving target) are in the Phase 8 addenda and jcm-strat_phase8_qbo.pdf.", maxh=11 * cm))

    # ------------------------------------------------------------------ dt and resolution
    s.append(P("3. Time step and grid (Phases 7 and 9)", H1))
    s.append(P("<b>Time step.</b> The semi-Lagrangian pull request suggested an accuracy knee near 30 min and stability to 2–3 h. Phase 7 swept 12 / 30 / 45 / "
               "60 / 90 / 120 min with one and two departure-point iterations on the Phase 6 configuration. 30 min is stable and within 1 K / 1 m/s of the "
               "12-min climatology but weakens the Antarctic jet by 18 % (66 → 54 m/s); 45 min degrades the winds (u RMSE 6.8 → 13.4 m/s); at 60 min the "
               "model blows up within two months with one iteration and, with two, drifts into a state with 500 m/s easterlies that the limiter keeps "
               "finite. The extra iteration buys robustness, not accuracy, so the departure solve is not the limit; the semi-implicit off-centering "
               "probably is (open). End-to-end the 30-min step gains nothing because output dominates. Decision: 12 min for production, 30 min as a "
               "fast mode for sensitivity work only."))
    s.append(fig("07_timestep/dt_sweep.png", "Phase 7: metrics against the time step, failures as crosses (docs/outputs/07_timestep/dt_sweep.png).", maxh=9.5 * cm))
    s.append(P("<b>Resolution.</b> Before fixing a grid for aerosol work, Phase 9 asked how much of the age-of-air excess against CLaMS is implicit "
               "diffusion of the semi-Lagrangian transport. Nine 2005–2009 chains: T63 / T85 / T119 (the 1° grid; T127 is not constructible in JCM) × "
               "L95 / strat63 / strat47, where the reduced tables are subsets of the L95 interfaces with the 1–159 hPa stratosphere kept intact "
               "(strat63) or halved between 1 and 30 hPa (strat47), the time step scaled with truncation (12 / 9 / 6 min), one change per run. "
               "Result: the age-of-air RMSE against CLaMS is 0.73–0.75 yr and the tropical age at 55 hPa 2.11–2.18 yr in <i>every</i> run, across "
               "a factor 3.5 in columns, 2 in stratospheric spacing and 11 in cost. strat63 reproduces L95 within 0.02 yr / 0.1 K / 0.3 m/s at "
               "1.4× the speed; strat47 costs 0.1 yr aloft, 1 m/s of QBO amplitude and 2–4 m/s of vortex for another 16 %; T119 improves the "
               "climatology (u RMSE 4.9 → 4.6 m/s, stronger jets, the February 2006 warming) at 3.5× the cost and does not touch the age. Decision: "
               "T63 strat63. In hindsight (Phase 10) the \"0.8 yr excess\" all nine runs shared was a 5-year spin-up reading of a clock that never "
               "converges, which strengthens rather than weakens the conclusion that the grid is not the lever."))
    s.append(fig("09_resolution/resolution_sweep.png", "Phase 9: age of air, circulation, climatology and cost across the nine grids "
                 "(docs/outputs/09_resolution/resolution_sweep.png).", maxh=12 * cm))

    # ------------------------------------------------------------------ production
    s.append(P("4. The production run and what it revealed (Phase 10)", H1))
    s.append(P("<b>Design.</b> The archive is training data for an ML transport model with a 6-hour step, so Phase 10 switched to instantaneous 6-hourly "
               "output with omega, the Gregorian calendar (JCM's 365_day default had run the season and the QBO month 5–12 days early in Phases 6–9), "
               "and a tracer set with known structure: three clocks (700 hPa, 150 hPa entry age, surface), the sai box source, five Gaussian pulses at "
               "different latitudes, longitudes and heights, four continuous Gaussian sources, and N2O- and CFC-11-like species initialised from "
               "WACCM (the only chemistry output on the machine; ERA5 and the PARADIS CESM data have none) with WACCM's zonal-mean loss frequencies. "
               "A 2005–2009 review chain was run first; Susanne's review changed the pulses from quarterly re-injection to a single injection at "
               "t0, added the continuous sources (one site her choice), and the 1990–2019 chain followed (30.5 min per year, GPU 0, ~15 h)."))
    s.append(P("<b>Found and fixed on the way.</b> (1) The N2O-like tracers grew to 1.07 in the tropical upper troposphere: JCM's global mass fixer "
               "rescales the whole field each step to restore the post-physics mass, which is right for tendencies that add or remove mass and wrong for "
               "a physics that imposes a <i>value</i> (1 below 700 hPa); the factor compounds. Same mechanism as the Phase 3 clock bug; both species "
               "left the fixer. (2) A chain prefix must never be reused: the production chain would have skipped 2005–2009 as \"done\" from the review "
               "run and failed on 2010; caught ten minutes before. (3) A missing ERA5 QBO year silently froze the target on the last month; the term now "
               "refuses. (4) Passive tracers are linear: a 5-day run with pulse_1 doubled gave exactly 2× the field and a bit-identical flow, so the "
               "amplitudes probe nothing and were dropped in Phase 11."))
    s.append(P("<b>What the tracers do.</b> Every stratospheric pulse's mass centroid descends to 160–180 hPa within 1–2 years; the pulses decay "
               "exponentially with an e-folding that grows with height (70 d at 70 hPa, 150 d at 30 hPa, 240 d at 10 hPa, 320 d at 3 hPa) and are below "
               "1e-4 of the injected mass after 2.5 years, so they carry signal for two years of the 30. The late-time rate (~75 d) is the same for all "
               "of them and is tropospheric removal: the only sink is relaxation in the two lowest layers, reached by the resolved ERA5-nudged flow alone "
               "(no convection or boundary-layer mixing), a property of the stripped physics. The sources equilibrate within a year at residence times "
               "0.24–0.49 yr with a ±10–20 % annual cycle from the seasonal Brewer–Dobson circulation; the 60°S / 5 hPa source shows the vortex descent "
               "and its summer breakdown in its centroid. N2O and CFC-11 lose 11–14 % of their WACCM mass in two years and then hold."))
    s.append(fig("10_production/p10_30yr_tracers_vertical.png",
                 "Phase 10, 1990–2019: mass-centroid pressure and vertical spread of the five pulses and four sources over the first two years "
                 "(docs/outputs/10_production/p10_30yr_tracers_vertical.png).", maxh=9.5 * cm))
    s.append(P("<b>The finding that changed the plan: the mesosphere is never ventilated.</b> The age-of-air comparison against CLaMS, made at "
               "Susanne's request after 30 years, shows the clock never equilibrates: 55 hPa tropics 4.9 yr at the end of 2009 and 6.5 yr in 2019 "
               "(CLaMS 1.3), 12 hPa extratropics 13.6 → 18.4 yr (CLaMS 4.7), growing 0.2–0.5 yr per year. Above ~1 hPa the age is 22–23 yr and "
               "<i>uniform in latitude</i>: the mesosphere has not been flushed once, and the smooth fall-off below is a stagnant lid leaking down by "
               "mixing. This is not a weak Brewer–Dobson circulation (Susanne's objection, and correct): the tropical upward mass flux at 100 / 70 / "
               "30 / 10 hPa is 11.1 / 8.2 / 3.7 / 1.35 × 10⁹ kg/s against WACCM6's 10.8 / 6.1 / 3.1 / 1.39. The stratospheric cell is as strong as "
               "WACCM's but closes below a mesosphere that has no drag to drive a circulation: gravity-wave drag was dropped in Phase 1 because "
               "JCM's Hines/Lott-Miller terms are column-vectorised and Held-Suarez is not (issue #20), the Rayleigh sponge only damps, and the "
               "semi-Lagrangian top is a no-flux cap. Consequences: the Phase 9 \"0.8 yr too old\" was a 5-year clock reading of an unbounded clock; "
               "the N2O/CFC-11 isopleths ~6 km below WACCM's (half-value at 21 vs 8 hPa in the tropics) were read as recirculated N2O-free "
               "mesospheric air."))
    s.append(fig("10_production/p10_30yr_aoa_triptych.png",
                 "Phase 10: surface-clock mean age after 30 years (2019 annual mean) against CLaMS and WACCM6 "
                 "(docs/outputs/10_production/p10_30yr_aoa_triptych.png).", maxh=8.5 * cm))

    # ------------------------------------------------------------------ phase 11
    s.append(PageBreak())
    s.append(P("5. The tracer lid (Phase 11)", H1))
    s.append(P("<b>What was tried.</b> A dynamical fix (mesospheric drag) is a tuning project and was deferred. Instead the tracers are prescribed where "
               "the dynamics are not credible, the same logic as nudging the troposphere to ERA5: above 1 hPa the clocks relax with tau 1 d to WACCM6 "
               "REF-D1's zonal-mean mean age (~4.4 yr, flat in latitude; +110 d for the 700 hPa and surface clocks), and n2o / cfc11 to their WACCM state. "
               "1 hPa rather than the sponge (0.2 hPa) because the Phase 10 age is flat, i.e. shows no circulation, down to 1–2 hPa; WACCM's age rather than "
               "zero so the mesosphere does not become a second surface. At the same time the injections were revised as asked: unit amplitudes, a "
               "sharp-edged twin of every pulse and source (1 inside the cap, 0 outside), and no surface sink, so pulses conserve their mass. Two 5-year "
               "runs 1990–1994 in parallel: <b>A</b> with no sink anywhere, <b>B</b> with the pulses, sources and sai relaxed to zero above the lid."))
    s.append(P("<b>What it showed.</b> The lid does what it was asked, no more. The oldest air anywhere is 5.4 yr (Phase 10: 23); the tropical pipe is "
               "young up to ~20 hPa; the extratropical lower stratosphere reads 4.5 yr at 55 hPa against CLaMS 4.1. But above ~20 hPa the age is "
               "4.5–5 yr with almost no latitude structure, the lid value propagated downward: the model's own deep branch still does not ventilate "
               "the upper stratosphere, the lid has replaced an unbounded reservoir by a bounded one. The tropical 55 hPa age is 2.7 yr (CLaMS 1.3) and "
               "still creeping up by ~0.15 yr per year, so the tropics–extratropics contrast is 1.9 yr against CLaMS's 2.8. N2O and CFC-11 did not "
               "move at all (burdens 0.858 / 0.809, exactly the Phase 10 values), so the Phase 10 reading was incomplete: with the mesosphere pinned to "
               "WACCM's state the depletion is unchanged, hence it is produced <i>inside</i> the stratosphere, where 5–30 hPa air is 4.5–5 yr old "
               "against WACCM's 3–4 and the extra residence is extra photolysis. Same root cause, different path."))
    rows = [["end of", "55 hPa tropics", "55 hPa 50–70°", "12 hPa tropics", "12 hPa 50–70°", "3 hPa tropics", "max"],
            ["1990", "0.91", "1.75", "1.70", "3.11", "3.72", "4.92"], ["1992", "2.31", "3.84", "3.89", "4.67", "4.63", "4.98"],
            ["1994", "2.67", "4.49", "4.52", "5.08", "4.94", "5.41"], ["CLaMS 2005–2009", "1.33", "4.12", "3.68", "4.56", "—", "—"]]
    s.append(table(rows, [3.0 * cm] + [2.3 * cm] * 6, hl=[4]))
    s.append(P("Run A, surface-clock mean age in years at year ends (docs/outputs/11_lid_tracers/output.md).", CAP))
    s.append(P("<b>A versus B, and the decision.</b> The meteorology is identical (passive tracers), so the difference is the lid sink alone: it removes "
               "14–15 % of the 3 hPa pulse in the first half year and then nothing, 4 % of the 5 hPa source as a steady leak, ~1 % of the 10 hPa pulse "
               "and the 20 hPa source, 0.4 % of sai; the eight lower injections, the species and the clocks are unchanged to 1e-3. The box twins are "
               "injected to 0.02–0.03 RMSE (the interpolation of a step), never go negative, and decay like the Gaussians; in A every pulse's mass is "
               "constant to 2e-3 over five years, which is the advection scheme's own audit. Susanne chose <b>A</b> (2026-09-16) and asked for 15 more "
               "years; the chain 1995–2009 is running on GPU 0 (31 min per year, ~8 h) and will show where the tropical age settles."))
    s.append(fig("11_lid_tracers/p11a_5yr_aoa_triptych.png",
                 "Phase 11 run A: surface-clock mean age at the end of 1994 against CLaMS and WACCM6 (docs/outputs/11_lid_tracers/p11a_5yr_aoa_triptych.png, "
                 "branch phase11-lid-tracers).", maxh=8.5 * cm))
    s.append(fig("11_lid_tracers/p11a_5yr_steady_clocks.png",
                 "Phase 11 run A: N2O- and CFC-11-like zonal means against WACCM (top) and the three clocks (bottom) after five years "
                 "(docs/outputs/11_lid_tracers/p11a_5yr_steady_clocks.png).", maxh=9.5 * cm))

    # ------------------------------------------------------------------ phase 12
    s.append(PageBreak())
    s.append(P("6. Circulation tests, running now (Phase 12)", H1))
    s.append(P("Susanne, after the Phase 11 review: \"the circulation in the phase11 runs looks too weak and some things seem off, so I want to do a "
               "couple of different tries.\" Two suspects, each tested alone against a control with the Phase 11 A dynamics, 1990–1994, so the "
               "comparison is like for like at the same stage of spin-up:"))
    s.extend(bullets([
        "<b>QBO nudging off</b> (p12_noqbo). Since Phase 8 the tropical zonal-mean wind between 90 and 1 hPa is relaxed with tau 1 d. A strong, fast "
        "relaxation of the zonal wind is a momentum forcing of the tropical stratosphere; if it fights the model's own wave driving it changes the "
        "residual circulation. Read: w* and the upward mass flux at 100 / 70 / 30 / 10 hPa, age of air, before and after.",
        "<b>The full L95 troposphere</b> (p12_l81, strat81 = strat63 with all 26 tropospheric layers put back). The troposphere is where the nudging acts "
        "and where the waves that drive the Brewer–Dobson circulation are generated; 8 layers over 850 hPa of it may under-resolve both.",
        "Age of air is read on two clocks: the surface clock (CLaMS convention) and a new <b>aoa500</b> clock zeroed wherever p &gt; 500 hPa, "
        "as asked. The 19 injection tracers are integrated but not written, so the archive is 12 instead of 31 3-D fields.",
    ]))
    s.append(P("Status at the time of writing (2026-09-16 evening PDT): the control and strat81 chains are on their 1993 segments (GPUs 1 and 2), "
               "the QBO-off chain on 1991 (GPU 3, released for it). Its first attempt failed on a bash quirk: an empty per-segment override "
               "variable expanded to a literal brace; fixed and re-launched. Diagnostics (scripts/phase12_compare.py: w* from the TEM streamfunction, "
               "age per clock, WACCM6 and CLaMS as references) run when all three chains are done. A functional test of the comparison on Phase 11 A vs B "
               "already put numbers on the control: w* at 70 hPa 0.33 mm/s against WACCM6's 0.21 (lower branch <i>stronger</i>) and the 10 hPa "
               "up-flux 1.16 vs 1.37 × 10⁹ kg/s (deep branch weaker), with a 5-year-mean noise floor of ~0.01–0.08 × 10⁹ kg/s."))

    # ------------------------------------------------------------------ tried and dropped
    s.append(P("7. Things tried and set aside", H1))
    rows = [["Tried", "Outcome", "Where"],
            ["Gravity-wave drag in the stripped model", "Dropped in Phase 1: JCM's GWD terms are column-vectorised, Held-Suarez is full-field. Now the prime suspect for the unventilated mesosphere", "issue #20; Phase 10 record"],
            ["A single 5-year run instead of chained segments", "OOM at L95 (154 GB of ERA5 target on an 80 GB card); chaining through checkpoints is exact at every boundary", "KEY_DECISIONS #20, issue #26"],
            ["Clock and value-imposing tracers under JCM's global mass fixer", "Clock slowed to 0.44 day/day (Phase 3); n2o grew to 1.07 (Phase 10). Exempted", "KEY_DECISIONS #19, #36"],
            ["e90 as a tropopause marker; unity as a conservation probe", "e90 is unusable in a dry model (issue #23); unity's job is done by the pulses' mass. Both dropped in Phase 10", "Phase 10 record"],
            ["Polvani-Kushner as published (tau 40 d, half-year cosine season, unbounded cooling aloft)", "Jets 55 % of ERA5, wrong autumn onset, 143 K at 3 hPa. Chosen: tau 15 d, equinox-to-equinox, faded above 3 hPa", "KEY_DECISIONS #24"],
            ["Full ECHAM physics under specified dynamics as the stratosphere", "Better T (4.3 K) but no Arctic vortex and 9.7 m/s of wind error, at 30× the cost", "Phase 6 record, issue #35"],
            ["dt 30 and 45 min", "30 min: Antarctic jet −18 %; 45 min: winds degrade; kept as a fast mode only", "Phase 7, issue #51"],
            ["QBO window top 4 hPa; tau 10 and 5 d; daily QBO target", "4 hPa left a 1–3 hPa easterly bias; tau 10/5 d gave 80/86 % amplitude; daily target dropped as not-QBO variability", "Phase 8 addenda, KEY_DECISIONS #26, #32"],
            ["Higher horizontal resolution (T85, T119), thinner stratosphere (strat47)", "No change in transport; T119 climatology only at 3.5× cost; strat47 costs QBO amplitude", "Phase 9, KEY_DECISIONS #31"],
            ["Pulse amplitudes as a probe of concentration dependence", "Passive tracers are exactly linear; amplitudes carry no information. Unit amplitudes since Phase 11", "Phase 10 record"],
            ["Surface sink for pulses and sources", "Made the pulses vanish in 2–3 years at the stripped model's own ~75 d tropospheric removal rate; removed in Phase 11 at Susanne's request", "Phase 11 record"],
            ["Lid sink for injections (Phase 11 B)", "Removes 14–15 % of the 3 hPa pulse and 4 % of the 5 hPa source, else identical; A preferred for exact conservation", "Phase 11 record"],
            ["PARADIS rollout winds through offline clocks", "Stratosphere too young everywhere; shown as a lower bound only (the rollout carries no tracer)", "Phase 4 follow-ups, PRs #30, #37"],
            ["JCM's 365_day calendar", "Season and QBO month 5–12 days early in Phases 6–9; Gregorian since Phase 10 (not re-run: small against the biases)", "KEY_DECISIONS #34"]]
    s.append(table(rows, [5.0 * cm, 8.2 * cm, 3.8 * cm]))

    # ------------------------------------------------------------------ open
    s.append(PageBreak())
    s.append(P("8. Open questions", H1))
    s.extend(bullets([
        "<b>Why does the deep branch not ventilate the upper stratosphere?</b> The lower branch is as strong as or stronger than WACCM's, the 10 hPa "
        "up-flux is ~15 % weaker, and above ~20 hPa the age is flat in latitude. Phase 12 tests the QBO nudging and the thinned troposphere; the "
        "remaining candidate is the missing mesospheric drag (a column-vectorised Held-Suarez would let JCM's Hines/Lott-Miller terms compose, issue "
        "#20), which would also let the lid go.",
        "<b>The tropical lower-stratospheric age</b> (2.7 yr at 55 hPa after five years vs CLaMS 1.3, still creeping): how much is the missing "
        "deep branch, how much the slow transit through an unmixed troposphere (issue #25; the entry-age clock separates the two), how much the "
        "subtropical mixing? The 1995–2009 extension of Phase 11 A will show the equilibrium.",
        "<b>N2O and CFC-11 too low by ~6 km</b>: produced inside the stratosphere by too-old 5–30 hPa air; follows the deep-branch answer.",
        "<b>Lid height</b>: the age is flat from 1 to ~3 hPa, so a lid at 3 hPa might pin less and give the same stratosphere. Not tested.",
        "<b>The nudging cutoff</b> is a hard 150 hPa mask; it should follow the model's tropopause with a taper (issue #1).",
        "<b>Which biases matter for aerosol?</b> Nothing here has aerosol or radiation yet. RRTMGP with prescribed ozone (issue #2), MAM4 or TOMAS "
        "as a physics term (issues #9, #10) and the Pinatubo validation (issue #11) are the next part of the plan once transport is trusted.",
        "<b>The time-step ceiling</b>: is the 0.2 semi-implicit off-centering what limits the step to below 60 min? Two departure iterations did not help.",
    ]))

    s.append(P("9. Operational lessons", H1))
    s.extend(bullets([
        "JAX falls back to the CPU <i>silently</i> when it cannot see a GPU. On this node the /dev/nvidia* device nodes vanish at every reboot (the "
        "driver lives in a GPU-Operator container); two launches ran on the CPU at 30 simulated days per hour before this was caught. "
        "chain_segments.sh now refuses without a GPU; scripts/restore_nvidia_dev.sh recreates the nodes. The node's cards became H200 141 GB during "
        "the 2026-09-14/16 reboots.",
        "The ERA5 nudging target is GPU-resident: one-year segments, JAX preallocation at 0.92, and 30-day smoke tests do not exercise the memory "
        "limit (their target is 12× smaller).",
        "Never reuse a run prefix across chains (the chain skips segments whose logs show a clean exit). Never edit a running bash script in place.",
        "Diagnostics on 6-hourly archives must stride (every 20th frame = 5 days); a stride-4 pass over 650 GB ran for 4 h without finishing.",
        "Every phase ran unattended in tmux from a pipeline script that also writes the record, commits and opens the PR, so sessions can be closed.",
    ]))
    s.append(Spacer(1, 10))
    s.append(P("Records: docs/outputs/&lt;NN&gt;/output.md per phase (numbers, commands, acceptance tables, figures); KEY_DECISIONS.md (#1–#42) for every "
               "default and why; DEFERRED.md for what is consciously not done; PROGRESS.md for the running throughput table. Per-phase PDFs: "
               "jcm-strat_phases_0-4.pdf, _phase6_stratosphere.pdf, _phase7_timestep.pdf, _phase8_qbo.pdf, _phase9_resolution.pdf.", CAP))

    doc.build(s)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", default=os.path.join(REPO, "docs", "outputs", "jcm-strat_phases_0-12_summary.pdf"))
    ap.add_argument("--figure-roots", nargs="*", default=[], help="additional checkouts to look up docs/outputs figures in (e.g. an unmerged phase worktree)")
    a = ap.parse_args()
    FIGURE_ROOTS[:] = [REPO] + [os.path.abspath(r) for r in a.figure_roots]
    build(a.out)
    print(a.out)
