# Phase 13b — the Jucker et al. (2013) relaxation in the dry model, without and with gravity-wave drag (strat81, 1990–1994)

Status: **running** (launched 2026-09-23 evening PDT, GPU 1, tmux `phase13b-jucker`, log `runs/p13b_run.log`). Runs
`p13jucker_5yr` and `p13juckergwd_5yr`; references `p12l81_5yr` (same grid, Polvani–Kushner, no drag), `p13gwd_5yr`
(strat63, Polvani–Kushner + drag), `p12echam_5yr` (full physics).

## Why

Phase 13 (`docs/outputs/13_gwd/`) showed that Hines + Lott-Miller drag in the dry Polvani–Kushner model deposits its
momentum in the lower stratosphere and none above the stratopause: shallow branch 2.6× WACCM6, extratropical lower
stratosphere 1.4 yr too young, 10 hPa ascent collapsed, mesosphere still downward. The same schemes give the full physics
a mesospheric cell. The dry model's difference is what the waves propagate through: Polvani–Kushner relaxes to a flat
standard atmosphere above 3 hPa with one 15-day timescale, while the radiative equilibrium has a ~300 K summer stratopause,
a 190–205 K winter polar upper stratosphere and a 4–6 day relaxation time there. Jucker, Fueglistaler & Vallis (2013, JAS
70, 3341) computed exactly that: T_e(month, p, lat) and tau(month, p, lat) from a radiative calculation, published with
their code (`github.com/mjucker/JFV-strat`). Susanne, 2026-09-23: "can you try this Jucker thing? ... Go but do it with L81".

## Setup

`jcm_strat.jucker.JuckerColumns` replaces the Polvani–Kushner stratosphere above 100 hPa by the JFV2013 fields
(`jcm_strat/data/jfv2013_te_tau_zm.nc`, the zonal slice of their `temp/tau_monthly_L10_full.nc`; interpolated in log-p and
latitude onto the run's levels once, linearly and periodically in the fraction of year between mid-months at run time);
below 250 hPa the Held-Suarez troposphere as before; linear blend between (JFV's `hs_forcing.f90` defaults). QBO nudging
(inside the term), ERA5 nudging < 150 hPa, sponge, tracers with the 1 hPa lid, 6-hourly output: unchanged from `p12_l81`.

| run | grid | relaxation | drag | one change against |
|---|---|---|---|---|
| `p13_jucker` | strat81 (8 + 47 + 26) | JFV2013 above 100 hPa | none | `p12l81_5yr` (PK relaxation) |
| `p13_jucker_gwd` | strat81 | JFV2013 | Hines (launch 634 hPa = level 10) + Lott-Miller, JCM defaults | `p13jucker_5yr` (drag); `p13gwd_5yr` (relaxation + troposphere grid) |

On the strat81 levels the table gives, in mid-January: T_e at 0.9 hPa 304 K at 85S, 275 K at the equator, 206 K at 85N;
at 30 hPa 236 / 218 / 183 K; tau 4.5–6 d at 1–0.3 hPa, 5–9 d at 10 hPa, 12–39 d at 100 hPa (tropics longest), 8–10 d at
the 0.018 hPa top level (where the sponge's 250 K temperature damping, tau 1.5 h, dominates as before).

## Acceptance (Phase 13 criteria; entry-age clock `aoa150` vs WACCM6, w* vs WACCM6 histSST, mesosphere w* 1994)

| quantity | strat81 control (`p12l81_5yr`) | target | jucker | jucker_gwd |
|---|---|---|---|---|
| tropical w* 30 hPa [mm/s] | 0.02 | 0.26 (within 1.5×) | | |
| tropical w* 10 hPa [mm/s] | 0.31 | 0.47 (within 1.5×) | | |
| tropical w* 100 hPa [mm/s] | 0.35 | 0.40 (PK + drag: 1.05) | | |
| tropical `aoa150` 12 hPa [yr] | 3.80 | 2.90 ± 0.4 | | |
| tropical `aoa150` 55 hPa [yr] | 1.31 | 1.19 (not worse) | | |
| 50–70° `aoa150` 55 hPa [yr] | 3.64 | ≥ 3.6 (PK + drag: 2.47) | | |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | −0.75 / −0.98 / −0.12 | upward (ECHAM +0.96 / +1.31 / +1.92) | | |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −0.07 / −0.51 | ECHAM −2.82 / −5.27 | | |
| `aoa150` latitude std at 3 / 1.5 hPa [yr] | 0.05 / 0.05 | > 0.05 (ECHAM 0.18 / 0.14) | | |
| cost vs strat81 control [min/yr e2e] | 26–27 | ≤ 1.3× | | |

## Results

*(filled when the pipeline finishes: `jucker_*`, `jucker_gwd_*`, `jucker_gwd_vs_gwd_*`, `jucker_gwd_vs_echam_*` from
`scripts/phase12_compare.py`; `p13jucker*_aoa_*` from `scripts/aoa_vs_clams.py`; `p13b_mesosphere.md/.png`.)*

## Open questions

- The sponge damps temperature toward 250 K in the top four levels (tau 1.5 h at the top) while T_e there is 150–330 K;
  the two fight in the top ~3 levels. Left as is (same as under Polvani–Kushner); a sponge without temperature damping
  is a separate test.
