# Phase 12 comparison: Full ECHAM, nudged, QBO term, 1990-1994: old jcm (broken LM, 10-level sponge, nudged < 150 hPa) -> new jcm (fixed LM, ECHAM sponge, < 400 hPa)

before `/data/JCM_stripped/jcm-strat-phase12/runs/p12echam_5yr`, after `runs/p21echam_5yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 27.64 | 13.56 | -14.08 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 12.10 | 9.02 | -3.08 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 3.15 | 3.56 | +0.41 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.32 | 1.53 | -0.79 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 1.457 | 0.459 | -0.998 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.595 | 0.354 | -0.240 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.152 | 0.298 | +0.147 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.182 | 0.305 | +0.123 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.800 | 0.555 | -0.246 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 43.87 | 15.29 | -28.58 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 18.52 | 10.76 | -7.76 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.94 | 4.64 | -0.30 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.78 | 2.35 | -1.42 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 1.792 | 0.460 | -1.333 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | 0.650 | 0.361 | -0.289 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | 0.106 | 0.344 | +0.237 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.155 | 0.360 | +0.206 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.858 | 0.684 | -0.174 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 35.02 | 12.06 | -22.95 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 11.71 | 8.00 | -3.71 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.72 | 3.70 | -1.02 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.37 | 2.17 | -1.20 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | 0.586 | 0.327 | -0.259 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.573 | 0.265 | -0.307 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.253 | 0.236 | -0.017 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.242 | 0.275 | +0.033 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.655 | 0.563 | -0.092 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.33 | 0.96 | -0.37 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.73 | 2.98 | +0.26 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.64 | 2.29 | -1.35 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.38 | 3.75 | -0.63 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.07 | 0.59 | -0.48 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.56 | 2.69 | +0.13 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.51 | 1.94 | -1.57 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.31 | 3.51 | -0.80 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 0.96 | 0.44 | -0.52 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.41 | 2.55 | +0.14 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.33 | 1.81 | -1.53 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.08 | 3.35 | -0.73 | 4.56 |
