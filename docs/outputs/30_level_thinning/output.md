# Phase 30 — thinned vertical grids: fewer mesospheric and nudged-tropospheric levels

**Goal (Susanne, 2026-11-08):** can layers in the troposphere or the mesosphere be cut from the best runs (QBO10d, AL7h)
to make them faster, without losing what the scorecard measures?

**What can be cut.** Everything that defines the configurations is pressure-based: the AL7h correction, the QBO
nudging, the Hines launch level (634 hPa) and the ERA5 nudging cutoff. So L95 can lose levels where the solution is
either nudged or above the 1 hPa tracer lid, and keep 1.08-402 hPa exactly. Three new tables in `jcm_strat/levels.py`,
each a subset of L95's interfaces (grid configs `strat_t63_l{76,84,87}_hybrid.yaml`):

| table | cut | levels |
|---|---|---|
| strat84 | mesosphere above 1.08 hPa: 22 -> 11 layers (every other L95 interface) | 84 |
| strat87 | ERA5-nudged troposphere below 402 hPa: 16 -> 8 layers | 87 |
| strat76 | both | 76 |

**Known risks from earlier phases.**
- In Phase 19, 8 thick mesospheric layers with the cubic semi-Lagrangian scheme blew up. 11 layers is milder but was
  untested.
- In Phase 12, thinning the *whole* troposphere to 8 layers halved the deep branch. The free 159-402 hPa layer is kept
  here.

## Runs

1. **Timing bench** (`scripts/phase30_bench.sh`, 2026-11-08 18:53-19:05 PST, GPU 1).
   - 30 days from 2007-01-01 on the QBO10d configuration, with the ERA5 initial state on each grid.
   - All four grids stayed healthy.
2. **QBO10dL76**: QBO10d on strat76 (`scripts/phase30_run.sh`, tmux `strat_p30_run`).
   - The 2005-2010 chain ran on GPU 0 from 2026-11-08 20:03 to 21:20 PST: 77 minutes, no health stop.
3. **AL7hL84**: AL7h on strat84, the mesosphere cut only (Susanne, 2026-11-09: "mesosphere cut only, but on AL7h").
   - Launched as `NLEV=84 N=AL7hL84 QBO_TAU= bash scripts/phase30_run.sh` (tmux `strat_p30_al7h`).
   - The 2005-2010 chain ran on GPU 1 from 18:42 to 20:05 PST: 83 minutes, no health stop.

Both runs start, like every restart run, from P20b's end-of-2004 state.
- `scripts/remap_checkpoint_levels.py` merges the L95 checkpoint onto the thinned table: a pressure-thickness-weighted
  mean over the L95 layers each new layer contains.
- The untouched middle layers are bit-identical, and tracer mass is conserved to 1e-10.
- The remapped states sit in `runs/p30_L76_20040101` and `runs/p30_AL7hL84_20040101`.

Both runs are scored on 2006-2010 beside the Phase 28/29 runs (QBO30 left out, Susanne 2026-11-09):
- groups A-C with `scripts/success_metrics.py`;
- daily zonal means with `scripts/daily_zm.py`, which now reads the levels of the run it processes;
- group D against the CDS ERA5 reference.

Logs: `runs/p30_run.log`, `runs/p30_bench.log`.

Outputs (this directory):
- `success_0610/success_table.md`: groups A-D for all nine runs, from `success_metrics.json`.
- `variability_table.md`, `variability.json` and `variability_*.png`: group D.
- `w0610/QBO10dL76/`, `w0610/AL7hL84/`: vortex, seasonal, QBO and TEM diagnostics.

## Speed

Seconds per 10-day chunk:

| grid | bench, 30 days | 2005-2010 chain, 2007 segment median | speed-up |
|---|---|---|---|
| L95 | 21.2 | 21.2 (QBO10d), 21.3 (AL7h) | 1.00x |
| strat87 | 19.6 | | 1.08x |
| strat84 | 19.2 | 19.1 (AL7hL84) | 1.11-1.12x |
| strat76 | 17.7 | 17.8 (QBO10dL76) | 1.19-1.20x |

The bench fits about 3.7 s fixed per chunk plus 0.18 s per level. So the level count is a weak lever: even L63 would
only reach about 1.4x.

## Result (2006-2010)

| | QBO10d (L95) | **QBO10dL76** | AL7h (L95) | **AL7hL84** |
|---|---|---|---|---|
| A age of air, mean err | 1.11 | **0.98** | 1.10 | **1.10** |
| B residual circulation, mean err | 0.90 | **0.93** | 1.05 | **1.05** |
| C polar vortex, mean err | 0.95 | **0.84** | 0.66 | **0.82** |
| **combined (A-C)** | 0.99 | **0.91** | 0.93 | **0.99** |
| passed / 21 | 14 | **16** | 14 | **12** |
| D variability, mean err | 1.04 | **1.35** | 1.22 | **1.12** |
| D passed / 13 | 8 | **8** | 8 | **8** |

Selected metrics (reference in brackets):

| metric | QBO10d | QBO10dL76 | AL7h | AL7hL84 |
|---|---|---|---|---|
| A1 entry age 55 hPa tropics [yr] (CLaMS 1.11) | 0.95 | 0.98 | 1.00 | 1.00 |
| A2 2-D age RMSE vs CLaMS [yr] | 0.61 | 0.55 | 0.62 | 0.62 |
| A4 transit 70 -> 10 hPa [yr] (2.3-3.2) | 2.16 | 2.21 | 2.15 | 2.15 |
| B1 w* 100 / 70 / 50 hPa [mm/s] (WACCM 0.40 / 0.21 / 0.20) | 0.17 / 0.20 / 0.26 | 0.16 / 0.19 / 0.26 | 0.14 / 0.22 / 0.29 | 0.15 / 0.22 / 0.29 |
| C1 NH jet 10 hPa [m/s, deg] (ERA5 25.2 at 62.5N) | 16.1 at 55.0N | 17.4 at 58.8N | 18.5 at 60.6N | 17.1 at 56.9N |
| C1 SH jet 10 hPa [m/s] (ERA5 71.9) | 65.6 | 65.6 | 66.0 | 65.9 |
| C2 polar-cap T bias 50 hPa N / S [K] | -0.48 / 1.55 | -1.15 / 1.66 | -1.05 / 1.27 | -0.72 / 1.38 |
| D1-N year-to-year std winter u 10 hPa [m/s] (ERA5 6.51) | 3.62 | 3.94 | 3.50 | 2.96 |
| D2-N daily std winter u 60N 10 hPa [m/s] (ERA5 15.0) | 10.4 | 8.56 | 11.4 | 9.71 |
| D3 NH major SSWs (ERA5 8) | 4 | 2 | 3 | 6 |
| D6 heat flux -> polar-cap T slope N / S (ERA5 0.97 / 0.77) | 0.47 / 0.64 | 0.36 / 0.60 | 0.53 / 0.57 | 0.38 / 0.61 |
| D7 age vs w* slope [yr per mm/s] (CLaMS -4.52) | -2.40 | -2.32 | -1.88 | -1.71 |

## Findings

1. **Both thinned grids are stable and keep the mean transport.**
   - Five years on each grid ran without a health stop. The 11-layer mesosphere does not repeat Phase 19's blow-up.
   - Age of air and the residual circulation hardly move: A1, A4 and B1 change by at most 0.05 in their units.
   - On A-C, QBO10dL76 even scores better than QBO10d (0.91 against 0.99). The gain is split between:
     - A (0.98 against 1.11), from a smaller 2-D age RMSE (0.55 against 0.61 yr);
     - C (0.84 against 0.95), from a northern 10 hPa jet at 58.8N instead of 55N.
   - AL7hL84 loses on C (0.82 against 0.66) through the northern 10 hPa jet: 17.1 m/s at 56.9N, against 18.5 m/s at
     60.6N on L95.
2. **The speed-up is small: 1.12x (strat84) to 1.19x (strat76).** The fixed per-step cost dominates, so no level table
   will make these runs much faster.
3. **Both thinned runs have a weaker northern vortex response to the waves.**
   - The two changes that go the same way in both runs are D2-N, the daily wind spread at 60N (10.4 -> 8.6 and
     11.4 -> 9.7 m/s), and D6-N, the heat-flux response (0.47 -> 0.36 and 0.53 -> 0.38). ERA5 is 15.0 and 0.97,
     so both move further away.
   - The mean D score moves in opposite directions: 1.04 -> 1.35 for QBO10dL76, 1.22 -> 1.12 for AL7hL84. The
     difference comes from D3 and D1-N, which in five winters are too few events to read (2 against 6 SSWs).
   - The mesosphere cut is common to both runs, so it is the likely cause of the weaker NH variability. No strat87-only
     run was made to separate the two cuts.

**Caveats.**
- One five-year run per grid; five winters is a small sample for D1 and D3 (see Phase 28).
- The restart runs keep drifting younger after the restart (Phase 26). That applies equally to the L95 runs compared
  here.

**Status.** Nothing was adopted: the production runs since then (the Phase 31 AL7h validation, the 50-year and the
1970-2022 chains) stay on L95. strat76 and strat84 remain available as `grid=strat_t63_l{76,84}_hybrid
level_table=strat` for runs where 12-20 % matters more than NH vortex variability.
