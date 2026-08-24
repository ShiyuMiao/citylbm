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


def enable_rejected_stress_ddf(metadata_path: Path) -> None:
    metadata = load_json(metadata_path)
    metadata["ReconstructInletStressDdf"] = {"Enabled": True}
    metadata["SyntheticEddy"] = {"DeviceSemStressDdf": True}
    write(metadata_path, json.dumps(metadata, indent=2))


def disable_rejected_stress_ddf(metadata_path: Path) -> None:
    metadata = load_json(metadata_path)
    metadata.pop("ReconstructInletStressDdf", None)
    metadata.pop("SyntheticEddy", None)
    write(metadata_path, json.dumps(metadata, indent=2))


def create_velocity_only_inlet_audit(path: Path) -> None:
    audit = {
        "schema": "citylbm.inlet_source_audit.v1",
        "inlet_source_gate": "fail",
        "paper_grade_inlet_source_gate": "fail",
        "inlet_source_method_class": "stg_lite_velocity_field_only",
        "inlet_source_turbulent_inflow_fidelity_class": "uncorrelated_rms_velocity_field_only",
        "inlet_source_distribution_consistent": False,
        "inlet_source_velocity_field_only": True,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": True,
        "has_profile_k_lbm": True,
        "has_k_driven_three_component_stg": True,
        "has_inlet_length_scale_evidence": False,
        "has_reynolds_stress_tensor_evidence": False,
        "has_documented_isotropic_k_assumption": True,
        "reynolds_stress_treatment": "documented_isotropic_k_only",
    }
    write(path, json.dumps(audit, indent=2))


def create_paper_grade_inlet_audit(path: Path) -> None:
    audit = {
        "schema": "citylbm.inlet_source_audit.v1",
        "inlet_source_gate": "pass",
        "paper_grade_inlet_source_gate": "pass",
        "inlet_source_method_class": "digital_filter_distribution_consistent",
        "inlet_source_turbulent_inflow_fidelity_class": "distribution_consistent_digital_filter",
        "inlet_source_distribution_consistent": True,
        "inlet_source_velocity_field_only": False,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": False,
        "has_profile_k_lbm": True,
        "has_k_driven_three_component_stg": True,
        "has_inlet_length_scale_evidence": True,
        "has_reynolds_stress_full_tensor_source_evidence": True,
        "has_measured_or_precursor_reynolds_stress_tensor_evidence": True,
        "has_reynolds_stress_tensor_evidence": True,
        "has_documented_isotropic_k_assumption": False,
        "reynolds_stress_treatment": "measured_or_precursor_full_tensor",
    }
    write(path, json.dumps(audit, indent=2))


def create_paper_grade_boundary_audit(path: Path) -> None:
    audit = {
        "schema": "citylbm.boundary_source_audit.v1",
        "boundary_source_gate": "pass",
        "paper_grade_boundary_source_gate": "pass",
        "boundary_source_method_class": "wind_tunnel_equivalent_boundary_source",
        "boundary_source_fidelity_class": "wind_tunnel_equivalent_complete",
        "boundary_source_wind_tunnel_equivalent": True,
        "boundary_source_simplified": False,
        "has_paper_grade_rough_wall_source": True,
        "has_paper_grade_development_source": True,
    }
    write(path, json.dumps(audit, indent=2))


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
        if statuses["inlet_distribution_consistency"] != "fail":
            raise AssertionError(statuses)

        metadata = load_json(case / "case_metadata.json")
        if metadata["AijCase"] != "CaseA" or metadata["WindDirection"] != "N":
            raise AssertionError(metadata)
        if metadata["WindDirectionUnitVector"] != [1.0, 0.0, 0.0]:
            raise AssertionError(metadata)

        enable_rejected_stress_ddf(case / "case_metadata.json")
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
            ]
        )
        stress_audit = load_json(case / "validation_protocol_audit.json")
        stress_items = {item["Key"]: item for item in stress_audit["Items"]}
        for key in ["inlet_reynolds_stress_tensor", "inlet_distribution_consistency"]:
            if stress_items[key]["Status"] != "fail":
                raise AssertionError((key, stress_items[key], stress_audit))
            if "RejectedStressDdfDiagnostic=true" not in stress_items[key]["Evidence"]:
                raise AssertionError((key, stress_items[key]))
        disable_rejected_stress_ddf(case / "case_metadata.json")

        velocity_only_inlet = temp / "velocity_only_inlet_audit.json"
        create_velocity_only_inlet_audit(velocity_only_inlet)
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
                "--inlet-source-audit",
                str(velocity_only_inlet),
            ]
        )
        velocity_only_audit = load_json(case / "validation_protocol_audit.json")
        velocity_only_statuses = {item["Key"]: item["Status"] for item in velocity_only_audit["Items"]}
        if velocity_only_statuses["inlet_distribution_consistency"] != "fail":
            raise AssertionError(velocity_only_statuses)
        if velocity_only_statuses["inlet_reynolds_stress_tensor"] != "partial":
            raise AssertionError(velocity_only_statuses)

        paper_grade_inlet = temp / "paper_grade_inlet_audit.json"
        paper_grade_boundary = temp / "paper_grade_boundary_audit.json"
        create_paper_grade_inlet_audit(paper_grade_inlet)
        create_paper_grade_boundary_audit(paper_grade_boundary)
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
                "--inlet-source-audit",
                str(paper_grade_inlet),
                "--boundary-source-audit",
                str(paper_grade_boundary),
            ]
        )
        paper_audit = load_json(case / "validation_protocol_audit.json")
        paper_statuses = {item["Key"]: item["Status"] for item in paper_audit["Items"]}
        for key in [
            "inlet_turbulence_k",
            "inlet_turbulence_length_scale",
            "inlet_reynolds_stress_tensor",
            "inlet_distribution_consistency",
            "boundary_conditions",
            "wall_roughness_model",
        ]:
            if paper_statuses[key] != "pass":
                raise AssertionError((key, paper_statuses, paper_audit))
        if paper_audit["Gate"] != "diagnostic_only":
            raise AssertionError(paper_audit)

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
            "validation_protocol_item_fail:native_fluidx3d_baseline",
        ]:
            if expected not in reasons:
                raise AssertionError((expected, reasons))
        for not_expected in [
            "validation_protocol_item_fail:boundary_conditions",
            "validation_protocol_item_fail:wall_roughness_model",
        ]:
            if not_expected in reasons:
                raise AssertionError((not_expected, reasons))
        if result["SharedRunConditions"]["ComputedVtkFrameCount"] != 51:
            raise AssertionError(result["SharedRunConditions"])

    print("write_validation_protocol_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
