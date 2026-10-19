# Phase 12 comparison: Jucker + GWD: nudging cutoff 150 -> 400 hPa (and 5 -> 10 yr)

before `runs/p13juckergwd_5yr`, after `runs/p13jgn400_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 21.55 | 6.67 | -14.87 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 9.04 | 4.10 | -4.94 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.31 | 1.51 | -0.80 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 0.65 | 0.75 | +0.09 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.988 | 0.062 | -0.926 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.308 | 0.054 | -0.254 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.166 | 0.021 | -0.144 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.063 | -0.069 | -0.132 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.248 | 0.359 | +0.111 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 41.66 | 10.32 | -31.35 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.88 | 8.15 | -11.74 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 6.11 | 5.32 | -0.79 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.20 | 1.09 | -0.11 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.314 | 0.067 | -1.247 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.374 | 0.053 | -0.321 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.182 | 0.074 | -0.107 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.149 | 0.023 | -0.126 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.218 | 0.363 | +0.145 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 25.32 | 8.02 | -17.31 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.58 | 5.64 | -5.94 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.96 | 4.22 | -0.74 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.30 | 1.27 | -0.02 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.559 | 0.021 | -0.538 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.239 | 0.026 | -0.213 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.095 | -0.064 | -0.159 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | -0.031 | -0.148 | -0.118 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.388 | 0.449 | +0.062 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.60 | 4.29 | +2.70 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.50 | 4.98 | +2.49 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.03 | 5.89 | +1.85 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.46 | 5.81 | +1.35 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.28 | 3.96 | +2.68 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.22 | 4.72 | +2.50 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.85 | 5.72 | +1.87 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.32 | 5.70 | +1.38 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.12 | 2.91 | +1.79 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.06 | 3.65 | +1.60 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.65 | 5.02 | +1.38 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.10 | 5.13 | +1.03 | 4.56 |
