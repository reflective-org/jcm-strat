# Phase 12 comparison: full L95 troposphere: strat63 -> strat81 (QBO on, 1990-1994)

before `runs/p12ctl_5yr`, after `runs/p12l81_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 11.81 | -1.09 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 7.72 | -0.60 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 3.25 | -0.09 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 1.34 | +0.08 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 0.353 | -0.051 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | 0.261 | -0.071 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.166 | -0.098 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.017 | -0.071 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 0.306 | +0.173 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 13.13 | -0.84 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 9.73 | -0.71 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 4.41 | -0.03 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 1.92 | +0.08 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 0.294 | -0.066 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | 0.176 | -0.093 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | 0.131 | -0.107 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.077 | -0.082 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 0.594 | +0.189 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 12.48 | -0.97 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 7.65 | -0.79 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 3.34 | -0.19 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 1.70 | +0.14 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | 0.324 | -0.024 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | 0.286 | -0.049 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | 0.156 | -0.101 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.015 | -0.058 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 0.167 | +0.162 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 3.07 | +0.33 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 4.77 | +0.19 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 4.77 | +0.18 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 5.18 | +0.08 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 2.29 | -0.10 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 4.39 | -0.01 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 4.42 | -0.02 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 5.01 | -0.01 | 4.56 |
