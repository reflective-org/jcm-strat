# Phase 12 comparison: Phase 15 n100 vs JCM full physics (p12_echam), 1990-1994

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p15_n100_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 27.64 | 9.64 | -18.00 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 12.10 | 6.97 | -5.13 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.15 | 3.01 | -0.14 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.32 | 1.26 | -1.06 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.457 | 0.358 | -1.100 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.595 | 0.250 | -0.344 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.152 | 0.297 | +0.145 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.182 | 0.334 | +0.152 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.800 | 0.438 | -0.363 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.87 | 13.16 | -30.71 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 18.52 | 9.46 | -9.05 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.94 | 4.70 | -0.24 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.78 | 2.26 | -1.52 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.792 | 0.447 | -1.345 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.650 | 0.278 | -0.372 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.106 | 0.342 | +0.236 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.155 | 0.404 | +0.250 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.858 | 0.590 | -0.269 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.02 | 8.86 | -26.16 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.71 | 6.45 | -5.26 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.72 | 3.69 | -1.03 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.37 | 1.78 | -1.59 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.586 | 0.239 | -0.347 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.573 | 0.170 | -0.402 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.253 | 0.241 | -0.013 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.242 | 0.287 | +0.046 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.655 | 0.402 | -0.253 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 3.38 | +2.05 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 4.86 | +2.13 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 4.83 | +1.19 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 5.25 | +0.87 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 2.67 | +1.60 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 4.50 | +1.94 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 4.45 | +0.94 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 5.11 | +0.79 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.60 | +0.64 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 3.64 | +1.24 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.72 | +0.38 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.63 | +0.55 | 4.56 |
