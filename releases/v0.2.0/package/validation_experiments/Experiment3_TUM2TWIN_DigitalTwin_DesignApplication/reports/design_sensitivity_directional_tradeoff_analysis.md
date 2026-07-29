# Design-Sensitivity Directional Trade-Off Analysis

evidence_type: newly_run

This report reprocesses the existing S0, S1 and S2 FluidX3D VTK outputs without rerunning the solver. The goal is to determine whether the negative or near-null equal-weighted design result hides directional or local trade-offs.

## Protocol

- Source VTK: `F:/citylbm_fluidx3d_workspace/tum2twin_case/output`
- Scenarios: `S0`, `S1_ventilation_relief`, `S2_network_porosity`
- Wind directions: 0, 45, 90, 135, 180, 225, 270, 315 deg.
- Averaging: three post-spin-up samples per wind direction.
- Pedestrian-layer focus: z~2 m.
- Local trade-off threshold: `Delta VR > 0.02` for improved common-open cells and `Delta VR < -0.02` for worsened common-open cells.

## Key Findings

For S1-S0, the best common-open wind direction is `270` deg with mean common-open delta VR `0.000105`. The mean area share of common-open cells with delta VR>0.02 across directions is only `0.000513`, while the mean worsened share is `0.000248`. Newly opened S1 cells never form an effective pedestrian-height flow path; the highest direction-wise mean VR among newly opened cells is `0.004615`.

For S2-S0, the best common-open wind direction is `315` deg with mean common-open delta VR `0.000368`. The mean improved share is `0.002374`, while the mean worsened share is `0.000534`. Although S2 has more local response than S1, the highest newly opened mean VR across wind directions is still only `0.006646`, and the minimum newly opened stagnation ratio remains `1.000000`.

S2-S1 confirms that the stronger network-porosity case changes local common-open cells more than S1, but it still does not create a global ventilation recovery. Its best global wind direction is `315` deg with global mean delta VR `-0.000117`.

## Paper Interpretation

The design result should not be written as a simple null statement. S1/S2 produce weak and directionally localized changes in common-open cells, but these local changes are too sparse to shift the equal-weighted pedestrian-layer state. The newly opened cells are the decisive evidence: they remain low-speed, meaning that the intervention geometry created open space without creating a momentum-carrying path. This supports a more precise design conclusion: in this campus-core configuration, wind-environment improvement requires wind-sector-coupled gateway placement and pressure-exchange continuity, not only increased geometric porosity.

## Artifacts

- `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_summary_z2m.csv`
- `figures/fluidx3d_design_sensitivity_directional_tradeoff_heatmap_z2m.png`
- `figures/fluidx3d_s2_minus_s0_directional_delta_panel_z2m.png`
- `figures/fluidx3d_s1_minus_s0_directional_delta_panel_z2m.png`
- `figures/fluidx3d_s2_minus_s1_directional_delta_panel_z2m.png`

## Claim Boundary

This is a deterministic post-processing analysis of existing FluidX3D outputs. It does not add measured validation, annual wind-rose comfort probability, pollutant dispersion or constructability evidence.
