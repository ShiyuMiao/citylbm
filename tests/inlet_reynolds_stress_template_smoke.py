#!/usr/bin/env python3
"""Smoke-test inlet Reynolds-stress template generation."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TEMPLATE_SCRIPT = REPO / "scripts" / "create_inlet_reynolds_stress_template.py"
BUILDER_SCRIPT = REPO / "scripts" / "build_inlet_reynolds_stress_evidence.py"


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
    with tempfile.TemporaryDirectory(prefix="citylbm_inlet_template_", dir=str(REPO)) as raw:
        tmp = Path(raw)
        metadata_path = tmp / "case_metadata.json"
        metadata = {"AijCase": "CaseE", "WindDirection": "N"}
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        metadata_sha = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
        af_path = tmp / "AF_caseE.csv"
        with af_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["z(m)", "U(m/s)", "k(m2/s2)"])
            writer.writeheader()
            writer.writerow({"z(m)": 2.0, "U(m/s)": 1.0, "k(m2/s2)": 0.1})
            writer.writerow({"z(m)": 15.9, "U(m/s)": 3.9, "k(m2/s2)": 0.3})

        out_csv = tmp / "inlet_reynolds_stress_tensor_template.csv"
        out_json = tmp / "equivalent_precursor_evidence_template.json"
        created = run_command(
            [
                str(TEMPLATE_SCRIPT),
                "--metadata",
                str(metadata_path),
                "--af-csv",
                str(af_path),
                "--out-csv",
                str(out_csv),
                "--out-precursor-json",
                str(out_json),
                "--case",
                "CaseE",
                "--wind-direction",
                "N",
            ]
        )
        if created.returncode != 0:
            raise AssertionError(created.stdout + "\n" + created.stderr)

        rows = list(csv.DictReader(out_csv.open("r", encoding="utf-8-sig", newline="")))
        require(len(rows) == 2, {"rows": rows})
        require(rows[0]["z"] == "2.0", {"rows": rows})
        require(rows[0]["R11"] == "", {"rows": rows})
        precursor = json.loads(out_json.read_text(encoding="utf-8"))
        require(precursor["Gate"] == "draft", precursor)
        require(precursor["PaperAdmissible"] is False, precursor)
        require(precursor["case_metadata_sha256"] == metadata_sha, precursor)

        builder_out = tmp / "inlet_reynolds_stress_evidence.json"
        measured_check = run_command(
            [
                str(BUILDER_SCRIPT),
                "--metadata",
                str(metadata_path),
                "--stress-csv",
                str(out_csv.relative_to(REPO)),
                "--source-type",
                "measured_tensor",
                "--out",
                str(builder_out),
            ]
        )
        if measured_check.returncode == 0:
            raise AssertionError("Blank tensor template must not pass measured_tensor evidence.")
        evidence = json.loads(builder_out.read_text(encoding="utf-8"))
        require(evidence["paper_grade_gate"] == "fail", evidence)
        require("stress_csv_no_valid_full_tensor_rows" in evidence["reasons"], evidence)

        af_rms_path = tmp / "AF_caseE_rms.csv"
        with af_rms_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["z(m)", "U(m/s)", "u_rms(m/s)", "v_rms(m/s)", "w_rms(m/s)", "k(m2/s2)"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "z(m)": 2.0,
                    "U(m/s)": 1.0,
                    "u_rms(m/s)": 0.6,
                    "v_rms(m/s)": 0.4,
                    "w_rms(m/s)": 0.2,
                    "k(m2/s2)": 0.28,
                }
            )
            writer.writerow(
                {
                    "z(m)": 15.9,
                    "U(m/s)": 3.9,
                    "u_rms(m/s)": 0.7,
                    "v_rms(m/s)": 0.5,
                    "w_rms(m/s)": 0.3,
                    "k(m2/s2)": 0.42,
                }
            )
        out_rms_csv = tmp / "inlet_reynolds_stress_tensor_template_from_rms.csv"
        created_rms = run_command(
            [
                str(TEMPLATE_SCRIPT),
                "--metadata",
                str(metadata_path),
                "--af-csv",
                str(af_rms_path),
                "--out-csv",
                str(out_rms_csv),
                "--case",
                "CaseE",
                "--wind-direction",
                "N",
            ]
        )
        if created_rms.returncode != 0:
            raise AssertionError(created_rms.stdout + "\n" + created_rms.stderr)
        rms_rows = list(csv.DictReader(out_rms_csv.open("r", encoding="utf-8-sig", newline="")))
        require(rms_rows[0]["R11"] == "0.36", {"rows": rms_rows})
        require(rms_rows[0]["R22"] == "0.16", {"rows": rms_rows})
        require(rms_rows[0]["R33"] == "0.04", {"rows": rms_rows})
        require(rms_rows[0]["R12"] == "", {"rows": rms_rows})
        require("prefilled from AF measured" in rms_rows[0]["source_note"], {"rows": rms_rows})

        full_tensor_check = run_command(
            [
                str(BUILDER_SCRIPT),
                "--metadata",
                str(metadata_path),
                "--stress-csv",
                str(out_rms_csv.relative_to(REPO)),
                "--source-type",
                "measured_tensor",
                "--out",
                str(tmp / "rms_prefill_full_tensor_check.json"),
            ]
        )
        if full_tensor_check.returncode == 0:
            raise AssertionError("RMS-prefilled diagonal template must not pass full measured_tensor evidence without off-diagonal covariances.")

    print("inlet_reynolds_stress_template_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
