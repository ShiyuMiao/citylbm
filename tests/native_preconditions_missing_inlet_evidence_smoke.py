#!/usr/bin/env python3
"""Smoke-test that missing inlet profile/correlation evidence fails traceability."""

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
    with tempfile.TemporaryDirectory(prefix="citylbm_missing_inlet_evidence_") as tmp:
        root = Path(tmp)
        report = root / "native_preconditions_audit.json"
        (root / "case_metadata.json").write_text(
            json.dumps(
                {
                    "ReconstructInletStressDdf": {"Enabled": True},
                    "SyntheticEddy": {"DeviceSemStressDdf": True},
                },
                indent=2,
            ),
            encoding="utf-8",
        )

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
        inlet_reasons = data.get("native_inlet_equivalence_gate_reasons", [])
        priorities = data.get("native_diagnostic_priority", [])

        require(data.get("native_preconditions_gate") == "fail", data)
        require(data.get("native_inlet_equivalence_gate") == "fail", data)
        require(data.get("inlet_source_setup_cpp_sha256_matches_current") is False, data)

        for expected in [
            "inlet_source_audit_missing",
            "inlet_source_setup_cpp_sha256_missing",
            "inlet_source_current_setup_cpp_missing",
            "inlet_profile_audit_missing",
            "inlet_correlation_audit_missing",
            "inlet_profile_runtime_source_time_steps_missing",
            "inlet_profile_source_time_steps_missing",
            "inlet_profile_runtime_source_vtk_hashes_missing",
            "inlet_profile_source_vtk_hashes_missing",
            "inlet_profile_runtime_source_step_hash_pairs_missing",
            "inlet_profile_source_step_hash_pairs_missing",
            "inlet_correlation_runtime_source_time_steps_missing",
            "inlet_correlation_source_time_steps_missing",
            "inlet_correlation_runtime_source_vtk_hashes_missing",
            "inlet_correlation_source_vtk_hashes_missing",
            "inlet_correlation_runtime_source_step_hash_pairs_missing",
            "inlet_correlation_source_step_hash_pairs_missing",
            "native_inlet_equivalence_gate_not_pass",
            "rejected_stress_ddf_diagnostic_route:ReconstructInletStressDdf",
            "rejected_stress_ddf_diagnostic_route:SyntheticEddy.DeviceSemStressDdf",
        ]:
            require(expected in gate_reasons, {"missing": expected, "reasons": gate_reasons})

        for expected in [
            "inlet_source_audit_missing",
            "inlet_source_setup_cpp_sha256_matches_current_not_true:False",
            "inlet_profile_audit_missing",
            "inlet_profile_source_time_steps_match_runtime_not_true:False",
            "inlet_profile_source_vtk_sha256_match_runtime_not_true:False",
            "inlet_profile_source_step_hash_pairs_match_runtime_not_true:False",
            "inlet_correlation_audit_missing",
            "inlet_correlation_source_time_steps_match_runtime_not_true:False",
            "inlet_correlation_source_vtk_sha256_match_runtime_not_true:False",
            "inlet_correlation_source_step_hash_pairs_match_runtime_not_true:False",
        ]:
            require(expected in inlet_reasons, {"missing": expected, "reasons": inlet_reasons})

        inlet_priority = [
            item for item in priorities if item.get("key") == "turbulent_inlet_method_and_u_k_preservation"
        ]
        require(inlet_priority, priorities)
        for expected in [
            "inlet_source_audit_missing",
            "inlet_profile_audit_missing",
            "inlet_correlation_audit_missing",
        ]:
            require(expected in inlet_priority[0].get("reasons", []), inlet_priority[0])

    print("native_preconditions_missing_inlet_evidence_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
