# Key decisions

Every default in this repo and why it is what it is. Newer entries at the bottom.
If `docs/` disagrees with this file, this file is current.

| # | Date | Decision | Why |
|---|---|---|---|
| 1 | 2026-09-02 | Repo is a config overlay + tiny package, **not a fork of JCM** | JCM `dev` moves daily; we must be able to follow it with a SHA bump. Hydra `--config-dir` makes an overlay trivial. |
| 2 | 2026-09-02 | Upstreams pinned as submodules: jax-gcm `849893b` (dev, 2026-09-01), dinosaur `bd99e39b` (semi-lagrangian, 2026-08-24) | JCM's dinosaur requirement is a floating branch name; an unpinned install is not reproducible. |
| 3 | 2026-09-02 | Own environment under `/data/JCM_stripped/jcm-strat/`; nothing from other users' homes | Only SL-capable Dinosaur on the machine sat in a colleague's venv; `/data/jax-gcm-fork` is a stale June snapshot. Root disk 97% full → all caches inside the repo. |
| 4 | 2026-09-02 | **GPU 0 only**, runs strictly sequential | Shared 8×H100 node; user requirement. |
| 5 | 2026-09-02 | Phase-1 grid **T63L95** (existing, lid 0.01 hPa); ~30-level grid later | Only 40/47/95-level tables exist in JCM; a new table needs code + diffusion orders. Validate the physics first on a validated parent grid, then reduce and A/B. |
| 6 | 2026-09-02 | Stratospheric temperature held by **Held-Suarez relaxation** in Phase 1; RRTMGP filed as an issue | Zero code; radiation is the dominant cost and would blur the speed number. Known limitation: no polar-night jet in the HS profile (Polvani-Kushner is a deferred issue). |
| 7 | 2026-09-02 | ERA5 nudging of **winds + temperature**, τ = 6 h, `pbl_levels: 2` | With convection removed, only relaxation would hold up tropospheric T. |
| 8 | 2026-09-02 | Nudging cutoff **150 hPa hard mask for now** (`nudging.min_pressure_hpa: 150`) | Comparable to AIDE-SAI-link's 150 hPa domain; one YAML key. Must become a dynamical tropopause (issue). WeatherBench2 ERA5 has no usable data above ~60 hPa anyway. |
| 9 | 2026-09-02 | ERA5 period **2005–2009** | Quiet volcanically; overlaps CLaMS age-of-air reference (2004–2023); three observed SSWs (Jan 2006, Feb 2008, Jan 2009). |
| 10 | 2026-09-02 | Age-of-air clock tracer reset where **p > 700 hPa** | Standard clock-tracer convention; comparable to CLaMS and WACCM `AOA1` references on `/data`. |
| 11 | 2026-09-02 | No conservation code in Phase 1 | JCM's dycore already applies a global proportional mass fixer to SL tracers (`_fix_nodal_tracer_mass`, on by default). A `unity` tracer measures what it hides. |
| 12 | 2026-09-02 | Each phase ships `docs/outputs/<NN>/output.md` + tracked plots | Scientific model: every step is validated and the evidence is reviewable in the PR. |
