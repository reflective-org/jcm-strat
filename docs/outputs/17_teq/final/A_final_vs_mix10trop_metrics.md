# Phase 12 comparison: Phase 17 A_final vs Phase 16 mix10trop, 1990-1999

before `/data/JCM_stripped/jcm-strat-phase16/runs/p16_mix10trop_10yr`, after `runs/p17_A_final_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.75 | 8.84 | -0.91 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 7.11 | 5.82 | -1.29 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.14 | 3.02 | -0.12 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.32 | 1.45 | +0.13 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.355 | 0.332 | -0.023 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.251 | 0.211 | -0.040 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.301 | 0.229 | -0.072 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.340 | 0.288 | -0.052 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.451 | 0.541 | +0.090 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.43 | 11.82 | -1.61 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 9.73 | 7.63 | -2.10 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.98 | 4.06 | -0.93 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.50 | 2.67 | +0.18 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.442 | 0.412 | -0.029 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.286 | 0.237 | -0.049 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.349 | 0.248 | -0.101 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.405 | 0.303 | -0.101 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.610 | 0.662 | +0.052 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 9.08 | 7.97 | -1.11 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 6.72 | 5.57 | -1.15 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.05 | 3.79 | -0.26 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.01 | 2.35 | +0.34 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.235 | 0.211 | -0.024 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.170 | 0.131 | -0.039 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.245 | 0.192 | -0.053 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.300 | 0.282 | -0.018 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.394 | 0.502 | +0.108 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.82 | 3.11 | +0.29 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.71 | 4.87 | +0.15 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.64 | 4.81 | +0.17 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.31 | 5.41 | +0.10 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.43 | 2.72 | +0.29 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 4.61 | +0.15 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.36 | 4.51 | +0.15 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.18 | 5.28 | +0.10 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.68 | 1.90 | +0.22 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.68 | 3.76 | +0.08 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.69 | 3.77 | +0.09 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.69 | 4.77 | +0.07 | 4.56 |
