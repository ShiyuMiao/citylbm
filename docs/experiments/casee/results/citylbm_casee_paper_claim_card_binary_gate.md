# CityLBM Case E Paper Claim Card Binary Gate

Generated: 2026-08-13T13:05:39.992888+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_packaged_casee_paper_claim_card_component`
- Formal accuracy claim supported: False
- Default setting allowed: False
- Tracked GHA: `CityLBM/bin/CityLBM.gha`
- Tracked GHA SHA256: `bc25b3f4d312a5a86ec0f0729c69a449891af728da0c3d942603fb701fd822b2`

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
| `CaseEPaperClaimCardComponent` | True |
| `Case E Paper Claim Card` | True |
| `Paper Ready Claims` | True |
| `Limitations` | True |
| `Forbidden Claims` | True |
| `Evidence Paths` | True |
| `negative-validation result` | True |
| `Do not claim predictive accuracy` | True |
| `Do not claim mesh independence` | True |
| `Do not claim LES improvement` | True |
| `Do not claim formal v0.4.0 release readiness` | True |
| `post-hoc affine calibration` | True |
| `casee_paper_evidence_gate.json` | True |
| `citylbm_software_feedback_matrix.json` | True |
| `BA36730E-EEE4-4DB6-A360-61F889517DF1` | True |

## Boundary

This gate checks that the packaged GHA contains the Case E Paper Claim Card component strings. It is software packaging evidence only; it does not prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0.
