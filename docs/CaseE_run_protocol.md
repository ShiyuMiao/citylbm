# AIJ Case E strict validation protocol

This document defines the strict rerun protocol for CityLBM v0.3.0. It is not a result file.

## Scope

- Case: AIJ Case E, construction-after condition `ac`
- Wind direction: `N`
- Software platform: Rhino 7 + Grasshopper + CityLBM v0.3.0
- Solver backend: FluidX3D through CityLBM generated `setup.cpp`

## Inputs

- Geometry: `BD_caseE.stl`
- Geometry scale: STL is `1:250`; scale by `250` before simulation or ensure generated STL is in full-scale meters.
- Inflow profile: `AF_caseE.csv`
- Required profile columns: `z(m), U(m/s), k(m2/s2)`
- CityLBM setting: `Wind Profile = 3` (`CustomTable`)
- Wind vector: `(0,-1,0)` for N wind interpreted as north-to-south flow
- Uref metadata: `3.928296 m/s @ 15.9 m`
- Measurement file: `RS_caseE.csv`
- Validation subset: `case=ac`, `direction=N`, pedestrian height `z=2 m`

## Simulation settings

- First smoke run: `dx=5 m`, `steps=2000-5000`, `save interval=500 or 1000`
- Formal validation: `dx=2-3 m`, `steps>=10000`, save enough final VTK frames for time averaging
- Use LES consistently and record `Cs`, viscosity, grid dimensions and GPU model.
- Archive LBM stability evidence for the exact native/CityLBM run: target maximum lattice velocity, estimated maximum
  Mach number, `tau`, `nu_lbm`, physical viscosity, Reynolds number, velocity set, LES/subgrid model and solver-log
  stability warnings. The v0.3.0 machine gate fails paper-grade promotion unless the runtime metrics row records a
  passing stability gate such as `lbm_stability_gate=solver_log_no_stability_warnings` and
  `solver_stability_warnings=none`.
  In v0.3.0, generated cases compute `nu_lbm = nu_SI * velocity_scale_mps_to_lbm / dx` and do not clamp `tau` upward to
  0.55. If `tau` is too close to 0.5, treat that as a stability/protocol issue to solve with grid, velocity-scale,
  LES/subgrid and solver-log evidence, not as a value to hide in case generation.
- For AF files with `k(m2/s2)`, enable `Run Simulation / Synthetic Inlet` only when testing the experimental STG-lite inlet.
  Record `STG Scale`/synthetic scale, `STG Corr Cells`/correlation cells, `STG Update`/pattern-update interval, `STG Max Frac`/amplitude cap,
  `STG Length Source`/correlation-length evidence source, and the generated `case_metadata.json` fields
  `SyntheticTurbulentInletRequested`, `SyntheticTurbulentInletInjected`,
  `SyntheticTurbulentInletLengthScaleSource` and `SyntheticTurbulentInletLengthScaleGate`.
  Leave `STG Length Source` empty unless the selected correlation length is backed by archived AIJ/official,
  precursor/recycling, DFM/SEM or validated synthetic-eddy length-scale evidence.
- Do not compare a single early VTK frame as a final result.
- CityLBM v0.3.0 validation runs must use an explicit external FluidX3D source path in `Run Simulation / FX3D`.
  The legacy bundled v0.5.0 fallback is disabled for controlled validation because it is not the baseline.
  Mode 1/2/3 reject auto-detected paths for validation. The FX3D path must point to a deployable native source root
  containing `FluidX3D.sln`, `Makefile` or `CMakeLists.txt`, plus `src/setup.cpp`, `src/defines.hpp`, `src/lbm.hpp` and
  `src/lbm.cpp`. Mode 0 may still generate a case without FX3D for offline preparation, but that is not a run.

## Required checks before accepting a run

- Generated `setup.cpp` contains `profile_z_m[]`, `profile_z_lbm[]`, `profile_u_lbm[]`, `profile_k_m2s2[]`, `profile_k_lbm[]` and `profile_origin_z_m`.
- If STG-lite is enabled, generated `setup.cpp` also contains `syntheticTurbulentInlet`, `applySyntheticTurbulentInlet`,
  `citylbm_stg_*` constants and the divergence-reduced transverse spectral-mode projection.
- The generated `validation_protocol_audit` must explicitly record `native_fluidx3d_baseline`, `boundary_conditions`,
  `lbm_stability_scaling`, `wind_direction_sign`, `probe_projection`, `normalization_basis` and `systematic_bias_gate`.
  Treat these items as paper-blocking until their run evidence is archived.
- `domain_origin.json` exists in both case root and output directory.
- `case_metadata.json` exists in both case root and output directory.
  Archive `BoundaryProtocolAudit` from this file: inlet/outlet/lateral/top faces, clearances in meters and H units,
  approximate frontal/plan blockage ratios, blockage gate, boundary protocol gate, and the simplified `TYPE_E`/`TYPE_S`
  boundary-type record. The blockage ratios are axis-aligned diagnostics from model/domain bounds; verify them against
  the official AIJ wind-tunnel blockage definition before making paper-grade claims.
- Archive an explicit AIJ boundary evidence JSON and generate `boundary_protocol_audit.json`. The evidence JSON must
  include `aij_case`, `wind_direction`, `inlet_boundary`, `outlet_boundary`, `lateral_boundary`, `top_boundary`,
  `ground_wall_treatment`, `roughness_treatment`, `blockage_source`, `fetch_clearance_source` and
  `boundary_evidence_gate=pass`. Domain clearance alone is diagnostic and cannot pass the paper-grade boundary gate.
- `validation_protocol_audit.json` and `validation_protocol_audit.md` exist in both case root and output directory.
  Treat any `risk` or `fail` item as a blocker for paper-grade validation claims until resolved or explicitly justified.
- VTK files are newly generated for the current run directory, not copied from older experiments.
- The AF inlet profile must be verified from real post-spinup VTK frames before probe accuracy is interpreted. Run
  `scripts\audit_inlet_profile_from_vtk.py` on the output VTK sequence, compare against `AF_caseE.csv`, and archive the
  resulting `inlet_profile_audit.json` and `.csv`. This audit checks that `Wind Profile=3` actually preserved both
  `U(z)` and the AF third-column `k(m2/s2)` statistics at the selected inlet/empty-tunnel plane.
  It also records all available VTK steps, selected source steps, `selected_last_window`,
  `source_steps_strictly_increasing`, `source_step_spacing_uniform`, `time_averaging_gate_reasons`,
  `negative_streamwise_fraction`, and `inlet_streamwise_direction_gate`. Short, non-final or irregular inlet windows
  fail before probe accuracy is interpreted, and a high reverse-streamwise fraction flags wind-vector or velocity
  component sign errors.
- The turbulent-inlet correlation must be verified from the same real final-window VTK frames with
  `scripts\audit_inlet_correlation_from_vtk.py`. This audit records streamwise fluctuation variance, temporal lag-1
  correlation and adjacent spatial correlation. It is required because preserving AF `k` magnitude alone does not prove
  a digital-filter, SEM, precursor/recycling or otherwise correlated turbulent inlet.
- The STG length-scale gate is not passed by choosing a convenient number of lattice cells. It passes only when
  `STG Length Source`/`SyntheticTurbulentInletLengthScaleSource` contains an archived evidence tag such as
  `aij_length_scale_verified`, `official_length_scale_verified`, `precursor_length_scale`,
  `digital_filter_length_scale`, `synthetic_eddy_length_scale`, `sem_length_scale`, `dfm_length_scale` or
  `validated_length_scale_model`; otherwise the run remains diagnostic.
- Post-processing reads the final averaged velocity field, not an initial transient.
  In `Read VTK`, set `Average Last N > 0` and archive the `Averaging Audit` JSON output.
  This JSON records the actual averaged frame count, source time steps, mean speed, mean/max pointwise speed standard
  deviation, mean/max relative fluctuation, the available VTK frame count, whether the selected frames are the last
  available window, and whether source time steps are strictly increasing and uniformly spaced.
  A short window with large residual fluctuation is diagnostic only and must not be treated as paper-grade time averaging.
  For native FluidX3D runs outside Grasshopper, run `scripts\audit_native_run.py` on the run directory and pass its JSON
  to `validation_metrics_from_probe_audit.py --read-vtk-audit`. This records VTK frame hashes, selected final time steps,
  solver-log stability warnings and LBM stability fields in the same schema used by the `Read VTK` audit output.
  When full-field statistics are not supplied manually, the script deterministically samples up to 20,000 points from
  the selected final VTK frames and computes `mean_speed_stddev_ratio` and `max_speed_stddev_ratio` from the real
  velocity time series.
- Measurement interpolation uses the official `ac + N` points and records failed or out-of-domain probes.
- The probe audit table must contain official point number, original coordinate, interpolation distance,
  compared velocity component, compared value, wind-vector components, `wind_direction_valid`, `normalization_valid`,
  tolerance, out-of-tolerance flag and failure flag.
- In `Data Probe`, connect `Uref=3.928296`, `Wind Direction=(0,-1,0)`, `Probe IDs` from the official `RS_caseE.csv`
  point-number field, `Tolerance` from the run protocol, and `Compared Component`.
  Use `speed_ratio` when comparing with AIJ velocity-ratio magnitudes; use `streamwise_ratio` only if the validation
  table is explicitly defined as along-wind signed velocity. Archive the appended outputs `Speed Ratio`,
  `Streamwise Ratio`, `Nearest Distance`, `Audit CSV`, `Validation Status`, `Compared Value` and `Probe ID`.
  These outputs are diagnostic only: `Uref` is used for validation ratios and must not be used to replace `AF_caseE.csv`.
  The metrics builder records `compared_component_consistency_gate`, `compared_component_unique_values` and
  `official_coordinate_delta_count`; the machine gate fails if valid probes mix components or if coordinate deltas are
  not available for every valid official probe. Native FluidX3D reruns outside Grasshopper must generate the same audit
  schema with `scripts\probe_vtk_points.py`, filtered to `case=ac` and `Wind_direction=N`, before building metrics.
  Use structured-grid trilinear sampling for the velocity value; the nearest-node distance remains the coverage and
  tolerance evidence.
- A paired native FluidX3D baseline must use the same `setup.cpp` physics choices, grid, VTK averaging window and probe
  extraction before any CityLBM-vs-AIJ error is attributed to the Grasshopper integration layer.
- `case_metadata.json` must be archived with the run. It records the boundary-condition summary, expected VTK frame count,
  time-averaging requirement, and known protocol risks.
- `native_fluidx3d_baseline_manifest.json` and `.md` must be archived. This manifest lists the exact generated
  `setup.cpp`, `defines.hpp`, `buildings.stl`, metadata files, shared run settings and paired evidence required for a
  native FluidX3D baseline, including SHA256 hashes for the generated source/metadata files. Treat the manifest gate
  `required_before_paper_grade_accuracy_claim` as blocking until the native baseline and CityLBM-driven run are compared
  with the same VTK averaging and probe audit table.
  The manifest also records whether the FluidX3D source path was explicitly supplied and whether the original native
  source tree passed the required-file check. If `NativeFluidX3DPathExplicitlyProvided=false` or source validation fails,
  the run cannot be used as the native baseline for paper claims.
- Convert the `Data Probe` audit table and official `RS_caseE.csv` subset into a standard metrics row:

```powershell
python scripts\audit_inlet_profile_from_vtk.py <run_dir>\output --af-csv <official_data>\AF_caseE.csv --metadata <case_metadata.json> --wind-direction 0,-1,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_profile_audit.json --out-csv <run_dir>\inlet_profile_audit.csv

python scripts\audit_inlet_correlation_from_vtk.py <run_dir>\output --metadata <case_metadata.json> --wind-direction 0,-1,0 --plane-axis auto-inlet --average-last-n 10 --min-frames 10 --out-json <run_dir>\inlet_correlation_audit.json

python scripts\probe_vtk_points.py <run_dir>\output --official <official_data>\RS_caseE.csv --case ac --wind-direction-label N --wind-direction 0,-1,0 --u-ref 3.928296 --compared-component speed_ratio --interpolation trilinear --tolerance <probe_tolerance_m> --average-last-n 10 --out <probe_audit.csv>

python scripts\audit_component_sensitivity.py --probe-audit <probe_audit.csv> --official <RS_caseE.csv> --case ac --wind-direction N --selected-component speed_ratio --out-json <run_dir>\component_sensitivity_audit.json --out-csv <run_dir>\component_sensitivity_audit.csv

python scripts\validation_metrics_from_probe_audit.py --probe-audit <probe_audit.csv> --official <RS_caseE.csv> --metadata <case_metadata.json> --read-vtk-audit <read_vtk_averaging_audit.json> --inlet-profile-audit <run_dir>\inlet_profile_audit.json --inlet-correlation-audit <run_dir>\inlet_correlation_audit.json --component-sensitivity-audit <run_dir>\component_sensitivity_audit.json --case ac --wind-direction N --u-ref 3.928296 --z-ref 15.9 --out <validation_metrics.csv> --comparison-out <probe_comparison.csv>
```

Generate the boundary protocol audit before the final gate:

```powershell
python scripts\audit_boundary_protocol.py <run_dir> --metadata <case_metadata.json> --evidence <boundary_evidence_casee_ac_N.json> --out <run_dir>\boundary_protocol_audit.json
```

- For a native FluidX3D or CityLBM run package with newly generated VTK frames, produce the complete post-run evidence
  package with one command:

```powershell
python scripts\run_native_validation_chain.py <run_dir> --official <official_data>\RS_caseE.csv --af-csv <official_data>\AF_caseE.csv --metadata <case_metadata.json> --boundary-evidence <boundary_evidence_casee_ac_N.json> --solver-log <solver.log> --case ac --wind-direction-label N --wind-vector 0,-1,0 --u-ref 3.928296 --z-ref 15.9 --software citylbm --average-last-n 10 --min-avg-frames 10 --compared-component speed_ratio --interpolation trilinear --probe-tolerance <probe_tolerance_m> --dx <dx_m> --steps <steps> --save-interval <save_interval> --geometry-scale 250
```

  The command creates `validation_chain_manifest.json`, `native_run_audit.json`, `inlet_profile_audit.json/.csv`,
  `inlet_correlation_audit.json`, `boundary_protocol_audit.json`, `probe_audit.csv`,
  `component_sensitivity_audit.json/.csv`, `validation_metrics.csv`, `probe_comparison.csv` and
  `validation_gate_report.json` under `<run_dir>\validation_chain`. It does not start a CFD simulation and must not be
  used to imply that Case E was rerun unless the VTK frames in `<run_dir>` were newly produced by the current Rhino 7/
  Grasshopper/CityLBM experiment.

- Run the machine gate after postprocessing:

```powershell
python scripts\validation_gate.py <run_dir> --case CaseE --software citylbm --metrics <validation_metrics.csv> --probe-audit <probe_audit.csv> --expected-compared-component speed_ratio --expected-uref 3.928296 --expected-wind-vector 0,-1,0 --max-mean-speed-stddev-ratio 0.05 --max-point-speed-stddev-ratio 0.20 --out <run_dir>\validation_gate_report.json
```

  The gate must pass before Case E is described as paper-grade validation. A failed gate means the run remains
  diagnostic, even if Rhino/Grasshopper visualization and screenshots are complete.
  By default, the gate fails CityLBM's current velocity-field-only STG-lite inlet because it does not reconstruct
  FluidX3D distribution functions. The optional `--allow-velocity-only-inlet` flag is reserved for explicitly labelled
  diagnostic sensitivity runs after an empty-tunnel `U/k` preservation check; do not use it for SCI-grade Case E claims.

## Metrics to report

- Valid point count and failed point count
- MAE and RMSE for normalized speed ratio
- Bias and bias ratio
- R2
- Regression slope and intercept
- Maximum absolute error
- Best-fit scale to official measurements, scaled RMSE and `bias_diagnosis` to separate Uref/unit/component errors from
  boundary/inlet physics errors.
- Component/Uref sensitivity audit: selected compared component, best RMSE component, selected/best RMSE, best-fit
  normalization scale, scaled-improvement ratio and `component_normalization_gate`. A failing audit means speed-ratio
  versus streamwise-ratio selection or Uref/SI conversion must be fixed before interpreting physical-model error.
- Grid spacing, steps, averaging window and VTK frame list
- Mean speed, mean/max pointwise speed standard deviation and mean/max relative fluctuation from the averaged VTK field
- `time_averaging` gate must use the final available VTK window, contain at least 10 frames, have strictly increasing
  uniformly spaced source steps, and satisfy `mean_speed_stddev_ratio <= 0.05` and `max_speed_stddev_ratio <= 0.20`
  unless a stricter case-specific stationarity criterion is documented.
- Inlet/outlet/lateral/top boundary faces and upstream/downstream/lateral/top clearances in building-height units
- Domain size, maximum building height, approximate frontal blockage ratio, approximate plan blockage ratio and blockage gate
- `boundary_protocol_audit.json`, `boundary_evidence_gate` and `boundary_missing_evidence_fields`
- Mean probe distance and maximum probe distance
- Compared component consistency gate, unique compared components and official coordinate-delta coverage count
- Native FluidX3D baseline run id or archive path
- Empty-tunnel `U/k` preservation gate, `empty_tunnel_U_bias_ratio`, `empty_tunnel_k_bias_ratio`
- Inlet profile preservation audit: selected plane, source VTK steps, `inlet_profile_gate`, `inlet_u_profile_gate`,
  `inlet_k_profile_gate`, `inlet_u_mae_ratio`, `inlet_u_rmse_ratio`, `inlet_k_mae_ratio`, and
  `inlet_k_rmse_ratio`
- Inlet correlation audit: `inlet_correlation_gate`, temporal lag-1 absolute correlation, adjacent spatial correlation
  and streamwise fluctuation variance
- Native baseline gate and `validation_gate_report.json`
- Protocol gate from `validation_protocol_audit.json`
- Systematic bias flag and `bias_diagnosis`. If mean bias remains around `-0.20` to `-0.35` speed-ratio units, do not
  tune parameters first. If best-fit scaling removes much of the error, audit Uref, velocity-unit conversion, compared
  component and wind-direction sign. If scaled RMSE remains large, audit inlet turbulence, boundary treatment, roughness
  and probe projection.
- `validation_gate_report.json` `diagnostic_priority` ranks the next actions after a failed run. For SCI-grade Case E,
  do not skip lower-rank failures: coordinate/component/Uref/probe closure plus component/Uref sensitivity precedes time averaging; time averaging
  precedes inlet `U/k` preservation; inlet `U/k` preservation precedes turbulent-inlet method and length-scale claims;
  inlet correlation evidence precedes boundary/roughness/blockage evidence; boundary/roughness/blockage evidence
  precedes interpreting a remaining `-34 pp` style low bias as solver accuracy.

## Current v0.3.0 limitation

CityLBM v0.3.0 reads, converts and records `k(m2/s2)`. It also provides an optional experimental STG-lite inlet that converts isotropic `k` to bounded deterministic spectral velocity perturbations using `sigma=sqrt(2k/3)`, with inlet refresh controlled by `SyntheticTurbulenceUpdateInterval`. The synthetic spectral-mode amplitudes are projected normal to their wave vectors to reduce non-physical divergent inlet fluctuations, and the spectral normalization targets the component RMS implied by isotropic `k` rather than the lower former diagnostic amplitude. This is a software-level improvement over the former metadata-only `k` chain and the earlier sparse-eddy diagnostic pattern, but it is not a full digital-filter, precursor/recycling, or Reynolds-stress turbulent inflow because the AF table does not provide Reynolds-stress tensors, turbulent length scales or a precursor field. The inlet correlation audit is therefore a necessary precondition that checks real VTK fluctuation correlation, not a replacement for a validated digital-filter/SEM/precursor inlet. The v0.3.0 machine gate treats velocity-field-only STG-lite as non-paper-grade by default; it can only be explicitly allowed for diagnostic sensitivity analysis with `--allow-velocity-only-inlet`. Any paper claim must state whether the validation used metadata-only inflow, STG-lite diagnostic inflow, or a later distribution-consistent turbulent inlet.

The current boundary conditions are also a simplified FluidX3D `TYPE_E` setup: velocity-profile inlet, pressure/free-outflow outlet approximation, lateral/top `TYPE_E`, and no-slip ground/buildings. CityLBM v0.3.0 initializes all `TYPE_E` boundary velocities from the mean wind profile before uploading flags/velocity fields, so outlet/lateral/top boundaries no longer start from zero velocity after their early boundary-return path. This removes one plausible software-side damping source, but it does not make the boundary protocol identical to the AIJ wind tunnel. CityLBM v0.3.0 records domain clearance and approximate frontal/plan blockage ratios in `BoundaryProtocolAudit`, and `validation_gate.py` fails the boundary gate when approximate frontal blockage exceeds the diagnostic threshold. These fields help detect protocol-scale errors, but they remain screening diagnostics until compared with the AIJ wind-tunnel boundary setup or replaced by a stronger inlet/outlet treatment.
