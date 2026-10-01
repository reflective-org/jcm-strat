#!/usr/bin/env python3
"""Phase 17: one damped fixed-point step of the JFV T_e correction toward the ERA5 temperature climatology.

    python scripts/teq_correction.py runs/p17_A0_10yr --out cache/teq/A1.nc [--prev cache/teq/A0.nc] [--alpha 0.7]

T_model(month, p, lat) - T_ERA5(month, p, lat) is formed from the run's monthly zonal means over the last ``--window-years``
years (every 6-hourly frame) and the ERA5 monthly zonal means of ``--era5-years`` (default 1990-1999: a climatology, so the
correction does not chase the model's or ERA5's individual warmings), on the ERA5 levels 100-1 hPa. The new cumulative
correction is

    dT_e(new) = dT_e(prev) - alpha * S[T_model - T_ERA5]

S = 1-2-1 smoothing, twice in latitude and once (periodic) in month. Matching the monthly zonal-mean T everywhere matches the
meridional gradients and so, through thermal wind from the nudged 100 hPa level up, the zonal wind; no region masks (their
edges would themselves be gradients). Below 100 hPa the correction is zero (ERA5 nudging, Held-Suarez blend). Above 1 hPa
ERA5 has no data: the 1 hPa value is tapered linearly in log p to zero at 0.1 hPa. The total is capped at +-``--cap`` K.
Written as (month[12], pfull, lat) in K, the format ``JuckerColumns(te_correction_file=...)`` reads.
"""
from __future__ import annotations

import argparse, os, sys
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_score as ss          # noqa: E402
import strat_compare as sc        # noqa: E402

P_CORR = np.array([1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100.0])     # ERA5 levels carrying the correction


def model_monthly_T(rundir, window_years):
    files = ss._files(rundir)
    last = xr.open_dataset(files[-1], decode_times=True); t_end = last.time.values[-1]; last.close()
    t0 = t_end - np.timedelta64(int(round(window_years * 365.25 * 24)), "h")
    sums = acc = None; p_hpa = lat = None; count = np.zeros(12)
    for f in files:
        d = xr.open_dataset(f, decode_times=True)
        sel = d.time.values > t0
        if not sel.any():
            d.close(); continue
        d = d.isel(time=np.where(sel)[0])
        p_hpa = d.level.values * ss.P0_HPA; lat = d.lat.values
        tz = d.temperature.mean("lon").values                    # (time, lev, lat)
        months = d.time.dt.month.values
        if sums is None:
            sums = np.zeros((12,) + tz.shape[1:])
        for m in range(1, 13):
            k = months == m
            if k.any():
                sums[m - 1] += tz[k].sum(0); count[m - 1] += k.sum()
        d.close()
    if (count == 0).any():
        raise SystemExit(f"window lacks months {np.where(count == 0)[0] + 1}")
    tm = sums / count[:, None, None]
    da = xr.DataArray(tm, dims=("month", "level", "lat"), coords={"month": np.arange(1, 13), "level": p_hpa, "lat": lat})
    return sc._interp_logp(da, p_hpa, P_CORR, "level"), lat, (str(t0)[:10], str(t_end)[:10])


def era5_monthly_T(years, lat):
    zm, _ = sc.load_era5(years, lat)
    t = zm["T"].sel(plev=P_CORR)
    return t.groupby("time.month").mean("time")


CLAMS_REA_ZIP = "/data/CLaMS/CLaMS_v3/clams_reanalyses/clams_era5_zm_lat_press.zip"
HEAT_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "era5_ref", "era5_heating_clams_2000-2014.npz")


def era5_monthly_Q(lat):
    """Phase 18: ERA5 total diabatic heating as a temperature tendency Q = theta_dot (p/1000)^kappa [K/day], monthly climatology
    of the CLaMS v3 ERA5 reanalysis files 2000-2014 (``THETA_DOT_TOT``, the vertical velocity CLaMS itself is driven by; its
    units attribute is a placeholder, the values are K/day), on P_CORR x ``lat`` -> (12, len(P_CORR), nlat)."""
    if not os.path.exists(HEAT_CACHE):
        import zipfile, netCDF4
        z = zipfile.ZipFile(CLAMS_REA_ZIP); acc = []
        for n in sorted(x for x in z.namelist() if x.endswith(".nc")):
            d = netCDF4.Dataset(n, memory=z.read(n)); acc.append(np.asarray(d["THETA_DOT_TOT"][:], float))
            p = np.asarray(d["press"][:], float); la = np.asarray(d["lat"][:], float); d.close()
        os.makedirs(os.path.dirname(HEAT_CACHE), exist_ok=True)
        np.savez(HEAT_CACHE, p=p, lat=la, thdot=np.mean(acc, 0), years="2000-2014")
    z = np.load(HEAT_CACHE); p, la = z["p"], z["lat"]
    q = z["thdot"] * (p[None, :, None] / 1000.0) ** 0.2857                  # (12, np, nlat) K/day of T
    o = np.argsort(p); q, p = q[:, o], p[o]
    from jcm_strat.jucker import interpolate_table
    return interpolate_table(q, p, la, P_CORR, lat)


def model_monthly_Q(tm, lat, prev):
    """The model's own Newtonian heating (T_e - T) / tau [K/day] from its monthly-mean T on P_CORR, with the JFV T_e plus the
    correction ``prev`` the run used (monthly means of a linear relaxation; T_e and tau vary slowly within a month)."""
    from jcm_strat.jucker import load_jfv_table, interpolate_table
    _, pj, latj, te, tau = load_jfv_table()
    te_k = interpolate_table(te, pj, latj, P_CORR, lat) + (0.0 if prev is None else prev)
    tau_d = interpolate_table(tau, pj, latj, P_CORR, lat) / 86400.0
    return (te_k - tm) / tau_d, tau_d


def heating_mask(lat, lat_full, lat_zero, p_full, p_zero):
    """1 inside |lat| <= lat_full and p >= p_full (hPa), cos^2 tapers to 0 at lat_zero and (in log p) at p_zero; (len(P_CORR), nlat)."""
    al = np.abs(np.asarray(lat))
    ml = np.where(al <= lat_full, 1.0, np.where(al >= lat_zero, 0.0, np.cos(0.5 * np.pi * (al - lat_full) / (lat_zero - lat_full)) ** 2))
    lp = np.log(P_CORR); x = np.clip((np.log(p_full) - lp) / (np.log(p_full) - np.log(p_zero)), 0.0, 1.0)
    mp = np.cos(0.5 * np.pi * x) ** 2
    return mp[:, None] * ml[None, :]


def smooth121(x, axis, periodic=False):
    x = np.moveaxis(x, axis, -1)
    if periodic:
        y = 0.25 * np.roll(x, 1, -1) + 0.5 * x + 0.25 * np.roll(x, -1, -1)
    else:
        xp = np.concatenate([x[..., :1], x, x[..., -1:]], -1)
        y = 0.25 * xp[..., :-2] + 0.5 * xp[..., 1:-1] + 0.25 * xp[..., 2:]
    return np.moveaxis(y, -1, axis)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("--out", required=True); ap.add_argument("--prev", default=None)
    ap.add_argument("--alpha", type=float, default=0.7); ap.add_argument("--cap", type=float, default=25.0)
    ap.add_argument("--window-years", type=float, default=2.0); ap.add_argument("--era5-years", default="1990-1999")
    # Phase 18: inside a tropical lower-stratosphere mask the target is ERA5's diabatic HEATING, not its temperature:
    # dT_e -= alpha * tau * (Q_model - Q_ERA5); the T target stays outside; cos^2 tapers between
    ap.add_argument("--heating-target", action="store_true")
    ap.add_argument("--heat-lat", type=float, nargs=2, default=(30.0, 40.0), help="full / zero weight |lat| (deg)")
    ap.add_argument("--heat-p", type=float, nargs=2, default=(30.0, 15.0), help="full weight at p >= first, zero at p <= second (hPa)")
    ap.add_argument("--outer-from", default=None, help="Phase 18 first step: take the correction OUTSIDE the mask from this file "
                    "(e.g. Phase 17's converged A4) and start the inside from the run's own heating error")
    a = ap.parse_args()
    y0, y1 = (int(v) for v in a.era5_years.split("-"))
    tm, lat, span = model_monthly_T(a.rundir, a.window_years)
    te = era5_monthly_T(list(range(y0, y1 + 1)), lat)
    diff = (tm - te).transpose("month", "plev", "lat").values        # (12, 11, nlat)
    w = np.cos(np.deg2rad(lat))
    rms_before = float(np.sqrt(np.nansum(w * diff ** 2) / np.sum(w * np.isfinite(diff))))
    def read_corr(path):
        with xr.open_dataset(path) as d:
            return d.dte.sel(pfull=list(P_CORR)).interp(lat=lat).transpose("month", "pfull", "lat").values
    prev = read_corr(a.prev) if a.prev else None
    err = diff                                                # K, the quantity the update drives to zero
    heat_report = None
    if a.heating_target:
        m = heating_mask(lat, a.heat_lat[0], a.heat_lat[1], a.heat_p[0], a.heat_p[1])[None]      # (1, np, nlat)
        qm, tau_d = model_monthly_Q(tm.transpose("month", "plev", "lat").values, lat, prev)
        qe = era5_monthly_Q(lat)
        err = m * tau_d * (qm - qe) + (1.0 - m) * diff     # heating error in K (tau * dQ) inside, T error outside
        inside = (m[0] > 0.5)
        dq = (qm - qe)[:, inside]; wq = np.broadcast_to(np.cos(np.deg2rad(lat))[None, :], m[0].shape)[inside][None, :]
        heat_report = (float(np.sqrt(np.nansum(wq * dq ** 2) / np.sum(wq * np.isfinite(dq)))), qm, qe)
    inc = smooth121(smooth121(err, 2), 2)
    inc = -a.alpha * smooth121(inc, 0, periodic=True)
    inc[:, P_CORR == 100.0, :] = 0.0                          # nudged below; keep the 100 hPa node at zero
    base = prev
    if a.outer_from:
        if not a.heating_target:
            raise SystemExit("--outer-from needs --heating-target")
        base = (1.0 - m[0][None]) * read_corr(a.outer_from) + m[0][None] * (0.0 if prev is None else prev)
        inc = inc * m                                         # outside, the converged file already answers this run's T error
    tot = np.clip(inc + (0.0 if base is None else base), -a.cap, a.cap)
    # vertical extension: zero at 150 hPa and below, taper above 1 hPa to zero at 0.1 hPa
    p_top = np.array([0.01, 0.1, 0.2, 0.3, 0.5, 0.7])
    taper = np.log(p_top / 0.1) / np.log(10.0); taper = np.clip(taper, 0.0, 1.0)
    upper = tot[:, :1, :] * taper[None, :, None]
    p_all = np.concatenate([p_top, P_CORR, [150.0, 1000.0]])
    dte = np.concatenate([upper, tot, np.zeros((12, 2, lat.size))], axis=1)
    ds = xr.Dataset({"dte": (("month", "pfull", "lat"), dte.astype("f8"))},
                    coords={"month": np.arange(1, 13), "pfull": p_all, "lat": lat})
    ds.dte.attrs.update(units="K", long_name="additive correction to the JFV2013 equilibrium temperature")
    ds.attrs.update(source_run=os.path.abspath(a.rundir), window=f"{span[0]}..{span[1]}", era5_years=a.era5_years,
                    alpha=a.alpha, cap=a.cap, prev=str(a.prev), rms_T_error_before=rms_before,
                    heating_target=int(a.heating_target), heat_lat=str(a.heat_lat), heat_p=str(a.heat_p), outer_from=str(a.outer_from),
                    rms_heating_error_inside=(heat_report[0] if heat_report else -1.0))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ds.to_netcdf(a.out)
    # report: error and correction per region
    lev = {p: i for i, p in enumerate(P_CORR)}
    print(f"[teq] {a.rundir} window {span[0]}..{span[1]} vs ERA5 {a.era5_years}: monthly T RMSE 100-1 hPa {rms_before:.2f} K; "
          f"increment {np.nanmin(inc):+.1f}..{np.nanmax(inc):+.1f} K, total {np.nanmin(tot):+.1f}..{np.nanmax(tot):+.1f} K -> {a.out}")
    if heat_report:
        rq, qm, qe = heat_report
        print(f"[teq] heating target inside |lat|<{a.heat_lat[0]:g} (zero at {a.heat_lat[1]:g}), p>={a.heat_p[0]:g} hPa (zero at {a.heat_p[1]:g}): "
              f"monthly heating RMSE inside {rq:.3f} K/day")
        for pl in (70, 50, 30, 20, 10):
            k = lev[pl]
            print(f"[teq]   annual heating at {pl:>3} hPa, lat 0/15/25/35, model | ERA5 [K/d]: " +
                  " ".join(f"{np.interp(l, lat, qm[:, k].mean(0)):+.2f}" for l in (0, 15, 25, 35)) + " | " +
                  " ".join(f"{np.interp(l, lat, qe[:, k].mean(0)):+.2f}" for l in (0, 15, 25, 35)))
    for pl in (1, 5, 10, 30, 70):
        row = tot[:, lev[pl], :].mean(0)
        print(f"[teq]   annual dT_e at {pl:>3} hPa, lat -80/-60/-30/0/30/60/80: " +
              " ".join(f"{np.interp(l, lat, row):+5.1f}" for l in (-80, -60, -30, 0, 30, 60, 80)))


if __name__ == "__main__":
    main()
