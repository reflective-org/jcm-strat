# Phase 12 — circulation tests: QBO nudging off, and the full L95 troposphere (1990–1994)

Status: **complete** (2026-09-16: setup 14:00–15:00 PDT; chains 15:05–18:35 PDT on GPUs 1, 2 and 3; diagnostics done
20:31 PDT; record 2026-09-18). Runs `p12ctl_5yr`, `p12noqbo_5yr`, `p12l81_5yr` (1990–1994); figures and metrics
tables below. Headline: **neither change closes the age-of-air gap.** Switching the QBO nudging off *weakens* the
lower-branch upwelling and makes the tropical lower stratosphere 0.3 yr older; the full L95 troposphere doubles the
deep-branch upwelling at 10 hPa (towards WACCM6) but leaves the stratospheric age (500 hPa clock) unchanged while adding
0.4 yr of tropospheric transit to the surface clock.

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

Found while running: in `chain_segments.sh` the default `${EXTRA_PER_SEG-physics...qbo.year={year}}` ends, for bash,
at the *first* `}` — so with `EXTRA_PER_SEG=""` (the QBO-off chain) the per-segment override became a literal `}` and
Hydra refused segment 1 (`p12noqbo_19900101`, 15:05 PDT). Fixed in 1abb96b (default in a variable); the noqbo chain is
rerun by `scripts/phase12_finish.sh` on GPU 3 in parallel with the control (which the first pipeline started in its place
on GPU 1) and strat81 (GPU 2).

Found while setting up: the `p10_prod` experiment merges `physics.terms.held_suarez.qbo.tau_days: 1.0` on top of
whichever physics group is chosen, so a physics group *without* a `qbo` mapping still receives one (a class without
that argument would fail at instantiation). Caught by `tests/test_phase12.py`; hence `qbo: null` (repeated in
`p12_noqbo.yaml`, which merges last) instead of a class swap.

## Runs

| run | experiment | GPU | years | notes |
|---|---|---|---|---|
| `p12noqbo_smoke5`, `p12l81_smoke5` | 5 days from 1990-01-01 | 1 / 2 | — | GPU smoke; log must show `QBO nudging OFF` / 81 levels, no pulses in the output, `aoa500` present |
| `p12noqbo_1990..1994` → `p12noqbo_5yr` | `p12_noqbo` | 3 | 1990–1994 | QBO nudging off, strat63; first attempt (GPU 1, 15:03 PDT) failed on the `}` override; rerun by `phase12_finish.sh` from 16:10 PDT on GPU 3, which Susanne released for it ("if GPU3 is available you can use that") |
| `p12l81_1990..1994` → `p12l81_5yr` | `p12_l81` | 2 | 1990–1994 | QBO on, strat81 (own ERA5 windows, 26 GB/yr) |
| `p12ctl_1990..1994` → `p12ctl_5yr` | `p12_ctl` | 1 | 1990–1994 | control = Phase 11 A + aoa500; the "before" (started 15:05 PDT) |
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
| control reproduces Phase 11 A | `ctl_vs_p11a_wstar.png`: w* difference at roundoff; `aoa_sfc` identical | **pass**: up-flux within 0.1 × 10⁹ kg/s, tropical w* within 0.005 mm/s, age within 0.01 yr (the 5-yr-mean noise floor of a chaotic run, `ctl_vs_p11a_metrics.md`) |
| smokes | `QBO nudging OFF` in the noqbo log; 81 levels in the l81 output; `aoa500` = 0 where p > 500 hPa, otherwise = `aoa` where both run | **pass**: header line present; 63 / 81 levels; 13 output variables, no pulses; at day 5 `aoa500` reads 0.3 d against 3.7 d for `aoa` in the 500–700 hPa band (the reset is applied after the transport step, so it is not exactly 0) |
| w*, QBO off (`noqbo_wstar*.png`, `noqbo_metrics.md`) | tropical w* and upward mass flux at 100/70/30/10 hPa before vs after vs WACCM6; is the deep branch (10 hPa and above) stronger without the wind relaxation? | **no**: annual tropical w* 70 / 50 / 30 / 10 hPa 0.33 / 0.26 / 0.09 / 0.13 → 0.25 / 0.16 / 0.06 / 0.18 mm/s (WACCM6 0.21 / 0.20 / 0.26 / 0.47); up-flux 70 hPa 8.3 → 7.6, 10 hPa 1.26 → 1.26 × 10⁹ kg/s. The nudging adds ~0.1 mm/s of lower-branch upwelling (its secondary circulation); the deep branch does not depend on it |
| w*, strat81 (`l81_wstar*.png`, `l81_metrics.md`) | same, strat63 vs strat81 | **deep branch doubled, lower branch weaker**: 70 / 50 / 30 / 10 hPa 0.33 / 0.26 / 0.09 / 0.13 → 0.26 / 0.17 / 0.02 / 0.31 mm/s; DJF 10 hPa 0.41 → 0.59 (WACCM6 0.64); up-flux 10 hPa 1.26 → 1.34 (WACCM6 1.37), 70 hPa 8.3 → 7.7 (WACCM6 6.1). The 30 hPa minimum (~0) remains |
| age of air (`*_age_aoa_sfc.png`, `*_age_aoa500.png`, `*_age_profiles.png`) | 55 hPa tropics (ctl ≈ 2.7 yr after 5 yr, CLaMS 1.3) and the tropics–extratropics contrast; does either change move the upper stratosphere (20–1 hPa) off the lid value? | **no**: 55 hPa tropics, surface clock 2.74 → 3.00 (QBO off) / 3.07 (strat81); 500 hPa clock 2.39 → 2.67 / 2.29. 12 hPa within ±0.2 yr of the control everywhere; 20–1 hPa stays at the lid value (4.5–5.2 yr) in all three runs |
| throughput | noqbo ≈ ctl ≈ Phase 11 minus the output saving; strat81 ≈ 1.3× slower | ctl 4,440 d/hr stepping (7 ms/step), noqbo 4,990 (the QBO term is ~11 % of a step), strat81 3,590 (8 ms/step); end-to-end 800–880 d/hr = **27–30 min/yr for all three** — output-bound, so the extra 18 levels cost nothing end-to-end and dropping the 19 injection tracers saved little (`docs/outputs/throughput.csv`) |

## Results (`docs/outputs/12_circulation/`, 2026-09-16)

Diagnostics: `scripts/phase12_compare.py` for each pair (TEM covariances from every 4th 6-hourly frame = daily, whole run
and DJF / JJA; age = zonal mean of the last 60 days of 1994), `scripts/aoa_vs_clams.py --var aoa_sfc|aoa500` for each run.
References: WACCM6 histSST 1996–2014 daily TEM tape (w* by the same formula), CLaMS v3.1 / ERA5 2005–2009 (surface clock).

**The control reproduces Phase 11 A** (`ctl_vs_p11a_*`): every circulation and age number agrees to the noise floor
of a 5-year mean of a chaotic run (up-flux ±0.1 × 10⁹ kg/s, w* ±0.005 mm/s, age ±0.01 yr). Differences below that
in the two experiments are not differences.

**Where the control stands** (`*_wstar.png` left column, `*_wstar_tropics.png`): the model's tropical upwelling is
*stronger* than WACCM6's in the lower branch (annual w* 0.33 vs 0.21 mm/s at 70 hPa; up-flux 8.3 vs 6.1 × 10⁹ kg/s)
and *weaker* above 50 hPa — at 30 hPa it nearly vanishes (0.09 vs 0.26) before recovering to 0.13 at 10 hPa (WACCM6
0.47). The extratropical downwelling is diffuse and weak. The zonal-mean w* field is patchy: vertically alternating
cells 10–20° wide in the tropics, present in the Eulerian [w] as well, so a feature of the flow and not of the TEM
eddy term. WACCM6's smooth, broad pipe is not what the dry, ERA5-nudged troposphere plus Polvani–Kushner
stratosphere produces.

**QBO nudging off** (`noqbo_*`): the difference is confined to |lat| < 30° and 100–5 hPa and has the tilted dipole
structure of the QBO's secondary meridional circulation (`noqbo_wstar.png`, DJF / JJA difference panels). Without the
nudging the lower-branch upwelling *falls*: 0.33 → 0.25 mm/s at 70 hPa, 0.26 → 0.16 at 50 hPa (annual; the same in
both seasons), up-flux 8.3 → 7.6 × 10⁹ kg/s at 70 hPa; at 10 hPa nothing changes (1.26 → 1.26; w* +0.05). The
imposed ERA5 shear zones therefore *add* ~0.1 mm/s of upwelling in the lower stratosphere (their secondary
circulation, as theory says) and do nothing to the deep branch. Consistently, the tropical lower stratosphere gets
*older*: 55 hPa tropics 2.74 → 3.00 yr (surface clock), 2.39 → 2.67 (500 hPa clock), the extratropics +0.16–0.18;
12 hPa unchanged (−0.06). The QBO nudging is not what makes the stratosphere too old; it slightly helps.
The QBO-off run's own equatorial wind is the model's weak easterly regime of Phases 6–7 (smoke: −16 m/s at 20 hPa).

**Full L95 troposphere** (`l81_*`): the deep branch strengthens markedly — tropical w* at 10 hPa 0.13 → 0.31 mm/s
annual, 0.41 → 0.59 in DJF (WACCM6 0.47 / 0.64), up-flux 10 hPa 1.26 → 1.34 (WACCM6 1.37) — and the polar
downwelling above 10 hPa deepens (`l81_wstar.png`, difference panels: more downward flow poleward of 60° in the upper
stratosphere, more upward in the tropics above 10 hPa). But the lower branch weakens like in the QBO-off run (70 hPa
0.33 → 0.26, 50 hPa 0.26 → 0.17) and the 30 hPa minimum gets worse (0.09 → 0.02): the model's ascent now stalls
between 50 and 20 hPa and resumes above. The age of air splits by clock: the **surface clock** gets older (55 hPa
tropics 2.74 → 3.07 yr, extratropics +0.19, 12 hPa tropics +0.18) while the **500 hPa clock is unchanged or slightly
younger** (2.39 → 2.29 at 55 hPa tropics, ±0.02 elsewhere). The gap between the two clocks — the surface → 500 hPa
transit — grows from 0.35 to 0.78 yr: with 26 instead of 8 tropospheric layers the resolved vertical transport of the
dry model (no convection, no boundary-layer mixing; Phase 10 found a ~75 d tropospheric removal time) is slower. That
transit is model artefact, not stratospheric transport, and it inflates every surface-clock comparison with CLaMS
(whose surface → tropopause transit is weeks). The 500 hPa clock is the fairer one to compare, and it says: the
strat81 stratosphere is as old as strat63's.

**Reading.** Both suspects are cleared. The lower branch is already stronger than WACCM6's, and the age excess
(2.3–2.4 yr vs CLaMS 1.3 at 55 hPa with the 500 hPa clock; 4.4 vs 3.7 at 12 hPa) sits with (i) the near-zero ascent
between 50 and 20 hPa, which neither change repairs, (ii) the lid-filled upper stratosphere (20–1 hPa at 4.5–5 yr in
all three runs), and (iii) the tropospheric transit of the surface clock. The 50–20 hPa stall and the weak deep branch
point at the wave driving of the middle and upper stratosphere (planetary waves that the dry, ERA5-nudged troposphere
sends up; no gravity-wave drag) rather than at the tropospheric grid or the QBO term; the strat81 result shows the
deep branch does respond to how the troposphere is resolved, so the wave source is part of it.

Figures: `noqbo_wstar.png`, `noqbo_wstar_tropics.png`, `noqbo_age_aoa_sfc.png`, `noqbo_age_aoa500.png`,
`noqbo_age_profiles.png`, `noqbo_metrics.md`; the same six with prefix `l81_`; `ctl_vs_p11a_{wstar,wstar_tropics,
age_aoa_sfc,age_aoa,age_profiles}.png` + `_metrics.md`; `p12{ctl,noqbo,l81}_5yr_{aoa_sfc,aoa500}_aoa_{triptych,profiles}.png`.

## Open questions

- Why does the tropical ascent stall between 50 and 20 hPa in every configuration (w* ≈ 0 at 30 hPa against WACCM6's
  0.26 mm/s)? Candidates: the Polvani–Kushner equilibrium temperature (no radiative heating of the tropical middle
  stratosphere), the absence of gravity-wave drag, the planetary-wave flux out of the nudged troposphere. A wave-flux
  (EP-flux divergence) diagnostic on these archives would separate them — not run (keep-it-simple).
- Should the reference clock for CLaMS comparisons become `aoa500` (or `aoa150`) rather than the surface clock, given
  the 0.35–0.8 yr tropospheric transit of the dry model? Susanne's call; the numbers for both are in the tables.
- strat81 costs nothing end-to-end at 6-hourly output (output-bound) and improves the deep branch: keep it for the
  production grid? It changes the strat63 decision of Phase 9 (KEY_DECISIONS #31), which was made on age of air at
  5 yr — an artefact-dominated metric, as Phase 11 showed.
- The QBO-off run has no QBO at all (weak steady easterlies); a free QBO would need the gravity-wave forcing the
  dry model lacks. Nudging stays on (KEY_DECISIONS #27 stands).
