#!/usr/bin/env python3
"""Phase 15: plan stage 2 (combinations) and stage 3 (the 5-year winner) from the stage-1 scores.

    python scripts/sweep_plan.py --scores docs/outputs/15_sweep/scores --matrix scripts/phase15_matrix.txt \
        --stage2 scripts/phase15_matrix_stage2.txt              # writes the stage-2 matrix, prints it
    python scripts/sweep_plan.py --scores ... --best             # prints the name of the best scored run (any stage)

Rules (fixed in advance so the unattended sweep needs no judgement calls):
  * the stage-1 runs belong to three knob FAMILIES - drag (ray*, hines*, lm), relaxation (tau*), other (spongeT, n100);
  * in each family the member with the lowest composite is the family's winner if it beats the base by more than
    MARGIN (0.02) - a smaller gain is noise at three years;
  * stage 2 = the pairwise combination of the drag and relaxation winners, plus that pair with the "other" winner if
    there is one, plus the drag winner with the relaxation winner's family runner-up when the two relaxation knobs
    both beat the base (the two act on different levels). Combinations that would repeat a stage-1 run are dropped.
    A Rayleigh winner is also tried at the neighbouring strength (tau x 0.5 if the strong one won, x 2 if the weak one).
  * stage 3 = the run with the lowest composite over all stages (``--best``), extended to 1990-1994.
The physics group of a combination follows from the drag terms it needs (strat15_jucker[_hines][_lm][_ray]); the
overrides are the union of the members' overrides. Output line format = scripts/phase15_matrix.txt's.
"""
from __future__ import annotations

import argparse, glob, json, os, re

MARGIN = 0.02
FAMILY = {"drag": re.compile(r"^(ray|hines|lm)"), "relax": re.compile(r"^tau"), "other": re.compile(r"^(spongeT|n100)")}


def read_matrix(path):
    rows = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, phys, ov, desc = [c.strip() for c in line.split("|", 3)]
        rows[name] = dict(name=name, physics=phys, overrides=[] if ov == "-" else ov.split(), desc=desc)
    return rows


def group_for(physics_groups):
    flags = {k: any(k in g for g in physics_groups) for k in ("hines", "lm", "ray")}
    return "strat15_jucker" + "".join(f"_{k}" for k in ("hines", "lm", "ray") if flags[k])


def combine(name, members, desc):
    ov = []
    for m in members:
        for o in m["overrides"]:
            if o not in ov:
                ov.append(o)
    return dict(name=name, physics=group_for([m["physics"] for m in members]), overrides=ov, desc=desc)


def fmt(row):
    return f"{row['name']:<14} | {row['physics']:<26} | {' '.join(row['overrides']) or '-':<60} | {row['desc']}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", required=True); ap.add_argument("--matrix", default=None); ap.add_argument("--stage2", default=None)
    ap.add_argument("--best", action="store_true"); ap.add_argument("--margin", type=float, default=MARGIN)
    ap.add_argument("--top", type=int, default=0, help="print the N best CHANGED runs (not the base, not *_5yr rows), one per line")
    a = ap.parse_args()
    scores = {}
    for f in glob.glob(os.path.join(a.scores, "*.json")):
        r = json.load(open(f)); scores[r["name"]] = r
    if a.best:
        best = min(scores.values(), key=lambda r: r["composite"]); print(best["name"]); return
    if a.top:
        cands = sorted([r for n, r in scores.items() if n != "base" and not n.endswith("_5yr")], key=lambda r: r["composite"])
        print("\n".join(r["name"] for r in cands[:a.top])); return
    matrix = read_matrix(a.matrix)
    base = scores.get("base")
    if base is None:
        raise SystemExit("no base score")
    winners, notes = {}, []
    for fam, rx in FAMILY.items():
        members = sorted([r for n, r in scores.items() if rx.match(n) and n in matrix], key=lambda r: r["composite"])
        if not members:
            notes.append(f"{fam}: no scored member"); continue
        w = members[0]
        if w["composite"] < base["composite"] - a.margin:
            winners[fam] = members
            notes.append(f"{fam}: winner {w['name']} ({w['composite']:.3f} vs base {base['composite']:.3f})")
        else:
            notes.append(f"{fam}: best member {w['name']} ({w['composite']:.3f}) does not beat the base ({base['composite']:.3f}) by {a.margin}")
    rows = []
    d, rl, ot = (winners.get(k) for k in ("drag", "relax", "other"))
    if d and rl:
        rows.append(combine(f"{d[0]['name']}+{rl[0]['name']}", [matrix[d[0]["name"]], matrix[rl[0]["name"]]], f"stage 2: {matrix[d[0]['name']]['desc']} + {matrix[rl[0]['name']]['desc']}"))
        if len(rl) > 1 and rl[1]["composite"] < base["composite"] - a.margin:
            rows.append(combine(f"{d[0]['name']}+{rl[1]['name']}", [matrix[d[0]["name"]], matrix[rl[1]["name"]]], f"stage 2: {matrix[d[0]['name']]['desc']} + {matrix[rl[1]['name']]['desc']}"))
    if d and ot:
        rows.append(combine(f"{d[0]['name']}+{ot[0]['name']}", [matrix[d[0]["name"]], matrix[ot[0]["name"]]], f"stage 2: {matrix[d[0]['name']]['desc']} + {matrix[ot[0]['name']]['desc']}"))
    if d and rl and ot:
        rows.append(combine(f"{d[0]['name']}+{rl[0]['name']}+{ot[0]['name']}", [matrix[d[0]["name"]], matrix[rl[0]["name"]], matrix[ot[0]["name"]]],
                            f"stage 2: {matrix[d[0]['name']]['desc']} + {matrix[rl[0]['name']]['desc']} + {matrix[ot[0]['name']]['desc']}"))
    if rl and ot and not d:
        rows.append(combine(f"{rl[0]['name']}+{ot[0]['name']}", [matrix[rl[0]["name"]], matrix[ot[0]["name"]]], f"stage 2: {matrix[rl[0]['name']]['desc']} + {matrix[ot[0]['name']]['desc']}"))
    if d and d[0]["name"].startswith("ray"):
        m = re.search(r"tau_days=(\d+)", " ".join(matrix[d[0]["name"]]["overrides"]))
        if m:
            tau = int(m.group(1)); tau2 = tau // 2 if tau <= 10 else tau * 2 if tau >= 30 else tau // 2
            others = [n for n in scores if n.startswith("ray") and f"tau_days={tau2}" in " ".join(matrix.get(n, {}).get("overrides", []))]
            if not others:
                row = dict(matrix[d[0]["name"]]); row = dict(name=f"ray{tau2}", physics=row["physics"],
                           overrides=[o if not o.startswith("physics.terms.rayleigh_drag.tau_days=") else f"physics.terms.rayleigh_drag.tau_days={tau2}" for o in row["overrides"]],
                           desc=f"stage 2: Rayleigh drag 30 -> 1 hPa, tau {tau2} d (neighbour of the stage-1 winner {d[0]['name']})")
                rows.append(row)
    rows = [r for r in rows if r["name"] not in scores]
    hdr = ["# Phase 15 stage 2 (written by scripts/sweep_plan.py from the stage-1 scores):"] + [f"#   {n}" for n in notes]
    text = "\n".join(hdr + [fmt(r) for r in rows]) + "\n"
    if a.stage2:
        open(a.stage2, "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
