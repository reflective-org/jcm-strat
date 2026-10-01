#!/usr/bin/env python3
"""Phase 15: one number (and its parts) for how close a run's stratosphere is to CLaMS / ERA5.

    python scripts/sweep_score.py runs/p15_ray10_3yr --name ray10 --out docs/outputs/15_sweep/scores \
        [--window-years 2] [--age-days 60] [--desc "Rayleigh 30-1 hPa, tau 10 d"]

Reads a chained run's archive (6-hourly instantaneous frames; EVERY frame is used - the TEM eddy covariance from a single
daily phase is biased by the model's tides, see the Phase 15 record) over the LAST ``--window-years`` years (the first year
of a 3-year run is spin-up) and scores four things, each against the best reference this repo has:

  age    entry-age clock ``aoa150`` (reset below 150 hPa) vs the CLaMS v3.1/ERA5 mean age 2005-2009 minus CLaMS'
         own tropical age at 150 hPa (0.09 yr; scripts/aoa_vs_clams.py): cos-weighted RMSE over 100-5 hPa, |lat| <= 80.
         The surface clock ``aoa_sfc`` vs CLaMS AGE itself is reported too but not scored: the dry troposphere's transit
         (Phase 12 addendum) puts 1.5-2 yr on it that no stratospheric knob can remove.
  w*     TEM residual vertical velocity, tropics 15S-15N, at 100/70/50/30/10 hPa vs WACCM6 histSST 1996-2014
         (scripts/strat_circulation.py, as scripts/phase12_compare.py): mean |ln(w*_model / w*_WACCM)| with w* floored at
         0.02 mm/s and each level capped at ln(10). CLaMS has no w*; WACCM6 is the circulation reference of Phases 12-13.
  u, T   zonal-mean climatology 100-1 hPa, DJF and JJA of the window, vs ERA5 monthly zonal means of the SAME months
         (scripts/strat_compare.py loaders): cos-weighted RMSE, averaged over the two seasons.

composite = mean( age_rmse / 0.5 yr,  w*_logerr / ln 1.5,  u_rmse / 5 m/s,  T_rmse / 5 K )  - lower is better; 1.0 means
"half a year of age, a factor 1.5 in w*, 5 m/s and 5 K", i.e. every part at the edge of what Phases 12-13 called acceptable.
Also written: the Phase 12/13 table numbers (tropical / 50-70 deg ages at 55 and 12 hPa for the three clocks, upward mass
flux at 100/70/30/10 hPa, mesospheric w* at 5-0.5 hPa tropics / polar caps), the profiles the leaderboard plots, and the
run's end-to-end minutes per simulated year from the [launch] lines of its log. References (WACCM w*, CLaMS age, WACCM
entry age) are computed once and cached in ``cache/sweep_refs/``.
"""
from __future__ import annotations

import argparse, glob, json, os, re, sys, datetime as dt
import numpy as np
import xarray as xr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strat_circulation as circ      # noqa: E402
import strat_compare as sc            # noqa: E402
import aoa_vs_clams as aoa            # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(REPO, "cache", "sweep_refs")
P0_HPA = 1013.25
SEASONS = {"annual": tuple(range(1, 13)), "DJF": (12, 1, 2), "JJA": (6, 7, 8)}
W_LEVELS = (100.0, 70.0, 50.0, 30.0, 10.0)
FLUX_LEVELS = (100.0, 70.0, 30.0, 10.0)
MESO_LEVELS = (5.0, 2.0, 1.0, 0.5)
CLAMS_YEARS = list(range(2005, 2010))
WACCM_YEARS = list(range(1996, 2015))
# normalisation of the composite: "acceptable" size of each error (PLANS Phase 13 acceptance)
NORM = dict(age=0.5, w=np.log(1.5), u=5.0, T=5.0)
W_FLOOR, W_CAP = 0.02, np.log(10.0)


def _files(rundir):
    fs = sorted(glob.glob(os.path.join(rundir, "longrun_day*.nc")), key=lambda q: int(re.search(r"_day(\d+)\.nc$", q).group(1)))
    if not fs:
        raise SystemExit(f"no longrun_day*.nc in {rundir}")
    return fs


def band(lat, row, lo, hi):
    m = (np.abs(lat) >= lo) & (np.abs(lat) <= hi) & np.isfinite(row)
    w = np.cos(np.deg2rad(lat[m]))
    return float(np.sum(row[m] * w) / np.sum(w))


def at_level(p_hpa, field, target):
    return field[int(np.argmin(np.abs(p_hpa - target)))]


def on_grid(field, p_src_hpa, lat_src, p_dst_hpa, lat_dst):
    """(p, lat) field -> (p_dst, lat_dst), linear in log p and latitude, NaN outside the source range."""
    o = np.argsort(p_src_hpa); lp, lpo = np.log(p_src_hpa[o]), np.log(np.asarray(p_dst_hpa, float))
    f = field[o]
    ol = np.argsort(lat_src); f = f[:, ol]; lat_s = lat_src[ol]
    tmp = np.stack([np.interp(lat_dst, lat_s, f[k], left=np.nan, right=np.nan) for k in range(f.shape[0])])   # (p_src, lat_dst)
    out = np.stack([np.interp(lpo, lp, tmp[:, j], left=np.nan, right=np.nan) for j in range(tmp.shape[1])], axis=1)
    return out


def weighted_rmse(diff, lat, mask=None):
    w = np.cos(np.deg2rad(lat))[None, :] * np.ones_like(diff)
    ok = np.isfinite(diff) if mask is None else (np.isfinite(diff) & mask)
    return float(np.sqrt(np.sum((w * diff ** 2)[ok]) / np.sum(w[ok]))), float(np.sum((w * diff)[ok]) / np.sum(w[ok]))


# ------------------------------------------------------------------------------------------------ model archive
def load_model(rundir, window_years=2.0, age_days=60.0):
    """Zonal means of every frame in the last ``window_years`` years, and the clocks over the last ``age_days`` days."""
    files = _files(rundir)
    last = xr.open_dataset(files[-1], decode_times=True)
    t_end = last.time.values[-1]; last.close()
    t0 = t_end - np.timedelta64(int(round(window_years * 365.25 * 24)), "h")
    t_age = t_end - np.timedelta64(int(round(age_days * 24)), "h")
    ub, vb, tb, thb, vth, omb, times = [], [], [], [], [], [], []
    ages = {k: [] for k in ("aoa150", "aoa_sfc", "aoa500")}
    p_hpa = lat = None
    for f in files:
        d = xr.open_dataset(f, decode_times=True)
        sel = d.time.values > t0
        if not sel.any():
            d.close(); continue
        d = d.isel(time=np.where(sel)[0])
        p_hpa = d.level.values * P0_HPA; lat = d.lat.values
        theta = d.temperature * (1000.0 / p_hpa)[None, :, None, None] ** circ.KAPPA
        v = d.v_wind; vbar = v.mean("lon"); thbar = theta.mean("lon")
        ub.append(d.u_wind.mean("lon").values); vb.append(vbar.values); tb.append(d.temperature.mean("lon").values)
        thb.append(thbar.values); vth.append(((v - vbar) * (theta - thbar)).mean("lon").values)
        omb.append(d.omega.mean("lon").values); times.append(d.time.values)
        asel = d.time.values > t_age
        if asel.any():
            for k in ages:
                if k in d:
                    ages[k].append(d[k].isel(time=np.where(asel)[0]).mean("lon").values)
        d.close()
    t = np.concatenate(times)
    mk = lambda arr: xr.DataArray(np.concatenate(arr), dims=("time", "level", "lat"), coords={"time": t, "level": p_hpa, "lat": lat})
    fields = dict(u=mk(ub), v=mk(vb), T=mk(tb), th=mk(thb), vth=mk(vth), om=mk(omb))
    age = {k: np.concatenate(v).mean(0) / 365.25 for k, v in ages.items() if v}     # (lev, lat), years
    return fields, age, p_hpa, lat, (str(t[0])[:10], str(t_end)[:10], int(t.size))


def wstar_fields(fields, months):
    m = fields["v"].time.dt.month
    keep = m.isin(list(months))
    vbar = fields["v"].where(keep, drop=True).mean("time").values
    cov = fields["vth"].where(keep, drop=True).mean("time").values
    th = fields["th"].where(keep, drop=True).mean("time").values
    p_pa = fields["v"].level.values * 100.0; lat = fields["v"].lat.values
    p, vstar, psi = circ.tem_streamfunction(vbar, cov, th, p_pa, lat)
    return p / 100.0, lat, psi, circ.residual_w(p, psi, lat)          # p ascending in hPa


# ------------------------------------------------------------------------------------------------ references
def waccm_wstar():
    f = os.path.join(REF_DIR, "waccm_wstar.npz")
    if os.path.exists(f):
        z = np.load(f); return {s: (z[f"{s}_p"], z[f"{s}_lat"], z[f"{s}_psi"], z[f"{s}_w"]) for s in SEASONS}
    os.makedirs(REF_DIR, exist_ok=True)
    print("[refs] computing WACCM6 w* 1996-2014 (cached afterwards)", flush=True)
    V, VTH, TH = circ.waccm_tem_fields(WACCM_YEARS)
    out, save = {}, {}
    for s, months in SEASONS.items():
        vbar = circ.seasonal(V, months, "month"); cov = circ.seasonal(VTH, months, "month"); th = circ.seasonal(TH, months, "month")
        p, vstar, psi = circ.tem_streamfunction(vbar.values, cov.values, th.values, V.level.values, V.lat.values)
        w = circ.residual_w(p, psi, V.lat.values)
        out[s] = (p / 100.0, V.lat.values, psi, w)
        save.update({f"{s}_p": p / 100.0, f"{s}_lat": V.lat.values, f"{s}_psi": psi, f"{s}_w": w})
    np.savez(f, **save)
    return out


def clams_ref():
    f = os.path.join(REF_DIR, "clams_age.npz")
    if os.path.exists(f):
        z = np.load(f); return z["p"], z["lat"], z["age"]
    os.makedirs(REF_DIR, exist_ok=True)
    p, lat, age = aoa.clams_age(CLAMS_YEARS)
    np.savez(f, p=p, lat=lat, age=age); return p, lat, age


def waccm_age_ref():
    f = os.path.join(REF_DIR, "waccm_entry_age.npz")
    if os.path.exists(f):
        z = np.load(f); return z["p"], z["lat"], z["age"]
    os.makedirs(REF_DIR, exist_ok=True)
    p, lat, age = aoa.waccm_age(CLAMS_YEARS)
    np.savez(f, p=p, lat=lat, age=age); return p, lat, age


def minutes_per_year(rundir):
    """Mean end-to-end minutes per segment from the [launch] start/exit line pairs of log.txt (segments are calendar years)."""
    log = os.path.join(rundir, "log.txt")
    if not os.path.exists(log):
        return None
    starts, durs = [], []
    for line in open(log, errors="replace"):
        m = re.match(r"\[launch\] (\S+) (.*)", line)
        if not m:
            continue
        ts = dt.datetime.fromisoformat(m.group(1))
        if "exit=" in m.group(2):
            if starts:
                durs.append((ts - starts.pop()).total_seconds() / 60.0)
        else:
            starts.append(ts)
    return float(np.mean(durs)) if durs else None


# ------------------------------------------------------------------------------------------------ score
def score(rundir, window_years, age_days):
    fields, age, p_hpa, lat, span = load_model(rundir, window_years, age_days)
    out = {"window": {"start": span[0], "end": span[1], "frames": span[2], "years": window_years, "age_days": age_days}}

    # --- w* vs WACCM6
    wref = waccm_wstar()
    wm = {s: wstar_fields(fields, months) for s, months in SEASONS.items()}
    w_terms = []
    for s in SEASONS:
        p, la, psi, w = wm[s]; pw, law, psiw, ww = wref[s]
        for lv in W_LEVELS:
            out[f"wstar_{s}_{lv:g}"] = circ.tropical_wstar(p * 100.0, w, la, lv)
            out[f"wstar_waccm_{s}_{lv:g}"] = circ.tropical_wstar(pw * 100.0, ww, law, lv)
        for lv in FLUX_LEVELS:
            out[f"flux_{s}_{lv:g}"] = circ.upward_mass_flux(p * 100.0, psi, lv, la) / 1e9
            out[f"flux_waccm_{s}_{lv:g}"] = circ.upward_mass_flux(pw * 100.0, psiw, lv, law) / 1e9
    for lv in W_LEVELS:
        a, b = out[f"wstar_annual_{lv:g}"], out[f"wstar_waccm_annual_{lv:g}"]
        w_terms.append(min(abs(np.log(max(a, W_FLOOR) / max(b, W_FLOOR))), W_CAP))
    out["w_logerr"] = float(np.mean(w_terms))
    p, la, _, w = wm["annual"]
    for lv in MESO_LEVELS:
        row = at_level(p, w, lv)
        out[f"meso_{lv:g}_tropics"] = band(la, row, 0, 15); out[f"meso_{lv:g}_nh"] = band(la, row, 60, 88); out[f"meso_{lv:g}_sh"] = band(la, np.where(la < 0, row, np.nan), 60, 88)
    trop = np.abs(la) <= 15
    wgt = np.cos(np.deg2rad(la[trop]))
    out["profile_p"] = [float(x) for x in p]
    out["profile_wstar_tropics"] = [float(np.nansum(w[k, trop] * wgt) / np.sum(wgt)) for k in range(p.size)]
    pw, law, _, ww = wref["annual"]; tropw = np.abs(law) <= 15; wgtw = np.cos(np.deg2rad(law[tropw]))
    out["profile_waccm_p"] = [float(x) for x in pw]
    out["profile_waccm_wstar_tropics"] = [float(np.nansum(ww[k, tropw] * wgtw) / np.sum(wgtw)) for k in range(pw.size)]

    # --- age vs CLaMS (entry age) and WACCM6 entry age
    pc, latc, ac = clams_ref(); pwa, latwa, awa = waccm_age_ref()
    k150 = int(np.argmin(np.abs(pc - 150.0))); offset = band(latc, ac[k150], 0, 10)
    k500 = int(np.argmin(np.abs(pc - 500.0))); offset500 = band(latc, ac[k500], 0, 10)
    out["clams_offset_150"] = offset; out["clams_offset_500"] = offset500
    dom = (pc >= 5.0) & (pc <= 100.0)
    latmask = (np.abs(latc) <= 80.0)[None, :] & dom[:, None]
    for clock, off in (("aoa150", offset), ("aoa_sfc", 0.0), ("aoa500", offset500)):
        if clock not in age:
            continue
        am = on_grid(age[clock], p_hpa, lat, pc, latc)
        rm, bias = weighted_rmse(am - (ac - off), latc, latmask)
        out[f"age_rmse_{clock}"] = rm; out[f"age_bias_{clock}"] = bias
        for lv, tag in ((55.0, "55"), (12.0, "12")):
            row = at_level(p_hpa, age[clock], lv)
            out[f"age_{clock}_{tag}_tropics"] = band(lat, row, 0, 10); out[f"age_{clock}_{tag}_5070"] = band(lat, row, 50, 70)
    for lv, tag in ((55.0, "55"), (12.0, "12")):
        rc = at_level(pc, ac, lv); rw = at_level(pwa, awa, lv)
        out[f"age_clams_{tag}_tropics"] = band(latc, rc, 0, 10); out[f"age_clams_{tag}_5070"] = band(latc, rc, 50, 70)
        out[f"age_waccm_{tag}_tropics"] = band(latwa, rw, 0, 10); out[f"age_waccm_{tag}_5070"] = band(latwa, rw, 50, 70)
    if "aoa150" in age:
        out["profile_lat"] = [float(x) for x in lat]
        out["profile_age150_55"] = [float(x) for x in at_level(p_hpa, age["aoa150"], 55.0)]
        out["profile_age150_12"] = [float(x) for x in at_level(p_hpa, age["aoa150"], 12.0)]
        tm = np.abs(lat) <= 10
        out["profile_age150_tropics"] = [float(x) for x in np.nanmean(age["aoa150"][:, tm], axis=1)]
        out["profile_age_p"] = [float(x) for x in p_hpa]
        out["profile_clams_lat"] = [float(x) for x in latc]
        out["profile_clams_entry_55"] = [float(x) for x in at_level(pc, ac, 55.0) - offset]
        out["profile_clams_entry_12"] = [float(x) for x in at_level(pc, ac, 12.0) - offset]
        tc = np.abs(latc) <= 10
        out["profile_clams_p"] = [float(x) for x in pc]
        out["profile_clams_entry_tropics"] = [float(x) for x in np.nanmean(ac[:, tc], axis=1) - offset]

    # --- u, T climatology vs ERA5 (same months)
    t = fields["u"].time
    years = sorted({int(y) for y in np.unique(t.dt.year.values)})
    era5, _ = sc.load_era5(years, lat)
    u_rm, t_rm = [], []
    for s in ("DJF", "JJA"):
        months = SEASONS[s]
        keep = t.dt.month.isin(list(months))
        um = fields["u"].where(keep, drop=True).mean("time"); tm_ = fields["T"].where(keep, drop=True).mean("time")
        mod = xr.Dataset({"u": um, "T": tm_}).rename(level="lev")
        mod = sc._interp_logp(mod, mod.lev.values, sc.P_LEVELS, "lev")
        ek = (era5.time > np.datetime64(span[0])) & (era5.time <= np.datetime64(span[1])) & era5.time.dt.month.isin(list(months))
        ref = era5.where(ek, drop=True).mean("time")
        ur, tr = sc.rmse(mod["u"], ref["u"], mod.lat), sc.rmse(mod["T"], ref["T"], mod.lat)
        out[f"u_rmse_{s}"] = ur; out[f"T_rmse_{s}"] = tr; u_rm.append(ur); t_rm.append(tr)
        for latj, tag in ((60.0, "60N"), (-60.0, "60S")):
            out[f"u10_{tag}_{s}"] = float(mod["u"].sel(plev=10.0).interp(lat=latj)); out[f"u10_era5_{tag}_{s}"] = float(ref["u"].sel(plev=10.0).interp(lat=latj))
        cap = mod.lat > 60 if s == "DJF" else mod.lat < -60
        out[f"Tcap_bias_{s}"] = float((mod["T"] - ref["T"]).sel(plev=slice(10, 50)).where(cap).mean())
    out["u_rmse"] = float(np.mean(u_rm)); out["T_rmse"] = float(np.mean(t_rm))

    # --- composite
    parts = {"age": out.get("age_rmse_aoa150", np.nan) / NORM["age"], "w": out["w_logerr"] / NORM["w"],
             "u": out["u_rmse"] / NORM["u"], "T": out["T_rmse"] / NORM["T"]}
    out.update({f"score_{k}": float(v) for k, v in parts.items()})
    out["composite"] = float(np.mean(list(parts.values())))
    out["minutes_per_year"] = minutes_per_year(rundir)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rundir"); ap.add_argument("--name", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--desc", default=""); ap.add_argument("--stage", default="")
    ap.add_argument("--window-years", type=float, default=2.0); ap.add_argument("--age-days", type=float, default=60.0)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    res = score(a.rundir, a.window_years, a.age_days)
    res.update({"name": a.name, "rundir": os.path.abspath(a.rundir), "desc": a.desc, "stage": a.stage,
                "scored_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    cfg = os.path.join(a.rundir, ".hydra", "config.yaml")
    if os.path.exists(cfg):
        res["config_yaml"] = cfg
    f = os.path.join(a.out, f"{a.name}.json")
    json.dump(res, open(f, "w"), indent=1)
    print(f"[score {a.name}] composite {res['composite']:.3f} = mean(age {res['score_age']:.2f}, w* {res['score_w']:.2f}, "
          f"u {res['score_u']:.2f}, T {res['score_T']:.2f}); age150 RMSE vs CLaMS-entry {res.get('age_rmse_aoa150', float('nan')):.2f} yr "
          f"(bias {res.get('age_bias_aoa150', float('nan')):+.2f}); tropical w* 100/70/50/30/10: "
          + "/".join(f"{res[f'wstar_annual_{lv:g}']:.2f}" for lv in W_LEVELS)
          + f" (WACCM " + "/".join(f"{res[f'wstar_waccm_annual_{lv:g}']:.2f}" for lv in W_LEVELS) + f"); u RMSE {res['u_rmse']:.1f} m/s, "
          f"T RMSE {res['T_rmse']:.1f} K; {res['minutes_per_year'] or float('nan'):.0f} min/yr -> {f}")


if __name__ == "__main__":
    main()
