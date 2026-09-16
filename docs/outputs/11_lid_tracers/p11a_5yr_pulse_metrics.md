# P11a 1990-1994 (strat63, lid 1 hPa, no sink): production-tracer metrics

frames: 7304 (every 6 h), day 1826.0; time series every 20 frames

## pulses

| tracer | shape | first-frame RMSE vs target | burden after 1st injection | min over run | max over run | burden between injections (no sink: constant; with a sink: may only fall) |
|---|---|---|---|---|---|---|
| pulse_1 | gaussian | 0.007 | 1.105e-03 | 0.00e+00 | 0.774 | largest rise within a cycle 9.8e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_1_box | box | 0.017 | 3.644e-04 | 0.00e+00 | 0.923 | largest rise within a cycle 5.5e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_2 | gaussian | 0.014 | 2.527e-03 | 0.00e+00 | 0.623 | largest rise within a cycle 1.6e-03 of the peak burden (1 injections scheduled to day 1826) |
| pulse_2_box | box | 0.032 | 8.932e-04 | 0.00e+00 | 0.739 | largest rise within a cycle 2.4e-03 of the peak burden (1 injections scheduled to day 1826) |
| pulse_3 | gaussian | 0.013 | 3.684e-04 | 0.00e+00 | 0.830 | largest rise within a cycle 5.6e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_3_box | box | 0.029 | 1.219e-04 | 0.00e+00 | 0.910 | largest rise within a cycle 6.4e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_4 | gaussian | 0.007 | 1.105e-04 | 0.00e+00 | 0.728 | largest rise within a cycle 5.0e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_4_box | box | 0.018 | 4.017e-05 | 0.00e+00 | 0.763 | largest rise within a cycle 4.7e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_5 | gaussian | 0.003 | 1.047e-02 | 0.00e+00 | 0.706 | largest rise within a cycle 3.0e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_5_box | box | 0.007 | 3.949e-03 | 0.00e+00 | 0.714 | largest rise within a cycle 2.9e-04 of the peak burden (1 injections scheduled to day 1826) |

n2o: burden first/last 0.9667 / 0.8581; last-frame min/max 3.59e-04 / 1.0000

cfc11: burden first/last 0.9402 / 0.8093; last-frame min/max 1.54e-12 / 1.0000

src_1: burden last 1.511e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.514e-01

src_1_box: burden last 5.157e-03, reaches half of it at day 915; still rising at the end: no; last-frame max 1.170e-01

src_2: burden last 7.246e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.484e-01

src_2_box: burden last 2.266e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 6.362e-02

src_3: burden last 3.780e-03, reaches half of it at day 915; still rising at the end: no; last-frame max 1.674e-01

src_3_box: burden last 1.376e-03, reaches half of it at day 920; still rising at the end: no; last-frame max 1.405e-01

src_4: burden last 4.135e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.821e-01

src_4_box: burden last 1.510e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.285e-01

clocks (last frame): aoa150 <= aoa in 100.0% of cells, aoa <= aoa_sfc in 99.7%; global means 1.10 / 0.30 / 1.28 yr (aoa / aoa150 / aoa_sfc)

omega (last frame): max |level-mean| / rms = 0.015; rms at 30 hPa 2.68e-03 Pa/s
