#!/usr/bin/env python3
"""Smoke-test native empty-tunnel workflow orchestration."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_native_empty_tunnel_workflow.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def manifest(case_dir: Path, marker: Path, *, include_uref: bool) -> dict:
    output_dir = case_dir / "output"
    profile_json = case_dir / "inlet_profile_from_vtk.json"
    correlation_json = case_dir / "inlet_correlation_from_vtk.json"
    native_manifest = case_dir / "native_fluidx3d_baseline_manifest.json"
    validation_chain = case_dir / "validation_chain"
    chain_argv = [
        sys.executable,
        "run_native_validation_chain.py",
        str(case_dir),
        "--native-manifest",
        str(native_manifest),
        "--metadata",
        str(case_dir / "case_metadata.json"),
        "--official",
        str(case_dir / "RS-caseA.csv"),
        "--af-csv",
        str(case_dir / "AF_caseA.csv"),
        "--case",
        "CaseA",
        "--wind-vector",
        "1,0,0",
    ]
    if include_uref:
        chain_argv.extend(["--u-ref", "4.491"])
    return {
        "Schema": "citylbm.native_empty_tunnel_case.v1",
        "EmptyTunnelCaseDir": str(case_dir),
        "SetupPath": str(case_dir / "src" / "setup.cpp"),
        "Expected": {
            "ExpectedVtkFrameCount": 40,
            "MinVtkFrames": 40,
            "VtkPattern": "u-*.vtk",
        },
        "Commands": {
            "PreflightNoCfd": {
                "Argv": [
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path(r'{marker}').write_text('preflight', encoding='utf-8')",
                    "--case-dir",
                    str(case_dir),
                    "--fluidx3d-source",
                    str(case_dir / "FluidX3D"),
                    "--out-dir",
                    str(case_dir / "preflight"),
                    "--manifest-out",
                    str(native_manifest),
                ]
            },
            "InstallBuildRunFluidX3D": {
                "Argv": [
                    sys.executable,
                    "run_native_fluidx3d_case.py",
                    "--case-dir",
                    str(case_dir),
                    "--fluidx3d-source",
                    str(case_dir / "FluidX3D"),
                    "--out",
                    str(native_manifest),
                    "--install",
                    "--build",
                    "--run",
                    "--output-dir",
                    str(output_dir),
                ]
            },
            "AuditInletProfileAfterRun": {
                "Argv": [
                    sys.executable,
                    "audit_inlet_profile_from_vtk.py",
                    str(output_dir),
                    "--af-csv",
                    str(case_dir / "AF_caseA.csv"),
                    "--out-json",
                    str(profile_json),
                    "--average-last-n",
                    "40",
                    "--min-frames",
                    "40",
                    "--min-step-span",
                    "20000",
                ]
            },
            "AuditInletCorrelationAfterRun": {
                "Argv": [
                    sys.executable,
                    "audit_inlet_correlation_from_vtk.py",
                    str(output_dir),
                    "--out-json",
                    str(correlation_json),
                    "--average-last-n",
                    "40",
                    "--min-frames",
                    "40",
                    "--min-step-span",
                    "20000",
                ]
            },
            "ValidationChainAfterRun": {"Argv": chain_argv + ["--out-dir", str(validation_chain)]},
        },
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_empty_workflow_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        marker = temp / "preflight_marker.txt"
        manifest_path = temp / "empty_tunnel_manifest.json"
        report_path = temp / "status.json"
        write(case_dir / "src" / "setup.cpp", "void main_setup(){ const bool empty_tunnel = true; }\n")
        write(case_dir / "case_metadata.json", "{}\n")
        write(case_dir / "AF_caseA.csv", "z,U,k\n0.1,1.0,0.01\n")
        write(case_dir / "RS-caseA.csv", "No.,x,y,z,V\n1,0,0,0.02,1\n")
        write(manifest_path, json.dumps(manifest(case_dir, marker, include_uref=False), indent=2))

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--out-json", str(report_path)],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 3:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        report = load_json(report_path)
        status = report["Status"]
        if status["NextStage"] != "preflight":
            raise AssertionError(status)
        if status["LongRunRequired"] is not False:
            raise AssertionError(status)
        if not any("--u-ref" in item for item in status["CommandValidationErrors"]):
            raise AssertionError(status["CommandValidationErrors"])

        write(manifest_path, json.dumps(manifest(case_dir, marker, include_uref=True), indent=2))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--stage", "run", "--execute"],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 3 or "run_stage_requires_--allow-long-run" not in completed.stdout:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))

        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--stage", "preflight", "--execute"],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        if marker.read_text(encoding="utf-8") != "preflight":
            raise AssertionError("preflight command did not execute")

        preflight_manifest = case_dir / "preflight" / "native_preflight_pack_manifest.json"
        write(preflight_manifest, '{"Gate":"fail","Reasons":["coordinate_probe_gate_not_pass"]}\n')
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--out-json", str(report_path)],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        status = load_json(report_path)["Status"]
        if status["NextStage"] != "inspect_preflight_failures":
            raise AssertionError(status)

        write(preflight_manifest, '{"Gate":"pass","Reasons":[]}\n')
        output_dir = case_dir / "output"
        output_dir.mkdir(parents=True)
        for index in range(40):
            write(output_dir / f"u-{index + 1:09d}.vtk", "# vtk DataFile Version 3.0\n")
        write(case_dir / "inlet_profile_from_vtk.json", '{"inlet_profile_gate":"pass"}\n')
        write(case_dir / "inlet_correlation_from_vtk.json", '{"inlet_correlation_gate":"pass"}\n')
        chain_dir = case_dir / "validation_chain"
        write(chain_dir / "validation_chain_manifest.json", '{"ChainStatus":"pass"}\n')
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--manifest", str(manifest_path), "--out-json", str(report_path)],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        status = load_json(report_path)["Status"]
        if status["PaperGradeReady"] is not True:
            raise AssertionError(status)
        if status["NextStage"] != "building_case_can_start_after_boundary_preconditions":
            raise AssertionError(status)

    print("run_native_empty_tunnel_workflow_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
