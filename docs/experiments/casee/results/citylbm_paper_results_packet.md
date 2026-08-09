# CityLBM Paper Results Packet

Generated: 2026-08-09T15:41:11.700642+00:00

## Verdict

- Packet passed: True
- Result rows: 25
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False

## Readiness Counts

- available_for_manual_review: 1
- blocked_build_chain_diagnostic: 1
- blocked_formal_release_gate: 1
- blocked_official_followup_preflight: 1
- limitations_ready_candidate_result; blocked formal accuracy release: 1
- limitations_ready_dx1_feasibility: 1
- limitations_ready_dx3_low_cost_regression; blocked formal accuracy release: 1
- limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release: 1
- limitations_ready_negative_validation: 1
- limitations_ready_runtime_decomposition_ablation; blocked formal accuracy release: 1
- limitations_ready_zorigin_ablation; blocked formal accuracy release: 1
- must_state_as_boundary: 1
- paper_ready: 1
- paper_ready_as_screening: 1
- paper_ready_default_policy_boundary: 1
- paper_ready_followup_plan; blocked formal accuracy release: 1
- paper_ready_manifest_schema_boundary: 1
- paper_ready_negative_result: 1
- paper_ready_negative_validation_and_limitations: 1
- paper_ready_reproducibility; blocked formal accuracy release: 1
- paper_ready_with_boundary: 4
- paper_ready_workflow_guard: 1

## Paper-Ready Or Usable Results

| experiment | result | readiness | metric/status | paper use |
|---|---|---|---|---|
| Experiment 1 / AIJ Case A | `casea_smoke_regression_guard` | paper_ready_workflow_guard | status=passed; steps_complete=True; vtk_outputs=2; timestep_2000_vtk=True | Use as workflow non-regression evidence for the CityLBM/FluidX3D chain. |
| Experiment 2 / AIJ Case E | `casee_software_policy_boundary` | paper_ready_default_policy_boundary | default_policy_gate_passed=True; failure_modes=6; formal_allowed=False | Use to explain which CityLBM settings are formal defaults and which are diagnostic switches. |
| Experiment 2 / AIJ Case E | `zcenter_rerun_reproduced_failed_metric` | paper_ready_reproducibility; blocked formal accuracy release | status=passed_reproduced_failed_metric; log_completed_48000=True; csv_sha256_equal=True; MAE=21.111408125 pp; R2=-2.006330362229977; Pearson=0.11575649438573923 | Use as newly-run reproducibility evidence that the current compiled z-center Case E setup reproduces the same negative official z=2 m metric. |
| Experiment 2 / AIJ Case E | `candidate_sweep_followup_plan` | paper_ready_followup_plan; blocked formal accuracy release | candidate_count=8; executable_now_count=0; formal_accuracy_claim_supported=False | Use as a pre-registered follow-up sweep plan for improving the official z=2 m R2. |
| Experiment 2 / AIJ Case E | `casee_manuscript_section_pack` | paper_ready_negative_validation_and_limitations | section_pack_passed=True; formal_accuracy_claim_supported=False; formal_release_allowed=False | Use as ready-to-edit Methods, Results, Diagnostics, Limitations, Software implications, and Release-boundary prose for the negative-validation Case E result. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_M1` | paper_ready | paper_ready | TUM2TWIN layers are separated into visual reference, semantic/collision geometry and CFD/LBM simulation inputs. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R1` | paper_ready_as_screening | paper_ready_as_screening | S0 baseline pedestrian layer is dominated by low speed, while the upper layer recovers. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R2` | paper_ready_with_boundary | paper_ready_with_boundary | Open-Meteo 2024 weighting is a climate-proxy sensitivity layer, not an annual comfort assessment. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R3` | paper_ready_with_boundary | paper_ready_with_boundary | Basic morphology variables are interpretable screening descriptors; sector enclosure ranks above single-building footprint/elongation. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R4` | paper_ready_negative_result | paper_ready_negative_result | S1/S2 are negative design-sensitivity evidence rather than successful optimization. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_NUMERICAL_PROTOCOL` | paper_ready_with_boundary | paper_ready_with_boundary | FluidX3D numerical parameters are archived for screening-level reproduction; residual convergence, field validation and annual compliance are not claimed. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_FINAL_DISCUSSION` | paper_ready_with_boundary | paper_ready_with_boundary | Final discussion and conclusion paragraphs are mapped to evidence and retain blocked claim boundaries. |
| Experiment 3 / TUM2TWIN digital-twin application | `figure_table_manual_review_packet` | available_for_manual_review | available_figure_table_callouts=12 | Use as a checklist for manual figure/table selection in the manuscript. |
| CityLBM v0.4.0 release boundary | `manifest_schema_traceability` | paper_ready_manifest_schema_boundary | manifest_schema_gate_passed=true; formal_accuracy_claim_supported=false | Use to state that generated run manifests have an auditable Case E protocol and claim-boundary schema. |

## Limitations And Blocked Claims

| experiment | result | readiness | limitation | software feedback |
|---|---|---|---|---|
| Experiment 1 / AIJ Case A | `casea_smoke_regression_guard` | paper_ready_workflow_guard | Smoke regression only; it is not benchmark accuracy validation. | Keep Case A smoke as a required regression guard before stronger Case E claims. |
| Experiment 2 / AIJ Case E | `official_z2m_negative_validation` | limitations_ready_negative_validation | Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness. | Accuracy-improvement work should target near-wall, wall-model, inlet turbulence, voxelization, and official probe protocol fidelity. |
| Experiment 2 / AIJ Case E | `casee_software_policy_boundary` | paper_ready_default_policy_boundary | Default-policy evidence does not improve or replace the official z=2 m metric. | Keep raw_trilinear official z=2 m as formal output; keep nuLBM, zOff and non-raw sampling diagnostic-only. |
| Experiment 2 / AIJ Case E | `zcenter_rerun_reproduced_failed_metric` | paper_ready_reproducibility; blocked formal accuracy release | This reinforces repeatability of the failure; it is not an accuracy improvement and cannot support formal v0.4.0. | Prioritize physical wall/inlet/voxelization changes over more repeats of the same compiled baseline. |
| Experiment 2 / AIJ Case E | `next_official_run_readiness` | blocked_official_followup_preflight | Runtime readiness evidence only; no new solver output is produced. | Keep Rhino new-GHA loading and native source compile evidence as operational gates before new formal Case E sweeps. |
| Experiment 2 / AIJ Case E | `dx1_high_resolution_readiness` | limitations_ready_dx1_feasibility | No dx=1 FluidX3D solver output was produced; do not claim mesh independence or improved official z=2 m accuracy. | Keep dx=1 as a user-confirmed high-resolution follow-up path, not a default validation claim. |
| Experiment 2 / AIJ Case E | `candidate_sweep_followup_plan` | paper_ready_followup_plan; blocked formal accuracy release | Planning evidence only; it does not add solver output or justify changing CityLBM defaults. | Run candidates in priority order and promote settings only after official raw_trilinear metrics pass the release gate. |
| Experiment 2 / AIJ Case E | `c002_longer_mean_completed_no_improvement` | limitations_ready_candidate_result; blocked formal accuracy release | Completed candidate result only; it worsened the formal raw_trilinear metric and cannot be used for formal v0.4.0. | Do not promote longer averaging as a default accuracy fix; prioritize wall/inlet/voxelization changes. |
| Experiment 2 / AIJ Case E | `c003_zorigin_ablation_supports_sensitivity` | limitations_ready_zorigin_ablation; blocked formal accuracy release | The no-z-center ablation worsened the formal metric; it cannot support formal accuracy or a default z-origin model. | Keep z-origin alignment as a diagnostic switch and prioritize physical wall/inlet/voxelization work before default promotion. |
| Experiment 2 / AIJ Case E | `c004_dx3_low_cost_positive_but_worse` | limitations_ready_dx3_low_cost_regression; blocked formal accuracy release | Positive Pearson is not enough for formal validation; R2 remains negative and worse than the current z-center baseline. | Do not promote dx=3 coarse-grid settings as an accuracy fix; use it as a quick regression/control path. |
| Experiment 2 / AIJ Case E | `c005_decomposition_improves_mae_r2_but_unstable` | limitations_ready_runtime_decomposition_ablation; blocked formal accuracy release | R2 remains negative, Pearson decreased versus the z-center baseline, and decomposition consistency thresholds failed; no default promotion or formal v0.4.0 claim is supported. | Record domain decomposition in generated run IDs/manifests and treat 4x1x1 as an experimental switch, not a default accuracy setting. |
| Experiment 2 / AIJ Case E | `c008_c012_inlet_turbulence_best_negative_candidate` | limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release | R2 remains negative and the AF-k synthetic inlet scale is a diagnostic sweep parameter; it cannot support formal v0.4.0, predictive accuracy, LES improvement, or default promotion. | Keep AF-k inlet turbulence default-off until a physically validated inlet model reproduces positive R2 without benchmark-specific scale tuning. |
| Build-chain recovery / AIJ Case E follow-up | `build_chain_recovery_status` | blocked_build_chain_diagnostic | Build-chain status is not solver-output evidence and cannot support formal accuracy. | Keep VS C++ Build Tools recovery and Rhino/GHA load evidence as required operational gates before stronger software-release claims. |
| Experiment 2 / AIJ Case E | `casee_manuscript_section_pack` | paper_ready_negative_validation_and_limitations | Generated prose only; it does not add CFD output, improve official z=2 m metrics, or support formal accuracy. | Keep manuscript prose generation downstream of release_gate and manuscript_results_table so claim boundaries stay synchronized. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_M1` | paper_ready | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R1` | paper_ready_as_screening | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R2` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R3` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R4` | paper_ready_negative_result | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_L1` | must_state_as_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_NUMERICAL_PROTOCOL` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_FINAL_DISCUSSION` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `figure_table_manual_review_packet` | available_for_manual_review | Figure/table availability is not independent validation of CFD accuracy. | Keep release assets lightweight and hash-indexed; large VTK/3DM files should remain external or release assets. |
| CityLBM v0.4.0 release boundary | `manifest_schema_traceability` | paper_ready_manifest_schema_boundary | Manifest schema evidence does not add CFD output or improve official z=2 m metrics. | Keep manifest schema checks in the release-candidate evidence chain before stronger paper claims. |
| CityLBM v0.4.0 release boundary | `formal_release_block` | blocked_formal_release_gate | Formal v0.4.0 remains prohibited until the official z=2 m metric gate and Rhino/GHA loading gate pass. | Version software as release candidates until the formal gate passes. |

## Boundary

The packet is a manuscript organization and claim-control artifact. It preserves negative-validation and limitations boundaries and does not add new CFD results.
