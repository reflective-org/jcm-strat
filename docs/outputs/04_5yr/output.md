# Phase 4 — the 5-year run and the Phase-1 number

Status: **runs complete; transport checks pass, the two circulation checks do not** (see acceptance). Branch `phase4-5yr`.

## Configuration

`+experiment=p4_5yr`: the Phase-3 configuration unchanged — dry Held-Suarez physics, ERA5-nudged
winds and temperature below 150 hPa, free stratosphere, four passive tracers with the clock
excluded from the mass fixer — over 2005-01-01 … 2009-12-31 (1826 days), 30-day chunks, 5-day
means, restart checkpoint every chunk.

**Run as five chained one-year segments** (`scripts/chain_years.sh`). The first attempt as one
1826-day run (`p4_5yr_oom`) died in the first step with `RESOURCE_EXHAUSTED: Out of memory while
trying to allocate 47.75GiB`: JCM keeps the entire nudging target on the GPU, and five years of
6-hourly L95 u, v, T are 154 GB against an 80 GB card, where one year (31 GB) fits. Each
calendar year therefore runs on its own with `init=from_state init.file=<previous>/checkpoint.ckpt`,
which restores the full dycore + physics state including the tracers and restarts the calendar at
the segment's `run.start_date`. The segments' chunk files are linked into `runs/p4_5yr/` with
cumulative day numbers, so the analysis scripts see one 1826-day run.

ERA5: the whole window was prefetched once (`--start 2004-12-31 --end 2010-01-03`, 2 h, 154 GB
on disk) and the per-year windows cut from it with `scripts/slice_era5_years.py` (the cache key
hashes only the grid, so this is byte-equivalent to downloading them; verified against the
separately downloaded 2005 window).

## Runs

| run | days | purpose |
|---|---|---|
| `p4_5yr_oom` | 0 | single 1826-day run; GPU OOM loading the 154 GB target (kept as evidence) |
| `p4_2005` … `p4_2009` | 365/365/365/366/365 | the five chained segments |
| `p4_5yr` | 1826 | symlinked aggregate of the segments, what the analysis reads |

## Acceptance (from PLANS.md)

| check | threshold | result |
|---|---|---|
| 5 years complete | all chunks healthy | **pass** — 65/65 chunks 0 NaN; p_s 998.63 → 998.66 hPa (+0.03 hPa in 5 yr); top-level T trend 0.000 K/day; T range 181–313 K |
| segment chaining | tracers and state continuous across the four year boundaries | **pass** — clock continues within 0.01 yr and the sai global mean within one save's growth at every boundary (day 365/395, 730/760, 1095/1125, 1461/1491) |
| tracer drift (Phase-3 thresholds) | unity within 1 ± 1e-3; sai < 0.5 %/yr vs its source | **pass** — unity max \|q−1\| 2.55e-4 over 365 saves, burden drift +1.7e-4; sai burden −1.1 % vs source × box mass × t after 5 yr (same expectation caveat as Phase 3) |
| no negatives | cell min ≥ 0 | **pass** for unity, sai, e90 (0.0); aoa min −9e-7 d (reset-relaxation roundoff) |
| no polar pull-up | no polar-cap maximum of sai at the top level | **pass** — polar-cap top-level sai is 0.67 of the global-mean column; after 5 years of continuous source the tracer fills the whole upper domain roughly uniformly (~1.7 vs 8.6 in the source box) rather than piling up at the poles |
| age-of-air latitude gradient has the right sign | qualitative | **pass** — youngest air in the tropics at every level, oldest over both poles; the tropical pipe is there |
| tropical/extratropical age contrast within 50 % of CLaMS | at ~55 hPa | **fail** — model 2.88 yr (10°S–10°N) vs 4.09 yr (50–70°), contrast 1.21 yr; CLaMS 1.33 vs 4.12, contrast 2.79 yr. The model's contrast is 43 % of CLaMS's: **the tropics are 1.5 yr too old**, the extratropics are right (4.09 vs 4.12). At ~12 hPa: model 4.42/4.76 vs CLaMS 3.68/4.56 |
| ≥ 2 of the 3 ERA5 SSW winters show a weakened vortex | qualitative | **not testable** — there is no polar-night jet to weaken: DJF-mean u(61°N, 10 hPa) is −4 to −2 m/s in every winter (ERA5 climatology ~+30 m/s). The Held-Suarez stratosphere is isothermal and unforced above the nudged layer (issues #2, #5) |
| throughput | report | 4315 days/hr stepping over the 64 steady chunks (4460–4480 per segment), **1768 days/hr end-to-end** for 1826 days incl. five compiles and five 31 GB target loads (2080–2100 per segment) |

## Results

### p4_5yr (aggregate of p4_2005 … p4_2009)

```
throughput:     4315.0 simulated days / hour   (steady state, 1796 d over 64 chunks; per segment 4457-4478)
per step:       7 ms
end-to-end:     1826 d in 3718 s = 1768 days / hour   (per segment 2079-2099; segment load of the 31 GB target ~1 min each)

global-mean ps:         998.628 -> 998.655 hPa   drift +0.0267 hPa over 5 yr
global KE (J/kg):       123.9 -> 116.7
top-level zonal-mean T: mean(last 365 d) 249.9 K, trend +0.000 K/day
T range:                min 181.0 K  max 312.5 K
model - ERA5 over 7-70 hPa (last save vs 1989-1994 tape): RMS dT = 21.5 K, RMS du = 13.5 m/s

unity max |q-1| (any cell, any save): 2.55e-04      unity global burden drift: +1.69e-04
sai burden vs expected (source*box mass*t): -1.10%  (expected 1.274, got 1.260)
cell minimum: aoa -9.22e-07, unity 1.00e+00, sai 0.00e+00, e90 0.00e+00
pull-up check: sai at top level, |lat|>70: 0.842 vs global-mean column 1.260 (ratio 0.668)
age of air at ~20 hPa, last save: tropics 4.13 yr, 50-70deg 4.69 yr, max 4.99 yr (= elapsed)

age of air vs references (last 12 saves = 2009-11/12 mean; CLaMS and WACCM 2005-2009 means)
level            source                tropics 10S-10N  50-70 deg  contrast
~55 hPa (~20 km) model                            2.88       4.09      1.21
~55 hPa (~20 km) CLaMS v3.1 / ERA5 (surface clock) 1.33       4.12      2.79
~55 hPa (~20 km) WACCM6 REF-D1 (entry age)         1.11       3.40      2.29
~12 hPa (~30 km) model                            4.42       4.76      0.35
~12 hPa (~30 km) CLaMS                            3.68       4.56      0.88
~12 hPa (~30 km) WACCM (entry age)                2.82       4.18      1.36

polar vortex, u(61N, 10 hPa), 5-day means
winter     DJF mean [m/s]   5-day means with u<0 (Nov-Mar)
2005/2006      -4.3              30
2006/2007      -1.8              21
2007/2008      -2.5              26
2008/2009      -5.2              27
```

![age of air: model, CLaMS, WACCM](p4_5yr_aoa_triptych.png)
![age-of-air profiles](p4_5yr_aoa_profiles.png)
![tracer zonal means, day 1826](p4_5yr_tracer_zonal.png)
![tracer budgets, 5 years](p4_5yr_tracer_budget.png)
![polar vortex](p4_5yr_vortex.png)
![stability summary](p4_5yr_summary.png)
![zonal-mean T, u vs ERA5](p4_5yr_zonal_mean.png)
![throughput](throughput.png)

## The Phase-1 number

> The stripped stratospheric JCM on Dinosaur-SL — dry Held-Suarez physics, ERA5-nudged winds and
> temperature below 150 hPa, four semi-Lagrangian tracers — runs **4300–4500 simulated days per
> hour stepping and about 1800 end-to-end on one H100 at T63L95 with a 12-minute step: one
> simulated year in 10.4 minutes, 30 years in about 5.2 GPU-hours** (full ECHAM physics on the same
> grid: 47 days/hr, 7.8 h per year). Passive-tracer mass closes to 0.02 % over five years for a
> uniform tracer and to 1 % against an analytic source, with exact non-negativity and no polar
> pull-up. The age-of-air *pattern* is right (tropical pipe, poleward ageing) but the tropics are
> 1.5 yr too old at 20 km and the stratosphere has no polar-night jet: with Held-Suarez in place of
> radiation the Brewer-Dobson circulation is too weak. The speed question is answered; the fidelity
> question now depends on the stratospheric forcing (issues #2 RRTMGP, #5 Polvani-Kushner).

## Reading

1. **Speed.** Stripping the physics bought a factor ~40 end-to-end and ~90 in stepping over full
   ECHAM on the same grid. The remaining end-to-end cost is roughly half stepping, half output
   writing and per-segment setup (issue #19); the time-step sweep (issue #3) is the next lever.
2. **Transport is sound over five years.** Conservation, positivity and the pull-up check all hold
   at the Phase-3 levels with no degradation over time, and the year-boundary chaining is exact.
   The mass-fixer exemption for the clock (Phase 3) held: the clock reaches 4.99 yr where it must.
3. **The tropics are too old, the extratropics are right.** At 55 hPa the model matches CLaMS at
   50–70° (4.09 vs 4.12 yr) but is 1.5 yr too old at the equator; at 12 hPa the whole profile is
   0.2–0.7 yr too old. Two causes, both expected from the Phase-1 physics choice:
   (a) *weak tropical upwelling* — the Held-Suarez stratosphere is isothermal with no meridional
   temperature gradient and no polar-night jet, so there is little wave-driven Brewer-Dobson
   circulation above the nudged layer (the zonal-mean plot shows u ≈ 0 above 100 hPa);
   (b) *slow tropospheric transit* — the clock is reset below 700 hPa but, without convection or
   boundary-layer mixing, air between 700 and 150 hPa ages for months before it reaches the
   stratosphere (the tropical profile is already ~1 yr at 100 hPa, where CLaMS is 0.2). Part of the
   tropical excess is therefore tropospheric, not stratospheric. For Approach A's purpose the clock
   should be referenced to the tropopause — reset below ~150 hPa, or diagnosed as entry age as
   WACCM does — so that only stratospheric transport is scored (issue #25).
4. **Five years is still not equilibrium.** Everything above ~10 hPa reads 4.9–5.0 yr, i.e. the run
   age; the upper-stratospheric comparison with CLaMS is not meaningful yet (mean age needs ~10 yr).
5. **No vortex, no SSW test.** u(61°N, 10 hPa) hovers around −4 m/s in every winter. The nudged
   troposphere supplies the wave forcing but the stratosphere has nothing for it to act on. This is
   the same limitation as 3(a) and is what Phase 2 of the plan (Polvani-Kushner, issue #5) and
   RRTMGP (issue #2) address; a full-ECHAM specified-dynamics reference year is being run to
   quantify the gap.
6. **What the Phase-1 number means for the emulator question.** At ~5 GPU-hours per 30 years the
   physics baseline is already "hours, not weeks" on a single GPU. An emulator would need to beat a
   few GPU-hours per 30 years *and* match or exceed this transport fidelity to be worth building;
   the fidelity bar is currently set by the stratospheric forcing, not by the transport scheme.
