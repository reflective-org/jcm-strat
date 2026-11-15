| metric | reference | AL7h |
|---|---|---|
| **A1** entry age 55 hPa tropics [yr] | 1.11 | ✅ 1.02 |
| **A2** 2-D age RMSE vs CLaMS [yr] | 0 | ❌ 0.68 |
| **A3** age step tropics -> 50-70 deg, 55 hPa [yr] | 2.82 | ⚠️ 2.18 |
| **A4** transit 70 -> 10 hPa [yr] | 2.3-3.2 | ⚠️ 2.13 |
| **B1-100** w* 100 hPa [mm/s] | 0.40 (ERA5 0.44) | ❌ 0.14 |
| **B1-70** w* 70 hPa [mm/s] | 0.21 (ERA5 0.25) | ✅ 0.21 |
| **B1-50** w* 50 hPa [mm/s] | 0.20 (ERA5 0.27) | ⚠️ 0.29 |
| **B1-30** w* 30 hPa [mm/s] | 0.26 (ERA5 0.32) | ✅ 0.32 |
| **B1-10** w* 10 hPa [mm/s] | 0.47 (ERA5 0.37) | ✅ 0.43 |
| **B2-100** mass flux 100 hPa [1e9 kg/s] | 10.9 (ERA5 12.3) | ✅ 9.44 |
| **B2-70** mass flux 70 hPa [1e9 kg/s] | 6.05 (ERA5 6.0) | ✅ 6.76 |
| **C1-jet50_N** jet NH 50 hPa [m/s] | 18.2 | ✅ 16.8 |
| **C1-jet50_N-lat** jet NH 50 hPa latitude [deg] | 58.8 | ✅ 58.8 |
| **C1-jet10_N** jet NH 10 hPa [m/s] | 29.0 | ✅ 24.0 |
| **C1-jet10_N-lat** jet NH 10 hPa latitude [deg] | 62.5 | ✅ 62.5 |
| **C1-jet50_S** jet SH 50 hPa [m/s] | 48.2 | ✅ 44.6 |
| **C1-jet50_S-lat** jet SH 50 hPa latitude [deg] | -56.9 | ✅ -56.9 |
| **C1-jet10_S** jet SH 10 hPa [m/s] | 75.1 | ❌ 66.3 |
| **C1-jet10_S-lat** jet SH 10 hPa latitude [deg] | -56.9 | ✅ -56.9 |
| **C2-N** polar-cap T bias 50 hPa N [K] | 0 | ✅ -1.03 |
| **C2-S** polar-cap T bias 50 hPa S [K] | 0 | ✅ 1.42 |

| | AL7h |
|---|---|
| A age of air, mean err | 1.17 |
| B residual circulation, mean err | 1.03 |
| C polar vortex, mean err | 0.50 |
| **combined score** | **0.90** |
| passed (✅) / total | 15 / 21 |

Group D, variability and relations (ERA5 / CLaMS for the same days; not in the combined score):

| metric | reference | AL7h |
|---|---|---|
| **D1-N** year-to-year std of winter u 55-65N 10 hPa [m/s] | 10.5 | ❌ 4.52 |
| **D1-S** year-to-year std of winter u 55-65S 10 hPa [m/s] | 2.62 | ❌ 1.41 |
| **D2-N** daily std of winter u 60N 10 hPa [m/s] | 16.5 | ⚠️ 11.9 |
| **D2-S** daily std of winter u 60S 10 hPa [m/s] | 5.63 | ⚠️ 3.83 |
| **D3** NH major SSWs in the window [number] | 4.00 | ❌ 6.00 |
| **D4-fwN** final warming N, days after 1 Mar | 38.7 | ✅ 45.8 |
| **D4-fwS** final warming S, days after 1 Sep | 75.2 | ✅ 77.7 |
| **D4-w** annual-cycle amplitude of tropical w* 70 hPa [mm/s] | 0.19 | ✅ 0.16 |
| **D5-N** daily std of 100 hPa heat flux N [K m/s] | 11.8 | ✅ 11.7 |
| **D5-S** daily std of 100 hPa heat flux S [K m/s] | 7.04 | ✅ 7.13 |
| **D6-N** heat flux -> polar-cap T slope N [K per K m/s] | 1.05 | ❌ 0.65 |
| **D6-S** heat flux -> polar-cap T slope S [K per K m/s] | 1.23 | ❌ 0.69 |
| **D7** age vs w* slope [yr per mm/s] | -3.98 | ❌ -1.04 |
| **D variability, mean err** | | **1.27** |
| passed (✅) / total | | 5 / 13 |
