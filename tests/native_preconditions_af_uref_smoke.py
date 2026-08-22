#!/usr/bin/env python3
"""Smoke-test AF-derived Uref checks in native preconditions."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_native_af_uref_") as tmp:
        root = Path(tmp)
        run_dir = root / "run"
        run_dir.mkdir()
        af_csv = root / "AF.csv"
        metadata = root / "case_metadata.json"
        out_json = root / "native_preconditions_audit.json"
        write_text(af_csv, "z(m),U(m/s),k(m2/s2)\n10,3.0,0.1\n20,5.0,0.2\n")
        write_text(metadata, '{"ReferenceWindSpeedMps": 3.0, "WindProfile": "CustomTable"}\n')

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_native_preconditions.py"),
                str(run_dir),
                "--metadata",
                str(metadata),
                "--af-csv",
                str(af_csv),
                "--u-ref",
                "3.0",
                "--z-ref",
                "15.0",
                "--out",
                str(out_json),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 2:
            raise AssertionError(
                f"audit_native_preconditions returned {completed.returncode}, expected 2 for failing preconditions\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        reasons = report.get("native_preconditions_gate_reasons", [])
        if "uref_af_profile_mismatch" not in reasons:
            raise AssertionError(reasons)
        if report.get("af_uref_at_zref_mps") != 4.0:
            raise AssertionError(report.get("af_uref_at_zref_mps"))
        if report.get("native_preconditions_protocol_identity_gate") != "fail":
            raise AssertionError(report.get("native_preconditions_protocol_identity_gate"))

    print("native_preconditions_af_uref_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
