# Phase 13 — gravity-wave drag for the dry model, the same on native L95, and a 400 hPa nudging cutoff (1990–1994)

Status: **complete** (chains 2026-09-23 11:03–14:28 PDT on GPUs 1/2/3, diagnostics 19:00 PDT; tmux `phase13-gravity-wave`,
log `runs/p13_run.log`). Runs `p13gwd_5yr`, `p13gwdl95_5yr`, `p13l81n400_5yr`; the Phase 12 runs `p12ctl_5yr`, `p12l81_5yr`,
`p12echam_5yr` are the references. Headline: **the drag closes the tropical age gap but not by ventilating the mesosphere.**
Hines + Lott-Miller at JCM defaults put their momentum into the lower stratosphere: the shallow branch becomes 2.6× WACCM6
(tropical w* 100 hPa 1.05 vs 0.40 mm/s), the tropical surface-clock age at 55 hPa drops from 2.74 to 1.35 yr (CLaMS 1.33)
and at 12 hPa from 4.60 to 3.80 (3.68), the extratropical lower stratosphere becomes 1.4 yr too young (2.71 vs 4.12) — the
same signature as the full physics, which uses the same two schemes. The deep branch got *weaker* (tropical w* 10 hPa 0.13 →
0.02 mm/s, WACCM6 0.47) and the tropical mesosphere is still **downward** above ~1.5 hPa (−0.4 to −0.7 mm/s; on L95 −1.5
at 0.5 hPa), with no polar descent cell: the drag is exhausted below the stratopause. Native L95 changes the picture by
hundredths of a mm/s and 0.1–0.2 yr — the circulation is set by the drag, not the grid. Cutting the ERA5 nudging at
400 hPa instead of 150 (strat81, no drag) *weakens* the shallow branch (100 hPa w* 0.35 → 0.12) and ages the whole
stratosphere by 0.3–0.6 yr, while the 10 hPa ascent rises to 0.44 mm/s (WACCM6 0.47): the model's own upper troposphere
supplies less wave flux into the lower stratosphere than ERA5's, but its deep branch is not worse.

## Why

The Phase 12 record (`docs/outputs/12_circulation/output.md`) ends with two findings that set this phase: (1) the old
stratospheric age of air is the dry Polvani–Kushner configuration's — JCM's full physics puts the tropical age on CLaMS
under the same nudging; (2) the dry runs' mesosphere is not ventilated: the tropical residual motion is *downward* from
~1.5 hPa to the sponge (−0.4 to −1 mm/s), there is no polar descent, and the age between 20 and 1 hPa is flat in latitude
because lid-valued air is pushed down. Above the stratopause the dry model has no forcing but the sponge and the
relaxation, and neither drives a poleward flow. Gravity-wave momentum deposition is what ventilates the mesosphere in
the atmosphere and in the full-physics run, and by downward control the drag above 30 hPa is also what sets the
50–20 hPa ascent that stalls in every dry configuration. Susanne, 2026-09-23: run the drag-only version, keep the clocks
relaxed to WACCM above 1 hPa, add the same run on JCM's native L95 grid ("definitely use all levels for troposphere and
stratosphere"), and a strat81 run nudged only up to 400 hPa.

## Runs

| run | grid | drag | nudging cutoff | one change against |
|---|---|---|---|---|
| `p13_gwd` | strat63 (8 + 47 + 8) | Hines (launch 634 hPa → 589 hPa on strat63, rms 1.0 m/s) + Lott-Miller (JCM defaults) | 150 hPa | `p12ctl_5yr` |
| `p13_gwd_l95` | native L95 (22 + 47 + 26; L95 sponge, 10 levels) | same (launch level 10 = 634 hPa) | 150 hPa | `p13gwd_5yr` (and `p12echam_5yr`, same grid) |
| `p13_l81_n400` | strat81 (8 + 47 + 26) | none | **400 hPa** | `p12l81_5yr` |

Everything else is the Phase 12 control's: ERA5 nudging of u, v, T with tau 6 h (lowest 2 levels free), QBO nudging to
1 hPa (tau 1 d), Polvani–Kushner relaxation (gamma 4 K/km, tau 15 d, vortex cooling faded above 3 hPa), the four clocks
with the 1 hPa tracer lid, injections integrated but not written, 6-hourly output, Gregorian calendar.

Implementation notes: JCM's `HinesGwd` launches its spectrum from a fixed *count* of levels above the surface (10 =
634 hPa on L95); on the 8-layer tropospheres of strat63/77 that would be 126 hPa, so `jcm_strat.gwd.HinesGwdLaunch`
takes the launch level as a pressure and resolves it per level table (unit-tested on 63/81/95). The drag terms read
the pressure/height/density diagnostics of `MoistAirColumnState`, which therefore heads the dry physics list. The
Lott-Miller descriptors (orostd, orosig, orogam, orothe, oropic, oroval) are in the T63 terrain file the dry runs load.

## Acceptance (PLANS Phase 13; entry-age clock `aoa150` vs WACCM6, w* vs WACCM6 histSST)

| quantity | control (`p12ctl_5yr`) | target | gwd | gwd_l95 | l81_n400 |
|---|---|---|---|---|---|
| tropical w* 30 hPa [mm/s] | 0.09 | 0.26 (within 1.5×) | 0.19 | 0.11 | −0.03 (l81 control 0.02) |
| tropical w* 10 hPa [mm/s] | 0.13 | 0.47 (within 1.5×) | **0.02** | 0.08 | **0.44** (l81 control 0.31) |
| tropical `aoa150` 12 hPa [yr] | 3.77 | 2.90 ± 0.4 (WACCM6) | 3.55 | 3.39 | 4.34 (l81 control 3.80) |
| tropical `aoa150` 55 hPa [yr] | 1.29 | 1.19 (not worse) | 1.10 | 1.04 | 1.90 (l81 control 1.31) |
| 50–70° `aoa150` 55 hPa [yr] | 3.60 | ≥ 3.7 (CLaMS sfc 4.12) | **2.47** | **2.38** | 4.09 (l81 control 3.64) |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | −0.39 / −0.74 / −0.36 | upward (ECHAM +0.96 / +1.31 / +1.92) | **−0.39 / −0.73 / −0.64** | **−0.50 / −1.55 / −1.32** | −0.40 / −0.32 / +0.58 |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | +0.02 / −0.68 | ECHAM −2.82 / −5.27 | −0.42 / −0.66 | −0.39 / −0.69 | −0.62 / −0.53 |
| `aoa150` latitude std at 3 / 1.5 hPa [yr] | 0.05 / 0.05 | > 0.05 (ECHAM 0.18 / 0.14) | 0.10 / 0.07 | 0.11 / 0.08 | 0.01 / 0.03 |
| polar-night jets vs control | — | no weaker | not evaluated | not evaluated | not evaluated |
| cost vs control [min/yr e2e] | 27–31 | ≤ 1.3× | 31–33 (2580–2690 d/hr stepping) | 51–54 (1860–1920 d/hr; 1.7× — L95, not the drag) | 26–27 (3540–3590 d/hr) |

## Results

Figures and tables in this directory: `gwd_*` (drag vs control), `gwd_l95_*` (strat63 → L95 with drag), `gwd_l95_vs_ctl_*`,
`gwd_vs_echam_*` and `gwd_l95_vs_echam_*` (dry + drag vs JCM full physics, the latter on the same L95 grid), `l81_n400_*`
(nudging cutoff 150 → 400 hPa on strat81), `p13*_aoa_*` (each clock vs CLaMS/WACCM), `p13_mesosphere.md/.png`.

**Run 1, drag on strat63 (`gwd_metrics.md`).** Annual upward mass flux at 100 / 70 / 30 / 10 hPa: 12.9 → 23.8 / 8.3 → 11.4 /
3.3 → 3.7 / 1.26 → 1.44 ×10⁹ kg/s (WACCM6 10.9 / 6.1 / 3.1 / 1.37). Tropical w* 100 / 70 / 50 / 30 / 10 hPa: 0.40 → 1.05 /
0.33 → 0.46 / 0.26 → 0.33 / 0.09 → 0.19 / 0.13 → 0.02 mm/s (WACCM6 0.40 / 0.21 / 0.20 / 0.26 / 0.47). The extra upwelling is
almost all below 50 hPa; the 30 hPa stall eases a little and the 10 hPa ascent collapses. Ages: surface clock 55 hPa tropics
2.74 → 1.35 (CLaMS 1.33), 50–70° 4.58 → 2.71 (4.12); 12 hPa tropics 4.60 → 3.80 (3.68); entry-age clock 55 hPa tropics
1.29 → 1.10, 50–70° 3.60 → 2.47, 12 hPa tropics 3.77 → 3.55 (WACCM6 2.90). Against the full-physics run (`gwd_vs_echam`)
the dry + drag ages agree to 0.0–0.2 yr everywhere while its shallow branch is 30 % weaker and its deep branch 40× weaker
(10 hPa w* 0.02 vs 0.87) — the two configurations reach the same lower-stratospheric age by different routes.

**Run 2, the same on native L95 (`gwd_l95_metrics.md`).** Differences to run 1: mass fluxes within 0.3 ×10⁹ kg/s, tropical w*
within 0.08 mm/s (30 hPa 0.19 → 0.11, 10 hPa 0.02 → 0.08), ages 0.1–0.2 yr younger. The vertical grid is not what limits this
model; the drag is. Cost 1.7× (L95's 95 levels, not the drag terms: run 1 costs 1.1× the control).

**Run 3, strat81 nudged only below 400 hPa (`l81_n400_metrics.md`).** Shallow branch weaker: 100 hPa mass flux 11.8 → 7.7
(WACCM6 10.9), tropical w* 100 hPa 0.35 → 0.12 (0.40); 30 hPa 0.02 → −0.03; 10 hPa 0.31 → 0.44 (0.47). Every clock older by
0.2–0.7 yr (entry-age 55 hPa tropics 1.31 → 1.90 vs WACCM6 1.19; 12 hPa 3.80 → 4.34 vs 2.90). Freeing the upper troposphere
removes wave flux into the lower stratosphere rather than adding it; the deep branch, driven from higher up, is unaffected or
slightly better. Not a fix for the age, but it says the ERA5-nudged upper troposphere is not what holds the deep branch back.

**Mesosphere (`p13_mesosphere.md`, 1994 segments, annual mean, tropics / NH cap / SH cap, mm/s):**

| run | 10 hPa | 5 hPa | 2 hPa | 1 hPa | 0.5 hPa | 0.3 hPa | `aoa150` lat std at 3 / 1.5 hPa [yr] |
|---|---|---|---|---|---|---|---|
| dry control | +0.11 / −1.00 / −0.79 | +0.57 / −0.90 / −0.72 | +0.50 / −0.26 / −0.25 | −0.39 / −0.53 / −0.96 | −0.74 / +0.02 / −0.68 | −0.36 / −0.15 / −1.11 | 0.05 / 0.05 |
| strat81 | +0.28 / −0.93 / −0.67 | +0.78 / −1.01 / −0.59 | +0.35 / −0.49 / −0.08 | −0.75 / −0.71 / −0.74 | −0.98 / −0.07 / −0.51 | −0.12 / −0.23 / −1.06 | 0.05 / 0.05 |
| gwd | +0.03 / −1.16 / −1.04 | +0.21 / −0.39 / −0.79 | +0.19 / −0.19 / −0.66 | −0.39 / −0.31 / −0.69 | −0.73 / −0.42 / −0.66 | −0.64 / −0.28 / −0.39 | 0.10 / 0.07 |
| gwd L95 | +0.09 / −1.02 / −1.09 | +0.48 / −1.03 / −1.04 | +0.44 / −0.19 / −0.62 | −0.50 / −0.15 / −0.52 | −1.55 / −0.39 / −0.69 | −1.32 / −0.52 / −0.61 | 0.11 / 0.08 |
| l81 n400 | +0.37 / −0.79 / −0.61 | +0.76 / −0.96 / −0.59 | +0.06 / −0.74 / −0.18 | −0.40 / −1.11 / −0.74 | −0.32 / −0.62 / −0.53 | +0.58 / −0.67 / −0.94 | 0.01 / 0.03 |
| full ECHAM | +0.88 / −1.55 / −1.23 | +0.96 / −1.71 / −1.22 | +0.60 / −0.42 / −1.76 | +0.96 / −1.29 / −3.19 | +1.31 / −2.82 / −5.27 | +1.92 / −4.22 / −7.04 | 0.18 / 0.14 |

With the drag the tropical residual motion above ~1.5 hPa is as downward as without it (L95: more so), polar descent stays
below 0.7 mm/s against the full physics' 3–7, and the age just below the lid is only marginally less flat (std 0.10 vs 0.05).
**The mesosphere is not ventilated by Hines + Lott-Miller at these settings in the dry model.** The same two schemes give the
full physics a proper mesospheric cell, so the difference is in what the dry model offers them: the winds and stability they
propagate through (Polvani-Kushner's relaxed temperatures above 3 hPa, no diurnal/ radiative structure), and the shallow
branch tells where the momentum went instead — into the lower stratosphere.

**Verdict against the acceptance criteria.** Tropical ages: met or nearly (12 hPa entry age 3.55 vs 2.90 ± 0.4: not met, but
0.2 yr closer). w* at 30 hPa: 0.19 vs 0.26, met; at 10 hPa: 0.02 vs 0.47, failed (worse than the control). Extratropical
55 hPa entry age 2.47 vs ≥ 3.7: failed (the full-physics failure reproduced). Mesosphere: failed. Cost: met. So the drag as
configured is not the production setting; it is the diagnosis: the two schemes deposit too much momentum too low and none
above the stratopause.

## Open questions

- **Where is the momentum deposited?** Neither drag term's tendency is in the output. A zonal-mean u-tendency diagnostic
  for `hines_gwd` and `lott_miller_sso` (per-term, like `omega_diagnostic`) would show directly whether the lower-stratospheric
  overshoot is Lott-Miller's (orographic waves break low) or Hines' (saturating in the strong PK jets), and why nothing
  reaches 1 hPa. Cheapest next step: one 1-year segment with the diagnostic, or two 5-year runs Hines-only / Lott-Miller-only
  (PLANS Phase 13 allowed the latter).
- **Retune.** PLANS allows one retune of `rms_launch_wind` (1.0 m/s). Lowering it reduces the shallow overshoot but also what
  reaches the mesosphere; the mesosphere needs the flux to *survive* to 1 hPa, which is about the filtering winds as much as the
  amplitude. A Rayleigh drag profile above ~0.5 hPa remains the fallback that ventilates the mesosphere by construction.
- **The relaxation.** The Jucker et al. (2013) equilibrium temperature and tau(p) (PLANS Phase 13 (a)) change the winds the
  waves propagate through above 3 hPa, where Polvani-Kushner relaxes to a flat standard atmosphere; with the drag now in, this
  is the natural companion test.
- The 400 hPa cutoff run shows the deep branch does not depend on the nudged upper troposphere (10 hPa w* 0.44 vs 0.31 with
  the 150 hPa cutoff); a shallower cutoff is not a fix for the age, though.
- The tracer lid stays at 1 hPa; a lid-off segment would measure ventilation directly once a run shows a mesospheric cell.
- Polar-night jets vs ERA5 (acceptance row) not evaluated in this record.
