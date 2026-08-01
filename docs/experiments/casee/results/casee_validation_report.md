# AIJ Case E Validation Report

Generated: 2026-08-01T09:48:38.826857+00:00

## Protocol

- Condition: ac
- Wind direction: N
- Formal height: official z=2 m
- Probe aggregation: 80 official probes from RS_caseE.csv
- Validation sampling mode: raw_trilinear
- Diagnostic-only modes: nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half

## Metrics

- Prediction source: `docs\experiments\casee\results\casee_native_dx2_sampledt2000_probe_time_mean.csv`
- n: 80
- MAE: 31.436 percentage points
- RMSE: 35.774 percentage points
- Bias: -31.233 percentage points
- R2: -4.006626
- Pearson: -0.001683
- Evidence type: newly_run

## Release Gate

- Release target: v0.4.0
- Formal release allowed: False
- Recommended tag: v0.4.0-rc1

| Check | Status |
|---|---:|
| citylbm_build_passed | True |
| rhino_loaded_new_gha | False |
| native_fluidx3d_dx3_completed | True |
| native_fluidx3d_dx2_completed | True |
| official_z2m_metric_gate | False |
| casea_smoke_regression_passed | False |
| readme_changelog_release_notes_updated | True |
| evidence_trace_complete_for_available_artifacts | True |

## Claim Boundaries

- Paper-ready now: official data provenance, probe filtering protocol, and blocked release-gate transparency.
- Limitations now: formal accuracy remains blocked until native FluidX3D dx=3 m and dx=2 m official z=2 m runs produce complete probe CSVs.
- Not paper-ready: any claim that CityLBM v0.4.0 achieved predictive accuracy for Case E official z=2 m before the metric gate passes.
