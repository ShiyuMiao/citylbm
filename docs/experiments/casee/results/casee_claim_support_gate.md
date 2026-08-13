# Case E Claim Support Gate

Generated: 2026-08-13T04:52:04.786430+00:00

## Verdict

- Gate passed: True
- Formal release allowed: False
- Recommended tag: `v0.4.0-rc75`
- Official R2: -2.006330362229977
- No formal accuracy claims: True
- Forbidden success patterns blocked: True

## Support Classes

- blocked_formal_release: 1
- limitations_only_diagnostic: 9
- paper_methods_protocol: 1
- paper_reproducibility_context: 2
- paper_results_negative_validation: 1

## Claim Triage

| claim | class | readiness | supported | formal accuracy? | limitations |
|---|---|---|---:|---:|---|
| `C001` | paper_methods_protocol | paper_ready | True | False | Protocol setup does not imply accuracy success. |
| `C002` | paper_results_negative_validation | limitations_ready | True | False | Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness. |
| `C003` | limitations_only_diagnostic | weaken_claim | True | False | Do not describe z-origin offset as a validated default model. |
| `C004` | limitations_only_diagnostic | limitations_ready | True | False | Do not remove high-risk probes to report a formal validation metric. |
| `C005` | limitations_only_diagnostic | limitations_ready | True | False | Do not use vertical_valid_above or z_plus_half as the formal official z=2 m result. |
| `C006` | paper_reproducibility_context | paper_ready | True | False | Do not use build success as CFD accuracy validation. |
| `C007` | paper_reproducibility_context | weaken_claim | True | False | Do not claim the VS C++ build-chain requirement is fully installed. |
| `C008` | blocked_formal_release | blocked | True | False | Do not create or cite a formal v0.4.0 tag before the gate passes. |
| `C009` | limitations_only_diagnostic | limitations_ready | True | False | Do not promote C002 settings to CityLBM defaults or claim official z=2 m accuracy improvement. |
| `C010` | limitations_only_diagnostic | limitations_ready | True | False | Do not claim z-center is a validated default accuracy model or that C003 supports formal v0.4.0. |
| `C011` | limitations_only_diagnostic | limitations_ready | True | False | Do not claim dx=3 improves official z=2 m accuracy or proves mesh independence. |
| `C012` | limitations_only_diagnostic | limitations_ready | True | False | Do not promote 4x1x1 decomposition as a default accuracy model or claim formal v0.4.0 validation. |
| `C013` | limitations_only_diagnostic | limitations_ready | True | False | Do not claim formal predictive accuracy, LES improvement, mesh independence, or default promotion from the synthetic inlet/SGS sweep. |
| `C014` | limitations_only_diagnostic | limitations_ready | True | False | Do not report post-hoc affine calibration, z_plus_half, or any residual subset as the formal official z=2 m validation result. |

## Boundary

This gate supports manuscript claim triage only. It does not add CFD output, improve official z=2 m metrics, or permit a formal v0.4.0 release.
