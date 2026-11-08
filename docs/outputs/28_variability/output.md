# Phase 28 — success-metrics group D: variability, SSWs, seasonal cycle and two relations

**Goal (Susanne, 2026-11-05):** add year-to-year and daily spread, SSW counts, the seasonal cycle, daily variability and
two relations to the scoring. The two relations are the heat flux -> vortex relation (the dynamics) and age vs w* (the
transport). Holton-Tan was left out: five years is about two QBO cycles, and our QBO is nudged. Susanne also asked for
D3 to give only the number of SSWs, and for D1 to use a latitude band around 60 deg. D is its own group: **the combined
score stays the mean of A, B and C**, so every earlier score is unchanged.

**Method.**
- **Model.** `scripts/daily_zm.py` (jax on GPU 0) reduces every 6-hourly frame of the eight scorecard runs (2006-2010
  aggregates `runs/p26_<run>_0610`) to zonal means of u, v, T and theta, the eddy covariance v'theta' (stride 1,
  Phase 15) and the age clocks. It then averages each day's four frames into `cache/variability/<run>_0610.npz`.
- **ERA5.** `scripts/fetch_era5_daily_zm.py` downloads ERA5 from the Copernicus CDS (6-hourly, 2.5 deg) and reduces it
  the same way: 17 levels from 1 to 250 hPa for 2006-2010, and 10/50/100 hPa for the 1990-2022 context.
- **Age.** The age reference is CLaMS v3.1 (ERA5-driven), monthly.
- **Scoring.** `scripts/variability_score.py` computes the metrics below. Every anomaly is taken against the dataset's
  own seasonal climatology over the window. `success_metrics.py --variability` adds D to the A-C table.
- **Runs.**
  - Model reduction: `scripts/phase28_run.sh`, 2026-11-05, about 25 min per run (b5cbf9a).
  - ERA5 download and rescore: `scripts/phase28_rescore.sh` (tmux `strat_p28_rescore`, CPU only, under `memcap.sh`),
    2026-11-07 15:26 to 2026-11-08 15:48 PST (b1cdb71).
  - The CDS queue was the bottleneck: requests had to be split into half-months and quarters, and each waited minutes
    to hours. The machine rebooted on Nov 8; finished pieces were kept and the run resumed.
- **Check.** ERA5 u at 60N, 10 hPa matches the independently fetched `cache/era5_ref/era5_u10hPa_daily_2006-2009` exactly
  (r 1.000, same std, no bias).

**Correction to the first version (b5cbf9a).** The first ERA5 reference came from the L95 nudging windows
(`cache/era5/wb2_*`). They are WeatherBench2 data, which stops at 50 hPa: every level above is a copy of 50 hPa. Its
D1-D4 and D7 references were therefore wrong. Only D5 and D6 were valid, and they barely change here. The model numbers
were never affected. The conclusions of that version about early final warmings and a half-size w* annual cycle were
artefacts and are withdrawn. The nudging itself is unaffected, because it acts only below 150/400 hPa.

| id | metric | reference | bound |
|---|---|---|---|
| D1 | year-to-year std of the winter-mean u at 10 hPa, 55-65 deg (DJF N, JJA S) | ERA5, same winters | factor 1.5 |
| D2 | daily std of the winter u anomaly at 60 deg, 10 hPa | ERA5, same days | factor 1.35 |
| D3 | number of NH major SSWs (Charlton-Polvani, u 60N 10 hPa) | ERA5, same winters | +- 1 |
| D4 | final-warming date at 60 deg, 10 hPa (Black & McDaniel: first easterly crossing after which u stays below 5 m/s), springs both have | ERA5 | +- 10 days |
| D4-w | annual-cycle amplitude of tropical (15S-15N) w* at 70 hPa | ERA5 | factor 1.35 |
| D5 | daily std of the 100 hPa eddy heat flux v'T', 45-75 deg, in winter | ERA5 | factor 1.35 |
| D6 | slope of the 50 hPa polar-cap (60-90) T anomaly on the trailing 40-day 100 hPa heat-flux anomaly (Jan-Mar N, Jul-Oct S, pooled days; Newman et al. 2001) | ERA5 | factor 1.35 |
| D7 | slope of the monthly tropical age anomaly at 55 hPa (deseasonalised, detrended) on the trailing 3-month 70 hPa w* anomaly | CLaMS age / ERA5 w* | factor 1.5 |

Outputs:
- `variability_table.md`: the D table, the correlations and the ERA5 1990-2022 context.
- `success_0610/success_table.md`: groups A-D.
- `variability.json`.
- Figures:
  - `variability_vortex.png`: u at 60 deg, 10 hPa, daily, with the ERA5 SSWs.
  - `variability_heatflux.png`: D6 scatter and fits.
  - `variability_age_wstar.png`: D7.
  - `variability_seasonal.png`: tropical w* seasonal cycle.
- `report/`: scorecard v7.

## Result (2006-2010)

| | ERA5 / CLaMS | P20b | AL7 | AL7h | AL7t | L0 | LAL7 | QBO30 | QBO10d |
|---|---|---|---|---|---|---|---|---|---|
| D1 year-to-year std N / S [m/s] | 6.5 / 2.2 | 4.2 / 1.1 | 3.0 / 1.1 | 3.5 / 1.5 | 3.7 / 1.3 | 4.1 / 1.6 | 2.3 / 1.1 | 2.4 / 1.5 | 3.6 / 2.2 |
| D2 daily std N / S [m/s] | 15.0 / 5.3 | 10.0 / 3.6 | 11.1 / 3.3 | 11.4 / 3.8 | 8.9 / 3.5 | 9.9 / 3.2 | 12.6 / 3.0 | 10.7 / 3.9 | 10.4 / 3.9 |
| D3 NH major SSWs | 8 | 12 | 4 | 3 | 4 | 6 | 4 | 5 | 4 |
| D4 final warming N / S [days after 1 Mar / 1 Sep] | 44 / 90 | 36 / 76 | 52 / 87 | 44 / 85 | 53 / 87 | 47 / 85 | 57 / 97 | 46 / 85 | 46 / 86 |
| D4-w w* 70 hPa annual cycle [mm/s] | 0.19 | 0.17 | 0.20 | 0.20 | 0.21 | 0.13 | 0.16 | 0.18 | 0.18 |
| D5 heat-flux daily std N / S [K m/s] | 11.5 / 7.9 | 13.5 / 8.4 | 13.0 / 8.5 | 13.1 / 8.2 | 13.5 / 8.8 | 11.3 / 6.6 | 13.5 / 6.9 | 12.9 / 8.6 | 12.9 / 8.5 |
| D6 heat flux -> T slope N / S [K per K m/s] | 0.97 / 0.77 | 0.48 / 0.46 | 0.53 / 0.59 | 0.53 / 0.57 | 0.48 / 0.57 | 0.47 / 0.42 | 0.62 / 0.43 | 0.50 / 0.57 | 0.47 / 0.64 |
| D7 age vs w* slope [yr per mm/s] | -4.52 | -1.96 | -1.38 | -1.88 | -1.45 | -1.96 | -1.03 | -2.76 | -2.40 |
| **D mean err** | | 1.45 | 1.38 | 1.22 | 1.39 | 1.23 | 1.64 | 1.09 | **1.04** |
| D passed / 13 | | 4 | 6 | **8** | 6 | 5 | 5 | 7 | **8** |

The A-C scores and the combined score are unchanged from Phase 27: QBO30 0.88 is still the best.

**ERA5 checks.**
- The ERA5 SSWs in 2006-2010 are the six published events (21 Jan 2006, 24 Feb 2007, 22 Feb 2008, 24 Jan 2009,
  9 Feb 2010, 24 Mar 2010) plus two short follow-up reversals (11 Feb 2006, 14 Mar 2008).
- Over 1990-2022 the detector finds 22 events (0.67 per winter, the usual rate), including the quiet 1990s.
- The ERA5 final warmings are mid-April (N) and late November (S).
- The ERA5 tropical w* at 70 hPa runs from 0.31 mm/s in January to 0.13 mm/s in July.

**How much five winters scatter (ERA5 1990-2022).**
- **D3:** the number of SSWs in a 5-winter window ranges from 0 (1990-94) to 8 (2006-10), mean 3.6. **2006-2010 is the
  most active window on record.**
- **D1:** the 5-winter year-to-year std ranges from 4.4 to 13.0 m/s in the north and 1.7 to 3.9 m/s in the south.
- **D6:** over the 33 years it is 1.00 (N) and 1.14 (S).

## Findings

1. **The seasonal cycle is right.**
   - The final warmings at 10 hPa are within 10 days of ERA5 in almost every run. The exceptions are P20b, whose vortex
     breaks down 9 days early in the north and 14 days early in the south, and LAL7, which is 13 days late in the north.
   - The annual cycle of tropical w* at 70 hPa passes everywhere except L0 (0.13 against 0.19 mm/s).
2. **The stratosphere varies too little.**
   - The daily spread of the 10 hPa wind is too small in both hemispheres: D2-N 9-13 against 15 m/s, D2-S 3.0-3.9
     against 5.3 m/s.
   - The year-to-year spread is too small too, D1-N 2.3-4.2 against 6.5 m/s. In the south, AL7h, L0, QBO30 and QBO10d
     pass.
   - The corrected runs have 3-6 SSWs against ERA5's 8 in the same winters. P20b, with its weak vortex, has 12.
3. **The northern vortex responds only half as strongly to the wave forcing.** This is why it varies too little.
   - The waves coming up from the nudged troposphere are right: the heat-flux daily spread passes in every run (D5).
   - But the northern polar-cap temperature warms only about half as much per unit heat flux as in ERA5
     (D6-N 0.47-0.62 against 0.97), with a weaker correlation (0.52-0.75 against 0.81).
   - In the south the response passes in the corrected and QBO runs (0.57-0.64 against 0.77). It fails in P20b, L0 and
     LAL7 (0.42-0.46).
   - This is the main new deficit that groups A-C do not see. With the same waves, the model's northern vortex is too
     stiff, so it breaks down too rarely and swings too little.
4. **The tropical age responds too weakly to the upwelling.**
   - Every run has the right sign, but a slope 1.6-4.4 times shallower than CLaMS against ERA5 w* (-1.0 to -2.8 against
     -4.5 yr per mm/s). The QBO runs are closest (QBO30 -2.76, near).
   - The monthly w* variability is similar to ERA5's (std 0.026-0.035 against 0.041 mm/s). The difference is in the age:
     the model's deseasonalised tropical age at 55 hPa varies about three times less than CLaMS's (0.07-0.08 against
     0.23 yr).
   - Part of that may be the definitions. The model's age is the entry age (clock reset below 150 hPa). CLaMS's is the
     mean age from the surface, whose anomalies also carry upper-tropospheric and in-mixing variability.
5. **Ranking on D:** QBO10d 1.04, QBO30 1.09, AL7h 1.22, L0 1.23, AL7 1.38, AL7t 1.39, P20b 1.45, LAL7 1.64.
   - The two QBO runs score best on D.
   - QBO30 is best on A-C and second on D, so it stays the best overall configuration.
   - No run is inside the bounds on average. Every run fails D3, D6-N and D7.

**Caveats.**
- Five winters per hemisphere is a small sample, especially for D1 (std over 4-5 winters) and D3. The ERA5 ranges above
  show the scatter.
  - The tropospheric nudging gives the model the same waves as ERA5 (D5), so matching the same winters' events is a
    fair test.
  - But 2006-2010 was unusually active. 3-6 events would be normal for a 5-winter window.
- The restart runs keep drifting younger (Phase 26). That affects D7 only through a linear trend, which is removed.
- The ERA5 w* is computed on 17 levels with the top at 1 hPa, at 2.5 deg, from daily means of the 6-hourly eddy fluxes.
  The model's comes from its own 95 levels. Both use the same TEM code (`strat_circulation.py`).
