# Phase 12 comparison: Full ECHAM free-running, first 5 yr: old jcm -> new jcm

before `/data/JCM_stripped/jcm-strat-phase14/runs/p14free_5yr`, after `runs/p21free_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 11.32 | 10.96 | -0.36 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 4.99 | 7.48 | +2.49 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.77 | 3.27 | +0.51 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.44 | 1.54 | -0.90 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.173 | 0.371 | +0.198 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.105 | 0.241 | +0.136 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.003 | 0.223 | +0.220 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.172 | 0.285 | +0.113 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.857 | 0.538 | -0.319 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 13.99 | 13.30 | -0.70 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.13 | 9.28 | +1.15 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.71 | 4.58 | -0.13 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.92 | 2.68 | -1.24 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.448 | 0.408 | -0.040 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | -0.051 | 0.256 | +0.307 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | -0.030 | 0.250 | +0.280 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.163 | 0.371 | +0.208 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.929 | 0.791 | -0.137 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 32.85 | 9.78 | -23.07 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 10.65 | 6.71 | -3.94 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.09 | 3.33 | -0.76 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.44 | 2.20 | -1.24 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | -0.230 | 0.253 | +0.484 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.287 | 0.198 | -0.089 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.029 | 0.204 | +0.175 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.144 | 0.249 | +0.105 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.732 | 0.484 | -0.248 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.75 | 1.42 | -0.32 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.41 | 3.44 | +1.03 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.54 | 2.95 | -0.59 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.47 | 4.30 | -0.17 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.52 | 0.95 | -0.58 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.22 | 3.10 | +0.87 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.40 | 2.55 | -0.85 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.39 | 4.05 | -0.34 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.40 | 0.73 | -0.67 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.09 | 2.90 | +0.80 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.24 | 2.35 | -0.89 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.17 | 3.84 | -0.33 | 4.56 |
