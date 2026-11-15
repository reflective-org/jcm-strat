#!/usr/bin/env python3
"""Write runs/INDEX.md: one row per run family in runs/, so the folder can be read without opening it (Susanne
2026-11-15, after the runs/ cleanup).

    python scripts/runs_index.py [--runs RUNS_DIR] [--out OUT.md]

A family is a run name without its segment/aggregate suffix (_YYYYMMDD, _YYYY_YYYY, _Nyr, _MMYY window, _agg,
_spinup...). For each family it lists the kinds of entries (segments with data, aggregates made of links, top-level
links to another run, other dirs), the years in the segment names, the size of the real files (symlinks are never
followed, so nothing is counted twice), whether the chunk files are compressed, a status note and the phase record.
Read-only on runs/ except for the output file. Uses only the standard library; h5py, if importable, adds the
compression column.
"""
import argparse
import collections
import datetime
import glob
import os
import re
import zoneinfo

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"logs", "archive", "__pycache__"}
SUFFIX = re.compile(r"(_spinup(_\d{8})?|_\d{8}|_\d{4}_\d{4}|_\d+yr|_agg|_\d{4}|_prefetch)$")

# Status notes, first match wins. Keep these short; the phase record has the detail.
NOTES = [
    (r"^p31_AL7h70$", "current: AL7h 1970-2022 on real ERA5, all tracers (Phase 31)"),
    (r"^p31_AL7h50$", "current: AL7h 1990-2039, ERA5 recycled after 2022, all tracers (Phase 31)"),
    (r"^p31_", "Phase 31 validation"),
    (r"^p20bt$", "reference: P20b 1990-2039 without the AL7h correction, all tracers"),
    (r"^p25_AL7h$", "AL7h chain 2005-2019 (Phase 31 validation); 2020-2030 = abandoned first 50-yr attempt"),
    (r"^p22_AL7$", "AL7, the chosen Phase 22 correction; scorecard run"),
    (r"^p22_.*_final$", "Phase 22 track not chosen (AL was)"),
    (r"_bench_|^p23s_", "timing / precision test"),
    (r"^p19jhn", "Phase 19 baseline, superseded by P20b"),
    (r"^p20jhsso", "Phase 20, blew up in 1997; superseded by 20b"),
    (r"^p21(echam|free)", "full physics on the current jcm: reference"),
    (r"^p2[3-9]|^p30", "2005-2010 restart run: scorecard input"),
]


def family(name):
    base = name[4:] if name.startswith("old_") else name
    while True:
        new = SUFFIX.sub("", base)
        if new == base:
            break
        base = new
    return ("old_" if name.startswith("old_") else "") + base


def phase_of(fam):
    m = re.match(r"(?:old_)?p(\d+)", fam)
    return int(m.group(1)) if m else None


def note_for(fam, ph, f):
    if f["seg"] == 0 and f["agg"] > 0:
        return "links only: aggregate / scoring window over other runs' segments"
    for rx, note in NOTES:
        if re.search(rx, fam):
            return note
    if ph is not None and ph < 19:
        return "old jcm version (before Phase 19): historical"
    return ""


def real_size(path):
    """Bytes of regular files under path, never following symlinks."""
    total, stack = 0, [path]
    while stack:
        with os.scandir(stack.pop()) as it:
            for e in it:
                if e.is_symlink():
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
                elif e.is_file(follow_symlinks=False):
                    total += e.stat(follow_symlinks=False).st_size
    return total


def compressed(path):
    try:
        import h5py
    except ImportError:
        return ""
    files = [f for f in sorted(glob.glob(os.path.join(path, "longrun_day*.nc"))) if not os.path.islink(f)]
    if not files:
        return ""
    try:
        with h5py.File(files[len(files) // 2], "r") as h:
            big = [h[k] for k in h if isinstance(h[k], h5py.Dataset) and h[k].ndim >= 3]
            return "zlib" if big and all(v.compression for v in big) else "raw"
    except Exception:
        return "?"


def records(ph):
    if ph is None:
        return ""
    hits = sorted(glob.glob(os.path.join(REPO, "docs", "outputs", f"{ph:02d}*")))
    return " ".join(f"[{os.path.basename(h)}](../docs/outputs/{os.path.basename(h)}/)" for h in hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=os.path.join(REPO, "runs"))
    ap.add_argument("--out")
    a = ap.parse_args()
    runs = os.path.realpath(a.runs)
    out = a.out or os.path.join(runs, "INDEX.md")

    fams = collections.defaultdict(lambda: dict(seg=0, agg=0, link=0, other=0, bytes=0, years=set(), comp=set()))
    for name in sorted(os.listdir(runs)):
        p = os.path.join(runs, name)
        if name in SKIP or name.startswith(".") or not os.path.isdir(p):
            continue
        f = fams[family(name)]
        f["years"].update(int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d|20[0-4]\d)(?:\d{4})?(?!\d)", name[len(family(name)):]))
        if os.path.islink(p):
            f["link"] += 1
            continue
        chunks = glob.glob(os.path.join(p, "longrun_day*.nc"))
        n_real = sum(not os.path.islink(c) for c in chunks)
        if n_real:
            f["seg"] += 1
            c = compressed(p)
            if c:
                f["comp"].add(c)
        elif chunks:
            f["agg"] += 1
        else:
            f["other"] += 1
        f["bytes"] += real_size(p)

    by_phase = collections.defaultdict(list)
    for fam, f in fams.items():
        by_phase[phase_of(fam)].append((fam, f))
    total = sum(f["bytes"] for f in fams.values())
    now = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M %Z")

    L = [f"# runs/ index\n",
         f"Generated {now} by `scripts/runs_index.py` (regenerate after adding or deleting runs). "
         f"{len(fams)} run families, {total / 1e12:.1f} TB of real files. Pipeline logs are in `logs/<phase>/`, "
         f"cleanup manifests in `archive/`.\n",
         "Kinds: **seg** = segments holding data, **agg** = aggregates made of links to segments, "
         "**link** = top-level links to another run (shared spin-up years), **other** = no chunk files "
         "(spin-up checkpoints, markers). Size counts real files only.\n",
         "## By phase\n", "| phase | families | size [GB] |", "|---|---|---|"]
    keyf = lambda k: (k is None, k or 0)
    for ph in sorted(by_phase, key=keyf):
        L.append(f"| {ph if ph is not None else '-'} | {len(by_phase[ph])} | "
                 f"{sum(f['bytes'] for _, f in by_phase[ph]) / 1e9:,.0f} |")
    L += ["", "## Families\n", "| family | phase | seg / agg / link / other | years | size [GB] | compressed | status | record |",
          "|---|---|---|---|---|---|---|---|"]
    for ph in sorted(by_phase, key=keyf):
        for fam, f in sorted(by_phase[ph]):
            yrs = f"{min(f['years'])}-{max(f['years'])}" if f["years"] else ""
            L.append(f"| `{fam}` | {ph if ph is not None else '-'} | {f['seg']} / {f['agg']} / {f['link']} / {f['other']} | "
                     f"{yrs} | {f['bytes'] / 1e9:,.1f} | {'/'.join(sorted(f['comp']))} | {note_for(fam, ph, f)} | {records(ph)} |")
    with open(out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"wrote {out}: {len(fams)} families, {total / 1e12:.1f} TB")


if __name__ == "__main__":
    main()
