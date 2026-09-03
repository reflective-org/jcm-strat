#!/usr/bin/env python3
"""Stratospheric circulation diagnostics of a chunked jcm-strat run: QBO, SAO, Brewer-Dobson.

    python scripts/strat_circulation.py runs/<run> OUTDIR [--years 2005-2009] [--label NAME]

1. QBO / SAO. Equatorial (5S-5N) zonal-mean zonal wind as a time-height section, 100-1 hPa,
   for the run, ERA5 (monthly, CDS) and WACCM6 histSST (monthly h0 U); deseasonalised standard
   deviation at 10/20/30/50 hPa (the QBO signal, ~15-20 m/s in ERA5) and the amplitude of the
   semiannual harmonic at 1-3 hPa (the SAO).
2. Brewer-Dobson circulation. TEM residual meridional velocity in pressure coordinates,
   v* = [v] - d/dp( [v'th'] / d[th]/dp ), from the run's 5-day-mean fields (eddy covariances of
   the 5-day means, i.e. stationary and slow transient waves) and from WACCM6's daily zonal-mean
   TEM tape (Vzm, VTHzm, THzm on ilev). Residual mass streamfunction
   Psi*(phi, p) = (2 pi a cos(phi) / g) * integral_0^p v* dp', DJF / JJA / annual, and the
   tropical upward mass flux at 70 and 100 hPa (max - min of Psi* over latitude), the standard
   BDC strength metric (WACCM6 1996-2014 at 70 hPa: 8.8-10.1 x 10^9 kg/s in the AIDE validation).
3. Tropical ascent from age of air: mean age 10S-10N at 70/50/30/20/10 hPa for the run, CLaMS
   (surface clock) and WACCM6 REF-D1 (entry age); the 70 -> 10 hPa transit time and the implied
   mean ascent rate, dz / d(age) with z = 7 km ln(1000/p).

Outputs: qbo_time_height.png, tem_streamfunction.png, circulation_metrics.md.
"""
from __future__ import annotations

import argparse, glob, os, re, sys
import numpy as np
import xarray as xr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_compare as sc                      # loaders shared with the climatology comparison
import aoa_vs_clams as aoa

A_EARTH, G, KAPPA, P0_HPA = 6.371e6, 9.80665, 0.2857, 1013.25
WACCM_DAY = os.path.join(sc.WACCM_DIR, "day_1")


# ----------------------------------------------------------------------------- helpers
def band_mean(da, lat_name="lat", lo=-5.0, hi=5.0):
    sel = da.where((da[lat_name] >= lo) & (da[lat_name] <= hi), drop=True)
    w = np.cos(np.deg2rad(sel[lat_name]))
    return (sel * w).sum(lat_name) / w.sum()


def deseasonalised_std(u_month, plev_targets):
    """u_month: (time, plev) monthly means with a 'month' coordinate; returns {p: std}."""
    anom = u_month.groupby("month") - u_month.groupby("month").mean()
    return {p: float(anom.sel(plev=p, method="nearest").std()) for p in plev_targets}


def semiannual_amplitude(u_month, plev_targets):
    clim = u_month.groupby("month").mean()
    m = clim.month.values
    out = {}
    for p in plev_targets:
        c = clim.sel(plev=p, method="nearest").values
        out[p] = float(2 * abs(np.mean(c * np.exp(-1j * 4 * np.pi * (m - 0.5) / 12))))
    return out


def tem_streamfunction(vbar, vth, thbar, p_pa, lat_deg):
    """vbar, vth, thbar: (p, lat) arrays on pressure p_pa (Pa, any order). Returns v* and Psi* (kg/s),
    both on p sorted ascending (top first)."""
    order = np.argsort(p_pa); p = p_pa[order]
    vbar, vth, thbar = vbar[order], vth[order], thbar[order]
    dth_dp = np.gradient(thbar, p, axis=0)
    dth_dp = np.where(np.abs(dth_dp) < 1e-6, np.sign(dth_dp + 1e-30) * 1e-6, dth_dp)
    flux = vth / dth_dp
    vstar = vbar - np.gradient(flux, p, axis=0)
    cosphi = np.cos(np.deg2rad(lat_deg))[None, :]
    # cumulative trapezoid from the top
    integrand = vstar * cosphi
    psi = np.zeros_like(vstar)
    psi[1:] = np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(p)[:, None], axis=0)
    psi *= 2 * np.pi * A_EARTH / G
    return p, vstar, psi


def upward_mass_flux(p, psi, p_target_hpa, lat_deg, lat_max=60.0):
    i = int(np.argmin(np.abs(p / 100.0 - p_target_hpa)))
    row = psi[i][np.abs(lat_deg) <= lat_max]
    return float(row.max() - row.min())


# ----------------------------------------------------------------------------- model TEM
def model_tem_fields(rundir):
    """Per 5-day save: zonal means of v and theta and the zonal eddy covariance v'theta'."""
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))
    vb, vth, thb, times = [], [], [], []
    for f in files:
        d = xr.open_dataset(f, decode_times=True)
        p_hpa = d.level.values * P0_HPA
        theta = d.temperature * (1000.0 / p_hpa)[None, :, None, None] ** KAPPA
        v = d.v_wind
        vbar = v.mean("lon"); thbar = theta.mean("lon")
        cov = ((v - vbar) * (theta - thbar)).mean("lon")
        vb.append(vbar.values); thb.append(thbar.values); vth.append(cov.values); times.append(d.time.values)
        d.close()
    t = np.concatenate(times)
    lat = d.lat.values if "lat" in d else xr.open_dataset(files[0]).lat.values
    mk = lambda arr: xr.DataArray(np.concatenate(arr), dims=("time", "level", "lat"), coords={"time": t, "level": p_hpa * 100.0, "lat": lat})
    return mk(vb), mk(vth), mk(thb)


def waccm_tem_fields(years):
    def tape(var):
        f = glob.glob(os.path.join(WACCM_DAY, f"*.h6.{var}.*.nc"))[0]
        d = xr.open_dataset(f, decode_times=True, use_cftime=True)
        x = d[var].isel(zlon=0) if "zlon" in d[var].dims else d[var]
        x = x.sel(time=[tt for tt in x.time.values if tt.year in years])
        return x.rename({"ilev": "level"}).assign_coords(level=x.ilev.values * 100.0)
    v, vth, th = tape("Vzm"), tape("VTHzm"), tape("THzm")
    month = xr.DataArray([tt.month for tt in v.time.values], dims="time")
    return v.assign_coords(month=month), vth.assign_coords(month=month), th.assign_coords(month=month)


def seasonal(da, months, month_coord=None):
    m = da[month_coord] if month_coord else da.time.dt.month
    return da.where(m.isin(list(months)), drop=True).mean("time")


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--label", default=None)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = map(int, a.years.split("-")); years = list(range(y0, y1 + 1))
    label = a.label or os.path.basename(a.rundir.rstrip("/"))
    lines = [f"# Stratospheric circulation diagnostics: {label}, {a.years}", ""]

    # ---------------- 1. QBO / SAO
    first = xr.open_dataset(sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")))[0])
    lat_out = np.sort(first.lat.values)
    model = sc.load_model(a.rundir, lat_out)
    era5, _ = sc.load_era5(years, lat_out)
    waccm, _ = sc.load_waccm(years, lat_out)

    def eq_monthly(ds, month_coord=None):
        u = band_mean(ds["u"])
        if month_coord is None:
            um = u.resample(time="1MS").mean()
            tdec = np.array([t.year + (t.month - 0.5) / 12 for t in um.indexes["time"]])
            month = um.time.dt.month.values
        else:
            um = u; tdec = np.array([yy + (mm - 0.5) / 12 for yy, mm in zip(ds["year"].values, ds["month"].values)]); month = ds["month"].values
        return um.assign_coords(tdec=("time", tdec), month=("time", month))
    eq = {"model: " + label: eq_monthly(model)}
    if era5 is not None: eq["ERA5"] = eq_monthly(era5)
    if waccm is not None: eq["WACCM6 histSST (free-running, same years)"] = eq_monthly(waccm, "month")

    fig, axes = plt.subplots(len(eq), 1, figsize=(14, 3.2 * len(eq)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, (name, um) in zip(axes, eq.items()):
        um = um.sortby("tdec")
        cf = ax.contourf(um.tdec, um.plev, um.T, levels=np.arange(-40, 41, 5), cmap="RdBu_r", extend="both")
        ax.contour(um.tdec, um.plev, um.T, levels=[0], colors="k", linewidths=0.6)
        ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylim(100, 1); ax.set_ylabel(f"{name}\npressure [hPa]")
        plt.colorbar(cf, ax=ax, label="u 5S-5N [m/s]")
    axes[-1].set_xlabel("year")
    axes[0].set_title("Equatorial zonal-mean zonal wind, 5S-5N: the QBO (20-50 hPa) and the SAO (1-3 hPa)")
    fig.tight_layout(); out = os.path.join(a.outdir, "qbo_time_height.png"); fig.savefig(out, dpi=120); plt.close(fig); print("wrote", out)

    lines += ["## QBO and SAO (equatorial zonal wind, 5S-5N)", "",
              "| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |",
              "|---|---|---|---|"]
    for name, um in eq.items():
        q = deseasonalised_std(um, (10, 20, 30, 50)); s = semiannual_amplitude(um, (1, 2, 3))
        mean = {p: float(um.sel(plev=p, method="nearest").mean()) for p in (20, 30)}
        lines.append(f"| {name} | {q[10]:.1f} / {q[20]:.1f} / {q[30]:.1f} / {q[50]:.1f} | {s[1]:.1f} / {s[2]:.1f} / {s[3]:.1f} | {mean[20]:.0f} / {mean[30]:.0f} |")

    # ---------------- 2. TEM residual circulation
    vb, vth, thb = model_tem_fields(a.rundir)
    wv, wvth, wth = waccm_tem_fields(years)
    seasons = {"DJF": (12, 1, 2), "JJA": (6, 7, 8), "annual": tuple(range(1, 13))}
    results = {}
    for src, (V, VTH, TH, mc) in {"model: " + label: (vb, vth, thb, None), "WACCM6 histSST": (wv, wvth, wth, "month")}.items():
        for seas, months in seasons.items():
            vbar = seasonal(V, months, mc); cov = seasonal(VTH, months, mc); th = seasonal(TH, months, mc)
            p, vstar, psi = tem_streamfunction(vbar.values, cov.values, th.values, V.level.values, V.lat.values)
            results[(src, seas)] = (p, V.lat.values, vstar, psi)
    fig, axes = plt.subplots(2, 3, figsize=(17, 9), sharex=True, sharey=True)
    for i, src in enumerate([k[0] for k in results][::3]):
        for j, seas in enumerate(seasons):
            p, lat, vstar, psi = results[(src, seas)]
            ax = axes[i, j]
            lv = np.array([-40, -20, -10, -5, -2, -1, -0.5, -0.2, 0.2, 0.5, 1, 2, 5, 10, 20, 40]) * 1e9
            cf = ax.contourf(lat, p / 100.0, psi, levels=lv, cmap="RdBu_r", extend="both", norm=matplotlib.colors.SymLogNorm(linthresh=2e8, vmin=-4e10, vmax=4e10))
            ax.contour(lat, p / 100.0, psi, levels=[0], colors="k", linewidths=0.6)
            ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylim(300, 1)
            if i == 0: ax.set_title(f"residual mass streamfunction Psi*  {seas}")
            if j == 0: ax.set_ylabel(f"{src}\npressure [hPa]")
            if i == 1: ax.set_xlabel("latitude")
            plt.colorbar(cf, ax=ax, shrink=0.85, label="kg/s")
    fig.suptitle("Brewer-Dobson circulation: TEM residual streamfunction (red: clockwise, i.e. poleward flow in the north above the cell centre)")
    fig.tight_layout(); out = os.path.join(a.outdir, "tem_streamfunction.png"); fig.savefig(out, dpi=115); plt.close(fig); print("wrote", out)

    lines += ["", "## Brewer-Dobson circulation (TEM residual streamfunction)", "",
              "Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means "
              "(stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.", "",
              "| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |", "|---|---|---|---|---|---|"]
    for (src, seas), (p, lat, vstar, psi) in results.items():
        f = [upward_mass_flux(p, psi, ph, lat) / 1e9 for ph in (70, 100, 30, 10)]
        lines.append(f"| {src} | {seas} | {f[0]:.1f} | {f[1]:.1f} | {f[2]:.1f} | {f[3]:.2f} |")

    # ---------------- 3. tropical ascent from age of air
    pm, latm, am, _ = aoa.model_age(a.rundir)
    pc, latc, ac = aoa.clams_age(years)
    pw, latw, aw = aoa.waccm_age(years)
    def trop(p, lat, age, targets):
        sel = np.abs(lat) <= 10
        prof = np.nanmean(age[:, sel], axis=1)
        return {t: float(np.interp(np.log(t), np.log(p[np.argsort(p)]), prof[np.argsort(p)])) for t in targets}
    targets = (70, 50, 30, 20, 10)
    tm, tc, tw = trop(pm, latm, am, targets), trop(pc, latc, ac, targets), trop(pw, latw, aw, targets)
    dz = 7.0 * np.log(70 / 10)                                    # km between 70 and 10 hPa
    lines += ["", "## Tropical ascent from age of air (10S-10N)", "",
              "| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |", "|---|---|---|---|"]
    for name, t in (("model: " + label, tm), ("CLaMS v3.1 / ERA5 (surface clock)", tc), ("WACCM6 REF-D1 (entry age)", tw)):
        tr = t[10] - t[70]; w = dz * 1e6 / (tr * 365.25 * 86400) if tr > 0 else float("nan")
        lines.append(f"| {name} | {t[70]:.2f} / {t[50]:.2f} / {t[30]:.2f} / {t[20]:.2f} / {t[10]:.2f} | {tr:.2f} | {w:.2f} |")

    md = "\n".join(lines); print(md)
    with open(os.path.join(a.outdir, "circulation_metrics.md"), "w") as fh: fh.write(md + "\n")


if __name__ == "__main__":
    main()
