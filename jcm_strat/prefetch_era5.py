"""Prefetch the ERA5 nudging windows and the initial state for one Phase 9 configuration.

    JAX_PLATFORMS=cpu python -m jcm_strat.prefetch_era5 --scheme half --years 2005-2009 \\
        [--dry-run] [--no-init] -- +experiment=p9_res grid=echam_t85_l95_hybrid

Everything after ``--`` is a hydra override, composed exactly as ``jcm_strat.main`` composes a run
(JCM's primary config plus this repo's ``jcm_strat/config`` overlay, ``level_table`` honoured), so
the coordinate hash in the cache file name is the one the run will look for. One window per
segment (``[start - 1 d, start + days + 2 d]``, as ``jcm.runners._maybe_attach_nudging_target``)
instead of one multi-year file: a 5-year T119L95 window would be 565 GB in a single netCDF.
JCM's own ``python -m jcm.data.era5`` cannot be used because it composes on JCM's config dir
only and does not see the overlay grids.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")

from hydra import compose, initialize_config_dir  # noqa: E402

from jcm_strat import levels, segments  # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OVERLAY = os.path.join(_REPO, "jcm_strat", "config")


def compose_run_config(overrides):
    import jcm.main as _jcm_main
    jcm_config_dir = os.path.join(os.path.dirname(_jcm_main.__file__), "config")
    with initialize_config_dir(version_base=None, config_dir=jcm_config_dir):
        return compose(config_name="config",
                       overrides=[f"hydra.searchpath=[file://{_OVERLAY}]", *overrides])


def window(start: dt.date, days: int) -> tuple[str, str]:
    return str(start - dt.timedelta(days=1)), str(start + dt.timedelta(days=days + 2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scheme", default="year", choices=sorted(segments.SCHEMES) + ["smoke"],
                    help="segment scheme (jcm_strat.segments); 'smoke' = one 5-day window at the start of the first year")
    ap.add_argument("--years", default="2005-2009")
    ap.add_argument("--dry-run", action="store_true", help="print file names and sizes only")
    ap.add_argument("--no-init", action="store_true", help="skip the initial-state slice")
    ap.add_argument("overrides", nargs="*", help="hydra overrides (after --)")
    a = ap.parse_args(argv)

    cfg = compose_run_config(a.overrides)
    levels.install(cfg.get("level_table", None))
    from jcm.data import era5
    from jcm.runners import build_coords
    coords = build_coords(cfg)
    nlon, nlat = coords.horizontal.nodal_shape
    nlev = int(coords.vertical.a_centers.size)
    freq = str(cfg.nudging.get("freq", "6h"))
    per_day = {"6h": 4, "12h": 2, "1d": 1}[freq]
    segs = segments.segments(a.scheme, segments.parse_years(a.years))
    print(f"grid {nlon}x{nlat} L{nlev} T{cfg.grid.spectral_truncation}, nudging {freq}, "
          f"{len(segs)} segments ({a.scheme}), cache {era5.cache_dir()}")
    total = 0.0
    for i, (start, days, _year) in enumerate(segs):
        w0, w1 = window(start, days)
        nsteps = (days + 3) * per_day + 1
        gb = 3 * nlev * nlon * nlat * nsteps * 4 / 1e9
        total += gb
        name = era5._window_key(coords, w0, w1, freq, ("u", "v", "T"))
        exists = (era5.cache_dir() / name).exists()
        print(f"[{i + 1:2d}/{len(segs)}] {w0}..{w1} {nsteps} steps {gb:6.1f} GB {'(cached)' if exists else ''} {name}")
        if a.dry_run:
            continue
        ds = era5.dataset_on_model_grid(coords, w0, w1, freq=freq)
        ds.close()
        if i == 0 and not a.no_init:
            era5.initial_state(coords, str(start))
            print(f"      initial state {start} cached")
    print(f"total nudging target {total:.0f} GB{' (dry run)' if a.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
