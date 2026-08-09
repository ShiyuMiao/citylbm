# AIJ Case E Reproducibility Appendix

Generated: 2026-08-09T11:19:53.529604+00:00

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
- Recommended tag: `v0.4.0-rc30`.
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
- `casee_official_run_preflight` (passed, returncode=0): `python docs/experiments/casee/tools/casee_official_run_preflight.py`
- `casee_environment_recovery_runbook` (passed, returncode=0): `python docs/experiments/casee/tools/casee_environment_recovery_runbook.py`
- `casee_failure_mode_atlas` (passed, returncode=0): `python docs/experiments/casee/tools/casee_failure_mode_atlas.py`
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
- `casee_manuscript_results_table` (passed, returncode=0): `python docs/experiments/casee/tools/casee_manuscript_results_table.py`
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `caf06402885e2fc29c8624891e61c28665e8ddd0cd72080fc999acd2ecef1263` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `64af31a7b0efc97d3246670430d1e6b867453fe162d5351223bb5e852a276985` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `7c9fcd9a235ab14f530b5579d7faa679647a35bbea2f052603084448fc7e1d48` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `ae909b106832b177d92a66c2a1678c267658320fa27daebf970e80f6ff372c66` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `cb6adb03e74e2f25ffdcea90cbd945b818b31e0335782be8aaf1cead08372642` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `4c8b89591260bcedb7c3c6d661305fc996ee510b2bf4aff920310cf45ffa0b96` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `08d4a12a6efb5cb8a4d7c3f181cbd5f05e9c40674cfc39c4bd409759fead68d9` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_official_run_preflight.json` | lightweight_release_asset | blocked_official_followup_preflight | `e862cdfa9ef842803f34f7b1114557a890b1769516d5507db4d25d229821e081` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `71f82bb030ff69c5ea13f56c31b3494c9eaf9e4236a89faabac455ca9cdc8310` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | hash_record_only | paper_ready_figure_negative_validation | `a41a873c5237681138ac529167c519f9777f998e8b2e9cb4fbf69f230ef8867a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | lightweight_release_asset | paper_ready_figure_negative_validation | `f13c79aa53fce617fc0680a8b7a987ded70648e050592761cfc88660703a1e2f` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | lightweight_release_asset | paper_ready_figure_negative_validation | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |
| `docs/experiments/casee/results/casee_reproducibility_suite.json` | lightweight_release_asset | paper_ready_traceability | `9800e60617baf5e38e213b4a8f51e73c85d6693524955c1756c2054225ce28db` |
| `docs/experiments/casee/results/casee_validation_report.md` | lightweight_release_asset | limitations_ready_negative_validation | `b22c69da93692f5f80147f332ac1f8ee0aea1b3920584d60dcaaec4e99329c85` |
| `docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv` | lightweight_release_asset | limitations_ready_diagnostic | `58961ab3036c519f6d5665f17239c47007f2b2f34d86dc84aca139eb4bcc1a60` |
| `docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv` | lightweight_release_asset | limitations_ready_diagnostic | `dcf90ab869ee70f4d01af830b6d28653632e0f1fd2e013b9ae0f74d1a1f3c993` |
| `docs/experiments/casee/results/citylbm_manifest_output_gate.json` | lightweight_release_asset | paper_ready_manifest_traceability | `101b4273bc485d764b55215d3f45abfb10f3126c7ae61a2f4531e67118dfe4ee` |

## Claim Readiness Summary

- blocked: 2
- limitations_ready: 3
- paper_ready: 2
- weaken_claim: 1

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
- Recover the GPU runtime before additional long native FluidX3D runs; the latest `nvidia-smi` evidence reports a lost GPU.
- Complete the Visual Studio Build Tools 2022 C++ installation or continue with documented fallback build paths.

