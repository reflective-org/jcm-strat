# Phase 29 — LQBO10d: 10-day QBO nudging with the tropical ERA5 nudging up to 150 hPa

**Goal (Susanne, 2026-11-08):** one more run "like the QBO10 run but with nudging up to 150 hPa in the tropics". When
asked, she chose QBO10d over QBO30 as the base. The question: do the gentler QBO nudging and the higher tropical
nudging combine?

**Configuration.** LQBO10d = QBO10d with L0's ERA5 nudging top.
- Nudging top: experiment `p23_lattop`, which nudges below 150 hPa in the tropics and below 400 hPa in the
  extratropics (Phase 23).
- Temperature correction: AL7h's (`te_correction_file=.../25_al7_half/corrections/AL7h.nc`, `te_correction_mode=total`).
- QBO nudging: 10-day timescale (`++physics.terms.held_suarez.qbo.tau_days=10.0`), as in QBO10d.
- The run restarts from P20b's end-of-2004 state and covers 2005-2010, as all the other restart runs do. It is scored
  on 2006-2010 beside the eight Phase 28 runs, on groups A-C and on D.

**Run.**
- `scripts/phase29_run.sh` ran in tmux `strat_p29_run` from 2026-11-08 16:14 to 19:17 PST (log `runs/p29_run.log`).
  - The chain took 90 minutes on GPU 0. No segment hit a health stop.
  - The diagnostics ran on CPU under `memcap.sh`.
  - The daily zonal means were computed on GPU 0.
  - Group D for all nine runs was scored against the CDS ERA5 reference from Phase 28.
- The script then ran `scripts/phase29_report.sh` and committed (d88e7e6).
- The eight earlier runs reproduce their Phase 27 (A-C) and Phase 28 (D) numbers exactly.

Outputs:
- `success_0610/success_table.md`: groups A-D for all nine runs.
- `variability_table.md`, `variability.json` and the `variability_*.png` figures: group D.
- `w0610/LQBO10d/`: vortex, seasonal and circulation diagnostics.
- `report/`: scorecard v8.

## Result (2006-2010)

| | QBO10d | **LQBO10d** | QBO30 | L0 | AL7h |
|---|---|---|---|---|---|
| A age of air, mean err | 1.11 | **1.71** | 1.05 | 1.18 | 1.10 |
| B residual circulation, mean err | 0.90 | **0.77** | 0.88 | 1.02 | 1.05 |
| C polar vortex, mean err | 0.95 | **0.53** | 0.71 | 1.25 | 0.66 |
| **combined (A-C)** | 0.99 | **1.01** | **0.88** | 1.15 | 0.93 |
| passed / 21 | 14 | **13** | 16 | 10 | 14 |
| D variability, mean err | **1.04** | **1.61** | 1.09 | 1.23 | 1.22 |
| D passed / 13 | 8 | **5** | 7 | 5 | 8 |

Selected metrics (reference in brackets):

| metric | QBO10d | LQBO10d |
|---|---|---|
| A1 entry age 55 hPa tropics [yr] (CLaMS 1.11) | 0.95 | 0.69 |
| A2 2-D age RMSE vs CLaMS [yr] | 0.61 | 0.91 |
| A4 transit 70 -> 10 hPa [yr] (2.3-3.2) | 2.16 | 1.93 |
| B1 w* 100 / 70 / 50 hPa [mm/s] (WACCM 0.40 / 0.21 / 0.20) | 0.17 / 0.20 / 0.26 | 0.21 / 0.21 / 0.27 |
| C1 NH jet 10 hPa [m/s, deg] (ERA5 25.2 at 62.5N) | 16.1 at 55.0N | 22.7 at 62.5N |
| C1 SH jet 10 hPa [m/s] (ERA5 71.9) | 65.6 | 69.5 |
| C2 polar-cap T bias 50 hPa N / S [K] | -0.48 / 1.55 | -2.35 / 0.18 |
| D3 NH major SSWs (ERA5 8) | 4 | 2 |
| D4-w w* 70 hPa annual cycle [mm/s] (ERA5 0.19) | 0.18 | 0.13 |
| D6 heat flux -> polar-cap T slope N / S (ERA5 0.97 / 0.77) | 0.47 / 0.64 | 0.51 / 0.49 |
| D7 age vs w* slope [yr per mm/s] (CLaMS -4.52) | -2.40 | -1.65 |
| SAO amplitude at 1 hPa [m/s] (ERA5 32.4) | 12.9 | 26.1 |

## Findings

1. **The two changes do not combine into a better configuration.**
   - LQBO10d scores 1.01 on A-C, against 0.99 for QBO10d, and 1.61 on D, against 1.04.
   - **QBO30 stays the best configuration** (0.88 on A-C, 1.09 on D).
2. **Circulation and vortex improve.**
   - Group B is the best of any run so far (0.77).
     - w* at 100 hPa rises to 0.21 mm/s, the highest of all runs. It is still only half of WACCM6's 0.40.
     - w* at 50 and 70 hPa stays where QBO10d had it.
   - Group C improves from 0.95 to 0.53.
     - The northern jet at 10 hPa moves back to ERA5's latitude and nearly to its strength: 22.7 m/s at 62.5N,
       against QBO10d's 16.1 m/s at 55N.
     - The southern 10 hPa jet is within 3 m/s of ERA5.
     - The cost is a colder northern polar cap at 50 hPa (-2.35 K).
3. **The air gets much younger.** This is the same trade as L0 against P20b and LAL7 against AL7 (Phase 23).
   - The tropical entry age at 55 hPa falls from 0.95 to 0.69 years (CLaMS 1.11).
   - The 2-D age RMSE rises from 0.61 to 0.91 years.
   - The 70 -> 10 hPa transit shortens to 1.93 years (fails).
   - Group A goes from 1.11 to 1.71, which by itself outweighs the gains in B and C.
4. **Group D gets worse, and it fails the way L0 does.**
   - Only 2 NH major SSWs, the fewest of any run (ERA5 8).
   - The annual cycle of tropical w* at 70 hPa shrinks to 0.13 mm/s, exactly as in L0 (ERA5 0.19). So this is an effect
     of the 150 hPa nudging.
   - The southern daily wind spread (D2-S 2.98 against 5.25 m/s) and the southern heat-flux response (D6-S 0.49 against
     0.77) both fail, where QBO10d passed.
   - The tropical age responds even more weakly to w* (D7 -1.65 against QBO10d's -2.40).
   - The northern response to the heat flux is still half of ERA5's (D6-N 0.51), though better correlated (r 0.73
     against 0.56).
5. **Side effect at the top.** The semiannual oscillation at 1 hPa recovers from QBO10d's 12.9 to 26.1 m/s (ERA5 32.4),
   as it did from AL7h to L0 (16.1 to 25.2). Below 3 hPa the QBO is unchanged (std at 50 hPa 10.4 against 10.6 m/s,
   ERA5 11.3).

**Caveats.**
- LQBO10d restarts from P20b at the end of 2004, as the other restart runs do, so its age keeps drifting younger after
  the restart (Phase 26). This applies equally to QBO10d and L0, so the comparison is fair, but the absolute ages are
  biased young.
- Five winters is a small sample for D1 and D3. See Phase 28.

## Relative scorecard (Susanne, 2026-11-09)

Susanne asked for a second scorecard with every metric in relative terms, and with QBO30 left out because its QBO is
unacceptable. It was made with `scripts/relative_scores.py` and written to `relative/`, and it is published as a
separate page: https://claude.ai/artifact/2kndRHGuQKhXBQSXS1ZzDB.
- Each metric's deviation is model / reference - 1. Its error is that deviation divided by one common tolerance of
  25 %, with the old pass / near / fail thresholds.
- A4 is taken against the middle of its 2.3-3.2 yr range.
- Four kinds of metric have no meaningful relative form, and keep their absolute bounds (Susanne's choice):
  - A2, the 2-D age RMSE;
  - C1, the jet latitudes;
  - C2, the polar-cap T bias;
  - D4, the final-warming dates.

| | P20b | AL7 | AL7h | AL7t | L0 | LAL7 | QBO10d | LQBO10d |
|---|---|---|---|---|---|---|---|---|
| combined (A-C) | 0.90 | 0.84 | **0.81** | 0.84 | 1.00 | 1.09 | 0.86 | 0.90 |
| passed / 21 | 12 | **17** | **17** | 14 | 13 | 15 | 15 | 13 |
| D variability | 1.34 | 1.27 | 1.10 | 1.28 | 1.17 | 1.46 | **0.92** | 1.39 |

- In relative terms AL7h is the best configuration on A-C, with AL7 and AL7t close behind.
- QBO10d is the best on D and the only run inside the tolerance on average there.
- The ranking is the same as in the absolute scorecard once QBO30 is removed. Every score is lower because a 25 %
  tolerance is looser than most of the absolute bounds.
