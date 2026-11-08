# Phase 26 — scoring on five years (2006-2010)

**Goal (Susanne, 2026-10-27/28):** score on 5 years instead of 2, which is more robust and shows whether the restart runs drift
after a couple of years. Window 2006-2010, so the restart year 2005 is left out.

**Runs.** The five restart runs (AL7, AL7h, AL7t, L0, LAL7; from P20b's end-of-2004 state) were extended to 2009
(`scripts/phase26_run.sh`, GPU 0, Oct 27-28) and then to 2010 (`scripts/phase26_2010.sh`, GPU 1, Oct 28 16:25-18:13 PDT,
18-26 min per year, no health stops), each with the settings of its own chain. P20b uses p20bt's own years (2010 from the
50-year chain). The first 2010 launch (11:51 PDT) died after 5 min with no error when its tmux session disappeared; the relaunch
resumed it. Scoring under `scripts/memcap.sh` at 60G, one job at a time (about 1 h per run), finished Oct 29 05:10 PDT;
report rebuilt by `scripts/phase26_report.sh`.

Outputs: `success_0610/` (2006-2010, the headline), `success/` (2005-2009), `success_0809/` (2008-2009, drift check),
diagnostics `w0610/<run>/` and `<run>/`, scorecard page `report/` (published to the scorecard artifact, version 3).

## Result (success metrics, moderate bounds)

Combined score (passed / 21):

| window | P20b | AL7 | AL7h | AL7t | L0 | LAL7 |
|---|---|---|---|---|---|---|
| 2006-2007 (Phase 25) | 1.09 (11) | **0.82** (17) | 0.93 (14) | 0.99 (12) | 1.11 (10) | 1.10 (13) |
| 2008-2009 | 0.97 (12) | 1.11 (12) | **0.91** (15) | 1.03 (13) | 1.19 (11) | 1.26 (14) |
| 2005-2009 | 1.05 (12) | **0.86** (16) | 0.88 (15) | 0.93 (13) | 1.15 (10) | 1.11 (15) |
| **2006-2010** | 1.08 (11) | 0.94 (**16**) | **0.93** (14) | 0.94 (13) | 1.15 (10) | 1.21 (14) |

2006-2010 groups (A age / B circulation / C vortex): P20b 0.70/1.13/1.41, AL7 1.41/1.08/0.31, AL7h 1.10/1.05/0.66,
AL7t 1.49/1.06/0.26, L0 1.18/1.02/1.25, LAL7 2.01/1.06/0.55.

Mean entry-age bias vs CLaMS (aoa150, years) and 70 hPa mass flux (10^9 kg/s, WACCM6 6.05):

| window | P20b | AL7 | AL7h | AL7t | L0 | LAL7 |
|---|---|---|---|---|---|---|
| bias 2006-07 | -0.14 | -0.55 | -0.37 | -0.54 | -0.47 | -0.84 |
| bias 2008-09 | -0.16 | -0.70 | -0.47 | -0.69 | -0.54 | -1.04 |
| bias 2006-10 | -0.15 | -0.64 | -0.43 | -0.63 | -0.52 | -0.97 |
| flux 2006-10 | 6.43 | 7.23 | 6.80 | 7.58 | 6.81 | 7.17 |

## Findings

1. **The restart runs drift younger.** Every run restarted from P20b at the end of 2004 gets 0.07-0.20 yr younger between
   2006-07 and 2008-09; P20b (running since 1990) does not move. The age group score of the corrected runs rises accordingly,
   while circulation (B) and vortex (C) scores hardly change. The 2-year scores therefore flattered the corrected runs; the
   age clocks of a restart are not settled after 2-3 years.
2. **AL7h, AL7 and AL7t now tie** (0.93-0.94). AL7 still passes the most metrics (16) and keeps the vortex (C 0.31); AL7h
   trades half the vortex gain for two-thirds of the age error; AL7t has the best vortex (C 0.26) but the same age as AL7.
3. **The vortex fix holds over five winters.** AL7 jets within 1-4 m/s of ERA5 at 50 and 10 hPa in both hemispheres; P20b's
   SH 10 hPa jet 57 vs 72 m/s. AL7h's weak NH 10 hPa jet (18.5 vs 25 m/s) persists over five winters, so it was not only
   two-winter sampling.
4. **Unchanged:** 100 hPa w* 0.13-0.18 vs 0.40 mm/s in every run; tropical-top nudging (L0, LAL7) makes the air younger;
   LAL7 is the worst run.

No configuration gets vortex and age together. The drift means a correction should be judged on runs that have been going
several years past the restart (or from a longer spin-up).
