# Source this before anything else: `source scripts/env.sh`.
# Puts every cache and scratch path inside the repo (the root disk is ~97% full)
# and pins this project to GPU 0. GPUs 1-7 are not ours.
JCM_STRAT_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JCM_STRAT_REPO
export UV_CACHE_DIR="$JCM_STRAT_REPO/cache/uv"
export UV_PYTHON_INSTALL_DIR="$JCM_STRAT_REPO/cache/uv-python"
export HF_HOME="$JCM_STRAT_REPO/cache/huggingface"      # jcm boundary files (hf://bundles/...)
export JCM_ERA5_CACHE="$JCM_STRAT_REPO/cache/era5"       # regridded WeatherBench2 ERA5 windows
export SCRATCH="$JCM_STRAT_REPO/scratch"                 # jcm puts its JAX compile cache in $SCRATCH/jcm-jax-cache
export CUDA_VISIBLE_DEVICES=0                            # project policy: GPU 0 only
# The venv's editable install of jcm_strat points at the main checkout; in a git worktree the
# tree that sourced this file must win, so put it first on the import path.
export PYTHONPATH="$JCM_STRAT_REPO${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$HOME/.local/bin:$PATH"                     # uv
# libcuda.so.1 lives under the containerised driver mount, off the loader path.
# Without it JAX SILENTLY falls back to CPU (hours -> weeks); check_env.sh asserts a GPU.
# glibc reads LD_LIBRARY_PATH once at process start, so it must be exported here, not in Python.
_cuda_lib="${JCM_STRAT_CUDA_LIB:-/run/nvidia/driver/usr/lib/x86_64-linux-gnu}"
if [ ! -e "$_cuda_lib/libcuda.so.1" ]; then
  _cuda_lib="$(dirname "$(find /run/nvidia /usr/lib -name libcuda.so.1 -not -path '*/stubs/*' -not -path '*/lib32/*' 2>/dev/null | head -1)")"
fi
if [ -e "$_cuda_lib/libcuda.so.1" ]; then
  case ":${LD_LIBRARY_PATH:-}:" in *":$_cuda_lib:"*) ;; *) export LD_LIBRARY_PATH="$_cuda_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}";; esac
else
  echo "env.sh: WARNING libcuda.so.1 not found - JAX will run on CPU" >&2
fi
mkdir -p "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$HF_HOME" "$JCM_ERA5_CACHE" "$SCRATCH"
if [ -f "$JCM_STRAT_REPO/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$JCM_STRAT_REPO/.venv/bin/activate"
fi
