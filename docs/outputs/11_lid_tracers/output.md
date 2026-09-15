# Phase 11 — tracer lid and revised production tracers: two 5-year review runs (1990–1994)

Status: **running** (`scripts/phase11_run5.sh`, tmux `strat_p11_run5`, log `runs/p11_run5.log`). Started
2026-09-15 (Pacific). Results, figures and the A-vs-B decision are appended below when the chains finish.

## Why

The 1990–2019 Phase 10 run (`docs/outputs/10_production`, `p10_30yr_aoa_*.png`) showed that the model
mesosphere is never ventilated: above ~1 hPa the mean age of air is uniform in latitude and equal to the
run length (23 yr after 30 yr), and that air leaks down until the stratosphere is 3–5× too old (55 hPa
tropics 6.5 yr vs CLaMS 1.3; 12 hPa 13 vs 3.7) and still growing at 0.2–0.5 yr per year. The tropical
upward mass flux at 100–10 hPa matches WACCM6 (`docs/outputs/09_resolution/strat/strat_metrics.md`), so
this is not a weak Brewer–Dobson circulation but a stagnant lid — no gravity-wave drag, a Rayleigh sponge
in the top four levels, a semi-Lagrangian top boundary with nothing above. The same old air explains
why N2O and CFC-11 sit ~6 km too low: air that has been to the mesosphere comes back N2O-free. The
Phase 9 statement "0.8 yr too old at 55 hPa" was a spin-up artefact (a 5-year clock cannot exceed 5 yr).

Susanne (2026-09-15) asked for a redo with: a fix for the stagnant top (her suggestion: use the sponge
as a sink or relaxation), no amplitudes, a sharp-edged twin of every pulse and source, and no surface
sink. Two 5-year runs first, then the chosen one is extended to 30 years.

## What changed against Phase 10 (`jcm_strat/advection_tracers.py`, `physics/strat_pk_qbo_prod11.yaml`)

| item | Phase 10 (`p10_prod`) | Phase 11 (`p11a_prod` / `p11b_prod`) |
|---|---|---|
| model top | Rayleigh sponge (4 levels above 0.2 hPa), tracers free | sponge unchanged; **tracer lid above 1 hPa**: relaxation with tau 1 d to WACCM6 REF-D1's zonal-mean mean age (`aoa_ref` in `waccm_tracer_ref.nc`, 1990–2019 annual mean, ~4.4 yr, flat in latitude) for `aoa150`, the same + 110 d (~0.3 yr tropospheric transit) for `aoa` and `aoa_sfc`; n2o / cfc11 to their WACCM state (≈ 0 there) |
| pulses | 5 Gaussian blobs, amplitudes 1.0 / 0.5 / 0.2 / 0.1 / 0.05 | **10**: the 5 Gaussian blobs at unit amplitude + a **sharp-edged twin** each (`pulse_<i>_box`: 1 inside the 12° cap × ±0.25 decades, 0 outside — the same nominal size) |
| continuous sources | 4 Gaussian, amplitudes 1.0 / 0.5 / 0.2 / 0.3, S/90 d per step | **8**: unit amplitude + box twins (`src_<i>_box`), S/90 d per step |
| surface sink | pulses and sources relaxed to 0 in the lowest two layers | **none** (`surface_sink: false`): pulses conserve their mass, sources and sai grow linearly |
| lid sink for pulses / sources / sai | — | **A: none** (`lid_sink_injections: false`); **B: relaxed to 0 above 1 hPa** (tau 1 d) |
| tracers in the output | 15 | 24 (+ u, v, T, q, omega, p_s) |
| everything else | strat63, ERA5 nudging < 150 hPa tau 6 h, PK stratosphere, QBO tau 1 d mean-preserving to 1 hPa, 6-hourly instantaneous, Gregorian calendar, clocks + n2o/cfc11 out of the mass fixer | unchanged |

Why a lid and not a dynamical fix: the mesospheric circulation is gravity-wave driven and the dry model
has no drag above the sponge; adding one is a tuning project (DEFERRED, Phase 11). Prescribing the tracers
where the dynamics are not credible is the same logic as nudging the troposphere to ERA5. Why 1 hPa and
not the sponge (0.2 hPa): the age field is flat in latitude, i.e. shows no circulation, down to 1–2 hPa;
a lid at the sponge would leave a stagnant layer between 0.2 and 1 hPa. Why WACCM's age and not zero:
relaxing the clocks to zero would make the mesosphere a second surface and the descending polar branch
artificially young.

Why sites are unchanged: pulses (0°/0°E/30 hPa, 45°N/120°E/70 hPa, 60°S/240°E/10 hPa, 30°N/300°E/3 hPa,
15°S/60°E/300 hPa), sources (0°/180°E/20 hPa, 30°N/60°E/100 hPa, 60°S/300°E/5 hPa, 30°S/240°E/55 hPa);
amplitude only scaled the field (Phase 10 linearity check), so it carried no information.

## Runs

| run | experiment | GPU | years | notes |
|---|---|---|---|---|
| `p11a_smoke5`, `p11b_smoke5` | 5 days from 1990-01-01 | 0 / 1 | — | GPU smoke, lid and shapes checked in the log |
| `p11a_1990..1994` → `p11a_5yr` | `p11a_prod` | 0 | 1990–1994 | A: no sink anywhere |
| `p11b_1990..1994` → `p11b_5yr` | `p11b_prod` | 1 | 1990–1994 | B: lid sink for pulses / sources / sai |

Command (both chains from `scripts/phase11_run5.sh`; a single chain by hand):
```
EXPERIMENT=p11a_prod PREFIX=p11a SCHEME=calendar YEARS=1990-1994 AGG=p11a_5yr SAVE_INTERVAL=0.25 GPU=0 bash scripts/chain_segments.sh
```
Extension of the chosen run to 2019: the same PREFIX with `YEARS=1990-2019` (finished segments are skipped,
the chain continues from the 1994 checkpoint; KEY_DECISIONS #38 — never the other prefix).

## Acceptance checks (filled when the chains finish)

| check | expectation | result |
|---|---|---|
| lid | age above 1 hPa within 0.1 yr of WACCM + offset after the first days; no latitude-flat plateau below the lid | |
| age of air vs CLaMS (`p11?_5yr_aoa_*.png`) | bounded after 5 yr; 55 hPa tropics and 50–70° closer to CLaMS 1.3 / 4.1 yr than Phase 10's 2.2 / 3.8 at the same age of the run | |
| pulses | box twins injected exactly (first-frame RMSE ~0 where resolved); A: global mass constant to the fixer's roundoff; B: mass falls only through the lid | |
| sources / sai | A: linear growth = emission; B: growth minus lid removal | |
| n2o / cfc11 | in [0, 1]; stationary within ~2 yr; isopleths higher than Phase 10's (`p11?_5yr_steady_clocks.png`) | |
| throughput | ~25–35 min per year per chain with two chains sharing the CPU output path | |
