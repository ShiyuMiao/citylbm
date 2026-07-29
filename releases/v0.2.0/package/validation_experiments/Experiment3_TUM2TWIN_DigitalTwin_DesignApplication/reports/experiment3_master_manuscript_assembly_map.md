# Experiment 3 Master Manuscript Assembly Map

evidence_type: newly_run + preexisting_artifact + blocked

This report converts the current Experiment 3 archive into a manuscript assembly map. It does not add new simulation outcomes. It tells the author where each result belongs, what artifact supports it, which figure or table should be cited, and how the claim must be bounded.

## Assembly Summary

- Assembly rows: `11`
- Main safe positioning: `FluidX3D-native digital-twin-to-CFD wind screening with CityLBM-compatible geometry preparation`.
- Strongest paper contribution: data-layer separation, CFD-ready geometry construction, campus-core low-speed screening, building-form/context interpretation, and negative S1/S2 design-sensitivity evidence.
- Claims still blocked: field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE closure, CityLBM-Grasshopper end-to-end execution, and optimized S3-Sn intervention proof.

## Manuscript Assembly Table

| assembly_id | manuscript_section | figure_table_callouts | paper_ready_claim | claim_boundary | open_debt_or_author_action |
|---|---|---|---|---|---|
| E3-M0 | Experiment positioning after AIJ Case A/E | Table E3-2 | Experiment 3 is a real-campus digital-twin design-application case rather than a new solver-validation case. | Do not state that Experiment 3 independently proves solver accuracy or CityLBM-Grasshopper end-to-end execution. | Author must decide final paper title emphasis and target journal style. |
| E3-M1 | Digital-twin data layering and geometry workflow | Table E3-3 | UAS/photogrammetry assets support visual audit, while semantic or CAD-derived closed geometry supports CFD collision boundaries. | Do not describe textured photogrammetry or 3DGS primitives as directly accepted watertight rigid collision boundaries. | None for screening-level manuscript use. |
| E3-M2 | Geometry-to-CFD readiness | Table E3-3 | GCRI evidence separates CFD-ready collision geometry from visually faithful but CFD-fragile geometry (0.455 / 0.925 / 0.918). | GCBTE is proposed but not computed because no independent 3DGS-derived collision extraction was available. | Keep GCBTE as future validation unless a 3DGS collision extraction workflow is added. |
| E3-M3 | Baseline pedestrian wind field | Fig. E3-1; Table E3-1 | The baseline FluidX3D run supports a screening-level low-speed pedestrian-layer finding (0.076 / 0.934). | Do not convert VR maps into formal Lawson/NEN/AIJ annual comfort or safety classes. | Measured wind climate or wind-tunnel validation is needed for compliance or prediction claims. |
| E3-M4 | Vertical recovery and directionality | Fig. E3-S1; Fig. E3-S2 | Vertical layers and eight-direction summaries show quasi-omnidirectional sheltering near pedestrians and partial recovery aloft. | Sampling remains screening-level and does not replace convergence, grid-independence or validation evidence. | Add stronger temporal convergence and grid sensitivity if the target journal demands predictive CFD validation. |
| E3-M5 | Building-form interpretation | Fig. E3-2; Fig. E3-4; Fig. E3-S3; Fig. E3-S4; Fig. E3-S5 | At this campus-block scale, basic morphology parameters explain wind response better as local-context descriptors than as LCZ classes. | Treat correlations, thresholds, archetypes and directional fingerprints as sample-internal screening evidence, not universal causal laws. | External sites or measured datasets are needed before claiming universal morphology thresholds. |
| E3-M6 | Design sensitivity S1/S2 | Fig. E3-3; Table E3-1 | S1/S2 are negative or near-null design-sensitivity tests rather than successful optimization cases (-0.000213 / 0.000233; -0.000466 / 0.000633). | Do not claim optimized intervention performance or S3-Sn design proof. | A future optimization loop should add S3-Sn alternatives and objective functions before using the word optimized. |
| E3-M7 | Campus climate and application potential | Table E3-1; Fig. E3-S2 | The campus application value lies in repeatable screening of ventilation-sensitive spaces and in prioritizing morphology-aware design review. | Open-Meteo remains a climate proxy and cannot support formal annual comfort/safety exceedance claims. | Use local measured wind records if the final manuscript claims climate-compliance relevance. |
| E3-M8 | Limitations and claim boundary | Table E3-2 | The archive explicitly classifies remaining debts and blocked claim upgrades (7 / 1 / 4 / 1). | Keep blocked items visible: field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE and CityLBM-GH execution. | Open status counts: {'open_author_input': 1, 'blocked': 4, 'open_conditional': 1, 'closed_or_not_detected': 1}. |
| E3-M9 | Data, code and reproducibility statements | None | The GitHub archive contains a checkout-stable manifest and points to external large assets without embedding all raw/VTK files. | Do not imply that every large raw dataset or full VTK dump is stored directly in GitHub. | Author must fill funding, competing interests, acknowledgements and CRediT roles. |
| E3-M10 | Final conclusion paragraph | Table E3-1; Table E3-2 | The final conclusion should synthesize geometry readiness, low-speed dominance, morphology-context interpretation and negative design sensitivity (8 deep findings; 28 key-result rows; z2 mean VR 0.076, stagnation 93.4%; all-direction stagnation 87.2%; >20 m distance band mean VR 0.095; top morphology rho -0.534; S1/S2 z2 delta mean VR negative; GCRI 0.455 vs 0.925/0.918). | Retain screening-level wording unless the missing external validation and compliance evidence are added. | Manual author review should choose whether this is a standalone Experiment 3 section or a merged Results/Discussion subsection. |

## Recommended Narrative Order

1. Position Experiment 3 after AIJ Case A/E as a real digital-twin application case.
2. Explain why visual photogrammetry and semantic collision geometry must be separated.
3. Report GCRI/geometry QA before wind results so the reader sees why the CFD boundary is legitimate.
4. Present S0 baseline low-speed and vertical/directional recovery.
5. Interpret wind response with basic morphology parameters rather than LCZ classification.
6. Use S1/S2 as negative design-sensitivity evidence to show why porosity must be coupled to wind-entry context.
7. Close with campus application potential and explicit evidence boundaries.
