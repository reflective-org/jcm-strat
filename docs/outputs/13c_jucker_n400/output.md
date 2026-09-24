# Phase 13c — Jucker relaxation + gravity-wave drag with the nudging cut off at 400 hPa, ten years, Hines with and without Lott-Miller (strat81, 1990–1999)

Status: **running** (launched 2026-09-24 ~11:00 PDT, GPUs 1 and 2, tmux `phase13c-n400`, log `runs/p13c_run.log`). Runs
`p13jgn400_10yr` (Hines + Lott-Miller) and `p13jhn400_10yr` (Hines only); references `p13juckergwd_5yr` (same physics, nudged
below 150 hPa, 5 yr), `p13jucker_5yr` (no drag), `p12echam_5yr` (full physics).

## Why

Susanne, 2026-09-24: "Can you do an additional run, 10 years, with Jucker relaxation, gravity wave drag and nudging only until
400 hPa. And do the same but for gravity use only Hines, not Lott-Miller." Phase 13b showed the Jucker relaxation alone
ventilates the mesosphere and improves the deep branch, while Hines + Lott-Miller at JCM defaults over-drive the shallow branch
and make the extratropical lower stratosphere too young (Phases 13 and 13b alike). The two runs here ask (1) whether freeing the
upper troposphere (nudging only below 400 hPa: the tropopause region and the wave fluxes into the stratosphere become the model's
own — in Phase 13 this weakened the shallow branch on its own) changes that balance under the drag, over a ten-year chain that
lets the clocks equilibrate, and (2) how much of the lower-stratospheric momentum deposition is the orographic scheme's.

## Setup

| run | grid | relaxation | drag | nudging | years | one change against |
|---|---|---|---|---|---|---|
| `p13_jucker_gwd_n400` | strat81 | JFV2013 above 100 hPa | Hines (launch 634 hPa) + Lott-Miller, JCM defaults | u, v, T where p > **400 hPa**, tau 6 h | 1990–1999 | `p13juckergwd_5yr` (cutoff 150 → 400, 5 → 10 yr) |
| `p13_jucker_hines_n400` | strat81 | JFV2013 | **Hines only** | p > 400 hPa | 1990–1999 | `p13_jucker_gwd_n400` (Lott-Miller off) |

QBO nudging, sponge, clocks with the 1 hPa lid, 6-hourly output: unchanged. New in these runs: the nine `moist_air_state`
diagnostics the drag lists used to write (31 of 96 GB/yr) are dropped from the output; the analysis reads u, v, T, omega and the
clocks. The strat81 ERA5 windows for 1995–1999 were prefetched for this phase (hash 3af87627, 26 GB/yr).

## Acceptance (Phase 13 criteria; entry-age clock `aoa150` vs WACCM6, w* vs WACCM6 histSST, mesosphere w*)

| quantity | Jucker no drag (`p13jucker_5yr`) | Jucker + GWD < 150 hPa (`p13juckergwd_5yr`) | target | jgn400 (10 yr) | jhn400 (10 yr) |
|---|---|---|---|---|---|
| tropical w* 100 hPa [mm/s] | 0.29 | 0.99 | 0.40 | | |
| tropical w* 30 hPa [mm/s] | 0.03 | 0.06 | 0.26 (within 1.5×) | | |
| tropical w* 10 hPa [mm/s] | 0.41 | 0.25 | 0.47 (within 1.5×) | | |
| tropical `aoa150` 12 hPa [yr] | 3.67 | 3.65 | 2.90 ± 0.4 | | |
| tropical `aoa150` 55 hPa [yr] | 1.56 | 1.12 | 1.19 | | |
| 50–70° `aoa150` 55 hPa [yr] | 3.62 | 2.06 | ≥ 3.6 | | |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | +0.32 / +0.08 / +0.23 | +0.15 / +0.31 / +0.90 | upward (ECHAM +0.96 / +1.31 / +1.92) | | |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −1.76 / −2.92 | −2.97 / −4.60 | ECHAM −2.82 / −5.27 | | |
| cost [min/yr e2e] | 26–28 | 41 | ≤ 1.3× control (35) | | |

## Results

*(filled when the pipeline finishes: `hines_vs_lm_*`, `n400_*`, `jgn400_vs_echam_*`, `jhn400_vs_jucker_*` from
`scripts/phase12_compare.py`; `p13j*n400_10yr_aoa_*`; `p13c_mesosphere.md/.png` on the 1994 and 1999 segments.)*

## Open questions

- Comparisons of a 10-year run against a 5-year one: w* is a mean over all frames (different periods, 1990–1999 vs 1990–1994);
  the ages are the last 60 days (end-1999 vs end-1994; with the 1 hPa lid the clocks are near equilibrium after 5 yr, Phase 11).
  `hines_vs_lm` is the clean like-for-like pair.
