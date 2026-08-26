#!/usr/bin/env python3
"""Smoke-test inlet Reynolds-stress evidence generation."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_inlet_reynolds_stress_evidence.py"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO),
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        af = temp / "AF.csv"
        write_csv(
            af,
            ["z(m)", "U(m/s)", "k(m2/s2)"],
            [
                {"z(m)": 1.0, "U(m/s)": 2.0, "k(m2/s2)": 0.30},
                {"z(m)": 2.0, "U(m/s)": 3.0, "k(m2/s2)": 0.60},
            ],
        )
        isotropic_out = temp / "isotropic.json"
        isotropic = run_script("--af-csv", str(af), "--out", str(isotropic_out))
        if isotropic.returncode != 2:
            raise AssertionError((isotropic.returncode, isotropic.stdout, isotropic.stderr))
        isotropic_report = load(isotropic_out)
        if isotropic_report["gate"] != "diagnostic_only" or isotropic_report["paper_grade_gate"] != "fail":
            raise AssertionError(isotropic_report)
        if isotropic_report["source_type"] != "isotropic_from_k":
            raise AssertionError(isotropic_report)
        sample = isotropic_report["af_csv"]["sample"][0]
        if abs(sample["r11_r22_r33_m2_s2"] - 0.20) > 1.0e-12:
            raise AssertionError(sample)

        blank_stress = temp / "blank_stress.csv"
        write_csv(
            blank_stress,
            ["z", "R11", "R22", "R33", "R12", "R13", "R23", "source_note"],
            [
                {"z": 1.0, "R11": "", "R22": "", "R33": "", "R12": "", "R13": "", "R23": "", "source_note": "template"},
                {"z": 2.0, "R11": "", "R22": "", "R33": "", "R12": "", "R13": "", "R23": "", "source_note": "template"},
            ],
        )
        blank_auto_out = temp / "blank_auto_fallback.json"
        blank_auto = run_script("--af-csv", str(af), "--stress-csv", str(blank_stress), "--out", str(blank_auto_out))
        if blank_auto.returncode != 2:
            raise AssertionError((blank_auto.returncode, blank_auto.stdout, blank_auto.stderr))
        blank_auto_report = load(blank_auto_out)
        if blank_auto_report["source_type"] != "isotropic_from_k":
            raise AssertionError(blank_auto_report)
        if blank_auto_report["gate"] != "diagnostic_only" or blank_auto_report["paper_grade_gate"] != "fail":
            raise AssertionError(blank_auto_report)
        if "isotropic_k_assumption_only_not_paper_grade_reynolds_stress" not in blank_auto_report["reasons"]:
            raise AssertionError(blank_auto_report)
        if blank_auto_report["stress_csv"]["valid_row_count"] != 0:
            raise AssertionError(blank_auto_report["stress_csv"])

        af_rms = temp / "AF_rms.csv"
        write_csv(
            af_rms,
            ["z(m)", "U(m/s)", "u_rms(m/s)", "v_rms(m/s)", "w_rms(m/s)", "k(m2/s2)"],
            [
                {"z(m)": 1.0, "U(m/s)": 2.0, "u_rms(m/s)": 0.60, "v_rms(m/s)": 0.40, "w_rms(m/s)": 0.20, "k(m2/s2)": 0.28},
                {"z(m)": 2.0, "U(m/s)": 3.0, "u_rms(m/s)": 0.70, "v_rms(m/s)": 0.50, "w_rms(m/s)": 0.30, "k(m2/s2)": 0.42},
            ],
        )
        diagonal_out = temp / "diagonal.json"
        diagonal = run_script("--af-csv", str(af_rms), "--out", str(diagonal_out))
        if diagonal.returncode != 2:
            raise AssertionError((diagonal.returncode, diagonal.stdout, diagonal.stderr))
        diagonal_report = load(diagonal_out)
        if diagonal_report["gate"] != "diagnostic_only" or diagonal_report["paper_grade_gate"] != "fail":
            raise AssertionError(diagonal_report)
        if diagonal_report["source_type"] != "measured_diagonal_rms":
            raise AssertionError(diagonal_report)
        diagonal_sample = diagonal_report["af_diagonal_rms"]["sample"][0]
        if abs(diagonal_sample["r11_m2_s2"] - 0.36) > 1.0e-12:
            raise AssertionError(diagonal_sample)
        if "measured_diagonal_rms_missing_off_diagonal_covariances_not_paper_grade_full_tensor" not in diagonal_report["reasons"]:
            raise AssertionError(diagonal_report)

        stress = temp / "stress.csv"
        write_csv(
            stress,
            ["z", "R11", "R22", "R33", "R12", "R13", "R23"],
            [
                {"z": 1.0, "R11": 0.20, "R22": 0.18, "R33": 0.15, "R12": 0.01, "R13": 0.0, "R23": 0.0},
                {"z": 2.0, "R11": 0.30, "R22": 0.27, "R33": 0.22, "R12": 0.02, "R13": 0.0, "R23": 0.0},
            ],
        )
        measured_out = temp / "measured.json"
        measured = run_script("--stress-csv", str(stress), "--out", str(measured_out))
        if measured.returncode != 0:
            raise AssertionError((measured.returncode, measured.stdout, measured.stderr))
        measured_report = load(measured_out)
        if measured_report["gate"] != "pass" or measured_report["paper_grade_gate"] != "pass":
            raise AssertionError(measured_report)
        if measured_report["source_type"] != "measured_tensor":
            raise AssertionError(measured_report)
        if measured_report["stress_csv"]["invalid_positive_semidefinite_tensor_row_count"] != 0:
            raise AssertionError(measured_report["stress_csv"])

        invalid_stress = temp / "invalid_stress.csv"
        write_csv(
            invalid_stress,
            ["z", "R11", "R22", "R33", "R12", "R13", "R23"],
            [
                {"z": 1.0, "R11": 0.20, "R22": 0.18, "R33": 0.15, "R12": 0.30, "R13": 0.0, "R23": 0.0},
                {"z": 2.0, "R11": 0.30, "R22": -0.01, "R33": 0.22, "R12": 0.02, "R13": 0.0, "R23": 0.0},
            ],
        )
        invalid_stress_out = temp / "invalid_stress.json"
        invalid = run_script("--stress-csv", str(invalid_stress), "--out", str(invalid_stress_out))
        if invalid.returncode != 2:
            raise AssertionError((invalid.returncode, invalid.stdout, invalid.stderr))
        invalid_report = load(invalid_stress_out)
        if invalid_report["gate"] != "fail" or invalid_report["paper_grade_gate"] != "fail":
            raise AssertionError(invalid_report)
        if "stress_csv_invalid_positive_semidefinite_tensor_rows:2" not in invalid_report["reasons"]:
            raise AssertionError(invalid_report)
        if "stress_tensor_r11_r22_minor_not_positive_semidefinite" not in invalid_report["reasons"]:
            raise AssertionError(invalid_report)
        if "stress_tensor_negative_r22" not in invalid_report["reasons"]:
            raise AssertionError(invalid_report)

        metadata_stress = temp / "metadata_stress" / "case_metadata.json"
        metadata_stress.parent.mkdir(parents=True, exist_ok=True)
        (metadata_stress.parent / "stress.csv").write_text(stress.read_text(encoding="utf-8"), encoding="utf-8")
        metadata_stress.write_text(
            json.dumps({"AijCase": "CaseA", "InletReynoldsStress": {"TensorCsv": "stress.csv"}}, indent=2),
            encoding="utf-8",
        )
        metadata_measured_out = temp / "metadata_measured.json"
        metadata_measured = run_script("--metadata", str(metadata_stress), "--out", str(metadata_measured_out))
        if metadata_measured.returncode != 0:
            raise AssertionError((metadata_measured.returncode, metadata_measured.stdout, metadata_measured.stderr))
        metadata_measured_report = load(metadata_measured_out)
        if metadata_measured_report["source_type"] != "measured_tensor":
            raise AssertionError(metadata_measured_report)
        if metadata_measured_report["discovery"]["stress_csv"]["source"] != "metadata":
            raise AssertionError(metadata_measured_report["discovery"])
        if metadata_measured_report["discovery"]["stress_csv"]["exists"] is not True:
            raise AssertionError(metadata_measured_report["discovery"])

        metadata_bound_out = temp / "metadata_bound_measured.json"
        metadata_stress.write_text(
            json.dumps(
                {
                    "AijCase": "CaseA",
                    "WindDirection": "N",
                    "InletReynoldsStress": {
                        "TensorCsv": "stress.csv",
                        "TensorCsvSha256": hashlib.sha256((metadata_stress.parent / "stress.csv").read_bytes()).hexdigest(),
                        "EvidenceQuality": "measured_full_tensor",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        metadata_bound_measured = run_script(
            "--metadata",
            str(metadata_stress),
            "--case",
            "CaseA",
            "--wind-direction-label",
            "N",
            "--require-run-binding",
            "--out",
            str(metadata_bound_out),
        )
        if metadata_bound_measured.returncode != 0:
            raise AssertionError((metadata_bound_measured.returncode, metadata_bound_measured.stdout, metadata_bound_measured.stderr))
        metadata_bound_report = load(metadata_bound_out)
        if metadata_bound_report["paper_grade_gate"] != "pass":
            raise AssertionError(metadata_bound_report)
        if metadata_bound_report["run_binding_required"] is not True:
            raise AssertionError(metadata_bound_report)
        if metadata_bound_report["stress_csv_metadata_evidence_quality"] != "measured_full_tensor":
            raise AssertionError(metadata_bound_report)

        metadata_stress.write_text(
            json.dumps(
                {
                    "AijCase": "CaseA",
                    "WindDirection": "N",
                    "InletReynoldsStress": {
                        "TensorCsv": "stress.csv",
                        "TensorCsvSha256": hashlib.sha256((metadata_stress.parent / "stress.csv").read_bytes()).hexdigest(),
                        "EvidenceQuality": "diagnostic_template_not_paper_grade",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        metadata_diagnostic_out = temp / "metadata_diagnostic_measured.json"
        metadata_diagnostic_measured = run_script(
            "--metadata",
            str(metadata_stress),
            "--case",
            "CaseA",
            "--wind-direction-label",
            "N",
            "--require-run-binding",
            "--out",
            str(metadata_diagnostic_out),
        )
        if metadata_diagnostic_measured.returncode != 2:
            raise AssertionError((metadata_diagnostic_measured.returncode, metadata_diagnostic_measured.stdout, metadata_diagnostic_measured.stderr))
        metadata_diagnostic_report = load(metadata_diagnostic_out)
        if metadata_diagnostic_report["paper_grade_gate"] != "fail":
            raise AssertionError(metadata_diagnostic_report)
        if "stress_csv_evidence_quality_not_paper_grade:diagnostic_template_not_paper_grade" not in metadata_diagnostic_report["reasons"]:
            raise AssertionError(metadata_diagnostic_report)

        metadata_stress.write_text(
            json.dumps({"AijCase": "CaseA", "WindDirection": "N", "InletReynoldsStress": {"TensorCsv": "stress.csv"}}, indent=2),
            encoding="utf-8",
        )
        metadata_unbound_out = temp / "metadata_unbound_measured.json"
        metadata_unbound_measured = run_script(
            "--metadata",
            str(metadata_stress),
            "--case",
            "CaseA",
            "--wind-direction-label",
            "N",
            "--require-run-binding",
            "--out",
            str(metadata_unbound_out),
        )
        if metadata_unbound_measured.returncode != 2:
            raise AssertionError((metadata_unbound_measured.returncode, metadata_unbound_measured.stdout, metadata_unbound_measured.stderr))
        metadata_unbound_report = load(metadata_unbound_out)
        if "stress_csv_sha256_missing_in_metadata" not in metadata_unbound_report["reasons"]:
            raise AssertionError(metadata_unbound_report)

        precursor_dir = temp / "metadata_precursor"
        precursor_dir.mkdir(parents=True, exist_ok=True)
        precursor_evidence = precursor_dir / "equivalent_precursor_evidence.json"
        precursor_evidence.write_text(
            json.dumps(
                {
                    "Gate": "pass",
                    "SourceVtkSha256": "a" * 64,
                    "source_turbulence_method": "precursor_empty_tunnel_digital_filter",
                    "source_boundary_mode": "AIJ_equivalent_empty_tunnel",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        precursor_metadata = precursor_dir / "case_metadata.json"
        precursor_metadata.write_text(
            json.dumps(
                {
                    "AijCase": "CaseA",
                    "EquivalentPrecursor": {
                        "Enabled": True,
                        "PaperAdmissible": True,
                        "EvidenceJson": "equivalent_precursor_evidence.json",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        precursor_out = temp / "metadata_precursor.json"
        precursor = run_script("--metadata", str(precursor_metadata), "--out", str(precursor_out))
        if precursor.returncode != 0:
            raise AssertionError((precursor.returncode, precursor.stdout, precursor.stderr))
        precursor_report = load(precursor_out)
        if precursor_report["source_type"] != "precursor":
            raise AssertionError(precursor_report)
        if precursor_report["paper_grade_gate"] != "pass":
            raise AssertionError(precursor_report)
        if precursor_report["discovery"]["precursor_evidence"]["source"] != "metadata":
            raise AssertionError(precursor_report["discovery"])

        unbound_precursor_out = temp / "metadata_unbound_precursor.json"
        unbound_precursor = run_script(
            "--metadata",
            str(precursor_metadata),
            "--case",
            "CaseA",
            "--wind-direction-label",
            "N",
            "--require-run-binding",
            "--out",
            str(unbound_precursor_out),
        )
        if unbound_precursor.returncode != 2:
            raise AssertionError((unbound_precursor.returncode, unbound_precursor.stdout, unbound_precursor.stderr))
        unbound_precursor_report = load(unbound_precursor_out)
        if "precursor_case_metadata_sha256_missing" not in unbound_precursor_report["reasons"]:
            raise AssertionError(unbound_precursor_report)

        precursor_metadata_sha = hashlib.sha256(precursor_metadata.read_bytes()).hexdigest()
        precursor_evidence.write_text(
            json.dumps(
                {
                    "Gate": "pass",
                    "SourceVtkSha256": "a" * 64,
                    "source_turbulence_method": "precursor_empty_tunnel_digital_filter",
                    "source_boundary_mode": "AIJ_equivalent_empty_tunnel",
                    "case_metadata_sha256": precursor_metadata_sha,
                    "aij_case": "CaseA",
                    "wind_direction": "N",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        bound_precursor_out = temp / "metadata_bound_precursor.json"
        bound_precursor = run_script(
            "--metadata",
            str(precursor_metadata),
            "--case",
            "CaseA",
            "--wind-direction-label",
            "N",
            "--require-run-binding",
            "--out",
            str(bound_precursor_out),
        )
        if bound_precursor.returncode != 0:
            raise AssertionError((bound_precursor.returncode, bound_precursor.stdout, bound_precursor.stderr))
        bound_precursor_report = load(bound_precursor_out)
        if bound_precursor_report["paper_grade_gate"] != "pass":
            raise AssertionError(bound_precursor_report)
        if bound_precursor_report["precursor_evidence"]["case_metadata_sha256_matches_current"] is not True:
            raise AssertionError(bound_precursor_report["precursor_evidence"])

        weak_precursor = precursor_dir / "weak_precursor.json"
        weak_precursor.write_text(
            json.dumps({"Gate": "pass", "SourceVtkSha256": "not-a-hash"}, indent=2),
            encoding="utf-8",
        )
        weak_precursor_out = temp / "weak_precursor.json"
        weak = run_script("--precursor-evidence", str(weak_precursor), "--out", str(weak_precursor_out))
        if weak.returncode != 2:
            raise AssertionError((weak.returncode, weak.stdout, weak.stderr))
        weak_report = load(weak_precursor_out)
        for reason in [
            "precursor_sha256_evidence_missing_or_invalid",
            "precursor_turbulence_method_missing",
            "precursor_boundary_mode_missing",
        ]:
            if reason not in weak_report["reasons"]:
                raise AssertionError(weak_report)

    with tempfile.TemporaryDirectory(prefix="citylbm_inlet_stress_relative_", dir=str(REPO)) as raw:
        temp = Path(raw)
        stress = temp / "stress.csv"
        write_csv(
            stress,
            ["z", "R11", "R22", "R33", "R12", "R13", "R23"],
            [
                {"z": 1.0, "R11": 0.20, "R22": 0.18, "R33": 0.15, "R12": 0.01, "R13": 0.0, "R23": 0.0},
                {"z": 2.0, "R11": 0.30, "R22": 0.27, "R33": 0.22, "R12": 0.02, "R13": 0.0, "R23": 0.0},
            ],
        )
        metadata = temp / "metadata" / "case_metadata.json"
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_text(json.dumps({"AijCase": "CaseA"}, indent=2), encoding="utf-8")
        out = temp / "relative_measured.json"
        relative_stress = run_script(
            "--metadata",
            str(metadata),
            "--stress-csv",
            str(stress.relative_to(REPO)),
            "--out",
            str(out),
        )
        if relative_stress.returncode != 0:
            raise AssertionError((relative_stress.returncode, relative_stress.stdout, relative_stress.stderr))
        relative_report = load(out)
        if relative_report["discovery"]["stress_csv"]["source"] != "argument":
            raise AssertionError(relative_report["discovery"])
        if relative_report["discovery"]["stress_csv"]["exists"] is not True:
            raise AssertionError(relative_report["discovery"])
        if relative_report["source_type"] != "measured_tensor":
            raise AssertionError(relative_report)

    print("inlet_reynolds_stress_evidence_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
