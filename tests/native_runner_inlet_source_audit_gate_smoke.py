#!/usr/bin/env python3
"""Smoke-test native runner gating from inlet_source_audit.json."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
sys.path.insert(0, str(REPO / "tests"))

from native_fluidx3d_runner_smoke import create_case, create_source, load_json, sha256_file, write  # noqa: E402


def run_cmd(args: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def write_inlet_audit(
    path: Path,
    case_dir: Path,
    *,
    paper_gate: str,
    distribution_consistent: bool,
    velocity_field_only: bool,
) -> None:
    setup_path = case_dir / "src" / "setup.cpp"
    defines_path = case_dir / "src" / "defines.hpp"
    report = {
        "schema": "citylbm.inlet_source_audit.v1",
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": sha256_file(setup_path),
        "defines_hpp": str(defines_path),
        "defines_hpp_sha256": sha256_file(defines_path),
        "inlet_source_gate": "pass",
        "inlet_source_gate_reasons": ["inlet_source_consistent_with_declared_metadata"],
        "paper_grade_inlet_source_gate": paper_gate,
        "paper_grade_inlet_source_gate_reasons": (
            ["source_distribution_consistent"]
            if paper_gate == "pass"
            else ["source_not_distribution_consistent", "source_velocity_field_only"]
        ),
        "inlet_source_method_class": (
            "digital_filter_distribution_consistent"
            if distribution_consistent
            else "stg_lite_correlated_velocity_field_only"
        ),
        "inlet_source_turbulent_inflow_fidelity_class": (
            "distribution_consistent_digital_filter"
            if distribution_consistent
            else "correlated_velocity_field_only"
        ),
        "inlet_source_distribution_consistent": distribution_consistent,
        "inlet_source_velocity_field_only": velocity_field_only,
        "inlet_source_has_correlated_velocity_field_only": velocity_field_only,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": False,
    }
    write(path, json.dumps(report, indent=2))


def base_runner_args(case_dir: Path, source_root: Path, out_path: Path) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "--case-dir",
        str(case_dir),
        "--fluidx3d-source",
        str(source_root),
        "--out",
        str(out_path),
        "--baseline-id",
        "smoke-casea-native-inlet-audit",
        "--expected-aij-case",
        "CaseA",
        "--expected-wind-direction",
        "N",
        "--time-steps",
        "40000",
        "--vtk-save-interval",
        "1000",
        "--expected-vtk-frame-count",
        "40",
        "--min-flow-throughs",
        "0",
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        pass_audit = temp / "preflight" / "inlet_source_audit_pass.json"
        write_inlet_audit(
            pass_audit,
            case_dir,
            paper_gate="pass",
            distribution_consistent=True,
            velocity_field_only=False,
        )
        pass_manifest = temp / "pass" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(base_runner_args(case_dir, source_root, pass_manifest) + ["--inlet-source-audit", str(pass_audit)])
        passed = load_json(pass_manifest)
        if passed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(passed["RunnerGate"])
        if passed["InletSourceAuditGate"]["Gate"] != "pass":
            raise AssertionError(passed["InletSourceAuditGate"])

        fail_audit = temp / "preflight" / "inlet_source_audit_fail.json"
        write_inlet_audit(
            fail_audit,
            case_dir,
            paper_gate="fail",
            distribution_consistent=False,
            velocity_field_only=True,
        )
        fail_manifest = temp / "fail" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, fail_manifest) + ["--inlet-source-audit", str(fail_audit)],
            expected_returncode=2,
        )
        failed = load_json(fail_manifest)
        for reason in [
            "paper_grade_inlet_source_gate_not_pass:fail",
            "source_not_distribution_consistent",
            "source_velocity_field_only",
        ]:
            if reason not in failed["RunnerGate"]["Reasons"]:
                raise AssertionError(failed["RunnerGate"])

        missing_audit_manifest = temp / "missing_audit" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, missing_audit_manifest) + ["--run"],
            expected_returncode=2,
        )
        missing_audit = load_json(missing_audit_manifest)
        auto_audit = missing_audit.get("AutoInletSourceAudit", {})
        if auto_audit.get("Generated") is not True:
            raise AssertionError(auto_audit)
        auto_boundary_audit = missing_audit.get("AutoBoundarySourceAudit", {})
        if auto_boundary_audit.get("Generated") is not True:
            raise AssertionError(auto_boundary_audit)
        auto_coordinate_audit = missing_audit.get("AutoCoordinateProbeProtocolAudit", {})
        if auto_coordinate_audit.get("Generated") is not True:
            raise AssertionError(auto_coordinate_audit)
        if not missing_audit["InletSourceAuditPath"].endswith("inlet_source_audit_auto.json"):
            raise AssertionError(missing_audit["InletSourceAuditPath"])
        if not missing_audit["BoundarySourceAuditPath"].endswith("boundary_source_audit_auto.json"):
            raise AssertionError(missing_audit["BoundarySourceAuditPath"])
        if not missing_audit["CoordinateProbeProtocolAuditPath"].endswith(
            "coordinate_probe_protocol_audit_auto.json"
        ):
            raise AssertionError(missing_audit["CoordinateProbeProtocolAuditPath"])
        if "run_requested_without_inlet_source_audit" in missing_audit["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_audit["RunnerGate"])
        if "run_requested_without_boundary_source_audit" in missing_audit["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_audit["RunnerGate"])
        if "run_requested_without_coordinate_probe_protocol_audit" in missing_audit["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_audit["RunnerGate"])
        if "paper_grade_inlet_source_gate_not_pass:fail" not in missing_audit["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_audit["RunnerGate"])
        if missing_audit["Run"]["Gate"] != "blocked":
            raise AssertionError(missing_audit["Run"])

    print("native_runner_inlet_source_audit_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
