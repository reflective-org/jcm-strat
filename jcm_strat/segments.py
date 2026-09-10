"""Calendar-anchored run segments for chained multi-year runs (Phase 9).

A chained run is split into segments because JCM keeps the whole ERA5 nudging target of a
segment on the GPU (issue #26): one year fits at T63L95 (31 GB), half a year at T85L95, a
quarter at T119L95. Segment lengths are multiples of the 5-day save interval and never cross a
calendar year, because the chunk loop labels a tail chunk shorter than a save without
integrating it (``jcm/runners.py`` chunk loop with ``model.py``'s ``int(total_time /
save_interval)``). A 366-day year is run as 365 days, so 31 December of a leap year is skipped —
which is what ``chain_years.sh`` has always done implicitly.

    python -m jcm_strat.segments quarter 2005-2009      # prints "start days year" per segment
"""
from __future__ import annotations

import datetime as dt
import sys

SCHEMES = {
    "year": (365,),
    "half": (185, 180),
    "quarter": (90, 90, 90, 95),
    "bimonth": (60, 60, 60, 60, 60, 65),
}
SAVE_INTERVAL_DAYS = 5
SAVE_INTERVAL_MIN = SAVE_INTERVAL_DAYS * 24 * 60


def parse_years(spec: str) -> list[int]:
    if "-" in spec:
        y0, y1 = (int(s) for s in spec.split("-"))
        return list(range(y0, y1 + 1))
    return [int(s) for s in spec.split(",")]


def segments(scheme: str, years) -> list[tuple[dt.date, int, int]]:
    """``[(start_date, days, year), ...]`` for ``scheme`` over ``years``."""
    if scheme == "smoke":                       # one 5-day segment at the start of the first year
        y = list(years)[0]
        return [(dt.date(y, 1, 1), SAVE_INTERVAL_DAYS, y)]
    if scheme not in SCHEMES:
        raise ValueError(f"unknown scheme {scheme!r}; known: {sorted(SCHEMES)} and 'smoke'")
    lengths = SCHEMES[scheme]
    assert sum(lengths) == 365 and all(n % SAVE_INTERVAL_DAYS == 0 for n in lengths)
    out = []
    for y in years:
        start = dt.date(y, 1, 1)
        for n in lengths:
            out.append((start, n, y))
            start += dt.timedelta(days=n)
        assert start.year == y + 1 or (start.year == y and start.month == 12 and start.day == 31)
    return out


def check_time_step(dt_min: float) -> None:
    """Refuse a time step that does not divide the save interval (JCM truncates silently)."""
    if SAVE_INTERVAL_MIN % dt_min:
        raise ValueError(f"run.time_step={dt_min} min does not divide the {SAVE_INTERVAL_DAYS}-day save "
                         f"interval ({SAVE_INTERVAL_MIN} min); use 6, 8, 9, 10, 12 or 15")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    for start, days, year in segments(sys.argv[1], parse_years(sys.argv[2])):
        print(start.isoformat(), days, year)
