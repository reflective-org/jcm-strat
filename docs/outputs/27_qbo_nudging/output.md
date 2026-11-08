# Phase 27 — lighter QBO nudging on AL7h (QBO30, QBO10d)

**Goal (Susanne, 2026-10-29):** would removing the QBO nudging help the lower stratosphere? Removing it is not an
option: Phase 12's QBO-off run weakened the lower-branch w* and aged the tropics, the 100 hPa deficit lies below the
nudging window, and without the nudging the model has no QBO at all. Two lighter-touch variants were tried instead, both on AL7h.

**Current QBO nudging** (the same in every scorecard run, `jcm_strat/qbo_nudging.py`): tropical zonal-mean u relaxed to
the ERA5 monthly mean, full weight at |lat| <= 15 deg and zero at 25 deg, from 90 to 1 hPa with a 0.35-decade log-p taper
(full weight from about 40 to 2.2 hPa), tau 1 d.

**Runs** (`scripts/phase27_run.sh`, tmux `strat_p27_run`, 2026-10-29 14:03-19:54 PDT, no health stops). Both runs are AL7h
(`p22_teq` + the AL7 correction at half amplitude), start from P20b's end-of-2004 state, and cover 2005-2010 (prefix `p27_*`):

| run | GPU | change from AL7h | what it means |
|---|---|---|---|
| QBO30 | 1 | `++qbo.p_bot_hpa=50 ++qbo.taper_decades=0.22` | full weight from about 30 hPa, none below 50 hPa; the narrower taper also moves the top of full weight from 2.2 to 1.7 hPa |
| QBO10d | 0 | `++qbo.tau_days=10` | same window, ten times weaker relaxation |

Scored on 2006-2010, as in Phase 26. The Phase 26 raw scores are copied in, so the table has all eight runs.

Outputs: `success_0610/` (score table), `w0610/<run>/` (diagnostics), `report/` (scorecard page, published as
version 6 of the scorecard artifact; rebuilt by `scripts/phase27_report.sh`; the QBO figures come from `scripts/qbo_compare.py`).

## Result (success metrics, moderate bounds, 2006-2010)

| | P20b | AL7 | AL7h | AL7t | L0 | LAL7 | **QBO30** | QBO10d |
|---|---|---|---|---|---|---|---|---|
| A age of air | 0.70 | 1.41 | 1.10 | 1.49 | 1.18 | 2.01 | 1.05 | 1.11 |
| B residual circulation | 1.13 | 1.08 | 1.05 | 1.06 | 1.02 | 1.06 | **0.88** | 0.90 |
| C polar vortex | 1.41 | 0.31 | 0.66 | 0.26 | 1.25 | 0.55 | 0.71 | 0.95 |
| **combined** | 1.08 | 0.94 | 0.93 | 0.94 | 1.15 | 1.21 | **0.88** | 0.99 |
| passed / 21 | 11 | 16 | 14 | 13 | 10 | 14 | **16** | 14 |

| metric | reference | AL7h | QBO30 | QBO10d |
|---|---|---|---|---|
| entry age 55 hPa tropics [yr] | 1.11 | 1.00 | 0.94 | 0.95 |
| 2-D age RMSE vs CLaMS [yr] | 0 | 0.62 | 0.61 | 0.61 |
| w* 100 / 70 / 50 hPa [mm/s] | 0.40 / 0.21 / 0.20 | 0.14 / 0.22 / 0.29 | 0.18 / 0.21 / 0.27 | 0.17 / 0.20 / 0.26 |
| mass flux 70 hPa [1e9 kg/s] | 6.05 | 6.80 | 6.90 | 6.90 |
| NH jet 10 hPa [m/s, deg] | 25.2 at 62.5 | 18.5 at 60.6 | 18.1 at 58.8 | 16.1 at 55.0 |
| SH jet 10 hPa [m/s] | 71.9 | 66.0 | 66.1 | 65.6 |
| QBO std 50 hPa [m/s] (ERA5 11.3) | | 10.6 | 7.0 | |

Full table: `success_0610/success_table.md`.

## Findings

1. **QBO30 has the best score so far (0.88, 16/21).** The gain is all in the circulation group (B 1.05 -> 0.88). w* at
   50 hPa drops from 0.29 to 0.27 mm/s and now passes. At 100 hPa it rises from 0.14 to 0.18 mm/s, still less than half of
   WACCM6's 0.40. The 70 hPa mass flux does not drop (6.90). The vortex is AL7h's (jets within 1 m/s).
2. **The age of air does not improve.** The entry age is slightly younger (0.94 against 1.00 yr) and the 2-D RMSE is
   unchanged (0.61 against 0.62 yr). Neither variant fixes the age problem the corrected runs share.
3. **QBO30 weakens the lowest part of the QBO.** At 50 hPa the amplitude drops from 10.6 to 7.0 m/s (ERA5 11.3), and the
   wind there switches direction 2-3 months after ERA5. At 10-30 hPa it stays on ERA5 (15-18 m/s).
4. **QBO10d is worse overall (0.99).** It has the same circulation gain (B 0.90), but the NH 10 hPa jet weakens to 16 m/s
   and moves to 49-55 deg N. The SAO near 1 hPa is weaker and drifts out of phase with ERA5. Below 3 hPa its QBO is almost AL7h's.

No configuration gets the vortex and the age right together. QBO30 is the best candidate on the scorecard. If it is
adopted, it should be judged after a longer spin-up than a restart from 2004 (Phase 26: restart runs keep drifting younger).
