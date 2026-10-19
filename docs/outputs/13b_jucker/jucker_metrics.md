# Phase 12 comparison: Jucker et al. relaxation in place of Polvani-Kushner (strat81, no drag, 1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12l81_5yr`, after `runs/p13jucker_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 11.81 | 10.57 | -1.23 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.72 | 6.74 | -0.98 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.25 | 2.76 | -0.48 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.34 | 1.29 | -0.05 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.353 | 0.293 | -0.060 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.261 | 0.172 | -0.089 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.166 | 0.127 | -0.039 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.017 | 0.033 | +0.016 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.306 | 0.413 | +0.108 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.13 | 13.60 | +0.47 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.73 | 10.06 | +0.33 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.41 | 4.20 | -0.21 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.92 | 2.74 | +0.82 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.294 | 0.266 | -0.028 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.176 | 0.116 | -0.060 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.131 | 0.109 | -0.022 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.077 | 0.075 | -0.001 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.594 | 0.726 | +0.131 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 12.48 | 12.33 | -0.16 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.65 | 7.73 | +0.07 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.34 | 4.57 | +1.22 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.70 | 1.63 | -0.07 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.324 | 0.234 | -0.090 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.286 | 0.183 | -0.103 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.156 | 0.116 | -0.039 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.015 | 0.054 | +0.039 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.167 | 0.237 | +0.070 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.07 | 3.34 | +0.28 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.77 | 4.83 | +0.05 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.77 | 4.79 | +0.02 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.18 | 5.21 | +0.03 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.29 | 2.61 | +0.32 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.39 | 4.46 | +0.08 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.42 | 4.40 | -0.02 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.01 | 5.05 | +0.04 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.31 | 1.56 | +0.25 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.64 | 3.62 | -0.02 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.80 | 3.67 | -0.13 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.55 | 4.57 | +0.02 | 4.56 |
