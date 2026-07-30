# AIJ Case E Validation Report

Generated: 2026-07-30T11:06:52.927144+00:00

## Protocol

- Condition: ac
- Wind direction: N
- Formal height: official z=2 m
- Probe aggregation: 80 official probes from RS_caseE.csv
- Validation sampling mode: raw_trilinear
- Diagnostic-only modes: nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half

## Metrics

No complete predicted probe CSV was provided. Official z=2 m validation metrics are blocked.

- Evidence type: newly_run for data audit, blocked for accuracy metrics
- Claim readiness: blocked

## Release Gate

- Formal v0.3.0 allowed: False
- Recommended tag: v0.3.0-rc1

| Check | Status |
|---|---:|
| citylbm_build_passed | False |
| rhino_loaded_new_gha | False |
| native_fluidx3d_dx3_completed | False |
| native_fluidx3d_dx2_completed | False |
| official_z2m_metric_gate | False |
| casea_smoke_regression_passed | False |
| readme_changelog_release_notes_updated | True |
| evidence_trace_complete_for_available_artifacts | True |

## Claim Boundaries

- Paper-ready now: official data provenance, probe filtering protocol, and blocked release-gate transparency.
- Limitations now: local machine lacks native FluidX3D execution evidence and CityLBM build evidence.
- Not paper-ready: any claim that CityLBM v0.3.0 achieved predictive accuracy for Case E official z=2 m.
