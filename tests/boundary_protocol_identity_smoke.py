#!/usr/bin/env python3
"""Smoke-test boundary protocol evidence identity binding."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_metadata(path: Path, source_evidence_file: str = "") -> str:
    data = {
        "BoundaryProtocolAudit": {
            "Gate": "diagnostic_clearance_ok_verify_against_aij",
            "ProtocolEvidenceGate": "diagnostic_only_missing_aij_boundary_protocol_evidence",
            "ProtocolEvidenceSource": "diagnostic_clearance_only",
            "InletFace": "Y+",
            "OutletFace": "Y-",
            "LateralFaces": "X-/X+",
            "TopFace": "Z+",
            "GroundFace": "Z-",
            "ClearanceByBuildingHeight": {
                "Upstream": 6.0,
                "Downstream": 12.0,
                "MinLateral": 6.0,
                "Top": 6.0,
            },
            "BlockageDiagnostics": {
                "ApproxFrontalBlockageRatio": 0.02,
            },
        }
    }
    if source_evidence_file:
        data["BoundaryProtocol"] = {"SourceEvidenceFile": source_evidence_file}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_payload(metadata_sha: str, case: str = "CaseE", wind: str = "N") -> dict:
    return {
        "boundary_evidence_gate": "pass",
        "boundary_evidence_class": "wind_tunnel_protocol_matched",
        "boundary_evidence_source": "wind_tunnel_protocol_matched sha256 documented",
        "boundary_evidence_files": ["supporting_boundary_protocol.txt"],
        "case_metadata_sha256": metadata_sha,
        "aij_case": case,
        "wind_direction": wind,
        "boundary_equivalence_basis": "wind_tunnel_protocol_matched",
        "inlet_boundary": "official wind_tunnel_protocol_matched",
        "outlet_boundary": "non_reflecting_checked wind_tunnel_protocol_matched",
        "lateral_boundary": "wind_tunnel_protocol_matched",
        "top_boundary": "wind_tunnel_protocol_matched",
        "ground_wall_treatment": "validated_rough_wall measured",
        "roughness_treatment": "validated_rough_wall",
        "floor_roughness_source": "roughness_layout_source sha256",
        "blockage_source": "blockage_verified sha256",
        "fetch_clearance_source": "fetch_verified sha256",
        "inlet_fetch_clearance_h": 6.0,
        "downstream_clearance_h": 12.0,
        "min_lateral_clearance_h": 6.0,
        "top_clearance_h": 6.0,
        "outlet_reflection_check": "non_reflecting_checked sha256",
        "side_top_boundary_check": "reflection_checked sha256",
    }


def run_audit(repo: Path, tmp_dir: Path, evidence: Path, report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "audit_boundary_protocol.py"),
            str(tmp_dir),
            "--metadata",
            str(tmp_dir / "case_metadata.json"),
            "--evidence",
            str(evidence),
            "--expected-aij-case",
            "CaseE",
            "--expected-wind-direction",
            "N",
            "--out",
            str(report),
        ],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_audit_auto_evidence(repo: Path, tmp_dir: Path, report: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "audit_boundary_protocol.py"),
            str(tmp_dir),
            "--metadata",
            str(tmp_dir / "case_metadata.json"),
            "--expected-aij-case",
            "CaseE",
            "--expected-wind-direction",
            "N",
            "--out",
            str(report),
        ],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> int:
    repo = Path(__file__).resolve().parents[1]

    with tempfile.TemporaryDirectory(prefix="citylbm_boundary_protocol_identity_") as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "supporting_boundary_protocol.txt").write_text(
            "AIJ boundary protocol support for this run\n",
            encoding="utf-8",
        )
        metadata_sha = write_metadata(tmp_dir / "case_metadata.json")

        bad_evidence = tmp_dir / "bad_boundary_evidence.json"
        bad_evidence.write_text(
            json.dumps(evidence_payload("0" * 64), indent=2),
            encoding="utf-8",
        )
        bad_report = tmp_dir / "bad_boundary_protocol_audit.json"
        bad = run_audit(repo, tmp_dir, bad_evidence, bad_report)
        if bad.returncode == 0:
            raise AssertionError("Mismatched metadata hash should fail boundary protocol identity gate.")
        bad_data = json.loads(bad_report.read_text(encoding="utf-8"))
        require(bad_data.get("boundary_run_identity_gate") == "fail", bad_data)
        require("case_metadata_sha256_mismatch" in bad_data.get("boundary_run_identity_gate_reasons", []), bad_data)
        require(bad_data.get("boundary_protocol_gate") == "fail", bad_data)
        require(bad_data.get("development_acceleration_stage") == "fix_boundary_protocol_identity_before_cfd", bad_data)
        require(bad_data.get("development_acceleration_runs_cfd_next") is False, bad_data)

        wrong_case_evidence = tmp_dir / "wrong_case_boundary_evidence.json"
        wrong_case_evidence.write_text(
            json.dumps(evidence_payload(metadata_sha, case="CaseA"), indent=2),
            encoding="utf-8",
        )
        wrong_case_report = tmp_dir / "wrong_case_boundary_protocol_audit.json"
        wrong_case = run_audit(repo, tmp_dir, wrong_case_evidence, wrong_case_report)
        if wrong_case.returncode == 0:
            raise AssertionError("Case-mismatched evidence should fail when an expected case is supplied.")
        wrong_case_data = json.loads(wrong_case_report.read_text(encoding="utf-8"))
        require("aij_case_mismatch" in wrong_case_data.get("boundary_run_identity_gate_reasons", []), wrong_case_data)
        require(
            wrong_case_data.get("development_acceleration_stage") == "fix_boundary_protocol_identity_before_cfd",
            wrong_case_data,
        )

        simplified_evidence = tmp_dir / "simplified_boundary_evidence.json"
        simplified_payload = evidence_payload(metadata_sha)
        simplified_payload.update(
            {
                "outlet_boundary": "official TYPE_E free-outflow approximation sha256",
                "lateral_boundary": "official TYPE_E slip/free approximation sha256",
                "top_boundary": "official simplified open boundary sha256",
                "outlet_reflection_check": "official reflection_checked but free approximation",
                "side_top_boundary_check": "official reflection_checked but slip/free approximation",
            }
        )
        simplified_evidence.write_text(
            json.dumps(simplified_payload, indent=2),
            encoding="utf-8",
        )
        simplified_report = tmp_dir / "simplified_boundary_protocol_audit.json"
        simplified = run_audit(repo, tmp_dir, simplified_evidence, simplified_report)
        if simplified.returncode == 0:
            raise AssertionError("Simplified TYPE_E/free/slip boundary labels must fail boundary protocol evidence.")
        simplified_data = json.loads(simplified_report.read_text(encoding="utf-8"))
        require(simplified_data.get("boundary_protocol_gate") == "fail", simplified_data)
        require(simplified_data.get("boundary_condition_fields_supported") is False, simplified_data)
        require(
            "unsupported_boundary_condition_fields:"
            "outlet_boundary,lateral_boundary,top_boundary,outlet_reflection_check,side_top_boundary_check"
            in simplified_data.get("boundary_protocol_gate_reasons", []),
            simplified_data,
        )
        require(
            simplified_data.get("development_acceleration_stage") == "replace_simplified_boundary_protocol_before_cfd",
            simplified_data,
        )
        require(simplified_data.get("development_acceleration_runs_cfd_next") is False, simplified_data)

        good_evidence = tmp_dir / "good_boundary_evidence.json"
        good_evidence.write_text(
            json.dumps(evidence_payload(metadata_sha), indent=2),
            encoding="utf-8",
        )
        good_report = tmp_dir / "good_boundary_protocol_audit.json"
        good = run_audit(repo, tmp_dir, good_evidence, good_report)
        if good.returncode != 0:
            raise AssertionError(good.stdout + "\n" + good.stderr)
        good_data = json.loads(good_report.read_text(encoding="utf-8"))
        require(good_data.get("boundary_run_identity_gate") == "pass", good_data)
        require(good_data.get("evidence_metadata_sha256_matches_current") is True, good_data)
        require(good_data.get("boundary_protocol_gate") == "pass", good_data)
        require(good_data.get("development_acceleration_stage") == "eligible_for_short_native_canary", good_data)
        require(good_data.get("development_acceleration_runs_cfd_next") is True, good_data)
        require(good_data.get("long_cfd_allowed_by_boundary_protocol_audit") is True, good_data)

    with tempfile.TemporaryDirectory(prefix="citylbm_boundary_protocol_auto_") as tmp:
        tmp_dir = Path(tmp)
        (tmp_dir / "supporting_boundary_protocol.txt").write_text(
            "AIJ boundary protocol support for this run\n",
            encoding="utf-8",
        )
        metadata_sha = write_metadata(tmp_dir / "case_metadata.json", "auto_boundary_evidence.json")
        auto_evidence = tmp_dir / "auto_boundary_evidence.json"
        auto_evidence.write_text(
            json.dumps(evidence_payload(metadata_sha), indent=2),
            encoding="utf-8",
        )
        auto_report = tmp_dir / "auto_boundary_protocol_audit.json"
        auto = run_audit_auto_evidence(repo, tmp_dir, auto_report)
        if auto.returncode != 0:
            raise AssertionError(auto.stdout + "\n" + auto.stderr)
        auto_data = json.loads(auto_report.read_text(encoding="utf-8"))
        require(auto_data.get("boundary_protocol_gate") == "pass", auto_data)
        require(auto_data.get("evidence_discovery", {}).get("source") == "metadata", auto_data)
        require(auto_data.get("evidence_discovery", {}).get("exists") is True, auto_data)
        require(auto_data.get("development_acceleration_stage") == "eligible_for_short_native_canary", auto_data)

    print("boundary_protocol_identity_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
