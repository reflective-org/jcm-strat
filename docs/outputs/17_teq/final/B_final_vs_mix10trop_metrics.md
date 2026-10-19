# Phase 12 comparison: Phase 17 B_final vs Phase 16 mix10trop, 1990-1999

before `/data/JCM_stripped/jcm-strat-phase16/runs/p16_mix10trop_10yr`, after `runs/p17_B_final_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.75 | 8.79 | -0.95 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.11 | 5.66 | -1.46 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.14 | 2.79 | -0.35 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.32 | 1.34 | +0.02 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.355 | 0.331 | -0.024 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.251 | 0.210 | -0.041 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.301 | 0.228 | -0.073 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.340 | 0.287 | -0.053 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.451 | 0.521 | +0.070 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.43 | 11.84 | -1.60 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.73 | 7.52 | -2.20 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.98 | 3.83 | -1.15 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.50 | 2.35 | -0.14 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.442 | 0.414 | -0.028 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.286 | 0.240 | -0.046 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.349 | 0.253 | -0.096 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.405 | 0.314 | -0.091 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.610 | 0.666 | +0.057 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 9.08 | 7.64 | -1.43 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 6.72 | 5.15 | -1.57 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.05 | 3.29 | -0.76 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.01 | 1.93 | -0.08 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.235 | 0.206 | -0.029 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.170 | 0.125 | -0.045 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.245 | 0.183 | -0.063 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.300 | 0.270 | -0.030 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.394 | 0.466 | +0.072 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.82 | 3.14 | +0.32 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.71 | 4.90 | +0.19 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.64 | 4.83 | +0.19 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.31 | 5.41 | +0.10 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.43 | 2.75 | +0.32 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 4.67 | +0.21 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.36 | 4.55 | +0.19 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.18 | 5.31 | +0.13 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.68 | 1.93 | +0.26 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.68 | 3.83 | +0.15 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.69 | 3.84 | +0.15 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.69 | 4.83 | +0.14 | 4.56 |
