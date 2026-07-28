# S2 Network-Porosity FluidX3D Comparison Report

evidence_type: newly_run + preexisting_artifact

S2 is a stronger network-scale sensitivity experiment added after the near-null S1 result. It tests whether multiple connected porosity releases, rather than a single relief corridor, can alter the pedestrian-height wind response in the TUM Downtown campus core.

## Geometry and Run Protocol

- S2 geometry: `cfd_ready/core_prism_s2_network_porosity_collision_z0.stl`
- Geometry QA: `manifests/geometry_qa_core_prism_s2_network_porosity.json`
- Removed collision cells: `201` 5 m heightfield cells.
- Removed area: `5025.0 m2`, `8.50%` of the S0 footprint.
- Removed height min/max/mean: `12.38 / 32.43 / 21.71 m`.
- FluidX3D directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Successful runs: `8/8`, total elapsed `177.31 s`.
- Run summary: `figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_run_summary.csv`

## Main S0-S2 Metric Comparison

At z~2 m, S0 equal-weighted mean VR is `0.076338` and S2 is `0.075872`, giving `S2-S0 = -0.000466`. The VR<0.2 stagnation ratio changes from `0.933547` to `0.934181`. This remains a near-null/negative global response.

The common-open-cell decomposition is more diagnostic. At z~2 m, cells open in both S0 and S2 have mean delta VR `0.000247`, but the `1235` newly opened cells have mean VR only `0.004384` and stagnation ratio `1.000`. At z~10 m, the common-open mean delta rises to `0.001457`, but newly opened cells are still mostly stagnant with ratio `0.994`. At z~20 m, the global mean VR change is `-0.001109`.

## Paper Interpretation

S2 strengthens the design conclusion by converting the S1 observation into a two-level sensitivity result. S1 shows that a single light relief corridor is insufficient. S2 shows that a stronger multi-corridor porosity release still does not guarantee pedestrian-layer ventilation recovery when the released spaces are embedded in a deep sheltered campus-core flow field. The more defensible architectural conclusion is therefore not simply "increase porosity", but "increase wind-sector-coupled porosity at effective momentum-entry positions and reduce local enclosure where the external flow can actually enter".

## Figures for Manual Review

- `figures/core_prism_s2_network_porosity_geometry_audit.png`
- `figures/fluidx3d_core_prism_s2_network_porosity_8dir_dx2m_vr_panel_z2m.png`
- `figures/fluidx3d_s0_s2_network_porosity_equal_weighted_vr_delta_z2m.png`
- `figures/fluidx3d_s0_s1_s2_design_sensitivity_height_metric_comparison.png`

## Claim Boundary

S2 is a numerical morphology sensitivity scenario. It is not a constructability-verified campus proposal, not a pollutant-dispersion intervention, not a formal comfort/safety compliance test, and not proof that all porosity changes fail. It shows only that the tested network-porosity release does not materially improve the equal-weighted FluidX3D pedestrian-layer screening metrics under the current dx=2 m, 8-direction protocol.
