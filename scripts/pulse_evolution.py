#!/usr/bin/env python3
"""Phase 10: advection of every pulse and continuous-source tracer, as panels and as animations.

    python scripts/pulse_evolution.py runs/<run> <outdir> [--label TEXT] [--tracers pulse_1 src_2 ...] [--stages panels gif vertical mass]

For each tracer pulse_1..5 and src_1..4 (the sites come from ProductionTracers, so the map is drawn at
the tracer's own injection level and the site is marked):
  <outdir>/<run>_<tracer>_evolution.png   the layout of pulse_diagnostics' pulse_evolution figure: map at
                                          the injection level (top) and zonal mean (bottom), one column per
                                          time after the injection - pulses 0, 5, 20, 60, 180, 365 d;
                                          sources 5, 20, 60, 180, 365, 1825 d (the sources emit every step)
  <outdir>/<run>_<tracer>_evolution.gif   the same two panels as an animation over the first year: daily
                                          to day 60, every 3 d to day 180, every 10 d to day 365; the
                                          colour scale is logarithmic and fixed over the animation (four
                                          decades below the largest value in it) so decay stays visible
  <outdir>/<run>_tracers_evolution.gif    all nine maps side by side, same frames, own scale each
  <outdir>/<run>_<tracer>_vertical.png    the vertical structure over the first two years, every 5 d: time-pressure
                                          sections of the mass-weighted global mean and of the zonal mean within
                                          10 deg of the injection latitude (log colour, four decades), with the
                                          mass-centroid pressure overlaid; line profiles at fixed days
  <outdir>/<run>_tracers_vertical.png     all nine tracers: centroid pressure and vertical spread (std of log10 p,
                                          mass-weighted) against time - the descent / ascent of each blob
  <outdir>/<run>_tracer_mass.png          total global tracer mass (mixing ratio x layer air mass, summed over the
                                          globe, in kg) over the whole run for the pulses (as a fraction of the
                                          injected mass), the sources and sai (with the cumulative emission), and
                                          n2o / cfc11; every 10 d for two years, then every 30 d; read in parallel
  <outdir>/<run>_tracer_mass.md           the numbers: injected mass, half-life and e-folding time of each pulse,
                                          source rate, equilibrium mass and residence time of each source
Every frame is the instantaneous 6-hourly field; the file that holds a given day is opened once and all
tracers read from it. Runs on CPU (JAX is not used); ~10 min for the 1990-2019 run.
"""
from __future__ import annotations

import os
os.environ.setdefault("JAX_PLATFORMS", "cpu")           # before anything imports jax: this is a CPU analysis

import argparse
import datetime as dt
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import xarray as xr
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tracer_budget import P0, gauss_weights, install_level_table, layer_dp  # noqa: E402
from pulse_diagnostics import analytic_target  # noqa: E402

EARTH_AREA_OVER_G = 4 * np.pi * 6.371e6 ** 2 / 9.80665      # m2 s2/m: sum(q dp w) * this = kg of tracer (q a mass mixing ratio)
MASS_DAYS = np.concatenate([np.arange(0, 730, 10.0), np.arange(730, 11000, 30.0)])

PULSES = tuple(f"pulse_{i}" for i in range(1, 6))
SOURCES = tuple(f"src_{i}" for i in range(1, 5))
MASS_TRACERS = PULSES + SOURCES + ("sai", "n2o", "cfc11")
PANEL_DAYS = {"pulse": (0, 5, 20, 60, 180, 365), "src": (5, 20, 60, 180, 365, 1825)}
VERT_DAYS = np.arange(0, 730.01, 5.0); VERT_PROFILE_DAYS = (0, 5, 20, 60, 180, 365, 730)
GIF_DAYS = np.concatenate([np.arange(0, 60, 1.0), np.arange(60, 180, 3.0), np.arange(180, 365.01, 10.0)])
CMAP = "magma_r"


def frame_index(rundir):
    """(file, local index, run day) of every frame: 6-hourly output, so a file ending on day s1 that follows one
    ending on day s0 holds 4 (s1 - s0) frames, the first 6 h after s0 (opening all 1100 files would take 8 min)."""
    files = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda p: int(re.search(r"_day(\d+)\.nc$", p).group(1)))
    if not files:
        raise SystemExit("no longrun_day*.nc in " + rundir)
    ends = [int(re.search(r"_day(\d+)\.nc$", f).group(1)) for f in files]; starts = [0] + ends[:-1]
    out = []
    for f, s0, s1 in zip(files, starts, ends):
        n = 4 * (s1 - s0)
        out += [(f, j, s0 + (s1 - s0) / n * (j + 1)) for j in range(n)]
    with xr.open_dataset(files[0], decode_times=False) as d:
        if d.sizes["time"] != 4 * (ends[0] - starts[0]):
            raise SystemExit(f"{files[0]} holds {d.sizes['time']} frames for {ends[0] - starts[0]} days; expected 6-hourly output")
    return out


def start_date(rundir):
    seg = os.path.join(rundir, "segments.txt")
    if os.path.exists(seg):
        return dt.date.fromisoformat(open(seg).readline().split()[0])
    return None


def site(name, term):
    kind, i = name.split("_"); i = int(i) - 1
    return (term.pulses if kind == "pulse" else term.sources)[i]          # (lat, lon, p hPa, amp)


def read_frames(index, days, tracers, reduce=None):
    """dict tracer -> list over the frames nearest to `days` of the full (lev, lon, lat) array, or of
    reduce(q, nsp) when given (nsp = normalized surface pressure of the frame); opens each file once."""
    run_day = np.asarray([r[2] for r in index])
    picks = [int(np.argmin(np.abs(run_day - (run_day[0] + d)))) for d in days]
    data = {k: [None] * len(picks) for k in tracers}; when = [run_day[i] for i in picks]
    by_file = {}
    for slot, i in enumerate(picks):
        by_file.setdefault(index[i][0], []).append((slot, index[i][1]))
    for n, (f, items) in enumerate(sorted(by_file.items())):
        with xr.open_dataset(f, decode_times=False) as d:
            for slot, j in items:
                nsp = np.asarray(d.normalized_surface_pressure.isel(time=j)) if reduce else None
                for k in tracers:
                    q = np.asarray(d[k].isel(time=j))
                    data[k][slot] = reduce(q, nsp) if reduce else q
        print(f"  read {len(items)} frame(s) from {os.path.basename(f)} ({n + 1}/{len(by_file)})", flush=True)
    return data, when


def daystr(day, t0):
    return f"day {day:.2f}" + (f" ({(t0 + dt.timedelta(days=float(day))).isoformat()})" if t0 else "")


def draw_pair(axm, axz, q, klev, lat, lon, p_nom, s, title, norm=None, vmax=None):
    """map at the injection level and zonal mean of one field; returns the two mappables."""
    lat0, lon0, p0, _ = s
    if norm is None:
        m1 = axm.pcolormesh(lon, lat, q[klev].T, vmin=0, vmax=vmax if vmax else max(q[klev].max(), 1e-6), cmap=CMAP, shading="auto")
    else:
        m1 = axm.pcolormesh(lon, lat, np.maximum(q[klev].T, norm.vmin), norm=norm, cmap=CMAP, shading="auto")
    axm.plot(lon0, lat0, "c+", ms=10, mew=1.5); axm.set_title(title, fontsize=9); axm.set_xlim(0, 360); axm.set_ylim(-90, 90)
    z = q.mean(axis=1)
    if norm is None:
        m2 = axz.contourf(lat, p_nom, z, levels=np.linspace(0, vmax if vmax else max(z.max(), 1e-6), 11), cmap=CMAP, extend="min")
    else:
        lv = np.logspace(np.log10(norm.vmin), np.log10(norm.vmax), 13)
        m2 = axz.contourf(lat, p_nom, np.maximum(z, norm.vmin), levels=lv, norm=norm, cmap=CMAP, extend="both")
    axz.plot(lat0, p0, "c+", ms=10, mew=1.5); axz.set_yscale("log"); axz.set_ylim(1000, 0.1); axz.set_title("zonal mean", fontsize=9)
    return m1, m2


def panel_figure(name, data, when, s, klev, lat, lon, p_nom, label, t0, out):
    n = len(when); fig, axes = plt.subplots(2, n, figsize=(4.2 * n, 7))
    for c in range(n):
        m1, m2 = draw_pair(axes[0, c], axes[1, c], data[c], klev, lat, lon, p_nom, s, f"{name} at {p_nom[klev]:.0f} hPa, {daystr(when[c], t0)}")
        fig.colorbar(m1, ax=axes[0, c]); fig.colorbar(m2, ax=axes[1, c])
    kind = "pulse injected once at t0" if name.startswith("pulse") else "continuous source (A*G / 90 d per step)"
    fig.suptitle(f"{label}: {name} - {kind} at {s[0]:.0f}N {s[1]:.0f}E {s[2]:.0f} hPa, amplitude {s[3]}"); fig.tight_layout()
    fig.savefig(out, dpi=120); plt.close(fig); print("wrote", out, flush=True)


def fig_to_image(fig):
    fig.canvas.draw(); buf = np.asarray(fig.canvas.buffer_rgba())
    return Image.fromarray(buf[..., :3]).quantize(colors=256, method=Image.Quantize.MEDIANCUT)


def save_gif(images, out, ms=120):
    images[0].save(out, save_all=True, append_images=images[1:], duration=ms, loop=0, optimize=False)
    print(f"wrote {out} ({len(images)} frames, {os.path.getsize(out) / 1e6:.1f} MB)", flush=True)


def tracer_gif(name, data, when, s, klev, lat, lon, p_nom, label, t0, out):
    vmax = max(max(q[klev].max(), q.mean(axis=1).max()) for q in data); norm = mcolors.LogNorm(vmin=vmax * 1e-4, vmax=vmax)
    images = []
    for q, day in zip(data, when):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), dpi=90)
        m1, m2 = draw_pair(axes[0], axes[1], q, klev, lat, lon, p_nom, s, f"{name} at {p_nom[klev]:.0f} hPa, {daystr(day, t0)}", norm=norm)
        ticks = mticker.LogLocator(base=10)
        fig.colorbar(m1, ax=axes[0], ticks=ticks); fig.colorbar(m2, ax=axes[1], ticks=ticks, format=mticker.LogFormatterSciNotation())
        fig.suptitle(f"{label}: {name} ({s[0]:.0f}N {s[1]:.0f}E {s[2]:.0f} hPa, amplitude {s[3]}); log colour scale, fixed", fontsize=10); fig.tight_layout()
        images.append(fig_to_image(fig)); plt.close(fig)
    save_gif(images, out)


def overview_gif(names, data, when, sites, klevs, lat, lon, p_nom, label, t0, out):
    norms = {}
    for k in names:
        vmax = max(q[klevs[k]].max() for q in data[k]); norms[k] = mcolors.LogNorm(vmin=vmax * 1e-4, vmax=vmax)
    images = []
    for f in range(len(when)):
        fig, axes = plt.subplots(3, 3, figsize=(13, 8.5), dpi=80)
        for ax, k in zip(axes.flat, names):
            q = data[k][f]; s = sites[k]
            ax.pcolormesh(lon, lat, np.maximum(q[klevs[k]].T, norms[k].vmin), norm=norms[k], cmap=CMAP, shading="auto")
            ax.plot(s[1], s[0], "c+", ms=9, mew=1.5); ax.set_title(f"{k} at {p_nom[klevs[k]]:.0f} hPa (amp {s[3]}, max here {norms[k].vmax:.2g})", fontsize=9)
            ax.set_xticks([0, 90, 180, 270, 360]); ax.set_yticks([-60, -30, 0, 30, 60])
        fig.suptitle(f"{label}: pulse and source tracers at their injection levels, {daystr(when[f], t0)}; log scale, four decades below each tracer's largest value", fontsize=10)
        fig.tight_layout(); images.append(fig_to_image(fig)); plt.close(fig)
    save_gif(images, out)


def hybrid_boundaries(nlev):
    """(da, db) of the run's hybrid table, top-first, so a worker can form dp without importing JAX."""
    from jcm.physics.echam.echam_levels import get_echam_levels
    v = get_echam_levels(nlev)
    return np.diff(np.asarray(v.a_boundaries, dtype=np.float64)), np.diff(np.asarray(v.b_boundaries, dtype=np.float64))


def _mass_worker(args):
    """Total mass (kg) of each tracer and of the air in one frame: (file, local index, tracers, da, db).
    numpy and netCDF only - a forked worker must not touch JAX (it deadlocks on the parent's thread pool)."""
    f, j, tracers, da, db = args
    with xr.open_dataset(f, decode_times=False) as d:
        lat = np.asarray(d.lat); nsp = np.asarray(d.normalized_surface_pressure.isel(time=j))
        dp = (da[:, None, None] + db[:, None, None] * (nsp[None] * P0))[::-1]          # surface-first like the file
        wgt = dp * gauss_weights(lat)[None, None, :] * EARTH_AREA_OVER_G / d.sizes["lon"]   # w sums to 1 over lat, so /nlon
        out = {k: float((np.asarray(d[k].isel(time=j)) * wgt).sum()) for k in tracers if k in d}
    out["air"] = float(wgt.sum())
    return out


def mass_series(index, days, tracers, nlev, nproc=16):
    """Global mass of every tracer at the frames nearest to `days`, one process per file."""
    import multiprocessing as mp
    da, db = hybrid_boundaries(nlev)
    run_day = np.asarray([r[2] for r in index])
    picks = [int(np.argmin(np.abs(run_day - (run_day[0] + d)))) for d in days]
    jobs = [(index[i][0], index[i][1], tracers, da, db) for i in picks]
    with mp.get_context("fork").Pool(nproc) as pool:
        res = []
        for n, r in enumerate(pool.imap(_mass_worker, jobs, chunksize=4)):
            res.append(r)
            if n % 50 == 0 or n == len(jobs) - 1:
                print(f"  mass: frame {n + 1}/{len(jobs)}", flush=True)
    keys = [k for k in tracers if k in res[0]] + ["air"]
    return {k: np.asarray([r[k] for r in res]) for k in keys}, np.asarray([run_day[i] for i in picks])


def source_rate(name, term, lat, lon, p_nom, nsp0):
    """Emitted mass per day of a continuous source: the blob A G times the term's rate (1 / 90 d)."""
    kind_term = type("T", (), {"pulses": term.sources, "sigma_h": term.sigma_h, "sigma_z": term.sigma_z})
    G = analytic_target(name, lat, lon, p_nom * nsp0.mean(), kind_term)
    wgt = layer_dp(p_nom.size, nsp0) * gauss_weights(lat)[None, None, :] * EARTH_AREA_OVER_G / lon.size
    return float((G * wgt).sum()) * float(term.source_rate) * 86400.0


def mass_figure(M, tday, names, term, sites, lat, lon, p_nom, nsp0, label, t0, out_png, out_md):
    yr = tday / 365.25; pulses = [k for k in names if k.startswith("pulse")]; sources = [k for k in names if k.startswith("src")]
    steady = [k for k in ("n2o", "cfc11") if k in M]; has_sai = "sai" in M
    lines = [f"# {label}: global tracer mass", "", f"mass = sum over the globe of mixing ratio x layer air mass (4 pi a^2 / g x sum q dp w); air mass {M['air'][0]:.4e} kg; "
             f"{tday.size} frames to day {tday[-1]:.0f}", ""]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    ax = axes[0, 0]
    lines += ["## pulses (injected once)", "", "| tracer | injected mass (kg) | half-life (d) | e-folding time (d) | fraction left after 1 yr | after 5 yr | after 30 yr |", "|---|---|---|---|---|---|---|"]
    for k in pulses:
        m = M[k] / M[k][0]; (ln,) = ax.plot(yr, m, label=f"{k} ({sites[k][2]:.0f} hPa)"); axes[0, 1].plot(yr, m, color=ln.get_color(), label=k)
        def first_below(th):
            i = np.argmax(m < th); return f"{tday[i] - tday[0]:.0f}" if m.min() < th else f"> {tday[-1]:.0f}"
        def at(y):
            return f"{m[np.argmin(np.abs(yr - y))]:.1e}" if yr[-1] >= y - 0.1 else "-"
        lines.append(f"| {k} | {M[k][0]:.3e} | {first_below(0.5)} | {first_below(np.exp(-1))} | {at(1)} | {at(5)} | {at(30)} |")
    ax.set_yscale("log"); ax.set_ylim(1e-6, 1.5); ax.set_xlim(0, 5); ax.set_title("pulses: mass left, fraction of the injected mass (log, first five years)", fontsize=10); ax.legend(fontsize=8)
    ax = axes[0, 1]; ax.set_xlim(0, 2); ax.set_ylim(0, 1.05); ax.set_title("pulses: the first two years (linear)", fontsize=10); ax.legend(fontsize=8)
    ax = axes[1, 0]
    lines += ["", "## continuous sources and sai", "", "| tracer | emission (kg/d) | mass after 1 yr (kg) | after 5 yr | after 30 yr | residence time = mass / emission (yr, at 30 yr) |", "|---|---|---|---|---|---|"]
    for k in sources:
        S = source_rate(k, term, lat, lon, p_nom, nsp0); (ln,) = ax.plot(yr, M[k], label=f"{k} ({sites[k][2]:.0f} hPa)")
        ax.plot(yr, S * (tday - tday[0]) + M[k][0], ":", color=ln.get_color(), lw=1)
        def at(y):
            return f"{M[k][np.argmin(np.abs(yr - y))]:.3e}" if yr[-1] >= y - 0.1 else "-"
        lines.append(f"| {k} | {S:.3e} | {at(1)} | {at(5)} | {at(30)} | {M[k][-1] / S / 365.25:.2f} |")
    if has_sai:
        (ln,) = ax.plot(yr, M["sai"], "--", label="sai (box source, no sink)")
        S = M["sai"][-1] / (tday[-1] - tday[0]); lines.append(f"| sai | {S:.3e} (mean over the run) | {M['sai'][np.argmin(np.abs(yr - 1))]:.3e} | {M['sai'][np.argmin(np.abs(yr - 5))]:.3e} | {M['sai'][-1]:.3e} | no sink |")
    ax.set_yscale("log"); ax.set_title("sources: total mass (kg); dotted = cumulative emission, the gap is what the surface removed", fontsize=10); ax.legend(fontsize=8)
    ax = axes[1, 1]
    for k in steady:
        ax.plot(yr, M[k] / M[k][0], label=f"{k} (M0 {M[k][0]:.3e} kg)")
        lines.append(f"\n{k}: mass first / after 1 yr / last = {M[k][0]:.4e} / {M[k][np.argmin(np.abs(yr - 1))]:.4e} / {M[k][-1]:.4e} kg ({M[k][-1] / M[k][0] - 1:+.2%})")
    ax.plot(yr, M["air"] / M["air"][0], "k:", lw=1, label="dry air (reference)")
    ax.set_title("N2O-like tracers: mass relative to the WACCM initial state", fontsize=10); ax.legend(fontsize=8)
    for ax in axes.flat:
        ax.set_xlabel("years since " + (t0.isoformat() if t0 else "start")); ax.grid(alpha=0.3)
        if t0 and ax.get_xlim()[1] > 5:
            ticks = np.arange(0, int(yr[-1]) + 1, 5); ax.set_xticks(ticks); ax.set_xticklabels([str(t0.year + int(t)) for t in ticks])
    fig.suptitle(f"{label}: total global tracer mass"); fig.tight_layout(); fig.savefig(out_png, dpi=120); plt.close(fig); print("wrote", out_png, flush=True)
    open(out_md, "w").write("\n".join(lines) + "\n"); print("wrote", out_md, flush=True); print("\n".join(lines))


class VerticalReducer:
    """Per frame: the mass-weighted mean profile, globally and within `half` deg of each site latitude
    (dict tracer -> profile; the same reducer serves every tracer, so all bands are computed and the
    caller picks its own), the mass centroid of log10 p and its spread. Weights are the hybrid layer
    thickness times the Gaussian weights."""

    def __init__(self, lat, p_nom, lat0_by_tracer, half=10.0):
        self.w = gauss_weights(lat); self.logp = np.log10(p_nom); self.nlev = p_nom.size
        self.bands = {k: np.abs(lat - lat0) <= half for k, lat0 in lat0_by_tracer.items()}

    def __call__(self, q, nsp):
        wgt = layer_dp(self.nlev, nsp) * self.w[None, None, :]; qw = q * wgt
        glob = qw.sum(axis=(1, 2)) / wgt.sum(axis=(1, 2))
        band = {k: qw[:, :, b].sum(axis=(1, 2)) / wgt[:, :, b].sum(axis=(1, 2)) for k, b in self.bands.items()}
        m = qw.sum(axis=(1, 2)); M = max(m.sum(), 1e-300)
        c = (m * self.logp).sum() / M; sd = np.sqrt(max((m * (self.logp - c) ** 2).sum() / M, 0.0))
        return glob, band, c, sd


def vertical_figure(name, red, when, s, lat, p_nom, label, out):
    glob = np.stack([r[0] for r in red], axis=1); band = np.stack([r[1] for r in red], axis=1)   # (lev, time)
    cen = np.asarray([r[2] for r in red]); when = np.asarray(when)
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), gridspec_kw={"width_ratios": [1.3, 1.3, 1]})
    for ax, z, ttl in ((axes[0], glob, "global mass-weighted mean"), (axes[1], band, f"zonal mean within 10 deg of {s[0]:.0f}N")):
        vmax = z.max(); norm = mcolors.LogNorm(vmin=vmax * 1e-4, vmax=vmax)
        m = ax.pcolormesh(when, p_nom, np.maximum(z, norm.vmin), norm=norm, cmap=CMAP, shading="auto")
        fig.colorbar(m, ax=ax, ticks=mticker.LogLocator(base=10))
        ax.plot(when, 10 ** cen, "c-", lw=1.5, label="mass centroid"); ax.axhline(s[2], color="c", ls=":", lw=1, label="injection level")
        ax.set_yscale("log"); ax.set_ylim(1000, 0.1); ax.set_xlabel("day"); ax.set_ylabel("hPa"); ax.set_title(ttl, fontsize=10); ax.legend(fontsize=8, loc="lower right")
    ax = axes[2]; colors = plt.cm.viridis(np.linspace(0, 1, len(VERT_PROFILE_DAYS)))
    for c, d in zip(colors, VERT_PROFILE_DAYS):
        if d > when[-1]:
            continue
        i = int(np.argmin(np.abs(when - (when[0] + d)))); ax.plot(np.maximum(band[:, i], 1e-12), p_nom, color=c, label=f"day {when[i]:.0f}")
    ax.set_xscale("log"); ax.set_xlim(band.max() * 1e-5, band.max() * 2); ax.set_yscale("log"); ax.set_ylim(1000, 0.1); ax.axhline(s[2], color="c", ls=":", lw=1)
    ax.set_title(f"profiles of the band mean", fontsize=10); ax.set_xlabel("mixing ratio"); ax.legend(fontsize=8)
    kind = "pulse injected once at t0" if name.startswith("pulse") else "continuous source"
    fig.suptitle(f"{label}: {name} - {kind} at {s[0]:.0f}N {s[1]:.0f}E {s[2]:.0f} hPa, amplitude {s[3]}: vertical structure, first {when[-1]:.0f} days (mass-weighted, so the centroid starts below the injection level)"); fig.tight_layout()
    fig.savefig(out, dpi=120); plt.close(fig); print("wrote", out, flush=True)


def vertical_summary(names, reds, when, sites, label, out):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5)); when = np.asarray(when)
    for k in names:
        cen = np.asarray([r[2] for r in reds[k]]); sd = np.asarray([r[3] for r in reds[k]]); ls = "-" if k.startswith("pulse") else "--"
        (line,) = axes[0].plot(when, 10 ** cen, ls, label=f"{k} ({sites[k][2]:.0f} hPa)"); axes[1].plot(when, sd, ls, label=k)
        axes[0].plot(when[0], sites[k][2], "o", mfc="none", color=line.get_color(), ms=6)   # the injection level
    axes[0].set_yscale("log"); axes[0].set_ylim(1000, 1); axes[0].set_ylabel("hPa"); axes[0].set_title("mass-centroid pressure (mass-weighted mean of log10 p)", fontsize=10)
    axes[1].set_ylabel("decades"); axes[1].set_title("vertical spread (mass-weighted std of log10 p)", fontsize=10)
    for ax in axes: ax.set_xlabel("day"); ax.grid(alpha=0.3); ax.legend(fontsize=8, ncol=2)
    fig.suptitle(f"{label}: where the tracer mass sits - pulses (solid, injected once) and continuous sources (dashed); circles = injection level\n"
                 "(weights are the layer mass, so a blob centred at p0 in mixing ratio has its mass centroid below p0)", fontsize=10); fig.tight_layout()
    fig.savefig(out, dpi=120); plt.close(fig); print("wrote", out, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("outdir"); ap.add_argument("--label", default="")
    ap.add_argument("--tracers", nargs="*", default=None); ap.add_argument("--stages", nargs="*", default=["panels", "gif", "vertical", "mass"], choices=["panels", "gif", "vertical", "mass"])
    ap.add_argument("--nproc", type=int, default=16, help="worker processes for the mass stage")
    ap.add_argument("--recompute", action="store_true", help="mass stage: ignore <rundir>/tracer_mass.npz and re-read the frames")
    a = ap.parse_args()
    run = os.path.basename(a.rundir.rstrip("/")); label = a.label or run; os.makedirs(a.outdir, exist_ok=True)
    install_level_table(a.rundir)
    from jcm_strat.advection_tracers import ProductionTracers
    term = ProductionTracers()
    index = frame_index(a.rundir); t0 = start_date(a.rundir)
    with xr.open_dataset(index[0][0], decode_times=False) as d:
        lat = np.asarray(d.lat); lon = np.asarray(d.lon); p_nom = np.asarray(d.level) * P0 / 100.0
        present = [k for k in PULSES + SOURCES if k in d]
    names = [k for k in (a.tracers or present) if k in present]
    sites = {k: site(k, term) for k in names}; klevs = {k: int(np.argmin(np.abs(p_nom - sites[k][2]))) for k in names}
    last = index[-1][2]
    # ---- panels
    for kind, tr in (("pulse", [k for k in names if k.startswith("pulse")]), ("src", [k for k in names if k.startswith("src")])):
        if not tr or "panels" not in a.stages:
            continue
        days = [d for d in PANEL_DAYS[kind] if d <= last]
        print(f"panels: {tr} at days {days}", flush=True)
        data, when = read_frames(index, days, tr)
        for k in tr:
            panel_figure(k, data[k], when, sites[k], klevs[k], lat, lon, p_nom, label, t0, os.path.join(a.outdir, f"{run}_{k}_evolution.png"))
    # ---- animations (one read of the frames for all tracers)
    if "gif" in a.stages:
        days = [d for d in GIF_DAYS if d <= last]
        print(f"gif: {len(days)} frames to day {days[-1]:.0f}", flush=True)
        data, when = read_frames(index, days, names)
        for k in names:
            tracer_gif(k, data[k], when, sites[k], klevs[k], lat, lon, p_nom, label, t0, os.path.join(a.outdir, f"{run}_{k}_evolution.gif"))
        if len(names) > 1:
            overview_gif(names, data, when, sites, klevs, lat, lon, p_nom, label, t0, os.path.join(a.outdir, f"{run}_tracers_evolution.gif"))
        del data
    # ---- vertical structure (reduced per frame while reading; one reducer per tracer for its own latitude band)
    if "vertical" in a.stages:
        days = [d for d in VERT_DAYS if d <= last]
        print(f"vertical: {len(days)} frames to day {days[-1]:.0f}", flush=True)
        raw, when = read_frames(index, days, names, reduce=VerticalReducer(lat, p_nom, {k: sites[k][0] for k in names}))
        for k in names:
            red = [(g, b[k], c, sd) for (g, b, c, sd) in raw[k]]
            vertical_figure(k, red, when, sites[k], lat, p_nom, label, os.path.join(a.outdir, f"{run}_{k}_vertical.png"))
        if len(names) > 1:
            vertical_summary(names, {k: [(g, None, c, sd) for (g, b, c, sd) in raw[k]] for k in names}, when, sites, label, os.path.join(a.outdir, f"{run}_tracers_vertical.png"))
    # ---- total mass over the whole run
    if "mass" in a.stages:
        days = [d for d in MASS_DAYS if d <= last]
        print(f"mass: {len(days)} frames to day {days[-1]:.0f}, {a.nproc} processes", flush=True)
        cache = os.path.join(a.rundir, "tracer_mass.npz")
        if os.path.exists(cache) and not a.recompute:
            z = np.load(cache); tday = z["day"]; M = {k: z[k] for k in z.files if k != "day"}; print("mass series from", cache, flush=True)
        else:
            M, tday = mass_series(index, days, list(MASS_TRACERS), p_nom.size, a.nproc); np.savez(cache, day=tday, **M); print("mass series cached in", cache, flush=True)
        with xr.open_dataset(index[0][0], decode_times=False) as d:
            nsp0 = np.asarray(d.normalized_surface_pressure.isel(time=0))
        mass_figure(M, tday, names, term, sites, lat, lon, p_nom, nsp0, label, t0, os.path.join(a.outdir, f"{run}_tracer_mass.png"), os.path.join(a.outdir, f"{run}_tracer_mass.md"))


if __name__ == "__main__":
    main()
