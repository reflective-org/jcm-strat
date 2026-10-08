# Phase 12 comparison: 1990-1994, new jcm, fixed LM: dry 13d + LM nudged < 400 hPa (Phase 20) vs free-running full ECHAM (21b) [5 yr: Phase 20 stopped in 1997]

before `runs/p20jhsso_5yr`, after `runs/p21free_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 9.27 | 10.96 | +1.69 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 6.51 | 7.48 | +0.97 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.01 | 3.27 | +0.26 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.30 | 1.54 | +0.25 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.127 | 0.371 | +0.244 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.200 | 0.241 | +0.041 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.278 | 0.223 | -0.055 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.325 | 0.285 | -0.040 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.420 | 0.538 | +0.118 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 12.08 | 13.30 | +1.21 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.87 | 9.28 | +0.41 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.79 | 4.58 | -0.21 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 2.35 | 2.68 | +0.33 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.188 | 0.408 | +0.220 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.263 | 0.256 | -0.008 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.355 | 0.250 | -0.105 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.432 | 0.371 | -0.062 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.631 | 0.791 | +0.161 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 7.80 | 9.78 | +1.98 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 5.74 | 6.71 | +0.97 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.92 | 3.33 | -0.59 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.96 | 2.20 | +0.25 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.084 | 0.253 | +0.170 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.159 | 0.198 | +0.039 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.244 | 0.204 | -0.040 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.307 | 0.249 | -0.059 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.429 | 0.484 | +0.055 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.25 | 1.42 | -0.83 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.11 | 3.44 | -0.67 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.69 | 2.95 | -0.74 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.61 | 4.30 | -0.31 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.75 | 0.95 | -0.80 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 3.80 | 3.10 | -0.71 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.30 | 2.55 | -0.76 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.38 | 4.05 | -0.33 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.11 | 0.73 | -0.38 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.30 | 2.90 | -0.41 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 2.74 | 2.35 | -0.40 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 3.97 | 3.84 | -0.13 | 4.56 |
