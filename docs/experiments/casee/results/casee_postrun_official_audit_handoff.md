# Case E Post-run Official Audit Handoff

Generated: 2026-08-13T12:51:18.088418+00:00

## Verdict

- Gate passed: True
- Candidate supplied: False
- Candidate structurally admissible: False
- Ready to run official audit: False
- Formal result allowed now: False
- Claim readiness: `armed_no_candidate`

## Candidate

- Path: ``
- SHA256: ``
- Rows: 0
- Required columns present: False
- 80 official probe ids present: False

## Run Evidence

- Manifest: ``
- Protocol fields ok: False
- Steps ok: False
- Spinup ok: False
- Logs: 0
- Complete log found: False

## Official Audit Command

```powershell
python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0 --predicted <new_casee_probe_time_mean.csv>
```

## Boundary

This handoff validates whether a newly completed Case E probe CSV is ready for the official z=2 m raw_trilinear audit command. It does not run FluidX3D, does not replace release_gate.json unless the audit command is explicitly executed, does not promote diagnostic columns, and does not support formal v0.4.0 or predictive-accuracy claims by itself.
