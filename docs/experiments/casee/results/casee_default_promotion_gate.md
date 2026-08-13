# Case E Default Promotion Gate

Generated: 2026-08-13T12:50:53.079302+00:00

## Verdict

- Gate passed: True
- Any diagnostic default promotion allowed: False
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False

## Promotion Rows

| setting | status | promotion allowed | blockers |
|---|---|---:|---|
| `nu_lbm_override` | diagnostic_switch | False | official_z2m_metric_gate |
| `z_origin_offset` | diagnostic_switch | False | official_z2m_metric_gate |
| `wall_model` | default_off_followup | False | official_z2m_metric_gate; rhino_loaded_new_gha |
| `roughness_length` | default_off_followup | False | official_z2m_metric_gate; rhino_loaded_new_gha |
| `inlet_turbulence` | default_off_followup | False | official_z2m_metric_gate; rhino_loaded_new_gha |
| `residual_target` | default_off_followup | False | official_z2m_metric_gate; rhino_loaded_new_gha |
| `diagnostic_probe_sampling` | diagnostic_only | False | diagnostic_sampling_never_formal_default |

## Boundary

This gate is a promotion blocker: while official z=2 m accuracy, Case A regression, Rhino/GHA load, raw-trilinear protocol, no-fitting, and traceability gates are not all satisfied, diagnostic Case E settings must remain experimental switches. It does not run FluidX3D or update metrics.
