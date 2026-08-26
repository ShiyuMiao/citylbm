#!/usr/bin/env python3
"""Smoke-test the no-CFD native preflight evidence package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PREFLIGHT = REPO / "scripts" / "run_native_preflight_pack.py"
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "scripts"))

from native_fluidx3d_runner_smoke import create_case, create_source, load_json  # noqa: E402
from run_native_preflight_pack import (  # noqa: E402
    build_development_triage,
    build_diagnostic_canary_gate,
    build_next_optimization_target,
)


def run_preflight(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PREFLIGHT), *args],
        cwd=str(REPO),
        text=True,
        capture_output=True,
        encoding="utf-8",
    )


def require_artifacts(manifest: dict, keys: list[str]) -> None:
    artifacts = manifest["Artifacts"]
    for key in keys:
        path = Path(artifacts[key])
        if not path.is_file():
            raise AssertionError(f"missing artifact {key}: {path}")


def value_after(command: list[str], flag: str) -> str:
    return command[command.index(flag) + 1]


def canary_gate_fixture(*, current_codegen_route: bool) -> dict:
    return {
        "InletSourceAudit": {
            "inlet_source_gate": "pass",
            "runtime_inlet_diagnostics_source_gate": "pass",
            "paper_grade_inlet_source_gate": "fail",
            "paper_grade_inlet_source_gate_reasons": [
                "source_reynolds_stress_tensor_is_isotropic_k_assumption_only"
            ],
            "short_canary_allowed_by_codegen_route": current_codegen_route,
            "setup_inlet_codegen_route": (
                "current_citylbm_stg_layerwise_type_e_route"
                if current_codegen_route
                else "legacy_runtime_diagnostic_patch_route"
            ),
        },
        "InletReynoldsStressEvidence": {
            "source_type": "isotropic_from_k",
            "gate": "pass",
            "paper_grade_gate": "fail",
        },
        "BoundarySourceAudit": {
            "boundary_source_coherent": True,
            "has_type_e_velocity_initialization_before_device_upload": True,
            "boundary_source_gate": "pass",
            "paper_grade_boundary_source_gate": "fail",
        },
        "FluidX3DEquilibriumBoundaryAudit": {"Gate": "pass"},
        "CoordinateProbeProtocolAudit": {"coordinate_probe_protocol_gate": "pass"},
        "TimeAveragingEvidence": {"Gate": "diagnostic_only"},
        "ValidationProtocolAudit": {
            "PreRunGate": "diagnostic_only",
            "PaperGradeGate": "fail",
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_preflight_pack_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        source_root = temp / "FluidX3D"
        out_dir = temp / "preflight"
        create_case(case_dir)
        create_source(source_root)

        completed = run_preflight(
            [
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--solver-cwd",
                str(temp / "SolverCwd"),
                "--out-dir",
                str(out_dir),
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "1,0,0",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--require-af-k",
            ]
        )
        if completed.returncode != 2:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))

        manifest = load_json(out_dir / "native_preflight_pack_manifest.json")
        if manifest["Gate"] != "diagnostic_only":
            raise AssertionError(json.dumps(manifest, indent=2))
        execution = manifest.get("Execution", {})
        if execution.get("Mode") != "parallel_no_cfd_preflight":
            raise AssertionError(execution)
        if execution.get("InitialParallelStepCount", 0) < 5:
            raise AssertionError(execution)

        required = [
            "InletSourceAudit",
            "InletReynoldsStressEvidence",
            "BoundarySourceAudit",
            "FluidX3DEquilibriumBoundaryAudit",
            "DiagnosticFluidX3DSourcePatch",
            "DiagnosticDdfReconstructionRoute",
            "DiagnosticFluidX3DEquilibriumBoundaryAudit",
            "BoundaryProtocolEvidenceTemplate",
            "BoundaryProtocolAudit",
            "CoordinateProbeBoundMetadata",
            "InletBoundMetadata",
            "CoordinateProbeProtocolAudit",
            "InletReynoldsStressTensorTemplate",
            "EquivalentPrecursorEvidenceTemplate",
            "TurbulenceLengthScaleEvidence",
            "TimeAveragingEvidence",
            "ValidationProtocolAudit",
            "LegacyRuntimeInletDiagnosticsPatch",
            "NativeFluidX3DManifest",
            "DiagnosticCanaryCaseManifest",
            "DiagnosticSolverSourceManifest",
            "NativePreconditionsAudit",
        ]
        require_artifacts(manifest, required)

        step_names = [step["Name"] for step in manifest["Steps"]]
        for expected in [
            "bind_coordinate_probe_protocol_metadata",
            "audit_boundary_source",
            "audit_fluidx3d_equilibrium_boundary",
            "create_boundary_protocol_evidence_template",
            "audit_coordinate_probe_protocol",
            "create_inlet_reynolds_stress_template",
            "create_turbulence_length_scale_evidence",
            "build_time_averaging_evidence",
            "bind_turbulence_length_scale_metadata",
            "bind_inlet_reynolds_stress_metadata",
            "patch_legacy_runtime_inlet_diagnostics",
            "audit_inlet_source",
            "audit_boundary_protocol",
            "build_inlet_reynolds_stress_evidence",
            "write_validation_protocol_audit",
            "run_native_fluidx3d_case_preflight",
            "prepare_native_diagnostic_canary_case",
            "prepare_native_diagnostic_solver_source",
            "patch_diagnostic_fluidx3d_equilibrium_boundary_source",
            "enable_diagnostic_ddf_reconstruction_route",
            "audit_diagnostic_fluidx3d_equilibrium_boundary",
            "audit_native_preconditions",
        ]:
            if expected not in step_names:
                raise AssertionError(step_names)

        native_step = next(step for step in manifest["Steps"] if step["Name"] == "run_native_fluidx3d_case_preflight")
        artifacts = manifest["Artifacts"]
        if native_step["Command"][native_step["Command"].index("--metadata") + 1] != artifacts["InletBoundMetadata"]:
            raise AssertionError(native_step)
        if native_step["Command"][native_step["Command"].index("--boundary-source-audit") + 1] != artifacts["BoundarySourceAudit"]:
            raise AssertionError(native_step)
        if "--require-af-k" not in native_step["Command"]:
            raise AssertionError(native_step)
        time_averaging = load_json(Path(artifacts["TimeAveragingEvidence"]))
        if time_averaging["Gate"] != "pass":
            raise AssertionError(time_averaging)
        if time_averaging["PlannedVtkScheduleGate"]["ComputedFrameCount"] != 40:
            raise AssertionError(time_averaging["PlannedVtkScheduleGate"])

        patch_manifest = load_json(Path(artifacts["LegacyRuntimeInletDiagnosticsPatch"]))
        if patch_manifest["Gate"] not in ("pass", "fail"):
            raise AssertionError(patch_manifest)
        solver_source_manifest = load_json(Path(artifacts["DiagnosticSolverSourceManifest"]))
        if solver_source_manifest["Gate"] != "pass":
            raise AssertionError(solver_source_manifest)
        if solver_source_manifest["PlatformToolsetPatch"]["Gate"] != "pass":
            raise AssertionError(solver_source_manifest["PlatformToolsetPatch"])
        triage = manifest.get("DevelopmentTriage", {})
        if triage.get("Schema") != "citylbm.native_preflight_development_triage.v1":
            raise AssertionError(triage)
        if triage.get("LongCfdAllowedNow") is not False or triage.get("PaperGradeBlocked") is not True:
            raise AssertionError(triage)
        if "ExternalEvidenceRequired" not in triage:
            raise AssertionError(triage)
        auto_fix_names = [item.get("Name") for item in triage.get("AutomaticCodeFixes", [])]
        if "legacy_runtime_inlet_diagnostics_patch" not in auto_fix_names:
            raise AssertionError(triage)
        if "diagnostic_fluidx3d_ddf_reconstruction_route" not in auto_fix_names:
            raise AssertionError(triage)
        if triage.get("ShortDiagnosticCanaryAllowed") and not triage.get("SuggestedCommands"):
            raise AssertionError(triage)
        if "InletCorrelationAudit" not in manifest.get("Artifacts", {}):
            raise AssertionError(manifest.get("Artifacts", {}))
        suggested_names = [item.get("Name") for item in triage.get("SuggestedCommands", [])]
        if triage.get("ShortDiagnosticCanaryAllowed") and "audit_inlet_correlation_after_canary" not in suggested_names:
            raise AssertionError(triage)
        suggested = {item.get("Name"): item.get("Command", []) for item in triage.get("SuggestedCommands", [])}
        generated_prepare_cmd = suggested.get("prepare_native_diagnostic_canary_case")
        if generated_prepare_cmd:
            if value_after(generated_prepare_cmd, "--time-steps") != "500":
                raise AssertionError(generated_prepare_cmd)
            if value_after(generated_prepare_cmd, "--spinup-steps") != "100":
                raise AssertionError(generated_prepare_cmd)
            if value_after(generated_prepare_cmd, "--vtk-save-interval") != "100":
                raise AssertionError(generated_prepare_cmd)
            if value_after(generated_prepare_cmd, "--average-last-n") != "5":
                raise AssertionError(generated_prepare_cmd)
            if value_after(generated_prepare_cmd, "--synthetic-turbulence-temporal-step-scale") != "1.5":
                raise AssertionError(generated_prepare_cmd)
        generated_canary_cmd = suggested.get("run_native_diagnostic_canary")
        if generated_canary_cmd:
            if value_after(generated_canary_cmd, "--expected-vtk-frame-count") != "5":
                raise AssertionError(generated_canary_cmd)
            if value_after(generated_canary_cmd, "--average-last-n") != "5":
                raise AssertionError(generated_canary_cmd)
            if value_after(generated_canary_cmd, "--min-vtk-frames") != "5":
                raise AssertionError(generated_canary_cmd)
        generated_correlation_cmd = suggested.get("audit_inlet_correlation_after_canary")
        if generated_correlation_cmd:
            if value_after(generated_correlation_cmd, "--average-last-n") != "5":
                raise AssertionError(generated_correlation_cmd)
            if value_after(generated_correlation_cmd, "--min-frames") != "5":
                raise AssertionError(generated_correlation_cmd)
        next_target = manifest.get("NextOptimizationTarget", {})
        if next_target.get("Schema") != "citylbm.next_optimization_target.v1":
            raise AssertionError(next_target)
        if next_target != triage.get("NextOptimizationTarget"):
            raise AssertionError((next_target, triage.get("NextOptimizationTarget")))
        if not next_target.get("Key"):
            raise AssertionError(next_target)

        auto_case_dir = temp / "auto_case"
        auto_out_dir = temp / "auto_preflight"
        create_case(auto_case_dir, time_steps=60000)
        auto_af = temp / "official" / "AF_caseA.csv"
        auto_rs = temp / "official" / "RS_caseA.csv"
        auto_af.parent.mkdir(parents=True, exist_ok=True)
        auto_af.write_text("z,U,k\n0.0,1.0,0.10\n0.1,1.5,0.12\n", encoding="utf-8")
        auto_rs.write_text("No,x,y,z,V_exp_ratio\n1,0,0,0.02,1.0\n", encoding="utf-8")
        auto_metadata_path = auto_case_dir / "case_metadata.json"
        auto_metadata = load_json(auto_metadata_path)
        auto_metadata["TimeSteps"] = 60000
        auto_metadata["OfficialAF"] = str(auto_af)
        auto_metadata["OfficialRS"] = str(auto_rs)
        auto_metadata["VtkOutput"] = {
            "SaveIntervalSteps": 1000,
            "SaveStartStep": 10000,
            "EstimatedPostSpinupFrameCount": 51,
        }
        auto_metadata_path.write_text(json.dumps(auto_metadata, indent=2), encoding="utf-8")
        auto_completed = run_preflight(
            [
                "--case-dir",
                str(auto_case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out-dir",
                str(auto_out_dir),
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "1,0,0",
                "--require-af-k",
            ]
        )
        if auto_completed.returncode != 2:
            raise AssertionError((auto_completed.returncode, auto_completed.stdout, auto_completed.stderr))
        auto_manifest = load_json(auto_out_dir / "native_preflight_pack_manifest.json")
        auto_plan = auto_manifest["TimeAveragingPlan"]
        if auto_plan["TimeSteps"] != 60000 or auto_plan["ExpectedVtkFrameCount"] != 51:
            raise AssertionError(auto_plan)
        if auto_manifest["OfficialInputPlan"]["AfCsv"] != str(auto_af):
            raise AssertionError(auto_manifest["OfficialInputPlan"])
        if auto_manifest["OfficialInputPlan"]["Official"] != str(auto_rs):
            raise AssertionError(auto_manifest["OfficialInputPlan"])

        triage_allowed = build_development_triage(
            {"LegacyRuntimeInletDiagnosticsPatch": {"Gate": "pass", "Setup": str(case_dir / "setup.cpp")}},
            {"Gate": "pass"},
            ["paper_grade_blocker"],
            diagnostic_canary_case_command=[sys.executable, "prepare_native_diagnostic_canary_case.py"],
            diagnostic_canary_command=[
                sys.executable,
                "run_native_fluidx3d_case.py",
                "--out",
                str(out_dir / "native_diagnostic_canary_manifest.json"),
                "--inlet-diagnostics-csv",
                str(temp / "SolverCwd" / "citylbm_inlet_turbulence_stats.csv"),
                "--install",
                "--build",
                "--run",
                "--disable-graphics-for-run",
                "--allow-diagnostic-execution",
                "--platform-toolset",
                "v143",
            ],
            inlet_diagnostics_audit_command=[sys.executable, "audit_inlet_diagnostics_csv.py", "citylbm_inlet_turbulence_stats.csv"],
            inlet_correlation_audit_command=[
                sys.executable,
                "audit_inlet_correlation_from_vtk.py",
                "output",
                "--out-json",
                "inlet_correlation_audit.json",
            ],
        )
        suggested = {item.get("Name"): item.get("Command", []) for item in triage_allowed.get("SuggestedCommands", [])}
        if "prepare_native_diagnostic_canary_case" not in suggested:
            raise AssertionError(triage_allowed)
        canary_cmd = suggested.get("run_native_diagnostic_canary")
        if not canary_cmd:
            raise AssertionError(triage_allowed)
        for flag in ["--install", "--build", "--run", "--disable-graphics-for-run", "--allow-diagnostic-execution"]:
            if flag not in canary_cmd:
                raise AssertionError(canary_cmd)
        if "audit_runtime_inlet_diagnostics_after_canary" not in suggested:
            raise AssertionError(triage_allowed)
        if "audit_inlet_correlation_after_canary" not in suggested:
            raise AssertionError(triage_allowed)

        current_codegen_gate = build_diagnostic_canary_gate(
            canary_gate_fixture(current_codegen_route=True)
        )
        if current_codegen_gate["Gate"] != "pass":
            raise AssertionError(current_codegen_gate)
        source_first_target = build_next_optimization_target(
            {
                "native_diagnostic_priority": [
                    {
                        "rank": 0,
                        "key": "turbulent_inlet_method_and_u_k_preservation",
                        "reason_count": 2,
                        "reasons": ["inlet_source_velocity_field_only_not_false:True"],
                        "diagnosis": "inlet first",
                        "next_action": "fix inlet source",
                    }
                ],
                "native_rerun_prescription_experiment": "native_empty_tunnel_inlet_canary",
                "native_accuracy_interpretation_allowed": False,
                "native_accuracy_interpretation_gate": "fail",
            },
            current_codegen_gate,
        )
        if source_first_target["Key"] != "turbulent_inlet_method_and_u_k_preservation":
            raise AssertionError(source_first_target)
        if source_first_target["ShortDiagnosticCanaryAllowed"] is not True:
            raise AssertionError(source_first_target)
        if source_first_target["AccuracyInterpretationAllowed"] is not False:
            raise AssertionError(source_first_target)
        diagnostic_boundary_gate = build_diagnostic_canary_gate(
            {
                **canary_gate_fixture(current_codegen_route=True),
                "FluidX3DEquilibriumBoundaryAudit": {
                    "Gate": "fail",
                    "Reasons": ["original_source_not_case_enabled"],
                },
                "DiagnosticDdfReconstructionRoute": {"Gate": "pass", "Reasons": []},
            }
        )
        if diagnostic_boundary_gate["Gate"] != "pass":
            raise AssertionError(diagnostic_boundary_gate)
        if (
            diagnostic_boundary_gate["EvidenceUseClass"].get("ShortCanaryBoundaryGateSource")
            != "DiagnosticDdfReconstructionRoute"
        ):
            raise AssertionError(diagnostic_boundary_gate)

        legacy_codegen_gate = build_diagnostic_canary_gate(
            canary_gate_fixture(current_codegen_route=False)
        )
        if legacy_codegen_gate["Gate"] != "fail":
            raise AssertionError(legacy_codegen_gate)
        if (
            "setup_codegen_route_not_current_citylbm:legacy_runtime_diagnostic_patch_route"
            not in legacy_codegen_gate["Reasons"]
        ):
            raise AssertionError(legacy_codegen_gate)

    print("native_preflight_pack_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
