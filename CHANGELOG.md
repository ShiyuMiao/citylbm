# Changelog

## v0.4.0-rc31 - Manuscript section pack

- Added `casee_manuscript_section_pack.py` to generate claim-safe English Methods, Results, Diagnostics, Limitations, Software implications, Release-boundary prose, and a QA manifest from the gated Case E results table.
- Generated `casee_manuscript_section_pack.json`, `casee_manuscript_section_pack_qa.md`, and `academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md`.
- Integrated the section pack into the reproducibility suite, artifact index, paper evidence gate, paper appendix generator, cross-experiment paper results packet, and software-feedback matrix as SF014.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc31.md`.

This release candidate improves manuscript prose readiness and claim traceability only. It does not add CFD results, improve official Case E z=2 m metrics, promote diagnostic sampling to formal validation, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc30 - Grasshopper claim-gate output

- Added a `Claim Gate` (`Gate`) output to the Grasshopper `Run Simulation` component.
- The output reports the formal Case E boundary beside run status and manifest path: official `ac+N`, wind vector `(0,-1,0)`, z=2 m, 80 probes, `raw_trilinear`, and the external release-gate requirements.
- Extended `citylbm_manifest_output_gate.py`, `casee_default_policy_gate.py`, and `citylbm_software_feedback_matrix.py` to verify the new output as SF013.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc30.md`.

This release candidate improves UI-level claim safety and software traceability only. It does not add CFD results, improve official Case E z=2 m metrics, promote diagnostic sampling to formal validation, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc29 - Manifest formal accuracy gate contract

- Added `formal_accuracy_gate` to generated `citylbm_run_manifest.json` files so each CityLBM run records the formal v0.4.0 release-gate contract.
- The manifest contract records official Case E `ac+N`, wind vector `(0, -1, 0)`, z=2 m, 80 probes, `raw_trilinear`, required Case A smoke regression, Rhino/GHA load verification, and external `release_gate.json` dependency.
- Extended `citylbm_manifest_output_gate.py`, `casee_default_policy_gate.py`, and `citylbm_software_feedback_matrix.py` to verify the new manifest gate contract as SF012.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc29.md`.

This release candidate improves software traceability and misuse prevention only. It does not add CFD results, improve official Case E z=2 m metrics, promote diagnostic sampling to formal validation, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc28 - Paper results figure bundle

- Added `casee_paper_results_figure.py` to export the Case E manuscript results table as an editable SVG, PNG preview, source CSV, JSON QA manifest, and Markdown QA note.
- Integrated the figure bundle into the reproducibility suite, artifact index, paper evidence gate, reproducibility appendix command trace, and software-feedback matrix as SF011.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc28.md`.

This release candidate improves manuscript figure readiness only. It does not add CFD results, improve official Case E z=2 m metrics, promote diagnostic sampling to formal validation, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc27 - Manuscript results table boundary

- Added `casee_manuscript_results_table.py` to generate a paper-facing Case E results table with formal, diagnostic, limitations, traceability, and release-boundary rows.
- Generated `casee_manuscript_results_table.json`, `casee_manuscript_results_table.csv`, and `casee_manuscript_results_table.md`.
- Added paper-readiness metadata to generated `citylbm_run_manifest.json`: `paper_readiness`, `paper_allowed_uses`, and `paper_forbidden_claims`.
- Extended the manifest-output gate, paper evidence gate, artifact index, reproducibility suite, appendix command trace, and software-feedback matrix so the result table and manifest paper boundary are audited.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc27.md`.

This release candidate improves manuscript readiness and software traceability only. It does not add CFD results, improve official Case E z=2 m metrics, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc26 - Manifest path traceability output

- Added a `Manifest Path` (`Man`) output to the Grasshopper `Run Simulation` component so users can directly trace each run to `citylbm_run_manifest.json`.
- Added `citylbm_manifest_output_gate.py` to verify the component output, generated manifest path, and claim-boundary fields.
- Generated `citylbm_manifest_output_gate.json`, `citylbm_manifest_output_gate.csv`, and `citylbm_manifest_output_gate.md`.
- Integrated the manifest-output gate into the reproducibility suite, artifact index, paper evidence gate, reproducibility appendix command trace, and software feedback matrix as SF009.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc26.md`.

This release candidate improves software and paper traceability only. It does not add CFD results, improve official Case E z=2 m metrics, prove Rhino loaded the new GHA, or permit formal `v0.4.0`.

## v0.4.0-rc25 - Software feedback matrix

- Added `citylbm_software_feedback_matrix.py` to convert Experiments 1-3 findings into CityLBM default-quality gates, formal protocol defaults, diagnostic switches, blocked follow-up work, and paper-only interpretation layers.
- Generated `citylbm_software_feedback_matrix.json`, `citylbm_software_feedback_matrix.csv`, and `citylbm_software_feedback_matrix.md`.
- Integrated the matrix into the reproducibility suite, artifact index, paper evidence gate, and reproducibility appendix command trace.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc25.md`.

This release candidate improves software-feedback traceability only. It does not add new CFD results, improve official Case E z=2 m metrics, or permit formal `v0.4.0`.

## v0.4.0-rc24 - Cross-experiment paper results packet

- Added `citylbm_paper_results_packet.py` to consolidate Experiment 1, Experiment 2, and Experiment 3 evidence into manuscript-ready, limitations-ready, and blocked rows.
- Generated `citylbm_paper_results_packet.json`, `citylbm_paper_results_packet.csv`, and `citylbm_paper_results_packet.md`.
- Integrated the packet into the one-command reproducibility suite, artifact index, paper evidence gate, and reproducibility appendix command trace.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc24.md`.

This release candidate improves paper organization and cross-experiment claim control only. It does not add new CFD results, improve the official Case E z=2 m metric, or permit formal `v0.4.0`.

## v0.4.0-rc23 - Default policy gate

- Added `casee_default_policy_gate.py` to verify that CityLBM defaults remain aligned with the formal AIJ Case E protocol while diagnostic controls remain opt-in.
- Generated `casee_default_policy_gate.json`, `casee_default_policy_gate.csv`, and `casee_default_policy_gate.md`.
- Integrated the default-policy gate into the reproducibility suite, artifact index, paper evidence gate, and reproducibility appendix command trace.
- Updated release evidence pointers to `docs/releases/v0.4.0-rc23.md`.

This release candidate improves claim-boundary and software-policy traceability only. It does not change the official Case E metric or permit formal `v0.4.0`.

## v0.4.0-rc22 - Failure-mode atlas

- Added `casee_failure_mode_atlas.py` to synthesize audited Case E diagnostics into failure-mode rows for metric gate failure, underprediction bias, probe sampling sensitivity, near-wall/solid-corner risk, spatial-alignment audit, and runtime preflight blockers.
- Generated `casee_failure_mode_atlas.json`, `casee_failure_mode_atlas.csv`, `casee_failure_mode_atlas.md`, and `casee_failure_mode_atlas.png`.
- Integrated the atlas into the one-command reproducibility suite, artifact index, paper evidence gate, and reproducibility appendix.
- Kept all atlas claims in the limitations/software-feedback boundary; no diagnostic sampling mode is promoted to the formal official z=2 m result.

This release candidate improves manuscript-ready limitations evidence and software-feedback traceability only. It does not change the official Case E metric or permit formal `v0.4.0`.

## v0.4.0-rc21 - Environment recovery runbook

- Added `casee_environment_recovery_runbook.py` to turn the current GPU, VS C++ and Rhino/GHA load blockers into ordered recovery steps with verification commands.
- Generated `casee_environment_recovery_runbook.json`, `casee_environment_recovery_runbook.csv`, and `casee_environment_recovery_runbook.md`.
- Recorded workspace build-cache cleanup candidates and showed that they are too small to solve the C: drive VS installer-space blocker by themselves.
- Integrated the recovery runbook into the one-command reproducibility suite, artifact index, paper evidence gate, and reproducibility appendix.

This release candidate improves environment recovery traceability only. It does not delete files, install tools, run new CFD, change the official Case E metric, or permit formal `v0.4.0`.

## v0.4.0-rc20 - Official follow-up preflight gate

- Added `casee_official_run_preflight.py` to combine official-data, 80-probe protocol, CityLBM build, plugin identity, Rhino/GHA loading, .NET, FluidX3D, GPU runtime, VS C++ and Case A smoke-regression checks.
- Generated `casee_official_run_preflight.json`, `casee_official_run_preflight.csv`, and `casee_official_run_preflight.md`.
- Integrated the preflight gate into the one-command reproducibility suite.
- Extended the artifact index and paper evidence gate so the preflight gate and rc20 release note are required traceability artifacts.

This release candidate makes the next long official z=2 m run schedulable only after the real runtime blockers are cleared. It does not change the official Case E metric or permit formal `v0.4.0`.

## v0.4.0-rc19 - Rhino/GHA load gate

- Added `rhino_gha_load_gate.py` to audit whether Rhino/Grasshopper has loaded the tracked `CityLBM/bin/CityLBM.gha` rather than an older installed copy.
- Generated fail-closed `rhino_gha_load_gate.json` and `rhino_gha_load_gate.md`; without a real manual manifest and evidence artifacts, `rhino_loaded_new_gha` remains false.
- Integrated the Rhino/GHA load gate into the one-command reproducibility suite.
- Extended the artifact index and paper evidence gate so the Rhino/GHA load gate and rc19 release notes are required traceability artifacts.

This release candidate improves software-load traceability only. It does not change the official z=2 m Case E metric or permit formal `v0.4.0`.

## v0.4.0-rc18 - Next experiment runbook

- Added `casee_next_experiment_runbook.py` to generate a command matrix for the next official z=2 m Case E follow-up cycle.
- Generated `casee_next_experiment_runbook.json`, `casee_next_experiment_runbook.csv`, and `casee_next_experiment_runbook.md`.
- Integrated the runbook into the one-command reproducibility suite.
- Extended the artifact index and paper evidence gate so the runbook and rc18 release notes are required traceability artifacts.

This release candidate makes the next accuracy-improvement attempts auditable before execution. It does not add a solver result or change the official metric.

## v0.4.0-rc17 - Blocker remediation plan

- Added `casee_blocker_remediation_plan.py` to convert the current release-gate, build-chain, and run-matrix state into machine-readable blocker actions.
- Generated `casee_remaining_blockers.json`, `casee_remaining_blockers.csv`, and `casee_remaining_blockers.md`.
- Integrated the blocker remediation plan into the one-command reproducibility suite.
- Extended the artifact index and paper evidence gate so the remaining-blocker plan and rc17 release notes are required traceability artifacts.

This release candidate documents the exact external work needed before another official z=2 m accuracy run can support stronger claims. It does not change the official metric or permit formal `v0.4.0`.

## v0.4.0-rc16 - Paper reproducibility appendix

- Added `paper_appendix_generator.py` to generate Chinese and English AIJ Case E reproducibility appendices from the release gate, reproducibility suite, artifact index, claim matrix, paper evidence gate, and plugin identity gate.
- Generated `casee_v04_reproducibility_appendix_en.md`, `casee_v04_reproducibility_appendix_zh.md`, and `casee_paper_appendix_manifest.json`.
- Integrated the appendix generator into the one-command reproducibility suite.
- Extended the artifact index and paper evidence gate so the appendix and rc16 release notes are required traceability artifacts.

This improves paper reproducibility and reviewer traceability only. It does not change the official z=2 m Case E metric, and formal `v0.4.0` remains blocked.

## v0.4.0-rc15 - One-command Case E reproducibility suite

- Added `reproducibility_suite.py` to run the lightweight Case E evidence chain in a single command.
- Generated `casee_reproducibility_suite.json` and `casee_reproducibility_suite.md`.
- The suite rebuilds CityLBM, synchronizes the tracked `CityLBM.gha`, reruns Case E audit outputs, regenerates manuscript and artifact evidence, and records the formal release gate as an expected blocker while official z=2 m R2 remains negative.

This makes the current negative-validation and limitations evidence easier to reproduce for paper review. It is not a formal accuracy pass.

## v0.4.0-rc14 - Artifact index for paper and release traceability

- Added `artifact_index.py` to generate a hash-indexed Case E artifact catalogue for paper appendices and lightweight release assets.
- Generated `casee_artifact_index.csv`, `casee_artifact_index.json`, and `casee_artifact_index.md`.
- Extended `paper_evidence_gate.py` so manuscript claim safety also requires the artifact index to contain key release and paper evidence files.
- Updated plugin identity and paper evidence gates to point at the current rc14 release notes.

This improves evidence traceability only. It does not change the official z=2 m Case E metrics, and formal `v0.4.0` remains blocked.

## v0.4.0-rc13 - Plugin identity and paper-gate alignment

- Updated the Grasshopper plugin metadata from the old `0.1.0` WIP identity to the `0.4.0-rc` accuracy-diagnostic line.
- Kept `AssemblyVersion` numeric as `0.4.0.0` while the public plugin `Version` reports `0.4.0-rc`; this avoids implying that the formal `v0.4.0` gate has passed.
- Added a release note for the current rc line and updated README pointers to the paper evidence gate.

Status remains unchanged:

- Official z=2 m metrics: MAE = 21.111 pp, R2 = -2.006330, Pearson = 0.115756.
- Formal `v0.4.0` is still blocked by the official metric gate and unverified Rhino/Grasshopper loading of the new GHA.
- Paper-ready claims remain limited to protocol reproducibility, build/workflow evidence, negative validation, and limitations diagnostics.

## v0.4.0-rc12 - Paper evidence gate and claim-safe manifests

- Added `paper_evidence_gate.py` to audit the release gate, Case E claim matrix, and manuscript draft text for overstated success claims.
- Generated `casee_paper_evidence_gate.json` and `casee_paper_evidence_gate.md`.
- Added claim-boundary fields to `citylbm_run_manifest.json` generation so diagnostic settings are explicitly marked as non-formal accuracy evidence.

The paper evidence gate passes because the manuscript materials stay within the current negative-validation evidence boundary. This is not an accuracy pass.

## v0.4.0-rc11 - Paper-facing Case E text

- Added Chinese and English Case E Results/Limitations draft sections under `academic-paper-writer/paper-drafts/`.
- Added a Case E claim-control sheet separating paper-ready, limitations-ready, weakened diagnostic, and blocked claims.
- Kept diagnostic sampling modes and z-origin changes out of the formal official z=2 m result.

## v0.4.0-rc10 - Manuscript claim readiness matrix

- Added `manuscript_evidence_summary.py` to convert Case E outputs into a manuscript-facing claim matrix.
- Generated `casee_manuscript_claim_matrix.csv`, `casee_manuscript_claim_matrix.json`, and `casee_manuscript_evidence_summary.md`.
- Updated the Case E validation report to summarize claim readiness counts.

Current claim boundary:

- `paper_ready`: protocol definition and build/workflow non-regression evidence.
- `limitations_ready`: negative formal Case E validation, near-wall/probe-risk concentration, and diagnostic sampling sensitivity.
- `weaken_claim`: z-center alignment improved MAE/Pearson but did not make R2 positive.
- `blocked`: formal `v0.4.0`, predictive accuracy, fully ready VS C++/GPU native validation chain.

Official z=2 m metrics remain unchanged: MAE = 21.111 pp, R2 = -2.006330, Pearson = 0.115756.

## v0.4.0-rc9 - Diagnostic z-origin switch and build-chain audit

- Added a default-off `Diagnostic Z Origin Offset` (`zOff`) input to the Grasshopper `Run Simulation` component.
- Propagated `DiagnosticZOriginOffsetM` through `SimulationSettings`, generated FluidX3D setup code, and `citylbm_run_manifest.json`.
- Updated Case E probe-protocol risk metadata to compute lattice z placement from the effective diagnostic origin.
- Added `build_chain_audit.py` and `build_chain_manifest.json` to record .NET SDK, FluidX3D, Visual Studio Build Tools C++, GPU runtime, disk space, and installation-attempt status.

Current status:

- CityLBM Release build passes with 0 errors and existing nullable warnings.
- .NET SDK 8.0.423 and the existing FluidX3D binary are available.
- Visual Studio Build Tools 2022 C++ remains blocked: `winget` returned exit code 1602, the bootstrapper log indicates a possible declined UAC prompt, and C: has insufficient free space for the VS precheck.
- Official z=2 m metrics are unchanged from the latest z-center run: MAE = 21.111 pp, R2 = -2.006330, Pearson = 0.115756.

This improves reproducibility and diagnostic control but still does not support formal `v0.4.0` or a predictive-accuracy claim.

## v0.4.0-rc8 - Z-center lattice diagnostic

- Added `origin_z_offset_m` support to the native AIJ Case E generator.
- Completed a dx=2 m, one effective-ground cell, `origin_z_offset_m=1.0`, `nu_lbm=0.001` z-center diagnostic for 48000 steps.
- Extended the voxel/probe audit so the reported lattice placement matches shifted vertical origins.
- Updated the Case E validation report to include z-center probe-mode and voxel/probe diagnostic sections.

Current diagnostic finding:

- Formal `raw_trilinear` official z=2 m: MAE = 21.111 pp, R2 = -2.006330, Pearson = 0.115756.
- Best diagnostic mode: `vertical_valid_above`, MAE = 16.041 pp, R2 = -0.554717, Pearson = 0.336940.
- Z-center low protocol-risk probes: n = 47, raw MAE = 12.435 pp.
- Z-center high protocol-risk probes: n = 14, raw MAE = 34.589 pp.

This improves the diagnostic evidence but still does not support formal `v0.4.0` or a predictive-accuracy claim.

## v0.4.0-rc7 - Voxel/probe protocol audit

- Added a voxel/probe protocol audit for AIJ Case E official z=2 m probes against the scaled STL and dx=2 m effective-ground grid.
- Added CityLBM run-manifest protocol-risk metadata for Case E, including lattice z-layer placement and an explicit rule that `z_plus_half` is not a formal substitute.
- Updated the Case E validation report to include voxel/probe risk groups.

Current diagnostic finding:

- Low protocol-risk probes: n = 25, raw MAE = 12.932 pp.
- Moderate protocol-risk probes: n = 36, raw MAE = 27.162 pp.
- High protocol-risk probes: n = 19, raw MAE = 32.454 pp.
- z_plus_half diagnostic MAE improves the all-probe average from 23.972 pp to 21.217 pp, but official R2 remains negative.

This supports near-wall/probe-protocol limitations and software risk reporting, not formal predictive accuracy.

## v0.4.0-rc6 - Completed probe-mode diagnostic run

- Completed the native dx=2 m, effective-ground one-cell, `nu_lbm=0.001` probe-mode diagnostic run for 48000 steps.
- Recorded the full run log, probe CSV, audit manifest, mode metrics, solid-corner group metrics, and probe-mode figure.
- The formal `raw_trilinear` official z=2 m metric remains unchanged and below the release gate.

Probe-mode diagnostic results:

- `raw_trilinear` formal: MAE = 23.972 pp, R2 = -2.311768, Pearson = 0.071789.
- `vertical_valid_above`: MAE = 21.356 pp, R2 = -1.637050, Pearson = 0.118127.
- `z_plus_half`: MAE = 21.217 pp, R2 = -1.626431, Pearson = 0.187068.

These results strengthen the near-wall/probe-protocol limitation, but they still do not support a predictive-accuracy claim or formal `v0.4.0`.

## v0.4.0-rc5 - Probe-mode runner and spatial alignment diagnostic

- Added a native Case E probe-mode diagnostic runner that preserves formal `raw_trilinear` output while also writing `nearest_valid`, `fluid_weighted`, `vertical_valid_above`, and `z_plus_half` diagnostic columns for future full runs.
- Added a compile-only probe-mode audit manifest so the new native runner is traceable without claiming new accuracy metrics.
- Added a spatial alignment diagnostic for the best existing official z=2 m run.

Current diagnostic finding:

- Simple x/y flips, x/y swaps, and 90-degree coordinate transforms do not make official z=2 m R2 positive.
- Identity remains the best Pearson transform at Pearson = 0.071789, while the best R2 transform is still negative at R2 = -2.111059.
- This points away from a simple coordinate-convention failure and toward near-wall sampling, wall modeling, inlet turbulence, voxelization, or probe protocol fidelity.

Formal `v0.4.0` remains blocked because official z=2 m R2 is still negative and Rhino/Grasshopper loading of the new GHA is not independently verified.

## v0.4.0-rc4 - Case A smoke regression gate

- Added a reproducible AIJ Case A smoke-regression audit under `docs/experiments/casea/`.
- Generated and ran a native FluidX3D Case A smoke case with dx = 3.5 m and 2000 steps on this machine.
- Recorded the completed run log, compile log, generated case manifest, artifact hashes, and external VTK hashes without committing large VTK files.
- Wired the Case A smoke-regression status into the Case E release gate.

The release gate still blocks formal `v0.4.0`:

- Case A smoke regression now passes and can be used as a workflow non-regression guard.
- Best newly-run Case E official z=2 m result remains MAE = 23.972 pp, R2 = -2.311768, Pearson = 0.071789.
- Rhino/Grasshopper loading of the new GHA is still not independently verified.
- Case A smoke is not an accuracy-validation result and does not justify a formal predictive-accuracy claim.

## v0.4.0-rc3 - Probe-risk audit and nu diagnostic plugin switch

- Added automatic solid-corner metadata propagation in `casee_audit.py`; native probe CSVs with `solid_corner_neighbors_max` now produce probe residual risk labels and `casee_solid_corner_group_metrics.csv`.
- Updated `casee_validation_report.md` and XLSX output to include solid-corner group metrics.
- Fixed the release-gate recommendation so an existing HEAD rc tag, such as `v0.4.0-rc2`, is reported instead of always falling back to `v0.4.0-rc1`.
- Added the default-off Grasshopper `Diagnostic LBM Nu Override` input for reproducible `nu_lbm` sensitivity diagnostics without changing default solver behavior.

Case E remains below the formal accuracy gate:

- Best newly-run official z=2 m result remains MAE = 23.972 pp, R2 = -2.311768, Pearson = 0.071789.
- Solid-corner grouping shows 25 probes with zero solid interpolation neighbors have MAE = 12.932 pp and Pearson = 0.356584, while probes with 2 or 4 solid neighbors remain much worse.
- This supports a near-wall/probe-protocol limitation claim, not a predictive-accuracy claim.

## v0.4.0-rc1 - Native Case E diagnostic continuation

- Added a native FluidX3D Case E generator for official `ac+N`, scale factor 250, AF_caseE profile ingestion, binary STL conversion, and direct `casee_probe_time_mean.csv` output for the 80 official z=2 m probes.
- Completed newly-run native FluidX3D dx=3 m and dx=2 m Case E runs on this machine.
- Added diagnostic effective-ground offset and `nu_lbm` controls to the native Case E generator; these are not CityLBM defaults.
- Added a default-off Grasshopper input, `Diagnostic LBM Nu Override`, so native `nu_lbm` sensitivity can be reproduced from CityLBM case generation without changing generic defaults.
- Added MinGW/g++ fallback compilation in `FluidX3DInterface` so CityLBM can build FluidX3D when MSBuild is unavailable.
- Rebuilt CityLBM successfully with local .NET SDK 8.0.423; the generated GHA and build log are recorded in the Case E environment manifest. The build has 0 errors and existing nullable warnings.

Case E official z=2 m metrics remain below the formal accuracy gate:

- Best newly-run result so far: diagnostic dx=2 m, one effective-ground offset cell, `nu_lbm=0.001`, 48000 steps, spinup 12000, raw_trilinear, n=80.
- MAE = 23.972 percentage points, RMSE = 29.095 percentage points, bias = -20.833 percentage points.
- R2 = -2.311768 and Pearson = 0.071789.

Known blockers:

- Do not create the formal `v0.4.0` tag: the official z=2 m metric gate fails.
- Rhino/Grasshopper loading of the new GHA and Case A smoke regression are still not verified in this run.
- The dx=2 implementation currently reads full velocity fields for probe sampling; a true GPU-side probe-only reducer is needed before scaling to longer/high-resolution sweeps.
- Remaining accuracy risks are near-wall treatment, rough/effective ground modeling, inlet turbulence/digital-filter fidelity, LBM viscosity/Reynolds matching, voxelization alignment, and official probe sampling at solid corners.

## v0.3.0-rc1 - AIJ Case E accuracy diagnostic candidate

- Added source-level plugin optimization from Experiments 1-3: an explicit AIJ Case E preset input, Case E protocol policy, AF_caseE inlet-profile generation, lattice velocity cap scaling, and per-case run manifest output.
- Added an AIJ Case E `ac+N` preset for official z=2 m validation.
- Downloaded the official Zenodo Case E files into `docs/experiments/casee/official_data/` and recorded size, SHA256, Zenodo MD5, download time, and source URL in `docs/experiments/casee/data_manifest.csv`.
- Added the Case E protocol, native FluidX3D run matrix, and evidence inventory.
- Added `casee_audit.py` to generate official 80-probe filters, AF inlet-profile audits, residual tables, XLSX/PNG outputs, environment manifests, validation reports, and release-gate JSON.
- Added `release_gate.py`, which fails closed unless the formal v0.3.0 criteria pass.
- Added CityLBM config entries for Case E preset constants and diagnostic-only sampling/wall-ground switches.

Known blockers:

- The current machine has no .NET SDK/MSBuild command-line environment, so CityLBM source build is blocked.
- Native FluidX3D execution is blocked because `FluidX3D`, `nvidia-smi`, `nvcc`, and Visual Studio C++ build tools are not available from the command line.
- No formal v0.3.0 tag should be created until official z=2 m metrics are generated from native dx=3 m and dx=2 m runs and the full release gate passes.
