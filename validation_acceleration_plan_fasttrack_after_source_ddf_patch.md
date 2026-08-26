# CityLBM Validation Acceleration Plan

- Generated: 2026-08-25T02:09:58.027107Z
- Case preset: casee

## Development Time Compression

- Fastest phase: bind_reynolds_stress_evidence_to_current_case
- Next execution policy: bind_current_case_evidence_before_preflight
- Next batch: no_cfd_source_and_protocol_preflight
- Long CFD allowed now: false
- Parallel no-CFD command count: 16

### Next Command To Run First

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_inlet_reynolds_stress_metadata.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--stress-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_tensor_template.csv" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\case_metadata.reynolds_bound.json" "--source-note" "Identity binding only; keep diagnostic until full tensor or precursor audit passes."
```
- Time saved by:
  - stop_before_solver_when_source_protocol_or_probe_gates_fail
  - run_parallel_no_cfd_audits_before_any_canary
  - use_short_native_canary_before_paper_length_vtk_generation
  - migrate_to_citylbm_only_after_native_fluidx3d_evidence_passes

## Fastest Next Actions

### 1. bind_reynolds_stress_evidence_to_current_case
- Duration class: minutes
- Runs CFD: false
- Reason: The Reynolds-stress or precursor evidence is not explicitly bound to the current case metadata hash and source hash.
- Next action: Add the matching stress CSV SHA256 or precursor case_metadata_sha256/case/wind binding to case_metadata, then rerun the no-CFD preflight.

### 2. audit_runtime_inlet_csv_after_each_canary
- Duration class: seconds
- Runs CFD: false
- Reason: Runtime inlet statistics can be checked from CSV without waiting for expensive VTK postprocessing.
- Next action: Run audit_inlet_diagnostics_csv.py after every short canary and stop if U/k/RMS/Reynolds-stress preservation fails.

### 2. resolve_coordinate_probe_uref_protocol
- Duration class: minutes
- Runs CFD: false
- Reason: Coordinate axes, probe rows, wind vector, velocity component or Uref identity is blocking interpretation.
- Next action: Run audit_coordinate_probe_protocol.py and audit_component_sensitivity.py, then fix metadata, official probe subset or normalization before any long CFD run.

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

### bind_reynolds_stress_metadata

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_inlet_reynolds_stress_metadata.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--stress-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_tensor_template.csv" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\case_metadata.reynolds_bound.json" "--source-note" "Identity binding only; keep diagnostic until full tensor or precursor audit passes."
```

### bind_turbulence_length_scale_metadata

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_turbulence_length_scale_metadata.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--evidence-json" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\turbulence_length_scale_evidence.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\case_metadata.length_scale_bound.json" "--source-note" "Identity binding only; keep diagnostic until official, precursor or calibrated length-scale evidence passes."
```

### preflight_no_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k"
```

### diagnostic_canary_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "2000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "2" "--average-last-n" "2" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

### paper_candidate_cfd

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run"
```

## Parallel Development Batches

### 0. no_cfd_source_and_protocol_preflight
- Runs CFD: false
- Can run in parallel: true
- Purpose: Close cheap setup.cpp, inlet, boundary and protocol identity failures before any long FluidX3D run.
- Promotion gate: Do not launch CFD until inlet-source, boundary-source, official-input and protocol pre-run gates are clean enough for the selected diagnostic or paper route.
- Commands:

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\patch_fluidx3d_equilibrium_boundary_source.py" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\patch_fluidx3d_equilibrium_boundary_source_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\patch_legacy_customtable_profile_origin.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--setup" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\setup.cpp" "--domain-origin" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\domain_origin.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\patch_legacy_customtable_profile_origin_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_protocol.py" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_protocol_audit.json" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\write_validation_protocol_audit.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\validation_protocol_audit.json" "--case" "CaseE" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--inlet-reynolds-stress-evidence" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_evidence.json" "--boundary-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_source_audit.json" "--wind-direction-label" "N" "--wind-vector" "0,-1,0"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_coordinate_probe_protocol.py" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\coordinate_probe_protocol_audit.json" "--expected-aij-case" "CaseE" "--expected-wind-direction" "N" "--expected-wind-vector" "0,-1,0" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\enable_fluidx3d_ddf_reconstruction_route.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--defines" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\defines.hpp" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\enable_ddf_reconstruction_route_manifest.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_source.py" "--setup" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\setup.cpp" "--defines" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\defines.hpp" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_boundary_protocol_evidence_template.py" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_protocol_evidence_template.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_inlet_reynolds_stress_template.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--out-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_tensor_template.csv" "--out-precursor-json" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\equivalent_precursor_evidence_template.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\create_turbulence_length_scale_evidence_template.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\turbulence_length_scale_evidence.json" "--case" "CaseE" "--wind-direction" "N" "--force"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_turbulence_length_scale_metadata.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--evidence-json" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\turbulence_length_scale_evidence.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\case_metadata.length_scale_bound.json" "--source-note" "Identity binding only; keep diagnostic until official, precursor or calibrated length-scale evidence passes."
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\build_inlet_reynolds_stress_evidence.py" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--case" "CaseE" "--source-type" "auto" "--stress-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_tensor_template.csv" "--precursor-evidence" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\equivalent_precursor_evidence_template.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_evidence.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_boundary_source.py" "--setup" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\setup.cpp" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_source_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_fluidx3d_equilibrium_boundary.py" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\fluidx3d_equilibrium_boundary_audit.json"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\bind_inlet_reynolds_stress_metadata.py" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--stress-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_reynolds_stress_tensor_template.csv" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\case_metadata.reynolds_bound.json" "--source-note" "Identity binding only; keep diagnostic until full tensor or precursor audit passes."
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
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "2000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "2" "--average-last-n" "2" "--min-vtk-frames" "1" "--min-vtk-step-span" "0" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run" "--allow-diagnostic-execution"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_inlet_diagnostics_csv.py" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source\casee_inlet_turbulence_stats.csv" "--out-json" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_diagnostics_csv_audit.json" "--out-csv" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_diagnostics_csv_summary.csv" "--require-k" "--require-rms" "--require-reynolds-stress"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\audit_native_preconditions.py" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--manifest" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--metadata" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\case_metadata.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--boundary-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_source_audit.json" "--boundary-protocol-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\boundary_protocol_audit.json" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--case" "CaseE" "--average-last-n" "40" "--min-avg-frames" "40" "--min-avg-step-span" "20000" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\native_preconditions_audit.json" "--wind-direction-label" "N" "--wind-vector" "0,-1,0"
```

```powershell
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\summarize_validation_blockers.py" "--run-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--native-manifest" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--native-preconditions" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\native_preconditions_audit.json"
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
"C:\Users\MSY\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe" "scripts\run_native_fluidx3d_case.py" "--case-dir" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup" "--fluidx3d-source" "F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\casee_sci_rerun_20260716\fluidx3d_source" "--out" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\native_fluidx3d_baseline_manifest.json" "--inlet-source-audit" "C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\inlet_source_audit.json" "--expected-aij-case" "CaseE" "--official" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/RS_caseE.csv" "--af-csv" "F:/Grade2master2/CITYLBM开发文件/citylbm_v0.2.0_portable/validation/casee_sci_rerun_20260716/official_data/AF_caseE.csv" "--time-steps" "40000" "--vtk-save-interval" "1000" "--expected-vtk-frame-count" "40" "--average-last-n" "40" "--min-vtk-frames" "40" "--min-vtk-step-span" "20000" "--expected-wind-direction" "N" "--official-condition-filter" "ac" "--official-wind-filter" "N" "--expected-probe-row-count" "80" "--expected-probe-z" "2.0" "--z-ref" "15.9" "--expected-uref" "3.928296" "--expected-wind-vector" "0,-1,0" "--require-af-k" "--install" "--build" "--run"
```
- Stop if:
  - R2_or_bias_interpreted_before_native_preconditions_pass
  - systematic_bias_about_minus_0.20_to_minus_0.35_without_closed_inlet_boundary_probe_gates

## Run Findings

### C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\pack_after_source_ddf_patch
- Failures:
  - native_preconditions_gate:fail
  - native_precondition_closure_gate:fail
  - validation_protocol_audit.json:Gate:diagnostic_only (inlet_mean_profile; inlet_turbulence_k; inlet_reynolds_stress_tensor; inlet_temporal_sampling; inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; lbm_stability_scaling; wind_direction_sign; coordinate_transform; probe_projection; normalization_basis; systematic_bias_gate; grid_resolution)
  - validation_protocol_audit.json:PaperGradeGate:diagnostic_only (inlet_mean_profile; inlet_turbulence_k; inlet_reynolds_stress_tensor; inlet_temporal_sampling; inlet_distribution_consistency; native_fluidx3d_baseline; boundary_conditions; wall_roughness_model; lbm_stability_scaling; wind_direction_sign; coordinate_transform; probe_projection; normalization_basis; systematic_bias_gate; grid_resolution)
  - validation_protocol_audit.json:PreRunGate:diagnostic_only (inlet_mean_profile; inlet_turbulence_k; inlet_reynolds_stress_tensor; inlet_temporal_sampling; inlet_distribution_consistency; boundary_conditions; wall_roughness_model; lbm_stability_scaling; wind_direction_sign; coordinate_transform; normalization_basis)
  - validation_protocol_audit.json:RiskKeys (inlet_turbulence_length_scale)
  - validation_protocol_audit.json:PreRunRiskKeys (inlet_turbulence_length_scale)
  - native_preflight_pack_manifest.json:diagnostic_only (inlet_source:source_missing_turbulent_length_scale_evidence; inlet_source:source_has_measured_diagonal_rms_but_missing_offdiagonal_or_precursor_tensor; inlet_source:source_missing_runtime_inlet_diagnostics_csv_for_u_k_rms_preservation; inlet_reynolds_stress:stress_csv_no_valid_full_tensor_rows; inlet_reynolds_stress:measured_stress_tensor_requires_at_least_two_valid_heights; inlet_reynolds_stress:stress_csv_sha256_missing_in_metadata; inlet_reynolds_stress:stress_csv_evidence_quality_not_paper_grade:missing; turbulence_length_scale:length_scale_source_file_missing; turbulence_length_scale:paper_admissible_review_flag_missing; boundary_source:boundary_source_not_wind_tunnel_equivalent; boundary_source:boundary_source_fidelity_class_not_paper_grade:partial_type_e_boundary_source; boundary_source:boundary_source_missing_advanced_code_evidence; boundary_source:boundary_source_simplified_type_e_or_solid_only; boundary_source:ground_and_buildings_no_slip_without_rough_wall_or_precursor; boundary_source:outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary; boundary_source:missing_non_reflecting_or_validated_outlet_state; boundary_source:missing_side_top_boundary_pair_mapping; boundary_source:missing_rough_wall_or_wall_function_action; boundary_source:missing_precursor_or_recycling_development_field; boundary_protocol:metadata_boundary_protocol_gate_missing; boundary_protocol:approx_frontal_blockage_ratio_missing; boundary_protocol:missing_evidence_fields:inlet_fetch_clearance_h,downstream_clearance_h,min_lateral_clearance_h,top_clearance_h; boundary_protocol:boundary_evidence_gate_draft; boundary_protocol:boundary_evidence_class_todo: one of official_aij_documentation, wind_tunnel_protocol_matched, empty_tunnel_boundary_preservation, precursor_boundary, recycling_boundary, validated_boundary_model_unsupported; boundary_protocol:unsupported_boundary_condition_fields:inlet_boundary,outlet_boundary,lateral_boundary,top_boundary,ground_wall_treatment,roughness_treatment,floor_roughness_source,blockage_source,fetch_clearance_source,outlet_reflection_check,side_top_boundary_check; boundary_protocol:boundary_evidence_files_missing; boundary_protocol:upstream_clearance_h_missing; boundary_protocol:downstream_clearance_h_missing; boundary_protocol:min_lateral_clearance_h_missing; boundary_protocol:top_clearance_h_missing; coordinate_probe_protocol:coordinate_protocol_missing; coordinate_probe_protocol:coordinate_axis_x_not_declared_streamwise_downstream; coordinate_probe_protocol:coordinate_axis_z_not_declared_vertical; coordinate_probe_protocol:velocity_component_U_not_mapped_to_fluidx3d_u.x; coordinate_probe_protocol:normalization_output_ratio_Ux_over_Uref_missing; coordinate_probe_protocol:case_label_missing; coordinate_probe_protocol:wind_direction_label_missing; coordinate_probe_protocol:wind_vector_mismatch:!=0.0,-1.0,0.0; coordinate_probe_protocol:uref_mismatch:None!=3.928296; coordinate_probe_protocol:probe_projection_fields_missing:Formula,SamplingMethod,ProbeVolumeRadiusCells,ProbeZOffsetM,ProbeCellCenterCoordinates; coordinate_probe_protocol:probe_sampling_method_missing_or_unknown; validation_protocol:gate_not_pass:diagnostic_only; native_runner:gate_not_pass:diagnostic_only; native_preconditions:source_missing_turbulent_length_scale_evidence; native_preconditions:source_has_measured_diagonal_rms_but_missing_offdiagonal_or_precursor_tensor; native_preconditions:source_missing_runtime_inlet_diagnostics_csv_for_u_k_rms_preservation; step_failed:audit_inlet_source:2; step_failed:audit_boundary_source:2; step_failed:audit_coordinate_probe_protocol:2; step_failed:audit_boundary_protocol:2; step_failed:build_inlet_reynolds_stress_evidence:2; step_failed:run_native_fluidx3d_case_preflight:2; step_failed:audit_native_preconditions:2)
  - paper_grade_inlet_source_gate:fail (source_missing_turbulent_length_scale_evidence; source_has_measured_diagonal_rms_but_missing_offdiagonal_or_precursor_tensor; source_missing_runtime_inlet_diagnostics_csv_for_u_k_rms_preservation)
  - inlet_reynolds_stress_evidence.json:paper_grade_gate:fail:measured_tensor (stress_csv_no_valid_full_tensor_rows; measured_stress_tensor_requires_at_least_two_valid_heights; stress_csv_sha256_missing_in_metadata; stress_csv_evidence_quality_not_paper_grade:missing)
  - inlet_reynolds_stress_evidence.json:gate:fail:measured_tensor (stress_csv_no_valid_full_tensor_rows; measured_stress_tensor_requires_at_least_two_valid_heights; stress_csv_sha256_missing_in_metadata; stress_csv_evidence_quality_not_paper_grade:missing)
  - paper_grade_boundary_source_gate:fail (boundary_source_not_wind_tunnel_equivalent; boundary_source_fidelity_class_not_paper_grade:partial_type_e_boundary_source; boundary_source_missing_advanced_code_evidence; boundary_source_simplified_type_e_or_solid_only; ground_and_buildings_no_slip_without_rough_wall_or_precursor; outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary; missing_non_reflecting_or_validated_outlet_state; missing_side_top_boundary_pair_mapping; missing_rough_wall_or_wall_function_action; missing_precursor_or_recycling_development_field)
