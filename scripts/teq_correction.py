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
    a = ap.parse_args()
    y0, y1 = (int(v) for v in a.era5_years.split("-"))
    tm, lat, span = model_monthly_T(a.rundir, a.window_years)
    te = era5_monthly_T(list(range(y0, y1 + 1)), lat)
    diff = (tm - te).transpose("month", "plev", "lat").values        # (12, 11, nlat)
    w = np.cos(np.deg2rad(lat))
    rms_before = float(np.sqrt(np.nansum(w * diff ** 2) / np.sum(w * np.isfinite(diff))))
    inc = smooth121(smooth121(diff, 2), 2)
    inc = -a.alpha * smooth121(inc, 0, periodic=True)
    inc[:, P_CORR == 100.0, :] = 0.0                          # nudged below; keep the 100 hPa node at zero
    prev = None
    if a.prev:
        with xr.open_dataset(a.prev) as d:
            prev = d.dte.sel(pfull=list(P_CORR)).interp(lat=lat).transpose("month", "pfull", "lat").values
    tot = np.clip(inc + (0.0 if prev is None else prev), -a.cap, a.cap)
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
                    alpha=a.alpha, cap=a.cap, prev=str(a.prev), rms_T_error_before=rms_before)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    ds.to_netcdf(a.out)
    # report: error and correction per region
    lev = {p: i for i, p in enumerate(P_CORR)}
    print(f"[teq] {a.rundir} window {span[0]}..{span[1]} vs ERA5 {a.era5_years}: monthly T RMSE 100-1 hPa {rms_before:.2f} K; "
          f"increment {np.nanmin(inc):+.1f}..{np.nanmax(inc):+.1f} K, total {np.nanmin(tot):+.1f}..{np.nanmax(tot):+.1f} K -> {a.out}")
    for pl in (1, 5, 10, 30, 70):
        row = tot[:, lev[pl], :].mean(0)
        print(f"[teq]   annual dT_e at {pl:>3} hPa, lat -80/-60/-30/0/30/60/80: " +
              " ".join(f"{np.interp(l, lat, row):+5.1f}" for l in (-80, -60, -30, 0, 30, 60, 80)))


if __name__ == "__main__":
    main()
