#!/usr/bin/env bash
# Build /data/JCM_stripped/jcm-strat/.venv from the pinned submodules. Idempotent.
#
# Why each step is what it is:
#  * uv-managed CPython 3.11: system python is 3.10, jcm needs >=3.11.
#  * dinosaur installed FIRST from external/dinosaur (shoyer/dinosaur@semi-lagrangian,
#    pinned SHA): jcm's requirements.txt names that branch by *name*, and the branch
#    head moves. env/overrides.txt re-points jcm's requirement at the submodule.
#  * jax[cuda12] requested explicitly: jcm does not pin jax, so pip would otherwise
#    install the CPU wheel and JAX would silently run on CPU.
#  * everything (uv cache, python, venv) lives inside the repo; nothing in $HOME.
set -euo pipefail
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
echo "   dinosaur $(git -C "$REPO/external/dinosaur" rev-parse --short HEAD)"

echo ">> python 3.11 + venv"
"$UV" python install 3.11
[ -d "$REPO/.venv" ] || "$UV" venv --python 3.11 "$REPO/.venv"
# shellcheck disable=SC1091
source "$REPO/.venv/bin/activate"

echo ">> 1/4 dinosaur (pinned submodule)"
"$UV" pip install -e "$REPO/external/dinosaur"

echo ">> 2/4 jcm[era5] with the dinosaur requirement overridden onto the submodule"
mkdir -p "$REPO/env"
echo "dinosaur @ file://$REPO/external/dinosaur" > "$REPO/env/overrides.txt"
"$UV" pip install -e "$REPO/external/jax-gcm[era5]" --override "$REPO/env/overrides.txt"

echo ">> 3/4 CUDA JAX"
"$UV" pip install "jax[cuda12]"

echo ">> 4/4 jcm_strat overlay"
"$UV" pip install -e "$REPO[dev]"

"$UV" pip freeze > "$REPO/env/requirements.lock"
echo ">> done. lock written to env/requirements.lock; now run scripts/check_env.sh"
