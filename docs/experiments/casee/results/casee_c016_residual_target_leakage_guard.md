# Case E C016 Residual-Target Leakage Guard

Generated: 2026-08-11T01:10:33.115689+00:00

## Verdict

- Guard passed: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_protocol_risk_guard`
- Formal accuracy claim supported: False

## C014 Context

- C014 MAE: 13.7856467875 pp
- C014 R2: -0.22984501828340775
- C014 Pearson: 0.31496559664177526
- Post-hoc affine upper-bound R2: 0.09920332706790935

## Guards

| guard | passed | policy | mitigation |
|---|---:|---|---|
| `c016_residual_diagnosis_is_not_validation` | True | Residual diagnostics may motivate C016 hypotheses but cannot be cited as formal accuracy validation. | Require a future independent official z=2 m raw_trilinear run before any validation claim. |
| `posthoc_affine_upper_bound_blocked` | True | Post-hoc fitting on RS_caseE official targets is calibration leakage and is forbidden as validation. | If calibration is studied, report it only as an upper-bound diagnostic and validate on a separate benchmark or withheld probes. |
| `official_probe_targets_not_training_data` | True | RS_caseE targets are validation data for this project, not model-fitting data. | Freeze C016 settings before running FluidX3D and record them in the native case manifest. |
| `citylbm_residual_controls_default_off` | True | CityLBM must keep residual-target controls default-off until an official independent metric gate passes. | Keep residT/residS default-off and block default promotion in manifests and policy gates. |
| `range_compression_target_is_physics_hypothesis` | True | C016 may target range compression only through a pre-registered wall/inlet/channel-response hypothesis. | Do not use observed residuals as per-probe correction factors in the official metric. |

## Boundary

This guard is a protocol-risk and software-feedback artifact. It does not run FluidX3D, does not change official metrics, and does not support a formal v0.4.0 release. It prevents C016 residual-target work from becoming calibration leakage.
