#!/usr/bin/env python3
"""Smoke-test acceleration planner priority for CustomProfile/AF mismatch."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PLANNER = REPO / "scripts" / "plan_validation_acceleration.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_plan_profile_gate_") as raw:
        temp = Path(raw)
        run_dir = temp / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        write(
            run_dir / "custom_profile_af_fidelity_audit.json",
            json.dumps(
                {
                    "schema": "citylbm.custom_profile_af_fidelity.v1",
                    "Gate": "fail",
                    "Reasons": [
                        "custom_profile_rows_below_minimum:3<5",
                        "k_mae_ratio_above_threshold:0.37>0.1",
                    ],
                },
                indent=2,
            ),
        )
        out_json = temp / "plan.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(PLANNER),
                "--case",
                "casea",
                "--run-dir",
                str(run_dir),
                "--out-json",
                str(out_json),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))
        plan = load(out_json)
        action = plan["runs"][0]["recommended_next_action"]
        if action["phase"] != "fix_official_af_profile_ingestion":
            raise AssertionError(action)
        failures = ";".join(plan["runs"][0]["failures"])
        if "custom_profile_af_fidelity_audit.json:fail" not in failures:
            raise AssertionError(plan["runs"][0]["failures"])
        command = plan["command_templates"].get("audit_custom_profile_against_af", "")
        if "audit_custom_profile_against_af.py" not in command:
            raise AssertionError(plan["command_templates"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
