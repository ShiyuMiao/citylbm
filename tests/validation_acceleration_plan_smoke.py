#!/usr/bin/env python3
"""Smoke-test the validation acceleration planner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "plan_validation_acceleration.py"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_planner(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_phase(plan: dict, expected: str) -> None:
    actual = plan["recommended_sequence"][0]["phase"]
    if actual != expected:
        raise AssertionError(f"expected {expected}, got {actual}: {plan}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)

        empty_out = temp / "empty_plan.json"
        empty = run_planner("--case", "casee", "--out-json", str(empty_out))
        if empty.returncode != 0:
            raise AssertionError((empty.returncode, empty.stdout, empty.stderr))
        empty_plan = load(empty_out)
        assert_phase(empty_plan, "create_case_and_preflight")
        if empty_plan["acceleration_summary"]["next_execution_policy"] != "run_no_cfd_preflight_first":
            raise AssertionError(empty_plan["acceleration_summary"])
        if empty_plan["acceleration_summary"]["long_cfd_allowed_now"] is not False:
            raise AssertionError(empty_plan["acceleration_summary"])

        setup_blocked = temp / "setup_blocked"
        write_json(
            setup_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {
                    "Gate": "diagnostic_only",
                    "Reasons": ["case_setup_source_not_customtable"],
                },
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "diagnostic_only"},
                "PaperUseGate": {
                    "Gate": "fail",
                    "Reasons": ["debug_or_diagnostic_only_do_not_use_for_r2_or_paper_accuracy_claim"],
                },
            },
        )
        setup_out = temp / "setup_plan.json"
        setup = run_planner("--run-dir", str(setup_blocked), "--out-json", str(setup_out), "--fail-on-blockers")
        if setup.returncode != 2:
            raise AssertionError((setup.returncode, setup.stdout, setup.stderr))
        assert_phase(load(setup_out), "fix_codegen_inputs_before_solver")
        if "case_setup_source_not_customtable" not in setup_out.read_text(encoding="utf-8"):
            raise AssertionError(setup_out.read_text(encoding="utf-8"))
        if "PaperUseGate:fail" not in setup_out.read_text(encoding="utf-8"):
            raise AssertionError(setup_out.read_text(encoding="utf-8"))

        inlet_prerun_blocked = temp / "inlet_prerun_blocked"
        write_json(
            inlet_prerun_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {
                    "Gate": "diagnostic_only",
                    "PreRunGate": "diagnostic_only",
                    "Reasons": [
                        "validation_protocol_prerun_item_fail:inlet_distribution_consistency",
                        "validation_protocol_prerun_item_risk:inlet_reynolds_stress_tensor",
                    ],
                },
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "diagnostic_only"},
            },
        )
        inlet_prerun_out = temp / "inlet_prerun_plan.json"
        inlet_prerun = run_planner("--run-dir", str(inlet_prerun_blocked), "--out-json", str(inlet_prerun_out))
        if inlet_prerun.returncode != 0:
            raise AssertionError((inlet_prerun.returncode, inlet_prerun.stdout, inlet_prerun.stderr))
        assert_phase(load(inlet_prerun_out), "fix_turbulent_inlet_evidence")

        inlet_reynolds_evidence_blocked = temp / "inlet_reynolds_evidence_blocked"
        write_json(
            inlet_reynolds_evidence_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {
                    "Gate": "diagnostic_only",
                    "Reasons": ["validation_protocol_prerun_item_fail:inlet_distribution_consistency"],
                },
                "CaseMetadataPreconditionGate": {"Gate": "diagnostic_only"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "diagnostic_only"},
            },
        )
        write_json(
            inlet_reynolds_evidence_blocked / "preflight" / "inlet_source_audit.json",
            {
                "inlet_source_gate": "pass",
                "paper_grade_inlet_source_gate": "fail",
                "paper_grade_inlet_source_gate_reasons": [
                    "source_missing_measured_or_precursor_reynolds_stress_tensor_evidence"
                ],
            },
        )
        inlet_reynolds_out = temp / "inlet_reynolds_plan.json"
        inlet_reynolds = run_planner(
            "--run-dir",
            str(inlet_reynolds_evidence_blocked),
            "--out-json",
            str(inlet_reynolds_out),
        )
        if inlet_reynolds.returncode != 0:
            raise AssertionError((inlet_reynolds.returncode, inlet_reynolds.stdout, inlet_reynolds.stderr))
        inlet_reynolds_plan = load(inlet_reynolds_out)
        assert_phase(inlet_reynolds_plan, "resolve_inlet_reynolds_stress_evidence")
        if inlet_reynolds_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(inlet_reynolds_plan)
        if inlet_reynolds_plan["acceleration_summary"]["next_batch_name"] != "no_cfd_source_and_protocol_preflight":
            raise AssertionError(inlet_reynolds_plan["acceleration_summary"])
        if inlet_reynolds_plan["acceleration_summary"]["no_cfd_parallel_command_count"] <= 0:
            raise AssertionError(inlet_reynolds_plan["acceleration_summary"])

        reynolds_binding_blocked = temp / "reynolds_binding_blocked"
        write_json(
            reynolds_binding_blocked / "preflight" / "inlet_source_audit.json",
            {
                "paper_grade_inlet_source_gate": "fail",
                "development_acceleration_stage": "resolve_reynolds_stress_tensor_or_precursor_evidence",
                "development_acceleration_runs_cfd_next": False,
            },
        )
        write_json(
            reynolds_binding_blocked / "preflight" / "inlet_reynolds_stress_evidence.json",
            {
                "paper_grade_gate": "fail",
                "source_type": "measured_tensor",
                "reasons": ["stress_csv_sha256_missing_in_metadata"],
            },
        )
        reynolds_binding_out = temp / "reynolds_binding_plan.json"
        reynolds_binding = run_planner(
            "--run-dir",
            str(reynolds_binding_blocked),
            "--out-json",
            str(reynolds_binding_out),
        )
        if reynolds_binding.returncode != 0:
            raise AssertionError((reynolds_binding.returncode, reynolds_binding.stdout, reynolds_binding.stderr))
        reynolds_binding_plan = load(reynolds_binding_out)
        assert_phase(reynolds_binding_plan, "bind_reynolds_stress_evidence_to_current_case")
        if (
            "bind_inlet_reynolds_stress_metadata.py"
            not in reynolds_binding_plan["command_templates"].get("bind_reynolds_stress_metadata", "")
        ):
            raise AssertionError(reynolds_binding_plan["command_templates"])
        if (
            "bind_inlet_reynolds_stress_metadata.py"
            not in reynolds_binding_plan["acceleration_summary"]["next_command"]
        ):
            raise AssertionError(reynolds_binding_plan["acceleration_summary"])
        if reynolds_binding_plan["acceleration_summary"]["next_execution_policy"] != "bind_current_case_evidence_before_preflight":
            raise AssertionError(reynolds_binding_plan["acceleration_summary"])

        reynolds_tensor_blocked = temp / "reynolds_tensor_blocked"
        write_json(
            reynolds_tensor_blocked / "preflight" / "inlet_source_audit.json",
            {
                "paper_grade_inlet_source_gate": "fail",
                "development_acceleration_stage": "resolve_reynolds_stress_tensor_or_precursor_evidence",
                "development_acceleration_runs_cfd_next": False,
            },
        )
        write_json(
            reynolds_tensor_blocked / "preflight" / "inlet_reynolds_stress_evidence.json",
            {
                "paper_grade_gate": "fail",
                "source_type": "measured_tensor",
                "reasons": ["stress_csv_no_valid_full_tensor_rows"],
            },
        )
        reynolds_tensor_out = temp / "reynolds_tensor_plan.json"
        reynolds_tensor = run_planner(
            "--run-dir",
            str(reynolds_tensor_blocked),
            "--out-json",
            str(reynolds_tensor_out),
        )
        if reynolds_tensor.returncode != 0:
            raise AssertionError((reynolds_tensor.returncode, reynolds_tensor.stdout, reynolds_tensor.stderr))
        assert_phase(load(reynolds_tensor_out), "populate_reynolds_stress_tensor_or_precursor_template")

        preflight_pack_blocked = temp / "preflight_pack_blocked"
        write_json(
            preflight_pack_blocked / "native_preflight_pack_manifest.json",
            {
                "Gate": "diagnostic_only",
                "Reasons": [
                    "inlet_reynolds_stress:isotropic_k_assumption_only_not_paper_grade_reynolds_stress",
                    "boundary_source:boundary_source_not_wind_tunnel_equivalent",
                ],
            },
        )
        preflight_pack_out = temp / "preflight_pack_plan.json"
        preflight_pack = run_planner(
            "--run-dir",
            str(preflight_pack_blocked),
            "--out-json",
            str(preflight_pack_out),
            "--fail-on-blockers",
        )
        if preflight_pack.returncode != 2:
            raise AssertionError((preflight_pack.returncode, preflight_pack.stdout, preflight_pack.stderr))
        preflight_pack_plan = load(preflight_pack_out)
        assert_phase(preflight_pack_plan, "resolve_inlet_reynolds_stress_evidence")
        if preflight_pack_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(preflight_pack_plan)
        phases = [item["phase"] for item in preflight_pack_plan["recommended_sequence"]]
        if "resolve_boundary_and_wall_protocol_evidence" not in phases:
            raise AssertionError(preflight_pack_plan["recommended_sequence"])
        boundary_action = next(
            item
            for item in preflight_pack_plan["recommended_sequence"]
            if item["phase"] == "resolve_boundary_and_wall_protocol_evidence"
        )
        if boundary_action["runs_cfd"] is not False:
            raise AssertionError(boundary_action)

        ddf_macro_blocked = temp / "ddf_macro_blocked"
        write_json(
            ddf_macro_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
            },
        )
        write_json(
            ddf_macro_blocked / "preflight" / "fluidx3d_equilibrium_boundary_audit.json",
            {
                "Gate": "diagnostic_only",
                "Reasons": ["type_e_equilibrium_collision_available_but_no_explicit_boundary_ddf_reconstruct_macro_enabled"],
                "Evidence": {
                    "has_reconstruct_equilibrium_kernel": True,
                    "has_reconstruct_feq_from_rho_u": True,
                    "has_reconstruct_store_f": True,
                    "has_lbm_kernel_binding": True,
                    "has_lbm_public_call": True,
                },
                "EnabledMacros": {
                    "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF": False,
                    "RECONSTRUCT_INLET_STRESS_DDF": False,
                },
            },
        )
        ddf_macro_out = temp / "ddf_macro_plan.json"
        ddf_macro = run_planner("--run-dir", str(ddf_macro_blocked), "--out-json", str(ddf_macro_out))
        if ddf_macro.returncode != 0:
            raise AssertionError((ddf_macro.returncode, ddf_macro.stdout, ddf_macro.stderr))
        assert_phase(load(ddf_macro_out), "enable_fluidx3d_ddf_reconstruction_route")
        if "fluidx3d_equilibrium_boundary_audit" not in ddf_macro_out.read_text(encoding="utf-8"):
            raise AssertionError(ddf_macro_out.read_text(encoding="utf-8"))

        advanced_turbulence_blocked = temp / "advanced_turbulence_blocked"
        write_json(
            advanced_turbulence_blocked / "preflight" / "inlet_source_audit.json",
            {
                "inlet_distribution_route": "fluidx3d_reconstruct_equilibrium_boundaries",
                "inlet_distribution_route_gate": "pass",
                "development_acceleration_stage": "fix_distribution_consistent_inlet_source_before_cfd",
                "development_acceleration_runs_cfd_next": False,
                "inlet_source_gate_reasons": [
                    "custom_table_source_missing_profile_origin_z_m",
                    "digital_filter_source_missing_spatiotemporal_filter_state",
                ],
            },
        )
        advanced_turbulence_out = temp / "advanced_turbulence_plan.json"
        advanced_turbulence = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(advanced_turbulence_blocked),
            "--out-json",
            str(advanced_turbulence_out),
        )
        if advanced_turbulence.returncode != 0:
            raise AssertionError((advanced_turbulence.returncode, advanced_turbulence.stdout, advanced_turbulence.stderr))
        advanced_turbulence_plan = load(advanced_turbulence_out)
        assert_phase(advanced_turbulence_plan, "patch_legacy_customtable_profile_origin")
        advanced_summary = advanced_turbulence_plan["acceleration_summary"]
        if advanced_summary["next_execution_policy"] != "patch_legacy_customtable_origin_then_rerun_inlet_audit":
            raise AssertionError(advanced_summary)
        if "patch_legacy_customtable_profile_origin.py" not in advanced_summary["next_command"]:
            raise AssertionError(advanced_summary)
        if "enable_fluidx3d_ddf_reconstruction_route.py" in advanced_summary["next_command"]:
            raise AssertionError(advanced_summary)

        advanced_turbulence_without_origin_blocker = temp / "advanced_turbulence_without_origin_blocker"
        write_json(
            advanced_turbulence_without_origin_blocker / "preflight" / "inlet_source_audit.json",
            {
                "inlet_distribution_route": "fluidx3d_reconstruct_equilibrium_boundaries",
                "inlet_distribution_route_gate": "pass",
                "development_acceleration_stage": "fix_distribution_consistent_inlet_source_before_cfd",
                "development_acceleration_runs_cfd_next": False,
                "inlet_source_gate_reasons": [
                    "digital_filter_source_missing_spatiotemporal_filter_state",
                ],
            },
        )
        advanced_without_origin_out = temp / "advanced_without_origin_plan.json"
        advanced_without_origin = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(advanced_turbulence_without_origin_blocker),
            "--out-json",
            str(advanced_without_origin_out),
        )
        if advanced_without_origin.returncode != 0:
            raise AssertionError(
                (advanced_without_origin.returncode, advanced_without_origin.stdout, advanced_without_origin.stderr)
            )
        advanced_without_origin_plan = load(advanced_without_origin_out)
        assert_phase(advanced_without_origin_plan, "fix_advanced_turbulence_evidence_before_cfd")
        if "audit_inlet_source.py" not in advanced_without_origin_plan["acceleration_summary"]["next_command"]:
            raise AssertionError(advanced_without_origin_plan["acceleration_summary"])

        root_layout_case = temp / "root_layout_case"
        root_layout_case.mkdir()
        write_json(
            root_layout_case / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
            },
        )
        write_json(
            root_layout_case / "preflight" / "fluidx3d_equilibrium_boundary_audit.json",
            {
                "Gate": "diagnostic_only",
                "Reasons": ["type_e_equilibrium_collision_available_but_no_explicit_boundary_ddf_reconstruct_macro_enabled"],
                "Evidence": {
                    "has_reconstruct_equilibrium_kernel": True,
                    "has_reconstruct_feq_from_rho_u": True,
                    "has_reconstruct_store_f": True,
                    "has_lbm_kernel_binding": True,
                    "has_lbm_public_call": True,
                },
                "EnabledMacros": {
                    "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF": False,
                    "RECONSTRUCT_INLET_STRESS_DDF": False,
                },
            },
        )
        (root_layout_case / "setup.cpp").write_text("// root layout setup\n", encoding="utf-8")
        (root_layout_case / "defines.hpp").write_text("// root layout defines\n", encoding="utf-8")
        root_layout_out = temp / "root_layout_plan.json"
        root_layout = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(root_layout_case),
            "--case-dir",
            str(root_layout_case),
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--out-json",
            str(root_layout_out),
        )
        if root_layout.returncode != 0:
            raise AssertionError((root_layout.returncode, root_layout.stdout, root_layout.stderr))
        root_plan = load(root_layout_out)
        assert_phase(root_plan, "enable_fluidx3d_ddf_reconstruction_route")
        first_batch = "\n".join(root_plan["parallel_batches"][0]["commands"])
        if str(root_layout_case / "defines.hpp") not in first_batch:
            raise AssertionError(first_batch)
        if str(root_layout_case / "setup.cpp") not in first_batch:
            raise AssertionError(first_batch)
        if str(root_layout_case / "src" / "defines.hpp") in first_batch:
            raise AssertionError(first_batch)

        ready_no_vtk = temp / "ready_no_vtk"
        write_json(
            ready_no_vtk / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "PlannedSyntheticInletSamplingGate": {"Gate": "pass"},
                "PlannedVtkScheduleGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        ready_out = temp / "ready_plan.json"
        ready = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(ready_no_vtk),
            "--case-dir",
            "F:\\case",
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--solver-cwd",
            "C:\\CityLBM_native_runs\\casee",
            "--official",
            "F:\\RS_caseE.csv",
            "--af-csv",
            "F:\\AF_caseE.csv",
            "--out-json",
            str(ready_out),
        )
        if ready.returncode != 0:
            raise AssertionError((ready.returncode, ready.stdout, ready.stderr))
        ready_plan = load(ready_out)
        assert_phase(ready_plan, "launch_native_canary_or_resume_solver")
        if ready_plan["acceleration_summary"]["next_execution_policy"] != "run_short_native_canary_only":
            raise AssertionError(ready_plan["acceleration_summary"])
        if ready_plan["acceleration_summary"]["next_batch_name"] != "short_native_canary":
            raise AssertionError(ready_plan["acceleration_summary"])
        if "run_native_fluidx3d_case.py" not in ready_plan["acceleration_summary"]["next_command"]:
            raise AssertionError(ready_plan["acceleration_summary"])
        if "--expected-probe-row-count" not in ready_plan["command_templates"]["preflight_no_cfd"]:
            raise AssertionError(ready_plan["command_templates"])
        if "--require-af-k" not in ready_plan["command_templates"]["preflight_no_cfd"]:
            raise AssertionError(ready_plan["command_templates"])
        if "--solver-cwd" not in ready_plan["command_templates"]["diagnostic_canary_cfd"]:
            raise AssertionError(ready_plan["command_templates"])
        if "current_codegen_full_gate" not in ready_plan["command_templates"]:
            raise AssertionError(ready_plan["command_templates"])
        if "--quick" not in ready_plan["command_templates"].get("current_codegen_quick_gate", ""):
            raise AssertionError(ready_plan["command_templates"])
        if "--require-af-k" not in ready_plan["command_templates"]["current_codegen_full_gate"]:
            raise AssertionError(ready_plan["command_templates"])
        batches = ready_plan.get("parallel_batches", [])
        if not batches or batches[0]["name"] != "no_cfd_source_and_protocol_preflight":
            raise AssertionError(ready_plan)
        if batches[0]["runs_cfd"] is not False or batches[0]["can_run_in_parallel"] is not True:
            raise AssertionError(batches[0])
        first_batch_commands = "\n".join(batches[0].get("commands", []))
        for expected in [
            "scripts\\audit_inlet_source.py",
            "scripts\\create_boundary_protocol_evidence_template.py",
            "scripts\\create_inlet_reynolds_stress_template.py",
            "scripts\\create_turbulence_length_scale_evidence_template.py",
            "scripts\\bind_turbulence_length_scale_metadata.py",
            "scripts\\build_inlet_reynolds_stress_evidence.py",
            "scripts\\audit_boundary_source.py",
            "scripts\\audit_fluidx3d_equilibrium_boundary.py",
            "scripts\\audit_boundary_protocol.py",
            "scripts\\audit_coordinate_probe_protocol.py",
            "scripts\\write_validation_protocol_audit.py",
            "scripts\\run_native_fluidx3d_case.py",
            "--inlet-reynolds-stress-evidence",
            "--stress-csv",
            "--precursor-evidence",
            "--expected-aij-case",
            "--expected-wind-vector",
            "inlet_reynolds_stress_tensor_template.csv",
            "turbulence_length_scale_evidence.json",
            "case_metadata.length_scale_bound.json",
            "equivalent_precursor_evidence_template.json",
            "boundary_protocol_evidence_template.json",
            "src\\setup.cpp",
            "src\\defines.hpp",
        ]:
            if expected not in first_batch_commands:
                raise AssertionError((expected, batches[0]))
        if "inlet_source_velocity_field_only_without_distribution_reconstruction" not in batches[0].get("stop_if", []):
            raise AssertionError(batches[0])
        if "fluidx3d_type_e_ddf_route_not_proven" not in batches[0].get("stop_if", []):
            raise AssertionError(batches[0])
        if "coordinate_probe_protocol_or_Uref_identity_mismatch" not in batches[0].get("stop_if", []):
            raise AssertionError(batches[0])
        if batches[1]["name"] != "short_native_canary" or batches[1]["runs_cfd"] is not True:
            raise AssertionError(batches[1])
        if "audit_native_preconditions.py" not in "\n".join(batches[1].get("commands", [])):
            raise AssertionError(batches[1])
        if batches[2]["name"] != "paper_candidate_native_run":
            raise AssertionError(batches[2])

        ready_no_vtk_but_inlet_evidence_blocked = temp / "ready_no_vtk_but_inlet_evidence_blocked"
        write_json(
            ready_no_vtk_but_inlet_evidence_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "PlannedSyntheticInletSamplingGate": {"Gate": "pass"},
                "PlannedVtkScheduleGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_inlet_evidence_blocked / "preflight" / "inlet_source_audit.json",
            {
                "inlet_source_gate": "pass",
                "paper_grade_inlet_source_gate": "fail",
                "paper_grade_inlet_source_gate_reasons": [
                    "source_reynolds_stress_tensor_is_isotropic_k_assumption_only",
                ],
                "development_acceleration_stage": "resolve_reynolds_stress_tensor_or_precursor_evidence",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "source audit says the next step is evidence, not CFD",
            },
        )
        ready_inlet_out = temp / "ready_inlet_plan.json"
        ready_inlet = run_planner(
            "--case",
            "casea",
            "--run-dir",
            str(ready_no_vtk_but_inlet_evidence_blocked),
            "--out-json",
            str(ready_inlet_out),
        )
        if ready_inlet.returncode != 0:
            raise AssertionError((ready_inlet.returncode, ready_inlet.stdout, ready_inlet.stderr))
        ready_inlet_plan = load(ready_inlet_out)
        assert_phase(ready_inlet_plan, "resolve_reynolds_stress_offdiagonal_or_precursor_gap")
        if ready_inlet_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(ready_inlet_plan["recommended_sequence"][0])
        if "source audit says the next step is evidence" not in ready_inlet_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_inlet_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_length_scale_blocked = temp / "ready_no_vtk_but_length_scale_blocked"
        write_json(
            ready_no_vtk_but_length_scale_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_length_scale_blocked / "preflight" / "inlet_source_audit.json",
            {
                "inlet_source_gate": "pass",
                "paper_grade_inlet_source_gate": "fail",
                "paper_grade_inlet_source_gate_reasons": [
                    "source_missing_turbulent_length_scale_evidence",
                ],
                "development_acceleration_stage": "resolve_turbulent_length_scale_evidence",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "length-scale evidence is not bound to this case",
            },
        )
        ready_length_out = temp / "ready_length_plan.json"
        ready_length = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(ready_no_vtk_but_length_scale_blocked),
            "--out-json",
            str(ready_length_out),
        )
        if ready_length.returncode != 0:
            raise AssertionError((ready_length.returncode, ready_length.stdout, ready_length.stderr))
        ready_length_plan = load(ready_length_out)
        assert_phase(ready_length_plan, "resolve_turbulent_length_scale_evidence")
        length_summary = ready_length_plan["acceleration_summary"]
        if length_summary["next_execution_policy"] != "create_or_bind_turbulence_length_scale_evidence_before_cfd":
            raise AssertionError(length_summary)
        if "create_turbulence_length_scale_evidence_template.py" not in length_summary["next_command"]:
            raise AssertionError(length_summary)
        if "length-scale evidence is not bound" not in ready_length_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_length_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_boundary_source_blocked = temp / "ready_no_vtk_but_boundary_source_blocked"
        write_json(
            ready_no_vtk_but_boundary_source_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_boundary_source_blocked / "preflight" / "boundary_source_audit.json",
            {
                "boundary_source_gate": "pass",
                "paper_grade_boundary_source_gate": "fail",
                "development_acceleration_stage": "replace_simplified_type_e_box_boundary_before_cfd",
                "development_acceleration_duration_class": "code_then_short_cfd",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "boundary source says this is still a simplified TYPE_E box",
            },
        )
        ready_boundary_source_out = temp / "ready_boundary_source_plan.json"
        ready_boundary_source = run_planner(
            "--case",
            "casea",
            "--run-dir",
            str(ready_no_vtk_but_boundary_source_blocked),
            "--out-json",
            str(ready_boundary_source_out),
        )
        if ready_boundary_source.returncode != 0:
            raise AssertionError(
                (ready_boundary_source.returncode, ready_boundary_source.stdout, ready_boundary_source.stderr)
            )
        ready_boundary_source_plan = load(ready_boundary_source_out)
        assert_phase(ready_boundary_source_plan, "resolve_boundary_and_wall_protocol_evidence")
        if ready_boundary_source_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(ready_boundary_source_plan["recommended_sequence"][0])
        if "simplified TYPE_E box" not in ready_boundary_source_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_boundary_source_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_boundary_protocol_blocked = temp / "ready_no_vtk_but_boundary_protocol_blocked"
        write_json(
            ready_no_vtk_but_boundary_protocol_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_boundary_protocol_blocked / "preflight" / "boundary_protocol_audit.json",
            {
                "boundary_protocol_gate": "fail",
                "development_acceleration_stage": "fix_boundary_protocol_identity_before_cfd",
                "development_acceleration_duration_class": "minutes",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "boundary evidence is for the wrong case metadata hash",
            },
        )
        ready_boundary_protocol_out = temp / "ready_boundary_protocol_plan.json"
        ready_boundary_protocol = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(ready_no_vtk_but_boundary_protocol_blocked),
            "--out-json",
            str(ready_boundary_protocol_out),
        )
        if ready_boundary_protocol.returncode != 0:
            raise AssertionError(
                (ready_boundary_protocol.returncode, ready_boundary_protocol.stdout, ready_boundary_protocol.stderr)
            )
        ready_boundary_protocol_plan = load(ready_boundary_protocol_out)
        assert_phase(ready_boundary_protocol_plan, "resolve_boundary_and_wall_protocol_evidence")
        if ready_boundary_protocol_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(ready_boundary_protocol_plan["recommended_sequence"][0])
        if "wrong case metadata hash" not in ready_boundary_protocol_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_boundary_protocol_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_coordinate_blocked = temp / "ready_no_vtk_but_coordinate_blocked"
        write_json(
            ready_no_vtk_but_coordinate_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_coordinate_blocked / "preflight" / "coordinate_probe_protocol_audit.json",
            {
                "coordinate_probe_protocol_gate": "fail",
                "development_acceleration_stage": "fix_uref_normalization_before_cfd",
                "development_acceleration_duration_class": "minutes",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "Uref does not match the official AF profile",
            },
        )
        ready_coordinate_out = temp / "ready_coordinate_plan.json"
        ready_coordinate = run_planner(
            "--case",
            "casee",
            "--run-dir",
            str(ready_no_vtk_but_coordinate_blocked),
            "--out-json",
            str(ready_coordinate_out),
        )
        if ready_coordinate.returncode != 0:
            raise AssertionError((ready_coordinate.returncode, ready_coordinate.stdout, ready_coordinate.stderr))
        ready_coordinate_plan = load(ready_coordinate_out)
        assert_phase(ready_coordinate_plan, "resolve_coordinate_probe_uref_protocol")
        if ready_coordinate_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(ready_coordinate_plan["recommended_sequence"][0])
        if "official AF profile" not in ready_coordinate_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_coordinate_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_time_plan_blocked = temp / "ready_no_vtk_but_time_plan_blocked"
        write_json(
            ready_no_vtk_but_time_plan_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": False, "Gate": "not_requested"},
                "ActualVtkOutputGate": {"Gate": "not_applicable"},
            },
        )
        write_json(
            ready_no_vtk_but_time_plan_blocked / "preflight" / "time_averaging_evidence.json",
            {
                "Gate": "diagnostic_only",
                "development_acceleration_stage": "revise_time_averaging_schedule_before_cfd",
                "development_acceleration_duration_class": "minutes",
                "development_acceleration_runs_cfd_next": False,
                "development_acceleration_reason": "planned final window has only four VTK frames",
            },
        )
        ready_time_plan_out = temp / "ready_time_plan.json"
        ready_time_plan = run_planner(
            "--case",
            "casea",
            "--run-dir",
            str(ready_no_vtk_but_time_plan_blocked),
            "--out-json",
            str(ready_time_plan_out),
        )
        if ready_time_plan.returncode != 0:
            raise AssertionError((ready_time_plan.returncode, ready_time_plan.stdout, ready_time_plan.stderr))
        ready_time_plan_data = load(ready_time_plan_out)
        assert_phase(ready_time_plan_data, "verify_time_averaging_schedule")
        if ready_time_plan_data["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(ready_time_plan_data["recommended_sequence"][0])
        if "four VTK frames" not in ready_time_plan_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_time_plan_out.read_text(encoding="utf-8"))

        ready_no_vtk_but_actual_window_blocked = temp / "ready_no_vtk_but_actual_window_blocked"
        write_json(
            ready_no_vtk_but_actual_window_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": True, "Gate": "pass"},
                "ActualVtkOutputGate": {"Gate": "diagnostic_only"},
            },
        )
        write_json(
            ready_no_vtk_but_actual_window_blocked / "preflight" / "time_averaging_evidence.json",
            {
                "Gate": "diagnostic_only",
                "development_acceleration_stage": "collect_longer_actual_vtk_average_window",
                "development_acceleration_duration_class": "medium_cfd",
                "development_acceleration_runs_cfd_next": True,
                "development_acceleration_reason": "actual VTK window is too short after spin-up",
            },
        )
        ready_actual_window_out = temp / "ready_actual_window_plan.json"
        ready_actual_window = run_planner(
            "--case",
            "casea",
            "--run-dir",
            str(ready_no_vtk_but_actual_window_blocked),
            "--out-json",
            str(ready_actual_window_out),
        )
        if ready_actual_window.returncode != 0:
            raise AssertionError(
                (ready_actual_window.returncode, ready_actual_window.stdout, ready_actual_window.stderr)
            )
        ready_actual_window_plan = load(ready_actual_window_out)
        assert_phase(ready_actual_window_plan, "increase_time_averaging_before_physics_tuning")
        if ready_actual_window_plan["recommended_sequence"][0]["runs_cfd"] is not True:
            raise AssertionError(ready_actual_window_plan["recommended_sequence"][0])
        if "after spin-up" not in ready_actual_window_out.read_text(encoding="utf-8"):
            raise AssertionError(ready_actual_window_out.read_text(encoding="utf-8"))

        case_with_runtime = temp / "case_with_runtime"
        write_json(
            case_with_runtime / "case_metadata.json",
            {
                "TimeSteps": 60000,
                "VtkOutput": {
                    "SaveIntervalSteps": 1000,
                    "SaveStartStep": 10000,
                    "EstimatedPostSpinupFrameCount": 51,
                },
            },
        )
        runtime_out = temp / "runtime_plan.json"
        runtime_plan_result = run_planner(
            "--case",
            "casea",
            "--run-dir",
            str(ready_no_vtk),
            "--case-dir",
            str(case_with_runtime),
            "--fluidx3d-source",
            "F:\\FluidX3D",
            "--official",
            "F:\\RS_caseA.csv",
            "--af-csv",
            "F:\\AF_caseA.csv",
            "--out-json",
            str(runtime_out),
        )
        if runtime_plan_result.returncode != 0:
            raise AssertionError((runtime_plan_result.returncode, runtime_plan_result.stdout, runtime_plan_result.stderr))
        runtime_plan = load(runtime_out)
        runtime_preflight = runtime_plan["command_templates"]["preflight_no_cfd"]
        for expected in [
            '"--time-steps" "60000"',
            '"--vtk-save-start-step" "10000"',
            '"--expected-vtk-frame-count" "51"',
        ]:
            if expected not in runtime_preflight:
                raise AssertionError(runtime_plan["command_templates"])

        inlet_blocked = temp / "inlet_blocked"
        write_json(
            inlet_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": True, "Gate": "pass"},
                "ActualVtkOutputGate": {"Gate": "pass"},
            },
        )
        write_json(
            inlet_blocked / "validation_gate_report.json",
            {
                "verdict": "FAIL",
                "paper_grade": False,
                "gates": [
                    {
                        "key": "paper_grade_inlet_method",
                        "status": "FAIL",
                        "evidence": "velocity_field_only_no_distribution_function_reconstruction",
                    }
                ],
            },
        )
        inlet_out = temp / "inlet_plan.json"
        inlet = run_planner("--run-dir", str(inlet_blocked), "--out-json", str(inlet_out))
        if inlet.returncode != 0:
            raise AssertionError((inlet.returncode, inlet.stdout, inlet.stderr))
        assert_phase(load(inlet_out), "fix_turbulent_inlet_evidence")

        component_blocked = temp / "component_blocked"
        write_json(
            component_blocked / "native_fluidx3d_baseline_manifest.json",
            {
                "ValidationProtocolAuditGate": {"Gate": "pass"},
                "CaseMetadataPreconditionGate": {"Gate": "pass"},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass"},
                "OfficialInputPreconditionGate": {"Gate": "pass"},
                "PreExecutionGate": {"Gate": "pass"},
                "Run": {"Requested": True, "Gate": "pass"},
                "ActualVtkOutputGate": {"Gate": "pass"},
            },
        )
        write_json(
            component_blocked / "component_sensitivity_audit.json",
            {
                "component_source_window_gate": "pass",
                "component_normalization_gate": "fail",
                "component_sensitivity_gate": "pass",
                "normalization_scale_gate": "fail",
                "streamwise_sign_gate": "pass",
                "normalization_scale_gate_reasons": [
                    "mean_sim_to_exp_ratio_0.66_below_0.8_suggests_systematic_underprediction",
                    "best_fit_scale_1.52_suggests_uref_or_unit_error",
                ],
                "selected_component": "speed_ratio",
                "best_component_by_rmse": "speed_ratio",
                "selected_component_mean_sim_to_exp_ratio": 0.66,
                "selected_best_fit_scale_to_exp": 1.52,
            },
        )
        component_out = temp / "component_plan.json"
        component = run_planner("--run-dir", str(component_blocked), "--out-json", str(component_out))
        if component.returncode != 0:
            raise AssertionError((component.returncode, component.stdout, component.stderr))
        component_plan = load(component_out)
        assert_phase(component_plan, "fix_probe_component_normalization")
        if component_plan["recommended_sequence"][0]["runs_cfd"] is not False:
            raise AssertionError(component_plan["recommended_sequence"][0])
        component_text = component_out.read_text(encoding="utf-8")
        if "best_fit_scale_1.52_suggests_uref_or_unit_error" not in component_text:
            raise AssertionError(component_text)
        if not component_plan["runs"][0]["artifacts"]["component_sensitivity"].endswith(
            "component_sensitivity_audit.json"
        ):
            raise AssertionError(component_plan["runs"][0]["artifacts"])

        markdown_out = temp / "plan.md"
        md = run_planner("--case", "casee", "--run-dir", str(inlet_blocked), "--out-md", str(markdown_out))
        if md.returncode != 0:
            raise AssertionError((md.returncode, md.stdout, md.stderr))
        markdown = markdown_out.read_text(encoding="utf-8")
        if "CityLBM Validation Acceleration Plan" not in markdown:
            raise AssertionError(markdown)
        if "Parallel Development Batches" not in markdown:
            raise AssertionError(markdown)
        if "no_cfd_source_and_protocol_preflight" not in markdown:
            raise AssertionError(markdown)

    print("validation_acceleration_plan_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
