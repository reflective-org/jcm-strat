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
| `p14free_1990..1999` → `p14free_10yr` | `p14_free` | 0 | 1990–1999 | the run; `p14free_5yr` = the same first five segments linked as their own aggregate (same spin-up as the 5-yr references) |

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
| smoke | GPU, 95 levels, nudging off, no QBO term, clocks advance | — |
| w* (`free10_wstar*.png`, `free10_metrics.md`) | nudged full physics: tropical w* 100 / 70 / 50 / 30 / 10 hPa 1.46 / 0.60 / 0.20 / 0.28 / 0.87 mm/s (WACCM6 0.40 / 0.21 / 0.20 / 0.26 / 0.47); up-flux 70 hPa 11.3, 10 hPa 2.74 × 10⁹ kg/s (WACCM6 6.1 / 1.37). Does the shallow branch fall back toward WACCM6 without the nudging? | — |
| age of air, entry clock `aoa150` (`free10_age_aoa150.png`, profiles) | WACCM6 entry age 55 hPa tropics 1.19, poles 3.71; 12 hPa tropics 2.90. Nudged full physics too young everywhere by this clock | — |
| age of air, `aoa_sfc` / `aoa500` (`free10_age_aoa_sfc.png`, `free10_age_aoa500.png`, `p14free_10yr_*_aoa_triptych.png`) | nudged: 55 hPa tropics 1.33 / 1.07 vs CLaMS 1.33; 12 hPa 3.64 / 3.51 vs 3.68; 55 hPa 50–70° 2.73 vs CLaMS 4.12 | — |
| spin-up (`free5_*` vs `free10_*`) | how much of the 5-yr → 10-yr difference is the clock still filling (issue #44) rather than the circulation | — |
| tropical winds | does the free package produce a QBO at T63L95 (the nudged run had ERA5's)? monthly tropical w* series `free10_wstar_tropics.png`; a zonal-wind check is a follow-up if needed | — |
| throughput | nudged full physics 146–166 d/hr stepping, 106–118 e2e (3.1–3.4 h/yr) | — |

## Results

_pending — the chain runs ~30 h from 2026-09-22 21:00 PDT._

## Open questions

- Chosen reading of "no nudging": both relaxations off (ERA5 below 150 hPa and the QBO term). A QBO-only-off or
  troposphere-only-off variant would separate the two if the result needs it.
