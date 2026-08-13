# CityLBM Manifest Output Gate

Generated: 2026-08-13T10:43:52.398227+00:00

## Verdict

- Manifest output gate passed: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_manifest_traceability`
- Formal accuracy claim supported: False

## Checks

| check | passed | source | paper use |
|---|---:|---|---|
| `run_component_has_manifest_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Grasshopper exposes the generated run manifest path. |
| `run_component_has_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Grasshopper exposes the formal accuracy claim boundary beside run status. |
| `run_component_has_publication_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Grasshopper exposes the manuscript/publication-readiness boundary beside run status. |
| `manifest_path_helper_exists` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to trace the component output to the generated manifest filename. |
| `claim_gate_helper_exists` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show the component emits an explicit no-overclaim boundary for Case E runs. |
| `publication_gate_helper_exists` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show the component emits explicit manuscript-readiness dependencies for Case E runs. |
| `mode0_sets_manifest_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Generate Only mode returns the manifest path. |
| `mode0_sets_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Generate Only mode returns the claim-gate boundary. |
| `mode0_sets_publication_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show Generate Only mode returns the publication-readiness boundary. |
| `mode1_sets_manifest_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show full-auto mode returns the manifest path. |
| `mode1_sets_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show full-auto mode returns the claim-gate boundary. |
| `mode1_sets_publication_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show full-auto mode returns the publication-readiness boundary. |
| `mode2_sets_manifest_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show deploy-only mode returns the generated manifest path. |
| `mode2_sets_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show deploy-only mode returns the claim-gate boundary. |
| `mode2_sets_publication_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show deploy-only mode returns the publication-readiness boundary. |
| `async_sets_manifest_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show background mode returns the manifest path after completion. |
| `async_sets_claim_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show background mode returns the claim-gate boundary after completion. |
| `async_sets_publication_gate_output` | True | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` | Use to show background mode returns the publication-readiness boundary after completion. |
| `fluidx_writes_run_manifest` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show the exposed path points to a file written by the solver interface. |
| `manifest_contains_claim_boundary` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show the manifest records formal protocol and diagnostic boundaries. |
| `manifest_contains_wall_roughness_residual_followup_fields` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show run manifests trace wall/roughness/inlet/residual-target follow-up switches without promoting solver defaults. |
| `manifest_contains_paper_readiness_boundary` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show the manifest records paper-use and forbidden-claim boundaries. |
| `manifest_contains_publication_readiness_contract` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show the generated manifest carries reviewer-facing publication-readiness dependencies without claiming accuracy from the manifest alone. |
| `manifest_contains_formal_accuracy_gate_contract` | True | `CityLBM/src/Core/FluidX3DInterface.cs` | Use to show each generated run manifest records the formal v0.4.0 accuracy-gate contract. |

## Boundary

This gate verifies software traceability only: Run Simulation exposes the generated citylbm_run_manifest.json path, exposes the claim-gate and publication-gate boundaries in Grasshopper, and records claim-boundary and formal accuracy-gate fields. It does not validate CFD accuracy or Rhino loading of the new GHA.
