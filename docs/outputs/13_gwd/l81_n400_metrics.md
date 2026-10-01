# Phase 12 comparison: strat81: ERA5 nudging cutoff 150 -> 400 hPa (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12l81_5yr`, after `runs/p13l81n400_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 11.81 | 7.69 | -4.12 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.72 | 5.69 | -2.03 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.25 | 2.51 | -0.74 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.34 | 1.37 | +0.03 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.353 | 0.121 | -0.232 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.261 | 0.131 | -0.130 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.166 | 0.054 | -0.111 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.017 | -0.032 | -0.049 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.306 | 0.436 | +0.130 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.13 | 9.56 | -3.57 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.73 | 7.32 | -2.41 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.41 | 3.50 | -0.91 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.92 | 1.84 | -0.08 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.294 | 0.096 | -0.198 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.176 | 0.100 | -0.077 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.131 | 0.057 | -0.074 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.077 | 0.021 | -0.055 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.594 | 0.608 | +0.013 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 12.48 | 6.66 | -5.83 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.65 | 4.32 | -3.33 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.34 | 2.53 | -0.82 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.70 | 1.65 | -0.05 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.324 | 0.116 | -0.208 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.286 | 0.145 | -0.140 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.156 | 0.020 | -0.136 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.015 | -0.036 | -0.051 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.167 | 0.433 | +0.266 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.07 | 3.76 | +0.69 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.77 | 5.28 | +0.50 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.77 | 5.23 | +0.46 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.18 | 5.40 | +0.22 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.29 | 3.16 | +0.87 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.39 | 5.05 | +0.66 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.42 | 5.02 | +0.60 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.01 | 5.32 | +0.31 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.31 | 1.90 | +0.59 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.64 | 4.09 | +0.45 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.80 | 4.34 | +0.54 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.55 | 4.85 | +0.30 | 4.56 |
