#!/usr/bin/env python3
"""Smoke-test that missing boundary evidence cannot pass native preconditions."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(REPO),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def require(condition: bool, data: object) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_missing_boundary_evidence_") as tmp:
        root = Path(tmp)
        report = root / "native_preconditions_audit.json"

        audit = run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_native_preconditions.py"),
                str(root),
                "--case",
                "ac",
                "--wind-direction-label",
                "N",
                "--u-ref",
                "3.928296",
                "--expected-compared-component",
                "abs_streamwise_ratio",
                "--average-last-n",
                "3",
                "--min-avg-frames",
                "3",
                "--min-avg-step-span",
                "2000",
                "--out",
                str(report),
            ]
        )

        require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
        data = json.loads(report.read_text(encoding="utf-8"))
        gate_reasons = data.get("native_preconditions_gate_reasons", [])
        boundary_reasons = data.get("native_boundary_equivalence_gate_reasons", [])
        priorities = data.get("native_diagnostic_priority", [])

        require(data.get("native_preconditions_gate") == "fail", data)
        require(data.get("native_boundary_equivalence_gate") == "fail", data)
        require(data.get("boundary_source_setup_cpp_sha256_matches_current") is False, data)

        for expected in [
            "boundary_source_audit_missing",
            "boundary_source_setup_cpp_sha256_missing",
            "boundary_source_current_setup_cpp_missing",
            "boundary_protocol_audit_missing",
            "boundary_runtime_audit_missing",
            "native_boundary_equivalence_gate_not_pass",
        ]:
            require(expected in gate_reasons, {"missing": expected, "reasons": gate_reasons})

        for expected in [
            "boundary_source_audit_missing",
            "boundary_source_setup_cpp_sha256_matches_current_not_true:False",
            "boundary_protocol_audit_missing",
            "boundary_runtime_audit_missing",
            "boundary_runtime_source_vtk_hash_count_0_below_minimum_3",
        ]:
            require(expected in boundary_reasons, {"missing": expected, "reasons": boundary_reasons})

        boundary_priority = [item for item in priorities if item.get("key") == "boundary_roughness_blockage"]
        require(boundary_priority, priorities)
        for expected in [
            "boundary_source_audit_missing",
            "boundary_protocol_audit_missing",
            "boundary_runtime_audit_missing",
        ]:
            require(expected in boundary_priority[0].get("reasons", []), boundary_priority[0])

    print("native_preconditions_missing_boundary_evidence_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
