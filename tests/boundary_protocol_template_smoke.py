#!/usr/bin/env python3
"""Smoke-test boundary protocol evidence template generation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TEMPLATE_SCRIPT = REPO / "scripts" / "create_boundary_protocol_evidence_template.py"
AUDIT_SCRIPT = REPO / "scripts" / "audit_boundary_protocol.py"


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_boundary_template_", dir=str(REPO)) as raw:
        tmp = Path(raw)
        metadata = {
            "Case": "AIJ Case E",
            "BoundaryProtocol": {
                "Treatment": {
                    "inlet": "TYPE_E official AF profile",
                    "outlet": "TYPE_E profile outlet",
                    "sides": "periodic y",
                    "top": "TYPE_E top profile",
                },
                "DomainExtensionsInH": {
                    "upstream": 5.0,
                    "downstream": 15.0,
                    "lateral_each_side": 5.0,
                    "top_above_model": 5.0,
                },
                "BlockageEstimate": {"ratio": 0.02},
            },
        }
        metadata_path = tmp / "case_metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        metadata_sha = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
        support = tmp / "support.txt"
        support.write_text("support placeholder\n", encoding="utf-8")
        support_sha = hashlib.sha256(support.read_bytes()).hexdigest()
        out = tmp / "boundary_protocol_evidence_template.json"

        created = run_command(
            [
                str(TEMPLATE_SCRIPT),
                str(tmp),
                "--metadata",
                str(metadata_path),
                "--out",
                str(out),
                "--case",
                "CaseE",
                "--wind-direction",
                "N",
                "--supporting-file",
                str(support),
            ]
        )
        if created.returncode != 0:
            raise AssertionError(created.stdout + "\n" + created.stderr)
        data = json.loads(out.read_text(encoding="utf-8"))
        require(data["boundary_evidence_gate"] == "draft", data)
        require(data["case_metadata_sha256"] == metadata_sha, data)
        require(data["aij_case"] == "CaseE", data)
        require(data["wind_direction"] == "N", data)
        require(data["inlet_fetch_clearance_h"] == 5.0, data)
        require(data["downstream_clearance_h"] == 15.0, data)
        require(data["min_lateral_clearance_h"] == 5.0, data)
        require(data["top_clearance_h"] == 5.0, data)
        require(str(support) in data["boundary_evidence_files"], data)
        require(data["boundary_evidence_file_records"][0]["path"] == str(support.resolve()), data)
        require(data["boundary_evidence_file_records"][0]["exists"] is True, data)
        require(data["boundary_evidence_file_records"][0]["sha256"] == support_sha, data)

        audit_out = tmp / "boundary_protocol_audit.json"
        audited = run_command(
            [
                str(AUDIT_SCRIPT),
                str(tmp),
                "--metadata",
                str(metadata_path),
                "--evidence",
                str(out.relative_to(REPO)),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--out",
                str(audit_out),
            ]
        )
        if audited.returncode == 0:
            raise AssertionError("Draft template must not pass boundary protocol audit.")
        audit = json.loads(audit_out.read_text(encoding="utf-8"))
        require(audit["boundary_run_identity_gate"] == "pass", audit)
        require(audit["boundary_protocol_gate"] == "fail", audit)
        require(audit["approx_frontal_blockage_ratio"] == 0.02, audit)
        require("boundary_evidence_gate_draft" in audit["boundary_protocol_gate_reasons"], audit)
        require("approx_frontal_blockage_ratio_missing" not in audit["boundary_protocol_gate_reasons"], audit)
        require(audit["development_acceleration_stage"] == "resolve_boundary_protocol_evidence_before_cfd", audit)
        require(audit["development_acceleration_runs_cfd_next"] is False, audit)
        require(audit["long_cfd_allowed_by_boundary_protocol_audit"] is False, audit)

    print("boundary_protocol_template_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
