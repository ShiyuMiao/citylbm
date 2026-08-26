#!/usr/bin/env python3
"""Smoke-test metrics protocol failure for stale probe Uref values."""

from __future__ import annotations

import csv
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
    with tempfile.TemporaryDirectory(prefix="citylbm_metrics_uref_") as tmp:
        root = Path(tmp)
        probe = root / "probe_audit.csv"
        official = root / "official.csv"
        metrics = root / "metrics.csv"
        read_vtk_audit = root / "read_vtk_audit.json"

        write_text(
            official,
            """No.,case,wind_direction,x,y,z,Velocity_Ratio
P1,ac,N,0,0,2,0.50
P2,ac,N,1,0,2,0.75
""",
        )
        write_text(
            probe,
            """probe_id,x,y,z,compared_value,failed,validation_status,inside_vtk_grid_extent,normalization_valid,wind_direction_valid,Uref,compared_component,nearest_distance,vtk_source_time_steps,vtk_source_step_span,minimum_validation_average_step_span,vtk_source_sha256,vtk_source_step_hash_pairs
P1,0,0,2,0.50,false,pass,true,true,true,4.0,speed_ratio,0.0,1000;2000,1000,1000,aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,1000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;2000:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
P2,1,0,2,0.75,false,pass,true,true,true,4.0,speed_ratio,0.0,1000;2000,1000,1000,aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,1000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa;2000:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
""",
        )
        read_vtk_audit.write_text(
            json.dumps(
                {
                    "source_time_steps_csv": "1000;2000",
                    "source_vtk_sha256": [
                        "a" * 64,
                        "b" * 64,
                    ],
                    "minimum_validation_average_step_span": 1000,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
                "--probe-audit",
                str(probe),
                "--official",
                str(official),
                "--out",
                str(metrics),
                "--read-vtk-audit",
                str(read_vtk_audit),
                "--case",
                "ac",
                "--wind-direction",
                "N",
                "--source-time-steps",
                "1000;2000",
                "--u-ref",
                "3.928296",
            ],
            cwd=str(REPO),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + "\n" + completed.stderr)

        with metrics.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 1:
            raise AssertionError(f"Expected one metrics row, got {len(rows)}")
        row = rows[0]
        if row.get("protocol_gate") != "fail_probe_uref_mismatch":
            raise AssertionError(row.get("protocol_gate"))
        if row.get("probe_uref_expected_mps") != "3.928296":
            raise AssertionError(row.get("probe_uref_expected_mps"))
        if row.get("probe_uref_values") != "4":
            raise AssertionError(row.get("probe_uref_values"))
        if row.get("probe_uref_mismatch_count") != "2":
            raise AssertionError(row.get("probe_uref_mismatch_count"))

        missing_expected_metrics = root / "metrics_missing_expected.csv"
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
                "--probe-audit",
                str(probe),
                "--official",
                str(official),
                "--out",
                str(missing_expected_metrics),
                "--read-vtk-audit",
                str(read_vtk_audit),
                "--case",
                "ac",
                "--wind-direction",
                "N",
                "--source-time-steps",
                "1000;2000",
            ],
            cwd=str(REPO),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + "\n" + completed.stderr)

        with missing_expected_metrics.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        row = rows[0]
        if "fail_missing_expected_uref" not in row.get("protocol_gate", ""):
            raise AssertionError(row.get("protocol_gate"))
        if row.get("probe_uref_expected_mps") != "":
            raise AssertionError(row.get("probe_uref_expected_mps"))

    print("validation_metrics_uref_protocol_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
