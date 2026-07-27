# Morphology and LCZ-like Wind-Response Classification

evidence_type: newly_run + preexisting_artifact

Status update: this LCZ-like classification is retained as an audit trail only. The recommended manuscript-facing morphology interpretation now uses basic building-morphology parameters instead of LCZ labels; see `reports/basic_morphology_wind_response_analysis.md`.

## Method

- Edge-removal rule: components in the z~2 m building/solid mask are first labelled; components within 20 m of the outer solid-envelope boundary are marked `excluded_edge_incomplete` and removed from morphology-response statistics.
- Enclosure rule: retained central components are scored by local built fraction within 30 m and 8-sector surrounding-building occupancy within 50 m; low/medium/high enclosure classes are internal tertiles of this score after edge removal.
- LCZ rule: classes are LCZ-like morphology labels inferred from height, compactness/enclosure and footprint size. They are not official WUDAPT LCZ map labels.
- Wind-response rule: for each retained component and each of eight incoming wind directions, VR is sampled in two open-cell zones: 0-20 m facade-adjacent band and 20-50 m local-context band.

## Data

- VTK directory: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output`
- Grid metadata: `{'dims_xyz': (320, 390, 60), 'origin': (-318.999982, -388.999984, -59.0000008), 'spacing': (2.0, 2.0, 2.0), 'array_name': 'data', 'vtk_type': 'unsigned_char', 'n_components': 1}`
- Pedestrian layer used for morphology response: z~2.0 m / index 1
- Total labelled solid components: 179
- Retained central components: 101

## Component Counts

| status                   | enclosure_class   | lcz_like_class             |   component_count |
|:-------------------------|:------------------|:---------------------------|------------------:|
| excluded_edge_incomplete | high_enclosure    | LCZ1_compact_highrise_like |                 1 |
| excluded_edge_incomplete | high_enclosure    | LCZ2_compact_midrise_like  |                39 |
| excluded_edge_incomplete | medium_enclosure  | LCZ5_open_midrise_like     |                 4 |
| excluded_small_fragment  | high_enclosure    | LCZ1_compact_highrise_like |                 4 |
| excluded_small_fragment  | high_enclosure    | LCZ2_compact_midrise_like  |                29 |
| excluded_small_fragment  | medium_enclosure  | LCZ5_open_midrise_like     |                 1 |
| retained_central         | high_enclosure    | LCZ1_compact_highrise_like |                 5 |
| retained_central         | high_enclosure    | LCZ2_compact_midrise_like  |                29 |
| retained_central         | low_enclosure     | LCZ1_compact_highrise_like |                 2 |
| retained_central         | low_enclosure     | LCZ2_compact_midrise_like  |                 4 |
| retained_central         | low_enclosure     | LCZ4_open_highrise_like    |                 3 |
| retained_central         | low_enclosure     | LCZ5_open_midrise_like     |                25 |
| retained_central         | medium_enclosure  | LCZ1_compact_highrise_like |                 6 |
| retained_central         | medium_enclosure  | LCZ2_compact_midrise_like  |                27 |

## Retained Morphology-Wind Summary

| analysis_zone        | enclosure_class   | lcz_like_class             |   component_count |   sample_open_cells |   mean_vr |   p95_vr |   stagnation_ratio_vr_lt_0p2 |   acceleration_ratio_vr_gt_0p6 |
|:---------------------|:------------------|:---------------------------|------------------:|--------------------:|----------:|---------:|-----------------------------:|-------------------------------:|
| local_context_20_50m | high_enclosure    | LCZ1_compact_highrise_like |                 5 |               51896 |    0.0026 |   0.0099 |                       1.0000 |                         0.0000 |
| local_context_20_50m | high_enclosure    | LCZ2_compact_midrise_like  |                29 |              387400 |    0.0047 |   0.0198 |                       1.0000 |                         0.0000 |
| local_context_20_50m | low_enclosure     | LCZ1_compact_highrise_like |                 2 |               21416 |    0.0019 |   0.0100 |                       1.0000 |                         0.0000 |
| local_context_20_50m | low_enclosure     | LCZ2_compact_midrise_like  |                 4 |               76424 |    0.0079 |   0.0288 |                       1.0000 |                         0.0000 |
| local_context_20_50m | low_enclosure     | LCZ4_open_highrise_like    |                 3 |               44232 |    0.0298 |   0.0605 |                       1.0000 |                         0.0000 |
| local_context_20_50m | low_enclosure     | LCZ5_open_midrise_like     |                25 |              337848 |    0.0079 |   0.0300 |                       1.0000 |                         0.0000 |
| local_context_20_50m | medium_enclosure  | LCZ1_compact_highrise_like |                 6 |               60744 |    0.0015 |   0.0058 |                       1.0000 |                         0.0000 |
| local_context_20_50m | medium_enclosure  | LCZ2_compact_midrise_like  |                27 |              323488 |    0.0044 |   0.0171 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | high_enclosure    | LCZ1_compact_highrise_like |                 5 |               13000 |    0.0009 |   0.0038 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | high_enclosure    | LCZ2_compact_midrise_like  |                29 |              117960 |    0.0022 |   0.0101 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | low_enclosure     | LCZ1_compact_highrise_like |                 2 |                7048 |    0.0014 |   0.0048 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | low_enclosure     | LCZ2_compact_midrise_like  |                 4 |               47872 |    0.0074 |   0.0324 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | low_enclosure     | LCZ4_open_highrise_like    |                 3 |               12696 |    0.0191 |   0.0662 |                       0.9998 |                         0.0000 |
| near_facade_0_20m    | low_enclosure     | LCZ5_open_midrise_like     |                25 |              128760 |    0.0043 |   0.0163 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | medium_enclosure  | LCZ1_compact_highrise_like |                 6 |               16568 |    0.0015 |   0.0047 |                       1.0000 |                         0.0000 |
| near_facade_0_20m    | medium_enclosure  | LCZ2_compact_midrise_like  |                27 |              107936 |    0.0020 |   0.0085 |                       1.0000 |                         0.0000 |

## Interpretation

1. Removing edge-incomplete buildings prevents truncated peripheral fragments from dominating the morphology interpretation. The remaining components represent the central campus block more consistently.
2. The retained central morphology is interpreted primarily as compact/open low- to mid-rise LCZ-like campus fabric rather than an official LCZ product. This is suitable for intra-site wind interpretation but should not be reported as a city-scale LCZ map.
3. The facade-adjacent band remains extremely low-speed for almost all classes; the 20-50 m local-context band is more informative for comparing low, medium and high enclosure responses under different incoming wind directions.
4. The eight-direction grouping supports discussion of incoming-wind sensitivity, but the present results remain CFD screening evidence, not field-validated comfort compliance.

## Outputs

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_lcz_component_manifest.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_lcz_wind_response_by_component.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_wind_response_by_enclosure_and_wind.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_wind_response_by_lcz_and_wind.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_wind_response_by_enclosure_lcz_summary.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_lcz_central_building_classification_map.png`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_lcz_wind_response_summary.png`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\morphology_lcz_context_zone_response.png`

## Literature Boundary

- LCZ classes follow the Stewart and Oke/WUDAPT idea that urban sites can be grouped by building height, packing and surface cover at local scale. Source: https://www.wudapt.org/lcz/
- WUDAPT describes LCZs as a globally consistent morphology-relevant layer for climate, weather, environment and planning models. Source: https://www.wudapt.org/
- Because this project classifies a small campus core from CFD-ready geometry, the label used here is `LCZ-like`, not an official LCZ map.

## LCZ Scale Validity

The LCZ framework is valid here as a morphology vocabulary, not as an official LCZ mapping result. The present analysis unit is a retained central building component plus its 0-20 m and 20-50 m surrounding open-cell wind-sampling bands. This is finer and more CFD-specific than a conventional city-scale LCZ patch. The classification also uses relative enclosure tertiles within the cropped campus core rather than externally calibrated WUDAPT LCZ thresholds.

This means LCZ-like labels should be used to interpret compactness, openness, height and enclosure effects on wind response. They should not be used to claim that the TUM core has been formally mapped as LCZ1, LCZ2, LCZ4 or LCZ5. In the current results, the 0-20 m facade-adjacent band is too strongly sheltered for LCZ-like classes to separate cleanly; the 20-50 m local-context band is the more appropriate scale for LCZ-like interpretation.

Detailed discussion: `reports/lcz_scale_validity_in_this_model.md`.
