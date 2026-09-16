# Stratospheric circulation diagnostics: T63L47, 2005-2009

## QBO and SAO (equatorial zonal wind, 5S-5N)

| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |
|---|---|---|---|
| model: T63L47 | 12.6 / 13.0 / 11.7 / 7.8 | 8.0 / 13.7 / 12.8 | -12 / -7 |
| ERA5 | 17.5 / 17.5 / 15.2 / 10.7 | 30.7 / 20.7 / 15.6 | -13 / -8 |
| WACCM6 histSST (free-running, same years) | 12.6 / 10.0 / 8.6 / 4.6 | 18.4 / 20.0 / 18.0 | -3 / -1 |

## Brewer-Dobson circulation (TEM residual streamfunction)

Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means (stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.

| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |
|---|---|---|---|---|---|
| model: T63L47 | DJF | 9.3 | 13.2 | 4.6 | 1.98 |
| model: T63L47 | JJA | 6.6 | 9.3 | 2.7 | 1.11 |
| model: T63L47 | annual | 7.6 | 10.6 | 3.4 | 1.38 |
| WACCM6 histSST | DJF | 8.6 | 13.9 | 4.5 | 2.51 |
| WACCM6 histSST | JJA | 5.4 | 9.5 | 3.2 | 2.05 |
| WACCM6 histSST | annual | 6.1 | 10.8 | 3.1 | 1.39 |

## Tropical ascent from age of air (10S-10N)

| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |
|---|---|---|---|
| model: T63L47 | 1.96 / 2.32 / 2.87 / 3.37 / 4.04 | 2.08 | 0.21 |
| CLaMS v3.1 / ERA5 (surface clock) | 0.75 / 1.66 / 2.62 / 3.08 / 3.68 | 2.94 | 0.15 |
| WACCM6 REF-D1 (entry age) | 0.54 / 1.17 / 1.99 / 2.45 / 3.01 | 2.47 | 0.17 |
