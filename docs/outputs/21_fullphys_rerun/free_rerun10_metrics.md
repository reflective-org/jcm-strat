# Phase 12 comparison: Full ECHAM free-running 1990-1999: old jcm (broken LM, 10-level sponge) -> new jcm (fixed LM, ECHAM sponge)

before `/data/JCM_stripped/jcm-strat-phase14/runs/p14free_10yr`, after `runs/p21free_10yr`; TEM covariances from every 1th 6-hourly frame;
age = last 240 frames; WACCM6 histSST 1996-2014; CLaMS v3.1/ERA5 2005-2009.

## Residual circulation

| quantity | season | before | after | after - before | WACCM6 |
|---|---|---|---|---|---|
| upward mass flux 100 hPa [1e9 kg/s] | annual | 11.55 | 10.93 | -0.62 | 10.85 |
| upward mass flux 70 hPa [1e9 kg/s] | annual | 5.06 | 7.44 | +2.38 | 6.05 |
| upward mass flux 30 hPa [1e9 kg/s] | annual | 2.82 | 3.23 | +0.41 | 3.05 |
| upward mass flux 10 hPa [1e9 kg/s] | annual | 2.47 | 1.53 | -0.95 | 1.37 |
| tropical w* 15S-15N 100 hPa [mm/s] | annual | 0.168 | 0.367 | +0.200 | 0.398 |
| tropical w* 15S-15N 70 hPa [mm/s] | annual | 0.101 | 0.238 | +0.138 | 0.211 |
| tropical w* 15S-15N 50 hPa [mm/s] | annual | 0.009 | 0.222 | +0.213 | 0.201 |
| tropical w* 15S-15N 30 hPa [mm/s] | annual | 0.178 | 0.284 | +0.105 | 0.255 |
| tropical w* 15S-15N 10 hPa [mm/s] | annual | 0.873 | 0.541 | -0.331 | 0.469 |
| upward mass flux 100 hPa [1e9 kg/s] | DJF | 14.05 | 13.33 | -0.72 | 14.05 |
| upward mass flux 70 hPa [1e9 kg/s] | DJF | 8.18 | 9.37 | +1.19 | 8.53 |
| upward mass flux 30 hPa [1e9 kg/s] | DJF | 4.79 | 4.59 | -0.20 | 4.44 |
| upward mass flux 10 hPa [1e9 kg/s] | DJF | 3.96 | 2.72 | -1.23 | 2.42 |
| tropical w* 15S-15N 100 hPa [mm/s] | DJF | 0.444 | 0.400 | -0.043 | 0.446 |
| tropical w* 15S-15N 70 hPa [mm/s] | DJF | -0.052 | 0.254 | +0.306 | 0.251 |
| tropical w* 15S-15N 50 hPa [mm/s] | DJF | -0.021 | 0.249 | +0.270 | 0.234 |
| tropical w* 15S-15N 30 hPa [mm/s] | DJF | 0.175 | 0.371 | +0.196 | 0.295 |
| tropical w* 15S-15N 10 hPa [mm/s] | DJF | 0.952 | 0.812 | -0.140 | 0.644 |
| upward mass flux 100 hPa [1e9 kg/s] | JJA | 33.34 | 9.58 | -23.76 | 9.44 |
| upward mass flux 70 hPa [1e9 kg/s] | JJA | 10.90 | 6.55 | -4.35 | 5.33 |
| upward mass flux 30 hPa [1e9 kg/s] | JJA | 4.15 | 3.23 | -0.92 | 3.11 |
| upward mass flux 10 hPa [1e9 kg/s] | JJA | 3.49 | 2.16 | -1.33 | 2.00 |
| tropical w* 15S-15N 100 hPa [mm/s] | JJA | -0.239 | 0.246 | +0.485 | 0.276 |
| tropical w* 15S-15N 70 hPa [mm/s] | JJA | 0.271 | 0.193 | -0.077 | 0.125 |
| tropical w* 15S-15N 50 hPa [mm/s] | JJA | 0.040 | 0.202 | +0.163 | 0.135 |
| tropical w* 15S-15N 30 hPa [mm/s] | JJA | 0.149 | 0.243 | +0.094 | 0.201 |
| tropical w* 15S-15N 10 hPa [mm/s] | JJA | 0.743 | 0.470 | -0.273 | 0.452 |

## Age of air (years; zonal mean of the last frames)

| clock | level | region | before | after | after - before | CLaMS (surface clock) |
|---|---|---|---|---|---|---|
| aoa_sfc | 55 hPa | tropics 10S-10N | 1.81 | 1.45 | -0.36 | 1.33 |
| aoa_sfc | 55 hPa | 50-70 deg | 2.41 | 3.83 | +1.42 | 4.12 |
| aoa_sfc | 12 hPa | tropics 10S-10N | 3.63 | 3.31 | -0.32 | 3.68 |
| aoa_sfc | 12 hPa | 50-70 deg | 4.54 | 4.73 | +0.20 | 4.56 |
| aoa500 | 55 hPa | tropics 10S-10N | 1.57 | 0.95 | -0.62 | 1.33 |
| aoa500 | 55 hPa | 50-70 deg | 2.22 | 3.41 | +1.19 | 4.12 |
| aoa500 | 12 hPa | tropics 10S-10N | 3.47 | 2.83 | -0.63 | 3.68 |
| aoa500 | 12 hPa | 50-70 deg | 4.44 | 4.42 | -0.03 | 4.56 |
| aoa150 | 55 hPa | tropics 10S-10N | 1.45 | 0.74 | -0.71 | 1.33 |
| aoa150 | 55 hPa | 50-70 deg | 2.08 | 3.17 | +1.09 | 4.12 |
| aoa150 | 12 hPa | tropics 10S-10N | 3.31 | 2.60 | -0.70 | 3.68 |
| aoa150 | 12 hPa | 50-70 deg | 4.22 | 4.16 | -0.06 | 4.56 |
