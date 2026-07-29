# Experiment 3 Conclusion Figure Plan

evidence_type: newly_run + preexisting_artifact + blocked

## Core Figure Contract

- Core conclusion: TUM2TWIN becomes useful for campus wind-environment design only after visual digital-twin data are converted into auditable CFD collision geometry; the resulting FluidX3D screening shows persistent pedestrian-layer low-speed conditions that are better interpreted through basic local building-form parameters than through LCZ classes or simple porosity alone.
- Figure archetype: asymmetric mixed-modality figure.
- Target journal/output: Nature-family double-column figure, 183 mm wide, 170 mm high before tight bounding-box export.
- Backend: Python / matplotlib only.
- Export bundle: SVG, PDF, PNG and LZW-compressed TIFF, with source data CSV.
- Reviewer risks: no field validation, no annual comfort/safety compliance, no pollutant dispersion, no GCBTE closure and no CityLBM-Grasshopper end-to-end execution.

## Panel Plan

| panel | content | figure form | source data | evidence_type |
|---|---|---|---|---|
| a | Overall evidence chain from TUM2TWIN visual data to CFD-ready collision geometry, FluidX3D simulation and design interpretation. | Schematic-led evidence-flow panel. | manuscript logic; reports/claim_boundary.md; manifests/experiment3_master_manuscript_assembly_map.csv | newly_run + preexisting_artifact + blocked |
| b | CFD readiness separates visual mesh from closed collision geometry. | Horizontal GCRI bar chart with readiness reference line. | manifests/gcri_scoring_table.csv | newly_run + preexisting_artifact |
| c | Pedestrian layer is low speed while flow recovers aloft. | Dual-axis vertical profile for mean VR and VR<0.2 ratio. | figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv | newly_run |
| d | Near-building zones are strongly sheltered; wind recovery is clearer in the wider local-context band. | Distance-band bar and line chart. | figures/paraview_vtk_core_dx2m_building_distance_stats.csv | newly_run |
| e | Basic morphology parameters act as local-context screening descriptors. | Ranked Spearman correlation bars. | figures/experiment3_deep_conclusion_morphology_support.csv | newly_run |
| f | Building response classes differ in local VR and directional reactivity. | Grouped bar chart by near-to-context response class. | figures/morphology_directional_fingerprint_stage_summary.csv | newly_run + blocked |
| g | S1/S2 interventions are near-null or negative, so porosity alone is insufficient. | Height-wise delta line plot. | figures/fluidx3d_s0_s1_ventilation_relief_metric_comparison.csv; figures/fluidx3d_s0_s2_network_porosity_metric_comparison.csv | newly_run |
| h | Separate manuscript-safe claims from blocked claim upgrades. | Compact evidence-boundary checklist. | manifests/experiment3_submission_debt_register.csv; reports/claim_boundary.md | newly_run + blocked |

## Generated Files

- `figures/nature_style/experiment3_conclusion_figure_nature.svg`
- `figures/nature_style/experiment3_conclusion_figure_nature.pdf`
- `figures/nature_style/experiment3_conclusion_figure_nature.png`
- `figures/nature_style/experiment3_conclusion_figure_nature.tiff`
- `figures/nature_style/source_data/experiment3_conclusion_figure_source_data.csv`

## Nature-Style Checks

- Double-column width is used.
- Font family is sans-serif and text remains editable in SVG/PDF.
- Panel labels are lowercase bold letters.
- Quantitative panels are CSV-driven and no simulated or placeholder values are introduced.
- Red/green is not the only visual code; no rainbow colour map is used.
- Evidence boundaries are displayed as part of the figure instead of hidden in the caption.
