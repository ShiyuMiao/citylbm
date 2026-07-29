# Building Form and Wind Environment: Literature Context and New Insights from the TUM2TWIN Case

evidence_type: newly_run + preexisting_artifact

## 1. Purpose

This note connects the current TUM2TWIN/FluidX3D experiment with traditional conclusions in urban wind-environment research. It answers two questions:

1. What has the field traditionally concluded about building form and wind-environment distribution?
2. What new knowledge can this experiment add beyond those traditional conclusions?

The goal is not to claim field-validated wind comfort compliance. The goal is to position this experiment as a digital-twin-to-CFD application study with a morphology-aware interpretation.

## 2. Literature Sources Checked

| Source | Key contribution used here | Evidence type |
|---|---|---|
| Blocken, Stathopoulos & van Beeck, 2016, *Building and Environment*, DOI: 10.1016/j.buildenv.2016.02.004 | Pedestrian-level wind studies commonly use wind tunnel or CFD; results are expressed as local amplification factors; CFD/wind-tunnel accuracy is stronger for high amplification factors and weaker for low amplification factors. Link: https://research.tue.nl/en/publications/pedestrian-level-wind-conditions-around-buildings-review-of-wind-/ | preexisting_artifact |
| Blocken / Urban Physics pedestrian wind comfort page | Building construction changes the local microclimate; changes depend on building shape, size, orientation and surrounding obstacles; high-rise bases can create uncomfortable/dangerous winds. Link: https://www.urbanphysics.net/windcomfort.htm | preexisting_artifact |
| Oke, 1988, *Energy and Buildings*, "Street design and urban canopy layer climate" | Classic street-canyon view: open geometry helps pollution dispersion and solar access, while dense clustered geometry can provide shelter/energy conservation; H/W is central to canopy-layer climate. Link: https://www.semanticscholar.org/paper/Street-design-and-urban-canopy-layer-climate-Oke/53f2f26fc301dbeb032acff79547833d7eed391f | preexisting_artifact |
| Cheng, Liu & Leung, 2009, *Building Simulation*, DOI: 10.1007/S12273-008-8332-4 | Street-canyon ventilation depends on aspect ratio h/b; turbulent exchange can dominate air exchange in isothermal street canyons. Link: https://link.springer.com/article/10.1007/S12273-008-8332-4 | preexisting_artifact |
| Janssen, Blocken & van Hooff, 2013, *Building and Environment*, DOI: 10.1016/j.buildenv.2012.10.012 | Wind comfort assessment combines meteorological statistics, aerodynamic information and a comfort criterion; different criteria can lead to different comfort conclusions. Link: https://research.tue.nl/en/publications/pedestrian-wind-comfort-around-buildings-comparison-of-wind-comfo/ | preexisting_artifact |
| Tsang, Kwok & Hitchcock, 2012, *Building and Environment*, DOI: 10.1016/j.buildenv.2011.08.014 | Building dimensions, separation, row forms and podiums affect pedestrian-level air movement; wider buildings, small separations and podiums can adversely affect ventilation. Link: https://researchers.westernsydney.edu.au/en/publications/wind-tunnel-study-of-pedestrian-level-wind-environment-around-tal/ | preexisting_artifact |
| Haegbo, Giljarhus & Hjertager, 2020, arXiv:2010.12371 | Geometry acquisition method affects pedestrian wind simulation; geometry quality is essential, and different building-model sources can change simulated wind fields. Link: https://arxiv.org/abs/2010.12371 | preexisting_artifact |

## 3. Traditional Conclusions on Building Form and Wind Distribution

### 3.1 Tall buildings and local acceleration/downwash

Traditional pedestrian wind research emphasizes that individual buildings, especially high-rise buildings, can redirect faster upper-level wind toward the ground, producing high-speed regions near bases, corners, passages and exposed plazas. Building shape, size, orientation and neighbouring obstacles jointly determine whether the local change is favourable or unfavourable.

Implication for this experiment:

- If the TUM2TWIN core block had strong isolated tower-downwash behaviour, we would expect more localized VR>0.6 or VR>1.0 zones around corners and exposed building edges.
- Our result instead shows sparse repeated acceleration at z~2 m: only about 2.5% of open cells are accelerated under at least 2/8 directions.

Interpretation:

- The current core block behaves less like an isolated high-rise downwash case and more like a dense, sheltered canopy/block case at pedestrian height.

### 3.2 Street-canyon aspect ratio and skimming/recirculating flow

Street-canyon theory classically links H/W to flow regime and ventilation. Open or low-aspect streets allow more external flow penetration; deeper or more continuous canyons tend to develop recirculation/skimming behaviour, where exchange with the above-roof flow is limited and turbulent exchange becomes important.

Implication for this experiment:

- The core TUM Downtown geometry contains courtyards, narrow passages, enclosed blocks and partial street canyons rather than idealized single canyons.
- Our vertical profile is consistent with a canopy-layer sheltering pattern: mean VR is about 0.076 at 2 m and recovers to about 1.05 at 40 m, while VR<0.2 stagnation ratio drops from about 0.93 at 2 m to 0 at 40 m.

Interpretation:

- Traditional H/W theory explains the direction of the effect, but our experiment extends it from ideal canyon geometry to an irregular real digital-twin block.

### 3.3 Building width, separation, podiums and porosity

Parametric wind-tunnel studies around tall buildings show that building width, separation distance, row configuration and podium form affect pedestrian-level ventilation. Wider blocks, insufficient separations and podium-like continuous masses can reduce pedestrian air movement.

Implication for this experiment:

- The TUM2TWIN core block is not a single tower but an aggregate of continuous wings, courtyards and separated fragments.
- The robust stagnation result suggests that reduced porosity and blocked near-ground passages can dominate over individual wind-direction differences.

Interpretation:

- The important form variable in this real block is not just height, but the connectivity/porosity of open paths through the block.

### 3.4 Wind comfort depends on climate weighting and criteria

Traditional wind-comfort studies combine aerodynamic information with meteorological statistics and comfort criteria such as Lawson, Davenport, Melbourne or NEN 8100. The same aerodynamic field can lead to different comfort classifications depending on the criterion.

Implication for this experiment:

- We used Open-Meteo 2024 as a proxy wind-climate weighting layer, but we did not compute formal Lawson/NEN/AIJ annual exceedance classes.
- Therefore, our results support aerodynamic/morphological diagnosis, not final regulatory comfort classification.

Interpretation:

- The paper should report VR, stagnation probability and direction robustness as morphology-oriented screening indicators, and reserve formal comfort compliance for future measured or standardized annual assessment.

### 3.5 Geometry model quality matters

Recent work on geometry acquisition for pedestrian wind simulations notes that model source and geometric representation can influence simulated wind fields. This aligns directly with the present digital-twin problem.

Implication for this experiment:

- TUM2TWIN photogrammetry/Rhino data match the visual scene but are not watertight collision boundaries.
- LoD3-derived closed prism geometry is required for stable FluidX3D voxelization.

Interpretation:

- This experiment links traditional wind-environment morphology research with a new data-readiness problem: before discussing morphology-wind causality, the digital twin must first be converted into a physically usable collision boundary.

## 4. What This Experiment Adds Beyond Traditional Conclusions

### New insight 1: From form typology to real-block morphology

Traditional conclusions often come from idealized street canyons, isolated towers, or parametric podium/tower models. This experiment applies the same logic to an irregular real campus block reconstructed from TUM2TWIN. The main contribution is not discovering that dense geometry reduces near-ground wind; it is showing how that conclusion manifests in a real, visually verifiable digital-twin block with courtyards, irregular passages and mixed building heights.

### New insight 2: Directional robustness replaces single-wind-direction interpretation

Traditional case studies often emphasize wind-direction-specific maps. Our deepened analysis shows that the main pedestrian-layer diagnosis is directionally robust:

- 91.5% of open z~2 m cells are stagnant under at least 6/8 wind directions.
- 87.2% are stagnant under all 8 directions.
- Open-Meteo weighted mean stagnation probability is 0.9285.

This means the low-wind-speed distribution is a stable property of the block morphology, not merely a directional artefact.

### New insight 3: The result reframes the wind issue from "strong-wind danger" to "ventilation insufficiency"

Pedestrian wind literature often focuses on high-speed discomfort and safety near tall buildings. Our case shows the other side of the wind-environment problem: in a dense historic/campus block, repeated acceleration is sparse, while widespread low-speed stagnation dominates.

Evidence:

- Only about 2.5% of open cells exceed VR>0.6 under at least 2/8 directions.
- VR<0.2 dominates most of the pedestrian layer.

This supports a paper argument centred on ventilation insufficiency, pollutant retention risk and summer heat-stress relevance, while explicitly avoiding unsupported safety/compliance claims.

### New insight 4: Vertical recovery identifies a morphology-driven canopy interface

Traditional canopy theory predicts sheltering within the canopy and stronger flow above roof level. Our result quantifies this for the TUM2TWIN core block:

- Mean VR rises from about 0.076 at 2 m to about 1.05 at 40 m.
- Stagnation ratio falls from about 0.93 at 2 m to 0 at 40 m.

This provides a bridge between pedestrian wind environment and UAV/low-altitude wind exposure. The same block that is poorly ventilated at pedestrian level may be much more exposed above the canopy.

### New insight 5: Digital-twin data readiness becomes part of the wind-environment methodology

Traditional morphology studies usually start from already-clean CAD or ideal geometry. This experiment shows that for real digital twins:

- photogrammetry/3DGS-like visual meshes are visual evidence but poor collision boundaries;
- semantic LoD2/LoD3 data are the route to CFD-ready solids;
- geometry-to-CFD readiness is itself a measurable research object.

This creates a methodological contribution: a real urban digital twin is not automatically a CFD model; its layers must be functionally assigned before wind-environment conclusions can be trusted.

## 5. Recommended Paper-Level Argument

Traditional urban wind research explains that building height, width, spacing, street-canyon aspect ratio, podium continuity and porosity shape pedestrian-level wind through downwash, corner acceleration, channelization, recirculation and skimming-flow sheltering. The TUM2TWIN experiment does not overturn these conclusions. Instead, it extends them into a real digital-twin workflow: after converting visual/semantic data into a closed LoD3-derived FluidX3D boundary, the core block exhibits directionally robust pedestrian-layer stagnation rather than widespread acceleration. This suggests that, for dense courtyard/block morphologies, the key wind-environment issue may shift from isolated high-speed discomfort to persistent low-ventilation zones, and that digital-twin geometry readiness is a prerequisite for making this morphology-wind relationship computationally testable.

## 6. Citation-to-Claim Map

| Claim | Literature support | Experiment support | Claim readiness |
|---|---|---|---|
| Buildings alter pedestrian wind depending on shape, size, orientation and surroundings | Blocken/Urban Physics; Blocken et al. 2016 | TUM2TWIN geometry and FluidX3D maps | paper_ready |
| Deep/continuous street-block geometries tend to suppress pedestrian-layer exchange | Oke 1988; Cheng et al. 2009 | VR<0.2 robust stagnation maps and vertical recovery | paper_ready as simulation interpretation |
| Building width, separation and podium/continuous massing affect pedestrian air movement | Tsang et al. 2012 | Dense block + sparse repeated acceleration | paper_ready as qualitative link |
| Wind comfort needs climate statistics and criteria | Janssen et al. 2013 | Open-Meteo proxy weighting but no formal comfort class | weaken_claim for comfort compliance |
| Geometry acquisition affects pedestrian wind simulation | Haegbo et al. 2020 | photogrammetry STL vs LoD3-derived closed prism QA | paper_ready |
