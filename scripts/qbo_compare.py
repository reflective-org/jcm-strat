#!/usr/bin/env python3
"""Before/after comparison for QBO nudging: equatorial wind, its variability, and where the change is.

    python scripts/qbo_compare.py --before runs/<phase6 run> --after runs/<phase8 run> <outdir> \
        [--years 2005-2009] [--label-before TEXT] [--label-after TEXT]

Writes
  qbo_time_height_before_after.png   equatorial (5S-5N) zonal-mean u, monthly, 100-1 hPa: before | after | ERA5,
                                     with the nudging window (--p-top to --p-bot, default 1-90 hPa) marked
  qbo_profiles.png                   time-mean equatorial u and its deseasonalised standard deviation (the QBO
                                     amplitude) against pressure for before / after / ERA5; zonal-mean u change
                                     (after minus before, time mean) in latitude x pressure with the window drawn
  qbo_metrics.md                     the numbers: std at 10/20/30/50 hPa, mean u at 20/30 hPa, RMS of the
                                     equatorial monthly wind against ERA5 (10-70 hPa and 1-7 hPa), and the RMS change in
                                     zonal-mean u inside and outside the nudging window
Reuses the loaders of strat_compare.py (model runs regridded to the ERA5 reference levels in ln p).
"""
from __future__ import annotations

import argparse, glob, os, sys
import numpy as np
import xarray as xr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_compare as sc


def eq_monthly(zm, lo=-5.0, hi=5.0):
    u = zm["u"].where((zm.lat >= lo) & (zm.lat <= hi), drop=True).mean("lat")
    um = u.resample(time="1MS").mean()
    tdec = np.array([t.year + (t.month - 0.5) / 12 for t in um.indexes["time"]])
    return um.assign_coords(tdec=("time", tdec), month=("time", um.time.dt.month.values))


def deseason_std(um):
    """Standard deviation in time per level -> (plev,): after removing the mean annual cycle when the
    record has at least two years, otherwise the plain standard deviation (with 12 months the
    deseasonalised anomaly would be identically zero)."""
    if um.sizes["time"] >= 24:
        anom = um.groupby("month") - um.groupby("month").mean("time")
        return anom.std("time")
    return um.std("time")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir"); ap.add_argument("--before", required=True); ap.add_argument("--after", required=True)
    ap.add_argument("--years", default="2005-2009")
    ap.add_argument("--label-before", default="before: Phase 6, no QBO nudging"); ap.add_argument("--label-after", default="after: QBO nudged to ERA5")
    ap.add_argument("--p-bot", type=float, default=90.0); ap.add_argument("--p-top", type=float, default=1.0); ap.add_argument("--lat-zero", type=float, default=25.0)
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = map(int, a.years.split("-")); years = list(range(y0, y1 + 1))
    first = xr.open_dataset(sorted(glob.glob(os.path.join(a.after, "longrun_day*.nc")))[0]); lat_out = np.sort(first.lat.values)
    before = sc.load_model(a.before, lat_out); after = sc.load_model(a.after, lat_out)
    era5, _ = sc.load_era5(years, lat_out)
    # restrict ERA5 to the runs' time span
    t0, t1 = after.time.values.min(), after.time.values.max()
    era5 = era5.sel(time=slice(np.datetime64(t0, "M"), np.datetime64(t1, "M") + np.timedelta64(1, "M")))
    eq = {a.label_before: eq_monthly(before), a.label_after: eq_monthly(after), "ERA5 (monthly, CDS)": eq_monthly(era5)}

    # ---- figure 1: time-height
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    for ax, (name, um) in zip(axes, eq.items()):
        um = um.sortby("tdec")
        cf = ax.contourf(um.tdec, um.plev, um.T, levels=np.arange(-40, 41, 5), cmap="RdBu_r", extend="both")
        ax.contour(um.tdec, um.plev, um.T, levels=[0], colors="k", linewidths=0.6)
        ax.set_yscale("log"); ax.set_ylim(100, 1); ax.set_ylabel(f"{name}\npressure [hPa]", fontsize=8)
        for pp in (a.p_bot, a.p_top): ax.axhline(pp, color="k", ls=":", lw=0.8)
        plt.colorbar(cf, ax=ax, label="u 5S-5N [m/s]")
    axes[-1].set_xlabel("year"); axes[0].set_title(f"Equatorial zonal-mean zonal wind 5S-5N (monthly); dotted: the QBO-nudging window {a.p_top:g}-{a.p_bot:g} hPa", fontsize=10)
    fig.tight_layout(); f1 = os.path.join(a.outdir, "qbo_time_height_before_after.png"); fig.savefig(f1, dpi=120); plt.close(fig); print("wrote", f1)

    # ---- figure 2: profiles and where the change is
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    styles = ["--", "-", ":"]
    for (name, um), ls in zip(eq.items(), styles):
        axes[0].plot(um.mean("time"), um.plev, ls, label=name); axes[1].plot(deseason_std(um), um.plev, ls, label=name)
    std_kind = "deseasonalised std" if min(v.sizes["time"] for v in eq.values()) >= 24 else "std (single year: not deseasonalised)"
    for ax, ttl, xl in zip(axes[:2], ("time-mean equatorial u", f"{std_kind} of equatorial u (QBO amplitude)"), ("m/s", "m/s")):
        ax.set_yscale("log"); ax.set_ylim(100, 1); ax.set_title(ttl, fontsize=9); ax.set_xlabel(xl); ax.grid(alpha=.3); ax.legend(fontsize=7)
        for pp in (a.p_bot, a.p_top): ax.axhline(pp, color="k", ls=":", lw=0.8)
    axes[0].set_ylabel("pressure (hPa)"); axes[0].axvline(0, color="k", lw=.5)
    du = (after["u"].mean("time") - before["u"].mean("time"))                       # (plev, lat)
    lv = np.arange(-20, 21, 2.5)
    cf = axes[2].contourf(du.lat, du.plev, du, levels=lv, cmap="RdBu_r", extend="both"); plt.colorbar(cf, ax=axes[2], label="m/s")
    axes[2].set_yscale("log"); axes[2].set_ylim(1000, 1); axes[2].set_title("zonal-mean u, after minus before (time mean)", fontsize=9); axes[2].set_xlabel("latitude")
    axes[2].plot([-a.lat_zero, a.lat_zero, a.lat_zero, -a.lat_zero, -a.lat_zero], [a.p_bot, a.p_bot, a.p_top, a.p_top, a.p_bot], "k:", lw=0.9)
    fig.suptitle("QBO nudging: before / after / ERA5"); fig.tight_layout()
    f2 = os.path.join(a.outdir, "qbo_profiles.png"); fig.savefig(f2, dpi=120); plt.close(fig); print("wrote", f2)

    # ---- metrics
    def at(da, p): return float(da.sel(plev=p, method="nearest"))
    lines = [f"# QBO nudging: before / after / ERA5, {a.years}", "",
             f"| source | {std_kind} 10 / 20 / 30 / 50 hPa [m/s] | mean u 20 / 30 hPa [m/s] | RMS vs ERA5, eq. monthly u 10-70 hPa [m/s] | RMS vs ERA5, 1-7 hPa [m/s] |", "|---|---|---|---|---|"]
    ref = eq["ERA5 (monthly, CDS)"]
    for name, um in eq.items():
        sd = deseason_std(um); mu = um.mean("time")
        common = np.intersect1d(um.tdec.values.round(4), ref.tdec.values.round(4))
        def rms_band(p_lo, p_hi):
            if name.startswith("ERA5"):
                return 0.0
            band = (um.plev >= p_lo) & (um.plev <= p_hi)
            x = um.sortby("tdec").where(band, drop=True); r = ref.sortby("tdec").where(band, drop=True)
            n = min(x.sizes["time"], r.sizes["time"]); return float(np.sqrt(np.nanmean((x.values[:n] - r.values[:n]) ** 2)))
        rms = rms_band(10, 70); rms_top = rms_band(1, 7)          # the QBO layer; the layer above the original 4 hPa window top
        lines.append(f"| {name} | {at(sd,10):.1f} / {at(sd,20):.1f} / {at(sd,30):.1f} / {at(sd,50):.1f} | {at(mu,20):+.1f} / {at(mu,30):+.1f} | {rms:.1f} | {rms_top:.1f} |")
    w = np.cos(np.deg2rad(du.lat)); inside = (np.abs(du.lat) <= a.lat_zero); pin = (du.plev >= a.p_top) & (du.plev <= a.p_bot)
    def rms_region(mask_lat, mask_p):
        d = du.where(mask_lat & mask_p); ww = (w * xr.ones_like(du)).where(mask_lat & mask_p)
        return float(np.sqrt((d ** 2 * ww).sum() / ww.sum()))
    lines += ["", f"RMS change in time-mean zonal-mean u, after minus before: inside the window (|lat| <= {a.lat_zero:.0f}, {a.p_top:.0f}-{a.p_bot:.0f} hPa) {rms_region(inside, pin):.1f} m/s; "
              f"outside it in the stratosphere (|lat| > 30, 1-100 hPa) {rms_region(np.abs(du.lat) > 30, (du.plev >= 1) & (du.plev <= 100)):.1f} m/s; "
              f"troposphere (200-1000 hPa, all latitudes) {rms_region(xr.ones_like(du.lat, dtype=bool), (du.plev >= 200)):.1f} m/s."]
    md = "\n".join(lines); print(md)
    with open(os.path.join(a.outdir, "qbo_metrics.md"), "w") as fh: fh.write(md + "\n")


if __name__ == "__main__":
    main()
