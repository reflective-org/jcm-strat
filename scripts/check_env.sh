#!/usr/bin/env bash
# The environment acceptance test. All checks must pass before any model run.
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$REPO/scripts/env.sh"
fail=0
check() { if "$@"; then echo "PASS  $*"; else echo "FAIL  $*"; fail=1; fi; }

check python -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version"
check python -c "import jax; d = jax.devices(); assert len(d) == 1 and d[0].platform == 'gpu', d; print('     ', d)"
check python -c "import jax; assert jax.__version__; print('      jax', jax.__version__)"
check python -c "import dinosaur; assert dinosaur.__version__ == '1.4.0', dinosaur.__version__"
check python -c "import dinosaur.semi_lagrangian"
check python -c "from jcm.dycore.dinosaur.dycore import semi_lagrangian_available as a; assert a()"
check python -c "import jcm; assert jcm.__version__ == '2.1.0b0', jcm.__version__"
check python -c "
import json, pathlib, dinosaur
dist = [p for p in pathlib.Path(dinosaur.__file__).parents[1].glob('dinosaur-*.dist-info')][0]
u = json.loads((dist / 'direct_url.json').read_text())['url']
assert u.endswith('external/dinosaur'), u; print('      dinosaur from', u)"
check python -c "import jcm_strat"
check test "$(git -C "$REPO/external/dinosaur" rev-parse HEAD)" = bd99e39b2e256aabb9fb6d94a60be65c9ca8772a
check test "$(git -C "$REPO/external/jax-gcm"  rev-parse HEAD)" = 849893be46372b702c777057713c571675ca90ba
check test "$CUDA_VISIBLE_DEVICES" = 0
for v in UV_CACHE_DIR HF_HOME JCM_ERA5_CACHE SCRATCH; do
  check bash -c "[[ \"\${$v}\" == \"$REPO\"/* ]]"
done
exit $fail
