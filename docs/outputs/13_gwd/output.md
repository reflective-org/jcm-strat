# Phase 13 — gravity-wave drag for the dry model, the L95 mesosphere, and a 400 hPa nudging cutoff (1990–1994)

Status: **running** (launched 2026-09-23, GPUs 1/2/3, tmux `strat_p13_run`, log `runs/p13_run.log`). Runs `p13gwd_5yr`,
`p13gwdl77_5yr`, `p13l81n400_5yr`; the Phase 12 runs `p12ctl_5yr`, `p12l81_5yr`, `p12echam_5yr` are the references.

## Why

The Phase 12 record (`docs/outputs/12_circulation/output.md`) ends with two findings that set this phase: (1) the old
stratospheric age of air is the dry Polvani–Kushner configuration's — JCM's full physics puts the tropical age on CLaMS
under the same nudging; (2) the dry runs' mesosphere is not ventilated: the tropical residual motion is *downward* from
~1.5 hPa to the sponge (−0.4 to −1 mm/s), there is no polar descent, and the age between 20 and 1 hPa is flat in latitude
because lid-valued air is pushed down. Above the stratopause the dry model has no forcing but the sponge and the
relaxation, and neither drives a poleward flow. Gravity-wave momentum deposition is what ventilates the mesosphere in
the atmosphere and in the full-physics run, and by downward control the drag above 30 hPa is also what sets the
50–20 hPa ascent that stalls in every dry configuration. Susanne, 2026-09-23: run the drag-only version, keep the clocks
relaxed to WACCM above 1 hPa, add a run with the L95 mesospheric layers, and a strat81 run nudged only up to 400 hPa.

## Runs

| run | grid | drag | nudging cutoff | one change against |
|---|---|---|---|---|
| `p13_gwd` | strat63 (8 + 47 + 8) | Hines (launch 634 hPa → 589 hPa on strat63, rms 1.0 m/s) + Lott-Miller (JCM defaults) | 150 hPa | `p12ctl_5yr` |
| `p13_gwd_l77` | strat77 (22 + 47 + 8; L95 sponge, 10 levels) | same | 150 hPa | `p13gwd_5yr` |
| `p13_l81_n400` | strat81 (8 + 47 + 26) | none | **400 hPa** | `p12l81_5yr` |

Everything else is the Phase 12 control's: ERA5 nudging of u, v, T with tau 6 h (lowest 2 levels free), QBO nudging to
1 hPa (tau 1 d), Polvani–Kushner relaxation (gamma 4 K/km, tau 15 d, vortex cooling faded above 3 hPa), the four clocks
with the 1 hPa tracer lid, injections integrated but not written, 6-hourly output, Gregorian calendar.

Implementation notes: JCM's `HinesGwd` launches its spectrum from a fixed *count* of levels above the surface (10 =
634 hPa on L95); on the 8-layer tropospheres of strat63/77 that would be 126 hPa, so `jcm_strat.gwd.HinesGwdLaunch`
takes the launch level as a pressure and resolves it per level table (unit-tested on 63/77/81/95). The drag terms read
the pressure/height/density diagnostics of `MoistAirColumnState`, which therefore heads the dry physics list. The
Lott-Miller descriptors (orostd, orosig, orogam, orothe, oropic, oroval) are in the T63 terrain file the dry runs load.

## Acceptance (PLANS Phase 13; entry-age clock `aoa150` vs WACCM6, w* vs WACCM6 histSST)

| quantity | control (`p12ctl_5yr`) | target | gwd | gwd_l77 | l81_n400 |
|---|---|---|---|---|---|
| tropical w* 30 hPa [mm/s] | 0.09 | 0.26 (within 1.5×) | | | |
| tropical w* 10 hPa [mm/s] | 0.13 | 0.47 (within 1.5×) | | | |
| tropical `aoa150` 12 hPa [yr] | 3.80 | 2.90 ± 0.4 | | | |
| tropical `aoa150` 55 hPa [yr] | 1.39 | 1.19 (not worse than 1.39) | | | |
| polar-cap `aoa150` 55 hPa [yr] | 3.86 | ≥ 3.7 | | | |
| tropical w* 1 / 0.5 / 0.3 hPa [mm/s] (1994) | −0.39 / −0.74 / −0.36 | upward (ECHAM +0.96 / +1.31 / +1.92) | | | |
| polar descent 0.5 hPa NH / SH [mm/s] (1994) | +0.02 / −0.68 | ECHAM −2.82 / −5.27 | | | |
| `aoa150` latitude std at 3 / 1.5 hPa [yr] | 0.07 / 0.07 | > 0.07 (ECHAM 0.20 / 0.15) | | | |
| polar-night jets vs control | — | no weaker | | | |
| cost vs control [min/yr e2e] | 27–31 | ≤ 1.3× | | | |

## Results

*(filled when the chains finish: `<tag>_metrics.md`, `<tag>_wstar*.png`, `<tag>_age_*.png` from `scripts/phase12_compare.py`
for tags gwd, gwd_l77, gwd_l77_vs_ctl, l81_n400, gwd_vs_echam; `p13*_aoa_*` from `scripts/aoa_vs_clams.py`;
`p13_mesosphere.md/.png` from `scripts/mesosphere_wstar.py`.)*

## Open questions

- If `p13_gwd` over-drives the circulation like the full physics did, one retune of `rms_launch_wind` (and/or the
  Lott-Miller `wave_drag_coeff`) before the Rayleigh-profile fallback (PLANS Phase 13).
- The Jucker et al. (2013) relaxation (PLANS Phase 13 (a)) is postponed until the drag result is in.
- The tracer lid stays at 1 hPa in these runs; a lid-off segment (`lid_p_hpa: null`) would measure the ventilation
  directly once the dynamics show a cell.
