# Phase 12 comparison: Jucker + Hines: 5 -> 10 years (strat81, nudged < 150 hPa, 1990-1994 -> 1990-1999; stride 1)

before `runs/p13jh_5yr`, after `runs/p13jh_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.00 | 12.04 | +0.04 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.30 | 8.37 | +0.07 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.48 | 3.53 | +0.06 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.49 | 1.50 | +0.01 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.352 | 0.350 | -0.002 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.296 | 0.297 | +0.001 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.341 | 0.345 | +0.004 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.369 | 0.374 | +0.005 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.490 | 0.499 | +0.009 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 15.18 | 15.40 | +0.22 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.96 | 11.23 | +0.27 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 5.20 | 5.34 | +0.14 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.51 | 2.58 | +0.07 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.397 | 0.394 | -0.003 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.323 | 0.336 | +0.012 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.396 | 0.410 | +0.014 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.449 | 0.455 | +0.006 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.661 | 0.693 | +0.032 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 10.71 | 10.74 | +0.03 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.69 | 7.69 | +0.00 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.13 | 4.13 | +0.01 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.04 | 2.01 | -0.03 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.241 | 0.243 | +0.002 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.216 | 0.214 | -0.002 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.277 | 0.276 | -0.001 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.322 | 0.329 | +0.007 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.447 | 0.434 | -0.014 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.13 | 3.64 | +0.51 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.67 | 5.12 | +0.45 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.59 | 5.06 | +0.47 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.11 | 5.46 | +0.35 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.38 | 2.72 | +0.34 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.28 | 4.56 | +0.28 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.17 | 4.39 | +0.22 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.92 | 5.16 | +0.23 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.41 | 1.62 | +0.21 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.47 | 3.60 | +0.13 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.45 | 3.47 | +0.02 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.44 | 4.56 | +0.13 | 4.56 |
