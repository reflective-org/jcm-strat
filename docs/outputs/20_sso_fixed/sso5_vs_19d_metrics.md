# Phase 12 comparison: 13d physics, L95 cubic, n400, new jcm, 1990-1994: without (19d) -> with the fixed Lott-Miller (20)

before `runs/p19jhn400_5yr`, after `runs/p20jhsso_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 8.79 | 9.27 | +0.48 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.20 | 6.51 | +0.31 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.87 | 3.01 | +0.15 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.23 | 1.30 | +0.07 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.117 | 0.127 | +0.010 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.191 | 0.200 | +0.009 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.273 | 0.278 | +0.006 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.320 | 0.325 | +0.005 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.411 | 0.420 | +0.008 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 11.18 | 12.08 | +0.90 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.27 | 8.87 | +0.60 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.71 | 4.79 | +0.08 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.38 | 2.35 | -0.03 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.170 | 0.188 | +0.018 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.246 | 0.263 | +0.017 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.344 | 0.355 | +0.011 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.426 | 0.432 | +0.006 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.637 | 0.631 | -0.007 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 7.38 | 7.80 | +0.43 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 5.41 | 5.74 | +0.32 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.70 | 3.92 | +0.22 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.81 | 1.96 | +0.15 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.074 | 0.084 | +0.010 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.148 | 0.159 | +0.012 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.231 | 0.244 | +0.013 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.288 | 0.307 | +0.020 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.391 | 0.429 | +0.037 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.28 | 2.25 | -0.03 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.16 | 4.11 | -0.05 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.82 | 3.69 | -0.13 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.68 | 4.61 | -0.08 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.79 | 1.75 | -0.04 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 3.87 | 3.80 | -0.07 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.45 | 3.30 | -0.15 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.47 | 4.38 | -0.09 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.14 | 1.11 | -0.03 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.38 | 3.30 | -0.08 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 2.90 | 2.74 | -0.16 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 3.97 | -0.10 | 4.56 |
