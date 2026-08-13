# AIJ Case E Validation Report

Generated: 2026-08-13T12:32:45.743482+00:00

## Protocol

- Condition: ac
- Wind direction: N
- Formal height: official z=2 m
- Probe aggregation: 80 official probes from RS_caseE.csv
- Validation sampling mode: raw_trilinear
- Diagnostic-only modes: nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half

## Metrics

- Prediction source: `E:\citylbm_rc89_work\docs\experiments\casee\results\casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv`
- n: 80
- MAE: 21.111 percentage points
- RMSE: 27.721 percentage points
- Bias: -16.409 percentage points
- R2: -2.006330
- Pearson: 0.115756
- Evidence type: newly_run

## Solid-Corner Diagnostic

| solid_corner_neighbors_max | n | MAE pp | R2 | Pearson |
|---:|---:|---:|---:|---:|
| 0 | 47 | 12.435 | -0.281039 | 0.322599 |
| 2 | 20 | 31.925 | -2.746254 | -0.135504 |
| 4 | 13 | 35.845 | -4.513468 | -0.254465 |

## Spatial Alignment Diagnostic

- Evidence: `docs/experiments/casee/results/casee_spatial_alignment_diagnostic.csv`
- Identity Pearson: 0.071789; R2: -2.311768
- Best Pearson transform: `identity` with Pearson 0.071789
- Best R2 transform: `flip_y` with R2 -2.111059
- Interpretation: no tested x/y flip, swap, or 90-degree rotation makes official z=2 m R2 positive.

## Probe Sampling Modes Runner

- Status: passed_full_run
- Evidence type: newly_run
- Claim readiness: diagnostic_metrics_available
- Case: `docs/experiments/casee/native_cases/casee_native_dx2_yn_sgs_gshift1_nu0p001_pmodes_steps48000_spin12000`
- Full run completed: True
- Scope: diagnostic runner; formal release still uses raw_trilinear official z=2 m metrics.

## Probe Sampling Mode Metrics

- Evidence: `docs/experiments/casee/results/casee_probe_mode_metrics.csv`
- Formal raw_trilinear MAE: 23.972 pp; R2: -2.311768; Pearson: 0.071789
- Best diagnostic MAE: `z_plus_half` with MAE 21.217 pp and R2 -1.626431
- Best diagnostic Pearson: `z_plus_half` with Pearson 0.187068
- Interpretation: diagnostic sampling reduces error but all mode R2 values remain negative.

## Z-Center Lattice Diagnostic

- Evidence: `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`
- Setup: dx=2 m, one effective-ground offset cell, origin_z_offset_m=1.0, official z=2 m placed on a lattice-center height.
- Formal raw_trilinear MAE: 21.111 pp; R2: -2.006330; Pearson: 0.115756
- Best diagnostic MAE: `vertical_valid_above` with MAE 16.041 pp and R2 -0.554717
- Best diagnostic Pearson: `vertical_valid_above` with Pearson 0.336940
- Interpretation: vertical lattice centering improves MAE and Pearson but does not make official z=2 m R2 positive.

## Voxel/Probe Protocol Audit

- Evidence: `docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv`
- Low-risk probes: n=25, raw MAE 12.932 pp
- High-risk probes: n=19, raw MAE 32.454 pp
- All probes: raw MAE 23.972 pp; z_plus_half diagnostic MAE 21.217 pp
- Interpretation: official z=2 m probes are sensitive to voxel layer placement and solid-neighbor interpolation; this is limitations evidence.

## Z-Center Voxel/Probe Audit

- Evidence: `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv`
- Low-risk probes: n=47, raw MAE 12.435 pp
- High-risk probes: n=14, raw MAE 34.589 pp
- All probes: raw MAE 21.111 pp; vertical_valid_above diagnostic MAE 16.041 pp
- Interpretation: after z-center alignment, low-risk probes are substantially closer than moderate/high-risk probes; remaining failure is concentrated near solid-corner and wall-proximity cases.

## Build Chain Audit

- Evidence: `docs/experiments/casee/results/build_chain_manifest.json`
- .NET SDK status: ready
- FluidX3D binary status: ready_for_existing_binary
- Visual Studio Build Tools 2022 C++ status: blocked
- VS Build Tools blocker: winget returned 1602 during the current attempt
- VS Build Tools blocker: Visual Studio bootstrapper log reported possible declined UAC prompt
- VS Build Tools blocker: vswhere does not find Microsoft.VisualStudio.Component.VC.Tools.x86.x64
- VS Build Tools blocker: cl.exe is not on PATH
- VS Build Tools blocker: msbuild.exe is not on PATH
- VS Build Tools blocker: C: drive free space is below 8 GB; Visual Studio may still require more system-drive cache space

## Manuscript Claim Readiness

- Evidence: `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv`
- Summary: `docs/experiments/casee/results/casee_manuscript_evidence_summary.md`
- blocked: 1 claims
- limitations_ready: 9 claims
- paper_ready: 2 claims
- weaken_claim: 2 claims
- Interpretation: only protocol, build/workflow, and limitation claims are paper-ready; formal predictive-accuracy claims remain blocked.

## Release Gate

- Release target: v0.4.0
- Formal release allowed: False
- Recommended tag: v0.4.0-rc90

| Check | Status |
|---|---:|
| citylbm_build_passed | True |
| rhino_loaded_new_gha | False |
| native_fluidx3d_dx3_completed | True |
| native_fluidx3d_dx2_completed | True |
| official_z2m_metric_gate | False |
| casea_smoke_regression_passed | True |
| readme_changelog_release_notes_updated | True |
| evidence_trace_complete_for_available_artifacts | True |

## Case A Smoke Regression

- Status: passed
- Evidence type: newly_run
- Scope: workflow non-regression guard only; not accuracy validation.
- Evidence: `docs/experiments/casea/results/casea_smoke_regression.json` and `docs/experiments/casea/results/casea_vtk_manifest.csv`

## Claim Boundaries

- Paper-ready now: official data provenance, probe filtering protocol, and blocked release-gate transparency.
- Limitations now: native FluidX3D dx=3 m and dx=2 m official z=2 m runs are complete, but the metric gate still fails.
- Not paper-ready: any claim that CityLBM v0.4.0 achieved predictive accuracy for Case E official z=2 m before the metric gate passes.
