# Phase 12 comparison: JCM full physics vs dry Jucker + Hines (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13jh_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 11.68 | -17.03 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 7.46 | -3.81 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 3.01 | -1.46 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 1.41 | -1.32 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | 0.331 | -1.131 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | 0.186 | -0.416 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | 0.126 | -0.075 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.043 | -0.238 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 0.490 | -0.381 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 14.49 | -28.59 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 10.50 | -9.41 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 4.16 | -2.95 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 2.77 | -1.32 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 0.293 | -1.533 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | 0.116 | -0.582 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | 0.091 | -0.127 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.068 | -0.334 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 0.789 | -0.156 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 13.28 | -22.09 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 8.31 | -4.78 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.76 | -1.31 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 2.04 | -2.49 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | 0.266 | -0.350 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | 0.198 | -0.344 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | 0.127 | -0.042 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | 0.083 | -0.010 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 0.348 | -0.533 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 3.13 | +1.80 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 4.67 | +1.94 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 4.59 | +0.95 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 5.11 | +0.72 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 2.38 | +1.31 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 4.28 | +1.73 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 4.17 | +0.65 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.92 | +0.61 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.41 | +0.44 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 3.47 | +1.07 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.45 | +0.12 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.44 | +0.35 | 4.56 |
