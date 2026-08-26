# CityLBM Validation Acceleration: Actual Geometry Gate

Date: 2026-08-26

## Purpose

Shorten the validation development loop by separating actual AIJ geometry readiness from solver/runtime evidence.
This is a no-CFD preflight improvement. It does not provide Case A or Case E accuracy metrics.

## Change

- `scripts/run_codegen_preflight_canary.py` now accepts `--case-dir` so an existing CityLBM-generated case can be audited directly.
- The actual-geometry gate now parses binary STL files and recognizes the AIJ Case A standard block when:
  - the expected case is `CaseA`,
  - the STL is binary with 12 triangles,
  - the sorted extents are `0.08, 0.08, 0.16 m` within tolerance.
- Case E and other multi-building cases still require non-smoke geometry evidence; the small-STL exception is Case A only.
- `scripts/run_validation_dev_loop.py` passes `--case-dir` through to the preflight canary and now reports a specific `current_codegen_route_required` target when a valid geometry case uses stale generated source.

## Fresh Evidence

Command:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --case-dir 'F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casea_native_empty_tunnel_preflight_20260825_v2\case' --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casea_existing_standard_box_fast_preflight_20260826_v2' --strict-official-inputs --allow-diagnostic
```

Result:

- `validation_dev_loop_gate=diagnostic_only`
- `ActualValidationGeometryGate=pass`
- `CaseAStandardBoxGeometry=true`
- `BuildingsStlBytes=684`
- `TriangleCount=12`
- `NextOptimizationTarget.Key=current_codegen_route_required`

Blocking route reasons:

- `runtime_inlet_diagnostics_source_gate_not_pass:fail`
- `setup_codegen_route_not_current_citylbm:legacy_runtime_diagnostic_patch_route`

## Interpretation

The previous geometry blocker was too broad for AIJ Case A because the official isolated-building geometry is a small
analytical block, not a large city STL. The corrected gate now lets the Case A standard block pass, while still blocking
stale generated-source routes before any FluidX3D run.

Next required action is to regenerate the Case A standard-block case with the current CityLBM source so `setup.cpp`
contains the current runtime inlet diagnostics and STG/source-audit markers. No R2, MAE or paper-grade accuracy claim is
allowed from this preflight.

## Verification

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\codegen_preflight_canary_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\validation_dev_loop_smoke.py
dotnet build -c Release
```

All three checks passed on 2026-08-26.

## 2026-08-26 Startup Canary Update

Additional implementation changes:

- `tests/CodegenSmoke/Program.cs` now generates the Case A standard-block case without constructing a RhinoCommon
  `Mesh` in the command-line test process. The generated `buildings.stl` is still a binary 12-triangle `0.08 x 0.08 x
  0.16 m` AIJ Case A block, and `case_metadata.json` records one verified Case A building.
- `scripts/audit_coordinate_probe_protocol.py` now accepts official Case A probe tables that provide `U(m/s)` rather
  than a precomputed `Velocity_Ratio`; the audit records the measured ratio source as
  `computed_from_velocity_mps_over_Uref`.
- `scripts/run_validation_dev_loop.py` now has `--startup-canary`, a one-frame solver-startup mode for fast compile/run
  checks. This mode is not accuracy evidence.

Fresh commands:

```powershell
dotnet run --project tests\CodegenSmoke\CodegenSmoke.csproj -c Release
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casea_current_codegen_standard_box_preflight_20260826_v2' --strict-official-inputs --quick --allow-diagnostic
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_startup_canary_20260826' --strict-official-inputs --quick --startup-canary --allow-diagnostic --execute-canary
```

Fresh results:

- Current generated Case A metadata: `GeometryBuildingCount=1`, `GeometryBuildingHeightM=0.16`, `Nx=547`, `Ny=280`,
  `Nz=160`, `Dx=0.006`, `WindProfileCsvPath=AF_caseA.csv`.
- Current strict no-CFD preflight: `validation_dev_loop_gate=pass`, `diagnostic_canary_ready=true`.
- Startup native FluidX3D canary: `validation_dev_loop_gate=pass`, `NativeShortGate=pass`, `BuildGate=pass`,
  `RunGate=pass`, `RunReturnCode=0`, `RunElapsedSeconds=23.953`, `VtkFileCount=1`.
- Produced VTK: `C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_startup_canary_20260826\diagnostic_solver_cwd\output\u-000000100.vtk`
  (`294067460` bytes).
- Runtime inlet diagnostics audit passed for the startup canary.
- Inlet-correlation audit failed, as expected for a one-frame startup check; correlation and integral-scale evidence
  require a multi-frame development canary or paper-length run.

Updated interpretation:

The accelerated path can now verify, in minutes, that current CityLBM-generated Case A inputs compile and launch native
FluidX3D and produce at least one VTK frame. It still cannot support R2, MAE or paper-grade accuracy claims. The next
optimization target is no longer basic codegen/geometry; it is turbulent-inlet method and U/k/correlation preservation,
followed by boundary-condition equivalence and long-window averaging.

## 2026-08-26 Correlation Canary Update

Additional implementation changes:

- `scripts/run_validation_dev_loop.py` now has `--correlation-canary`, a five-frame diagnostic mode between
  `--startup-canary` and the default development canary.
- Runtime default modes are mutually exclusive: `--paper-defaults`, `--startup-canary`, and `--correlation-canary`
  cannot be combined.
- For non-startup executed canaries, the top-level dev-loop gate now becomes `diagnostic_only` when post-canary runtime
  evidence fails. This prevents a successful FluidX3D run from being misread as successful inlet validation.

Fresh command:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_20260826_gatefix' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary
```

Fresh results:

- `RuntimeDefaultMode=correlation_canary`
- Top-level `validation_dev_loop_gate=diagnostic_only`
- Top-level reason: `post_canary_runtime_evidence_not_pass:fail`
- Native short canary wrapper: `Gate=pass`
- Actual VTK output: `Gate=pass`, `ActualFrameCount=5`, `ExpectedFrameCount=5`, source steps
  `100;200;300;400;500`, final-window span `400`.
- VTK files:
  - `u-000000100.vtk` (`294067460` bytes)
  - `u-000000200.vtk` (`294067460` bytes)
  - `u-000000300.vtk` (`294067460` bytes)
  - `u-000000400.vtk` (`294067460` bytes)
  - `u-000000500.vtk` (`294067460` bytes)
- Runtime inlet diagnostics audit: `pass`.
- Inlet correlation audit: `fail`.
  - Reasons include `adjacent_pair_count_below_100`, `temporal_integral_lag_count_below_2`,
    `spatial_adjacent_correlation_below_0.05`, `spatial_finite_fraction_below_0.8`,
    `spatial_integral_lag_count_below_2`, `k_variance_ratio_below_0.5`, and `tke_to_k_ratio_below_0.5`.
  - `inlet_streamwise_variance_to_k_ratio=0.30920837065278367`.
  - `inlet_tke_to_k_ratio=0.4976367022189486`.
- Planned synthetic-inlet sampling remains diagnostic:
  - `ComputedRefreshCount=16`
  - `MinimumRefreshCount=200`
  - reason `planned_stg_refresh_count_16_below_minimum_200`.

Updated interpretation:

The current native FluidX3D route can compile, run, and write the planned five VTK frames from a real CityLBM-generated
Case A setup. The remaining blocker is no longer launchability; it is inlet turbulence fidelity. The AF mean/k profile
is preserved enough for the runtime diagnostics CSV gate, but the VTK-sampled fluctuation energy and temporal/spatial
correlation are still below validation thresholds. Do not spend time on long Case A or Case E probe-error/R2 runs until
the synthetic inlet update interval, target variance/TKE scaling, and spatial-correlation audit are fixed and this
correlation canary passes.

Verification added:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\validation_dev_loop_smoke.py
```

The smoke test now covers `--correlation-canary` defaults, runtime-mode mutual exclusion, and the top-level
`diagnostic_only` gate when a non-startup post-canary inlet audit fails.

## 2026-08-26 STG Refresh Sensitivity Update

Additional implementation changes:

- `scripts/prepare_native_diagnostic_canary_case.py` can now apply a diagnostic-only
  `--synthetic-turbulence-update-interval` override and replace
  `const uint citylbm_stg_update_interval = ...` in the cloned `setup.cpp`.
- `scripts/run_native_preflight_pack.py`, `scripts/run_codegen_preflight_canary.py`, and
  `scripts/run_validation_dev_loop.py` now pass this override through the full short-canary chain.
- `--correlation-canary` defaults to `diagnostic_canary_stg_update_interval=5`. A more aggressive value such as `2`
  can still be supplied explicitly for sensitivity testing, but it is not suitable as the default fast path.

Fresh command:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg2_20260826' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary --canary-timeout-seconds 900
```

Fresh results:

- Diagnostic canary clone patch: `Gate=pass`.
- `setup.cpp` patch evidence: `StgUpdateIntervalReplacementCount=1`.
- Metadata evidence:
  - `SyntheticTurbulenceUpdateInterval=2`
  - `SyntheticTurbulenceExpectedFinalWindowRefreshCount=200`
  - `ExpectedFinalWindowStepSpan=400`
- Native short canary wrapper: `Gate=fail`.
- Top-level dev-loop gate: `diagnostic_only`.
- Top-level reason: `native_short_canary_not_pass:fail`.
- FluidX3D run elapsed `900.313 s` and timed out before the planned fifth frame.
- Actual VTK output:
  - `u-000000100.vtk` (`294067460` bytes)
  - `u-000000200.vtk` (`294067460` bytes)
  - `u-000000300.vtk` (`294067460` bytes)
  - `u-000000400.vtk` (`294067460` bytes)
- Actual VTK gate reasons included `actual_vtk_frame_count_4_below_minimum_5`,
  `actual_vtk_final_window_step_span_300_below_minimum_400`, and
  `actual_vtk_source_time_steps_do_not_match_planned_schedule`.

Updated interpretation:

The refresh-interval override works, but `citylbm_stg_update_interval=2` exposes a performance bottleneck in the current
host-driven STG implementation: the generated setup repeatedly calls `lbm.run()` in very small chunks to refresh the
inlet. That is too slow for the fast validation loop and should not be used as a default optimization setting. The next
source-level optimization is to move toward an in-kernel or otherwise lower-overhead turbulent-inlet update path, then
rerun a medium refresh interval canary (`5` or `10`) before any paper-length Case A/E R2 evaluation.

Follow-up `interval=5` command:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_20260826' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary --canary-timeout-seconds 600
```

Follow-up `interval=5` results:

- Native short canary wrapper: `Gate=pass`.
- FluidX3D run timed out: `false`.
- Run elapsed: `401.766 s`.
- Actual VTK output: `Gate=pass`, `ActualFrameCount=5`, `ExpectedFrameCount=5`, `VtkFileCount=5`.
- Planned synthetic-inlet sampling gate remains `diagnostic_only`:
  `planned_stg_refresh_count_80_below_minimum_200`.
- Runtime inlet diagnostics audit: `pass`.
- Inlet correlation audit: `fail`.
  - Reasons: `adjacent_pair_count_below_100`, `temporal_integral_lag_count_below_2`,
    `spatial_adjacent_correlation_below_0.05`, `spatial_finite_fraction_below_0.8`,
    `spatial_integral_lag_count_below_2`, and `k_variance_ratio_below_0.5`.
  - `inlet_streamwise_variance_to_k_ratio=0.3133294371987209`.
  - `inlet_tke_to_k_ratio=0.501120964439765`.
  - `temporal_lag1_mean_correlation=0.19676878607254766`.

Interpretation update:

`interval=5` is a workable diagnostic default, but it does not solve the inlet-fidelity problem. The main blocker is now
the turbulent-inlet energy/correlation implementation itself: the VTK-sampled fluctuation energy remains about half of
the AF-table k target, and streamwise variance remains far below the isotropic target. The next code change should be
based on an empty-tunnel inlet preservation test before any empirical intensity scaling is accepted.

## 2026-08-26 STG Intensity Sensitivity And Correlation Audit Fix

Additional implementation changes:

- Added a diagnostic-only `--synthetic-turbulence-intensity-scale` override in
  `scripts/prepare_native_diagnostic_canary_case.py`.
- Passed that override through `scripts/run_native_preflight_pack.py`,
  `scripts/run_codegen_preflight_canary.py`, and `scripts/run_validation_dev_loop.py` as
  `--diagnostic-canary-stg-intensity-scale`.
- The override is recorded in the diagnostic canary metadata and manifests. It is not a CityLBM default and is not
  paper-grade calibration evidence by itself.
- Fixed a false-failure bug in `scripts/audit_inlet_correlation_from_vtk.py`: the previous strided sample selection
  could remove all lag-1 adjacent pairs from the inlet plane, giving `adjacent_pair_count=0` even when the VTK field
  was spatially correlated. The audit now keeps a spatially contiguous deterministic subset.

Fresh command:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1414_20260826' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary --canary-timeout-seconds 700 --diagnostic-canary-stg-intensity-scale 1.414214
```

Fresh runtime results:

- Top-level dev-loop gate: `diagnostic_only`.
- Top-level reason: `post_canary_runtime_evidence_not_pass:fail`.
- Diagnostic canary plan:
  - `SyntheticTurbulenceUpdateInterval=5`
  - `SyntheticTurbulenceIntensityScale=1.414214`
  - `ExpectedFinalWindowRefreshCount=80`
- Generated setup evidence: `const float citylbm_stg_scale = 1.414214f;`.
- Actual VTK output: 5 frames, `u-000000100.vtk` through `u-000000500.vtk`, each `294067460` bytes.
- Runtime inlet diagnostics audit: `pass`.

Original post-canary inlet correlation audit before the sampling fix:

- `inlet_tke_to_k_ratio=1.002242551155159`
- `inlet_streamwise_variance_to_k_ratio=0.6266592444144038`
- `temporal_lag1_mean_correlation=0.19676877499536372`
- Failed reasons still included artificial spatial-sampling failures:
  `adjacent_pair_count_below_100`, `spatial_adjacent_correlation_below_0.05`,
  `spatial_finite_fraction_below_0.8`, and `spatial_integral_lag_count_below_2`.

Re-audit of the same real VTK frames after the sampling fix:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\audit_inlet_correlation_from_vtk.py 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1414_20260826\diagnostic_solver_cwd\output' --out-json 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1414_20260826\inlet_correlation_audit_after_sampling_fix.json' --metadata 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1414_20260826\diagnostic_canary_case\case_metadata.json' --average-last-n 5 --min-frames 5 --min-step-span 400 --wind-direction '1,0,0' --af-csv 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casea_v020_rerun_20260716\official_data\AF_caseA.csv' --require-k-variance-check
```

Re-audit results:

- `inlet_correlation_gate=fail`
- Remaining reason: `temporal_integral_lag_count_below_2`
- `sample_count=20000`
- `adjacent_pair_count=39648`
- `spatial_adjacent_mean_correlation=0.968301380301449`
- `spatial_integral_positive_lag_count=8`
- `temporal_lag1_mean_correlation=0.2575620205219953`
- `temporal_integral_positive_lag_count=1`
- `inlet_tke_to_k_ratio=0.9797077010114744`
- `inlet_streamwise_variance_to_k_ratio=0.5969832785086854`

Updated interpretation:

The real native FluidX3D canary now shows that the previous TKE shortfall was primarily an inlet-intensity scaling
problem: using `scale=sqrt(2)` brings total TKE close to the AF/full-tensor target. The spatial-correlation failure was
partly an audit sampling bug, not solver physics. After fixing the audit, spatial correlation is strong and measurable.
The remaining blocker is temporal correlation persistence: the lag-1 correlation is positive, but the positive temporal
integral length reaches only one lag in this five-frame canary. Do not start Case E paper-grade validation until the
time-correlation model and longer averaging window pass the same audit without diagnostic-only caveats.

Verification:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\inlet_correlation_integral_scale_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\prepare_native_diagnostic_canary_case_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\codegen_preflight_canary_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\validation_dev_loop_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\native_preflight_pack_smoke.py
dotnet build -c Release
```

All listed checks passed. `dotnet build -c Release` completed with `0` warnings and `0` errors.

## 2026-08-26 temporal-step canary and audit correction

Additional implementation changes:

- Added a diagnostic-only `--synthetic-turbulence-temporal-step-scale` override in
  `scripts/prepare_native_diagnostic_canary_case.py`.
- Passed that override through `scripts/run_native_preflight_pack.py`,
  `scripts/run_codegen_preflight_canary.py`, and `scripts/run_validation_dev_loop.py` as
  `--diagnostic-canary-stg-temporal-step-scale`.
- Corrected `scripts/audit_inlet_correlation_from_vtk.py` so k/TKE evidence is estimated from per-frame inlet-plane
  spatial variance after subtracting the target mean profile. Fixed-point temporal variance is still reported, but it
  is no longer used as the k/TKE energy gate because a persistent turbulent inlet can be physically correlated in time
  and still preserve instantaneous plane RMS.
- Replaced biased prefix-only plane sampling with stratified inlet-plane sampling across the vertical profile while
  preserving adjacent pairs for spatial-correlation checks.

Rejected diagnostic setting:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1414_temporal010_20260826' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary --canary-timeout-seconds 700 --diagnostic-canary-stg-intensity-scale 1.414214 --diagnostic-canary-stg-temporal-step-scale 0.1
```

- Generated 5 real FluidX3D VTK frames, `u-000000100.vtk` through `u-000000500.vtk`.
- Runtime inlet diagnostics audit: `pass`.
- Full-plane re-audit after the spatial-energy fix: temporal/spatial correlation passed, but the additional
  `sqrt(2)` intensity scale over-amplified the full Reynolds-stress target and is therefore not a valid default.

Accepted short-canary diagnostic setting:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' scripts\run_validation_dev_loop.py --case casea --fluidx3d-source 'F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master' --out-dir 'C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1000_temporal010_20260826' --strict-official-inputs --quick --correlation-canary --allow-diagnostic --execute-canary --canary-timeout-seconds 700 --diagnostic-canary-stg-temporal-step-scale 0.1
```

Fresh runtime evidence:

- Real VTK output: 5 frames, `u-000000100.vtk` through `u-000000500.vtk`, each `294067460` bytes.
- Runtime inlet diagnostics audit: `pass`.
- Post-patch default balanced-sample audit:
  `C:\Users\MSY\AppData\Local\Temp\CityLBM\validation_runs\casea_correlation_canary_stg5_scale1000_temporal010_20260826\inlet_correlation_audit_balanced_sample_after_fix.json`
- `inlet_correlation_gate=pass`
- `sample_count=19880` of `plane_point_count=44800`
- `inlet_streamwise_variance_to_k_ratio=1.4355423979135937`
- `inlet_tke_to_k_ratio=1.248794274650052`
- `temporal_lag1_mean_correlation=0.8681908311134396`
- `temporal_integral_positive_lag_count=3`
- `spatial_adjacent_mean_correlation=0.839460306955738`
- `spatial_integral_positive_lag_count=5`

Updated interpretation:

This is a newly run native FluidX3D short canary, not a paper-grade validation run. It supports moving from source-level
inlet debugging to the next gate: a longer Case A native baseline with sufficient spin-up, averaging window and probe
post-processing. Do not report Case A R2/MAE as publishable until that longer run is complete. Do not start Case E SCI
validation until Case A native baseline error is quantified and the same inlet/boundary settings are migrated into the
CityLBM Grasshopper workflow.

Verification:

```powershell
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\prepare_native_diagnostic_canary_case_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\codegen_preflight_canary_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\validation_dev_loop_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\native_preflight_pack_smoke.py
& 'C:\Program Files\ladybug_tools\python\python.exe' tests\inlet_correlation_integral_scale_smoke.py
dotnet build -c Release
git diff --check -- scripts/audit_inlet_correlation_from_vtk.py scripts/prepare_native_diagnostic_canary_case.py scripts/run_native_preflight_pack.py scripts/run_codegen_preflight_canary.py scripts/run_validation_dev_loop.py tests/inlet_correlation_integral_scale_smoke.py tests/prepare_native_diagnostic_canary_case_smoke.py tests/codegen_preflight_canary_smoke.py tests/validation_dev_loop_smoke.py tests/native_preflight_pack_smoke.py
```

All Python smoke checks passed. `dotnet build -c Release` completed with `0` warnings and `0` errors. `git diff --check`
reported only LF-to-CRLF working-tree warnings for edited files and no whitespace errors.
