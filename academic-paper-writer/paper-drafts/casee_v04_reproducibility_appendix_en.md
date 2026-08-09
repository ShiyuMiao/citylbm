# AIJ Case E Reproducibility Appendix

Generated: 2026-08-09T16:05:39.427480+00:00

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
- Recommended tag: `v0.4.0-rc46`.
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `d1570ee200c8d2940700ad2c4f48fa661246af3038ef480b8e2435aef8f8654e` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `8ff73eb9370aedda0e60921327ec1eeda86d1f19793aee6f5505067813b1de6b` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `3caea1d4223771ff5665f18cdb174a21b8a6a97cd209e31b35cd0df14bcef85b` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `77bc71b0d05cd34bea1979d6aef7c8afaf7ad402e040a81a539ed448b6cd024b` |
| `docs/experiments/casee/results/casee_c002_longer_mean_audit.json` | lightweight_release_asset | limitations_ready_completed_candidate | `7285658a377355c79d816fb1467558c5a22e712240b791849f30f4b130017de6` |
| `docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json` | lightweight_release_asset | limitations_ready_zorigin_ablation | `4de48eb26c26fa5ec1e79e98d993fd0a9282446701c20dfee9f4700c5ff6ed84` |
| `docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json` | lightweight_release_asset | limitations_ready_dx3_low_cost_regression | `20d53fc4c126d5f15759430c9da2142dccbcbebc4da8edf757ad7bc69a9a6cb7` |
| `docs/experiments/casee/results/casee_c005_decomposition_audit.json` | lightweight_release_asset | limitations_ready_decomposition_sensitivity | `46a8a1ae2e18aa4c7cf27cab3b1970e736dd2e765ce1389e831658195a343151` |
| `docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json` | lightweight_release_asset | limitations_ready_inlet_turbulence_improvement | `88ced2faa44f762d5b8f6494bd24c4d4acceddecf8577309ee648e8e1267890d` |
| `docs/experiments/casee/results/casee_candidate_sweep_plan.json` | lightweight_release_asset | paper_ready_followup_plan | `4d4717ee65997047737ad0153f3452a1e4d38b7278cce38a0e1c27a852396176` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `f1365750c8aa05150a18dbe345c9be579104d8855180adb73471343c9a4ba329` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `eecd7e15025b197d924016bd290d7ce59fb99119e06126e7e210a7b3bbdb7289` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `3908ed6d70d88e64568154f6808c8da3d60b2775755de4cac6d5e2dcebfc5faf` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `d77b59420c8964d63e47a2d52d2c890ccc609dd2587cfe8734c4905418466924` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `219d939714299c18317c6d8dffdc88fed42491df8fe8a01c38fd963de2929e0c` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `ff0e5498a3abe2426a6f28d4b12f8d29951e2a2abfaa23117f25743f299358a8` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `07365c705daae1f1f2f9d30d1029343e99be19b0d31709d176560bfeaed3368c` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `8eb5363b6a5bbdaa5930a44a1cdd9a4d5c64feede1e2ec47cfe836f38c6830bc` |

## Claim Readiness Summary

- blocked: 1
- limitations_ready: 8
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

