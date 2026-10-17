# Phase 22 leaderboard (window 2005-04-01..2008-01-01, vs ERA5 same months)

u_ls_ext = RMSE of monthly zonal-mean u, 100-10 hPa, |lat| >= 30 (the ranking metric); jets = winter jet maximum over 30-90 deg [m/s @ lat] model (ERA5); cap T50 = polar-cap (60-90) T bias at 50 hPa in winter; w_logerr = mean |log(w*/w*_ERA5)| tropics 70-30 hPa (ERA5 1996-2001); age150 at 55 hPa (clocks carried from P20b, 3 years of the new circulation).

| run | u_ls_ext | u50_ext | u_up_ext | T_ls | jet50 N | jet50 S | jet10 N | jet10 S | cap T50 N / S | w_logerr | age150 trop / 50-70N / 50-70S | description |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B0 | 6.89 | 5.11 | 11.18 | 5.17 | 16@53 (17@59) | 45@-57 (47@-57) | 18@61 (26@62) | 63@-59 (76@-57) | -2.4 / +0.6 | 0.091 | 1.01 / 3.31 / 3.28 | as A + polar-cap relaxation time <= 10 d poleward of 60 deg (blend from 50), iteration 0 |
| P20b_base | 7.80 | 6.03 | 11.19 | 5.22 | 15@51 (17@59) | 39@-59 (47@-57) | 19@55 (26@62) | 58@-59 (76@-57) | -2.9 / +2.8 | 0.075 | 1.1 / 3.65 / 3.57 | P20b (p20bt) itself, no correction: Jucker JFV T_e, fixed Lott-Miller, bottom levels nudged |
