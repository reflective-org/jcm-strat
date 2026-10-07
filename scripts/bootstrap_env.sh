#!/usr/bin/env bash
# Build <this tree>/.venv from the pinned jax-gcm submodule + PyPI dinosaur. Idempotent.
#
# Why each step is what it is:
#  * uv-managed CPython 3.11: system python is 3.10, jcm needs >=3.11.
#  * dinosaur from PyPI, EXACT version (Phase 19): jcm >= 35dc1997 requires
#    dinosaur>=1.5.0, which ships the semi-Lagrangian core upstream, so the old
#    shoyer/dinosaur@semi-lagrangian submodule is gone. env/overrides.txt pins it.
#    dinosaur 1.5's float32 GPU dots are miscompiled by jaxlib < 0.11.2; jcm #892
#    overrides them to HIGHEST on import (scripts/check_env.sh asserts it).
#  * jax[cuda12] requested explicitly (pinned to jcm's validated 0.10.2): otherwise pip
#    installs the CPU wheel and JAX would silently run on CPU.
#  * everything (uv cache, python, venv) lives inside the repo; nothing in $HOME.
set -euo pipefail
DINOSAUR_VERSION=1.5.0
JAX_VERSION=0.10.2
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"

UV="$HOME/.local/bin/uv"
if [ ! -x "$UV" ]; then
  echo ">> installing uv into $HOME/.local/bin"
  curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="$HOME/.local/bin" UV_NO_MODIFY_PATH=1 sh
fi

echo ">> submodules"
for i in 1 2 3 4 5 6 7 8 9 10; do
  git -C "$REPO" submodule update --init --recursive && break
  echo "   (git lock busy, retrying)"; python3 -c "import time; time.sleep(1)"
done
echo "   jax-gcm  $(git -C "$REPO/external/jax-gcm"  rev-parse --short HEAD)"
echo "   dinosaur $DINOSAUR_VERSION (PyPI)"

echo ">> python 3.11 + venv"
"$UV" python install 3.11
[ -d "$REPO/.venv" ] || "$UV" venv --python 3.11 "$REPO/.venv"
# shellcheck disable=SC1091
source "$REPO/.venv/bin/activate"

echo ">> 1/4 dinosaur==$DINOSAUR_VERSION (PyPI)"
"$UV" pip install "dinosaur==$DINOSAUR_VERSION"

echo ">> 2/4 jcm[era5] with dinosaur and jax held at the exact pins"
mkdir -p "$REPO/env"
printf 'dinosaur==%s\njax==%s\njaxlib==%s\n' "$DINOSAUR_VERSION" "$JAX_VERSION" "$JAX_VERSION" > "$REPO/env/overrides.txt"
"$UV" pip install -e "$REPO/external/jax-gcm[era5]" --override "$REPO/env/overrides.txt"

echo ">> 3/4 CUDA JAX"
"$UV" pip install "jax[cuda12]==$JAX_VERSION"

echo ">> 4/4 jcm_strat overlay"
"$UV" pip install -e "$REPO[dev]"

"$UV" pip freeze > "$REPO/env/requirements.lock"
echo ">> done. lock written to env/requirements.lock; now run scripts/check_env.sh"
