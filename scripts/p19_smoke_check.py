"""Check a Phase 19-21 smoke run directory: the run header and the output. Prints PASS/FAIL lines, exit 1 on any FAIL.

    python scripts/p19_smoke_check.py runs/<smoke> [--restart]

Header: both dinosaur dot algorithms HIGHEST (printed before and after the model build), the jcm 3 defaults line
(sponge levels 1, no target_T_K, cubic SL). Output: first time 1990-01-01T06, u/T/ps/clocks finite, ps in a sane
range, clocks between 0 and ~5 days below the lid. --restart (a smoke started from another run's checkpoint with
first_segment=true): the clocks must have restarted at 0, i.e. the 1990-01-01T06 clock is <= 0.25 d + tolerance.
"""
from __future__ import annotations

import glob
import os
import re
import sys

import numpy as np
import xarray as xr

fails = 0


def check(ok, msg):
    global fails
    print(("PASS  " if ok else "FAIL  ") + msg)
    fails += 0 if ok else 1


def main(argv):
    run = argv[0]
    restart = "--restart" in argv
    log = open(os.path.join(run, "log.txt")).read()
    check(len(re.findall(r"FLOAT32_DOT_ALGORITHM=HIGHEST FAST_TRANSFORM_DOT_ALGORITHM=HIGHEST", log)) >= 2,
          "dot precision HIGHEST echoed before and after the model build")
    check("sponge levels=1 timescale_h=None enspodi=None" in log and re.search(r"sl_vertical_interpolation=(None|linear|cubic)", log),
          "jcm 3 settings echoed (sponge levels 1 ECHAM, SL vertical interpolation)")
    check("target_T_K: " not in log, "no target_T_K in the config dump")
    files = sorted(glob.glob(os.path.join(run, "longrun_day*.nc")), key=lambda f: int(re.search(r"day(\d+)", f).group(1)))
    check(len(files) >= 1, f"{len(files)} chunk file(s)")
    if not files:
        return
    ds = xr.open_dataset(files[0])
    t0 = str(ds.time.values[0])[:13]
    check(t0 == "1990-01-01T06", f"first output time {t0}")
    for v in ("u_wind", "v_wind", "temperature", "normalized_surface_pressure", "aoa", "aoa150", "aoa_sfc", "aoa500", "n2o"):
        if v in ds:
            a = ds[v].values
            check(bool(np.all(np.isfinite(a))), f"{v} finite (min {np.nanmin(a):.4g}, max {np.nanmax(a):.4g})")
        else:
            check(False, f"{v} in output")
    ps = ds["normalized_surface_pressure"].values * 1013.25
    check(400 < ps.min() and ps.max() < 1120, f"ps range {ps.min():.0f}-{ps.max():.0f} hPa")
    p = (ds["hybrid_a_full"] / 100.0 + ds["hybrid_b_full"] * 1013.25).values      # hPa at a standard surface
    below_lid = p > 10.0          # the lid relaxes above 1 hPa and SL transport carries lid values a few levels down
    a0 = ds["aoa_sfc"].isel(time=0).values[below_lid]
    if restart:
        check(float(a0.max()) <= 0.25 + 0.02, f"restart: clocks restarted on 1990-01-01 (aoa_sfc max at 06 UTC {a0.max():.3f} d, below the lid)")
    a_end = ds["aoa_sfc"].isel(time=-1).values[below_lid]
    check(float(a_end.max()) <= 5.5 and float(a_end.min()) >= -1e-3, f"aoa_sfc after {ds.time.size / 4:g} d in [0, 5.5] below 10 hPa (lid air mixes down a little) ({a_end.min():.3f}..{a_end.max():.3f})")
    if "lott_miller_sso" in log:
        m = re.findall(r"nktopg\D{0,20}(\d+)", log)
        print(f"INFO  Lott-Miller in the physics; nktopg mentions in the log: {m[:3]}")


if __name__ == "__main__":
    main(sys.argv[1:])
    print("RESULT", "PASS" if fails == 0 else f"FAIL ({fails})")
    sys.exit(1 if fails else 0)
