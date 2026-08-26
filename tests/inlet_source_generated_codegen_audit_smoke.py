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
    require(data.get("inlet_source_method_class") == "synthetic_eddy_distribution_consistent", data)
    require(data.get("inlet_source_turbulent_inflow_fidelity_class") == "distribution_consistent_synthetic_eddy", data)
    require(data.get("distribution_consistency_basis") == "sem_eddy_population_distribution_reconstruction", data)
    require(data.get("inlet_source_distribution_consistent") is True, data)
    require(data.get("inlet_source_velocity_field_only") is False, data)
    require(data.get("inlet_source_has_correlated_velocity_field_only") is False, data)
    require(data.get("inlet_source_has_uncorrelated_rms_velocity_field_only") is False, data)
    require(data.get("has_uncorrelated_random_inlet") is False, data)
    require(data.get("inlet_distribution_route") == "fluidx3d_reconstruct_inlet_stress_boundaries", data)
    require(data.get("inlet_distribution_route_gate") == "pass", data)
    require(data.get("has_distribution_function_write") is False, data)
    require(data.get("has_reconstruct_inlet_stress_ddf_define") is True, data)
    require(data.get("has_reconstruct_inlet_stress_call") is True, data)
    require(data.get("has_type_e_inlet_stress_reconstruction_route") is True, data)
    require(data.get("has_inlet_distribution_reconstruction") is True, data)
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
    require(data.get("has_full_tensor_covariance_preserving_mean_correction") is True, data)
    require(data.get("has_full_tensor_component_rms_rescale_guard") is True, data)
    require(data.get("setup_inlet_codegen_route") == "current_citylbm_stg_layerwise_type_e_route", data)
    require(data.get("has_current_citylbm_stg_codegen_route") is True, data)
    require(data.get("has_legacy_runtime_diagnostic_patch_route") is False, data)
    require(data.get("short_canary_allowed_by_codegen_route") is True, data)
    require(data.get("has_inlet_length_scale_evidence") is True, data)
    require(data.get("has_source_length_scale_evidence") is False, data)
    require(data.get("has_metadata_length_scale_evidence") is True, data)
    require(data.get("inlet_length_scale_evidence_basis") == "metadata_gate_only", data)
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
        "source_reynolds_stress_tensor_is_isotropic_k_assumption_only",
    ]:
        require(expected in paper_reasons, data)
    for cleared in [
        "source_not_distribution_consistent",
        "source_velocity_field_only",
        "source_correlated_velocity_field_only_without_distribution_reconstruction",
    ]:
        require(cleared not in paper_reasons, data)
    require(data.get("development_acceleration_stage") == "resolve_reynolds_stress_tensor_or_precursor_evidence", data)
    require(data.get("development_acceleration_runs_cfd_next") is False, data)
    require(data.get("long_cfd_allowed_by_inlet_source_audit") is False, data)

    tensor_case_dir = Path(tempfile.gettempdir()) / "CityLBM" / "stg_full_reynolds_stress_tensor"
    tensor_setup = tensor_case_dir / "setup.cpp"
    tensor_defines = tensor_case_dir / "defines.hpp"
    tensor_metadata = tensor_case_dir / "case_metadata.json"
    tensor_report = tensor_case_dir / "inlet_source_full_tensor_codegen_audit.json"
    require(tensor_setup.exists(), {"missing": str(tensor_setup), "stdout": codegen.stdout})
    require(tensor_defines.exists(), {"missing": str(tensor_defines), "stdout": codegen.stdout})
    require(tensor_metadata.exists(), {"missing": str(tensor_metadata), "stdout": codegen.stdout})

    tensor_audit = run_command(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_inlet_source.py"),
            "--setup",
            str(tensor_setup),
            "--defines",
            str(tensor_defines),
            "--metadata",
            str(tensor_metadata),
            "--out",
            str(tensor_report),
        ]
    )
    require(tensor_audit.returncode == 0, {"stdout": tensor_audit.stdout, "stderr": tensor_audit.stderr})
    tensor_data = json.loads(tensor_report.read_text(encoding="utf-8"))
    require(tensor_data.get("inlet_source_gate") == "pass", tensor_data)
    require(tensor_data.get("paper_grade_inlet_source_gate") == "pass", tensor_data)
    require(tensor_data.get("inlet_source_distribution_consistent") is True, tensor_data)
    require(tensor_data.get("inlet_distribution_route") == "fluidx3d_reconstruct_inlet_stress_boundaries", tensor_data)
    require(tensor_data.get("has_type_e_inlet_stress_reconstruction_route") is True, tensor_data)
    require(tensor_data.get("has_reynolds_stress_full_tensor_source_evidence") is True, tensor_data)
    require(tensor_data.get("has_reynolds_stress_full_tensor_usage_evidence") is True, tensor_data)
    require(tensor_data.get("has_measured_or_precursor_reynolds_stress_tensor_evidence") is True, tensor_data)
    require(tensor_data.get("reynolds_stress_tensor_paper_grade_gate") == "pass", tensor_data)
    require(tensor_data.get("reynolds_stress_treatment") == "measured_or_precursor_full_tensor", tensor_data)
    require(tensor_data.get("has_full_tensor_covariance_preserving_mean_correction") is True, tensor_data)
    require(tensor_data.get("has_full_tensor_component_rms_rescale_guard") is True, tensor_data)
    require(tensor_data.get("setup_inlet_codegen_route") == "current_citylbm_stg_layerwise_type_e_route", tensor_data)
    require(tensor_data.get("has_current_citylbm_stg_codegen_route") is True, tensor_data)
    require(tensor_data.get("has_legacy_runtime_diagnostic_patch_route") is False, tensor_data)
    require(tensor_data.get("short_canary_allowed_by_codegen_route") is True, tensor_data)
    tensor_paper_reasons = tensor_data.get("paper_grade_inlet_source_gate_reasons", [])
    for cleared in [
        "source_reynolds_stress_tensor_is_isotropic_k_assumption_only",
        "source_has_measured_diagonal_rms_but_missing_offdiagonal_or_precursor_tensor",
        "source_reynolds_stress_tensor_declared_but_not_used_in_inlet",
        "source_missing_measured_or_precursor_reynolds_stress_tensor_evidence",
        "source_full_tensor_component_rms_rescale_not_covariance_preserving",
    ]:
        require(cleared not in tensor_paper_reasons, tensor_data)
    require(tensor_data.get("development_acceleration_stage") == "eligible_for_short_native_canary", tensor_data)
    require(tensor_data.get("development_acceleration_runs_cfd_next") is True, tensor_data)
    require(tensor_data.get("long_cfd_allowed_by_inlet_source_audit") is True, tensor_data)

    print("inlet_source_generated_codegen_audit_smoke passed")
    print(report)
    print(tensor_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
