# Stratospheric circulation diagnostics: AL7, 2006-2010

## QBO and SAO (equatorial zonal wind, 5S-5N)

| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |
|---|---|---|---|
| model: AL7 | 16.4 / 17.6 / 15.4 / 10.6 | 15.0 / 18.9 / 13.2 | -9 / -5 |
| ERA5 | 17.1 / 18.3 / 15.7 / 11.3 | 32.4 / 21.2 / 14.6 | -10 / -6 |
| WACCM6 histSST (free-running, same years) | 12.4 / 9.4 / 8.5 / 4.9 | 18.3 / 19.7 / 17.3 | -4 / -2 |

## Brewer-Dobson circulation (TEM residual streamfunction)

Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means (stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.

| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |
|---|---|---|---|---|---|
| model: AL7 | DJF | 9.1 | 12.1 | 5.2 | 2.33 |
| model: AL7 | JJA | 5.6 | 7.5 | 3.4 | 2.04 |
| model: AL7 | annual | 7.2 | 9.7 | 3.9 | 1.83 |
| WACCM6 histSST | DJF | 8.6 | 13.9 | 4.5 | 2.46 |
| WACCM6 histSST | JJA | 5.3 | 9.3 | 3.2 | 2.03 |
| WACCM6 histSST | annual | 6.0 | 10.7 | 3.0 | 1.36 |

## Tropical ascent from age of air (10S-10N; model clock aoa_sfc)

| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |
|---|---|---|---|
| model: AL7 | 1.89 / 2.20 / 2.86 / 3.20 / 4.03 | 2.13 | 0.20 |
| CLaMS v3.1 / ERA5 (surface clock) | 0.74 / 1.61 / 2.56 / 3.04 / 3.69 | 2.95 | 0.15 |
| WACCM6 REF-D1 (entry age) | 0.54 / 1.16 / 2.00 / 2.47 / 3.04 | 2.50 | 0.17 |
