"""Production tracer set for the long runs (Phase 10, revised in Phase 11): transport-learning tracers plus the clocks.

One PhysicsTerm that replaces ``PassiveTracers`` in the production physics. Transport is the
dycore's job (semi-Lagrangian, nodal tracers, global mass fixer); this term only adds the local
tendencies, on jcm's column-vectorized path (``vectorize_columns: true``, fields ``(nlev, ncols)``).
Units and the per-second -> nondimensional conversion (``_per_s``) are exactly as in ``tracers.py``.
The Phase 10 form of this term (amplitudes 0.05-1, Gaussian blobs only, surface absorption, no lid)
is commit d0b58c6.

Tracers (all ``nondimensionalize=False``, so state, dycore and netCDF carry the same numbers):

``aoa``       age of air in days, reset to zero on one step wherever p > 700 hPa (as in Phases 3-9).
``aoa150``    the same clock reset wherever p > 150 hPa: "entry age" into the stratosphere
              (KEY_DECISIONS #22).
``aoa_sfc``   the same clock reset only in the lowest ``sfc_layers`` model layers: the CLaMS/WACCM
              surface boundary condition.
``aoa500``    (``ProductionTracersAoa500`` only, Phase 12) the same clock reset wherever p > 500 hPa.
              The clock set is the class attribute ``CLOCKS``; a subclass adds a clock by extending it
              and ``_reset_masks`` (the Phase 11 set and its checkpoints are untouched).
``sai``       continuous source of 1e-6 per second in the box 15S-15N, 25-55 hPa, no sink (as before).
``pulse_<i>``, single injections of unit amplitude: on the first step of the run (``injection: once``,
``pulse_<i>_box``  ``first_segment=true`` marks that segment) the field is SET to a shape S_i(lat, lon, p)
              centred at (lat_i, lon_i, p_i) and never again. ``pulse_<i>`` is a Gaussian blob with
              widths ``pulse_sigma_deg`` (great-circle) and ``pulse_sigma_decades`` (log10 p);
              ``pulse_<i>_box`` is its sharp-edged twin, 1 inside the cap of radius ``pulse_sigma_deg``
              and within ``pulse_sigma_decades`` of the centre pressure, 0 outside (Phase 11: the
              same nominal size, so the two differ only in their edges). With ``injection: quarterly``
              the shape is re-set on 1 January and every 365/``n_pulses_per_year`` days of each year.
``src_<i>``,  continuous sources at a second set of sites: every step adds S_i / ``source_timescale_days``
``src_<i>_box``  (the shape alone would reach 1 in that time), Gaussian and sharp-edged twin as above.
``n2o``,      steady tracers with a tropospheric source and a stratospheric photochemical sink:
``cfc11``     held at 1 wherever p > ``n2o_source_pressure_hpa``, loss  -k(lat, p) q  elsewhere with
              WACCM's zonal-mean loss-frequency climatology, and initialised (first step of the
              first segment, ``first_segment=true``) from WACCM's zonal-mean January distribution
              normalised to 1 at the surface. Both come from ``jcm_strat/data/waccm_tracer_ref.nc``
              (scripts/make_waccm_tracer_ref.py). Their steady state is set by the model's own
              transport against a realistic sink, so they carry permanent, latitude- and
              height-dependent gradients spanning 1 to ~1e-2 (N2O) and 1 to ~1e-4 (CFC-11).

Sinks. ``surface_sink`` (Phase 10: true; Phase 11: false) relaxes the pulses and sources to zero in
the lowest ``absorb_layers`` layers on one step. Without it the pulses conserve their injected mass
for ever and the sources grow linearly, like ``sai``.

Tracer lid (Phase 11). The 1990-2019 Phase 10 run showed the model's mesosphere is never
ventilated: the age of air above ~1 hPa was uniform in latitude and equal to the run length, and
that air leaked down until the whole stratosphere was 3-5 times too old (docs/outputs/10_production).
Above ``lid_p_hpa`` (1 hPa) the tracers are therefore relaxed on ``lid_tau_days`` towards prescribed
values, the same logic as nudging the troposphere to ERA5 - prescribe where the model is not
credible: ``aoa150`` towards WACCM6 REF-D1's zonal-mean mean age (``aoa_ref``, ~4.5 yr and nearly
flat in latitude up there; an entry age relative to 103 hPa), ``aoa`` and ``aoa_sfc`` towards the
same plus ``lid_clock_offset_days`` (the tropospheric transit a surface clock adds, ~0.3 yr),
``n2o``/``cfc11`` towards their WACCM state (essentially 0 there). With ``lid_sink_injections``
(the Phase 11 "B" run) the pulses, sources and ``sai`` are relaxed to zero above the lid as well;
otherwise (the "A" run) they have no sink anywhere. ``lid_p_hpa: null`` switches the lid off.

Time. A term sees no clock; like ``QboNudging`` this one reads the fraction of year from
``forcing.solar.tyear``, which is exactly 0 at 00:00 on 1 January of every chained segment under
``calendar: gregorian`` (jcm_strat/main.py). The injection fires on the step whose interval contains
an injection date; with a 12-min step that is one step, at most two in a leap year.

Mass fixer. The dycore applies the fixer after the physics, with the post-physics mass as the target,
so neither the injections nor the lid nor the surface absorption are fought by it; the pulses,
sources and ``sai`` stay under the fixer. The three clocks and the two steady tracers impose a value,
not a mass, and must be listed in ``sl_mass_fixer_exclude`` (KEY_DECISIONS #19, #34).
"""
from __future__ import annotations

import os
from typing import ClassVar, Sequence

import jax.numpy as jnp
import numpy as np
import xarray as xr
from dinosaur.scales import units
from flax import nnx

import jcm.constants as jcm_constants
from jcm.dycore.dinosaur.dycore import physics_specs_from_constants
from jcm.physics.coords_util import column_lat_lon
from jcm.physics.physics_term import PhysicsTerm, TracerSpec
from jcm.physics_interface import PhysicsState, PhysicsTendency

P0_PA = 101325.0
DAY = 86400.0
DEFAULT_REF = os.path.join(os.path.dirname(__file__), "data", "waccm_tracer_ref.nc")

# (lat deg, lon deg E, p hPa): different heights, hemispheres and longitudes; every injection has unit amplitude
DEFAULT_PULSES = (
    (0.0, 0.0, 30.0),        # tropical middle stratosphere
    (45.0, 120.0, 70.0),     # NH lower stratosphere
    (-60.0, 240.0, 10.0),    # SH polar middle stratosphere
    (30.0, 300.0, 3.0),      # upper stratosphere
    (-15.0, 60.0, 300.0),    # tropical upper troposphere, crosses the tropopause
)
# continuous sources (lat deg, lon deg E, p hPa): sites distinct from the pulses
DEFAULT_SOURCES = (
    (0.0, 180.0, 20.0),      # tropical middle stratosphere
    (30.0, 60.0, 100.0),     # NH subtropical lowermost stratosphere
    (-60.0, 300.0, 5.0),     # SH polar upper stratosphere
    (-30.0, 240.0, 55.0),    # SH subtropical lower stratosphere (Susanne, 2026-09-11)
)
SHAPES = ("", "_box")        # every site carries a Gaussian tracer and a sharp-edged twin
STEADY = ("n2o", "cfc11")
CLOCKS = ("aoa", "aoa150", "aoa_sfc")


def shape_names(prefix: str, sites) -> tuple[str, ...]:
    return tuple(f"{prefix}_{i + 1}{s}" for i in range(len(sites)) for s in SHAPES)


def site_of(name: str):
    """(kind, site index, shape suffix) of a pulse/source tracer name, e.g. 'src_2_box' -> ('src', 1, '_box')."""
    parts = name.split("_")
    return parts[0], int(parts[1]) - 1, ("_" + parts[2] if len(parts) > 2 else "")


class ProductionTracers(PhysicsTerm):
    name: ClassVar[str] = "production_tracers"
    category: ClassVar[str] = "tracers"
    requires: ClassVar[tuple[str, ...]] = ()
    provides: ClassVar[tuple[str, ...]] = ()
    output_attrs: ClassVar = {
        "aoa": {"units": "day", "long_name": "age of air (clock tracer, reset below 700 hPa; relaxed to WACCM6 age + offset above the lid)"},
        "aoa150": {"units": "day", "long_name": "age of air, clock reset below 150 hPa (stratospheric entry age; relaxed to WACCM6 age above the lid)"},
        "aoa_sfc": {"units": "day", "long_name": "age of air, clock reset in the lowest two model layers (surface boundary condition; relaxed to WACCM6 age + offset above the lid)"},
        "sai": {"units": "1", "long_name": "idealised stratospheric injection tracer (source 15S-15N, 25-55 hPa)"},
        "n2o": {"units": "1", "long_name": "N2O-like tracer: 1 below 700 hPa, WACCM loss frequency above, WACCM zonal-mean initial state"},
        "cfc11": {"units": "1", "long_name": "CFC-11-like tracer: 1 below 700 hPa, WACCM loss frequency above, WACCM zonal-mean initial state"},
    }
    _pulse_names: tuple[str, ...] = shape_names("pulse", DEFAULT_PULSES)
    _source_names: tuple[str, ...] = shape_names("src", DEFAULT_SOURCES)
    CLOCKS: ClassVar[tuple[str, ...]] = CLOCKS                # the clock tracers this class declares
    ENTRY_CLOCKS: ClassVar[tuple[str, ...]] = ("aoa150",)     # read WACCM's entry age above the lid as is; the others + offset

    def __init__(
        self,
        pulses: Sequence[Sequence[float]] = DEFAULT_PULSES,
        injection: str = "once",
        n_pulses_per_year: int = 4,
        sources: Sequence[Sequence[float]] = DEFAULT_SOURCES,
        source_timescale_days: float = 90.0,
        pulse_sigma_deg: float = 12.0,
        pulse_sigma_decades: float = 0.25,
        surface_sink: bool = False,
        absorb_layers: int = 2,
        sfc_layers: int = 2,
        aoa_reset_pressure_hpa: float = 700.0,
        aoa150_reset_pressure_hpa: float = 150.0,
        sai_source_per_s: float = 1e-6,
        sai_lat_deg: float = 15.0,
        sai_p_top_hpa: float = 25.0,
        sai_p_bot_hpa: float = 55.0,
        ref_file: str = DEFAULT_REF,
        n2o_source_pressure_hpa: float = 700.0,
        lid_p_hpa: float | None = 1.0,
        lid_tau_days: float = 1.0,
        lid_clock_offset_days: float = 110.0,
        lid_sink_injections: bool = False,
        first_segment: bool = False,
    ) -> None:
        self.pulses = tuple(tuple(float(v) for v in p[:3]) for p in pulses)
        if len(self.pulses) != len(DEFAULT_PULSES):
            raise ValueError(f"ProductionTracers declares {len(DEFAULT_PULSES)} pulse sites; got {len(self.pulses)} centres")
        if injection not in ("once", "quarterly"):
            raise ValueError(f"injection={injection!r}; expected 'once' or 'quarterly'")
        self.injection = injection
        self.n_pulses = int(n_pulses_per_year)
        self.sources = tuple(tuple(float(v) for v in p[:3]) for p in sources)
        if len(self.sources) != len(DEFAULT_SOURCES):
            raise ValueError(f"ProductionTracers declares {len(DEFAULT_SOURCES)} source sites; got {len(self.sources)} sites")
        self.source_rate = 1.0 / (float(source_timescale_days) * DAY)      # per second, times S_i
        self.sigma_h = float(np.deg2rad(pulse_sigma_deg))
        self.sigma_z = float(pulse_sigma_decades)
        self.surface_sink = bool(surface_sink)
        self.absorb_layers = int(absorb_layers)
        self.sfc_layers = int(sfc_layers)
        self.aoa_reset_pa = float(aoa_reset_pressure_hpa) * 100.0
        self.aoa150_reset_pa = float(aoa150_reset_pressure_hpa) * 100.0
        self.sai_source_per_s = float(sai_source_per_s)
        self.sai_lat = float(np.deg2rad(sai_lat_deg))
        self.sai_p_top_pa = float(sai_p_top_hpa) * 100.0
        self.sai_p_bot_pa = float(sai_p_bot_hpa) * 100.0
        self.ref_file = str(ref_file)
        self.steady_source_pa = float(n2o_source_pressure_hpa) * 100.0
        self.lid_pa = None if lid_p_hpa is None else float(lid_p_hpa) * 100.0
        self.lid_tau_s = float(lid_tau_days) * DAY
        self.lid_clock_offset_s = float(lid_clock_offset_days) * DAY
        self.lid_sink_injections = bool(lid_sink_injections)
        self.first_segment = bool(first_segment)
        specs = physics_specs_from_constants(jcm_constants.physical_constants)
        self._per_s = float(specs.nondimensionalize(1.0 / units.second))
        self._coords_cached = False

    @classmethod
    def required_tracers(cls) -> tuple[TracerSpec, ...]:
        clocks = tuple(TracerSpec(n, units="day", initial_value=0.0, nondimensionalize=False) for n in cls.CLOCKS)
        pulses = tuple(TracerSpec(n, units="1", initial_value=0.0, nondimensionalize=False) for n in cls._pulse_names)
        sources = tuple(TracerSpec(n, units="1", initial_value=0.0, nondimensionalize=False) for n in cls._source_names)
        steady = tuple(TracerSpec(n, units="1", initial_value=1.0, nondimensionalize=False) for n in STEADY)
        return clocks + (TracerSpec("sai", units="1", initial_value=0.0, nondimensionalize=False),) + pulses + sources + steady

    # ------------------------------------------------------------------ shapes
    def shape(self, lat, lon, zeta, lat0, lon0, p0, suffix):
        """S(lat, lon, p) of one site on columns (lat, lon in radians, (ncols,)) and levels (zeta = log10(p/1000 hPa),
        (nlev,)): the Gaussian blob (suffix '') or the sharp-edged cap x slab of the same nominal size ('_box')."""
        la0, lo0 = np.deg2rad(lat0), np.deg2rad(lon0)
        cosang = np.sin(lat) * np.sin(la0) + np.cos(lat) * np.cos(la0) * np.cos(lon - lo0)
        theta = np.arccos(np.clip(cosang, -1.0, 1.0))                                          # (ncols,)
        dz = zeta - np.log10(p0 / 1000.0)                                                      # (nlev,)
        if suffix == "":
            return np.exp(-0.5 * (theta / self.sigma_h) ** 2)[None, :] * np.exp(-0.5 * (dz / self.sigma_z) ** 2)[:, None]
        if suffix == "_box":
            return ((np.abs(dz) <= self.sigma_z)[:, None] & (theta <= self.sigma_h)[None, :]).astype(np.float64)
        raise ValueError(f"unknown shape suffix {suffix!r}")

    # ------------------------------------------------------------------ setup
    def cache_coords(self, coords) -> None:
        vertical = coords.vertical
        sigma = vertical.centers if hasattr(vertical, "centers") else vertical.get_sigma_centers(P0_PA)
        sigma = np.asarray(sigma, dtype=np.float64)
        lat, lon = column_lat_lon(coords.horizontal)
        lat = np.asarray(lat, dtype=np.float64); lon = np.asarray(lon, dtype=np.float64)      # radians, (ncols,)
        n = sigma.shape[0]; idx = np.arange(n)
        surf_first = bool(sigma[0] > sigma[-1])
        def lowest(k):
            return (idx < k) if surf_first else (idx >= n - k)
        self._sigma = nnx.Variable(jnp.asarray(sigma))
        self._lat = nnx.Variable(jnp.asarray(lat))
        self._absorb_mask = nnx.Variable(jnp.asarray(lowest(self.absorb_layers)))
        self._sfc_mask = nnx.Variable(jnp.asarray(lowest(self.sfc_layers)))
        # shapes on the reference pressure (sigma * P0): pulses (npulse, nlev, ncols), sources (nsrc, nlev, ncols)
        zeta = np.log10(sigma * P0_PA / 1000e2)                                                # log10(p / 1000 hPa)
        def shapes(sites):
            return np.stack([self.shape(lat, lon, zeta, *c, s) for c in sites for s in SHAPES])
        self._targets = nnx.Variable(jnp.asarray(shapes(self.pulses), jnp.float32))
        self._sources = nnx.Variable(jnp.asarray(shapes(self.sources), jnp.float32))
        # WACCM reference: (lev, lat) -> model (nlev, ncols), latitude first then ln p
        ref = xr.open_dataset(self.ref_file)
        lat_deg = np.rad2deg(lat)
        lp_ref = np.log(ref.lev.values.astype(np.float64)); lp_mod = np.log(sigma * P0_PA / 100.0)
        order = np.argsort(lp_ref); lp_ref = lp_ref[order]
        def on_model(var):
            src = ref[var].values.astype(np.float64)[order]                                    # (lev, lat), lev ascending in p
            on_lat = np.stack([np.interp(lat_deg, ref.lat.values, src[k]) for k in range(src.shape[0])])   # (lev, ncols)
            return np.stack([np.interp(lp_mod, lp_ref, on_lat[:, j]) for j in range(on_lat.shape[1])], axis=1)
        self._q0 = nnx.Variable(jnp.asarray(np.stack([on_model(f"{sp}_q0") for sp in STEADY]), jnp.float32))   # (2, nlev, ncols)
        self._k = nnx.Variable(jnp.asarray(np.stack([on_model(f"{sp}_k") for sp in STEADY]), jnp.float32))     # (2, nlev, ncols), 1/s
        if self.lid_pa is not None:
            if "aoa_ref" not in ref:
                raise ValueError(f"{self.ref_file} has no 'aoa_ref' (WACCM mean age) but the tracer lid is on; "
                                 "rebuild it with scripts/make_waccm_tracer_ref.py or set lid_p_hpa: null")
            self._aoa_ref = nnx.Variable(jnp.asarray(on_model("aoa_ref"), jnp.float32))                        # (nlev, ncols), days
        self._coords_cached = True

    def _pressure(self, normalized_surface_pressure):
        return self._sigma.get_value()[:, jnp.newaxis] * normalized_surface_pressure * P0_PA

    def _reset_masks(self, p, sfc) -> dict:
        """Where each clock is reset to zero: ``p`` (nlev, ncols) in Pa, ``sfc`` the lowest-layers mask."""
        return {"aoa": p > self.aoa_reset_pa, "aoa150": p > self.aoa150_reset_pa, "aoa_sfc": sfc}

    def _lid_targets(self, a_ref) -> dict:
        """Value each clock relaxes to above the lid: WACCM's entry age, plus the tropospheric transit for clocks reset below it."""
        return {n: a_ref if n in self.ENTRY_CLOCKS else a_ref + self.lid_clock_offset_s / DAY for n in self.CLOCKS}

    # ------------------------------------------------------------------ step
    def __call__(self, state: PhysicsState, diagnostics: dict, forcing, terrain):
        dt = diagnostics["_dt_seconds"]
        p = self._pressure(state.normalized_surface_pressure)
        lat = self._lat.get_value()
        solar = getattr(forcing, "solar", None)
        tyear = solar.tyear if solar is not None else jnp.asarray(0.0)
        x = tyear * 365.0                                     # model-days into the year
        period = 365.0 / self.n_pulses
        first = jnp.logical_and(self.first_segment, x < dt / DAY)             # very first step of the run
        if self.injection == "once":
            fire = first
        else:
            fire = jnp.floor(x / period) != jnp.floor((x - dt / DAY) / period)  # an injection date lies in this step
        absorb = self._absorb_mask.get_value()[:, jnp.newaxis] if self.surface_sink else jnp.zeros_like(p, dtype=bool)
        sfc = self._sfc_mask.get_value()[:, jnp.newaxis]
        lid = (p < self.lid_pa) if self.lid_pa is not None else jnp.zeros_like(p, dtype=bool)
        tau = self.lid_tau_s
        tr = state.tracers
        d = {}
        # clocks: +1 day per day, reset in their boundary region, relaxed to WACCM's age above the lid
        if self.lid_pa is not None:
            lid_target = self._lid_targets(self._aoa_ref.get_value())
        reset = self._reset_masks(p, sfc)
        for name in self.CLOCKS:
            q = tr[name]
            t = jnp.where(reset[name], -q / dt, 1.0 / DAY)
            d[name] = jnp.where(lid, (lid_target[name] - q) / tau, t) if self.lid_pa is not None else t
        sai_box = (jnp.abs(lat) <= self.sai_lat) & (p >= self.sai_p_top_pa) & (p <= self.sai_p_bot_pa)
        d["sai"] = jnp.where(sai_box, self.sai_source_per_s, 0.0)
        targets = self._targets.get_value()
        for i, name in enumerate(self._pulse_names):
            q = tr[name]
            d[name] = jnp.where(fire, (targets[i] - q) / dt, jnp.where(absorb, -q / dt, 0.0))
        srcs = self._sources.get_value()
        for i, name in enumerate(self._source_names):
            q = tr[name]
            d[name] = jnp.where(absorb, -q / dt, self.source_rate * srcs[i])
        if self.lid_pa is not None and self.lid_sink_injections:
            for name in ("sai",) + self._pulse_names + self._source_names:
                d[name] = jnp.where(lid, -tr[name] / tau, d[name])
        q0 = self._q0.get_value(); kk = self._k.get_value()
        for i, name in enumerate(STEADY):
            q = tr[name]
            k_safe = jnp.minimum(kk[i], 0.25 / dt)            # forward-Euler safety for the fastest loss
            steady = jnp.where(p > self.steady_source_pa, (1.0 - q) / dt, -k_safe * q)
            if self.lid_pa is not None:
                steady = jnp.where(lid, (q0[i] - q) / tau, steady)
            d[name] = jnp.where(first, (q0[i] - q) / dt, steady)
        k = self._per_s                                       # per-second -> per nondimensional time
        zeros = jnp.zeros_like(state.temperature)
        return PhysicsTendency(u_wind=zeros, v_wind=zeros, temperature=zeros, specific_humidity=zeros,
                               tracers={n: k * v for n, v in d.items()}), diagnostics


_SHAPE_TEXT = {"": "Gaussian blob (sigma 12 deg, 0.25 decades)", "_box": "sharp-edged cap (radius 12 deg, +-0.25 decades)"}
for _i, (_lat, _lon, _p) in enumerate(DEFAULT_PULSES):
    for _s in SHAPES:
        ProductionTracers.output_attrs[f"pulse_{_i + 1}{_s}"] = {
            "units": "1",
            "long_name": (f"pulse tracer {_i + 1}{_s}: {_SHAPE_TEXT[_s]} of unit amplitude centred at {_lat} deg lat, {_lon} deg E, "
                          f"{_p} hPa, injected once at the start of the run"),
        }
for _i, (_lat, _lon, _p) in enumerate(DEFAULT_SOURCES):
    for _s in SHAPES:
        ProductionTracers.output_attrs[f"src_{_i + 1}{_s}"] = {
            "units": "1",
            "long_name": (f"continuous-source tracer {_i + 1}{_s}: {_SHAPE_TEXT[_s]} source, unit shape per 90 d, centred at {_lat} deg lat, "
                          f"{_lon} deg E, {_p} hPa, every step"),
        }


class ProductionTracersAoa500(ProductionTracers):
    """Phase 12: the Phase 11 tracer set plus ``aoa500``, a clock reset wherever p > 500 hPa.

    Susanne (2026-09-16) asked for the age of air with the clock set to zero at the surface (``aoa_sfc``)
    and at 500 hPa. A subclass rather than a fourth clock in ``ProductionTracers`` so the Phase 11
    experiments and their checkpoints keep their tracer set. ``aoa500`` must be in ``sl_mass_fixer_exclude``
    like the other clocks.
    """
    CLOCKS: ClassVar[tuple[str, ...]] = CLOCKS + ("aoa500",)
    output_attrs: ClassVar = {
        **ProductionTracers.output_attrs,
        "aoa500": {"units": "day", "long_name": "age of air, clock reset below 500 hPa (Phase 12; relaxed to WACCM6 age + offset above the lid)"},
    }

    def __init__(self, aoa500_reset_pressure_hpa: float = 500.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.aoa500_reset_pa = float(aoa500_reset_pressure_hpa) * 100.0

    def _reset_masks(self, p, sfc) -> dict:
        masks = super()._reset_masks(p, sfc)
        masks["aoa500"] = p > self.aoa500_reset_pa
        return masks
