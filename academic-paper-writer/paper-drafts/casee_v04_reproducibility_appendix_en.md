# AIJ Case E Reproducibility Appendix

Generated: 2026-08-11T00:41:57.689691+00:00

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
- Recommended tag: `v0.4.0-rc51`.
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
- `build_chain_audit` (passed, returncode=0): `python docs/experiments/casee/tools/build_chain_audit.py`
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
- `casee_candidate_sweep_plan` (passed, returncode=0): `python docs/experiments/casee/tools/casee_candidate_sweep_plan.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `citylbm_manifest_schema_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_schema_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
- `casee_manuscript_section_pack` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_section_pack.py`
- `casee_paper_results_figure` (passed, returncode=0): `python docs/experiments/casee/tools/casee_paper_results_figure.py`
- `citylbm_software_feedback_matrix` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_software_feedback_matrix.py`
- `artifact_index_pre_appendix` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_appendix_generator` (passed, returncode=0): `python docs/experiments/casee/tools/paper_appendix_generator.py`
- `casee_blocker_remediation_plan` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_blocker_remediation_plan.py`
- `casee_next_experiment_runbook` (passed, returncode=0): `python C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\docs\experiments\casee\tools\casee_next_experiment_runbook.py`
- `artifact_index` (passed, returncode=0): `python docs/experiments/casee/tools/artifact_index.py`
- `paper_evidence_gate` (passed, returncode=0): `python docs/experiments/casee/tools/paper_evidence_gate.py`
- `formal_release_gate_expected_block` (passed, returncode=1): `python docs/experiments/casee/tools/release_gate.py`

## Key Artifacts

| artifact | role | readiness | sha256 |
|---|---|---|---|
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `52137c07edc5c6c31386239761404ae1a5972d36c65b9048093f0ce4af1e1be0` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `dc6ad3fed9f0d840cd37dd1ec4b08bf6a320604fb8780ccdfed8a6cf498d4309` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `ef52a02951253261730a7ca308f1a97b1ec2bfa92023c1b96e513f4a30c5d0c0` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `dd3642be67d1f65540340c9a7e272d594eb912fa36c2d5c31f665596dc3ba241` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `f1cd384abbbe47b9aae857dd405f047e1a18d6fb7fb696bac212c9e9dd1758c3` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `176f88ceda2497c7375e8cb6e39f08c9f163875db9db0cb2bf279f6aede760b6` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `ba68ac987771a0e23537326db3f8e559e1e481098caff0420b6dc8b94b770bb6` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `7084f4f0a1c30614fba26371255538add6e1a8c0367ec471daee8a3549f05e23` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `0eed7f87785225166c7fb8ab8e2e5ea9f5a34e0fbbce8fb6d5a06955966d4050` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `e71c535ec315598bf4ee00324a1bb9c8a8b4adc74a45b79088af7ce8d1aa5dda` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `507b2a4c2111f1fcb741d84b28278ede0e1b17d0bd65364c2c662fb3088623b2` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `996d41c2c8a94ca1a817dea19a1dab1086489cd51c985a702c685e3c5bab2b94` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `2668894311e27377d411c34a3f2f75f264b3189474eb4d957bb3d8a4086b01b3` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `c6674f65fbcdfca7795bed751976871c3ab78555c6a6092e067f22a68024ecce` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `15db27d5174430c6c3727363a43420f477a86e26fc2bac658e25baf51c53a8ed` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `30a5220bb888010c76924da2ba7feb01b2acf27fca20da15fa82184fdfaf9268` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `2ebd4a75ef841bad5dabbaa8ade41ab68425d474f2978e57ee62c4dae3918aae` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `4405bf655937220a025b81bf89747cec3cbc049fcb745c7dcd08d0e068b456cd` |

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

