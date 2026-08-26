#!/usr/bin/env python3
"""Smoke-test turbulence length-scale metadata identity binding."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CREATE_SCRIPT = REPO / "scripts" / "create_turbulence_length_scale_evidence_template.py"
BIND_SCRIPT = REPO / "scripts" / "bind_turbulence_length_scale_metadata.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_bind_length_scale_") as raw:
        temp = Path(raw)
        metadata = temp / "case_metadata.json"
        source = temp / "aij_length_scale_source.txt"
        evidence = temp / "turbulence_length_scale_evidence.json"
        out = temp / "case_metadata.length_scale_bound.json"
        metadata.write_text(
            json.dumps(
                {
                    "AijCase": "AIJ Case E ac + N",
                    "WindDirection": "N",
                    "SyntheticTurbulenceCorrelationCells": 4.0,
                    "grid": {"dx_m": 3.0},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        source.write_text("paper-admissible AIJ length-scale extraction note\n", encoding="utf-8")
        created = run_script(
            CREATE_SCRIPT,
            "--metadata",
            str(metadata),
            "--source-path",
            str(source),
            "--source-type",
            "official_aij",
            "--source-note",
            "Smoke-test official AIJ source.",
            "--paper-admissible",
            "--case",
            "CaseE",
            "--wind-direction",
            "N",
            "--out",
            str(evidence),
        )
        if created.returncode != 0:
            raise AssertionError((created.returncode, created.stdout, created.stderr))
        bound_result = run_script(
            BIND_SCRIPT,
            "--metadata",
            str(metadata),
            "--evidence-json",
            str(evidence),
            "--out",
            str(out),
        )
        if bound_result.returncode != 0:
            raise AssertionError((bound_result.returncode, bound_result.stdout, bound_result.stderr))
        bound = load_json(out)
        expected_hash = hashlib.sha256(evidence.read_bytes()).hexdigest()
        record = bound["TurbulenceLengthScale"]
        if record["EvidenceJsonSha256"] != expected_hash:
            raise AssertionError(record)
        if record["EvidenceGate"] != "pass":
            raise AssertionError(record)
        if bound["SyntheticTurbulentInletLengthScaleGate"] != "pass":
            raise AssertionError(bound)
        if bound["SyntheticTurbulenceLengthScaleSource"] != "aij_length_scale_verified":
            raise AssertionError(bound)

    print("bind_turbulence_length_scale_metadata_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
