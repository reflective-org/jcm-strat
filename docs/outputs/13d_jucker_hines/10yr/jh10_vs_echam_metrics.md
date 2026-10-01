# Phase 12 comparison: JCM full physics (5 yr) vs dry Jucker + Hines (10 yr; stride 1)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13jh_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 27.64 | 12.04 | -15.59 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 12.10 | 8.37 | -3.73 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.15 | 3.53 | +0.39 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.32 | 1.50 | -0.82 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.457 | 0.350 | -1.107 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.595 | 0.297 | -0.297 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.152 | 0.345 | +0.193 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.182 | 0.374 | +0.193 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.800 | 0.499 | -0.302 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.87 | 15.40 | -28.47 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 18.52 | 11.23 | -7.29 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.94 | 5.34 | +0.40 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.78 | 2.58 | -1.20 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.792 | 0.394 | -1.398 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.650 | 0.336 | -0.315 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.106 | 0.410 | +0.304 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.155 | 0.455 | +0.301 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.858 | 0.693 | -0.165 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.02 | 10.74 | -24.28 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.71 | 7.69 | -4.02 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.72 | 4.13 | -0.58 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.37 | 2.01 | -1.36 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.586 | 0.243 | -0.343 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.573 | 0.214 | -0.359 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.253 | 0.276 | +0.022 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.242 | 0.329 | +0.087 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.655 | 0.434 | -0.221 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 3.64 | +2.31 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 5.12 | +2.40 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 5.06 | +1.42 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 5.46 | +1.07 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 2.72 | +1.65 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 4.56 | +2.00 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 4.39 | +0.87 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 5.16 | +0.84 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.62 | +0.66 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 3.60 | +1.20 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.47 | +0.14 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.56 | +0.48 | 4.56 |
