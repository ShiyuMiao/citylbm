# AIJ Case E Results and Limitations Draft

evidence_type: newly_run
status: v0.4.0-rc evidence only
generated_from:
- docs/experiments/casee/results/release_gate.json
- docs/experiments/casee/results/casee_manuscript_claim_matrix.csv
- docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv
- docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv

## Results Text

AIJ Case E was re-evaluated under the official `ac+N` condition using the pedestrian-height `z=2 m` protocol and the 80 official probes selected from `RS_caseE.csv` with `case=ac` and `Wind_direction=N`. The formal metric uses only `raw_trilinear` sampling; `z_plus_half`, `vertical_valid_above`, and any vertically shifted diagnostic are excluded from the official result. The latest z-center diagnostic run produced MAE = 21.111 percentage points, RMSE = 27.721 percentage points, Bias = -16.409 percentage points, R2 = -2.006330, and Pearson = 0.115756 (newly_run; source: `docs/experiments/casee/results/release_gate.json`). Because R2 remains negative, this result should be reported as a strict negative validation and error-diagnosis outcome rather than as evidence of validated predictive accuracy.

Relative to the previous dx=2 m probe-mode run, z-center lattice alignment improved the formal `raw_trilinear` MAE from 23.972 to 21.111 percentage points, improved R2 from -2.311768 to -2.006330, and increased Pearson from 0.071789 to 0.115756 (newly_run; sources: `docs/experiments/casee/results/casee_probe_mode_metrics.csv` and `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`). This indicates that the vertical placement of the lattice affects pedestrian-height Case E probes, but the improvement is insufficient for a paper claim of validated prediction accuracy.

The voxel/probe audit shows that the remaining error is concentrated near walls and solid-corner interpolation risks. In the z-center audit, formal `raw_trilinear` MAE is 12.435 percentage points for low-risk probes, compared with 32.644 and 34.589 percentage points for moderate-risk and high-risk probes, respectively (newly_run; source: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv`). The dominant limitation is therefore associated with near-wall sampling, voxelized boundaries, and wall-model behavior rather than with a simple reporting or post-processing error.

## Discussion and Limitations Text

The current Case E evidence supports three bounded claims. First, CityLBM v0.4.0-rc implements a traceable workflow for the official Case E preconditions, 80-probe filtering, inlet-profile handling, and probe-sampling diagnostics. Second, z-center alignment and probe-risk auditing reduce some error and identify where the failure concentrates. Third, the formal `z=2 m` validation still fails, with a negative R2, so the release should remain an accuracy-diagnostic release candidate rather than a formal predictive-accuracy release.

Diagnostic sampling modes are useful for sensitivity analysis but cannot replace the official metric. In the z-center run, `vertical_valid_above` reduces MAE to 16.041 percentage points, with R2 = -0.554717 and Pearson = 0.336940 (newly_run; source: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`). However, this mode changes the official z=2 m probe protocol and should be used only to diagnose near-wall and solid-corner sensitivity.

Accordingly, the manuscript should state that CityLBM now provides a reproducible Case E diagnostic workflow and identifies a pedestrian-height near-wall error mechanism. It should not state that CityLBM has reached research-grade predictive accuracy for AIJ Case E. A formal v0.4.0 release requires positive official z=2 m R2, stable positive Pearson correlation, a clear MAE reduction below the present 21 pp level, verified loading of the new GHA in Rhino/Grasshopper, Case A smoke-regression preservation, and a complete build-chain audit.

## Allowed Manuscript Sentences

- CityLBM/FluidX3D completed a traceable AIJ Case E audit under the official `ac+N`, `z=2 m`, 80-probe protocol.
- The current official z=2 m result is MAE = 21.111 percentage points, R2 = -2.006330, and Pearson = 0.115756; therefore, it does not pass the formal accuracy gate.
- Z-center lattice alignment reduced MAE and increased Pearson, but did not make R2 positive.
- High-risk near-wall and solid-corner probes dominate the remaining error, motivating future work on wall modelling, voxelized boundaries, and probe-protocol treatment.

## Forbidden Manuscript Sentences

- CityLBM v0.4.0 has passed AIJ Case E accuracy validation.
- z_plus_half or vertical_valid_above is the official z=2 m validation result.
- The current result proves LES improvement or mesh independence.
- Z-center lattice alignment can be promoted as a default accuracy model for all urban wind cases.
