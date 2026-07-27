# External Artifacts and Large-File Boundary

evidence_type: newly_run + preexisting_artifact

This GitHub archive intentionally stores the lightweight, reviewable experiment package rather than every raw digital-twin or CFD field file.

## Not Embedded in GitHub

- Full TUM2TWIN raw UAS/photogrammetry downloads.
- Full texture folders and original OBJ/JPG/MTL archives.
- Full FluidX3D VTK time-sampled output matrices.
- Local ParaView installation.
- Local FluidX3D build tree and binaries.

## Local Artifact Roots Used During the Experiment

- TUM2TWIN heavy data store: `D:\citylbm_tum2twin_heavy_store`
- FluidX3D and VTK workspace: `F:\citylbm_fluidx3d_workspace\tum2twin_case`
- FluidX3D source/build root: `F:\citylbm_fluidx3d_workspace\FluidX3D`
- ParaView portable installation: `F:\citylbm_fluidx3d_workspace\ParaView_zip\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64`

These paths are machine-local provenance records, not portable dependencies. Use the reports and manifests in this folder to reproduce the acquisition and conversion steps on another workstation.

## Embedded Lightweight Evidence

This archive does include:

- Postprocessed figures and statistical CSVs.
- Geometry QA reports and selected CFD-ready STL/Rhino files.
- Reproducible scripts used for VTK parsing, morphology analysis, and figure generation.
- Selected `.pvsm` ParaView state files.
- Selected logs documenting run status and blockers.

## Claim Boundary

The embedded files are sufficient to audit the reported digital-twin data workflow, geometry-readiness decisions, FluidX3D screening results, morphology-response statistics, and paper-text conclusions. They are not sufficient to re-run the full simulation without re-downloading external TUM2TWIN assets and regenerating FluidX3D VTK outputs.
