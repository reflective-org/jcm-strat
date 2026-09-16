# Phase 11 — tracer lid and revised production tracers: two 5-year review runs (1990–1994)

Status: **both 5-year chains complete** (2026-09-15 14:31 → 17:09 PDT, GPUs 0 and 1 in parallel, 31 min per
year each; `runs/p11a_5yr`, `runs/p11b_5yr`, ~650 GB each). Diagnostics below (2026-09-16). Awaiting Susanne's
choice of A or B for the extension to 2019; recommendation: **A**.

## Why

The 1990–2019 Phase 10 run (`docs/outputs/10_production`, `p10_30yr_aoa_*.png`) showed that the model
mesosphere is never ventilated: above ~1 hPa the mean age of air is uniform in latitude and equal to the
run length (23 yr after 30 yr), and that air leaks down until the stratosphere is 3–5× too old (55 hPa
tropics 6.5 yr vs CLaMS 1.3; 12 hPa 13 vs 3.7) and still growing at 0.2–0.5 yr per year. The tropical
upward mass flux at 100–10 hPa matches WACCM6 (`docs/outputs/09_resolution/strat/strat_metrics.md`), so
this is not a weak Brewer–Dobson circulation but a stagnant lid — no gravity-wave drag, a Rayleigh sponge
in the top four levels, a semi-Lagrangian top boundary with nothing above. The same old air explains
why N2O and CFC-11 sit ~6 km too low: air that has been to the mesosphere comes back N2O-free. The
Phase 9 statement "0.8 yr too old at 55 hPa" was a spin-up artefact (a 5-year clock cannot exceed 5 yr).

Susanne (2026-09-15) asked for a redo with: a fix for the stagnant top (her suggestion: use the sponge
as a sink or relaxation), no amplitudes, a sharp-edged twin of every pulse and source, and no surface
sink. Two 5-year runs first, then the chosen one is extended to 30 years.

## What changed against Phase 10 (`jcm_strat/advection_tracers.py`, `physics/strat_pk_qbo_prod11.yaml`)

| item | Phase 10 (`p10_prod`) | Phase 11 (`p11a_prod` / `p11b_prod`) |
|---|---|---|
| model top | Rayleigh sponge (4 levels above 0.2 hPa), tracers free | sponge unchanged; **tracer lid above 1 hPa**: relaxation with tau 1 d to WACCM6 REF-D1's zonal-mean mean age (`aoa_ref` in `waccm_tracer_ref.nc`, 1990–2019 annual mean, ~4.4 yr, flat in latitude) for `aoa150`, the same + 110 d (~0.3 yr tropospheric transit) for `aoa` and `aoa_sfc`; n2o / cfc11 to their WACCM state (≈ 0 there) |
| pulses | 5 Gaussian blobs, amplitudes 1.0 / 0.5 / 0.2 / 0.1 / 0.05 | **10**: the 5 Gaussian blobs at unit amplitude + a **sharp-edged twin** each (`pulse_<i>_box`: 1 inside the 12° cap × ±0.25 decades, 0 outside — the same nominal size) |
| continuous sources | 4 Gaussian, amplitudes 1.0 / 0.5 / 0.2 / 0.3, S/90 d per step | **8**: unit amplitude + box twins (`src_<i>_box`), S/90 d per step |
| surface sink | pulses and sources relaxed to 0 in the lowest two layers | **none** (`surface_sink: false`): pulses conserve their mass, sources and sai grow linearly |
| lid sink for pulses / sources / sai | — | **A: none** (`lid_sink_injections: false`); **B: relaxed to 0 above 1 hPa** (tau 1 d) |
| tracers in the output | 15 | 24 (+ u, v, T, q, omega, p_s) |
| everything else | strat63, ERA5 nudging < 150 hPa tau 6 h, PK stratosphere, QBO tau 1 d mean-preserving to 1 hPa, 6-hourly instantaneous, Gregorian calendar, clocks + n2o/cfc11 out of the mass fixer | unchanged |

Why a lid and not a dynamical fix: the mesospheric circulation is gravity-wave driven and the dry model
has no drag above the sponge; adding one is a tuning project (DEFERRED, Phase 11). Prescribing the tracers
where the dynamics are not credible is the same logic as nudging the troposphere to ERA5. Why 1 hPa and
not the sponge (0.2 hPa): the age field is flat in latitude, i.e. shows no circulation, down to 1–2 hPa;
a lid at the sponge would leave a stagnant layer between 0.2 and 1 hPa. Why WACCM's age and not zero:
relaxing the clocks to zero would make the mesosphere a second surface and the descending polar branch
artificially young.

Why sites are unchanged: pulses (0°/0°E/30 hPa, 45°N/120°E/70 hPa, 60°S/240°E/10 hPa, 30°N/300°E/3 hPa,
15°S/60°E/300 hPa), sources (0°/180°E/20 hPa, 30°N/60°E/100 hPa, 60°S/300°E/5 hPa, 30°S/240°E/55 hPa);
amplitude only scaled the field (Phase 10 linearity check), so it carried no information.

## Runs

| run | experiment | GPU | years | notes |
|---|---|---|---|---|
| `p11a_smoke5`, `p11b_smoke5` | 5 days from 1990-01-01 | 0 / 1 | — | GPU smoke, lid and shapes checked in the log |
| `p11a_1990..1994` → `p11a_5yr` | `p11a_prod` | 0 | 1990–1994 | A: no sink anywhere |
| `p11b_1990..1994` → `p11b_5yr` | `p11b_prod` | 1 | 1990–1994 | B: lid sink for pulses / sources / sai |

Command (both chains from `scripts/phase11_run5.sh`; a single chain by hand):
```
EXPERIMENT=p11a_prod PREFIX=p11a SCHEME=calendar YEARS=1990-1994 AGG=p11a_5yr SAVE_INTERVAL=0.25 GPU=0 bash scripts/chain_segments.sh
```
Extension of the chosen run to 2019: the same PREFIX with `YEARS=1990-2019` (finished segments are skipped,
the chain continues from the 1994 checkpoint; KEY_DECISIONS #38 — never the other prefix).

## Acceptance checks (filled when the chains finish)

| check | expectation | result |
|---|---|---|
| lid | age above 1 hPa within 0.1 yr of WACCM + offset after the first days; no latitude-flat plateau below the lid | **pass / partly**: 4.72 yr above the lid at day 5 (target 4.4 + 0.3); the oldest air anywhere is 5.4 yr (Phase 10: 23). But the age is nearly flat in latitude from the lid down to ~20 hPa: the upper stratosphere is filled from the lid, not ventilated (see Results) |
| age of air vs CLaMS (`p11?_5yr_aoa_*.png`) | bounded after 5 yr; 55 hPa tropics and 50–70° closer to CLaMS 1.3 / 4.1 yr than Phase 10's 2.2 / 3.8 at the same age of the run | **bounded**; 55 hPa: 2.7 / 4.5 yr (extratropics right, tropics 1.3 yr too old and still creeping: 2.31 → 2.52 → 2.67 at the last three year ends); 12 hPa: 4.5 / 5.1 vs CLaMS 3.7 / 4.6 |
| pulses | box twins injected exactly (first-frame RMSE ~0 where resolved); A: global mass constant to the fixer's roundoff; B: mass falls only through the lid | **pass**: box RMSE 0.017–0.032 (Gaussian 0.003–0.014; the interpolation of a step); no negative cells; A: mass constant to < 2e-3; B: only the 3 hPa pulse loses mass (14–15 %), the 10 hPa one 1 % |
| sources / sai | A: linear growth = emission; B: growth minus lid removal | **pass**: A mass = emission × t (residence 4.9–5.0 yr = elapsed time); B: src_3 (5 hPa) −4 %, src_1 (20 hPa) −1 %, sai −0.4 %, the rest identical; sai burden −1.5 % / −1.9 % of the analytic line (threshold 2 %) |
| n2o / cfc11 | in [0, 1]; stationary within ~2 yr; isopleths higher than Phase 10's (`p11?_5yr_steady_clocks.png`) | **in range, stationary — but NOT higher**: burden 0.967 → 0.858 (n2o), 0.940 → 0.809 (cfc11) in 5 yr, the Phase 10 30-year values; isopleths as in Phase 10 |
| throughput | ~25–35 min per year per chain with two chains sharing the CPU output path | **pass**: 4,180 d/hr stepping (7 ms/step), 750 d/hr end-to-end, 31 min per year, on both GPUs at once |

## Results (`docs/outputs/11_lid_tracers/`, 2026-09-16)

Diagnostics: `scripts/phase11_diag.sh` (aoa_vs_clams, pulse_diagnostics and tracer_budget at stride 20 = every
5 days, pulse_evolution panels/vertical/mass) and `scripts/ab_diff.py` (A vs B). The stride-4 default of
pulse_diagnostics walked the 654 GB archive for 4 h without finishing and was stopped.

**The lid does what it was asked to do, no more.** The clocks are bounded (`p11a_5yr_aoa_triptych.png`,
`p11a_5yr_steady_clocks.png` bottom row): the oldest air is 5.4 yr, the tropical pipe is young up to ~20 hPa,
the extratropical lower stratosphere reads 4.5 yr at 55 hPa against CLaMS 4.1. Above ~20 hPa the age is 4.5–5 yr
with almost no latitude structure — the value the lid prescribes at 1 hPa, propagated downward. The model's own
deep branch still does not ventilate the upper stratosphere; the lid has replaced an unbounded reservoir by a
bounded one at WACCM's mesospheric age. Year-end sampling of run A:

| end of | 55 hPa tropics | 55 hPa 50–70° | 12 hPa tropics | 12 hPa 50–70° | 3 hPa tropics | max |
|---|---|---|---|---|---|---|
| 1990 | 0.91 | 1.75 | 1.70 | 3.11 | 3.72 | 4.92 |
| 1992 | 2.31 | 3.84 | 3.89 | 4.67 | 4.63 | 4.98 |
| 1994 | 2.67 | 4.49 | 4.52 | 5.08 | 4.94 | 5.41 |

The tropical 55 hPa age is still creeping up (increments 0.21, 0.15 yr in the last two years) and will settle
somewhat above 3 yr; the tropics–extratropics contrast is 1.9 yr against CLaMS's 2.8. The Phase 10 5-year
number (2.2) was younger only because a 5-year clock cannot exceed 5 yr and the top was still empty of age.

**N2O and CFC-11 did not move** (`p11a_5yr_steady_clocks.png`, top row; `p11a_5yr_tracer_mass.png`): the
burdens fall to 0.858 / 0.809 within two years and stay there, exactly the Phase 10 values after 30 years, and
the isopleths sit where they sat. So the Phase 10 reading that *recirculated mesospheric air* depletes N2O was
incomplete: with the mesosphere pinned to WACCM's (near-zero) state the depletion is unchanged. It is produced
inside the stratosphere: air between 5 and 30 hPa is 4.5–5 yr old where WACCM has 3–4, and with WACCM's loss
frequencies that extra residence is extra photolysis. Same root cause (no deep-branch ventilation), different
path.

**The revised injections behave** (`p11a_5yr_pulse_burdens.png`, `p11a_5yr_<tracer>_evolution.png`,
`_vertical.png`): the box twins are injected to 0.02–0.03 RMSE (the semi-Lagrangian interpolation of a step),
never go negative, and their peaks decay like the Gaussians' (`p11a_5yr_pulse_metrics.md`); the mass of every
pulse is constant to < 2e-3 over five years in A; the sources grow linearly with residence time = elapsed time.

**A versus B** (`p11a_5yr_vs_p11b_5yr_burden_ratio.png`, `_zonal.png`): the meteorology is identical (the
tracers are passive), so the difference is the lid sink alone. It removes 14–15 % of the 3 hPa pulse
(`pulse_4`, `pulse_4_box`) within the first half year and then nothing more, 4 % of the 5 hPa source
(`src_3`, 2.6 % of its box twin) as a steady leak, 1 % of the 10 hPa pulse and the 20 hPa source, 0.4 % of
`sai`; the eight lower injections and n2o/cfc11/clocks are unchanged to < 1e-3. Spatially the B − A difference
is confined to above ~3 hPa and to the plumes' upper edges. **Recommendation: extend A.** The injected mass is
then conserved exactly, which the budget confirms and which is the advection scheme's own audit; B buys only a
slow leak from the two highest injections into a layer holding 0.1 % of the atmosphere.

Figures: `p11{a,b}_5yr_aoa_{triptych,profiles}.png`, `_steady_clocks.png`, `_pulse_burdens.png`,
`_pulse_evolution.png`, `_tracer_budget.png`, `_tracer_zonal.png`, `_omega.png`, `_<tracer>_evolution.png` and
`_<tracer>_vertical.png` for all 18 injected tracers, `_tracers_vertical.png`, `_tracer_mass.png`/`.md`,
`p11a_5yr_vs_p11b_5yr_{burden_ratio,zonal}.png`; numbers in `p11{a,b}_5yr_pulse_metrics.md`.

## Open questions

- The upper stratosphere (20–1 hPa) is filled from the lid: the model's deep branch does not reach it. The lid
  value (WACCM's 4.4 yr) is therefore what the stratosphere above 20 hPa will read in the 30-year run, and the
  N2O/CFC-11 depletion will persist. Only a dynamical fix (mesospheric drag; DEFERRED) changes that.
- Whether 1 hPa is the right lid height: the age is flat from the lid to ~3 hPa, so a lid at 3 hPa would give
  the same stratosphere below it and pin less; not tested (keep-it-simple).
- The tropical 55 hPa age converges slowly (~0.15 yr per year after five years); the 30-year extension will
  show the equilibrium.

## Operations: the GPU device nodes vanish at every reboot (2026-09-15/16)

The node rebooted on 2026-09-14 09:03 PDT and again on 2026-09-16 09:30 PDT. Its NVIDIA driver is a GPU-Operator
container (`/run/nvidia/driver`; `nvidia-smi` on the host is a sudo-chroot wrapper into it), and nothing recreates the
host's `/dev/nvidia*` nodes at boot. Without them JAX falls back to the CPU **silently** (`CUDA_ERROR_NO_DEVICE` in
the log, `1xcpu` in the provenance line, ~30 simulated days per hour instead of ~4,000) — the first Phase 11 pipeline
launch and the first launch of the 1995–2009 extension both ran on the CPU and were killed. Fix (root, after every
reboot until an admin adds a udev rule or boot unit):

```
for i in 0 1 2 3 4 5 6 7; do sudo mknod -m 666 /dev/nvidia$i c 195 $i; done
sudo mknod -m 666 /dev/nvidiactl c 195 255; sudo mknod -m 666 /dev/nvidia-modeset c 195 254
sudo mknod -m 666 /dev/nvidia-uvm c 501 0; sudo mknod -m 666 /dev/nvidia-uvm-tools c 501 1
```

(major/minor numbers from `/run/nvidia/driver/dev`). `scripts/chain_segments.sh` now refuses to start when JAX
sees no GPU. Check before any launch: `python -c "import jax; print(jax.devices())"` must print a `CudaDevice`.

## Extension of A to 2009 (requested 2026-09-16)

Susanne chose A and asked for 15 more years: `PREFIX=p11a YEARS=1990-2009 AGG=p11a_20yr` (tmux `strat_p11a_20yr`,
GPU 0; the chain skips 1990–1994 and continues from the 1994 checkpoint). First launch 14:01 PDT ran on the CPU
(see above), was stopped and its partial 1995 segment removed; relaunch pending the device nodes.

Relaunched 2026-09-16 15:47 PDT after Susanne recreated the device nodes (an earlier relaunch had a line break inside
the tmux command and left an idle shell). The 1995 segment stepped its first chunk in 24.8 s, as before. **The node's
GPUs are now NVIDIA H200 (141 GB), not the H100 80 GB the 1990–1994 segments ran on** — the reboots of 2026-09-14
and 09-16 were a hardware change. Same code, same driver container; the checkpoint restart is exact, but the two
halves of the chain ran on different silicon (roundoff-level differences only; the tracers are passive).
