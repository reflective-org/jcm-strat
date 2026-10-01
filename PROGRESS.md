# Progress

Newest first. Each row links to the per-phase record in `docs/outputs/`.

| Date | Phase | State | Record |
|---|---|---|---|
| 2026-09-24 | 14 — free-running full physics, 10 years | **done** (branch `phase14-free-physics`, not pushed): `p14free_10yr` 1990–1999, 3.1 h/yr; spun up by year 5 (ages move ≤ 0.1 yr to year 10). Without nudging the tropical lower-stratospheric residual motion is *downward* (70 hPa −0.22 mm/s; WACCM6 +0.21) with ascent in the summer subtropics, the deep branch 2.8× WACCM6; 55 hPa age tropics 1.81 (CLaMS 1.33), 50–70° 2.41 (4.12) — the Phase 12 "tropical age on CLaMS" was the nudging's shallow branch | [docs/outputs/14_free_physics/output.md](docs/outputs/14_free_physics/output.md) |
| 2026-09-24 | 15 — hyperparameter sweep toward CLaMS/ERA5-like stratospheric dynamics (strat81, Jucker base; drag / relaxation / sponge / nudging knobs) | **done** (see the leaderboard in the record): stage 1 = 11 one-knob 3-yr runs 1990-1992, stage 2 = combinations of the family winners, stage 3 = the best to 1990-1994; scored against CLaMS entry age, WACCM6 w*, ERA5 u/T; leaderboard rewritten after every run | [docs/outputs/15_sweep/output.md](docs/outputs/15_sweep/output.md) |
| 2026-09-28 | 16 — tropospheric tracer mixing + in-mixing knobs on the Phase 15 winner (ten-year chains) | **done** (see the leaderboard in the record): base10 / mix10 / mix30 (GPU 0), qbonarrow / hdiff2 / slit2 (GPU 1), n100_10 / n100mix10 / mix10trop (first idle GPU); scored on 1998-1999 as Phase 15 plus the surface clock and the 500->100 hPa transit | [docs/outputs/16_mixing/output.md](docs/outputs/16_mixing/output.md) |
| 2026-10-01 | 17 — JFV equilibrium temperature corrected toward ERA5 (iterated), new ERA5 w* reference | **done**: tracks A (with Rayleigh) / B (without) / B0, four 1998-1999 iterations each, then ten years 1990-1999. T RMSE 5.4 -> 1.3 K, u RMSE 3.7 -> 2.5 m/s, SH polar-night jet 60 -> 70 m/s (ERA5 73); but entry-age RMSE 0.44 -> 0.51 yr, subtropical barrier step 0.95 -> 0.86 yr (CLaMS 1.57) and w* vs ERA5 log-error 0.07 -> 0.21 (weaker ascent 100-30 hPa). The Phase 16 start already matched ERA5 w* | [docs/outputs/17_teq/output.md](docs/outputs/17_teq/output.md) |
| 2026-09-10 | 8d/8e — QBO nudging, tau 2 d and 1 d; **tau 1 d is the default** | **done**: 2005-2009 chains `p8d_5yr`, `p8e_5yr`; amplitude 80 → 90 → 92 % of ERA5, QBO-layer error 4.0 → 2.3 m/s, global u RMSE 4.9 → 4.4, nothing else moves. Mean-preserving target interpolation (`p8f_5yr`): amplitude 92 → 93 % of ERA5, QBO-layer RMS 2.3 → 2.2 m/s (addendum written unattended) | [docs/outputs/08_qbo/output.md](docs/outputs/08_qbo/output.md) |
| 2026-09-10 | 8c — QBO nudging, tau 5 d sensitivity test | **done**, not adopted as default: 2005-2009 chain `p8c_5yr` vs the tau 10 d chain; QBO amplitude 80 → 86 % of ERA5, QBO-layer error 4.0 → 3.1 m/s, everything else unchanged | [docs/outputs/08_qbo/output.md](docs/outputs/08_qbo/output.md) |
| 2026-09-09 | 8b — QBO nudging, window top 1 hPa | **done** (branch `phase8-qbo-nudging`, not pushed): 2005 and the 2005–2009 chain with the window top at 1 hPa; removes the easterly bias above 4 hPa (1–7 hPa error 22.7 → 12.5 m/s), adds the SAO at 2–3 hPa, global u RMSE 6.4 → 4.9 m/s; QBO layer, vortex, age of air unchanged; new default. PDF `docs/outputs/jcm-strat_phase8_qbo.pdf` | [docs/outputs/08_qbo/output.md](docs/outputs/08_qbo/output.md) |
| 2026-09-04 | 8 — QBO nudging to ERA5 | **done** (branch `phase8-qbo-nudging`, not yet pushed): 2005 and the 2005–2009 chain; equatorial u RMS vs ERA5 16 → 4 m/s, QBO amplitude 80 % of ERA5, change confined to the tropics; age of air moves 0.1 yr younger in the tropics | [docs/outputs/08_qbo/output.md](docs/outputs/08_qbo/output.md) |
| 2026-09-03 | 7 — time-step sweep | **done**: 12/30/45/60/90/120 min x 1-2 departure iterations on the Phase 6 configuration; knee at 30 min (2.35x, Antarctic jet -18 percent), >= 60 min unusable | [docs/outputs/07_timestep/output.md](docs/outputs/07_timestep/output.md) |
| 2026-09-03 | 6 — stratosphere without radiation (Polvani-Kushner, seasonal) | A/B of 8 configurations done, choice fixed as `strat_pk` defaults; **done**: 5-year chain (6.4 K / 5.6 m/s vs ERA5, 2 of 3 SSW winters, AoA pattern vs CLaMS); full-ECHAM reference year: better T (4.3 K) but no Arctic vortex and 9.7 m/s | [docs/outputs/06_stratosphere/output.md](docs/outputs/06_stratosphere/output.md) |
| 2026-09-03 | 4 — 5-year run, the Phase-1 number | **done**: 2005–2009 as five chained segments; transport checks pass; age-of-air pattern right but tropics 1.5 yr too old and no polar-night jet (Held-Suarez stratosphere) | [docs/outputs/04_5yr/output.md](docs/outputs/04_5yr/output.md) |
| 2026-09-03 | 3 — passive tracers | **done**: aoa/unity/sai/e90 term, 1-yr run 2005, all acceptance checks pass; mass-fixer/clock interaction found and fixed | [docs/outputs/03_tracers/output.md](docs/outputs/03_tracers/output.md) |
| 2026-09-03 | 2 — specified dynamics | runs done (90 d check, 1-yr 2005), PR open | [docs/outputs/02_nudged/output.md](docs/outputs/02_nudged/output.md) |
| 2026-09-02 | 1 — stripped dry model | run done (1-yr HS), PR open | [docs/outputs/01_dry/output.md](docs/outputs/01_dry/output.md) |
| 2026-09-02 | 0 — environment, baseline | **done**: env built and accepted, two smoke runs, 10-day baseline timed at dt 12 and 15, issues #1–#15 filed | [docs/outputs/00_phase0/output.md](docs/outputs/00_phase0/output.md) |

## Throughput table

Simulated days per wall-clock hour, one H100 (GPU 0), `run=longrun` unless stated.

| Phase | Configuration | Grid | dt [min] | days/hr | ms/step | run | date |
|---|---|---|---|---|---|---|---|
| 0 | JCM full ECHAM physics (reference) | T63L95 | 12 | 51.6 | 582 | `base_echam_l95_10d` | 2026-09-02 |
| 0 | JCM full ECHAM physics (reference) | T63L95 | 15 | 51.9 | 723 | `base_echam_l95_10d_dt15` | 2026-09-02 |
| 1 | P1 dry HS | T63L95 | 12 | 6000.0 (e2e 991) | 5 | `p1_dry_30d` | 2026-09-02 |
| 1 | P1 dry HS | T63L95 | 12 | 5786.9 (e2e 2368) | 5 | `p1_dry_1yr` | 2026-09-02 |
| 2 | P2 SD | T63L95 | 12 | 5454.5 (e2e 2326) | 6 | `p2_sd_1yr` | 2026-09-03 |
| 3 | P3 SD + passive tracers (aoa, unity, sai, e90) | T63L95 | 12 | 4458.4 (e2e 2082) | 7 | `p3_tracers_1yr` | 2026-09-03 |
| 4 | P4 same, 5 years as five chained segments | T63L95 | 12 | 4315 aggregate, 4457–4478 per segment (e2e 1768; 2079–2099 per segment) | 7 | `p4_5yr` (`p4_2005`…`p4_2009`) | 2026-09-03 |
| 6 | P6 SD + tracers + Polvani-Kushner stratosphere | T63L95 | 12 | 4445.3 (e2e 2012) | 7 | `p6_pk_g4_t15_s05_top3` | 2026-09-03 |
| 6 | reference: full ECHAM physics + SD nudging (12 h target), GPU 1 | T63L95 | 12 | 139.9 (e2e 131) | 214 | `ref_echam_sd_2005` | 2026-09-03 |
| 7 | P6 configuration, dt 30 | T63L95 | 30 | 10432 (e2e 1891) | 7 | `p7_dt30` | 2026-09-03 |
| 7 | P6 configuration, dt 45, 2 departure iterations | T63L95 | 45 | 12369 (e2e 3028) | 9 | `p7_dt45_it2` | 2026-09-03 |
| 8b | P8b: + QBO nudging to 1 hPa (the Phase 9 T63L95 point), five chained years | T63L95 | 12 | 3890–3930 per segment (e2e 1872–1904) | 8 | `p8b_5yr` | 2026-09-09 |
| 9 | P8b configuration, strat63 (L95 with mesosphere and troposphere thinned) | T63 strat63 | 12 | 5374 (e2e 1750) | 6 | `p9_t63l63_5yr` | 2026-09-09 |
| 9 | same, strat47 (also 1–30 hPa every other level) | T63 strat47 | 12 | 6228 (e2e 1948) | 5 | `p9_t63l47_5yr` | 2026-09-09 |
| 9 | same, T85 (ten half-year segments) | T85L95 | 9 | 1636 (e2e 847) | 14 | `p9_t85l95_5yr` | 2026-09-10 |
| 9 | same | T85 strat63 | 9 | 2356 (e2e 1075) | 10 | `p9_t85l63_5yr` | 2026-09-09 |
| 9 | same | T85 strat47 | 9 | 3059 (e2e 1356) | 7 | `p9_t85l47_5yr` | 2026-09-09 |
| 9 | same, T119 = 1° (twenty quarter-year segments) | T119L95 | 6 | 557 (e2e 403) | 27 | `p9_t119l95_5yr` | 2026-09-10 |
| 9 | same | T119 strat63 | 6 | 790 (e2e 516) | 19 | `p9_t119l63_5yr` | 2026-09-10 |
| 9 | same (ten half-year segments) | T119 strat47 | 6 | 1045 (e2e 697) | 14 | `p9_t119l47_5yr` | 2026-09-10 |

## Wall-clock per simulated year and per six simulated hours

One H100, T63L95. Stepping excludes JIT compile and output writing; end-to-end includes both. Six simulated hours is the interval one emulator step would cover. Generated by `python scripts/make_report.py --walltime-md`.

| Configuration | dt | sim. days per hour (stepping / end-to-end) | one simulated year (stepping / end-to-end) | six simulated hours (stepping) |
|---|---|---|---|---|
| Phase 0: stock JCM, full ECHAM physics | 12 min | 52 / 47 | 7.1 h / 7.8 h | 17.44 s |
| Phase 0: same, 15 min step | 15 min | 52 / 47 | 7.0 h / 7.8 h | 17.34 s |
| Phase 1: dry Held-Suarez | 12 min | 5,787 / 2,368 | 3.8 min / 9.2 min | 0.16 s |
| Phase 2: + ERA5-nudged troposphere | 12 min | 5,454 / 2,326 | 4.0 min / 9.4 min | 0.17 s |
| Phase 3: + four passive tracers | 12 min | 4,458 / 2,082 | 4.9 min / 10.5 min | 0.20 s |
| Phase 4: same, five chained one-year segments (per-segment mean) | 12 min | 4,467 / 2,087 | 4.9 min / 10.5 min | 0.20 s |
| Phase 6: + Polvani-Kushner stratosphere (chosen) | 12 min | 4,445 / 2,012 | 4.9 min / 10.9 min | 0.20 s |
| Phase 6 reference: full ECHAM physics + SD nudging (12 h target) | 12 min | 140 / 131 | 2.6 h / 2.8 h | 6.4 s |
| Phase 8b: + QBO nudging to 1 hPa (T63L95) | 12 min | 3,900 / 1,890 | 5.6 min / 11.6 min | 0.23 s |
| Phase 9: same on strat63 (T63, 63 levels, stratosphere intact) — recommended | 12 min | 5,374 / 1,750 | 4.1 min / 12.5 min | 0.17 s |
| Phase 10: strat63 production — 15 tracers, omega, 6-hourly instantaneous output (output-bound) | 12 min | 4,760 / 860 | 4.6 min / 26 min | 0.20 s |
| Phase 11: same with 24 tracers (unit-amplitude Gaussian + box twins, no surface sink, 1 hPa tracer lid); two chains at once on GPUs 0 and 1 | 12 min | 4,180 / 750 | 5.2 min / 29 min | 0.22 s |
| Phase 9: same on strat47 (T63, 47 levels) | 12 min | 6,228 / 1,948 | 3.5 min / 11.2 min | 0.14 s |
| Phase 9: same at T85L95 (dt 9) | 9 min | 1,636 / 847 | 13.4 min / 26 min | 0.55 s |
| Phase 9: same at T119L95, the 1° grid (dt 6) | 6 min | 557 / 403 | 39 min / 54 min | 1.6 s |
| Phase 10 | production tracer set, 6-h instantaneous output, QBO tau 1 d | strat63 | 12 | 4,760 (e2e 860) | 6 | p10_2005-2009 review chain (`p10rev_5yr`); 1990-2019 chain `p10_30yr` running | 2026-09-11 |
| Phase 11 | tracer lid above 1 hPa (WACCM targets), 24 tracers, no surface sink; A no sink / B lid sink | strat63 | 12 | 4,180 (e2e 750) | 7 | `p11a_5yr`, `p11b_5yr` 1990-1994; extension to 2019 pending | 2026-09-16 |
| Phase 12 | circulation tests vs a control: QBO nudging off (`p12_noqbo`), full L95 troposphere (`p12_l81`, strat81); clock `aoa500`; injection tracers not written | strat63 / strat81 | 12 | 4,440 / 4,990 / 3,590 (e2e 800-880 for all) | 7 / 6 / 8 | `p12ctl_5yr`, `p12noqbo_5yr`, `p12l81_5yr` 1990-1994 done; QBO off weakens the lower branch (+0.3 yr age), strat81 doubles the deep branch, stratospheric age unchanged | 2026-09-16 |
| Phase 14 | JCM full ECHAM physics, free-running (no ERA5, no QBO nudging), Phase 12 clocks (`p14_free`) | T63L95 | 12 | 157-169 (e2e 115-122) | 177-192 | `p14free_10yr` 1990-1999: equatorial lower-strat descent, deep branch 2.8x WACCM6, 55 hPa age 1.81 tropics / 2.41 extratropics | 2026-09-24 |
| Phase 12, run 4 | JCM full ECHAM physics + the same nudging, QBO term and clocks (`p12_echam`) | T63L95 | 12 | 146-166 (e2e 106-118) | 181-206 | `p12echam_5yr` 1990-1994: tropical age of air = CLaMS (1.33 / 3.64 yr at 55 / 12 hPa); extratropics 1.4 yr too young, shallow branch 3x WACCM6 | 2026-09-21 |
| Phase 13 | dry + Hines/Lott-Miller GWD (`p13_gwd`), the same on native L95 (`p13_gwd_l95`), strat81 nudged only below 400 hPa (`p13_l81_n400`) | T63L63 / L95 / L81 | 12 | 2580–2690 (e2e 660–711) / 1860–1920 (e2e ~450) / 3540–3590 (e2e ~850) | 11 / 16 / 8 | `p13gwd_5yr`, `p13gwdl95_5yr`, `p13l81n400_5yr` 1990-1994: drag closes the tropical age (55 hPa 1.35 vs CLaMS 1.33) via a 2.6× shallow branch, extratropics 1.4 yr too young, 10 hPa ascent collapses, mesosphere still downward; L95 changes ≤ 0.2 yr; 400 hPa cutoff ages everything 0.3–0.6 yr | 2026-09-23 |
| Phase 13b | Jucker et al. (2013) relaxation in place of Polvani-Kushner (`p13_jucker`), + Hines/Lott-Miller (`p13_jucker_gwd`) | T63L81 | 12 | 3415–3570 (e2e ~850) / 2180 (e2e ~530) | 8–9 / 14 | `p13jucker_5yr`, `p13juckergwd_5yr` 1990-1994: JFV relaxation alone VENTILATES THE MESOSPHERE (tropical w* 1-0.3 hPa upward, polar descent 1.7-4.9 mm/s, no drag), 10 hPa w* 0.41 (WACCM 0.47), extratropical age right; 30 hPa stall remains, tropical 55 hPa 0.25 yr older; drag on top repeats the Phase 13 damage | 2026-09-24 |
| Phase 13c | Jucker + drag, ERA5 nudging only below 400 hPa, 10 yr: Hines + Lott-Miller (`p13_jucker_gwd_n400`) / Hines only (`p13_jucker_hines_n400`) | T63L81 | 12 | 2170–2200 (e2e ~530) / 2460–2510 (e2e ~600) | 14 / 12 | `p13jgn400_10yr`, `p13jhn400_10yr` 1990-1999: the 400 hPa cutoff removes the shallow branch (100 hPa w* 0.06 / 0.10 vs WACCM 0.40) and ages the tropics to 2.9 / 2.3 yr at 55 hPa; deep branch (10 hPa 0.36 / 0.58) and mesosphere at ECHAM strength; Lott-Miller off better everywhere (ages 0.7-0.8 yr younger) | 2026-09-25 |
| Phase 13d | Jucker + Hines only (no Lott-Miller), nudged below 150 hPa (`p13_jucker_hines`) | T63L81 | 12 | 2460–2520 (e2e 695–737) | 12 | `p13jh_5yr` 1990-1994: BEST DRY CONFIGURATION SO FAR — shallow branch 0.33 mm/s (WACCM 0.40, no overshoot), deep branch 0.49 (0.47), mesosphere at ECHAM strength (0.3 hPa +2.0 / −4.1 / −6.9), entry ages 0.13–0.23 yr younger than no drag (55 hPa tropics 1.41, 50–70° 3.47, 12 hPa 3.45); Lott-Miller confirmed as the whole Phase 13/13b shallow-branch damage; 30 hPa still 0.04 (stride-4 sampled) | 2026-09-25 |
| Phase 13d, 10 yr | the same chain extended 1995-1999 (`p13jh_10yr`), diagnostics at stride 1 | T63L81 | 12 | 2470–2510 (e2e 719–748) | 12 | STRIDE 1: tropical w* 100/70/50/30/10 hPa 0.35/0.30/0.34/0.37/0.49 (WACCM 0.40/0.21/0.20/0.26/0.47) - the '30 hPa stall' of Phases 12-13d was the 06 UTC tidal phase; circulation stationary 5 -> 10 yr; entry age 50-70 55 hPa 3.47 -> 3.60 (criterion met), tropics 55 hPa 1.41 -> 1.62 (WACCM 1.19, NOT converged at 5 yr, in-mixing), 12 hPa 3.47 converged; 1 hPa tropical ascent +1.0 at stride 1 | 2026-09-25 |

(e2e = end-to-end incl. compile and output writing.) Reference from upstream (A100-40GB, `docs/source/design/dinosaur_sl_jam_configuration.md` in
JCM): T63L47 full science 115 days/hr at dt=15 min; T63L95 full science 52 days/hr.
