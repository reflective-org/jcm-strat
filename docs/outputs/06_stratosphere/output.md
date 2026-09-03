# Phase 6 — a stratosphere without radiation: seasonal Polvani-Kushner

Status: **in progress** (2026-09-03). Branch `phase6-stratosphere` (worktree `jcm-strat-phase6`).

## Question this phase answers

Can an analytic relaxation give the stripped model a defensible stratosphere — polar-night jet,
seasonal cycle, roughly the right temperatures — without bringing radiation back? Judged against
ERA5, WACCM6 and JCM's own full-physics ECHAM configuration under the same specified dynamics.

## Configuration

`+experiment=p6_pk`: the Phase-3/4 configuration (ERA5-nudged u/v/T below 150 hPa, tau 6 h;
four passive tracers; clock exempt from the mass fixer; T63L95; dt 12 min; 2005) with
`physics=strat_pk`: `PolvaniKushnerColumns` replaces `HeldSuarezColumns`.

The term (`jcm_strat/polvani_kushner.py`): below 100 hPa the Held-Suarez equilibrium with the
200 K floor replaced by the US Standard Atmosphere and a winter-hemisphere asymmetry
(epsilon = 10 K); above 100 hPa `(1-W) T_US + W T_PV`, `T_PV = T_US(100 hPa) (p/100 hPa)^(R gamma/g)`,
`W` a tanh cap poleward of 50 deg (width 10 deg). The winter cap follows the calendar:
`s = cos(2 pi (tyear - 0.04))`, NH amplitude `max(0, s)`, SH amplitude `max(0, -s)`, so each
vortex is present for half the year with a smooth onset and breakdown. Stratospheric relaxation
time `tau_strat_days` is a separate knob (PK02 and Held-Suarez: 40 d).

## Reference data

| reference | source | what is used |
|---|---|---|
| ERA5 monthly | CDS `reanalysis-era5-pressure-levels-monthly-means`, 25 levels 1000-1 hPa, zonal-meaned (`scripts/fetch_era5_strat_ref.py`, `cache/era5_ref/era5_zm_monthly_<Y>.nc`) | zonal-mean T and u climatology 300-1 hPa, polar-cap T |
| ERA5 daily | CDS `reanalysis-era5-pressure-levels`, u at 10 hPa, 6-hourly to daily mean, 1 deg (`cache/era5_ref/era5_u10hPa_daily_<Y>.nc`) | u(60N/60S, 10 hPa) series, SSW central dates |
| WACCM6 | CESM2.1.5 WACCM6 histSST member `f.e21.FWHIST.f09_f09_mg17.atmos-scale_fixedSST_1996-2014.001`, monthly `h0` T/U and daily `h6` Uzm (`/data/cesm2.1.5_output/histSST/`) | same-period climatology; day-of-year envelope for the vortex (free-running dynamics, so not year-matched) |
| ECHAM reference | `+experiment=ref_echam_sd`: JCM full ECHAM physics, ERA5 init, same nudging below 150 hPa, 2005, target sampled 12-hourly (memory) | what JCM's own radiation buys; run on GPU 1 by agreement |

## Runs

| run | physics | gamma [K/km] | tau_strat [d] | days | purpose |
|---|---|---|---|---|---|
| `p6_pk_smoke` | strat_pk | 4 | 40 | 5 | plumbing (0 NaN, exit 0) |
| `p6_pk_g4_t40` | strat_pk | 4 | 40 | 365 | PK02 defaults |
| `p6_pk_g4_t15` | strat_pk | 4 | 15 | 365 | radiative-timescale relaxation (Duncan, sec. 4.3) |
| `p6_pk_g2_t40` | strat_pk | 2 | 40 | 365 | weaker vortex |
| `ref_echam_sd_2005` | echam (full) | - | - | 365 | reference, GPU 1 |
| `p3_tracers_1yr` | strat_passive (Held-Suarez) | - | 40 | 365 | the Phase-3 baseline, for contrast |

## Acceptance (proposed in PLANS.md, PR 7)

ACCEPTANCE_TABLE

## Results

RESULTS

## Reading

READING
