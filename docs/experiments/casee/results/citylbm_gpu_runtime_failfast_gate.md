# CityLBM GPU Runtime Fail-Fast Gate

Generated: 2026-08-13T10:43:34.464553+00:00

## Verdict

- Gate passed: True
- GPU runtime ready: False
- GPU lost detected: True
- Long FluidX3D run allowed: False
- Claim readiness: `blocked_gpu_runtime_failfast`

## nvidia-smi

- Return code: 15
- Message: `GPU is lost`

## Boundary

GPU runtime fail-fast evidence only. This gate runs nvidia-smi and records whether long FluidX3D scheduling must be blocked; it does not run FluidX3D, create solver output, improve official z=2 m metrics, recover the GPU, or permit formal v0.4.0.
