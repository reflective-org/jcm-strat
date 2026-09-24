#!/usr/bin/env python3
"""Link finished calendar-year segments into one virtual run with cumulative day numbers (Phase 15).

    python scripts/link_segments.py runs/p15_base_3yr /path/runs/p13jucker_19900101 /path/runs/p13jucker_19910101 ...

The same linking scripts/chain_segments.sh does at the end of a chain, for segments that were run elsewhere (the
Phase 13b Jucker segments 1990-1992 serve as the sweep's base without re-running them). Segment lengths are the
true calendar-year lengths of the start dates in the directory names (<prefix>_YYYYMMDD). Existing links in the
aggregate are removed first; log.txt is the concatenation of the segments' logs (for the throughput numbers) and
.hydra/ is copied from the first segment.
"""
from __future__ import annotations

import datetime as dt, glob, os, re, shutil, sys


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    agg, segs = argv[1], argv[2:]
    os.makedirs(agg, exist_ok=True)
    for f in glob.glob(os.path.join(agg, "longrun_day*.nc")):
        os.remove(f)
    offset, lines = 0, []
    with open(os.path.join(agg, "log.txt"), "w") as log:
        for i, seg in enumerate(segs):
            m = re.search(r"_(\d{4})(\d{2})(\d{2})$", seg.rstrip("/"))
            if not m:
                sys.exit(f"{seg}: name must end in _YYYYMMDD")
            start = dt.date(*map(int, m.groups())); days = (dt.date(start.year + 1, 1, 1) - start).days
            files = glob.glob(os.path.join(seg, "longrun_day*.nc"))
            if not files:
                sys.exit(f"{seg}: no longrun_day*.nc")
            for f in files:
                n = int(re.search(r"longrun_day(\d+)\.nc$", f).group(1))
                os.symlink(os.path.abspath(f), os.path.join(agg, f"longrun_day{offset + n}.nc"))
            lines.append(f"{start} {days} {os.path.abspath(seg)}")
            if os.path.exists(os.path.join(seg, "log.txt")):
                log.write(open(os.path.join(seg, "log.txt"), errors="replace").read())
            if i == 0 and os.path.isdir(os.path.join(seg, ".hydra")):
                shutil.rmtree(os.path.join(agg, ".hydra"), ignore_errors=True); shutil.copytree(os.path.join(seg, ".hydra"), os.path.join(agg, ".hydra"))
            offset += days
    open(os.path.join(agg, "segments.txt"), "w").write("\n".join(lines) + "\n")
    print(f"linked {len(glob.glob(os.path.join(agg, 'longrun_day*.nc')))} chunk files ({offset} days) into {agg}")


if __name__ == "__main__":
    main(sys.argv)
