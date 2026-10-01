# Phase 13c — Jucker relaxation + gravity-wave drag with the nudging cut off at 400 hPa, ten years, Hines with and without Lott-Miller (strat81, 1990–1999)

Status: **complete** (pipeline 2026-09-24 10:44 → 19:00 PDT on GPUs 1 and 2; chains 11:23–17:10, diagnostics 17:10–19:00).
Runs `p13jgn400_10yr` (Hines + Lott-Miller) and `p13jhn400_10yr` (Hines only), 1990–1999; references `p13juckergwd_5yr` (same
physics, nudged below 150 hPa, 5 yr), `p13jucker_5yr` (no drag), `p12echam_5yr` (full physics). Headline: **cutting the nudging
at 400 hPa removes the shallow branch and makes the stratosphere far too old**, with either drag configuration: tropical w* at
100 hPa 0.06 / 0.10 mm/s (WACCM6 0.40; the same physics nudged below 150 hPa gives 0.99), 100 hPa upward mass flux 6.7 / 9.2
×10⁹ kg/s (10.9), tropical entry age at 55 hPa 2.9 / 2.3 yr (WACCM6 1.19) and at 12 hPa 5.0 / 4.2 yr (2.90). The deep branch and
the mesosphere are fine — 10 hPa w* 0.36 / 0.58 (0.47), polar descent 2.3–6.2 mm/s, tropical ascent at 0.3 hPa 1.6–2.0 (ECHAM
1.9) — so the two branches separate cleanly: the shallow branch of the dry model is driven by the wave flux the ERA5-nudged
upper troposphere supplies, the deep branch and the mesosphere by the relaxation and the drag. **Lott-Miller off is better on
every stratospheric measure** (shallow branch +40 %, 10 hPa w* +0.22 mm/s, tropical entry ages 0.7–0.8 yr younger): the
orographic scheme takes momentum out of the deep branch and adds nothing the stratosphere needs here.

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
| tropical w* 100 hPa [mm/s] | 0.29 | 0.99 | 0.40 | **0.06** | **0.10** |
| tropical w* 30 hPa [mm/s] | 0.03 | 0.06 | 0.26 (within 1.5×) | −0.07 | 0.01 |
| tropical w* 10 hPa [mm/s] | 0.41 | 0.25 | 0.47 (within 1.5×) | 0.36 | 0.58 |
| tropical `aoa150` 12 hPa [yr] | 3.67 | 3.65 | 2.90 ± 0.4 | **5.02** | **4.21** |
| tropical `aoa150` 55 hPa [yr] | 1.56 | 1.12 | 1.19 | **2.91** | **2.26** |
| 50–70° `aoa150` 55 hPa [yr] | 3.62 | 2.06 | ≥ 3.6 | 3.65 | 3.96 |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | +0.32 / +0.08 / +0.23 | +0.15 / +0.31 / +0.90 | upward (ECHAM +0.96 / +1.31 / +1.92) | +0.05 / +0.44 / +1.63 | +0.26 / +0.78 / +1.89 |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | −1.76 / −2.92 | −2.97 / −4.60 | ECHAM −2.82 / −5.27 | −2.61 / −3.71 | −2.99 / −4.86 |
| cost [min/yr e2e] | 26–28 | 41 | ≤ 1.3× control (35) | 41 (2170–2200 d/hr) | 36 (2460–2510 d/hr) |

## Results

Figures and tables here: `hines_vs_lm_*` (the clean pair: both 10 yr, Lott-Miller on → off), `n400_*` (Jucker + GWD: cutoff
150 → 400 hPa, 5 → 10 yr), `jhn400_vs_jucker_*`, `jgn400_vs_echam_*`, `p13j*n400_10yr_aoa_*` (clocks vs CLaMS/WACCM),
`p13c_mesosphere.md/.png` (1994 and 1999 segments).

**The 400 hPa cutoff (`n400_metrics.md`).** Against the same physics nudged below 150 hPa: 100 hPa upward mass flux 21.6 → 6.7
×10⁹ kg/s (WACCM6 10.9), tropical w* 100 / 70 / 30 / 10 hPa 0.99 → 0.06 / 0.31 → 0.05 / 0.06 → −0.07 / 0.25 → 0.36 mm/s; every
clock 1.0–1.8 yr older (entry age 55 hPa tropics 1.12 → 2.91, 12 hPa 3.65 → 5.02). Part of the ageing is the longer chain (a
10-year clock against a 5-year one), but Phase 13 measured the cutoff alone at 5 yr as +0.5 yr, and the w* collapse at 100 hPa
is not a clock effect. With the ERA5 forcing stopped at ~7 km the dry Held-Suarez troposphere (no convection, no moist
baroclinic waves) generates far less wave flux into the lower stratosphere than ERA5's upper troposphere carries; the drag,
which over-drove the shallow branch when that flux was present, cannot replace it. Freeing the upper troposphere is therefore
not a route to a realistic shallow branch in the dry model.

**Lott-Miller off (`hines_vs_lm_metrics.md`, both 10 yr, nudged < 400 hPa).** Hines only: 100 hPa mass flux 6.7 → 9.2, tropical
w* 100 / 70 / 30 / 10 hPa 0.06 → 0.10 / 0.05 → 0.11 / −0.07 → 0.01 / 0.36 → 0.58 (WACCM6 0.40 / 0.21 / 0.26 / 0.47); entry age
55 hPa tropics 2.91 → 2.26, 12 hPa 5.02 → 4.21, 50–70° 55 hPa 3.65 → 3.96 (CLaMS 4.12). The orographic scheme weakens both
branches of the residual circulation and ages the tropics by 0.7–0.8 yr; Hines alone gives a deep branch slightly *above*
WACCM6 at 10 hPa. In the w* maps (`hines_vs_lm_wstar.png`) Lott-Miller's signature is broad extratropical descent through the
whole stratosphere in both winters. Cost 36 vs 41 min/yr.

**Mesosphere (`p13c_mesosphere.md`; tropics / NH cap / SH cap, mm/s, annual, 1994 and 1999 segments):** both runs keep the
Jucker-relaxation cell and the drag strengthens its top: tropical ascent at 0.3 hPa +1.6 / +1.8 (Hines + LM, 1994 / 1999) and
+1.9 / +2.0 (Hines only) against full ECHAM's +1.9; polar descent at 0.3 hPa 4.1–5.5 (Hines + LM) and 3.2–6.2 (Hines only)
against ECHAM's 4.2–7.0. At 1 hPa the tropical mean is small and changes sign between years (−0.4 to +0.3): the cell's base
sits near 1–2 hPa. The Hines-only run has the strongest mesospheric cell of every dry configuration so far.

**Caveat on the w* numbers.** The TEM covariances here are formed from every 4th 6-hourly frame (one phase of the day). The
Phase 15 sweep found that this daily-phase sampling biases the tropical w* in the middle stratosphere (tides), so the 30 hPa
values in every Phase 12–13 table are uncertain at the ±0.1 mm/s level; the clocks, the 100 hPa and the 10 hPa values and the
mesosphere table (where the signal is 1–6 mm/s) are not affected in their conclusions. Recompute with `--stride 1` before
quoting a 30 hPa number.

**Verdict.** Neither run is a candidate configuration: the 400 hPa cutoff fails the shallow-branch and tropical-age criteria by
a wide margin in both. The pair does settle the Lott-Miller question — off is better everywhere in the stratosphere — and shows
that the drag (Hines alone) plus the Jucker relaxation give a deep branch and a mesosphere at WACCM6/ECHAM strength. The
configuration to test next follows directly: **Jucker + Hines only, nudged below 150 hPa** (the shallow branch from ERA5's
troposphere, the deep branch from Hines, the mesosphere from the relaxation), with the Hines amplitude as the one knob if the
shallow branch overshoots as in Phases 13/13b.

## Open questions

- **Next configuration:** `p13_jucker` + Hines only (no Lott-Miller), nudged below 150 hPa, 5 yr on strat81 — the one
  combination not yet run. If its shallow branch overshoots (Phase 13b's Jucker + both schemes gave 100 hPa w* 0.99), lower
  `rms_launch_wind` (1.0 → 0.5–0.7 m/s) once. Also on the list: the Phase 15 sweep is exploring these knobs on GPU 0.
- Ages from a 10-year clock vs a 5-year one: with the 1 hPa lid Phase 11 expected equilibrium within ~10 yr; the 5-year numbers
  in Phases 12–13b are lower bounds by up to a few tenths of a year. A like-for-like age comparison needs equal chain lengths
  (the `hines_vs_lm` pair) or the clock's time series.
- The stride-4 tide bias in the TEM w* (Phase 15 finding): rerun `phase12_compare.py --stride 1` on the archived pairs when a
  30 hPa number matters.
