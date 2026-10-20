#!/usr/bin/env python3
"""Phase 22 score: the lower/middle-stratosphere circulation of a run against ERA5, same months.

    JAX_PLATFORMS=cpu python scripts/teq_score.py runs/<agg> --t0 2005-04-01 --t1 2008-01-01 --name A1 --desc TEXT --out DIR

Monthly zonal means of u and T over [t0, t1) (every 6-hourly frame) against ERA5's monthly zonal means of the same months
(cache/era5_ref/era5_zm_monthly_<year>.nc, interpolated in log p onto the model's reference levels). Writes DIR/<name>.json with:

  u_ls_ext   RMSE of monthly u, 100-10 hPa, |lat| >= 30 (cos-weighted)       <- the Phase 22 ranking metric
  u50_ext    the same at 50 hPa only;  u_up_ext  10-1 hPa (guard: the upper stratosphere must not be wrecked)
  T_ls, T_ls_ext, T50_cap   RMSE of T 100-10 hPa (all / |lat|>=30), polar-cap (60-90) T bias at 50 hPa DJF N / JJA S
  jet50_N/S, jet10_N/S      winter jet maximum over 30-90 deg (DJF north, JJA south) [m/s] and its latitude, model and ERA5
  w_trop     tropical (15S-15N) annual TEM w* at 70/50/30/10 hPa [mm/s], model vs ERA5 1996-2001 (only TEM years cached),
             w_logerr = mean |log(model/ERA5)| over 70-30 hPa (guard: the shallow branch must not collapse)
  age150     aoa150 at 55 hPa, tropics (10S-10N) and 50-70N/S, last 60 days [yr] (diagnostic; clocks carried from P20b)
"""
from __future__ import annotations

import argparse, json, os, sys
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_compare as sc        # noqa: E402
import sweep_score as ss          # noqa: E402
import strat_circulation as circ  # noqa: E402
from teq_update import run_files, ERA5_ZM   # noqa: E402

WIN = {"N": ((12, 1, 2), 1), "S": ((6, 7, 8), -1)}


def load(rundir, t0, t1):
    ub, vb, tb, thb, vth, times, age = [], [], [], [], [], [], []
    p = lat = None
    for f in run_files(rundir):
        d = xr.open_dataset(f, decode_times=True); tt = d.time.values
        k = np.where((tt >= t0) & (tt < t1))[0]
        if k.size == 0:
            d.close(); continue
        d = d.isel(time=k); p = d.level.values * sc.P0_HPA; lat = d.lat.values
        theta = d.temperature * (1000.0 / p)[None, :, None, None] ** circ.KAPPA
        v = d.v_wind; vbar = v.mean("lon"); thbar = theta.mean("lon")
        ub.append(d.u_wind.mean("lon").values); vb.append(vbar.values); tb.append(d.temperature.mean("lon").values)
        thb.append(thbar.values); vth.append(((v - vbar) * (theta - thbar)).mean("lon").values); times.append(d.time.values)
        if "aoa150" in d and tt[k][-1] > t1 - np.timedelta64(60, "D"):
            j = d.time.values > t1 - np.timedelta64(60, "D")
            age.append(d.aoa150.isel(time=np.where(j)[0]).mean("lon").values)
        d.close()
    t = np.concatenate(times)
    mk = lambda a: xr.DataArray(np.concatenate(a), dims=("time", "level", "lat"), coords={"time": t, "level": p, "lat": lat})
    f = dict(u=mk(ub), v=mk(vb), T=mk(tb), th=mk(thb), vth=mk(vth))
    a = np.concatenate(age).mean(0) / 365.25 if age else None
    return f, p, lat, a


def era5_monthly(var, keys, p, lat):
    out = {}
    for y in sorted({k[0] for k in keys}):
        ds = xr.open_dataset(ERA5_ZM.format(y=y), decode_times=True)
        tname = [c for c in ds.coords if c.startswith("time") or c == "valid_time"][0]
        x = ds[var].rename({tname: "time"}).interp(lat=lat); lp = np.log(ds.level.values.astype(float)); o = np.argsort(lp)
        for m in range(1, 13):
            if (y, m) in keys:
                prof = x.sel(time=x.time.dt.month == m).mean("time").values[o]
                lpo = np.log(np.clip(p, np.exp(lp[o][0]), np.exp(lp[o][-1])))
                out[(y, m)] = np.stack([np.interp(lpo, lp[o], prof[:, j]) for j in range(lat.size)], axis=1)
        ds.close()
    return out


def rmse(d, lat, mask):
    w = np.broadcast_to(np.cos(np.deg2rad(lat)), d.shape)
    return float(np.sqrt(np.sum((d ** 2 * w)[mask]) / np.sum(w[mask])))


def jet(u, lat, sign):
    m = (sign * lat >= 30)
    i = int(np.argmax(u[m])); return float(u[m][i]), float(lat[m][i])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("--t0", required=True); ap.add_argument("--t1", required=True)
    ap.add_argument("--name", required=True); ap.add_argument("--desc", default=""); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    t0, t1 = np.datetime64(a.t0), np.datetime64(a.t1)
    f, p, lat, age = load(a.rundir, t0, t1)
    um = f["u"].resample(time="1MS").mean(); Tm = f["T"].resample(time="1MS").mean()
    keys = [(int(str(x)[:4]), int(str(x)[5:7])) for x in um.time.values]
    eu, eT = era5_monthly("uzm", keys, p, lat), era5_monthly("tzm", keys, p, lat)
    U = um.values; T = Tm.values; EU = np.stack([eu[k] for k in keys]); ET = np.stack([eT[k] for k in keys])
    mon = np.array([k[1] for k in keys])
    L = lambda lo, hi: ((p >= lo) & (p <= hi))[None, :, None]
    ext = (np.abs(lat) >= 30)[None, None, :]
    full = np.ones_like(U, bool)
    k50 = int(np.argmin(np.abs(p - 50))); k10 = int(np.argmin(np.abs(p - 10)))
    s = dict(name=a.name, desc=a.desc, run=a.rundir, window=f"{a.t0}..{a.t1}", months=len(keys),
             u_ls_ext=rmse(U - EU, lat, full & L(10, 100) & ext), u50_ext=rmse((U - EU)[:, k50], lat, np.broadcast_to(np.abs(lat) >= 30, (U.shape[0], lat.size))),
             u_up_ext=rmse(U - EU, lat, full & L(1, 10) & ext), T_ls=rmse(T - ET, lat, full & L(10, 100)), T_ls_ext=rmse(T - ET, lat, full & L(10, 100) & ext))
    for h, (months, sign) in WIN.items():
        k = np.isin(mon, months)
        um_s, eu_s = U[k].mean(0), EU[k].mean(0); tm_s, et_s = T[k].mean(0), ET[k].mean(0)
        for lev, kk in (("50", k50), ("10", k10)):
            mj, ml = jet(um_s[kk], lat, sign); ej, el = jet(eu_s[kk], lat, sign)
            s[f"jet{lev}_{h}"] = [round(mj, 1), round(ml, 1), round(ej, 1), round(el, 1)]
            s[f"u60_{lev}_{h}"] = [round(float(np.interp(60 * sign, lat, um_s[kk])), 1), round(float(np.interp(60 * sign, lat, eu_s[kk])), 1)]
        cap = (sign * lat >= 60); w = np.cos(np.deg2rad(lat[cap]))
        s[f"T50_cap_{h}"] = round(float(np.sum((tm_s[k50] - et_s[k50])[cap] * w) / np.sum(w)), 2)
    # tropical w* vs the ERA5 1996-2001 TEM climatology
    pm, lm, _, wm = ss.wstar_fields(f, tuple(range(1, 13)))
    ew = ss.era5_wstar(list(range(1996, 2002)))
    s["w_trop"] = {}
    if ew is not None:
        pe, le, _, we = ew["annual"]
        def trop(pp, ll, ww, lev):
            m = np.abs(ll) <= 15; c = np.cos(np.deg2rad(ll[m])); prof = np.sum(ww[:, m] * c, 1) / np.sum(c)
            o = np.argsort(pp); return float(np.interp(np.log(lev), np.log(pp[o]), prof[o]) * 1e3)
        errs = []
        for lev in (70, 50, 30, 10):
            mv, ev = trop(pm, lm, wm, lev), trop(pe, le, we, lev)
            s["w_trop"][str(lev)] = [round(mv, 3), round(ev, 3)]
            if lev in (70, 50, 30) and mv > 0 and ev > 0:
                errs.append(abs(np.log(mv / ev)))
        s["w_logerr"] = round(float(np.mean(errs)), 3) if len(errs) == 3 else None
    if age is not None:
        k55 = int(np.argmin(np.abs(p - 55)))
        band = lambda lo, hi: float(np.average(age[k55, (lat >= lo) & (lat <= hi)], weights=np.cos(np.deg2rad(lat[(lat >= lo) & (lat <= hi)]))))
        s["age150"] = dict(trop=round(band(-10, 10), 2), n50_70=round(band(50, 70), 2), s50_70=round(band(-70, -50), 2))
    for k in ("u_ls_ext", "u50_ext", "u_up_ext", "T_ls", "T_ls_ext"):
        s[k] = round(s[k], 3)
    json.dump(s, open(os.path.join(a.out, f"{a.name}.json"), "w"), indent=1)
    print(f"[score] {a.name}: u_ls_ext {s['u_ls_ext']:.2f} m/s, u50_ext {s['u50_ext']:.2f}, u_up_ext {s['u_up_ext']:.2f}, T_ls {s['T_ls']:.2f} K, "
          f"jet50 N {s['jet50_N'][0]:.0f}@{s['jet50_N'][1]:.0f} (ERA5 {s['jet50_N'][2]:.0f}@{s['jet50_N'][3]:.0f}), "
          f"S {s['jet50_S'][0]:.0f}@{s['jet50_S'][1]:.0f} (ERA5 {s['jet50_S'][2]:.0f}@{s['jet50_S'][3]:.0f}), "
          f"cap T50 N {s['T50_cap_N']:+.1f} S {s['T50_cap_S']:+.1f} K, w_logerr {s.get('w_logerr')}, age150 {s.get('age150')}")


if __name__ == "__main__":
    main()
