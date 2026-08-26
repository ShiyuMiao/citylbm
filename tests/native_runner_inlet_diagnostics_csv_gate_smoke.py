#!/usr/bin/env python3
"""Smoke-test native runner ingestion of runtime inlet diagnostics CSV."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
sys.path.insert(0, str(REPO / "tests"))

from native_fluidx3d_runner_smoke import create_case, create_source, load_json, write  # noqa: E402


HEADER = (
    "step,profile_index,z_m,z_cell,target_U_mps,target_u_rms_mps,target_v_rms_mps,"
    "target_w_rms_mps,target_k_m2s2,mean_U_mps,mean_V_mps,mean_W_mps,u_rms_mps,"
    "v_rms_mps,w_rms_mps,k_m2s2,samples_y,effective_sample_z_cell,effective_sample_z_m\n"
)


def inlet_row(step: int, profile: int) -> str:
    target_u = 1.0 + profile * 0.25
    target_k = 0.05 + profile * 0.01
    return (
        f"{step},{profile},{0.1 + profile * 0.1:.3f},{profile},"
        f"{target_u},0.20,0.15,0.10,{target_k},{target_u * 1.01},0.01,0.01,"
        f"0.20,0.15,0.10,{target_k * 1.02},8,1.0,0.1\n"
    )


def run_cmd(cmd: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != expected_returncode:
        raise AssertionError((completed.returncode, completed.stdout, completed.stderr, cmd))
    return completed


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_runner_inlet_diag_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        source_root = temp / "FluidX3D"
        create_case(case_dir)
        create_source(source_root)

        inlet_csv = temp / "casea_inlet_turbulence_stats.csv"
        rows = [HEADER]
        for step in (1000, 2000, 3000):
            rows.append(inlet_row(step, 0))
            rows.append(inlet_row(step, 1))
        write(inlet_csv, "".join(rows))

        manifest = temp / "manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(manifest),
                "--baseline-id",
                "smoke-runner-inlet-diagnostics",
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
                "--inlet-diagnostics-csv",
                str(inlet_csv),
                "--require-af-k",
            ],
            expected_returncode=2,
        )
        result = load_json(manifest)
        gate = result["RuntimeInletDiagnosticsGate"]
        if gate["Gate"] != "pass":
            raise AssertionError(gate)
        if gate["ParsedAudit"]["ProfileCount"] != 2:
            raise AssertionError(gate)
        if result["PaperUseGate"]["Gate"] != "fail":
            raise AssertionError(result["PaperUseGate"])
        if "native_accuracy_evidence:native_run_not_requested" not in result["PaperUseGate"]["Reasons"]:
            raise AssertionError(result["PaperUseGate"])

        preconditions = temp / "native_preconditions_audit.json"
        run_cmd(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_native_preconditions.py"),
                str(case_dir),
                "--metadata",
                str(case_dir / "case_metadata.json"),
                "--manifest",
                str(manifest),
                "--out",
                str(preconditions),
            ],
            expected_returncode=2,
        )
        precondition_result = load_json(preconditions)
        if precondition_result["runtime_inlet_diagnostics_gate"] != "pass":
            raise AssertionError(precondition_result)
        if precondition_result["runtime_inlet_diagnostics_requested"] is not True:
            raise AssertionError(precondition_result)
        if precondition_result["runtime_inlet_diagnostics_csv_sha256"] != gate["CsvSha256"]:
            raise AssertionError(precondition_result)

        auto_case_dir = temp / "auto_case"
        auto_source_root = temp / "AutoFluidX3D"
        auto_output_dir = temp / "auto_output"
        create_case(auto_case_dir)
        create_source(auto_source_root)
        auto_output_dir.mkdir(parents=True, exist_ok=True)
        auto_csv = auto_output_dir / "auto_case_inlet_turbulence_stats.csv"
        auto_rows = [HEADER]
        for step in (1000, 2000, 3000):
            auto_rows.append(inlet_row(step, 0))
            auto_rows.append(inlet_row(step, 1))
        write(auto_csv, "".join(auto_rows))
        auto_metadata_path = auto_case_dir / "case_metadata.json"
        auto_metadata = load_json(auto_metadata_path)
        auto_metadata["RuntimeInletDiagnosticsCsv"] = auto_csv.name
        write(auto_metadata_path, json.dumps(auto_metadata, indent=2))

        auto_manifest = temp / "auto_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(auto_case_dir),
                "--fluidx3d-source",
                str(auto_source_root),
                "--out",
                str(auto_manifest),
                "--baseline-id",
                "smoke-runner-inlet-diagnostics-auto",
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
                "--output-dir",
                str(auto_output_dir),
                "--require-af-k",
            ],
            expected_returncode=2,
        )
        auto_result = load_json(auto_manifest)
        auto_resolution = auto_result["RuntimeInletDiagnosticsResolution"]
        if auto_resolution["Source"] != "metadata":
            raise AssertionError(auto_resolution)
        if auto_resolution["ExistingCandidate"] != str(auto_csv.resolve()):
            raise AssertionError(auto_resolution)
        auto_gate = auto_result["RuntimeInletDiagnosticsGate"]
        if auto_gate["Gate"] != "pass":
            raise AssertionError(auto_gate)
        if auto_gate["CsvPath"] != str(auto_csv.resolve()):
            raise AssertionError(auto_gate)

        run_case_dir = temp / "run_case"
        run_source_root = temp / "RunFluidX3D"
        solver_cwd = temp / "solver_cwd"
        create_case(run_case_dir)
        create_source(run_source_root)
        write(run_case_dir / "src" / "defines.hpp", "#define SX 4u\n#define SY 4u\n#define SZ 4u\n")
        solver_cwd.mkdir(parents=True, exist_ok=True)
        run_metadata_path = run_case_dir / "case_metadata.json"
        run_metadata = load_json(run_metadata_path)
        run_metadata["RuntimeInletDiagnosticsCsv"] = "output\\casea_inlet_turbulence_stats.csv"
        write(run_metadata_path, json.dumps(run_metadata, indent=2))
        fake_exe = temp / "fake_fluidx3d.cmd"
        write(
            fake_exe,
            (
                "@echo off\r\n"
                "if not exist output mkdir output\r\n"
                "echo # vtk DataFile Version 3.0> output\\u-000001000.vtk\r\n"
                "echo smoke 1000>> output\\u-000001000.vtk\r\n"
                "echo # vtk DataFile Version 3.0> output\\u-000002000.vtk\r\n"
                "echo smoke 2000>> output\\u-000002000.vtk\r\n"
                f"echo {HEADER.strip()}> output\\casea_inlet_turbulence_stats.csv\r\n"
                f"echo {inlet_row(1000, 0).strip()}>> output\\casea_inlet_turbulence_stats.csv\r\n"
                f"echo {inlet_row(1000, 1).strip()}>> output\\casea_inlet_turbulence_stats.csv\r\n"
                f"echo {inlet_row(2000, 0).strip()}>> output\\casea_inlet_turbulence_stats.csv\r\n"
                f"echo {inlet_row(2000, 1).strip()}>> output\\casea_inlet_turbulence_stats.csv\r\n"
            ),
        )
        run_manifest = temp / "run_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(run_case_dir),
                "--fluidx3d-source",
                str(run_source_root),
                "--solver-cwd",
                str(solver_cwd),
                "--out",
                str(run_manifest),
                "--baseline-id",
                "smoke-runner-inlet-diagnostics-after-run",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "2000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "2",
                "--average-last-n",
                "2",
                "--min-vtk-frames",
                "2",
                "--min-vtk-step-span",
                "1000",
                "--min-stg-refreshes",
                "1",
                "--exe",
                str(fake_exe),
                "--run",
                "--allow-diagnostic-execution",
                "--require-af-k",
            ],
            expected_returncode=2,
        )
        run_result = load_json(run_manifest)
        pre_reasons = run_result["PreExecutionGate"]["Reasons"]
        if "runtime_inlet_diagnostics_csv_missing" in pre_reasons:
            raise AssertionError(run_result["PreExecutionGate"])
        if "run_requested_without_runtime_inlet_diagnostics_path" in pre_reasons:
            raise AssertionError(run_result["PreExecutionGate"])
        if run_result["Run"]["Gate"] != "pass":
            raise AssertionError(run_result["Run"])
        run_gate = run_result["RuntimeInletDiagnosticsGate"]
        if run_gate["Gate"] != "pass":
            raise AssertionError(run_gate)
        if run_gate["CsvPath"] != str((solver_cwd / "output" / "casea_inlet_turbulence_stats.csv").resolve()):
            raise AssertionError(run_gate)

    print("native_runner_inlet_diagnostics_csv_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
