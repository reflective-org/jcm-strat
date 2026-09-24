# QBO nudging: before / after / ERA5, 1990-1999

| source | deseasonalised std 10 / 20 / 30 / 50 hPa [m/s] | mean u 20 / 30 hPa [m/s] | RMS vs ERA5, eq. monthly u 10-70 hPa [m/s] | RMS vs ERA5, 1-7 hPa [m/s] |
|---|---|---|---|---|
| nudged full physics (p12echam, 1990-1994) | 13.3 / 11.9 / 10.1 / 7.1 | -3.7 / -3.2 | 6.4 | 10.8 |
| free-running full physics (p14free, 1990-1999) | 0.2 / 0.1 / 0.2 / 0.3 | -0.8 / -0.4 | 16.3 | 19.9 |
| ERA5 (monthly, CDS) | 18.8 / 18.2 / 16.0 / 11.9 | -7.8 / -5.5 | 0.0 | 0.0 |

RMS change in time-mean zonal-mean u, after minus before: inside the window (|lat| <= 25, 1-90 hPa) 4.2 m/s; outside it in the stratosphere (|lat| > 30, 1-100 hPa) 2.5 m/s; troposphere (200-1000 hPa, all latitudes) 7.6 m/s.
