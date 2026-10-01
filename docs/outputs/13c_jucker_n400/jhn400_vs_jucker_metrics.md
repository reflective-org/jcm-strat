# Phase 12 comparison: Jucker no drag (5 yr, < 150 hPa) -> Jucker + Hines only, nudged < 400 hPa (10 yr)

before `runs/p13jucker_5yr`, after `runs/p13jhn400_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 10.57 | 9.16 | -1.42 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.74 | 6.33 | -0.41 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.76 | 2.52 | -0.24 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.29 | 1.51 | +0.22 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.293 | 0.104 | -0.189 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.172 | 0.107 | -0.065 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.127 | 0.097 | -0.030 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.033 | 0.013 | -0.020 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.413 | 0.579 | +0.165 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.60 | 12.22 | -1.39 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.06 | 9.34 | -0.72 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.20 | 3.86 | -0.34 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.74 | 2.74 | +0.01 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.266 | 0.142 | -0.124 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.116 | 0.128 | +0.012 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.109 | 0.139 | +0.030 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.075 | 0.082 | +0.007 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.726 | 0.856 | +0.130 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 12.33 | 8.30 | -4.03 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 7.73 | 5.60 | -2.13 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.57 | 4.28 | -0.29 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.63 | 2.30 | +0.66 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.234 | 0.053 | -0.181 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.183 | 0.091 | -0.091 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.116 | 0.069 | -0.047 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.054 | 0.037 | -0.018 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.237 | 0.502 | +0.265 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 3.34 | 4.56 | +1.22 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.83 | 5.72 | +0.89 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.79 | 5.83 | +1.04 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.21 | 5.75 | +0.54 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.61 | 3.77 | +1.16 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.46 | 5.30 | +0.83 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.40 | 5.35 | +0.95 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.05 | 5.57 | +0.51 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.56 | 2.26 | +0.69 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.62 | 3.96 | +0.34 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.67 | 4.21 | +0.54 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.57 | 4.90 | +0.33 | 4.56 |
