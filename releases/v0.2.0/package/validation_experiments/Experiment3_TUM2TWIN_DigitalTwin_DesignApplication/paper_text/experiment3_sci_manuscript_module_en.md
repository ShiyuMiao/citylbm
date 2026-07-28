# Experiment 3 SCI Manuscript Module: TUM2TWIN Digital-Twin Campus Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Suggested Title

From real urban digital-twin data to CFD-ready wind screening: a FluidX3D experiment on the TUM2TWIN campus core

## Study Positioning

Cases A and E support the preceding solver benchmark layer. Experiment 3 does not re-claim solver accuracy; it tests whether a real urban digital twin can be converted into CFD-ready geometry, simulated in FluidX3D and interpreted as a campus wind-design screening case. The workflow separates UAS/photogrammetry visual assets, semantic LoD/OBJ geometry, Rhino/OBJ management models and closed STL collision boundaries. This positioning follows the evidence boundary required by pedestrian-wind CFD and campus decision-support studies [R1,R5-R7].

## Methods

TUM2TWIN data are divided by function. UAS photogrammetry and textured meshes support scene audit and visual consistency checks; semantic building data and LoD/CAD-derived geometry support closed collision-boundary construction; the user photogrammetry STL is retained as a visual reference and geometry-readiness counterexample rather than as the final LBM collision body. Geometry readiness is recorded by GCRI, with photogrammetry visual STL / core closed-prism collision / district prism collision scores of 0.455 / 0.925 / 0.918.

The FluidX3D core-domain simulation uses dx=2 m, eight inflow directions and three post-spin-up samples at 8000, 10000 and 12000 steps. Post-processing first averages the three samples per direction, then computes equal-weighted eight-direction statistics, Open-Meteo 2024 proxy direction weighting, vertical VR profiles, morphology-response relations and S1/S2 design-sensitivity comparisons. Metrics include mean VR, P75/P90/P95, VR<0.2 low-speed ratio, VR>0.6 acceleration ratio and VR>1.0 high-speed ratio. The Open-Meteo layer is used only as proxy directional sensitivity, not formal annual comfort probability.

## Experimental Setup

The study object is the TUM Downtown campus core corresponding to the photogrammetry visual block. S0 is the core closed-prism collision baseline; S1 is a single light relief corridor; S2 is a three-corridor network-porosity case. S1/S2 share the dx=2 m, eight-direction and three-sample post-processing protocol with S0, so their comparison isolates geometry sensitivity within the present screening design.

## Results

The S0 baseline shows pedestrian-layer ventilation insufficiency rather than a strong-wind hazard. At z~2 m, mean VR / low-speed ratio is 0.076 / 0.934; at z~40 m it becomes 1.049 / 0.000. The vertical contrast shows that above-roof recovery cannot be used as a surrogate for campus pedestrian-space ventilation. Open-Meteo 2024 proxy weighting gives z~2 m mean VR / low-speed ratio of 0.077 / 0.931, close to the equal-weighted result. The low-speed conclusion is therefore stable under this proxy weighting, but this does not support annual Lawson/NEN/AIJ compliance [R5,R8-R10].

The morphology analysis translates traditional canyon/canopy reasoning into a local digital-twin diagnosis. The 0-20 m facade-adjacent band is almost uniformly sheltered, while the 20-50 m local-context band better distinguishes wind recovery. The multivariate robustness result is 0.122+/-0.166 / -0.147 / 0.083; thus morphology variables are useful as interpretable screening descriptors but not as a high-accuracy surrogate model. Sector enclosure and mean height rank above individual footprint, elongation and perimeter-area compactness, indicating that local enclosure, wind-entry opportunity and pressure-exchange continuity are more informative than isolated building shape [R2-R4].

The building-form response archetype addendum gives R1_A1_linear_low_relative_height_recovery / R4_A5_open_or_mixed_low_response / 0.0001682 / 0.0080 vs 0.0007. Because the clusters are formed from basic morphology descriptors and interpreted afterward with FluidX3D-derived wind response, this result supports a combined-form screening typology rather than a causal typology. The stage-transition addendum further separates the near-facade shelter stage from the local-context recovery stage: near/local/recovery mean VR 0.003182 / 0.005560 / 0.002378; best rule mean_height_m_tertile=low + elongation_ratio_tertile=high + relative_enclosure_score_tertile=high / n=5 / mean recovery 0.0065 / top share 1.000; height/sqrt(area) Cliff delta -0.577. This result refines the building-form conclusion. The key contrast is not absolute building size by itself, but whether relative vertical scale, plan continuity and local enclosure allow momentum exchange outside the immediate facade-adjacent sheltered band. The subgroup rule remains sample-internal and must be written as a digital-twin screening descriptor rather than a field-validated morphology threshold.

The S1/S2 design-sensitivity sequence further narrows the design claim. S1 changes z~2 m mean VR / low-speed ratio by -0.000213 / 0.000233; S2 changes them by -0.000466 / 0.000633. Directional trade-off analysis gives 315 deg / 0.002374 / 0.006646. S1/S2 should therefore be interpreted as negative design evidence: geometric opening area alone does not recover pedestrian ventilation unless aligned with effective inflow sectors, momentum entry and pressure-exchange paths.

## Discussion

Compared with idealized canyon or simplified urban-block studies, the added value of this experiment is not a claim of higher predictive accuracy but a traceable digital-twin-to-CFD conversion pathway. Photogrammetry and 3DGS-like assets provide visual realism and scene audit capability, whereas final FluidX3D/CityLBM collision boundaries require semantic or LoD/CAD-derived closed geometry [R11,R12]. The wind-design interpretation also shifts from strong-wind danger toward persistent ventilation insufficiency and its local morphology controls.

## Limitations

The module does not claim field validation, wind-tunnel closure, formal annual comfort/safety compliance, pollutant dispersion, positive S3-Sn optimization, GCBTE closure or CityLBM-Grasshopper end-to-end execution. Open-Meteo is a climate proxy, not a measured site wind rose; S1/S2 are negative sensitivity tests, not final design proposals; and morphology statistics are explanatory screening evidence, not a replacement for CFD or measurement.

## Abstract-Ready Takeaway

The experiment demonstrates that TUM2TWIN digital-twin data can be transformed through semantic closed geometry into a FluidX3D-ready campus wind-screening workflow. The tested campus core shows persistent pedestrian-layer low-speed conditions, upper-layer flow recovery and local enclosure-controlled wind recovery, while the negative S1/S2 sensitivity results indicate that design intervention should move from simple porosity area toward wind-sector-coupled momentum entry and pressure-exchange continuity.

## Reference Key

[R1] Blocken; Stathopoulos; van Beeck (2016). Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment. Building and Environment, 100, 50-81. doi:10.1016/j.buildenv.2016.02.004.
[R2] Oke (1988). Street design and urban canopy layer climate. Energy and Buildings, 11, 103-113. doi:10.1016/0378-7788(88)90026-6.
[R3] Cheng; Liu; Leung (2009). On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number. Building Simulation, 2, 53-61. doi:10.1007/S12273-008-8332-4.
[R4] Tsang; Kwok; Hitchcock (2012). Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium. Building and Environment, 49, 167-181. doi:10.1016/j.buildenv.2011.08.014.
[R5] Janssen; Blocken; van Hooff (2013). Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study. Building and Environment, 59, 547-562. doi:10.1016/j.buildenv.2012.10.012.
[R6] Blocken; Janssen; van Hooff (2012). CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus. Environmental Modelling and Software, 30, 15-34. doi:10.1016/j.envsoft.2011.11.009.
[R7] Hagbo; Giljarhus (2022). Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions. Frontiers in Built Environment, 8. doi:10.3389/fbuil.2022.858067.
[R8] Peel; Finlayson; McMahon (2007). Updated world map of the Koppen-Geiger climate classification. Hydrology and Earth System Sciences, 11, 1633-1644. doi:10.5194/hess-11-1633-2007.
[R9] Beck et al. (2018). Present and future Koppen-Geiger climate classification maps at 1-km resolution. Scientific Data, 5. doi:10.1038/sdata.2018.214.
[R10] Fadl; Karadelis (2013). CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus. International Journal of Architecture, Engineering and Construction, 2, 131-143. doi:10.7492/IJAEC.2013.013.
[R11] TUM2TWIN project (2025). TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks. Official TUM2TWIN website.
[R12] Hagbo; Giljarhus; Hjertager (2020). Influence of geometry acquisition method on pedestrian wind simulations. arXiv:2010.12371.
