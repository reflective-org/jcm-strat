#!/usr/bin/env python3
"""Offline age-of-air clocks carried by a PARADIS rollout's own winds (issue #29).

    python scripts/paradis_offline_clock.py <member_dir>/state.zarr <out.nc> [--skip-days 30] [--days N] [--substep-h 6]

PARADIS carries no tracer. This transports two passive clock tracers with the rollout's resolved
winds on the rollout's own grid (1 degree, 17 pressure levels 1-1000 hPa), so the result is
"PARADIS winds + an offline advection scheme", not PARADIS itself:

  age_sfc   +1 day/day everywhere, reset to 0 in the lowest level (1000 hPa) - the CLaMS / WACCM
            surface boundary condition
  age_150   +1 day/day everywhere, reset to 0 at every level with p >= 150 hPa - an entry age
            that scores stratospheric transport only

Scheme: semi-Lagrangian, backward trajectories with a two-pass midpoint iteration, trilinear
interpolation in (longitude, latitude, ln p). Horizontal displacement from u, v on the sphere
(poles handled by reflection), vertical from omega as d(ln p) = omega dt / p, clamped to the
1-1000 hPa domain (air arriving from above the top level takes the top-level value). Daily wind
snapshots are linearly interpolated in time to the sub-step. A clock is not a conserved quantity,
so the scheme's lack of mass conservation does not matter here; positivity is exact (linear
interpolation of non-negative fields). Sanity check built in: far from any reset the clock must
advance exactly one day per day; the run prints the top-level maximum against elapsed time.

Output: monthly zonal means of both clocks (time, level, lat) in days, plus the final 3-D fields,
plus the mean over the last 12 months (what aoa_vs_clams.py --paradis-clock reads).
"""
import argparse
import sys
import time as _time

import jax
import jax.numpy as jnp
import numpy as np
import xarray as xr
import zarr

R_EARTH = 6.371e6
DAY = 86400.0


def cartesian_to_uv(wx, wy, wz, lonr, latr):
    u = -np.sin(lonr) * wx + np.cos(lonr) * wy
    v = -np.sin(latr) * np.cos(lonr) * wx - np.sin(latr) * np.sin(lonr) * wy + np.cos(latr) * wz
    return u, v


class Grid:
    def __init__(self, lon_deg, lat_deg, plev_hpa):
        self.lon = np.deg2rad(lon_deg); self.lat = np.deg2rad(lat_deg); self.lnp = np.log(plev_hpa.astype(float))
        self.nlon, self.nlat, self.nlev = len(lon_deg), len(lat_deg), len(plev_hpa)
        self.dlon = self.lon[1] - self.lon[0]; self.dlat = self.lat[1] - self.lat[0]
        # order levels top -> bottom (increasing ln p) for the vertical interpolation
        self.lev_order = np.argsort(self.lnp); self.lnp_sorted = self.lnp[self.lev_order]
        LNP, LAT, LON = np.meshgrid(self.lnp_sorted, self.lat, self.lon, indexing="ij")
        self.LNP, self.LAT, self.LON = (jnp.asarray(x, jnp.float32) for x in (LNP, LAT, LON))   # arrival points
        self.lat_j = jnp.asarray(self.lat, jnp.float32); self.lnp_j = jnp.asarray(self.lnp_sorted, jnp.float32)

    def interp(self, field, lnp, lat, lon):
        """Trilinear interpolation of field (nlev, nlat, nlon, top->bottom) at arbitrary points."""
        # longitude: periodic
        x = (lon % (2 * np.pi)) / self.dlon; i0 = jnp.floor(x).astype(jnp.int32) % self.nlon; fx = x - jnp.floor(x); i1 = (i0 + 1) % self.nlon
        # latitude: clamp to the cell centres (points beyond the last centre use the last row)
        y = (lat - self.lat[0]) / self.dlat; y = jnp.clip(y, 0, self.nlat - 1 - 1e-6); j0 = jnp.floor(y).astype(jnp.int32); fy = y - j0; j1 = jnp.minimum(j0 + 1, self.nlat - 1)
        # vertical: clamp to the domain (top level value above the top, bottom below the bottom)
        z = jnp.clip(lnp, self.lnp_sorted[0], self.lnp_sorted[-1]); k0 = jnp.searchsorted(self.lnp_j, z, side="right") - 1
        k0 = jnp.clip(k0, 0, self.nlev - 2); k1 = k0 + 1
        fz = (z - self.lnp_j[k0]) / (self.lnp_j[k1] - self.lnp_j[k0])
        f = field
        c00 = f[k0, j0, i0] * (1 - fx) + f[k0, j0, i1] * fx; c01 = f[k0, j1, i0] * (1 - fx) + f[k0, j1, i1] * fx
        c10 = f[k1, j0, i0] * (1 - fx) + f[k1, j0, i1] * fx; c11 = f[k1, j1, i0] * (1 - fx) + f[k1, j1, i1] * fx
        c0 = c00 * (1 - fy) + c01 * fy; c1 = c10 * (1 - fy) + c11 * fy
        return c0 * (1 - fz) + c1 * fz

    def departure(self, u, v, w_lnp, dt):
        """Backward midpoint trajectories: returns departure (lnp, lat, lon) for every arrival point."""
        lnp_d, lat_d, lon_d = self.LNP, self.LAT, self.LON
        for _ in range(2):
            # velocities at the trajectory midpoint
            lnp_m = 0.5 * (self.LNP + lnp_d); lat_m = 0.5 * (self.LAT + lat_d); lon_m = 0.5 * (self.LON + lon_d)
            um = self.interp(u, lnp_m, lat_m, lon_m); vm = self.interp(v, lnp_m, lat_m, lon_m); wm = self.interp(w_lnp, lnp_m, lat_m, lon_m)
            lat_d = self.LAT - vm * dt / R_EARTH
            coslat = jnp.maximum(jnp.cos(jnp.clip(lat_m, -np.pi / 2 + 1e-6, np.pi / 2 - 1e-6)), 1e-3)
            lon_d = self.LON - um * dt / (R_EARTH * coslat)
            lnp_d = self.LNP - wm * dt
            # pole reflection
            over = lat_d > np.pi / 2; lat_d = jnp.where(over, np.pi - lat_d, lat_d); lon_d = jnp.where(over, lon_d + np.pi, lon_d)
            under = lat_d < -np.pi / 2; lat_d = jnp.where(under, -np.pi - lat_d, lat_d); lon_d = jnp.where(under, lon_d + np.pi, lon_d)
        return lnp_d, lat_d, lon_d


def make_step(grid, reset_sfc, reset_150):
    @jax.jit
    def step(age_sfc, age_150, u, v, w, dt):
        lnp_d, lat_d, lon_d = grid.departure(u, v, w, dt)
        a1 = grid.interp(age_sfc, lnp_d, lat_d, lon_d) + dt / DAY
        a2 = grid.interp(age_150, lnp_d, lat_d, lon_d) + dt / DAY
        return jnp.where(reset_sfc, 0.0, a1), jnp.where(reset_150, 0.0, a2)
    return step


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("store"); ap.add_argument("out")
    ap.add_argument("--skip-days", type=float, default=30.0); ap.add_argument("--days", type=int, default=None, help="stop after N days (smoke test)")
    ap.add_argument("--substep-h", type=float, default=6.0)
    a = ap.parse_args()
    g = zarr.open_group(a.store, mode="r")
    fn = [str(x) for x in g["feature_names"][:]]
    t = g["time"][:].astype("datetime64[ns]"); plev = g["pressure_levels"][:].astype(float)
    lat_deg = g["latitude"][:]; lon_deg = g["longitude"][:]
    keep = np.where(t >= t[0] + np.timedelta64(int(a.skip_days * 24), "h"))[0]
    if a.days: keep = keep[: a.days + 1]
    grid = Grid(lon_deg, lat_deg, plev)
    lonr = grid.lon[None, None, :]; latr = grid.lat[None, :, None]
    ix = {k: [fn.index(f"{k}_h{int(p)}") for p in plev] for k in ("wind_x", "wind_y", "wind_z", "vertical_velocity")}
    order = grid.lev_order; p_sorted_pa = np.exp(grid.lnp_sorted)[:, None, None] * 100.0
    state = g["state"]

    def winds(i):
        s = state[i]
        wx, wy, wz = s[ix["wind_x"]][order], s[ix["wind_y"]][order], s[ix["wind_z"]][order]
        u, v = cartesian_to_uv(wx, wy, wz, lonr, latr)
        w_lnp = s[ix["vertical_velocity"]][order] / p_sorted_pa           # d(ln p)/dt = omega / p
        return (jnp.asarray(u, jnp.float32), jnp.asarray(v, jnp.float32), jnp.asarray(w_lnp, jnp.float32))

    print("JAX devices:", jax.devices(), flush=True)
    reset_sfc = np.zeros((grid.nlev, grid.nlat, grid.nlon), bool); reset_sfc[-1] = True            # lowest level (1000 hPa)
    reset_150 = np.broadcast_to(np.exp(grid.lnp_sorted)[:, None, None] >= 150.0 - 1e-6, reset_sfc.shape)
    step = make_step(grid, jnp.asarray(reset_sfc), jnp.asarray(reset_150))
    age_sfc = jnp.zeros(reset_sfc.shape, jnp.float32); age_150 = jnp.zeros(reset_sfc.shape, jnp.float32)

    zm_t, zm_sfc, zm_150 = [], [], []
    u0, v0, w0 = winds(keep[0]); elapsed = 0.0; t_start = _time.time(); last_month = None
    for n in range(len(keep) - 1):
        u1, v1, w1 = winds(keep[n + 1])
        span_s = float((t[keep[n + 1]] - t[keep[n]]) / np.timedelta64(1, "s")); nsub = max(1, int(round(span_s / (a.substep_h * 3600)))); dt = span_s / nsub
        for s in range(nsub):
            f = (s + 0.5) / nsub
            u = u0 * (1 - f) + u1 * f; v = v0 * (1 - f) + v1 * f; w = w0 * (1 - f) + w1 * f
            age_sfc, age_150 = step(age_sfc, age_150, u, v, w, jnp.float32(dt))
            elapsed += dt / DAY
        u0, v0, w0 = u1, v1, w1
        month = str(t[keep[n + 1]])[:7]
        if month != last_month:
            if last_month is not None:
                zm_t.append(t[keep[n + 1]]); zm_sfc.append(np.asarray(age_sfc.mean(-1))); zm_150.append(np.asarray(age_150.mean(-1)))
            last_month = month
        if n % 100 == 0 or n == len(keep) - 2:
            a_np = np.asarray(age_sfc); b_np = np.asarray(age_150)
            print(f"  day {n+1}/{len(keep)-1} {str(t[keep[n+1]])[:10]}  elapsed {elapsed:7.1f} d  top-level max age_sfc {a_np[0].max():7.1f} d "
                  f"age_150 {b_np[0].max():7.1f} d  min {a_np.min():.2e}  wall {(_time.time()-t_start)/60:.1f} min", flush=True)
    # always record the final state as the last zonal-mean sample
    zm_t.append(t[keep[-1]]); zm_sfc.append(np.asarray(age_sfc.mean(-1))); zm_150.append(np.asarray(age_150.mean(-1)))
    age_sfc = np.asarray(age_sfc, dtype=np.float64); age_150 = np.asarray(age_150, dtype=np.float64)
    lev_out = np.exp(grid.lnp_sorted)
    n12 = min(12, len(zm_sfc))
    ds = xr.Dataset(
        {"age_sfc_zm": (("time", "level", "lat"), np.array(zm_sfc) / 365.25, {"units": "yr", "long_name": "offline clock, surface reset, zonal mean at month start"}),
         "age_150_zm": (("time", "level", "lat"), np.array(zm_150) / 365.25, {"units": "yr", "long_name": "offline clock, reset below 150 hPa, zonal mean at month start"}),
         "age_sfc_last12_zm": (("level", "lat"), np.mean(zm_sfc[-n12:], axis=0) / 365.25, {"units": "yr"}),
         "age_150_last12_zm": (("level", "lat"), np.mean(zm_150[-n12:], axis=0) / 365.25, {"units": "yr"}),
         "age_sfc_final": (("level", "lat", "lon"), (age_sfc / 365.25).astype(np.float32), {"units": "yr"}),
         "age_150_final": (("level", "lat", "lon"), (age_150 / 365.25).astype(np.float32), {"units": "yr"})},
        coords={"time": np.array(zm_t), "level": ("level", lev_out, {"units": "hPa"}), "lat": lat_deg, "lon": lon_deg},
        attrs={"source": a.store, "scheme": "semi-Lagrangian, midpoint x2, trilinear (lon, lat, ln p), substep_h=%g" % a.substep_h,
               "elapsed_days": elapsed, "start": str(t[keep[0]]), "end": str(t[keep[-1]]), "skipped_days": a.skip_days})
    ds.to_netcdf(a.out); print("wrote", a.out, f"({elapsed:.0f} days transported)")


if __name__ == "__main__":
    main()
