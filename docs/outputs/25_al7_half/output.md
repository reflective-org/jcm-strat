# Phase 25 — AL7 at half amplitude (AL7h)

**Goal (Susanne, 2026-10-27):** "try the weaker correction run". AL7 fixes the polar vortex but makes the air ~0.5 yr too young
(Phase 24 found the age error follows the vortex fix itself). Test whether half of AL7's T_eq correction keeps most of the vortex
gain while bringing the 70 hPa mass flux and the ages back toward WACCM6 and CLaMS.

**Run.** `AL7h`: AL7.nc x 0.5 -> `corrections/AL7h.nc` (-20..+17 K). Same protocol as AL7: P20b physics and nudging (`p22_teq`,
correction mode total), 2005-2007 from P20b's end-of-2004 state. `scripts/phase25_run.sh 0` (tmux `strat_p25_run`, GPU 0),
2026-10-27 09:17-10:07 PDT (50 min), no health stops; diagnostics and success metrics (2006-2007, memory-capped) done 10:38 PDT,
commit 5eaff9e.

## Result (success metrics, moderate bounds; full table `success/success_table.md`)

| | P20b | AL7 | L0 | LAL7 | AL7t | **AL7h** |
|---|---|---|---|---|---|---|
| A age of air | 0.66 | 1.21 | 1.09 | 1.72 | 1.29 | 0.97 |
| B residual circulation | 1.11 | 1.10 | 0.99 | 1.08 | 1.08 | 1.06 |
| C polar vortex | 1.50 | 0.17 | 1.25 | 0.49 | 0.61 | 0.75 |
| **combined** | 1.09 | **0.82** | 1.11 | 1.10 | 0.99 | 0.93 |
| passed / 21 | 11 | **17** | 10 | 13 | 12 | 14 |

1. **Half the correction gives about half of each effect.** Mean entry-age bias vs CLaMS: P20b -0.14, AL7h -0.37, AL7 -0.55 yr;
   55 hPa tropical entry age 0.99 yr (WACCM6 1.11, AL7 0.90); 70 hPa mass flux 6.9 x 10^9 kg/s (P20b 6.4, AL7 7.2, WACCM6 6.05).
2. **The southern vortex is also halfway:** JJA jet 43 m/s at 50 hPa, 67 at 10 hPa (P20b 39/57, AL7 46/75, ERA5 46/74). Polar-cap
   T at 50 hPa within 1.5 K in both hemispheres.
3. **The northern upper-stratospheric jet is the weakest of all runs** (DJF 17 m/s at 10 hPa, 18 at 5 hPa; ERA5 26). It is not
   between P20b and AL7, so probably sampling of two northern winters, not the correction.
4. **Scaling the amplitude trades vortex against age almost linearly**, so amplitude alone cannot reach both targets. AL7h is
   second best (0.93, 14 passes); AL7 remains the best configuration.

**Next step (not run):** getting both needs a change that strengthens the vortex without speeding up the lower-stratospheric
branch, or something that slows the lower branch on top of AL7.

## Scorecard document

Same page, updated in place to six runs: https://claude.ai/artifact/FAtP968h6fgMEEYpkN7LpM. Source `report/` (built as in
Phase 24); run colours re-validated for six runs (OKLab dE x100: normal >= 16.3, deutan/protan >= 10.8).
