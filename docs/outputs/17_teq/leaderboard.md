# Phase 15 sweep leaderboard

2 scored run(s) as of 2026-09-30 19:45 PDT. Composite = mean(age RMSE/0.5 yr, w* log-error/ln 1.5, u RMSE/5 m/s, T RMSE/5 K); lower is closer; the age term is the entry-age clock against CLaMS (AGE minus CLaMS' own 0.09 yr at 150 hPa), w* against WACCM6, u and T against ERA5 (same months).

**Best so far: `A1`** — mix10trop (Jucker + Rayleigh 30 d + tropical tracer mixing), iteration 1 (1998-1999 from mix10trop 1997): composite 0.611 (base 0.785); age RMSE 0.46 (base 0.44) yr, bias +0.14 (base +0.12); tropical w* 100/70/50/30/10 hPa 0.34/0.23/0.27/0.31/0.51 (base 0.35/0.24/0.29/0.33/0.47, WACCM6 0.40/0.21/0.20/0.26/0.47); u RMSE 2.9 (base 3.7) m/s, T RMSE 2.8 (base 5.4) K; `aoa150` 55 hPa tropics 1.73 (base 1.68) / 50-70 3.69 (base 3.68), 12 hPa tropics 3.66 (base 3.69) yr; cost 34 (base 34) min/yr.

Closer than the base (0.785): A1. Further from it: none.

| rank | run | stage | composite | age RMSE `aoa150` vs CLaMS-entry [yr] | age bias | w* log-err | u RMSE [m/s] | T RMSE [K] | w* 100/70/50/30/10 hPa [mm/s] | `aoa150` 55 hPa trop / 50-70 | `aoa150` 12 hPa trop / 50-70 | `aoa_sfc` RMSE vs CLaMS | `aoa_sfc` 55 hPa trop (CLaMS 1.33) | `aoa500` 100 hPa trop [yr] (500->100 transit) | w* 1 hPa trop / NH / SH | w* ref | ERA5 w* 100/70/50/30/10 | barrier age 55 hPa (25-35 minus 0-10) | min/yr | what |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **A1** | A | 0.611 | 0.46 | +0.14 | 0.16 | 2.9 | 2.8 | 0.34/0.23/0.27/0.31/0.51 | 1.73 / 3.69 | 3.66 / 4.69 | 1.24 | 2.89 | 1.05 | 1.28 / -2.15 / -2.45 | WACCM6 | —/—/—/—/— | 0.94 | 34 | mix10trop (Jucker + Rayleigh 30 d + tropical tracer mixing), iteration 1 (1998-1999 from mix10trop 1997) |
| 2 | p16_mix10trop | ref | 0.785 | 0.44 | +0.12 | 0.18 | 3.7 | 5.4 | 0.35/0.24/0.29/0.33/0.47 | 1.68 / 3.68 | 3.69 / 4.69 | 1.21 | 2.82 | 1.03 | 0.99 / -2.26 / -2.57 | WACCM6 | —/—/—/—/— | 0.95 | 34 | Phase 16 mix10trop (the start state of every Phase 17 track) |
| | *references* | | | CLaMS entry age (AGE − 0.09) | | WACCM6 | ERA5 | ERA5 | 0.40/0.21/0.20/0.26/0.47 | CLaMS 1.24 / 4.03 (WACCM entry 1.11 / 3.40) | CLaMS 3.59 / 4.47 (WACCM 2.82 / 4.18) | | | | full ECHAM 1994: +0.96 / −1.29 / −3.19 | | | CLaMS 1.57 | | |
