#!/usr/bin/env python3
"""Daily zonal means for the variability scores (Phase 28): a model run or ERA5, same code, on GPU.

    python scripts/daily_zm.py OUT.npz --run runs/<agg>  --t0 2006-01-01 --t1 2011-01-01
    python scripts/daily_zm.py OUT.npz --era5 1990       (one calendar year from the 192x96 L95 nudging windows)
    (--era5 is NOT a stratospheric reference: the windows are WeatherBench2 data, constant above 50 hPa; Phase 28 uses
     scripts/fetch_era5_daily_zm.py instead)

Every 6-hourly frame is reduced on the GPU (jax): zonal means of u, v, T, theta and the eddy covariance v'theta'
formed within each snapshot (stride 1, Phase 15), plus aoa150 and aoa_sfc for a model run. The four frames of a
calendar day are then averaged. ERA5 comes from cache/era5/wb2_192x96_l95_*_6h_u-v-T.nc, the ERA5 nudging target on
the model's own grid and L95 levels (the files store the levels top first; they are flipped to the model's
bottom-first order). Both are put on the model's reference pressures (level * 1013.25 hPa), as everywhere else in
the scoring (teq_score.py, strat_circulation.py).

OUT.npz: days (datetime64[D]), p_hpa (lev), lat, and u, v, T, th, vth [, aoa150, aoa_sfc] as (day, lev, lat) float32.
"""
from __future__ import annotations

import argparse, glob, os, re, sys, time
import numpy as np
import xarray as xr
import jax, jax.numpy as jnp

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAPPA = 0.2857
P0 = 1013.25
CHUNK = 40          # frames per GPU call


@jax.jit
def _reduce(u, v, T, fac):
    """(t, lev, lon, lat) -> zonal means (t, lev, lat); fac = (1000/p)^kappa per level."""
    th = T * fac[None, :, None, None]
    vb = v.mean(2); thb = th.mean(2)
    vth = ((v - vb[:, :, None]) * (th - thb[:, :, None])).mean(2)
    return u.mean(2), vb, T.mean(2), thb, vth


@jax.jit
def _zm(x):
    return x.mean(2)


class Acc:
    """Sums frames into calendar days."""
    def __init__(self):
        self.s, self.n = {}, {}

    def add(self, days, fields):
        for k, a in fields.items():
            for j, d in enumerate(days):
                key = (d, k)
                if key in self.s:
                    self.s[key] += a[j]
                else:
                    self.s[key] = a[j].astype(np.float64)
                self.n[key] = self.n.get(key, 0) + 1

    def out(self, keys):
        days = sorted({d for d, _ in self.s})
        days = [d for d in days if all(self.n.get((d, k), 0) >= 4 for k in keys)]   # complete days only
        return np.array(days, dtype="datetime64[D]"), {k: np.stack([self.s[(d, k)] / self.n[(d, k)] for d in days]).astype(np.float32) for k in keys}


def run_files(rundir):
    fs = glob.glob(os.path.join(rundir, "longrun_day*.nc"))
    return sorted(fs, key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))


def ref_levels():
    f = run_files(os.path.join(REPO, "runs", "p26_AL7h_0610"))[0]
    with xr.open_dataset(f) as d:
        return d.level.values * P0, d.lat.values


def day_of(t):
    # a frame at 00 UTC closes the previous day (frames are 06/12/18/00): shift by 1 s before flooring
    return (t - np.timedelta64(1, "s")).astype("datetime64[D]")


def process(acc, d, names, fac, flip, aoa, t0, t1):
    tt = d.time.values
    k = np.where((day_of(tt) >= t0) & (day_of(tt) < t1))[0]
    for i0 in range(0, k.size, CHUNK):
        sel = k[i0:i0 + CHUNK]
        x = d.isel(time=sel)
        arr = {n: x[v].values for n, v in names.items()}
        if flip:
            arr = {n: a[:, ::-1] for n, a in arr.items()}
        r = _reduce(jnp.asarray(arr["u"]), jnp.asarray(arr["v"]), jnp.asarray(arr["T"]), fac)
        f = dict(zip(("u", "v", "T", "th", "vth"), (np.asarray(a) for a in r)))
        for a in aoa:
            f[a] = np.asarray(_zm(jnp.asarray(x[a].values)))
        acc.add(day_of(tt[sel]), f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--run"); ap.add_argument("--era5", type=int)
    ap.add_argument("--t0"); ap.add_argument("--t1")
    a = ap.parse_args()
    print("[daily_zm] devices", jax.devices(), flush=True)
    p, lat = ref_levels()
    fac = jnp.asarray(((1000.0 / p) ** KAPPA).astype(np.float32))
    acc = Acc(); tic = time.time()
    if a.era5:
        y = a.era5
        fs = glob.glob(os.path.join(REPO, "cache", "era5", f"wb2_192x96_l95_*_{y - 1}-12-31_{y + 1}-01-0*_6h_u-v-T.nc"))
        if not fs:
            sys.exit(f"no ERA5 L95 window for {y}")
        t0, t1 = np.datetime64(f"{y}-01-01"), np.datetime64(f"{y + 1}-01-01")
        with xr.open_dataset(sorted(fs)[-1]) as d:
            process(acc, d, dict(u="u", v="v", T="T"), fac, True, (), t0, t1)
        aoa = ()
    else:
        t0, t1 = np.datetime64(a.t0), np.datetime64(a.t1)
        aoa = ("aoa150", "aoa_sfc")
        for i, f in enumerate(run_files(a.run)):
            with xr.open_dataset(f) as d:
                if not ((day_of(d.time.values) >= t0) & (day_of(d.time.values) < t1)).any():
                    continue
                av = tuple(x for x in aoa if x in d)
                process(acc, d, dict(u="u_wind", v="v_wind", T="temperature"), fac, False, av, t0, t1)
            if i % 20 == 0:
                print(f"[daily_zm] {i} files, {time.time() - tic:.0f} s", flush=True)
        aoa = tuple(k for k in aoa if any(kk == k for _, kk in acc.s))
    keys = ("u", "v", "T", "th", "vth") + tuple(aoa)
    days, f = acc.out(keys)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.savez(a.out, days=days, p_hpa=p, lat=lat, **f)
    print(f"[daily_zm] {a.out}: {days.size} days {days[0]}..{days[-1]}, {time.time() - tic:.0f} s", flush=True)


if __name__ == "__main__":
    main()
