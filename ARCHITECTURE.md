# Architecture

## One paragraph

`jcm-strat` runs the unmodified `jcm` package with (a) our own Hydra config files and (b) one
extra physics term. Hydra's `--config-dir` puts `jcm_strat/config/` on the config search path,
so `physics=strat_dry` or `+experiment=p2_sd` resolve from our tree while every other group
(`grid`, `run`, `init`, `nudging`, `terrain`, `forcing`, `dycore`, `diffusion`) comes from the
installed `jcm.config`. Our physics YAMLs reference our term by import path
(`_target_: jcm_strat.tracers.PassiveTracers`), which is why `jcm_strat` is an installable
package and not a loose directory.

```
python -m jcm.main --config-dir jcm_strat/config  physics=strat_dry +experiment=p1_dry ...
        │                       │
        │                       └── our overlay: physics/*.yaml, experiment/*.yaml
        └── jcm.main → jcm.runners.run(cfg) → Model(dinosaur SL dycore + ComposablePhysics)
                                                  └── terms: held_suarez, [hines_gwd, lott_miller_sso], [passive_tracers], [nudging]
```

## Layers

| Layer | Where | Changes how often |
|---|---|---|
| Dinosaur (dycore, semi-Lagrangian transport) | `external/dinosaur` @ pinned SHA | only by a deliberate pin bump |
| JCM (model, physics library, runner, ERA5 I/O) | `external/jax-gcm` @ pinned SHA | only by a deliberate pin bump |
| Config overlay | `jcm_strat/config/` | every phase |
| Our physics | `jcm_strat/tracers.py` | Phase 3 onward |
| Run tooling | `scripts/` | as needed |
| Analysis / plots | `scripts/*.py` → `docs/outputs/<phase>/` | every phase |

## Why a pinned submodule and an override, not `pip install jcm`

JCM's `requirements.txt` says `dinosaur @ git+https://github.com/shoyer/dinosaur@semi-lagrangian`.
That is a branch, not a commit: a colleague's environment resolved commit `f7a44f68`, ours
resolves `bd99e39b`, and tomorrow's would resolve something else. `scripts/bootstrap_env.sh`
installs Dinosaur from `external/dinosaur` first and then installs JCM with
`--override env/overrides.txt` re-pointing the requirement at that path. `scripts/check_env.sh`
verifies the installed Dinosaur really came from the submodule. When PR neuralgcm/dinosaur#135
merges and a release contains it, both go away (DEFERRED issue "pin dinosaur to a release").

JCM also does not pin `jax` itself, so a plain install gets the CPU wheel and JAX runs on CPU
*silently*. The bootstrap requests `jax[cuda12]` explicitly and `check_env.sh` asserts a GPU
device.

## Environment and disk

Everything lives inside the repo directory: `.venv/`, `cache/{uv,uv-python,huggingface,era5}/`,
`scratch/` (JAX compile cache), `runs/`. `scripts/env.sh` exports the variables JCM reads
(`HF_HOME`, `JCM_ERA5_CACHE`, `SCRATCH`) so nothing defaults into `$HOME` — the root disk had
15 GB free when this project started and one regridded ERA5 year is larger than that.

## GPU policy

GPU 0 only. `scripts/env.sh` sets `CUDA_VISIBLE_DEVICES=0`; `scripts/launch.sh` refuses to
start if a `strat_*` tmux session exists or GPU 0 has a process. Comparisons (A/B runs) are run
one after the other, never side by side. GPUs 1–7 belong to other work on this shared node.

## Run outputs and the per-phase record

`runs/<session>/` holds the raw output (`log.txt`, `.hydra/` resolved config, netCDF) and is
gitignored. Each phase's analysis script copies its final figures into
`docs/outputs/<NN_phase>/` next to an `output.md` that records the exact command, the commit,
wall-clock, the numbers against the acceptance thresholds, and the decision taken. Those
figures *are* tracked (`!docs/outputs/**` in `.gitignore`).

## Time conventions

`run.time_step` is in minutes; `run.total_time` in days; `run.save_interval` in days.
Throughput is reported as *simulated days per wall-clock hour on one H100*.
