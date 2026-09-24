# Phase 12 comparison: Hines + Lott-Miller drag added to the dry model (strat63, 1990-1994)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12ctl_5yr`, after `runs/p13gwd_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.90 | 23.75 | +10.85 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 11.38 | +3.06 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.34 | 3.74 | +0.40 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 1.44 | +0.18 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 1.046 | +0.642 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.331 | 0.464 | +0.133 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.332 | +0.068 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.087 | 0.188 | +0.101 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.132 | 0.022 | -0.110 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.97 | 36.11 | +22.14 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.44 | 16.68 | +6.24 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.44 | 5.24 | +0.81 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.84 | 2.07 | +0.23 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.360 | 1.289 | +0.929 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.270 | 0.473 | +0.203 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.238 | 0.319 | +0.081 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.159 | 0.266 | +0.107 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.406 | 0.134 | -0.272 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.46 | 24.29 | +10.83 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.44 | 11.62 | +3.18 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.54 | 4.14 | +0.60 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.56 | 1.53 | -0.03 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.348 | 0.766 | +0.418 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.335 | 0.474 | +0.138 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.257 | 0.358 | +0.102 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.216 | +0.143 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.005 | 0.088 | +0.083 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.74 | 1.35 | -1.39 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 2.71 | -1.86 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.60 | 3.80 | -0.80 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 4.40 | -0.70 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 2.39 | 1.26 | -1.14 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 4.40 | 2.64 | -1.76 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 4.43 | 3.74 | -0.69 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 5.02 | 4.36 | -0.66 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.29 | 1.10 | -0.20 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 3.60 | 2.47 | -1.13 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.77 | 3.55 | -0.22 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.54 | 4.14 | -0.40 | 4.56 |
