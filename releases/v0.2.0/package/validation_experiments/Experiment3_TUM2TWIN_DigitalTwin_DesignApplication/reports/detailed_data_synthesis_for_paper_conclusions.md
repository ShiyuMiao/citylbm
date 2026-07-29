# Detailed Data Synthesis for Paper Conclusions

evidence_type: newly_run + preexisting_artifact + blocked

This report consolidates the existing FluidX3D, ParaView, morphology, Open-Meteo proxy, and geometry-readiness artifacts into paper-ready conclusions. No new CFD field is invented here; all numbers are derived from archived CSV artifacts.

## 1. Vertical Wind-Response Structure

| 高度 | mean VR | P95 VR | 滞风比例 | VR>0.6比例 | 相对2 m均值倍数 |
| --- | --- | --- | --- | --- | --- |
| 2.0 | 0.076338 | 0.241286 | 93.35% | 1.30% | 1.000 |
| 4.0 | 0.186721 | 0.634857 | 66.53% | 5.25% | 2.446 |
| 10.0 | 0.404277 | 0.915226 | 31.40% | 27.62% | 5.296 |
| 20.0 | 0.601949 | 1.020634 | 24.52% | 59.41% | 7.885 |
| 40.0 | 1.048508 | 1.146731 | 0.00% | 100.00% | 13.735 |

Interpretation: the strongest manuscript conclusion is a vertical decoupling between the pedestrian layer and the upper flow. At z≈2 m, mean VR is only `0.076` and `93.35%` of open cells fall below VR<0.2. By z≈20 m, mean VR rises to `0.602`, while at z≈40 m the open layer is essentially above the low-speed threshold. This supports a campus-canyon interpretation: above-canopy flow recovery does not directly translate into pedestrian ventilation.

## 2. Directional Robustness

At z≈2 m, the directional mean VR range is only `0.0060`, while the stagnation ratio varies by only `1.74%` across eight wind directions. The spatial robustness table further shows all-direction stagnation over `87.25%` of the pedestrian plane and robust stagnation frequency >=0.75 over `91.49%`.

This means that the main z≈2 m conclusion is not a single-wind-direction artifact. The campus core geometry produces a stable low-ventilation footprint across wind directions.

## 3. Climate-Proxy Weighting

| 高度 | 8风向mean VR | Open-Meteo mean VR | 均值差 | 滞风比例差 |
| --- | --- | --- | --- | --- |
| 2.0 | 0.076338 | 0.076763 | 0.000425 | -0.002263 |
| 4.0 | 0.186721 | 0.187861 | 0.001141 | -0.009473 |
| 10.0 | 0.404277 | 0.406364 | 0.002087 | 0.009265 |
| 20.0 | 0.601949 | 0.603270 | 0.001321 | 0.007650 |
| 40.0 | 1.048508 | 1.050839 | 0.002332 | 0.000000 |

Open-Meteo 2024 proxy data concentrate `48.83%` of hours in the two largest velocity-to sectors and `60.54%` in the three largest sectors (`90, 45, 270` degrees). However, applying those weights changes the z≈2 m mean VR by only `0.0004` and the z≈2 m stagnation ratio by `-0.0023`. The proxy weighting is therefore useful for sensitivity discussion, but not a substitute for measured wind rose or formal exceedance-probability comfort assessment.

## 4. Distance-to-Building Gradient

| 距建筑 | mean VR | P95 VR | 滞风比例 | VR>0.6比例 |
| --- | --- | --- | --- | --- |
| 0-4m | 0.002137 | 0.009514 | 100.00% | 0.00% |
| 4-10m | 0.009280 | 0.042526 | 100.00% | 0.00% |
| 10-20m | 0.021861 | 0.072575 | 100.00% | 0.00% |
| >20m | 0.095054 | 0.287127 | 90.79% | 1.01% |

The distance-gradient result sharpens the architectural conclusion. The 0-4 m, 4-10 m, and 10-20 m bands are almost fully low-speed zones, while the >20 m band recovers to mean VR `0.095` but still keeps `90.79%` below VR<0.2. Thus, the wind-environment issue is not restricted to an immediate facade boundary layer; it propagates into the block-scale pedestrian network.

## 5. Building-Morphology Explanation

| 分析带 | 形态参数 | 响应指标 | Spearman rho | p值 |
| --- | --- | --- | --- | --- |
| near_facade_0_20m | combined enclosure score | directional_mean_vr | -0.534374 | 8.639e-09 |
| near_facade_0_20m | combined enclosure score | directional_range_mean_vr | -0.498323 | 1.140e-07 |
| near_facade_0_20m | local built fraction, r=30 m | directional_mean_vr | -0.464310 | 1.004e-06 |
| near_facade_0_20m | local built fraction, r=30 m | directional_range_mean_vr | -0.427082 | 8.429e-06 |
| near_facade_0_20m | combined enclosure score | directional_p95_vr | -0.422714 | 1.065e-05 |
| near_facade_0_20m | sector enclosure, r=50 m | directional_mean_vr | -0.408346 | 2.244e-05 |
| near_facade_0_20m | sector enclosure, r=50 m | directional_range_mean_vr | -0.405406 | 2.604e-05 |
| local_context_20_50m | sector enclosure, r=50 m | directional_mean_vr | -0.395640 | 4.221e-05 |

The strongest shape-response relationships come from local context parameters rather than from simple object dimensions. In the 20-50 m band, sector enclosure has Spearman rho `-0.396` with mean VR, while mean height has rho `-0.351` and combined enclosure has rho `-0.302`. Footprint area, elongation, and perimeter-area compactness are weak for mean VR in this cropped campus setting.

| 分析带 | 参数 | 低组mean VR | 高组mean VR | 高-低变化 | 相对变化 |
| --- | --- | --- | --- | --- | --- |
| local_context_20_50m | combined enclosure score | 0.009638 | 0.004460 | -0.005178 | -0.5373 |
| local_context_20_50m | local built fraction, r=30 m | 0.009212 | 0.004563 | -0.004649 | -0.5047 |
| near_facade_0_20m | combined enclosure score | 0.005932 | 0.002033 | -0.003898 | -0.6572 |
| near_facade_0_20m | local built fraction, r=30 m | 0.005106 | 0.002119 | -0.002987 | -0.5850 |
| local_context_20_50m | sector enclosure, r=50 m | 0.009141 | 0.006339 | -0.002803 | -0.3066 |
| local_context_20_50m | mean height | 0.007993 | 0.006294 | -0.001699 | -0.2126 |
| near_facade_0_20m | sector enclosure, r=50 m | 0.005060 | 0.003459 | -0.001601 | -0.3164 |
| near_facade_0_20m | mean height | 0.003598 | 0.004858 | 0.001260 | 0.3502 |

The high-vs-low tertile table gives the most intuitive design reading: high combined enclosure in the 20-50 m band reduces mean VR from `0.0096` to `0.0045`, a relative change of `53.73%`. High local built fraction produces a similarly strong reduction. The paper should therefore discuss courtyard enclosure, passage continuity, and near-ground porosity before treating height or footprint as primary explanatory variables.

## 6. Digital-Twin Model Performance

The GCRI table supports a separate digital-twin conclusion. The visual photogrammetry STL scores `0.455`, while the accepted core and district prism collision geometries score `0.925` and `0.918`. The direct LoD3 OBJ candidate scores `0.528` before repair. This shows that visual fidelity and CFD readiness are not equivalent: a digital twin can be visually consistent with the study block but still fail as a closed, voxelizable collision boundary.

## 7. Detailed Paper Conclusions

1. The current TUM2TWIN campus-core result should be framed as a robust low-ventilation screening result: z≈2 m low-speed dominance persists across all eight wind directions.
2. The vertical profile indicates a strong pedestrian/upper-flow decoupling. Wind recovery appears at 10-20 m and becomes dominant by 40 m, but that recovery does not solve pedestrian-layer stagnation.
3. Building distance matters, but the recovery length is larger than the immediate facade zone. Even cells farther than 20 m from buildings remain mostly below VR<0.2 in this cropped core.
4. Local enclosure and built fraction are more explanatory than footprint area, elongation, or compactness. The practical design target is therefore releasing enclosure and improving passage connectivity, not only reducing isolated building height.
5. Open-Meteo weighting barely changes the main screening result. This strengthens the internal robustness of the geometric interpretation but must not be written as measured climate validation.
6. The digital-twin contribution is methodological: the study demonstrates a separation between visual digital-twin assets and CFD-ready collision assets, quantified through GCRI.

## 8. Claims That Must Stay Limited

- No field-measured or wind-tunnel validation is available.
- No formal Lawson/NEN/AIJ comfort-safety exceedance assessment is supported.
- No pollutant dispersion result is available.
- S1 ventilation-relief and S2 network-porosity have been simulated, but both are near-null/negative design-sensitivity results rather than proof of successful optimization; S3-Sn interventions remain future work.
- No GCBTE value is computed because no independent 3DGS-derived collision boundary extraction exists.
- No completed Rhino-Grasshopper/CityLBM end-to-end run is claimed; the current positioning remains FluidX3D-native with a CityLBM-compatible geometry package.

## Output Tables

- `figures/detailed_conclusion_vertical_gradient.csv`
- `figures/detailed_conclusion_climate_weighting_delta.csv`
- `figures/detailed_conclusion_directional_extremes.csv`
- `figures/detailed_conclusion_building_distance_gradient.csv`
- `figures/detailed_conclusion_top_morphology_correlations.csv`
- `figures/detailed_conclusion_morphology_tertile_effects.csv`
- `manifests/detailed_conclusion_claims.csv`
