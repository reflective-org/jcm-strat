# P10 1990-2019 (strat63, tau 1 d): production-tracer metrics

frames: 43828 (every 6 h), day 10957.0; time series every 120 frames

## pulses

| tracer | amplitude | first-frame RMSE vs target / amp | burden after 1st injection | min over run | max over run | burden between injections (should only fall) |
|---|---|---|---|---|---|---|
| pulse_1 | 1.0 | 0.007 | 1.027e-03 | -1.13e-13 | 0.135 | largest rise within a cycle 1.4e-35 of the peak burden (1 injections scheduled to day 10957) |
| pulse_2 | 0.5 | 0.014 | 9.181e-04 | -3.74e-13 | 0.026 | largest rise within a cycle 1.5e-35 of the peak burden (1 injections scheduled to day 10957) |
| pulse_3 | 0.2 | 0.013 | 7.366e-05 | -1.42e-14 | 0.092 | largest rise within a cycle 1.9e-34 of the peak burden (1 injections scheduled to day 10957) |
| pulse_4 | 0.1 | 0.007 | 1.104e-05 | -5.08e-16 | 0.008 | largest rise within a cycle 1.3e-33 of the peak burden (1 injections scheduled to day 10957) |
| pulse_5 | 0.05 | 0.004 | 3.530e-04 | -4.39e-13 | 0.003 | largest rise within a cycle 3.9e-35 of the peak burden (1 injections scheduled to day 10957) |

n2o: burden first/last 0.9567 / 0.8589; last-frame min/max 3.21e-06 / 1.0000

cfc11: burden first/last 0.9217 / 0.8129; last-frame min/max 1.58e-29 / 1.0000

src_1: burden last 1.505e-03, reaches half of it at day 120; still rising at the end: no; last-frame max 1.205e-01

src_2: burden last 1.637e-03, reaches half of it at day 90; still rising at the end: no; last-frame max 1.957e-02

src_3: burden last 6.875e-05, reaches half of it at day 90; still rising at the end: no; last-frame max 3.247e-02

src_4: burden last 6.839e-04, reaches half of it at day 60; still rising at the end: yes; last-frame max 3.152e-02

clocks (last frame): aoa150 <= aoa in 100.0% of cells, aoa <= aoa_sfc in 99.7%; global means 2.97 / 0.92 / 3.46 yr (aoa / aoa150 / aoa_sfc)

omega (last frame): max |level-mean| / rms = 0.018; rms at 30 hPa 2.65e-03 Pa/s
