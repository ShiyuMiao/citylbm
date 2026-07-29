# Experiment 3 Directional Anisotropy Analysis

evidence_type: newly_run + preexisting_artifact + blocked

## Protocol

This addendum analyzes the eight time-mean FluidX3D wind directions already archived for the core-prism dx=2 m case. It uses `figures/fluidx3d_core_prism_timesampled_8dir_dx2m_metrics.csv` for S0, `figures/fluidx3d_design_sensitivity_directional_tradeoffs_z2m.csv` for S1/S2 design sensitivity, and `manifests/open_meteo_tum_city_campus_2024_windrose_8dir_weights.csv` only as a proxy direction-weighting context. No new solver run is introduced.

## Key Directional Results

- S0 z~2 m mean VR ranges from `0.073210` at `180` deg to `0.079211` at `45` deg; directional anisotropy index = `0.078610`.
- S0 z~2 m stagnation ratio ranges from `0.922676` at `135` deg to `0.940074` at `0` deg; directional anisotropy index = `0.018724`.
- Paired z~40 m minus z~2 m mean-VR recovery is positive in all eight directions, ranging from `0.953365` at `45` deg to `0.998616` at `90` deg.
- S1 global z~2 m mean-VR delta is negative in all eight directions, from `-0.000264` to `-0.000148`.
- S2 global z~2 m mean-VR delta is also negative in all eight directions, from `-0.000532` to `-0.000336`.
- S2 common-open-cell local response is directionally localized; the strongest common-open delta occurs at `315` deg with value `0.000368`.

## Paper-Safe Interpretation

The directional analysis changes the discussion from a single averaged map to a mechanism-oriented claim. The campus core is not dominated by one exceptional wind direction: pedestrian-height mean VR remains low and the stagnation ratio remains high across all eight simulated directions. At the same time, local design response is directional. S2 has a clearer common-open-cell response than S1, especially near 315 deg, but the global pedestrian-layer delta remains negative in every tested direction. This supports the design conclusion that effective ventilation interventions should be aligned with wind-sector entry and pressure-exchange paths, rather than increasing porosity area in isolation.

## Evidence Boundary

This is an eight-direction simulation-screening result. It does not constitute a measured annual wind rose, annual comfort/safety exceedance probability, field validation, wind-tunnel closure, pollutant dispersion result, or proof of a successful design optimization.

## Output Artifacts

- `figures/experiment3_directional_response_by_wind.csv`
- `figures/experiment3_directional_anisotropy_summary.csv`
- `figures/experiment3_directional_anisotropy_panel.png`
- `reports/experiment3_directional_anisotropy_analysis.md`
- `paper_text/experiment3_directional_anisotropy_results_zh.md`
- `manifests/experiment3_directional_anisotropy_claims.csv`
