#!/usr/bin/env python3
"""Smoke-test inlet source audit against the real generated setup.cpp."""

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
    report = case_dir / "inlet_source_generated_codegen_audit.json"
    require(setup.exists(), {"missing": str(setup), "stdout": codegen.stdout})
    require(defines.exists(), {"missing": str(defines), "stdout": codegen.stdout})
    require(metadata.exists(), {"missing": str(metadata), "stdout": codegen.stdout})

    audit = run_command(
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
            str(report),
        ]
    )
    require(audit.returncode == 2, {"stdout": audit.stdout, "stderr": audit.stderr})
    data = json.loads(report.read_text(encoding="utf-8"))
    require(data.get("inlet_source_gate") == "pass", data)
    require(data.get("paper_grade_inlet_source_gate") == "fail", data)
    require(data.get("synthetic_inlet_requested") is True, data)
    require(data.get("has_profile_k_lbm") is True, data)
    require(data.get("inlet_source_method_class") == "stg_lite_correlated_velocity_field_only", data)
    require(data.get("inlet_source_turbulent_inflow_fidelity_class") == "correlated_velocity_field_only", data)
    require(data.get("inlet_source_distribution_consistent") is False, data)
    require(data.get("inlet_source_velocity_field_only") is True, data)
    require(data.get("inlet_source_has_correlated_velocity_field_only") is True, data)
    require(data.get("inlet_source_has_uncorrelated_rms_velocity_field_only") is False, data)
    require(data.get("has_uncorrelated_random_inlet") is False, data)
    require(data.get("inlet_distribution_route") == "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u", data)
    require(data.get("inlet_distribution_route_gate") == "pass", data)
    require(data.get("has_distribution_function_write") is False, data)
    require(data.get("has_inlet_distribution_reconstruction") is False, data)
    require(data.get("has_taylor_advection_evidence") is True, data)
    require(data.get("has_transverse_projection_evidence") is True, data)
    require(data.get("has_temporal_filter_state") is True, data)
    require(data.get("has_native_synthetic_eddy_structure_evidence") is True, data)
    require(data.get("has_native_synthetic_eddy_temporal_refresh_evidence") is True, data)
    require(data.get("has_native_synthetic_eddy_evidence") is True, data)
    require(data.get("has_sem_eddy_population_evidence") is True, data)
    require(data.get("has_sem_eddy_update_evidence") is True, data)
    require(data.get("has_sem_eddy_velocity_coupling_evidence") is True, data)
    require(data.get("has_digital_filter_evidence") is False, data)
    require(data.get("has_layerwise_rms_preserving_inlet_correction") is True, data)
    require(data.get("has_inlet_length_scale_evidence") is True, data)
    require(data.get("has_reynolds_stress_diagonal_source_evidence") is True, data)
    require(data.get("has_reynolds_stress_offdiagonal_source_evidence") is True, data)
    require(data.get("has_reynolds_stress_full_tensor_source_evidence") is True, data)
    require(data.get("has_isotropic_k_reynolds_stress_source_evidence") is True, data)
    require(data.get("has_measured_or_precursor_reynolds_stress_tensor_evidence") is False, data)
    require(data.get("reynolds_stress_tensor_paper_grade_gate") == "fail", data)
    require(data.get("reynolds_stress_treatment") == "documented_isotropic_k_tensor_source", data)
    require(data.get("synthetic_inlet_spectral_mode_count") == 128, data)
    require(data.get("synthetic_inlet_spectral_mode_count_gate") == "pass", data)
    require(data.get("has_streamwise_clipping_control") is True, data)
    require(data.get("streamwise_clipping_enabled") is False, data)
    require(data.get("streamwise_min_fraction") == 0.0, data)
    require(data.get("has_legacy_hardcoded_streamwise_clipping") is False, data)

    paper_reasons = data.get("paper_grade_inlet_source_gate_reasons", [])
    for expected in [
        "source_not_distribution_consistent",
        "source_velocity_field_only",
        "source_correlated_velocity_field_only_without_distribution_reconstruction",
        "source_reynolds_stress_tensor_is_isotropic_k_assumption_only",
    ]:
        require(expected in paper_reasons, data)

    print("inlet_source_generated_codegen_audit_smoke passed")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
