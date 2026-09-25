# Phase 13d — Jucker relaxation + Hines only, nudged below 150 hPa (strat81, 1990–1994)

Status: **complete** (pipeline 2026-09-25 10:12 → 14:08 PDT on GPU 1; chain 10:19–13:06, diagnostics 13:06–14:08; tmux
`phase13d-jucker-hines`, log `runs/p13d_run.log`). Run `p13jh_5yr`; references at equal length: `p13jucker_5yr` (no drag),
`p13juckergwd_5yr` (Hines + Lott-Miller), `p12echam_5yr` (full physics). Headline: **Jucker + Hines only is the best dry
configuration so far.** Without Lott-Miller the shallow branch does not overshoot (tropical w* 100 hPa 0.33 mm/s, WACCM6 0.40;
with both schemes 0.99), the deep branch reaches WACCM6 (10 hPa 0.49 vs 0.47), the mesospheric cell is at full-physics strength
(0.3 hPa tropics / NH / SH +2.0 / −4.1 / −6.9 mm/s, ECHAM +1.9 / −4.2 / −7.0), and every entry-age number moves toward the target
by 0.13–0.23 yr against the no-drag run: tropics 55 hPa 1.41 (WACCM6 1.19), 12 hPa 3.45 (2.90 ± 0.4), 50–70° 55 hPa 3.47
(≥ 3.6). Three criteria are still missed, all by ≤ 0.15 yr or at the 30 hPa stall (0.04 vs 0.26, stride-4 sampled); cost 31 min/yr
(1.15× no drag). Lott-Miller is confirmed as the whole of the Phase 13/13b shallow-branch damage.

## Why

Susanne, 2026-09-25: "an additional run: Jucker relaxation plus Hines only, nudged below 150 hPa, on strat81" — the one
combination Phases 13b/13c left out. Phase 13b: the Jucker relaxation alone ventilates the mesosphere and fixes the deep branch,
Hines + Lott-Miller on top over-drive the shallow branch (100 hPa w* 0.99 vs 0.40) and make the extratropics too young (2.06 yr).
Phase 13c: Lott-Miller off is better on every stratospheric measure; the shallow branch comes from the ERA5-nudged upper
troposphere, so the cutoff stays at 150 hPa.

## Setup

`p13_jucker_hines` = `p13_jucker_gwd` with `lott_miller_sso` removed (physics `strat_jucker_hines_prod13`): strat81, JFV2013
T_e/tau above 100 hPa, Hines at JCM defaults (launch 634 hPa = level 10, rms 1.0 m/s), ERA5 nudging of u, v, T below 150 hPa,
QBO nudging, four clocks with the 1 hPa lid, 6-hourly output without the moist-air diagnostics. 1990–1994.

## Acceptance (entry-age clock `aoa150` vs WACCM6, w* vs WACCM6 histSST, mesosphere w* 1994)

| quantity | Jucker no drag | Jucker + Hines + LM | target | Jucker + Hines |
|---|---|---|---|---|
| tropical w* 100 hPa [mm/s] | 0.29 | 0.99 | 0.40 | **0.33** |
| tropical w* 30 hPa [mm/s] (stride-4 caveat) | 0.03 | 0.06 | 0.26 | 0.04 |
| tropical w* 10 hPa [mm/s] | 0.41 | 0.25 | 0.47 (within 1.5×) | **0.49** |
| tropical `aoa150` 12 hPa [yr] | 3.67 | 3.65 | 2.90 ± 0.4 | 3.45 |
| tropical `aoa150` 55 hPa [yr] | 1.56 | 1.12 | 1.19 | 1.41 |
| 50–70° `aoa150` 55 hPa [yr] | 3.62 | 2.06 | ≥ 3.6 | 3.47 |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | +0.32 / +0.08 / +0.23 | +0.15 / +0.31 / +0.90 | upward (ECHAM +0.96 / +1.31 / +1.92) | **+0.04 / +0.46 / +1.98** |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −1.76 / −2.92 | −2.97 / −4.60 | ECHAM −2.82 / −5.27 | **−3.51 / −5.54** |
| cost [min/yr e2e] | 26–28 | 41 | ≤ 35 | **30–32** (2460–2520 d/hr stepping, 695–737 e2e) |

## Results

Figures and tables in this directory: `hines_*` (Hines added under the Jucker relaxation: `p13jucker_5yr` → `p13jh_5yr`),
`lm_off_*` (Lott-Miller removed: `p13juckergwd_5yr` → `p13jh_5yr`), `jh_vs_echam_*` (full physics → this run),
`p13jh_5yr_aoa_*` (each clock vs CLaMS/WACCM, `p13jucker_5yr` alongside), `p13d_mesosphere.md/.png` (1994 segments of every
Phase 12/13 strat81 run and full ECHAM).

**Hines added to the Jucker relaxation (`hines_metrics.md`).** Annual upward mass flux 100 / 70 / 30 / 10 hPa: 10.6 → 11.7 /
6.7 → 7.5 / 2.8 → 3.0 / 1.29 → 1.41 ×10⁹ kg/s (WACCM6 10.9 / 6.1 / 3.1 / 1.37) — every level now within 10 % of WACCM6 except
70 hPa (+23 %). Tropical w* 100 / 70 / 50 / 30 / 10 hPa: 0.29 → 0.33 / 0.17 → 0.19 / 0.13 → 0.13 / 0.03 → 0.04 / 0.41 → 0.49 mm/s
(WACCM6 0.40 / 0.21 / 0.20 / 0.26 / 0.47). The drag strengthens the shallow branch by 13 % and the deep branch by 19 %; the
50–20 hPa layer does not move. Seasonally the deep branch gains most in JJA (10 hPa 0.24 → 0.35, WACCM6 0.45) and the DJF value
sits above WACCM6 (0.79 vs 0.64), as it already did without drag. In the w* maps (`hines_wstar.png`) the difference is a
stronger winter-hemisphere descent through the upper stratosphere and a slightly wider tropical pipe; nothing changes sign.
Ages (entry-age clock): tropics 55 hPa 1.56 → 1.41 (WACCM6 1.19; the no-drag run had lost 0.25 yr against Polvani–Kushner's
1.31, Hines recovers 0.15 of it), 12 hPa 3.67 → 3.45 (2.90 ± 0.4: still 0.15 outside the tolerance, was 0.37), 50–70° 55 hPa
3.62 → 3.47 (≥ 3.6: now 0.13 short; WACCM6 entry age ~3.7, CLaMS surface clock 4.12). All four clocks get 0.10–0.23 yr younger
everywhere, tropics slightly more than extratropics, so the age *contrast* is kept (`hines_age_profiles.png`).

**Lott-Miller removed (`lm_off_metrics.md`; same relaxation, same nudging, 5 yr each).** 100 hPa mass flux 21.6 → 11.7 (WACCM6
10.9), tropical w* 100 hPa 0.99 → 0.33, 70 hPa 0.31 → 0.19, 10 hPa 0.25 → 0.49; DJF 100 hPa 1.31 → 0.29 (WACCM6 0.45), DJF 10 hPa
0.22 → 0.79 (0.64). Entry age 50–70° 55 hPa 2.06 → 3.47, tropics 55 hPa 1.12 → 1.41, 12 hPa 3.65 → 3.45. The orographic scheme
alone was the 2.5× shallow branch and the too-young extratropics of Phases 13 and 13b, and it *halved* the deep branch; taking it
out restores both. Under the 150 hPa nudging this is the same verdict Phase 13c reached under the 400 hPa cutoff, now without the
cutoff's confound. `lm_off_wstar.png` shows Lott-Miller's signature as before: broad extratropical descent through the whole
lower stratosphere in both winters, gone in this run.

**Against full physics (`jh_vs_echam_metrics.md`).** The dry Jucker + Hines run is closer to WACCM6 than JCM's full ECHAM physics
on every circulation number: 100 hPa w* 0.33 vs 1.46 (WACCM6 0.40), 70 hPa 0.19 vs 0.60 (0.21), 10 hPa 0.49 vs 0.87 (0.47), 100 hPa
mass flux 11.7 vs 28.7 (10.9). The ECHAM run keeps the advantage at 30 hPa (0.28 vs 0.04, WACCM6 0.26). Entry ages: tropics 55 hPa
1.41 vs 0.96 (WACCM6 1.19; the two runs bracket it), 12 hPa 3.45 vs 3.33 (2.90), 50–70° 55 hPa 3.47 vs 2.41 (the dry run is
right, the full physics 1.7 yr too young). The surface clock in the tropics still reads 3.13 vs ECHAM's 1.33 (CLaMS 1.33): the
dry troposphere's transit (Phase 12 addendum), not a stratospheric difference — the entry-age clock is the one to compare.

**Mesosphere (`p13d_mesosphere.md`, 1994 segments, annual mean, tropics / NH cap / SH cap, mm/s):**

| run | 10 hPa | 5 hPa | 2 hPa | 1 hPa | 0.5 hPa | 0.3 hPa | `aoa150` lat std at 3 / 1.5 hPa [yr] |
|---|---|---|---|---|---|---|---|
| strat81 control (PK) | +0.28 / −0.93 / −0.67 | +0.78 / −1.01 / −0.59 | +0.35 / −0.49 / −0.08 | −0.75 / −0.71 / −0.74 | −0.98 / −0.07 / −0.51 | −0.12 / −0.23 / −1.06 | 0.05 / 0.05 |
| Jucker | +0.36 / −0.51 / −0.66 | +1.09 / −0.79 / −0.78 | +0.67 / −0.94 / −1.05 | +0.32 / −1.74 / −2.51 | +0.08 / −1.76 / −2.92 | +0.23 / −3.07 / −4.89 | 0.12 / 0.10 |
| Jucker + Hines + LM | +0.19 / −0.06 / −0.56 | +0.58 / −0.29 / −0.81 | +0.58 / −0.81 / −1.78 | +0.15 / −1.94 / −3.42 | +0.31 / −2.97 / −4.60 | +0.90 / −4.53 / −6.07 | 0.12 / 0.11 |
| **Jucker + Hines** | +0.46 / −0.73 / −0.93 | +1.18 / −1.07 / −1.26 | +0.67 / −1.50 / −2.26 | +0.04 / −3.03 / −4.37 | **+0.46 / −3.51 / −5.54** | **+1.98 / −4.12 / −6.91** | 0.14 / 0.11 |
| full ECHAM | +0.88 / −1.55 / −1.23 | +0.96 / −1.71 / −1.22 | +0.60 / −0.42 / −1.76 | +0.96 / −1.29 / −3.19 | +1.31 / −2.82 / −5.27 | +1.92 / −4.22 / −7.04 | 0.18 / 0.14 |

The Hines-only run has the strongest mesospheric cell of every dry configuration and at 0.5–0.3 hPa it is the full-physics cell
to within 0.3 mm/s in all three bands. The polar descent is stronger than with both schemes at every level from 5 hPa up (NH
0.5 hPa −3.5 vs −3.0, SH −5.5 vs −4.6): Lott-Miller was not adding to the mesospheric cell either, it was weakening the deep
branch below it. The tropical mean at 1 hPa is ~0 (the cell's base sits near 1–2 hPa, as in Phase 13c); the latitude structure
of the age at 3 / 1.5 hPa (std 0.14 / 0.11 yr) is the largest of the dry runs.

**Caveat on the w* numbers.** As in Phases 12–13c the TEM covariances are formed from every 4th 6-hourly frame. The Phase 15
sweep found this daily-phase sampling biases the tropical w* in the middle stratosphere (tides; the 30 hPa value of the 1991
Jucker segment is 0.11 from the 06 UTC frames and 0.42 from all frames, WACCM6 0.26), so the 30 hPa row above is not evidence
of a stall on its own. The 100 and 10 hPa values, the clocks and the mesosphere table are not affected in their conclusions.
Before comparing this run with the Phase 15 leaderboard (stride 1), rerun `scripts/phase12_compare.py --stride 1` on it.

**Verdict against the acceptance criteria.** Met: mesosphere (upward tropics at 0.5–0.3 hPa, polar descent 3.5–5.5 mm/s —
ECHAM strength), 10 hPa w* (0.49 vs 0.47), 100 hPa w* (0.33 vs 0.40, no overshoot), cost (31 min/yr, 1.15×). Missed, all
narrowly: tropical entry age 12 hPa 3.45 vs 2.90 ± 0.4 (0.15 outside), 55 hPa 1.41 vs 1.19 (0.10 worse than the PK value 1.31 the
criterion was written against), 50–70° 55 hPa 3.47 vs ≥ 3.6 (0.13 short); 30 hPa w* 0.04 vs 0.26 (stride-4 sampled, see above).
Every one of the missed numbers is better than in the no-drag run, and none of the failures of Phases 13/13b (shallow branch 2.5×,
extratropics 2.06 yr, deep-branch collapse) is present. **`p13_jucker_hines` replaces `p13_jucker` as the candidate production
dry configuration**, subject to Susanne's decision and to the stride-1 w* check. The Hines amplitude knob (`rms_launch_wind`)
that Phase 13c reserved for a shallow-branch overshoot is not needed: the shallow branch is *under* WACCM6 by 17 %.

## Open questions

- **Five-year clocks.** As in every 5-year chain the ages are lower bounds where air is old (Phase 13c: the 10-year clocks are
  0.3–0.4 yr older in the extratropics); the 50–70° number 3.47 would likely pass ≥ 3.6 at 10 yr, and the tropical 12 hPa number
  would likely move away from 2.90. A 10-year extension (`YEARS=1990-1999`, segments 1990–1994 reused; strat81 ERA5 windows exist
  to 1999) settles both.
- **The 30 hPa layer.** With the 100 and 10 hPa levels now on WACCM6, whether a 50–20 hPa deficit remains is a stride-1 question
  first. If it does, the Phase 15 sweep's Rayleigh-drag family (30 → 1 hPa) is the candidate fix, and its leaderboard already
  ranks `ray30+n100` first with `aoa150` RMSE 0.45 yr vs CLaMS; Hines + Rayleigh together has not been run.
- The tropical lower stratosphere (55 hPa entry age 1.41 vs 1.19) is the JFV relaxation's slower 100–70 hPa upwelling (Phase 13b:
  tau 12–39 d there against PK's 15 d). The `p_bd` 70 hPa blend-boundary test from Phase 13b is still untested; the Phase 15
  `tau15cap` knob (JFV tau capped at 15 d) addresses the same thing.
- The drag-tendency diagnostic (per-term momentum deposition on one segment) proposed in Phase 13b would show where Hines puts its
  momentum in this run; still not written.
