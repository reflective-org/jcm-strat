#!/usr/bin/env python3
"""Zonal-mean circulation of a PARADIS long-range rollout, cached as one small netCDF.

    python scripts/paradis_zonal.py <member_dir>/state.zarr <out.nc> [--skip-days 30]

Reads the raw zarr store (time, feature, lat, lon), converts the Cartesian wind components to
zonal (u) and meridional (v) wind, and writes zonal means of u, v, T and omega (Pa/s) on the
17 pressure levels for every saved time after the first ``skip_days`` days (the 6-hourly
spin-up month is dropped; the rest is daily). The cache is what plot_zonal_mean.py and
vortex_series.py read with --paradis.
"""
import argparse
import sys

import numpy as np
import xarray as xr
import zarr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("store"); ap.add_argument("out"); ap.add_argument("--skip-days", type=float, default=30.0)
    a = ap.parse_args()
    g = zarr.open_group(a.store, mode="r")
    fn = [str(x) for x in g["feature_names"][:]]
    t = g["time"][:].astype("datetime64[ns]")
    plev = g["pressure_levels"][:]
    lat = g["latitude"][:]; lon = g["longitude"][:]
    lonr = np.deg2rad(lon)[None, :]; latr = np.deg2rad(lat)[:, None]
    keep = np.where(t >= t[0] + np.timedelta64(int(a.skip_days * 24), "h"))[0]
    print(f"{len(keep)} of {len(t)} times kept: {t[keep[0]]} .. {t[keep[-1]]}", flush=True)
    ix = {k: [fn.index(f"{k}_h{p}") for p in plev] for k in ("wind_x", "wind_y", "wind_z", "temperature", "vertical_velocity")}
    nt, nl, ny = len(keep), len(plev), len(lat)
    U = np.empty((nt, nl, ny), np.float32); V = np.empty_like(U); T = np.empty_like(U); W = np.empty_like(U)
    state = g["state"]
    for j, i in enumerate(keep):
        s = state[i]
        wx, wy, wz = s[ix["wind_x"]], s[ix["wind_y"]], s[ix["wind_z"]]
        u = -np.sin(lonr) * wx + np.cos(lonr) * wy
        v = -np.sin(latr) * np.cos(lonr) * wx - np.sin(latr) * np.sin(lonr) * wy + np.cos(latr) * wz
        U[j] = u.mean(-1); V[j] = v.mean(-1); T[j] = s[ix["temperature"]].mean(-1); W[j] = s[ix["vertical_velocity"]].mean(-1)
        if j % 200 == 0:
            print(f"  {j}/{nt} {t[i]}", flush=True)
    ds = xr.Dataset(
        {"u": (("time", "level", "lat"), U, {"units": "m/s", "long_name": "zonal-mean zonal wind"}),
         "v": (("time", "level", "lat"), V, {"units": "m/s", "long_name": "zonal-mean meridional wind"}),
         "T": (("time", "level", "lat"), T, {"units": "K", "long_name": "zonal-mean temperature"}),
         "omega": (("time", "level", "lat"), W, {"units": "Pa/s", "long_name": "zonal-mean pressure vertical velocity"})},
        coords={"time": t[keep], "level": ("level", plev, {"units": "hPa"}), "lat": lat},
        attrs={"source": a.store, "init_date": str(dict(g.attrs).get("init_date")), "skipped_days": a.skip_days,
               "note": "PARADIS v2 stage 3d long-range rollout; Cartesian winds converted to u, v; zonal means over 360 longitudes"})
    ds.to_netcdf(a.out); print("wrote", a.out)


if __name__ == "__main__":
    main()
