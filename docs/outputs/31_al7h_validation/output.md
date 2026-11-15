# Phase 31 — AL7h validation on out-of-sample years; AL7h 50-year and 1970-2022 chains

**Goal (Susanne, 2026-11-09):** a document that validates AL7h, the configuration chosen in Phases 22-29, using the
scorecard metrics.

Two changes were agreed before writing it:
1. **Separate what is imposed or tuned from what is emergent.**
   - Imposed: u, v and T below 400 hPa (ERA5 nudging), and the equatorial zonal wind (QBO nudging, tau 1 d).
   - Tuned: the T_e correction was fitted to ERA5 extratropical temperature, so C2 is tuned and C1 is constrained by
     thermal wind.
   - Emergent: age of air (A), the residual circulation (B), variability (D) and tropical temperature.
2. **Score out of sample.** The AL7h correction was fitted on 2005-04..2008-01, which overlaps the 2006-2010 scoring
   window. Susanne chose to "extend AL7h through 2019 and make both": a PDF in the repo and a page.

**The validation document is the main output of this phase.**
- PDF: `docs/outputs/jcm-strat_phase31_al7h_validation.pdf`
- Page: https://claude.ai/artifact/2TbAEtC5sdjwgs36TLMnWc
- Both are built by `scripts/make_phase31_report.py` from this directory. This record summarises the document and
  adds the two long chains that were run afterwards.

## Scoring scope (Susanne, 2026-11-10)

These changes apply to the validation document only; `scripts/success_metrics.py` and the Phase 24-30 scorecards are
unchanged.

- **Shown but not scored** (`UNSCORED` in `make_phase31_report.py`), so the score counts only what the model should
  get right:
  - winds at 10 hPa and above: the 10 hPa jets (C1-jet10), the vortex variability (D1, D2) and the final-warming dates
    (D4-fw);
  - the number of major SSWs (D3);
  - the heat-flux -> polar-cap T and age-w* relations (D6, D7);
  - age on the surface clock.
- **Age is scored on the 150 hPa clock only.**
- **A2 is now the RMSE of the 150 hPa clock against the WACCM6 REF-D1 2-D entry age for the same years**
  (`scripts/a2_waccm_age.py`; 100-5 hPa, |lat| <= 80, bound 0.4 yr).
  - The old A2 was against CLaMS shifted by its own tropical 150 hPa age. It is kept as a faded row.
  - Its error was mostly a uniform offset of about -0.5 yr, and WACCM6 shares that offset, so it came from the shift,
    not from the model.
- `sweep_score.py` takes `SCORE_REF_YEARS`, so the CLaMS and WACCM6 age references are always taken for the scored
  years.

## Runs

1. **Extension.** `scripts/phase31_extend.sh` continued the `p25_AL7h` chain through 2011-2019.
   - It ran on GPU 2 on 2026-11-09 from 18:07 to 20:27 PST: 140 minutes, no health stop.
   - Aggregates: `runs/p31_AL7h_1990_2019`, and `runs/p31_AL7h_1119` for 2011-2019.
2. **Validation pipeline.** `scripts/phase31_validate.sh` (tmux `strat_p31_validate`, log `runs/p31_run.log`) ran:
   - the diagnostics for both windows into `w0610/` and `w1119/`;
   - A-C into `success_0610/` and `success_1119/`, each with same-year references;
   - `a2_waccm.json`;
   - the daily zonal means;
   - group D against CDS ERA5 daily zonal means, fetched for 2011-2019 into `cache/variability_cds`.
3. **AL7h on 50 years, 1990-2039** (Susanne, 2026-11-13: "all 50 years need to be AL7h"). Script
   `scripts/phase31_50yr.sh`.
   - Same experiment as p20bt_50yr (`p20b_ext`, all tracers written, 6-hourly output) with the AL7h correction on every
     segment.
   - 31-day spin-up from ERA5 on 1989-12-01; tracers injected 1990-01-01.
   - After 2022, ERA5 is recycled (`ERA5_RECYCLE="2023 32"`): model years 2023-2039 are nudged to ERA5 1991-2007, and
     the QBO target is the ERA5 year.
   - Ran on GPU 2 from 2026-11-13 16:09 to 11-14 07:39 PST: 930 minutes, no health stop.
   - Output: `runs/p31_AL7h50_YYYY0101` (about 140 GB per year after compaction, 7.1 TB in total), aggregate
     `runs/p31_AL7h50_1990_2039`.
   - A first attempt that continued `p25_AL7h` beyond 2019 on top of P20b's 1990-2004 was stopped during 2029, because
     Susanne wanted AL7h on every year. Its segments `p25_AL7h_2020..2029` (410 GB) are still on disk.
4. **AL7h on 1970-2022, all real ERA5** (Susanne, 2026-11-14). Script `scripts/phase31_al7h70.sh`.
   - The WeatherBench2 ERA5 store covers 1959-01-01..2023-01-10, so 2022 is the last full year.
   - Same configuration as run 3, with a spin-up from 1969-12-01 and tracers injected 1970-01-01. There is no recycling
     and no matching run without AL7h.
   - Three streams feed the chain one year at a time:
     - the CDS monthly QBO reference for 1969-1988;
     - the CPU prefetch of the 1970-1989 nudging windows (memcap 200 G, retried; the 1985 prefetch failed once);
     - the GPU chain.
   - Ran on GPU 0 from 2026-11-14 07:54 to 11-15 04:59 PST: 1265 minutes for 53 years, no health stop.
     - Early years took about 18 minutes, later ones about 24; the cause was not checked.
   - Output: `runs/p31_AL7h70_YYYY0101` (7.4 TB), aggregate `runs/p31_AL7h70_1970_2022`.
   - Pre-1979 ERA5 assimilates no satellite soundings and is weaker. That falls mostly inside the roughly 10-year
     spin-up of the age clocks (p20bt_50yr).

**No analysis has been run on runs 3 and 4 yet.**

Outputs (this directory):
- `report/`: the page and its figures; `summary.png` is the per-metric overview.
- `success_0610/`, `success_1119/`: the A-C tables and `a2_waccm.json`.
- `variability_table.md` and `variability_*.png`: group D for 2011-2019.
- `w0610/`, `w1119/`: vortex, seasonal, QBO, TEM and temperature diagnostics.

## Result

Scored metrics only. Errors are in units of each metric's bound: 1 or less passes, 1.5 or less is near, above that
fails.

| group | class | 2006-2010 (in sample) | **2011-2019 (out of sample)** |
|---|---|---|---|
| A age of air (150 hPa clock) | emergent | 0.93 | **0.95** |
| B residual circulation | emergent | 1.05 | **1.03** |
| C polar vortex (50 hPa jets, polar-cap T) | C1 constrained, C2 tuned | 0.52 | **0.37** |
| **combined A-C** | | 0.83 | **0.78** |
| passed A-C | | 13 / 17 | **13 / 17** |
| D variability (D4-w, D5) | emergent | 0.25 | **0.26** |
| passed D | | 3 / 3 | **3 / 3** |

Selected metrics (reference for the same years in brackets):

| metric | 2006-2010 | 2011-2019 |
|---|---|---|
| A1 entry age 55 hPa tropics [yr] | 1.00 (1.10) | 1.02 (1.11) |
| A2 150 hPa clock vs WACCM6 2-D entry age, RMSE / bias [yr] | 0.32 / -0.07 | 0.32 / -0.08 |
| A3 age step tropics -> 50-70 deg, 55 hPa [yr] | 2.26 (2.84) | 2.18 (2.82) |
| A4 transit 70 -> 10 hPa [yr] (2.3-3.2) | 2.15 | 2.13 |
| B1 w* 100 / 50 hPa [mm/s] (WACCM6 0.40 / 0.20) | 0.14 / 0.29 | 0.14 / 0.29 |
| B2 mass flux 100 hPa [1e9 kg/s] (10.9) | 9.50 | 9.44 |
| C2 polar-cap T bias 50 hPa N / S [K] | -1.05 / 1.27 | -1.03 / 1.42 |
| *not scored:* NH jet 10 hPa [m/s] (ERA5 same years) | 18.5 (25.2) | 24.0 (29.0) |
| *not scored:* NH major SSWs (ERA5) | 3 (8) | 6 (4) |
| *not scored:* D6-N heat flux -> polar-cap T slope (ERA5) | 0.53 (0.97) | 0.65 (1.05) |
| *not scored:* D7 age vs w* slope (CLaMS) | -1.88 (-4.52) | -1.04 (-3.98) |

## Findings

1. **AL7h does as well out of sample as in sample.**
   - On 2011-2019, years the temperature correction never saw, it scores 0.78 on A-C, against 0.83 on 2006-2010, with
     13 / 17 passed in both.
   - The tuned polar-cap temperatures stay within 1.5 K of ERA5, so the correction is not overfitted to its fitting
     years.
2. **What the model gets right on its own:**
   - the entry age at 55 hPa;
   - the 2-D age field measured from 150 hPa (0.32 yr against WACCM6 in both periods);
   - w* at 70, 30 and 10 hPa;
   - the 70 hPa and 100 hPa mass flux;
   - the shape and seasonality of the Brewer-Dobson cells;
   - the latitude of both polar-night jets.
3. **The main scored failure is w* at 100 hPa: 0.14 mm/s against 0.40, in both periods.**
   - The 100 hPa mass flux passes (9.4 against 10.9), so the deficit is in the tropical core of the upwelling, not in
     the total.
   - Near the bounds: the tropics-to-midlatitude age step (A3, the tropical pipe is leakier than CLaMS), the 70 -> 10
     hPa transit (a little fast) and w* at 50 hPa (a little fast).
4. **Failures outside the score**, reported plainly in the document:
   - The tropical tropopause (100 hPa) is about 11 K too warm (203.4 against 192.1 K in DJF). That is consistent with
     the weak 100 hPa w*, and it is the same in both periods.
   - The tropical temperature errors stack vertically: about -6 K at 200-300 hPa, +11 K at 100 hPa, -6 K at 10-20 hPa
     and +7 to +10 K at 1-3 hPa.
   - On the surface clock, air at 100-70 hPa in the tropics and subtropics is 0.5-1.5 yr too old. Since the 150 hPa
     clock matches, that excess builds up below 150 hPa.
   - Both winter jets are 10-20 % weak at 10 hPa, and the winter subtropical jet near 200 hPa is 10-20 m/s weak.
   - The northern vortex varies too little.
   - The NH polar cap responds to the 100 hPa heat flux at half to two thirds of ERA5's rate.
   - Tropical age rises too slowly with upwelling (D7).
5. **The QBO follows ERA5 because it is nudged.** Its standard deviation at 10-50 hPa is within 0.8 m/s of ERA5. The
   SAO at 1 hPa is half of ERA5's amplitude (14.4 against 27.6 m/s).

**Caveats.**
- The SSW count is not comparable between the two windows. ERA5 has 8 major SSWs in 2006-2010 and 4 in 2011-2019, and
  five to nine winters are too few to read a count.
- The scoring scope above is the document's. The scorecards of Phases 24-30 score more metrics, so their numbers
  (AL7h 0.93 on 2006-2010) are not comparable with the 0.83 here.
- The 2006-2010 window is in sample by construction.

**Status.** The document is done (page v3, PDF in the repo). The 50-year and 1970-2022 chains are healthy and
compacted, and are waiting for analysis.
