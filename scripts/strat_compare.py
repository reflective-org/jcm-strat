#!/usr/bin/env python3
"""Stratospheric climatology and polar-vortex comparison: model runs vs ERA5 and WACCM6.

    python scripts/strat_compare.py OUTDIR --run LABEL=runs/<session> [--run LABEL=... ] [--years 2005-2005]

Reads chunked jcm output (``longrun_day*.nc``, 5-day means) and compares zonal-mean T and u
above 300 hPa with

  ERA5    monthly zonal means on 25 pressure levels, 1000-1 hPa, and daily zonal-mean u at
          10 hPa, both from the CDS (``scripts/fetch_era5_strat_ref.py`` -> ``cache/era5_ref/``).
  WACCM6  CESM2.1.5 WACCM6 histSST member (1996-2014), monthly T/U (h0) and daily zonal-mean
          U (h6.Uzm); free-running dynamics, so it enters as a same-period climatology with a
          day-of-year envelope, not as a year-matched series. Its hybrid ``lev`` is taken as
          pressure, exact above ~150 hPa (hybm ~ 0).

Outputs (in OUTDIR): ``strat_climatology_<LABEL>.png`` per run (T and u, DJF and JJA, run /
ERA5 / WACCM / run minus ERA5), ``vortex_series.png`` (u at 60N and 60S, 10 hPa, all runs vs
ERA5 vs WACCM envelope, ERA5 SSW central dates marked), ``polar_cap_T.png`` (60-90 deg,
10-50 hPa monthly), and ``strat_metrics.md`` (RMSE of T and u over 100-1 hPa vs ERA5 and vs
WACCM for DJF/JJA/annual, DJF u(60N,10hPa), SSW counts). The model's 5-day means make the
model-side SSW dates uncertain by +-5 days.
"""
from __future__ import annotations

import argparse, glob, os, re, json
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERA5_DIR = os.path.join(REPO, "cache", "era5_ref")
WACCM_DIR = ("/data/cesm2.1.5_output/histSST/f.e21.FWHIST.f09_f09_mg17.atmos-scale_fixedSST_1996-2014.001"
             "/archive/atm/proc/tseries")
P_LEVELS = np.array([1, 2, 3, 5, 7, 10, 20, 30, 50, 70, 100, 125, 150, 175, 200, 225, 250, 300.0])
P0_HPA = 1013.25
SEASONS = {"DJF": (12, 1, 2), "JJA": (6, 7, 8)}


# ----------------------------------------------------------------------------- loading
def _interp_logp(da, p_src, p_dst, dim):
    """Linear interpolation in log-pressure along `dim` (both axes in hPa)."""
    da = da.assign_coords({dim: np.log(np.asarray(p_src, dtype=float))}).sortby(dim)
    out = da.interp({dim: np.log(p_dst)}, kwargs={"fill_value": np.nan})
    return out.assign_coords({dim: p_dst}).rename({dim: "plev"})


def load_model(rundir, lat_out):
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")),
                   key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not files:
        raise SystemExit(f"no longrun_day*.nc in {rundir}")
    ds = xr.open_mfdataset(files, combine="by_coords", decode_times=True)[["temperature", "u_wind"]]
    zm = ds.mean("lon").rename(temperature="T", u_wind="u").sortby("lat")
    zm = zm.assign_coords(lat=zm.lat.values)
    zm = zm.interp(lat=lat_out) if not np.allclose(zm.lat.values, lat_out) else zm
    p = zm.level.values * P0_HPA
    zm = _interp_logp(zm, p, P_LEVELS, "level")
    zm = zm.sortby("time").load()
    zm["time"] = xr.DataArray(zm.indexes["time"].to_datetimeindex() if hasattr(zm.indexes["time"], "to_datetimeindex")
                              else zm.indexes["time"], dims="time")
    return zm


def load_era5(years, lat_out):
    files = [os.path.join(ERA5_DIR, f"era5_zm_monthly_{y}.nc") for y in years]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return None, None
    ds = xr.open_mfdataset(files, combine="by_coords", decode_times=True)
    tname = [c for c in ds.coords if c.startswith("time") or c == "valid_time"][0]
    zm = ds.rename({"tzm": "T", "uzm": "u", tname: "time"}).interp(lat=lat_out)
    zm = _interp_logp(zm, zm.level.values, P_LEVELS, "level").load()
    dfiles = [os.path.join(ERA5_DIR, f"era5_u10hPa_daily_{y}.nc") for y in years]
    dfiles = [f for f in dfiles if os.path.exists(f)]
    daily = xr.open_mfdataset(dfiles, combine="by_coords")["uzm_10hPa"].load() if dfiles else None
    return zm, daily


def load_waccm(years, lat_out):
    def tseries(kind, var):
        pat = os.path.join(WACCM_DIR, kind, f"*.{var}.*.nc")
        fs = glob.glob(pat)
        return xr.open_dataset(fs[0], decode_times=True, use_cftime=True) if fs else None
    T = tseries("month_1", "h0.T"); U = tseries("month_1", "h0.U")
    if T is None or U is None:
        return None, None
    sel = lambda d: d.sel(time=[t for t in d.time.values if t.year in years])
    zm = xr.Dataset({"T": sel(T)["T"].mean("lon"), "u": sel(U)["U"].mean("lon")}).interp(lat=lat_out)
    zm = _interp_logp(zm, zm.lev.values, P_LEVELS, "lev")
    # cftime noleap -> month/year labels only (used for seasonal means)
    zm = zm.assign_coords(month=("time", [t.month for t in zm.time.values]),
                          year=("time", [t.year for t in zm.time.values])).load()
    Uzm = tseries("day_1", "h6.Uzm")
    daily = None
    if Uzm is not None:
        u = Uzm["Uzm"].isel(zlon=0) if "zlon" in Uzm["Uzm"].dims else Uzm["Uzm"]
        vdim = "ilev" if "ilev" in u.dims else "lev"          # the zonal-mean tapes sit on interfaces
        u10 = _interp_logp(u, Uzm[vdim].values, np.array([10.0]), vdim).isel(plev=0)
        daily = u10.interp(lat=[60.0, -60.0]).assign_coords(
            doy=("time", [t.dayofyr for t in u10.time.values])).load()
    return zm, daily


# ----------------------------------------------------------------------------- helpers
def season_mean(zm, months, month_coord=None):
    m = zm[month_coord] if month_coord else zm.time.dt.month
    return zm.where(m.isin(list(months)), drop=True).mean("time")


def rmse(a, b, lat, pmin=1.0, pmax=100.0):
    d = (a - b).sel(plev=slice(pmin, pmax))
    w = np.cos(np.deg2rad(lat)) * xr.ones_like(d)
    w = w.where(d.notnull())
    return float(np.sqrt((w * d ** 2).sum() / w.sum()))


def ssw_dates(u60n, times, min_sep_days=20):
    """Charlton-Polvani-style central dates: first easterly day Nov-Mar, >= 20 d apart,
    not a final warming (westerlies must return for 10 consecutive days before 30 April)."""
    t = np.asarray(times).astype("datetime64[D]"); u = np.asarray(u60n)
    events, last = [], None
    for i in range(1, len(t)):
        month = int(str(t[i])[5:7])
        if u[i] < 0 <= u[i - 1] and month in (11, 12, 1, 2, 3):
            if last is not None and (t[i] - last).astype(int) < min_sep_days:
                continue
            # final-warming check: 10 consecutive westerly days before 30 April of that winter
            yr = int(str(t[i])[:4]) + (1 if month >= 11 else 0)
            end = np.datetime64(f"{yr}-04-30")
            sel = (t > t[i]) & (t <= end)
            after, ta = u[sel], t[sel]
            # count westerly *days*, not samples, so 5-day model means and daily ERA5 behave alike
            run_start = None; ok = False
            for v, tt in zip(after, ta):
                if v > 0:
                    run_start = tt if run_start is None else run_start
                    if (tt - run_start).astype(int) >= 10: ok = True; break
                else:
                    run_start = None
            if ok:
                events.append(t[i]); last = t[i]
    return events


# ----------------------------------------------------------------------------- plots
def plot_climatology(label, model, era5, waccm, outdir, extra=None):
    """extra: optional (name, dataset) shown as one more reference row (e.g. the full-ECHAM year)."""
    cols = [("T", "DJF"), ("u", "DJF"), ("T", "JJA"), ("u", "JJA")]
    rows = [("model: " + label, model, None), ("ERA5", era5, None), ("WACCM6 histSST", waccm, "month")]
    if extra is not None:
        rows.append((extra[0], extra[1], None))
    nref = len(rows)
    rows.append(("model - ERA5", None, None))
    fig, axes = plt.subplots(len(rows), 4, figsize=(18, 3.75 * len(rows)), sharex=True, sharey=True)
    for j, (var, seas) in enumerate(cols):
        fields = {}
        for i, (name, ds, mc) in enumerate(rows[:nref]):
            if ds is None: continue
            fields[name] = season_mean(ds[var], SEASONS[seas], mc)
        for i, (name, ds, mc) in enumerate(rows):
            ax = axes[i, j]
            if i < nref:
                if name not in fields: ax.set_axis_off(); continue
                f = fields[name]
                if var == "T":
                    cf = ax.contourf(f.lat, f.plev, f, levels=np.arange(180, 301, 10), cmap="RdYlBu_r", extend="both")
                else:
                    cf = ax.contourf(f.lat, f.plev, f, levels=np.arange(-80, 81, 10), cmap="RdBu_r", extend="both")
                    ax.contour(f.lat, f.plev, f, levels=[0], colors="k", linewidths=0.8)
            else:
                if "model: " + label not in fields or "ERA5" not in fields: ax.set_axis_off(); continue
                d = fields["model: " + label] - fields["ERA5"]
                lv = np.arange(-30, 31, 5) if var == "T" else np.arange(-40, 41, 5)
                cf = ax.contourf(d.lat, d.plev, d, levels=lv, cmap="RdBu_r", extend="both")
            ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylim(300, 1)
            if i == 0: ax.set_title(f"{'temperature [K]' if var == 'T' else 'zonal wind [m/s]'}  {seas}")
            if j == 0: ax.set_ylabel(f"{name}\npressure [hPa]")
            if i == len(rows) - 1: ax.set_xlabel("latitude")
            plt.colorbar(cf, ax=ax, shrink=0.85)
    fig.suptitle(f"Zonal-mean stratosphere, {label} vs ERA5 and WACCM6 (300-1 hPa)")
    fig.tight_layout(); out = os.path.join(outdir, f"strat_climatology_{label}.png"); fig.savefig(out, dpi=110); plt.close(fig)
    print("wrote", out)


def plot_climatology_panel(models, era5, waccm, outdir, fname="strat_climatology_panel.png"):
    """One figure, one row per model version (in the given order) followed by ERA5 and WACCM6."""
    cols = [("T", "DJF"), ("u", "DJF"), ("T", "JJA"), ("u", "JJA")]
    rows = [(name, ds, None) for name, ds in models.items()]
    if era5 is not None: rows.append(("ERA5", era5, None))
    if waccm is not None: rows.append(("WACCM6 histSST", waccm, "month"))
    fig, axes = plt.subplots(len(rows), 4, figsize=(18, 3.6 * len(rows)), sharex=True, sharey=True)
    for j, (var, seas) in enumerate(cols):
        for i, (name, ds, mc) in enumerate(rows):
            ax = axes[i, j]
            f = season_mean(ds[var], SEASONS[seas], mc)
            if var == "T":
                cf = ax.contourf(f.lat, f.plev, f, levels=np.arange(180, 301, 10), cmap="RdYlBu_r", extend="both")
            else:
                cf = ax.contourf(f.lat, f.plev, f, levels=np.arange(-80, 81, 10), cmap="RdBu_r", extend="both")
                ax.contour(f.lat, f.plev, f, levels=[0], colors="k", linewidths=0.8)
            ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylim(300, 1)
            if i == 0: ax.set_title(f"{'temperature [K]' if var == 'T' else 'zonal wind [m/s]'}  {seas}")
            if j == 0: ax.set_ylabel(f"{name}\npressure [hPa]")
            if i == len(rows) - 1: ax.set_xlabel("latitude")
            plt.colorbar(cf, ax=ax, shrink=0.85)
    fig.suptitle("Zonal-mean stratosphere, 300-1 hPa: model versions against ERA5 and WACCM6")
    fig.tight_layout(); out = os.path.join(outdir, fname); fig.savefig(out, dpi=110); plt.close(fig)
    print("wrote", out)


def plot_vortex(models, era5_daily, waccm_daily, outdir, years):
    fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
    ssws = []
    for ax, lat0, hemi in ((axes[0], 60.0, "60N"), (axes[1], -60.0, "60S")):
        if waccm_daily is not None:
            w = waccm_daily.sel(lat=lat0)
            clim = w.groupby("doy").mean(); sd = w.groupby("doy").std()
            yrs = list(years)                    # paint the climatological envelope on every run year
            for y in yrs:
                days = np.arange(np.datetime64(f"{y}-01-01"), np.datetime64(f"{y + 1}-01-01"))
                doy = np.minimum(np.arange(1, len(days) + 1), 365)
                ax.fill_between(days, clim.sel(doy=doy).values - sd.sel(doy=doy).values,
                                clim.sel(doy=doy).values + sd.sel(doy=doy).values, color="0.85",
                                label="WACCM6 1996-2014 day-of-year mean ± 1σ" if y == yrs[0] else None)
                ax.plot(days, clim.sel(doy=doy).values, color="0.5", lw=0.8)
        if era5_daily is not None:
            e = era5_daily.interp(lat=lat0)
            ax.plot(e.time, e, color="k", lw=1.0, label="ERA5 daily")
            if lat0 > 0:
                ssws = ssw_dates(e.values, e.time.values)
                for d in ssws: ax.axvline(d, color="r", ls="--", lw=0.8)
        for name, m in models.items():
            u = m["u"].sel(plev=10.0).interp(lat=lat0)
            ax.plot(u.time, u, lw=1.4, label=f"{name} (5-day means)")
        ax.axhline(0, color="k", lw=0.5); ax.set_ylabel(f"u {hemi}, 10 hPa [m/s]"); ax.grid(alpha=0.3)
    axes[0].legend(loc="upper left", fontsize=8, ncol=2)
    axes[0].set_title("Polar-vortex zonal wind at 10 hPa; red dashed: ERA5 SSW central dates (60N reversal, Nov-Mar)")
    fig.tight_layout(); out = os.path.join(outdir, "vortex_series.png"); fig.savefig(out, dpi=110); plt.close(fig)
    print("wrote", out)
    return ssws


def polar_cap(zm, hemi, month_coord=None):
    lat = zm.lat
    sel = zm["T"].sel(plev=slice(10, 50)).where((lat >= 60) if hemi == "N" else (lat <= -60), drop=True)
    w = np.cos(np.deg2rad(sel.lat))
    cap = (sel * w).sum("lat") / w.sum()
    return cap.mean("plev")


def plot_polar_cap(models, era5, waccm, outdir, years):
    fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
    for ax, hemi in ((axes[0], "N"), (axes[1], "S")):
        if era5 is not None:
            c = polar_cap(era5, hemi); ax.plot(c.time, c, "k", lw=1.5, label="ERA5 monthly")
        if waccm is not None:
            c = polar_cap(waccm, hemi).groupby("month").mean()
            yrs = list(years)
            times = [np.datetime64(f"{y}-{mm:02d}-15") for y in yrs for mm in range(1, 13)]
            vals = [float(c.sel(month=mm)) for y in yrs for mm in range(1, 13)]
            ax.plot(times, vals, color="0.5", lw=1.2, label="WACCM6 same-period monthly climatology")
        for name, m in models.items():
            c = polar_cap(m, hemi); ax.plot(c.time, c, lw=1.4, label=name)
        ax.set_ylabel(f"polar-cap T {hemi}, 60-90°, 10-50 hPa [K]"); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8, ncol=2); axes[0].set_title("Polar-cap temperature")
    fig.tight_layout(); out = os.path.join(outdir, "polar_cap_T.png"); fig.savefig(out, dpi=110); plt.close(fig)
    print("wrote", out)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir"); ap.add_argument("--run", action="append", required=True, help="LABEL=rundir")
    ap.add_argument("--years", default=None, help="e.g. 2005-2009; default: the first run's years")
    ap.add_argument("--climatology-for", default=None,
                    help="comma-separated run labels that get a climatology figure (default: all)")
    ap.add_argument("--panel", action="store_true",
                    help="also draw one figure with every --run as a row, then ERA5 and WACCM6 (strat_climatology_panel.png)")
    ap.add_argument("--extra-row", default=None,
                    help="LABEL=rundir: a run shown as an additional reference row in every climatology figure")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    runs = dict(r.split("=", 1) for r in a.run)
    first = xr.open_dataset(sorted(glob.glob(os.path.join(list(runs.values())[0], "longrun_day*.nc")))[0])
    lat_out = np.sort(first.lat.values)
    models = {k: load_model(v, lat_out) for k, v in runs.items()}
    if a.years:
        y0, y1 = map(int, a.years.split("-")); years = list(range(y0, y1 + 1))
    else:
        t = list(models.values())[0].time.values; years = sorted({int(str(x)[:4]) for x in t})
    era5, era5_daily = load_era5(years, lat_out)
    waccm, waccm_daily = load_waccm(years, lat_out)
    print("years", years, "| ERA5:", era5 is not None, "| WACCM:", waccm is not None)

    lines = ["| run | ref | season | RMSE T 100-1 hPa [K] | RMSE u 100-1 hPa [m/s] | u(60N,10hPa) DJF [m/s] | u(60S,10hPa) JJA [m/s] |",
             "|---|---|---|---|---|---|---|"]
    clim_for = set(a.climatology_for.split(",")) if a.climatology_for else set(models)
    extra = None
    if a.extra_row:
        xl, xd = a.extra_row.split("=", 1)
        extra = (xl, load_model(xd, lat_out))
    for name, m in models.items():
        if name in clim_for:
            plot_climatology(name, m, era5, waccm, a.outdir, extra=extra)
    if a.panel:
        plot_climatology_panel(models, era5, waccm, a.outdir)
        for refname, ref, mc in (("ERA5", era5, None), ("WACCM6", waccm, "month")):
            if ref is None: continue
            for seas in ("DJF", "JJA", "annual"):
                if seas == "annual":
                    mm, rr = m.mean("time"), ref.mean("time")
                else:
                    mm, rr = season_mean(m, SEASONS[seas]), season_mean(ref, SEASONS[seas], mc)
                un = float(mm["u"].sel(plev=10).interp(lat=60)); us = float(mm["u"].sel(plev=10).interp(lat=-60))
                rn = float(rr["u"].sel(plev=10).interp(lat=60)); rs = float(rr["u"].sel(plev=10).interp(lat=-60))
                lines.append(f"| {name} | {refname} | {seas} | {rmse(mm['T'], rr['T'], mm.lat):.1f} | "
                             f"{rmse(mm['u'], rr['u'], mm.lat):.1f} | {un:.0f} (ref {rn:.0f}) | {us:.0f} (ref {rs:.0f}) |")
    ssws = plot_vortex(models, era5_daily, waccm_daily, a.outdir, years)
    plot_polar_cap(models, era5, waccm, a.outdir, years)
    lines.append("")
    lines.append(f"ERA5 SSW central dates (60N, 10 hPa reversal, Nov-Mar, not final warmings): "
                 f"{', '.join(str(d) for d in ssws) if ssws else 'none / no daily ERA5'}")
    for name, m in models.items():
        u = m["u"].sel(plev=10.0).interp(lat=60.0)
        ev = ssw_dates(u.values, u.time.values)
        lines.append(f"{name} SSW-like reversals (5-day means, +-5 d): {', '.join(str(d) for d in ev) if ev else 'none'}")
    md = "\n".join(lines); print(md)
    with open(os.path.join(a.outdir, "strat_metrics.md"), "w") as f: f.write(md + "\n")


if __name__ == "__main__":
    main()
