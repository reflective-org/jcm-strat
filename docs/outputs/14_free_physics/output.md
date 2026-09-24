# Phase 14 — free-running full physics: JCM's ECHAM package with no nudging, 10 years (1990–1999)

Branch `phase14-free-physics` off `phase12-circulation` (212a933). Pipeline `scripts/phase14_run.sh` in tmux
`strat_p14_run` (log `runs/p14_run.log`), GPU 0. Susanne, 2026-09-22 (PDT): "Can you create a new phase that runs JCM
full physics with no nudging? Can you run it for 10 years? Look at the same plots as in phase 12."

## Why

Phase 12 run 4 (`docs/outputs/12_circulation/`, `p12echam_5yr`) ran JCM's full ECHAM physics under the project's two
relaxations — u/v/T nudged to ERA5 below 150 hPa (tau 6 h) and the zonal-mean tropical wind nudged to ERA5's QBO (tau
1 d, 90–1 hPa) — and found the tropical age of air on CLaMS but the shallow branch of the Brewer–Dobson circulation
3× WACCM6 at 100 hPa, no Arctic vortex, and the extratropics 1.4 yr too young. Whether that over-driven circulation is the
package's own or is forced by the nudging (the relaxation's secondary circulation, the ERA5 wave field imposed on a
model whose stratosphere responds differently) is not separable in that run. This phase removes both relaxations and
lets JCM's physics make its own troposphere, QBO (or not) and vortex; ten years give a spun-up clock (issue #44: the
5-yr chains are ~0.6 yr young in the extratropics) and a climatology with several winters.

## What changed (code)

| item | change |
|---|---|
| `jcm_strat/config/physics/echam_free14.yaml` | `echam_prod12` without the `qbo_nudging` term; every other term identical, same order |
| `jcm_strat/config/experiment/p14_free.yaml` | `p12_echam` + `override /nudging: none` (+ `nudging.enabled: false` repeated in the body: the inherited nudging keys merge onto any group and would otherwise read like a live configuration in the log) |
| `tests/test_phase14.py` | composes `p14_free` and `p12_echam`: nudging disabled, no `qbo_nudging`, all other terms, grid, run, output and mass-fixer settings equal |
| `scripts/chain_segments.sh` | the first-segment WACCM tracer initialisation now applies to every `p1[1-9]*` experiment (was `p10_*|p11*|p12*`) |
| `scripts/phase14_run.sh` | the pipeline: inputs → pytest → 5-day smoke (log must show `enabled: false` under `nudging:` and no nudging term) → 10-segment chain → 5-yr aggregate of the first five years → Phase 12 diagnostics |

Unchanged from `p12_echam`: T63L95 (JCM's level table), ERA5 initial state 1990-01-01, present-day climatological SST /
sea ice / ozone (`forcing_pd.nc`, cycled every year), Phase 12 tracer term (`ProductionTracersAoa500`: clocks `aoa`,
`aoa150`, `aoa_sfc`, `aoa500`, steady `n2o`/`cfc11`, injections integrated but not written), omega, `output_keep`, 6-hourly
instantaneous output, 5-day chunks, Gregorian calendar, one calendar year per segment, dt 12 min. The calendar years are
labels for the tracer bookkeeping — the free model sees no year-specific forcing.

## Runs

| run | experiment | GPU | years | notes |
|---|---|---|---|---|
| `p14free_smoke5` | `p14_free`, 5 days from 1990-01-01 | 0 | — | GPU smoke; config echo must show `nudging: enabled: false` and no `qbo_nudging`; 95 levels, 13 output variables |
| `p14free_1990..1999` → `p14free_10yr` | `p14_free` | 0 | 1990–1999 | the run, one chain; `p14free_5yr` = the first five segments linked as their own aggregate (same spin-up as the 5-yr references). Susanne, 2026-09-23: report the 5-year run first, as in the earlier phases, then the extension to 10 — the chain already is that (segment 1995 restarts from 1994's checkpoint), so `scripts/phase14_5yr_diag.sh` (tmux `strat_p14_5yr`) runs the 5-yr diagnostics on the CPU as soon as segment 1994 lands while the GPU continues |

Commands (all from `scripts/phase14_run.sh`):
```
EXTRA_PER_SEG="" FIRST_SEG_EXTRA="physics.terms.production_tracers.first_segment=true" EXPERIMENT=p14_free PREFIX=p14free \
  SCHEME=calendar YEARS=1990-1999 AGG=p14free_10yr SAVE_INTERVAL=0.25 GPU=0 bash scripts/chain_segments.sh
python scripts/phase12_compare.py --before runs/p12echam_5yr --after runs/p14free_10yr --tag free10        --clocks aoa_sfc aoa500 aoa150 --out docs/outputs/14_free_physics
python scripts/phase12_compare.py --before runs/p12echam_5yr --after runs/p14free_5yr  --tag free5         --clocks aoa_sfc aoa500 aoa150 --out docs/outputs/14_free_physics
python scripts/phase12_compare.py --before runs/p12ctl_5yr   --after runs/p14free_10yr --tag free10_vs_ctl --clocks aoa_sfc aoa500 aoa150 --out docs/outputs/14_free_physics
python scripts/aoa_vs_clams.py runs/p14free_10yr docs/outputs/14_free_physics --last-saves 240 --var {aoa_sfc,aoa500,aoa150}
```

## What to look at (the Phase 12 set; filled when the chain finishes)

| check | Phase 12 reference values | result |
|---|---|---|
| smoke | GPU, 95 levels, nudging off, no QBO term, clocks advance | **pass** (`p14free_smoke5`, 2026-09-22 21:17 PDT): config echo `nudging: enabled: false`, no `qbo_nudging`; 95 levels, 13 variables; T 179–312 K, u −116…131 m/s at day 5 |
| w* (`free10_wstar*.png`, `free10_metrics.md`) | nudged full physics: tropical w* 100 / 70 / 50 / 30 / 10 hPa 1.46 / 0.60 / 0.20 / 0.28 / 0.87 mm/s (WACCM6 0.40 / 0.21 / 0.20 / 0.26 / 0.47); up-flux 70 hPa 11.3, 10 hPa 2.74 × 10⁹ kg/s (WACCM6 6.1 / 1.37). Does the shallow branch fall back toward WACCM6 without the nudging? | **the shallow branch collapses at the equator, the deep branch grows**: annual tropical (15S–15N) w* 100 / 70 / 50 / 30 / 10 hPa = **−0.05 / −0.22 / −0.28 / +0.01 / +1.32** mm/s — downward residual motion in the deep tropics from 100 to ~40 hPa in every season, 10 hPa 2.8× WACCM6. The hemispheric up-flux is nevertheless near WACCM6 at 100 / 70 hPa (12.6 / 7.5 vs 10.9 / 6.1 × 10⁹ kg/s) because the ascent sits off the equator (subtropics, monsoon: JJA 100 hPa up-flux 36 = 3.8× WACCM6, DJF 11.8 ≈ WACCM6); 30 hPa up-flux 2.1 (WACCM6 3.05, nudged 4.5); 10 hPa 3.1 (1.37) |
| age of air, entry clock `aoa150` (`free10_age_aoa150.png`, profiles) | WACCM6 entry age 55 hPa tropics 1.19, poles 3.71; 12 hPa tropics 2.90. Nudged full physics too young everywhere by this clock | 55 hPa tropics **1.45** (nudged 0.96; WACCM6 1.19), 50–70° **2.08** (nudged 2.41; WACCM6 ~3.4–3.7); 12 hPa tropics 3.31 (nudged 3.33; WACCM6 2.90), 50–70° 4.22. The 55 hPa age is nearly **flat in latitude** (1.3–2.4 yr from 50°S to 60°N) with a local *maximum* at the equator and minima at ±20–30° — the fingerprint of the equatorial descent flanked by subtropical ascent. SH polar cap older than nudged (3.1 vs 2.4 at 85°S) |
| age of air, `aoa_sfc` / `aoa500` (`free10_age_aoa_sfc.png`, `free10_age_aoa500.png`, `p14free_10yr_*_aoa_triptych.png`) | nudged: 55 hPa tropics 1.33 / 1.07 vs CLaMS 1.33; 12 hPa 3.64 / 3.51 vs 3.68; 55 hPa 50–70° 2.73 vs CLaMS 4.12 | 55 hPa tropics **1.81 / 1.57** (+0.5 yr vs nudged; CLaMS 1.33), 50–70° **2.41 / 2.22** (CLaMS 4.12; −0.3 vs nudged); 12 hPa tropics 3.63 / 3.47 (CLaMS 3.68, unchanged), 50–70° 4.54 / 4.44 (CLaMS 4.56). Tropics–extratropics contrast at 55 hPa **0.6 yr** (nudged 1.4, CLaMS 2.8): the free lower stratosphere is even more horizontally mixed than the nudged one. Tropical profile on CLaMS above ~30 hPa, 0.3–0.5 yr too old between 100 and 30 hPa |
| spin-up (`free5_*` vs `free10_*`) | how much of the 5-yr → 10-yr difference is the clock still filling (issue #44) rather than the circulation | **spun up**: years 5 → 10 move the ages by ≤ 0.1 yr everywhere tabulated (55 hPa tropics 1.75 → 1.81, 12 hPa tropics 3.54 → 3.63, 12 hPa 50–70° 4.47 → 4.54, 55 hPa 50–70° 2.41 → 2.41); w* identical to two decimals (the two aggregates share the first five years; the second five add nothing new). No extension needed |
| tropical winds | does the free package produce a QBO at T63L95 (the nudged run had ERA5's)? monthly tropical w* series `free10_wstar_tropics.png`; a zonal-wind check is a follow-up if needed | the monthly w* at 70 and 30 hPa is a pure annual cycle (±0.4 mm/s at 30 hPa) with no interannual modulation; `scripts/qbo_compare.py` run on the equatorial winds → `qbo_time_height_before_after.png`, `qbo_metrics.md` (see Results) |
| throughput | nudged full physics 146–166 d/hr stepping, 106–118 e2e (3.1–3.4 h/yr) | **157–169 d/hr stepping (177–192 ms/step), 115–122 d/hr end-to-end = 3.1 h/yr**, 31.2 h for the ten segments (2026-09-22 21:17 → 2026-09-24 04:27 PDT). Removing the nudging target buys nothing: the step is the physics. Compacted archive 82 GB/yr (`docs/outputs/throughput.csv`) |

## Results (`docs/outputs/14_free_physics/`, 2026-09-24)

Chain `p14free_1990..1999` ran 2026-09-22 21:17 → 2026-09-24 04:27 PDT on GPU 0 (3.1 h/yr, 31 h; commit d946f56 at
launch), diagnostics finished 07:17 PDT. The 5-year milestone (`p14free_5yr`, tag `free5`) and the 10-year run (tag
`free10`) are reported together because they are indistinguishable: every tabulated age moves by ≤ 0.1 yr between
year 5 and year 10 and the seasonal w* fields by ≤ 0.03 mm/s, so the run is spun up at year 5 in the sense of issue #44
and the 10-year numbers below are the converged ones. (The CPU watcher `scripts/phase14_5yr_diag.sh` failed at its link
step — `chain_segments.sh` refused because GPU 1, the idle card it was told to check, had meanwhile been taken by the
Phase 13b chain; the main pipeline produced the same `free5` comparison 12 h later and the `p14free_5yr_*` age plots
were made by hand afterwards. `free5_vs_ctl` was not made; `free10_vs_ctl` covers it.)

**1. Without the nudging the full package has no tropical pipe in the lower stratosphere.** The zonal-mean residual
vertical velocity averaged over 15°S–15°N is *downward* from 100 to ~40 hPa in every season (annual −0.05 / −0.22 /
−0.28 mm/s at 100 / 70 / 50 hPa; WACCM6 +0.40 / +0.21 / +0.20; nudged full physics +1.46 / +0.60 / +0.20). The
latitude–pressure panels (`free10_wstar.png`) show why the hemispheric upward mass flux is nevertheless close to WACCM6
at 100 and 70 hPa (12.6 / 7.5 vs 10.9 / 6.1 × 10⁹ kg/s): the ascent sits off the equator, in the summer subtropics —
JJA 100 hPa up-flux 36 × 10⁹ kg/s, 3.8× WACCM6, over 0–40°N (the monsoon anticyclone), DJF 11.8 ≈ WACCM6 — with descent
at the equator between. The 30 hPa up-flux is 2.1 (WACCM6 3.05; nudged 4.5). The deep branch is *stronger* than nudged
and 2.8× WACCM6 (10 hPa tropical w* 1.32 mm/s, up-flux 3.1 vs 1.37), and the mesosphere has a proper cell (tropical
ascent, polar descent above 3 hPa) as in the nudged full physics.

**2. The nudging was supplying the shallow branch — too much of it.** Nudged: 100 hPa w* 3.7× WACCM6. Free: below zero.
Neither is the observed 0.4 mm/s; the nudging's secondary circulation (relaxing u, v, T to ERA5 below 150 hPa with
tau 6 h in a model whose own tropics want something else) was the source of the over-driven shallow branch found in
Phase 12 run 4, and what remains without it is the package's own lower-stratospheric tropics, which are not a pipe. The
Phase 12 ambiguity ("package or nudging?") is resolved: the *excess* was the nudging, the *structure* underneath is the
package's.

**3. Age of air: tropics older, extratropics younger, almost no latitudinal contrast** (`free10_age_*.png`,
`free10_age_profiles.png`, `p14free_10yr_*_aoa_triptych.png`). Surface clock at 55 hPa: tropics 1.81 yr (nudged 1.33,
CLaMS 1.33), 50–70° 2.41 (nudged 2.73, CLaMS 4.12); contrast 0.6 yr against CLaMS's 2.8. The 55 hPa age curve has a
local *maximum* at the equator and minima at ±20–30° — the equatorial descent between two subtropical ascent regions,
read directly off the tracer. The entry clock (`aoa150`) says the same: 1.45 tropics / 2.08 at 50–70° against WACCM6's
1.19 / ~3.5. At 12 hPa the tropical age is unchanged and on CLaMS (3.63 vs 3.68) and 50–70° is on CLaMS too (4.54 vs
4.56); the tropical profile lies on CLaMS above ~30 hPa and is 0.3–0.5 yr too old between 100 and 30 hPa. The SH polar
cap is older than in the nudged run (3.5 vs 2.7 at 55 hPa, 85°S), the NH polar cap slightly younger — the free SH vortex
isolates more, the NH not.

**4. Against the dry control** (`free10_vs_ctl_*`): the dry Polvani-Kushner control has the *right* shallow branch
(100 / 70 hPa w* 0.40 / 0.33 ≈ WACCM6) and no deep branch (10 hPa 0.13); the free full physics is the mirror image
(shallow branch reversed at the equator, 10 hPa 1.32). By the entry clock the control is closer to WACCM6 at 55 hPa in
the tropics (1.29 vs 1.45) and far closer in the extratropics (3.60 vs 2.08); the free run wins only at 12 hPa (3.31 vs
3.77; WACCM6 2.90) because its deep branch actually ascends.

**5. Throughput.** 157–169 sim d/hr stepping, 115–122 end-to-end = 3.1 h/yr — identical to the nudged run; the ERA5 target
was never the cost, the physics step is. 82 GB per year compacted.

**Reading.** The full ECHAM package at T63L95, left alone with climatological SST, does not produce the observed
lower-stratospheric tropical pipe: its tropical residual circulation is monsoon-dominated with equatorial descent, and its
deep branch and polar-night drag are too strong. The Phase 12 conclusion that "full physics puts the tropical age on
CLaMS" was the nudging's doing (it was the nudging's over-driven shallow branch, and the 55 hPa age went from 1.33 to
1.81 without it). Neither the dry configuration nor the free package is right on its own; the dry one has the better
lower stratosphere and extratropics, the package the better deep branch and mesosphere — which is the Phase 13
(relaxation + drag) direction from the other side.


## Addendum 2026-09-24: the free package has no QBO (`qbo_time_height_before_after.png`, `qbo_profiles.png`, `qbo_metrics.md`)

`scripts/qbo_compare.py` on the equatorial (5°S–5°N) zonal-mean wind, 1990–1999, free vs nudged vs ERA5. The free run's
equatorial stratosphere is **steady**: deseasonalised standard deviation 0.2 / 0.1 / 0.2 / 0.3 m/s at 10 / 20 / 30 / 50 hPa
against ERA5's 18.8 / 18.2 / 16.0 / 11.9 (the nudged run, with the QBO term, 13.3 / 11.9 / 10.1 / 7.1). The time–height
section shows weak westerlies (+5 to +10 m/s) from 100 to ~30 hPa, near-zero wind from 30 to 3 hPa and weak easterlies
(−10 m/s) above, with only a faint semiannual wiggle at 2 hPa — no QBO, no SAO. RMS against ERA5's monthly equatorial
wind 16.3 m/s (10–70 hPa; nudged 6.4). The tropical stratosphere of JCM's ECHAM package at T63L95 with its Hines/SSO
settings therefore has no wave-driven equatorial oscillation at all; the tropospheric wave source and the parameterised
drag are not producing one. With the QBO term switched off together with the ERA5 nudging, the "no nudging" run has a
wind structure the real atmosphere never has — a permanent weak westerly shear zone in the lower stratosphere — which is
part of why the equatorial residual motion there is downward (result 1) and the 55 hPa age flat in latitude (result 3).
This makes the troposphere-only-off variant (QBO term kept, Open questions) the informative next run: it separates
"the package has no tropical pipe" from "the package has no QBO". (The nudged panel has data gaps in 1990–1991: months
the loader could not read from the compacted `p12echam` chunks, not a model gap; the metrics are over the months present.)

## Open questions

- Chosen reading of "no nudging": both relaxations off (ERA5 below 150 hPa and the QBO term). A QBO-only-off or
  troposphere-only-off variant would separate the two; given result 1, the troposphere-only-off variant (QBO term kept)
  is the one that would tell whether the equatorial descent is a missing-QBO effect or the package's tropics.
- ~~Does the free package make a QBO?~~ No (addendum above): equatorial wind steady to 0.3 m/s. Why not — Hines source
  spectrum / launch level at T63L95, or the SL dycore's tropical wave damping — is a Phase 13-type drag question.
- Why is the equatorial lower-stratospheric residual motion downward: is it the monsoon/subtropical heating pattern of the
  Tiedtke convection at T63, or the Hines drag deposited too low? A zonal-mean u and T climatology of the free run against
  ERA5 (`scripts/strat_compare.py`) is the next diagnostic; not run here (Phase 12 set only).
- The 5-yr watcher's GPU-check workaround (`GPU=1` to bypass `chain_segments.sh`'s busy check) is fragile on a shared node;
  a link-only mode of `chain_segments.sh` would be the clean fix (the script must not be edited while a chain runs).
