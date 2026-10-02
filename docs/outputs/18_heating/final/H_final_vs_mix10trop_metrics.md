# Phase 12 comparison: Phase 18 H_final vs Phase 16 mix10trop, 1990-1999

before `/data/JCM_stripped/jcm-strat-phase16/runs/p16_mix10trop_10yr`, after `runs/p18_H_final_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.75 | 9.49 | -0.25 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.11 | 6.97 | -0.14 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.14 | 3.05 | -0.08 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.32 | 1.45 | +0.13 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.355 | 0.331 | -0.025 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.251 | 0.211 | -0.040 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.301 | 0.252 | -0.049 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.340 | 0.309 | -0.031 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.451 | 0.538 | +0.087 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.43 | 12.34 | -1.09 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.73 | 8.76 | -0.97 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.98 | 4.34 | -0.65 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.50 | 2.70 | +0.20 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.442 | 0.405 | -0.037 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.286 | 0.230 | -0.056 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.349 | 0.279 | -0.070 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.405 | 0.332 | -0.072 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.610 | 0.662 | +0.053 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 9.08 | 8.22 | -0.85 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 6.72 | 6.10 | -0.62 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.05 | 3.71 | -0.35 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.01 | 2.33 | +0.33 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.235 | 0.208 | -0.027 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.170 | 0.128 | -0.043 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.245 | 0.197 | -0.049 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.300 | 0.279 | -0.021 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.394 | 0.493 | +0.099 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.82 | 2.96 | +0.14 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.71 | 4.74 | +0.03 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.64 | 4.65 | +0.00 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.31 | 5.33 | +0.02 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.43 | 2.58 | +0.14 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 4.49 | +0.02 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.36 | 4.35 | -0.01 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.18 | 5.20 | +0.02 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.68 | 1.80 | +0.12 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.68 | 3.68 | +0.00 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.69 | 3.65 | -0.04 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.69 | 4.70 | +0.01 | 4.56 |
