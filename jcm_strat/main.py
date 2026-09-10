"""jcm-strat entry point: jcm.main plus the one dycore knob jcm does not expose.

    python -m jcm_strat.main --config-dir jcm_strat/config +experiment=p3_tracers ...

Identical to ``python -m jcm.main`` (same primary config, same runner) except that two extra
top-level config keys are honoured before the model is built:

``sl_mass_fixer`` (bool, default true)
    JCM's dycore rescales every semi-Lagrangian nodal tracer by one global factor per step so
    its mass matches the pre-transport value (``DinosaurDycore._fix_nodal_tracer_mass``,
    Diamantakis & Flemming 2014). ``false`` switches that off for all tracers (issue #8).

``sl_mass_fixer_exclude`` (list of tracer names, default [])
    Tracers that keep the fixer's *input* value, i.e. are transported but never rescaled. A
    clock tracer must be here: it is not a conserved quantity, and in Phase 3 the fixer's
    global rescaling — compensating spurious mass created by the limiter at the clock's sharp
    700 hPa reset edge — slowed the whole stratospheric clock from 1.00 to 0.44 day/day over
    one year (docs/outputs/03_tracers/output.md, KEY_DECISIONS #19).

``level_table`` (``null`` or ``strat``, default null)
    ``strat`` serves the Phase 9 L95-derived vertical tables (``jcm_strat/levels.py``) for
    ``grid.layers`` 47 and 63, with hyperdiffusion order profiles mapped from L95's.

All are logged in the run header so any log is self-describing. Implemented as a wrapper
around the dycore method because ``sl_options`` from the runner carries only
``off_centering``; upstreaming a per-tracer flag is part of issue #13.
"""
from __future__ import annotations

import logging
import os

import hydra
from omegaconf import DictConfig, OmegaConf

import jcm.main as _jcm_main
from jcm.dycore.dinosaur import dycore as _dycore

from jcm_strat import levels

_ORIG_FIX = _dycore.DinosaurDycore._fix_nodal_tracer_mass
_ORIG_INIT = _dycore.DinosaurDycore.__init__
_JCM_CONFIG_DIR = os.path.join(os.path.dirname(_jcm_main.__file__), "config")


def install_sl_options(extra: dict) -> None:
    """Merge ``extra`` into the ``sl_options`` the runner hands to ``DinosaurDycore``.

    The runner only forwards ``off_centering`` (``sl_off_centering``); the Phase 7 time-step sweep
    needs ``departure_iterations`` (dinosaur's fixed-point iterations for the semi-Lagrangian
    departure points, default 1; the accuracy condition scales with dt x wind shear).
    """
    extra = {k: v for k, v in extra.items() if v is not None}
    if not extra:
        return

    def patched_init(self, *args, **kwargs):
        opts = dict(kwargs.get("sl_options") or {})
        opts.update(extra)
        kwargs["sl_options"] = opts
        return _ORIG_INIT(self, *args, **kwargs)

    _dycore.DinosaurDycore.__init__ = patched_init
    logging.getLogger("jcm_strat").info("jcm_strat: semi-Lagrangian options %s", extra)


def install_mass_fixer_policy(enabled: bool = True, exclude=()) -> None:
    """Patch ``DinosaurDycore._fix_nodal_tracer_mass`` according to the policy."""
    exclude = tuple(str(n) for n in (exclude or ()))

    def patched(self, state_ref, state_new):
        if not enabled:
            return state_new
        fixed = _ORIG_FIX(self, state_ref, state_new)
        if exclude:
            tracers = dict(fixed.tracers)
            for name in exclude:
                if name in tracers:
                    tracers[name] = state_new.tracers[name]
            fixed = fixed.replace(tracers=tracers)
        return fixed

    _dycore.DinosaurDycore._fix_nodal_tracer_mass = patched
    logging.getLogger("jcm_strat").info(
        "semi-Lagrangian tracer mass fixer: %s%s",
        "on" if enabled else "OFF",
        f", excluded tracers: {list(exclude)}" if (enabled and exclude) else "",
    )


def install_calendar(name: str | None) -> None:
    """Make every ``Model`` use calendar ``name`` (``gregorian`` or ``365_day``).

    JCM's ``Model`` defaults to ``365_day`` and neither ``build_model`` nor the run config sets it.
    Under ``365_day`` the fraction of year is ``(days since 1970-01-01) % 365 / 365``, which for a
    real Gregorian start date is 5-12 days ahead of the true day of year (9 d in 2005): the
    Polvani-Kushner season and the QBO month ran that much early in Phases 6-9. ``gregorian`` gives
    the true day of year, and exactly 0 at 00:00 on 1 January (KEY_DECISIONS, Phase 10).
    """
    if not name:
        return
    if name not in ("gregorian", "365_day"):
        raise ValueError(f"calendar={name!r}; expected gregorian or 365_day")

    def patched_init(self, *args, **kwargs):
        kwargs["calendar"] = name
        return _ORIG_MODEL_INIT(self, *args, **kwargs)

    _model.Model.__init__ = patched_init
    logging.getLogger("jcm_strat").info("jcm_strat: model calendar %s", name)


def install_output_policy(drop=()) -> None:
    """Drop the listed variables from every dataset ``ModelPredictions.to_xarray`` returns.

    JCM writes every prognostic and every diagnostic a term provides; it has no output-variable
    list (``run.tracer_vars`` selects *inputs*). At 6-hourly output one 3-D field is 10 GB per
    simulated year at T63L95, so Phase 10 drops what is a diagnostic of other outputs.
    """
    drop = tuple(str(v) for v in (drop or ()))
    if not drop:
        return

    def patched(self):
        ds = _ORIG_TO_XARRAY(self)
        return ds.drop_vars([v for v in drop if v in ds])

    _predictions.ModelPredictions.to_xarray = patched
    logging.getLogger("jcm_strat").info("jcm_strat: output drops %s", list(drop))


def _as_list(raw):
    if raw is None:
        return []
    return list(OmegaConf.to_container(raw)) if OmegaConf.is_config(raw) else list(raw)


@hydra.main(version_base=None, config_path=_JCM_CONFIG_DIR, config_name="config")
def main(cfg: DictConfig) -> None:
    enabled = bool(cfg.get("sl_mass_fixer", True))
    raw = cfg.get("sl_mass_fixer_exclude", None)
    # a config without the key (e.g. the full-ECHAM reference) yields a plain default, not a
    # ListConfig; OmegaConf.to_container refuses plain lists
    exclude = list(OmegaConf.to_container(raw)) if raw is not None and OmegaConf.is_config(raw) else list(raw or [])
    install_mass_fixer_policy(enabled, exclude)
    di = cfg.get("sl_departure_iterations", None)
    install_sl_options({"departure_iterations": int(di) if di is not None else None})
    install_calendar(cfg.get("calendar", None))
    install_output_policy(_as_list(cfg.get("output_drop", None)))
    # ``level_table: strat`` (Phase 9): serve the L95-derived strat47/strat63 hybrid tables and
    # their hyperdiffusion profiles for grid.layers 47/63 (jcm_strat/levels.py)
    levels.install(cfg.get("level_table", None))
    # hand the already-composed config to jcm's task function (hydra's decorated main accepts
    # a pass-through config and then does not re-parse the command line)
    _jcm_main.main(cfg_passthrough=cfg)


if __name__ == "__main__":
    main()
