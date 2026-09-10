#!/usr/bin/env python3
"""Rewrite a finished segment's chunk files compressed (CPU, background; Phase 10).

JCM writes raw float32 netCDF (no encoding). At 6-hourly output a T63L95 year is ~160 GB, so the
chain script calls this on each finished segment: every ``longrun_day*.nc`` is rewritten with
zlib level 1 + byte shuffle (lossless, typically 1.5-2x smaller for these fields) to a temporary
file next to it and moved into place atomically, so a reader - or the aggregate's symlinks - never
sees a half-written file. A file whose variables already carry zlib is skipped, so the script is
idempotent and restartable. Compression is deliberately not done inside the run: it would sit on
the GPU's critical path (issue #19).

    python scripts/compact_run.py runs/p10_20050101 [--level 1]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time

import xarray as xr


def compact(path: str, level: int) -> tuple[int, int]:
    ds = xr.open_dataset(path)
    if all(ds[v].encoding.get("zlib") for v in ds.data_vars if ds[v].ndim >= 3):
        ds.close()
        return 0, 0
    enc = {v: {"zlib": True, "complevel": level, "shuffle": True} for v in ds.data_vars if ds[v].ndim >= 2}
    tmp = path + ".compact.tmp"
    ds.load().to_netcdf(tmp, encoding=enc)
    ds.close()
    before, after = os.path.getsize(path), os.path.getsize(tmp)
    os.replace(tmp, path)                       # atomic: symlinks to `path` keep working
    return before, after


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rundir")
    ap.add_argument("--level", type=int, default=1)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")), key=lambda f: int(f.rsplit("day", 1)[1][:-3]))
    if not files:
        sys.exit(f"no longrun_day*.nc in {a.rundir}")
    t0 = time.time(); tot_b = tot_a = 0
    for f in files:
        b, aft = compact(f, a.level)
        tot_b += b; tot_a += aft
        print(f"[compact] {os.path.basename(f)}: {b/1e9:.2f} -> {aft/1e9:.2f} GB" if b else f"[compact] {os.path.basename(f)}: already compressed", flush=True)
    print(f"[compact] {a.rundir}: {tot_b/1e9:.1f} -> {tot_a/1e9:.1f} GB in {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
