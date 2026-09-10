# Phase 9 — resolution sensitivity: what horizontal and vertical resolution do to stratospheric transport

Status: **in progress** (2026-09-09). Branch `phase9-resolution` (off `phase8-qbo-nudging`), worktree
`/data/JCM_stripped/jcm-strat-phase9`, GPU 0. Runs launched by `scripts/phase9_queue.sh`; this record
is filled in by `scripts/phase9_analysis.sh` output as chains finish.

## Why

Both resolutions set the implicit diffusion of the semi-Lagrangian transport: the horizontal
truncation through the interpolation at the departure points and the hyperdiffusion that goes
with it, the vertical spacing through the interpolation across levels in a stratosphere whose
transport is a slow ascent against a strong stratification. Phase 8 left the model at T63L95
with a tropical age of air 0.8 yr too old at 55 hPa against CLaMS/ERA5 and a tropics–extratropics
contrast of 1.4–1.6 yr against 2.8. Before a grid is fixed for the aerosol work this phase asks how
much of that gap is resolution, in which direction each axis moves it, and what each step costs.

## Question this phase answers

For the Phase 8b configuration (Polvani-Kushner stratosphere, ERA5-nudged troposphere below
150 hPa, QBO nudged to ERA5 up to 1 hPa, four passive tracers), how do age of air, the
Brewer-Dobson upwelling, the ERA5 climatology error and the cost change across T63 → T85 → T119
and across L95 → L63 → L47 (stratosphere kept), and where does each metric stop changing?

## Configuration

Everything is Phase 8b (`+experiment=p8_qbo` at commit 77fc70d, KEY_DECISIONS #26) except the
grid, the time step, the segment length of the 2005–2009 chain and, for the reduced vertical
grids, the sponge depth. One change per run.

| run | grid | columns | levels | dt | segments | ERA5 target per segment | hyperdiffusion profile |
|---|---|---|---|---|---|---|---|
| T63L95 (baseline, `p8b_5yr`) | `echam_t63_l95_hybrid` | 192×96 = 18 432 | 95 | 12 min | 5 × year | 31 GB | ECHAM (63, 95) |
| T63L63 | `strat_t63_l63_hybrid` | 18 432 | 63 | 12 | 5 × year | 21 GB | mapped from (63, 95) |
| T63L47 | `strat_t63_l47_hybrid` | 18 432 | 47 | 12 | 5 × year | 15 GB | mapped from (63, 95) |
| T85L95 | `echam_t85_l95_hybrid` | 256×128 = 32 768 | 95 | 9 | 10 × half-year | 28 GB | ECHAM (63, 95) (nearest) |
| T119L95 | `echam_t119_l95_hybrid` | 360×180 = 64 800 | 95 | 6 | 20 × quarter | 28 GB | ECHAM (127, 95) (nearest) |
| T85L63, T85L47 | as above, `grid.spectral_truncation=85` | 32 768 | 63 / 47 | 9 | 10 × half / 5 × year | 18 / 28 GB | mapped from (63, 95) |
| T119L63, T119L47 | as above, `grid.spectral_truncation=119` | 64 800 | 63 / 47 | 6 | 20 × quarter / 10 × half | 18 / 27 GB | mapped from (127, 95) |

**Horizontal.** T127 is not constructible in JCM (valid truncations are 21, 31, 42, 63, 85, 106,
119, 170, …); T119 on 360 × 180 Gaussian points is the 1° grid. The time step scales with
truncation (12 → 9 → 6 min) and must divide the 5-day save interval (KEY_DECISIONS #29). The
ECHAM hyperdiffusion base timescale is interpolated in truncation by JCM (7 h at T63 → 1.5 h at
T127); the order profile borrows the nearest tabulated truncation (T85 → T63's, T119 → T127's).

**Vertical** (`jcm_strat/levels.py`, KEY_DECISIONS #28). Both reduced tables are subsets of the
L95 interfaces, so every kept level is an L95 level:

- **strat63 = 8 + 47 + 8**: the 47 L95 levels between 1.08 and 159 hPa are kept exactly; the 21
  mesospheric levels above 1 hPa become 8 (interfaces 0.035, 0.073, 0.111, 0.198, 0.333, 0.458,
  0.714, 1.08 hPa), the 27 tropospheric levels below 159 hPa become 8 (210, 306, 402, 522, 656,
  795, 957, 1013 hPa).
- **strat47 = 7 + 15 + 17 + 8**: 30–159 hPa kept exactly (17 levels, ~1 km); 1.08–30 hPa every
  other L95 interface (15 levels, ~2 km); mesosphere 7 levels; troposphere the same 8 as strat63.
  This is not ECHAM's own L47, whose stratosphere is ~2 km throughout.

The hyperdiffusion order at each reduced level is the L95 order at the L95 index of its centre
(strat63 at T63: del² × 4, del⁴ × 3, del⁶ × 4, del⁸ × 52; strat47: 3 / 3 / 2 / 39). The upper
sponge keeps L95's tau(p): 4 levels with a factor 6.73 per level on strat63, 3 levels with a
factor 8 on strat47, both reaching ~0.2 hPa like L95's 10 levels with factor 2. The QBO window
(90 → 1 hPa) and the nudging cutoff (150 hPa) contain the same levels as on L95.

**Held fixed, and recorded as limitations.** The T63 terrain file is interpolated to every grid
(only T63 and T106 have native files; the dry model has no sub-grid orography), so the orography
spectrum is the same at all truncations. The ERA5 nudging target is 6-hourly everywhere; its
WeatherBench2 source store is 240×121 for T63 and 360×181 for T85 and T119. The clock tracer is
the surface clock (reset below 700 hPa) only, so the vertical axis includes tropospheric transit
(issue #25). All chains start from ERA5 on 2005-01-01 and carry the Phase 4 spin-up deficit of
the 5-yr clock (issue #44), which is the same kind of bias in every run.

## Reference data

| quantity | reference | source |
|---|---|---|
| age of air (surface clock) | CLaMS v3.1 driven by ERA5, 2005–2009 annual mean, 1° × 39 levels | `/data/CLaMS/CLaMS_v3/clams_v3.1_era5_zm_lat.zip` |
| age of air (entry age, pattern only) | WACCM6 REF-D1 | `/data/CESM2_REFD1_AOA/` |
| zonal-mean u, T 1–1000 hPa; equatorial u | ERA5 monthly (CDS), 2005–2009 | `cache/era5_ref/era5_zm_monthly_*.nc` |
| u(60N/60S, 10 hPa) daily | ERA5 (CDS) | `cache/era5_ref/era5_u10hPa_daily_*.nc` |
| tropical upward mass flux (TEM) | WACCM6 histSST 2005–2009, same method; ERA5-era literature 6–8 × 10⁹ kg/s at 70 hPa | `/data/cesm2.1.5_output/histSST/...` |

Age of air is the ranking metric (RMSE against CLaMS over latitude × ln p, 100–5 hPa, cos-lat
weighted, model from the last 12 months = 73 five-day means); ERA5 climatology, QBO, up-flux and
cost stand beside it, unweighted (`scripts/resolution_metrics.py`).

## Runs

| run | days | segments | status |
|---|---|---|---|
| `p9smoke_*` (8) | 5 | 1 | all exit 0: no OOM, ERA5 from cache, lmidatm diffusion profile in use, health OK |
| `p9_t63l63_*` → `p9_t63l63_5yr` | 1825 | 5 | **done**, 65 min on GPU 0 (2026-09-09 20:40–21:45), all segments exit 0 |
| `p9_t63l47_*` → `p9_t63l47_5yr` | 1825 | 5 | **done**, 58 min on GPU 0 (21:45–22:43), all segments exit 0 |
| `p9_t85l95_*` → `p9_t85l95_5yr` | 1825 | 10 | running (GPU 0, from 22:48) |
| `p9_t119l95_*` → `p9_t119l95_5yr` | 1825 | 20 | queued |
| `p9_t85l63_*` → `p9_t85l63_5yr` | 1825 | 10 | **done**, 1 h 44 min on GPU 2 (22:08–23:52), all segments exit 0 |
| `p9_t85l47_*` → `p9_t85l47_5yr` | 1825 | 5 | **done**, 1 h 23 min on GPU 1 (22:28–23:51), all segments exit 0 |
| `p9_t119l63_*` → `p9_t119l63_5yr` | 1825 | 20 | running (GPU 1, from 2026-09-10 00:40) |
| `p9_t119l47_*` → `p9_t119l47_5yr` | 1825 | 10 | queued (GPU 2, waiting for its ERA5 windows) |

Susanne released GPUs 0–2 to this phase for 2026-09-09/10, so from 22:08 UTC the chains ran three at a time (one queue per GPU, `phase9_queue.sh` claim files).

## Acceptance

| check | threshold | result |
|---|---|---|
| every chain complete | all segments exit 0, 1825 days linked, no OOM, ERA5 from cache | pending |
| tracers at every resolution | unity max \|q−1\| < 1e-3, sai burden within ±2 % of analytic, minima ≥ 0 | pending |
| stability at the chosen dt | u RMSE 100–1 hPa vs ERA5 < 30 m/s, no NaN | pending |
| ranking delivered | `resolution_metrics.md` with per-metric ranks; convergence statement per axis; GPU-hours per unit of AoA improvement | pending |

## Results

(filled in from `scripts/phase9_analysis.sh` as chains finish)

## Reading

(pending)
