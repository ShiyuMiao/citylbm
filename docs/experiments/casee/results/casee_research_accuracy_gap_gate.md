# Case E Research Accuracy Gap Gate

Generated: 2026-08-13T11:21:31.938312+00:00

## Verdict

- Gap gate passed: True
- Formal accuracy claim supported: False
- Formal release allowed: False
- Recommended tag: `v0.4.0-rc87`

## Formal Gap

- MAE gap to <15 pp: 6.111 pp
- R2 gap to >0: 2.006330
- Pearson gap to >0: 0.000000

## Candidate Rows

| candidate | role | MAE pp | R2 | Pearson | metric gate | default? |
|---|---|---:|---:|---:|---:|---:|
| `formal_official_z2m_current` | `formal_official_gate` | 21.111 | -2.006330 | 0.115756 | False | False |
| `best_diagnostic_c014_no_sgs_afk_s2p0` | `diagnostic_candidate` | 13.786 | -0.229845 | 0.314966 | False | False |
| `best_diagnostic_sampling_vertical_valid_above` | `diagnostic_sampling_only` | 16.041 | -0.554717 | 0.336940 | False | False |
| `post_hoc_affine_upper_bound_c014` | `post_hoc_upper_bound_only` | 12.363 | 0.099203 | 0.314966 | True | False |

## Boundary

This gate quantifies the gap to the current project release metric threshold. It does not create new CFD output, does not improve official z=2 m metrics, does not authorize diagnostic sampling or post-hoc calibration as validation, and does not permit formal v0.4.0.
