# Phase 12 comparison: QBO nudging off (strat63, 1990-1994)

before `runs/p12ctl_5yr`, after `runs/p12noqbo_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 11.98 | -0.92 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 7.56 | -0.76 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 3.13 | -0.20 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 1.26 | +0.01 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 0.385 | -0.019 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | 0.250 | -0.082 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.162 | -0.102 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.057 | -0.031 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 0.181 | +0.048 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 13.81 | -0.16 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 10.15 | -0.29 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 4.18 | -0.25 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 1.74 | -0.09 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 0.371 | +0.011 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | 0.214 | -0.055 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | 0.143 | -0.095 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.112 | -0.046 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 0.338 | -0.067 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 12.98 | -0.47 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 7.83 | -0.61 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 3.28 | -0.26 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 1.50 | -0.06 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | 0.315 | -0.033 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | 0.249 | -0.086 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | 0.149 | -0.108 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.034 | -0.039 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 0.043 | +0.039 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 3.00 | +0.26 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 4.74 | +0.16 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 4.53 | -0.06 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 5.19 | +0.09 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 2.67 | +0.28 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 4.58 | +0.18 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 4.36 | -0.07 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 5.12 | +0.10 | 4.56 |
