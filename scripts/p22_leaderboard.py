#!/usr/bin/env python3
"""Phase 22 leaderboard: docs/outputs/22_teq_vortex/scores/*.json -> leaderboard.md, sorted by u_ls_ext (lower is better)."""
import glob, json, os, sys
out = sys.argv[1]
rows = [json.load(open(f)) for f in glob.glob(os.path.join(out, "scores", "*.json"))]
rows.sort(key=lambda r: r["u_ls_ext"])
L = ["# Phase 22 leaderboard (window " + (rows[0]["window"] if rows else "") + ", vs ERA5 same months)\n",
     "u_ls_ext = RMSE of monthly zonal-mean u, 100-10 hPa, |lat| >= 30 (the ranking metric); jets = winter jet maximum over 30-90 deg "
     "[m/s @ lat] model (ERA5); cap T50 = polar-cap (60-90) T bias at 50 hPa in winter; w_logerr = mean |log(w*/w*_ERA5)| tropics 70-30 hPa "
     "(ERA5 1996-2001); age150 at 55 hPa (clocks carried from P20b, 3 years of the new circulation).\n",
     "| run | u_ls_ext | u50_ext | u_up_ext | T_ls | jet50 N | jet50 S | jet10 N | jet10 S | cap T50 N / S | w_logerr | age150 trop / 50-70N / 50-70S | description |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    j = lambda k: f"{r[k][0]:.0f}@{r[k][1]:.0f} ({r[k][2]:.0f}@{r[k][3]:.0f})"
    a = r.get("age150") or {}
    L.append(f"| {r['name']} | {r['u_ls_ext']:.2f} | {r['u50_ext']:.2f} | {r['u_up_ext']:.2f} | {r['T_ls']:.2f} | {j('jet50_N')} | {j('jet50_S')} | "
             f"{j('jet10_N')} | {j('jet10_S')} | {r['T50_cap_N']:+.1f} / {r['T50_cap_S']:+.1f} | {r.get('w_logerr')} | "
             f"{a.get('trop', '-')} / {a.get('n50_70', '-')} / {a.get('s50_70', '-')} | {r['desc']} |")
open(os.path.join(out, "leaderboard.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:6]))
