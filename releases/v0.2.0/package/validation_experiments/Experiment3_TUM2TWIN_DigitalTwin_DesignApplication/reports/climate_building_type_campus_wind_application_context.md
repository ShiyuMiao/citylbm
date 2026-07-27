# Climate, Building Type, and Campus Wind-Environment Application Context

evidence_type: newly_run + preexisting_artifact

## 1. Purpose

This note strengthens the conclusion/discussion layer of the TUM2TWIN wind-environment experiment. It adds three contextual dimensions that should shape the final claims:

1. the climatic setting of Munich;
2. the building type and campus morphology of the TUM city-centre campus;
3. the performance and limitations of digital-twin base models for wind-environment simulation.

The goal is to discuss what the present FluidX3D/ParaView evidence can support for a campus environment, while keeping the boundary clear: no field-validated comfort compliance, no measured pollutant result, and no claim that photogrammetry/3DGS visual models are ready collision geometry.

## 2. Sources Checked

| Source | Information used | Evidence type |
|---|---|---|
| TUM campus locations page, https://www.tum.de/en/about-tum/locations | TUM has been in Munich since 1868; the Munich home site is in the city center and extends to other Munich facilities. | preexisting_artifact |
| TUM2TWIN TUM ED news page, https://www.ed.tum.de/en/ed/news-single-view-start/article/tum2twin-the-digital-twin-of-the-munich-tum-campus-pushes-the-limits/ | TUM2TWIN is a digital twin of the TUM campus in Munich city centre; it contains 32 high-resolution multimodal datasets and covers about 100,000 m2; the campus is a complex urban scenario with buildings of different architectural styles. | preexisting_artifact |
| TUM2TWIN arXiv paper, https://arxiv.org/html/2505.07396v2 | TUM2TWIN provides georeferenced and semantically aligned 3D models and networks with terrestrial, mobile, aerial and satellite observations; it supports downstream tasks including LoD3 building reconstruction and view synthesis. | preexisting_artifact |
| Climate-Data.org Munich page, https://en.climate-data.org/europe/germany/free-state-of-bavaria/munich-6426/ | Munich is described as mild/moderate, wet throughout the year, Cfb by Koeppen-Geiger; approximate annual mean temperature 8.8 deg C and annual precipitation 1000 mm. | preexisting_artifact |
| meteoblue Munich modelled climate page, https://www.meteoblue.com/en/weather/historyclimate/climatemodelled/munich_germany_2867714 | Munich climate diagrams include wind-speed frequency and wind rose from modelled historical climate data; this supports using a wind-climate weighting layer but not field-validated local campus wind measurement. | preexisting_artifact |
| Peel et al. 2007, Hydrology and Earth System Sciences, https://hess.copernicus.org/articles/11/1633/2007/hess-11-1633-2007.html | Koeppen-Geiger classification remains widely used for climatic regionalisation; classification is based on long-term monthly precipitation and temperature. | preexisting_artifact |
| Beck et al. 2018, Scientific Data, https://pmc.ncbi.nlm.nih.gov/articles/PMC6207062/ | High-resolution present/future Koeppen-Geiger maps are available for climate-zone context; use only as climate-regional background unless local grid value is extracted. | preexisting_artifact |
| Blocken et al. 2012, Environmental Modelling & Software, DOI: 10.1016/j.envsoft.2011.11.009, https://research.tue.nl/en/publications/cfd-simulation-for-pedestrian-wind-comfort-and-wind-safety-in-urb/ | Campus wind comfort/safety has been studied with CFD using meteorological data, aerodynamic simulations and comfort/safety criteria; the Eindhoven campus case shows the relevance of campuses as wind-environment application sites. | preexisting_artifact |
| Fadl and Karadelis 2013, Coventry University campus, DOI: 10.7492/IJAEC.2013.013, https://pureportal.coventry.ac.uk/en/publications/cfd-simulation-for-wind-comfort-and-safety-in-urban-area-a-case-s-2/ | A university campus case study used CFD to evaluate pedestrian-level wind around campus buildings, supporting the broader campus-planning relevance of wind simulations. | preexisting_artifact |
| Present FluidX3D/ParaView outputs in this project | 8-direction VTK results, robust stagnation metrics, vertical recovery, building-distance statistics and ParaView state. | newly_run |

## 3. Climate-Zone Implications for the Conclusion

Munich should not be treated as a hot-arid or tropical campus case. The available climate references place it in a mild, wet, temperate setting, commonly reported as Koeppen-Geiger Cfb, with significant rainfall across the year and a cool-to-mild annual thermal regime. This matters for conclusion writing in three ways.

First, the main wind-environment value is not only protection from dangerous gusts. In a temperate, humid, year-round precipitation climate, campus wind design should also address ventilation insufficiency, moisture/pollution retention, outdoor thermal comfort during warm periods, and shelter/comfort during cold or wet seasons.

Second, the present Open-Meteo/meteoblue-style wind-climate weighting should be described as a proxy climate layer. It is useful for testing whether the aerodynamic result remains important under plausible local wind-frequency patterns, but it is not equivalent to a local mast measurement campaign on the TUM campus.

Third, because Munich is not a persistently high-wind coastal or high-rise downtown case, the observed low pedestrian-layer VR should be interpreted as a morphology-controlled ventilation finding rather than as a contradiction of high-wind comfort literature.

## 4. Building Type and Campus Morphology

The TUM city-centre campus is better framed as a dense, historical urban campus embedded in Munich's central fabric, not as a suburban greenfield campus and not as a high-rise cluster. TUM2TWIN itself describes the campus as a complex urban scenario with buildings of different architectural styles. The geometry used in the present experiment further indicates a block/courtyard morphology: continuous wings, narrow passages, internal courtyards, multiple roof heights, and limited near-ground porosity.

This building type changes the interpretation of wind distribution:

- The dominant risk in the present result is not widespread high-speed pedestrian discomfort.
- The dominant pattern is a robust low-ventilation layer around the pedestrian plane.
- Building continuity, courtyard enclosure, passage connectivity and near-ground porosity become more important explanatory variables than height alone.
- The vertical recovery pattern, from very low pedestrian-layer VR to approximately free-stream-like flow above the canopy, is consistent with a sheltered urban canopy/block form.

## 5. Digital-Twin Base Model Performance in Wind Simulation

The digital twin performs well when its layers are functionally assigned instead of treated as interchangeable 3D objects.

### 5.1 Visual fidelity layer

The TUM2TWIN photogrammetry/Rhino/OBJ texture model is strong for:

- confirming that the simulated object matches the real TUM downtown campus extent;
- communicating the campus setting to architecture and planning readers;
- identifying visible courtyards, streets, roofs, vegetation traces and facade complexity.

Its weakness is CFD readiness. The visual mesh is not a reliable closed rigid collision boundary. Its visual fidelity should not be mistaken for watertightness, semantic correctness or stable voxelization.

### 5.2 Semantic geometry layer

CityGML LoD2/LoD3 and CAD/OBJ-derived solids are stronger for:

- separating buildings from ground, vegetation and visual textures;
- creating closed or repairable collision solids;
- providing a reproducible bridge to STL, voxelization and FluidX3D.

In this project, the useful wind-environment boundary came from a LoD3-derived closed-prism collision interpretation, while the photogrammetry model remained a visual/reference layer.

### 5.3 Simulation and visualization layer

FluidX3D produced VTK wind-field outputs for eight wind directions. ParaView/pvpython successfully loaded those VTK files and saved a review state. Automated headless ParaView screenshots remain blocked by the Windows OpenGL/OSMesa environment, but this is a visualization-runtime limitation, not a failure of the VTK data or FluidX3D result. Immediate audit maps were generated from the same VTK arrays and flags.

## 6. Campus Wind-Environment Application Potential

The campus environment is a useful landing scenario for digital-twin wind simulation because it combines high pedestrian exposure with recurring operational and design decisions.

Potential application directions:

1. Entrance and courtyard diagnosis: locate persistently stagnant entrances, courtyards and passage interiors where low ventilation may affect comfort, perceived air quality and pollutant dilution.
2. Pedestrian and cycling route planning: evaluate whether common campus paths pass through robust low-ventilation zones or locally accelerated corridors.
3. Retrofit and design interventions: compare opening passages, removing low-level blockage, modifying courtyard gates, adding wind-permeable landscape elements or redistributing vegetation.
4. Seasonal operation: in a temperate wet climate, balance winter wind shelter against summer ventilation and warm-period heat/pollution dispersion.
5. Emergency and event management: use wind-field layers to inform temporary installations, queuing zones, campus festivals or construction-phase circulation.
6. Digital-twin governance: update the geometry after campus renovations and rerun standardized wind indicators rather than rebuilding a CFD model from scratch.

## 7. Claim Boundary

Supported:

- TUM2TWIN can be converted into a wind-simulation-ready campus case when visual and semantic geometry layers are separated.
- The present core block shows robust low pedestrian-layer ventilation across eight wind directions.
- The wind issue in this campus block is better framed as ventilation insufficiency than as widespread high-wind danger.
- Campus wind simulation has practical value for pedestrian routes, courtyards, entrances, retrofit screening and digital-twin planning.

Not supported yet:

- Formal Lawson/NEN/AIJ annual comfort or safety compliance.
- Field-validated wind prediction accuracy.
- Pollutant concentration or infection-risk conclusions.
- A claim that photogrammetry/3DGS visual meshes can directly serve as final CFD collision boundaries.
