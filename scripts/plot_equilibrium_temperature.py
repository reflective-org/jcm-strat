#!/usr/bin/env python3
"""The temperature each stratosphere option aims for: Held-Suarez, Polvani-Kushner, and ERA5.

    python scripts/plot_equilibrium_temperature.py docs/physics_explainer_teq.png \
        [--era5 "cache/era5_ref/era5_zm_monthly_*.nc"]

Held-Suarez (1994): T_eq = max(200 K, [315 - 60 sin^2(lat) - 10 ln(p/p0) cos^2(lat)] (p/p0)^kappa).
Polvani-Kushner (2002), as used in jcm-strat Phase 6: below 100 hPa the Held-Suarez profile with the
200 K floor replaced by the US Standard Atmosphere; above 100 hPa (1-W) T_US + W T_PV with
T_PV = T_US(100 hPa) (p/100 hPa)^(R gamma/g), gamma = 4 K/km, and W a tanh cap poleward of 50 deg
(width 10 deg) in the winter hemisphere (here: southern winter, as in the paper). ERA5: zonal-mean
temperature, JJA mean (southern winter) of the CDS monthly means, for comparison with the same
hemisphere in winter.
"""
import argparse
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

R, G, KAPPA, P0 = 287.0, 9.81, 2.0 / 7.0, 1000.0
USSA = [(101325.0, 288.15, -0.0065), (22632.1, 216.65, 0.0), (5474.9, 216.65, 0.001), (868.02, 228.65, 0.0028),
        (110.91, 270.65, 0.0), (66.939, 270.65, -0.0028), (3.9564, 214.65, -0.002)]


def t_ussa(p_hpa):
    p = np.asarray(p_hpa) * 100.0; out = np.empty_like(p, dtype=float)
    for i, pp in enumerate(p.ravel()):
        for p_b, t_b, lapse in USSA:
            if pp <= p_b:
                base = (p_b, t_b, lapse)
        p_b, t_b, lapse = base
        out.ravel()[i] = t_b if lapse == 0 else t_b * (pp / p_b) ** (-R * lapse / G)
    return out


def held_suarez(lat_deg, p_hpa):
    lat = np.deg2rad(lat_deg)[None, :]; p = p_hpa[:, None]
    t = (315 - 60 * np.sin(lat) ** 2 - 10 * np.log(p / P0) * np.cos(lat) ** 2) * (p / P0) ** KAPPA
    return np.maximum(200.0, t)


def polvani_kushner(lat_deg, p_hpa, gamma_k_per_km=4.0, p_t=100.0, phi0=50.0, dphi=10.0, winter="south"):
    lat = np.deg2rad(lat_deg)[None, :]; p = p_hpa[:, None]
    t_hs = (315 - 60 * np.sin(lat) ** 2 - 10 * np.log(p / P0) * np.cos(lat) ** 2) * (p / P0) ** KAPPA
    t_us = t_ussa(p_hpa)[:, None] * np.ones_like(lat)
    trop = np.maximum(t_us, t_hs)                                        # US standard atmosphere replaces the 200 K floor
    t_pv = t_ussa(np.array([p_t]))[0] * (p / p_t) ** (R * gamma_k_per_km * 1e-3 / G)
    s = -1 if winter == "south" else 1
    w = 0.5 * (1 + np.tanh((s * lat - np.deg2rad(phi0)) / np.deg2rad(dphi)))
    strat = (1 - w) * t_us + w * t_pv
    return np.where(p < p_t, strat, trop)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("out_png"); ap.add_argument("--era5", default=None)
    a = ap.parse_args()
    lat = np.linspace(-89, 89, 90); p = np.logspace(0, 3, 80)              # 1 .. 1000 hPa
    panels = [("Held-Suarez (1994) target temperature\n(Phases 1-4)", held_suarez(lat, p)),
              ("Polvani-Kushner (2002) target temperature\ngamma = 4 K/km, southern winter (Phase 6)", polvani_kushner(lat, p))]
    if a.era5:
        e = xr.open_mfdataset(sorted(glob.glob(a.era5)), combine="nested", concat_dim="time", decode_times=False)
        t = e.tzm.values; n = t.shape[0]; months = np.arange(n) % 12 + 1
        jja = t[np.isin(months, (6, 7, 8))].mean(0)                          # (25 lev, 721 lat)
        pe = e.level.values.astype(float); le = e.lat.values
        panels.append((f"ERA5: the real zonal-mean temperature\nJJA mean (southern winter), {n // 12} years", (pe, le, jja)))
    fig, axes = plt.subplots(1, len(panels), figsize=(5.6 * len(panels), 5.2), sharey=True)
    levels = np.arange(180, 311, 10)
    for ax, (title, data) in zip(np.atleast_1d(axes), panels):
        if isinstance(data, tuple):
            cf = ax.contourf(data[1], data[0], data[2], levels=levels, cmap="RdYlBu_r", extend="both")
            ax.contour(data[1], data[0], data[2], levels=[200, 220, 240, 260], colors="k", linewidths=0.5)
        else:
            cf = ax.contourf(lat, p, data, levels=levels, cmap="RdYlBu_r", extend="both")
            ax.contour(lat, p, data, levels=[200, 220, 240, 260], colors="k", linewidths=0.5)
        ax.set_yscale("log"); ax.set_ylim(1000, 1); ax.set_title(title, fontsize=9); ax.set_xlabel("latitude")
        ax.axhline(100, color="grey", ls=":", lw=0.8)
    np.atleast_1d(axes)[0].set_ylabel("pressure (hPa)")
    fig.colorbar(cf, ax=list(np.atleast_1d(axes)), label="K", shrink=0.9)
    fig.suptitle("What holds the stratosphere's temperature when radiation is switched off, versus the real atmosphere")
    fig.savefig(a.out_png, dpi=130, bbox_inches="tight"); print("wrote", a.out_png)


if __name__ == "__main__":
    main()
