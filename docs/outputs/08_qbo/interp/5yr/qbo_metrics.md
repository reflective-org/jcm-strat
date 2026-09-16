# QBO nudging: before / after / ERA5, 2005-2009

| source | deseasonalised std 10 / 20 / 30 / 50 hPa [m/s] | mean u 20 / 30 hPa [m/s] | RMS vs ERA5, eq. monthly u 10-70 hPa [m/s] | RMS vs ERA5, 1-7 hPa [m/s] |
|---|---|---|---|---|
| tau 1 d, linear target (p8e_5yr) | 15.7 / 16.1 / 14.2 / 9.3 | -12.6 / -7.8 | 2.3 | 7.7 |
| tau 1 d, mean-preserving target (p8f_5yr) | 15.9 / 16.2 / 14.3 / 9.4 | -12.6 / -7.8 | 2.2 | 7.1 |
| ERA5 (monthly, CDS) | 17.5 / 17.5 / 15.2 / 10.7 | -12.9 / -8.0 | 0.0 | 0.0 |

RMS change in time-mean zonal-mean u, after minus before: inside the window (|lat| <= 25, 1-90 hPa) 0.1 m/s; outside it in the stratosphere (|lat| > 30, 1-100 hPa) 0.3 m/s; troposphere (200-1000 hPa, all latitudes) 0.0 m/s.
