# AIJ Case E Validation Report

Generated: 2026-08-01T11:02:01.042819+00:00

## Protocol

- Condition: ac
- Wind direction: N
- Formal height: official z=2 m
- Probe aggregation: 80 official probes from RS_caseE.csv
- Validation sampling mode: raw_trilinear
- Diagnostic-only modes: nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half

## Metrics

- Prediction source: `docs\experiments\casee\results\casee_native_dx2_gshift1_nu001_probe_time_mean.csv`
- n: 80
- MAE: 23.972 percentage points
- RMSE: 29.095 percentage points
- Bias: -20.833 percentage points
- R2: -2.311768
- Pearson: 0.071789
- Evidence type: newly_run

## Solid-Corner Diagnostic

| solid_corner_neighbors_max | n | MAE pp | R2 | Pearson |
|---:|---:|---:|---:|---:|
| 0 | 25 | 12.932 | -0.176479 | 0.356584 |
| 2 | 37 | 27.110 | -3.232167 | -0.199618 |
| 3 | 2 | 13.338 | -17.017904 | -1.000000 |
| 4 | 16 | 35.294 | -3.349963 | 0.269639 |

## Spatial Alignment Diagnostic

- Evidence: `docs/experiments/casee/results/casee_spatial_alignment_diagnostic.csv`
- Identity Pearson: 0.071789; R2: -2.311768
- Best Pearson transform: `identity` with Pearson 0.071789
- Best R2 transform: `flip_y` with R2 -2.111059
- Interpretation: no tested x/y flip, swap, or 90-degree rotation makes official z=2 m R2 positive.

## Probe Sampling Modes Runner

- Status: passed
- Evidence type: newly_run
- Claim readiness: compile_only_no_accuracy_metric
- Case: `docs/experiments/casee/native_cases/casee_native_dx2_yn_sgs_gshift1_nu0p001_pmodes_steps48000_spin12000`
- Scope: compile-only diagnostic runner; no probe-mode accuracy metric is claimed until a full FluidX3D run completes.

## Release Gate

- Release target: v0.4.0
- Formal release allowed: False
- Recommended tag: v0.4.0-rc5

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
