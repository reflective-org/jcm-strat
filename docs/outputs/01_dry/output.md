# Phase 1 — strip the physics: dry Held-Suarez on the L95 high-top grid

Status: in progress (2026-09-02). Branch `phase1-stripped-dry`, PR into `dev`.

## Question this phase answers

How much faster is the model once every tropospheric physics term is gone, and does the
stratosphere survive with only Held-Suarez relaxation and the upper sponge holding it?

## Configuration

`+experiment=p1_dry` = `physics=strat_dry` (Held-Suarez only) on `grid=echam_t63_l95_hybrid`,
`run=longrun` (dt 12 min, 10-level sponge, `target_T_K=250`), `init=jw init.rh=0.0`, real
terrain, no forcing file, no nudging, no tracers. The planned gravity-wave-drag variant
could not be composed with Held-Suarez (issue #20) and was dropped from this phase.

## Runs

| run | command | wall | result |
|---|---|---|---|
| `p1_dry_30d` | `scripts/launch.sh p1_dry_30d +experiment=p1_dry run.total_time=30 run.chunk_days=10` | 109 s incl. compile | exit 0, 0 NaN, p_s drift -0.05 hPa, top-level T flat at 249.9 K |
| `p1_dry_1yr` | `scripts/launch.sh p1_dry_1yr +experiment=p1_dry run.total_time=365` | see results | see results |

## Acceptance (from PLANS.md)

| check | threshold | result |
|---|---|---|
| 365 days, no NaN | 0 NaN vars every chunk | _pending_ |
| global-mean surface pressure drift | < 0.1 hPa over the year | _pending_ |
| subtropical jets present | qualitative, zonal-mean u | _pending_ |
| top-level zonal-mean dT/dt, last 60 days | < 0.5 K/day | _pending_ |
| throughput vs Phase 0 baseline (51.6 days/hr) | ≥ 2× | _pending_ |
