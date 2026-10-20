# Phase 21 — full-physics references rerun on the new jcm (fixed Lott-Miller SSO)

Status: **complete** (pipeline `/data/JCM_stripped/jcm-strat-phase19/scripts/phase21_run.sh`, tmux `strat_p21_run`, launched
2026-10-07 12:02 PDT, commit 3b5768c; chains 12:34 PDT Oct 7 → 23:15 PDT (21a) / 09:01 PDT Oct 8 (21b); diagnostics to 12:02 PDT
Oct 8; two Phase 20 comparisons were rerun by hand over 1990–1994 by the failure agent, 12:03–13:00 PDT; this write-up 13:00 PDT).
Every decision with its options: [decisions.md](decisions.md); the set-up decisions shared by Phases 19–21 are in the Phase 19 log
(`/data/JCM_stripped/jcm-strat-phase19/docs/outputs/19_jcm_update/decisions.md`).

**Headline.**
- **(i) "Nudging puts tropical age on CLaMS" (Phase 12 run 4) does NOT survive.** With the new jcm, the fixed Lott-Miller
  and the nudging cutoff moved from 150 to 400 hPa, the nudged full physics has a WACCM-like shallow branch (100 hPa w*
  1.46 → 0.46 mm/s, WACCM6 0.40). Its tropical air is now too *young*: surface clock at 55 hPa 0.96 yr (CLaMS 1.33), at
  12 hPa 2.29 (3.68); entry age `aoa150` 0.44 / 1.81 (WACCM6 1.19 / 2.90). The old match to CLaMS was a coincidence of a
  shallow branch 3.7× too strong and a deep branch 1.7× too strong.
- **(ii) "Free-running lower-stratospheric tropical w* is downward" (Phase 14) does NOT survive either, for two reasons.**
  (a) The −0.05 / −0.22 / −0.28 mm/s at 100 / 70 / 50 hPa was a **stride-4 reading**. The same old run read at stride 1 gives
  +0.17 / +0.10 / +0.01: near-zero ascent, not descent. (b) On the new jcm, the free run's tropical w* is **on WACCM6 and
  ERA5 at every level**: 100 / 70 / 50 / 30 / 10 hPa = 0.37 / 0.24 / 0.22 / 0.28 / 0.54 mm/s (WACCM6 0.40 / 0.21 / 0.20 / 0.26 / 0.47;
  ERA5 1998–99 0.42 / 0.24 / 0.27 / 0.33 / 0.44). The 100 hPa mass flux is 10.9 (WACCM6 10.9), the JJA monsoon excess is gone
  (33 → 9.6 × 10⁹ kg/s), and there is a real tropical pipe: equatorial age *minimum*, 55 hPa age contrast 0.6 → 2.4 yr.
- **21b (free-running, new jcm) is now the best-scoring configuration of the project**: composite 1.39 (old free 2.26,
  21a 1.51), w log-error 0.14. Its weak points are the extratropical lower stratosphere, which is still too young (55 hPa
  50–70° 3.83 vs CLaMS 4.12, entry age 3.17 vs WACCM6 3.40), and the polar vortices: 10 hPa u at 60°S in JJA is 51 m/s
  (ERA5 73), and at 60°N in DJF 8.8 (ERA5 27).
- Both chains ran **healthy, with no health stops and no humidity exemption**. That is 15 model-years with the fixed
  Lott-Miller in full physics. The dry Phase 20 run with the same scheme blew up east of Tibet; that problem is specific
  to the dry configuration.

## What was run

| | 21a `p21_echam_n400` (PREFIX `p21echam`) | 21b `p21_free` (PREFIX `p21free`) |
|---|---|---|
| = old run | Phase 12 run 4 `p12echam_5yr` (old jcm 849893be) | Phase 14 `p14free_10yr` (old jcm) |
| physics | full ECHAM (RRTMGP, convection, PBL, Hines GWD, **fixed** Lott-Miller SSO) + `QboNudging` term + `echam_surface_exchange` | same, **no** QBO term |
| ERA5 nudging | below **400 hPa** (`min_pressure_hpa: 400`; old run 150), T included, τ 6 h, 12-h target | none |
| grid / dt | T63L95, 12 min, cubic SL vertical interpolation (`sl_vertical_interpolation: null`) | same |
| sponge | ECHAM `uspnge` (`run.sponge.levels=1`), no `target_T_K` (old: 10 levels, T → 250 K) | same |
| spin-up | 1989-12-01 + 31 d from ERA5, discarded; dynamics carried over, clocks re-initialised 1990-01-01 (`first_segment=true`) | same |
| years | 1990–1994 (`runs/p21echam_5yr`) | 1990–1999 (`runs/p21free_10yr`, first 5 yr `runs/p21free_5yr`) |
| GPU | 2 | 3 |
| throughput | 178–184 sim d/h stepping, 171–177 e2e = **2.1 h/yr** (old 3.1–3.4) | 179–189 / 176–186 e2e = **2.0 h/yr** (old 3.1) |
| health | no stops (watchdog `strat_p21_watch` clean), `health_ignore_q_max=False` | same |

Throughput per segment: [throughput_p21.csv](throughput_p21.csv). Runs live in `/data/JCM_stripped/jcm-strat-phase19/runs/`
(Phase 19 worktree; this worktree's `runs` is a symlink to it).

Diagnostics come from `scripts/phase12_compare.py`, the same as Phases 12/14. TEM uses **every 6-hourly frame (stride 1)**.
Age is the mean of the last 240 frames. References are WACCM6 histSST 1996–2014 (w*, mass flux, entry age) and CLaMS
v3.1/ERA5 2005–2009 (surface clock). Comparison tags:

| tag | before → after | files |
|---|---|---|
| `echam_rerun` | p12echam_5yr → p21echam_5yr | [echam_rerun_metrics.md](echam_rerun_metrics.md), `echam_rerun_*.png` |
| `free_rerun10` | p14free_10yr → p21free_10yr | [free_rerun10_metrics.md](free_rerun10_metrics.md), `free_rerun10_*.png` |
| `free_rerun5` | p14free_5yr → p21free_5yr | [free_rerun5_metrics.md](free_rerun5_metrics.md), `free_rerun5_*.png` |
| `echam_vs_p20` | Phase 20 p20jhsso_5yr → 21a (1990–1994) | [echam_vs_p20_metrics.md](echam_vs_p20_metrics.md), `echam_vs_p20_*.png` |
| `free_vs_p20_5yr` | Phase 20 p20jhsso_5yr → p21free_5yr (**5 yr**, not the planned 10: Phase 20 stopped in 1997, decisions.md 12:03) | [free_vs_p20_5yr_metrics.md](free_vs_p20_5yr_metrics.md), `free_vs_p20_5yr_*.png` |
| CLaMS/WACCM triptychs | p21echam_5yr, p21free_10yr, three clocks | `p21echam_5yr_*`, `p21free_10yr_*` |
| mesosphere | 21a 1994, 21b 1999 + 1994, Phase 20 1994, Phase 12 run 4 1994 | [p21_mesosphere.md](p21_mesosphere.md), [p21_mesosphere.png](p21_mesosphere.png) |
| scores (`sweep_score.py`, last 2 yr) | p21echam_5yr (1993–94, w vs WACCM6), p21free_10yr and p14free_10yr (1998–99, w vs ERA5) | [scores/](scores/) |

`era5_check/` holds Susanne's own 21a-vs-ERA5 check (`runs/p21a_era5_check.sh`). Its first output was committed with the pipeline
plots. When this was written a rerun was still going (tmux `eval_p21a_era5`), so it is described below but not interpreted.

## Results 21a — nudged full physics, old → new jcm

Tropical (15°S–15°N) annual w* [mm/s] and up-flux [10⁹ kg/s], stride 1:

| | 100 hPa | 70 | 50 | 30 | 10 | flux 100 | flux 70 | flux 10 |
|---|---|---|---|---|---|---|---|---|
| Phase 12 run 4 (old jcm, n150) | 1.457 | 0.595 | 0.152 | 0.182 | 0.800 | 27.6 | 12.1 | 2.32 |
| **21a** (new jcm, n400) | **0.459** | **0.354** | 0.298 | 0.305 | **0.555** | **13.6** | 9.0 | **1.53** |
| Phase 20 dry 13d + fixed LM, n400 | 0.127 | 0.200 | 0.278 | 0.325 | 0.420 | 9.3 | 6.5 | 1.30 |
| WACCM6 | 0.398 | 0.211 | 0.201 | 0.255 | 0.469 | 10.9 | 6.1 | 1.37 |

- **The residual circulation moves most of the way to WACCM6** ([echam_rerun_wstar.png](echam_rerun_wstar.png),
  [echam_rerun_wstar_tropics.png](echam_rerun_wstar_tropics.png)). The 100 hPa overshoot is gone and the up-flux halves. The deep
  branch weakens to 1.2× WACCM6 (10 hPa). The 50–30 hPa minimum of the old run is filled (0.15 → 0.30), so the profile is now
  WACCM-shaped from 100 to 3 hPa, about 0.1 mm/s too strong between 70 and 30 hPa. The DJF/JJA 100 hPa up-flux is 15.3 / 12.1
  (WACCM6 14.1 / 9.4), down from 43.9 / 35.0. In JJA the old run had strong ascent over the summer subtropics (0–40°N, monsoon);
  21a has it at WACCM strength.
- **The age moved past the references** ([echam_rerun_age_profiles.png](echam_rerun_age_profiles.png),
  `echam_rerun_age_aoa*.png`, `p21echam_5yr_*_triptych.png`):

| clock / region | old | **21a** | reference |
|---|---|---|---|
| `aoa_sfc` 55 hPa tropics / 50–70° | 1.33 / 2.73 | **0.96** / 2.98 | CLaMS 1.33 / 4.12 |
| `aoa_sfc` 12 hPa tropics / 50–70° | 3.64 / 4.38 | **2.29** / 3.75 | CLaMS 3.68 / 4.56 |
| `aoa150` 55 hPa tropics / 50–70° | 0.96 / 2.41 | **0.44** / 2.55 | WACCM6 1.19 / 3.71 (score window 1.11 / 3.40) |
| `aoa150` 12 hPa tropics | 3.33 | **1.81** | WACCM6 2.90 |

  The latitude contrast grows (55 hPa `aoa150` 1.45 → 2.11 yr; WACCM6 ~2.3). Above ~30 hPa the tropics are 1.3–1.6 yr younger
  than before, and so are the subtropics up to ±30°. In the new run a narrow tropical tongue of young air runs from 100 hPa
  to ~1 hPa, where CLaMS and WACCM6 have a broad one. Below ~40 hPa the extratropics became 0.3–1.2 yr *older* (more realistic),
  but they are still 1.1 yr short of CLaMS at 55 hPa. The tropical age profile is now younger than CLaMS at every level above
  ~70 hPa. The surface→150 hPa transit is unchanged (~0.5 yr, `aoa_sfc` − `aoa150`), so the change is inside the stratosphere.
- **Mesosphere** ([p21_mesosphere.md](p21_mesosphere.md)): the cell is intact, with tropical ascent and polar descent of
  3–5 mm/s at 0.3 hPa. Tropical ascent at 2–0.5 hPa is similar to the old run's (+0.4 to +1.7). The 1 hPa tropical value dips
  to +0.36. Because the young air sits in a narrow tropical tongue, ages vary strongly with latitude near the top: the lat-std
  of `aoa150` at 3 / 1.5 hPa is 0.58 / 0.57 yr (old 0.18 / 0.14). The memory note on the smoke test (mesospheric winds ~150 m/s with the ECHAM sponge vs ~90 old) was not
  re-diagnosed here. Susanne's `era5_check/strat_climatology_21a.png` shows equatorial u near 1 hPa
  30–40 m/s more westerly than ERA5 in both seasons.
- **Vortices** (scores, `era5_check/vortex_series.png`): 21a u at 10 hPa, 60°S JJA, is 47 m/s (ERA5 73; WACCM6 ~88), and the
  SH vortex breaks down 1–2 months early every year. At 60°N DJF it is 8.8 m/s (ERA5 34) and highly disturbed. Too much wave
  driving and too weak vortices are the issue #35 picture. The new jcm improved u RMSE but did not cure this. Scores: u RMSE
  9.6 m/s, T RMSE 4.9 K.
- **vs Phase 20 (same new jcm, same fixed LM, same n400; dry 13d physics), [echam_vs_p20_metrics.md](echam_vs_p20_metrics.md):**
  above 50 hPa the two have almost the same tropical w* (50 / 30 / 10 hPa 0.28 / 0.33 / 0.42 vs 0.30 / 0.31 / 0.56). Below that,
  full physics has the shallow branch the dry model lacks (100 hPa 0.46 vs 0.13). Yet 21a's air is 0.7–1.3 yr younger by every
  clock and region. Phase 20 sits much closer to CLaMS at 55 hPa (2.25 / 4.11 surface clock vs CLaMS 1.33 / 4.12).

### (i) Does "nudging puts tropical age on CLaMS" survive?

**No.** The new nudged run is 0.37 yr too young at 55 hPa and 1.4 yr too young at 12 hPa by the surface clock. It is
0.7–1.1 yr younger than WACCM6 by the entry clock.

**Separating the causes.** 21a changed two things at once: the code (new jcm + dinosaur 1.5, fixed Lott-Miller, ECHAM sponge,
cubic SL) and the nudging cutoff (150 → 400 hPa). The cleanest design would be a 2×2 (code × cutoff). Only the old/150 and
new/400 corners exist for nudged full physics. The free pair (old vs new code, no nudging) gives the effect of the code
without the cutoff, as long as the code acts the same way with and without nudging:

| quantity | Δ free (code only) | Δ nudged (code + cutoff) | residual = cutoff + interaction |
|---|---|---|---|
| tropical w* 100 hPa [mm/s] | +0.20 | **−1.00** | **−1.2** |
| tropical w* 70 hPa | +0.14 | −0.24 | −0.38 |
| up-flux 100 hPa annual [10⁹ kg/s] | −0.6 | −14.1 | −13.5 |
| up-flux 100 hPa JJA | −23.8 | −23.0 | ~0 |
| tropical w* 10 hPa | −0.33 | −0.25 | ~0 |
| `aoa150` 55 hPa tropics [yr] | −0.71 | −0.52 | +0.2 |
| `aoa150` 12 hPa tropics | −0.70 | −1.53 | −0.8 |
| `aoa150` 55 hPa 50–70° | +1.09 | +0.14 | −0.95 |

The comparison attributes some changes to the code and some to the cutoff, and leaves one open:

- **Due to the code:** the deep-branch reduction (10 hPa) and the loss of the JJA summer-subtropical (monsoon) excess. Both
  happen equally with and without nudging.
- **Due to the cutoff:** the collapse of the year-round 100 hPa shallow-branch overshoot (−1.0 mm/s, −14 × 10⁹ kg/s). The
  code alone *raises* 100 hPa w* in the free run, so the cutoff must be what removes it in 21a. This agrees with Phase 13c,
  where the 400 hPa cutoff removed the shallow branch of the dry model (100 hPa w* 0.33 → 0.06–0.10). Phase 12 run 4's strong
  shallow branch came from nudging the 150–400 hPa layer toward ERA5. That is the same mechanism Phase 14 named ("the nudging's
  shallow branch"), and Phase 21 confirms it.
- **Tropical age at 55 hPa:** this is mostly the code. The free run gets younger by the same amount (−0.7 yr) with no
  nudging at all. Phase 19's dry baseline shows the same thing: the jcm update + cubic SL makes every clock 0.4–1.4 yr younger
  at nearly unchanged w*.
- **Cannot be separated:** the extra −0.8 yr at 12 hPa in the tropics, and the extratropical 55 hPa age (+1.1 yr in the free
  run, +0.1 in the nudged). These need a nudged run on the new jcm with the old 150 hPa cutoff, or the old jcm with 400 hPa.
  The code's effect also need not be additive. The free run has no QBO term and no nudged troposphere, and both change how
  wave drag and the fixed SSO project onto the stratosphere. The table is an estimate, not a decomposition.

So the CLaMS match in Phase 12 depended on an artefact of the 150 hPa cutoff (the shallow-branch overshoot) and on the old
code's slower transport, which offset each other. Neither survives.

## Results 21b — free-running full physics, old → new jcm

Tropical (15°S–15°N) annual w* [mm/s], stride 1, 10-yr runs ([free_rerun10_wstar*.png](free_rerun10_wstar_tropics.png)):

| | 100 hPa | 70 | 50 | 30 | 10 | flux 100 | flux 70 | flux 10 | JJA flux 100 |
|---|---|---|---|---|---|---|---|---|---|
| Phase 14 as recorded (stride 4) | −0.05 | −0.22 | −0.28 | +0.01 | +1.32 | 12.6 | 7.5 | 3.1 | 36 |
| Phase 14 re-read at **stride 1** | +0.168 | +0.101 | +0.009 | +0.178 | +0.873 | 11.6 | 5.1 | 2.47 | 33.3 |
| **21b** (new jcm) | **0.367** | **0.238** | **0.222** | **0.284** | **0.541** | **10.9** | 7.4 | **1.53** | **9.6** |
| WACCM6 | 0.398 | 0.211 | 0.201 | 0.255 | 0.469 | 10.9 | 6.1 | 1.37 | 9.4 |
| ERA5 1998–99 (scores) | 0.417 | 0.240 | 0.267 | 0.327 | 0.442 | 11.9 | 5.9 | 1.09 | — |

- **The residual circulation is now WACCM-like at every level and season.** DJF 100 / 70 / 50 hPa is 0.40 / 0.25 / 0.25
  (WACCM6 0.45 / 0.25 / 0.23); JJA is 0.25 / 0.19 / 0.20 (0.28 / 0.13 / 0.14). The lat-height maps show ascent centred on the
  equator, not in the summer subtropics. The old run's tropical eddy-driven structure (Eulerian w̄ negative at 150–50 hPa
  over the equator, offset by the eddy term) is gone. Now w̄ ≈ w* as in WACCM6 ([free_rerun10_wstar_tropics.png](free_rerun10_wstar_tropics.png)).
  The old run's 70 hPa monthly w* swung between −0.1 and +0.5. The new one follows the WACCM6 annual cycle at 0.15–0.35.
  `w_logerr` against ERA5 is 1.09 → **0.14**.
- **Age: a tropical pipe appears** ([free_rerun10_age_profiles.png](free_rerun10_age_profiles.png),
  [free_rerun10_age_aoa150.png](free_rerun10_age_aoa150.png), `p21free_10yr_*_triptych.png`). The old run had an equatorial
  age *maximum* at 55 hPa between minima at ±20–25°, the fingerprint of the weak equatorial ascent. The new run has a single
  equatorial *minimum*, as in CLaMS and WACCM6:

| clock / region | Phase 14 | **21b** | reference |
|---|---|---|---|
| `aoa_sfc` 55 hPa tropics / 50–70° | 1.81 / 2.41 | **1.45 / 3.83** | CLaMS 1.33 / 4.12 |
| `aoa_sfc` 12 hPa tropics / 50–70° | 3.63 / 4.54 | **3.31 / 4.73** | CLaMS 3.68 / 4.56 |
| `aoa150` 55 hPa tropics / 50–70° | 1.45 / 2.08 | **0.74 / 3.17** | WACCM6 1.19 / 3.71 (score window 1.11 / 3.40) |
| `aoa150` 12 hPa tropics | 3.31 | **2.60** | WACCM6 2.90 |
| 55 hPa contrast (`aoa_sfc`) | 0.6 | **2.4** | CLaMS 2.8 |

  By the surface clock, 21b is the closest any jcm-strat run has come to CLaMS at both levels and both regions (`age_rmse`
  aoa_sfc 0.46 yr; old 0.85, 21a 0.92). By the entry clock it is too young in the tropics (0.74 vs 1.19 at 55 hPa). That
  means the troposphere→150 hPa transit (0.7 yr in the tropics) is long: the surface clock is right for partly the wrong
  reason. The SH polar lower stratosphere is now *older* than CLaMS (5.4 yr at 85°S, 55 hPa). In the NH the 55 hPa
  50–70° band is still 0.3 yr short.
- **Spin-up**: 5 → 10 yr ([free_rerun5_metrics.md](free_rerun5_metrics.md)): w* changes ≤ 0.01 mm/s. The tropical ages are
  converged at 55 hPa (+0.03) but still rising at 12 hPa (+0.36 `aoa_sfc`) and in the extratropics (55 hPa 50–70° +0.39). The
  10-yr numbers are therefore the ones to quote, and they are still a lower bound for the upper-stratosphere and polar ages.
- **Mesosphere**: intact. At 0.3 hPa: tropics +0.95, NH cap −3.4, SH cap −6.4 mm/s (1999). The 1 hPa tropical ascent is
  +1.6, the most of any run in the table. The latitudinal age gradient near the top is moderate (lat-std of `aoa150`
  0.29 / 0.36, vs 21a 0.58 / 0.57).
- **Scores** (1998–99, [scores/](scores/)): composite 2.26 → **1.39**, u RMSE 15.1 → 13.0 m/s, T RMSE 6.8 → 5.3 K. 60°S JJA
  10 hPa u is 51 m/s (ERA5 73), better than old (39) but still weak. 60°N DJF is 8.8 (ERA5 27). The free package still has no
  QBO (Phase 14 addendum); that was not re-checked here.
- **vs Phase 20 (dry + fixed LM, nudged < 400 hPa), 1990–1994 only** ([free_vs_p20_5yr_metrics.md](free_vs_p20_5yr_metrics.md)):
  the free full physics has the stronger, more realistic shallow branch (100 hPa 0.37 vs 0.13). Above 50 hPa the two are close
  (Phase 20 slightly stronger at 50–30, weaker at 10). 21b is 0.4–0.8 yr younger everywhere. Phase 20's surface clock is
  the closer to CLaMS at 55 hPa 50–70° (4.11 vs 3.44 at 5 yr) and at 12 hPa, while 21b is closer in the tropics at 55 hPa.

### (ii) Does "free-running lower-stratospheric tropical w* is downward" survive?

**No.**
1. **Sampling.** The Phase 14 numbers came from stride-4 TEM (`free10_metrics.md`: "every 4th 6-hourly frame"), the
   tide-biased reading Phase 15 later found. Re-read at stride 1, the *same* old run has an annual 15°S–15°N w* of +0.17 /
   +0.10 / +0.01 mm/s at 100 / 70 / 50 hPa. That is weak ascent, near zero at 50 hPa, with seasonal descent only at 70–50 hPa
   in DJF (−0.05 / −0.02) and at 100 hPa in JJA (−0.23). The robust part of the Phase 14 finding is the equatorial age maximum
   and the missing tropical pipe. Age does not depend on the sampling stride, so these were real: a shallow branch far too
   weak at the equator, displaced into the summer subtropics.
2. **The fixed code.** On the new jcm, that weakness is gone as well. 21b's lower-stratospheric tropical ascent is within
   ±0.05 mm/s of WACCM6 at 100–30 hPa, and the age has an equatorial minimum. Phase 21 cannot say *which* change in the code
   did it: fixed Lott-Miller, ECHAM sponge, cubic SL, dinosaur 1.5's hybrid-level T equation and the other jcm 3 changes all
   came together. The broken Lott-Miller (100× drag deposited through the column) is the obvious suspect, because it also
   explains the monsoon-season 100 hPa excess (33 → 9.6), but that is not proven.

Phase 14's corollary was that the package alone has no tropical pipe, and that the dry model and the free package are mirror
images. That is withdrawn: the new free package has both branches near WACCM6.

## Open questions / follow-ups (not run)

- **Attribution of the 21a/21b changes.** Separating the cutoff from the code in (i) needs a nudged new-jcm run with
  `min_pressure_hpa: 150` (≈ 2 h/yr, 5 yr). Separating the code changes in (ii) needs the free run on the new jcm with the
  *old* Lott-Miller behaviour, which jcm cannot select, or with the old sponge. The Phase 19 open question (jcm vs grid vs
  cubic SL for the young ages) applies here as well.
- **Which free/nudged configuration is the full-physics reference now?** 21b scores best overall and is the only run with a
  WACCM-like w* profile *without* nudging the troposphere toward ERA5. Its weaknesses are the weak vortices and the missing
  QBO. 21a adds the QBO term but has too-young air.
- **Why is the new full physics younger than WACCM6 by the entry clock** (21a 0.44, 21b 0.74 vs 1.19 at 55 hPa tropics) while
  its w* is close to WACCM6? This is the same pattern as Phase 19 (younger at unchanged w*). It points to less mixing or
  recirculation into the tropical pipe (cubic SL less diffusive?) rather than to the residual circulation.
- **21a's upper-stratosphere/mesosphere:** a narrow young tongue up to 1 hPa, high latitudinal age spread at 3–1.5 hPa, and
  +30–40 m/s equatorial u near 1 hPa vs ERA5 (Susanne's era5_check). Check the ECHAM sponge with the QBO term (the term nudges
  to 1 hPa?) against the mesospheric winds of ~150 m/s seen in the smoke test.
- **Vortices too weak in both** (10 hPa 60°S JJA ~50 m/s vs 73; 60°N DJF ~9 vs 27–34; early SH breakdown): issue #35 survives
  the fixed drag.
- **Fixed Lott-Miller is stable in full physics** (15 model-years, no q spikes, no health stop) but not in the dry 13d
  configuration (Phase 20: #62 q spikes, 1997 blow-up east of Tibet). Moist physics and PBL may damp what the dry
  configuration amplifies. Input for the Phase 20 stabiliser decision.
- `free_vs_p20` at 10 yr and the 1999 Phase 20 mesosphere row need Phase 20 rerun to 1999 (`cmp` line in
  `scripts/phase21_run.sh`).
- 21b 1990–1999 vs ERA5 u/T climatology (`strat_compare.py`), as Susanne is doing for 21a, and `qbo_compare.py` on 21b to
  confirm the free package still has no QBO/SAO on the new jcm.
- Plot artefacts: the monthly w* series end in a one-frame January spike (21a +1.5 at 70/30 hPa in 1995, 21b −0.85 at 30 hPa
  in 2000), and the old Phase 12 run 4 monthly curve has gaps (not investigated). Neither
  affects the annual or seasonal tables.
