# Current Data Summary and Evidence-Based Conclusions

evidence_type: newly_run + preexisting_artifact + user_claim + blocked

## 1. Current Data Inventory

### 1.1 Source and Manifest Data

| Data group | File / location | Count / size | Evidence type | Main use |
|---|---|---:|---|---|
| Download/source manifest | `manifests/data_manifest.csv` | 21 rows | newly_run + preexisting_artifact | Records source URL, size, checksum, download time, license/citation information |
| Geometry manifest | `manifests/geometry_manifest.csv` | 13 rows | newly_run | Records Rhino/OBJ/STL geometry files, roles, sizes and checksums |
| Evidence inventory | `manifests/evidence_inventory.csv` | 98 rows | newly_run + preexisting_artifact + user_claim + blocked | Maps claims to evidence type and source artifact |
| Wind-climate proxy weights | `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv` | 8 sectors | newly_run + preexisting_artifact | Converts 2024 hourly 10 m wind data into 8 FluidX3D velocity-direction weights |

### 1.2 Visual and Rhino Data

| Data layer | File | Key facts | Interpretation |
|---|---|---|---|
| User screenshot | `C:\Users\MIAOSH~1\AppData\Local\Temp\codex-clipboard-343f614c-f3f8-49ce-b283-ddbbcf6ca52e.png` | Oblique rendered view of TUM Downtown photogrammetry block | user_claim + visual reference |
| User Rhino model | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_rhino_layered_geometry.3dm` | 1 layer, 1 mesh, 999,999 faces, bbox about `409 x 543 x 47 m` | Same visual study block as screenshot, but not a semantic/CFD layer model |
| Official textured OBJ | `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh\TUM_Downtown_Photogrammetry_20241217_Mesh.obj` | OBJ/MTL/JPG photogrammetry data downloaded and checksum-recorded | Best source for textured visual review |
| Generated Rhino management file | `rhino/TUM2TWIN_Downtown_district_CFD_layered_geometry.3dm` | Contains generated management layers including CFD collision reference | Rhino/GH management file, not exact textured browsing substitute |

### 1.3 CFD-Ready Geometry Data

| Geometry | File | Key numbers | Status |
|---|---|---:|---|
| User photogrammetry STL | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726\converted\TUM_Downtown_Photogrammetry_20241217_fluidx3d_z0_fullres.stl` | 999,999 triangles; about `409 x 543 x 47 m`; 2,245 boundary edges | visual/reference and counterexample, not final collision |
| Core photogrammetry-extent prism | `cfd_ready/core_photogrammetry_extent_prism_collision_z0.stl` | 15,964 triangles; bbox `420 x 555 x 32.43 m`; 46 components; 2,365 footprint cells | current main local pedestrian-height CFD collision geometry |
| Whole-district prism | `cfd_ready/district_prism_collision_z0.stl` | 135,122 triangles; bbox `1540 x 1375 x 58 m`; 217 components; 21,967 footprint cells | whole-district screening geometry |
| Earlier small Rhino/LoD3 layer | recorded in `manifests/tum2twin_rhino_layered_geometry_scope_audit.csv` | about `105 x 68 m` | too small for current main study object |

### 1.4 FluidX3D Simulation Data

| Simulation layer | Inputs | Run setup | Output artifacts | Use |
|---|---|---|---|---|
| User photogrammetry STL pilot | User full-resolution photogrammetry STL | dx `2 m`, WD000, 2,000 steps | `figures/fluidx3d_user_photo_wd000_dx2m_2k_voxel_vr_audit.png` | Demonstrates why raw photogrammetry STL is not reliable final collision |
| Whole-district prism coarse/medium | `district_prism_collision_z0.stl` | dx `6 m` and `4 m`, 8 directions, 10,000 steps | district VR panels and metrics CSV | District-scale feasibility and screening |
| Core prism main result | `core_photogrammetry_extent_prism_collision_z0.stl` | dx `2 m`, grid `320 x 390 x 60`, 8 directions, spin-up 6,000 steps, samples at 8,000/10,000/12,000 | `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_vr_panel_z2m.png`, metrics CSV | Current strongest wind-environment result |
| Open-Meteo weighted result | Core prism 8-direction time-mean fields + 2024 wind-climate proxy | direction-weighted post-processing | `figures/fluidx3d_core_prism_open_meteo_2024_weighted_vr_z2m.png`, weighted metrics CSV | Climate-proxy sensitivity layer, not measured annual comfort probability |

## 2. Main Numerical Results

### 2.1 Core Prism, Equal-Weighted 8 Directions

Aggregation: FluidX3D dx `2 m`; each direction averaged from three samples after spin-up; then eight directions are equally averaged.

| Height | VR mean | VR P75 | VR P90 | VR P95 | VR max | VR<0.2 stagnation | VR>0.6 | VR>1.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 m | 0.076 | 0.080 | 0.155 | 0.241 | 1.000 | 0.934 | 0.013 | 0.000 |
| 4 m | 0.187 | 0.237 | 0.412 | 0.635 | 1.048 | 0.665 | 0.053 | 0.000 |
| 10 m | 0.404 | 0.625 | 0.831 | 0.915 | 1.041 | 0.314 | 0.276 | 0.004 |
| 20 m | 0.602 | 0.936 | 1.002 | 1.021 | 1.068 | 0.245 | 0.594 | 0.104 |
| 40 m | 1.049 | 1.123 | 1.139 | 1.147 | 1.182 | 0.000 | 1.000 | 0.734 |

Evidence source: `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv`.

### 2.2 Core Prism, Open-Meteo 2024 Direction-Weighted Result

Aggregation: same FluidX3D time-mean fields, weighted by Open-Meteo 2024 hourly 10 m wind direction sectors. This is a wind-climate proxy, not field-measured validation.

| Height | VR mean | VR P75 | VR P90 | VR P95 | VR max | VR<0.2 stagnation | VR>0.6 | VR>1.0 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 m | 0.077 | 0.081 | 0.151 | 0.246 | 1.000 | 0.931 | 0.013 | 0.000 |
| 4 m | 0.188 | 0.239 | 0.416 | 0.616 | 1.061 | 0.656 | 0.053 | 0.000 |
| 10 m | 0.406 | 0.631 | 0.843 | 0.936 | 1.061 | 0.323 | 0.283 | 0.006 |
| 20 m | 0.603 | 0.951 | 1.008 | 1.025 | 1.105 | 0.253 | 0.588 | 0.123 |
| 40 m | 1.051 | 1.132 | 1.155 | 1.167 | 1.207 | 0.000 | 1.000 | 0.734 |

Evidence source: `figures/fluidx3d_core_prism_open_meteo_2024_weighted_metrics.csv`.

### 2.3 Open-Meteo 2024 Direction Weights

| Velocity-to sector | Weight | Hours | Mean 10 m wind speed | P90 10 m wind speed |
|---:|---:|---:|---:|---:|
| 0 deg | 0.112 | 980 | 1.89 m/s | 3.01 m/s |
| 45 deg | 0.229 | 2008 | 2.89 m/s | 5.01 m/s |
| 90 deg | 0.260 | 2281 | 3.98 m/s | 6.50 m/s |
| 135 deg | 0.071 | 625 | 2.40 m/s | 4.31 m/s |
| 180 deg | 0.041 | 356 | 1.58 m/s | 2.65 m/s |
| 225 deg | 0.097 | 855 | 2.03 m/s | 3.27 m/s |
| 270 deg | 0.117 | 1029 | 2.44 m/s | 4.00 m/s |
| 315 deg | 0.074 | 650 | 2.04 m/s | 3.20 m/s |

Evidence source: `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`.

## 3. Conclusions Supported by Current Data

### Conclusion 1: The simulation object and screenshot object are consistent at the study-area level.

The screenshot/Rhino photogrammetry block has a visual bbox of about `409 x 543 m`; the main core CFD geometry covers about `420 x 555 m`. The main result therefore analyzes the same TUM Downtown block scale, not only a few isolated buildings. However, the computational mesh is a LoD3-derived closed prism reconstruction rather than the raw photogrammetry mesh.

Claim readiness: `paper_ready`.

### Conclusion 2: Photogrammetry/3DGS-like visual meshes should not be treated as final CFD collision boundaries.

The user photogrammetry STL has 999,999 triangles and matches the visual object scale, but contains 2,245 boundary edges and is not watertight. Its FluidX3D pilot is useful as a geometry-to-solver counterexample. This supports the manuscript argument that photogrammetry and 3DGS-like outputs are excellent for appearance and spatial reference, but require semantic/solid reconstruction before CFD/LBM.

Claim readiness: `paper_ready`.

### Conclusion 3: The LoD3-derived closed prism workflow produces a simulation-ready urban block geometry.

The core prism geometry has a recorded bbox, triangle count, footprint cells, components, z0 alignment, and QA figure. It was accepted by FluidX3D and generated eight-direction velocity outputs. This directly supports the workflow claim that TUM2TWIN semantic city data can be translated into CFD-ready LBM geometry.

Claim readiness: `paper_ready`.

### Conclusion 4: Near-pedestrian wind speed ratios are low in the current core-prism pilot.

At z about `2 m`, the equal-weighted eight-direction mean VR is about `0.076`, P95 is about `0.241`, and the VR<0.2 stagnation ratio is about `0.934`. The Open-Meteo weighted result is very close: mean VR about `0.077`, P95 about `0.246`, stagnation ratio about `0.931`. This indicates extensive low-speed/stagnation zones in the current modeled pedestrian layer.

Claim readiness: `weaken_claim` if framed as real-world comfort assessment; `paper_ready` if framed as preliminary FluidX3D screening.

### Conclusion 5: Vertical wind-speed recovery is strong.

In the equal-weighted result, mean VR increases from about `0.076` at 2 m to about `1.049` at 40 m. The stagnation ratio drops from about `0.934` at 2 m to `0` at 40 m. This supports a vertical-structure observation: the closed urban block strongly suppresses pedestrian-height flow, while higher layers recover toward or above reference speed.

Claim readiness: `paper_ready` as a simulation observation; `weaken_claim` for general field prediction.

### Conclusion 6: Open-Meteo weighting changes the pedestrian-height metrics only slightly compared with equal weighting.

The 2 m mean VR changes from about `0.076` to `0.077`, and the stagnation ratio changes from about `0.934` to `0.931`. Thus, for the current geometry and eight-direction set, the general low-speed pedestrian-layer conclusion is robust to this proxy direction weighting. This should be described as sensitivity to a climate proxy, not as measured annual exceedance probability.

Claim readiness: `paper_ready` with climate-proxy wording.

### Conclusion 7: The current package supports workflow-level SCI claims, not final validation claims.

The data support claims about data hierarchy, geometry readiness, FluidX3D execution, repeatable post-processing, and preliminary wind-environment screening. They do not support claims of measured predictive accuracy, formal Lawson/NEN/AIJ annual comfort classes, pollutant exposure results, or full grid-independent CFD validation.

Claim readiness: `paper_ready` for evidence boundary.

## 4. What Cannot Be Concluded Yet

| Unsupported conclusion | Current status | Needed evidence |
|---|---|---|
| FluidX3D result is field-validated for TUM Downtown | blocked | onsite wind sensors, wind tunnel data, or validated reference CFD |
| Formal Lawson/NEN 8100/AIJ annual comfort/safety class | blocked | threshold exceedance probabilities from calibrated annual wind climate |
| Pollutant dispersion hotspots and exposure integrals | blocked | scalar transport/pollutant simulation outputs |
| Raw photogrammetry mesh is a valid final collision geometry | contradicted by current QA | watertight repair, semantic segmentation, solid reconstruction and voxelization QA |
| Roof/facade fine-detail aerodynamic accuracy is resolved | blocked / weaken_claim | finer geometry, roughness model, mesh sensitivity and validation |

## 5. Recommended Manuscript-Level Takeaway

The current data support the following central conclusion:

> In the TUM2TWIN Downtown case, photogrammetry/Rhino data reliably define and visualize the real urban study scene, but cannot be directly used as a rigorous LBM collision boundary. A LoD3-derived closed semantic-prism reconstruction over the same visual extent enables FluidX3D simulation and produces reproducible preliminary pedestrian-height wind-speed-ratio maps. The results indicate extensive low-speed zones at pedestrian height in the current pilot, while higher layers recover substantially. These findings support and document the digital-twin-to-CFD application workflow and its evidence boundary, rather than providing final field-validated comfort or safety compliance results.

### 7.1 S1 Design-Sensitivity Addendum

S1 ventilation relief was simulated after the baseline synthesis. It removes 66 heightfield collision cells along a least-removal east-west corridor and reruns the same FluidX3D dx=2 m, eight-direction, three-sample protocol. The comparison shows a near-null/negative outcome: at z~2 m, equal-weighted mean VR changes by only `-0.000213`, while newly opened cells remain low-speed. The design implication is that this campus-core stagnation is not resolved by a single light corridor opening.

### 7.2 S2 Network-Porosity Addendum

S2 network porosity was simulated as a stronger follow-up to S1. It removes `201` heightfield collision cells (`8.50%` of S0 footprint) along three least-removal corridors and reruns the same FluidX3D dx=2 m, eight-direction, three-sample protocol. At z~2 m, equal-weighted mean VR changes by `-0.000466`, while newly opened cells have mean VR `0.004384` and stagnation ratio `1.000`. This extends the design conclusion: simple geometric porosity, even at a network scale, is insufficient unless located where external momentum can enter the campus core.

### 7.3 Directional Trade-Off Addendum

Directional post-processing of S1/S2 confirms that the interventions are not simply blank null results. S2-S0 has its best common-open response at 315 deg, with mean common-open delta VR `0.000368`, but the mean share of common-open cells with delta VR>0.02 is only `0.002374`. Newly opened S2 cells still have maximum direction-wise mean VR only `0.006646` and remain fully stagnant at z~2 m. The paper-safe interpretation is that local aerodynamic response exists but is too sparse and too weak to generate pedestrian-layer ventilation recovery.

### 7.4 Multivariate Morphology Robustness Addendum

The basic morphology interpretation was rechecked using bootstrap Spearman intervals, partial Spearman, and repeated 5-fold rank-transformed ridge regression on 101 retained building components. For the 20-50 m local-context band, the mean-VR model has limited cross-validated explanatory power (`R2 = 0.122 +/- 0.166`), but the ordered signal remains useful: 50 m sector enclosure has the strongest negative coefficient (`-0.147`) and largest permutation importance (`0.083`), followed by mean height and combined enclosure. The paper-safe conclusion is that this experiment identifies local enclosure and pressure/momentum exchange context as stronger screening descriptors than single-building footprint or elongation, not that morphology parameters can precisely predict real wind speed.

### 7.5 Final Integrated Paper-Readiness Addendum

The final integrated layer consolidates the main evidence into `figures/final_integrated_key_result_matrix.csv` and `reports/experiment3_completion_audit_and_paper_readiness.md`. The paper-ready position is now explicit: Experiment 3 is complete as a FluidX3D-native digital-twin wind screening, morphology interpretation, and negative S1/S2 design-sensitivity case. It remains bounded against field validation, annual comfort/safety compliance, pollutant dispersion, GCBTE closure, successful S3-Sn optimization, and CityLBM-GH end-to-end execution.
