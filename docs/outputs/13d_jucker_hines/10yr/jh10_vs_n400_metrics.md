# Phase 12 comparison: Jucker + Hines, ten years: ERA5 nudging cutoff 400 -> 150 hPa (strat81, 1990-1999; stride 1)

before `runs/p13jhn400_10yr`, after `runs/p13jh_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.31 | 12.04 | +2.73 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.60 | 8.37 | +1.77 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.89 | 3.53 | +0.64 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.19 | 1.50 | +0.32 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.157 | 0.350 | +0.194 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.213 | 0.297 | +0.084 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.289 | 0.345 | +0.056 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.328 | 0.374 | +0.046 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.421 | 0.499 | +0.078 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 12.34 | 15.40 | +3.06 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.13 | 11.23 | +2.10 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.76 | 5.34 | +0.58 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.29 | 2.58 | +0.29 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.220 | 0.394 | +0.174 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.283 | 0.336 | +0.053 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.363 | 0.410 | +0.047 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.415 | 0.455 | +0.041 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.603 | 0.693 | +0.090 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 7.77 | 10.74 | +2.97 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 5.81 | 7.69 | +1.88 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.97 | 4.13 | +0.16 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.00 | 2.01 | +0.01 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.117 | 0.243 | +0.126 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.164 | 0.214 | +0.050 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.249 | 0.276 | +0.027 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.314 | 0.329 | +0.015 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.420 | 0.434 | +0.014 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 4.56 | 3.64 | -0.92 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 5.72 | 5.12 | -0.60 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 5.83 | 5.06 | -0.77 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.75 | 5.46 | -0.30 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 3.77 | 2.72 | -1.05 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 5.30 | 4.56 | -0.74 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 5.35 | 4.39 | -0.97 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.57 | 5.16 | -0.41 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 2.26 | 1.62 | -0.64 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.96 | 3.60 | -0.36 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 4.21 | 3.47 | -0.74 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.90 | 4.56 | -0.33 | 4.56 |
