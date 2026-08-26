#!/usr/bin/env python3
"""Smoke-test critical native/CityLBM parity field coverage."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_metrics(path: Path, software: str, audit_module, *, missing_field: str = "") -> None:
    fields = sorted(
        {
            "software",
            *audit_module.TEXT_FIELDS,
            *audit_module.GATE_FIELDS,
            *audit_module.HASH_FIELDS,
            *audit_module.NUMERIC_FIELDS,
        }
    )
    row = {field: "same" for field in fields}
    row.update(
        {
            "software": software,
            "case": "CaseA",
            "wind_direction": "N",
        }
    )
    for field in audit_module.GATE_FIELDS:
        row[field] = "pass"
    for field in audit_module.HASH_FIELDS:
        row[field] = "a" * 64
    for field in audit_module.NUMERIC_FIELDS:
        row[field] = "1"
    if missing_field:
        row[missing_field] = ""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def run_parity_audit(audit_script: Path, city: Path, native: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(audit_script),
            "--citylbm-metrics",
            str(city),
            "--native-metrics",
            str(native),
            "--out",
            str(out),
            "--case",
            "CaseA",
            "--wind-direction",
            "N",
        ],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    gate_module = load_module("validation_gate", REPO / "scripts" / "validation_gate.py")
    audit_module = load_module(
        "audit_native_citylbm_parity",
        REPO / "scripts" / "audit_native_citylbm_parity.py",
    )

    with tempfile.TemporaryDirectory(prefix="citylbm_parity_critical_") as tmp:
        tmp_path = Path(tmp)
        city = tmp_path / "city.csv"
        native = tmp_path / "native.csv"
        out = tmp_path / "native_citylbm_parity_audit.json"
        write_metrics(city, "citylbm", audit_module)
        write_metrics(native, "native-fluidx3d", audit_module)
        passed = run_parity_audit(REPO / "scripts" / "audit_native_citylbm_parity.py", city, native, out)
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr))
        report = json.loads(out.read_text(encoding="utf-8"))
        if report["critical_parity_field_gate"] != "pass":
            raise AssertionError(report)
        for field in [
            "time_averaging_fidelity_class",
            "native_preconditions_strict_native_run_gate",
            "probe_component_fidelity_class",
            "streamwise_sign_gate",
            "synthetic_temporal_sampling_gate",
            "synthetic_expected_final_window_refresh_count",
            "inlet_source_distribution_consistent",
            "inlet_source_velocity_field_only",
            "inlet_source_requires_distribution_reconstruction",
            "inlet_synthetic_correlation_model",
            "inlet_source_has_reynolds_stress_tensor_metadata_claim",
            "inlet_source_has_reynolds_stress_diagonal_source_evidence",
            "inlet_source_has_reynolds_stress_offdiagonal_source_evidence",
            "inlet_source_has_reynolds_stress_full_tensor_source_evidence",
            "inlet_source_has_reynolds_stress_diagonal_usage_evidence",
            "inlet_source_has_reynolds_stress_offdiagonal_usage_evidence",
            "inlet_source_has_reynolds_stress_full_tensor_usage_evidence",
            "inlet_source_has_sem_eddy_update_evidence",
            "inlet_source_has_sem_eddy_velocity_coupling_evidence",
            "inlet_source_has_k_driven_three_component_stg",
            "inlet_source_has_rms_k_velocity_surrogate",
            "inlet_source_rms_k_surrogate_gate",
            "inlet_source_rms_k_surrogate_reasons",
            "inlet_source_has_source_length_scale_evidence",
            "inlet_source_has_metadata_length_scale_evidence",
            "inlet_source_length_scale_evidence_basis",
            "inlet_source_has_temporal_filter_state",
            "runtime_inlet_diagnostics_evidence_required",
            "runtime_inlet_diagnostics_evidence_required_basis_csv",
            "runtime_inlet_diagnostics_evidence_gate",
            "runtime_inlet_diagnostics_step_window_gate",
            "runtime_inlet_diagnostics_selected_steps_csv",
            "runtime_inlet_diagnostics_steps_cover_runtime_window",
            "runtime_inlet_diagnostics_csv_sha256",
            "runtime_inlet_diagnostics_audit_json_sha256",
            "native_inlet_equivalence_gate",
            "source_time_steps",
            "source_step_span",
            "selected_last_window",
            "final_window_stationarity_gate",
            "native_preconditions_runtime_final_window_frame_count_gate",
            "native_preconditions_runtime_source_vtk_sha256_count",
            "native_preconditions_time_averaging_evidence_file_gate",
            "native_preconditions_time_averaging_evidence_schema",
            "native_preconditions_time_averaging_evidence_gate",
            "native_preconditions_time_averaging_evidence_actual_vtk_output_gate",
            "native_preconditions_time_averaging_evidence_bound",
            "native_preconditions_time_averaging_evidence_selected_steps",
            "native_preconditions_time_averaging_evidence_selected_hash_count",
            "probe_mapping_table_sha256",
            "velocity_component",
            "compared_component_unique_values",
            "probe_vtk_source_time_steps",
            "probe_grid_extent_gate",
            "max_official_coordinate_delta_m",
            "official_probe_set_gate",
            "official_probe_height_gate",
            "component_sensitivity_probe_audit_sha256",
            "component_source_window_gate",
            "component_source_sha256",
            "best_component_by_rmse",
            "normalization_best_fit_scale",
            "probe_uref_values",
            "native_probe_component_equivalence_gate",
            "native_probe_component_interpretation_gate",
            "native_probe_official_height_gate",
            "native_probe_max_official_coordinate_delta_m",
            "native_probe_uref_mismatch_count",
            "native_probe_out_of_tolerance_count",
            "native_probe_component_source_step_hash_pairs_match_runtime",
            "boundary_equivalence_supported",
            "boundary_evidence_files_all_hashed",
            "boundary_condition_fields_supported",
            "roughness_treatment_supported",
            "floor_roughness_source_supported",
            "clearance_numeric_gate",
            "boundary_runtime_side_top_normal_leakage_gate",
            "boundary_source_has_non_reflecting_outlet_method",
            "boundary_source_has_periodic_pair_mapping_evidence",
            "boundary_source_has_rough_wall_action_evidence",
            "boundary_source_has_precursor_or_recycling_boundary_field_evidence",
            "boundary_source_missing_paper_grade_source_evidence",
            "boundary_runtime_source_time_steps_csv",
            "boundary_runtime_source_time_steps_match_runtime",
            "boundary_runtime_source_vtk_sha256_match_runtime",
            "boundary_runtime_source_step_hash_pairs_match_runtime",
        ]:
            if field not in report["required_critical_fields"]:
                raise AssertionError((field, report["required_critical_fields"]))
        status = gate_module.native_citylbm_parity_critical_status(report)
        if not status["ok"]:
            raise AssertionError(status)

        legacy = dict(report)
        for key in [
            "critical_parity_field_gate",
            "required_critical_fields",
            "required_critical_field_count",
            "matched_critical_field_count",
            "missing_critical_fields",
        ]:
            legacy.pop(key, None)
        legacy_status = gate_module.native_citylbm_parity_critical_status(legacy)
        if legacy_status["ok"]:
            raise AssertionError(legacy_status)
        if "critical_parity_field_gate_not_pass:missing" not in legacy_status["reasons"]:
            raise AssertionError(legacy_status)

        stale_report = dict(report)
        stale_required = [
            field
            for field in stale_report["required_critical_fields"]
            if field not in {"native_preconditions_strict_native_run_gate", "streamwise_sign_gate"}
        ]
        stale_report["required_critical_fields"] = stale_required
        stale_report["required_critical_field_count"] = len(stale_required)
        stale_report["matched_critical_fields"] = stale_required
        stale_report["matched_critical_field_count"] = len(stale_required)
        stale_report["missing_critical_fields"] = []
        stale_status = gate_module.native_citylbm_parity_critical_status(stale_report)
        if stale_status["ok"]:
            raise AssertionError(stale_status)
        if not any(
            reason.startswith("required_critical_fields_omit_current:")
            for reason in stale_status["reasons"]
        ):
            raise AssertionError(stale_status)

        bad_native = tmp_path / "native_missing_synthetic_gate.csv"
        bad_out = tmp_path / "bad_native_citylbm_parity_audit.json"
        write_metrics(
            bad_native,
            "native-fluidx3d",
            audit_module,
            missing_field="synthetic_temporal_sampling_gate",
        )
        failed = run_parity_audit(REPO / "scripts" / "audit_native_citylbm_parity.py", city, bad_native, bad_out)
        if failed.returncode == 0:
            raise AssertionError((failed.returncode, failed.stdout, failed.stderr))
        bad_report = json.loads(bad_out.read_text(encoding="utf-8"))
        if bad_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_report)
        if "synthetic_temporal_sampling_gate" not in bad_report["missing_critical_fields"]:
            raise AssertionError(bad_report)

        bad_length_basis = tmp_path / "native_missing_inlet_length_basis.csv"
        bad_length_basis_out = tmp_path / "bad_length_basis_native_citylbm_parity_audit.json"
        write_metrics(
            bad_length_basis,
            "native-fluidx3d",
            audit_module,
            missing_field="inlet_source_length_scale_evidence_basis",
        )
        failed_length_basis = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_length_basis,
            bad_length_basis_out,
        )
        if failed_length_basis.returncode == 0:
            raise AssertionError(
                (
                    failed_length_basis.returncode,
                    failed_length_basis.stdout,
                    failed_length_basis.stderr,
                )
            )
        bad_length_basis_report = json.loads(bad_length_basis_out.read_text(encoding="utf-8"))
        if bad_length_basis_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_length_basis_report)
        if (
            "inlet_source_length_scale_evidence_basis"
            not in bad_length_basis_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_length_basis_report)

        bad_sem = tmp_path / "native_missing_sem_coupling.csv"
        bad_sem_out = tmp_path / "bad_sem_native_citylbm_parity_audit.json"
        write_metrics(
            bad_sem,
            "native-fluidx3d",
            audit_module,
            missing_field="inlet_source_has_sem_eddy_velocity_coupling_evidence",
        )
        failed_sem = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_sem,
            bad_sem_out,
        )
        if failed_sem.returncode == 0:
            raise AssertionError((failed_sem.returncode, failed_sem.stdout, failed_sem.stderr))
        bad_sem_report = json.loads(bad_sem_out.read_text(encoding="utf-8"))
        if bad_sem_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_sem_report)
        if (
            "inlet_source_has_sem_eddy_velocity_coupling_evidence"
            not in bad_sem_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_sem_report)

        bad_inlet_equivalence = tmp_path / "native_missing_inlet_equivalence.csv"
        bad_inlet_equivalence_out = tmp_path / "bad_inlet_equivalence_native_citylbm_parity_audit.json"
        write_metrics(
            bad_inlet_equivalence,
            "native-fluidx3d",
            audit_module,
            missing_field="native_inlet_equivalence_gate",
        )
        failed_inlet_equivalence = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_inlet_equivalence,
            bad_inlet_equivalence_out,
        )
        if failed_inlet_equivalence.returncode == 0:
            raise AssertionError(
                (
                    failed_inlet_equivalence.returncode,
                    failed_inlet_equivalence.stdout,
                    failed_inlet_equivalence.stderr,
                )
            )
        bad_inlet_equivalence_report = json.loads(
            bad_inlet_equivalence_out.read_text(encoding="utf-8")
        )
        if bad_inlet_equivalence_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_inlet_equivalence_report)
        if (
            "native_inlet_equivalence_gate"
            not in bad_inlet_equivalence_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_inlet_equivalence_report)

        bad_boundary = tmp_path / "native_missing_boundary_detail.csv"
        bad_boundary_out = tmp_path / "bad_boundary_native_citylbm_parity_audit.json"
        write_metrics(
            bad_boundary,
            "native-fluidx3d",
            audit_module,
            missing_field="boundary_source_has_non_reflecting_outlet_method",
        )
        failed_boundary = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_boundary,
            bad_boundary_out,
        )
        if failed_boundary.returncode == 0:
            raise AssertionError(
                (failed_boundary.returncode, failed_boundary.stdout, failed_boundary.stderr)
            )
        bad_boundary_report = json.loads(bad_boundary_out.read_text(encoding="utf-8"))
        if bad_boundary_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_boundary_report)
        if (
            "boundary_source_has_non_reflecting_outlet_method"
            not in bad_boundary_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_boundary_report)

        bad_boundary_window = tmp_path / "native_missing_boundary_window.csv"
        bad_boundary_window_out = tmp_path / "bad_boundary_window_native_citylbm_parity_audit.json"
        write_metrics(
            bad_boundary_window,
            "native-fluidx3d",
            audit_module,
            missing_field="boundary_runtime_source_step_hash_pairs_match_runtime",
        )
        failed_boundary_window = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_boundary_window,
            bad_boundary_window_out,
        )
        if failed_boundary_window.returncode == 0:
            raise AssertionError(
                (
                    failed_boundary_window.returncode,
                    failed_boundary_window.stdout,
                    failed_boundary_window.stderr,
                )
            )
        bad_boundary_window_report = json.loads(bad_boundary_window_out.read_text(encoding="utf-8"))
        if bad_boundary_window_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_boundary_window_report)
        if (
            "boundary_runtime_source_step_hash_pairs_match_runtime"
            not in bad_boundary_window_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_boundary_window_report)

        bad_time_evidence = tmp_path / "native_missing_time_evidence_file_gate.csv"
        bad_time_evidence_out = tmp_path / "bad_time_evidence_native_citylbm_parity_audit.json"
        write_metrics(
            bad_time_evidence,
            "native-fluidx3d",
            audit_module,
            missing_field="native_preconditions_time_averaging_evidence_file_gate",
        )
        failed_time_evidence = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_time_evidence,
            bad_time_evidence_out,
        )
        if failed_time_evidence.returncode == 0:
            raise AssertionError(
                (
                    failed_time_evidence.returncode,
                    failed_time_evidence.stdout,
                    failed_time_evidence.stderr,
                )
            )
        bad_time_evidence_report = json.loads(bad_time_evidence_out.read_text(encoding="utf-8"))
        if bad_time_evidence_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_time_evidence_report)
        if (
            "native_preconditions_time_averaging_evidence_file_gate"
            not in bad_time_evidence_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_time_evidence_report)

        bad_roughness_support = tmp_path / "native_missing_roughness_support.csv"
        bad_roughness_support_out = tmp_path / "bad_roughness_support_native_citylbm_parity_audit.json"
        write_metrics(
            bad_roughness_support,
            "native-fluidx3d",
            audit_module,
            missing_field="roughness_treatment_supported",
        )
        failed_roughness_support = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_roughness_support,
            bad_roughness_support_out,
        )
        if failed_roughness_support.returncode == 0:
            raise AssertionError(
                (
                    failed_roughness_support.returncode,
                    failed_roughness_support.stdout,
                    failed_roughness_support.stderr,
                )
            )
        bad_roughness_support_report = json.loads(
            bad_roughness_support_out.read_text(encoding="utf-8")
        )
        if bad_roughness_support_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_roughness_support_report)
        if (
            "roughness_treatment_supported"
            not in bad_roughness_support_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_roughness_support_report)

        bad_velocity_component = tmp_path / "native_missing_velocity_component.csv"
        bad_velocity_component_out = tmp_path / "bad_velocity_component_native_citylbm_parity_audit.json"
        write_metrics(
            bad_velocity_component,
            "native-fluidx3d",
            audit_module,
            missing_field="velocity_component",
        )
        failed_velocity_component = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_velocity_component,
            bad_velocity_component_out,
        )
        if failed_velocity_component.returncode == 0:
            raise AssertionError(
                (
                    failed_velocity_component.returncode,
                    failed_velocity_component.stdout,
                    failed_velocity_component.stderr,
                )
            )
        bad_velocity_component_report = json.loads(
            bad_velocity_component_out.read_text(encoding="utf-8")
        )
        if bad_velocity_component_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_velocity_component_report)
        if "velocity_component" not in bad_velocity_component_report["missing_critical_fields"]:
            raise AssertionError(bad_velocity_component_report)

        bad_native_probe_gate = tmp_path / "native_missing_probe_component_gate.csv"
        bad_native_probe_gate_out = tmp_path / "bad_probe_component_gate_native_citylbm_parity_audit.json"
        write_metrics(
            bad_native_probe_gate,
            "native-fluidx3d",
            audit_module,
            missing_field="native_probe_component_equivalence_gate",
        )
        failed_native_probe_gate = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_native_probe_gate,
            bad_native_probe_gate_out,
        )
        if failed_native_probe_gate.returncode == 0:
            raise AssertionError(
                (
                    failed_native_probe_gate.returncode,
                    failed_native_probe_gate.stdout,
                    failed_native_probe_gate.stderr,
                )
            )
        bad_native_probe_gate_report = json.loads(
            bad_native_probe_gate_out.read_text(encoding="utf-8")
        )
        if bad_native_probe_gate_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_native_probe_gate_report)
        if (
            "native_probe_component_equivalence_gate"
            not in bad_native_probe_gate_report["missing_critical_fields"]
        ):
            raise AssertionError(bad_native_probe_gate_report)

        bad_clearance_gate = tmp_path / "native_missing_clearance_gate.csv"
        bad_clearance_gate_out = tmp_path / "bad_clearance_gate_native_citylbm_parity_audit.json"
        write_metrics(
            bad_clearance_gate,
            "native-fluidx3d",
            audit_module,
            missing_field="clearance_numeric_gate",
        )
        failed_clearance_gate = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_clearance_gate,
            bad_clearance_gate_out,
        )
        if failed_clearance_gate.returncode == 0:
            raise AssertionError(
                (
                    failed_clearance_gate.returncode,
                    failed_clearance_gate.stdout,
                    failed_clearance_gate.stderr,
                )
            )
        bad_clearance_gate_report = json.loads(bad_clearance_gate_out.read_text(encoding="utf-8"))
        if bad_clearance_gate_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_clearance_gate_report)
        if "clearance_numeric_gate" not in bad_clearance_gate_report["missing_critical_fields"]:
            raise AssertionError(bad_clearance_gate_report)

        bad_time = tmp_path / "native_missing_time_window.csv"
        bad_time_out = tmp_path / "bad_time_native_citylbm_parity_audit.json"
        write_metrics(
            bad_time,
            "native-fluidx3d",
            audit_module,
            missing_field="source_time_steps",
        )
        failed_time = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_time,
            bad_time_out,
        )
        if failed_time.returncode == 0:
            raise AssertionError((failed_time.returncode, failed_time.stdout, failed_time.stderr))
        bad_time_report = json.loads(bad_time_out.read_text(encoding="utf-8"))
        if bad_time_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_time_report)
        if "source_time_steps" not in bad_time_report["missing_critical_fields"]:
            raise AssertionError(bad_time_report)

        bad_probe = tmp_path / "native_missing_probe_coordinate.csv"
        bad_probe_out = tmp_path / "bad_probe_native_citylbm_parity_audit.json"
        write_metrics(
            bad_probe,
            "native-fluidx3d",
            audit_module,
            missing_field="max_official_coordinate_delta_m",
        )
        failed_probe = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_probe,
            bad_probe_out,
        )
        if failed_probe.returncode == 0:
            raise AssertionError((failed_probe.returncode, failed_probe.stdout, failed_probe.stderr))
        bad_probe_report = json.loads(bad_probe_out.read_text(encoding="utf-8"))
        if bad_probe_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_probe_report)
        if "max_official_coordinate_delta_m" not in bad_probe_report["missing_critical_fields"]:
            raise AssertionError(bad_probe_report)

        bad_component = tmp_path / "native_missing_component_source_hash.csv"
        bad_component_out = tmp_path / "bad_component_native_citylbm_parity_audit.json"
        write_metrics(
            bad_component,
            "native-fluidx3d",
            audit_module,
            missing_field="component_source_sha256",
        )
        failed_component = run_parity_audit(
            REPO / "scripts" / "audit_native_citylbm_parity.py",
            city,
            bad_component,
            bad_component_out,
        )
        if failed_component.returncode == 0:
            raise AssertionError(
                (failed_component.returncode, failed_component.stdout, failed_component.stderr)
            )
        bad_component_report = json.loads(bad_component_out.read_text(encoding="utf-8"))
        if bad_component_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_component_report)
        if "component_source_sha256" not in bad_component_report["missing_critical_fields"]:
            raise AssertionError(bad_component_report)

    print("validation_gate_native_citylbm_parity_critical_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
