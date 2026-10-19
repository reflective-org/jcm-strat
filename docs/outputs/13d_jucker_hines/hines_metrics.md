# Phase 12 comparison: Hines only added under the Jucker relaxation (strat81, nudged < 150 hPa, 1990-1994)

before `runs/p13jucker_5yr`, after `runs/p13jh_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 10.57 | 11.68 | +1.11 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.74 | 7.46 | +0.71 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.76 | 3.01 | +0.25 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.29 | 1.41 | +0.12 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.293 | 0.331 | +0.038 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.172 | 0.186 | +0.014 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.127 | 0.126 | -0.000 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.033 | 0.043 | +0.009 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.413 | 0.490 | +0.077 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.60 | 14.49 | +0.89 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.06 | 10.50 | +0.44 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.20 | 4.16 | -0.03 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.74 | 2.77 | +0.04 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.266 | 0.293 | +0.027 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.116 | 0.116 | -0.000 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.109 | 0.091 | -0.018 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.075 | 0.068 | -0.008 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.726 | 0.789 | +0.063 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 12.33 | 13.28 | +0.95 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.73 | 8.31 | +0.59 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.57 | 4.76 | +0.19 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.63 | 2.04 | +0.40 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.234 | 0.266 | +0.032 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.183 | 0.198 | +0.016 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.116 | 0.127 | +0.011 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.054 | 0.083 | +0.028 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.237 | 0.348 | +0.111 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.34 | 3.13 | -0.22 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.83 | 4.67 | -0.16 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.79 | 4.59 | -0.20 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.21 | 5.11 | -0.10 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.61 | 2.38 | -0.23 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 4.28 | -0.18 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.40 | 4.17 | -0.23 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.05 | 4.92 | -0.13 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.56 | 1.41 | -0.16 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.62 | 3.47 | -0.14 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.67 | 3.45 | -0.22 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.57 | 4.44 | -0.13 | 4.56 |
