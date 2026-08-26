#!/usr/bin/env python3
"""Smoke-test coordinate/probe/Uref protocol audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_coordinate_probe_protocol.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_coord_probe_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        case_dir.mkdir()
        official = case_dir / "RS_filtered.csv"
        af_csv = case_dir / "AF.csv"
        domain_origin = case_dir / "domain_origin.json"
        metadata_path = case_dir / "case_metadata.json"
        out = temp / "audit.json"

        write(official, "No.,x,y,z,U\n1,0,0,2.0,0.5\n2,1,0,2.0,0.7\n")
        write(af_csv, "z(m),U(m/s),k(m2/s2)\n0,0.0,0.01\n15.9,3.928296,0.1\n30,6.0,0.2\n")
        write(domain_origin, json.dumps({"DomainMinX": -10.0, "DomainMinY": -20.0, "DomainMinZ": 0.0, "Dx": 2.5}, indent=2))
        metadata = {
            "AijCase": "CaseE",
            "WindDirection": "N",
            "WindDirectionUnitVector": {"X": 0.0, "Y": -1.0, "Z": 0.0},
            "OfficialRS": str(official),
            "OfficialAF": str(af_csv),
            "ProbeCount": 2,
            "CoordinateProtocol": {
                "Axes": {
                    "x": "lateral/spanwise",
                    "y": "streamwise; downstream follows wind vector",
                    "z": "vertical; floor at z=0",
                },
                "VelocityComponents": {
                    "U": "speed magnitude compared with official Velocity_Ratio; FluidX3D umag"
                },
                "Normalization": {
                    "Uref_mps": 3.928296,
                    "Zref_m": 15.9,
                    "OutputRatios": ["Umag_over_Uref", "Velocity_Ratio"],
                },
                "ProbeProjection": {
                    "Formula": "(coordinate_m - DomainMin) / dx",
                    "SamplingMethod": "nearest-valid",
                    "ProbeVolumeRadiusCells": 1,
                    "ProbeZOffsetM": 0.0,
                    "ProbeCellCenterCoordinates": False,
                },
            },
        }
        write(metadata_path, json.dumps(metadata, indent=2))

        passed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(case_dir),
                "--metadata",
                str(metadata_path),
                "--official",
                str(official),
                "--af-csv",
                str(af_csv),
                "--out",
                str(out),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "2.0",
                "--z-ref",
                "15.9",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr, load(out)))
        report = load(out)
        if report["coordinate_probe_protocol_gate"] != "pass":
            raise AssertionError(report)
        if report["OfficialProbeSummary"]["row_count"] != 2:
            raise AssertionError(report)
        if report["OfficialProbeIdentity"]["id_column"] != "No.":
            raise AssertionError(report)
        if report["OfficialProbeIdentity"]["value_column"] != "U":
            raise AssertionError(report)
        if report["OfficialProbeIdentity"]["duplicate_ids"]:
            raise AssertionError(report)
        if report["OfficialProbeIdentity"]["invalid_coordinate_count"] != 0:
            raise AssertionError(report)
        if report["WindVector"]["metadata"] != [0.0, -1.0, 0.0]:
            raise AssertionError(report)
        if report["CoordinateProtocol"]["DomainOrigin"]["valid"] is not True:
            raise AssertionError(report)
        if report["CoordinateProtocol"]["DomainOrigin"]["dx_m"] != 2.5:
            raise AssertionError(report)
        if report["CoordinateProtocol"]["DomainOrigin"]["domain_min_m"] != [-10.0, -20.0, 0.0]:
            raise AssertionError(report)
        if report["development_acceleration_stage"] != "eligible_for_short_native_canary":
            raise AssertionError(report)
        if report["development_acceleration_runs_cfd_next"] is not True:
            raise AssertionError(report)
        if report["long_cfd_allowed_by_coordinate_probe_protocol"] is not True:
            raise AssertionError(report)

        range_official = case_dir / "RS_caseA.csv"
        range_af_csv = case_dir / "AF_caseA.csv"
        range_metadata_path = case_dir / "casea_metadata.json"
        range_out = temp / "range_audit.json"
        write(range_official, "No.,x,y,z,U\n1,0,0,0.01,0.5\n2,1,0,0.16,0.7\n3,2,0,0.28,0.9\n")
        write(range_af_csv, "z(m),U(m/s),k(m2/s2)\n0,0.0,0.01\n0.16,4.491,0.1\n0.32,6.0,0.2\n")
        range_metadata = dict(metadata)
        range_metadata["AijCase"] = "CaseA"
        range_metadata["WindDirectionUnitVector"] = [1.0, 0.0, 0.0]
        range_metadata["OfficialRS"] = str(range_official)
        range_metadata["OfficialAF"] = str(range_af_csv)
        range_metadata["ProbeCount"] = 3
        range_metadata["CoordinateProtocol"] = dict(metadata["CoordinateProtocol"])
        range_metadata["CoordinateProtocol"]["Normalization"] = {
            "Uref_mps": 4.491,
            "Zref_m": 0.16,
            "OutputRatios": ["Umag_over_Uref", "Velocity_Ratio"],
        }
        write(range_metadata_path, json.dumps(range_metadata, indent=2))
        ranged = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(case_dir),
                "--metadata",
                str(range_metadata_path),
                "--official",
                str(range_official),
                "--out",
                str(range_out),
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-vector",
                "1,0,0",
                "--expected-probe-row-count",
                "3",
                "--expected-probe-z-min",
                "0.01",
                "--expected-probe-z-max",
                "0.28",
                "--z-ref",
                "0.16",
                "--expected-uref",
                "4.491",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if ranged.returncode != 0:
            raise AssertionError((ranged.returncode, ranged.stdout, ranged.stderr, load(range_out)))
        range_report = load(range_out)
        if range_report["OfficialProbeSummary"]["z_range_mismatch_count"] != 0:
            raise AssertionError(range_report)
        if range_report["OfficialProbeIdentity"]["value_source"] != "computed_from_velocity_mps_over_Uref":
            raise AssertionError(range_report)
        if range_report["OfficialProbeIdentity"]["value_uref_mps"] != 4.491:
            raise AssertionError(range_report)
        if range_report["development_acceleration_stage"] != "eligible_for_short_native_canary":
            raise AssertionError(range_report)

        filtered_official = case_dir / "RS_caseE_full.csv"
        filtered_out = temp / "filtered_audit.json"
        write(
            filtered_official,
            "No.,case,Wind_direction,x(m),y(m),z(m),Velocity_Ratio\n"
            "1,bc,N,0,0,2.0,0.1\n"
            "2,ac,N,1,0,2.0,0.2\n"
            "3,ac,N,2,0,2.0,0.3\n"
            "4,ac,E,3,0,2.0,0.4\n",
        )
        filtered = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(case_dir),
                "--metadata",
                str(metadata_path),
                "--official",
                str(filtered_official),
                "--out",
                str(filtered_out),
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
                "2.0",
                "--z-ref",
                "15.9",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if filtered.returncode != 0:
            raise AssertionError((filtered.returncode, filtered.stdout, filtered.stderr, load(filtered_out)))
        filtered_report = load(filtered_out)
        if filtered_report["OfficialProbeFilter"]["input_row_count"] != 4:
            raise AssertionError(filtered_report)
        if filtered_report["OfficialProbeFilter"]["row_count"] != 2:
            raise AssertionError(filtered_report)
        if filtered_report["OfficialProbeFilter"]["condition_column"] != "case":
            raise AssertionError(filtered_report)
        if filtered_report["OfficialProbeFilter"]["wind_column"] != "Wind_direction":
            raise AssertionError(filtered_report)

        bad_metadata = dict(metadata)
        bad_metadata["CoordinateProtocol"] = {
            "Axes": {"x": "lateral", "z": "height"},
            "VelocityComponents": {"U": "unclassified scalar"},
            "Normalization": {"Uref_mps": 3.0, "OutputRatios": []},
            "ProbeProjection": {"SamplingMethod": "nearest-valid"},
        }
        bad_metadata_path = case_dir / "bad_case_metadata.json"
        bad_out = temp / "bad_audit.json"
        write(bad_metadata_path, json.dumps(bad_metadata, indent=2))
        failed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(case_dir),
                "--metadata",
                str(bad_metadata_path),
                "--official",
                str(official),
                "--out",
                str(bad_out),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--expected-probe-row-count",
                "80",
                "--expected-probe-z",
                "2.0",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if failed.returncode != 2:
            raise AssertionError((failed.returncode, failed.stdout, failed.stderr))
        bad_report = load(bad_out)
        for reason in [
            "coordinate_streamwise_axis_not_declared",
            "velocity_component_U_not_mapped_to_official_velocity_ratio",
            "normalization_output_ratio_missing",
            "official_probe_row_count_mismatch:2!=80",
        ]:
            if reason not in bad_report["Reasons"]:
                raise AssertionError(bad_report)
        if bad_report["development_acceleration_stage"] != "fix_coordinate_axis_component_mapping_before_cfd":
            raise AssertionError(bad_report)
        if bad_report["development_acceleration_runs_cfd_next"] is not False:
            raise AssertionError(bad_report)
        if bad_report["long_cfd_allowed_by_coordinate_probe_protocol"] is not False:
            raise AssertionError(bad_report)

        duplicate_official = case_dir / "RS_duplicate.csv"
        duplicate_out = temp / "duplicate_audit.json"
        write(
            duplicate_official,
            "No.,x(m),y(m),z(m),Velocity_Ratio\n"
            "1,0,0,2.0,0.1\n"
            "1,1,0,2.0,0.2\n"
            "3,not-a-number,0,2.0,bad\n",
        )
        duplicate_failed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(case_dir),
                "--metadata",
                str(metadata_path),
                "--official",
                str(duplicate_official),
                "--out",
                str(duplicate_out),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--expected-probe-row-count",
                "3",
                "--expected-probe-z",
                "2.0",
                "--z-ref",
                "15.9",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if duplicate_failed.returncode != 2:
            raise AssertionError((duplicate_failed.returncode, duplicate_failed.stdout, duplicate_failed.stderr))
        duplicate_report = load(duplicate_out)
        for reason in [
            "official_probe_duplicate_ids:1",
            "official_probe_invalid_coordinate_count:1",
            "official_probe_invalid_velocity_ratio_count:1",
        ]:
            if reason not in duplicate_report["Reasons"]:
                raise AssertionError(duplicate_report)
        if duplicate_report["development_acceleration_runs_cfd_next"] is not False:
            raise AssertionError(duplicate_report)

        domainless_dir = temp / "domainless_case"
        domainless_dir.mkdir()
        domainless_official = domainless_dir / "RS.csv"
        domainless_af = domainless_dir / "AF.csv"
        domainless_metadata = domainless_dir / "case_metadata.json"
        domainless_out = temp / "domainless_audit.json"
        write(domainless_official, "No.,x,y,z,Velocity_Ratio\n1,0,0,2.0,0.2\n2,1,0,2.0,0.3\n")
        write(domainless_af, "z(m),U(m/s),k(m2/s2)\n0,0,0.01\n15.9,3.928296,0.1\n")
        write(domainless_metadata, json.dumps(metadata, indent=2))
        domainless_failed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(domainless_dir),
                "--metadata",
                str(domainless_metadata),
                "--official",
                str(domainless_official),
                "--af-csv",
                str(domainless_af),
                "--out",
                str(domainless_out),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "2.0",
                "--z-ref",
                "15.9",
                "--expected-uref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if domainless_failed.returncode != 2:
            raise AssertionError((domainless_failed.returncode, domainless_failed.stdout, domainless_failed.stderr))
        domainless_report = load(domainless_out)
        for reason in [
            "domain_origin_json_missing",
            "domain_origin_dx_m_missing_or_invalid",
            "domain_origin_domain_min_m_missing_or_invalid",
        ]:
            if reason not in domainless_report["Reasons"]:
                raise AssertionError(domainless_report)
        if domainless_report["CoordinateProtocol"]["DomainOrigin"]["valid"] is not False:
            raise AssertionError(domainless_report)
        if domainless_report["development_acceleration_stage"] != "fix_probe_subset_projection_before_cfd":
            raise AssertionError(domainless_report)
        if domainless_report["long_cfd_allowed_by_coordinate_probe_protocol"] is not False:
            raise AssertionError(domainless_report)

    print("coordinate_probe_protocol_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
