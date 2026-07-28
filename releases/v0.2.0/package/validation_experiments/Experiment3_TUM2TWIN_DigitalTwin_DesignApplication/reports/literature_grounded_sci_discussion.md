# Literature-Grounded SCI Discussion for Experiment 3

evidence_type: newly_run + preexisting_artifact + blocked

This report deepens the Experiment 3 conclusion by binding each manuscript claim to verified literature, archived FluidX3D/ParaView statistics, geometry QA, and explicit evidence boundaries. It does not introduce new CFD results.

## 1. Verified Reference Layer

| ref_id | status | authors | year | title | source | doi | url |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | verified_crossref | Blocken; Stathopoulos; van Beeck | 2016 | Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment | Building and Environment, 100, 50-81 | 10.1016/j.buildenv.2016.02.004 | https://doi.org/10.1016/j.buildenv.2016.02.004 |
| R2 | verified_crossref | Oke | 1988 | Street design and urban canopy layer climate | Energy and Buildings, 11, 103-113 | 10.1016/0378-7788(88)90026-6 | https://doi.org/10.1016/0378-7788(88)90026-6 |
| R3 | verified_crossref | Cheng; Liu; Leung | 2009 | On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number | Building Simulation, 2, 53-61 | 10.1007/S12273-008-8332-4 | https://doi.org/10.1007/s12273-008-8332-4 |
| R4 | verified_crossref | Tsang; Kwok; Hitchcock | 2012 | Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium | Building and Environment, 49, 167-181 | 10.1016/j.buildenv.2011.08.014 | https://doi.org/10.1016/j.buildenv.2011.08.014 |
| R5 | verified_crossref | Janssen; Blocken; van Hooff | 2013 | Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study | Building and Environment, 59, 547-562 | 10.1016/j.buildenv.2012.10.012 | https://doi.org/10.1016/j.buildenv.2012.10.012 |
| R6 | verified_crossref | Blocken; Janssen; van Hooff | 2012 | CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus | Environmental Modelling and Software, 30, 15-34 | 10.1016/j.envsoft.2011.11.009 | https://doi.org/10.1016/j.envsoft.2011.11.009 |
| R7 | verified_crossref | Hagbo; Giljarhus | 2022 | Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions | Frontiers in Built Environment, 8 | 10.3389/fbuil.2022.858067 | https://doi.org/10.3389/fbuil.2022.858067 |
| R8 | verified_crossref | Peel; Finlayson; McMahon | 2007 | Updated world map of the Koppen-Geiger climate classification | Hydrology and Earth System Sciences, 11, 1633-1644 | 10.5194/hess-11-1633-2007 | https://doi.org/10.5194/hess-11-1633-2007 |
| R9 | verified_crossref | Beck et al. | 2018 | Present and future Koppen-Geiger climate classification maps at 1-km resolution | Scientific Data, 5 | 10.1038/sdata.2018.214 | https://doi.org/10.1038/sdata.2018.214 |
| R10 | verified_crossref | Fadl; Karadelis | 2013 | CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus | International Journal of Architecture, Engineering and Construction, 2, 131-143 | 10.7492/IJAEC.2013.013 | https://doi.org/10.7492/ijaec.2013.013 |
| R11 | verified_official_url | TUM2TWIN project | 2025 | TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks | Official TUM2TWIN website |  | https://tum2t.win/datasets |
| R12 | verified_url_pending_bibliographic_form | Hagbo; Giljarhus; Hjertager | 2020 | Influence of geometry acquisition method on pedestrian wind simulations | arXiv:2010.12371 |  | https://arxiv.org/abs/2010.12371 |

## 2. Citation-to-Claim Map

| claim_id | claim | inline_marker | reference_ids | claim_support_type | experiment_support | evidence_boundary |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | 本实验应定位为真实数字孪生街区的风环境筛查与设计解释，而非实测验证或法规级舒适度判定。 | [R1,R5,R6] | R1;R5;R6 | literature_boundary + newly_run_screening | FluidX3D 8-direction time-mean VR fields; no field or wind-tunnel closure. | Do not claim field-validated prediction accuracy or formal Lawson/NEN/AIJ compliance. |
| C2 | TUM Downtown core block is better described as a sheltered campus/block canopy than as an isolated high-rise downwash case. | [R2,R3,R4] | R2;R3;R4 | traditional_theory_consistency + newly_run | z=2 m mean VR=0.076; VR<0.2 ratio=93.35%; repeated acceleration is sparse. | Consistent with canopy/canyon sheltering, not a causal proof of every individual form mechanism. |
| C3 | 主结论应从强风危险转向通风不足：低速区跨风向稳定，而高风速加速区很少。 | [R1,R7] | R1;R7 | newly_run_directional_robustness + literature_context | 87.25% of pedestrian open cells stagnant under all 8 directions; 91.49% stagnant under >=6/8 directions. | Supports aerodynamic screening, not pollutant or thermal-risk quantification. |
| C4 | 20-50 m local-context morphology explains wind recovery better than single-building footprint/shape descriptors. | [R2,R3,R4] | R2;R3;R4 | newly_run_statistical_analysis + traditional_form_logic | context-only CV R2=0.325 versus size-height-shape CV R2=-0.130; sector enclosure rho=-0.396. | Component-level association; do not write as causal identification. |
| C5 | 数字孪生底层模型的表现是本实验的方法贡献：视觉真实不等于 CFD-ready。 | [R11,R12] | R11;R12 | digital_twin_method + geometry_QA | photogrammetry visual STL GCRI=0.455; accepted core/district prism GCRI=0.925/0.918; LoD/closed-prism geometry simulated in FluidX3D. | No computed GCBTE because no independent 3DGS-derived collision extraction was available. |
| C6 | 气候区与校园建筑类型可用于解释应用场景，但 Open-Meteo 2024 代理不能替代正式风玫瑰。 | [R5,R8,R9,R10] | R5;R8;R9;R10 | contextualization + proxy_sensitivity | Open-Meteo weighting changes z=2 m mean VR by only 0.0004 relative to equal-weighted 8-direction average. | Use as climate proxy sensitivity only; no annual exceedance probability comfort classification. |

## 3. Data-Driven Conclusion Synthesis

The most defensible conclusion is not that the real campus block has been field-validated, but that a multimodal digital twin can be converted into a simulation-ready urban-wind screening workflow. Traditional pedestrian-wind literature shows that building geometry, spacing, canyon aspect ratio, podium continuity and surrounding obstacles shape near-ground airflow [R1-R4]. The TUM2TWIN result is consistent with that tradition, but its added value is the real-block translation: visual photogrammetry, semantic building data, Rhino/OBJ management and closed-prism STL collision boundaries are separated into different functional layers before FluidX3D simulation.

The aerodynamic pattern is dominated by low-speed sheltering rather than high-speed danger. At z=2 m, mean VR is 0.076, the VR<0.2 stagnation ratio is 93.35%, and the VR>0.6 acceleration ratio is only 1.30%. By z=40 m, mean VR recovers to 1.049. This vertical gradient supports a canopy-decoupling interpretation: the upper flow recovers above roof scale, while pedestrian paths inside the block remain weakly ventilated.

The building-form conclusion can now be written more sharply. The near-facade 0-20 m band is almost uniformly sheltered, so it is less useful for distinguishing design mechanisms. The 20-50 m local-context band is more diagnostic: the sector-enclosure correlation with mean VR is rho=-0.396; combined enclosure remains negative under bootstrap resampling (rho=-0.302, 95% CI [-0.483, -0.097]); and the context-only model reaches cross-validated R2=0.325, compared with R2=-0.130 for the size-height-shape-only model. The stronger design reading is therefore about local enclosure, passage continuity and neighborhood porosity, not about isolated footprint size or elongation alone.

The distance gradient strengthens this interpretation. Even cells more than 20 m from the nearest building have mean VR=0.095 and a low-speed ratio of 90.79%. The stagnation problem is therefore not merely a facade boundary-layer artifact; it propagates across the campus pedestrian network.

The digital-twin model result is a separate methodological contribution. The textured photogrammetry visual mesh has GCRI=0.455, while the accepted core and district closed-prism collision geometries have GCRI=0.925 and 0.918. This supports the claim that visual fidelity and CFD readiness are different properties. In this experiment, photogrammetry is valuable for scope audit and scene consistency, but semantic/closed geometry is the defensible collision-boundary route.

## 4. What Is New Relative to Traditional Conclusions

1. The experiment translates traditional canyon/block-wind reasoning from idealized geometry into a real, visually auditable campus digital-twin block.
2. It reframes the site problem from strong-wind safety to persistent ventilation insufficiency, which is more relevant for dense campus courtyards and pedestrian networks.
3. It shows that local-context morphology is more explanatory than individual-building size descriptors within this low-speed background.
4. It makes geometry readiness an explicit wind-environment variable: the same urban scene can be visually credible but physically unsuitable for LBM collision until repaired or semantically reconstructed.

## 5. Claim Boundary

These conclusions are paper-ready as simulation-based design-screening and morphology-interpretation claims. They are not field validation, wind-tunnel validation, formal annual wind-comfort/safety compliance, pollutant dispersion prediction, S1-Sn intervention proof, CityLBM-GH end-to-end execution, or a computed 3DGS-to-collision transfer-error result.
