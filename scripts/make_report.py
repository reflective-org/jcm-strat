#!/usr/bin/env python3
"""Build the jcm-strat status report (PDF) from the phase records and their figures.

    python scripts/make_report.py docs/outputs/jcm-strat_phases_0-4.pdf

The narrative lives in this file (one section per phase, plain language first); the figures are
the tracked PNGs under docs/outputs/<NN_phase>/. Regenerate after every phase so the PDF and
the per-phase output.md records never disagree. Numbers quoted here are copied from those
records - the records are canonical.
"""
import datetime as dt
import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "docs", "outputs")
TITLE = "jcm-strat: Phases 0 to 4"
FOOT = "jcm-strat Phases 0-4"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=10, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9, leading=12, alignment=TA_LEFT, spaceAfter=5)
SMALL = ParagraphStyle("S", parent=P, fontSize=8, leading=10)
CAP = ParagraphStyle("Cap", parent=P, fontSize=7.5, leading=9.5, textColor=colors.HexColor("#333333"), spaceBefore=2, spaceAfter=8)
CELL = ParagraphStyle("Cell", parent=P, fontSize=7.5, leading=9.5, spaceAfter=0)
QUOTE = ParagraphStyle("Q", parent=P, leftIndent=10, rightIndent=10, backColor=colors.HexColor("#f2f2f2"),
                       borderPadding=6, spaceBefore=6, spaceAfter=10)

W = A4[0] - 4 * cm


def para(t, st=P): return Paragraph(t, st)
def bullets(items): return ListFlowable([ListItem(Paragraph(i, P), leftIndent=10) for i in items], bulletType="bullet", start="•", leftIndent=12)
def fig(rel, caption, width=W, maxh=13 * cm):
    p = os.path.join(OUT, rel)
    if not os.path.exists(p):
        return [para(f"[missing figure {rel}]", CAP)]
    from PIL import Image as PILImage
    w, h = PILImage.open(p).size
    scale = min(width / w, maxh / h)
    return [Image(p, width=w * scale, height=h * scale), para(caption, CAP)]
def table(rows, widths, header=True):
    data = [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6e6e6")))
    t.setStyle(TableStyle(st))
    return t


def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("Helvetica", 7.5); canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"{FOOT}  |  page {doc.page}"); canvas.restoreState()


def build(out_pdf: str) -> None:
    S = []
    today = dt.date.today().strftime("%-d %B %Y")
    S += [Paragraph(TITLE, ss["Title"]),
          para(f"Approach A, a stripped-down stratosphere model on JCM / Dinosaur semi-Lagrangian. Status record as of "
               f"{today}. Repository reflective-org/jcm-strat, working copy /data/JCM_stripped/jcm-strat.", SMALL)]

    S += [para("The idea in one paragraph", H1),
          para("Start from the full JCM climate model, remove every piece of tropospheric physics, replace what the "
               "troposphere needs with ERA5 nudging, then add passive tracers to measure stratospheric transport. Each "
               "phase adds or removes exactly one thing, so any change in behaviour has one cause. The target for Part 1 is a "
               "model that runs years of stratospheric tracer transport per hour on one H100, conserves tracer mass, stays "
               "non-negative, and produces an age-of-air pattern comparable to CLaMS. All runs use GPU 0 of the shared 8x "
               "H100 node, one at a time, on the T63L95 grid (1.9 degrees, 95 hybrid levels, top near 0.01 hPa) with a 12 "
               "minute time step.")]
    S += [para("Phase overview", H2), table([
        ["Phase", "What changed", "Run length", "Speed (sim. days / hour, stepping)", "Status"],
        ["0", "Nothing. Stock JCM, full ECHAM physics", "10 days", "52", "merged (PR 16)"],
        ["1", "Removed all 12 ECHAM terms; kept Held-Suarez only (dry)", "1 year", "5 787", "merged (PR 21)"],
        ["2", "Added ERA5 nudging of u, v, T below 150 hPa; ERA5 initial state", "1 year (2005)", "5 455", "merged (PR 22)"],
        ["3", "Added four passive tracers (aoa, unity, sai, e90)", "1 year (2005)", "4 458", "merged (PR 24)"],
        ["4", "Nothing physical; run 2005-2009 as five chained one-year segments; age of air vs CLaMS and WACCM",
         "5 years", "4 315 (4 460-4 480 per segment)", "done, PR open"],
    ], [1.2 * cm, 6.6 * cm, 2.4 * cm, 3.3 * cm, 2.7 * cm])]
    S += [para("The Phase-1 number (from Phase 4)", H2),
          para("The stripped model runs one simulated year in 10.4 minutes end to end on one H100 (about 4 400 simulated "
               "days per hour stepping, 1 800 end to end), so 30 years cost about 5 GPU-hours; full ECHAM physics on the same "
               "grid takes 7.8 hours per year. Passive-tracer mass closes to 0.02 percent over five years for a uniform tracer "
               "and to 1 percent against an analytic source, with exact non-negativity and no polar pull-up. The age-of-air "
               "pattern is right (tropical pipe, poleward ageing) but the tropics are 1.5 years too old at 20 km and there is no "
               "polar-night jet: with Held-Suarez standing in for radiation the Brewer-Dobson circulation is too weak. The "
               "speed question is answered; the fidelity question now hinges on the stratospheric forcing (issues 2 and 5).", QUOTE)]

    # ---------------- Phase 0
    S += [para("Phase 0: reproduce the stock model", H1),
          para("Nothing of ours. Stock JCM with the full ECHAM physics package (RRTMGP radiation, Tiedtke convection, "
               "clouds, TKE diffusion, surface scheme, Hines and orographic gravity-wave drag) on the T63L95 grid for 10 "
               "days. Purpose: prove the environment is sound and set the reference speed."),
          bullets(["Environment: uv-managed Python 3.11, JAX 0.10.2 with CUDA 12, dinosaur 1.4.0 from the pinned "
                   "semi-lagrangian branch (bd99e39b), JCM 2.1.0b0 from the pinned dev branch (849893b). Everything, "
                   "including caches and runs, lives under /data because the root disk is 97 percent full.",
                   "Result: 51.6 simulated days per hour at a 12 minute step and 51.9 at 15 minutes. The published A100 "
                   "reference for this configuration is 52. Wall time per simulated day is independent of the step because "
                   "radiation, firing every 2 hours, dominates the cost. The speed lever is therefore removing physics, not "
                   "lengthening the step.",
                   "One real bug found and fixed: JAX silently ran on CPU until the containerised libcuda path was added to the "
                   "loader path. The environment check now asserts a CUDA device."])]
    S += fig("00_phase0/baseline_zonal_mean_day10.png",
             "Figure 1. Phase 0 sanity plot: zonal-mean temperature and zonal wind at day 10 of the stock model from the "
             "dry Jablonowski-Williamson state. A spin-up, not a climatology.", maxh=8 * cm)

    # ---------------- Phase 1
    S += [PageBreak(), para("Phase 1: strip the physics (dry Held-Suarez)", H1),
          para("Removed: all 12 ECHAM terms. Convection, cloud fraction, cloud microphysics, boundary-layer diffusion, "
               "surface exchange, RRTMGP radiation, aerosol, chemistry, and both gravity-wave schemes. Kept: Held-Suarez "
               "(1994) only, that is Newtonian relaxation of temperature toward a prescribed profile plus Rayleigh friction near "
               "the surface. The model is dry: it carries no water, has no moisture physics, and starts from a zero-humidity "
               "Jablonowski-Williamson state."),
          para("Held-Suarez acts at every level. Below about the tropopause the equilibrium temperature has real structure "
               "(warm tropics, cold poles). Above it the target is clamped to a flat 200 K at every latitude and the relaxation time "
               "is 40 days. The stratosphere is therefore pulled toward an isothermal state with no seasonal cycle and no "
               "polar-night jet. A separate upper sponge relaxes the top ten levels toward 250 K as a numerical lid."),
          bullets(["One year, no NaNs in any of 13 chunks, surface pressure drift +0.005 hPa, top-level temperature flat.",
                   "Speed: 5 787 simulated days per hour stepping, about 110 times Phase 0. A simulated year takes 9 minutes "
                   "end to end including compile and output.",
                   "Stratosphere is 21 K RMS colder than ERA5 between 7 and 70 hPa and has essentially no zonal wind. This is "
                   "the known limitation of Held-Suarez, not a bug; fixes are filed as issues 2 (RRTMGP) and 5 (Polvani-Kushner).",
                   "The planned gravity-wave-drag variant could not be composed with Held-Suarez on JCM's 3-D physics path "
                   "and was dropped (issue 20). Phase 3 later removed that blocker."])]
    S += fig("01_dry/p1_dry_1yr_zonal_mean.png",
             "Figure 2. Phase 1 after one year. Top: zonal-mean temperature and zonal wind. Two symmetric subtropical jets near "
             "200 hPa, an isothermal 200 K stratosphere, no polar-night jet. Bottom: model minus the ERA5 1989-1994 annual-mean "
             "zonal-mean tape over 7-70 hPa, the stratospheric cold bias and the missing stratospheric winds.", maxh=12.5 * cm)

    # ---------------- Phase 2
    S += [PageBreak(), para("Phase 2: nudge the troposphere to ERA5 (specified dynamics)", H1),
          para("Added: the initial state from ERA5 on 1 January 2005, and Newtonian nudging of the zonal wind, meridional "
               "wind and temperature toward 6-hourly ERA5 with a 6 hour relaxation time. Nothing else changed. The nudging "
               "is masked off in the lowest two model levels (boundary layer free) and at every level with reference pressure "
               "below 150 hPa, so the whole stratosphere evolves freely. Surface pressure, humidity and tracers are never nudged."),
          bullets(["One year (2005), stable, surface pressure drift -0.02 hPa, speed within 6 percent of Phase 1.",
                   "The troposphere now carries real 2005 meteorology: global kinetic energy has a seasonal cycle, high in "
                   "boreal winter and lowest around day 150, which the seasonless Phase 1 could not produce. Jets are "
                   "asymmetric between hemispheres in late December.",
                   "No visible discontinuity at the 150 hPa cutoff in temperature or wind.",
                   "Stratosphere above 150 hPa is unchanged from Phase 1 by construction: still Held-Suarez, no polar-night "
                   "jet. Planetary waves from the nudged troposphere can propagate up, but there is no radiatively driven vortex "
                   "for them to act on.",
                   "Not yet measured: RMSE against ERA5 at 500 hPa, the tropopause position, and the January 2006 SSW. The "
                   "diagnostic scripts are issue 17."])]
    S += fig("02_nudged/p2_sd_1yr_summary.png",
             "Figure 3. Phase 2 stability summary over 2005: global-mean surface pressure, global kinetic energy, top-level "
             "temperature, global temperature extremes. The seasonal cycle in kinetic energy is the signature of the nudged "
             "troposphere.", maxh=9 * cm)
    S += fig("02_nudged/p2_sd_1yr_zonal_mean.png",
             "Figure 4. Phase 2 at day 365 (late December 2005). Top: hemispherically asymmetric jets, no kink at 150 hPa "
             "(dotted line). Bottom: the stratospheric bias against ERA5 is the same as in Phase 1, as it must be.", maxh=12 * cm)

    # ---------------- Phase 3
    S += [PageBreak(), para("Phase 3: passive tracers", H1),
          para("Added: one physics term carrying four passive tracers, advected by the semi-Lagrangian dycore as grid-point "
               "(nodal) fields with JCM's global proportional mass fixer on. Tracers ride on the winds and never feed back on the "
               "dynamics, so the meteorology is identical to Phase 2. Each tracer isolates a different property of the transport "
               "scheme:"),
          table([["Tracer", "Definition", "Question it answers", "Result after 1 year"],
                 ["unity", "1 everywhere, no sources or sinks",
                  "Does the scheme move air without inventing or destroying it? Any deviation is numerical error.",
                  "Worst cell off by 2.6e-4. Pass."],
                 ["sai", "Constant source in 15S-15N, 25-55 hPa (about 20-25 km); no sink",
                  "Is mass conserved with a known analytic answer (burden = source x box mass x time)? Also: minimum "
                  "exactly zero, no polar pull-up at the top.",
                  "Tracks the analytic line to 1.4 percent; min 0.0; polar top-level value 0.1 percent of the global column. Pass."],
                 ["aoa", "Clock: +1 day per day everywhere, reset to 0 where p > 700 hPa",
                  "How long has this air been in the stratosphere? The mean age of air, the primary transport metric.",
                  "0.97-0.99 yr above 100 hPa: correct but uninformative after one year. Needs Phase 4."],
                 ["e90", "100 in the two lowest layers, 90-day e-folding sink (Prather et al. 2011)",
                  "Where is the tropopause? The 90 contour is a standard dynamical tropopause marker.",
                  "Does not work here: the dry model has no convection to stir the troposphere, so the 90 contour sits at 970 hPa. Issue 23."],
                 ], [1.3 * cm, 4.2 * cm, 5.6 * cm, 5.1 * cm]),
          Spacer(1, 6),
          para("<b>The genuine find.</b> The first attempt lost 56 percent of the clock over the year. JCM's global mass fixer "
               "restores each tracer's global mass after every step. At the sharp 700 hPa reset edge the limiter creates a little "
               "mass each step, and the fixer removed it by rescaling the whole field, stratosphere included. A clock is not a "
               "conserved quantity and must not be mass-fixed. It was invisible in every conservation diagnostic (unity, sai and "
               "e90 were all fine). Fixed with a config key that exempts aoa from the fixer, verified by a 5-day run and a unit test."),
          bullets(["Speed: 4 458 simulated days per hour stepping; four extra tracers cost about 1 ms on a 6 ms step. End to "
                   "end a simulated year takes 10.5 minutes.",
                   "Held-Suarez had to be re-implemented as a per-column variant with identical forcing, because JCM's 3-D "
                   "physics path cannot add tracer tendencies across terms. This also unblocks gravity-wave drag (issue 20)."])]
    S += fig("03_tracers/p3_tracers_1yr_tracer_zonal.png",
             "Figure 5. Phase 3 zonal means at day 365. Age of air (top left) reads about one year everywhere above 100 hPa, "
             "with only a faint tropical minimum: the stratosphere has aged, fresh air has barely entered. The injection tracer "
             "(top right) stays in its source region. e90 (bottom left) decays from the surface instead of marking the tropopause. "
             "unity - 1 (bottom right) is uniform to 1.5e-4.", maxh=11 * cm)
    S += fig("03_tracers/p3_tracers_1yr_tracer_budget.png",
             "Figure 6. Phase 3 budgets over 2005. unity's global burden and cell extremes stay within 3e-4 of one. The sai "
             "burden (bottom left) follows the analytic source line. e90's global mean saturates after about 100 days as expected "
             "for a 90-day lifetime.", maxh=9.5 * cm)

    # ---------------- Phase 4
    S += [PageBreak(), para("Phase 4: five years, 2005-2009, and the age of air", H1),
          para("Nothing physical changed: the Phase 3 configuration was run from 1 January 2005 to 31 December 2009 "
               "(1 826 days). It could not be run as one job. JCM keeps the whole ERA5 nudging target on the GPU, and five years "
               "of 6-hourly targets at L95 are 154 GB against an 80 GB card, so the first attempt died in its first step with an "
               "out-of-memory error. The five years therefore run as five chained calendar-year segments, each warm-started "
               "from the previous segment's checkpoint, which restores the full model state including the tracers. The clock and "
               "the injection tracer are continuous to within one save at every year boundary. The segments' output is linked "
               "into one 1 826-day run for the analysis. The per-year ERA5 windows were cut locally from one prefetched "
               "five-year file rather than downloaded again (issue 26 asks upstream to stream the target)."),
          para("What passes", H2),
          bullets(["Stability over five years: 65 of 65 chunks healthy, surface pressure drift +0.03 hPa, top-level temperature "
                   "trend zero.",
                   "Transport: unity within 2.6e-4 of one in every cell at every one of 365 saves and its global burden drifts by "
                   "1.7e-4 over five years; the sai burden stays on its analytic line to 1.1 percent; no tracer goes negative "
                   "beyond roundoff; no polar pull-up (after five years of continuous source the tracer fills the whole upper "
                   "domain roughly uniformly rather than piling up at the poles).",
                   "Age-of-air pattern: youngest air in the tropics at every level, oldest over both poles; the tropical pipe "
                   "is there (Figure 7).",
                   "Speed: 4 315 simulated days per hour stepping over the 64 steady chunks (4 460-4 480 within each "
                   "segment), 1 768 end to end for the whole five years including five compiles and five 31 GB target loads. "
                   "One simulated year in 10.4 minutes; 30 years in about 5.2 GPU-hours."]),
          para("What does not", H2),
          bullets(["<b>The tropics are 1.5 years too old.</b> At 55 hPa (about 20 km) the model's mean age is 2.9 years between "
                   "10S and 10N against 1.3 in CLaMS, while at 50-70 degrees it matches (4.1 vs 4.1). The tropics-to-"
                   "extratropics contrast is 1.2 years against 2.8 in CLaMS, 43 percent, so the 'within 50 percent' acceptance "
                   "fails. At 12 hPa the whole profile is 0.2-0.7 years too old (Figure 8). Two causes, both expected from the "
                   "Phase 1 physics choice. First, weak tropical upwelling: the Held-Suarez stratosphere is isothermal with no "
                   "meridional temperature gradient and no polar-night jet, so there is little wave-driven Brewer-Dobson "
                   "circulation above the nudged layer. Second, slow tropospheric transit: the clock resets below 700 hPa but, "
                   "without convection or boundary-layer mixing, air between 700 and 150 hPa ages for months before it reaches "
                   "the stratosphere; the tropical profile already reads about one year at 100 hPa where CLaMS reads 0.2. Part of "
                   "the tropical excess is therefore tropospheric, not stratospheric, and the clock should be referenced to the "
                   "tropopause for this purpose (issue 25).",
                   "<b>No polar-night jet, so no SSW test.</b> The zonal-mean wind at 61N and 10 hPa is -4 to -2 m/s in every "
                   "winter, where ERA5 has about +30 m/s. The nudged troposphere supplies the wave forcing but the Held-Suarez "
                   "stratosphere has no vortex for it to disturb, so the three observed warmings of 2006, 2008 and 2009 cannot "
                   "show up (Figure 9). This is the limitation flagged since Phase 1 (issues 2 and 5); a full-ECHAM specified-"
                   "dynamics reference year is being run to quantify the gap.",
                   "Five years is still not equilibrium: everything above about 10 hPa reads 4.9-5.0 years, the run age. The "
                   "upper-stratospheric comparison with CLaMS becomes meaningful only after about 10 years."]),
          para("What it means", H2),
          para("The speed question Approach A was set up to answer is answered: a physics dycore with the troposphere "
               "stripped and nudged does 30 years of stratospheric tracer transport in about five GPU-hours on one H100, "
               "with the remaining end-to-end cost split roughly half stepping, half output writing (issue 19), and the "
               "time-step sweep (issue 3) still untried. An emulator would need to beat a few GPU-hours per 30 years and match "
               "this transport fidelity to be worth building. The fidelity bar is currently set by the stratospheric forcing, not "
               "by the transport scheme: the same tracers on a stratosphere with a polar-night jet and a realistic Brewer-Dobson "
               "circulation are the next experiment.")]
    S += fig("04_5yr/p4_5yr_aoa_triptych.png",
             "Figure 7. Zonal-mean age of air at the end of 2009: the model (last 12 saves), CLaMS v3.1 driven by ERA5 "
             "(2005-2009 mean, a surface clock like ours) and WACCM6 REF-D1 (2005-2009 mean, an entry age relative to 103 hPa, "
             "hence younger by construction). The model has the right shape and the right extratropical ages but a tropical pipe "
             "that is far too old and too shallow.", maxh=7.5 * cm)
    S += fig("04_5yr/p4_5yr_aoa_profiles.png",
             "Figure 8. Mean age against latitude at about 55 hPa (left) and 12 hPa (middle), and the tropical vertical profile "
             "(right). The extratropics match CLaMS at 55 hPa; the tropics are 1.5 years too old; the tropical profile is already "
             "about one year old at 100 hPa, the tropospheric-transit signature.", maxh=6.5 * cm)
    S += fig("04_5yr/p4_5yr_vortex.png",
             "Figure 9. Zonal-mean zonal wind at 10 hPa and 61N (blue) and 61S (orange), 5-day means, with the ERA5 sudden-"
             "warming dates marked. There is no winter westerly jet to disrupt in either hemisphere.", maxh=5.5 * cm)
    S += fig("04_5yr/p4_5yr_tracer_zonal.png",
             "Figure 10. Zonal means at day 1826. Age of air (top left) now shows the tropical pipe through the whole lower "
             "stratosphere; the injection tracer (top right) has spread over the entire upper domain after five years of "
             "continuous source; e90 (bottom left) still hugs the surface; unity - 1 (bottom right) is uniform to 1e-4.", maxh=11 * cm)
    S += fig("04_5yr/p4_5yr_tracer_budget.png",
             "Figure 11. Five-year tracer budgets: unity's burden and cell extremes stay within 3e-4 of one throughout; the sai "
             "burden follows the analytic source line for five years; e90 stays saturated.", maxh=9.5 * cm)
    S += fig("04_5yr/p4_5yr_summary.png",
             "Figure 12. Five-year stability summary: surface pressure, global kinetic energy with its five seasonal cycles, "
             "top-level temperature, global temperature extremes.", maxh=9 * cm)

    # ---------------- speed + overall
    S += [PageBreak(), para("Speed across the phases", H1),
          para("Blue is model stepping only, from per-chunk wall time. Orange is end to end including JIT compile and writing "
               "output. The end-to-end number is the one that matters for a 30-year run; the gap between the two is output "
               "volume and per-chunk overhead (issue 19). The 12 minute step is far below the semi-Lagrangian ceiling, so a "
               "time-step sweep (issue 3) is the next speed lever.")]
    S += fig("04_5yr/throughput.png",
             "Figure 13. Simulated days per wall-clock hour on one H100 for each configuration, log scale. Removing the physics "
             "gave a factor of about 110; nudging cost 6 percent and four tracers a further 18 percent in stepping; the five "
             "Phase-4 segments repeat the Phase-3 number to within 1 percent.", maxh=9 * cm)
    S += [para("Overall reading", H1),
          para("The chain is internally consistent: each phase changed one thing and the diagnostics moved only where they "
               "should. The transport machinery is cheap, conserving and stable over five years. The one standing scientific "
               "weakness is the Held-Suarez stratosphere, isothermal with no polar-night jet and no seasonal cycle, and Phase 4 "
               "has now measured its cost: a tropical pipe 1.5 years too old and no vortex. Fixing the stratospheric forcing "
               "(Polvani-Kushner, issue 5, or RRTMGP with prescribed gases, issue 2) is the first thing to do next, with the "
               "same passive tracers as the yardstick.")]

    # ---------------- reference data
    S += [PageBreak(), para("Reference data: where it comes from", H1),
          para("ERA5 for nudging and initialisation (Phases 2 onward)", H2),
          para("Source: the WeatherBench2 public ERA5 archive on Google Cloud Storage, anonymous access, read through JCM's "
               "own reader (jcm.data.era5). For the T63 grid (192 longitudes) the reader picks the 240 x 121 equiangular store: "
               "<font face='Courier' size='7'>gs://weatherbench2/datasets/era5/1959-2023_01_10-6h-240x121_equiangular_with_poles_conservative.zarr</font>"),
          bullets(["6-hourly, 1959-2023, 13 pressure levels from 1000 to 50 hPa. Values above 50 hPa are clamped, which is why "
                   "nudging must stop well below that; the 150 hPa cutoff keeps a wide margin.",
                   "Fields used: u, v, T (nudging target) and the full state for the 1 January 2005 initial condition. Regridded "
                   "once to the model's hybrid levels and cached under the repository (cache/era5). One year of target is 31 GB "
                   "and is held on the GPU during the run; five years (154 GB) do not fit an 80 GB card, hence the chained "
                   "one-year segments in Phase 4.",
                   "Period 2005-2009: volcanically quiet, overlaps the CLaMS record (2004-2023), contains three observed sudden "
                   "stratospheric warmings (January 2006, February 2008, January 2009)."]),
          para("ERA5 zonal-mean tape for the stratospheric comparison rows", H2),
          para("The bottom rows of Figures 2 and 4 compare against a monthly zonal-mean ERA5 tape from the Copernicus Climate "
               "Data Store product reanalysis-era5-pressure-levels-monthly-means, prepared earlier for the AIDE atmosphere "
               "validation. It holds zonal-mean U and T for 1989-1994 on six levels between 7 and 70 hPa at 0.25 degree latitude. "
               "Location: <font face='Courier' size='7'>/home/susanne/docs/AIDE-atmosphere_validation/AIDE-atmosphere/output/era5_monthly_tape.nc</font>"),
          para("Note that the tape years (1989-1994) differ from the model years (2005-2009). Since the Held-Suarez stratosphere "
               "has no interannual variability this is a bias check, not a year-matched comparison."),
          para("CLaMS age of air (Phase 4 reference)", H2),
          para("Chemical Lagrangian Model of the Stratosphere, version 3.1 (Konopka et al. 2025), driven by ERA5, from the Zenodo "
               "dataset 'Gridded CLaMS Simulations Driven by Multiple Reanalyses' (doi:10.5281/zenodo.17357000, PI F. Ploeger, "
               "Forschungszentrum Juelich). Monthly zonal means on 39 pressure levels and a 1 degree latitude grid, 2004-2023. The "
               "variable AGE is mean age from a clock tracer increasing linearly at the Earth's surface, in years. Local copy: "
               "<font face='Courier' size='7'>/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip</font> (one file per year)."),
          para("Note the definitional difference from our clock: CLaMS resets at the surface, jcm-strat resets everywhere below "
               "700 hPa, and WACCM (below) measures age relative to an entry point at about 100 hPa. CLaMS is the like-for-like "
               "reference; WACCM is shown for the pattern. Referencing our clock to the tropopause is issue 25."),
          para("WACCM6 age of air (Phase 4 reference)", H2),
          para("CESM2 WACCM6 REF-D1 simulations (the CCMI-2022 reference historical experiment), ensemble member 04, AOA1mf "
               "clock tracer, 1970-2019, 70 levels, 192 latitudes, noleap calendar. Age is given in years relative to a base point "
               "at latitude 0.47 degrees, 103 hPa. Members 01-03 and SF6-derived ages are also available in the SAVE subdirectory. "
               "Local copy: <font face='Courier' size='7'>/data/CESM2_REFD1_AOA/AoA_waccm6_refd1.04_AOA1mf_1970-2019_ba_0_100.0_ck_0_50.0.nc</font>"),
          para("Model code and pins", H2),
          bullets(["JCM (climate-analytics-lab/jax-gcm), branch dev, commit 849893b, 1 September 2026, as a submodule.",
                   "Dinosaur (shoyer/dinosaur), branch semi-lagrangian, commit bd99e39b, 24 August 2026, as a submodule; the "
                   "open upstream PR is neuralgcm/dinosaur#135.",
                   "Every phase's exact command, resolved configuration, commit and wall-clock time is in "
                   "docs/outputs/&lt;phase&gt;/output.md in the repository, with the plots shown here beside it. This PDF is "
                   "generated from those records by scripts/make_report.py."])]

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title=TITLE, author="Susanne Baur")
    doc.build(S, onFirstPage=footer, onLaterPages=footer)
    print("wrote", out_pdf)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "jcm-strat_phases_0-4.pdf"))
