# Phase 12 comparison: Hines only added under the Jucker relaxation (strat81, nudged < 150 hPa, 1990-1994) at STRIDE 1

before `runs/p13jucker_5yr`, after `runs/p13jh_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 10.94 | 12.00 | +1.06 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.62 | 8.30 | +0.68 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.17 | 3.48 | +0.30 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.32 | 1.49 | +0.17 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.308 | 0.352 | +0.045 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.272 | 0.296 | +0.025 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.328 | 0.341 | +0.013 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.353 | 0.369 | +0.017 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.456 | 0.490 | +0.034 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 14.27 | 15.18 | +0.91 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.48 | 10.96 | +0.48 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 5.06 | 5.20 | +0.14 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.40 | 2.51 | +0.11 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.354 | 0.397 | +0.043 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.300 | 0.323 | +0.023 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.385 | 0.396 | +0.012 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.435 | 0.449 | +0.015 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.630 | 0.661 | +0.031 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 9.68 | 10.71 | +1.03 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.01 | 7.69 | +0.68 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.79 | 4.13 | +0.33 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.78 | 2.04 | +0.26 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.205 | 0.241 | +0.037 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.193 | 0.216 | +0.022 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.260 | 0.277 | +0.017 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.298 | 0.322 | +0.024 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.402 | 0.447 | +0.045 | 0.452 |

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
