#!/usr/bin/env python3
"""Throughput of one jcm run: simulated days per wall-clock hour and ms per step.

    python scripts/throughput.py runs/<session> [--label TEXT] [--append PROGRESS.md]

Sources, in order of preference:
  1. the per-chunk netCDF files jcm writes under run=longrun, whose
     ``jcm_prov_chunk_wall_seconds`` attribute is the measured wall time of
     that chunk (compile time included in chunk 0, so chunk 0 is reported
     separately and excluded from the steady-state number);
  2. the health-report lines in log.txt (``Chunk N | Day D``) when no netCDF
     attribute is available.
The time step comes from the resolved Hydra config in .hydra/config.yaml.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys


def _dt_minutes(rundir: str) -> float | None:
    cfg = os.path.join(rundir, ".hydra", "config.yaml")
    if not os.path.exists(cfg):
        return None
    try:
        import yaml
        with open(cfg) as f:
            c = yaml.safe_load(f)
        return float(c["run"]["time_step"])
    except Exception:  # noqa: BLE001 - best effort
        return None


def _chunks_from_netcdf(rundir: str):
    try:
        import xarray as xr
    except ImportError:
        return []
    rows = []
    for p in sorted(glob.glob(os.path.join(rundir, "*_day*.nc"))):
        m = re.search(r"_day(\d+)\.nc$", p)
        if not m:
            continue
        try:
            with xr.open_dataset(p, decode_times=False) as ds:
                wall = ds.attrs.get("jcm_prov_chunk_wall_seconds")
        except Exception:  # noqa: BLE001
            continue
        if wall is not None:
            rows.append((int(m.group(1)), float(wall)))
    rows.sort()
    out, prev = [], 0
    for day, wall in rows:
        out.append({"chunk_end_day": day, "days": day - prev, "wall_s": wall})
        prev = day
    return out


def _chunks_from_log(rundir: str):
    log = os.path.join(rundir, "log.txt")
    if not os.path.exists(log):
        return []
    # Fallback: timestamps of successive "Chunk N | Day D" report lines.
    # launch.sh prefixes nothing, so we rely on the file's mtime spacing only
    # when the netCDF attribute is unavailable — coarse but honest.
    days = []
    with open(log, errors="replace") as f:
        for line in f:
            m = re.search(r"Chunk (\d+) \| Day (\d+)", line)
            if m:
                days.append(int(m.group(2)))
    return [{"chunk_end_day": d, "days": None, "wall_s": None} for d in days]


def _end_to_end(rundir: str):
    """Wall time from the first 'Model starting' to the launcher's exit line, from log.txt.

    This includes JIT compile, per-chunk output conversion/writing and health checks --
    everything the kernel-only chunk attribute leaves out -- so it is the number a user
    actually waits for. Returns (seconds, n_model_starts) or None.
    """
    import datetime as dt
    log = os.path.join(rundir, "log.txt")
    if not os.path.exists(log):
        return None
    t0 = t1 = None
    n = 0
    with open(log, errors="replace") as f:
        for line in f:
            m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)[,.]\d+\].*Model starting", line)
            if m:
                n += 1
                if t0 is None:
                    t0 = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            m = re.match(r"\[launch\] (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)[^ ]* exit=", line)
            if m:
                t1 = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
    if t0 is None or t1 is None:
        return None
    return (t1 - t0).total_seconds(), n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("rundir")
    ap.add_argument("--label", default=None, help="row label for --append")
    ap.add_argument("--append", default=None, help="PROGRESS.md-style table to append a row to")
    ap.add_argument("--csv", default=None, help="CSV (label,grid,dt_min,days_per_hr,ms_per_step,run,date) to append to")
    ap.add_argument("--grid", default="", help="grid name for the CSV row")
    a = ap.parse_args()
    rundir = a.rundir.rstrip("/")
    dt = _dt_minutes(rundir)
    chunks = _chunks_from_netcdf(rundir)
    if not chunks:
        print("no per-chunk wall-time attributes found; log reports:", _chunks_from_log(rundir))
        return 1
    steady = chunks[1:] if len(chunks) > 1 else chunks
    days = sum(c["days"] for c in steady)
    wall = sum(c["wall_s"] for c in steady)
    days_per_hr = days / (wall / 3600.0)
    ms_per_step = None
    if dt:
        steps = days * 1440.0 / dt
        ms_per_step = 1000.0 * wall / steps
    print(f"run:            {rundir}")
    print(f"dt:             {dt} min")
    print(f"chunk 0:        {chunks[0]['days']} d in {chunks[0]['wall_s']:.0f} s (includes compile)")
    print(f"steady state:   {days} d in {wall:.0f} s over {len(steady)} chunk(s)")
    print(f"throughput:     {days_per_hr:.1f} simulated days / hour")
    if ms_per_step:
        print(f"per step:       {ms_per_step:.0f} ms")
    e2e = _end_to_end(rundir)
    total_days = sum(c["days"] for c in chunks)
    e2e_days_per_hr = None
    if e2e:
        e2e_days_per_hr = total_days / (e2e[0] / 3600.0)
        print(f"end-to-end:     {total_days} d in {e2e[0]:.0f} s incl. compile + output = "
              f"{e2e_days_per_hr:.0f} days / hour  ({e2e[1]} chunks)")
    if a.append:
        label = a.label or os.path.basename(rundir)
        row = (f"| {label} | {dt:g} | {days_per_hr:.1f} | "
               f"{ms_per_step:.0f} | `{os.path.basename(rundir)}` |")
        with open(a.append, "a") as f:
            f.write(row + "\n")
        print("appended:", row)
    if a.csv:
        import csv, datetime
        new = not os.path.exists(a.csv)
        with open(a.csv, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["label", "grid", "dt_min", "days_per_hr", "ms_per_step",
                            "e2e_days_per_hr", "run", "date"])
            w.writerow([a.label or os.path.basename(rundir), a.grid, dt, round(days_per_hr, 1),
                        round(ms_per_step or 0), round(e2e_days_per_hr or 0),
                        os.path.basename(rundir), datetime.date.today().isoformat()])
        print("csv row appended to", a.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
