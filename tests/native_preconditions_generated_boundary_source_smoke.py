#!/usr/bin/env python3
"""Smoke-test native preconditions with generated inlet and boundary source audits."""

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
    defines = case_dir / "defines.hpp"
    metadata = case_dir / "case_metadata.json"
    manifest = case_dir / "native_fluidx3d_baseline_manifest.json"
    inlet_source = case_dir / "inlet_source_generated_native_boundary_smoke.json"
    boundary_source = case_dir / "boundary_source_generated_native_boundary_smoke.json"
    report = case_dir / "native_preconditions_generated_boundary_source_audit.json"
    for required in [setup, defines, metadata, manifest]:
        require(required.exists(), {"missing": str(required), "stdout": codegen.stdout})

    inlet_audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_inlet_source.py"),
            "--setup",
            str(setup),
            "--defines",
            str(defines),
            "--metadata",
            str(metadata),
            "--out",
            str(inlet_source),
        ]
    )
    require(inlet_audit.returncode == 2, {"stdout": inlet_audit.stdout, "stderr": inlet_audit.stderr})

    boundary_audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_boundary_source.py"),
            "--setup",
            str(setup),
            "--metadata",
            str(metadata),
            "--out",
            str(boundary_source),
        ]
    )
    require(boundary_audit.returncode == 2, {"stdout": boundary_audit.stdout, "stderr": boundary_audit.stderr})

    native_audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_native_preconditions.py"),
            str(case_dir),
            "--manifest",
            str(manifest),
            "--metadata",
            str(metadata),
            "--inlet-source-audit",
            str(inlet_source),
            "--boundary-source-audit",
            str(boundary_source),
            "--out",
            str(report),
        ]
    )
    require(native_audit.returncode == 2, {"stdout": native_audit.stdout, "stderr": native_audit.stderr})
    data = json.loads(report.read_text(encoding="utf-8"))
    reasons = data.get("native_preconditions_gate_reasons", [])
    boundary_reasons = data.get("native_boundary_equivalence_gate_reasons", [])

    require(data.get("inlet_source_setup_cpp_sha256_matches_current") is True, data)
    require(data.get("boundary_source_setup_cpp_sha256_matches_current") is True, data)
    require(data.get("boundary_source_gate") == "pass", data)
    require(data.get("paper_grade_boundary_source_gate") == "fail", data)
    require(data.get("boundary_source_method_class") == "profile_maintenance_buffer_diagnostic", data)
    require(data.get("boundary_source_fidelity_class") == "diagnostic_profile_maintenance_buffer", data)
    require(data.get("boundary_source_wind_tunnel_equivalent") is False, data)
    require(data.get("boundary_source_simplified") is False, data)
    require(data.get("boundary_source_has_simplified_wind_tunnel_surrogate") is True, data)
    require(data.get("boundary_source_simplified_wind_tunnel_surrogate_gate") == "fail", data)
    require(data.get("boundary_source_has_complete_wind_tunnel_evidence") is False, data)
    require(data.get("boundary_source_advanced_code_evidence") is False, data)
    require(data.get("boundary_source_has_fixed_mean_outlet_lateral_top_treatment") is True, data)
    require(data.get("boundary_source_fixed_mean_outlet_lateral_top_treatment_gate") == "diagnostic_only_with_profile_maintenance_buffer", data)
    require(data.get("native_boundary_equivalence_gate") == "fail", data)

    for expected in [
        "paper_grade_boundary_source_gate_not_pass",
        "boundary_source_not_wind_tunnel_equivalent",
        "boundary_source_has_simplified_wind_tunnel_surrogate",
        "boundary_source_simplified_wind_tunnel_surrogate_gate_not_pass",
        "boundary_source_simplified_wind_tunnel_surrogate_reason_simplified_type_e_box",
        "boundary_source_fidelity_class_not_paper_grade_diagnostic_profile_maintenance_buffer",
        "boundary_source_has_complete_wind_tunnel_evidence_not_true",
        "boundary_source_advanced_code_evidence_not_true",
        "boundary_source_fixed_mean_outlet_lateral_top_treatment_diagnostic_only",
        "boundary_source_missing_paper_grade_evidence_non_reflecting_or_validated_outlet_state",
        "boundary_source_missing_paper_grade_evidence_side_top_boundary_pair_mapping",
        "boundary_source_missing_paper_grade_evidence_precursor_or_recycling_development_field",
        "boundary_protocol_audit_missing",
        "boundary_runtime_audit_missing",
        "native_boundary_equivalence_gate_not_pass",
    ]:
        require(expected in reasons, data)

    for expected in [
        "paper_grade_boundary_source_gate_not_pass:fail",
        "boundary_source_wind_tunnel_equivalent_not_true:False",
        "boundary_source_has_simplified_wind_tunnel_surrogate_not_false:True",
        "boundary_source_simplified_wind_tunnel_surrogate_gate_not_pass:fail",
        "boundary_source_simplified_wind_tunnel_surrogate_reason:simplified_type_e_box",
        "boundary_source_fidelity_class_not_paper_grade:diagnostic_profile_maintenance_buffer",
        "boundary_protocol_audit_missing",
        "boundary_runtime_audit_missing",
        "boundary_runtime_source_vtk_hash_count_0_below_minimum_40",
    ]:
        require(expected in boundary_reasons, data)

    print("native_preconditions_generated_boundary_source_smoke passed")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
