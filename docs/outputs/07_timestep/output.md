# Phase 7 — time-step sweep

Status: **in progress** (2026-09-03). Branch `phase7-timestep` (off `phase6-stratosphere`).

## Question this phase answers

How long a time step does the semi-Lagrangian dycore tolerate on the Phase 6 configuration before
the stratosphere (climatology, polar-night jets) or the tracers degrade, and what does that do to
throughput? Duncan's handover (sec. 4.6): "double the dycore step until the polar vortex
climatology or the age of air degrades. That step is the answer."

## Configuration

`+experiment=p6_pk run.time_step=<min>` — the chosen Phase 6 stratosphere (gamma 4, tau 15 d,
equinox-to-equinox season, vortex cooling faded above 3 hPa), ERA5 nudging below 150 hPa, four
passive tracers, T63L95, 2005. Nothing else changes with dt: the 6-hourly nudging target is
interpolated to whatever step is used, the sponge and relaxation rates are per unit time.
`sl_departure_iterations=2` (via `jcm_strat.main`) doubles dinosaur's fixed-point iterations
for the departure points, whose accuracy condition is dt x |grad V| < 1.

## Runs

| run | dt [min] | departure iterations | GPU |
|---|---|---|---|
| `p6_pk_g4_t15_s05_top3` (Phase 6) | 12 | 1 | 0 |
| `p7_dt30` | 30 | 1 | 0 |
| `p7_dt60` | 60 | 1 | 1 |
| `p7_dt120` | 120 | 1 | 2 |
| `p7_dt90` | 90 | 1 | - |
| `p7_dt60_it2`, `p7_dt120_it2` | 60, 120 | 2 | - |

## Acceptance

Within the Phase 6 band: T RMSE 100-1 hPa vs ERA5 within 1 K of the 12-min run, u RMSE within
1 m/s, polar-night jets within 5 m/s, tracer checks of Phase 3 unchanged (unity 1e-3, sai 0.5
percent, minima >= 0, no pull-up), no NaN. The longest dt inside the band is the answer.

## Results

RESULTS

## Reading

READING
