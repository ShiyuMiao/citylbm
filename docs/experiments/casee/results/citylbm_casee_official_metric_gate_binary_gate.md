# CityLBM Case E Official Metric Gate Binary Gate

Generated: 2026-08-13T13:38:24.069230+00:00

## Verdict

- Gate passed: True
- Claim readiness: `paper_ready_packaged_casee_official_metric_gate_component`
- Formal accuracy claim supported: False
- Default setting allowed: False
- Tracked GHA: `CityLBM/bin/CityLBM.gha`
- Tracked GHA SHA256: `25ce377acae4ce5bfc6702998677439c49125308e25f5112eb17643806104cad`

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
| `CaseEOfficialMetricGateComponent` | True |
| `Case E Official Metric Gate` | True |
| `Metric Rows` | True |
| `Threshold Rows` | True |
| `Gate Checks` | True |
| `Forbidden Claims` | True |
| `MAE_pp=21.111408125` | True |
| `RMSE_pp=27.72103208243715` | True |
| `bias_pp=-16.409216` | True |
| `R2=-2.006330362229977` | True |
| `Pearson=0.11575649438573923` | True |
| `MAE threshold: < 15.0 pp` | True |
| `R2 threshold: > 0.0` | True |
| `Pearson threshold: > 0.0` | True |
| `official_z2m_metric_gate=` | True |
| `formal_release_allowed=false` | True |
| `Do not claim predictive accuracy` | True |
| `Do not claim research-grade wind-field accuracy` | True |
| `Do not claim mesh independence` | True |
| `Do not claim LES improvement` | True |
| `Do not claim formal v0.4.0 release readiness` | True |
| `E0A4B8D7-0269-4090-9F50-9125A84D43DF` | True |

## Boundary

This gate checks that the packaged GHA contains the Case E Official Metric Gate component strings. It is software packaging and metric-verdict evidence only; it does not prove Rhino loaded the plugin, run CFD, improve official z=2 m metrics, or permit formal v0.4.0.
