# LCZ Scale Validity in the TUM2TWIN Core Wind Model

evidence_type: newly_run + preexisting_artifact

Status update: LCZ-like labels are retained only as an audit trail. The recommended manuscript analysis now uses basic building-morphology parameters instead of LCZ classification. See `reports/basic_morphology_wind_response_analysis.md`.

## 1. Purpose

This note discusses whether Local Climate Zone (LCZ) concepts are valid at the scale of the present TUM2TWIN/FluidX3D core campus model. The answer is deliberately bounded:

- LCZ is useful as a **morphology vocabulary** for interpreting compact/open, low-/mid-/high-rise-like campus fabrics.
- LCZ is not valid here as an **official LCZ map product**, nor as a complete thermal-climate classification.

The term used in this project should therefore remain `LCZ-like morphology`, not simply `LCZ`.

## 2. External Reference Boundary

| Source | Relevance | Evidence type |
|---|---|---|
| Stewart and Oke, 2012, *Bulletin of the American Meteorological Society*, DOI: 10.1175/BAMS-D-11-00019.1, https://journals.ametsoc.org/abstract/journals/bams/93/12/bams-d-11-00019.1.xml | LCZ comprises 17 zone types at local scale, based on surface structure, cover and human activity; the local scale is broader than an individual building component. | preexisting_artifact |
| WUDAPT LCZ page, https://www.wudapt.org/lcz/ | LCZ classes are based mainly on surface structure such as building/tree height and density, and surface cover such as pervious/impervious cover. | preexisting_artifact |
| WUDAPT main page, https://www.wudapt.org/ | WUDAPT frames LCZ as a globally consistent data layer for climate, weather, environment and planning models. | preexisting_artifact |
| Present TUM2TWIN/FluidX3D model | Core CFD domain and z~2 m flags/velocity fields support component-scale morphology and wind-response statistics. | newly_run |

## 3. Scale Match and Scale Mismatch

### 3.1 What matches LCZ logic

The present model contains geometry variables that overlap with LCZ logic:

- building height;
- building compactness and local built fraction;
- open versus compact fabric;
- low-/mid-/high-rise-like height categories;
- local context around buildings.

These are exactly the kinds of structural features that make LCZ useful as a bridge between urban morphology and climate-related performance. For a campus wind study, this vocabulary helps move the conclusion from a purely geometric statement such as "building cluster A has low VR" to a more transferable statement such as "compact midrise-like, high-enclosure campus fabric suppresses pedestrian-layer ventilation."

### 3.2 What does not match official LCZ mapping

The present model does not satisfy the requirements for an official LCZ classification:

- The analysis unit is a CFD-ready building component and its 0-20 m / 20-50 m surrounding wind-sampling bands, not a city-scale LCZ patch.
- The classification uses relative enclosure tertiles within the cropped central campus, not externally calibrated LCZ parameter ranges.
- The current model does not include full LCZ surface-cover parameters such as pervious/impervious fraction, vegetation canopy, thermal admittance, albedo or anthropogenic heat.
- The classification is derived from a cropped simulation domain after edge-building removal; it should not be generalized to the whole Munich urban fabric.
- LCZ was developed primarily for urban temperature and local climate comparison, whereas this analysis targets pedestrian wind distribution around buildings.

Therefore, an official claim such as "the TUM core belongs to LCZ2" would be too strong. The defensible wording is: "parts of the retained central campus geometry exhibit compact midrise-like or open midrise-like LCZ morphology."

## 4. Validity Level in This Study

| Use of LCZ | Validity in this model | Recommended wording |
|---|---|---|
| Morphology vocabulary | High | `LCZ-like morphology`, `compact midrise-like`, `open midrise-like` |
| Within-site grouping after edge removal | Moderate to high | `relative enclosure groups within the retained core campus` |
| Explaining wind-response differences | Moderate | `LCZ-like groups help organize wind-response differences, especially in the 20-50 m local-context band` |
| Official WUDAPT LCZ map | Low / not supported | Avoid |
| City-scale climate-zone claim for Munich | Not supported by this model | Avoid |
| Thermal comfort or heat-island conclusion | Not supported by current wind-only simulation | Avoid |

## 5. Interpretation for the Present Results

After removing 44 edge-incomplete components and 34 small fragments, 101 retained central components were classified into low, medium and high relative enclosure groups. These groups include LCZ1/LCZ2/LCZ4/LCZ5-like morphology labels, but the labels should be interpreted as a compact/open and height-based morphology grammar.

The results show that the facade-adjacent 0-20 m band is so strongly sheltered that LCZ-like differences are numerically compressed: nearly all classes remain below VR=0.2. The 20-50 m local-context band is the more meaningful scale for LCZ-like interpretation, because it captures how surrounding building fabric modifies wind recovery away from immediate facades.

This scale behavior is important. It means LCZ is less useful as a direct label for individual building edges and more useful as a way to classify **local morphological context** around buildings. In other words, LCZ-like interpretation becomes more valid as the sampling window moves from a single facade to a surrounding urban-fabric patch.

## 6. Recommended Paper Claim

The LCZ framework is effective in this study as a bounded morphology lens rather than as a formal mapping product. At the campus-core scale, LCZ-like labels help classify retained central building components by compactness, height and enclosure, and they provide a transferable vocabulary for comparing wind response under different incoming wind directions. However, because the model uses a cropped CFD-ready geometry, relative enclosure thresholds and wind-only indicators, the labels should not be interpreted as official WUDAPT LCZ classes or as full local climate classifications.

## 7. Evidence Boundary

Supported:

- LCZ-like morphology labels are useful for organizing wind-response results at the retained campus-core scale.
- The 20-50 m local-context band is more appropriate for LCZ-like interpretation than the 0-20 m facade-adjacent band.
- LCZ-like interpretation helps connect building form to wind-environment application potential in a campus setting.

Not supported:

- Official WUDAPT LCZ mapping.
- City-wide LCZ classification of Munich or the entire TUM campus.
- Thermal LCZ performance, urban heat island magnitude, or seasonal thermal comfort conclusions.
