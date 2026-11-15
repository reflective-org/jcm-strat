# Stratospheric circulation diagnostics: AL7h, 2011-2019

## QBO and SAO (equatorial zonal wind, 5S-5N)

| source | QBO: deseasonalised std at 10 / 20 / 30 / 50 hPa [m/s] | SAO: semiannual amplitude at 1 / 2 / 3 hPa [m/s] | mean u at 20 / 30 hPa [m/s] |
|---|---|---|---|
| model: AL7h | 16.9 / 18.8 / 16.8 / 9.8 | 14.4 / 19.8 / 16.1 | -8 / -5 |
| ERA5 | 17.7 / 19.5 / 17.3 / 10.3 | 27.6 / 23.2 / 18.8 | -7 / -5 |
| WACCM6 histSST (free-running, same years) | 11.1 / 9.5 / 8.0 / 3.8 | 18.7 / 19.8 / 16.0 | -5 / -5 |

## Brewer-Dobson circulation (TEM residual streamfunction)

Tropical upward mass flux = max - min of Psi* over |lat| <= 60 at the level, 10^9 kg/s. Model covariances from 5-day means (stationary + slow transient waves); WACCM6 from its daily zonal-mean TEM tape. WACCM6 1996-2014 at 70 hPa in the AIDE validation: 8.8-10.1.

| source | season | up-flux 70 hPa | up-flux 100 hPa | up-flux 30 hPa | up-flux 10 hPa |
|---|---|---|---|---|---|
| model: AL7h | DJF | 8.8 | 12.1 | 4.5 | 2.23 |
| model: AL7h | JJA | 5.2 | 7.2 | 3.4 | 1.97 |
| model: AL7h | annual | 6.8 | 9.4 | 3.4 | 1.49 |
| WACCM6 histSST | DJF | 8.3 | 14.1 | 4.3 | 2.41 |
| WACCM6 histSST | JJA | 5.5 | 9.8 | 3.2 | 2.13 |
| WACCM6 histSST | annual | 6.1 | 11.0 | 3.1 | 1.40 |

## Tropical ascent from age of air (10S-10N; model clock aoa_sfc)

| source | age at 70 / 50 / 30 / 20 / 10 hPa [yr] | transit 70 -> 10 hPa [yr] | mean ascent 70 -> 10 hPa [mm/s] |
|---|---|---|---|
| model: AL7h | 1.90 / 2.29 / 2.99 / 3.27 / 3.84 | 1.94 | 0.22 |
| CLaMS v3.1 / ERA5 (surface clock) | 0.80 / 1.74 / 2.74 / 3.21 / 3.74 | 2.94 | 0.15 |
| WACCM6 REF-D1 (entry age) | 0.54 / 1.16 / 1.97 / 2.44 / 3.02 | 2.48 | 0.17 |
