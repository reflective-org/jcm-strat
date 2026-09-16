# Phase 12 — circulation tests: QBO nudging off, and the full L95 troposphere (1990–1994)

Status: **set up 2026-09-16 (14:00–15:00 PDT); pipeline running** (`scripts/phase12_run.sh`, tmux `strat_p12_run`,
log `runs/p12_run.log`). The host had lost its `/dev/nvidia*` device nodes in the 09:30 PDT reboot (the Phase 11
extension chain launched at 14:00 PDT ran on the CPU and was stopped); they were recreated at 14:44 PDT and the
pipeline passed its GPU check. It waits for the strat81 ERA5 windows (tmux `preproc_p12_l81_prefetch`), then runs
pytest, the 5-day GPU smokes, the three chains and the diagnostics. Results section to be filled from them.

## Why

Susanne, 2026-09-16, after the Phase 11 review (`docs/outputs/11_lid_tracers`): "The circulation in the phase11 runs
looks too weak and some things seem off so I want to do a couple of different tries." The Phase 11 age of air above
~20 hPa is filled from the 1 hPa tracer lid rather than ventilated, the tropical 55 hPa age is 2.7 yr against CLaMS
1.3 and still creeping up, and N2O/CFC-11 sit ~6 km too low. Two suspects are tested here, each against a control:

1. **QBO nudging off.** Since Phase 8 the tropical zonal-mean zonal wind between 90 and 1 hPa is relaxed to ERA5's
   monthly means with tau 1 d (|lat| < 25°). A strong, fast relaxation of the zonal wind is a momentum forcing of
   the tropical stratosphere; if it is fighting the model's own wave driving it changes the residual circulation.
   Test: the same run without the QBO term (`p12_noqbo`): w* and age of air before and after.
2. **The thinned troposphere of strat63.** The Phase 9 table keeps the 47 L95 levels between 1.08 and 159 hPa and
   thins the 26 L95 layers below 159 hPa to 8. The troposphere is where the ERA5 nudging acts and where the waves
   that drive the Brewer–Dobson circulation are generated and propagate upward; 8 layers over 850 hPa of it may
   under-resolve both. Test: the same run on `strat81` = strat63 with every L95 tropospheric layer put back
   (`p12_l81`, QBO on): w* and age of air before and after.

Age of air is shown for two clocks, as asked: **`aoa_sfc`** (zero in the lowest two model layers, the CLaMS
convention, present since Phase 10) and the new **`aoa500`** (zero wherever p > 500 hPa). Phase 11's clocks `aoa`
(700 hPa) and `aoa150` are still carried.

## What changed (code, `phase12-circulation` off `phase11-lid-tracers` 42a3f59)

| item | change | where |
|---|---|---|
| clock at 500 hPa | `ProductionTracersAoa500`, a subclass adding `aoa500` (reset p > 500 hPa; above the lid relaxed to WACCM age + 110 d like `aoa`/`aoa_sfc`). The clock set became the class attribute `CLOCKS` with `_reset_masks` / `_lid_targets` hooks; `ProductionTracers` itself and the Phase 11 checkpoints are unchanged | `jcm_strat/advection_tracers.py`, `physics/strat_pk_qbo_prod12.yaml` |
| QBO off | `PolvaniKushnerQbo(qbo=None)` now means *no nudging* (the term is then exactly `PolvaniKushnerColumns`, unit-tested); before Phase 12 a null silently built `QboNudging` with its defaults | `jcm_strat/qbo_nudging.py`, `physics/strat_pk_prod12_noqbo.yaml` |
| strat81 table | `levels.interface_indices(81)` = 8 thinned mesospheric + all L95 interfaces from 1.08 hPa down; hyperdiffusion orders mapped as for strat63; `sponge_for(81)` = (4, 6.73) = strat63's | `jcm_strat/levels.py`, `grid/strat_t63_l81_hybrid.yaml` |
| experiments | `p12_ctl` (= `p11a_prod` + aoa500, injection tracers not written), `p12_noqbo` (ctl, `qbo: null`), `p12_l81` (ctl on strat81) | `jcm_strat/config/experiment/p12_*.yaml` |
| chain script | `EXTRA_PER_SEG=""` (empty, not unset) disables the per-segment `qbo.year` override, needed for an experiment without the QBO term; `p12*` experiments inject on segment 1 like `p10_*`/`p11*` | `scripts/chain_segments.sh` |
| diagnostics | `strat_circulation.py`: frame stride for 6-hourly archives, zonal-mean omega, `residual_w` (w* from Psi*); `aoa_vs_clams.py --var <clock>`; **`scripts/phase12_compare.py`**: before/after/difference/WACCM panels of w* (annual, DJF, JJA), tropical w* profiles with the Eulerian [w] as a check, monthly tropical w* at 70 and 30 hPa, age of air per clock (before/after/difference/CLaMS), profiles, metrics table | `scripts/` |
| output volume | the 19 injection tracers (sai, pulses, sources) are integrated but not written (`output_drop`): 12 instead of 31 3-D fields at 6-hourly. They are passive and linear (Phase 10 check), so the dynamics are p11a's | `experiment/p12_ctl.yaml` |
| device nodes | `scripts/restore_nvidia_dev.sh`: recreates `/dev/nvidia*` from the driver container's nodes after a reboot | `scripts/` |

Why a control run rather than `p11a_5yr` as the "before": `p11a_5yr` has no `aoa500`. The control (`p12_ctl`) has the same
dynamics as `p11a` (passive tracers, same grid, same nudging), which the pipeline checks by comparing their w* and
`aoa_sfc` (`ctl_vs_p11a_*`). Why 1990–1994 and 5 years: the same years and length as Phase 11's A/B, so the
comparison is like for like; a 5-year clock has not converged (Phase 11: 55 hPa tropics still +0.15 yr/yr), so the
age plots compare *the same stage of spin-up*, not equilibria — differences are meaningful, absolute values are bounds.
Why the two tests are not combined: one change per run, so each effect is attributable (keep-it-simple rule).

Found while setting up: the `p10_prod` experiment merges `physics.terms.held_suarez.qbo.tau_days: 1.0` on top of
whichever physics group is chosen, so a physics group *without* a `qbo` mapping still receives one (a class without
that argument would fail at instantiation). Caught by `tests/test_phase12.py`; hence `qbo: null` (repeated in
`p12_noqbo.yaml`, which merges last) instead of a class swap.

## Runs

| run | experiment | GPU | years | notes |
|---|---|---|---|---|
| `p12noqbo_smoke5`, `p12l81_smoke5` | 5 days from 1990-01-01 | 1 / 2 | — | GPU smoke; log must show `QBO nudging OFF` / 81 levels, no pulses in the output, `aoa500` present |
| `p12noqbo_1990..1994` → `p12noqbo_5yr` | `p12_noqbo` | 1 | 1990–1994 | QBO nudging off, strat63 |
| `p12l81_1990..1994` → `p12l81_5yr` | `p12_l81` | 2 | 1990–1994 | QBO on, strat81 (own ERA5 windows, 26 GB/yr) |
| `p12ctl_1990..1994` → `p12ctl_5yr` | `p12_ctl` | 1 (after noqbo) | 1990–1994 | control = Phase 11 A + aoa500; the "before" |
| `p12noqbo_cpusmoke` | `p12_noqbo`, 5 d on the CPU | — | — | instantiation check while the GPUs were unavailable (2026-09-16) |

Commands (all from `scripts/phase12_run.sh`):
```
EXTRA_PER_SEG="" EXPERIMENT=p12_noqbo PREFIX=p12noqbo SCHEME=calendar YEARS=1990-1994 AGG=p12noqbo_5yr SAVE_INTERVAL=0.25 GPU=1 bash scripts/chain_segments.sh
EXPERIMENT=p12_l81   PREFIX=p12l81   SCHEME=calendar YEARS=1990-1994 AGG=p12l81_5yr   SAVE_INTERVAL=0.25 GPU=2 bash scripts/chain_segments.sh
EXPERIMENT=p12_ctl   PREFIX=p12ctl   SCHEME=calendar YEARS=1990-1994 AGG=p12ctl_5yr   SAVE_INTERVAL=0.25 GPU=1 bash scripts/chain_segments.sh
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12noqbo_5yr --tag noqbo --out docs/outputs/12_circulation
python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12l81_5yr   --tag l81   --out docs/outputs/12_circulation
```

## Acceptance checks (filled when the chains finish)

| check | expectation | result |
|---|---|---|
| control reproduces Phase 11 A | `ctl_vs_p11a_wstar.png`: w* difference at roundoff; `aoa_sfc` identical | |
| smokes | `QBO nudging OFF` in the noqbo log; 81 levels in the l81 output; `aoa500` = 0 where p > 500 hPa, otherwise = `aoa` where both run | |
| w*, QBO off (`noqbo_wstar*.png`, `noqbo_metrics.md`) | tropical w* and upward mass flux at 100/70/30/10 hPa before vs after vs WACCM6; is the deep branch (10 hPa and above) stronger without the wind relaxation? | |
| w*, strat81 (`l81_wstar*.png`, `l81_metrics.md`) | same, strat63 vs strat81 | |
| age of air (`*_age_aoa_sfc.png`, `*_age_aoa500.png`, `*_age_profiles.png`) | 55 hPa tropics (ctl ≈ 2.7 yr after 5 yr, CLaMS 1.3) and the tropics–extratropics contrast; does either change move the upper stratosphere (20–1 hPa) off the lid value? | |
| throughput | noqbo ≈ ctl ≈ Phase 11 minus the output saving; strat81 ≈ 1.3× slower | |

## Results

(pending)

## Open questions

(pending)
