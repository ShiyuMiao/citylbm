# CityLBM Validation Acceleration Plan

- Generated: 2026-08-25T04:40:31.818481Z
- Case preset: casee

## Development Time Compression

- Fastest phase: resolve_turbulent_length_scale_evidence
- Next execution policy: create_or_bind_turbulence_length_scale_evidence_before_cfd
- Next batch: no_cfd_source_and_protocol_preflight
- Long CFD allowed now: false
- Parallel no-CFD command count: 18

### Next Command To Run First

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_turbulence_length_scale_evidence_template.py" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\turbulence_length_scale_evidence.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```
- Time saved by:
  - stop_before_solver_when_source_protocol_or_probe_gates_fail
  - run_parallel_no_cfd_audits_before_any_canary
  - use_short_native_canary_before_paper_length_vtk_generation
  - migrate_to_citylbm_only_after_native_fluidx3d_evidence_passes

## Fastest Next Actions

### 1. resolve_turbulent_length_scale_evidence
- Duration class: minutes
- Runs CFD: false
- Reason: The inlet source needs traceable turbulent length-scale evidence before paper-grade CFD.
- Next action: Link an official, precursor, recycling or validated length-scale evidence source in metadata before launching a paper-length run.

### 2. audit_runtime_inlet_csv_after_each_canary
- Duration class: seconds
- Runs CFD: false
- Reason: Runtime inlet statistics can be checked from CSV without waiting for expensive VTK postprocessing.
- Next action: Run audit_inlet_diagnostics_csv.py after every short canary and stop if U/k/RMS/Reynolds-stress preservation fails.

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
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_codegen_preflight_canary.py" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--allow-diagnostic" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--require-af-k"
```

### current_codegen_quick_gate

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_codegen_preflight_canary.py" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--allow-diagnostic" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--require-af-k" "--quick"
```

### preflight_pack_no_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_preflight_pack.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out-dir" "<case_dir>\preflight" "--manifest-out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "<case_dir>\case_metadata.json" "--expected-aij-case" "CaseE" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--patch-metadata-identity" "--allow-diagnostic" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--require-af-k" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>"
```

### bind_reynolds_stress_metadata

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_inlet_reynolds_stress_metadata.py" "--metadata" "<case_dir>\case_metadata.json" "--stress-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--out" "<case_dir>\preflight\case_metadata.reynolds_bound.json" "--source-note" "Identity binding only; keep diagnostic until full tensor or precursor audit passes."
```

### bind_turbulence_length_scale_metadata

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_turbulence_length_scale_metadata.py" "--metadata" "<case_dir>\case_metadata.json" "--evidence-json" "<case_dir>\preflight\turbulence_length_scale_evidence.json" "--out" "<case_dir>\preflight\case_metadata.length_scale_bound.json" "--source-note" "Identity binding only; keep diagnostic until official, precursor or calibrated length-scale evidence passes."
```

### preflight_no_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k"
```

### diagnostic_canary_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "2000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "2" "--average-last-n" "2" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

### paper_candidate_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run"
```

## Parallel Development Batches

### 0. no_cfd_source_and_protocol_preflight
- Runs CFD: false
- Can run in parallel: true
- Purpose: Close cheap setup.cpp, inlet, boundary and protocol identity failures before any long FluidX3D run.
- Promotion gate: Do not launch CFD until inlet-source, boundary-source, official-input and protocol pre-run gates are clean enough for the selected diagnostic or paper route.
- Commands:

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_preflight_pack.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out-dir" "<case_dir>\preflight" "--manifest-out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "<case_dir>\case_metadata.json" "--expected-aij-case" "CaseE" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--patch-metadata-identity" "--allow-diagnostic" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--require-af-k" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\patch_legacy_customtable_profile_origin.py" "--case-dir" "<case_dir>" "--setup" "<case_dir>\src\setup.cpp" "--domain-origin" "<case_dir>\domain_origin.json" "--out" "<case_dir>\preflight\patch_legacy_customtable_profile_origin_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_protocol.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_protocol_audit.json" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\write_validation_protocol_audit.py" "--case-dir" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\validation_protocol_audit.json" "--case" "CaseE" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--inlet-reynolds-stress-evidence" "<case_dir>\preflight\inlet_reynolds_stress_evidence.json" "--boundary-source-audit" "<case_dir>\preflight\boundary_source_audit.json" "--wind-direction-label" "N" "--wind-vector" "0,-1,0"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_coordinate_probe_protocol.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\patch_fluidx3d_equilibrium_boundary_source.py" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\patch_fluidx3d_equilibrium_boundary_source_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\enable_fluidx3d_ddf_reconstruction_route.py" "--case-dir" "<case_dir>" "--defines" "<case_dir>\src\defines.hpp" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\enable_ddf_reconstruction_route_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_coordinate_probe_protocol_metadata.py" "--metadata" "<case_dir>\case_metadata.json" "--case-dir" "<case_dir>" "--setup" "<case_dir>\src\setup.cpp" "--out" "<case_dir>\preflight\case_metadata.coordinate_probe_bound.json" "--case-label" "CaseE" "--wind-direction" "N" "--wind-vector" "0,-1,0" "--probe-count" "80" "--z-ref" "15.9" "--uref" "3.928296" "--official-rs" "<official_RS_csv>" "--official-af" "<official_AF_csv>"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_source.py" "--setup" "<case_dir>\src\setup.cpp" "--defines" "<case_dir>\src\defines.hpp" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\inlet_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_boundary_protocol_evidence_template.py" "<case_dir>" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_protocol_evidence_template.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_inlet_reynolds_stress_template.py" "--metadata" "<case_dir>\case_metadata.json" "--af-csv" "<official_AF_csv>" "--out-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--out-precursor-json" "<case_dir>\preflight\equivalent_precursor_evidence_template.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_turbulence_length_scale_evidence_template.py" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\turbulence_length_scale_evidence.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_turbulence_length_scale_metadata.py" "--metadata" "<case_dir>\case_metadata.json" "--evidence-json" "<case_dir>\preflight\turbulence_length_scale_evidence.json" "--out" "<case_dir>\preflight\case_metadata.length_scale_bound.json" "--source-note" "Identity binding only; keep diagnostic until official, precursor or calibrated length-scale evidence passes."
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\build_inlet_reynolds_stress_evidence.py" "--af-csv" "<official_AF_csv>" "--metadata" "<case_dir>\case_metadata.json" "--case" "CaseE" "--source-type" "auto" "--stress-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--precursor-evidence" "<case_dir>\preflight\equivalent_precursor_evidence_template.json" "--out" "<case_dir>\preflight\inlet_reynolds_stress_evidence.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_source.py" "--setup" "<case_dir>\src\setup.cpp" "--metadata" "<case_dir>\case_metadata.json" "--out" "<case_dir>\preflight\boundary_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_fluidx3d_equilibrium_boundary.py" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\preflight\fluidx3d_equilibrium_boundary_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_inlet_reynolds_stress_metadata.py" "--metadata" "<case_dir>\case_metadata.json" "--stress-csv" "<case_dir>\preflight\inlet_reynolds_stress_tensor_template.csv" "--out" "<case_dir>\preflight\case_metadata.reynolds_bound.json" "--source-note" "Identity binding only; keep diagnostic until full tensor or precursor audit passes."
```
- Stop if:
  - inlet_source_velocity_field_only_without_distribution_reconstruction
  - inlet_reynolds_stress_evidence_missing_offdiagonal_or_precursor
  - fluidx3d_source_reconstruct_hook_patch_failed
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
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "2000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "2" "--average-last-n" "2" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_diagnostics_csv.py" "<solver_cwd_or_fluidx3d_source>\casee_inlet_turbulence_stats.csv" "--out-json" "<case_dir>\preflight\inlet_diagnostics_csv_audit.json" "--out-csv" "<case_dir>\preflight\inlet_diagnostics_csv_summary.csv" "--require-k" "--require-rms" "--require-reynolds-stress"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_native_preconditions.py" "<case_dir>" "--manifest" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "<case_dir>\case_metadata.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--boundary-source-audit" "<case_dir>\preflight\boundary_source_audit.json" "--boundary-protocol-audit" "<case_dir>\preflight\boundary_protocol_audit.json" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--case" "CaseE" "--average-last-n" "40" "--min-avg-frames" "40" "--min-avg-step-span" "20000" "--out" "<case_dir>\preflight\native_preconditions_audit.json" "--wind-direction-label" "N" "--wind-vector" "0,-1,0"
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
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "<case_dir>" "--fluidx3d-source" "<fluidx3d_source>" "--out" "<case_dir>\native_fluidx3d_baseline_manifest.json" "--metadata" "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825\case_metadata.inlet_bound.json" "--inlet-source-audit" "<case_dir>\preflight\inlet_source_audit.json" "--coordinate-probe-protocol-audit" "<case_dir>\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--official" "<official_RS_csv>" "--af-csv" "<official_AF_csv>" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run"
```
- Stop if:
  - R2_or_bias_interpreted_before_native_preconditions_pass
  - systematic_bias_about_minus_0.20_to_minus_0.35_without_closed_inlet_boundary_probe_gates

## Run Findings

### F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825
- Failures:
  - ValidationProtocolAuditGate:diagnostic_only (validation_protocol_item_fail:inlet_mean_profile; validation_protocol_item_fail:inlet_turbulence_k; validation_protocol_item_fail:inlet_distribution_consistency)
  - CaseMetadataPreconditionGate:diagnostic_only (case_metadata_paper_grade_turbulent_inlet_prerequisite_not_pass:fail; case_metadata_paper_grade_boundary_prerequisite_not_pass:fail; case_metadata_turbulent_inlet_status_diagnostic_only)
  - CaseSetupSourcePreconditionGate:diagnostic_only (case_setup_source_time_steps_mismatch_expected_60000; case_setup_source_save_interval_mismatch_expected_500)
  - PreExecutionGate:diagnostic_only (validation_protocol_item_fail:inlet_mean_profile; validation_protocol_item_fail:inlet_turbulence_k; validation_protocol_item_fail:inlet_distribution_consistency)
  - PlannedSyntheticInletSamplingGate:diagnostic_only (metadata_stg_refresh_count_36_does_not_match_computed_1580)
  - RunnerGate:diagnostic_only (validation_protocol_item_fail:inlet_mean_profile; validation_protocol_item_fail:inlet_turbulence_k; validation_protocol_item_fail:inlet_distribution_consistency)
  - NativeAccuracyEvidenceGate:fail (native_run_not_requested; actual_vtk_output_not_required_by_this_invocation; actual_vtk_output_gate_not_pass:not_applicable)
  - PaperUseGate:fail (inlet_source_gate_not_pass:diagnostic_only; inlet_source:paper_grade_inlet_source_gate_not_pass:fail; inlet_source:source_missing_turbulent_length_scale_evidence)
  - native_preconditions_gate:fail
  - native_precondition_closure_gate:fail
  - validation_protocol_audit.json:Gate:diagnostic_only (inlet_mean_profile; inlet_turbulence_k; inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; lbm_stability_scaling; systematic_bias_gate; grid_resolution)
  - validation_protocol_audit.json:PaperGradeGate:diagnostic_only (inlet_mean_profile; inlet_turbulence_k; inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; lbm_stability_scaling; systematic_bias_gate; grid_resolution)
