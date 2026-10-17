# Phase 22 decisions (questions that came up, options, what was chosen)

- **2026-10-16 17:00 PDT — Which iterative method is "Mooring's"?** The poster cites Chang (2006) and Wu & Reichler (2018);
  neither paper was readable (AMS/Science pages 403). Options: (a) Phase 17's update and call it Mooring's; (b) reconstruct the
  rule from public code; (c) ask Susanne. **Chose (b):** Wu & Reichler's `correct_teq.m` (public) has the Chang step
  `Teq - 2/3 (T_model - T_obs)`, pointwise, 3-D, monthly. Tracks C (zonal) and C3 (3-D) implement it.
- **Where to apply the correction vertically.** JuckerColumns adds Phase 17's correction to the JFV T_e, which the 100-250 hPa
  blend fades to nothing, and 100-400 hPa is not nudged. The 50 hPa vortex is the thermal-wind integral of the T gradient from
  the nudged 400 hPa up. **Added `te_correction_mode: total`** (correction on the blended T_eq on every level) so a correction
  can reach 400 hPa; A keeps Phase 17's 100-1 hPa exactly, AL and C/C3 use 400-1 hPa.
- **"Outside the tropics".** Options: Phase 17's suggestion (~30S-30N) or the QBO-nudging band (25 deg). **Chose zero at
  abs(lat) <= 25 deg, full at >= 35 deg (sin^2 taper):** the tropics stay as P20b (QBO-nudged winds, shallow-branch heating).
- **Polar-cap tau.** JFV gives 25-40 d at 50-100 hPa over the winter pole, so T_eq changes act slowly there. **Chose tau <= 10 d
  (B) and <= 5 d (B5) poleward of 60 deg, sin^2 blend from 50 deg, above 100 hPa**, applied as min(tau_JFV, tau_polar).
- **Iteration run.** Options: full 20-year reruns per iteration (~5 h each) or short restarts. **Chose 3-year restarts
  (2005-2007) from P20b's end-of-2004 state**, scored on 2005-04..2007-12 (first quarter discarded as adjustment): ~1 h per
  iteration on one GPU, 8 iterations per track. Each track's best is then confirmed by a full 1990-2009 run from the spin-up.
- **Target years.** Phase 17 used an ERA5 1990-1999 climatology. **Chose ERA5 for the same months as the window**: the run
  is nudged below 400 hPa, so its wave forcing follows those years (e.g. the 2006 SSW); a climatology would penalise what the
  nudging gets right. Risk: over-fitting 2005-2007 - the 20-year finals check it.
- **3-D ERA5 target.** The ERA5 cache used for nudging (WeatherBench2, 13 levels) stops at 50 hPa and is clamped above it (a
  first 3-D correction from it came out -16 K at 10 hPa, -40 K at 1 hPa - discarded). **Downloading ERA5 monthly means 1-500 hPa,
  1 deg, 2005-2007 from CDS** (`scripts/fetch_era5_t3d_monthly.py`, tmux `preproc_era5_t3d`); C3 waits for it (up to 6 h).
- **Cap.** Phase 17 capped the correction at +-25 K; the northern vortex now also fights the Lott-Miller drag, so **+-40 K**.
- **Output.** Iterations write only u, v, T, omega, surface pressure and aoa150/aoa_sfc (~25 GB per model year compacted) to keep
  ~40 iterations within the 8 TB free on /data.
