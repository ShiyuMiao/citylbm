# Case E Manuscript Results Table

Generated: 2026-08-11T00:47:28.557190+00:00

## Verdict

- Table passed: True
- Row count: 6
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False
- Claim readiness: `paper_ready_manuscript_results_table`

## Rows

| row | boundary | n | MAE pp | R2 | Pearson | paper sentence |
|---|---|---:|---:|---:|---:|---|
| `formal_official_z2m` | limitations_ready_negative_validation | 80 | 21.111 | -2.006330 | 0.115756 | Under the official AIJ Case E z=2 m protocol, the current CityLBM rc result remains a negative validation (MAE 21.111 pp, R2 -2.006330, Pearson 0.115756). |
| `best_diagnostic_sampling` | limitations_ready_diagnostic | 80 | 16.041 | -0.554717 | 0.336940 | The best diagnostic sampling row is `vertical_valid_above`, with MAE 16.041 pp and Pearson 0.336940. |
| `diagnostic_improvement_direction` | limitations_ready_diagnostic | 80 | 21.217 | -1.626431 | 0.187068 | Compared with the earlier diagnostic best MAE 21.217 pp, z-center diagnostics reduce the diagnostic lower bound to 16.041 pp. |
| `near_wall_risk_gradient` | limitations_ready_diagnostic | low=47; high=14 | low=12.435; high=34.589 |  |  | In the z-center audit, low-risk probes have raw MAE 12.435 pp, whereas high-risk probes have raw MAE 34.589 pp. |
| `software_traceability_status` | paper_ready_manifest_traceability | 17 |  |  |  | CityLBM exposes and audits the run manifest path so protocol and claim-boundary metadata are traceable from the Grasshopper workflow. |
| `release_boundary_status` | blocked_formal_release_gate |  |  |  |  | The formal release gate remains closed (`formal_release_allowed=False`), and the recommended tag is `v0.4.0-rc52`. |

## Limitations And Forbidden Claims

| row | limitations sentence | forbidden claim |
|---|---|---|
| `formal_official_z2m` | This row must be reported as benchmark failure/limitation evidence, not as predictive-accuracy validation. | CityLBM passes AIJ Case E official z=2 m accuracy validation. |
| `best_diagnostic_sampling` | Diagnostic sampling may explain near-wall sensitivity but cannot replace the formal raw_trilinear official z=2 m result. | vertical_valid_above, z_plus_half, or another diagnostic mode is the official validation result. |
| `diagnostic_improvement_direction` | The directional improvement is not a mesh-independence result and all diagnostic R2 values remain negative. | The diagnostic improvement proves LES improvement or mesh independence. |
| `near_wall_risk_gradient` | The earlier high-risk group raw MAE was 32.454 pp; these rows support near-wall/probe-risk limitations only. | The probe-risk gradient is independent field validation. |
| `software_traceability_status` | Manifest traceability does not prove Rhino loaded the new GHA and does not improve CFD accuracy. | A manifest path output proves benchmark accuracy. |
| `release_boundary_status` | Formal v0.4.0 must not be created until official z=2 m metrics and load/runtime gates pass. | The current rc is a formal v0.4.0 accuracy release. |

## Boundary

This table converts existing Case E metrics into manuscript rows. It preserves the formal official z=2 m negative-validation result and keeps all diagnostic sampling rows in limitations.
