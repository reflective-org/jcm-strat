#!/usr/bin/env python3
"""Where a run lives in runs/ (Susanne 2026-11-15): runs/<phase>/<family>/<run name>.

    python3 scripts/runs_layout.py dir NAME       # absolute run directory for run NAME
    python3 scripts/runs_layout.py logdir NAME    # absolute runs/logs/<phase>/ for NAME's chain and pipeline logs
    python3 scripts/runs_layout.py rel NAME       # <phase>/<family>/<NAME>, relative to runs/

<phase> is "p<N>" from the name's leading p<N> (p31_AL7h70_19700101 -> p31, p8f_2005 -> p8), "misc" otherwise.
<family> is the name without its segment/aggregate suffix (_YYYYMMDD, _YYYY_YYYY, _Nyr, _MMYY window, _agg,
_spinup_YYYYMMDD, _prefetch), so every segment, spin-up and aggregate of one chain sits together:
runs/p31/p31_AL7h70/{p31_AL7h70_spinup_19691201, p31_AL7h70_19700101, ..., p31_AL7h70_1970_2022}.
Run names stay unchanged; only their parent folders are added. Every launcher (chain_segments.sh, chain_years.sh,
launch.sh, launch_gpu.sh, pipeline.sh) and scripts/runs_index.py use this module, so they cannot disagree.
Standard library only (system python3 is enough).
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# realpath: in a worktree runs/ is a symlink to the main checkout's; resolving it keeps every path (and every symlink
# the chain scripts create) pointing at the real directory, never through a worktree that will be removed.
RUNS = os.path.realpath(os.path.join(REPO, "runs"))
SUFFIX = re.compile(r"(_spinup(_\d{8})?|_\d{8}|_\d{4}_\d{4}|_\d+yr|_agg|_\d{4}|_prefetch)$")
PHASE_DIR = re.compile(r"^(p\d+|misc)$")      # names of the top-level phase folders
RESERVED = {"logs", "archive", "INDEX.md"}


def family(name):
    old = name.startswith("old_")
    base = name[4:] if old else name
    while True:
        new = SUFFIX.sub("", base)
        if new == base:
            break
        base = new
    return ("old_" if old else "") + base


def phase(name):
    m = re.match(r"(?:old_)?p(\d+)", name)
    return f"p{int(m.group(1))}" if m else "misc"


def rel(name):
    if not name or "/" in name or name in RESERVED or PHASE_DIR.match(name):
        raise ValueError(f"not a run name: {name!r}")
    return os.path.join(phase(name), family(name), name)


def run_dir(name):
    return os.path.join(RUNS, rel(name))


def log_dir(name):
    return os.path.join(RUNS, "logs", phase(name))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("dir", "logdir", "rel"):
        sys.exit(__doc__.split("\n\n")[1])
    cmd, name = sys.argv[1:]
    print({"dir": run_dir, "logdir": log_dir, "rel": rel}[cmd](name))
