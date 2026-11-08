#!/usr/bin/env python3
"""Build the shareable transport scorecard page (Phase 24) from the success metrics and the figures.

    python scripts/build_scorecard.py SUCCESS_JSON REPORT_DIR FINDINGS_HTML NAME=DIAG_DIR [...]

SUCCESS_JSON is scripts/success_metrics.py's output for the runs; REPORT_DIR holds the comparison figures
(scripts/report_figures.py) and receives index.html plus a runs/<NAME>/ copy of each run's diagnostic plots;
FINDINGS_HTML is the hand-written summary inserted at the top. Every number on the page comes from SUCCESS_JSON.
"""
from __future__ import annotations

import html, json, os, re, shutil, sys

RUNS_INFO = {  # what changes from P20b, why the run was made
    "P20b": ("Nothing: the reference configuration, run continuously since 1990.",
             "Baseline. Good age of air, but the polar vortices are too weak."),
    "AL7": ("Adds the full temperature correction poleward of 25&deg; (ramping in to full strength at 35&deg;).",
            "Fix the polar vortex."),
    "AL7h": ("As AL7, with the correction at half strength.",
             "Does a weaker correction keep most of the vortex gain while ageing the air less?"),
    "AL7t": ("As AL7, with the correction moved poleward: zero up to 35&deg;, full strength from 50&deg;.",
             "Does the young air come from the subtropical part of the correction?"),
    "L0": ("Extends the ERA5 nudging in the tropics up to 150 hPa (400 hPa in the extratropics, as P20b).",
           "Does nudging the tropical upper troposphere fix the weak upwelling at 100 hPa?"),
    "LAL7": ("AL7's correction plus L0's higher tropical nudging.",
             "Do the two changes combine?"),
    "QBO30": ("As AL7h, with the QBO nudging window starting higher: no nudging below 50 hPa, full strength from 30 hPa "
              "(AL7h: zero at 90 hPa, full from about 40 hPa).",
              "Does leaving the lowest stratosphere free let the upwelling there adjust towards WACCM6?"),
    "QBO10d": ("As AL7h, with the QBO nudging ten times weaker: relaxation timescale 10 days instead of 1 day (WACCM6 uses "
               "10 days). Same window as AL7h.",
               "Does gentler QBO nudging over the whole window help in the same way?"),
}
DESIGN = [  # rows of the design grid: correction label, run with P20b's nudging, run with the higher tropical nudging
    ("None", "P20b", "L0"),
    ("Full (AL7)", "AL7", "LAL7"),
    ("Half strength", "AL7h", None),
    ("Full, moved poleward", "AL7t", None),
    ("Half strength, QBO nudging from 30 hPa", "QBO30", None),
    ("Half strength, QBO nudging at 10 days", "QBO10d", None),
]
COLORS = {"P20b": "#242729", "AL7": "#6f382a", "AL7h": "#b18e63", "AL7t": "#5e7227", "L0": "#25a3b2", "LAL7": "#6f6194", "QBO30": "#d1495b",
          "QBO10d": "#2b59c3"}
GROUPS = {"A": "Age of air", "B": "Residual circulation", "C": "Polar vortex", "D": "Variability and relations"}
BOUNDS = [  # group, id, metric, reference ({X} = that metric's reference value from the scores), bound
    ("A", "A1", "Tropical (10&deg;S&ndash;10&deg;N) entry age at 55 hPa (clock reset below 150 hPa)", "WACCM6 entry age ({A1} yr)", "&plusmn; 0.25 yr"),
    ("A", "A2", "Entry age over the whole stratosphere, 100&ndash;5 hPa, RMS error", "CLaMS (ERA5-driven)", "&lt; 0.4 yr"),
    ("A", "A3", "Age step from the tropics to 50&ndash;70&deg; at 55 hPa", "CLaMS ({A3} yr)", "&plusmn; 0.5 yr"),
    ("A", "A4", "Tropical transit time from 70 to 10 hPa", "CLaMS 3.0 yr, WACCM6 2.5 yr", "inside 2.3&ndash;3.2 yr"),
    ("B", "B1", "Tropical (15&deg;S&ndash;15&deg;N) w* at 100, 70, 50, 30 and 10 hPa (5 metrics)", "WACCM6 histSST 1996&ndash;2014", "within a factor of 1.35"),
    ("B", "B2", "Upward mass flux at 100 and 70 hPa (2 metrics)", "WACCM6 ({B2-100} and {B2-70} &times; 10<sup>9</sup> kg/s)", "&plusmn; 20 %"),
    ("C", "C1", "Winter jet maximum (30&ndash;90&deg;) at 50 and 10 hPa, both hemispheres: strength and latitude (8 metrics)", "ERA5, same months", "&plusmn; 5 m/s, &plusmn; 4&deg;"),
    ("C", "C2", "Winter polar-cap (60&ndash;90&deg;) temperature bias at 50 hPa, DJF north / JJA south (2 metrics)", "ERA5, same months", "&plusmn; 2 K"),
    ("D", "D1", "Year-to-year spread: standard deviation over winters of the winter-mean wind at 10 hPa, 55&ndash;65&deg; (DJF north, JJA south; 2 metrics)", "ERA5, same winters", "within a factor of 1.5"),
    ("D", "D2", "Daily spread: standard deviation of daily wind anomalies at 60&deg;, 10 hPa, in winter (2 metrics)", "ERA5, same days", "within a factor of 1.35"),
    ("D", "D3", "Number of northern major sudden stratospheric warmings (wind at 60&deg;N, 10 hPa turning easterly in winter)", "ERA5, same winters", "&plusmn; 1 event"),
    ("D", "D4", "Seasonal cycle: final-warming date at 60&deg;, 10 hPa (2 metrics) and the annual-cycle amplitude of tropical w* at 70 hPa", "ERA5", "&plusmn; 10 days; factor 1.35"),
    ("D", "D5", "Daily variability of the upward wave forcing: standard deviation of the daily 100 hPa eddy heat flux, 45&ndash;75&deg;, in winter (2 metrics)", "ERA5, same days", "within a factor of 1.35"),
    ("D", "D6", "Heat flux &rarr; vortex: slope of the 50 hPa polar-cap temperature on the heat flux of the previous 40 days (Newman et al. 2001; 2 metrics)", "ERA5, same days", "within a factor of 1.35"),
    ("D", "D7", "Age &harr; upwelling: slope of the monthly tropical age anomaly at 55 hPa on the 70 hPa w* anomaly of the previous 3 months", "CLaMS age, ERA5 w*", "within a factor of 1.5"),
]
DIAG = [("age_seasonal_aoa150.png", "Entry age, DJF and JJA, against WACCM6"),
        ("age_seasonal_aoa_sfc.png", "Surface-clock age, DJF and JJA, against CLaMS"),
        ("tem_streamfunction.png", "Residual-circulation streamfunction against WACCM6"),
        ("vortex_jets.png", "Winter jets: strength and position by height"),
        ("wind_seasonal.png", "Zonal-mean wind, DJF and JJA, against ERA5"),
        ("qbo_time_height.png", "Equatorial wind (QBO and SAO) against ERA5")]

CSS = r"""
:root{
  /* layout: one reading column (~46rem) with full-width bands for figures and the scorecard */
  --bg:#ffffff; --panel:#F6EFEA; --line:#E1CBBA; --ink:#282C2E; --muted:#5f6264; --accent:#A47F52; --link:#466F8D;
  --plate:#ffffff; --pass:#4f6b34; --pass-bg:#e7ecdc; --near:#7a5a00; --near-bg:#fff1c2; --fail:#8e3b28; --fail-bg:#f6dfd8;
  --display:"Libre Caslon Text", Georgia, "Times New Roman", serif; --body:"Open Sans", "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#1d2022; --panel:#262a2c; --line:#3a3f42; --ink:#ECE6E0; --muted:#b4b8b9; --accent:#d1ab7c; --link:#9cc0da;
  --plate:#f4f1ee; --pass:#c6dba8; --pass-bg:#33402a; --near:#ffd866; --near-bg:#4a3d12; --fail:#f2b4a3; --fail-bg:#4d2a22; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#1d2022; --panel:#262a2c; --line:#3a3f42; --ink:#ECE6E0; --muted:#b4b8b9; --accent:#d1ab7c; --link:#9cc0da;
  --plate:#f4f1ee; --pass:#c6dba8; --pass-bg:#33402a; --near:#ffd866; --near-bg:#4a3d12; --fail:#f2b4a3; --fail-bg:#4d2a22; color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.55;font-weight:400}
.wrap{max-width:62rem;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:2.5rem 4rem}
.col{max-width:46rem}
a{color:var(--link)}
.eyebrow{font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 .5rem}
h1,h2,h3{font-family:var(--display);font-weight:400;text-wrap:balance;line-height:1.25;margin:0}
h1{font-size:2.1rem;margin-bottom:.6rem} h2{font-size:1.5rem;margin:3rem 0 .8rem} h3{font-size:1.1rem;margin:1.6rem 0 .5rem}
p{margin:.6rem 0} .lede{font-size:1.05rem;color:var(--ink)} .muted{color:var(--muted)} .small{font-size:.85rem}
section{border-top:1px solid var(--line);margin-top:2.5rem}
.findings{background:var(--panel);border-radius:6px;padding:1.1rem 1.3rem;margin:1.5rem 0}
.findings ol{margin:.3rem 0 .2rem 1.1rem;padding:0} .findings li{margin:.45rem 0}
.tablewrap{overflow-x:auto;margin:.8rem 0}
table{border-collapse:collapse;width:100%;font-size:.88rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:.78rem;letter-spacing:.03em;text-transform:uppercase}
td.num,th.num{text-align:right}
.run{display:inline-flex;align-items:center;gap:.4rem;font-weight:600;white-space:nowrap}
.run i{width:.7rem;height:.7rem;border-radius:50%;display:inline-block;background:var(--c);box-shadow:0 0 0 1.5px var(--plate)}
.pill{display:inline-block;border-radius:999px;padding:.05rem .5rem;font-size:.78rem;font-weight:600;white-space:nowrap}
.pass{color:var(--pass);background:var(--pass-bg)} .near{color:var(--near);background:var(--near-bg)} .fail{color:var(--fail);background:var(--fail-bg)}
.best{outline:2px solid var(--accent);outline-offset:-2px}
.score{font-family:var(--display);font-size:1.25rem}
.bar{height:.4rem;border-radius:3px;background:var(--line);margin-top:.25rem;position:relative;min-width:6rem}
.bar span{position:absolute;inset:0 auto 0 0;border-radius:3px;background:var(--c)}
.bar b{position:absolute;top:-.2rem;bottom:-.2rem;width:2px;background:var(--ink);left:var(--one)}
figure{margin:1.2rem 0;background:var(--plate);border-radius:6px;padding:.8rem}
figure img{display:block;width:100%;height:auto}
figcaption{color:#3b3f41;font-size:.85rem;margin-top:.5rem}
.figs2{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,22rem),1fr));gap:1rem}
.figs2 figure{margin:0}
.tabs{display:flex;flex-wrap:wrap;gap:.4rem;margin:.8rem 0 .4rem}
.tabs button{font:inherit;font-size:.85rem;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:999px;padding:.25rem .8rem;cursor:pointer;display:inline-flex;align-items:center;gap:.4rem}
.tabs button[aria-selected="true"]{background:var(--panel);border-color:var(--accent);font-weight:600}
.tabs button:focus-visible{outline:2px solid var(--link);outline-offset:2px}
.tabs i{width:.6rem;height:.6rem;border-radius:50%;background:var(--c);display:inline-block}
details{margin:.6rem 0} summary{cursor:pointer;color:var(--link)}
code{font-size:.85em;background:var(--panel);padding:.05rem .3rem;border-radius:3px}
@media (max-width:640px){h1{font-size:1.7rem} th,td{padding:.4rem .4rem}}
"""


def pill(err):
    if err <= 1.0:
        return '<span class="pill pass">&#10003; pass</span>'
    if err <= 1.5:
        return '<span class="pill near">~ near</span>'
    return '<span class="pill fail">&#10007; fail</span>'


def run_tag(n):
    return f'<span class="run" style="--c:{COLORS[n]}"><i></i>{n}</span>'


def fmt(v):
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return f"{v[0]:g}-{v[1]:g}"
    if v == 0:
        return "0"
    return f"{v:.2f}" if abs(v) < 10 else f"{v:.1f}"


def main():
    sj, rep, fh = sys.argv[1], sys.argv[2], sys.argv[3]
    y0, y1 = os.environ.get("WINDOW", "2006-2007").split("-")      # scoring window, e.g. WINDOW=2006-2010 (Phase 26)
    runs = dict(a.split("=", 1) for a in sys.argv[4:])
    S = json.load(open(sj)); names = list(runs)
    best = min(names, key=lambda n: S[n]["combined"])
    hasD = all("D_metrics" in S[n] for n in names)                 # Phase 28: group D, reported beside the combined score
    for n, dd in runs.items():                                   # copy each run's diagnostic plots next to the page
        os.makedirs(os.path.join(rep, "runs", n), exist_ok=True)
        for f, _ in DIAG:
            if os.path.exists(os.path.join(dd, f)):
                shutil.copy2(os.path.join(dd, f), os.path.join(rep, "runs", n, f))
    H = []
    H.append('<title>Stratospheric transport scorecard</title>\n<meta name="claude:viewport-fit-sides" content="cover">')
    H.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Caslon+Text&family=Open+Sans:wght@400;600&display=swap">')
    H.append(f"<style>{CSS}</style>")
    H.append('<div class="wrap">')
    H.append('<header class="col"><p class="eyebrow">jcm-strat &middot; dry model &middot; tracer transport</p>'
             '<h1>Stratospheric transport scorecard</h1>'
             f'<p class="lede">{["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"][len(names) - 1]} configurations of the dry JCM model, scored against CLaMS, WACCM6 and ERA5 on age of air, '
             f'the residual circulation and the polar vortex, {y0}&ndash;{y1}'
             + (', with a separate group on variability and two physical relations' if hasD else '') + '.</p></header>')
    H.append(f'<div class="findings col">{open(fh).read()}</div>')

    # --- scorecard summary
    H.append('<section><h2>Scores at a glance</h2><p class="col">Each metric&rsquo;s error is divided by its bound, so 1 is the edge '
             'of acceptable. A group score is the mean over its metrics; the combined score is the mean of the three groups. '
             'Lower is better; the marker on each bar is 1.</p><div class="tablewrap"><table><thead><tr><th>Run</th>'
             + "".join(f'<th>{GROUPS[g]}</th>' for g in "ABC") + '<th>Combined</th><th class="num">Metrics passed</th>'
             + ('<th>D: variability</th><th class="num">D passed</th>' if hasD else '') + '</tr></thead><tbody>')
    scale = max(max(S[n]["groups"][g] for g in "ABC") for n in names) * 1.05
    for n in names:
        cells = ""
        for g in "ABC":
            v = S[n]["groups"][g]
            cells += (f'<td><span class="score">{v:.2f}</span><div class="bar" style="--c:{COLORS[n]};--one:{100/scale:.1f}%">'
                      f'<span style="width:{min(v/scale,1)*100:.1f}%"></span><b></b></div></td>')
        npass = sum(m["err"] <= 1 for m in S[n]["metrics"])
        cls = ' class="best"' if n == best else ""
        H.append(f'<tr{cls}><td>{run_tag(n)}</td>{cells}<td><span class="score">{S[n]["combined"]:.2f}</span></td>'
                 f'<td class="num">{npass} / {len(S[n]["metrics"])}</td>'
                 + (f'<td><span class="score">{S[n]["D"]:.2f}</span></td><td class="num">'
                    f'{sum(m["err"] <= 1 for m in S[n]["D_metrics"])} / {len(S[n]["D_metrics"])}</td>' if hasD else '') + '</tr>')
    H.append('</tbody></table></div>' + ('<p class="col small muted">Group D (variability, SSWs, seasonal cycle and two relations) is '
             'scored the same way but kept out of the combined score, so the combined score stays comparable with earlier versions.</p>'
             if hasD else '') + '</section>')

    # --- runs and metrics
    H.append(f'<section><h2>The runs</h2><p class="col">All {len(names)} runs are the same dry model (T63, 95 levels; relaxation to an '
             'equilibrium temperature, gravity-wave drag, QBO nudging, ERA5 nudging of winds and temperature in the troposphere). '
             'They differ in three settings:</p><ul class="col">'
             '<li><b>A correction to the equilibrium temperature in the extratropics</b>, from 400 to 1 hPa. It was obtained by '
             'repeatedly nudging the equilibrium temperature towards ERA5 temperatures, and its purpose is to strengthen the '
             'polar vortex.</li>'
             '<li><b>How high the ERA5 nudging reaches</b>: up to 400 hPa everywhere, or up to 150 hPa in the tropics.</li>'
             '<li><b>The QBO nudging</b>: the tropical (15&deg;S&ndash;15&deg;N, fading out by 25&deg;) zonal-mean wind is relaxed '
             'towards ERA5&rsquo;s monthly mean so that the model has the observed QBO. In all runs but QBO30 and QBO10d it acts from '
             '90 to 1 hPa with a 1-day timescale. QBO30 raises the bottom of that window to 50 hPa; QBO10d lengthens the timescale '
             'to 10 days.</li></ul>'
             f'<p class="col">P20b has run since 1990. The other {len(names) - 1} start from P20b&rsquo;s state at the end of 2004 and run '
             f'2005&ndash;{y1}; the scores leave out the first year after that restart.</p>')
    H.append('<div class="tablewrap"><table><thead><tr><th>Temperature correction</th><th>ERA5 nudging up to 400 hPa</th>'
             '<th>Up to 150 hPa in the tropics</th></tr></thead><tbody>')
    for lab, r1, r2 in DESIGN:
        cell = lambda r: run_tag(r) if r in names else '<span class="muted">&ndash;</span>'
        H.append(f"<tr><td>{lab}</td><td>{cell(r1)}</td><td>{cell(r2)}</td></tr>")
    H.append('</tbody></table></div>')
    H.append('<div class="tablewrap"><table><thead><tr><th>Run</th><th>What changes from P20b</th><th>Question it answers</th>'
             '</tr></thead><tbody>')
    for n in names:
        a, b = RUNS_INFO[n]
        H.append(f"<tr><td>{run_tag(n)}</td><td>{a}</td><td>{b}</td></tr>")
    H.append('</tbody></table></div>')
    ref = {m["id"]: m["ref"] for m in S[names[0]]["metrics"]}
    rows, grp = "", None
    for g, i, metric, r, bound in BOUNDS:
        if g == "D" and not hasD:
            continue
        if g != grp:
            grp = g; rows += f'<tr><td colspan="4"><b>{g}: {GROUPS[g]}</b></td></tr>'
        r = re.sub(r"\{([^}]+)\}", lambda m: f"{ref[m.group(1)]:.3g}", r)
        rows += f"<tr><td><b>{i}</b></td><td>{metric}</td><td>{r}</td><td>{bound}</td></tr>"
    nm = len(S[names[0]]["metrics"]); per = {g: sum(m["group"] == g for m in S[names[0]]["metrics"]) for g in "ABC"}
    H.append('<h3>How each metric is scored</h3><div class="tablewrap"><table><thead><tr><th></th><th>Metric</th><th>Reference</th>'
             '<th>Bound (normalised error = 1)</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
             '<h3>How the scores are combined</h3><ul class="col">'
             '<li>Each metric&rsquo;s error is divided by its bound, so 1 means &ldquo;at the edge of acceptable&rdquo;.</li>'
             '<li><b>Pass</b>: normalised error at most 1. <b>Near</b>: at most 1.5. <b>Fail</b>: beyond 1.5.</li>'
             '<li>A <b>group score</b> (A, B or C) is the mean of the normalised errors in that group.</li>'
             f'<li>The <b>combined score</b> is the mean of the three group scores, so each group counts equally even though C has '
             f'{per["C"]} metrics and A only {per["A"]}.</li>'
             f'<li>There are <b>{nm} metrics</b> in total ({per["A"]} + {per["B"]} + {per["C"]}); &ldquo;passed&rdquo; counts how many '
             'are at or below 1.</li>'
             '<li>The bounds are &ldquo;moderate&rdquo;: roughly the size of the disagreement between CLaMS and WACCM6.</li>'
             + (f'<li>Group D&rsquo;s {len(S[names[0]]["D_metrics"])} metrics are scored the same way and reported as their own '
                'group, outside the combined score.</li>' if hasD else '') +
             f'<li>All metrics are computed over {y0}&ndash;{y1}.</li></ul></section>')

    def gallery(sec, files, label):
        tabs = "".join(f'<button type="button" role="tab" id="t-{sec}-{n}" aria-selected="{str(i == 0).lower()}" '
                       f'data-sec="{sec}" data-run="{n}" style="--c:{COLORS[n]}"><i></i>{n}</button>' for i, n in enumerate(names))
        panes = ""
        for i, n in enumerate(names):
            figs = "".join(f'<figure><img src="runs/{n}/{f}" alt="{n}: {cap}" loading="lazy"><figcaption>{n}: {cap}</figcaption></figure>'
                           for f, cap in DIAG if f in files and os.path.exists(os.path.join(rep, "runs", n, f)))
            panes += f'<div class="pane" data-sec="{sec}" data-run="{n}"{"" if i == 0 else " hidden"}>{figs}</div>'
        return f'<h3>{label}</h3><div class="tabs" role="tablist" aria-label="{label}">{tabs}</div>{panes}'

    # --- age of air
    H.append('<section><h2>Age of air</h2><p class="col">The entry age counts time since the air was last below 150 hPa, so it '
             'measures transport within the stratosphere only. CLaMS (driven by ERA5) and WACCM6 bracket the plausible range; they '
             'disagree by about 0.6 years in the extratropics at 55 hPa.</p><div class="figs2">'
             '<figure><img src="age_profile.png" alt="Tropical entry age against height for each run, CLaMS and WACCM6"><figcaption>'
             'Tropical (10S&ndash;10N) entry age against height. Faster ascent gives younger air at every level.</figcaption></figure>'
             '<figure><img src="age_latitude.png" alt="Entry age against latitude at 55 and 12 hPa"><figcaption>Entry age against '
             'latitude at 55 and 12 hPa. The step from the tropics to midlatitudes measures how isolated the tropical pipe is.'
             '</figcaption></figure></div>')
    H.append(gallery("age", {"age_seasonal_aoa150.png", "age_seasonal_aoa_sfc.png"}, "Seasonal age maps by run"))
    H.append(_metric_table(S, names, "A") + '</section>')

    # --- circulation
    H.append('<section><h2>Residual circulation</h2><p class="col">The transformed-Eulerian-mean residual circulation carries '
             'tracers up in the tropics and down at high latitudes. Its tropical upwelling at 100 hPa (the shallow branch) and '
             'higher up (the deep branch) set how fast air ages.</p><figure class="col"><img src="wstar_profile.png" alt="Tropical '
             'w* against height"><figcaption>Tropical (15S&ndash;15N) residual vertical velocity against height. WACCM6 is '
             '1996&ndash;2014, ERA5 1996&ndash;2001 (the years on disk).</figcaption></figure>')
    if os.path.exists(os.path.join(rep, "qbo_nudging.png")):
        H.append('<h3>Lighter QBO nudging: AL7h, QBO30 and QBO10d</h3><p class="col">The QBO nudging pins the tropical wind to '
                 'ERA5, and with it the wave drag that drives part of the tropical upwelling. QBO30 and QBO10d loosen it in two ways '
                 'to see whether the lower-stratospheric upwelling then moves towards WACCM6.</p>'
                 '<figure><img src="qbo_nudging.png" alt="QBO nudging rate, QBO amplitude, correlation with ERA5 and 50 hPa '
                 'equatorial wind for AL7h, QBO30 and QBO10d"><figcaption>(a) Strength of the QBO nudging against height. '
                 '(b) QBO amplitude, the standard deviation of monthly equatorial-wind anomalies. (c) Correlation of those anomalies '
                 'with ERA5: 1 means the model QBO is in phase with the observed one. (d) Equatorial wind at 50 hPa, where QBO30 is '
                 'no longer nudged.</figcaption></figure>'
                 '<figure class="col"><img src="qbo_upwelling.png" alt="Tropical w* and entry age for AL7h, QBO30 and QBO10d">'
                 '<figcaption>Tropical upwelling and entry age for the three runs that differ only in the QBO nudging.'
                 '</figcaption></figure>')
    H.append(gallery("circ", {"tem_streamfunction.png", "qbo_time_height.png"}, "Streamfunction and QBO by run"))
    H.append(_metric_table(S, names, "B") + '</section>')

    # --- vortex
    H.append('<section><h2>Polar vortex</h2><p class="col">The winter polar vortex is the barrier that keeps polar air old. '
             'Its strength and position are compared with ERA5 for the same months.</p><figure><img src="jets.png" alt="Winter '
             'jet maximum against height, both hemispheres"><figcaption>Winter jet maximum (strongest zonal-mean wind poleward of '
             '30&deg;) against height.</figcaption></figure>')
    H.append(gallery("vortex", {"vortex_jets.png", "wind_seasonal.png"}, "Jets and seasonal winds by run"))
    H.append(_metric_table(S, names, "C") + '</section>')

    # --- variability and relations (Phase 28)
    if hasD:
        H.append('<section><h2>Variability and relations</h2><p class="col">Groups A&ndash;C score multi-year means. Group D asks '
                 'whether the model also varies like the atmosphere: how much the vortex changes from day to day and from winter to '
                 'winter, how often it breaks down, when it breaks down in spring, and whether two physical links have the observed '
                 'strength. The links are the response of the polar vortex to the waves coming up from the troposphere, and the '
                 'response of the tropical age of air to changes in upwelling. ERA5 here is the full stratospheric reanalysis from '
                 'the Copernicus Climate Data Store, reduced to daily zonal means.</p>'
                 '<figure><img src="variability_vortex.png" alt="Daily zonal-mean wind at 60 degrees and 10 hPa for each run and ERA5">'
                 '<figcaption>Daily zonal-mean wind at 60&deg;, 10 hPa, north and south. Dotted lines mark the ERA5 major sudden '
                 'warmings.</figcaption></figure><div class="figs2">'
                 '<figure><img src="variability_heatflux.png" alt="Polar-cap temperature against the heat flux of the previous 40 days">'
                 '<figcaption>D6: 50 hPa polar-cap temperature anomaly against the 100 hPa heat flux of the previous 40 days. The '
                 'slope is how strongly the vortex warms for a given wave forcing.</figcaption></figure>'
                 '<figure><img src="variability_age_wstar.png" alt="Tropical age anomaly against w* anomaly"><figcaption>D7: monthly '
                 'tropical age anomaly at 55 hPa against the 70 hPa upwelling anomaly of the previous three months.</figcaption></figure>'
                 '</div><figure class="col"><img src="variability_seasonal.png" alt="Seasonal cycle of tropical w* at 70 hPa">'
                 '<figcaption>D4: seasonal cycle of tropical (15S&ndash;15N) w* at 70 hPa.</figcaption></figure>')
        H.append(_metric_table(S, names, "D") + '</section>')

    H.append(open(os.path.join(rep, "notes.html")).read() if os.path.exists(os.path.join(rep, "notes.html")) else "")
    H.append('</div>')
    H.append("""<script>
document.querySelectorAll('.tabs button').forEach(function(b){b.addEventListener('click',function(){
  var s=b.dataset.sec;document.querySelectorAll('.tabs button[data-sec="'+s+'"]').forEach(function(x){x.setAttribute('aria-selected',x===b?'true':'false')});
  document.querySelectorAll('.pane[data-sec="'+s+'"]').forEach(function(p){p.hidden=p.dataset.run!==b.dataset.run});});});
</script>""")
    open(os.path.join(rep, "index.html"), "w").write("\n".join(H))
    print("wrote", os.path.join(rep, "index.html"))


def _metric_table(S, names, g):
    key = "D_metrics" if g == "D" else "metrics"
    first = S[names[0]][key]
    rows = []
    for i, m in enumerate(first):
        if m["group"] != g:
            continue
        cells = "".join(f'<td class="num">{fmt(S[n][key][i]["model"])} {pill(S[n][key][i]["err"])}</td>' for n in names)
        rows.append(f'<tr><td><b>{m["id"].split("-")[0]}</b> {html.escape(m["label"])}</td><td class="num">{fmt(m["ref"])}</td>{cells}</tr>')
    head = "".join(f'<th class="num">{run_tag(n)}</th>' for n in names)
    return (f'<h3>Scores: {GROUPS[g].lower()}</h3><div class="tablewrap"><table><thead><tr><th>Metric</th><th class="num">Reference</th>'
            f'{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


if __name__ == "__main__":
    main()
