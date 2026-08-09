# AIJ Case E Reproducibility Appendix

Generated: 2026-08-09T11:55:42.985575+00:00

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
- Recommended tag: `v0.4.0-rc33`.
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
- `casee_default_policy_gate` (passed, returncode=0): `python docs/experiments/casee/tools/casee_default_policy_gate.py`
- `citylbm_paper_results_packet` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_paper_results_packet.py`
- `citylbm_manifest_output_gate` (passed, returncode=0): `python docs/experiments/casee/tools/citylbm_manifest_output_gate.py`
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
| `CityLBM/bin/CityLBM.gha` | lightweight_release_asset | paper_ready_software_identity | `555f96b38551f40ed68783fcf7544a8b8e4393e20e0d9e5c65ab1f0b7553fee6` |
| `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md` | lightweight_release_asset | paper_ready_reproducibility | `a4e6c12999f17ebea9aaf02f91fbad48674b70f0306c294acc9ff17e184304bd` |
| `docs/experiments/casee/results/build_chain_manifest.json` | lightweight_release_asset | paper_ready_reproducibility | `f5a8057998c61564f1e953fc930ce8354052cf1f755114142fe8a67575b1bea3` |
| `docs/experiments/casee/results/build_chain_manifest.md` | lightweight_release_asset | paper_ready_reproducibility | `38ca54c97a7a03a107f3e9b0ede30e85e52984f947b4a1f2e7a48990c31d90d4` |
| `docs/experiments/casee/results/casee_default_policy_gate.json` | lightweight_release_asset | paper_ready_default_policy_boundary | `d8b49c9b8a86147015f415eaddbaef745afc46d22613c6b3f3305d6479f1ad38` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.json` | lightweight_release_asset | limitations_ready_dx1_feasibility | `07063479d98588420c3e550ff6a2fcd48d5d73db361c7cce1953e2d6879f92aa` |
| `docs/experiments/casee/results/casee_dx1_readiness_audit.md` | lightweight_release_asset | limitations_ready_dx1_feasibility | `016ad25450120caf1742bcefb0072c1a30704cc5a2e59f197699110239b6473c` |
| `docs/experiments/casee/results/casee_environment_recovery_runbook.json` | lightweight_release_asset | blocked_environment_recovery_runbook | `039be851321c898aeb68abbcd16f5eadee6d84e64000fe3ca4d391abbcfa3e11` |
| `docs/experiments/casee/results/casee_failure_mode_atlas.json` | lightweight_release_asset | limitations_ready_failure_mode_atlas | `063fcf20777136d8996121dcf58499f7c90cf486ae65417f6830f2d134537fdf` |
| `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv` | lightweight_release_asset | paper_ready_reproducibility | `9ca85047de2d818ff5ac98cdb6197b5f92c4d9dab0389f41fd778689c349edf0` |
| `docs/experiments/casee/results/casee_manuscript_results_table.json` | lightweight_release_asset | paper_ready_manuscript_results_table | `cb8d1fc815c4d99a7abd899328652a15b2e33454a37f75fd5c8b5f9b9fbd16d2` |
| `docs/experiments/casee/results/casee_manuscript_section_pack.json` | lightweight_release_asset | paper_ready_section_pack_negative_validation | `dd6314a14a97a80f145ccd0ac717825f1ec9b5bcacffcc2ceeadfb8ac9bf3c58` |
| `docs/experiments/casee/results/casee_metrics.csv` | lightweight_release_asset | limitations_ready_negative_validation | `a19e0f80d2c68afa7cc1e3fe59dd1e773f5c4e7930b381799d6bdb56e828051b` |
| `docs/experiments/casee/results/casee_official_run_preflight.json` | lightweight_release_asset | blocked_official_followup_preflight | `b1a27f11f5a943e4bd78453bd24040cfff49bb17054ce764824bce9932740c8e` |
| `docs/experiments/casee/results/casee_paper_evidence_gate.json` | lightweight_release_asset | paper_ready_traceability | `f4fed5a5a28c441962d1c879e8e814c772f5718aa346efd0945265a7a68b5dc2` |
| `docs/experiments/casee/results/casee_paper_results_figure.svg` | hash_record_only | paper_ready_figure_negative_validation | `ec5fead9978df0fc64bd8de61a508738f05f73170ed841fd4d9d0d320bc5f02a` |
| `docs/experiments/casee/results/casee_paper_results_figure_qa.json` | lightweight_release_asset | paper_ready_figure_negative_validation | `7777be3ae25b3e35fbff0cef020806c9c01818f928971f7df69fa2a904b5e451` |
| `docs/experiments/casee/results/casee_paper_results_figure_source.csv` | lightweight_release_asset | paper_ready_figure_negative_validation | `a4dadabe6de2dac38521d339d0db355d5c1ab8a37128e3cb5f044657e65eb2bb` |

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
- Use the dx=1 readiness audit before any high-resolution long run; the current audit is limitations/planning evidence only.
- Complete the Visual Studio Build Tools 2022 C++ installation or continue with documented fallback build paths.

