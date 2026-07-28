# Metric System for Digital Twin Wind Application

evidence_type: newly_run + preexisting_artifact

## 1. Pedestrian Wind-Speed Metrics

Core variable:

`VR = U_ped / U_ref`

Current experiment setting:

- `U_ref = 5 m/s`
- local pedestrian layer: `z ~= 2 m`
- additional low-altitude layers: `4, 10, 20, 40 m`
- primary reported result: time-mean of 3 samples per wind direction, then 8-direction aggregation

| Metric | Definition | Current Output |
|---|---|---|
| `VR_mean` | mean of open-cell `VR` | CSV + map |
| `VR_P75/P90/P95` | percentile statistics over open cells | CSV |
| `VR_max` | maximum open-cell `VR` | CSV |
| Stagnation ratio | `A(VR < 0.2) / A_open` | CSV + interpretation |
| Accelerated-flow ratio | `A(VR > 0.6) / A_open` | CSV |
| High-speed ratio | `A(VR > 1.0) / A_open` | CSV |

Current strongest result:

- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_equal_weighted_vr_z2m.png`

## 2. Wind-Direction Aggregation

Two aggregation modes are reported:

| Aggregation | Formula | Evidence Boundary |
|---|---|---|
| Equal-weighted 8 directions | `VR_eq = mean(VR_wd000 ... VR_wd315)` | solver/method comparison |
| Open-Meteo 2024 proxy weighted | `VR_w = sum(p_i * VR_i)` | climate-proxy sensitivity, not site-measured comfort probability |

Wind-climate proxy:

- source: Open-Meteo Historical Weather API
- location: TUM City Campus proxy coordinate `(48.148, 11.568)`
- period: 2024-01-01 to 2024-12-31
- variables: hourly `wind_speed_10m`, `wind_direction_10m`
- convention: meteorological from-direction converted to velocity-to direction by adding 180 degrees, then assigned to nearest 45-degree simulated sector

Artifacts:

- `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`
- `figures/open_meteo_tum_city_campus_2024_windrose_8dir_velocity_to.png`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`
- `figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv`

## 3. Comfort and Safety Framework

Lawson, NEN 8100, and AIJ-style assessment requires threshold wind speeds and exceedance probabilities. The present experiment does not yet claim formal comfort/safety classes because:

- no measured site wind rose is available;
- Open-Meteo is only a reanalysis-based proxy;
- no activity-specific threshold/exceedance standard has been fixed;
- no field or wind-tunnel validation is available.

Current output should therefore be written as:

- preliminary pedestrian-height VR screening;
- stagnation and ventilation-insufficiency mapping;
- workflow demonstration from digital twin data to FluidX3D simulation;
- not final comfort/safety certification.

## 4. Digital Twin Geometry-to-CFD Metrics

### 4.1 Geometry-to-CFD Readiness Index, GCRI

Recommended formula:

`GCRI = 0.20 W + 0.15 M + 0.15 S + 0.15 C + 0.15 E + 0.20 V`

| Sub-metric | Meaning | Score |
|---|---|---|
| `W` watertightness | boundary edges, holes, closedness | 0-1 |
| `M` manifoldness | non-manifold edges, duplicate/degenerate faces | 0-1 |
| `S` semantic completeness | building/ground/road/vegetation/visual/collision layers | 0-1 |
| `C` coordinate/unit consistency | z0, bbox, units, offsets | 0-1 |
| `E` export success | STL/3DM/VTK/ParaView state generated | 0-1 |
| `V` voxelization success | FluidX3D solid mask matches expected geometry | 0-1 |

Current evidence and computed scores are now recorded in `manifests/gcri_scoring_table.csv` and `reports/geometry_to_cfd_readiness_index_results.md`.

| Geometry | Current GCRI | Status |
|---|---:|---|
| User photogrammetry STL | `0.455` | visual reference / counterexample, not final collision |
| Core semantic prism STL | `0.925` | preferred local CFD-ready collision geometry |
| District prism STL | `0.918` | preferred whole-district screening geometry |
| LoD3 direct OBJ collision candidate | `0.528` | semantic reference requiring repair before collision use |

### 4.2 3DGS/Photogrammetry-to-Collision Transfer Error

If a 3DGS or photogrammetry-derived collision boundary is later extracted, compare it against semantic LoD2/LoD3 collision geometry using:

- 2D footprint IoU;
- Chamfer distance;
- Hausdorff distance;
- roof-height error;
- wall/roof boundary error;
- solid voxel mask agreement.

This metric directly supports the paper argument that visual reconstruction must be semantically converted or repaired before becoming a robust CFD collision boundary.

Current status: the metric is defined but not computed because this archive does not include an independent 3DGS-derived building collision extraction. The available photogrammetry STL is treated as a qualitative counterexample only. See `manifests/gcbte_status_table.csv`.

## 5. Pollutant and Ventilation Risk Metrics

Pollutant dispersion has not been run yet. The following are templates only:

| Metric | Definition | Current Status |
|---|---|---|
| Dimensionless concentration | `C* = C / C0` | blocked |
| Hotspot area ratio | `A(C* > C_thr*) / A_open` | blocked |
| Pedestrian path exposure | `integral_path C*(s) ds` | blocked |
| Stagnation-pollution coupled risk | `I(VR < 0.2) * C*` | blocked |
| Ventilation potential proxy | `mean(VR)_open` or flux proxy | newly_run for velocity only |

## 6. Scenario Comparison Metrics

For baseline `S0` and interventions `S1...Sn`:

- comfort-area improvement: `Delta A_comfort = A_comfort(Si) - A_comfort(S0)`
- unsafe-area reduction: `Delta A_unsafe = A_unsafe(S0) - A_unsafe(Si)`
- stagnation change: `Delta A_stag = A_stag(Si) - A_stag(S0)`
- pollution hotspot reduction: `Delta A_hotspot = A_hotspot(S0) - A_hotspot(Si)`
- Wind Benefit per Modeling Cost: `Delta A_comfort / modeling_hours`
- Digital Twin Scenario Turnaround Time: `t_case_ready - t_download_start`

`S1` ventilation relief has now been simulated numerically as a design-sensitivity scenario. The comparison is reported in `reports/s1_ventilation_relief_fluidx3d_comparison_report.md` and `figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv`. The current S1 result is near-null/negative and should be used to discuss intervention insufficiency, not design optimization success. Additional `S2...Sn` alternatives remain future work.

## 7. Evidence Boundary

| Claim | evidence_type |
|---|---|
| TUM2TWIN source download and geometry audit | newly_run + preexisting_artifact |
| User photogrammetry package audit | user_claim + newly_run |
| FluidX3D whole-district and local core simulations | newly_run |
| Local dx=2 m time-sampled VR/stagnation metrics | newly_run |
| Open-Meteo 2024 wind-climate proxy weighting | newly_run + preexisting_artifact |
| Formal comfort/safety probability classification | blocked |
| Pollutant dispersion | blocked |
| Measured validation | blocked |
