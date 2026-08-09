# CityLBM Software Feedback Matrix

Generated: 2026-08-09T11:14:50.722468+00:00

## Verdict

- Matrix passed: True
- Feedback rows: 12
- All source paths exist: True
- No forbidden default promotion: True
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False

## Decision Counts

- application_workflow_policy: 1
- blocked_default_accuracy_upgrade: 1
- blocked_followup_run: 1
- default_quality_gate: 1
- diagnostic_switch: 2
- formal_protocol_default: 1
- paper_figure_output: 1
- paper_interpretation_layer: 1
- paper_traceability_output: 1
- software_traceability_output: 2

## Feedback Rows

| id | experiment | decision | status | default? | finding |
|---|---|---|---|---:|---|
| `SF001` | Experiment 1 / AIJ Case A | default_quality_gate | implemented_as_release_gate_requirement | True | Case A smoke regression guards the Rhino/GH -> FluidX3D -> VTK workflow but is not accuracy validation. |
| `SF002` | Experiment 2 / AIJ Case E | blocked_default_accuracy_upgrade | formal_release_blocked | False | Official z=2 m validation remains negative: MAE=21.111408125 pp, R2=-2.006330362229977, Pearson=0.11575649438573923. |
| `SF003` | Experiment 2 / AIJ Case E | formal_protocol_default | implemented | True | The formal Case E protocol must remain z=2 m, 80 ac+N probes, and raw_trilinear sampling. |
| `SF004` | Experiment 2 / AIJ Case E | diagnostic_switch | implemented_default_off | False | Diagnostic nu_lbm sensitivity is useful for investigation but has not produced a formal official z=2 m pass. |
| `SF005` | Experiment 2 / AIJ Case E | diagnostic_switch | implemented_default_off | False | Vertical-origin and probe sampling diagnostics expose near-wall/protocol sensitivity but remain non-formal. |
| `SF006` | Experiment 2 / AIJ Case E | blocked_followup_run | ready_for_next_official_run | False | The next official Case E run is blocked by runtime and load-identity gates. |
| `SF007` | Experiment 3 / TUM2TWIN digital-twin application | application_workflow_policy | paper_ready_workflow_guidance | True | TUM2TWIN layers are separated into visual reference, semantic/collision geometry and CFD/LBM simulation inputs. |
| `SF008` | Experiment 3 / TUM2TWIN digital-twin application | paper_interpretation_layer | paper_ready_with_boundary | False | Basic morphology variables are interpretable screening descriptors; sector enclosure ranks above single-building footprint/elongation. |
| `SF009` | CityLBM traceability layer | software_traceability_output | implemented | True | Run Simulation exposes the generated citylbm_run_manifest.json path as a Grasshopper output for direct reviewer tracing. |
| `SF010` | Experiment 2 / AIJ Case E paper-readiness layer | paper_traceability_output | implemented | True | Run manifests and manuscript result rows now record allowed paper uses and forbidden accuracy claims. |
| `SF011` | Experiment 2 / AIJ Case E paper-figure layer | paper_figure_output | implemented | True | The manuscript result table is exported as an editable SVG/PNG/source-CSV figure bundle with QA checks. |
| `SF012` | Experiment 2 / AIJ Case E manifest gate contract | software_traceability_output | implemented | True | Generated run manifests now encode the formal v0.4.0 accuracy-gate contract and keep manifest-only accuracy claims blocked. |

## Paper Boundary

| id | paper use | limitations |
|---|---|---|
| `SF001` | Use as workflow non-regression evidence. | Do not use as wind-field accuracy validation. |
| `SF002` | Use as negative validation and motivation for limitations. | Cannot claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0. |
| `SF003` | Use as method/protocol policy. | Protocol correctness alone is not accuracy evidence. |
| `SF004` | Use as sensitivity diagnostic evidence. | Do not promote tuned nu_lbm as a default accuracy model. |
| `SF005` | Use for near-wall/probe-protocol limitations. | Do not report z_plus_half, vertical_valid_above, or z-offset results as official validation. |
| `SF006` | Use to explain why no new official long run is reported in this rc. | Operational readiness evidence only; not solver-output evidence. |
| `SF007` | Use as CityLBM-compatible digital-twin workflow evidence. | Does not prove Case E benchmark accuracy or CityLBM-GH end-to-end execution for Experiment 3. |
| `SF008` | Use as design-screening interpretation evidence. | Sample-internal screening only; no field validation or annual comfort compliance. |
| `SF009` | Use as software traceability evidence for run manifests and protocol metadata. | Traceability output only; does not prove Rhino loaded the new GHA or improve official z=2 m accuracy. |
| `SF010` | Use to move Case E results into manuscript tables without overstating formal accuracy. | Paper-readiness metadata does not change the official z=2 m metric or permit formal v0.4.0. |
| `SF011` | Use as a paper figure for negative validation and limitations only. | Figure output does not add CFD results, improve official z=2 m metrics, or justify formal accuracy claims. |
| `SF012` | Use as software traceability evidence that each generated case records the formal release-gate contract. | Manifest-gate metadata does not add solver output, improve official z=2 m metrics, or permit formal v0.4.0. |

## Boundary

This matrix converts audited experiment findings into software policy, diagnostic switch, and blocker decisions. It does not add CFD results or upgrade the official Case E metric.
