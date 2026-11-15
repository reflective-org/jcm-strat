#!/usr/bin/env python
"""Merge an L95 checkpoint onto one of the L95-subset tables of ``jcm_strat/levels.py`` (Phase 30).

    python scripts/remap_checkpoint_levels.py IN.ckpt OUT.ckpt --levels 76

Each target layer is a run of whole L95 layers (the tables are subsets of L95's interfaces), so every
full-level field becomes the pressure-thickness-weighted mean of the L95 layers it contains and every
half-level field keeps the shared interfaces. The weights are the layer thicknesses at the reference
surface pressure (1013.25 hPa). That is exact for pure-pressure layers (all of the mesosphere) and
mass-conserving to the column's p_s/p0 variation elsewhere. The cuts are all above 1.08 hPa or below
402 hPa, so nothing between them changes: those layers are copied bit for bit.
The dycore reference temperature is isothermal, so ``temperature_variation`` is averaged like T itself;
spectral fields are averaged coefficient by coefficient (the operation is linear).
Everything else in the payload (clock, schema, tracer set, surface fields) is carried over unchanged.
"""
from __future__ import annotations

import argparse
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flax.serialization as fs  # noqa: E402
import numpy as np  # noqa: E402

from jcm_strat import levels  # noqa: E402

P0 = 101325.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--levels", type=int, required=True)
    a = ap.parse_args(argv)

    idx = levels.interface_indices(a.levels)
    l95 = levels._orig_get_echam_levels(95)
    ph = np.asarray(l95.a_boundaries, float) + np.asarray(l95.b_boundaries, float) * P0
    dp = np.diff(ph)
    W = np.zeros((a.levels, 95))
    for j in range(a.levels):
        k0, k1 = idx[j], idx[j + 1]
        W[j, k0:k1] = dp[k0:k1] / dp[k0:k1].sum()

    d = fs.msgpack_restore(open(a.src, "rb").read())
    n_full = n_half = 0

    def remap(tree):
        nonlocal n_full, n_half
        for k, v in tree.items():
            if isinstance(v, dict):
                remap(v)
                continue
            arr = np.asarray(v)
            if arr.ndim >= 1 and arr.shape[0] == 95:
                tree[k] = np.tensordot(W, arr.astype(np.float64), axes=(1, 0)).astype(arr.dtype)
                n_full += 1
            elif arr.ndim >= 1 and arr.shape[0] == 96:
                tree[k] = arr[idx]
                n_half += 1

    remap(d["dycore"])
    remap(d["physics"])
    with open(a.dst, "wb") as f:
        f.write(fs.to_bytes(d))
    print(f"{a.src} -> {a.dst}: L95 -> L{a.levels}, {n_full} full-level and {n_half} half-level arrays merged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
