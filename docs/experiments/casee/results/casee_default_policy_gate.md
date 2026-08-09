# Case E Default Policy Gate

Generated: 2026-08-09T14:50:44.596024+00:00

## Verdict

- Default policy gate passed: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_default_policy_boundary`
- Formal v0.4.0 allowed: False

## Default Settings Allowed

- Official Case E formal validation uses z=2 m, 80 ac+N probes, and raw_trilinear sampling.
- Generic CityLBM viscosity remains the standard physical-viscosity mapping when nuLBM is 0.
- Case E preset metadata may set protocol constants and manifest/risk fields.
- Run manifests may record diagnostic availability and claim-boundary metadata.
- Run manifests may record the formal accuracy-gate contract for reviewer traceability.
- Run Simulation may expose claim-boundary text as a traceability output.

## Experimental Switches

- Diagnostic LBM Nu Override / nuLBM sensitivity control.
- Diagnostic Z Origin Offset / zOff vertical-origin sensitivity control.
- Diagnostic Wall Model / wallModel follow-up control.
- Diagnostic Roughness Length / z0Wall follow-up control.
- nearest_valid, fluid_weighted, vertical_valid_above, and z_plus_half probe sampling.
- Effective-ground, rough-wall, wall-model, voxelization, and inlet-turbulence follow-up settings until official z=2 m raw_trilinear improvement is proven.

## Checks

| check | passed | source | policy boundary |
|---|---:|---|---|
| `simulation_settings_formal_raw_trilinear` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Formal validation defaults to official z=2 m raw_trilinear sampling. |
| `simulation_settings_diag_modes_empty_by_default` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Generic simulations do not enable diagnostic probe modes by default. |
| `simulation_settings_nu_override_default_off` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | LBM viscosity override is default-off; standard physical-viscosity mapping remains default. |
| `simulation_settings_z_origin_offset_default_off` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Vertical-origin offset is default-off and cannot redefine official z=2 m. |
| `simulation_settings_wall_model_default_none` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Diagnostic wall model is default-off and cannot replace the existing wall treatment by default. |
| `simulation_settings_roughness_default_zero` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Diagnostic roughness length is default-off and cannot become a formal accuracy model without official z=2 m improvement. |
| `run_component_casee_preset_default_false` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Case E preset is explicit and opt-in in Grasshopper. |
| `run_component_nu_input_default_zero` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Diagnostic LBM Nu Override stays off unless the user supplies a positive value. |
| `run_component_zoff_input_default_zero` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Diagnostic Z Origin Offset stays off unless explicitly set. |
| `run_component_wall_model_input_default_none` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Diagnostic Wall Model stays at none unless explicitly changed. |
| `run_component_roughness_input_default_zero` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Diagnostic Roughness Length stays at zero unless explicitly changed. |
| `run_component_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Run Simulation exposes the formal accuracy claim boundary directly in Grasshopper. |
| `manifest_blocks_z_plus_half_formal` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Run manifests forbid diagnostic modes as formal official z=2 m substitutes. |
| `manifest_formal_accuracy_gate_contract` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Run manifests encode the formal v0.4.0 accuracy-gate contract and keep manifest-only claims blocked. |
| `manifest_blocks_wall_roughness_formal_defaults` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Run manifests forbid wall-model and roughness diagnostics from becoming default accuracy claims. |
| `native_generator_formal_output_raw` | True | `docs/experiments/casee/tools/generate_native_casee.py` | Native Case E probe CSV keeps predicted_velocity_ratio as the raw formal result. |
| `native_generator_diagnostic_modes_declared` | True | `docs/experiments/casee/tools/generate_native_casee.py` | Native diagnostic sampling modes are recorded as diagnostics. |
| `casee_preset_formal_default_raw` | True | `docs/experiments/casee/casee_preset.json` | Case E preset formal validation mode is raw_trilinear. |
| `casee_preset_diagnostic_only_complete` | True | `docs/experiments/casee/casee_preset.json` | Case E preset lists nearest_valid, fluid_weighted, vertical_valid_above, and z_plus_half as diagnostic-only. |
| `release_gate_formal_blocked` | True | `docs/experiments/casee/results/release_gate.json` | Formal v0.4.0 remains blocked while official z=2 m metrics fail. |
| `failure_atlas_limitations_ready` | True | `docs/experiments/casee/results/casee_failure_mode_atlas.json` | Failure-mode atlas supports limitations/software-feedback discussion only. |
| `readme_declares_diagnostics_nonformal` | True | `README.md` | Repository documentation states diagnostic offsets and sampling modes are not formal validation. |

## Boundary

This gate proves only that the software defaults and documentation do not promote diagnostic Case E settings into formal accuracy defaults. It does not add a solver run, improve the official z=2 m metric, or permit the formal v0.4.0 tag.
