# CityLBM Validation Acceleration Plan

- Generated: 2026-08-24T23:31:42.950819Z
- Case preset: casea

## Development Time Compression

- Fastest phase: resolve_reynolds_stress_offdiagonal_or_precursor_gap
- Next execution policy: run_no_cfd_preflight_first
- Next batch: no_cfd_source_and_protocol_preflight
- Long CFD allowed now: false
- Parallel no-CFD command count: 11

### Next Command To Run First

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\enable_fluidx3d_ddf_reconstruction_route.py" "--case-dir" "<case_dir>" "--defines" "<case_dir>\src\defines.hpp" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\enable_ddf_reconstruction_route_manifest.json"
```
- Time saved by:
  - stop_before_solver_when_source_protocol_or_probe_gates_fail
  - run_parallel_no_cfd_audits_before_any_canary
  - use_short_native_canary_before_paper_length_vtk_generation
  - migrate_to_citylbm_only_after_native_fluidx3d_evidence_passes

## Fastest Next Actions

### 1. resolve_reynolds_stress_offdiagonal_or_precursor_gap
- Duration class: minutes
- Runs CFD: false
- Reason: The AF file provides measured diagonal RMS components, so the isotropic-k fallback is no longer the main issue; the remaining inlet evidence gap is missing off-diagonal covariance or precursor-equivalent evidence.
- Next action: Use the diagonal RMS path for diagnostic canaries, but collect/derive off-diagonal Reynolds-stress or a traceable precursor/equivalent-inlet evidence file before claiming paper-grade turbulent inflow.

### 3. resolve_boundary_and_wall_protocol_evidence
- Duration class: minutes
- Runs CFD: false
- Reason: Boundary, outlet, side/top or rough-wall evidence is also blocking paper-grade validation.
- Next action: Prepare a traceable AIJ-equivalent boundary-protocol evidence JSON and link it in case_metadata before any long CFD run.

### 10. native_first_then_citylbm
- Duration class: policy
- Runs CFD: false
- Reason: CityLBM should only inherit settings that improve the native FluidX3D baseline.
- Next action: Do not tune CityLBM against AIJ before native FluidX3D passes the same input, averaging and probe gates.

### 11. batch_only_after_single_case_passes
- Duration class: policy
- Runs CFD: false
- Reason: Batching many directions before one strict case passes multiplies bad evidence.
- Next action: Keep Case E ac+N as the first strict chain; add Case A/E batches only after this gate is stable.

## Command Templates

### current_codegen_full_gate

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_codegen_preflight_canary.py" "--expected-aij-case" "CaseA" "--expected-wind-direction" "N" "--expected-wind-vector" "1,0,0" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--allow-diagnostic" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--require-af-k"
```

### current_codegen_quick_gate

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_codegen_preflight_canary.py" "--expected-aij-case" "CaseA" "--expected-wind-direction" "N" "--expected-wind-vector" "1,0,0" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--allow-diagnostic" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--require-af-k" "--quick"
```

### preflight_no_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k"
```

### diagnostic_canary_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "5000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "5" "--average-last-n" "5" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

### paper_candidate_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k" "--install" "--build" "--run"
```

## Parallel Development Batches

### 0. no_cfd_source_and_protocol_preflight
- Runs CFD: false
- Can run in parallel: true
- Purpose: Close cheap setup.cpp, inlet, boundary and protocol identity failures before any long FluidX3D run.
- Promotion gate: Do not launch CFD until inlet-source, boundary-source, official-input and protocol pre-run gates are clean enough for the selected diagnostic or paper route.
- Commands:

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\enable_fluidx3d_ddf_reconstruction_route.py" "--case-dir" "<case_dir>" "--defines" "<case_dir>\src\defines.hpp" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\enable_ddf_reconstruction_route_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_source.py" "--setup" "<case_dir>\src\setup.cpp" "--defines" "<case_dir>\src\defines.hpp" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\inlet_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_protocol.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_protocol_audit.json" "--expected-aij-case" "CaseA" "--expected-wind-direction" "N"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\write_validation_protocol_audit.py" "--case-dir" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\validation_protocol_audit.json" "--case" "CaseA" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--inlet-reynolds-stress-evidence" "<case_dir>\preflight\inlet_reynolds_stress_evidence.json" "--boundary-source-audit" "<case_dir>\preflight\boundary_source_audit.json" "--wind-direction-label" "N" "--wind-vector" "1,0,0"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_coordinate_probe_protocol.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseA" "--expected-wind-direction" "N" "--expected-wind-vector" "1,0,0" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_boundary_protocol_evidence_template.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_protocol_evidence_template.json" "--case" "CaseA" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_inlet_reynolds_stress_template.py" "--metadata" "<case_dir>\case_metadata.json" "--af-csv" "<official_AF_csv>" "--out-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--out-precursor-json" "<case_dir>\preflight\equivalent_precursor_evidence_template.json" "--case" "CaseA" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\build_inlet_reynolds_stress_evidence.py" "--af-csv" "<official_AF_csv>" "--metadata" "<case_dir>\case_metadata.json" "--case" "CaseA" "--source-type" "auto" "--stress-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--precursor-evidence" "<case_dir>\preflight\equivalent_precursor_evidence_template.json" "--out" "<case_dir>\preflight\inlet_reynolds_stress_evidence.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_source.py" "--setup" "<case_dir>\src\setup.cpp" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_fluidx3d_equilibrium_boundary.py" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\fluidx3d_equilibrium_boundary_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k"
```
- Stop if:
  - inlet_source_velocity_field_only_without_distribution_reconstruction
  - inlet_reynolds_stress_evidence_missing_offdiagonal_or_precursor
  - fluidx3d_type_e_ddf_route_not_proven
  - boundary_source_simplified_without_AIJ_boundary_evidence
  - coordinate_probe_protocol_or_Uref_identity_mismatch
  - validation_protocol_prerun_gate_not_ready
  - official_AF_or_RS_identity_mismatch

### 1. short_native_canary
- Runs CFD: true
- Can run in parallel: false
- Purpose: Run only a short native FluidX3D canary after no-CFD gates identify no blocking source or protocol errors.
- Promotion gate: Promote to paper-length CFD only if new VTK hashes, source parity, inlet/boundary runtime audits and probe projection gates are interpretable.
- Commands:

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "5000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "5" "--average-last-n" "5" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_diagnostics_csv.py" "<solver_cwd_or_fluidx3d_source>\casea_inlet_turbulence_stats.csv" "--out-json" "<case_dir>\preflight\inlet_diagnostics_csv_audit.json" "--out-csv" "<case_dir>\preflight\inlet_diagnostics_csv_summary.csv" "--require-k" "--require-rms"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_native_preconditions.py" "<case_dir>" "--manifest" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "<case_dir>\case_metadata.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--boundary-source-audit" "<case_dir>\preflight\boundary_source_audit.json" "--boundary-protocol-audit" "<case_dir>\preflight\boundary_protocol_audit.json" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--case" "CaseA" "--average-last-n" "40" "--min-avg-frames" "40" "--min-avg-step-span" "20000" "--out" "<case_dir>\preflight\native_preconditions_audit.json" "--wind-direction-label" "N" "--wind-vector" "1,0,0"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\summarize_validation_blockers.py" "--run-dir" "<case_dir>" "--native-manifest" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--native-preconditions" "<case_dir>\preflight\native_preconditions_audit.json"
```
- Stop if:
  - fresh_VTK_missing_or_stale
  - runtime_inlet_diagnostics_csv_missing_or_failed
  - inlet_U_or_k_profile_not_preserved
  - boundary_runtime_profile_not_preserved
  - probe_projection_or_Uref_component_mismatch

### 2. paper_candidate_native_run
- Runs CFD: true
- Can run in parallel: false
- Purpose: Spend long solver time only after the canary closes the protocol-level blockers.
- Promotion gate: Only after this native chain passes should the same setup be migrated to CityLBM and compared as a native-CityLBM parity test.
- Commands:

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseA" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--expected-probe-row-count" "186" "--expected-probe-z-min" "0.01" "--expected-probe-z-max" "0.28" "--z-ref" "0.16" "--expected-uref" "4.491" "--expected-wind-vector" "1,0,0" "--require-af-k" "--install" "--build" "--run"
```
- Stop if:
  - R2_or_bias_interpreted_before_native_preconditions_pass
  - systematic_bias_about_minus_0.20_to_minus_0.35_without_closed_inlet_boundary_probe_gates

## Run Findings

### F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casea_native_preflight_current_strict_20260825_zrange_require_k_rerun2
- Failures:
  - ValidationProtocolAuditGate:diagnostic_only (validation_protocol_prerun_item_fail:inlet_distribution_consistency; validation_protocol_prerun_item_fail:boundary_conditions; validation_protocol_prerun_item_fail:wall_roughness_model)
  - CaseMetadataPreconditionGate:diagnostic_only (case_metadata_paper_grade_turbulent_inlet_prerequisite_missing; case_metadata_paper_grade_boundary_prerequisite_missing; case_metadata_synthetic_turbulent_inlet_injected_missing)
  - PreExecutionGate:diagnostic_only (validation_protocol_prerun_item_fail:inlet_distribution_consistency; validation_protocol_prerun_item_fail:boundary_conditions; validation_protocol_prerun_item_fail:wall_roughness_model)
  - RunnerGate:diagnostic_only (validation_protocol_prerun_item_fail:inlet_distribution_consistency; validation_protocol_prerun_item_fail:boundary_conditions; validation_protocol_prerun_item_fail:wall_roughness_model)
  - NativeAccuracyEvidenceGate:fail (native_run_not_requested; actual_vtk_output_not_required_by_this_invocation; actual_vtk_output_gate_not_pass:not_applicable)
  - PaperUseGate:fail (pre_execution_gate_not_pass:diagnostic_only; pre_execution:validation_protocol_prerun_item_fail:inlet_distribution_consistency; pre_execution:validation_protocol_prerun_item_fail:boundary_conditions)
  - native_preconditions_gate:fail
  - native_precondition_closure_gate:fail
  - validation_protocol_audit.json:Gate:diagnostic_only (inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; systematic_bias_gate)
  - validation_protocol_audit.json:PaperGradeGate:diagnostic_only (inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; systematic_bias_gate)
  - validation_protocol_audit.json:PreRunGate:diagnostic_only (inlet_distribution_consistency; boundary_conditions; wall_roughness_model)
  - validation_protocol_audit.json:RiskKeys (grid_resolution)
