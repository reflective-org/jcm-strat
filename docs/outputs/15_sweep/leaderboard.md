# Phase 15 sweep leaderboard

3 scored run(s) as of 2026-09-24 15:44 PDT. Composite = mean(age RMSE/0.5 yr, w* log-error/ln 1.5, u RMSE/5 m/s, T RMSE/5 K); lower is closer; the age term is the entry-age clock against CLaMS (AGE minus CLaMS' own 0.09 yr at 150 hPa), w* against WACCM6, u and T against ERA5 (same months).

**Best so far: `hines05`** — Hines only (no Lott-Miller), launch 634 hPa, rms launch wind 0.5 m/s (half the JCM default): composite 1.012 (base 1.022); age RMSE 0.57 (base 0.55) yr, bias -0.27 (base -0.25); tropical w* 100/70/50/30/10 hPa 0.32/0.28/0.34/0.36/0.44 (base 0.32/0.28/0.34/0.36/0.43, WACCM6 0.40/0.21/0.20/0.26/0.47); u RMSE 5.7 (base 5.9) m/s, T RMSE 5.4 (base 5.4) K; `aoa150` 55 hPa tropics 1.45 (base 1.48) / 50-70 3.20 (base 3.22), 12 hPa tropics 3.14 (base 3.21) yr; cost 33 (base 32) min/yr.

Closer than the base (1.022): hines05. Further from it: ray10.

| rank | run | stage | composite | age RMSE `aoa150` vs CLaMS-entry [yr] | age bias | w* log-err | u RMSE [m/s] | T RMSE [K] | w* 100/70/50/30/10 hPa [mm/s] | `aoa150` 55 hPa trop / 50-70 | `aoa150` 12 hPa trop / 50-70 | `aoa_sfc` RMSE vs CLaMS | w* 1 hPa trop / NH / SH | min/yr | what |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **hines05** | 1 | 1.012 | 0.57 | -0.27 | 0.29 | 5.7 | 5.4 | 0.32/0.28/0.34/0.36/0.44 | 1.45 / 3.20 | 3.14 / 4.26 | 0.94 | 1.46 / -2.67 / -2.86 | 33 | Hines only (no Lott-Miller), launch 634 hPa, rms launch wind 0.5 m/s (half the JCM default) |
| 2 | base | 1 | 1.022 | 0.55 | -0.25 | 0.29 | 5.9 | 5.4 | 0.32/0.28/0.34/0.36/0.43 | 1.48 / 3.22 | 3.21 / 4.29 | 0.96 | 1.50 / -2.43 / -2.63 | 32 | p13_jucker segments 1990-1992 (Phase 13b): strat81, JFV relaxation, no drag - THE BASE |
| 3 | ray10 | 1 | 1.075 | 0.75 | -0.50 | 0.29 | 5.0 | 5.4 | 0.33/0.29/0.35/0.37/0.45 | 1.33 / 2.92 | 2.82 / 3.93 | 0.87 | 0.85 / -2.32 / -2.60 | 29 | Rayleigh drag 30 -> 1 hPa, tau 10 d at 1 hPa (idealised stand-in for the missing upper-stratospheric wave drag) |
| | *references* | | | CLaMS entry age (AGE − 0.09) | | WACCM6 | ERA5 | ERA5 | 0.40/0.21/0.20/0.26/0.47 | CLaMS 1.24 / 4.03 (WACCM entry 1.11 / 3.40) | CLaMS 3.59 / 4.47 (WACCM 2.82 / 4.18) | | full ECHAM 1994: +0.96 / −1.29 / −3.19 | | |
