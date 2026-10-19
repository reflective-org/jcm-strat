# Phase 12 comparison: Lott-Miller off: Hines + LM -> Hines only (Jucker, strat81, nudged < 400 hPa, 1990-1999)

before `runs/p13jgn400_10yr`, after `runs/p13jhn400_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 6.67 | 9.16 | +2.48 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 4.10 | 6.33 | +2.24 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 1.51 | 2.52 | +1.01 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 0.75 | 1.51 | +0.77 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.062 | 0.104 | +0.042 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.054 | 0.107 | +0.053 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.021 | 0.097 | +0.075 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | -0.069 | 0.013 | +0.082 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.359 | 0.579 | +0.220 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 10.32 | 12.22 | +1.90 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.15 | 9.34 | +1.19 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 5.32 | 3.86 | -1.46 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.09 | 2.74 | +1.65 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.067 | 0.142 | +0.075 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.053 | 0.128 | +0.075 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.074 | 0.139 | +0.065 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.023 | 0.082 | +0.059 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.363 | 0.856 | +0.493 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 8.02 | 8.30 | +0.28 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 5.64 | 5.60 | -0.04 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.22 | 4.28 | +0.06 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.27 | 2.30 | +1.02 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.021 | 0.053 | +0.033 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.026 | 0.091 | +0.065 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | -0.064 | 0.069 | +0.133 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | -0.148 | 0.037 | +0.185 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.449 | 0.502 | +0.053 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 4.29 | 4.56 | +0.27 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.98 | 5.72 | +0.74 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 5.89 | 5.83 | -0.06 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.81 | 5.75 | -0.06 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 3.96 | 3.77 | -0.19 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.72 | 5.30 | +0.58 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 5.72 | 5.35 | -0.36 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.70 | 5.57 | -0.13 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 2.91 | 2.26 | -0.66 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.65 | 3.96 | +0.30 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 5.02 | 4.21 | -0.82 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 5.13 | 4.90 | -0.23 | 4.56 |
