# Phase 12 comparison: Phase 15 ray30+n100 vs JCM full physics (p12_echam), 1990-1994

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p15_ray30_n100_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 27.64 | 9.70 | -17.94 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 12.10 | 7.09 | -5.00 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.15 | 3.13 | -0.02 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.32 | 1.32 | -1.00 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.457 | 0.360 | -1.098 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.595 | 0.253 | -0.342 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.152 | 0.300 | +0.148 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.182 | 0.337 | +0.155 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.800 | 0.446 | -0.354 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.87 | 13.19 | -30.68 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 18.52 | 9.57 | -8.94 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.94 | 4.90 | -0.04 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.78 | 2.43 | -1.34 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.792 | 0.448 | -1.344 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.650 | 0.279 | -0.371 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.106 | 0.343 | +0.237 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.155 | 0.405 | +0.250 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.858 | 0.583 | -0.275 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.02 | 9.04 | -25.97 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.71 | 6.73 | -4.97 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.72 | 4.02 | -0.70 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.37 | 2.03 | -1.34 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.586 | 0.241 | -0.345 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.573 | 0.174 | -0.399 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.253 | 0.246 | -0.008 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.242 | 0.291 | +0.049 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.655 | 0.406 | -0.249 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 3.32 | +1.99 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 4.78 | +2.05 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 4.75 | +1.11 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 5.21 | +0.83 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 2.61 | +1.54 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 4.42 | +1.86 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 4.36 | +0.84 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 5.05 | +0.73 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.56 | +0.60 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 3.56 | +1.16 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.61 | +0.28 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.55 | +0.47 | 4.56 |
