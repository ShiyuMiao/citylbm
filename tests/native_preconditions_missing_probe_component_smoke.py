#!/usr/bin/env python3
"""Smoke-test that missing probe/component/official evidence fails native audits."""

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
    with tempfile.TemporaryDirectory(prefix="citylbm_missing_probe_component_") as tmp:
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
        equivalence_reasons = data.get("native_probe_component_equivalence_gate_reasons", [])
        hash_reasons = data.get("component_sensitivity_hash_traceability_gate_reasons", [])
        priorities = data.get("native_diagnostic_priority", [])

        require(data.get("native_preconditions_gate") == "fail", data)
        require(data.get("native_probe_component_equivalence_gate") == "fail", data)
        require(data.get("component_sensitivity_hash_traceability_gate") == "fail", data)
        require(data.get("probe_component_fidelity_class") == "missing_probe_or_official_evidence", data)

        for expected in [
            "probe_audit_missing_or_empty",
            "component_sensitivity_audit_missing",
            "component_source_time_steps_missing",
            "component_source_sha256_missing",
            "component_source_step_hash_pairs_missing",
            "probe_audit_sha256_missing",
            "official_measurement_sha256_missing",
            "component_sensitivity_probe_audit_sha256_missing",
            "component_sensitivity_official_sha256_missing",
        ]:
            require(expected in equivalence_reasons, {"missing": expected, "reasons": equivalence_reasons})

        for expected in [
            "component_sensitivity_audit_missing",
            "probe_audit_sha256_missing",
            "official_measurement_sha256_missing",
        ]:
            require(expected in hash_reasons, {"missing": expected, "reasons": hash_reasons})

        require("native_probe_component_equivalence_gate_not_pass" in gate_reasons, data)
        coordinate_priority = [
            item for item in priorities
            if item.get("key") == "coordinate_component_normalization"
        ]
        require(coordinate_priority, priorities)
        for expected in [
            "probe_audit_missing_or_empty",
            "component_sensitivity_audit_missing",
            "component_normalization_gate_not_pass",
            "normalization_scale_gate_not_pass",
        ]:
            require(expected in coordinate_priority[0].get("reasons", []), coordinate_priority[0])

    print("native_preconditions_missing_probe_component_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
