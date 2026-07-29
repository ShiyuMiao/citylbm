# Deepened Wind-Environment Conclusions

evidence_type: newly_run + preexisting_artifact

## Purpose

This deepened analysis reuses the existing FluidX3D core-prism 8-direction, 3-sample velocity outputs. It does not rerun the solver. The goal is to move beyond mean/P95 reporting and test whether the pedestrian-layer low-speed conclusion is directionally robust.

## Command

```powershell
python .\scripts\deepen_core_prism_wind_analysis.py
```

Workdir:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究`

## Inputs

- FluidX3D velocity VTK files:
  `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_core_prism_avg_wd*_dx2m_spin6k_s3_u_sample_*u-*.vtk`
- FluidX3D flag VTK files:
  `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_core_prism_avg_wd*_dx2m_spin6k_s3_flags_sample_2flags-000012000.vtk`
- Wind-climate proxy weights:
  `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`

## Outputs

| Artifact | Role |
|---|---|
| `figures/fluidx3d_core_prism_deepened_directional_robustness_z2m.png` | z~2 m spatial maps of mean VR, direction standard deviation, range, stagnation frequency, Open-Meteo weighted stagnation probability, and best ventilation direction |
| `figures/fluidx3d_core_prism_deepened_direction_response_z2m.png` | z~2 m per-direction mean VR, stagnation ratio, and wind-climate proxy weight |
| `figures/fluidx3d_core_prism_deepened_vertical_profile.png` | vertical profiles of VR mean, VR P95, and VR<0.2 ratio |
| `figures/fluidx3d_core_prism_deepened_directional_summary.csv` | per-direction, per-height time-mean statistics |
| `figures/fluidx3d_core_prism_deepened_spatial_robustness_metrics.csv` | robust stagnation and direction-sensitivity metrics |

## Key Deepened Metrics

Pedestrian layer: z approximately `2 m`.

| Metric | Value | Interpretation |
|---|---:|---|
| Mean directional std(VR) | 0.0238 | Directional variability is low over most open pedestrian cells |
| P95 directional std(VR) | 0.0698 | Even high-variability areas remain moderate in directional spread |
| Mean directional range(VR) | 0.0710 | Typical best-worst wind-direction difference is small relative to the low mean VR |
| Robust stagnation area, frequency >= 0.75 | 0.9149 | About 91.5% of open z~2 m cells are stagnant under at least 6 of 8 directions |
| All-direction stagnation area | 0.8725 | About 87.2% of open z~2 m cells are stagnant under all 8 directions |
| Open-Meteo weighted mean stagnation probability | 0.9285 | The climate-proxy weighted stagnation probability remains very high |
| Area with Open-Meteo weighted stagnation probability >= 0.75 | 0.9030 | About 90.3% of open z~2 m cells remain robustly stagnant under weighted wind climate |
| Directionally accelerated area, frequency >= 0.25 | 0.0255 | Only about 2.5% of open cells are accelerated under at least 2 of 8 directions |

## Directional Response at z~2 m

| Velocity direction | Weight | Mean VR | VR P95 | VR<0.2 ratio | VR>0.6 ratio |
|---:|---:|---:|---:|---:|---:|
| 0 deg | 0.112 | 0.0768 | 0.2539 | 0.9401 | 0.0185 |
| 45 deg | 0.229 | 0.0792 | 0.2533 | 0.9227 | 0.0191 |
| 90 deg | 0.260 | 0.0751 | 0.2683 | 0.9312 | 0.0198 |
| 135 deg | 0.071 | 0.0737 | 0.2525 | 0.9227 | 0.0191 |
| 180 deg | 0.041 | 0.0732 | 0.2520 | 0.9400 | 0.0185 |
| 225 deg | 0.097 | 0.0774 | 0.2529 | 0.9227 | 0.0191 |
| 270 deg | 0.117 | 0.0775 | 0.2685 | 0.9305 | 0.0198 |
| 315 deg | 0.074 | 0.0778 | 0.2535 | 0.9234 | 0.0191 |

The largest z~2 m mean VR occurs for 45 deg, but the difference among directions is small. The lowest stagnation ratio occurs for 135 deg, while 0 deg and 180 deg produce the highest stagnation ratios. These differences do not overturn the primary conclusion that pedestrian-layer stagnation is widespread.

## Deepened Conclusions

### 1. The low-pedestrian-speed conclusion is directionally robust.

The earlier result showed a high equal-weighted stagnation ratio at z~2 m. The new robustness analysis strengthens this conclusion: 91.5% of open pedestrian-layer cells are below VR=0.2 under at least six of the eight wind directions, and 87.2% are below VR=0.2 under all eight directions. Thus, stagnation is not a single-direction artifact.

Claim readiness: `paper_ready` as a simulation-based robustness conclusion.

### 2. Wind direction mainly affects boundary/open-path details, not the core low-speed diagnosis.

The direction standard deviation and range maps show that the largest directional differences occur near domain edges, open paths, and building-edge corridors. Most inner block areas remain low-speed across directions. This supports a refined spatial interpretation: wind direction redistributes local ventilation channels, but the core block remains poorly ventilated at pedestrian height in the current model.

Claim readiness: `paper_ready` with preliminary-screening wording.

### 3. Open-Meteo weighting reinforces, rather than weakens, the stagnation conclusion.

The Open-Meteo 2024 proxy-weighted mean stagnation probability is 0.9285, and 90.3% of open pedestrian-layer cells have weighted stagnation probability at least 0.75. Because the dominant proxy directions still produce low pedestrian-layer VR, climate weighting does not materially change the diagnosis.

Claim readiness: `paper_ready` if described as wind-climate proxy sensitivity, not measured annual comfort probability.

### 4. Acceleration zones are sparse and directionally limited.

Only about 2.5% of open pedestrian-layer cells exceed VR=0.6 in at least two of the eight directions. This supports the conclusion that the current pilot is dominated by low-speed/stagnation behavior rather than widespread hazardous acceleration. It does not yet support formal safety classification, because threshold exceedance probability and field validation are absent.

Claim readiness: `weaken_claim`.

### 5. Vertical recovery remains a central physical pattern.

The vertical profile figure confirms the earlier pattern: VR mean and VR P95 increase strongly with height, while VR<0.2 ratio drops toward zero at 40 m. This strengthens the interpretation that the geometry suppresses near-ground ventilation while flow recovers above the urban canopy.

Claim readiness: `paper_ready` as a modeled vertical-structure observation.

## Protocol Risks and Boundaries

| Risk | Treatment |
|---|---|
| The deepened analysis reuses existing FluidX3D runs rather than new solver runs | Marked as newly run post-processing based on preexisting/newly generated VTK outputs |
| Open-Meteo is a reanalysis-based climate proxy, not a field measurement | Do not call weighted outputs annual comfort compliance |
| NaN warnings occur in solid/domain-outside areas | Metrics are computed only on open fluid cells; warnings are expected for masked solid areas |
| No pollutant scalar is simulated | Pollution conclusions remain blocked |
| No field or wind-tunnel validation exists | Accuracy/compliance claims remain blocked |
