# Phase 12 comparison: Jucker + Hines, nudged < 400 hPa, 1990-1994: OLD jcm 849893be strat81 -> NEW jcm 35dc1997 L95 cubic (stride 1)

before `runs/old_p13jhn400_5yr`, after `runs/p19jhn400_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.35 | 8.79 | -0.56 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.63 | 6.20 | -0.43 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.95 | 2.87 | -0.08 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.21 | 1.23 | +0.02 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.157 | 0.117 | -0.040 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.214 | 0.191 | -0.023 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.290 | 0.273 | -0.017 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.330 | 0.320 | -0.011 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.419 | 0.411 | -0.008 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 12.18 | 11.18 | -1.00 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.95 | 8.27 | -0.68 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.82 | 4.71 | -0.11 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.29 | 2.38 | +0.10 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.210 | 0.170 | -0.040 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.269 | 0.246 | -0.023 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.357 | 0.344 | -0.013 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.424 | 0.426 | +0.002 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.591 | 0.637 | +0.046 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 7.98 | 7.38 | -0.60 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 6.04 | 5.41 | -0.63 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.04 | 3.70 | -0.35 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 2.02 | 1.81 | -0.21 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.126 | 0.074 | -0.052 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.176 | 0.148 | -0.029 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.256 | 0.231 | -0.026 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.314 | 0.288 | -0.026 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.428 | 0.391 | -0.037 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.69 | 2.28 | -1.40 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 5.03 | 4.16 | -0.86 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 5.05 | 3.82 | -1.23 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.30 | 4.68 | -0.62 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 3.12 | 1.79 | -1.33 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.77 | 3.87 | -0.90 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.79 | 3.45 | -1.34 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.20 | 4.47 | -0.73 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.92 | 1.14 | -0.78 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.74 | 3.38 | -0.36 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 4.02 | 2.90 | -1.12 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.69 | 4.08 | -0.62 | 4.56 |
