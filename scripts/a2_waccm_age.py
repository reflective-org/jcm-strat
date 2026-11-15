#!/usr/bin/env python3
"""A2 on the WACCM6 entry-age field (Susanne 2026-11-10): RMSE of the model's 150 hPa clock against the WACCM6 REF-D1
2-D entry age for the same years, cos-weighted over 100-5 hPa, |lat| <= 80, on the WACCM6 grid.

    SCORE_REF_YEARS=2011-2019 JAX_PLATFORMS=cpu python scripts/a2_waccm_age.py runs/p31_AL7h_1119 OUT.json

Replaces the old A2 (aoa150 against CLaMS shifted by CLaMS' own tropical 150 hPa age), whose 0.09 yr shift does not put
CLaMS on a 150 hPa clock. The clock is averaged over every frame of the run directory (as success_metrics.py does with
--age-days = the window). For comparison the old CLaMS-based number and the WACCM6 - shifted-CLaMS disagreement are
written too.
"""
import argparse
import json
import os
import sys

import numpy as np
import xarray as xr

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sweep_score as ss  # noqa: E402

BOUND = 0.4     # yr, as the old A2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir"); ap.add_argument("out")
    a = ap.parse_args()
    acc, n, p_hpa, lat = None, 0, None, None
    for f in ss._files(a.rundir):
        d = xr.open_dataset(f, decode_times=False)
        z = d["aoa150"].mean("lon")
        s = z.sum("time").values; k = z.sizes["time"]
        acc = s if acc is None else acc + s; n += k
        p_hpa = d.level.values * ss.P0_HPA; lat = d.lat.values
        d.close()
    age = acc / n / 365.25                                   # (lev, lat) years

    pw, latw, aw = ss.waccm_age_ref()
    pc, latc, ac = ss.clams_ref()
    out = {"years": ss.CLAMS_YEARS[0:1] + ss.CLAMS_YEARS[-1:], "frames": int(n)}
    for tag, (pr, latr, ar, off) in {"waccm": (pw, latw, aw, 0.0),
                                     "clams": (pc, latc, ac, ss.band(latc, ac[int(np.argmin(np.abs(pc - 150.0)))], 0, 10))}.items():
        am = ss.on_grid(age, p_hpa, lat, pr, latr)
        mask = (np.abs(latr) <= 80.0)[None, :] & ((pr >= 5.0) & (pr <= 100.0))[:, None]
        rm, bias = ss.weighted_rmse(am - (ar - off), latr, mask)
        out[f"rmse_{tag}"], out[f"bias_{tag}"] = rm, bias
    # how far apart the two references are on this measure
    cw = ss.on_grid(ac - out.get("clams_offset", ss.band(latc, ac[int(np.argmin(np.abs(pc - 150.0)))], 0, 10)), pc, latc, pw, latw)
    mask = (np.abs(latw) <= 80.0)[None, :] & ((pw >= 5.0) & (pw <= 100.0))[:, None]
    out["rmse_waccm_vs_clams"], out["bias_waccm_vs_clams"] = ss.weighted_rmse(aw - cw, latw, mask)
    out["err"] = out["rmse_waccm"] / BOUND
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    main()
