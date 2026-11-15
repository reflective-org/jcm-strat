# Mesosphere check (p20): annual-mean TEM w* above 10 hPa, mm/s, upward positive

Every 1th 6-hourly frame of each run directory; bands cos-weighted; `aoa150` latitude std over the last 240 frames (|lat| <= 88). Cells: tropics / NH cap / SH cap.

| run | 10 hPa | 5 hPa | 2 hPa | 1 hPa | 0.5 hPa | 0.3 hPa | `aoa150` lat std at 3 / 1.5 hPa [yr] |
|---|---|---|---|---|---|---|---|
| 20 fixed LM 1994 (`p20jhsso_19940101`) | +0.34 / -0.84 / -0.92 | +0.61 / -1.04 / -1.23 | +0.74 / -1.66 / -2.17 | +0.59 / -2.33 / -3.14 | +1.87 / -2.95 / -4.45 | +1.92 / -3.34 / -5.51 | 0.26 / 0.21 |
| 19d no SSO 1994 (`p19jhn400_19940101`) | +0.32 / -0.61 / -0.85 | +0.58 / -0.80 / -1.10 | +0.68 / -1.21 / -1.92 | +0.46 / -1.79 / -2.83 | +1.48 / -2.32 / -4.37 | +1.71 / -2.90 / -5.71 | 0.25 / 0.17 |
| full ECHAM (old jcm) 1994 (`p12echam_19940101`) | +0.73 / -1.49 / -1.15 | +0.90 / -1.82 / -1.20 | +0.52 / -0.92 / -1.66 | +0.91 / -1.75 / -2.83 | +1.78 / -3.36 / -4.85 | +2.64 / -4.96 / -6.59 | 0.18 / 0.14 |
