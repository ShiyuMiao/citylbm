# CityLBM Software Feedback Matrix

Generated: 2026-08-11T03:13:38.141429+00:00

## Verdict

- Matrix passed: True
- Feedback rows: 43
- All source paths exist: True
- No forbidden default promotion: True
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False

## Decision Counts

- application_workflow_policy: 1
- blocked_default_accuracy_upgrade: 1
- blocked_followup_run: 3
- build_chain_recovery_gate: 1
- calibration_leakage_guard_no_default_promotion: 1
- completed_candidate_no_default_promotion: 1
- default_quality_gate: 1
- diagnostic_ablation_no_default_promotion: 1
- diagnostic_switch: 3
- followup_sweep_plan: 1
- formal_protocol_default: 1
- gpu_runtime_failfast_gate: 1
- inlet_turbulence_diagnostic_no_default_promotion: 1
- local_orphan_candidate_no_default_promotion: 1
- low_cost_regression_no_default_promotion: 1
- manual_rhino_load_evidence_kit: 1
- manual_rhino_load_manifest_schema_gate: 1
- packaged_gha_identity_component_gate: 1
- paper_claim_support_gate: 1
- paper_figure_output: 1
- paper_interpretation_layer: 1
- paper_provenance_ledger: 1
- paper_release_asset_manifest: 1
- paper_traceability_output: 2
- portable_plugin_build_script: 1
- portable_toolchain_activation_gate: 1
- rerun_reproducibility_guard: 1
- residual_structure_no_default_promotion: 1
- residual_target_hook_no_default_promotion: 1
- runtime_decomposition_sensitivity_no_default_promotion: 1
- software_gha_staging_audit: 1
- software_identity_component: 1
- software_publication_gate_output: 1
- software_publication_readiness_contract: 1
- software_traceability_gate: 1
- software_traceability_output: 3

## Feedback Rows

| id | experiment | decision | status | default? | finding |
|---|---|---|---|---:|---|
| `SF001` | Experiment 1 / AIJ Case A | default_quality_gate | implemented_as_release_gate_requirement | True | Case A smoke regression guards the Rhino/GH -> FluidX3D -> VTK workflow but is not accuracy validation. |
| `SF002` | Experiment 2 / AIJ Case E | blocked_default_accuracy_upgrade | formal_release_blocked | False | Official z=2 m validation remains negative: MAE=21.111408125 pp, R2=-2.006330362229977, Pearson=0.11575649438573923. |
| `SF003` | Experiment 2 / AIJ Case E | formal_protocol_default | implemented | True | The formal Case E protocol must remain z=2 m, 80 ac+N probes, and raw_trilinear sampling. |
| `SF004` | Experiment 2 / AIJ Case E | diagnostic_switch | implemented_default_off | False | Diagnostic nu_lbm sensitivity is useful for investigation but has not produced a formal official z=2 m pass. |
| `SF005` | Experiment 2 / AIJ Case E | diagnostic_switch | implemented_default_off | False | Vertical-origin and probe sampling diagnostics expose near-wall/protocol sensitivity but remain non-formal. |
| `SF006` | Experiment 2 / AIJ Case E | blocked_followup_run | blocked_until_external_recovery | False | The next official Case E run is blocked by runtime and load-identity gates. |
| `SF007` | Experiment 3 / TUM2TWIN digital-twin application | application_workflow_policy | paper_ready_workflow_guidance | True | TUM2TWIN layers are separated into visual reference, semantic/collision geometry and CFD/LBM simulation inputs. |
| `SF008` | Experiment 3 / TUM2TWIN digital-twin application | paper_interpretation_layer | paper_ready_with_boundary | False | Basic morphology variables are interpretable screening descriptors; sector enclosure ranks above single-building footprint/elongation. |
| `SF009` | CityLBM traceability layer | software_traceability_output | implemented | True | Run Simulation exposes the generated citylbm_run_manifest.json path as a Grasshopper output for direct reviewer tracing. |
| `SF010` | Experiment 2 / AIJ Case E paper-readiness layer | paper_traceability_output | implemented | True | Run manifests and manuscript result rows now record allowed paper uses and forbidden accuracy claims. |
| `SF011` | Experiment 2 / AIJ Case E paper-figure layer | paper_figure_output | implemented | True | The manuscript result table is exported as an editable SVG/PNG/source-CSV figure bundle with QA checks. |
| `SF012` | Experiment 2 / AIJ Case E manifest gate contract | software_traceability_output | implemented | True | Generated run manifests now encode the formal v0.4.0 accuracy-gate contract and keep manifest-only accuracy claims blocked. |
| `SF013` | Experiment 2 / AIJ Case E Grasshopper claim boundary | software_traceability_output | implemented | True | Run Simulation now exposes a Claim Gate output so users can see the formal accuracy boundary beside run status and manifest path. |
| `SF014` | Experiment 2 / AIJ Case E manuscript prose layer | paper_traceability_output | implemented | True | The generated section pack converts gated Case E rows into Methods, Results, Diagnostics, Limitations, Software implications, and Release-boundary prose with explicit evidence notes. |
| `SF015` | Build-chain recovery / Case E follow-up readiness | blocked_followup_run | blocked_vs_cpp_build_tools | False | The current build-chain audit records .NET and FluidX3D as available, GPU runtime as blocked, and VS Build Tools C++ as blocked after a winget BuildTools attempt exited 1602 with UAC-related bootstrapper evidence. |
| `SF033` | CityLBM portable plugin build script | portable_plugin_build_script | implemented_portable_plugin_build | True | The CityLBM build script now supports -DotNetPath, CITYLBM_DOTNET, the audited local E: build-chain .NET SDK, and -NoPause so the Grasshopper plugin can be rebuilt on the new computer even when dotnet is not on PATH. |
| `SF016` | Experiment 2 / AIJ Case E dx=1 follow-up readiness | blocked_followup_run | blocked_until_user_confirmed_dx1_dry_run | False | The dx=1 m high-resolution official follow-up is a high-risk long-run candidate: readiness=high_risk_blocked_until_dry_run, memory_headroom_ok=False, moderate required per GPU=13.79 GiB, minimum free GPU memory=0.0 GiB. |
| `SF017` | Experiment 2 / AIJ Case E wall and roughness follow-up | diagnostic_switch | implemented_default_off | False | Near-wall underprediction and solid-corner diagnostics justify a default-off wall/roughness follow-up interface, but the official z=2 m raw_trilinear metric has not improved enough to promote any wall model as a default accuracy setting. |
| `SF018` | Experiment 2 / AIJ Case E manifest schema traceability | software_traceability_gate | implemented_schema_gate | False | Generated run manifests need a stable reader-facing schema so Case E protocol fields, diagnostic substitute blockers, and paper-forbidden claim classes can be audited without reinterpreting solver logs. |
| `SF020` | Experiment 2 / AIJ Case E z-center rerun | rerun_reproducibility_guard | baseline_failure_reproduced | False | A newly-run 48000-step rerun of the currently compiled z-center Case E setup reproduced the same official z=2 m raw_trilinear failure metric, so repeating the baseline is not an accuracy-improvement path. |
| `SF021` | Experiment 2 / AIJ Case E C002 longer mean | completed_candidate_no_default_promotion | candidate_completed_no_improvement | False | The completed 96000-step C002 longer-time-mean candidate worsened the official z=2 m raw_trilinear metric, so longer averaging alone should not be promoted as a CityLBM accuracy fix. |
| `SF022` | Experiment 2 / AIJ Case E C003 z-origin ablation | diagnostic_ablation_no_default_promotion | zorigin_sensitivity_confirmed | False | The completed C003 no-z-center ablation worsened the official z=2 m raw_trilinear metric relative to the z-center baseline, so z-origin alignment remains a diagnostic sensitivity rather than a validated default model. |
| `SF023` | Experiment 2 / AIJ Case E C004 dx=3 control | low_cost_regression_no_default_promotion | dx3_control_completed_positive_correlation | False | The completed C004 dx=3 low-cost control kept positive Pearson correlation but worsened MAE and R2, so it is useful as a quick protocol/direction regression rather than an accuracy default. |
| `SF024` | Experiment 2 / AIJ Case E C005 domain decomposition | runtime_decomposition_sensitivity_no_default_promotion | decomposition_sensitivity_detected | False | The completed C005 dx=2 m 4x1x1 domain-decomposition ablation improved MAE and R2 versus the z-center baseline, but R2 stayed negative, Pearson decreased, and reproducibility-consistency thresholds failed. |
| `SF025` | Experiment 2 / AIJ Case E C008-C015 inlet turbulence and SGS ablation | inlet_turbulence_diagnostic_no_default_promotion | inlet_turbulence_candidate_improved_but_blocked | False | The C008-C015 AF-k synthetic full-plane inlet and no-SGS ablation candidates produced the largest official-height improvement so far, with best MAE=13.7856467875 pp, R2=-0.22984501828340775, and Pearson=0.31496559664177526, but R2 remained negative. |
| `SF026` | Experiment 2 / AIJ Case E C014 residual structure | residual_structure_no_default_promotion | residual_structure_identifies_next_physics_target | False | The C014 residual audit shows velocity-ratio range compression: high official-speed probes remain underpredicted, downstream R2=-0.5663250697292279, and even a post-hoc affine upper bound only reaches R2=0.09920332706790935. |
| `SF027` | Experiment 2 / AIJ Case E C016 residual-target software hook | residual_target_hook_no_default_promotion | implemented_default_off | False | The C014 residual-structure audit is now represented in CityLBM as a default-off residual-target diagnostic hook (residT/residS) for reproducible follow-up planning, without changing default solver behavior. |
| `SF028` | Experiment 2 / AIJ Case E C016 calibration-leakage guard | calibration_leakage_guard_no_default_promotion | implemented_protocol_guard | False | C016 residual-target work is now protected by a protocol-risk guard: C014 residuals may motivate pre-registered physics hypotheses, but the official 80 RS_caseE targets cannot be used for post-hoc fitting and then reported as validation. |
| `SF029` | Experiment 2 / AIJ Case E solver-run provenance ledger | paper_provenance_ledger | implemented_paper_traceability | True | The Case E solver-result evidence now has a consolidated provenance ledger mapping each official-height candidate to its command/config, CSV, log, metric values, evidence type, and claim boundary. |
| `SF030` | Experiment 2 / AIJ Case E manuscript claim support | paper_claim_support_gate | implemented_paper_claim_boundary | True | The Case E manuscript claim matrix is now checked by a claim-support gate that separates methods/protocol claims, negative validation, limitations-only diagnostics, reproducibility context, and blocked formal-release claims. |
| `SF031` | CityLBM manifest publication-readiness contract | software_publication_readiness_contract | implemented_manifest_publication_boundary | True | Generated citylbm_run_manifest.json files now include a publication_readiness_contract that records required external gates and artifacts before a generated case can support manuscript use. |
| `SF032` | CityLBM Run Simulation publication gate output | software_publication_gate_output | implemented_publication_gate_output | True | Run Simulation now exposes a Publication Gate output beside the Claim Gate so Grasshopper users see manuscript-readiness dependencies at the point of case generation. |
| `SF034` | Case E release asset manifest | paper_release_asset_manifest | implemented_release_asset_manifest | True | The release upload asset manifest separates compiled GHA, validation reports, CSV/XLSX summaries, figures, data/environment manifests, and paper gates from raw or large hash-only files. |
| `SF035` | CityLBM VS C++ Build Tools recovery gate | build_chain_recovery_gate | implemented_vs_cpp_recovery_gate | True | The Windows native C++ build-chain recovery path is now scripted and audited, with explicit guards for manual -Install use, elevation, system-drive free space, winget availability, and required VC workload components. |
| `SF036` | CityLBM GHA staging/install audit | software_gha_staging_audit | implemented_gha_staging_audit | True | The tracked CityLBM.gha can now be audited against common Grasshopper Libraries locations, with exact SHA256 matching and an explicit manual copy command before any Rhino load claim is made. |
| `SF037` | CityLBM Rhino/GHA load evidence kit | manual_rhino_load_evidence_kit | implemented_rhino_load_evidence_kit | True | Rhino/Grasshopper load verification now has a fail-closed evidence kit that detects Rhino, checks the staged GHA hash, and writes a manual manifest template without claiming that Rhino loaded the plugin. |
| `SF038` | CityLBM Plugin Identity Grasshopper component | software_identity_component | implemented_plugin_identity_component | True | CityLBM now exposes a Plugin Identity component that reports the loaded plugin version, assembly version, GHA path, SHA256, manifest template, and explicit claim boundary inside Grasshopper. |
| `SF039` | CityLBM packaged GHA identity-component gate | packaged_gha_identity_component_gate | implemented_packaged_gha_identity_component_gate | True | The tracked packaged CityLBM.gha is now audited for Plugin Identity component markers, including the component name, GHA SHA256 output, manifest-template output, GUID, and accuracy-claim boundary. |
| `SF040` | CityLBM portable .NET / FluidX3D / MinGW toolchain activation | portable_toolchain_activation_gate | implemented_portable_toolchain_activation_gate | True | The local portable toolchain can now be activated and audited without changing system PATH: portable .NET, the existing FluidX3D binary, and MinGW/g++ are verified while VS C++ and GPU runtime remain explicit blockers. |
| `SF041` | CityLBM GPU runtime fail-fast gate | gpu_runtime_failfast_gate | implemented_gpu_runtime_failfast_gate | True | Long native FluidX3D scheduling is now guarded by a newly-run nvidia-smi fail-fast gate. When the GPU reports a lost device, the gate passes only by keeping long FluidX3D runs blocked. |
| `SF042` | CityLBM Rhino/GHA manual load manifest schema gate | manual_rhino_load_manifest_schema_gate | implemented_rhino_load_manifest_schema_gate | True | The manual Rhino/GHA load manifest now has a schema gate that checks required fields, expected plugin version, expected GHA SHA256, and evidence-artifact requirements without treating the template itself as load evidence. |
| `SF043` | Experiment 2 / local orphan native candidate CSV audit | local_orphan_candidate_no_default_promotion | implemented_orphan_candidate_csv_audit | False | Local untracked native candidate CSVs are now inventoried by hash and metric summary before any paper use. The best raw candidate remains negative, and no candidate is formal-result eligible because complete run logs are absent. |
| `SF019` | Experiment 2 / AIJ Case E official z=2 m follow-up planning | followup_sweep_plan | planned_candidate_matrix | False | The candidate sweep plan converts the current negative official metric and failure-mode evidence into prioritized follow-up runs with explicit commands, blockers, pass conditions, and default-promotion boundaries. |

## Paper Boundary

| id | paper use | limitations |
|---|---|---|
| `SF001` | Use as workflow non-regression evidence. | Do not use as wind-field accuracy validation. |
| `SF002` | Use as negative validation and motivation for limitations. | Cannot claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0. |
| `SF003` | Use as method/protocol policy. | Protocol correctness alone is not accuracy evidence. |
| `SF004` | Use as sensitivity diagnostic evidence. | Do not promote tuned nu_lbm as a default accuracy model. |
| `SF005` | Use for near-wall/probe-protocol limitations. | Do not report z_plus_half, vertical_valid_above, or z-offset results as official validation. |
| `SF006` | Use to explain why no new official long run is reported in this rc. | Operational readiness evidence only; not solver-output evidence. |
| `SF007` | Use as CityLBM-compatible digital-twin workflow evidence. | Does not prove Case E benchmark accuracy or CityLBM-GH end-to-end execution for Experiment 3. |
| `SF008` | Use as design-screening interpretation evidence. | Sample-internal screening only; no field validation or annual comfort compliance. |
| `SF009` | Use as software traceability evidence for run manifests and protocol metadata. | Traceability output only; does not prove Rhino loaded the new GHA or improve official z=2 m accuracy. |
| `SF010` | Use to move Case E results into manuscript tables without overstating formal accuracy. | Paper-readiness metadata does not change the official z=2 m metric or permit formal v0.4.0. |
| `SF011` | Use as a paper figure for negative validation and limitations only. | Figure output does not add CFD results, improve official z=2 m metrics, or justify formal accuracy claims. |
| `SF012` | Use as software traceability evidence that each generated case records the formal release-gate contract. | Manifest-gate metadata does not add solver output, improve official z=2 m metrics, or permit formal v0.4.0. |
| `SF013` | Use as software misuse-prevention evidence: successful execution is separated from formal benchmark accuracy. | UI claim-boundary text does not add solver output, improve official z=2 m metrics, or prove Rhino loaded the new GHA. |
| `SF014` | Use as ready-to-edit manuscript prose for negative validation, diagnostic interpretation, limitations, and release-boundary text. | Generated prose does not add CFD output, improve official z=2 m metrics, or support a formal predictive-accuracy claim. |
| `SF015` | Use as environment/build-chain evidence explaining why another full software/native validation loop still requires manual VS C++ recovery. | Build-chain readiness does not add CFD output, improve official z=2 m metrics, prove Rhino loaded the new GHA, or permit formal v0.4.0. |
| `SF033` | Use as reproducible software-build evidence for the CityLBM plugin package. | Plugin build reproducibility only; it does not install VS C++ Build Tools, recover GPU runtime, add CFD output, or improve official Case E metrics. |
| `SF016` | Use as high-resolution follow-up feasibility and limitations evidence. | Readiness evidence only; no dx=1 solver output, no official z=2 m metric improvement, and no mesh-independence claim. |
| `SF017` | Use as software-feedback evidence that Case E diagnostics were converted into controlled follow-up interfaces. | No wall-model or roughness setting is a formal validation result until completed official z=2 m raw_trilinear runs pass the release gate. |
| `SF018` | Use as reviewer-facing manifest schema and claim-boundary evidence. | Schema traceability does not add CFD output, improve official z=2 m metrics, or permit a formal accuracy claim. |
| `SF020` | Use as reproducibility evidence that the current best compiled diagnostic repeats the negative official z=2 m result. | Does not improve accuracy, does not support formal v0.4.0, and does not justify promoting diagnostic settings. |
| `SF021` | Use as candidate-run evidence that longer time averaging did not solve the official z=2 m accuracy failure. | Single candidate run; useful for narrowing the failure mode, not for formal accuracy or mesh-independence claims. |
| `SF022` | Use as ablation evidence that z-origin placement affects near-wall/probe-protocol metrics. | Single ablation run; it worsens the formal metric and cannot support formal v0.4.0 or a default z-origin model. |
| `SF023` | Use as low-cost regression evidence that the wind-direction/protocol chain remains positively correlated at dx=3. | R2 remains negative and worse than the current baseline; this does not prove accuracy or mesh independence. |
| `SF024` | Use as runtime/decomposition sensitivity evidence and as a limited negative diagnostic improvement result. | Single decomposition ablation; R2 remains negative and consistency thresholds failed, so it cannot support formal v0.4.0 or default promotion. |
| `SF025` | Use as evidence that AF k, full-plane inlet turbulence, and SGS treatment are the strongest current improvement directions. | Diagnostic sweep on one benchmark; C014 no-SGS scale 2.00 is best but R2 remains negative, C015 rolls back, and the result cannot support formal v0.4.0, LES improvement, or a default accuracy model. |
| `SF026` | Use as residual-structure evidence explaining why the best C014 diagnostic candidate is still not paper-grade validation. | Audit over preexisting C014 solver output; it does not add a new FluidX3D run, change release_gate.json, or justify post-hoc calibration/default promotion. |
| `SF027` | Use as software-feedback traceability from C014 residual diagnosis to a reproducible C016 follow-up interface. | No new FluidX3D run is added here; residual-target controls are not validation results and cannot justify formal v0.4.0. |
| `SF028` | Use as protocol-risk control for residual-target follow-up design. | This guard adds no new CFD metric; it prevents calibration leakage and keeps formal v0.4.0 blocked until an independent official run passes. |
| `SF029` | Use as the manuscript appendix table linking Case E metrics to commands, logs, CSVs, and claim boundaries. | The ledger consolidates existing evidence only; it does not add a new solver run or make formal v0.4.0 pass. |
| `SF030` | Use as the manuscript claim-support gate before turning Case E evidence into Results, Discussion, or Limitations text. | Claim boundary evidence only; it does not add solver output, improve official metrics, or allow formal v0.4.0. |
| `SF031` | Use as software traceability evidence that CityLBM generated cases carry publication-readiness dependencies in the manifest. | Manifest contract only; it does not add solver output, improve official metrics, or permit formal v0.4.0. |
| `SF032` | Use as software traceability evidence that CityLBM surfaces manuscript-readiness boundaries in the plugin UI. | UI traceability only; it does not add solver output, improve official metrics, change defaults, or permit formal v0.4.0. |
| `SF034` | Use for release/data-availability traceability and reviewer artifact checks. | Release planning only; it does not create a GitHub Release, add CFD output, or permit formal v0.4.0. |
| `SF035` | Use as build-chain recovery evidence and to explain why VS C++ remains an operational blocker. | Build-chain recovery only; default script mode does not install tools, recover GPU, run CFD, improve metrics, or permit formal v0.4.0. |
| `SF036` | Use as software delivery traceability before manual Rhino/Grasshopper load verification. | Staging audit only; it does not copy files automatically, prove Rhino loaded the GHA, run CFD, improve metrics, or permit formal v0.4.0. |
| `SF037` | Use as manual software-load evidence collection protocol before closing the Rhino/GHA load gate. | Manual evidence kit only; it does not prove Rhino loaded the plugin, run CFD, improve official metrics, or permit formal v0.4.0. |
| `SF038` | Use as in-Grasshopper software identity evidence for manual Rhino/GHA load verification screenshots. | Software identity component only; it does not prove CFD accuracy, run FluidX3D, improve official metrics, or permit formal v0.4.0. |
| `SF039` | Use as packaged-plugin software identity evidence before manual Rhino/GHA load verification. | Packaged GHA string audit only; it does not prove Rhino loaded the plugin, run CFD, improve official metrics, or permit formal v0.4.0. |
| `SF040` | Use as build-chain reproducibility evidence for the local portable toolchain. | Toolchain activation only; it does not install VS C++, recover GPU, run FluidX3D, improve official metrics, or permit formal v0.4.0. |
| `SF041` | Use as runtime safety and reproducibility evidence explaining why no new long FluidX3D run is scheduled while GPU runtime is blocked. | Runtime fail-fast gate only; it does not recover GPU, run FluidX3D, add solver output, improve official metrics, or permit formal v0.4.0. |
| `SF042` | Use as reviewer-facing schema evidence for the manual Rhino/GHA load manifest contract. | Schema gate only; it does not create manual evidence, prove Rhino loaded the plugin, run CFD, improve metrics, or permit formal v0.4.0. |
| `SF043` | Use as local candidate inventory and protocol-risk evidence only. | The raw candidate CSVs are local/untracked and lack complete run logs; do not use them as formal validation, default-promotion evidence, or formal v0.4.0 support. |
| `SF019` | Use as a pre-registered follow-up experiment plan for improving official z=2 m R2. | Planning evidence only; no candidate has produced new official metrics and no default can be promoted from the plan alone. |

## Boundary

This matrix converts audited experiment findings into software policy, diagnostic switch, and blocker decisions. It does not add CFD results or upgrade the official Case E metric.
