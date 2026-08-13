# CityLBM Case E Post-run Audit Binary Gate

Generated: 2026-08-13T11:21:05.562605+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_packaged_casee_postrun_audit_component`
- Tracked GHA: `CityLBM/bin/CityLBM.gha`
- Tracked GHA SHA256: `90e2a84115958130bd3adb63c8c13f60b3df12fcfd30d54e633b44900e47fc48`

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
| `CaseEPostRunAuditComponent` | True |
| `Case E Post-run Audit` | True |
| `Audit Command` | True |
| `Ready For Official Audit` | True |
| `Formal Result Allowed Now` | True |
| `Candidate SHA256` | True |
| `raw_trilinear` | True |
| `casee_audit.py` | True |
| `does not permit formal v0.4.0` | True |
| `19B94D68-EB71-41C0-B4AB-35DAFECE4079` | True |

## Boundary

This gate checks that the packaged GHA contains the Case E post-run audit component strings. It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, update official metrics, or permit formal v0.4.0.
