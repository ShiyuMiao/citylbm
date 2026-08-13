# CityLBM Case E Accuracy Action Plan Binary Gate

Generated: 2026-08-13T13:55:01.165696+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_packaged_casee_accuracy_action_plan_component`
- Formal accuracy claim supported: False
- Default setting allowed: False
- Tracked GHA: `CityLBM/bin/CityLBM.gha`
- Tracked GHA SHA256: `bcb9670a5a5060187960a42fa3e1eb33e01107c89bfe39e802db066c48925c1a`

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
| `CaseEAccuracyActionPlanComponent` | True |
| `Case E Accuracy Action Plan` | True |
| `MAE Gap pp` | True |
| `R2 Gap` | True |
| `Next Actions` | True |
| `default_setting_allowed: false` | True |
| `predictive accuracy` | True |
| `mesh independence` | True |
| `LES improvement` | True |
| `formal v0.4.0` | True |
| `post-hoc affine` | True |
| `A001` | True |
| `A004` | True |
| `A005` | True |
| `A006` | True |
| `A008` | True |
| `862C4BA3-B4EC-4E33-88CA-0F7345708B68` | True |

## Boundary

This gate checks that the packaged GHA contains the Case E accuracy action-plan component strings. It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0.
