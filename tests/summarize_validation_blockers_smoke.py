#!/usr/bin/env python3
"""Smoke-test the compact validation blocker summary CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "summarize_validation_blockers.py"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_summary(run_dir: Path, fail_on_blockers: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--run-dir", str(run_dir)]
    if fail_on_blockers:
        command.append("--fail-on-blockers")
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        write_json(
            run_dir / "native_fluidx3d_baseline_manifest.json",
            {
                "RunnerGate": {"Gate": "pass", "Reasons": []},
                "NativeAccuracyEvidenceGate": {
                    "Gate": "fail",
                    "Reasons": [
                        "native_run_not_requested",
                        "actual_vtk_output_gate_not_pass:not_applicable",
                    ],
                },
                "ValidationProtocolAuditGate": {
                    "Gate": "pass",
                    "PreRunGate": "ready_for_validation_run",
                    "PaperGradeGate": "diagnostic_only",
                    "Reasons": [],
                },
                "CaseMetadataPreconditionGate": {"Gate": "pass", "Reasons": []},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass", "Reasons": []},
                "OfficialInputPreconditionGate": {"Gate": "pass", "Reasons": []},
                "PlannedSyntheticInletSamplingGate": {"Gate": "pass", "Reasons": []},
                "RuntimeInletDiagnosticsGate": {"Gate": "not_applicable", "Reasons": []},
                "PlannedVtkScheduleGate": {
                    "Gate": "pass",
                    "RecommendedAverageLastNForStepSpan": 40,
                    "FinalWindowStepSpan": 39000,
                    "Reasons": [],
                },
                "ActualVtkOutputGate": {"Gate": "not_applicable", "Reasons": []},
                "SharedRunConditions": {
                    "RecommendedMinimumTimeStepsForCurrentSaveInterval": 40000
                },
            },
        )
        write_json(
            run_dir / "native_preconditions_audit.json",
            {
                "native_preconditions_gate": "fail",
                "accuracy_interpretation_gate": "fail",
                "native_precondition_closure_gate": "fail",
                "native_top_blocking_priority_key": "coordinate_component_normalization",
                "native_top_blocking_priority_diagnosis": "Probe coordinates or velocity component mismatch.",
                "native_top_blocking_priority_next_action": "Recompute official probe mapping and streamwise sign.",
                "native_top_blocking_priority_reasons": [
                    "streamwise_sign_gate_not_pass:fail",
                    "max_official_coordinate_delta_m_above_tolerance",
                ],
            },
        )
        write_json(
            run_dir / "validation_gate_report.json",
            {
                "verdict": "FAIL",
                "paper_grade": False,
                "diagnostic_priority": [
                    {
                        "key": "native_fluidx3d_baseline",
                        "diagnosis": "Native baseline has not closed prerequisite gates.",
                        "required_next_action": "Run native FluidX3D Case A baseline first.",
                    }
                ],
                "gates": [
                    {
                        "key": "paper_grade_inlet_method",
                        "status": "FAIL",
                        "evidence": "AF k column is not preserved as turbulent inlet evidence.",
                    }
                ],
            },
        )

        fail_result = run_summary(run_dir, fail_on_blockers=True)
        if fail_result.returncode != 2:
            raise AssertionError((fail_result.returncode, fail_result.stdout, fail_result.stderr))
        required = [
            "Native runner manifest:",
            "recommended minimum steps for current save interval: 40000",
            "recommended AverageLastN: 40",
            "setup source preconditions: pass",
            "official input preconditions: pass",
            "protocol pre-run gate: ready_for_validation_run",
            "protocol paper-grade gate: diagnostic_only",
            "accelerated next stage: preflight is clean enough to launch the real FluidX3D run",
            "native_run_not_requested",
            "Native preconditions:",
            "top blocker: coordinate_component_normalization",
            "streamwise_sign_gate_not_pass:fail",
            "Validation gate:",
            "top diagnostic: native_fluidx3d_baseline",
            "paper_grade_inlet_method: FAIL",
        ]
        for text in required:
            if text not in fail_result.stdout:
                raise AssertionError((text, fail_result.stdout))

        summary_result = run_summary(run_dir)
        if summary_result.returncode != 0:
            raise AssertionError((summary_result.returncode, summary_result.stderr))
        if "paper grade: false" not in summary_result.stdout:
            raise AssertionError(summary_result.stdout)

        diagnostic_dir = run_dir / "diagnostic_only"
        diagnostic_dir.mkdir()
        write_json(
            diagnostic_dir / "native_fluidx3d_baseline_manifest.json",
            {
                "RunnerGate": {"Gate": "diagnostic_only", "Reasons": ["protocol_not_closed"]},
                "NativeAccuracyEvidenceGate": {"Gate": "not_applicable", "Reasons": []},
                "ValidationProtocolAuditGate": {"Gate": "diagnostic_only", "Reasons": []},
                "CaseMetadataPreconditionGate": {"Gate": "pass", "Reasons": []},
                "CaseSetupSourcePreconditionGate": {
                    "Gate": "diagnostic_only",
                    "Reasons": ["case_setup_source_not_customtable"],
                },
                "OfficialInputPreconditionGate": {
                    "Gate": "diagnostic_only",
                    "Reasons": ["official:official_z_mismatch_count_80"],
                },
                "PlannedSyntheticInletSamplingGate": {"Gate": "pass", "Reasons": []},
                "RuntimeInletDiagnosticsGate": {"Gate": "pass", "Reasons": []},
                "PlannedVtkScheduleGate": {"Gate": "pass", "Reasons": []},
                "ActualVtkOutputGate": {"Gate": "not_applicable", "Reasons": []},
            },
        )
        diagnostic_result = run_summary(diagnostic_dir, fail_on_blockers=True)
        if diagnostic_result.returncode != 2:
            raise AssertionError(
                (diagnostic_result.returncode, diagnostic_result.stdout, diagnostic_result.stderr)
            )
        if "runner gate: diagnostic_only" not in diagnostic_result.stdout:
            raise AssertionError(diagnostic_result.stdout)
        if "setup source preconditions: diagnostic_only" not in diagnostic_result.stdout:
            raise AssertionError(diagnostic_result.stdout)
        if "official input preconditions: diagnostic_only" not in diagnostic_result.stdout:
            raise AssertionError(diagnostic_result.stdout)

        runtime_inlet_dir = run_dir / "runtime_inlet_failed"
        runtime_inlet_dir.mkdir()
        write_json(
            runtime_inlet_dir / "native_fluidx3d_baseline_manifest.json",
            {
                "RunnerGate": {"Gate": "pass", "Reasons": []},
                "NativeAccuracyEvidenceGate": {"Gate": "fail", "Reasons": []},
                "ValidationProtocolAuditGate": {"Gate": "pass", "Reasons": []},
                "CaseMetadataPreconditionGate": {"Gate": "pass", "Reasons": []},
                "CaseSetupSourcePreconditionGate": {"Gate": "pass", "Reasons": []},
                "OfficialInputPreconditionGate": {"Gate": "pass", "Reasons": []},
                "PlannedSyntheticInletSamplingGate": {"Gate": "pass", "Reasons": []},
                "RuntimeInletDiagnosticsGate": {
                    "Gate": "fail",
                    "Reasons": ["mean_u_rel_error_above_0.1", "k_rel_error_above_0.35"],
                },
                "PlannedVtkScheduleGate": {"Gate": "pass", "Reasons": []},
                "ActualVtkOutputGate": {"Gate": "pass", "Reasons": []},
            },
        )
        runtime_result = run_summary(runtime_inlet_dir, fail_on_blockers=True)
        if runtime_result.returncode != 2:
            raise AssertionError((runtime_result.returncode, runtime_result.stdout, runtime_result.stderr))
        for text in [
            "runtime inlet diagnostics: fail",
            "fix runtime inlet U/k/RMS preservation with short canaries",
            "mean_u_rel_error_above_0.1",
        ]:
            if text not in runtime_result.stdout:
                raise AssertionError((text, runtime_result.stdout))

    print("summarize_validation_blockers_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
