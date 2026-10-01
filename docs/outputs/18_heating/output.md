# Phase 18 — T_e correction with ERA5's diabatic heating as the tropical target (strat81, GPU 0)

Status: **running unattended** (tmux `strat_p18`, log `runs/p18.log`, branch `phase18-heating` in the main `jcm-strat` checkout).
Susanne, 2026-10-01: "I need age of air to look like that of CLaMS, and the tropical upwelling needs to match ERA5 better too" ...
"can you set this up what you just laid out and run it? Use GPU 0". Nothing is pushed by the pipeline.

## Why

Phase 17 fitted the JFV equilibrium temperature to ERA5's temperature everywhere: T RMSE 5.4 → 1.3 K, u 3.7 → 2.5 m/s, but the
age got older (0.44 → 0.51 yr), the subtropical barrier leakier and w* moved away from ERA5. The model's own Newtonian heating
(T_e − T)/τ against ERA5's total diabatic heating (`THETA_DOT_TOT` of the CLaMS v3 ERA5 reanalysis files, 2000–2014 climatology,
as a temperature tendency θ̇ (p/1000)^κ; its units attribute is a placeholder, the values are K/day) shows why — annual means,
K/day, at 0 / 15 / 25 / 35°:

| p | Phase 16 `mix10trop` (start) | ERA5 | Phase 17 `A4` |
|---|---|---|---|
| 100 hPa | 0.39 / 0.42 / 0.41 / 0.25 | 0.41 / 0.40 / 0.32 / 0.11 | 0.40 / 0.43 / 0.43 / 0.27 |
| 70 hPa | 0.31 / 0.35 / 0.27 / 0.11 | 0.15 / 0.36 / 0.33 / 0.10 | 0.13 / 0.15 / 0.06 / −0.02 |
| 50 hPa | 0.34 / 0.31 / 0.20 / 0.10 | 0.19 / 0.21 / 0.17 / 0.01 | 0.23 / 0.25 / 0.18 / 0.09 |
| 30 hPa | 0.30 / 0.25 / 0.11 / 0.05 | 0.27 / 0.21 / 0.10 / −0.06 | 0.27 / 0.25 / 0.14 / 0.06 |
| 10 hPa | 0.43 / 0.24 / −0.01 / −0.19 | 0.65 / 0.49 / 0.29 / 0.03 | 0.70 / 0.42 / 0.12 / −0.10 |

The start state heats too much at the equator at 70–50 hPa and too far poleward at 100 hPa (the upward mass flux at 70 hPa is
+19 % annual, +42 % in JJA against ERA5 while the 15S–15N w* matches: the upwelling region is too wide). Phase 17's temperature
target cut the 70 hPa heating at 15–25° to less than half of ERA5's — the weaker shallow branch and the older ages. In the
tropics the cross-isentropic transport is the diabatic heating itself (CLaMS uses θ̇ as its vertical velocity), so the target
there should be ERA5's heating, not its temperature.

## Method

* `scripts/teq_correction.py --heating-target`: inside the mask (|lat| ≤ 30° and p ≥ 30 hPa full weight, cos² tapers to zero at
  40° and 15 hPa) the update is dT_e −= α τ (Q_model − Q_ERA5), with Q_model = (T_e − T)/τ from the run's monthly-mean T and the
  T_e it used; outside, Phase 17's dT_e −= α (T_model − T_ERA5). α = 0.7, the same smoothing, cap and 100 hPa / 1 hPa handling.
* H1 = Phase 17's converged `A4` outside the mask (its temperature and wind gains) plus the first heating step inside, computed
  from `mix10trop` itself; H2…H4 iterate from their own runs. Each iteration runs 1998–1999 from `mix10trop`'s 1997 state (with
  the Rayleigh drag, as `mix10trop` and `A4`); the best-scoring correction then runs ten years 1990–1999 from ERA5 (`H_final`).
* Score: `sweep_score.py --w-metric full` — the w* term is now the mean |ln ratio| against ERA5 over annual, DJF and JJA w* at
  100/70/50/30/10 hPa AND the upward mass flux at 100/70/30/10 hPa (the width of the upwelling region), with age vs CLaMS, u
  and T vs ERA5 as before. The references `p16_mix10trop`, `p17_A2`, `p17_A4` are re-scored with the same metric.

## Leaderboard

<!-- leaderboard:start -->
_no scored runs yet_
<!-- leaderboard:end -->

## Results

_to be written when the run finishes_

## Run log
- 2026-10-01 11:34 PDT — started (GPU 0, commit 678dd06, 4 iterations, alpha 0.7)
