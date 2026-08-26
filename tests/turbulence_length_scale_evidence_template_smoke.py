#!/usr/bin/env python3
"""Smoke-test turbulence length-scale evidence generation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "create_turbulence_length_scale_evidence_template.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        metadata = temp / "case_metadata.json"
        metadata.write_text(
            json.dumps(
                {
                    "AijCase": "AIJ Case E ac + N",
                    "WindDirection": "N",
                    "SyntheticTurbulenceCorrelationCells": 4.0,
                    "SyntheticTurbulenceCorrelationLengthM": 12.0,
                    "grid": {"dx_m": 3.0},
                }
            ),
            encoding="utf-8",
        )

        draft_out = temp / "draft.json"
        draft = run_script(
            "--metadata",
            str(metadata),
            "--case",
            "CaseE",
            "--wind-direction",
            "N",
            "--out",
            str(draft_out),
        )
        if draft.returncode != 0:
            raise AssertionError((draft.returncode, draft.stdout, draft.stderr))
        draft_payload = load(draft_out)
        if draft_payload["paper_grade_gate"] != "fail":
            raise AssertionError(draft_payload)
        if "length_scale_source_file_missing" not in draft_payload["reasons"]:
            raise AssertionError(draft_payload)
        if draft_payload["current_length_scale_settings"]["correlation_length_m"] != 12.0:
            raise AssertionError(draft_payload)

        source = temp / "aij_length_scale_note.txt"
        source.write_text("AIJ length-scale extraction note for smoke test.\n", encoding="utf-8")
        pass_out = temp / "pass.json"
        passed = run_script(
            "--metadata",
            str(metadata),
            "--source-path",
            str(source),
            "--source-type",
            "official_aij",
            "--source-note",
            "Smoke-test official AIJ length-scale evidence.",
            "--paper-admissible",
            "--case",
            "CaseE",
            "--wind-direction",
            "N",
            "--out",
            str(pass_out),
        )
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr))
        pass_payload = load(pass_out)
        if pass_payload["paper_grade_gate"] != "pass":
            raise AssertionError(pass_payload)
        patch = pass_payload["suggested_citylbm_metadata_patch"]
        if patch["SyntheticTurbulenceLengthScaleSource"] != "aij_length_scale_verified":
            raise AssertionError(pass_payload)
        if not pass_payload["source_sha256"]:
            raise AssertionError(pass_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
