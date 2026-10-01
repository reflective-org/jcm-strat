# Phase 12 comparison: same L95 grid: JCM full physics vs dry + GWD (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13gwdl95_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 23.96 | -4.75 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 11.65 | +0.39 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 3.73 | -0.74 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 1.55 | -1.19 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | 1.059 | -0.403 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | 0.488 | -0.114 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | 0.298 | +0.097 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.112 | -0.169 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 0.079 | -0.792 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 36.21 | -6.88 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 17.08 | -2.82 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 5.11 | -2.00 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 2.16 | -1.93 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 1.276 | -0.550 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | 0.478 | -0.220 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | 0.275 | +0.057 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.170 | -0.232 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 0.201 | -0.744 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 24.08 | -11.29 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 11.56 | -1.53 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.12 | -1.95 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 1.72 | -2.80 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | 0.792 | +0.176 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | 0.491 | -0.051 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | 0.307 | +0.138 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | 0.139 | +0.046 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 0.134 | -0.747 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 1.50 | +0.17 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.80 | +0.07 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 3.77 | +0.14 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 4.40 | +0.02 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 1.17 | +0.10 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.53 | -0.03 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 3.56 | +0.05 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.25 | -0.06 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.04 | +0.08 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.38 | -0.02 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.39 | +0.06 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.05 | -0.03 | 4.56 |
