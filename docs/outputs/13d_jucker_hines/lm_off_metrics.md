# Phase 12 comparison: Lott-Miller off: Jucker + Hines + LM -> Jucker + Hines (strat81, nudged < 150 hPa, 1990-1994)

before `runs/p13juckergwd_5yr`, after `runs/p13jh_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 21.55 | 11.68 | -9.86 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 9.04 | 7.46 | -1.58 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.31 | 3.01 | +0.70 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 0.65 | 1.41 | +0.76 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.988 | 0.331 | -0.657 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.308 | 0.186 | -0.122 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.166 | 0.126 | -0.040 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.063 | 0.043 | -0.020 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.248 | 0.490 | +0.243 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 41.66 | 14.49 | -27.18 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.88 | 10.50 | -9.38 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 6.11 | 4.16 | -1.95 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.20 | 2.77 | +1.57 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.314 | 0.293 | -1.021 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.374 | 0.116 | -0.258 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.182 | 0.091 | -0.091 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.149 | 0.068 | -0.081 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.218 | 0.789 | +0.571 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 25.32 | 13.28 | -12.05 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.58 | 8.31 | -3.27 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.96 | 4.76 | -0.20 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.30 | 2.04 | +0.74 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.559 | 0.266 | -0.293 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.239 | 0.198 | -0.041 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.095 | 0.127 | +0.032 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | -0.031 | 0.083 | +0.113 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.388 | 0.348 | -0.040 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.60 | 3.13 | +1.53 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.50 | 4.67 | +2.17 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.03 | 4.59 | +0.56 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.46 | 5.11 | +0.65 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.28 | 2.38 | +1.10 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.22 | 4.28 | +2.06 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.85 | 4.17 | +0.32 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.32 | 4.92 | +0.60 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.12 | 1.41 | +0.29 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.06 | 3.47 | +1.42 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.65 | 3.45 | -0.19 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.10 | 4.44 | +0.34 | 4.56 |
