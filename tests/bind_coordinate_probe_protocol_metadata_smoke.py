#!/usr/bin/env python3
"""Smoke-test coordinate/probe protocol metadata binding."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BIND = REPO / "scripts" / "bind_coordinate_probe_protocol_metadata.py"
AUDIT = REPO / "scripts" / "audit_coordinate_probe_protocol.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_bind_coord_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        case_dir.mkdir()
        metadata = case_dir / "case_metadata.json"
        official = case_dir / "RS_caseE.csv"
        af_csv = case_dir / "AF_caseE.csv"
        domain_origin = case_dir / "domain_origin.json"
        setup = case_dir / "setup.cpp"
        bound = case_dir / "preflight" / "case_metadata.coordinate_probe_bound.json"
        audit = case_dir / "preflight" / "coordinate_probe_protocol_audit.json"

        write(
            metadata,
            json.dumps(
                {
                    "case": "AIJ Case E ac + N",
                    "target_rs_subset": {"rows": 2},
                    "physics": {"u_ref_mps_at_15p9m": 3.928296},
                    "inlet": {"wind_vector": [0.0, -1.0, 0.0]},
                },
                indent=2,
            ),
        )
        write(official, "No.,case,Wind_direction,x(m),y(m),z(m),Velocity_Ratio\n1,ac,N,0,0,2,0.2\n2,ac,N,1,0,2,0.3\n")
        write(af_csv, "z(m),U(m/s),k(m2/s2)\n0,0,0.01\n15.9,3.928296,0.1\n")
        write(domain_origin, json.dumps({"DomainMin": [-300.0, -300.0, 0.0], "Dx": 2.5}, indent=2))
        write(setup, "const double umag_mps = sqrt(ux_mps*ux_mps + uy_mps*uy_mps + uz_mps*uz_mps);\nconst double sim_ratio = umag_mps/u_ref_si;\n")

        bind_result = subprocess.run(
            [
                sys.executable,
                str(BIND),
                "--metadata",
                str(metadata),
                "--case-dir",
                str(case_dir),
                "--out",
                str(bound),
                "--case-label",
                "CaseE",
                "--wind-direction",
                "N",
                "--wind-vector",
                "0,-1,0",
                "--probe-count",
                "2",
                "--z-ref",
                "15.9",
                "--uref",
                "3.928296",
                "--official-rs",
                str(official),
                "--official-af",
                str(af_csv),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if bind_result.returncode != 0:
            raise AssertionError((bind_result.returncode, bind_result.stdout, bind_result.stderr))
        bound_data = load(bound)
        protocol = bound_data["CoordinateProtocol"]
        if protocol["VelocityComponents"]["MappingMode"] != "velocity_magnitude":
            raise AssertionError(bound_data)
        if "Umag_over_Uref" not in protocol["Normalization"]["OutputRatios"]:
            raise AssertionError(bound_data)
        if "streamwise" not in protocol["Axes"]["y"]:
            raise AssertionError(bound_data)
        projection = protocol["ProbeProjection"]
        if projection["DomainOriginPath"] != str(domain_origin.resolve()):
            raise AssertionError(bound_data)
        if projection["DomainOriginSha256"] != sha256(domain_origin):
            raise AssertionError(bound_data)
        if projection["DomainMinM"] != [-300.0, -300.0, 0.0]:
            raise AssertionError(bound_data)
        if projection["DxM"] != 2.5:
            raise AssertionError(bound_data)
        if bound_data.get("OfficialAFSha256") != sha256(af_csv):
            raise AssertionError(bound_data)
        if bound_data.get("OfficialRSSha256") != sha256(official):
            raise AssertionError(bound_data)
        if bound_data.get("OfficialProbeDataSha256") != sha256(official):
            raise AssertionError(bound_data)
        if bound_data.get("DomainOriginSha256") != sha256(domain_origin):
            raise AssertionError(bound_data)

        audit_result = subprocess.run(
            [
                sys.executable,
                str(AUDIT),
                str(case_dir),
                "--metadata",
                str(bound),
                "--official",
                str(official),
                "--af-csv",
                str(af_csv),
                "--out",
                str(audit),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--official-condition-filter",
                "ac",
                "--official-wind-filter",
                "N",
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "2",
                "--z-ref",
                "15.9",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if audit_result.returncode != 0:
            raise AssertionError((audit_result.returncode, audit_result.stdout, audit_result.stderr, load(audit)))
        report = load(audit)
        if report["coordinate_probe_protocol_gate"] != "pass":
            raise AssertionError(report)
        if report["CoordinateProtocol"]["VelocityRatioMapping"]["mode"] != "velocity_magnitude":
            raise AssertionError(report)
        if report["CoordinateProtocol"]["DomainOrigin"]["valid"] is not True:
            raise AssertionError(report)

    print("bind_coordinate_probe_protocol_metadata_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
