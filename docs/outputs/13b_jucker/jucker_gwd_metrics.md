# Phase 12 comparison: Hines + Lott-Miller drag added under the Jucker relaxation (strat81, 1990-1994)

before `runs/p13jucker_5yr`, after `runs/p13juckergwd_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 10.57 | 21.55 | +10.97 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.74 | 9.04 | +2.30 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.76 | 2.31 | -0.45 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.29 | 0.65 | -0.64 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.293 | 0.988 | +0.695 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.172 | 0.308 | +0.136 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.127 | 0.166 | +0.039 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.033 | 0.063 | +0.029 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.413 | 0.248 | -0.166 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.60 | 41.66 | +28.06 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.06 | 19.88 | +9.83 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.20 | 6.11 | +1.92 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.74 | 1.20 | -1.54 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.266 | 1.314 | +1.048 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.116 | 0.374 | +0.258 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.109 | 0.182 | +0.073 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.075 | 0.149 | +0.074 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.726 | 0.218 | -0.508 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 12.33 | 25.32 | +13.00 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.73 | 11.58 | +3.85 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.57 | 4.96 | +0.39 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.63 | 1.30 | -0.34 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.234 | 0.559 | +0.325 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.183 | 0.239 | +0.057 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.116 | 0.095 | -0.022 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.054 | -0.031 | -0.085 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.237 | 0.388 | +0.151 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.34 | 1.60 | -1.75 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.83 | 2.50 | -2.33 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.79 | 4.03 | -0.76 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.21 | 4.46 | -0.75 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.61 | 1.28 | -1.33 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 2.22 | -2.24 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.40 | 3.85 | -0.55 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.05 | 4.32 | -0.73 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.56 | 1.12 | -0.44 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.62 | 2.06 | -1.56 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.67 | 3.65 | -0.03 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.57 | 4.10 | -0.47 | 4.56 |
