# Phase 1 — strip the physics: dry Held-Suarez on the L95 high-top grid

Status: in progress (2026-09-02). Branch `phase1-stripped-dry`, PR into `dev`.

## Question this phase answers

How much faster is the model once every tropospheric physics term is gone, and does the
stratosphere survive with only Held-Suarez relaxation and the upper sponge holding it?

## Configuration

`+experiment=p1_dry` = `physics=strat_dry` (Held-Suarez only) on `grid=echam_t63_l95_hybrid`,
`run=longrun` (dt 12 min, 10-level sponge, `target_T_K=250`), `init=jw init.rh=0.0`, real
terrain, no forcing file, no nudging, no tracers. Variant `physics=strat_dry_gwd` adds Hines
non-orographic and Lott-Miller orographic gravity-wave drag.

## Runs

| run | command | wall | result |
|---|---|---|---|
| `p1_dry_30d` | `scripts/launch.sh p1_dry_30d +experiment=p1_dry run.total_time=30 run.chunk_days=10` | _pending_ | _pending_ |

## Acceptance (from PLANS.md)

| check | threshold | result |
|---|---|---|
| 365 days, no NaN | 0 NaN vars every chunk | _pending_ |
| global-mean surface pressure drift | < 0.1 hPa over the year | _pending_ |
| subtropical jets present | qualitative, zonal-mean u | _pending_ |
| top-level zonal-mean dT/dt, last 60 days | < 0.5 K/day | _pending_ |
| throughput vs Phase 0 baseline (51.6 days/hr) | ≥ 2× | _pending_ |
