# Experiment 3 Submission Statements

evidence_type: newly_run + preexisting_artifact + blocked

## Data Availability

The lightweight Experiment 3 archive contains processed reports, manifests, selected CFD-ready geometry, postprocessed statistical tables, paper-facing figures, ParaView state files, and manuscript text. Full raw TUM2TWIN downloads, complete texture folders, local ParaView installation files, local FluidX3D source/build files, and full VTK output matrices are not embedded in the GitHub package because of size and machine-specific environment constraints. Their provenance and local boundaries are recorded in `EXTERNAL_ARTIFACTS.md` and `manifests/data_manifest.csv`. License wording should be checked against the original TUM2TWIN and Zenodo records before journal submission.

## Code Availability

The archive includes the postprocessing, morphology-analysis, figure-generation, claim-audit and manifest-refresh scripts used to build the paper-facing outputs. The canonical lightweight rebuild command from the Experiment 3 release-package root is `& .\scripts\rebuild_experiment3_paper_assets.ps1`. FluidX3D case templates and CityLBM-compatible geometry templates are included, but the CityLBM-Grasshopper folder is an interoperability template rather than evidence of a completed end-to-end plugin execution.

## Reproducibility

The archived files are sufficient to audit the data-layer separation, CFD-ready geometry preparation, processed FluidX3D screening metrics, ParaView/manual-review assets, morphology-response analyses, figure/table narratives, and claim boundaries. Re-running the full CFD workflow requires re-downloading or restoring external TUM2TWIN assets, rebuilding or restoring FluidX3D, and regenerating the full VTK output set. The package does not claim field validation, formal annual comfort or safety compliance, pollutant dispersion, GCBTE closure, or successful design optimization.

## Computational Resources

The numerical protocol is recorded in `manifests/fluidx3d_numerical_protocol_audit.csv` and `reports/fluidx3d_numerical_protocol_and_stability_audit.md`, including dx, grid/domain size, reference velocity, air viscosity, LBM conversion, tau/Re descriptors, wind directions and sample steps. GPU model, wall-clock runtime, residual convergence and complete grid-independence evidence should not be invented and should be reported only if separately measured.

## Ethics, Funding and Competing Interests

The current archive contains no newly collected human-subject data and no site wind-measurement campaign. AUTHOR_INPUT_NEEDED: funding, competing interests, acknowledgements and CRediT author-contribution statements must be completed by the authors.
