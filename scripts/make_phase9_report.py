#!/usr/bin/env python3
"""Build the Phase 9 (resolution sensitivity) PDF from the Phase 9 record and its figures.

    python scripts/make_phase9_report.py [docs/outputs/jcm-strat_phase9_resolution.pdf]

The narrative lives here, plain language first; the figures are the tracked PNGs under
docs/outputs/09_resolution/ and the metrics table is read from resolution_metrics.md there, so the
numbers cannot drift from the record. Regenerate the PDF whenever the record changes.
"""
import datetime as dt
import os
import sys

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(REPO, "docs", "outputs", "09_resolution")
W = A4[0] - 4 * cm
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=8, spaceAfter=5)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
BL = ParagraphStyle("BL", parent=B, leftIndent=12, spaceAfter=3)
CAP = ParagraphStyle("CAP", parent=B, fontSize=8.5, leading=11, textColor=colors.HexColor("#444444"), spaceBefore=2, spaceAfter=10)
SM = ParagraphStyle("SM", parent=B, fontSize=7.6, leading=9.6)
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


def metrics_rows():
    """The main table of resolution_metrics.md as a list of rows (strings), header first."""
    rows = []
    for line in open(os.path.join(D, "resolution_metrics.md")):
        if line.startswith("## "):
            break
        if line.startswith("| ") and not line.startswith("|---"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def build(out_pdf):
    today = dt.date.today().strftime("%-d %B %Y")
    rows = metrics_rows()
    # columns: run, grid, columns, dt, AoA RMSE, bias, age55, age12, transit, upflux, T, u, jets, QBO, stepping, ms, hours
    keep = [0, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]
    hdr = ["run", "columns", "dt [min]", "AoA RMSE vs CLaMS [yr]", "age 55 hPa: tropics / 50-70 / contrast [yr]",
           "age 12 hPa: tropics / 50-70 / contrast [yr]", "transit 70-10 hPa [yr]", "up-flux 70 hPa [10^9 kg/s]", "T RMSE vs ERA5 [K]",
           "u RMSE vs ERA5 [m/s]", "u(60N) DJF / u(60S) JJA [m/s]", "QBO RMS vs ERA5 [m/s]", "stepping [d/hr]", "5-yr wall [h]"]
    trows = [hdr] + [[r[i] for i in keep] for r in rows[1:]]
    colw = [1.55, 1.25, 0.9, 1.35, 2.35, 2.35, 1.25, 1.35, 1.15, 1.15, 1.55, 1.25, 1.2, 1.0]
    scale = W / sum(colw)
    colw = [c * scale * cm / cm for c in colw]
    colw = [c * (W / sum(colw)) for c in colw]

    s = [P("jcm-strat Phase 9: resolution sensitivity of stratospheric transport", TITLE),
         P("Nine 2005-2009 runs of the Phase 8b configuration (Polvani-Kushner stratosphere, ERA5-nudged troposphere, QBO nudged to ERA5 "
           "up to 1 hPa, four passive tracers) at T63, T85 and T119 horizontally and on the L95 grid and two reductions of it that keep the "
           f"stratospheric levels, strat63 and strat47. Benchmarked against CLaMS/ERA5 age of air and the ERA5 climatology. Record as of {today}, "
           "branch phase9-resolution.", SUB)]

    s += [P("1. The question", H1),
          P("Both resolutions set the implicit diffusion of the semi-Lagrangian transport: the horizontal truncation through the interpolation at "
            "the departure points and the hyperdiffusion that comes with it, the vertical spacing through the interpolation across levels in a "
            "stratosphere whose transport is a slow ascent against a strong stratification. After Phase 8 the model's tropical air at 55 hPa "
            "was 0.8 years too old against CLaMS driven by ERA5, and the age contrast between the tropics and 50 to 70 degrees was half of "
            "CLaMS' (1.4 against 2.8 years). Before a grid is fixed for the aerosol work: how much of that is resolution, which way does each "
            "axis move it, and what does each step cost?"),
          P("2. What was varied, and what was held", H1),
          *bullets([
              "<b>Horizontal: T63, T85, T119.</b> T127 cannot be built in JCM (the valid truncations jump from 106 to 119 to 170); T119 on 360 by "
              "180 Gaussian points is the 1 degree grid. The time step follows the truncation, 12, 9 and 6 minutes, because Phase 7 showed that "
              "the step matters on its own and a fixed step at a finer grid would have been a second changed variable. Each step must divide the "
              "5-day save interval: JCM truncates the ratio silently.",
              "<b>Vertical: L95, strat63, strat47.</b> Both reductions are subsets of the L95 interfaces, so every kept level is an L95 level. "
              "strat63 keeps all 47 L95 levels between 1 and 159 hPa and thins the mesosphere from 21 to 8 levels and the troposphere from 27 to 8. "
              "strat47 additionally keeps only every other interface between 1 and 30 hPa (15 levels of about 2 km) while 30 to 159 hPa stays at "
              "the L95 spacing of about 1 km. This is not ECHAM's own L47, whose stratosphere is 2 km throughout. The hyperdiffusion order at "
              "each reduced level is L95's order at that level; the upper sponge keeps L95's damping profile in pressure (4 levels with a factor "
              "6.7 per level on strat63, 3 levels with a factor 8 on strat47). The tables are served by a configuration key, level_table: strat; "
              "JCM's own tables are untouched.",
              "<b>Everything else is Phase 8b.</b> The same nudging (6-hourly ERA5 below 150 hPa, QBO to 1 hPa with a 10-day relaxation), the same "
              "tracers, the same 2005 start from ERA5, the same five years. The T63L95 point is the Phase 8b chain itself.",
              "<b>Held fixed and recorded as limitations.</b> The T63 terrain file is interpolated to every grid (only T63 and T106 have native "
              "files; the dry model has no sub-grid orography), so the orography does not sharpen with the truncation. T85 and T119 take their "
              "nudging target from the finer WeatherBench2 store (360 by 181) where T63 uses the 240 by 121 one. The clock is the surface clock, "
              "so it includes tropospheric transit. All runs carry the same 5-year spin-up deficit of the clock (issue 44).",
              "<b>Chained segments.</b> JCM keeps the whole ERA5 target of a run on the GPU, about 3 bytes per level per column per 6-hourly step "
              "per variable: 31 GB for a year at T63L95, 109 GB at T119L95. So the five years are chained in segments that fit, one year at T63, "
              "half a year at T85L95, a quarter at T119L95, restarting from the checkpoint each time; segment lengths are multiples of the 5-day "
              "save interval and never cross a calendar year. The ERA5 windows for all nine runs are 2.2 TB and their prefetch, not the GPU, "
              "was the critical path.",
          ])]

    s += [PageBreak(), P("3. The runs and the checks", H1),
          table([["run", "columns", "levels", "dt", "segments", "target per segment", "GPU", "wall for 5 years"],
                 ["T63L95 (Phase 8b chain)", "18 432", "95", "12 min", "5 x year", "31 GB", "0", "1 h 17"],
                 ["T63L63", "18 432", "63", "12", "5 x year", "21 GB", "0", "1 h 05"],
                 ["T63L47", "18 432", "47", "12", "5 x year", "15 GB", "0", "58 min"],
                 ["T85L95", "32 768", "95", "9", "10 x half-year", "28 GB", "0", "2 h 12"],
                 ["T85L63", "32 768", "63", "9", "10 x half-year", "18 GB", "2", "1 h 44"],
                 ["T85L47", "32 768", "47", "9", "5 x year", "28 GB", "1", "1 h 23"],
                 ["T119L95", "64 800", "95", "6", "20 x quarter", "28 GB", "0", "4 h 34"],
                 ["T119L63", "64 800", "63", "6", "20 x quarter", "18 GB", "1", "3 h 37"],
                 ["T119L47", "64 800", "47", "6", "10 x half-year", "27 GB", "2", "2 h 40"]],
                [3.4 * cm, 1.6 * cm, 1.3 * cm, 1.3 * cm, 2.6 * cm, 2.6 * cm, 1.1 * cm, 2.6 * cm], style=B),
          Spacer(1, 4),
          P("GPUs 0 to 2 were released to this phase for the day, so from 22:08 UTC on 9 September the chains ran three at a time. Wall times "
            "include about 10 minutes per segment for loading the target, compiling and writing output, which is why the 20-segment T119 "
            "chains are slower than their stepping rate alone would say.", CAP),
          P("Acceptance", H2),
          table([["check", "threshold", "result"],
                 ["every chain complete", "all segments exit 0, 1825 days, no out-of-memory, ERA5 from cache",
                  "<b>pass</b>: 8 chains, 75 segments, every one exit 0 and a cache hit; the 28 to 31 GB targets fit at every resolution"],
                 ["tracer conservation: unity", "max deviation below 1e-3", "<b>pass</b>: 2.4e-4 to 3.1e-4 in the nine runs"],
                 ["tracer minima", "at or above 0", "<b>pass</b>: sai and e90 minima 0; the clock -1e-6 day (roundoff)"],
                 ["sai burden vs analytic", "within 2 percent",
                  "<b>formally fails on 6 of 9</b> (-4.0 to +3.6 percent), but the model burdens agree across grids (1.254 to 1.260 at T63 and T119, "
                  "1.295 at T85): the spread is each grid's rendering of the 15 degree by 25 to 55 hPa source box, and the budget script renders "
                  "the analytic box differently again. Conservation is the unity check. Filed in DEFERRED."],
                 ["stability at the chosen step", "u RMSE below 30 m/s, no NaN", "<b>pass</b>: 4.4 to 4.9 m/s, no NaN, surface-pressure drift below 0.03 hPa, top level 249.8 K everywhere"],
                 ["ranking delivered", "per-metric ranks, convergence per axis, cost per unit of improvement", "<b>pass</b>: section 4 and 5"]],
                [3.6 * cm, 4.6 * cm, 8.8 * cm], style=B)]

    s += [PageBreak(), P("4. Results", H1),
          P("Age of air from the last twelve months of each chain against the CLaMS v3.1 / ERA5 2005 to 2009 mean (surface clock in both); "
            "the climatology against ERA5 monthly means 100 to 1 hPa; the tropical upward mass flux from the TEM residual circulation against "
            "WACCM6 with the same method; the QBO as the RMS of the equatorial monthly wind against ERA5 over 10 to 70 hPa. Read from "
            "docs/outputs/09_resolution/resolution_metrics.md."),
          table(trows, colw), Spacer(1, 6),
          P("Reference rows: CLaMS is the target for the age columns (contrast 2.79 years, transit 2.94 years); WACCM6 gives 6.1 for the "
            "70 hPa up-flux (ERA5-era literature 6 to 8); ERA5 is the zero of the T, u and QBO columns and has u(60N, 10 hPa) 28 m/s in DJF "
            "and u(60S) 72 m/s in JJA.", CAP),
          fig("resolution_sweep.png",
              "Figure 1. Every metric against the number of columns (T63, T85, T119), one line per vertical grid; dotted lines are the references. "
              "Axes start at zero so that a flat response reads as flat. Top row: age-of-air fidelity; middle: circulation and climatology; "
              "bottom: QBO and cost.", maxh=13.5 * cm)]

    s += [PageBreak(),
          fig("strat/strat_climatology_panel.png",
              "Figure 2. Zonal-mean temperature and zonal wind 300 to 1 hPa, DJF and JJA, for the nine runs (rows) and ERA5 and WACCM6 (bottom rows). "
              "The runs are indistinguishable at this scale; the differences are 0.3 K and 0.5 m/s in RMSE.", maxh=24 * cm)]
    s += [PageBreak(),
          fig("strat/vortex_series.png",
              "Figure 3. u(60N, 10 hPa) and u(60S, 10 hPa) through 2005 to 2009 for the nine runs, ERA5 and WACCM6. The polar-night jets strengthen "
              "by 3 to 6 m/s from T63 to T119; the February 2006 warming appears in every T85 and T119 run and in no T63 run.", maxh=12 * cm),
          fig("T63L95/p8b_5yr_aoa_profiles.png",
              "Figure 4. Age of air at T63L95 (the Phase 8b baseline): latitude profiles at 55 and 12 hPa and the tropical vertical profile, "
              "against CLaMS (surface clock) and WACCM6 (entry age).", maxh=6 * cm),
          fig("T119L95/p9_t119l95_5yr_aoa_profiles.png", "Figure 5. The same at T119L95, 3.5 times the columns and half the time step.", maxh=6 * cm)]
    s += [PageBreak(),
          fig("T63L47/p9_t63l47_5yr_aoa_profiles.png",
              "Figure 6. The same at T63 on strat47 (2 km levels between 1 and 30 hPa). The clock reads 0.1 year older above 30 hPa.", maxh=6 * cm),
          fig("T119L47/p9_t119l47_5yr_aoa_profiles.png", "Figure 7. T119 on strat47: the two changes together, still the same picture.", maxh=6 * cm)]

    s += [PageBreak(), P("5. Reading", H1),
          *bullets([
              "<b>Horizontal resolution does not move the transport.</b> From T63 to T119, 3.5 times the columns, half the step and 3.5 times the "
              "cost per simulated year, the age-of-air RMSE against CLaMS goes 0.74, 0.75, 0.75 years; the tropical age at 55 hPa 2.11, 2.13, "
              "2.13; the 70 to 10 hPa transit 1.96, 1.93, 1.92; the 70 hPa up-flux 7.7, 7.6, 7.6. The tropics-to-extratropics contrast even shrinks "
              "a little (1.43, 1.40, 1.38 against CLaMS' 2.79). The T63 to T85 step changes each transport number by less than the T85 to T119 "
              "step does, and both are below 0.03 years: for this scheme the transport is converged in the horizontal at T63. What T119 buys is "
              "the climatology: u RMSE 4.9 to 4.6 m/s, polar-night jets 3 to 6 m/s stronger (u(60S) in JJA 64 to 70 against ERA5's 72; u(60N) in "
              "DJF 31 to 34 against 28, so overshooting), and the February 2006 warming that no T63 run produces. None of it reaches the age of air.",
              "<b>Thinning the mesosphere and the troposphere changes nothing and buys 38 percent.</b> strat63 agrees with L95 within 0.02 years, "
              "0.1 K and 0.3 m/s at all three truncations, with identical tracer and stability checks. Halving the 1 to 30 hPa spacing as well "
              "(strat47) is visible but small: the clock reads 0.1 year older above 30 hPa (tropical age at 12 hPa 3.43 to 3.54; the 70 to 10 hPa "
              "transit 1.95 to 2.08, coincidentally towards CLaMS' 2.94), the QBO amplitude at 20 hPa drops from 14.1 to 13.0 m/s and its RMS "
              "against ERA5 rises from 4.0 to 4.7 to 5.0 m/s (fewer levels in the nudging window and 2 km levels where the shear zones are about "
              "1 km), and the polar-night jets are 2 to 4 m/s weaker. strat47 is 60 percent faster than L95 at every truncation.",
              "<b>The age bias is not a resolution problem.</b> The 0.8-year tropical excess at 55 hPa and the halved contrast are the same in all "
              "nine runs to within 0.07 years, across a factor 3.5 in columns, a factor 2 in stratospheric level spacing and a factor 11 in cost. "
              "Implicit diffusion of the semi-Lagrangian transport at these resolutions is therefore not the cause; the Phase 6 diagnosis stands "
              "(too much aged air mixed into the tropical lower stratosphere, and slow transit through the unmixed troposphere; issues 25 and 31), "
              "and the 150 hPa entry clock of decision 22 is the tool to separate the two. The cost per unit of age-of-air improvement from "
              "resolution is undefined: there is no improvement to buy.",
              "<b>Recommendation.</b> Keep T63 and adopt strat63 as the working vertical grid: the same physics and transport as L95 at 1.4 times "
              "the speed, a five-year chain in 65 minutes. strat47 is the option when throughput matters more than the QBO amplitude and the "
              "upper-stratospheric wind (another 16 percent). Higher horizontal resolution is worth revisiting only once the model has a reason "
              "to resolve more, for example interactive aerosol heating or a wave-driven QBO; for passive transport under nudging it costs "
              "3.5 times for nothing.",
              "<b>Caveats.</b> The 5-year clock is 0.6 years young in the extratropics in every run alike (issue 44); the surface clock includes "
              "tropospheric transit (issue 25); the T63 terrain was interpolated to T85 and T119, so the resolved orography did not sharpen with the "
              "grid; T85 and T119 take their nudging target from the finer WeatherBench2 store. None of these can create the flatness seen here, "
              "but the jet and warming differences at T119 are the kind of result that native orography could alter.",
          ]),
          P("6. Where things are", H2),
          P("Runs under runs/p9_* in the phase9 worktree (segments runs/p9_&lt;grid&gt;_&lt;YYYYMMDD&gt;, aggregates runs/p9_&lt;grid&gt;_5yr); the record "
            "docs/outputs/09_resolution/output.md with resolution_metrics.md, resolution_sweep.png and one directory of figures per run; the level "
            "tables jcm_strat/levels.py with tests/test_levels.py; the segment schemes jcm_strat/segments.py; the per-segment ERA5 prefetch "
            "jcm_strat/prefetch_era5.py; the chain and queue scripts scripts/chain_segments.sh, phase9_*.sh; the analysis scripts/phase9_analysis.sh "
            "and scripts/resolution_metrics.py; experiments p9_res, p9_l63, p9_l47 and grid presets strat_t63_l63_hybrid, strat_t63_l47_hybrid, "
            "echam_t85_l95_hybrid under jcm_strat/config. Decisions 27 to 31 in KEY_DECISIONS.md; findings in DEFERRED.md (Phase 9 section).")]

    doc = SimpleDocTemplate(out_pdf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="jcm-strat Phase 9: resolution sensitivity", author="Susanne Baur")

    def footer(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#666666"))
        c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"jcm-strat Phase 9  |  page {d.page}"); c.restoreState()
    doc.build(s, onFirstPage=footer, onLaterPages=footer); print("wrote", out_pdf)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "docs", "outputs", "jcm-strat_phase9_resolution.pdf"))
