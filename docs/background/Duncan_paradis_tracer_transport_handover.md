# Fast stratospheric aerosol transport in JCM: two approaches

I tried to get Claude to make this accessible so that it's clear to everyone, without skimping on details. Skip anything that's obvious and just shout if you want more detail.

There are two approaches. Approach A, the "physical" one, is a stripped-down configuration of our own model, JCM, running on the semi-Lagrangian Dinosaur dycore. Approach B teaches the PARADIS neural network to output a reusable transport operator, and is the research challenger to Approach A. Section 3 explains why the physical approach is built on Dinosaur rather than on a neural weather model.

## 1. The problem in one paragraph

We want to simulate where injected stratospheric sulfate aerosol goes over 30 years, as fast as possible while staying realistic enough to trust. The aerosol is carried as several tens of 3-D fields (size modes or bins, plus SO2 and H2SO4 gas), and every field has to be moved by the wind every time step and then acted on by aerosol microphysics and radiation. Today the reference for this is the AIDE-SAI-link coupler (CESM winds read from an archive, Lin-Rood advection, TOMAS microphysics, RRTMGP radiation), which is accurate but slow and cannot let the winds respond to the aerosol. Both approaches below aim at a model where transport is cheap and shared across all fields, the circulation can respond to aerosol heating, and a 30-year run takes hours rather than weeks.

## 2. Shared background

### 2.1 Terms

**Tracer.** Any substance carried by the air without changing the air's motion: aerosol, ozone, a dye. Described by its *mixing ratio*, the fraction of the air in a grid cell that is that substance. Mixing ratio stays constant as an air parcel moves, even when the parcel expands or compresses, which is why it is the right quantity to transport.

**Advection / transport.** Movement of a tracer by the wind. Nothing else.

**Dynamical core (dycore).** The part of an atmospheric model that solves the fluid equations for wind, pressure and temperature. **Dinosaur** is a conventional (non-learned) spectral dycore written in JAX, used inside NeuralGCM and JCM. **PARADIS** is a learned dycore: a neural network that maps the atmosphere at time t to the atmosphere at t plus 6 hours.

**Physics.** Everything the dycore does not do: radiation, convection, clouds, turbulence, aerosol microphysics, gravity-wave drag. In JCM each of these is a plug-in `PhysicsTerm`, and a configuration is a list of them.

**Semi-Lagrangian (SL) transport.** For every grid cell, trace backwards along the wind to find where the air came from (the *departure point*), then read the tracer value there by interpolation. Stable for any time step. The departure points are computed once per step and reused for every tracer, so adding a tracer costs one interpolation.

**Mass conservation.** Total tracer mass must not change just because we moved it. Errors compound over 30 years, so this is not optional. **Positivity.** Mixing ratios cannot go negative.

**Nudging.** Adding a term that gently pulls a model variable toward a prescribed value (for example a reanalysis) on a chosen timescale. Strong nudging pins the variable; weak nudging only stops slow drift.

**Reanalysis (ERA5).** The best available reconstruction of the real atmosphere, hourly, 1940 to present. We use it as a target to nudge toward and as truth to validate against.

### 2.2 The single idea both approaches rest on

Transport is *linear in the tracer*: the fraction of what is in cell i that ends up in cell j over one step depends only on the wind, not on the substance. Written as an operation, new_tracer = T times old_tracer, where T is a large sparse matrix built from the wind. One T serves every tracer. For the ML reader, T is a stochastic matrix (non-negative entries summing to one), which gives conservation and positivity by construction, and linearity in the tracer means it generalises to fields never seen in training. For the atmosphere reader, this is the discretised continuity equation for a passive tracer; every advection scheme you know is a way of building T.

Semi-Lagrangian transport is one such T (the interpolation weights). Approach A uses the one already built into Dinosaur. Approach B tries to make PARADIS produce one.

## 3. Why the physical approach is built on Dinosaur

Currently AIDE-SAI-link takes winds from PARADIS and uses Lin-Rood to advect tracers appropriately. A semi-Lagrangian transport scheme would be more efficient, especially as the number of tracers increases, but there is no need: the `semi-lagrangian` branch of Dinosaur (Stephan Hoyer's fork, open PR neuralgcm/dinosaur#135) already contains exactly that, and we can already run it without PARADIS winds. It has pole-free departure-point solves in Cartesian coordinates, gather-based interpolation with longitude wrap and cross-pole handling, a quasi-monotone limiter, hybrid vertical coordinates, and an option to store tracers on the grid rather than spectrally (`nodal_tracers`) so sharp aerosol fields skip every spectral transform and stay exactly non-negative. It is differentiable. On GPU the departure solve dominates and the gather is cheap, so many tracers add little.

Beyond convenience, a physics dycore removes the largest risks of a learned one for a 30-year run: it does not drift over tens of thousands of steps, its response to aerosol heating is real dynamics rather than an out-of-distribution extrapolation, tracers are first-class variables, and vertical velocity comes from mass continuity by construction. PARADIS keeps two advantages, a 6-hour step and the open research question of whether a learned dycore can beat a physical one, which is exactly what Approach B and the shared benchmark exist to test.

Two things still need doing on the Dinosaur side: conservative remapping is not in the PR, so SL tracers are bounded but not exactly mass-conserving (fix in Section 4.4), and the time-step extension study the PR defers is the number that decides our speed comparison (Section 4.6).

## 4. Approach A: a stripped-down stratosphere model in JCM (atmospheric scientist)

### 4.1 The idea

Run JCM on the Dinosaur-SL dycore with only the physics that matters for stratospheric sulfate: transport, aerosol microphysics, and the radiative heating of the aerosol. Remove convection, clouds, cloud microphysics and the detailed surface scheme. Replace what the troposphere needs from convection with nudging or relaxation. Keep gravity-wave drag. Concentrate the vertical levels on the stratosphere. Then find the longest time step the model tolerates. The hypothesis is that a model this lean, on a semi-Lagrangian core, runs 30 years in hours while keeping the stratospheric circulation realistic.

JCM's composable physics makes the mechanics trivial: `echam_physics(radiation_scheme=...).remove("convection").remove(...)`. The scientific content of the experiment is entirely in *what* you remove, what you replace it with, and how you validate that the stratosphere survived.

### 4.2 The trap: you cannot remove convection and keep a troposphere

Convection is what keeps the troposphere stable. Switch it off with radiation still on and the tropics become super-adiabatic, the model either goes unstable or invents grid-scale convection, the Hadley circulation is wrong, and so is the wave forcing from below that drives the entire stratospheric circulation. Something must replace convection's role below the tropopause. We will build two configurations, in this order.

**Configuration 1, ERA5 nudging (first).** Nudge tropospheric winds and temperature toward ERA5 on a timescale of a few hours. This is "specified dynamics", the standard approach for stratospheric composition modelling (WACCM-SD). The troposphere then carries the real QBO forcing, ENSO and volcanic-era meteorology of whichever 30 years we choose, the wave forcing into the stratosphere is right by construction, and the stratosphere above is left free (or only weakly nudged, see 4.3) to respond to the aerosol. It also gives us the ideal validation case: nudge 1991 to 1995 and compare against the observed Pinatubo aerosol. Costs I/O, not compute.

**Configuration 2, Polvani-Kushner (second).** Replace tropospheric physics with Newtonian relaxation of temperature toward an analytic, seasonally varying equilibrium profile, with a realistic stratosphere and polar vortex above (the Polvani and Kushner 2002 setup). JCM already ships the Held-Suarez relaxation this extends. Fully self-contained, no external data, very fast, and it produces its own baroclinic eddies. It lacks the stationary planetary waves from land-sea contrast unless terrain is kept on. This is the pure speed benchmark and the idealised laboratory.

### 4.3 Radiation and thermodynamics: three tiers

Once moist physics is gone there is no interactive water cycle, and this changes what radiation has to do. Three options, from cheapest to most complete. Start at the top and move down only if validation demands it.

**Tier 1, aerosol-only heating.** We already have a configuration that calls radiation a second time to diagnose the aerosol radiative effect (all-sky minus clean-sky). Make that the *only* radiation call: the model's radiative tendency is just the aerosol heating anomaly, and the background temperature structure of the stratosphere is maintained by the relaxation or nudging term instead of by full radiation. This is coherent, and it is exactly how Polvani-Kushner works, but it carries one requirement that must be set deliberately: the relaxation timescale in the stratosphere is now playing the role of radiative damping of the aerosol-induced warming. Set it to the real stratospheric radiative relaxation timescale, roughly 5 to 20 days and altitude-dependent, not to the hours used in the troposphere. Too short and you damp out the self-lofting and circulation response that the experiment exists to capture; too long and the stratosphere drifts. Even in this dry configuration the aerosol scheme needs stratospheric water vapour for the H2SO4/H2O droplet composition and hygroscopic growth, so prescribe an H2O climatology as an input field.

**Tier 2, full RRTMGP with prescribed trace gases.** JAX-RRTMGP lets us specify O3, H2O, CO2, CH4 and N2O directly, so feed it climatologies (SPARC or CESM output; the AIDE coupler already reads Q, O3 and CH4 for RRTMGP, so these inputs simply become climatological). The stratosphere then has its own radiative equilibrium and the nudging can be weakened there. Surface needs only prescribed SST or land temperature and albedo as boundary conditions, which JCM's forcing config already handles; the multi-tile surface scheme can go. This is the configuration whose stratosphere you can defend on its own terms.

**Tier 3, emulated radiation.** The neural-network radiation backend was recently fixed and is a selectable option (`radiation_scheme="emulated"`). Check that it reproduces Tier 2 heating rates for aerosol-perturbed profiles before trusting it, since it was not trained on volcanic-scale sulfate loadings. If it does, it is the fastest full-radiation option.

### 4.4 Aerosol scheme

Start with the MAM4 modal scheme already in JCM's ECHAM stack (a handful of transported moments per mode rather than 40 bins). It is much cheaper, already wired to the radiation, and enough to establish the transport, coupling and time-step results. Bring in TOMAS from the AIDE coupler (the `gpu-fast` engine wrapped as a `PhysicsTerm`) once the configuration is stable, as the fidelity check on size-distribution details that matter for sedimentation and optics.

Whichever scheme, carry the aerosol as nodal tracers in Dinosaur-SL and add one extra tracer for dry-air mass moved by the same operator. Dividing every tracer by the moved air mass restores mass consistency cell by cell without a global rescaling, and it is the standard fix for a non-conserving SL scheme. Fold gravitational settling into transport as a per-mode (or per-bin) vertical offset on top of the shared horizontal departure geometry.

### 4.5 Vertical grid, gravity waves and the QBO

Adapt the existing high-top 95-level configuration down to about 30 levels rather than designing from scratch. Keep the top high (around 0.01 hPa), keep a sponge of Rayleigh damping over the top four or five levels so upward-propagating waves are absorbed rather than reflected off the lid, and spend the remaining levels roughly as: six to eight coarse tropospheric levels to about 150 hPa, about sixteen stratospheric levels at roughly 1 km spacing from 150 to 1 hPa, and the rest in the mesospheric sponge. Hybrid coordinates are already supported on the SL branch and in use; confirm the semi-Lagrangian equation class is on the hybrid path in the adapted config, since the PR text lists it as a deferred item.

Keep Hines non-orographic gravity-wave drag, and orographic drag if terrain is on. Without it a coarse stratospheric model has no QBO, a polar-night jet that is too strong, and a cold-pole bias, and all three change the Brewer-Dobson circulation and hence aerosol residence time. Hines uses a fixed launch spectrum, so it does not break when convection is removed.

Know that ~30 levels will almost certainly not produce a spontaneous QBO, which needs about 500 to 700 m spacing in the tropical lower stratosphere and tuned drag. Configuration 1 partly rescues this because the nudged troposphere supplies observed wave forcing, and if needed the tropical stratospheric zonal wind can be nudged toward the observed QBO, a standard trick in SAI studies. Configuration 2 will simply not have one; treat that as a known limitation of the idealised model.

### 4.6 Where the time-step ceiling actually is

Give each process its own clock. The semi-Lagrangian dycore is the pacing item: its ceiling is the convergence of the trajectory iteration, which the PR analysis puts near 2.8 h in jet-region shear, so expect a stable 1 to 2 h step at T42 to T63. The stripped troposphere helps, because the fastest resolved tendencies (convective heating) are gone. Radiation can run every 2 to 3 h; the stratospheric radiative timescale is days, so this is conservative. SO2 oxidation has a monthly lifetime and is fine at any of these steps provided the diurnal OH cycle is sampled, which the AIDE chemistry already does. Sedimentation is far inside its stability limit for sub-micron particles. The one stiff process is nucleation and condensation inside the injection plume, with timescales of minutes to hours; sub-step the microphysics adaptively in those columns only, since the rest of the globe is nowhere near that regime. The AIDE coupler already runs TOMAS stably at a 6 h step, so this is a known quantity.

The experiment is then clean: double the dycore step until the polar vortex climatology or the age of air degrades. That step is the answer, and simulated-years-per-day at that step is the number to report.

### 4.7 Validation, in order

Age of air (release a clock tracer, compare stratospheric transit times to the CLaMS/ERA5 reference). Polar vortex and zonal-mean climatology against ERA5. Then the nudged 1991 to 1995 Pinatubo run: compare burden, AOD and e-folding time against SAGE and HIRS. That last test is the one that says whether a 30-year SAI number from this configuration means anything.

### 4.8 Steps

1. Build the ~30-level hybrid grid from the 95-level config, with sponge. Run the dry dycore alone with Held-Suarez forcing to confirm it is stable and the vortex forms.
2. Add ERA5 nudging of tropospheric u, v, T (Configuration 1). Confirm the stratosphere sits in a realistic climatology with the nudging off above ~100 hPa (or weak, at radiative timescales, if using Tier 1).
3. Add MAM4 as nodal tracers plus the air-mass tracer, with Hines drag on and everything else off. Add settling. Run a passive injection with radiation off; check conservation and age of air.
4. Turn on Tier 1 aerosol-only heating with the stratospheric relaxation timescale set to radiative values. Check for self-lofting in a tropical injection.
5. Run the time-step doubling study.
6. Pinatubo validation (1991 to 1995).
7. Then, as needed: Tier 2 RRTMGP with trace gases, Tier 3 emulated radiation check, TOMAS swap-in, Configuration 2 Polvani-Kushner.

## 5. Approach B: retraining PARADIS with a transport head (ML engineer)

### 5.1 The idea

PARADIS was trained to predict a fixed list of variables six hours ahead, and nothing in that objective ever asked it to separate "how air moves" from "what happens to each variable", so the movement is baked into weights specific to those variables. There is no input slot for a new field. An earlier attempt to add a generic passive tracer to training failed because the CESM training data had no tracer at high enough temporal resolution.

The fix is to give PARADIS an extra output that *is* T from Section 2.2: for each cell, non-negative weights over its neighbours summing to one, depending only on the flow and never on the tracer. Train those weights so that applying T to a tracer reproduces how it actually moved. Because the tracer never enters the weights, the trained T applies to any new field. Do not modify PARADIS's existing advection layer to do this; it learns separate trajectories for different internal modes, which is how it represents wave propagation. Add the transport head alongside it.

### 5.2 Steps

1. **Generate training data with Dinosaur.** Run Dinosaur (Eulerian or SL, on the same grid and 6 h step as PARADIS) with moist physics off so only the wind acts on tracers. Add several passive tracers per run with deliberately varied shapes: smooth gradients, compact blobs, thin filaments, plus a realistic field such as specific humidity as a starting pattern. Save at least hourly. Variety matters: a network trained on one kind of pattern learns that pattern instead of learning transport (the literature documents models trained on square pulses turning every shape into squares).

2. **Design the transport head.** Either a *weight head* (logits over a 5-by-5 horizontal stencil, softmax, so conservation and positivity are built in) or a *trajectory head* (a displacement vector per cell, then interpolate, with conservation restored as in 4.4). The stencil must cover the largest one-step displacement; if the jet moves air further, widen it or apply T several times per step (repeated application of a stochastic matrix stays stochastic).

3. **Train.** Loss is the difference between T applied to the Dinosaur tracer at t and the Dinosaur tracer one step later, plus a multi-step rollout loss and a spectral loss to stop filaments being smoothed away, trained jointly with the normal weather loss so forecast skill does not degrade. No conservation loss is needed.

4. **Inference.** Each step PARADIS produces the weather state and T; apply T to all tracers. No separate transport code path.

5. **Validate.** Same idealised tests as Approach A (solid-body rotation, deformational flow that reverses), a check that PARADIS's forecast metrics are unchanged, and then the head-to-head in Section 6.

## 6. The shared benchmark

Everything reports on one harness. Run the same 1-year stratosphere-only injection scenario through Approach A (Dinosaur-SL) and through PARADIS with its transport head, with Lin-Rood in the AIDE coupler as the reference. Report wall-clock per step and simulated-years-per-day, mass drift, tracer correlation against the reference, and the physical diagnostics (burden, AOD550, e-folding time, age of air). This is the only defensible way to answer "which dycore" and it is why keeping the Lin-Rood path alive in the same JAX configuration is worth the maintenance.

## 7. Shared risks

**Approach A, damping the response you want.** In the Tier 1 configuration the stratospheric relaxation timescale is the radiative damping of the aerosol warming. Get it wrong and the experiment quietly answers a different question. Check it against Tier 2 on a short run early.

**Approach A, no QBO and no interactive water.** Both are known limitations of a ~30-level dry model. Configuration 1 mitigates the first through the nudged troposphere; nothing mitigates the second, so the tape-recorder water-vapour diagnostic is unavailable and stratospheric H2O is an input.

**Approach B, long rollouts.** 30 years is about 44,000 consecutive PARADIS steps. Weather networks are built and validated for days and typically drift over weeks. Run one year and inspect the zonal-mean state before investing further.

**Both, vertical motion.** Over 30 years the aerosol lifetime is controlled by slow vertical motion (the Brewer-Dobson circulation), not by horizontal transport. Dinosaur gets it from continuity by construction; PARADIS does not, and its vertical velocity should be derived from continuity rather than taken from the network. Age of air is the test for both.

## 8. Recommended order

Start Approach A immediately; steps 1 to 3 in Section 4.8 reuse existing JCM configurations and produce a running model within weeks. Start the Dinosaur data generation for Approach B in parallel, since it is the long pole and depends on nothing else. Begin Approach B's architecture and training once a month or so of tracer data exists. Judge everything on the Section 6 harness.

