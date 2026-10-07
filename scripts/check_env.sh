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
check python -c "import dinosaur; assert dinosaur.__version__ == '1.5.0', dinosaur.__version__"
check python -c "import dinosaur.semi_lagrangian"
check python -c "from jcm.dycore.dinosaur.dycore import semi_lagrangian_available as a; assert a()"
check python -c "import jcm; assert jcm.__version__ == '3.0.0rc1', jcm.__version__"
# jcm #892: dinosaur 1.5's bf16 GPU dots are miscompiled by jaxlib < 0.11.2 (NH->SH mass drift);
# importing jcm must leave both defaults at HIGHEST.
check python -c "
import jax, jcm, jcm_strat
from dinosaur import jax_numpy_utils as j, spherical_harmonic as s
print('      FLOAT32_DOT_ALGORITHM', j.FLOAT32_DOT_ALGORITHM, '| FAST_TRANSFORM_DOT_ALGORITHM', s.FAST_TRANSFORM_DOT_ALGORITHM)
assert j.FLOAT32_DOT_ALGORITHM == jax.lax.Precision.HIGHEST, j.FLOAT32_DOT_ALGORITHM
assert s.FAST_TRANSFORM_DOT_ALGORITHM == jax.lax.Precision.HIGHEST, s.FAST_TRANSFORM_DOT_ALGORITHM"
check python -c "import jcm_strat"
check test "$(git -C "$REPO/external/jax-gcm"  rev-parse HEAD)" = 35dc19974670044eb7ab8a3a8944a6143eae54eb
check test -n "$CUDA_VISIBLE_DEVICES"
for v in UV_CACHE_DIR HF_HOME JCM_ERA5_CACHE SCRATCH; do
  check bash -c "[[ \"\${$v}\" == \"$REPO\"/* ]]"
done
exit $fail
