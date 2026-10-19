# Phase 12 comparison: JCM full physics vs dry Jucker + GWD (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13juckergwd_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 21.55 | -7.16 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 9.04 | -2.22 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 2.31 | -2.16 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 0.65 | -2.08 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | 0.988 | -0.474 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | 0.308 | -0.294 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | 0.166 | -0.035 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.063 | -0.218 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 0.248 | -0.623 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 41.66 | -1.42 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 19.88 | -0.02 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 6.11 | -1.00 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 1.20 | -2.89 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 1.314 | -0.512 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | 0.374 | -0.324 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | 0.182 | -0.036 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.149 | -0.253 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 0.218 | -0.727 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 25.32 | -10.04 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 11.58 | -1.52 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.96 | -1.11 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 1.30 | -3.23 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | 0.559 | -0.057 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | 0.239 | -0.303 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | 0.095 | -0.074 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | -0.031 | -0.123 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 0.388 | -0.493 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 1.60 | +0.27 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.50 | -0.23 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 4.03 | +0.39 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 4.46 | +0.08 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 1.28 | +0.20 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.22 | -0.34 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 3.85 | +0.33 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.32 | +0.01 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.12 | +0.16 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.06 | -0.35 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.65 | +0.31 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.10 | +0.01 | 4.56 |
