# Stratospheric circulation diagnostics: LQBO10d, 2006-2010

## QBO and SAO (equatorial zonal wind, 5S-5N)

| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |
|---|---|---|---|
| model: LQBO10d | 16.9 / 17.4 / 15.0 / 10.4 | 26.1 / 19.2 / 12.7 | -9 / -5 |
| ERA5 | 17.1 / 18.3 / 15.7 / 11.3 | 32.4 / 21.2 / 14.6 | -10 / -6 |
| WACCM6 histSST (free-running, same years) | 12.4 / 9.4 / 8.5 / 4.9 | 18.3 / 19.7 / 17.3 | -4 / -2 |

## Brewer-Dobson circulation (TEM residual streamfunction)

Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means (stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.

| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |
|---|---|---|---|---|---|
| model: LQBO10d | DJF | 9.6 | 13.0 | 4.7 | 2.36 |
| model: LQBO10d | JJA | 5.9 | 8.4 | 3.3 | 2.02 |
| model: LQBO10d | annual | 6.9 | 9.7 | 3.5 | 1.67 |
| WACCM6 histSST | DJF | 8.6 | 13.9 | 4.5 | 2.46 |
| WACCM6 histSST | JJA | 5.3 | 9.3 | 3.2 | 2.03 |
| WACCM6 histSST | annual | 6.0 | 10.7 | 3.0 | 1.36 |

## Tropical ascent from age of air (10S-10N; model clock aoa_sfc)

| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |
|---|---|---|---|
| model: LQBO10d | 1.71 / 2.10 / 2.54 / 2.89 / 3.42 | 1.70 | 0.25 |
| CLaMS v3.1 / ERA5 (surface clock) | 0.74 / 1.61 / 2.56 / 3.04 / 3.69 | 2.95 | 0.15 |
| WACCM6 REF-D1 (entry age) | 0.54 / 1.16 / 2.00 / 2.47 / 3.04 | 2.50 | 0.17 |
