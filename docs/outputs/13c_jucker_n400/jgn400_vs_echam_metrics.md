# Phase 12 comparison: JCM full physics vs dry Jucker + GWD, nudged < 400 hPa

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p13jgn400_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 28.71 | 6.67 | -22.04 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 11.26 | 4.10 | -7.16 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 4.47 | 1.51 | -2.96 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.74 | 0.75 | -1.99 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.462 | 0.062 | -1.400 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.602 | 0.054 | -0.549 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.201 | 0.021 | -0.180 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.281 | -0.069 | -0.350 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.871 | 0.359 | -0.512 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.08 | 10.32 | -32.76 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 19.91 | 8.15 | -11.76 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 7.12 | 5.32 | -1.79 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 4.09 | 1.09 | -3.00 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.826 | 0.067 | -1.759 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.698 | 0.053 | -0.645 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.218 | 0.074 | -0.144 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.402 | 0.023 | -0.379 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.945 | 0.363 | -0.582 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.36 | 8.02 | -27.34 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 13.09 | 5.64 | -7.45 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 6.07 | 4.22 | -1.85 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 4.53 | 1.27 | -3.25 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.616 | 0.021 | -0.595 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.542 | 0.026 | -0.516 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.169 | -0.064 | -0.233 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.093 | -0.148 | -0.241 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.881 | 0.449 | -0.431 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 4.29 | +2.96 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 4.98 | +2.26 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 5.89 | +2.25 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 5.81 | +1.43 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 3.96 | +2.89 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 4.72 | +2.16 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 5.72 | +2.20 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 5.70 | +1.38 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 2.91 | +1.95 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 3.65 | +1.25 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 5.02 | +1.69 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 5.13 | +1.04 | 4.56 |
