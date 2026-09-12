# P10 2005-2009 quick look (every 50 d): production-tracer metrics

frames: 7304 (every 6 h), day 1826.0; time series every 200 frames

## pulses

| tracer | amplitude | first-frame RMSE vs target / amp | burden after 1st injection | min over run | max over run | decay monotone between injections |
|---|---|---|---|---|---|---|
| pulse_1 | 1.0 | 0.004 | 9.416e-04 | -6.34e-10 | 0.941 | NO (5 injections seen) |
| pulse_2 | 0.5 | 0.014 | 6.273e-04 | -2.29e-10 | 0.433 | NO (16 injections seen) |
| pulse_3 | 0.2 | 0.015 | 7.356e-05 | -3.13e-10 | 0.188 | NO (1 injections seen) |
| pulse_4 | 0.1 | 0.008 | 1.104e-05 | -9.47e-11 | 0.095 | NO (0 injections seen) |
| pulse_5 | 0.05 | 0.004 | 2.521e-04 | -3.09e-11 | 0.044 | NO (18 injections seen) |

n2o: burden first/last 0.9620 / 0.9562; last-frame min/max 7.45e-06 / 1.0687

cfc11: burden first/last 0.9318 / 0.9219; last-frame min/max 1.67e-22 / 1.0715

clocks (last frame): aoa150 <= aoa in 100.0% of cells, aoa <= aoa_sfc in 99.7%; global means 0.91 / 0.27 / 1.05 yr (aoa / aoa150 / aoa_sfc)

omega (last frame): max |level-mean| / rms = 0.006; rms at 30 hPa 2.54e-03 Pa/s
