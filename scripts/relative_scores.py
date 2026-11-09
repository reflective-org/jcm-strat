#!/usr/bin/env python3
"""Relative scorecard (Susanne 2026-11-09): every metric as a relative deviation from its reference, one common tolerance.

    python scripts/relative_scores.py SUCCESS_JSON OUTDIR [--drop QBO30] [--tol 0.25]

Reads success_metrics.json (groups A-C and D, scripts/success_metrics.py) and rescores it:
  rel = model / ref - 1 (-40 % = 40 % too small, also for a negative slope), err = |rel| / tol   (tol 25 %: pass err <= 1, near <= 1.5, fail beyond, as before)
  A4 (a range, 2.3-3.2 yr) is taken relative to its midpoint 2.75 yr.
Metrics with no meaningful relative form keep their absolute bound and error, as Susanne chose:
  A2 (2-D age RMSE, reference 0), C1 jet latitudes (+-4 deg), C2 polar-cap T bias (reference 0, +-2 K),
  D4-fwN/S final-warming dates (+-10 days).
Group scores are the mean err per group; combined = mean of A, B, C; D separate. QBO30 is dropped by default: its
QBO is unacceptable (50 hPa amplitude 7.0 vs ERA5 11.3 m/s, 2-3 months late).
Writes OUTDIR/relative_metrics.json (one row per metric, a column per run), relative_scores.json (one row per run)
and relative_table.md.
"""
import argparse, json, os
import numpy as np

ABSOLUTE = {"A2", "C1-jet50_N-lat", "C1-jet10_N-lat", "C1-jet50_S-lat", "C1-jet10_S-lat", "C2-N", "C2-S", "D4-fwN", "D4-fwS"}
ABS_BOUND = {"A2": "< 0.4 yr", "C2-N": "± 2 K", "C2-S": "± 2 K", "D4-fwN": "± 10 days", "D4-fwS": "± 10 days"}


def status(e):
    return "pass" if e <= 1 else ("near" if e <= 1.5 else "fail")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("success_json"); ap.add_argument("outdir")
    ap.add_argument("--drop", nargs="*", default=["QBO30"]); ap.add_argument("--tol", type=float, default=0.25)
    a = ap.parse_args()
    S = json.load(open(a.success_json))
    runs = [n for n in S if n not in a.drop]
    first = S[runs[0]]["metrics"] + S[runs[0]].get("D_metrics", [])
    rows, per = [], {n: {g: [] for g in "ABCD"} for n in runs}
    for i, m0 in enumerate(first):
        mid = m0["id"]; absolute = mid in ABSOLUTE
        ref = m0["ref"]; refv = float(np.mean(ref)) if isinstance(ref, list) else float(ref)
        row = {"order": i, "id": mid, "group": m0["group"], "metric": m0["label"],
               "reference": (f"{ref[0]:g}-{ref[1]:g} (mid {refv:.2f})" if isinstance(ref, list) else f"{refv:.3g}"),
               "unit": ({"A2": "yr", "C2-N": "K", "C2-S": "K", "D4-fwN": "days", "D4-fwS": "days"}.get(mid, "deg") if absolute else "%"),
               "basis": ABS_BOUND.get(mid, "± 4 deg") if absolute else f"± {a.tol:.0%} of reference"}
        for n in runs:
            m = next(x for x in S[n]["metrics"] + S[n].get("D_metrics", []) if x["id"] == mid)
            if absolute:
                d = abs(m["model"]) - abs(refv) if "lat" in mid else m["model"] - refv
                err = m["err"]; val = round(d, 2)                # absolute difference in the metric's own unit
            else:
                rel = m["model"] / refv - 1; err = abs(rel) / a.tol; val = round(100 * rel, 1)   # %
            row[n] = val; row[f"{n}_err"] = round(err, 3); row[f"{n}_status"] = status(err)
            per[n][m0["group"]].append(err)
        rows.append(row)
    scores = []
    for n in runs:
        g = {k: float(np.mean(v)) for k, v in per[n].items()}
        scores.append({"run": n, "A": round(g["A"], 2), "B": round(g["B"], 2), "C": round(g["C"], 2),
                       "combined": round((g["A"] + g["B"] + g["C"]) / 3, 2),
                       "passed": int(sum(e <= 1 for k in "ABC" for e in per[n][k])), "total": sum(len(per[n][k]) for k in "ABC"),
                       "D": round(g["D"], 2), "D_passed": int(sum(e <= 1 for e in per[n]["D"])), "D_total": len(per[n]["D"])})
    os.makedirs(a.outdir, exist_ok=True)
    json.dump({"rows": rows}, open(os.path.join(a.outdir, "relative_metrics.json"), "w"), indent=1)
    json.dump({"rows": scores}, open(os.path.join(a.outdir, "relative_scores.json"), "w"), indent=1)
    sym = {"pass": "✅", "near": "⚠️", "fail": "❌"}
    L = [f"Relative scores: % off the reference, tolerance ± {a.tol:.0%}; absolute metrics marked (abs). Runs: {', '.join(runs)}.", "",
         "| metric | reference | basis | " + " | ".join(runs) + " |", "|---|---|---|" + "---|" * len(runs)]
    for r in rows:
        u = "" if r["id"] in ABSOLUTE else "%"
        L.append(f"| **{r['id']}** {r['metric']} | {r['reference']} | {r['basis']} | "
                 + " | ".join(f"{sym[r[n + '_status']]} {r[n]:+g}{u}" for n in runs) + " |")
    L += ["", "| | " + " | ".join(runs) + " |", "|---|" + "---|" * len(runs)]
    for k, lab in (("A", "A age"), ("B", "B circulation"), ("C", "C vortex"), ("combined", "**combined**"), ("D", "D variability")):
        L.append(f"| {lab} | " + " | ".join(f"{s[k]:.2f}" for s in scores) + " |")
    L.append("| passed A-C | " + " | ".join(f"{s['passed']} / {s['total']}" for s in scores) + " |")
    L.append("| passed D | " + " | ".join(f"{s['D_passed']} / {s['D_total']}" for s in scores) + " |")
    open(os.path.join(a.outdir, "relative_table.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[-8:]))


if __name__ == "__main__":
    main()
