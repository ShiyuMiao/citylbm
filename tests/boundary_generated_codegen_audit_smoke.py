#!/usr/bin/env python3
"""Smoke-test boundary source audit against the real generated setup.cpp."""

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
    build = run_command(["dotnet", "build", "-c", "Release"])
    if build.returncode != 0:
        raise AssertionError(build.stdout + "\n" + build.stderr)

    codegen = run_command(
        [
            "dotnet",
            "run",
            "--project",
            str(REPO / "tests" / "CodegenSmoke" / "CodegenSmoke.csproj"),
            "-c",
            "Release",
        ]
    )
    if codegen.returncode != 0:
        raise AssertionError(codegen.stdout + "\n" + codegen.stderr)

    case_dir = Path(tempfile.gettempdir()) / "CityLBM" / "stg_codegen_smoke"
    setup = case_dir / "setup.cpp"
    metadata = case_dir / "case_metadata.json"
    report = case_dir / "boundary_generated_codegen_audit.json"
    require(setup.exists(), {"missing": str(setup), "stdout": codegen.stdout})
    require(metadata.exists(), {"missing": str(metadata), "stdout": codegen.stdout})

    audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_boundary_source.py"),
            "--setup",
            str(setup),
            "--metadata",
            str(metadata),
            "--out",
            str(report),
        ]
    )
    require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
    data = json.loads(report.read_text(encoding="utf-8"))
    require(data.get("boundary_source_gate") == "pass", data)
    require(data.get("paper_grade_boundary_source_gate") == "fail", data)
    require(data.get("boundary_source_method_class") == "simplified_type_e_box", data)
    require(data.get("boundary_source_fidelity_class") == "simplified_type_e_box", data)
    require(data.get("boundary_source_simplified") is True, data)
    require(data.get("boundary_source_wind_tunnel_equivalent") is False, data)
    require(data.get("boundary_source_has_complete_wind_tunnel_evidence") is False, data)
    require(data.get("boundary_source_advanced_code_evidence") is False, data)
    require(data.get("has_type_e_velocity_initialization_before_device_upload") is True, data)
    require(data.get("has_flags_device_upload_after_type_e_velocity_initialization") is True, data)
    require(data.get("has_u_device_upload_after_type_e_velocity_initialization") is True, data)
    require(data.get("has_fixed_mean_type_e_boundary_velocity") is True, data)
    require(data.get("has_fixed_mean_outlet_lateral_top_treatment") is True, data)
    require(data.get("fixed_mean_outlet_lateral_top_treatment_gate") == "diagnostic_only", data)
    require(data.get("has_paper_grade_outlet_source") is False, data)
    require(data.get("has_paper_grade_side_top_source") is False, data)
    require(data.get("has_paper_grade_rough_wall_source") is False, data)
    require(data.get("has_paper_grade_development_source") is False, data)

    paper_reasons = data.get("paper_grade_boundary_source_gate_reasons", [])
    for expected in [
        "boundary_source_not_wind_tunnel_equivalent",
        "boundary_source_fidelity_class_not_paper_grade:simplified_type_e_box",
        "boundary_source_missing_advanced_code_evidence",
        "boundary_source_simplified_type_e_or_solid_only",
        "ground_and_buildings_no_slip_without_rough_wall_or_precursor",
        "outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary",
        "missing_non_reflecting_or_validated_outlet_state",
        "missing_side_top_boundary_pair_mapping",
        "missing_rough_wall_or_wall_function_action",
        "missing_precursor_or_recycling_development_field",
    ]:
        require(expected in paper_reasons, data)

    print("boundary_generated_codegen_audit_smoke passed")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
