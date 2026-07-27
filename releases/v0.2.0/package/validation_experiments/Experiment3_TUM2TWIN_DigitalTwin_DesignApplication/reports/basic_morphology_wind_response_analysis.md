# Basic Building-Morphology Parameters and Wind-Response Analysis

evidence_type: newly_run

## Purpose

This analysis removes LCZ labels and uses basic, transferable morphology parameters to explain wind-response differences in the retained TUM2TWIN core campus buildings.

## Execution Record

- Command: `python scripts\analyze_basic_morphology_wind_response.py`
- Morphology input: `figures/morphology_lcz_component_manifest.csv`
- Wind-response input: `figures/morphology_lcz_wind_response_by_component.csv`
- Aggregation: retained central building components, two open-cell analysis zones, eight incoming wind directions.
- Note: stagnation-ratio correlations are not interpreted where the response is constant across components.

## Parameters

- `footprint_area_m2`: footprint area
- `mean_height_m`: mean height
- `height_to_sqrt_area`: height / sqrt(area)
- `compactness_p2_over_a`: perimeter^2 / area
- `elongation_ratio`: elongation ratio
- `local_built_fraction_r30m`: local built fraction, r=30 m
- `sector_enclosure_ratio_r50m`: sector enclosure, r=50 m
- `relative_enclosure_score`: combined enclosure score

## Main Finding

The 0-20 m facade-adjacent band is almost uniformly sheltered, so morphology parameters have limited practical separation there. The 20-50 m local-context band is more diagnostic because it captures partial wind recovery away from immediate building faces.

## Strongest Correlations With 20-50 m Mean VR

| parameter_label              |   spearman_rho |   p_value |   n_components |
|:-----------------------------|---------------:|----------:|---------------:|
| sector enclosure, r=50 m     |        -0.3956 |    0.0000 |            101 |
| mean height                  |        -0.3507 |    0.0003 |            101 |
| combined enclosure score     |        -0.3019 |    0.0022 |            101 |
| local built fraction, r=30 m |        -0.2260 |    0.0231 |            101 |
| height / sqrt(area)          |        -0.2083 |    0.0366 |            101 |
| elongation ratio             |         0.0832 |    0.4081 |            101 |
| footprint area               |         0.0811 |    0.4204 |            101 |
| perimeter^2 / area           |         0.0509 |    0.6131 |            101 |

## Comparison: 0-20 m Facade Band

| parameter_label              |   spearman_rho |   p_value |   n_components |
|:-----------------------------|---------------:|----------:|---------------:|
| combined enclosure score     |        -0.5344 |    0.0000 |            101 |
| local built fraction, r=30 m |        -0.4643 |    0.0000 |            101 |
| sector enclosure, r=50 m     |        -0.4083 |    0.0000 |            101 |
| mean height                  |        -0.2862 |    0.0037 |            101 |
| footprint area               |        -0.1314 |    0.1901 |            101 |
| perimeter^2 / area           |        -0.1229 |    0.2208 |            101 |
| elongation ratio             |        -0.1119 |    0.2652 |            101 |
| height / sqrt(area)          |         0.0245 |    0.8077 |            101 |

## New Interpretable Conclusions

1. The most useful explanatory scale is not the immediate facade band but the 20-50 m local morphological context. This suggests a scale transition from facade shelter to neighbourhood-context recovery.
2. Local built fraction, sector enclosure and combined enclosure score are more transferable explanatory variables than named LCZ categories in this cropped campus model.
3. Height alone is not sufficient to explain pedestrian-layer wind recovery; surrounding compactness/enclosure controls whether above-canopy flow can reconnect with the pedestrian layer.
4. The result supports a design-oriented interpretation: improving ventilation should target local porosity, passage connectivity and enclosure release rather than only reducing building height.

## Outputs

- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_component_parameters.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_wind_response_by_component.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_parameter_correlations.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_parameter_tertile_wind_response.csv`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_parameter_correlation_heatmap.png`
- `C:\Users\miaoshiyu\Documents\【citylbm】实验3：数字孪生应用研究\figures\basic_morphology_parameter_tertile_wind_response.png`

## Claim Boundary

These conclusions are CFD-derived morphology-response screening evidence. They do not constitute field validation, official comfort compliance or pollutant dispersion analysis.
