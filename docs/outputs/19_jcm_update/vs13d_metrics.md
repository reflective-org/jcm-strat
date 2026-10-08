# Phase 12 comparison: 13d (Jucker + Hines, nudged < 150 hPa, old jcm) vs 19d (nudged < 400 hPa, new jcm), 1990-1994 (stride 1)

before `/data/JCM_stripped/jcm-strat-phase13/runs/p13jh_5yr`, after `runs/p19jhn400_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.00 | 8.79 | -3.21 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.30 | 6.20 | -2.10 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.48 | 2.87 | -0.61 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.49 | 1.23 | -0.26 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.352 | 0.117 | -0.236 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.296 | 0.191 | -0.106 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.341 | 0.273 | -0.068 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.369 | 0.320 | -0.050 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.490 | 0.411 | -0.079 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 15.18 | 11.18 | -4.00 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.96 | 8.27 | -2.68 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 5.20 | 4.71 | -0.49 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.51 | 2.38 | -0.13 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.397 | 0.170 | -0.227 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.323 | 0.246 | -0.077 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.396 | 0.344 | -0.052 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.449 | 0.426 | -0.023 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.661 | 0.637 | -0.024 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 10.71 | 7.38 | -3.33 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.69 | 5.41 | -2.28 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.13 | 3.70 | -0.43 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.04 | 1.81 | -0.22 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.241 | 0.074 | -0.167 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.216 | 0.148 | -0.068 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.277 | 0.231 | -0.046 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.322 | 0.288 | -0.034 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.447 | 0.391 | -0.056 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.13 | 2.28 | -0.84 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.67 | 4.16 | -0.51 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.59 | 3.82 | -0.77 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.11 | 4.68 | -0.42 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.38 | 1.79 | -0.59 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.28 | 3.87 | -0.41 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.17 | 3.45 | -0.71 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.92 | 4.47 | -0.45 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.41 | 1.14 | -0.27 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.47 | 3.38 | -0.09 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.45 | 2.90 | -0.55 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.44 | 4.08 | -0.36 | 4.56 |
