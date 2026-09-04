# Phase 8 — QBO nudging: giving the stripped model the tropical wind oscillation it cannot grow

Status: **in progress**. Branch `phase8-qbo-nudging` (off `phase6-circulation`).

## Why

Phase 6 gave the model a defensible stratosphere (Polvani-Kushner target, polar-night jets, most
sudden warmings) but no QBO: the equatorial wind sits in steady easterlies of 12–14 m/s with a
deseasonalised variability of 4 m/s where ERA5 has 17 (Phase 6 addendum). The QBO is driven by
tropical waves launched by convection, which the dry model does not have, and needs ~500–700 m
vertical spacing in the tropical lower stratosphere; neither can be supplied cheaply. For aerosol
transport the QBO matters directly: it modulates tropical upwelling and the subtropical mixing
barrier, so an injected layer's residence time in the tropics and its leak to mid-latitudes differ
by tens of percent between phases (Pinatubo; every SAI study reports it). Under specified dynamics
the standard remedy is to nudge the tropical stratospheric wind to observations (issue #6); this
phase does that and measures what changes.

## What is nudged, towards what

`jcm_strat/qbo_nudging.py` (`QboNudging`, in `physics/strat_pk_qbo.yaml`, `+experiment=p8_qbo`):

| | choice | reason |
|---|---|---|
| **Target** | ERA5 monthly-mean zonal-mean zonal wind, CDS `reanalysis-era5-pressure-levels-monthly-means`, 25 levels 1–1000 hPa, 2005–2009 (`cache/era5_ref/era5_zm_monthly_<year>.nc`), interpolated to the model's latitudes and reference pressures in ln p, linearly in time between month centres | Your preference was ERA5 and the data is there (the CDS fetch made for Phase 6 reaches 1 hPa, unlike the WeatherBench2 store that stops at 50 hPa). ERA5 is also what the troposphere is already nudged to, so the whole column follows one reanalysis. Monthly means are enough: the QBO evolves over months and descends about 1 km per month. |
| **What is relaxed** | only the **zonal mean** of the model's zonal wind: at every longitude of a latitude row the same tendency, −(ū_model − ū_ERA5)/τ, is applied | The waves that do the transport are left untouched; only the mean flow they propagate through is corrected. Relaxing the full wind field would damp the eddies too. |
| **Where** | weight 1 for \|lat\| ≤ 15°, cos² taper to 0 at 25°; full weight 9–40 hPa, log-linear taper to 0 at 4 and 90 hPa | The QBO's domain. Stays clear of the tropospheric nudging cutoff at 150 hPa below and of the SAO region above 4 hPa. |
| **How fast** | τ = 10 days | WACCM's QBO-nudging choice: slow enough not to fight the resolved waves step by step, fast enough to hold the observed phase. |
| **Everything else** | Phase 6 as chosen (Polvani-Kushner γ = 4 K/km, τ_strat 15 d, seasonal winter cap faded above 3 hPa; ERA5 u/v/T nudging below 150 hPa; four passive tracers; T63L95; dt 12 min) | one change at a time |

Implementation notes: the term runs on the column path; the zonal mean is a segment mean over the
columns of each latitude row; the fraction of year comes from `forcing.solar.tyear` like the
seasonal Polvani-Kushner term and the calendar year is a config argument that the segment chain
passes per year (`EXTRA_PER_YEAR="physics.terms.qbo_nudging.year={year}"`). Two CPU tests check the
weights and that the tendency equals −k w (ū − target) exactly. One hazard found and fixed: with
JAX's per-term checkpointing on, adding the term made the compiled step hold a second copy of the
29 GB nudging target on the GPU (`p8_qbo_2005_oom`); `checkpoint_terms: false` in the QBO physics
config removes that with no change to the results.

## Runs

| run | days | purpose | before |
|---|---|---|---|
| `p8_qbo_2005` | 365 | first year with QBO nudging | `p6_pk_g4_t15_s05_top3` (Phase 6 chosen configuration, same year) |
| `p8_2005` … `p8_2009`, aggregate `p8_5yr` | 1826 | the 5-year chain with tracers | `p6_5yr` (Phase 6 chain) |

## Acceptance (proposed)

| check | threshold |
|---|---|
| equatorial 5°S–5°N monthly u vs ERA5, 10–70 hPa | RMS < 5 m/s (Phase 6: 17 m/s) and deseasonalised std within 30 % of ERA5's at 20 and 30 hPa over 2005–2009 |
| the change is confined to the tropics | RMS change of time-mean zonal-mean u for \|lat\| > 30°, 1–100 hPa, < 2 m/s; troposphere unchanged |
| polar vortex, sudden warmings, tracer conservation | unchanged from Phase 6 within noise |
| age of air | reported; the tropical pipe's contrast with the extratropics is the quantity expected to move |
| throughput | within 5 % of Phase 6 |

## Results

RESULTS

## Reading

READING
