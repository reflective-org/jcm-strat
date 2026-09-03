# Phase 4 — the 5-year run and the Phase-1 number

Status: **in progress**. Branch `phase4-5yr` (stacked on Phase 3, PR #24).

## Configuration

`+experiment=p4_5yr`: the Phase-3 configuration unchanged — dry Held-Suarez physics, ERA5-nudged
winds and temperature below 150 hPa, free stratosphere, four passive tracers with the clock
excluded from the mass fixer — run from 2005-01-01 for 1826 days (through 2009-12-31), 30-day
chunks, 5-day means, restart checkpoint every chunk.

ERA5 window prefetched as one file: `python -m jcm.data.era5 --grid echam_t63_l95_hybrid
--start 2004-12-31 --end 2010-01-03 --init` (the runner pads the window by −1/+2 days; the cache
key hashes grid and window, so the dates must match exactly). Size: ~155 GB on disk and resident
in RAM during the run (1 TB available).

## Runs

| run | days | purpose |
|---|---|---|
| `p4_5yr` | 1826 | the Phase-4 run, 2005–2009 |

## Acceptance (from PLANS.md)

ACCEPTANCE_TABLE

## Results

RESULTS

## The Phase-1 number

HEADLINE

## Reading

READING
