# Phase 13d — Jucker relaxation + Hines only, nudged below 150 hPa (strat81, 1990–1994)

Status: **running** (launched 2026-09-25 ~10:20 PDT, GPU 1, tmux `phase13d-jucker-hines`, log `runs/p13d_run.log`). Run
`p13jh_5yr`; references at equal length: `p13jucker_5yr` (no drag), `p13juckergwd_5yr` (Hines + Lott-Miller), `p12echam_5yr`.

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
| tropical w* 100 hPa [mm/s] | 0.29 | 0.99 | 0.40 | |
| tropical w* 30 hPa [mm/s] (stride-4 caveat) | 0.03 | 0.06 | 0.26 | |
| tropical w* 10 hPa [mm/s] | 0.41 | 0.25 | 0.47 (within 1.5×) | |
| tropical `aoa150` 12 hPa [yr] | 3.67 | 3.65 | 2.90 ± 0.4 | |
| tropical `aoa150` 55 hPa [yr] | 1.56 | 1.12 | 1.19 | |
| 50–70° `aoa150` 55 hPa [yr] | 3.62 | 2.06 | ≥ 3.6 | |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | +0.32 / +0.08 / +0.23 | +0.15 / +0.31 / +0.90 | upward (ECHAM +0.96 / +1.31 / +1.92) | |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −1.76 / −2.92 | −2.97 / −4.60 | ECHAM −2.82 / −5.27 | |
| cost [min/yr e2e] | 26–28 | 41 | ≤ 35 | |

## Results

*(filled when the pipeline finishes: `hines_*`, `lm_off_*`, `jh_vs_echam_*`, `p13jh_5yr_aoa_*`, `p13d_mesosphere.md/.png`.)*
