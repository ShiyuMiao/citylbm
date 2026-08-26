# Native FluidX3D Flow-Through Gate Update

Date: 2026-08-26

## Purpose

The native FluidX3D precondition chain now rejects runs that are too short for the flow to traverse the computational domain. This prevents short diagnostic runs from being interpreted as paper-grade AIJ validation evidence only because they produced VTK files.

## Implemented Gate

- Runner: `scripts/run_native_fluidx3d_case.py`
- Audit: `scripts/audit_native_preconditions.py`
- New manifest field: `FlowThroughTimeGate`
- Default paper-grade threshold: `--min-flow-throughs 3.0`

The gate estimates:

- dominant flow axis from `WindDirectionUnitVector`
- domain length in lattice cells from `defines.hpp`
- reference lattice velocity from case metadata, preferring `ReferenceWindSpeedMps * VelocityScaleMpsToLbm`
- one flow-through step count as `ceil(domain_length_cells / reference_velocity_lbm)`
- minimum planned steps as `ceil(one_flowthrough_steps * min_flow_throughs)`

## Case A Diagnostic Check

Evidence type: `preexisting_artifact` plus newly generated audit metadata.

Input run:

- `validation_runs/casea_full_af_native_300_150_W_v143_20260826`
- planned steps: `300`
- save interval: `150`
- existing VTK frames: `2`

New flow-through audit:

- output manifest: `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/native_fluidx3d_baseline_manifest_flowthrough_preflight.json`
- output precondition audit: `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/native_preconditions_audit_flowthrough_preflight.json`
- grid dimensions: `547, 280, 160`
- dominant axis: `x`
- domain length: `547` cells
- reference velocity: `0.06652347800325878` LBM units
- estimated one flow-through: `8223` steps
- required minimum for 3 flow-throughs: `24669` steps
- planned flow-through count: `0.036483035388544326`
- gate: `diagnostic_only`
- reason: `planned_time_steps_300_below_minimum_flowthrough_steps_24669`

## Current Reliability Status

This change does not improve the numerical result by itself. It improves protocol reliability by blocking a false paper-grade interpretation.

## Auto Inlet Source Audit

The native runner now auto-generates an inlet source audit when `--run` is requested and `--inlet-source-audit` is not supplied. It audits the exact case `setup.cpp`, `defines.hpp`, and `case_metadata.json` before allowing a solver run. This closes a workflow gap where a run could be blocked or misclassified simply because the source audit sidecar was not passed manually.

New manifest field:

- `AutoInletSourceAudit`

Case A pre-run check generated:

- `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/native_fluidx3d_baseline_manifest_auto_inlet_preflight.json`
- `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/inlet_source_audit_auto.json`

Result:

- auto audit generated: `true`
- auto audit gate: `pass`
- inlet source class: `synthetic_eddy_distribution_consistent`
- fidelity class: `distribution_consistent_synthetic_eddy`
- paper use gate still: `fail`

Interpretation: current Case A source-level inlet implementation can pass the inlet source audit, but the validation chain remains non-paper-grade until runtime U/k/correlation audits, time averaging, flow-through time, boundary-equivalence, and coordinate/probe protocol gates pass on the same run window.

## Auto Boundary And Coordinate Audits

The native runner now also auto-generates source/protocol audits for two other paper-grade blockers when `--run` is requested and the sidecar audit paths are not supplied manually.

New manifest fields:

- `AutoBoundarySourceAudit`
- `AutoCoordinateProbeProtocolAudit`

Case A pre-run check generated:

- `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/native_fluidx3d_baseline_manifest_auto_protocol_preflight.json`
- `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/boundary_source_audit_auto.json`
- `validation_runs/casea_full_af_native_300_150_W_v143_20260826/validation_chain_streamwise_velocity_2frames/coordinate_probe_protocol_audit_auto.json`

Result:

- auto inlet audit generated: `true`, gate: `pass`
- auto boundary audit generated: `true`, gate: `diagnostic_only`
- auto coordinate/probe audit generated: `true`, gate: `pass`
- runner gate: `diagnostic_only`
- paper use gate: `fail`

Boundary blockers from source audit:

- `paper_grade_boundary_source_gate_not_pass:fail`
- `boundary_source_not_wind_tunnel_equivalent`
- `boundary_source_fidelity_class_not_paper_grade:advanced_boundary_incomplete`
- `boundary_source_missing_advanced_code_evidence`
- `outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary`
- `boundary_method_named_without_concrete_state_or_field_evidence`
- `missing_non_reflecting_or_validated_outlet_state`
- `missing_side_top_boundary_pair_mapping`
- `missing_precursor_or_recycling_development_field`

Interpretation: the current Case A package is no longer blocked by missing sidecar audit files for boundary or coordinate checks. It is blocked by substantive boundary physics/protocol evidence, missing official CSV binding in the run command, insufficient flow-through/time averaging, and missing runtime inlet U/k/correlation evidence.

The current Case A diagnostic chain remains not paper-grade because:

- runtime `k` preservation and inlet correlation gates remain unproven on the same long run window
- boundary-equivalence evidence is still incomplete and is now the strongest source-level blocker
- the time window is too short, now including explicit flow-through insufficiency
- official RS/AF CSV binding, component normalization, and probe projection must still be proven for the final metric-producing run

Next valid optimization step is a native FluidX3D rerun with at least the computed flow-through threshold, plus the existing strict inlet, boundary, runtime averaging, and probe-audit gates.
