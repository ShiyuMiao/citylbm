# Data Source and Download Manifest

evidence_type: newly_run + preexisting_artifact + user_claim

## Official Pages Verified

The following TUM2TWIN pages were checked and used to define evidence boundaries:

- `https://tum2t.win/datasets`
- `https://tum2t.win/datasets/cm-mesh`
- `https://tum2t.win/datasets/cm-buildings`
- `https://tum2t.win/datasets/cm-vegetation`
- `https://tum2t.win/datasets/cm-cad`
- `https://tum2t.win/benchmarks/pc-fac`

## Main Data Sources

| Source | Local storage | Use |
|---|---|---|
| Zenodo 14899378 v1.1.0 | `D:\citylbm_tum2twin_heavy_store\raw\zenodo_14899378_v1_1_0_textured_mesh` | official textured photogrammetry mesh and documentation |
| TUM2TWIN GitLab selected OBJ/CityGML | `D:\citylbm_tum2twin_heavy_store\raw\tum2twin_gitlab_selected` | semantic LoD3/LoD2 geometry source |
| User-provided `converted.rar` | `D:\citylbm_tum2twin_heavy_store\converted\user_converted_rhino_layered_20260726` | screenshot-matching Rhino/photogrammetry package |
| Open-Meteo Historical Weather API | `D:\citylbm_tum2twin_heavy_store\raw\wind_climate_open_meteo` | 2024 wind-climate proxy |
| FluidX3D GitHub clone/build | `F:\citylbm_fluidx3d_workspace\FluidX3D` | solver source and executable |
| Portable ParaView | `F:\citylbm_fluidx3d_workspace\ParaView_zip` | manual visualization and pipeline states |

Heavy data were stored outside C drive because C drive free space is low. The main storage drives are D and F.

## Manifest Files

Detailed path, URL, file size, checksum, timestamp, license/citation, and evidence-type records are stored in:

- `manifests/data_manifest.csv`
- `manifests/geometry_manifest.csv`
- `manifests/evidence_inventory.csv`
- `manifests/full_lod2_download_manifest.csv`
- `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv`

## Important Evidence Notes

- Official Zenodo 14899378 lists OBJ/MTL/JPG/LAZ/DSM/orthophoto/OPF/image files, not an official Rhino `.3dm`.
- The user-provided Rhino package is a derived local artifact and is recorded as `user_claim` until extracted and audited locally.
- The user photogrammetry STL is not watertight and is not used as final collision geometry.
- Open-Meteo data are treated as a reanalysis-based wind-climate proxy, not site-measured wind data.
