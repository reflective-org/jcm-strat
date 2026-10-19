# Phase 22 — equilibrium-temperature optimisation for the stratospheric vortex

**Goal (Susanne, 2026-10-16):** "getting the polar vortex right at around 50 hPa is essential". Iterate on the equilibrium
temperature (T_eq) of the dry dycore so that the lower and middle stratosphere comes closest to ERA5. Use Todd Mooring's iterative
method; definitely re-run the Phase 17 T_e correction on the p20b setup, applied only outside the tropics and with a shorter
relaxation time at the polar cap. GPUs 0, 1 and 2; at most 55 hours (deadline **Mon 2026-10-19 00:24 PDT**,
`runs/p22_deadline`). Run unattended, document everything.

## Starting point

P20b (`runs/p20bt_20yr`): dry 13d physics (JFV2013 relaxation + Hines + fixed Lott-Miller), L95 + cubic, ERA5 nudging below
400 hPa including the bottom levels. Scored on 2005-04..2007-12 against ERA5 (same months):

| | P20b | ERA5 |
|---|---|---|
| u RMSE 100-10 hPa, abs(lat) >= 30 | 7.80 m/s | |
| jet maximum 50 hPa, DJF north | 15 m/s @ 51N | 17 @ 59N |
| jet maximum 50 hPa, JJA south | 39 m/s @ 59S | 47 @ 57S |
| jet maximum 10 hPa, DJF north / JJA south | 19 @ 55N / 58 @ 59S | 26 @ 62N / 76 @ 57S |
| polar-cap T bias at 50 hPa, winter | north -2.9 K, south +2.8 K | |

From the 1990-1994 vortex comparison (`../20_sso_fixed/p20b_extension/vortex_1990-1994`): the northern weakness is mostly the
Lott-Miller drag (19d without it: 29 vs P20b 17 m/s at 10 hPa); the southern one is the dry setup itself (59 vs 57, ERA5 75).

## Method

**Mooring & Linz / Chang (2006).** Mooring & Linz's idealized GCM (GFDL dry core, T42L72, JFV2013 radiative damping times,
Held-Suarez below 100 hPa, realistic orography) generates T_eq "using an iterative algorithm (Chang 2006, see also Wu and Reichler
2018) that attempts to make the time mean temperature field of the model reproduce a user-specified three-dimensional input
climatology" (poster `~/docs/refs/mooring_linz_final.pdf`). The full papers are behind paywalls; the update rule comes from Wu &
Reichler's published code (`github.com/ZhengWinnieWu/WR_simpleGCM`, `correct_teq.m`, line 148):

    Teq_new = Teq_old - 2/3 * (T_model - T_obs)        pointwise, 3-D, monthly, no smoothing, clamped 100-400 K; ~31 iterations

Phase 17's `teq_correction.py` is the same fixed-point idea (alpha 0.7) on zonal means, with 1-2-1 smoothing, 100-1 hPa only.

**Iteration protocol** (`scripts/p22_track.sh`). Every iteration restarts from P20b's end-of-2004 state (the 1990-2004 segments
are links to P20b's, so the age clocks are 15 years old) and runs 2005-2007 with the current correction; the window
2005-04..2007-12 is scored against ERA5 for the same months (`scripts/teq_score.py`) and gives the next cumulative correction
(`scripts/teq_update.py`). A track stops after 8 iterations, when two iterations in a row gain < 0.1 m/s, or at the deadline.
Then `scripts/p22_final.sh` reruns the track's best iteration 1990-2009 from the 1989-12 spin-up (as P20b) and makes the vortex,
seasonal age/wind and age-vs-CLaMS diagnostics for 2005-2009.

**Ranking metric:** `u_ls_ext`, the RMSE of monthly zonal-mean u over 100-10 hPa poleward of 30 deg (thermal wind makes the
vortex a temperature-gradient problem; the 50 hPa jet maximum and the polar-cap T are reported alongside). Guards reported for
every run: the upper stratosphere (u 10-1 hPa), tropical w* 70-30 hPa vs ERA5 (Phase 17's full-domain correction weakened the
shallow branch), and aoa150 at 55 hPa.

## Tracks

| track | GPU | recipe |
|---|---|---|
| A | 0 | Phase 17 correction on P20b, **extratropics only** (zero at abs(lat) <= 25, full >= 35), 100-1 hPa, smoothed, alpha 0.7 |
| AL | 0 | A, with the correction reaching down to 400 hPa (lowermost extratropical stratosphere; the 100-400 hPa layer is neither nudged nor JFV-controlled and sets the 50 hPa wind through thermal wind) |
| B | 1 | A + **polar-cap tau <= 10 d** poleward of 60 deg (blend from 50 deg; JFV has 25-40 d in the lower polar stratosphere) |
| B5 | 1 | A + polar-cap tau <= 5 d |
| C | 2 | **Chang / Mooring & Linz on zonal means**: pointwise, all latitudes, 400-1 hPa, alpha 2/3, no smoothing |
| C3 | 2 | **Chang / Mooring & Linz in 3-D** (zonally varying T_eq) against ERA5 3-D monthly means (CDS) |
| finals | 0/1/2 | best iteration of each track, 1990-2009 from spin-up |

Results: `leaderboard.md` (updated after every score), `runlog.md` (every step), `scores/*.json`, `corrections/*.nc`,
`final/<track>_final/`. Decisions: `decisions.md`.

## Results (written 2026-10-19)

Scores on 2005-04..2007-12 against ERA5 for the same months (full table in `leaderboard.md`). `w_logerr` = mean abs(log(w*/w*_ERA5)),
tropics, 70-30 hPa (lower is better); ages are aoa150 at 55 hPa.

| run | u RMSE 100-10 hPa, abs(lat) >= 30 [m/s] | jet 50 hPa N / S [m/s] (ERA5 17 / 47) | w_logerr | age tropics / 50-70N / 50-70S [yr] (CLaMS tropical entry 1.24) |
|---|---|---|---|---|
| P20b (no correction) | 7.80 | 15 / 39 | 0.08 | 1.10 / 3.65 / 3.57 |
| A2 (Phase 17 correction, extratropics, 100-1 hPa) | 7.04 | 12 / 41 | 0.11 | 1.13 / 3.78 / 3.56 |
| **AL7** (A down to 400 hPa) | 3.84 | 19 / 46 | **0.07** | **0.93** / 3.11 / 2.74 |
| B0 (A + polar-cap tau <= 10 d, iteration 0) | 6.89 | 16 / 45 | 0.09 | 1.01 / 3.31 / 3.28 |
| B52 (A + polar-cap tau <= 5 d) | 5.36 | 17 / 45 | 0.09 | 1.01 / 3.39 / 3.13 |
| C5 (Chang / Mooring & Linz, zonal, all latitudes, 400-1 hPa) | 3.48 | 19 / 47 | **1.27** | 1.21 / 3.26 / 2.55 |
| C37 (the same in 3-D) | 3.49 | 19 / 46 | not computed | 1.30 / 3.23 / 2.62 |

1. **Option 1 as specified (100-1 hPa) barely moves the vortex**: u RMSE 7.80 -> 7.04 m/s and the 50 hPa jets stay weak, although
   the polar-cap temperatures are fixed. The 100-400 hPa layer is neither nudged nor JFV-controlled, and the 50 hPa wind is the
   thermal-wind integral through it.
2. **Extending the extratropical correction to 400 hPa (AL) fixes the 50 hPa vortex** (19 / 46 m/s against 17 / 47) and keeps the
   tropical upwelling (w_logerr 0.07, as P20b), because the tropics are not corrected. Its cost is a **too-young tropical entry age**
   (0.93 yr against P20b 1.10 and CLaMS 1.24); the extratropical ages get younger too (3.11 / 2.74).
3. **Option 2 (shorter polar-cap tau)** fixes the cap temperatures but the winds stay behind AL's (5 d: 5.36 m/s; 10 d: no gain over A).
4. **The Mooring & Linz iteration gives the best winds and temperatures (T 1.0-1.1 K) but breaks the tropical upwelling**
   (w_logerr 1.27 for C5) because it also corrects the tropics; not usable for transport in this form.
5. **The 3-year iterations are representative.** Where a 20-year rerun from spin-up exists, it reproduces the short run:

   | | u RMSE, 3 yr -> 20 yr | jet 50 hPa N/S | age tropics / 50-70N / 50-70S |
   |---|---|---|---|
   | A2 -> A_final | 7.04 -> 7.07 | 12/41 -> 11/41 | 1.13/3.78/3.56 -> 1.12/3.77/3.55 |
   | B52 -> B5_final | 5.36 -> 5.37 | 17/45 -> 17/45 | 1.01/3.39/3.13 -> 0.99/3.31/3.02 |
   | C37 -> C3_final | 3.49 -> 3.52 | 19/46 -> 19/46 | 1.30/3.23/2.62 -> 1.30/3.10/2.51 |

   The winds settle within months; the tropical 55 hPa age agrees to 0.02 yr, the extratropical ages within ~0.1 yr (slightly
   younger at 20 yr). An AL rerun would therefore most likely only confirm AL7.

**Incomplete runs.** `AL_final` (reached 2002) and `C_final` (reached 1990) both stopped on 2026-10-17 at 13:05 PDT with no model
error; a restart on 2026-10-19 reported "Disk quota exceeded" on /data, the likely cause. Not rerun (Susanne, 2026-10-19: point 5 makes
them low value). `B_final` used the correction of iteration B52 with tau <= 10 d: `p22_final.sh` picks the best `B<digits>` score,
which also matches the B5 track's files, and the B track itself stopped after B0. So `B_final` is not a B-track result.

**Verdict.** AL is the only correction that fixes the 50 hPa vortex without damaging the tropical upwelling, but it makes the
tropical air at 55 hPa too young. Suggested next step (Susanne decides, nothing run): AL with the correction shrunk further toward
the tropics, to see whether the entry age returns without losing the jets. The 3.7 TB of iteration runs (`runs/p22_[ABC]*_2005-2007`)
are kept until Susanne decides.
