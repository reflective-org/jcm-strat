# Phase 12 comparison: drag + native L95 vs the dry control (1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12ctl_5yr`, after `runs/p13gwdl95_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 23.96 | +11.06 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 11.65 | +3.33 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 3.73 | +0.39 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 1.55 | +0.29 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 1.059 | +0.655 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | 0.488 | +0.157 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.298 | +0.035 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.112 | +0.025 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 0.079 | -0.053 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 36.21 | +22.24 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 17.08 | +6.64 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 5.11 | +0.68 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 2.16 | +0.32 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 1.276 | +0.916 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | 0.478 | +0.208 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | 0.275 | +0.037 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.170 | +0.011 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 0.201 | -0.205 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 24.08 | +10.62 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 11.56 | +3.12 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 4.12 | +0.59 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 1.72 | +0.16 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | 0.792 | +0.444 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | 0.491 | +0.156 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | 0.307 | +0.051 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.139 | +0.066 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 0.134 | +0.129 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 1.50 | -1.24 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 2.80 | -1.78 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 3.77 | -0.82 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 4.40 | -0.70 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 1.17 | -1.22 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 2.53 | -1.87 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 3.56 | -0.87 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 4.25 | -0.77 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.29 | 1.04 | -0.25 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.60 | 2.38 | -1.21 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.77 | 3.39 | -0.38 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.54 | 4.05 | -0.49 | 4.56 |
