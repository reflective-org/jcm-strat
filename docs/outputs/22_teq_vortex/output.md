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
