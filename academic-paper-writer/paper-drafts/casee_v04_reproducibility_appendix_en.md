# AIJ Case E Reproducibility Appendix

Generated: 2026-08-11T01:58:32.184747+00:00

## Section Contract

Reader state before: the reader has seen the CityLBM workflow and needs enough detail to audit the Case E validation protocol.
Reader state after: the reader can identify the exact official protocol, the available evidence chain, the release boundary, and the remaining blockers.
Required moves: protocol definition, command provenance, artifact provenance, metric scope, software identity, and limitations boundary.
Evidence hooks: release gate JSON, reproducibility suite JSON, artifact index, claim matrix, plugin identity gate, and official Case E metric CSV.

## Protocol Scope

- Benchmark: AIJ Case E.
- Condition: `ac`.
- Wind direction: `N`; wind vector convention recorded as `(0, -1, 0)` in the Case E protocol.
- Geometry: official `BD_caseE.stl`, scale factor 250.
- Reference speed and height: Uref = 3.928296 m/s, zref = 15.9 m.
- Formal validation height: official z = 2 m.
- Formal probe set: 80 probes filtered from `RS_caseE.csv` by `case=ac` and `Wind_direction=N`.
- Formal sampling mode: `raw_trilinear` only.

## Current Official Metric

The current official z = 2 m Case E result is MAE = 21.111 percentage points, RMSE = 27.721 percentage points, bias = -16.409 percentage points, R2 = -2.006330, and Pearson = 0.115756 (newly_run; source: `docs/experiments/casee/results/release_gate.json`). Because the formal R2 remains negative and the release gate is closed, this is a negative-validation result, not an accuracy-success result.

## Reproducibility Chain

- Suite passed: True.
- Paper evidence gate passed: True.
- Plugin identity gate passed: True.
- Formal v0.4.0 release allowed: False.
- Recommended tag: `v0.4.0-rc59`.
- CityLBM build passed: True.
- Case A smoke regression passed: True.
- Rhino loaded new GHA: False.
- Official z = 2 m metric gate passed: False.

## Commands Used For Traceability

- `citylbm_release_build` (passed, returncode=0): `E:\citylbm_buildchain\dotnet\dotnet.exe build CityLBM/CityLBM.csproj -c Release`
- `casee_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_audit.py --predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv --release-target v0.4.0 --dotnet-command E:/citylbm_buildchain/dotnet/dotnet.exe --fluidx3d-exe E:/citylbm_buildchain/FluidX3D/bin/FluidX3D.exe`
- `manuscript_evidence_summary` (passed, returncode=0): `python docs/experiments/casee/tools/manuscript_evidence_summary.py`
- `plugin_identity_gate` (passed, returncode=0): `python docs/experiments/casee/tools/plugin_identity_gate.py`
- `rhino_gha_load_gate` (passed, returncode=0): `python docs/experiments/casee/tools/rhino_gha_load_gate.py`
- `citylbm_gha_install_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\citylbm_gha_install_audit.py`
- `build_chain_audit` (passed, returncode=0): `python docs/experiments/casee/tools/build_chain_audit.py`
- `vs_cpp_recovery_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\vs_cpp_recovery_gate.py`
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `casee_dx1_readiness_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_dx1_readiness_audit.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_zcenter_rerun_consistency` (passed, returncode=0): `python docs/experiments/casee/tools/casee_zcenter_rerun_consistency.py`
- `casee_c002_longer_mean_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c002_longer_mean_audit.py`
- `casee_c003_zorigin_ablation_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c003_zorigin_ablation_audit.py`
- `casee_c004_dx3_low_cost_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c004_dx3_low_cost_audit.py`
- `casee_c005_decomposition_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c005_decomposition_audit.py`
- `casee_c008_c009_inlet_turbulence_audit` (passed, returncode=0): `python docs/experiments/casee/tools/casee_c008_c009_inlet_turbulence_audit.py`
- `casee_c014_residual_structure_audit` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c014_residual_structure_audit.py`
- `casee_c016_residual_target_leakage_guard` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_c016_residual_target_leakage_guard.py`
- `casee_solver_run_provenance_ledger` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_solver_run_provenance_ledger.py`
- `casee_claim_support_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_claim_support_gate.py`
- `casee_candidate_sweep_plan` (passed, returncode=0): `python docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `citylbm_manifest_schema_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `casee_manuscript_section_pack` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `casee_paper_results_figure` (passed, returncode=0): `python docs/experiments/casee/tools/casee_paper_results_figure.py`
- `artifact_index_pre_release_assets` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\artifact_index.py`
- `casee_release_asset_manifest` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `citylbm_software_feedback_matrix` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `casee_next_experiment_runbook` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_next_experiment_runbook.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `casee_release_asset_manifest_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_release_asset_manifest.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `casee_publication_readiness_gate` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_publication_readiness_gate.py`
- `artifact_index_final` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\artifact_index.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## Key Artifacts

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `2f96a89a6293c5e4111bf27448cfc2579751b6b11294d37a2df4167b72c5216b` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `0858e810c6043c01507bde744072b8e1c6038fc1d3206cb59671a950254af6f3` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `bc88f5f9f53a0560814db3b2ba68b5e43f125a1435e743d5aea53dfde87fd6ff` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `b5d02ab2b7f62d83ead652f90cd65e904fb0121c6bc426f9851e04d466fe854c` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `8dec0354998e4bf3173546705fd7633affadf5cdf38a919a6a49c84d820c5dd1` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `17dcbf747f419b84030475fbbfb45caaf1a7a7ee9d0b69940d6ee57d85f939e2` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `6fe9c293d18df13d5a4ee47bc456e67553e5145b9e35a5264e4d3d988b7d4bca` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `c68a85d37a127652e50a4a7e13d5bb83c3178a295800edb2839f4e38f5c1ad8f` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `b5fc5b08ccc67d67d842a8e702d8c896f93e01b6c90db61d1d4309a40b4e91fc` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `815a826b3011cf3e18b86ed112bedd37527c11bcde48147350add5bdf0958468` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `f46a9790d4350ecc3939d63b1c635b130ee5a957685dc196e50e68b79c3cf204` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `c2960d88ac20a5ed860c9317d7ee182da9f0379115ff33c2d88f63113149dc5b` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `bc3537d9408a7f7585c44b1818d55be3e215d1d82998b3f44eef1a362438413b` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `2e4ba8c32bb700b73183af0923eeb5147ff0d8d1ba13673fbc94ec76c7133f59` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `83ba84461da1289087993b037de4709138f1d2883a184f5a57626ce05a11bf62` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `ce7e990bee29e5ed116a66c110419b3361137d2c690884d4f6de6ac67e536512` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `ead59d28e34c7f74fe19da93df5e423b10af1138056fdab107013313cd334d3e` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `87ffa1fabfc191f4411429e2d5f216a8b86ca37a4e09170a1e04556b02103d60` |

## Claim Readiness Summary

- blocked: 1
- limitations_ready: 9
- paper_ready: 2
- weaken_claim: 2

## Manuscript-Allowed Claims

- The Case E official protocol and 80-probe filtering are reproducible from the archived inputs.
- The current CityLBM release-candidate build and tracked GHA are identifiable by hash.
- The official z = 2 m result is a transparent negative validation result.
- Near-wall, solid-corner, voxelization, and probe-sampling effects are supported as limitations diagnostics.

## Forbidden Claims

- CityLBM v0.4.0 has validated predictive accuracy for AIJ Case E.
- A diagnostic z-offset, `z_plus_half`, or `vertical_valid_above` result is the formal official z = 2 m result.
- The current evidence proves mesh independence or LES improvement.
- The current evidence proves that Rhino/Grasshopper has loaded the newly built GHA.

## Remaining Blockers

- Improve the official z = 2 m `raw_trilinear` metric until MAE is clearly below the previous near-20 pp level and R2/Pearson are positive.
- Independently verify that Rhino/Grasshopper loads the new GHA instead of an old plugin copy.
- Use the dx=1 readiness audit before any high-resolution long run; the current audit is limitations/planning evidence only.
- Complete the Visual Studio Build Tools 2022 C++ installation or continue with documented fallback build paths.

