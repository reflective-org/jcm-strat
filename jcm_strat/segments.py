"""Calendar-anchored run segments for chained multi-year runs (Phase 9).

A chained run is split into segments because JCM keeps the whole ERA5 nudging target of a
segment on the GPU (issue #26): one year fits at T63L95 (31 GB), half a year at T85L95, a
quarter at T119L95. Segment lengths are multiples of the 5-day save interval and never cross a
calendar year, because the chunk loop labels a tail chunk shorter than a save without
integrating it (``jcm/runners.py`` chunk loop with ``model.py``'s ``int(total_time /
save_interval)``). A 366-day year is run as 365 days, so 31 December of a leap year is skipped —
which is what ``chain_years.sh`` has always done implicitly.

Phase 10 adds the scheme ``calendar``: one segment per year of its TRUE length (365 or 366 days),
allowed when the save interval divides one day (6-hourly output), so no day is skipped.

    python -m jcm_strat.segments quarter 2005-2009            # prints "start days year" per segment
    python -m jcm_strat.segments calendar 1990-2019 0.25      # 6-hourly save interval
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


def segments(scheme: str, years, save_interval_days: float = SAVE_INTERVAL_DAYS) -> list[tuple[dt.date, int, int]]:
    """``[(start_date, days, year), ...]`` for ``scheme`` over ``years``."""
    if scheme == "calendar":                    # true calendar years, 6-hourly (or finer) output
        if (1.0 / save_interval_days) % 1:
            raise ValueError(f"scheme 'calendar' needs a save interval that divides one day, not {save_interval_days} d")
        return [(dt.date(y, 1, 1), (dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days, y) for y in years]
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


def check_time_step(dt_min: float, save_interval_days: float = SAVE_INTERVAL_DAYS) -> None:
    """Refuse a time step that does not divide the save interval (JCM truncates silently)."""
    save_min = round(save_interval_days * 24 * 60, 6)
    if save_min % dt_min:
        raise ValueError(f"run.time_step={dt_min} min does not divide the {save_interval_days}-day save "
                         f"interval ({save_min:g} min)")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    save = float(sys.argv[3]) if len(sys.argv) == 4 else SAVE_INTERVAL_DAYS
    for start, days, year in segments(sys.argv[1], parse_years(sys.argv[2]), save):
        print(start.isoformat(), days, year)
