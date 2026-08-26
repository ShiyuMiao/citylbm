"""Smoke-test native runner gating from boundary_source_audit.json."""

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


def write_inlet_audit(path: Path, case_dir: Path) -> None:
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
        "paper_grade_inlet_source_gate": "pass",
        "paper_grade_inlet_source_gate_reasons": ["source_distribution_consistent"],
        "inlet_source_distribution_consistent": True,
        "inlet_source_velocity_field_only": False,
    }
    write(path, json.dumps(report, indent=2))


def write_boundary_audit(path: Path, case_dir: Path, *, paper_gate: str) -> None:
    setup_path = case_dir / "src" / "setup.cpp"
    defines_path = case_dir / "src" / "defines.hpp"
    if paper_gate == "pass":
        paper_reasons = ["boundary_source_wind_tunnel_equivalent"]
        simplified = False
        method_class = "wind_tunnel_equivalent"
        fidelity_class = "wind_tunnel_equivalent_complete"
    else:
        paper_reasons = [
            "boundary_source_not_wind_tunnel_equivalent",
            "boundary_source_simplified_type_e_or_solid_only",
        ]
        simplified = True
        method_class = "simplified_type_e_box"
        fidelity_class = "simplified_type_e_box"
    report = {
        "schema": "citylbm.boundary_source_audit.v1",
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": sha256_file(setup_path),
        "defines_hpp": str(defines_path),
        "defines_hpp_sha256": sha256_file(defines_path),
        "boundary_source_gate": "pass",
        "boundary_source_gate_reasons": ["boundary_source_consistent_with_declared_metadata"],
        "paper_grade_boundary_source_gate": paper_gate,
        "paper_grade_boundary_source_gate_reasons": paper_reasons,
        "boundary_source_method_class": method_class,
        "boundary_source_fidelity_class": fidelity_class,
        "boundary_source_wind_tunnel_equivalent": paper_gate == "pass",
        "boundary_source_simplified": simplified,
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
        "smoke-casea-native-boundary-audit",
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
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        inlet_audit = temp / "preflight" / "inlet_source_audit_pass.json"
        write_inlet_audit(inlet_audit, case_dir)

        pass_boundary_audit = temp / "preflight" / "boundary_source_audit_pass.json"
        write_boundary_audit(pass_boundary_audit, case_dir, paper_gate="pass")
        pass_manifest = temp / "pass" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, pass_manifest)
            + ["--inlet-source-audit", str(inlet_audit), "--boundary-source-audit", str(pass_boundary_audit)]
        )
        passed = load_json(pass_manifest)
        if passed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(passed["RunnerGate"])
        if passed["BoundarySourceAuditGate"]["Gate"] != "pass":
            raise AssertionError(passed["BoundarySourceAuditGate"])

        fail_boundary_audit = temp / "preflight" / "boundary_source_audit_fail.json"
        write_boundary_audit(fail_boundary_audit, case_dir, paper_gate="fail")
        fail_manifest = temp / "fail" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, fail_manifest)
            + ["--inlet-source-audit", str(inlet_audit), "--boundary-source-audit", str(fail_boundary_audit)],
            expected_returncode=2,
        )
        failed = load_json(fail_manifest)
        for reason in [
            "paper_grade_boundary_source_gate_not_pass:fail",
            "boundary_source_not_wind_tunnel_equivalent",
            "boundary_source_simplified_type_e_or_solid_only",
        ]:
            if reason not in failed["RunnerGate"]["Reasons"]:
                raise AssertionError(failed["RunnerGate"])

        missing_boundary_manifest = temp / "missing_boundary" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, missing_boundary_manifest)
            + ["--inlet-source-audit", str(inlet_audit), "--run"],
            expected_returncode=2,
        )
        missing_boundary = load_json(missing_boundary_manifest)
        if "run_requested_without_boundary_source_audit" not in missing_boundary["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_boundary["RunnerGate"])
        if missing_boundary["Run"]["Gate"] != "blocked":
            raise AssertionError(missing_boundary["Run"])

    print("native_runner_boundary_source_audit_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
