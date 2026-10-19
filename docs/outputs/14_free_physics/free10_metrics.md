# Phase 12 comparison: free-running full physics 1990-1999 vs the nudged full physics 1990-1994 (both T63L95)

before `runs/p12echam_5yr`, after `runs/p14free_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 12.56 | -16.15 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 7.53 | -3.73 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 2.07 | -2.40 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 3.10 | +0.37 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | -0.054 | -1.516 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | -0.218 | -0.821 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | -0.276 | -0.477 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.009 | -0.272 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 1.324 | +0.453 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 11.84 | -31.24 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 9.52 | -10.39 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 5.38 | -1.74 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 4.26 | +0.17 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 0.214 | -1.612 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | -0.303 | -1.001 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | -0.126 | -0.344 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.308 | -0.094 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 1.355 | +0.410 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 36.13 | +0.77 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 15.93 | +2.84 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.53 | -1.54 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 5.01 | +0.48 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | -0.488 | -1.104 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | -0.086 | -0.628 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | -0.368 | -0.537 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | -0.279 | -0.372 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 1.294 | +0.413 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 1.81 | +0.48 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.41 | -0.31 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 3.63 | -0.01 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 4.54 | +0.15 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 1.57 | +0.50 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.22 | -0.34 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 3.47 | -0.05 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.44 | +0.13 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.45 | +0.49 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.08 | -0.32 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.31 | -0.03 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.22 | +0.14 | 4.56 |
