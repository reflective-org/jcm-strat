# Phase 10 — production tracer set and 6-hourly output: the 2005–2009 review run

Status: **review chain complete, renamed `p10rev_*` on 2026-09-12 so the production chain (`p10_1990..2019`) does not skip 2005-2009 as already done; (five calendar years, strat63, QBO tau 1 d); tracer diagnostics in
progress; one defect found (the N2O-like tracers exceed 1 under the global mass fixer, see
Results) — a rerun with those two tracers exempt from the fixer is proposed before the 30-year
production run.** Branch `phase10-production` (off `phase9-resolution` at 042f234), worktree
`/data/JCM_stripped/jcm-strat-phase10`. Chain 2026-09-10 23:52 to 2026-09-11 02:11 UTC on GPU 0
(2.3 h; 16:52–19:11 PDT).

## Why

The runs so far were validation runs: 5-day means of a handful of diagnostic tracers. The end use
of this model is training data for an ML transport model, which needs (a) tracers that carry
diverse, known spatial structure and a wide range of concentrations without mixing out over
decades, (b) instantaneous fields at the emulator's step (6 h) including the vertical velocity,
and (c) a long record. Susanne's decisions (2026-09-10): run 2005–2009 first with the new tracer
set and output, review the tracers, then run 1990–2019.

## Configuration (`+experiment=p10_prod`, commit d9917c4)

Everything is Phase 8b on the strat63 grid Phase 9 recommended (`p9_l63`, KEY_DECISIONS #31)
except:

| item | Phases 3–9 | Phase 10 | why |
|---|---|---|---|
| QBO relaxation time | 10 d | **1 d** (pinned in the experiment) | Phase 8d/8e sweep; the QBO branch made 1 d its default in 1551065, after this branch was cut |
| calendar | JCM default `365_day` | **gregorian** | under `365_day` the fraction of year is (days since 1970 mod 365)/365: 9 days ahead of the true date in 2005, 12 in 2019, so the Polvani-Kushner season and the QBO month ran early in Phases 6–9 |
| output | 5-day means, 30-day chunks | **instantaneous every 6 h**, 10-day chunks (40 frames ≈ 3.5 GB on the GPU) | emulator step; the chunk's frames sit on the GPU until written |
| omega | not written | **written** (`OmegaDiagnostic`; lags u, v, T by one 12-min step in snapshot mode) | vertical advection |
| geopotential | written | written (dropped in the 2005-2009 review run, restored for production at Susanne's request) | `output_drop` in jcm_strat.main can drop any variable |
| tracers | aoa, unity, sai, e90 (`PassiveTracers`) | **`ProductionTracers`** below; unity and e90 gone | see below |
| mass fixer | all but aoa | all but aoa, aoa150, aoa_sfc | clocks are not conserved (KEY_DECISIONS #19) |
| segments | 365 d per year | true calendar years (2008 = 366 d) | 6-hourly saves divide any year |
| compression | none | zlib-1 + shuffle after each segment, in the background (`scripts/compact_run.py`) | 108.6 → 73–79 GB per year, off the GPU's critical path |

### The tracer set (`jcm_strat/advection_tracers.py`)

| tracer | initial | tendency | fixer |
|---|---|---|---|
| `aoa` | 0 | clock, reset below 700 hPa (as before) | excluded |
| `aoa150` | 0 | clock, reset below 150 hPa: stratospheric entry age (KEY_DECISIONS #22) | excluded |
| `aoa_sfc` | 0 | clock, reset in the lowest two layers: the CLaMS/WACCM surface boundary condition | excluded |
| `sai` | 0 | 1e-6 s⁻¹ in 15S–15N, 25–55 hPa (as before) | on |
| `pulse_1..5` | 0 | **injected** on 1 Jan, ~2 Apr, ~2 Jul, ~1 Oct (set to a Gaussian blob, σ 12° great-circle × 0.25 decades of pressure); between injections **absorbed in the lowest two layers**, no other source or sink | on |
| `n2o`, `cfc11` | WACCM January zonal mean, normalised to 1 at the surface | held at 1 below 700 hPa; loss `−k(lat, p) q` with WACCM's zonal-mean loss-frequency climatology (CCMI-REFD2 `N2O_CHML`, `CFC11_CHML` / vmr / n_air, 2015–2024 mean; `jcm_strat/data/waccm_tracer_ref.nc`) | on (**the defect**) |

Pulse centres and amplitudes: (0°, 0°E, 30 hPa, 1.0), (45°N, 120°E, 70 hPa, 0.5), (60°S, 240°E,
10 hPa, 0.2), (30°N, 300°E, 3 hPa, 0.1), (15°S, 60°E, 300 hPa, 0.05). The N2O-like tracers have
WACCM lifetimes of 9.4 yr at 30 hPa and 0.9 yr at 10 hPa (N2O), 0.6 yr at 30 hPa (CFC-11); ERA5
and CAMS have no N2O, so WACCM is the only source of an initial state on this machine.

## Runs

| run | dates | days | wall | stepping | e2e | output raw → compressed |
|---|---|---|---|---|---|---|
| `p10_smoke5` | 2005-01-01 | 5 | 1 min | — | — | 1.5 GB (one 5-day file, 20 frames) |
| `p10_smoke30` | 2005-01-01 | 30 | 4 min | — | — | 8.5 GB |
| `p10rev_20050101` | 2005 | 365 | 25 min | 4718 d/hr, 6 ms/step | 880 d/hr | 108.6 → 73.2 GB |
| `p10rev_20060101` | 2006 | 365 | 25 min | 4723 | 881 | 108.6 → 77.0 |
| `p10rev_20070101` | 2007 | 365 | 26 min | 4805 | 836 | 108.6 → 78.1 |
| `p10rev_20080101` | 2008 | 366 | 26 min | 4748 | 834 | 108.9 → 78.6 |
| `p10rev_20090101` | 2009 | 365 | 26 min | 4787 | 853 | 108.6 → 78.4 |
| `p10rev_5yr` | aggregate | 1826 | 2 h 20 min | | | 385 GB, 185 files × 40 frames, 17 variables |

Stepping is 12 % slower than Phase 9's strat63 (5374 d/hr): eleven nodal tracers instead of four
plus the omega diagnostic. End-to-end is now **output-bound**: 13 s of stepping per 10-day chunk
against ~30 s of conversion and writing of 3 GB (issue #19), 26 min per year instead of 12. A
30-year run at this setting is ~13 h of GPU 0 and ~2.3 TB compressed. Unit tests: 36 passed
(`runs/p10_tests.log`).

## Acceptance

| check | threshold | result |
|---|---|---|
| segments finish, no NaN | all five, 0 NaN variables | **pass** (5/5, 0/17 in every health check) |
| output content | u, v, T, q, omega, p_s + 11 tracers, 40 frames per 10-day file, 6 h apart | **pass** |
| pulses | max ≤ 1.01 × amplitude, min ≥ −1e-6; injections on schedule; mass falls only through the surface | max ≤ amplitude, min −3e-10 (roundoff); schedule and decay: see diagnostics |
| clocks | aoa150 ≤ aoa ≤ aoa_sfc in > 99 % of cells | **pass** (100 % / 99.3 % at day 5; last frame 2009: means 3.6 / 3.1 / 3.7 yr) |
| n2o, cfc11 | in [0, 1 + 1e-4]; drift small | **FAIL**: max 1.07 (see Results) |
| omega | level-mean ≪ rms | **pass** (max ratio 0.009) |
| throughput | stepping ≥ 3000 d/hr | **pass** (4720–4800) |

## Results

### The N2O-like tracers exceed 1 under the global mass fixer

`n2o` and `cfc11` should never exceed 1 (their source holds them at 1, the sink only removes).
Both develop values above 1 in the tropical upper troposphere and lower stratosphere
(60–190 hPa), growing from 1.006 at day 10 to 1.035 at day 100, 1.05 after one year and 1.07 by
2009, while the troposphere below 700 hPa stays at 1.000 ± 0.002. This is KEY_DECISIONS #19
again: the fixer rescales the whole field by one global factor per step so that its mass matches
the post-physics mass. A tracer with a fixed boundary value is not a conserved quantity — the
physics re-imposes 1 below 700 hPa every step, so the fixer's per-step factor (~1 + 1e-6, the
semi-Lagrangian mass error) is applied afresh to air that already sits at 1 above the source
region and is never reset there. Over the months such air spends in the tropical upper
troposphere the factor compounds to several percent. The pulses, which have no source, and the
clocks, which are already exempt, do not show it. **Fix: add `n2o` and `cfc11` to
`sl_mass_fixer_exclude`** (as for the clocks); the SL scheme's own mass error for them is then the
few 1e-4 per year that `unity` measured in Phases 4–9, three orders of magnitude below the artefact.

### Tracer diagnostics of the review run (`runs/p10rev_5yr`, figures `p10rev_5yr_*.png` here)

- **Pulses.** Each injection reproduces its analytic blob to 0.4–1.5 % RMSE of the amplitude (the
  grid's rendering of a 12° × 0.25-decade Gaussian). The tropical 30 hPa blob is sheared into a
  zonal band within 5 days, reaches 40°N in filaments by day 20, and after 60 days is a tropical band
  at 3 % of its peak with spirals into both hemispheres (`p10rev_5yr_pulse_evolution.png`); vertically
  it stays within 20–50 hPa. Global burdens are flat between injections for the four stratospheric
  pulses (nothing but transport; the sub-1e-3 wiggles are the moving air-mass weighting) and fall
  within weeks for the 300 hPa pulse, which reaches the absorbing layers. Cell minima −1.7e-9 or
  better, maxima never above the amplitude.
- **Steady tracers.** Global burdens settle in ~250 days (n2o 0.968 → 0.956, cfc11 0.943 → 0.922)
  and then hold; the stratospheric contours sit below WACCM's January state, i.e. this model's
  tropical ascent is slower (the same direction as its old age of air). The defect: values up to
  1.07 in the tropics below ~60 hPa from the mass fixer, see above; fixed for production.
- **Clocks.** aoa150 ≤ aoa in 100 % of cells, aoa ≤ aoa_sfc in 99.7 %; at 20 hPa after 5 years the
  tropical / 50–70° ages read 3.05 / 4.30 yr (aoa), 2.29 / 3.94 (aoa150), 3.13 / 4.33 (aoa_sfc): the
  entry age is 0.4–0.8 yr younger than the 700 hPa clock, the surface clock 0.05 yr older. None is
  converged at 5 years (issue #44), as expected.
- **sai** burden −1.7 % against the analytic source line (threshold 2 %, pass; Phase 9 read −4 to
  +3.6 % on this grid family). **omega**: level means ≤ 0.6 % of the rms; rms 2.5e-3 Pa/s at 30 hPa.
- **Throughput**: 4720–4800 simulated days/hr stepping, 6 ms/step; end-to-end 830–880 d/hr, i.e.
  output-bound.

## Review and the production design (2026-09-11)

Susanne reviewed the quick-look figures and approved the 30-year run with these changes:

| item | 2005–2009 review run | 1990–2019 production run |
|---|---|---|
| pulses | re-injected quarterly | **injected once**, at the first step of 1990-01-01, then pure advection + surface absorption ("one injection at t0 and see how it gets advected") |
| continuous sources | none (only `sai`) | **`src_1..4`**: Gaussian sources every step, A·G/90 d, surface absorption — 0°/180°E/20 hPa (1.0), 30°N/60°E/100 hPa (0.5), 60°S/300°E/5 hPa (0.2), **30°S/240°E/55 hPa (0.3, her request)** |
| n2o, cfc11 | under the mass fixer (→ 1.07 artefact) | **exempt** (`sl_mass_fixer_exclude`), see below |
| QBO target | tau 1 d, linear monthly interpolation | tau 1 d, **mean-preserving** monthly nodes (QBO branch head merged, KEY_DECISIONS #32) |

**Why the N2O-like tracers leave the fixer** (her question). The fixer restores the global mass a
tracer had after the physics by one multiplicative factor per step. That is right for a tracer whose
physics adds or removes *mass* (the pulses' absorption, the sources' emission, `sai`) — the target
then already contains the physics. It is wrong for a tracer whose physics imposes a *value*: `n2o`
is set to 1 below 700 hPa each step, so every step's factor (1 + ε, ε ≈ 1e-6 the SL mass error) is
re-applied to air that already sits at 1 above 700 hPa, and compounds over the months such air spends
in the tropical upper troposphere — 1.07 after two years in `p10rev_5yr`. The clocks were exempted for
the same reason in Phase 3 (KEY_DECISIONS #19). Without the fixer the tracer's mass error is the SL
scheme's own, which `unity` measured at a few 1e-4 per year in Phases 4–9: three orders of magnitude
smaller than the artefact, and irrelevant for a field whose value is pinned at its source. Exempt.

The 30-year chain is `scripts/phase10_run30.sh` (tmux `strat_p10_30yr`): waits for the ERA5 prefetch
(four CPU streams) and the CDS QBO target 1989–2020, runs a 5-day smoke, then
`chain_segments.sh` with `YEARS=1990-2019 AGG=p10_30yr`. Output: `runs/p10_<YYYY>0101/` per year
(37 files × 40 frames, ~130 GB raw → ~90 GB compressed), aggregate `runs/p10_30yr/` (symlinks with
cumulative day numbers). Expected ~30 min per year → ~15 h.

## Pulse and source evolution, 1990–2019 (`scripts/pulse_evolution.py`, 2026-09-14)

One figure per tracer in the layout of `p10_30yr_pulse_evolution.png` (map at the tracer's own
injection level, zonal mean below, injection site marked): `p10_30yr_pulse_<i>_evolution.png` at
0, 5, 20, 60, 180 and 365 days after the single injection, `p10_30yr_src_<i>_evolution.png` at
5, 20, 60, 180, 365 and 1825 days of continuous emission. Animations over the first year (daily to
day 60, then every 3 d to 180, every 10 d to 365; log colour scale fixed at four decades below the
tracer's largest value): `p10_30yr_<tracer>_evolution.gif`, and all nine maps together in
`p10_30yr_tracers_evolution.gif`.

```
python scripts/pulse_evolution.py runs/p10_30yr docs/outputs/10_production --label "P10 1990-2019 (strat63, tau 1 d)"
```

What the panels show (instantaneous fields, peak values in the colour bars):

- **pulse_1** (0°, 30 hPa, 1.0): sheared into a zonal band within 5 d, filaments to 60°N by day 20,
  a tropical band at 3 % of the amplitude after 60 d, a nearly zonal tropical maximum at 2.5e-3 after
  180 d and 2e-4 after a year; vertically it stays in the 10–100 hPa layer for the first two months
  and has spread from 300 to 1 hPa after a year.
- **pulse_2** (45°N, 70 hPa, 0.5): torn apart by the winter vortex edge within 5 d, fills the
  northern extratropics by day 60 (5e-3) and is hemispherically uniform, 4e-4, after 180 d; a
  sharp gradient at the subtropical edge persists all year, with the southern hemisphere at
  a tenth of the north. Vertically it drains downwards past 200 hPa within 6 months.
- **pulse_3** (60°S, 10 hPa, 0.2): the summer polar stratosphere; the blob circles the pole once in
  5 d, is zonal by day 20 and stays confined to the southern extratropics for the whole year
  (2.5e-5 after 365 d) while descending from 10 to 100 hPa: the smallest horizontal spread of the
  five and the clearest downward branch.
- **pulse_4** (30°N, 3 hPa, 0.1): rolled up by the planetary-wave breaking of the upper stratosphere
  (a closed vortex at day 5), spread across the whole northern hemisphere by day 60 (2e-3) and, after
  a year, descended to a maximum near 30 hPa with the tropics still an order of magnitude lower.
- **pulse_5** (15°S, 300 hPa, 0.05): the tropospheric pulse is stretched into filaments within 5 d,
  covers 40°S–40°N by day 20 at a tenth of its amplitude and fills the whole troposphere by day 60;
  a tail leaks into the tropical lower stratosphere and after a year the maximum of what is left
  (1e-5) sits at 50–100 hPa: the troposphere has drained to the surface while the stratosphere holds.
- **src_1** (0°, 20 hPa, 1.0): a tropical plume that saturates in about six months (zonal-mean peak
  0.054 at 180 d, 0.056 at 5 yr) and stays within 30°S–30°N at the injection level; the filaments to
  the extratropics are at a few percent of the core.
- **src_2** (30°N, 100 hPa, 0.5): sheared along the subtropical jet, its plume fills the northern
  lower stratosphere and upper troposphere; the equilibrium peak (0.012–0.013) is reached after a
  year, the southern hemisphere stays clean.
- **src_3** (60°S, 5 hPa, 0.2): polar summer at the start, so the plume circles the pole; by day 180
  (austral winter) the vortex confines it to 60–90°S at 0.02 and only after a year does the plume
  reach 40°S. Equilibrium peak 0.014.
- **src_4** (30°S, 55 hPa, 0.3, Susanne's site): the southern subtropical plume mixes into the
  southern hemisphere within 60 d and reaches equilibrium (0.011) in about a year; its northern edge
  sits at the equator.

All four sources are near their equilibrium burden after a year (`p10_30yr_pulse_metrics.md`:
src_1–3 flat, src_4 still rising slowly at the end); the five pulses are the transient signal, a
homogeneous background within one hemisphere after 6–12 months.

**Vertical structure** (`p10_30yr_<tracer>_vertical.png`, `p10_30yr_tracers_vertical.png`; first
730 days, every 5 days, `--stages vertical`). Each tracer's figure shows time–pressure sections of
the mass-weighted global mean and of the zonal mean within 10° of the injection latitude, the
mass-centroid pressure (mass-weighted mean of log10 p) overlaid, and line profiles of the band mean
at 0, 5, 20, 60, 180, 365 and 730 days. The summary figure has the centroid and the vertical spread
(mass-weighted std of log10 p) of all nine. Because the weights are layer mass, a blob centred at
p0 in mixing ratio has its centroid below p0 from the start (30 hPa → 45 hPa for pulse_1).

- Every stratospheric pulse's centroid **descends and converges to 160–180 hPa within 1–2 years**
  (pulse_1 from 45 hPa in ~300 d, pulse_2 from 100 hPa in ~50 d, pulse_3 from 13 hPa in ~250 d,
  pulse_4 from 3 hPa in ~500 d): the mass that is left sits in the lowermost stratosphere and upper
  troposphere while the surface sink drains what reaches the troposphere. The tropospheric pulse_5
  moves the other way, from 300 to 170 hPa, as its tropospheric part is removed and the lower-
  stratospheric tail is what remains after a year.
- Vertical spread grows from the injected 0.25 decades to 0.45–0.5 decades for the stratospheric
  pulses within 100–200 days and then stays; pulse_4 (3 hPa) spreads most (0.67 decades at 250 d)
  because it descends through the whole stratosphere.
- The sources reach a fixed profile: src_1 (20 hPa) has its centroid at 65 hPa and a plume spanning
  1–200 hPa after a year; src_2 (100 hPa) and src_4 (55 hPa) settle at 200 and 170 hPa within 100 d
  with the smallest spread (0.3–0.4 decades). **src_3 (60°S, 5 hPa) shows a clear annual cycle**:
  its centroid sinks from 20 to 55 hPa during austral winter (day ~250 and ~600) and rises back to
  25 hPa in austral summer (day ~450), i.e. the polar vortex descent and its summer breakdown are in
  the tracer, with the spread swinging between 0.6 and 0.7 decades in step.
- The profiles of pulse_1 and pulse_3 at 365 and 730 days show the blob reaching the 1 hPa level at
  1e-3 to 1e-4 of the amplitude: the tropical upwelling branch carries the tropical pulse up as the
  bulk descends, the polar pulse_3 has no such tail.

**Total global tracer mass** (`p10_30yr_tracer_mass.png`, numbers in `p10_30yr_tracer_mass.md`;
`--stages mass`, every 10 d for two years then every 30 d, 414 frames, series cached in
`runs/p10_30yr/tracer_mass.npz`). Mass = mixing ratio × layer air mass summed over the globe
(4πa²/g · Σ q Δp w), in kg; the dry-air total comes out at 5.19e18 kg, as it should. The GIFs and
panels above show mixing ratio, not mass.

| tracer | injected / emitted | half-life | e-folding | left after 1 yr |
|---|---|---|---|---|
| pulse_1 (30 hPa) | 5.7e15 kg | 120 d | 150 d | 3.9 % |
| pulse_2 (70 hPa) | 6.5e15 kg | 50 d | 70 d | 0.7 % |
| pulse_3 (10 hPa) | 3.8e14 kg | 210 d | 240 d | 7.1 % |
| pulse_4 (3 hPa) | 5.7e13 kg | 280 d | 320 d | 22 % |
| pulse_5 (300 hPa) | 2.5e15 kg | 60 d | 90 d | 0.8 % |
| src_1 (20 hPa) | 4.3e13 kg/d | | residence 0.49 yr | equilibrium 7.7e15 kg |
| src_2 (100 hPa) | 1.0e14 kg/d | | residence 0.24 yr | 7.7–9.3e15 kg |
| src_3 (5 hPa) | 2.2e12 kg/d | | residence 0.44 yr | 3.5–3.8e14 kg |
| src_4 (55 hPa) | 3.6e13 kg/d | | residence 0.26 yr | 3.4–3.7e15 kg |

- **The pulses are gone within 2–3 years**: below 1e-4 of the injected mass after 2.5 yr, 1e-8 to
  1e-10 after 5 yr, and at 1e-32 to 1e-34 (float32 roundoff, still positive) after 30 years. The decay
  is exponential after the first 100–200 days, with an e-folding time that increases with height:
  70 d at 70 hPa, 150 d at 30 hPa, 240 d at 10 hPa, 320 d at 3 hPa. Two time scales are in this:
  the time the air needs to reach the tropopause, and **tropospheric removal, which in this model is
  itself slow, ~75 d**. The only sink is relaxation to zero in the two lowest layers, and the dry
  model has no convection or boundary-layer mixing, so tracer reaches those layers by the resolved
  (ERA5-nudged) circulation alone. Splitting pulse_5's mass at 150 hPa shows it: 96 % of the
  300 hPa pulse is tropospheric at t0, and that tropospheric part alone falls to 41 % after 60 d and
  26 % after 90 d; the 4–8 % above 150 hPa decays in step with it, so it is not a lingering tail.
  From day 180 on every pulse decays at the same ~75–80 d e-folding, the tropospheric removal
  rate; pulse_2 (70 hPa, 45°N, injected in NH winter) falls faster at first only because it starts
  with 23 % of its mass below 150 hPa and the winter lowermost stratosphere flushes into the
  troposphere within two months (77 % → 11 % above 150 hPa by day 60). A real troposphere removes a
  300 hPa tracer to the boundary layer in days to a couple of weeks; the model's 75 d is a property
  of the stripped physics, not of the atmosphere, and it lengthens every pulse's lifetime by the same
  amount. So the once-injected pulses carry signal for the first two years of the archive and are
  exactly zero for the other 28 (their fields still cost 5 × 186 MB per 10-day file; see the question
  below).
- **The sources reach equilibrium within a year** and then hold a stratospheric mass of
  residence time × emission, with the residence time 0.24–0.49 yr: shortest for the 100 hPa and
  55 hPa sources, longest for the 20 hPa and 5 hPa ones. All four show an **annual cycle** of
  ±10–20 % in mass (strongest for src_3, the polar one): the seasonal Brewer-Dobson circulation
  modulates how fast the plume reaches the troposphere. The cumulative-emission lines (dotted) show
  that after 30 years 98–99 % of what was emitted has been absorbed at the surface.
- **n2o and cfc11 lose 11–12 % / 13–14 % of their WACCM initial mass in the first two years** and
  then hold a stationary level with an annual cycle of ±0.5 %: the model's stratospheric loss
  (the WACCM CHML rates) is stronger than the WACCM state implies for this circulation, or the tropical
  ascent that carries fresh tracer up is slower (the same direction as the old age of air, KEY_DECISIONS
  #35). Below 700 hPa they are pinned at 1, so all of the lost mass is stratospheric, consistent
  with the zonal means sitting below the WACCM contours in `p10_30yr_steady_clocks.png`. Which of
  the two causes dominates is not settled here.
- **sai** (box source, no sink) grows to 3.9e19 kg in 30 years, 0.8 % of the atmosphere's mass; its
  growth rate is the analytic source to within the 2 % threshold (`p10_30yr_pulse_metrics.md`).

## Linearity check: the pulse amplitude only scales the field (2026-09-15)

Susanne asked whether advection depends on the concentration, i.e. whether the five amplitudes
(1.0, 0.5, 0.2, 0.1, 0.05) probe anything beyond a scale factor. In this model they cannot: the
tracers are passive, the winds are prescribed (dry Held-Suarez + ERA5 nudging), and every operator
on q — semi-Lagrangian interpolation, the quasi-monotone limiter, the mass fixer, the surface
relaxation — is homogeneous of degree one. Checked by running p10_prod for 5 days from 2005-01-01
twice, once with the default pulses and once with pulse_1's amplitude set to 2.0 (`runs/lin_a1`,
`runs/lin_a2`, `runs/lin_check.sh`; CPU, ~10 min each):

- pulse_1: the doubled run equals exactly 2 × the reference in 94 % of the cells in float32 and
  differs by < 1e-18 (denormal roundoff near zero) in the rest, at every one of the 20 frames; peak
  ratio 2.0000000, global-mass ratio 2.0000000.
- pulse_2, src_1, u, T: bit-identical between the two runs — the tracer does not touch the flow.

So the amplitude sets the initial mixing ratio and nothing else; the transport pattern, timing and
lifetimes are amplitude-independent. Concentration-dependent transport (self-lofting by aerosol
heating, size-dependent settling after coagulation) requires a model in which the tracer acts on
the dynamics or has nonlinear microphysics — the coupled TOMAS/CESM model or an emulated dycore
closing the loop — and is outside Approach A by construction. The amplitude variety in the archive
is useful only as a linearity / normalisation test for a learned transport operator.

## Questions that came up, and my answers

*(kept while the run proceeds; Susanne reviews once the 30 years are done)*

- **Should the pulses keep the surface sink now that they are injected once?** Yes: without it a
  pulse ends as a uniform constant that never leaves, and the ML model would see a field with no
  gradients but non-zero mass; with it the field drains to zero on the transport time scale to the
  surface (years), which is itself a transport signal.
- **Do the once-only pulses become useless after a few years?** After 1–3 years each is a nearly
  homogeneous, slowly draining background (the 5-year run shows the 30 hPa blob at 3 % of its peak
  after 60 days and zonally uniform). They still cost a field each in the output; if that matters for
  the 30-year archive they can be dropped from the netCDF after the fact — nothing else depends on
  them. The continuous sources carry the long-term gradients.
- **Is 90 days the right source time scale?** Only the amplitude depends on it (the equilibrium
  burden scales as A × residence time / 90 d); the *shape* of the plume does not. Any value is fine
  for a model that normalises its inputs; 90 d keeps the equilibrium mixing ratios O(1e-2–1e-1),
  well inside float32.
- **Why are the first years' clocks unusable?** A clock cannot read older than the run (issue #44):
  the three age tracers are converged only after ~6–8 years of the 30. Analyses of age should use
  1998 onward; the ML training set can use every year since it learns the local transport, not the
  absolute age.

## Age of air after 30 years: the mesosphere is never ventilated (`scripts/aoa_vs_clams.py`, 2026-09-15)

Susanne asked which figure compares age of air with CLaMS; none existed for this run, so it was made:
`p10_30yr_2009_aoa_{triptych,profiles}.png` (the chain at the end of 2009, last 60 days, against
CLaMS/WACCM 2005–2009 — the window Phases 4–9 used) and `p10_30yr_aoa_{triptych,profiles}.png` (the 2019
annual mean against 2015–2019). **The clock never equilibrates.** Surface-clock mean age in years:

| level, band | end 2009 | 2019 | CLaMS |
|---|---|---|---|
| 55 hPa, tropics | 4.9 | 6.5 | 1.3 |
| 55 hPa, 50–70° | 10.8 | 13.7 | 4.2 |
| 12 hPa, tropics | 10.4 | 13.0 | 3.7 |
| 12 hPa, 50–70° | 13.6 | 18.4 | 4.7 |

Sampled at every second year end, the age grows almost linearly: 0.2 yr per year at 55 hPa in the tropics,
0.5 yr per year at 12 hPa. In the last frame the age above ~1 hPa is 22–23 yr **and uniform in latitude**
(tropics 23.2, poles 23.2 at 0.02 hPa; the oldest cell, 23.3 yr, is at the model top): the mesosphere has
not been flushed once in 30 years, and the smooth fall-off below it is the profile of a stagnant lid
leaking down by mixing, not of an overturning cell. This is **not a weak Brewer–Dobson circulation**
(Susanne's objection, correct): the tropical upward mass flux at 100 / 70 / 30 / 10 hPa is 11.1 / 8.2 /
3.7 / 1.35 × 10⁹ kg/s against WACCM6's 10.8 / 6.1 / 3.1 / 1.39 (`09_resolution/strat/strat_metrics.md`),
and 1.35 × 10⁹ kg/s through 10 hPa would replace the air above it in ~1.2 yr. The stratospheric cell is as
strong as WACCM's but closes below the mesosphere, which has no drag to drive a circulation (gravity-wave
drag was dropped in Phase 1, issue #20; the Rayleigh sponge holds the top four levels above 0.2 hPa; the
semi-Lagrangian top is a no-flux cap). Mean age is a mass-weighted average over all transit paths, so a
correct w* and a very old mean age coexist once the old-air tail exists.

Consequences. (1) The Phase 9 statement "0.8 yr too old at 55 hPa" was a spin-up artefact — a 5-year clock
cannot exceed 5 yr, and the 1994 value of this chain (2.2 yr) matches the 5-year chains. The answer above,
"converged after ~6–8 years", is wrong: the clocks never converge in this configuration. (2) The N2O and
CFC-11 depletion (isopleths ~6 km below WACCM's, half-value surface at 21 hPa vs 8 hPa in the tropics) has
the same cause: air that has been to the mesosphere returns N2O-free and is recirculated into the pipe and
the lowermost stratosphere (0.43 vs 0.85 at 100 hPa, 50–70°, where the lifetime is centuries). CFC-11 in
the tropical pipe above 30 hPa, where its lifetime is months and the field is set locally by ascent against
loss, matches WACCM (0.18 vs 0.20 at 20 hPa) — the fingerprint of recirculated old air rather than slow
ascent. The implied N2O emission (stratospheric loss at steady state) is 0.39 % of the atmosphere per year,
i.e. a whole-atmosphere lifetime of ~256 yr against the accepted ~120: the loss is supply-limited because
the pipe is diluted with depleted air. **Phase 11** (branch `phase11-lid-tracers`, `11_lid_tracers/output.md`)
prescribes the tracers above 1 hPa (relaxation to WACCM's mesospheric age and state) and re-runs; the
dynamical fix is deferred.
