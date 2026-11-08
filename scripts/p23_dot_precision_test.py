"""Phase 23 side test (Susanne 2026-10-20): run jcm_strat.main with dinosaur's own float32 dot algorithm
(BF16_BF16_F32_X6) instead of jcm's Precision.HIGHEST override, to measure the speed difference. TIMING ONLY:
on jaxlib < 0.11.2 this algorithm is miscompiled (jcm #892, dinosaur#147) and the run drifts NH -> SH mass;
never use its output for science. Usage: python p23_dot_precision_test.py <jcm_strat.main hydra args...>
"""
import sys

import jax
import jcm.dycore.dinosaur.dot_precision as dp
from dinosaur import jax_numpy_utils

dp.apply_dot_precision_workaround = lambda *a, **k: {"float32": False, "fast_transform": False}
dp.jaxlib_is_affected = lambda *a, **k: False          # lets jcm_strat.main.log_dot_precision accept the setting
jax_numpy_utils.FLOAT32_DOT_ALGORITHM = jax.lax.DotAlgorithmPreset.BF16_BF16_F32_X6

import jcm_strat.main as m   # noqa: E402

print(f"p23 dot test: FLOAT32_DOT_ALGORITHM={jax_numpy_utils.FLOAT32_DOT_ALGORITHM}", flush=True)
m.main()
