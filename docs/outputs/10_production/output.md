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

### Tracer diagnostics

Figures and numbers from `scripts/pulse_diagnostics.py` and `scripts/tracer_budget.py` on
`runs/p10rev_5yr` are written into this directory (`p10rev_5yr_pulse_burdens.png`,
`p10rev_5yr_pulse_evolution.png`, `p10rev_5yr_steady_clocks.png`, `p10rev_5yr_omega.png`,
`p10rev_5yr_pulse_metrics.md`, `p10rev_5yr_tracer_budget.png`, `p10rev_5yr_tracer_zonal.png`); a coarser
quick look (every 50 days) is in `quicklook/`. *[to be filled from the finished diagnostics]*

## Reading

*[to be written after the diagnostics: pulse dispersal time scales per injection site, steady
tracer equilibration, clock ordering and the entry-age vs surface-age difference, omega]*

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
