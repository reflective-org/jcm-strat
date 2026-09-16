"""Stratosphere-preserving reductions of the ECHAM L95 hybrid grid (Phase 9).

L95 has 21 levels above 1 hPa, 47 between 1.08 and 159 hPa and 27 below. The two tables here
are subsets of L95's own interfaces, so every kept level *is* an L95 level and the stratosphere
is bit-identical to L95's:

    strat63 = 8 (mesosphere)  + 47 (1.08-159 hPa, intact)                          + 8 (troposphere)
    strat47 = 7 (mesosphere)  + 15 (1.08-30 hPa, every other interface) + 17 (30-159 hPa, intact) + 8

Thinned regions take every n-th L95 interface at (nearly) uniform index stride, so the layer
thickness in log p grows by the same factor everywhere in that region.

Selection is by the top-level config key ``level_table: strat`` (honoured by ``jcm_strat.main``
and ``jcm_strat.prefetch_era5``), which

* patches ``jcm.physics.echam.echam_levels.get_echam_levels`` for the two level counts — 47
  collides with ECHAM's own L47 table, which therefore stays the default in every process that
  does not set the key;
* adds hyperdiffusion order profiles for ``(63, n)`` and ``(127, n)`` to
  ``jcm.diffusion._ECHAM_LMIDATM_ORDERS``, mapped level by level from the L95 profiles by the
  L95 index at the centre of each new level (ECHAM's own tables are index tables, see the note
  in ``jcm/diffusion.py``), and rebinds ``ECHAM_LMIDATM_LAYERS`` in ``jcm.diffusion`` and
  ``jcm.runners`` — without that ``diffusion.kind=auto`` silently falls back to uniform del2.

The upper sponge is a count of top levels (``run.sponge.levels``) with a timescale doubling per
level (``enspodi``); :func:`sponge_for` gives the (levels, enspodi) that reproduce L95's tau(p)
over the same pressure range. The p9_l63 / p9_l47 experiments carry those numbers.
"""
from __future__ import annotations

import logging

import numpy as np

_L95_NLEV = 95
# L95 interface indices (TOA first, 0..95). 22 is the 1.08 hPa interface, 52 the 30 hPa one,
# 69 the 159 hPa one; the L95 sponge (10 levels) ends at interface 10 (0.165 hPa).
_I_1HPA, _I_30HPA, _I_159HPA = 22, 52, 69
_SPONGE_BOTTOM_L95 = 10

# The L95 lmidatm profiles (jcm/diffusion.py) as (count, order) runs, TOA first.
_L95_ORDER_RUNS = {
    63: ((10, 1), (10, 2), (5, 3), (70, 4)),
    127: ((10, 1), (15, 2), (70, 3)),
}

_log = logging.getLogger("jcm_strat")


def _thin(i0: int, i1: int, n: int) -> list[int]:
    """``n`` layers between L95 interfaces ``i0`` and ``i1`` at uniform index stride."""
    return [int(v) for v in np.rint(np.linspace(i0, i1, n + 1))]


def interface_indices(nlevels: int) -> np.ndarray:
    """L95 interface indices that make up the ``nlevels`` table (sorted, unique, 0 and 95 included)."""
    tropo = _thin(_I_159HPA, _L95_NLEV, 8)
    if nlevels == 63:
        idx = _thin(0, _I_1HPA, 8) + list(range(_I_1HPA, _I_159HPA + 1)) + tropo
    elif nlevels == 47:
        idx = (_thin(0, _I_1HPA, 7) + list(range(_I_1HPA, _I_30HPA + 1, 2))
               + list(range(_I_30HPA, _I_159HPA + 1)) + tropo)
    else:
        raise ValueError(f"no strat level table for {nlevels} levels (have 47, 63)")
    out = np.unique(np.asarray(idx, dtype=int))
    assert out.size == nlevels + 1, (nlevels, out.size)
    return out


TABLES = (47, 63)


def strat_table(nlevels: int):
    """``HybridCoordinates`` for the reduced table (``a_boundaries`` in Pa, as JCM's tables)."""
    from dinosaur.hybrid_coordinates import HybridCoordinates
    import jax.numpy as jnp

    l95 = _orig_get_echam_levels(_L95_NLEV)
    idx = interface_indices(nlevels)
    a = np.asarray(l95.a_boundaries, dtype=np.float64)[idx]
    b = np.asarray(l95.b_boundaries, dtype=np.float64)[idx]
    return HybridCoordinates(a_boundaries=jnp.asarray(a), b_boundaries=jnp.asarray(b))


def _expand(runs) -> list[int]:
    out: list[int] = []
    for count, order in runs:
        out.extend([order] * count)
    return out


def level_orders(truncation: int, nlevels: int) -> list[int]:
    """Per-level hyperdiffusion order for the reduced table, from the L95 profile of ``truncation``."""
    base = _expand(_L95_ORDER_RUNS[truncation])
    idx = interface_indices(nlevels)
    return [base[(idx[j] + idx[j + 1]) // 2] for j in range(nlevels)]


def order_runs(truncation: int, nlevels: int):
    """``level_orders`` as the ``(count, order)`` run tuple ``_ECHAM_LMIDATM_ORDERS`` stores."""
    runs = []
    for o in level_orders(truncation, nlevels):
        if runs and runs[-1][1] == o:
            runs[-1] = (runs[-1][0] + 1, o)
        else:
            runs.append((1, o))
    return tuple(runs)


def sponge_for(nlevels: int) -> tuple[int, float]:
    """(levels, enspodi) reproducing L95's sponge tau(p): count the reduced levels whose lower
    interface lies at or above L95's sponge bottom (interface 10, 0.165 hPa; a level is kept if
    its lower interface is within one L95 interface of that), enspodi = 2 ** (mean L95 levels
    per sponge level)."""
    idx = interface_indices(nlevels)
    n = int(np.sum(idx[1:] <= _SPONGE_BOTTOM_L95 + 1))
    stride = idx[n] / n
    return n, float(round(2.0 ** stride, 2))


def pressures_hpa(nlevels: int, ps_pa: float = 101325.0) -> np.ndarray:
    """Interface pressures (hPa, TOA first) of a table at surface pressure ``ps_pa``."""
    c = strat_table(nlevels) if nlevels in TABLES else _orig_get_echam_levels(nlevels)
    return (np.asarray(c.a_boundaries) + np.asarray(c.b_boundaries) * ps_pa) / 100.0


def _orig_get_echam_levels(nlevels: int):
    import jcm.physics.echam.echam_levels as el
    return getattr(el, "_jcm_strat_orig", el.get_echam_levels)(nlevels)


def install(name) -> None:
    """Activate the tables for this process if ``name`` is ``"strat"`` (``None``/empty: no-op)."""
    if not name:
        return
    if str(name) != "strat":
        raise ValueError(f"level_table={name!r}: only 'strat' is known")
    import jcm.diffusion as jd
    import jcm.physics.echam.echam_levels as el
    import jcm.runners as jr

    if not hasattr(el, "_jcm_strat_orig"):
        el._jcm_strat_orig = el.get_echam_levels

        def patched(nlevels: int):
            if nlevels in TABLES:
                return strat_table(nlevels)
            return el._jcm_strat_orig(nlevels)

        el.get_echam_levels = patched
    for n in TABLES:
        for trunc in _L95_ORDER_RUNS:
            jd._ECHAM_LMIDATM_ORDERS[(trunc, n)] = order_runs(trunc, n)
    layers = frozenset(nlev for _, nlev in jd._ECHAM_LMIDATM_ORDERS)
    jd.ECHAM_LMIDATM_LAYERS = layers
    jr.ECHAM_LMIDATM_LAYERS = layers
    _log.info("jcm_strat: level_table=strat — L%s are the L95-derived tables (jcm_strat/levels.py); "
              "hyperdiffusion orders mapped from the L95 profiles", "/".join(str(n) for n in TABLES))


if __name__ == "__main__":  # print the tables for the record
    for n in TABLES:
        p = pressures_hpa(n)
        print(f"strat{n}: {n} levels; interfaces (hPa):")
        print(np.array2string(p, precision=3, max_line_width=120))
        for t in _L95_ORDER_RUNS:
            print(f"  orders T{t}: {order_runs(t, n)}")
        print(f"  sponge: levels, enspodi = {sponge_for(n)}")
