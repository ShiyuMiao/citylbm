# S1 Ventilation-Relief FluidX3D Comparison Report

evidence_type: newly_run + preexisting_artifact

This report upgrades S1 from a placeholder into an executed design-sensitivity experiment. S1 removes a Dijkstra-selected east-west relief corridor from the S0 core-prism collision field and reruns FluidX3D with the same dx=2 m, 8-direction, three-sample-after-spin-up protocol used for S0.

## Geometry and Run Protocol

- S1 geometry: `cfd_ready/core_prism_s1_ventilation_relief_collision_z0.stl`
- Geometry QA: `manifests/geometry_qa_core_prism_s1_ventilation_relief.json`
- Removed collision cells: `66` 5 m heightfield cells.
- Removed area: `1650.0 m2`, `2.79%` of the S0 footprint.
- Removed height min/max/mean: `12.72 / 23.45 / 18.67 m`.
- FluidX3D directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Successful runs: `8/8`, total elapsed `176.32 s`.
- Run summary: `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_run_summary.csv`

## Main S0-S1 Metric Comparison

Machine-readable tables:

- `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_metrics.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv`
- `figures/fluidx3d_s0_s1_ventilation_relief_common_open_delta_summary.csv`

At z~2 m, S0 equal-weighted mean VR is `0.076338` and S1 is `0.076124`, giving `S1-S0 = -0.000213`. The stagnation ratio changes from `0.933547` to `0.933780`. This is not a meaningful global improvement.

The common-open-cell decomposition clarifies the result. At z~2 m, cells open in both S0 and S1 have mean delta VR `0.000043`. S1 newly opens `470` cells at z~2 m, but those cells have mean VR `0.002697` and stagnation ratio `1.000`. The intervention therefore creates additional open space inside a very low-speed background rather than a functioning high-ventilation corridor.

At z~20 m, the mean VR also remains nearly unchanged (`S1-S0 = -0.000654`). The S1 effect is therefore not an upper-layer recovery mechanism either.

## Figures for Manual Review

- `figures/core_prism_s1_ventilation_relief_geometry_audit.png`
- `figures/fluidx3d_core_prism_s1_ventilation_relief_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_s0_s1_ventilation_relief_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_ventilation_relief_height_metric_comparison.png`

## Paper Interpretation

The design-application conclusion is a negative or near-null sensitivity result: a small single-corridor relief through the collision field does not materially alter the pedestrian-height ventilation state of the core campus block. This strengthens the morphology argument because it shows that the low-wind condition is not simply caused by one local blockage. Within this digital-twin model, meaningful ventilation improvement would likely require network-scale porosity changes, larger gateway openings, or interventions aligned with multiple wind sectors.

## Claim Boundary

S1 is a numerical morphology sensitivity scenario. It is not a constructability-verified architectural proposal, not a pollutant-dispersion intervention, and not a formal comfort/safety compliance test. The result should be written as a design-screening finding: the tested single-corridor relief is insufficient under the current FluidX3D protocol.
