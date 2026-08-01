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
best run so far is a z-center lattice diagnostic dx=2 m run with one
effective-ground offset cell, `origin_z_offset_m=1.0`, and `nu_lbm=0.001`,
48000 steps, spinup 12000, raw_trilinear sampling: MAE 21.111 percentage
points, R2 -2.006330, Pearson 0.115756. These results show directional
improvement but support a limitations/diagnostic discussion only, not a
predictive-accuracy claim or a formal `v0.4.0` release.

Current Case E, release-gate, and manuscript-boundary materials:

- `docs/experiments/casee/data_manifest.csv`
- `docs/experiments/casee/casee_preset.json`
- `docs/experiments/casee/casee_protocol.md`
- `docs/experiments/casee/tools/casee_audit.py`
- `docs/experiments/casee/tools/generate_native_casee.py`
- `docs/experiments/casee/tools/release_gate.py`
- `docs/experiments/casee/tools/paper_evidence_gate.py`
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
- `docs/experiments/casee/results/casee_manuscript_claim_matrix.csv`
- `docs/experiments/casee/results/casee_manuscript_evidence_summary.md`
- `docs/experiments/casee/results/casee_paper_evidence_gate.json`
- `docs/experiments/casee/results/casee_paper_evidence_gate.md`
- `docs/experiments/casea/results/casea_smoke_regression.json`
- `docs/experiments/casea/results/casea_vtk_manifest.csv`
- `docs/releases/v0.4.0-rc13.md`

The current-machine AIJ Case A smoke regression passed as a workflow
non-regression guard: dx = 3.5 m, 2000 FluidX3D steps, a completed run log, and
two external VTK outputs recorded by hash. This does not provide accuracy
validation for CityLBM; it only guards against breaking the earlier Case A
workflow while Case E is being optimized.

CityLBM includes one experiment-derived default-off solver switch in this branch:
`Diagnostic LBM Nu Override` (`nuLBM`) on the Grasshopper `Run Simulation`
component. It is for reproducing `nu_lbm` sensitivity diagnostics only; leaving
it at 0 keeps the standard physical-viscosity mapping.

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

The z-center lattice diagnostic puts official z=2 m on a dx=2 m lattice center.
It improves the formal raw_trilinear MAE to 21.111 pp and Pearson to 0.115756,
but R2 remains negative. Its best diagnostic sampling mode,
`vertical_valid_above`, reaches MAE 16.041 pp and Pearson 0.336940, but this is
still not a formal validation result.

CityLBM now exposes the corresponding `Diagnostic Z Origin Offset` (`zOff`)
input on the Grasshopper `Run Simulation` component. The default is 0 m. This
is an experiment switch for inlet-height and probe-protocol diagnostics, not a
validated default accuracy model.

Current build-chain audit: .NET SDK 8.0.423 and the existing FluidX3D binary are
available under `E:\citylbm_buildchain`, but Visual Studio Build Tools 2022 C++
is still blocked. `winget` returned exit code 1602, the bootstrapper log
reported a possible declined UAC prompt, and C: has less than the free space
required by the VS precheck.

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

Run the audit after official data are present:

```powershell
python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0
python docs/experiments/casee/tools/release_gate.py
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
