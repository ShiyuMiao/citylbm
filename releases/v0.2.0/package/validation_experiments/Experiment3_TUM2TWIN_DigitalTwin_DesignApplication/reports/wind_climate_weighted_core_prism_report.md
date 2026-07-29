# Wind-Climate Weighted Core Prism Report

evidence_type: newly_run + preexisting_artifact

Open-Meteo Historical Weather API hourly wind speed/direction data for 2024 was used as a wind-climate proxy for the TUM City Campus location (`48.148, 11.568`). The API documentation states that historical weather data are based on reanalysis datasets and include hourly wind speed/direction variables.

Direction convention: Open-Meteo wind direction is treated as meteorological from-direction. It was converted to a velocity-to direction by adding 180 degrees, then assigned to the nearest 45-degree FluidX3D simulated velocity-direction sector. This assumes no additional local model rotation; therefore the weighted result is a climate-proxy sensitivity layer, not a final measured exceedance-probability comfort assessment.

- Raw data: `D:\citylbm_tum2twin_heavy_store\raw\wind_climate_open_meteo\open_meteo_tum_city_campus_2024_hourly_wind_10m.json`
- Weights CSV: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`
- Wind rose figure: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\open_meteo_tum_city_campus_2024_windrose_8dir_velocity_to.png`
- Weighted VR figure: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`
- Weighted metrics CSV: `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv`

## 2024 Direction Weights

| Velocity-to sector (deg) | Hours | Weight | Mean wind speed 10m (m/s) |
|---:|---:|---:|---:|
| 0 | 980 | 0.112 | 1.89 |
| 45 | 2008 | 0.229 | 2.89 |
| 90 | 2281 | 0.260 | 3.98 |
| 135 | 625 | 0.071 | 2.40 |
| 180 | 356 | 0.041 | 1.58 |
| 225 | 855 | 0.097 | 2.03 |
| 270 | 1029 | 0.117 | 2.44 |
| 315 | 650 | 0.074 | 2.04 |

## Weighted Metrics

| Height (m) | VR mean | VR P95 | Stagnation VR<0.2 |
|---:|---:|---:|---:|
| 2 | 0.077 | 0.246 | 0.931 |
| 4 | 0.188 | 0.616 | 0.656 |
| 10 | 0.406 | 0.936 | 0.323 |
| 20 | 0.603 | 1.025 | 0.253 |
| 40 | 1.051 | 1.167 | 0.000 |
