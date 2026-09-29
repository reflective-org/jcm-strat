# Phase 15 sweep leaderboard

2 scored run(s) as of 2026-09-29 14:40 PDT. Composite = mean(age RMSE/0.5 yr, w* log-error/ln 1.5, u RMSE/5 m/s, T RMSE/5 K); lower is closer; the age term is the entry-age clock against CLaMS (AGE minus CLaMS' own 0.09 yr at 150 hPa), w* against WACCM6, u and T against ERA5 (same months).

| rank | run | stage | composite | age RMSE `aoa150` vs CLaMS-entry [yr] | age bias | w* log-err | u RMSE [m/s] | T RMSE [K] | w* 100/70/50/30/10 hPa [mm/s] | `aoa150` 55 hPa trop / 50-70 | `aoa150` 12 hPa trop / 50-70 | `aoa_sfc` RMSE vs CLaMS | `aoa_sfc` 55 hPa trop (CLaMS 1.33) | `aoa500` 100 hPa trop [yr] (500->100 transit) | w* 1 hPa trop / NH / SH | min/yr | what |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **base10** | A | 0.805 | 0.48 | +0.20 | 0.18 | 3.7 | 5.4 | 0.35/0.24/0.29/0.33/0.47 | 1.83 / 3.74 | 3.77 / 4.73 | 1.99 | 3.92 | 1.70 | 0.99 / -2.26 / -2.57 | 30 | Phase 15 winner (Jucker, Rayleigh 30 d above 30 hPa, nudged < 100 hPa) continued from its 1994 checkpoint to 1999 - THE BASE |
| 2 | n100_10 | C | 0.866 | 0.49 | +0.25 | 0.18 | 4.7 | 5.5 | 0.35/0.24/0.29/0.33/0.46 | 1.87 / 3.80 | 3.82 / 4.78 | 2.00 | 3.94 | 1.72 | 1.32 / -2.25 / -2.61 | 29 | Phase |
| | *references* | | | CLaMS entry age (AGE − 0.09) | | WACCM6 | ERA5 | ERA5 | 0.40/0.21/0.20/0.26/0.47 | CLaMS 1.24 / 4.03 (WACCM entry 1.11 / 3.40) | CLaMS 3.59 / 4.47 (WACCM 2.82 / 4.18) | | | | full ECHAM 1994: +0.96 / −1.29 / −3.19 | | |
