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
export PATH="$HOME/.local/bin:$PATH"                     # uv
mkdir -p "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$HF_HOME" "$JCM_ERA5_CACHE" "$SCRATCH"
if [ -f "$JCM_STRAT_REPO/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$JCM_STRAT_REPO/.venv/bin/activate"
fi
