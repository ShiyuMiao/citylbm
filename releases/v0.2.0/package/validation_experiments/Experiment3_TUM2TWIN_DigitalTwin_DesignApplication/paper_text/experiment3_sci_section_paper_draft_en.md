# Experiment 3 Draft Section: TUM2TWIN Digital-Twin Campus Wind Application

evidence_type: newly_run + preexisting_artifact + blocked

## Study Aim and Positioning

Following AIJ Cases A and E as the benchmark layer, Experiment 3 evaluates whether real urban digital-twin data can be translated into CFD-ready geometry and used for campus wind-screening and design interpretation. TUM2TWIN provides visual photogrammetry, semantic/CAD-derived geometry and Rhino/OBJ management assets. These layers are functionally different: photogrammetry and 3DGS-like assets are useful for visual audit and scene consistency, whereas FluidX3D/CityLBM collision boundaries require closed semantic or CAD-derived geometry. This boundary follows established pedestrian-wind CFD practice, where simulation uncertainty and comfort assessment chains must be stated before compliance claims are made [1,5,6].

## Data-to-CFD Workflow

The workflow separates visual reference, semantic geometry, collision geometry and solver input. The textured photogrammetry mesh is used to audit the study extent; the user Rhino model confirms consistency with the TUM Downtown visual block; LoD/OBJ/CAD-derived data provide z0-aligned closed STL collision bodies; and the accepted core closed-prism geometry is used in FluidX3D. GCRI scores for the photogrammetry visual STL, core prism and district prism are `0.455 / 0.925 / 0.918`, showing that visual fidelity and CFD readiness are separable properties of the same digital twin [11,12].

## Simulation Protocol

The FluidX3D core-domain simulation uses dx=2 m, eight inflow directions and three post-spin-up samples at 8000, 10000 and 12000 steps. Metrics include mean VR, P75/P90/P95, VR<0.2 low-speed ratio, VR>0.6 acceleration ratio and VR>1.0 high-speed ratio. Open-Meteo 2024 is used only as a proxy directional weighting layer and not as a measured site wind rose or annual comfort-compliance input [5,7,8,9].

## Results

The S0 baseline indicates persistent pedestrian-layer ventilation insufficiency rather than a strong-wind hazard. At z~2 m, mean VR / low-speed ratio is `0.076 / 0.934`; at z~40 m it becomes `1.049 / 0.000`. Thus, above-roof recovery cannot substitute for pedestrian-space assessment in campus courtyards, entrances and connecting streets. The Open-Meteo proxy-weighted z~2 m mean VR / low-speed ratio is `0.077 / 0.931`, close to the equal-weighted result, supporting the stability of the low-speed screening conclusion but not formal Lawson/NEN/AIJ compliance [5,7,10].

Morphology analysis converts traditional canopy and canyon reasoning into a local digital-twin diagnosis [2,3,4]. The 0-20 m facade-adjacent band is almost uniformly sheltered, whereas the 20-50 m local-context band reveals morphology-dependent recovery. The multivariate robustness result is `0.122+/-0.166 / -0.147 / 0.083`, so morphology variables should be treated as interpretable screening descriptors rather than a high-accuracy surrogate model. The threshold-rule addendum gives `mean_height_m=low_tertile + elongation_ratio=high_tertile / 0.0057 / 0.857 / -0.416`, moving the design interpretation from isolated building size or opening area toward combined local exposure, relative vertical scale and plan continuity. The rule remains sample-internal and should not be generalized as a field-validated design threshold.

A morphology-response archetype addendum further clusters the 101 components by basic form variables alone and then interprets the resulting groups using the FluidX3D-derived response metrics. The groups differ in 20-50 m recovery delta with Kruskal-Wallis `p=0.0001682`; the strongest archetype has 20-50 m mean VR / recovery delta of `0.0237 / 0.0080`, whereas the weakest has `0.0043 / 0.0007`. This supports a more detailed conclusion that the campus-core response is controlled by combinations of relative vertical massing, elongation and local enclosure, not by a single footprint, height or porosity descriptor.

The S1/S2 design-sensitivity sequence tests whether additional porosity can relieve the low-speed condition. S1 changes z~2 m mean VR / low-speed ratio by `-0.000213 / 0.000233`, and S2 changes them by `-0.000466 / 0.000633`. Directional local response is `315 deg / 0.002374 / 0.006646`. S1/S2 therefore provide negative design evidence: geometric porosity alone is insufficient unless coupled to effective inflow sectors, momentum entry and pressure-exchange paths.

## Discussion and Evidence Boundary

The main contribution of Experiment 3 is a traceable digital-twin-to-CFD application chain and a morphology-informed campus wind-screening interpretation. It does not claim field validation, wind-tunnel closure, annual comfort/safety compliance, pollutant dispersion, successful S3-Sn optimization, GCBTE closure or CityLBM-Grasshopper end-to-end execution. Future compliance work requires a calibrated wind rose, threshold exceedance probabilities, grid/time sensitivity, field or wind-tunnel closure and additional scalar or thermal coupling where relevant.

## References

[1] Blocken; Stathopoulos; van Beeck (2016). Pedestrian-level wind conditions around buildings: Review of wind-tunnel and CFD techniques and their accuracy for wind comfort assessment. Building and Environment, 100, 50-81. doi:10.1016/j.buildenv.2016.02.004. https://doi.org/10.1016/j.buildenv.2016.02.004
[2] Oke (1988). Street design and urban canopy layer climate. Energy and Buildings, 11, 103-113. doi:10.1016/0378-7788(88)90026-6. https://doi.org/10.1016/0378-7788(88)90026-6
[3] Cheng; Liu; Leung (2009). On the comparison of the ventilation performance of street canyons of different aspect ratios and Richardson number. Building Simulation, 2, 53-61. doi:10.1007/S12273-008-8332-4. https://doi.org/10.1007/s12273-008-8332-4
[4] Tsang; Kwok; Hitchcock (2012). Wind tunnel study of pedestrian level wind environment around tall buildings: Effects of building dimensions, separation and podium. Building and Environment, 49, 167-181. doi:10.1016/j.buildenv.2011.08.014. https://doi.org/10.1016/j.buildenv.2011.08.014
[5] Janssen; Blocken; van Hooff (2013). Pedestrian wind comfort around buildings: Comparison of wind comfort criteria based on whole-flow field data for a complex case study. Building and Environment, 59, 547-562. doi:10.1016/j.buildenv.2012.10.012. https://doi.org/10.1016/j.buildenv.2012.10.012
[6] Blocken; Janssen; van Hooff (2012). CFD simulation for pedestrian wind comfort and wind safety in urban areas: General decision framework and case study for the Eindhoven University campus. Environmental Modelling and Software, 30, 15-34. doi:10.1016/j.envsoft.2011.11.009. https://doi.org/10.1016/j.envsoft.2011.11.009
[7] Hagbo; Giljarhus (2022). Pedestrian Wind Comfort Assessment Using Computational Fluid Dynamics Simulations With Varying Number of Wind Directions. Frontiers in Built Environment, 8. doi:10.3389/fbuil.2022.858067. https://doi.org/10.3389/fbuil.2022.858067
[8] Peel; Finlayson; McMahon (2007). Updated world map of the Koppen-Geiger climate classification. Hydrology and Earth System Sciences, 11, 1633-1644. doi:10.5194/hess-11-1633-2007. https://doi.org/10.5194/hess-11-1633-2007
[9] Beck et al. (2018). Present and future Koppen-Geiger climate classification maps at 1-km resolution. Scientific Data, 5. doi:10.1038/sdata.2018.214. https://doi.org/10.1038/sdata.2018.214
[10] Fadl; Karadelis (2013). CFD Simulation for Wind Comfort and Safety in Urban Area: A Case Study of Coventry University Central Campus. International Journal of Architecture, Engineering and Construction, 2, 131-143. doi:10.7492/IJAEC.2013.013. https://doi.org/10.7492/ijaec.2013.013
[11] TUM2TWIN project (2025). TUM2TWIN dataset pages: mesh, buildings, vegetation, CAD and benchmarks. Official TUM2TWIN website. https://tum2t.win/datasets
[12] Hagbo; Giljarhus; Hjertager (2020). Influence of geometry acquisition method on pedestrian wind simulations. arXiv:2010.12371. https://arxiv.org/abs/2010.12371
