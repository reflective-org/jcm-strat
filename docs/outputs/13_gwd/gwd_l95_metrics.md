# Phase 12 comparison: drag on: strat63 -> native L95 (all 95 levels, 1990-1994)

before `runs/p13gwd_5yr`, after `runs/p13gwdl95_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 23.75 | 23.96 | +0.22 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.38 | 11.65 | +0.27 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.74 | 3.73 | -0.01 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.44 | 1.55 | +0.11 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.046 | 1.059 | +0.013 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.464 | 0.488 | +0.024 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.332 | 0.298 | -0.033 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.188 | 0.112 | -0.076 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.022 | 0.079 | +0.057 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 36.11 | 36.21 | +0.10 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 16.68 | 17.08 | +0.40 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 5.24 | 5.11 | -0.13 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.07 | 2.16 | +0.09 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.289 | 1.276 | -0.013 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.473 | 0.478 | +0.005 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.319 | 0.275 | -0.044 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.266 | 0.170 | -0.096 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.134 | 0.201 | +0.068 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 24.29 | 24.08 | -0.21 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.62 | 11.56 | -0.06 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.14 | 4.12 | -0.02 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.53 | 1.72 | +0.19 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.766 | 0.792 | +0.026 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.474 | 0.491 | +0.018 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.358 | 0.307 | -0.051 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.216 | 0.139 | -0.077 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.088 | 0.134 | +0.047 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.35 | 1.50 | +0.15 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.71 | 2.80 | +0.08 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.80 | 3.77 | -0.02 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.40 | 4.40 | -0.00 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.26 | 1.17 | -0.09 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.64 | 2.53 | -0.11 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.74 | 3.56 | -0.18 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.36 | 4.25 | -0.11 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.10 | 1.04 | -0.06 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.47 | 2.38 | -0.09 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.55 | 3.39 | -0.16 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.14 | 4.05 | -0.09 | 4.56 |
