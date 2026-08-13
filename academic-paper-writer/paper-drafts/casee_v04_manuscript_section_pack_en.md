# AIJ Case E Manuscript Section Pack

Generated: 2026-08-13T12:51:03.600360+00:00
evidence_type: newly_run
claim_readiness: paper_ready_negative_validation_and_limitations

## Methods Paragraph

AIJ Case E was evaluated under the official `ac+N` condition with wind direction `N` and the CityLBM convention `wind vector = (0, -1, 0)`. The formal benchmark protocol uses `BD_caseE.stl`, scale factor 250, Uref = 3.928296 m/s, zref = 15.9 m, the official pedestrian height z = 2 m, and the 80 probes selected from `RS_caseE.csv` where `case=ac` and `Wind_direction=N`. The formal sampling mode is `raw_trilinear`; `z_plus_half`, `vertical_valid_above`, non-raw interpolation modes, and z-origin offsets are retained only as diagnostic controls. (newly_run; source: `docs/experiments/casee/results/release_gate.json`)

## Results Paragraph

Under this official z = 2 m protocol, the current CityLBM release-candidate result is MAE = 21.111 percentage points, RMSE = 27.721 percentage points, bias = -16.409 percentage points, R2 = -2.006330, and Pearson = 0.115756 across n = 80 probes. Because the formal R2 remains negative, the result is a negative validation outcome and does not support a formal benchmark-accuracy claim. (newly_run; source: `docs/experiments/casee/results/release_gate.json`)

## Diagnostic Paragraph

Diagnostic sampling identifies protocol sensitivity without replacing the formal metric. The best diagnostic row reports MAE = 16.041 percentage points, R2 = -0.554717, and Pearson = 0.336940 for n = 80 probes. This row is useful for explaining near-wall sampling and solid-corner effects, but it is not the official z = 2 m result. (newly_run; source: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`)

## Limitations Paragraph

The remaining error is concentrated in near-wall and solid-corner probe-risk groups. The z-center audit reports low=12.435; high=34.589 percentage points for the low- and high-risk groups, with low=47; high=14 probes in those groups. This supports a limitation focused on wall treatment, voxelized boundaries, and probe-protocol sensitivity rather than a claim of validated accuracy. (newly_run; source: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv; docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv`)

## Software Implications Paragraph

The software changes should be described as traceability and misuse-prevention improvements. CityLBM now exposes the run manifest path, records the formal accuracy-gate contract, and shows a Grasshopper `Claim Gate` output so workflow completion is not confused with benchmark accuracy. These additions do not change the official Case E metric. (newly_run; source: `docs/experiments/casee/results/citylbm_manifest_output_gate.json; CityLBM/src/Core/FluidX3DInterface.cs`)

## Release Boundary Paragraph

The formal release gate remains closed: `formal_release_allowed=False`, with recommended tag `v0.4.0-rc91`. A formal `v0.4.0` release requires official z = 2 m R2 to become positive, Pearson to remain positive, MAE to improve clearly below the present near-21 percentage-point level, Case A smoke regression to remain intact, Rhino/Grasshopper to load the new GHA, and metrics to trace to command, log, CSV, figure, and report artifacts. (newly_run; source: `docs/experiments/casee/results/release_gate.json`)

## Manuscript Sentence Bank

- Under the official AIJ Case E z=2 m protocol, the current CityLBM rc result remains a negative validation (MAE 21.111 pp, R2 -2.006330, Pearson 0.115756). (newly_run; source: `docs/experiments/casee/results/release_gate.json`)
- The best diagnostic sampling row is `vertical_valid_above`, with MAE 16.041 pp and Pearson 0.336940. (newly_run; source: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`)
- In the z-center audit, low-risk probes have raw MAE 12.435 pp, whereas high-risk probes have raw MAE 34.589 pp. (newly_run; source: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv; docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv`)
- CityLBM exposes and audits the run manifest path so protocol and claim-boundary metadata are traceable from the Grasshopper workflow. (newly_run; source: `docs/experiments/casee/results/citylbm_manifest_output_gate.json; CityLBM/src/Core/FluidX3DInterface.cs`)
- The formal release gate remains closed (`formal_release_allowed=False`), and the recommended tag is `v0.4.0-rc91`. (newly_run; source: `docs/experiments/casee/results/release_gate.json`)

## Forbidden Wording

- Do not state that CityLBM has passed AIJ Case E benchmark-accuracy validation.
- Do not state that diagnostic sampling is the official z = 2 m result.
- Do not state that the current evidence proves mesh independence or LES improvement.
- Do not state that the current manifest or Claim Gate output proves CFD accuracy.
