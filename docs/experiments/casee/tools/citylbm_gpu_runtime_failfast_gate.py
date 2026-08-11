#!/usr/bin/env python3
"""Fail-fast GPU runtime gate before scheduling long FluidX3D Case E runs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_gpu_runtime_failfast_gate.md"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(args: List[str], timeout: int = 20) -> Dict[str, Any]:
    exe = shutil.which(args[0]) if not Path(args[0]).exists() else args[0]
    if not exe:
        return {
            "command": " ".join(args),
            "found": False,
            "returncode": None,
            "stdout": "",
            "stderr": "not found",
        }
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": " ".join(args),
        "found": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    rows = [
        {
            "check": "nvidia_smi_found",
            "passed": payload["checks"]["nvidia_smi_found"],
            "value": payload["nvidia_smi"].get("command", ""),
            "boundary": "GPU runtime evidence only.",
        },
        {
            "check": "gpu_runtime_ready",
            "passed": payload["gpu_runtime_ready"],
            "value": payload["gpu_runtime_status"],
            "boundary": "False blocks new long FluidX3D runs.",
        },
        {
            "check": "gpu_lost_detected",
            "passed": payload["gpu_lost_detected"],
            "value": payload["gpu_lost_message"],
            "boundary": "Diagnostic blocker, not solver output.",
        },
        {
            "check": "long_fluidx3d_run_allowed",
            "passed": payload["long_fluidx3d_run_allowed"],
            "value": payload["claim_readiness"],
            "boundary": "Must be false while GPU runtime is blocked.",
        },
        {
            "check": "failfast_gate_passed",
            "passed": payload["gpu_runtime_failfast_gate_passed"],
            "value": "gate closed correctly" if payload["gpu_runtime_failfast_gate_passed"] else "gate failed",
            "boundary": payload["boundary"],
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed", "value", "boundary"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM GPU Runtime Fail-Fast Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['gpu_runtime_failfast_gate_passed']}",
        f"- GPU runtime ready: {payload['gpu_runtime_ready']}",
        f"- GPU lost detected: {payload['gpu_lost_detected']}",
        f"- Long FluidX3D run allowed: {payload['long_fluidx3d_run_allowed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        "",
        "## nvidia-smi",
        "",
        f"- Return code: {payload['nvidia_smi'].get('returncode')}",
        f"- Message: `{payload['gpu_lost_message'] or payload['nvidia_smi'].get('stderr') or payload['nvidia_smi'].get('stdout')}`",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-chain", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    parser.add_argument("--preflight", type=Path, default=RESULTS_DIR / "casee_official_run_preflight.json")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-csv", type=Path, default=OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()

    nvidia = run_cmd(["nvidia-smi"], timeout=20)
    text = f"{nvidia.get('stdout', '')}\n{nvidia.get('stderr', '')}"
    gpu_lost_detected = "GPU is lost" in text
    gpu_runtime_ready = bool(nvidia.get("returncode") == 0 and not gpu_lost_detected)
    build_chain = read_json(args.build_chain)
    preflight = read_json(args.preflight)
    build_gpu_status = str((build_chain.get("gpu_runtime") or {}).get("status", ""))
    preflight_blocked = "gpu_runtime" in (preflight.get("blocked_gates") or [])
    long_run_allowed = bool(gpu_runtime_ready and not preflight_blocked)
    expected_block = not gpu_runtime_ready
    boundary = (
        "GPU runtime fail-fast evidence only. This gate runs nvidia-smi and records whether long "
        "FluidX3D scheduling must be blocked; it does not run FluidX3D, create solver output, "
        "improve official z=2 m metrics, recover the GPU, or permit formal v0.4.0."
    )
    checks = {
        "nvidia_smi_found": bool(nvidia.get("found")),
        "gpu_runtime_status_consistent": (build_gpu_status in {"blocked", "ready", ""}),
        "gpu_lost_blocks_long_run": (not gpu_lost_detected) or (long_run_allowed is False),
        "blocked_preflight_consistent": (not expected_block) or preflight_blocked or preflight == {},
        "no_solver_run_attempted": True,
        "formal_accuracy_claim_not_supported": True,
        "boundary_safe": all(phrase in boundary for phrase in ["does not run FluidX3D", "improve official z=2 m metrics", "formal v0.4.0"]),
    }
    gate_passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "gpu_runtime_failfast_gate_passed": gate_passed,
        "gpu_runtime_ready": gpu_runtime_ready,
        "gpu_runtime_status": "ready" if gpu_runtime_ready else "blocked",
        "gpu_lost_detected": gpu_lost_detected,
        "gpu_lost_message": "GPU is lost" if gpu_lost_detected else "",
        "long_fluidx3d_run_allowed": long_run_allowed,
        "claim_readiness": "ready_for_gpu_backed_run" if long_run_allowed else "blocked_gpu_runtime_failfast",
        "checks": checks,
        "nvidia_smi": nvidia,
        "build_chain_gpu_status": build_gpu_status,
        "preflight_gpu_blocked": preflight_blocked,
        "formal_accuracy_claim_supported": False,
        "boundary": boundary,
    }
    args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(args.out_csv, payload)
    write_markdown(args.out_md, payload)
    print(
        json.dumps(
            {
                "gpu_runtime_failfast_gate_passed": gate_passed,
                "gpu_runtime_ready": gpu_runtime_ready,
                "long_fluidx3d_run_allowed": long_run_allowed,
                "out_json": str(args.out_json),
            },
            indent=2,
        )
    )
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
