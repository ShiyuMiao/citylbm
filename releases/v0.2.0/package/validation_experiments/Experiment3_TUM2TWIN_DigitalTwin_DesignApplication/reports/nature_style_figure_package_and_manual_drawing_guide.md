# Nature-Style Figure Package and Manual Drawing Guide

evidence_type: newly_run

## 1. Figure Contract

Core conclusion:

> TUM2TWIN visual photogrammetry/Rhino data define the real urban scene, but FluidX3D wind simulation requires a semantic closed collision boundary; once converted to a LoD3-derived closed prism, the core TUM Downtown block shows directionally robust pedestrian-layer stagnation and strong vertical wind-speed recovery.

Figure archetype:

- Fig. 1: schematic-led composite, methods and evidence-chain figure.
- Fig. 2: asymmetric mixed-modality quantitative result figure, with a hero spatial map plus supporting quantitative panels.

Backend and export:

- Backend: Python / Matplotlib only.
- Final layout width: double-column, approximately 183 mm.
- Exported formats: SVG, PDF, PNG and TIFF.
- Editable text: SVG `svg.fonttype=none`; PDF `pdf.fonttype=42`.
- Source data: exported as CSV files in the figure package.

## 2. Output Package

Heavy/export-complete directory:

`D:\citylbm_tum2twin_heavy_store\paper_figures\nature_style_20260727`

Lightweight project copies:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\nature_style`

Manifest:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\manifests\nature_style_figure_manifest.csv`

Generation script:

`C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\scripts\create_nature_style_figures.py`

## 3. Generated Figures

### Fig. 1: Digital-Twin-to-CFD Workflow

Files:

- `nature_fig1_digital_twin_to_cfd_workflow.svg`
- `nature_fig1_digital_twin_to_cfd_workflow.pdf`
- `nature_fig1_digital_twin_to_cfd_workflow.png`
- `nature_fig1_digital_twin_to_cfd_workflow.tiff`

Source data:

- `source_data/source_data_nature_fig1_geometry_workflow.csv`

Panel logic:

| Panel | Role | Main message |
|---|---|---|
| a | Evidence-chain schematic | Visual twin -> semantic city model -> CFD-ready geometry -> FluidX3D -> wind metrics |
| b | Extent comparison | Visual model and core CFD geometry cover the same TUM Downtown block scale |
| c | Representation shift | Photogrammetry is dense visual mesh; CFD prism is simplified but simulation-ready |
| d | Collision readiness | Visual STL has boundary edges; closed semantic prism has collision-boundary logic |
| e | Qualitative readiness logic | Photogrammetry excels as visual reference; LoD3-derived prism supports simulation |

Manual drawing recommendation:

- Redraw panel a in Illustrator/Figma as a clean horizontal pipeline.
- Keep the same five nodes and arrows; use restrained pastel fills.
- Replace rounded boxes with slightly rounded 2-3 mm radius rectangles if the journal layout feels too informal.
- Keep panel b-d as small quantitative anchors; do not overdecorate them.
- If manually redrawing panel e, use direct labels instead of a detached legend to reduce eye travel.

### Fig. 2: Core Wind Robustness Result

Files:

- `nature_fig2_core_wind_robustness.svg`
- `nature_fig2_core_wind_robustness.pdf`
- `nature_fig2_core_wind_robustness.png`
- `nature_fig2_core_wind_robustness.tiff`

Source data:

- `source_data/source_data_nature_fig2_core_wind_robustness.csv`

Panel logic:

| Panel | Role | Main message |
|---|---|---|
| a | Hero spatial map | Open-Meteo weighted stagnation probability remains high across most open pedestrian cells |
| b | Directional variability map | Directional standard deviation is spatially localized and generally low |
| c | Directional response | Mean VR remains low and stagnation ratio remains high under all eight directions |
| d | Vertical profiles | VR recovers with height while stagnation decays toward zero |
| e | Robustness summary | 91.5% of open cells are stagnant in at least 6/8 directions; 87.2% are stagnant in all directions |

Manual drawing recommendation:

- Use panel a as the hero panel occupying about 45-55% of figure area.
- For manual redrawing, keep the building/solid mask white and use a single blue sequential palette for stagnation probability.
- Avoid a rainbow colormap for the final paper version; probability should read as a monotonic scalar.
- Keep panel e as a horizontal bar summary because it carries the strongest quantitative conclusion.
- If space is tight, remove panel b before removing panel e; panel e is more important for the paper argument.

## 4. Figure Legends Draft

**Fig. 1 | Digital-twin-to-CFD transformation for TUM2TWIN wind simulation.**
a, Evidence chain from TUM2TWIN photogrammetry/Rhino visual assets to semantic city geometry, closed CFD collision boundary, FluidX3D simulation and wind-environment metrics. b, Comparison of the visual photogrammetry/Rhino extent and the core CFD-ready STL extent. c, Triangle-count reduction from the dense visual photogrammetry mesh to the LoD3-derived closed prism. d, Boundary-edge contrast between the non-watertight visual STL and the accepted semantic-prism collision geometry. e, Qualitative geometry-to-CFD readiness logic for photogrammetry/Rhino and LoD3-derived prism representations. Source data are provided as a Source Data file.

**Fig. 2 | Directionally robust pedestrian-layer stagnation in the core TUM Downtown block.**
a, Open-Meteo 2024 proxy-weighted stagnation probability at z≈2 m, where stagnation is defined as VR<0.2. White areas indicate solid collision cells. b, Directional standard deviation of VR across the eight FluidX3D wind directions. c, Directional response of mean VR and VR<0.2 area ratio at z≈2 m. d, Vertical profiles of mean VR and VR<0.2 ratio for equal-weighted and Open-Meteo-weighted aggregation. e, Robustness summary showing the fraction of open z≈2 m cells that remain stagnant across most or all wind directions and the sparse occurrence of repeated acceleration. FluidX3D results use dx=2 m, eight directions and three post-spin-up samples per direction. Source data are provided as a Source Data file.

## 5. Manual Drawing Rules for Later Polishing

1. Keep one figure = one claim. Fig. 1 should argue "visual twin is not CFD boundary"; Fig. 2 should argue "pedestrian stagnation is directionally robust".
2. Use lowercase bold panel labels `a-e`, 7-8 pt, outside the data area but close to the top-left corner.
3. Use 5-7 pt text at final 183 mm width; avoid large dashboard-like headings.
4. Keep maps as raster layers but keep labels, axes, color bars and annotations as editable vector text.
5. Do not use saturated rainbow colormaps. Use blue sequential for probability, purple/grey sequential for variability, red/gold only for stagnation warning metrics.
6. Use direct numeric labels on key bars: `0.915`, `0.872`, `0.903`, `0.025`.
7. Preserve evidence wording: "Open-Meteo proxy-weighted", not "measured annual probability".
8. Preserve model wording: "LoD3-derived closed prism", not "raw photogrammetry mesh".
9. For Illustrator redraw, lock the source PNG/map layer, trace only clean outlines if needed, and keep the source-data CSV linked in the figure folder.
10. Before final submission, re-export PDF/SVG from Illustrator with editable text and check that all color bars still match the original numeric range.

## 6. QA Notes

Automated preflight:

- `PASS`: Python source parses.
- `PASS`: sans-serif publication font configured.
- `PASS`: text size floor above 5 pt.
- `PASS`: no rainbow/jet/hsv colormap.
- `PASS`: SVG/PDF editable-text settings configured.
- `PASS`: SVG and PDF exports present.
- `WARN`: static validator did not detect dynamically generated TIFF/DPI/width, but actual TIFF files were exported and the script uses 183 mm figure widths.
- `WARN`: log axis appears in Fig. 1c; plotted triangle counts are positive.

Runtime warnings:

- `Mean of empty slice` warnings arise from solid or invalid masked cells in the VTK grid. Metrics and maps are computed over open fluid cells, and solid cells are masked in the figure.
