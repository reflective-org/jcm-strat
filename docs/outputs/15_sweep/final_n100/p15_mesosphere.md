# Mesosphere check (p15): annual-mean TEM w* above 10 hPa, mm/s, upward positive

Every 1th 6-hourly frame of each run directory; bands cos-weighted; `aoa150` latitude std over the last 240 frames (|lat| <= 88). Cells: tropics / NH cap / SH cap.

| run | 10 hPa | 5 hPa | 2 hPa | 1 hPa | 0.5 hPa | 0.3 hPa | `aoa150` lat std at 3 / 1.5 hPa [yr] |
|---|---|---|---|---|---|---|---|
| base Jucker (1994) (`p13jucker_19940101`) | +0.36 / -0.60 / -0.73 | +0.63 / -0.78 / -0.90 | +0.73 / -1.10 / -1.38 | +1.54 / -1.99 / -2.65 | +1.34 / -1.80 / -2.91 | +0.69 / -2.66 / -4.69 | 0.12 / 0.10 |
| n100 (1994) (`p15_n100_19940101`) | +0.34 / -0.53 / -0.72 | +0.58 / -0.62 / -0.87 | +0.65 / -0.92 / -1.33 | +1.39 / -1.68 / -2.59 | +1.04 / -1.68 / -2.84 | +0.68 / -2.54 / -4.60 | 0.11 / 0.10 |
| full ECHAM (1994) (`p12echam_19940101`) | +0.73 / -1.49 / -1.15 | +0.90 / -1.82 / -1.20 | +0.52 / -0.92 / -1.66 | +0.91 / -1.75 / -2.83 | +1.78 / -3.36 / -4.85 | +2.64 / -4.96 / -6.59 | 0.18 / 0.14 |
