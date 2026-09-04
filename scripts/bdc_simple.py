#!/usr/bin/env python3
"""The Brewer-Dobson circulation in one simple figure.

    python scripts/bdc_simple.py runs/<run> OUT.png [--years 2005-2009] [--label NAME]

Top row: zonal-mean injection tracer ``sai`` (constant source 15S-15N, 25-55 hPa) after 3 months,
1, 2 and 5 years. A Brewer-Dobson circulation lifts the plume in the tropics, carries it poleward
in the middle stratosphere and brings it down over the winter poles; without one the plume would
only diffuse in place. Bottom: tropical upward mass flux at 70 hPa month by month (TEM residual
streamfunction, max - min over |lat| <= 60), the run against WACCM6 histSST for the same years,
with the ERA5-based literature range shaded. The annual cycle (strongest in boreal winter) and the
magnitude (6-8 x 10^9 kg/s) are the two things to check.
"""
from __future__ import annotations

import argparse, glob, os, re, sys
import numpy as np
import xarray as xr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_circulation as circ

C = {"blue": "#2a78d6", "orange": "#eb6834", "muted": "#52514e", "grid": "#e6e5e2", "ink": "#0b0b0b"}


def monthly_upflux(V, VTH, TH, month_coord=None, p_hpa=70.0):
    """Monthly mean fields -> upward mass flux per month (10^9 kg/s), with a decimal-year axis."""
    if month_coord is None:
        Vm, VTHm, THm = (x.resample(time="1MS").mean() for x in (V, VTH, TH))
        tdec = np.array([t.year + (t.month - 0.5) / 12 for t in Vm.indexes["time"]])
    else:
        ym = np.array([t.year * 100 + t.month for t in V.time.values])
        keys = np.unique(ym)
        Vm = xr.concat([V.isel(time=np.where(ym == k)[0]).mean("time") for k in keys], "time")
        VTHm = xr.concat([VTH.isel(time=np.where(ym == k)[0]).mean("time") for k in keys], "time")
        THm = xr.concat([TH.isel(time=np.where(ym == k)[0]).mean("time") for k in keys], "time")
        tdec = np.array([k // 100 + ((k % 100) - 0.5) / 12 for k in keys])
    out = []
    for i in range(Vm.sizes["time"]):
        p, vstar, psi = circ.tem_streamfunction(Vm.isel(time=i).values, VTHm.isel(time=i).values, THm.isel(time=i).values,
                                                V.level.values, V.lat.values)
        out.append(circ.upward_mass_flux(p, psi, p_hpa, V.lat.values) / 1e9)
    return tdec, np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("out")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--label", default=None)
    a = ap.parse_args()
    y0, y1 = map(int, a.years.split("-")); years = list(range(y0, y1 + 1))
    label = a.label or os.path.basename(a.rundir.rstrip("/"))

    files = sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")), key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))
    sai = xr.open_mfdataset(files, combine="nested", concat_dim="time", decode_times=False, data_vars=["sai"])["sai"]
    p_hpa = sai.level.values * 1013.25
    days = []
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]; starts = [0] + ends[:-1]
    for f, s0, s1 in zip(files, starts, ends):
        with xr.open_dataset(f, decode_times=False) as d: n = d.sizes["time"]
        days.extend(s0 + (s1 - s0) / n * (j + 1) for j in range(n))
    days = np.array(days)

    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.15, 1], hspace=0.38, wspace=0.3)
    snaps = [(90, "3 months"), (365, "1 year"), (730, "2 years"), (days[-1], f"{days[-1] / 365.25:.0f} years")]
    vmax = None
    for j, (d0, title) in enumerate(snaps):
        i = int(np.argmin(np.abs(days - d0)))
        zm = sai.isel(time=i).mean("lon").values                     # (lev, lat)
        if vmax is None: vmax = float(np.nanmax(sai.isel(time=int(np.argmin(np.abs(days - 365)))).mean("lon").values))
        ax = fig.add_subplot(gs[0, j])
        cf = ax.contourf(sai.lat, p_hpa, zm, levels=np.linspace(0, vmax, 13), cmap="YlOrRd", extend="max")
        ax.contour(sai.lat, p_hpa, zm, levels=[0.05 * vmax], colors=C["ink"], linewidths=0.8)
        ax.set_yscale("log"); ax.invert_yaxis(); ax.set_ylim(300, 1)
        ax.axhspan(25, 55, xmin=(75 - 15) / 180 + 0.02, xmax=(90 + 15) / 180 - 0.02, color="none", ec=C["muted"], ls="--", lw=0.8)
        ax.set_title(f"injection tracer after {title}", fontsize=10)
        ax.set_xlabel("latitude"); ax.grid(True, color=C["grid"], lw=0.6)
        if j == 0: ax.set_ylabel("pressure [hPa]")
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    plt.colorbar(cf, ax=fig.axes[:4], shrink=0.8, pad=0.01, label="zonal-mean sai (mixing ratio, arbitrary)")
    fig.text(0.5, 0.93, "Top: the plume injected at 15S-15N, 25-55 hPa (dashed box) is lifted in the tropics, carried poleward and brought down over the winter poles: the Brewer-Dobson circulation at work",
             ha="center", fontsize=9.5, color=C["muted"])

    ax = fig.add_subplot(gs[1, :])
    vb, vth, thb = circ.model_tem_fields(a.rundir)
    t_m, f_m = monthly_upflux(vb, vth, thb)
    wv, wvth, wth = circ.waccm_tem_fields(years)
    t_w, f_w = monthly_upflux(wv, wvth, wth, month_coord="month")
    ax.axhspan(6.0, 8.0, color="0.92", label="ERA5-era estimates, 70 hPa (6-8 x 10^9 kg/s, literature)")
    ax.plot(t_w, f_w, color=C["muted"], lw=1.6, label="WACCM6 histSST, same years (daily TEM tape)")
    ax.plot(t_m, f_m, color=C["orange"], lw=2.2, label=f"model: {label} (5-day-mean covariances)")
    ax.set_ylabel("tropical upward mass flux at 70 hPa\n[10^9 kg/s]"); ax.set_xlabel("year"); ax.grid(True, color=C["grid"])
    ax.set_ylim(0, max(12, float(np.nanmax([f_m.max(), f_w.max()])) * 1.1))
    for y in years: ax.axvline(y, color=C["grid"], lw=0.8)
    ax.legend(frameon=False, fontsize=9, loc="upper left", ncol=3)
    ax.set_title(f"Bottom: strength of the circulation month by month. Annual means: model {f_m.mean():.1f}, WACCM6 {f_w.mean():.1f} x 10^9 kg/s; "
                 f"boreal winter peaks {np.percentile(f_m, 90):.1f} vs {np.percentile(f_w, 90):.1f}", fontsize=10, loc="left")
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.suptitle("Is the Brewer-Dobson circulation there?  Phase 6 configuration, 2005-2009", fontsize=13, y=0.99)
    fig.savefig(a.out, dpi=120, bbox_inches="tight"); print("wrote", a.out)
    print(f"annual-mean upward mass flux at 70 hPa: model {f_m.mean():.2f}, WACCM6 {f_w.mean():.2f} x 10^9 kg/s; model monthly range {f_m.min():.1f}-{f_m.max():.1f}, WACCM6 {f_w.min():.1f}-{f_w.max():.1f}")


if __name__ == "__main__":
    main()
