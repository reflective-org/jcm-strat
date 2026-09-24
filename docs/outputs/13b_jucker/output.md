# Phase 13b — the Jucker et al. (2013) relaxation in the dry model, without and with gravity-wave drag (strat81, 1990–1994)

Status: **complete** (pipeline 2026-09-23 21:25 PDT → 2026-09-24 04:24 PDT on GPU 1; chains 21:35–03:17, diagnostics 03:17–04:24).
Runs `p13jucker_5yr` and `p13juckergwd_5yr`; references `p12l81_5yr` (same grid, Polvani–Kushner, no drag), `p13gwd_5yr`
(strat63, Polvani–Kushner + drag), `p12echam_5yr` (full physics). Headline: **the Jucker relaxation alone ventilates the
mesosphere** — with no gravity-wave drag at all the tropical residual motion at 1–0.3 hPa turns upward (+0.3 / +0.1 / +0.2 mm/s
against −0.75 / −0.98 / −0.12 in the strat81 control) and the polar descent becomes 1.7–4.9 mm/s (control < 1, full physics
1.3–7). The deep branch improves too (tropical w* 10 hPa 0.31 → 0.41 mm/s, WACCM6 0.47; 12 hPa entry age 3.80 → 3.67 yr) and the
extratropical lower-stratospheric age stays right (50–70° 3.62 yr, CLaMS 4.12, WACCM6 entry age ~3.7). What it does not fix:
the 50–20 hPa stall (30 hPa w* 0.03 vs 0.26) and the tropical lower stratosphere, which gets slightly older (55 hPa entry age
1.31 → 1.56 vs 1.19). Adding Hines + Lott-Miller at JCM defaults on top repeats the Phase 13 damage — shallow branch 2.5× WACCM6,
extratropical 55 hPa entry age 2.06 yr, 10 hPa ascent back down to 0.25 — while strengthening the mesospheric cell further.
**The Jucker relaxation without drag is the best dry configuration so far; the drag as configured is not usable.**

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
| tropical w* 30 hPa [mm/s] | 0.02 | 0.26 (within 1.5×) | 0.03 | 0.06 |
| tropical w* 10 hPa [mm/s] | 0.31 | 0.47 (within 1.5×) | **0.41** | 0.25 |
| tropical w* 100 hPa [mm/s] | 0.35 | 0.40 (PK + drag: 1.05) | 0.29 | **0.99** |
| tropical `aoa150` 12 hPa [yr] | 3.80 | 2.90 ± 0.4 | 3.67 | 3.65 |
| tropical `aoa150` 55 hPa [yr] | 1.31 | 1.19 (not worse) | 1.56 | 1.12 |
| 50–70° `aoa150` 55 hPa [yr] | 3.64 | ≥ 3.6 (PK + drag: 2.47) | **3.62** | **2.06** |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | −0.75 / −0.98 / −0.12 | upward (ECHAM +0.96 / +1.31 / +1.92) | **+0.32 / +0.08 / +0.23** | **+0.15 / +0.31 / +0.90** |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −0.07 / −0.51 | ECHAM −2.82 / −5.27 | **−1.76 / −2.92** | **−2.97 / −4.60** |
| `aoa150` latitude std at 3 / 1.5 hPa [yr] | 0.05 / 0.05 | > 0.05 (ECHAM 0.18 / 0.14) | 0.12 / 0.10 | 0.12 / 0.11 |
| cost vs strat81 control [min/yr e2e] | 26–27 | ≤ 1.3× | 26–28 (3415–3570 d/hr; 1.0×) | 41 (2180 d/hr; 1.6× — the drag terms on 81 levels) |

## Results

Figures and tables in this directory: `jucker_*` (relaxation swap on strat81, vs `p12l81_5yr`), `jucker_gwd_*` (drag added under
the new relaxation), `jucker_gwd_vs_gwd_*` (both drag runs: PK/strat63 vs JFV/strat81), `jucker_gwd_vs_echam_*`, `p13jucker*_aoa_*`
(each clock vs CLaMS/WACCM), `p13b_mesosphere.md/.png` (all Phase 12/13 runs).

**Run 1, Jucker relaxation, no drag (`jucker_metrics.md`).** Annual upward mass flux 100 / 10 hPa: 11.8 → 10.6 / 1.34 → 1.29
×10⁹ kg/s (WACCM6 10.9 / 1.37). Tropical w* 100 / 70 / 30 / 10 hPa: 0.35 → 0.29 / 0.26 → 0.17 / 0.02 → 0.03 / 0.31 → 0.41 mm/s
(WACCM6 0.40 / 0.21 / 0.26 / 0.47). The w* maps (`jucker_wstar.png`) show the change: a coherent summer-to-winter cell above
~5 hPa in both solstice seasons — DJF ascent over the whole southern hemisphere and descent over the northern polar cap, JJA the
mirror image — where the Polvani–Kushner run has a patchwork. Below 10 hPa the two runs are alike. Ages (entry-age clock): tropics
55 hPa 1.31 → 1.56 (WACCM6 1.19), 12 hPa 3.80 → 3.67 (2.90); 50–70° 55 hPa 3.64 → 3.62 (WACCM6 ~3.7, CLaMS surface clock 4.12);
surface clock tropics 55 hPa 3.07 → 3.34 (the dry troposphere's transit, Phase 12 addendum). Cost unchanged (26–28 min/yr).

**Run 2, Jucker + Hines + Lott-Miller (`jucker_gwd_metrics.md`, `jucker_gwd_vs_gwd_metrics.md`).** The drag repeats what it did
under Polvani–Kushner: 100 hPa mass flux 10.6 → 21.6 (2× WACCM6), tropical w* 100 hPa 0.29 → 0.99, 70 hPa 0.17 → 0.31,
10 hPa 0.41 → 0.25; entry age 55 hPa tropics 1.56 → 1.12 (WACCM6 1.19) but 50–70° 3.62 → 2.06 (the full-physics failure, now
worse); 12 hPa tropics unchanged 3.65. Against the strat63 PK drag run the relaxation change gives +0.23 mm/s at 10 hPa and
−0.4 yr in the extratropics — the drag dominates the lower stratosphere whatever the relaxation. Cost 1.6× (41 min/yr): the two
drag terms on 81 levels.

**Mesosphere (`p13b_mesosphere.md`, 1994 segments, annual mean, tropics / NH cap / SH cap, mm/s):**

| run | 10 hPa | 5 hPa | 2 hPa | 1 hPa | 0.5 hPa | 0.3 hPa | `aoa150` lat std at 3 / 1.5 hPa [yr] |
|---|---|---|---|---|---|---|---|
| strat81 control (PK) | +0.28 / −0.93 / −0.67 | +0.78 / −1.01 / −0.59 | +0.35 / −0.49 / −0.08 | −0.75 / −0.71 / −0.74 | −0.98 / −0.07 / −0.51 | −0.12 / −0.23 / −1.06 | 0.05 / 0.05 |
| PK + GWD (strat63) | +0.03 / −1.16 / −1.04 | +0.21 / −0.39 / −0.79 | +0.19 / −0.19 / −0.66 | −0.39 / −0.31 / −0.69 | −0.73 / −0.42 / −0.66 | −0.64 / −0.28 / −0.39 | 0.10 / 0.07 |
| **Jucker** | +0.36 / −0.51 / −0.66 | +1.09 / −0.79 / −0.78 | +0.67 / −0.94 / −1.05 | **+0.32 / −1.74 / −2.51** | **+0.08 / −1.76 / −2.92** | **+0.23 / −3.07 / −4.89** | 0.12 / 0.10 |
| Jucker + GWD | +0.19 / −0.06 / −0.56 | +0.58 / −0.29 / −0.81 | +0.58 / −0.81 / −1.78 | +0.15 / −1.94 / −3.42 | +0.31 / −2.97 / −4.60 | +0.90 / −4.53 / −6.07 | 0.12 / 0.11 |
| full ECHAM | +0.88 / −1.55 / −1.23 | +0.96 / −1.71 / −1.22 | +0.60 / −0.42 / −1.76 | +0.96 / −1.29 / −3.19 | +1.31 / −2.82 / −5.27 | +1.92 / −4.22 / −7.04 | 0.18 / 0.14 |

With the JFV equilibrium temperature the dry model has a mesospheric cell of the right sign and roughly half the full-physics
strength — without any parameterised wave drag. The relaxation itself supplies it: with a 4–6 day timescale toward a 300 K summer
and 200 K winter stratopause the meridional temperature gradient above 5 hPa is an order of magnitude larger than under the flat
standard-atmosphere T_e, the resolved waves and the sponge's Rayleigh friction provide the momentum sink, and the resulting
summer-to-winter flow descends 1.7–4.9 mm/s over the winter pole. Adding the drag strengthens the top of the cell (0.3 hPa:
+0.9 / −4.5 / −6.1, close to ECHAM's +1.9 / −4.2 / −7.0) at the cost of the lower stratosphere.

**Verdict against the acceptance criteria.** Run 1: mesosphere met (upward tropics at 1–0.3 hPa, polar descent > 1 mm/s);
10 hPa w* met (0.41 vs 0.47); extratropical 55 hPa entry age met (3.62); cost met; 30 hPa w* failed (0.03 vs 0.26, unchanged);
tropical entry age 12 hPa 3.67 vs 2.90 ± 0.4 failed (0.13 better), 55 hPa 1.56 vs "not worse than 1.31" failed (0.25 worse).
Run 2: mesosphere and tropical 55 hPa met, everything else failed as in Phase 13 (extratropics 2.06, shallow branch 2.5×).

## Open questions

- **The 50–20 hPa stall is now the one defect of the dry model's circulation** (30 hPa w* 0.03 vs WACCM6 0.26 in every dry
  configuration, with or without the JFV relaxation). By downward control it is the wave drag between ~30 and 5 hPa that is
  missing — the region where the parameterised drag should act but where Hines + Lott-Miller at JCM defaults instead put their
  momentum below 50 hPa. Candidates, cheapest first: (a) Hines alone with a weaker launch spectrum (`rms_launch_wind` 0.5 m/s)
  and Lott-Miller off, to see whether the low deposition is the orographic scheme's; (b) a per-term drag-tendency diagnostic on
  one segment; (c) a Rayleigh drag profile confined to 30–1 hPa as an idealised stand-in.
- The tropical lower stratosphere is 0.25 yr older under the JFV relaxation (55 hPa entry age 1.56 vs 1.31, WACCM6 1.19) because
  the 100–70 hPa upwelling is 15–35 % weaker (JFV tau is 12–39 d there against PK's 15 d, and its T_e at 100 hPa is colder). A blend
  boundary higher than 100 hPa (p_bd 70 hPa) would keep PK's shallow branch — untested.
- The sponge damps temperature toward 250 K in the top four levels (tau 1.5 h at the top) while the JFV T_e there is 150–330 K;
  the cell forms anyway. A sponge without temperature damping is a separate test.
- Production choice: `p13_jucker` (strat81, JFV relaxation, no drag) is the candidate replacement for the Phase 11/12 dry
  configuration. The clocks kept the 1 hPa lid in these runs; with a ventilated mesosphere the lid can be tested off
  (`lid_p_hpa: null`) on one segment.
