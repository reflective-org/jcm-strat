#!/usr/bin/env python3
"""Cut per-segment ERA5 nudging windows out of one prefetched multi-year cache file.

    python scripts/slice_era5_years.py <big_cache_file> 2006 2007 2008 2009

For each year Y writes the window the runner asks for when run.start_date=Y-01-01 and
run.total_time = days in Y — i.e. [Y-01-01 minus 1 day, (Y+1)-01-01 plus 2 days] — under
the cache name jcm.data.era5 would use, so the segment run hits the cache instead of
downloading. The cache key hashes grid coordinates only (not the window), so the name is the
big file's name with the dates replaced. Verified: the slice for 2005 reproduces the
separately downloaded 2005 file (1476 six-hourly steps, same first/last time).
"""
import datetime as dt
import os
import re
import sys

import xarray as xr


def main(big: str, years) -> None:
    m = re.match(r"(.*_)(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})(_.*\.nc)$", os.path.basename(big))
    if not m:
        sys.exit("unexpected cache file name: " + big)
    prefix, _, _, suffix = m.groups()
    ds = xr.open_dataset(big)
    for y in years:
        y = int(y)
        s = dt.date(y, 1, 1); n = (dt.date(y + 1, 1, 1) - s).days
        start, end = s - dt.timedelta(days=1), s + dt.timedelta(days=n + 2)
        out = os.path.join(os.path.dirname(big), f"{prefix}{start}_{end}{suffix}")
        if os.path.exists(out):
            print("exists", out); continue
        sl = ds.sel(time=slice(str(start), str(end)))
        tmp = out + ".tmp"
        sl.to_netcdf(tmp); os.replace(tmp, out)
        print(f"wrote {out}  ({sl.sizes['time']} steps, {start}..{end})", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
