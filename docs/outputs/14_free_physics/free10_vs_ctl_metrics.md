# Phase 12 comparison: free-running full physics 1990-1999 (T63L95) vs the dry Polvani-Kushner control 1990-1994 (strat63)

before `runs/p12ctl_5yr`, after `runs/p14free_10yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 12.56 | -0.34 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 7.53 | -0.80 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 2.07 | -1.27 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 3.10 | +1.85 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | -0.054 | -0.457 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | -0.218 | -0.550 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | -0.276 | -0.540 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.009 | -0.078 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 1.324 | +1.191 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 11.84 | -2.12 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 9.52 | -0.93 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 5.38 | +0.94 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 4.26 | +2.42 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 0.214 | -0.146 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | -0.303 | -0.573 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | -0.126 | -0.364 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.308 | +0.149 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 1.355 | +0.949 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 36.13 | +22.67 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 15.93 | +7.49 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 4.53 | +0.99 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 5.01 | +3.44 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | -0.488 | -0.836 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | -0.086 | -0.421 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | -0.368 | -0.625 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | -0.279 | -0.352 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 1.294 | +1.289 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 1.81 | -0.93 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 2.41 | -2.16 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 3.63 | -0.96 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 4.54 | -0.57 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 1.57 | -0.82 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 2.22 | -2.18 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 3.47 | -0.97 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 4.44 | -0.58 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.29 | 1.45 | +0.16 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.60 | 2.08 | -1.51 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.77 | 3.31 | -0.46 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.54 | 4.22 | -0.32 | 4.56 |
