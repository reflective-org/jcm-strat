# Phase 12 comparison: Phase 12 control vs Phase 11 A (same dynamics)

before `/data/JCM_stripped/jcm-strat-phase11/runs/p11a_5yr`, after `runs/p12ctl_5yr`; TEM covariances from every 4th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 12.89 | 12.90 | +0.01 | - |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 8.32 | 8.32 | +0.00 | - |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.32 | 3.34 | +0.02 | - |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 1.26 | 1.26 | -0.01 | - |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.404 | 0.404 | -0.001 | - |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.332 | 0.331 | -0.001 | - |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.264 | 0.264 | -0.000 | - |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.088 | 0.087 | -0.001 | - |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.137 | 0.132 | -0.005 | - |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 14.07 | 13.97 | -0.10 | - |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 10.52 | 10.44 | -0.08 | - |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.48 | 4.44 | -0.04 | - |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 1.85 | 1.84 | -0.01 | - |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.364 | 0.360 | -0.004 | - |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.274 | 0.270 | -0.005 | - |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.244 | 0.238 | -0.005 | - |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.164 | 0.159 | -0.005 | - |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.399 | 0.406 | +0.006 | - |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 13.41 | 13.46 | +0.05 | - |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 8.40 | 8.44 | +0.04 | - |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 3.53 | 3.54 | +0.00 | - |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 1.55 | 1.56 | +0.01 | - |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.345 | 0.348 | +0.003 | - |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.332 | 0.335 | +0.003 | - |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.253 | 0.257 | +0.003 | - |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.073 | 0.073 | +0.000 | - |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.004 | 0.005 | +0.001 | - |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 2.73 | 2.74 | +0.00 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 4.58 | 4.58 | +0.00 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 4.58 | 4.60 | +0.01 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 5.10 | 5.10 | +0.01 | 4.56 |
| aoa | 55 hPa | tropics 10S-10N | 2.60 | 2.61 | +0.01 | 1.33 |
| aoa | 55 hPa | 50-70 deg | 4.51 | 4.51 | +0.00 | 4.12 |
| aoa | 12 hPa | tropics 10S-10N | 4.52 | 4.53 | +0.01 | 3.68 |
| aoa | 12 hPa | 50-70 deg | 5.07 | 5.07 | +0.01 | 4.56 |
