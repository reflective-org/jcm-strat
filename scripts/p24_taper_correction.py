#!/usr/bin/env python3
"""Phase 24: the AL7 T_eq correction with its equatorward edge moved poleward.

    python scripts/p24_taper_correction.py IN.nc OUT.nc A0 A1

Multiplies dte by teq_update.region_mask's latitude ramp (0 for |lat| <= A0, sin^2 to 1 at |lat| >= A1). AL7 itself ramps
25 -> 35 deg, so with A0 >= 25 the result is AL7 unchanged poleward of A1 and zero equatorward of A0.
"""
import sys
import numpy as np
import xarray as xr

src, dst, a0, a1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
d = xr.open_dataset(src).load()
al = np.abs(d.lat.values)
w = np.where(al >= a1, 1.0, np.where(al <= a0, 0.0, np.sin(0.5 * np.pi * (al - a0) / (a1 - a0)) ** 2))
d["dte"] = d.dte * xr.DataArray(w, dims="lat")
d.attrs.update(p24_source=src, p24_lat_taper=f"({a0}, {a1})")
d.to_netcdf(dst)
print(f"[p24] {dst}: max |dte| at |lat|<35 {float(abs(d.dte.where(abs(d.lat) < 35)).max()):.2f} K, >=50 {float(abs(d.dte.where(abs(d.lat) >= 50)).max()):.2f} K")
