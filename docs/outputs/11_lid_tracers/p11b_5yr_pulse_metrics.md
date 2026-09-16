# P11b 1990-1994 (strat63, lid 1 hPa, lid sink): production-tracer metrics

frames: 7304 (every 6 h), day 1826.0; time series every 20 frames

## pulses

| tracer | shape | first-frame RMSE vs target | burden after 1st injection | min over run | max over run | burden between injections (no sink: constant; with a sink: may only fall) |
|---|---|---|---|---|---|---|
| pulse_1 | gaussian | 0.007 | 1.105e-03 | 0.00e+00 | 0.774 | largest rise within a cycle 9.8e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_1_box | box | 0.017 | 3.644e-04 | 0.00e+00 | 0.923 | largest rise within a cycle 5.4e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_2 | gaussian | 0.014 | 2.527e-03 | 0.00e+00 | 0.623 | largest rise within a cycle 1.6e-03 of the peak burden (1 injections scheduled to day 1826) |
| pulse_2_box | box | 0.032 | 8.932e-04 | 0.00e+00 | 0.739 | largest rise within a cycle 2.4e-03 of the peak burden (1 injections scheduled to day 1826) |
| pulse_3 | gaussian | 0.013 | 3.682e-04 | 0.00e+00 | 0.830 | largest rise within a cycle 3.7e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_3_box | box | 0.029 | 1.219e-04 | 0.00e+00 | 0.910 | largest rise within a cycle 5.5e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_4 | gaussian | 0.007 | 1.059e-04 | 0.00e+00 | 0.717 | largest rise within a cycle 2.5e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_4_box | box | 0.018 | 3.919e-05 | 0.00e+00 | 0.758 | largest rise within a cycle 2.4e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_5 | gaussian | 0.003 | 1.047e-02 | 0.00e+00 | 0.706 | largest rise within a cycle 2.9e-04 of the peak burden (1 injections scheduled to day 1826) |
| pulse_5_box | box | 0.007 | 3.949e-03 | 0.00e+00 | 0.715 | largest rise within a cycle 2.9e-04 of the peak burden (1 injections scheduled to day 1826) |

n2o: burden first/last 0.9667 / 0.8575; last-frame min/max 3.59e-04 / 1.0000

cfc11: burden first/last 0.9402 / 0.8089; last-frame min/max 8.73e-17 / 1.0000

src_1: burden last 1.495e-02, reaches half of it at day 910; still rising at the end: no; last-frame max 1.551e-01

src_1_box: burden last 5.091e-03, reaches half of it at day 910; still rising at the end: no; last-frame max 1.124e-01

src_2: burden last 7.242e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.499e-01

src_2_box: burden last 2.265e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 6.466e-02

src_3: burden last 3.626e-03, reaches half of it at day 915; still rising at the end: no; last-frame max 1.695e-01

src_3_box: burden last 1.341e-03, reaches half of it at day 915; still rising at the end: no; last-frame max 1.439e-01

src_4: burden last 4.131e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.841e-01

src_4_box: burden last 1.509e-02, reaches half of it at day 915; still rising at the end: no; last-frame max 1.277e-01

clocks (last frame): aoa150 <= aoa in 100.0% of cells, aoa <= aoa_sfc in 99.7%; global means 1.10 / 0.31 / 1.28 yr (aoa / aoa150 / aoa_sfc)

omega (last frame): max |level-mean| / rms = 0.015; rms at 30 hPa 2.68e-03 Pa/s
