# Phase 15 sweep leaderboard

10 scored run(s) as of 2026-09-25 02:49 PDT. Composite = mean(age RMSE/0.5 yr, w* log-error/ln 1.5, u RMSE/5 m/s, T RMSE/5 K); lower is closer; the age term is the entry-age clock against CLaMS (AGE minus CLaMS' own 0.09 yr at 150 hPa), w* against WACCM6, u and T against ERA5 (same months).

**Best so far: `n100`** — ERA5 nudging cutoff raised from 150 to 100 hPa (bracket: how much of the gap is the tropopause layer): composite 0.924 (base 1.022); age RMSE 0.54 (base 0.55) yr, bias -0.23 (base -0.25); tropical w* 100/70/50/30/10 hPa 0.37/0.26/0.31/0.34/0.42 (base 0.32/0.28/0.34/0.36/0.43, WACCM6 0.40/0.21/0.20/0.26/0.47); u RMSE 5.2 (base 5.9) m/s, T RMSE 5.2 (base 5.4) K; `aoa150` 55 hPa tropics 1.50 (base 1.48) / 50-70 3.20 (base 3.22), 12 hPa tropics 3.24 (base 3.21) yr; cost 28 (base 32) min/yr.

Closer than the base (1.022): n100, ray30, hines1_l100, hines05. Further from it: spongeT, ray10, tau15cap, lm, tau05.

| rank | run | stage | composite | age RMSE `aoa150` vs CLaMS-entry [yr] | age bias | w* log-err | u RMSE [m/s] | T RMSE [K] | w* 100/70/50/30/10 hPa [mm/s] | `aoa150` 55 hPa trop / 50-70 | `aoa150` 12 hPa trop / 50-70 | `aoa_sfc` RMSE vs CLaMS | w* 1 hPa trop / NH / SH | min/yr | what |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **n100** | 1 | 0.924 | 0.54 | -0.23 | 0.22 | 5.2 | 5.2 | 0.37/0.26/0.31/0.34/0.42 | 1.50 / 3.20 | 3.24 / 4.32 | 0.96 | 1.46 / -2.33 / -2.63 | 28 | ERA5 nudging cutoff raised from 150 to 100 hPa (bracket: how much of the gap is the tropopause layer) |
| 2 | ray30 | 1 | 0.967 | 0.62 | -0.34 | 0.29 | 4.3 | 5.3 | 0.32/0.28/0.34/0.36/0.44 | 1.42 / 3.11 | 3.03 / 4.18 | 0.91 | 1.09 / -2.37 / -2.59 | 28 | Rayleigh drag 30 -> 1 hPa, tau 30 d at 1 hPa (a third of ray10) |
| 3 | hines1_l100 | 1 | 1.009 | 0.53 | -0.21 | 0.29 | 5.8 | 5.4 | 0.32/0.28/0.33/0.35/0.40 | 1.51 / 3.25 | 3.30 / 4.33 | 0.97 | 1.21 / -2.46 / -2.66 | 31 | Hines only, JCM default amplitude 1.0 m/s but launched at 100 hPa (no deposition in the troposphere/tropopause layer) |
| 4 | hines05 | 1 | 1.012 | 0.57 | -0.27 | 0.29 | 5.7 | 5.4 | 0.32/0.28/0.34/0.36/0.44 | 1.45 / 3.20 | 3.14 / 4.26 | 0.94 | 1.46 / -2.67 / -2.86 | 33 | Hines only (no Lott-Miller), launch 634 hPa, rms launch wind 0.5 m/s (half the JCM default) |
| 5 | base | 1 | 1.022 | 0.55 | -0.25 | 0.29 | 5.9 | 5.4 | 0.32/0.28/0.34/0.36/0.43 | 1.48 / 3.22 | 3.21 / 4.29 | 0.96 | 1.50 / -2.43 / -2.63 | 32 | p13_jucker segments 1990-1992 (Phase 13b): strat81, JFV relaxation, no drag - THE BASE |
| 6 | spongeT | 1 | 1.023 | 0.55 | -0.25 | 0.29 | 6.0 | 5.4 | 0.32/0.28/0.34/0.36/0.44 | 1.47 / 3.23 | 3.17 / 4.28 | 0.96 | 1.49 / -2.45 / -2.66 | 29 | sponge damps winds only: no temperature damping toward 250 K in the top four levels (JFV T_e there is 150-330 K) |
| 7 | ray10 | 1 | 1.075 | 0.75 | -0.50 | 0.29 | 5.0 | 5.4 | 0.33/0.29/0.35/0.37/0.45 | 1.33 / 2.92 | 2.82 / 3.93 | 0.87 | 0.85 / -2.32 / -2.60 | 29 | Rayleigh drag 30 -> 1 hPa, tau 10 d at 1 hPa (idealised stand-in for the missing upper-stratospheric wave drag) |
| 8 | tau15cap | 1 | 1.202 | 0.66 | -0.42 | 0.45 | 6.1 | 5.8 | 0.46/0.43/0.46/0.43/0.46 | 1.18 / 3.09 | 2.95 / 4.18 | 0.85 | 1.51 / -2.55 / -2.66 | 28 | JFV relaxation time capped at 15 d (lower stratosphere relaxes as fast as Polvani-Kushner; upper unchanged) |
| 9 | lm | 1 | 1.574 | 1.25 | -0.98 | 0.27 | 9.2 | 6.5 | 0.93/0.30/0.23/0.25/0.48 | 1.11 / 1.81 | 3.36 / 3.80 | 1.03 | 1.02 / -1.35 / -1.79 | 31 | Lott-Miller orographic drag only (no Hines), JCM defaults - the other half of the Phase 13c pair |
| 10 | tau05 | 1 | 1.580 | 0.71 | -0.45 | 0.52 | 11.2 | 6.9 | 0.41/0.41/0.51/0.54/0.61 | 1.17 / 3.15 | 2.94 / 4.24 | 0.87 | 3.18 / -3.04 / -3.62 | 30 | JFV relaxation time halved everywhere above 100 hPa (T_e unchanged) |
| | *references* | | | CLaMS entry age (AGE − 0.09) | | WACCM6 | ERA5 | ERA5 | 0.40/0.21/0.20/0.26/0.47 | CLaMS 1.24 / 4.03 (WACCM entry 1.11 / 3.40) | CLaMS 3.59 / 4.47 (WACCM 2.82 / 4.18) | | full ECHAM 1994: +0.96 / −1.29 / −3.19 | | |
