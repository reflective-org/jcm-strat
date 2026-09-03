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

Both are logged in the run header so any log is self-describing. Implemented as a wrapper
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

_ORIG_FIX = _dycore.DinosaurDycore._fix_nodal_tracer_mass
_JCM_CONFIG_DIR = os.path.join(os.path.dirname(_jcm_main.__file__), "config")


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


@hydra.main(version_base=None, config_path=_JCM_CONFIG_DIR, config_name="config")
def main(cfg: DictConfig) -> None:
    enabled = bool(cfg.get("sl_mass_fixer", True))
    raw = cfg.get("sl_mass_fixer_exclude", None)
    # a config without the key (e.g. the full-ECHAM reference) yields a plain default, not a
    # ListConfig; OmegaConf.to_container refuses plain lists
    exclude = list(OmegaConf.to_container(raw)) if raw is not None and OmegaConf.is_config(raw) else list(raw or [])
    install_mass_fixer_policy(enabled, exclude)
    # hand the already-composed config to jcm's task function (hydra's decorated main accepts
    # a pass-through config and then does not re-parse the command line)
    _jcm_main.main(cfg_passthrough=cfg)


if __name__ == "__main__":
    main()
