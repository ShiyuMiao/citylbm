#!/usr/bin/env python3
"""Smoke-test metadata-derived validation protocol audit writing."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WRITER = REPO / "scripts" / "write_validation_protocol_audit.py"
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
    write(root / "src" / "setup.cpp", "// native setup\n")
    write(root / "src" / "defines.hpp", "// native defines\n")
    write(root / "src" / "lbm.hpp", "// lbm header\n")
    write(root / "src" / "lbm.cpp", "// lbm source\n")


def create_case(root: Path) -> None:
    write(root / "src" / "setup.cpp", "// case setup\n")
    write(root / "src" / "defines.hpp", "// case defines\n")
    write(root / "domain_origin.json", json.dumps({"origin": [0, 0, 0]}, indent=2))
    write(root / "buildings.stl", "solid smoke\nendsolid smoke\n")
    metadata = {
        "EvidenceType": "generated_case_not_run",
        "Case": "AIJ Case A native FluidX3D strict baseline",
        "OfficialAF": "official/AF_caseA.csv",
        "OfficialAFSha256": "A" * 64,
        "OfficialRSSha256": "B" * 64,
        "Dx": 0.006,
        "ProbeCount": 186,
        "Uref": 4.491,
        "Zref": 0.16,
        "Tau": 0.500333333333333,
        "ReH": 24000.0,
        "TargetReH": 24000.0,
        "TurbulenceMethod": "synthetic-eddy",
        "TurbulenceScale": 1.0,
        "InletUpdateInterval": 1,
        "BoundaryMode": "side_periodic_top_profile_e",
        "BoundaryProtocol": {
            "PaperBoundaryAdmissible": False,
            "BoundarySourceDocumented": False,
        },
        "RoughnessLayout": {
            "PaperSourceAdmissible": False,
        },
        "EquivalentPrecursor": {
            "PaperAdmissible": False,
        },
        "VtkOutput": {
            "SaveIntervalSteps": 1000,
            "SaveStartStep": 10000,
            "EstimatedPostSpinupFrameCount": 51,
        },
    }
    write(root / "case_metadata.json", json.dumps(metadata, indent=2))


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source = temp / "FluidX3D"
        case = temp / "case"
        create_source(source)
        create_case(case)

        run_cmd(
            [
                sys.executable,
                str(WRITER),
                "--case-dir",
                str(case),
                "--case",
                "CaseA",
                "--wind-direction-label",
                "N",
                "--wind-vector",
                "1,0,0",
                "--patch-metadata-identity",
            ]
        )

        audit = load_json(case / "validation_protocol_audit.json")
        if audit["Gate"] != "diagnostic_only":
            raise AssertionError(audit)
        if audit["MetadataIdentityPatched"] is not True:
            raise AssertionError(audit)
        statuses = {item["Key"]: item["Status"] for item in audit["Items"]}
        for key in audit["RequiredItemKeys"]:
            if key not in statuses:
                raise AssertionError((key, audit))
        if statuses["wind_direction_sign"] != "pass":
            raise AssertionError(statuses)
        for key in ["native_fluidx3d_baseline", "boundary_conditions", "wall_roughness_model", "systematic_bias_gate"]:
            if statuses[key] != "fail":
                raise AssertionError((key, statuses))

        metadata = load_json(case / "case_metadata.json")
        if metadata["AijCase"] != "CaseA" or metadata["WindDirection"] != "N":
            raise AssertionError(metadata)
        if metadata["WindDirectionUnitVector"] != [1.0, 0.0, 0.0]:
            raise AssertionError(metadata)

        manifest = temp / "native_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case),
                "--fluidx3d-source",
                str(source),
                "--out",
                str(manifest),
                "--baseline-id",
                "write-protocol-smoke",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "60000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "51",
            ],
            expected_returncode=2,
        )
        result = load_json(manifest)
        reasons = result["RunnerGate"]["Reasons"]
        for forbidden in [
            "case_required_file_missing:Validation protocol audit",
            "validation_protocol_audit_missing_or_empty",
            "wind_direction_missing_in_metadata",
        ]:
            if forbidden in reasons:
                raise AssertionError((forbidden, reasons))
        for expected in [
            "validation_protocol_audit_gate_not_paper_grade:diagnostic_only",
            "validation_protocol_item_fail:boundary_conditions",
            "validation_protocol_item_fail:wall_roughness_model",
            "validation_protocol_item_fail:native_fluidx3d_baseline",
        ]:
            if expected not in reasons:
                raise AssertionError((expected, reasons))
        if result["SharedRunConditions"]["ComputedVtkFrameCount"] != 51:
            raise AssertionError(result["SharedRunConditions"])

    print("write_validation_protocol_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
