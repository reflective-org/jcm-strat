#!/usr/bin/env python3
"""Zonal-mean N2O / CFC-11 reference from WACCM for the Phase 10 steady tracers (CPU, run once).

Source: CESM2.1.5 WACCM CCMI-REFD2 monthly history on this machine
(``/data/cesm2.1.5_output/CCMI_REFD2/month_1/``): mixing ratios ``N2O``, ``CFC11`` (mol/mol),
chemical loss rates ``N2O_CHML``, ``CFC11_CHML`` (molecules cm-3 s-1) and ``T``. For each species the
file written here holds, on WACCM's (lev, lat) grid:

``<sp>_q0``   zonal-mean mixing ratio of January of the first year, divided by the zonal-and-global
              mean of its lowest model level, so the tracer is 1 in the troposphere and falls to
              ~1e-2 (N2O) / ~1e-4 (CFC-11) in the upper stratosphere. Used as the initial state.
``<sp>_k``    loss frequency  k = CHML / (vmr * n_air)  in 1/s, n_air = p / (k_B T), averaged over
              the first ten years (all months), so the tracers have a steady, latitude- and
              height-dependent sink with WACCM's photolysis climatology.

The model term (``jcm_strat/advection_tracers.py``) interpolates both in latitude and ln p onto its
columns. Levels are WACCM's hybrid reference pressures (``lev``, hPa), which are pure pressure above
~100 hPa; the small error in the troposphere is irrelevant for a tracer held at 1 there.

    python scripts/make_waccm_tracer_ref.py [--years 10] [--out jcm_strat/data/waccm_tracer_ref.nc]
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import os

import numpy as np
import xarray as xr

SRC = "/data/cesm2.1.5_output/CCMI_REFD2/month_1"
CASE = "b.e21.BWSSP245cmip6.f09_g17.CCMI-REFD2.001.cam.h0"
K_B = 1.380649e-23   # J/K
SPECIES = ("N2O", "CFC11")


def _open(var: str) -> xr.DataArray:
    files = sorted(glob.glob(f"{SRC}/{CASE}.{var}.*.nc"))
    if not files:
        raise FileNotFoundError(f"no {var} file under {SRC}")
    ds = xr.open_dataset(files[0], decode_times=False)      # first file = 2015-2064, enough
    return ds[var], ds


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, default=10, help="years averaged for the loss frequency")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "jcm_strat", "data", "waccm_tracer_ref.nc"))
    a = ap.parse_args()
    nm = 12 * a.years
    T, tds = _open("T")
    T = T.isel(time=slice(0, nm)).mean("lon")                                    # (time, lev, lat)
    p_pa = (T.lev * 100.0).astype("float64")                                     # hPa -> Pa
    n_air = (p_pa / (K_B * T)) * 1e-6                                            # molecules cm-3
    out = {}
    for sp in SPECIES:
        q, qds = _open(sp)
        chml, _ = _open(f"{sp}_CHML")
        qz = q.isel(time=slice(0, nm)).mean("lon")                               # (time, lev, lat), mol/mol
        cz = chml.isel(time=slice(0, nm)).mean("lon")                            # molecules cm-3 s-1
        surf = qz.isel(time=0, lev=-1)                                           # lowest level (lev ascends downward)
        w = np.cos(np.deg2rad(surf.lat)); norm = float((surf * w).sum() / w.sum())
        q0 = (qz.isel(time=0) / norm).clip(0.0, None)                            # 1 in the troposphere
        k = (cz / (qz.clip(1e-30, None) * n_air)).mean("time").clip(0.0, None)   # 1/s, annual & 10-yr mean
        out[f"{sp.lower()}_q0"] = q0.astype("float32").assign_attrs(units="1", long_name=f"WACCM zonal-mean {sp} of {int(qds.time.attrs['units'].split()[2][:4])}-01, normalised by its surface mean ({norm:.3e} mol/mol)")
        out[f"{sp.lower()}_k"] = k.astype("float32").assign_attrs(units="1/s", long_name=f"WACCM {sp} loss frequency CHML/(vmr n_air), mean of the first {a.years} years")
        print(f"{sp}: surface mean {norm:.3e} mol/mol; q0 eq at 10/1 hPa = "
              f"{float(q0.sel(lat=0, method='nearest').sel(lev=10, method='nearest')):.3f} / "
              f"{float(q0.sel(lat=0, method='nearest').sel(lev=1, method='nearest')):.4f}; "
              f"lifetime 1/k eq at 30/10/3/1 hPa (yr) = " +
              " / ".join(f"{1/max(float(k.sel(lat=0, method='nearest').sel(lev=l, method='nearest')), 1e-30)/3.15576e7:.2f}" for l in (30, 10, 3, 1)))
    ds = xr.Dataset(out)
    ds["lev"].attrs.update(units="hPa", long_name="WACCM hybrid reference pressure (surface last)")
    ds.attrs.update(source=f"{SRC}/{CASE}.*", created=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    description="Zonal-mean N2O and CFC-11 initial state and loss frequency for jcm-strat Phase 10 (scripts/make_waccm_tracer_ref.py)")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ds.to_netcdf(a.out)
    print(f"wrote {a.out}: {dict(ds.sizes)}, {os.path.getsize(a.out)/1e3:.0f} kB")


if __name__ == "__main__":
    main()
