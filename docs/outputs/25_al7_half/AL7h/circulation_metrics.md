# Stratospheric circulation diagnostics: AL7h, 2006-2007

## QBO and SAO (equatorial zonal wind, 5S-5N)

| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |
|---|---|---|---|
| model: AL7h | 16.4 / 16.3 / 15.3 / 10.7 | 20.8 / 20.6 / 13.2 | -9 / -9 |
| ERA5 | 16.8 / 17.1 / 16.0 / 11.1 | 37.0 / 22.5 / 14.9 | -10 / -8 |
| WACCM6 histSST (free-running, same years) | 9.8 / 10.1 / 7.6 / 3.5 | 18.4 / 19.4 / 17.1 | -3 / -2 |

## Brewer-Dobson circulation (TEM residual streamfunction)

Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means (stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.

| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |
|---|---|---|---|---|---|
| model: AL7h | DJF | 9.3 | 12.7 | 4.8 | 2.16 |
| model: AL7h | JJA | 5.6 | 7.5 | 3.6 | 2.12 |
| model: AL7h | annual | 6.9 | 9.6 | 3.5 | 1.52 |
| WACCM6 histSST | DJF | 8.6 | 14.0 | 4.5 | 2.51 |
| WACCM6 histSST | JJA | 5.3 | 9.4 | 3.0 | 1.98 |
| WACCM6 histSST | annual | 6.0 | 10.7 | 3.0 | 1.37 |

## Tropical ascent from age of air (10S-10N; model clock aoa_sfc)

| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |
|---|---|---|---|
| model: AL7h | 1.90 / 2.38 / 2.99 / 3.46 / 4.28 | 2.38 | 0.18 |
| CLaMS v3.1 / ERA5 (surface clock) | 0.73 / 1.56 / 2.58 / 3.06 / 3.74 | 3.01 | 0.14 |
| WACCM6 REF-D1 (entry age) | 0.53 / 1.13 / 1.97 / 2.46 / 3.05 | 2.51 | 0.17 |
