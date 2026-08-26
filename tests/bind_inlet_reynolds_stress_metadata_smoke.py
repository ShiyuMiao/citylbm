#!/usr/bin/env python3
"""Smoke-test Reynolds-stress metadata identity binding."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "bind_inlet_reynolds_stress_metadata.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_bind_reynolds_") as raw:
        temp = Path(raw)
        metadata = temp / "case_metadata.json"
        stress = temp / "inlet_reynolds_stress_tensor_template.csv"
        out = temp / "case_metadata.bound.json"
        metadata.write_text(json.dumps({"AijCase": "CaseA", "WindDirection": "N"}, indent=2), encoding="utf-8")
        stress.write_text(
            "z,R11,R22,R33,R12,R13,R23,source_note\n"
            "0.1,0.2,0.2,0.2,,,,diagnostic diagonal template\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--metadata",
                str(metadata),
                "--stress-csv",
                str(stress),
                "--out",
                str(out),
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        bound = load_json(out)
        expected_hash = hashlib.sha256(stress.read_bytes()).hexdigest()
        inlet = bound["InletReynoldsStress"]
        if inlet["TensorCsvSha256"] != expected_hash:
            raise AssertionError(inlet)
        if bound["InletReynoldsStressTensorCsvSha256"] != expected_hash:
            raise AssertionError(bound)
        if inlet["EvidenceQuality"] != "diagnostic_template_not_paper_grade":
            raise AssertionError(inlet)
        if "paper_grade" == inlet["EvidenceQuality"]:
            raise AssertionError(inlet)

    print("bind_inlet_reynolds_stress_metadata_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
