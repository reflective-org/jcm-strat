#!/usr/bin/env python3
"""Phase 22: ERA5 monthly-mean 3-D temperature 1-500 hPa (CDS reanalysis-era5-pressure-levels-monthly-means, 1 deg) for the
Chang/Mooring 3-D T_eq iteration - the nudging cache (WeatherBench2 13 levels) stops at 50 hPa and clamps above it.
    python scripts/fetch_era5_t3d_monthly.py 2005 2007   -> cache/era5_ref/era5_t3d_monthly_<y>.nc
"""
import os, sys
import cdsapi
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = ["1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125", "150", "175", "200", "225", "250", "300", "350", "400", "450", "500"]
y0, y1 = int(sys.argv[1]), int(sys.argv[2])
for y in range(y0, y1 + 1):
    out = os.path.join(REPO, "cache", "era5_ref", f"era5_t3d_monthly_{y}.nc")
    if os.path.exists(out):
        print("have", out); continue
    tmp = out + ".part"
    cdsapi.Client(quiet=True, progress=False).retrieve(
        "reanalysis-era5-pressure-levels-monthly-means",
        {"product_type": ["monthly_averaged_reanalysis"], "variable": ["temperature"], "pressure_level": LEVELS,
         "year": [str(y)], "month": [f"{m:02d}" for m in range(1, 13)], "time": ["00:00"], "grid": [1.0, 1.0],
         "data_format": "netcdf", "download_format": "unarchived"}, tmp)
    os.replace(tmp, out); print("wrote", out, flush=True)
