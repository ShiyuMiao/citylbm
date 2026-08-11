# CityLBM Manifest Schema Gate

Generated: 2026-08-11T01:39:36.732089+00:00

## Verdict

- Manifest schema gate passed: True
- Evidence type: `newly_run`
- Claim readiness: `paper_ready_manifest_schema_boundary`
- Formal accuracy claim supported: False
- Contract version: `casee_manifest_contract_v2`

## Checks

| check | passed | schema area | source |
|---|---:|---|---|
| `manifest_writer_emits_named_file` | True | `file_identity` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `grasshopper_exposes_manifest_and_claim_gate` | True | `ui_traceability` | `CityLBM/src/Components/Simulation/RunSimulationComponent.cs` |
| `top_level_manifest_sections_present` | True | `top_level_sections` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `official_casee_contract_fields_present` | True | `formal_casee_contract` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `diagnostic_substitutes_are_blocked` | True | `diagnostic_boundary` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `wall_roughness_residual_default_safe_fields_present` | True | `wall_roughness_residual_boundary` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `probe_protocol_risk_fields_present` | True | `probe_protocol_risk` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `paper_forbidden_claims_present` | True | `paper_claim_boundary` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `publication_readiness_contract_present` | True | `publication_readiness_contract` | `CityLBM/src/Core/FluidX3DInterface.cs` |
| `default_policy_gate_passed` | True | `upstream_gate` | `docs/experiments/casee/results/casee_default_policy_gate.json` |
| `manifest_output_gate_passed` | True | `upstream_gate` | `docs/experiments/casee/results/citylbm_manifest_output_gate.json` |
| `formal_release_still_blocked_by_metrics` | True | `release_boundary` | `docs/experiments/casee/results/release_gate.json` |

## Boundary

This gate verifies the static schema and claim contract for generated CityLBM run manifests. It is paper-ready traceability evidence, not CFD solver-output evidence, and it cannot support a formal accuracy claim.
