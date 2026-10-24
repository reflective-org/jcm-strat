# Success metrics for stratospheric tracer transport: P20b, AL7, L0, LAL7

**Purpose (Susanne, 2026-10-23):** one fixed yardstick for "is the stratospheric tracer transport right", applied the same way to
every run. Metric groups, bounds and references were chosen on 2026-10-23: age of air (A), residual circulation (B), polar vortex
(C); **moderate** bounds (about the size of the CLaMS - WACCM6 disagreement); w* scored against WACCM6, ERA5 shown; a pass/fail
table plus one combined score. Computed by `scripts/success_metrics.py` (reusable for any run), raw scores in `success/raw/`.

## The runs

| run | T_eq correction (Phase 22) | ERA5 nudging top |
|---|---|---|
| P20b | none | 400 hPa everywhere |
| AL7 | extratropics, 400-1 hPa | 400 hPa everywhere |
| L0 | none | 150 hPa tropics -> 400 hPa extratropics (Phase 23) |
| LAL7 | extratropics, 400-1 hPa | 150 hPa tropics -> 400 hPa extratropics |

All: dry 13d physics + fixed Lott-Miller, bottom levels nudged, QBO nudged, T63L95. Window **2006-2007**; AL7, L0 and LAL7 are
2005-2007 restarts from P20b's end-of-2004 state, so their clocks carry P20b's 1990-2004 history.

## Metrics and bounds

| | metric | reference | bound |
|---|---|---|---|
| A1 | tropical (10S-10N) entry age at 55 hPa, `aoa150` | WACCM6 REF-D1 entry age | +- 0.25 yr |
| A2 | `aoa150` vs CLaMS (ERA5-driven) minus CLaMS' own tropical 150 hPa age; RMSE over 100-5 hPa, abs(lat) <= 80 | CLaMS v3.1 | < 0.4 yr |
| A3 | age step from the tropics to 50-70 deg at 55 hPa (tropical pipe / in-mixing) | CLaMS | +- 0.5 yr |
| A4 | tropical transit time 70 -> 10 hPa (deep-branch ascent) | CLaMS 3.0, WACCM6 2.5 yr | 2.3-3.2 yr |
| B1 | tropical (15S-15N) annual w* at 100, 70, 50, 30, 10 hPa | WACCM6 (ERA5 shown) | factor 1.35 each |
| B2 | annual upward mass flux at 100 and 70 hPa | WACCM6 (ERA5 shown) | +- 20 % |
| C1 | winter jet maximum at 50 and 10 hPa (DJF north, JJA south): strength and latitude | ERA5, same months | +- 5 m/s, +- 4 deg |
| C2 | winter polar-cap (60-90) T bias at 50 hPa | ERA5, same months | +- 2 K |

Each metric's error is divided by its bound (for w* and mass flux, the log ratio by the log of the factor): **✅ <= 1, ⚠️ <= 1.5,
❌ > 1.5**. The **combined score** is the mean error within each group, then the mean of the three groups (lower is better; <= 1
means inside the bounds on average). References: CLaMS 2005-2009 mean, WACCM6 entry age 2005-2009, WACCM6 TEM 1996-2014, ERA5 TEM
1996-2001 (the years on disk), ERA5 winds and temperatures for 2006-2007.

## Results

| metric | reference | P20b | AL7 | L0 | LAL7 |
|---|---|---|---|---|---|
| **A1** entry age 55 hPa tropics [yr] | 1.11 | ✅ 1.14 | ✅ 0.90 | ⚠️ 0.84 | ❌ 0.64 |
| **A2** 2-D age RMSE vs CLaMS [yr] | 0 | ⚠️ 0.42 | ❌ 0.73 | ❌ 0.62 | ❌ 1.00 |
| **A3** age step tropics -> 50-70 deg, 55 hPa [yr] | 2.79 | ✅ 2.48 | ⚠️ 2.14 | ✅ 2.52 | ⚠️ 2.14 |
| **A4** transit 70 -> 10 hPa [yr] | 2.3-3.2 | ✅ 2.36 | ✅ 2.35 | ⚠️ 2.20 | ⚠️ 2.21 |
| **B1** w* 100 hPa [mm/s] | 0.40 (ERA5 0.44) | ❌ 0.13 | ❌ 0.16 | ❌ 0.17 | ❌ 0.18 |
| **B1** w* 70 hPa | 0.21 (ERA5 0.25) | ✅ 0.20 | ✅ 0.24 | ✅ 0.20 | ✅ 0.25 |
| **B1** w* 50 hPa | 0.20 (ERA5 0.27) | ⚠️ 0.28 | ⚠️ 0.31 | ⚠️ 0.30 | ❌ 0.33 |
| **B1** w* 30 hPa | 0.26 (ERA5 0.32) | ✅ 0.32 | ✅ 0.31 | ✅ 0.34 | ✅ 0.32 |
| **B1** w* 10 hPa | 0.47 (ERA5 0.37) | ✅ 0.38 | ✅ 0.40 | ✅ 0.43 | ✅ 0.42 |
| **B2** mass flux 100 hPa [10^9 kg/s] | 10.9 (ERA5 12.3) | ✅ 9.1 | ✅ 9.7 | ✅ 9.7 | ✅ 9.5 |
| **B2** mass flux 70 hPa | 6.05 (ERA5 6.0) | ✅ 6.4 | ✅ 7.2 | ✅ 6.9 | ✅ 7.2 |
| **C1** jet NH 50 hPa [m/s] | 17.6 | ✅ 15.1 | ✅ 19.0 | ✅ 16.8 | ⚠️ 22.7 |
| **C1** latitude [deg] | 58.8 | ❌ 51.3 | ✅ 58.8 | ❌ 47.6 | ✅ 58.8 |
| **C1** jet NH 10 hPa [m/s] | 25.9 | ⚠️ 18.8 | ✅ 25.8 | ❌ 18.2 | ⚠️ 31.6 |
| **C1** latitude [deg] | 64.4 | ❌ 55.0 | ✅ 66.2 | ❌ 56.9 | ✅ 66.2 |
| **C1** jet SH 50 hPa [m/s] | 46.4 | ❌ 38.8 | ✅ 46.2 | ⚠️ 41.2 | ✅ 47.2 |
| **C1** latitude [deg] | -56.9 | ✅ -58.8 | ✅ -56.9 | ✅ -55.0 | ✅ -55.0 |
| **C1** jet SH 10 hPa [m/s] | 74.1 | ❌ 57.3 | ✅ 75.4 | ❌ 60.2 | ✅ 77.6 |
| **C1** latitude [deg] | -56.9 | ✅ -58.8 | ✅ -58.8 | ✅ -56.9 | ✅ -56.9 |
| **C2** polar-cap T bias 50 hPa N [K] | 0 | ❌ -3.2 | ✅ +0.1 | ⚠️ -2.4 | ✅ -1.1 |
| **C2** polar-cap T bias 50 hPa S [K] | 0 | ⚠️ +2.9 | ✅ +0.2 | ✅ +1.4 | ✅ -0.7 |

| | P20b | AL7 | L0 | LAL7 |
|---|---|---|---|---|
| A age of air, mean error | **0.66** | 1.21 | 1.09 | 1.72 |
| B residual circulation, mean error | 1.11 | 1.10 | **0.99** | 1.08 |
| C polar vortex, mean error | 1.50 | **0.17** | 1.25 | 0.49 |
| **combined score** | 1.09 | **0.82** | 1.11 | 1.10 |
| passed / 21 | 11 | **17** | 10 | 13 |

## What it says

1. **AL7 is the best run overall** (0.82, 17 of 21): the vortex is essentially solved (C 0.17) with the circulation unchanged.
   Its weakness is the age of air.
2. **Every change makes the stratospheric air younger, and age is now the binding constraint.** The mean age bias against CLaMS
   is -0.14 yr for P20b, -0.47 for L0, -0.55 for AL7 and -0.84 for LAL7. P20b, the run that fails the vortex, has the best ages.
   Correcting the vortex (AL7) speeds up transport into the extratropics (A3 step 2.48 -> 2.14 yr); nudging the tropical upper
   troposphere (L0) speeds up the tropical ascent (A1, A4).
3. **w* at 100 hPa fails in every run** (0.13-0.18 against 0.40): the shallow branch at the tropopause is under half of WACCM6's
   and ERA5's. The 100 hPa mass flux nevertheless passes (9.1-9.7 against 10.9), so the upwelling within 15 deg of the equator is
   too weak while the total is nearly right - presumably spread over a wider band (not checked); 50 hPa w* is ~50 % too strong in all four (the deep branch makes up for it).
4. **The Phase 23 nudging top does not pay off on these metrics.** L0 vs P20b: B improves slightly (1.11 -> 0.99), C slightly
   (1.50 -> 1.25), A gets worse (0.66 -> 1.09), combined unchanged (1.09 -> 1.11). LAL7 vs AL7: worse in A and C, combined 0.82 ->
   1.10.

## Caveats

- **The two age references disagree.** At 55 hPa, 50-70 deg, CLaMS' entry age is 4.0 yr and WACCM6's 3.4 yr. A2 and A3 use CLaMS
  (the ERA5 age), so the runs look ~0.6 yr less young against WACCM6 in the extratropics.
- **Restart clocks.** AL7, L0 and LAL7 have three years of their own circulation on top of P20b's 15. Phase 22 found 3-year and
  20-year ages within ~0.1 yr; deep-stratosphere ages could still drift a little younger with longer runs.
- **Two years** (2006-2007), so the jets carry interannual noise of a few m/s; the jet latitude is on the T63 grid (~1.9 deg).
- **ERA5 w*** is for 1996-2001, not 2006-2007 (only those years are on disk); it is shown, not scored.

## Suggested next step (not run)

The vortex is solved by AL7; the open problem is that air is too young once the vortex is right. The candidate from Phase 22 fits
this: **AL7 with the correction tapered further away from the tropics**, to recover the A3 step (and A1) while keeping C. Scoring it
takes one 3-year restart and `scripts/success_metrics.py`.

**Rerun the table:** aggregates holding only the window's years, then
`bash scripts/memcap.sh -m 96G -- .venv/bin/python scripts/success_metrics.py OUTDIR NAME=runs/<agg> ...` (about 20 min per run).
