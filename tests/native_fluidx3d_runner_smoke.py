#!/usr/bin/env python3
"""Smoke-test the native FluidX3D runner manifest and install path."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(args: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def create_source(root: Path) -> None:
    write(root / "FluidX3D.sln", "Microsoft Visual Studio Solution File\n")
    write(root / "src" / "setup.cpp", "// original native setup\n")
    write(root / "src" / "defines.hpp", "// original native defines\n")
    write(root / "src" / "lbm.hpp", "// lbm header\n")
    write(root / "src" / "lbm.cpp", "// lbm source\n")


def create_case(root: Path) -> None:
    write(root / "src" / "setup.cpp", "// case setup\n")
    write(root / "src" / "defines.hpp", "// case defines\n")
    write(root / "case_metadata.json", json.dumps({"AijCase": "CaseA", "WindDirection": "N"}, indent=2))
    write(root / "domain_origin.json", json.dumps({"origin": [0, 0, 0]}, indent=2))
    write(root / "validation_protocol_audit.json", json.dumps({"items": []}, indent=2))
    write(root / "buildings.stl", "solid smoke\nendsolid smoke\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        dry_manifest = temp / "dry" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(dry_manifest),
                "--baseline-id",
                "smoke-casea-native",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "1000",
                "--vtk-save-interval",
                "100",
                "--expected-vtk-frame-count",
                "10",
            ]
        )
        dry = load_json(dry_manifest)
        if dry["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(dry["RunnerGate"])
        if dry["NativeFluidX3DPathExplicitlyProvided"] is not True:
            raise AssertionError("native path was not marked explicit")
        if dry["NativeFluidX3DSourceValidation"]["IsValid"] is not True:
            raise AssertionError(dry["NativeFluidX3DSourceValidation"])
        if dry["Install"]["Performed"] is not False:
            raise AssertionError(dry["Install"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// original native setup\n":
            raise AssertionError("dry-run modified source setup.cpp")
        roles = {record["Role"] for record in dry["RequiredSourceFiles"]}
        for role in [
            "Native FluidX3D original setup",
            "Native FluidX3D original defines",
            "Native FluidX3D lbm.hpp",
            "Native FluidX3D lbm.cpp",
            "FluidX3D setup",
            "FluidX3D defines",
            "Case metadata",
            "Domain origin",
            "Validation protocol audit",
        ]:
            if role not in roles:
                raise AssertionError(f"missing manifest role: {role}")

        install_manifest = temp / "install" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(install_manifest),
                "--baseline-id",
                "smoke-casea-native-install",
                "--install",
            ]
        )
        installed = load_json(install_manifest)
        if installed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(installed["RunnerGate"])
        if installed["Install"]["Performed"] is not True:
            raise AssertionError(installed["Install"])
        if len(installed["Install"]["Backups"]) != 2:
            raise AssertionError(installed["Install"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// case setup\n":
            raise AssertionError("install did not replace setup.cpp")
        if not (install_manifest.parent / "native_source_backups").exists():
            raise AssertionError("backup directory was not created")

    print("native_fluidx3d_runner_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
