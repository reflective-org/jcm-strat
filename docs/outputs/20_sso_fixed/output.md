# Phase 20 — the fixed Lott-Miller SSO in the dry model (and Phase 20b: bottom levels nudged)

Status: **complete** (written 2026-10-20 from the decision log, the metric files and the 20b extension; the runs ended
2026-10-07 23:50 PDT (Phase 20) and 2026-10-16 02:41 PDT (Phase 20b, `p20bt`)). Runs were made from the phase19 worktree
(`/data/JCM_stripped/jcm-strat-phase19/scripts/phase20_run.sh`, `scripts/p20b_extend.sh`) into its `runs/`; only this record
lives on this branch. Every decision with its options: [decisions.md](decisions.md); the set-up decisions shared by Phases 19–21
are in the Phase 19 log (`docs/outputs/19_jcm_update/decisions.md`).

**Headline.**
- **Phase 20 (dry 13d + fixed Lott-Miller, L95 + cubic, nudged below 400 hPa) is not stable.** Near-surface humidity spikes
  over the SE edge of the Himalaya appear every year (up to 162 g/kg; 19d without SSO ≤ 6 g/kg), exempted from the health
  check under issue #62, and on 1997-12-20 a one-to-two-grid-point hot/cold dipole east of the Tibetan Plateau (106.9E / 114.4E,
  30.8N, sigma 0.98) runs away to T 25–780 K. 1990–1996 are healthy.
- **The cause is the dry model's un-nudged bottom levels plus Lott-Miller, not Lott-Miller alone and not nudging.** 19d (the same
  dry config without Lott-Miller) runs through 1998; 21a (nudged full physics with Lott-Miller) and 21b (free full physics with
  Lott-Miller) both run through 1997 and later with no health stops and no humidity exemption.
- **Phase 20b fixes it**: the same configuration with the bottom two levels nudged as well (`nudging.pbl_levels: 0`,
  `p20b_sso_pbl0`). It passes Dec 1997 (east-Tibet bottom levels 259–291 K) and needs no humidity exemption. `p20bt` reran
  1990–2009 from the spin-up with every tracer written and is healthy throughout. **P20b is the base of Phase 22.**
- **Over 1990–1994 the fixed Lott-Miller barely changes the stratospheric circulation** (sso5 vs 19d): tropical w* +0.005–0.010
  mm/s, 100 hPa mass flux +5 %, ages 0.03–0.16 yr younger. Its clear cost is the NH vortex: the 10 hPa DJF jet is 29 m/s
  without it and 17 m/s with it (ERA5 35). The SH vortex is weak either way (59 / 57 m/s vs ERA5 75): that weakness belongs
  to the dry configuration (T_e / Hines), not to Lott-Miller.

## What was run

| run | config | years | outcome |
|---|---|---|---|
| `p20jhsso` | `p20_jh_sso_n400` = 19d (`p19_jh_n400`) + `lott_miller_sso`, L95 + cubic, n400, `health_ignore_q_max: true` | 1990–1997 | 1990–1996 healthy; 1997 health stop at day 360 |
| `p20jhsso_5yr` | 5-yr aggregate of the above | 1990–1994 | the sso5_vs_19d comparison |
| `p20b` | `p20b_sso_pbl0` = Phase 20 with `nudging.pbl_levels: 0` | 1990–1998 | healthy; superseded by `p20bt` |
| `p20bt` | `p20b_ext` (all 36 output variables incl. pulses / box / sources / SAI) | 1990–2009 | healthy; aggregate `p20bt_20yr` |

Earlier attempts on Oct 7 (strat81 + cubic, which blew up in every year, and the first L95 + cubic run, which stopped at
1990 day 60 on q_max) are recorded in `decisions.md`; their output is invalid and was moved aside.

## Results — Phase 20: the stability problem

- **Humidity (issue #62).** On L95 + cubic, q at the lowest level (sigma 0.983) over the SE Himalaya edge (97–99E, 25–29N)
  reaches 104.7 g/kg by 1990 day 60, and q spikes recur in every year 1990–1996 (q_max 105, 149, 58, 33, 162, 39, 110 g/kg).
  Susanne chose to treat humidity as unimportant in the dry run for now (2026-10-07 19:25 PDT): q_max > 100 g/kg is reported
  but not fatal, and every temperature check stays fatal.
- **The 1997 blow-up.** Everything is normal up to 1997-12-19 18Z. From 1997-12-20 00Z, T_max at sigma 0.98 over 106.9E 30.8N
  (Sichuan Basin) grows 406 → 639 K in 24 h and peaks at 780 K, while a cold partner two grid points east (114.4E) falls to
  25 K. It is a grid-scale numerical instability, in the same SE-Tibet sector as the humidity spikes. Humidity was not large at
  the time (2.4 g/kg).
- **Attribution.** 19d (no Lott-Miller) is healthy through 1998, and 21a extended to 1997 is healthy (east-Tibet bottom levels
  247–289 K through Dec 20–27 1997). Only the dry configuration leaves the bottom two levels to the dynamics and the
  Lott-Miller drag alone, with no boundary layer, and Phase 20b's nudging of those levels removes both symptoms.

## Results — the fixed Lott-Miller's effect, 1990–1994 (`sso5_vs_19d_metrics.md`)

| quantity | 19d (no SSO) | Phase 20 (fixed LM) | WACCM6 / CLaMS |
|---|---|---|---|
| tropical w* 100 / 70 / 50 / 30 / 10 hPa [mm/s] | 0.117 / 0.191 / 0.273 / 0.320 / 0.411 | 0.127 / 0.200 / 0.278 / 0.325 / 0.420 | 0.398 / 0.211 / 0.201 / 0.255 / 0.469 |
| upward mass flux 100 hPa, annual [1e9 kg/s] | 8.79 | 9.27 | 10.85 |
| `aoa150` 55 hPa tropics / 50–70° [yr] | 1.14 / 3.38 | 1.11 / 3.30 | CLaMS 1.33 / 4.12 |
| `aoa_sfc` 55 hPa tropics / 50–70° [yr] | 2.28 / 4.16 | 2.25 / 4.11 | CLaMS 1.33 / 4.12 |
| 10 hPa jet DJF N / JJA S [m/s] (`vortex_1990-1994`) | 29 / 59 | 17 / 57 (P20b) | ERA5 35 / 75 |

The mesosphere is unaffected in sign and structure (`p20_mesosphere.md`): tropical w* above 10 hPa slightly stronger with
Lott-Miller (+1.87 vs +1.48 mm/s at 0.5 hPa), polar caps slightly more downward.

## Results — Phase 20b / p20bt, 2005–2009 (`p20b_extension/`)

| quantity | P20b | reference |
|---|---|---|
| `aoa150` 55 hPa tropics DJF / JJA [yr] | 1.15 / 1.24 | WACCM6 1.04 / 1.10 |
| `aoa_sfc` 55 hPa tropics DJF / JJA [yr] | 2.63 / 2.73 | CLaMS 1.44 / 1.53 (too old) |
| `aoa_sfc` 55 hPa 50–70N / 50–70S, DJF [yr] | 5.00 / 5.12 | CLaMS 3.94 / 4.42 |
| 10 hPa jet DJF N [m/s @ lat] | 19 @ 59 | ERA5 28 @ 62 |
| 10 hPa jet JJA S [m/s @ lat] | 57 @ -59 | ERA5 73 @ -57 |
| 50 hPa jet DJF N / JJA S [m/s] | 14 / 39 | ERA5 18 / 46 |
| RMSE vs ERA5 100–1 hPa, annual: T / u | 6.2 K / 5.4 m/s | |

The tropics-to-midlatitude age gradient at 55 hPa is larger than WACCM's (2.4 vs 2.2 yr in DJF), so there is no sign of excess
in-mixing into the tropics; the old surface-clock ages come with weak vortices. P20b has SSW-like 10 hPa reversals in most
winters (18 in 1991–2003; ERA5 2006–2009 has 6). Tracer pulse evolution, omega and the AoA triptychs for the full 20 years are
in `p20b_extension/tracers/` and `p20b_extension/`.

## Open questions / follow-ups (not run)

- **Issue #62 stays open.** P20b removes the humidity spikes and the blow-up by nudging the bottom levels; it does not show
  that Lott-Miller is stable in an un-nudged dry boundary. Whether the fixed Lott-Miller needs a stabiliser (tendency cap,
  implicit or limited drag, orography smoothing over SE Tibet, smaller dt) before it is used without bottom-level nudging is
  undecided.
- The diagnostic suggested in `decisions.md` (rerun 1997-12-07 to 12-21 with 6-h SSO u/v/T tendencies at 100–115E, 25–35N) was
  not run. The incomplete 1997 segment was deleted in the 2026-10-19 disk cleanup; `runs/p20jhsso_19960101/checkpoint.ckpt`
  remains, and the run is deterministic, so the blow-up can be reproduced from it (about 30 min on one GPU).
- The weak vortices (issue #35) are what Phase 22 then worked on, on P20b.
