# Phase 12 comparison: free-running full physics, first 5 yr (1990-1994) vs the nudged full physics 1990-1994 (both T63L95)

before `runs/p12echam_5yr`, after `runs/p14free_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 12.76 | -15.95 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 7.54 | -3.72 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 2.05 | -2.42 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 3.04 | +0.31 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | -0.049 | -1.511 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | -0.211 | -0.814 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | -0.275 | -0.476 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.010 | -0.271 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 1.298 | +0.427 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 12.21 | -30.87 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 9.65 | -10.25 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 5.40 | -1.71 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 4.23 | +0.14 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 0.207 | -1.619 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | -0.305 | -1.003 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | -0.132 | -0.350 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.288 | -0.114 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 1.291 | +0.346 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 35.65 | +0.28 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 15.90 | +2.81 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.41 | -1.67 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 4.94 | +0.41 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | -0.476 | -1.091 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | -0.057 | -0.599 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | -0.362 | -0.530 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | -0.251 | -0.344 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 1.277 | +0.397 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 1.75 | +0.42 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.41 | -0.32 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 3.54 | -0.09 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 4.47 | +0.09 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 1.52 | +0.45 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.22 | -0.34 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 3.40 | -0.12 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.39 | +0.08 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.40 | +0.44 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.09 | -0.31 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.24 | -0.09 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.17 | +0.09 | 4.56 |
