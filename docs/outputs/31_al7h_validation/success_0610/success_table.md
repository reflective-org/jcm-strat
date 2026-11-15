| metric | reference | AL7h |
|---|---|---|
| **A1** entry age 55 hPa tropics [yr] | 1.10 | ✅ 1.00 |
| **A2** 2-D age RMSE vs CLaMS [yr] | 0 | ❌ 0.60 |
| **A3** age step tropics -> 50-70 deg, 55 hPa [yr] | 2.84 | ⚠️ 2.26 |
| **A4** transit 70 -> 10 hPa [yr] | 2.3-3.2 | ⚠️ 2.15 |
| **B1-100** w* 100 hPa [mm/s] | 0.40 (ERA5 0.44) | ❌ 0.14 |
| **B1-70** w* 70 hPa [mm/s] | 0.21 (ERA5 0.25) | ✅ 0.22 |
| **B1-50** w* 50 hPa [mm/s] | 0.20 (ERA5 0.27) | ⚠️ 0.29 |
| **B1-30** w* 30 hPa [mm/s] | 0.26 (ERA5 0.32) | ✅ 0.32 |
| **B1-10** w* 10 hPa [mm/s] | 0.47 (ERA5 0.37) | ✅ 0.40 |
| **B2-100** mass flux 100 hPa [1e9 kg/s] | 10.9 (ERA5 12.3) | ✅ 9.50 |
| **B2-70** mass flux 70 hPa [1e9 kg/s] | 6.05 (ERA5 6.0) | ✅ 6.80 |
| **C1-jet50_N** jet NH 50 hPa [m/s] | 16.4 | ✅ 14.3 |
| **C1-jet50_N-lat** jet NH 50 hPa latitude [deg] | 56.9 | ✅ 53.2 |
| **C1-jet10_N** jet NH 10 hPa [m/s] | 25.2 | ⚠️ 18.5 |
| **C1-jet10_N-lat** jet NH 10 hPa latitude [deg] | 62.5 | ✅ 60.6 |
| **C1-jet50_S** jet SH 50 hPa [m/s] | 46.7 | ✅ 43.6 |
| **C1-jet50_S-lat** jet SH 50 hPa latitude [deg] | -56.9 | ✅ -56.9 |
| **C1-jet10_S** jet SH 10 hPa [m/s] | 71.9 | ⚠️ 66.0 |
| **C1-jet10_S-lat** jet SH 10 hPa latitude [deg] | -56.9 | ✅ -58.8 |
| **C2-N** polar-cap T bias 50 hPa N [K] | 0 | ✅ -1.05 |
| **C2-S** polar-cap T bias 50 hPa S [K] | 0 | ✅ 1.27 |

| | AL7h |
|---|---|
| A age of air, mean err | 1.10 |
| B residual circulation, mean err | 1.05 |
| C polar vortex, mean err | 0.66 |
| **combined score** | **0.94** |
| passed (✅) / total | 14 / 21 |
