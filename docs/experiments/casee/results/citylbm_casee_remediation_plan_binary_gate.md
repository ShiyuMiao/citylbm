# CityLBM Case E Remediation Plan Binary Gate

Generated: 2026-08-13T14:13:58.741049+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_packaged_casee_remediation_plan_component`
- Formal accuracy claim supported: False
- Default setting allowed: False
- Tracked GHA: `CityLBM/bin/CityLBM.gha`
- Tracked GHA SHA256: `5dd119b4c86fcc2fb36ef5e1bbc8f09b3fc403ce42bcf52542588bca7b997af0`

## Checks

| check | passed |
|---|---:|
| `tracked_gha_exists` | True |
| `release_gha_exists` | True |
| `tracked_gha_matches_release_gha` | True |
| `source_component_gate_passed` | True |
| `all_required_markers_present_in_tracked_gha` | True |

## Required Binary Markers

| marker | present |
|---|---:|
| `CaseERemediationPlanComponent` | True |
| `Case E Remediation Plan` | True |
| `Blockers` | True |
| `Required Actions` | True |
| `Verification` | True |
| `Pass Conditions` | True |
| `Forbidden Claims` | True |
| `Next Experiments` | True |
| `B001 official_z2m_metric_gate` | True |
| `B002 rhino_new_gha_load` | True |
| `B003 gpu_runtime` | True |
| `B004 vs_cpp_build_tools` | True |
| `B005 dx1_high_resolution_run` | True |
| `casee_audit.py --release-target v0.4.0` | True |
| `Do not claim predictive accuracy` | True |
| `Do not claim mesh independence` | True |
| `Do not claim LES improvement` | True |
| `Do not claim formal v0.4.0 release readiness` | True |
| `casee_wall_model_followup` | True |
| `casee_inlet_turbulence_followup` | True |
| `casee_dx1_feasibility_or_run` | True |
| `3F46B886-F94E-492D-9D4F-FA6F170BF1D2` | True |

## Boundary

This gate checks that the packaged GHA contains the Case E Remediation Plan component strings. It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0.
