# Resolution sweep: 2005-2009, age of air from the last 73 saves

| run | grid | columns | dt [min] | AoA RMSE vs CLaMS 100-5 hPa [yr] | AoA bias [yr] | age 55 hPa tropics / 50-70 / contrast [yr] | age 12 hPa tropics / 50-70 / contrast [yr] | transit 70->10 hPa [yr] | up-flux 70 hPa annual [1e9 kg/s] | T RMSE 100-1 hPa vs ERA5 [K] | u RMSE [m/s] | u(60N,10hPa) DJF / u(60S) JJA [m/s] | QBO RMS vs ERA5 10-70 hPa [m/s] | stepping [d/hr] | ms/step | chain wall [h] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T63L95 | T63 L95 (echam) | 18432 | 12 | 0.74 | 0.12 | 2.11 / 3.55 / 1.43 | 3.43 / 4.12 / 0.69 | 1.96 | 7.7 | 6.3 | 4.9 | 31 / 64 | 4.0 | 3890 | 8 | 1.3 |
| T63L63 | T63 L63 (strat) | 18432 | 12 | 0.74 | 0.11 | 2.11 / 3.54 / 1.44 | 3.41 / 4.11 / 0.69 | 1.95 | 7.7 | 6.1 | 4.6 | 31 / 64 | 4.0 | 5374 | 6 | 1.1 |
| T63L47 | T63 L47 (strat) | 18432 | 12 | 0.73 | 0.18 | 2.16 / 3.59 / 1.43 | 3.54 / 4.18 / 0.64 | 2.08 | 7.6 | 6.0 | 4.6 | 28 / 62 | 4.7 | 6228 | 5 | 1.0 |
| T85L95 | T85 L95 (echam) | 32768 | 9 | 0.75 | 0.11 | 2.13 / 3.53 / 1.40 | 3.43 / 4.10 / 0.67 | 1.93 | 7.6 | 6.2 | 4.7 | 32 / 67 | 4.0 | 1636 | 14 | 2.2 |
| T85L63 | T85 L63 (strat) | 32768 | 9 | 0.74 | 0.09 | 2.11 / 3.51 / 1.39 | 3.41 / 4.08 / 0.67 | 1.93 | 7.6 | 6.1 | 4.5 | 31 / 66 | 4.1 | 2356 | 10 | 1.7 |
| T85L47 | T85 L47 (strat) | 32768 | 9 | 0.74 | 0.16 | 2.16 / 3.56 / 1.40 | 3.53 / 4.15 / 0.62 | 2.05 | 7.5 | 6.0 | 4.5 | 28 / 64 | 4.8 | 3059 | 7 | 1.4 |
| CLaMS v3.1 / ERA5 | 1 deg, 39 levels | - | - | 0 | 0 | 1.33 / 4.12 / 2.79 | 3.68 / 4.56 / 0.88 | 2.94 | - | - | - | - | - | - | - | - |
| ERA5 / WACCM6 histSST | - | - | - | - | - | - | - | - | 6.1 (WACCM6) | 0 | 0 | 28 / 72 (ERA5) | 0 | - | - | - |

## Ranks (1 = closest to the reference; mean rank is unweighted)

| run | AoA RMSE | |age 55 hPa tropics - CLaMS| | |contrast 55 hPa - CLaMS| | |transit - CLaMS| | |up-flux 70 - WACCM6| | T RMSE vs ERA5 | u RMSE vs ERA5 | QBO RMS vs ERA5 | mean rank |
|---|---|---|---|---|---|---|---|---|---|
| T63L95 | 3 | 3 | 3 | 3 | 5 | 6 | 6 | 1 | 3.75 |
| T63L63 | 4 | 1 | 1 | 4 | 6 | 3 | 3 | 2 | 3.00 |
| T63L47 | 1 | 5 | 2 | 1 | 2 | 1 | 4 | 5 | 2.62 |
| T85L95 | 6 | 4 | 4 | 5 | 3 | 5 | 5 | 3 | 4.38 |
| T85L63 | 5 | 2 | 6 | 6 | 4 | 4 | 1 | 4 | 4.00 |
| T85L47 | 2 | 6 | 5 | 2 | 1 | 2 | 2 | 6 | 3.25 |

Ranks compare model runs only; the reference rows are the targets. Cost is reported, not ranked.
