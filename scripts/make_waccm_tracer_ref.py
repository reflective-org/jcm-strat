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
``aoa_ref``   WACCM6 REF-D1 zonal-mean mean age of air in days (``/data/CESM2_REFD1_AOA``, the
              ``AOA`` variable: entry age relative to 0.47N/103 hPa), annual mean over
              ``--aoa-years`` (default 1990-2019). Phase 11 relaxes the clocks towards it above the
              tracer lid (1 hPa), where WACCM's age is ~4.5 yr and nearly flat in latitude; negative
              values (below the base point) are set to 0 and never used.

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
AOA_FILE = "/data/CESM2_REFD1_AOA/AoA_waccm6_refd1.04_AOA1mf_1970-2019_ba_0_100.0_ck_0_50.0.nc"


def _open(var: str) -> xr.DataArray:
    files = sorted(glob.glob(f"{SRC}/{CASE}.{var}.*.nc"))
    if not files:
        raise FileNotFoundError(f"no {var} file under {SRC}")
    ds = xr.open_dataset(files[0], decode_times=False)      # first file = 2015-2064, enough
    return ds[var], ds


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", type=int, default=10, help="years averaged for the loss frequency")
    ap.add_argument("--aoa-years", default="1990-2019", help="years averaged for the mesospheric age target")
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
    # WACCM6 REF-D1 mean age (years -> days), annual mean over the requested years, on the same 70 levels
    w6 = xr.open_dataset(AOA_FILE, decode_times=False)
    y0, y1 = (int(v) for v in a.aoa_years.split("-")); d = w6.date.values
    sel = np.where((d >= y0 * 10000 + 101) & (d < (y1 + 1) * 10000 + 101))[0]
    aoa = (w6.AOA.isel(time=sel).mean("time") * 365.25).clip(0.0, None).fillna(0.0)
    q0lat, q0lev = out[f"{SPECIES[0].lower()}_q0"].lat, out[f"{SPECIES[0].lower()}_q0"].lev
    aoa = aoa.assign_coords(lat=q0lat) if np.allclose(aoa.lat, q0lat, atol=1e-3) else aoa.interp(lat=q0lat)   # same f09 grid, roundoff apart
    assert np.allclose(aoa.lev.values, q0lev.values, rtol=1e-4), "WACCM AOA levels differ from the CCMI grid"
    aoa = aoa.assign_coords(lev=q0lev)
    out["aoa_ref"] = aoa.astype("float32").assign_attrs(units="day", long_name=f"WACCM6 REF-D1 zonal-mean mean age of air (entry age, base 103 hPa), {a.aoa_years} annual mean, {sel.size} months; negative values set to 0")
    print(f"AOA: {sel.size} months; global mean at 1 / 0.1 / 0.01 hPa = " + " / ".join(f"{float(aoa.sel(lev=l, method='nearest').mean()) / 365.25:.2f} yr" for l in (1, 0.1, 0.01)))
    ds = xr.Dataset(out)
    ds["lev"].attrs.update(units="hPa", long_name="WACCM hybrid reference pressure (surface last)")
    ds.attrs.update(source=f"{SRC}/{CASE}.*", created=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    description="Zonal-mean N2O and CFC-11 initial state and loss frequency (Phase 10) and WACCM6 mean age for the tracer lid (Phase 11); scripts/make_waccm_tracer_ref.py")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ds.to_netcdf(a.out)
    print(f"wrote {a.out}: {dict(ds.sizes)}, {os.path.getsize(a.out)/1e3:.0f} kB")


if __name__ == "__main__":
    main()
