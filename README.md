# CityLBM

CityLBM is an academic, design-oriented urban wind field simulation
and risk identification system based on the lattice Boltzmann method (LBM).

The system is developed as part of doctoral research in urban and architectural studies.

## Project Status
CityLBM is under active academic development.
The repository currently serves as a reference point for the project
and will be progressively updated.

## AIJ Case E v0.4.0 Release Gate

The active Experiment 2 branch is preparing CityLBM v0.4.0 around AIJ Case E
`ac+N` validation. Formal validation is locked to the official z=2 m probe
set: `RS_caseE.csv` filtered by `case=ac` and `Wind_direction=N` gives 80
probes. Diagnostic height offsets such as `z_plus_half` or `z+4.5 m` are not
accepted as formal validation results.

Current newly-run native results do not satisfy the formal accuracy gate. The
formal release-gate baseline remains the z-center dx=2 m official z=2 m
raw_trilinear run: MAE 21.111 percentage points, R2 -2.006330, Pearson
0.115756. The strongest diagnostic candidate so far is C014, a default-off
no-SGS AF-k synthetic full-plane inlet run at scale 2.00: MAE 13.786
percentage points, R2 -0.229845, Pearson 0.314966. A residual-structure audit
shows that even a post-hoc affine upper bound only reaches R2 0.099203, so
these results support a limitations/diagnostic discussion only, not a
predictive-accuracy claim or a formal `v0.4.0` release.

The rc87 research-accuracy gap gate quantifies the remaining official gap using
the current project release threshold (`MAE < 15 pp`, `R2 > 0`, `Pearson > 0`):
the formal official result is still 6.111 pp above the MAE threshold and 2.006330
below positive R2. These are limitations and next-experiment planning numbers,
not evidence of research-grade accuracy.

The rc88 action-plan gate converts that gap into ordered next steps: keep formal
release blocked, complete Rhino/GHA load evidence, recover GPU/preflight, then
run official wall-model, AF-k/no-SGS inlet, and C016 channel-response follow-ups
only after recovery. All of those actions remain default-off until audited
official z=2 m metrics pass.

Current Case E, release-gate, and manuscript-boundary materials:

- `docs/experiments/casee/data_manifest.csv`
- `docs/experiments/casee/casee_preset.json`
- `docs/experiments/casee/casee_protocol.md`
- `docs/experiments/casee/tools/casee_audit.py`
- `docs/experiments/casee/tools/generate_native_casee.py`
- `docs/experiments/casee/tools/release_gate.py`
- `docs/experiments/casee/tools/paper_evidence_gate.py`
- `docs/experiments/casee/tools/casee_release_asset_manifest.py`
- `docs/experiments/casee/tools/vs_cpp_recovery_gate.py`
- `docs/experiments/casee/tools/vs_cpp_buildtools_recovery.ps1`
- `docs/experiments/casee/tools/vs_cpp_system_drive_space_gate.py`
- `docs/experiments/casee/tools/vs_cpp_elevated_launcher_gate.py`
- `docs/experiments/casee/tools/vs_cpp_buildtools_elevated_launcher.ps1`
- `docs/experiments/casee/tools/citylbm_gha_install_audit.py`
- `docs/experiments/casee/tools/rhino_gha_load_gate.py`
- `docs/experiments/casee/tools/build_chain_audit.py`
- `docs/experiments/casee/tools/casee_official_run_preflight.py`
- `docs/experiments/casee/tools/casee_dx1_readiness_audit.py`
- `docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `docs/experiments/casee/tools/casee_operational_recovery_dashboard.py`
- `docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `docs/experiments/casee/tools/casee_zcenter_rerun_consistency.py`
- `docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `docs/experiments/casee/tools/casee_c002_longer_mean_audit.py`
- `docs/experiments/casee/tools/casee_c003_zorigin_ablation_audit.py`
- `docs/experiments/casee/tools/casee_c004_dx3_low_cost_audit.py`
- `docs/experiments/casee/tools/casee_c005_decomposition_audit.py`
- `docs/experiments/casee/tools/casee_c008_c009_inlet_turbulence_audit.py`
- `docs/experiments/casee/tools/casee_c014_residual_structure_audit.py`
- `docs/experiments/casee/tools/casee_claim_support_gate.py`
- `docs/experiments/casee/tools/casee_publication_readiness_gate.py`
- `docs/experiments/casee/tools/casee_default_policy_gate.py`
- `docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `docs/experiments/casee/tools/casee_paper_results_figure.py`
- `docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `docs/experiments/casee/results/casee_native_metric_comparison.csv`
- `docs/experiments/casee/results/casee_ground_nu_diagnostic_comparison.csv`
- `docs/experiments/casee/results/casee_solid_corner_group_metrics.csv`
- `docs/experiments/casee/results/casee_spatial_alignment_diagnostic.csv`
- `docs/experiments/casee/results/casee_probe_modes_compile_manifest.json`
- `docs/experiments/casee/results/casee_probe_mode_metrics.csv`
- `docs/experiments/casee/results/casee_native_dx2_gshift1_nu001_pmodes_probe_time_mean.csv`
- `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv`
- `docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv`
- `docs/experiments/casee/results/casee_voxel_probe_audit.csv`
- `docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv`
- `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv`
- `docs/experiments/casee/results/build_chain_manifest.json`
- `docs/experiments/casee/results/build_chain_manifest.csv`
- `docs/experiments/casee/results/build_chain_manifest.md`
- `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv`
- `docs/experiments/casee/results/casee_manuscript_evidence_summary.md`
- `docs/experiments/casee/results/casee_paper_evidence_gate.json`
- `docs/experiments/casee/results/casee_paper_evidence_gate.md`
- `docs/experiments/casee/results/casee_paper_appendix_manifest.json`
- `docs/experiments/casee/results/casee_c014_residual_structure_audit.json`
- `docs/experiments/casee/results/casee_c014_residual_structure_audit.md`
- `docs/experiments/casee/results/casee_c014_residual_top_probes.csv`
- `docs/experiments/casee/results/casee_claim_support_gate.json`
- `docs/experiments/casee/results/casee_claim_support_gate.md`
- `docs/experiments/casee/results/casee_publication_readiness_gate.json`
- `docs/experiments/casee/results/casee_publication_readiness_gate.md`
- `docs/experiments/casee/results/casee_remaining_blockers.json`
- `docs/experiments/casee/results/casee_remaining_blockers.md`
- `docs/experiments/casee/results/casee_release_asset_manifest.json`
- `docs/experiments/casee/results/casee_release_asset_manifest.md`
- `docs/experiments/casee/results/github_release_publication_gate.json`
- `docs/experiments/casee/results/github_release_publication_gate.md`
- `docs/experiments/casee/results/casee_workspace_hygiene_gate.json`
- `docs/experiments/casee/results/casee_workspace_hygiene_gate.md`
- `docs/experiments/casee/results/casee_postrun_official_audit_handoff.json`
- `docs/experiments/casee/results/casee_postrun_official_audit_handoff.md`
- `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.json`
- `docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.md`
- `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.json`
- `docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.md`
- `docs/experiments/casee/results/casee_wall_followup_codegen_gate.json`
- `docs/experiments/casee/results/casee_wall_followup_codegen_gate.md`
- `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.json`
- `docs/experiments/casee/results/casee_inlet_followup_codegen_gate.md`
- `docs/experiments/casee/results/casee_c016_codegen_gate.json`
- `docs/experiments/casee/results/casee_c016_codegen_gate.md`
- `docs/experiments/casee/results/casee_native_codegen_smoke_gate.json`
- `docs/experiments/casee/results/casee_native_codegen_smoke_gate.md`
- `docs/experiments/casee/results/casee_runbook_codegen_preflight.json`
- `docs/experiments/casee/results/casee_runbook_codegen_preflight.md`
- `docs/experiments/casee/results/casee_default_promotion_gate.json`
- `docs/experiments/casee/results/casee_default_promotion_gate.md`
- `docs/experiments/casee/results/casee_research_accuracy_gap_gate.json`
- `docs/experiments/casee/results/casee_research_accuracy_gap_gate.md`
- `docs/experiments/casee/results/casee_accuracy_action_plan_gate.json`
- `docs/experiments/casee/results/casee_accuracy_action_plan_gate.md`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.json`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.json`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.json`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.json`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.json`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.md`
- `docs/experiments/casee/results/rhino_gha_load_manifest.expected.json`
- `docs/releases/v0.4.0-rc89.md`
- `docs/releases/v0.4.0-rc90.md`
- `docs/releases/v0.4.0-rc87.md`
- `docs/releases/v0.4.0-rc88.md`
- `docs/releases/v0.4.0-rc86.md`
- `docs/releases/v0.4.0-rc85.md`
- `docs/releases/v0.4.0-rc84.md`
- `docs/releases/v0.4.0-rc83.md`
- `docs/releases/v0.4.0-rc82.md`
- `docs/releases/v0.4.0-rc81.md`
- `docs/releases/v0.4.0-rc80.md`
- `docs/releases/v0.4.0-rc79.md`
- `docs/releases/v0.4.0-rc78.md`
- `docs/releases/v0.4.0-rc77.md`
- `docs/releases/v0.4.0-rc76.md`
- `docs/experiments/casee/results/vs_cpp_recovery_gate.json`
- `docs/experiments/casee/results/vs_cpp_recovery_gate.md`
- `docs/experiments/casee/results/vs_cpp_system_drive_space_gate.json`
- `docs/experiments/casee/results/vs_cpp_system_drive_space_gate.md`
- `docs/experiments/casee/results/vs_cpp_elevated_launcher_gate.json`
- `docs/experiments/casee/results/vs_cpp_elevated_launcher_gate.md`
- `docs/experiments/casee/results/citylbm_gha_install_audit.json`
- `docs/experiments/casee/results/citylbm_gha_install_audit.md`
- `docs/experiments/casee/results/casee_rhino_load_evidence_kit.json`
- `docs/experiments/casee/results/casee_rhino_load_evidence_kit.md`
- `docs/experiments/casee/results/rhino_gha_load_manifest.template.json`
- `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.json`
- `docs/experiments/casee/results/rhino_gha_load_manifest_schema_gate.md`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.json`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.md`
- `docs/experiments/casee/results/rhino_gha_load_manifest.expected.json`
- `docs/experiments/casee/results/citylbm_plugin_identity_component_gate.json`
- `docs/experiments/casee/results/citylbm_plugin_identity_component_gate.md`
- `docs/experiments/casee/results/citylbm_plugin_identity_binary_gate.json`
- `docs/experiments/casee/results/citylbm_plugin_identity_binary_gate.md`
- `docs/experiments/casee/results/citylbm_portable_toolchain_gate.json`
- `docs/experiments/casee/results/citylbm_portable_toolchain_gate.md`
- `docs/experiments/casee/results/citylbm_portable_toolchain_activation.json`
- `docs/experiments/casee/results/citylbm_gpu_runtime_failfast_gate.json`
- `docs/experiments/casee/results/citylbm_gpu_runtime_failfast_gate.md`
- `docs/experiments/casee/results/casee_operational_recovery_dashboard.json`
- `docs/experiments/casee/results/casee_operational_recovery_dashboard.md`
- `docs/experiments/casee/results/casee_orphan_candidate_csv_audit.json`
- `docs/experiments/casee/results/casee_orphan_candidate_csv_audit.md`
- `docs/releases/v0.4.0-rc75.md`
- `docs/releases/v0.4.0-rc74.md`
- `docs/releases/v0.4.0-rc73.md`
- `docs/releases/v0.4.0-rc72.md`
- `docs/releases/v0.4.0-rc71.md`
- `docs/releases/v0.4.0-rc70.md`
- `docs/releases/v0.4.0-rc69.md`
- `docs/releases/v0.4.0-rc68.md`
- `docs/releases/v0.4.0-rc67.md`
- `docs/releases/v0.4.0-rc66.md`
- `docs/releases/v0.4.0-rc65.md`
- `docs/releases/v0.4.0-rc64.md`
- `docs/releases/v0.4.0-rc63.md`
- `docs/releases/v0.4.0-rc62.md`
- `docs/releases/v0.4.0-rc61.md`
- `docs/releases/v0.4.0-rc60.md`
- `docs/releases/v0.4.0-rc59.md`
- `docs/releases/v0.4.0-rc58.md`
- `docs/releases/v0.4.0-rc57.md`
- `docs/releases/v0.4.0-rc56.md`
- `docs/releases/v0.4.0-rc55.md`
- `docs/releases/v0.4.0-rc54.md`
- `docs/releases/v0.4.0-rc53.md`
- `docs/releases/v0.4.0-rc52.md`
- `docs/releases/v0.4.0-rc51.md`
- `docs/releases/v0.4.0-rc50.md`
- `docs/releases/v0.4.0-rc49.md`
- `docs/releases/v0.4.0-rc48.md`
- `docs/releases/v0.4.0-rc47.md`
- `docs/experiments/casee/results/casee_next_experiment_runbook.json`
- `docs/experiments/casee/results/casee_next_experiment_runbook.md`
- `docs/experiments/casee/results/rhino_gha_load_gate.json`
- `docs/experiments/casee/results/rhino_gha_load_gate.md`
- `docs/experiments/casee/results/casee_official_run_preflight.json`
- `docs/experiments/casee/results/casee_official_run_preflight.md`
- `docs/experiments/casee/results/casee_dx1_readiness_audit.json`
- `docs/experiments/casee/results/casee_dx1_readiness_audit.md`
- `docs/experiments/casee/results/casee_dx1_readiness_audit.csv`
- `docs/experiments/casee/results/casee_environment_recovery_runbook.json`
- `docs/experiments/casee/results/casee_environment_recovery_runbook.md`
- `docs/experiments/casee/results/casee_failure_mode_atlas.json`
- `docs/experiments/casee/results/casee_failure_mode_atlas.md`
- `docs/experiments/casee/results/casee_failure_mode_atlas.png`
- `docs/experiments/casee/results/casee_zcenter_rerun_consistency.json`
- `docs/experiments/casee/results/casee_zcenter_rerun_consistency.md`
- `docs/experiments/casee/results/casee_zcenter_rerun_consistency.csv`
- `docs/experiments/casee/results/casee_c002_longer_mean_audit.json`
- `docs/experiments/casee/results/casee_c002_longer_mean_audit.md`
- `docs/experiments/casee/results/casee_c002_longer_mean_audit.csv`
- `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json`
- `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.md`
- `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.csv`
- `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json`
- `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.md`
- `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.csv`
- `docs/experiments/casee/results/casee_c005_decomposition_audit.json`
- `docs/experiments/casee/results/casee_c005_decomposition_audit.md`
- `docs/experiments/casee/results/casee_c005_decomposition_audit.csv`
- `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json`
- `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md`
- `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv`
- `docs/experiments/casee/results/casee_candidate_sweep_plan.json`
- `docs/experiments/casee/results/casee_candidate_sweep_plan.md`
- `docs/experiments/casee/results/casee_candidate_sweep_plan.csv`
- `docs/experiments/casee/results/casee_default_policy_gate.json`
- `docs/experiments/casee/results/casee_default_policy_gate.md`
- `docs/experiments/casee/results/casee_default_policy_gate.csv`
- `docs/experiments/casee/results/casee_default_promotion_gate.json`
- `docs/experiments/casee/results/casee_default_promotion_gate.md`
- `docs/experiments/casee/results/casee_default_promotion_gate.csv`
- `docs/experiments/casee/results/casee_research_accuracy_gap_gate.json`
- `docs/experiments/casee/results/casee_research_accuracy_gap_gate.md`
- `docs/experiments/casee/results/casee_research_accuracy_gap_gate.csv`
- `docs/experiments/casee/results/casee_accuracy_action_plan_gate.json`
- `docs/experiments/casee/results/casee_accuracy_action_plan_gate.md`
- `docs/experiments/casee/results/casee_accuracy_action_plan_gate.csv`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.json`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.md`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_component_gate.csv`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.json`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.md`
- `docs/experiments/casee/results/citylbm_casee_accuracy_action_plan_binary_gate.csv`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.json`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.md`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_component_gate.csv`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.json`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.md`
- `docs/experiments/casee/results/citylbm_casee_paper_claim_card_binary_gate.csv`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.json`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.md`
- `docs/experiments/casee/results/casee_rhino_load_evidence_packet_gate.csv`
- `docs/experiments/casee/results/casee_manuscript_results_table.json`
- `docs/experiments/casee/results/casee_manuscript_results_table.md`
- `docs/experiments/casee/results/casee_manuscript_results_table.csv`
- `docs/experiments/casee/results/casee_manuscript_section_pack.json`
- `docs/experiments/casee/results/casee_manuscript_section_pack_qa.md`
- `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md`
- `docs/experiments/casee/results/casee_paper_results_figure.svg`
- `docs/experiments/casee/results/casee_paper_results_figure.png`
- `docs/experiments/casee/results/casee_paper_results_figure_source.csv`
- `docs/experiments/casee/results/casee_paper_results_figure_qa.json`
- `docs/experiments/casee/results/casee_paper_results_figure_qa.md`
- `docs/experiments/casee/results/citylbm_paper_results_packet.json`
- `docs/experiments/casee/results/citylbm_paper_results_packet.md`
- `docs/experiments/casee/results/citylbm_paper_results_packet.csv`
- `docs/experiments/casee/results/citylbm_manifest_output_gate.json`
- `docs/experiments/casee/results/citylbm_manifest_output_gate.md`
- `docs/experiments/casee/results/citylbm_manifest_output_gate.csv`
- `docs/experiments/casee/results/citylbm_manifest_schema_gate.json`
- `docs/experiments/casee/results/citylbm_manifest_schema_gate.md`
- `docs/experiments/casee/results/citylbm_manifest_schema_gate.csv`
- `docs/experiments/casee/results/citylbm_software_feedback_matrix.json`
- `docs/experiments/casee/results/citylbm_software_feedback_matrix.md`
- `docs/experiments/casee/results/citylbm_software_feedback_matrix.csv`
- `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md`
- `academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md`
- `docs/experiments/casea/results/casea_smoke_regression.json`
- `docs/experiments/casea/results/casea_vtk_manifest.csv`
- `docs/releases/v0.4.0-rc46.md`

The current-machine AIJ Case A smoke regression passed as a workflow
non-regression guard: dx = 3.5 m, 2000 FluidX3D steps, a completed run log, and
two external VTK outputs recorded by hash. This does not provide accuracy
validation for CityLBM; it only guards against breaking the earlier Case A
workflow while Case E is being optimized.

CityLBM includes one experiment-derived default-off solver switch in this branch:
`Diagnostic LBM Nu Override` (`nuLBM`) on the Grasshopper `Run Simulation`
component. It is for reproducing `nu_lbm` sensitivity diagnostics only; leaving
it at 0 keeps the standard physical-viscosity mapping.

CityLBM also exposes default-off wall and roughness follow-up controls on
`Run Simulation`: `Diagnostic Wall Model` (`wallModel`, default `none`) and
`Diagnostic Roughness Length` (`z0Wall`, default `0.0 m`). Generated
`setup.cpp` and `citylbm_run_manifest.json` record these settings for audit
traceability only. They do not change the default wall treatment and are not
formal validation or accepted accuracy-improvement claims.

The native Case E generator also supports a compile-verified probe-mode
diagnostic runner. It keeps `predicted_velocity_ratio` as the formal
`raw_trilinear` z=2 m result and adds diagnostic columns for `nearest_valid`,
`fluid_weighted`, `vertical_valid_above`, and `z_plus_half`. These columns are
experimental only until a full run is completed and audited.

The completed probe-mode diagnostic run reduced the best diagnostic MAE to
21.217 percentage points with `z_plus_half` and raised Pearson to 0.187068, but
R2 remained negative. This is limitations evidence for near-wall/probe-protocol
sensitivity, not formal validation.

The voxel/probe protocol audit shows the same limitation from the geometry side:
low-risk probes have raw MAE 12.932 pp, while high-risk probes have raw MAE
32.454 pp. CityLBM now records Case E probe protocol risk metadata in generated
run manifests so this condition is visible before results are interpreted.

The Grasshopper `Run Simulation` component now exposes a `Manifest Path` (`Man`)
output pointing to the generated `citylbm_run_manifest.json`. This is a
traceability improvement for paper and reviewer auditing of protocol metadata;
it does not change solver numerics or official z=2 m accuracy.

The generated run manifest now also records `paper_readiness`,
`paper_allowed_uses`, and `paper_forbidden_claims` under
`release_claim_boundary`. These fields make the formal release gate and
diagnostic-only boundaries visible in each generated case folder.

Generated run manifests also include a `formal_accuracy_gate` contract for the
`v0.4.0` line. It records the official Case E `ac+N` z=2 m raw-trilinear
requirements, Case A/Rhino/release-gate dependencies, and explicitly states
that the manifest alone cannot authorize a formal accuracy claim.

The `citylbm_manifest_schema_gate.py` audit now verifies that generated run
manifests keep a stable Case E claim contract: official protocol fields,
diagnostic substitute blockers, wall/roughness default-safety fields, and
paper-forbidden claim classes. This is schema/traceability evidence only, not
CFD solver-output evidence.

The Grasshopper `Run Simulation` component now exposes a `Claim Gate` (`Gate`)
output next to `Manifest Path`. For Case E runs it reports the official
validation contract and states that diagnostic sampling, z offsets, wall
models, roughness lengths, and inlet turbulence scale are limitations-only.
This output is intended to prevent workflow-success from being mistaken for
benchmark-accuracy success.

The z-center lattice diagnostic puts official z=2 m on a dx=2 m lattice center.
It improves the formal raw_trilinear MAE to 21.111 pp and Pearson to 0.115756,
but R2 remains negative. Its best diagnostic sampling mode,
`vertical_valid_above`, reaches MAE 16.041 pp and Pearson 0.336940, but this is
still not a formal validation result.

A newly-run 48000-step rerun of the currently compiled z-center setup on
2026-08-09 reproduced the same official z=2 m raw_trilinear CSV and metrics
bit-for-bit against the current baseline (`R2=-2.006330`, MAE 21.111 pp). This
supports repeatability and limitations claims only; it confirms that repeating
the same compiled baseline is not an accuracy-improvement path.

A newly-run source-recompiled C002 follow-up extended the dx=2 m z-center
candidate to 96000 steps with spinup 24000. The run completed and produced the
80 official z=2 m probe CSV, but it worsened the formal metric: MAE 22.015 pp,
R2 -2.185136, and Pearson -0.008937. This is negative follow-up evidence that
longer averaging alone is not the current accuracy bottleneck; it is not a
CityLBM default setting and does not permit formal `v0.4.0`.

A newly-run source-recompiled C003 z-origin ablation removed the z-center
alignment while keeping dx=2 m, ground offset, and `nu_lbm=0.001`. The run
completed 48000 steps and produced the 80 official z=2 m probe CSV, but it
worsened the current best formal metric: MAE 23.126 pp, R2 -2.221379, and
Pearson 0.099217. This supports treating z-origin alignment as a near-wall and
probe-protocol sensitivity diagnostic, not as a validated default accuracy
model.

A newly-run source-recompiled C004 dx=3 m low-cost control completed 48000
steps and kept Pearson positive, but it worsened the current best formal
metric: MAE 24.485 pp, R2 -2.528299, and Pearson 0.109349. This supports use
as a quick direction/protocol regression check only; it is not a coarse-grid
accuracy improvement and does not support mesh independence.

A newly-run source-recompiled C005 dx=2 m 4x1x1 domain-decomposition ablation
completed 48000 steps and improved MAE/R2 relative to the z-center baseline:
MAE 19.726 pp, R2 -1.608075, and Pearson 0.099315. The result remains below
paper-grade accuracy because R2 is still negative, Pearson decreased relative
to the baseline, and decomposition consistency thresholds failed. It is
runtime/decomposition sensitivity evidence and a prompt to keep decomposition
in generated run IDs/manifests, not a default accuracy setting.

Newly-run source-recompiled C008-C015 inlet-turbulence and SGS-ablation
candidates used `AF_caseE.csv` z,U,k to drive a default-off synthetic
full-plane inlet. The best candidate, C014 with SUBGRID disabled and scale
2.00, completed 48000 steps and produced the strongest official-height
diagnostic result so far: MAE 13.786 pp, R2 -0.229845, and Pearson 0.314966.
This supports AF-k inlet turbulence and SGS treatment as the main next software
targets, but R2 is still negative and the no-SGS/scale combination is a
diagnostic sweep parameter, so it is not a formal accuracy model. During the
C010-C015 runs `nvidia-smi` reported GPU3 lost, so FluidX3D was launched on
devices `0 1 2`; this is recorded as a runtime protocol risk. C015 scale 2.50
rolled back, so continued blind scale growth remains a limitations finding
rather than a release path.

CityLBM now exposes the AF-k inlet finding as default-off Grasshopper
diagnostic controls on `Run Simulation`: `Diagnostic Inlet Turbulence Mode`
(`inletT`, default `none`) and `Diagnostic Inlet Turbulence Scale` (`inletS`,
default `0.0`). Setting `inletT=k_synthetic_fullplane` and a positive scale
generates the synthetic full-plane inlet based on `AF_caseE.csv` k and records
the setting in `citylbm_run_manifest.json`. This is a reproducibility and
follow-up switch only; it does not change the default inlet model or make the
official z=2 m R2 positive.

CityLBM now exposes the corresponding `Diagnostic Z Origin Offset` (`zOff`)
input on the Grasshopper `Run Simulation` component. The default is 0 m. This
is an experiment switch for inlet-height and probe-protocol diagnostics, not a
validated default accuracy model.

Current build-chain audit: portable .NET SDK 8.0.423, the existing FluidX3D
binary, and the MinGW/g++ fallback are present locally. The portable toolchain
activation gate records how to activate those paths for the current PowerShell
process without changing system PATH by default. Visual Studio Build Tools 2022
C++ remains blocked: the current shell is not elevated, system-drive free space
is below the audit threshold, `cl.exe`/`msbuild.exe` are not on PATH, and
`vswhere` does not find the VC workload. GPU runtime also remains blocked
because `nvidia-smi` reports `GPU is lost`. The GPU runtime fail-fast gate
records this as `long_fluidx3d_run_allowed=false`, so new official long
FluidX3D validation runs must wait for GPU recovery. These are build/runtime
limitations; source-recompiled candidates still need a recorded native build
path.

The dx=1 m high-resolution readiness audit records the exact future generation
command, the current generator domain (600 x 800 x 241 cells), the conservative
STL-padding domain estimate, and GPU memory scenarios. It does not start
FluidX3D or commit a generated dx=1 STL copy. Under the moderate 512 bytes/cell
scenario, the current generator needs about 13.79 GiB per GPU on a 2 x 2 x 1
decomposition, leaving insufficient 25% headroom on the current P100 cards; the
conservative overhead scenario is not feasible. This is limitations/follow-up
planning evidence only, not mesh-independence or accuracy evidence.

The candidate sweep plan now separates the currently compiled z-center rerun
from source-recompiled follow-up candidates. New longer-time, z-origin,
decomposition, dx=1, wall-model, and inlet-turbulence candidates remain governed
by source-compile, runtime, memory, and formal raw_trilinear metric gates before
any default promotion.

The orphan candidate CSV audit inventories local untracked native
`casee_probe_time_mean.csv` files by SHA256 and metric summary. The current
local candidates remain limitations-only: no complete run logs are present, the
best raw official z=2 m candidate still has negative R2, and no candidate is
eligible for default promotion or formal release-gate replacement.

The manuscript evidence summary now converts Case E outputs into a claim matrix.
It marks protocol and build/workflow evidence as paper-ready, marks the current
official z=2 m result as a negative validation/limitations result, and blocks
formal predictive-accuracy or `v0.4.0` release claims until the metric gate
passes.

The Grasshopper plugin identity is now aligned to the `0.4.0-rc` line while the
release gate remains fail-closed. This prevents the in-app plugin metadata from
appearing as the old `0.1.0` WIP line, but it is still an accuracy-diagnostic
release candidate rather than a formal `v0.4.0` release.

The paper evidence gate scans the release gate, manuscript claim matrix, and
Case E draft text for overstated success claims. Passing this gate means the
paper text is claim-safe under the current negative validation evidence; it does
not mean the CFD accuracy gate passed.

The paper reproducibility appendix generator now creates Chinese and English
Case E appendices from the release gate, reproducibility suite, artifact index,
claim matrix, paper evidence gate, and plugin identity gate. These appendices
are reviewer-facing traceability support only; they do not change the official
z=2 m accuracy result or permit a formal `v0.4.0` tag.

The remaining-blocker remediation plan converts the current release gate,
build-chain audit, dx=1 readiness audit, and run matrix into concrete pass
conditions for the next work cycle. It records the official metric gate failure,
Rhino new-GHA loading gap, incomplete Visual Studio C++ build chain, and dx=1 m
follow-up status as operational blockers rather than accuracy evidence.

The next-experiment runbook turns those blockers into a future command matrix
for preflight checks, dx=2 replication, wall-model and inlet-turbulence
follow-ups, dx=1 feasibility/generation, and post-run official auditing. It is
a run policy and traceability artifact only; it does not add a solver result.

The default-policy gate verifies that software defaults remain claim-safe:
official Case E validation stays locked to z=2 m, 80 ac+N probes, and
`raw_trilinear`; generic viscosity mapping remains the default; `nuLBM`,
`zOff`, effective-ground shifts, wall/roughness follow-ups, and non-raw probe
sampling modes remain experimental switches. This is software-policy evidence,
not formal validation.

The cross-experiment paper results packet now consolidates Experiment 1
workflow evidence, Experiment 2 Case E negative-validation evidence, and
Experiment 3 digital-twin screening evidence into manuscript-ready,
limitations-ready, and blocked rows. It is intended for paper organization and
claim control; it does not add new CFD output or turn Case E into a successful
accuracy validation.

The software-feedback matrix converts Experiments 1-3 into CityLBM decisions:
Case A remains a default release-quality guard; Case E protocol constants remain
the formal validation default; `nuLBM`, `zOff`, and non-raw probe sampling remain
diagnostic switches; GPU/Rhino/VS C++ readiness remains a blocked follow-up
condition; Experiment 3 stays in the digital-twin screening/application layer.
This matrix is the current basis for software optimization claims, not a formal
accuracy-upgrade claim.

The release asset manifest defines the lightweight GitHub Release upload set:
compiled GHA, validation reports, CSV/XLSX summaries, figures, data and
environment manifests, claim/publication gates, and manuscript support files.
Raw geometry, VTK output, large logs, and source-data duplicates remain excluded
or hash-only. This is release traceability only, not CFD accuracy evidence.

The VS C++ recovery gate adds an audit-only-by-default PowerShell recovery
script for Visual Studio Build Tools 2022 C++. The current machine still reports
VS C++ as blocked because `vswhere` does not find the VC tools workload, the
current shell is not elevated, C: free space is below the configured threshold,
and `cl.exe`/`msbuild.exe` are not on PATH. The recovery script records the
manual `winget` command but only installs when run explicitly with `-Install`.

The VS C++ elevated launcher gate adds a separate default-audit launcher for
the same recovery script. It opens a UAC-elevated recovery process only when run
explicitly with `-Launch`, records the post-install verifier
`python docs/experiments/casee/tools/vs_cpp_recovery_gate.py`, and currently
refuses to launch because C: free space is below 8 GB. This is build-chain
recovery traceability only, not CFD accuracy evidence.

The VS C++ system-drive space gate inventories manual cleanup candidates without
deleting files. On this machine C: has about 4.986 GB free, the configured VS
C++ preflight threshold is 8 GB, and low-risk cache candidates total about
0.921 GB, which is not enough to cover the shortfall. VS C++ recovery therefore
remains blocked until larger manual system-drive cleanup is completed and the
elevated launcher gate is rerun.

The operational recovery dashboard orders the remaining environment and protocol
blockers into one run-scheduling view: C: space, VS C++ readiness, UAC launch,
GPU recovery, Rhino/GHA load evidence, official follow-up preflight, and the
formal metric gate. It currently records that long FluidX3D official follow-up
runs are not allowed while system-drive space, GPU runtime, and official
preflight blockers remain active.

The GHA install audit checks whether the tracked `CityLBM/bin/CityLBM.gha`
already appears in common Grasshopper Libraries directories with the expected
SHA256. On the current machine the synchronized GHA is staged in the user's
Grasshopper Libraries directory, but the Rhino/GHA load gate remains blocked
until a real Rhino/Grasshopper session records matching version/hash evidence.

The Rhino load evidence kit prepares that manual check without faking it. It
detects local Rhino executables, verifies the staged GHA SHA256, and writes a
`rhino_gha_load_manifest.template.json`; the actual
`rhino_gha_load_manifest.json` must still be produced from a real Rhino/
Grasshopper session with screenshot or log evidence.

The Rhino load manifest schema gate verifies that this manual manifest contract
is complete before it can be used as load evidence. It checks required fields,
the expected plugin version, the expected GHA SHA256, and listed screenshot/log
artifacts, while keeping the Rhino load gate fail-closed until those real
artifacts exist.

The Rhino load evidence packet gate adds an operator-facing expected manifest
with the exact plugin version, staged GHA path, SHA256, required screenshot/log
artifacts, post-capture commands, and forbidden interpretations. This closes a
paper-review risk where a template or old GHA could be mistaken for real load
evidence; it still does not prove Rhino loaded the plugin until the manual
manifest and artifacts exist.

The `Plugin Identity` Grasshopper component strengthens that manual workflow by
reporting the loaded plugin version, assembly version, GHA path, SHA256,
manifest template, and claim boundary from inside Grasshopper. Its output can
be captured in the required Rhino/GHA load screenshot, but it is still software
identity evidence only and not CFD accuracy evidence.

The packaged GHA identity-component gate then checks the compiled
`CityLBM/bin/CityLBM.gha` itself for those component markers and confirms the
tracked GHA hash matches the plugin identity gate. This proves the release
asset contains the evidence component, but still does not prove a real Rhino/
Grasshopper session loaded it.

The `Case E Accuracy Action Plan` Grasshopper component exposes the current
official z=2 m gap directly in the plugin workflow: MAE 21.111 pp, R2
-2.006330, Pearson 0.115756, plus the ordered actions needed before another
formal accuracy claim can be considered. It is a workflow and claim-boundary
component only; it does not change solver numerics, promote diagnostic
settings to defaults, run FluidX3D, or make `v0.4.0` publishable.

The packaged GHA action-plan gate checks the compiled `CityLBM/bin/CityLBM.gha`
for that component's metric-gap outputs, action IDs, and forbidden-claim
strings. This proves the release asset contains the component, but it still
does not prove Rhino loaded it or improve official Case E accuracy.

The `Case E Paper Claim Card` Grasshopper component turns the same evidence
chain into paper-writing outputs: paper-ready negative-validation statements,
limitations, forbidden claims, and evidence paths. It is intended to prevent
overstated manuscript language while working from the plugin canvas. It does
not run CFD, change solver defaults, update official z=2 m metrics, prove Rhino
loaded the new GHA, or permit formal `v0.4.0`.

The packaged GHA claim-card gate checks that this component is present in
`CityLBM/bin/CityLBM.gha` with the official metric, claim boundary, limitations,
and evidence-path markers intact. This is packaging and paper-boundary evidence
only.

The portable toolchain activation gate verifies the local portable .NET,
FluidX3D, and MinGW/g++ paths needed for reproducible builds and native-source
fallbacks. It does not install VS C++, recover the lost GPU, launch FluidX3D, or
support an accuracy claim.

The GPU runtime fail-fast gate runs `nvidia-smi` before any new long FluidX3D
schedule and closes the run gate when the device reports `GPU is lost`. This is
runtime safety evidence only; it does not recover the device or add solver
output.

The manuscript results table converts Case E evidence into paper-facing rows:
the official z=2 m result is a negative-validation result, the best diagnostic
sampling and near-wall risk rows are limitations-only, and the release boundary
row blocks any formal `v0.4.0` accuracy claim.

The research accuracy gap gate turns that boundary into explicit deltas against
the current release metric threshold. It reports the official MAE and R2 gaps,
keeps C014 and diagnostic sampling in limitations-only roles, and records that
no diagnostic candidate or post-hoc upper bound authorizes default promotion.

The accuracy action plan gate then maps those deltas to next actions. It
prioritizes software-load evidence and environment recovery before any long
official CFD run, and it ranks wall-model, AF-k/no-SGS inlet, and C016
channel-response follow-ups as recovery-gated actions rather than current
results.

The paper results figure exports that table into an editable SVG, PNG preview,
source CSV, and QA manifest. It is suitable for a negative-validation and
limitations figure only; diagnostic bars and risk-group results are not formal
official z=2 m validation evidence.

The manuscript section pack turns the gated Case E result rows into SCI-ready
English Methods, Results, Diagnostics, Limitations, Software implications, and
Release-boundary prose with explicit evidence notes. It is a negative-validation
and limitations writing aid only; it does not change the official z=2 m metric.

Run the audit after official data are present:

```powershell
python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0
python docs/experiments/casee/tools/release_gate.py
python docs/experiments/casee/tools/rhino_gha_load_gate.py
python docs/experiments/casee/tools/build_chain_audit.py
python docs/experiments/casee/tools/casee_official_run_preflight.py
python docs/experiments/casee/tools/casee_environment_recovery_runbook.py
python docs/experiments/casee/tools/casee_failure_mode_atlas.py
python docs/experiments/casee/tools/casee_candidate_sweep_plan.py
python docs/experiments/casee/tools/casee_default_policy_gate.py
python docs/experiments/casee/tools/casee_manuscript_results_table.py
python docs/experiments/casee/tools/casee_manuscript_section_pack.py
python docs/experiments/casee/tools/casee_paper_results_figure.py
python docs/experiments/casee/tools/citylbm_paper_results_packet.py
python docs/experiments/casee/tools/citylbm_manifest_output_gate.py
python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py
python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py
python docs/experiments/casee/tools/paper_evidence_gate.py
```

If a complete solver output exists, provide a CSV with 80 probe predictions:

```powershell
python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted path\to\casee_probe_time_mean.csv
```

The release gate fails closed unless CityLBM builds, the new GHA is loaded in
Rhino/Grasshopper, native FluidX3D dx=3 m and dx=2 m official z=2 m runs
complete, MAE improves clearly below the previous ~20 percentage-point level,
R2 and Pearson are positive, Case A smoke regression passes, and all metrics
trace to command/log/CSV/figure artifacts.

## Research Experiment Archive

The v0.2.0 package includes a validation/application evidence archive under
`releases/v0.2.0/package/validation_experiments/`:

- `AIJ_CaseA/`: benchmark validation support.
- `AIJ_CaseE/`: benchmark validation support.
- `Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/`: real digital-twin
  urban wind-environment design-application experiment.

In the paper structure, AIJ Case A and AIJ Case E support the workflow and
solver validation layer, while Experiment 3 evaluates how TUM2TWIN digital-twin
urban data can be transformed into CFD-ready geometry, simulated with FluidX3D,
reviewed with ParaView/Rhino, and interpreted through basic building-morphology
parameters.

The current Experiment 3 SCI section draft and verification package are stored
under `academic-paper-writer/paper-drafts/`, with release copies under
`releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/`.

The latest Experiment 3 submission-readiness layer adds figure/table captions,
asset-level evidence checks, and a reviewer-facing readiness audit:

- `academic-paper-writer/paper-drafts/figure_table_captions.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_sci_figure_captions_zh.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_sci_table_captions_zh.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_submission_readiness_audit.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/manifests/experiment3_submission_readiness_checklist.csv`

The newest statistical addendum adds effect-size and uncertainty evidence for
the Experiment 3 conclusions:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_effect_size_uncertainty_analysis.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/experiment3_effect_size_uncertainty_summary.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/experiment3_effect_size_uncertainty_forest.png`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_effect_size_uncertainty_results_zh.md`

The directional-mechanism addendum further explains whether the wind response
is caused by a single inflow direction or by the campus block morphology:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_directional_anisotropy_analysis.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/experiment3_directional_anisotropy_summary.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/experiment3_directional_anisotropy_panel.png`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_directional_anisotropy_results_zh.md`

The morphology stage-transition addendum separates near-facade shelter,
20-50 m recovery, and directional reactivity for the 101 retained building
components:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/morphology_stage_transition_analysis.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/morphology_stage_transition_panel.png`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/morphology_stage_transition_feature_contrasts.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/morphology_stage_transition_conclusion_zh.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/morphology_stage_transition_conclusion_en.md`

The morphology directional-fingerprint addendum links 20-50 m local-context
wind-sector response to basic morphology descriptors and stage-transition
classes:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/morphology_directional_fingerprint_analysis.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/morphology_directional_fingerprint_panel.png`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/figures/morphology_directional_fingerprint_feature_correlations.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/morphology_directional_fingerprint_conclusion_zh.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/morphology_directional_fingerprint_conclusion_en.md`

The reviewer reproducibility layer maps Experiment 3 claims to evidence type,
source artifact, reviewer risk, and safe response language:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_reviewer_reproducibility_and_claim_audit.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/manifests/experiment3_reviewer_claim_risk_matrix.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_reviewer_response_paragraphs_en.md`

The final Experiment 3 completeness layer consolidates the data, figures,
evidence boundaries, claim readiness, and remaining gaps for manuscript use:

- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_final_completeness_and_gap_audit.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_completion_audit_and_paper_readiness.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/reports/experiment3_paper_draft_verification.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/manifests/experiment3_final_requirement_coverage.csv`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_final_contribution_and_conclusion_zh.md`
- `releases/v0.2.0/package/validation_experiments/Experiment3_TUM2TWIN_DigitalTwin_DesignApplication/paper_text/experiment3_final_contribution_and_conclusion_en.md`

## License
License information will be provided upon the first public release.
The project is intended for non-commercial academic use.
