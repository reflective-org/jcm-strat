# Phase 24 — AL7 with the T_eq correction kept out of the subtropics

**Goal (Susanne, 2026-10-24):** AL7 (Phase 22) fixes the polar vortex but makes the stratospheric air too young. Test whether the
young air comes from the subtropical part of the correction: taper AL7's correction to zero at 35 deg and full strength from 50 deg
(AL7: 25 -> 35 deg). Also: a shareable scorecard document comparing all runs.

**Run.** `AL7t`: `scripts/p24_taper_correction.py` multiplies AL7.nc by a sin^2 latitude ramp (0 at 35, 1 at 50 deg) ->
`corrections/AL7t35_50.nc`. Same protocol as AL7: P20b physics and nudging (`p22_teq`), 2005-2007 from P20b's end-of-2004 state.
`scripts/phase24_run.sh 0` (tmux `strat_p24_run`, GPU 0), 2026-10-23 19:54-20:39 PDT (45 min), no health stops; diagnostics and
success metrics (2006-2007, memory-capped) done 21:08 PDT, commit 3278bf4.

## Result (success metrics, moderate bounds; full table `success/success_table.md`)

| | P20b | AL7 | L0 | LAL7 | **AL7t** |
|---|---|---|---|---|---|
| A age of air | 0.66 | 1.21 | 1.09 | 1.72 | 1.29 |
| B residual circulation | 1.11 | 1.10 | 0.99 | 1.08 | 1.08 |
| C polar vortex | 1.50 | 0.17 | 1.25 | 0.49 | 0.61 |
| **combined** | 1.09 | **0.82** | 1.11 | 1.10 | 0.99 |
| passed / 21 | 11 | **17** | 10 | 13 | 12 |

1. **Moving the correction out of the subtropics does not bring the age back.** Mean entry-age bias vs CLaMS: AL7 -0.55, AL7t
   -0.54 yr (P20b -0.14). The tropics-to-midlatitude step at 55 hPa moves only 2.14 -> 2.20 yr (CLaMS 2.79).
2. **It costs vortex strength,** mostly in the north: 10 hPa DJF jet 18 m/s (AL7 26, ERA5 26), at 61N; SH 10 hPa 71 (AL7 75, ERA5 74).
3. **The young air goes with a stronger lower-stratospheric circulation.** Upward mass flux at 70 hPa: P20b 6.4, AL7 7.2, LAL7 7.2,
   AL7t 7.7 x 10^9 kg/s (WACCM6 6.05). The age error follows the vortex fix itself, not its subtropical edge.
4. AL7 remains the best configuration.

**Next step (not run):** a weaker correction (a fraction of AL7's amplitude), to see whether most of the vortex gain survives
while the 70 hPa mass flux and the ages move back toward WACCM6 and CLaMS.

## Scorecard document

Shareable page (private until shared): https://claude.ai/artifact/FAtP968h6fgMEEYpkN7LpM. Source `report/index.html`, built by
`scripts/build_scorecard.py` from `success/success_metrics.json`, the comparison figures from `scripts/report_figures.py`
(`report/*.png`; run colours validated for colour-vision deficiency), each run's diagnostic plots in `report/runs/`, findings and notes
in `report/findings.html` and `report/notes.html`.
