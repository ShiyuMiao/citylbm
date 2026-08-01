# CityLBM Paper Results Packet

Generated: 2026-08-01T13:40:05.493775+00:00

## Verdict

- Packet passed: True
- Result rows: 14
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False

## Readiness Counts

- available_for_manual_review: 1
- blocked_formal_release_gate: 1
- blocked_official_followup_preflight: 1
- limitations_ready_negative_validation: 1
- must_state_as_boundary: 1
- paper_ready: 1
- paper_ready_as_screening: 1
- paper_ready_default_policy_boundary: 1
- paper_ready_negative_result: 1
- paper_ready_with_boundary: 4
- paper_ready_workflow_guard: 1

## Paper-Ready Or Usable Results

| experiment | result | readiness | metric/status | paper use |
|---|---|---|---|---|
| Experiment 1 / AIJ Case A | `casea_smoke_regression_guard` | paper_ready_workflow_guard | status=passed; steps_complete=True; vtk_outputs=2; timestep_2000_vtk=True | Use as workflow non-regression evidence for the CityLBM/FluidX3D chain. |
| Experiment 2 / AIJ Case E | `casee_software_policy_boundary` | paper_ready_default_policy_boundary | default_policy_gate_passed=True; failure_modes=6; formal_allowed=False | Use to explain which CityLBM settings are formal defaults and which are diagnostic switches. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_M1` | paper_ready | paper_ready | TUM2TWIN layers are separated into visual reference, semantic/collision geometry and CFD/LBM simulation inputs. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R1` | paper_ready_as_screening | paper_ready_as_screening | S0 baseline pedestrian layer is dominated by low speed, while the upper layer recovers. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R2` | paper_ready_with_boundary | paper_ready_with_boundary | Open-Meteo 2024 weighting is a climate-proxy sensitivity layer, not an annual comfort assessment. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R3` | paper_ready_with_boundary | paper_ready_with_boundary | Basic morphology variables are interpretable screening descriptors; sector enclosure ranks above single-building footprint/elongation. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R4` | paper_ready_negative_result | paper_ready_negative_result | S1/S2 are negative design-sensitivity evidence rather than successful optimization. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_NUMERICAL_PROTOCOL` | paper_ready_with_boundary | paper_ready_with_boundary | FluidX3D numerical parameters are archived for screening-level reproduction; residual convergence, field validation and annual compliance are not claimed. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_FINAL_DISCUSSION` | paper_ready_with_boundary | paper_ready_with_boundary | Final discussion and conclusion paragraphs are mapped to evidence and retain blocked claim boundaries. |
| Experiment 3 / TUM2TWIN digital-twin application | `figure_table_manual_review_packet` | available_for_manual_review | available_figure_table_callouts=12 | Use as a checklist for manual figure/table selection in the manuscript. |

## Limitations And Blocked Claims

| experiment | result | readiness | limitation | software feedback |
|---|---|---|---|---|
| Experiment 1 / AIJ Case A | `casea_smoke_regression_guard` | paper_ready_workflow_guard | Smoke regression only; it is not benchmark accuracy validation. | Keep Case A smoke as a required regression guard before stronger Case E claims. |
| Experiment 2 / AIJ Case E | `official_z2m_negative_validation` | limitations_ready_negative_validation | Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness. | Accuracy-improvement work should target near-wall, wall-model, inlet turbulence, voxelization, and official probe protocol fidelity. |
| Experiment 2 / AIJ Case E | `casee_software_policy_boundary` | paper_ready_default_policy_boundary | Default-policy evidence does not improve or replace the official z=2 m metric. | Keep raw_trilinear official z=2 m as formal output; keep nuLBM, zOff and non-raw sampling diagnostic-only. |
| Experiment 2 / AIJ Case E | `next_official_run_readiness` | blocked_official_followup_preflight | Runtime readiness evidence only; no new solver output is produced. | Recover GPU runtime, Rhino new-GHA loading, and VS C++ build chain before new formal Case E sweeps. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_M1` | paper_ready | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R1` | paper_ready_as_screening | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R2` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R3` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_R4` | paper_ready_negative_result | Use within the archived Experiment 3 scope. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_L1` | must_state_as_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_NUMERICAL_PROTOCOL` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `module_claim_FINAL_DISCUSSION` | paper_ready_with_boundary | Screening/application evidence only; field validation, annual comfort compliance, pollutant dispersion, GCBTE and CityLBM-GH end-to-end execution remain unsupported. | Use as design-application workflow evidence, not as Case E accuracy evidence. |
| Experiment 3 / TUM2TWIN digital-twin application | `figure_table_manual_review_packet` | available_for_manual_review | Figure/table availability is not independent validation of CFD accuracy. | Keep release assets lightweight and hash-indexed; large VTK/3DM files should remain external or release assets. |
| CityLBM v0.4.0 release boundary | `formal_release_block` | blocked_formal_release_gate | Formal v0.4.0 remains prohibited until the official z=2 m metric gate and Rhino/GHA loading gate pass. | Version software as release candidates until the formal gate passes. |

## Boundary

The packet is a manuscript organization and claim-control artifact. It preserves negative-validation and limitations boundaries and does not add new CFD results.
