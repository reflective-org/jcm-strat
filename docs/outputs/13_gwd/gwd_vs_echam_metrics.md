# Phase 12 comparison: dry + GWD against JCM full physics (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13gwd_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 23.75 | -4.96 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 11.38 | +0.12 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 3.74 | -0.73 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 1.44 | -1.30 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | 1.046 | -0.416 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | 0.464 | -0.138 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | 0.332 | +0.131 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | 0.188 | -0.093 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 0.022 | -0.848 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 36.11 | -6.98 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 16.68 | -3.23 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 5.24 | -1.87 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 2.07 | -2.02 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 1.289 | -0.537 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | 0.473 | -0.225 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | 0.319 | +0.101 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.266 | -0.136 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 0.134 | -0.811 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 24.29 | -11.07 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 11.62 | -1.48 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.14 | -1.93 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 1.53 | -2.99 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | 0.766 | +0.150 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | 0.474 | -0.068 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | 0.358 | +0.190 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | 0.216 | +0.123 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 0.088 | -0.793 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 1.35 | +0.02 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.71 | -0.01 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 3.80 | +0.16 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 4.40 | +0.02 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 1.26 | +0.18 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.64 | +0.08 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 3.74 | +0.23 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 4.36 | +0.05 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 1.10 | +0.13 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.47 | +0.06 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 3.55 | +0.22 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 4.14 | +0.06 | 4.56 |
