#!/usr/bin/env python3
"""Phase 12: before/after comparison of the residual circulation (w*) and the age of air of two chained runs.

    python scripts/phase12_compare.py --before runs/p12ctl_5yr --after runs/p12noqbo_5yr \
        --tag noqbo --label "QBO nudging off" --out docs/outputs/12_circulation [--stride 4] [--clocks aoa_sfc aoa500]

w*: TEM residual vertical velocity in log-pressure coordinates, from the residual mass streamfunction
Psi*(phi, p) (scripts/strat_circulation.py: v* = [v] - d/dp([v'th'] / d[th]/dp), Psi* = 2 pi a cos(phi)/g int v* dp,
omega* = -(g / 2 pi a^2 cos(phi)) dPsi*/dphi, w* = -H omega*/p, H = 7 km). The eddy covariance is formed in every
snapshot of the 6-hourly archive (every ``--stride``-th frame, default 4 = daily) and averaged over the whole run
(annual) and DJF / JJA. Reference: WACCM6 histSST's daily zonal-mean TEM tape (Vzm, VTHzm, THzm), same formula,
``--waccm-years`` (default 1996-2014, the tape's extent; the model years 1990-1994 are not in it). The Eulerian
zonal-mean vertical velocity [w] = -H [omega]/p is drawn alongside in the tropical profile as a check.

Age of air: zonal mean of each clock in ``--clocks`` over the last ``--last-saves`` frames (default 240 = the last
60 days of a 6-hourly archive), before, after, difference, and CLaMS v3.1 / ERA5 (surface clock, ``--clams-years``
climatology, 2005-2009 by default: CLaMS starts in 2004) for orientation. Fields of runs on different level tables
(strat63 vs strat81) are interpolated in log p onto the "before" levels for the difference; the stratospheric
levels are identical, so that is exact there.

Writes <out>/<tag>_wstar.png, <tag>_wstar_tropics.png, <tag>_age_<clock>.png, <tag>_age_profiles.png and
<tag>_metrics.md (upward mass flux at 100/70/30/10 hPa, tropical w*, age at 55/12 hPa) and prints the table.
"""
from __future__ import annotations

import argparse, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_circulation as circ
import aoa_vs_clams as aoa

SEASONS = {"annual": tuple(range(1, 13)), "DJF": (12, 1, 2), "JJA": (6, 7, 8)}
W_LEVELS = np.array([-2, -1, -0.5, -0.3, -0.2, -0.1, -0.05, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2])
DW_LEVELS = np.array([-0.5, -0.3, -0.2, -0.1, -0.05, -0.02, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5])
H_KM = 7.0


def on_levels(field, p_src, p_dst):
    """(p, lat) field interpolated in log p onto p_dst (both Pa or both hPa, any order)."""
    if p_src.shape == p_dst.shape and np.allclose(p_src, p_dst):
        return field
    o = np.argsort(p_src)
    return np.stack([np.interp(np.log(p_dst), np.log(p_src[o]), field[o, j]) for j in range(field.shape[1])], axis=1)


def wstar_by_season(V, VTH, TH, month_coord=None):
    out = {}
    for seas, months in SEASONS.items():
        vbar = circ.seasonal(V, months, month_coord); cov = circ.seasonal(VTH, months, month_coord); th = circ.seasonal(TH, months, month_coord)
        p, vstar, psi = circ.tem_streamfunction(vbar.values, cov.values, th.values, V.level.values, V.lat.values)
        out[seas] = (p, V.lat.values, psi, circ.residual_w(p, psi, V.lat.values))
    return out


def eulerian_w(OM, months):
    """[w] = -H [omega]/p in mm/s on (p ascending, lat)."""
    om = circ.seasonal(OM, months).values
    p = OM.level.values; o = np.argsort(p)
    return p[o], -H_KM * 1e3 * om[o] / p[o][:, None] * 1e3


def monthly_tropical_w(V, VTH, TH, p_hpa=70.0, lat_max=15.0):
    """Monthly-mean fields -> tropical w* at p_hpa month by month (mm/s), decimal-year axis."""
    Vm, VTHm, THm = (x.resample(time="1MS").mean() for x in (V, VTH, TH))
    tdec = np.array([t.year + (t.month - 0.5) / 12 for t in Vm.indexes["time"]])
    w = []
    for i in range(Vm.sizes["time"]):
        p, _, psi = circ.tem_streamfunction(Vm.isel(time=i).values, VTHm.isel(time=i).values, THm.isel(time=i).values, V.level.values, V.lat.values)
        w.append(circ.tropical_wstar(p, circ.residual_w(p, psi, V.lat.values), V.lat.values, p_hpa, lat_max))
    return tdec, np.array(w)


def plot_w_panel(ax, lat, p, w, levels, title, cmap="RdBu_r", pmin=1.0, pmax=300.0):
    cf = ax.contourf(lat, p / 100.0, w, levels=levels, cmap=cmap, extend="both")
    ax.contour(lat, p / 100.0, w, levels=[0], colors="k", linewidths=0.6)
    ax.set_yscale("log"); ax.set_ylim(pmax, pmin); ax.set_title(title, fontsize=9)
    return cf


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", required=True); ap.add_argument("--after", required=True)
    ap.add_argument("--tag", required=True); ap.add_argument("--label", default="")
    ap.add_argument("--before-label", default=None); ap.add_argument("--after-label", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stride", default="4", help="every n-th frame for the TEM covariances (4 = daily on a 6-hourly archive), or 'auto' = the 00 UTC frames of any archive")
    ap.add_argument("--clocks", nargs="*", default=["aoa_sfc", "aoa500"])
    ap.add_argument("--last-saves", type=int, default=240, help="frames averaged for the age (240 = last 60 d of a 6-hourly archive)")
    ap.add_argument("--last-days", type=float, default=None, help="instead of --last-saves: days averaged for the age, converted per run from its save interval (daily vs 6-hourly archives)")
    ap.add_argument("--waccm-years", default="1996-2014"); ap.add_argument("--clams-years", default="2005-2009")
    ap.add_argument("--no-waccm", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    a.stride = "auto" if str(a.stride) == "auto" else int(a.stride)
    def frames_for(run, days):
        if days is None:
            return a.last_saves
        f0 = sorted(__import__("glob").glob(os.path.join(run, "longrun_day*.nc")))[0]
        t = __import__("xarray").open_dataset(f0, decode_times=True).time.values
        dt_days = float((t[1] - t[0]) / np.timedelta64(1, "D")) if t.size > 1 else 1.0
        return max(1, int(round(days / dt_days)))
    nb = a.before_label or os.path.basename(a.before.rstrip("/")); na = a.after_label or os.path.basename(a.after.rstrip("/"))
    title = a.label or f"{nb} -> {na}"
    lines = [f"# Phase 12 comparison: {title}", "", f"before `{a.before}`, after `{a.after}`; TEM covariances from every {a.stride}th 6-hourly frame;",
             f"age = last {a.last_saves} frames; WACCM6 histSST {a.waccm_years}; CLaMS v3.1/ERA5 {a.clams_years}.", ""]

    # ------------------------------------------------------------------ w*
    fields = {}
    for name, run in (("before", a.before), ("after", a.after)):
        print(f"[w*] loading {name}: {run} (stride {a.stride})", flush=True)
        V, VTH, TH, OM = circ.model_tem_fields(run, stride=a.stride, with_omega=True)
        fields[name] = (V, VTH, TH, OM, wstar_by_season(V, VTH, TH))
    waccm = None
    if not a.no_waccm:
        y0, y1 = map(int, a.waccm_years.split("-"))
        wv, wvth, wth = circ.waccm_tem_fields(list(range(y0, y1 + 1)))
        waccm = wstar_by_season(wv, wvth, wth, "month")

    ncol = 4 if waccm else 3
    fig, axes = plt.subplots(3, ncol, figsize=(4.8 * ncol + 1.5, 11), sharex=True, sharey=True, layout="constrained")
    for i, seas in enumerate(SEASONS):
        pb, lat, _, wb = fields["before"][4][seas]; pa, lata, _, wa = fields["after"][4][seas]
        wa_on_b = on_levels(wa, pa, pb)
        cf = plot_w_panel(axes[i, 0], lat, pb, wb, W_LEVELS, f"{seas}  before: {nb}")
        plot_w_panel(axes[i, 1], lata, pa, wa, W_LEVELS, f"{seas}  after: {na}")
        cfd = plot_w_panel(axes[i, 2], lat, pb, wa_on_b - wb, DW_LEVELS, f"{seas}  after - before", cmap="PuOr_r")
        if waccm:
            pw, latw, _, ww = waccm[seas]
            plot_w_panel(axes[i, 3], latw, pw, ww, W_LEVELS, f"{seas}  WACCM6 histSST {a.waccm_years}")
        axes[i, 0].set_ylabel("pressure [hPa]")
    for ax in axes[-1]: ax.set_xlabel("latitude")
    fig.colorbar(cf, ax=list(axes[:, -1]), shrink=0.8, pad=0.02, label="w* [mm/s]")
    fig.colorbar(cfd, ax=list(axes[:, 2]), shrink=0.8, pad=0.02, label="after - before [mm/s]")
    fig.suptitle(f"{title}: TEM residual vertical velocity w* (upward positive)")
    f = os.path.join(a.out, f"{a.tag}_wstar.png"); fig.savefig(f, dpi=120); plt.close(fig); print("wrote", f)

    # tropical profiles + annual cycle
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    ax = axes[0]
    for name, col in (("before", "C0"), ("after", "C3")):
        V, VTH, TH, OM, ws = fields[name]
        p, lat, _, w = ws["annual"]
        prof = np.array([circ.tropical_wstar(p, w, lat, ph) for ph in p / 100.0])
        ax.plot(prof, p / 100.0, color=col, label=f"w* {name}: {nb if name == 'before' else na}")
        pe, we = eulerian_w(OM, SEASONS["annual"])
        ax.plot([circ.tropical_wstar(pe, we, lat, ph) for ph in pe / 100.0], pe / 100.0, color=col, ls=":", lw=1, label=f"Eulerian [w] {name}")
    if waccm:
        p, lat, _, w = waccm["annual"]
        ax.plot([circ.tropical_wstar(p, w, lat, ph) for ph in p / 100.0], p / 100.0, "k--", label=f"w* WACCM6 {a.waccm_years}")
    ax.axvline(0, color="grey", lw=0.5); ax.set_yscale("log"); ax.set_ylim(300, 1)
    lo, hi = ax.get_xlim(); ax.set_xlim(max(lo, -3.0), min(hi, 3.0))          # noise in the eddy term can be large; keep the plot readable
    ax.set_xlabel("mm/s"); ax.set_ylabel("pressure [hPa]"); ax.set_title("tropical (15S-15N) w*, annual mean"); ax.grid(alpha=.3); ax.legend(fontsize=7)
    for ax, ph in zip(axes[1:], (70.0, 30.0)):
        for name, col in (("before", "C0"), ("after", "C3")):
            V, VTH, TH, _, _ = fields[name]
            t, w = monthly_tropical_w(V, VTH, TH, ph); ax.plot(t, w, color=col, label=name)
        if waccm:
            wv, wvth, wth = circ.waccm_tem_fields(list(range(y0, y1 + 1)))
            clim = []
            for m in range(1, 13):
                vbar = circ.seasonal(wv, (m,), "month"); cov = circ.seasonal(wvth, (m,), "month"); th = circ.seasonal(wth, (m,), "month")
                p, _, psi = circ.tem_streamfunction(vbar.values, cov.values, th.values, wv.level.values, wv.lat.values)
                clim.append(circ.tropical_wstar(p, circ.residual_w(p, psi, wv.lat.values), wv.lat.values, ph))
            tb = fields["before"][0].time
            for yr in sorted(set(tb.dt.year.values)):
                ax.plot(yr + (np.arange(12) + 0.5) / 12, clim, "k--", lw=0.8, label=f"WACCM6 climatology" if yr == min(tb.dt.year.values) else None)
        ax.set_title(f"tropical w* at {ph:.0f} hPa, monthly"); ax.set_xlabel("year"); ax.set_ylabel("mm/s"); ax.grid(alpha=.3); ax.legend(fontsize=7)
    fig.suptitle(f"{title}: tropical upwelling"); fig.tight_layout()
    f = os.path.join(a.out, f"{a.tag}_wstar_tropics.png"); fig.savefig(f, dpi=120); plt.close(fig); print("wrote", f)

    lines += ["## Residual circulation", "", "| quantity | season | before | after | after - before | WACCM6 |", "|---|---|---|---|---|---|"]
    srcs = [fields["before"][4], fields["after"][4]] + ([waccm] if waccm else [])
    for seas in SEASONS:
        for ph in (100, 70, 30, 10):
            vals = [circ.upward_mass_flux(s[seas][0], s[seas][2], ph, s[seas][1]) / 1e9 for s in srcs]
            lines.append(f"| upward mass flux {ph} hPa [1e9 kg/s] | {seas} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[1] - vals[0]:+.2f} | {vals[2]:.2f} |" if waccm
                         else f"| upward mass flux {ph} hPa [1e9 kg/s] | {seas} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[1] - vals[0]:+.2f} | - |")
        for ph in (100, 70, 50, 30, 10):
            vals = [circ.tropical_wstar(s[seas][0], s[seas][3], s[seas][1], ph) for s in srcs]
            lines.append(f"| tropical w* 15S-15N {ph} hPa [mm/s] | {seas} | {vals[0]:.3f} | {vals[1]:.3f} | {vals[1] - vals[0]:+.3f} | " + (f"{vals[2]:.3f} |" if waccm else "- |"))

    # ------------------------------------------------------------------ age of air
    cy0, cy1 = map(int, a.clams_years.split("-")); pc, latc, ac = aoa.clams_age(list(range(cy0, cy1 + 1)))
    lines += ["", "## Age of air (years; zonal mean of the last frames)", "",
              "| clock | level | region | before | after | after - before | CLaMS (surface clock) |", "|---|---|---|---|---|---|---|"]
    prof_rows = []
    vmax = 6.0; levels = np.linspace(0, vmax, 25)
    for clock in a.clocks:
        print(f"[age] {clock}", flush=True)
        pb, latb, ab, dayb = aoa.model_age(a.before, frames_for(a.before, a.last_days), clock); pa, lata, aa, daya = aoa.model_age(a.after, frames_for(a.after, a.last_days), clock)
        aa_on_b = on_levels(aa, pa, pb)
        fig, axes = plt.subplots(1, 4, figsize=(23, 5.2), sharey=True, layout="constrained")
        for ax, (p, lat, age, ttl) in zip(axes[:2], ((pb, latb, ab, f"before: {nb}  [{clock}] ends day {dayb}"), (pa, lata, aa, f"after: {na}  [{clock}] ends day {daya}"))):
            cf = ax.contourf(lat, p, age, levels=levels, cmap="viridis", extend="max"); ax.contour(lat, p, age, levels=levels[::4], colors="w", linewidths=0.5)
            ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_title(ttl, fontsize=9); ax.set_xlabel("latitude")
        dl = np.linspace(-1.5, 1.5, 16)
        cfd = axes[2].contourf(latb, pb, aa_on_b - ab, levels=dl, cmap="PuOr_r", extend="both"); axes[2].contour(latb, pb, aa_on_b - ab, levels=[0], colors="k", linewidths=0.5)
        axes[2].set_yscale("log"); axes[2].set_ylim(300, 1); axes[2].set_title("after - before [yr]", fontsize=9); axes[2].set_xlabel("latitude")
        axes[3].contourf(latc, pc, ac, levels=levels, cmap="viridis", extend="max"); axes[3].contour(latc, pc, ac, levels=levels[::4], colors="w", linewidths=0.5)
        axes[3].set_yscale("log"); axes[3].set_ylim(300, 1); axes[3].set_title(f"CLaMS v3.1 / ERA5 {a.clams_years}\n(surface clock; for orientation)", fontsize=9); axes[3].set_xlabel("latitude")
        axes[0].set_ylabel("pressure [hPa]")
        fig.colorbar(cf, ax=[axes[3]], shrink=0.9, pad=0.02, label="mean age [yr]"); fig.colorbar(cfd, ax=[axes[2]], shrink=0.9, pad=0.02, label="after - before [yr]")
        fig.suptitle(f"{title}: age of air, clock {clock} ({'reset in the lowest two layers' if clock == 'aoa_sfc' else 'reset below ' + clock[3:] + ' hPa' if clock[3:].isdigit() else clock})")
        f = os.path.join(a.out, f"{a.tag}_age_{clock}.png"); fig.savefig(f, dpi=120); plt.close(fig); print("wrote", f)
        for ph, lab in ((55.0, "55 hPa"), (12.0, "12 hPa")):
            kb = int(np.argmin(np.abs(pb - ph))); ka = int(np.argmin(np.abs(pa - ph))); kc = int(np.argmin(np.abs(pc - ph)))
            for lo, hi, reg in ((0, 10, "tropics 10S-10N"), (50, 70, "50-70 deg")):
                b, af, c = aoa.band(latb, ab[kb], lo, hi), aoa.band(lata, aa[ka], lo, hi), aoa.band(latc, ac[kc], lo, hi)
                lines.append(f"| {clock} | {lab} | {reg} | {b:.2f} | {af:.2f} | {af - b:+.2f} | {c:.2f} |")
        prof_rows.append((clock, (pb, latb, ab), (pa, lata, aa)))

    fig, axes = plt.subplots(len(prof_rows), 3, figsize=(16, 4.6 * len(prof_rows)), squeeze=False)
    for i, (clock, (pb, latb, ab), (pa, lata, aa)) in enumerate(prof_rows):
        for ax, ph in zip(axes[i, :2], (55.0, 12.0)):
            ax.plot(latb, ab[int(np.argmin(np.abs(pb - ph)))], "C0", label=f"before {nb}"); ax.plot(lata, aa[int(np.argmin(np.abs(pa - ph)))], "C3", label=f"after {na}")
            ax.plot(latc, ac[int(np.argmin(np.abs(pc - ph)))], "k--", label="CLaMS (surface clock)")
            ax.set_title(f"{clock}: mean age at ~{ph:.0f} hPa"); ax.set_xlabel("latitude"); ax.set_ylabel("yr"); ax.grid(alpha=.3); ax.legend(fontsize=7)
        ax = axes[i, 2]
        for (p, lat, age), col, lab in (((pb, latb, ab), "C0", "before"), ((pa, lata, aa), "C3", "after"), ((pc, latc, ac), "k", "CLaMS")):
            m = np.abs(lat) <= 10; ax.plot(np.nanmean(age[:, m], axis=1), p, color=col, ls="--" if lab == "CLaMS" else "-", label=lab)
        ax.set_yscale("log"); ax.set_ylim(300, 1); ax.set_xlabel("yr"); ax.set_ylabel("pressure [hPa]"); ax.set_title(f"{clock}: tropical (10S-10N) profile"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.suptitle(f"{title}: age-of-air profiles"); fig.tight_layout()
    f = os.path.join(a.out, f"{a.tag}_age_profiles.png"); fig.savefig(f, dpi=120); plt.close(fig); print("wrote", f)

    md = "\n".join(lines); print(md)
    with open(os.path.join(a.out, f"{a.tag}_metrics.md"), "w") as fh: fh.write(md + "\n")


if __name__ == "__main__":
    main()
