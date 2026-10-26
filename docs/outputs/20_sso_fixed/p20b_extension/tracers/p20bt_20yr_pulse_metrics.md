# P20b 1990-2009 (fixed Lott-Miller, bottom levels nudged): production-tracer metrics

frames: 29220 (every 6 h), day 7305.0; time series every 120 frames

## pulses

| tracer | shape | first-frame RMSE vs target | burden after 1st injection | min over run | max over run | burden between injections (no sink: constant; with a sink: may only fall) |
|---|---|---|---|---|---|---|
| pulse_1 | gaussian | 0.005 | 1.105e-03 | 0.00e+00 | 0.447 | largest rise within a cycle 4.7e-04 of the peak burden (1 injections scheduled to day 7305) |
| pulse_1_box | box | 0.013 | 3.643e-04 | 0.00e+00 | 0.375 | largest rise within a cycle 5.4e-04 of the peak burden (1 injections scheduled to day 7305) |
| pulse_2 | gaussian | 0.010 | 2.550e-03 | 0.00e+00 | 0.140 | largest rise within a cycle 1.5e-03 of the peak burden (1 injections scheduled to day 7305) |
| pulse_2_box | box | 0.024 | 8.928e-04 | 0.00e+00 | 0.100 | largest rise within a cycle 1.4e-03 of the peak burden (1 injections scheduled to day 7305) |
| pulse_3 | gaussian | 0.007 | 3.683e-04 | 0.00e+00 | 0.610 | largest rise within a cycle 1.2e-03 of the peak burden (1 injections scheduled to day 7305) |
| pulse_3_box | box | 0.019 | 1.219e-04 | 0.00e+00 | 0.488 | largest rise within a cycle 1.3e-03 of the peak burden (1 injections scheduled to day 7305) |
| pulse_4 | gaussian | 0.010 | 1.105e-04 | 0.00e+00 | 0.135 | largest rise within a cycle 5.5e-04 of the peak burden (1 injections scheduled to day 7305) |
| pulse_4_box | box | 0.018 | 4.016e-05 | 0.00e+00 | 0.055 | largest rise within a cycle 5.7e-04 of the peak burden (1 injections scheduled to day 7305) |
| pulse_5 | gaussian | 0.003 | 1.045e-02 | 0.00e+00 | 0.155 | largest rise within a cycle 2.7e-04 of the peak burden (1 injections scheduled to day 7305) |
| pulse_5_box | box | 0.011 | 3.786e-03 | 0.00e+00 | 0.096 | largest rise within a cycle 2.9e-04 of the peak burden (1 injections scheduled to day 7305) |

n2o: burden first/last 0.9682 / 0.9629; last-frame min/max 3.16e-04 / 1.0000

cfc11: burden first/last 0.9427 / 0.9252; last-frame min/max -2.33e-14 / 1.0000

src_1: burden last 6.035e-02, reaches half of it at day 3660; still rising at the end: no; last-frame max 3.194e-01

src_1_box: burden last 2.060e-02, reaches half of it at day 3660; still rising at the end: no; last-frame max 1.584e-01

src_2: burden last 2.914e-01, reaches half of it at day 3660; still rising at the end: no; last-frame max 5.750e-01

src_2_box: burden last 1.037e-01, reaches half of it at day 3660; still rising at the end: no; last-frame max 2.843e-01

src_3: burden last 1.510e-02, reaches half of it at day 3660; still rising at the end: no; last-frame max 2.800e-01

src_3_box: burden last 5.497e-03, reaches half of it at day 3660; still rising at the end: no; last-frame max 1.755e-01

src_4: burden last 1.661e-01, reaches half of it at day 3660; still rising at the end: no; last-frame max 6.574e-01

src_4_box: burden last 6.027e-02, reaches half of it at day 3660; still rising at the end: no; last-frame max 3.765e-01

clocks (last frame): aoa150 <= aoa in 100.0% of cells, aoa <= aoa_sfc in 95.6%; global means 0.66 / 0.29 / 1.20 yr (aoa / aoa150 / aoa_sfc)

omega (last frame): max |level-mean| / rms = 0.013; rms at 30 hPa 2.60e-03 Pa/s
