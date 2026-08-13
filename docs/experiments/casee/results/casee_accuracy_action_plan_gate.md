# Case E Accuracy Action Plan Gate

Generated: 2026-08-13T12:33:38.333750+00:00

## Verdict

- Action plan gate passed: True
- Formal accuracy claim supported: False
- Formal release allowed: False
- Recommended tag: `v0.4.0-rc90`
- Enabled-now actions: 4

## Actions

| priority | action | class | enabled | blocked by | default? |
|---:|---|---|---:|---|---:|
| 1 | `A001_keep_formal_release_blocked` | `release_safety` | True |  | False |
| 2 | `A002_complete_rhino_gha_manual_load_packet` | `software_load_evidence` | True |  | False |
| 3 | `A003_recover_gpu_and_preflight` | `environment_recovery` | True |  | False |
| 4 | `A004_run_wall_model_followup_first` | `official_cfd_followup_after_recovery` | False | official_data_manifest;rhino_gha_load;gpu_runtime;vs_cpp_build_tools | False |
| 5 | `A005_run_afk_nosgs_inlet_followup_second` | `official_cfd_followup_after_recovery` | False | official_data_manifest;rhino_gha_load;gpu_runtime;vs_cpp_build_tools | False |
| 6 | `A006_run_c016_channel_response_only_after_leakage_guard` | `official_cfd_followup_after_recovery` | False | official_data_manifest;rhino_gha_load;gpu_runtime;vs_cpp_build_tools | False |
| 7 | `A007_audit_any_new_probe_csv_immediately` | `postrun_audit` | False | awaiting_completed_fluidx3d_probe_csv | False |
| 8 | `A008_reject_post_hoc_affine_as_default` | `claim_boundary` | True |  | False |

## Boundary

This action plan prioritizes next steps from existing evidence. It does not run FluidX3D, does not update official metrics, does not promote diagnostic settings to defaults, and does not permit formal v0.4.0.
