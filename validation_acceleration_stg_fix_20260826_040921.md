# CityLBM validation acceleration note - STG inlet temporal fix

Generated: 2026-08-26 04:09 CST

## Scope

This note records the development-speed fix applied before launching paper-length AIJ Case A/E validation. It is not a paper accuracy result.

## Problem Found

The generated FluidX3D `setup.cpp` used an over-slow synthetic turbulent inlet temporal advection:

- `citylbm_stg_temporal_step_scale = 0.050000f`
- `citylbm_stg_temporal_ar1_rho = 0.970000f`
- SEM eddy advection used an additional `advect_steps * 0.05f`

The inlet runtime diagnostics preserved spatial RMS/Rij on the inlet plane, but fixed VTK probes saw almost no temporal k variance. This explains why long validation could show systematic underprediction even when the inlet looked configured.

## Source Fix

Changed `src/Core/FluidX3DInterface.cs`:

- `citylbm_stg_temporal_step_scale = 0.500000f`
- `citylbm_stg_temporal_ar1_rho = 0.650000f`
- SEM eddy advection now uses `advect = advect_steps`
- metadata text now reports `temporal_step_scale_0.5` and `rho_0.65`

Changed tests:

- `tests/synthetic_inlet_component_norm_smoke.py` now rejects the old `0.05` temporal advection and `rho_0.97` metadata.
- `scripts/run_validation_dev_loop.py` and `scripts/run_casee_fast_dev_loop.ps1` now use a 10-frame/900-step development canary window.
- `tests/validation_dev_loop_smoke.py` checks the new dev defaults.

## Verification

Build and smoke tests:

- `dotnet build -c Release`: pass, 0 errors, 0 warnings.
- `tests/synthetic_inlet_component_norm_smoke.py`: pass.
- `tests/inlet_correlation_integral_scale_smoke.py`: pass.
- `tests/validation_dev_loop_smoke.py`: pass.
- `tests/validation_fasttrack_smoke.py`: pass.
- `tests/inlet_source_generated_codegen_audit_smoke.py`: pass.

Fresh native FluidX3D short canary:

- Output root: `C:\Users\MSY\AppData\Local\Temp\citylbm_casee_fast_dev_loop_20260826_040745`
- VTK output: `C:\Users\MSY\AppData\Local\Temp\citylbm_casee_fast_dev_loop_20260826_040745\diagnostic_solver_cwd\output`
- VTK count: 20
- Development loop gate: pass
- Inlet correlation gate: pass
- Runtime inlet diagnostics gate: pass

Key inlet metrics from `inlet_correlation_audit.json`:

- `inlet_streamwise_variance_to_k_ratio = 0.917102634847371`
- `inlet_tke_to_k_ratio = 0.947713495737447`
- `temporal_lag1_mean_correlation = 0.262157164082244`
- `temporal_integral_positive_lag_count = 3`
- `spatial_adjacent_mean_correlation = 0.753891873008547`
- `spatial_integral_positive_lag_count = 4`

Runtime inlet diagnostics from `runtime_inlet_diagnostics_csv_audit.json`:

- Gate: pass
- Rows: 300
- `MaxMeanURelErrorEffective = 2.06045058001589E-06`
- `MaxActiveKRelError = 1.43584444156636E-06`

## Current Gate

The inlet temporal/k preservation canary now passes. This means CityLBM can proceed to actual AIJ Case A/E validation runs.

It still does not prove paper-level accuracy. The next stage must use:

- actual Case A or Case E geometry, not the 16x16x16 diagnostic canary box;
- dx = 2-3 m or the corresponding official model-scale resolution;
- long averaging, normally 40000+ steps and at least 40 final VTK frames;
- official probe/AF identity gates;
- no reuse of older VTK as newly-run evidence.
