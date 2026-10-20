# Phase 12 comparison: 1990-1994, new jcm, fixed LM, nudged < 400 hPa: dry 13d + LM (Phase 20) vs full ECHAM (21a)

before `runs/p20jhsso_5yr`, after `runs/p21echam_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.27 | 13.56 | +4.29 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.51 | 9.02 | +2.51 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.01 | 3.56 | +0.54 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.30 | 1.53 | +0.23 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.127 | 0.459 | +0.332 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.200 | 0.354 | +0.155 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.278 | 0.298 | +0.020 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.325 | 0.305 | -0.020 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.420 | 0.555 | +0.135 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 12.08 | 15.29 | +3.21 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.87 | 10.76 | +1.89 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.79 | 4.64 | -0.15 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.35 | 2.35 | +0.00 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.188 | 0.460 | +0.272 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.263 | 0.361 | +0.098 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.355 | 0.344 | -0.012 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.432 | 0.360 | -0.072 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.631 | 0.684 | +0.054 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 7.80 | 12.06 | +4.26 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 5.74 | 8.00 | +2.27 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.92 | 3.70 | -0.22 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.96 | 2.17 | +0.21 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.084 | 0.327 | +0.243 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.159 | 0.265 | +0.106 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.244 | 0.236 | -0.008 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.307 | 0.275 | -0.033 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.429 | 0.563 | +0.135 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.25 | 0.96 | -1.29 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.11 | 2.98 | -1.13 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.69 | 2.29 | -1.40 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.61 | 3.75 | -0.86 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.75 | 0.59 | -1.16 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 3.80 | 2.69 | -1.12 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.30 | 1.94 | -1.36 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.38 | 3.51 | -0.87 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.11 | 0.44 | -0.67 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.30 | 2.55 | -0.75 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 2.74 | 1.81 | -0.94 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 3.97 | 3.35 | -0.62 | 4.56 |
