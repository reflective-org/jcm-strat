# Phase 22 leaderboard (window 2005-04-01..2008-01-01, vs ERA5 same months)

u_ls_ext = RMSE of monthly zonal-mean u, 100-10 hPa, |lat| >= 30 (the ranking metric); jets = winter jet maximum over 30-90 deg [m/s @ lat] model (ERA5); cap T50 = polar-cap (60-90) T bias at 50 hPa in winter; w_logerr = mean |log(w*/w*_ERA5)| tropics 70-30 hPa (ERA5 1996-2001); age150 at 55 hPa (clocks carried from P20b, 3 years of the new circulation).

| run | u_ls_ext | u50_ext | u_up_ext | T_ls | jet50 N | jet50 S | jet10 N | jet10 S | cap T50 N / S | w_logerr | age150 trop / 50-70N / 50-70S | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C2 | 5.18 | 4.18 | 9.19 | 1.73 | 15@53 (17@59) | 43@-59 (47@-57) | 18@62 (26@62) | 67@-59 (76@-57) | +0.8 / +1.6 | 0.438 | 1.22 / 3.52 / 3.12 | Chang 2006 / Mooring & Linz iteration (zonal mean): pointwise, all latitudes, 400-1 hPa, alpha 2/3, no smoothing, iteration 2 |
| B50 | 6.19 | 4.84 | 10.15 | 5.36 | 23@57 (17@59) | 48@-55 (47@-57) | 33@62 (26@62) | 71@-59 (76@-57) | -8.1 / -2.5 | 0.113 | 0.94 / 3.11 / 3.02 | as A + polar-cap relaxation time <= 5 d poleward of 60 deg (blend from 50), iteration 0 |
| C1 | 6.26 | 5.23 | 9.45 | 2.53 | 14@55 (17@59) | 41@-59 (47@-57) | 19@64 (26@62) | 63@-59 (76@-57) | -0.7 / +1.9 | 0.271 | 1.18 / 3.71 / 3.64 | Chang 2006 / Mooring & Linz iteration (zonal mean): pointwise, all latitudes, 400-1 hPa, alpha 2/3, no smoothing, iteration 1 |
| B0 | 6.89 | 5.11 | 11.18 | 5.17 | 16@53 (17@59) | 45@-57 (47@-57) | 18@61 (26@62) | 63@-59 (76@-57) | -2.4 / +0.6 | 0.091 | 1.01 / 3.31 / 3.28 | as A + polar-cap relaxation time <= 10 d poleward of 60 deg (blend from 50), iteration 0 |
| A2 | 7.04 | 5.76 | 10.47 | 4.50 | 12@51 (17@59) | 41@-59 (47@-57) | 16@57 (26@62) | 66@-61 (76@-57) | -0.1 / +0.8 | 0.113 | 1.13 / 3.78 / 3.56 | Phase 17 correction on P20b, extratropics only (zero at |lat|<=25, full >=35), 100-1 hPa, smoothed, alpha 0.7, iteration 2 |
| A1 | 7.08 | 5.66 | 9.90 | 4.66 | 12@51 (17@59) | 40@-59 (47@-57) | 17@59 (26@62) | 63@-59 (76@-57) | -0.5 / +1.5 | 0.093 | 1.11 / 3.71 / 3.53 | Phase 17 correction on P20b, extratropics only (zero at |lat|<=25, full >=35), 100-1 hPa, smoothed, alpha 0.7, iteration 1 |
| P20b_base | 7.80 | 6.03 | 11.19 | 5.22 | 15@51 (17@59) | 39@-59 (47@-57) | 19@55 (26@62) | 58@-59 (76@-57) | -2.9 / +2.8 | 0.075 | 1.1 / 3.65 / 3.57 | P20b (p20bt) itself, no correction: Jucker JFV T_e, fixed Lott-Miller, bottom levels nudged |
