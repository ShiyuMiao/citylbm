# Case E Paper Evidence Gate

Generated: 2026-08-01T14:01:51.245322+00:00

## Verdict

- Paper evidence gate passed: True
- Formal v0.4.0 release allowed: False
- Recommended tag: `v0.4.0-rc26`

## Official z=2 m Metric

- MAE: 21.111408125 pp
- R2: -2.006330362229977
- Pearson: 0.11575649438573923
- Negative validation status: True

## Claim Matrix

- Claims: 8
- Readiness counts: `{'paper_ready': 2, 'limitations_ready': 3, 'weaken_claim': 1, 'blocked': 2}`
- Blocked release claim present: True
- Negative validation claim present: True
- Recommended tag present: True
- No overstated paper-ready claims: True

## Draft Scan

- Checked files: 5
- Checked nonblank lines: 261
- Draft claim boundary passed: True

## Artifact Index

- Artifact index found: True
- Artifact count: 156
- Lightweight release assets: 124
- Required artifacts present: True
- Formal accuracy claim supported by index: False

## Rhino/GHA Load Gate

- Gate found: True
- Rhino loaded new GHA: False
- Claim readiness: `blocked_manual_rhino_load`
- Claim boundary safe: True

## Official Run Preflight

- Preflight found: True
- Official follow-up run allowed: False
- Formal release allowed: False
- Claim readiness: `blocked_official_followup_preflight`
- Claim boundary safe: True

## Environment Recovery Runbook

- Recovery runbook found: True
- Formal release allowed: False
- Claim readiness: `blocked_environment_recovery_runbook`
- Recovery steps: 7
- Claim boundary safe: True

## Failure-Mode Atlas

- Atlas found: True
- Failure modes: 6
- Claim readiness: `limitations_ready_failure_mode_atlas`
- Claim boundary safe: True

## Default Policy Gate

- Gate found: True
- Default policy gate passed: True
- Checks: 15
- Claim readiness: `paper_ready_default_policy_boundary`
- Claim boundary safe: True

## Cross-Experiment Paper Results Packet

- Packet found: True
- Packet passed: True
- Result rows: 14
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False
- Claim boundary safe: True

## Manifest Output Gate

- Gate found: True
- Gate passed: True
- Checks: 8
- Claim readiness: `paper_ready_manifest_traceability`
- Formal accuracy claim supported: False
- Claim boundary safe: True

## Software Feedback Matrix

- Matrix found: True
- Matrix passed: True
- Feedback rows: 9
- All source paths exist: True
- No forbidden default promotion: True
- Formal accuracy claim supported: False
- Formal v0.4.0 allowed: False
- Claim boundary safe: True

No forbidden success-claim violations were found outside negated or forbidden-claim sections.
