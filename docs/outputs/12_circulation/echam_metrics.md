# Phase 12 comparison: full ECHAM physics (T63L95) vs the dry Polvani-Kushner control (strat63), QBO on, 1990-1994

before `runs/p12ctl_5yr`, after `runs/p12echam_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 28.71 | +15.81 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 11.26 | +2.94 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 4.47 | +1.13 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 2.74 | +1.48 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 1.462 | +1.058 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | 0.602 | +0.271 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.201 | -0.062 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.281 | +0.194 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 0.871 | +0.739 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 43.08 | +29.12 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 19.91 | +9.46 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 7.12 | +2.68 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 4.09 | +2.25 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 1.826 | +1.466 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | 0.698 | +0.428 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | 0.218 | -0.020 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.402 | +0.243 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 0.945 | +0.539 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 35.36 | +21.90 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 13.09 | +4.65 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 6.07 | +2.54 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 4.53 | +2.97 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | 0.616 | +0.268 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | 0.542 | +0.207 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | 0.169 | -0.088 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.093 | +0.020 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 0.881 | +0.876 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 1.33 | -1.41 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 2.73 | -1.85 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 3.64 | -0.96 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 4.38 | -0.72 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 1.07 | -1.32 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 2.56 | -1.84 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 3.51 | -0.92 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 4.31 | -0.71 | 4.56 |
