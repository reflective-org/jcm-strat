#!/usr/bin/env python3
"""Polar-night jet strength AND position (Susanne 2026-10-16): is the model's vortex weaker, or just centred off 60N/60S?

    JAX_PLATFORMS=cpu python scripts/vortex_jets.py runs/<run> OUTDIR [--years 2005-2009] [--label TEXT]

Zonal-mean u of the model (every 6-hourly frame in --years), ERA5 and WACCM6 REF-D1 (monthly, same years), winter
season of each hemisphere (DJF north, JJA south). Writes to OUTDIR:
  vortex_jets.png   top: u(lat) at 10 hPa, DJF and JJA; middle/bottom: the jet maximum over 30-90 deg of the winter
                    hemisphere and its latitude, against pressure 100-1 hPa
  vortex_jets.md    the same numbers at 50, 30, 10, 5, 2, 1 hPa, plus u at 60N/60S for comparison with strat_compare
"""
from __future__ import annotations

import argparse, glob, os, re, sys
import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_compare as sc            # noqa: E402

WINTER = {"DJF": ((12, 1, 2), 1), "JJA": ((6, 7, 8), -1)}       # season -> (months, hemisphere sign)
P_TABLE = [50, 30, 10, 5, 2, 1]


def load_model_years(rundir, years, lat_out):
    """Monthly means of zonal-mean u on sc.P_LEVELS, from every frame of the chunk files that fall in ``years``."""
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    out = []
    for f in files:
        d = xr.open_dataset(f, decode_times=True)
        yrs = d.time.dt.year.values
        if not np.isin(yrs, years).any():
            d.close(); continue
        u = d["u_wind"].isel(time=np.where(np.isin(yrs, years))[0]).mean("lon").sortby("lat")
        out.append(u.load()); d.close()
    u = xr.concat(out, "time")
    u = sc._interp_logp(u, u.level.values * sc.P0_HPA, sc.P_LEVELS, "level")
    return u.resample(time="1MS").mean().interp(lat=lat_out)


def season(u, months, month_coord=None):
    m = u[month_coord] if month_coord else u.time.dt.month
    return u.where(m.isin(list(months)), drop=True).mean("time")


def jet(u_seas, sign):
    """Max u over 30-90 deg of the hemisphere (sign +1 north, -1 south) and its latitude, at every level."""
    lat = u_seas.lat.values
    m = (sign * lat >= 30) & (sign * lat <= 90)
    sub = u_seas.isel(lat=np.where(m)[0])
    k = sub.argmax("lat")
    return sub.max("lat").values, sub.lat.values[k.values]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("rundir"); ap.add_argument("outdir")
    ap.add_argument("--years", default="2005-2009"); ap.add_argument("--label", default="model")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    y0, y1 = (int(v) for v in a.years.split("-")); years = list(range(y0, y1 + 1))
    first = sorted(glob.glob(os.path.join(a.rundir, "longrun_day*.nc")))[0]
    lat_out = np.sort(xr.open_dataset(first).lat.values)
    print(f"[vortex_jets] model {a.rundir} {a.years}", flush=True)
    srcs = {a.label: (load_model_years(a.rundir, years, lat_out), None)}
    era, _ = sc.load_era5(years, lat_out)
    if era is not None: srcs["ERA5"] = (era["u"], None)
    wac, _ = sc.load_waccm(years, lat_out)
    if wac is not None and wac.sizes.get("time", 0) > 0: srcs["WACCM6 REF-D1"] = (wac["u"], "month")     # WACCM REF-D1 starts 1996
    style = {a.label: dict(color="C3", lw=2), "ERA5": dict(color="k", lw=1.6), "WACCM6 REF-D1": dict(color="C0", lw=1.4, ls="--")}

    p = sc.P_LEVELS; kp = (p <= 100) & (p >= 1)
    fig, axs = plt.subplots(3, 2, figsize=(12, 12))
    res = {}
    for j, (s, (months, sign)) in enumerate(WINTER.items()):
        for name, (u, mc) in srcs.items():
            us = season(u, months, mc).transpose("plev", "lat")
            umax, ulat = jet(us, sign)
            res[(s, name)] = (us, umax, ulat)
            axs[0, j].plot(us.lat, us.sel(plev=10), label=name, **style[name])
            axs[1, j].plot(umax[kp], p[kp], "o-", ms=3, label=name, **style[name])
            axs[2, j].plot(ulat[kp], p[kp], "o-", ms=3, label=name, **style[name])
        hemi = "N" if sign > 0 else "S"
        axs[0, j].axvline(60 * sign, color="grey", lw=0.6, ls=":"); axs[0, j].axhline(0, color="grey", lw=0.5)
        axs[0, j].set_title(f"{s}: zonal-mean u at 10 hPa [m/s]"); axs[0, j].set_xlabel("latitude"); axs[0, j].set_xlim(-90, 90)
        axs[1, j].set_title(f"{s}: polar-night jet maximum, 30-90{hemi} [m/s]"); axs[1, j].set_xlabel("m/s")
        axs[2, j].set_title(f"{s}: latitude of the jet maximum"); axs[2, j].set_xlabel("latitude")
        axs[2, j].axvline(60 * sign, color="grey", lw=0.6, ls=":")
        for ax in axs[1:, j]:
            ax.set_yscale("log"); ax.set_ylim(100, 1); ax.set_ylabel("hPa")
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(f"Polar vortex strength and position, {a.years}: {a.label} vs ERA5 / WACCM6", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(a.outdir, "vortex_jets.png"), dpi=110); plt.close(fig)

    names = list(srcs)
    L = [f"# Polar-night jet, {a.years}: {a.label} vs " + " / ".join(names[1:]) + "\n",
         "Jet maximum of the winter-hemisphere zonal-mean u over 30-90 deg (DJF north, JJA south), and its latitude; "
         "u at 60 deg as in strat_compare for comparison. Model: monthly means of every 6-hourly frame; references monthly.\n"]
    for s, (months, sign) in WINTER.items():
        L += [f"\n## {s} ({'north' if sign > 0 else 'south'})\n", "| hPa | " + " | ".join(f"{n}: max u [m/s] @ lat / u(60)" for n in names) + " |",
              "|---|" + "---|" * len(names)]
        for pp in P_TABLE:
            k = int(np.where(p == pp)[0][0]); cells = []
            for n in names:
                us, umax, ulat = res[(s, n)]
                cells.append(f"{umax[k]:.0f} @ {ulat[k]:.0f} / {float(us.sel(plev=pp).interp(lat=60 * sign)):.0f}")
            L.append(f"| {pp} | " + " | ".join(cells) + " |")
    open(os.path.join(a.outdir, "vortex_jets.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
