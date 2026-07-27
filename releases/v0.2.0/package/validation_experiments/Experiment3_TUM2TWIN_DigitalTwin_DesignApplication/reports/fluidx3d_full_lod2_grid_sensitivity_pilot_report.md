# FluidX3D Full LoD2 Grid-Sensitivity Pilot Report

evidence_type: newly_run

## Purpose

This pilot checks whether the complete TUM2TWIN LoD2 geometry remains feasible at a medium grid and whether the coarse `dx=4 m` matrix is sufficient only as a pipeline audit. It is a one-direction grid-sensitivity sample, not the final grid-converged study.

## Runs Compared

| Level | Direction | Grid | dx | Steps | Runtime |
|---|---:|---:|---:|---:|---:|
| coarse | WD000 | 306 x 306 x 64 | 4.0 m | 10000 | 15.01 s |
| medium | WD000 | 611 x 611 x 128 | 2.0 m | 10000 | 110.26 s |

## Outputs

- Comparison figure: `figures/fluidx3d_full_lod2_wd000_coarse_vs_medium_vr_audit.png`
- Comparison metrics: `figures/fluidx3d_full_lod2_wd000_coarse_vs_medium_metrics.csv`
- Medium run log: `F:\citylbm_fluidx3d_workspace\tum2twin_case\logs\run_full_lod2_wd000_medium2m_10k.log`
- Medium final velocity VTK: `F:\citylbm_fluidx3d_workspace\tum2twin_case\output\matrix_full_lod2_wd000_medium2m_10k_u_finalu-000010000.vtk`

## Metrics

| Level | Height approx. (m) | VR mean | VR P90 | VR P95 | VR max | Stagnation VR<0.2 |
|---|---:|---:|---:|---:|---:|---:|
| coarse dx=4 m | 4 | 0.094 | 0.151 | 0.269 | 1.000 | 0.929 |
| coarse dx=4 m | 8 | 0.237 | 0.444 | 0.699 | 1.129 | 0.643 |
| coarse dx=4 m | 20 | 0.550 | 0.942 | 1.020 | 1.123 | 0.041 |
| coarse dx=4 m | 40 | 0.867 | 1.086 | 1.113 | 1.126 | 0.002 |
| medium dx=2 m | 4 | 0.164 | 0.280 | 0.446 | 1.129 | 0.826 |
| medium dx=2 m | 8 | 0.336 | 0.597 | 0.831 | 1.159 | 0.087 |
| medium dx=2 m | 20 | 0.694 | 1.021 | 1.085 | 1.124 | 0.037 |
| medium dx=2 m | 40 | 0.982 | 1.095 | 1.101 | 1.108 | 0.002 |

## Interpretation Boundary

The medium run is feasible on the local Tesla P100 and resolves building edges and wake bands more clearly than the 4 m coarse grid. The difference between coarse and medium metrics is large at 4-8 m, so the 4 m matrix should be used only as an audit and case-screening layer. A rigorous final experiment should next run either:

- a full 8-direction `dx=2 m` matrix, or
- a selected subset of dominant directions at `dx=2 m` followed by one finer local refinement if hardware permits.

The current setup still requires time averaging and final boundary-condition refinement before being used for formal comfort/safety classification.
