"""Chained-run segments: 5-day multiples, calendar-anchored, never crossing a year."""
import datetime as dt

import pytest

from jcm_strat import segments


@pytest.mark.parametrize("scheme", sorted(segments.SCHEMES))
def test_segments_cover_each_year_in_five_day_multiples(scheme):
    segs = segments.segments(scheme, [2005, 2008])
    per_year = {}
    for start, days, year in segs:
        assert days % 5 == 0 and start.year == year
        assert (start + dt.timedelta(days=days - 1)).year == year   # last simulated day in the same year
        per_year[year] = per_year.get(year, 0) + days
    assert per_year == {2005: 365, 2008: 365}                        # leap day skipped, as chain_years.sh did
    assert segs[0][0] == dt.date(2005, 1, 1)


def test_quarter_dates():
    segs = segments.segments("quarter", [2005])
    assert [s.isoformat() for s, _, _ in segs] == ["2005-01-01", "2005-04-01", "2005-06-30", "2005-09-28"]
    assert [d for _, d, _ in segs] == [90, 90, 90, 95]


def test_parse_years_and_time_step():
    assert segments.parse_years("2005-2007") == [2005, 2006, 2007]
    assert segments.parse_years("2005,2009") == [2005, 2009]
    for ok in (6, 8, 9, 10, 12, 15):
        segments.check_time_step(ok)
    with pytest.raises(ValueError):
        segments.check_time_step(7)
    with pytest.raises(ValueError):
        segments.segments("month", [2005])
