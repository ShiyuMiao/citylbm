# CityLBM STG temporal-step acceleration evidence - 2026-08-26

Scope: AIJ Case A native FluidX3D short canary, generated from the CityLBM Case A full-AF source case. This is a diagnostic inlet-physics gate, not a publishable validation run.

Common setup:

- Solver: native FluidX3D, real run, graphics disabled.
- Case source: `C:\Users\MSY\AppData\Local\Temp\CityLBM\casea_full_reynolds_stress_tensor`
- Official AF: `F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casea_v020_rerun_20260716\official_data\AF_caseA.csv`
- Official RS/probes: `F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casea_v020_rerun_20260716\official_data\RS-caseA.csv`
- Wind vector used for native canary: `(1, 0, 0)`, matching the generated `setup.cpp`.
- Time steps: 500; VTK save interval: 25; actual VTK frames: 20.
- Profile gate threshold used here: `U_MAE_ratio <= 0.05`, `k_MAE_ratio <= 0.25`, no negative streamwise inlet velocity.

Results:

| temporal_step_scale | Real FluidX3D run | VTK frames | U_MAE_ratio | k_MAE_ratio | k_RMSE_ratio | temporal lag-1 | spatial adjacent corr. | Profile gate | Correlation gate |
|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| 0.5 | pass | 20 | 0.000684606 | 0.541240 | 0.560064 | 0.947322 | 0.942795 | fail | fail |
| 1.0 | pass | 20 | 0.000684606 | 0.375049 | 0.394597 | 0.898107 | 0.970977 | fail | fail |
| 1.5 | pass | 20 | 0.000684606 | 0.221767 | 0.242535 | 0.878871 | 0.982917 | pass | pass after temporal-variance gate fix |

Decision:

- Adopt `citylbm_stg_temporal_step_scale = 1.500000f` as the current CityLBM default because it is the first tested value that passes the short VTK inlet profile gate while preserving the AF mean-velocity profile.
- The original correlation-gate failure was traced to an audit estimator mismatch: it compared per-frame inlet-plane spatial streamwise variance against the AF isotropic-k streamwise target. The revised gate uses fixed-point temporal streamwise variance for the k-variance check and still reports the spatial-plane variance separately.
- Re-auditing the same real `t=1.5` VTK frames gives `inlet_correlation_gate=pass`, `inlet_k_variance_gate=pass`, `inlet_k_variance_gate_estimator=fixed_point_temporal_streamwise_variance`, `inlet_streamwise_variance_to_k_ratio=1.092798`, and `inlet_tke_to_k_ratio=1.141126`.
- Do not claim paper-grade Case A validation yet. The short canary still has only 500 steps and 20 diagnostic frames, and the spatial adjacent correlation remains high (`0.982917`), so boundary conditions, longer time averaging, probe projection and final Case A metrics still need to pass.
- Boundary-protocol audit was also corrected to use binary `buildings.stl` as a fallback when legacy metadata reports zero building height. Re-auditing the same Case A canary gives `clearance_numeric_gate=pass`, `blockage_gate=pass`, `approx_frontal_blockage_ratio=0.0079365`, and clearance values of approximately `5.25H` upstream, `15.25H` downstream, `5.25H` lateral and `6.0H` top.
- The boundary protocol still fails because external AIJ-equivalent boundary/fetch/roughness evidence is missing and cannot be inferred from the STL or metadata. This remains a real blocker before paper-grade accuracy claims.

Verification performed after source migration:

- `dotnet build -c Release`
- `python -m py_compile scripts\run_native_preflight_pack.py scripts\prepare_native_diagnostic_canary_case.py tests\native_preflight_pack_smoke.py tests\synthetic_inlet_component_norm_smoke.py tests\prepare_native_diagnostic_canary_case_smoke.py`
- `tests\native_preflight_pack_smoke.py`
- `tests\synthetic_inlet_component_norm_smoke.py`
- `tests\prepare_native_diagnostic_canary_case_smoke.py`
- `tests\custom_profile_af_fidelity_smoke.py`
- `tests\codegen_preflight_canary_smoke.py`
- `tests\inlet_correlation_integral_scale_smoke.py`
- `tests\boundary_protocol_identity_smoke.py`
- `tests\boundary_protocol_template_smoke.py`

Protocol-gate acceleration fixes:

- `bind_coordinate_probe_protocol_metadata.py` now writes SHA256 hashes for the official AF and RS/probe CSV files when those files are bound into metadata. This removes a false protocol failure where the official paths were present but `OfficialAFSha256` / `OfficialRSSha256` were missing.
- `write_validation_protocol_audit.py` now accepts the current CityLBM metadata field names `SyntheticTurbulentInletMethod`, `SyntheticTurbulenceIntensityScale`, `LbmTau` and `DxM` in addition to the older `TurbulenceMethod`, `TurbulenceScale`, `Tau` and `Dx` names.
- `run_native_fluidx3d_case.py` now uses `PreRunGate` / `PreRunFailKeys` / `PreRunRiskKeys` for run-start gating. Runtime-only items such as `native_fluidx3d_baseline`, `systematic_bias_gate` and `grid_resolution` remain reported in `FailKeys` / `RiskKeys`, but no longer falsely block a strict native run before the solver has been run.

Updated Case A protocol audit after metadata compatibility fixes:

- Audit file: `C:\Users\MSY\AppData\Local\Temp\CityLBM\casea_fullaf_rs_500x25_t15_20260826\validation_protocol_audit_after_metadata_compat.json`
- Result: `Gate=diagnostic_only`, `PreRunGate=diagnostic_only`, `fail=5`, `risk=2`.
- Total fail keys: `inlet_distribution_consistency`, `native_fluidx3d_baseline`, `boundary_conditions`, `wall_roughness_model`, `systematic_bias_gate`.
- Total risk keys: `inlet_turbulence_length_scale`, `grid_resolution`.
- Pre-run fail keys: `inlet_distribution_consistency`, `boundary_conditions`, `wall_roughness_model`.
- Pre-run risk keys: `inlet_turbulence_length_scale`.
- Interpretation: the remaining pre-run blockers are now real protocol or method gaps, not missing field-name compatibility. The current inlet source is distribution-consistent diagnostic STG/SEM evidence, but not yet paper-grade DFM/SEM/precursor evidence; the current boundary source is still a simplified Type-E box and lacks archived AIJ-equivalent boundary and rough-wall evidence.

Additional verification after protocol-gate fixes:

- `tests\bind_coordinate_probe_protocol_metadata_smoke.py`
- `tests\write_validation_protocol_audit_smoke.py`
- `tests\native_fluidx3d_runner_smoke.py`
- `dotnet build -c Release`

Rough-wall source acceleration fix:

- `src\Core\FluidX3DInterface.cs` now emits a real FluidX3D `FORCE_FIELD` near-ground equivalent rough-wall drag before device upload. The generated `setup.cpp` contains `rough_wall_function`, `rough_wall_drag_limit`, `apply_rough_wall()` and writes `lbm.F.x/y/z`, followed by `lbm.F.write_to_device()`.
- The force is derived from a log-law friction velocity using `RoughnessLength`, distributed over a near-ground layer and capped to `0.02 * local_horizontal_speed` per step for LBM stability.
- Metadata now records `BoundaryRoughWallFunctionImplemented=true` and `BoundaryRoughnessBoundaryTreatment=TYPE_S_no_slip_plus_near_ground_equivalent_rough_wall_drag_FORCE_FIELD_from_RoughnessLength`.
- The boundary source audit on the regenerated codegen smoke case reports `boundary_source_gate=pass`, `has_paper_grade_rough_wall_source=True`, `boundary_source_simplified=False`, and `boundary_source_fidelity_class=advanced_boundary_incomplete`.
- This is still not a paper-grade boundary model by itself. The audit correctly keeps `paper_grade_boundary_source_gate=fail` because non-reflecting/validated outlet, side/top wind-tunnel equivalence, precursor/recycling development and official boundary/fetch evidence remain missing.

Verification after rough-wall fix:

- `dotnet build -c Release`
- `dotnet run -c Release --project tests\CodegenSmoke\CodegenSmoke.csproj`
- `tests\boundary_source_audit_smoke.py`
- `tests\write_validation_protocol_audit_smoke.py`
- `python -m py_compile scripts\write_validation_protocol_audit.py tests\write_validation_protocol_audit_smoke.py tests\boundary_source_audit_smoke.py`
- `tests\native_fluidx3d_runner_smoke.py`
- `tests\native_preconditions_source_parity_gate_smoke.py`
