#!/usr/bin/env python3
"""Smoke-test official probe-set gates in VTK probe sampling."""

from __future__ import annotations

import csv
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_command(args: list[str], expect_ok: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True)
    if expect_ok and completed.returncode != 0:
        raise AssertionError(
            f"Command failed with {completed.returncode}: {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    if not expect_ok and completed.returncode == 0:
        raise AssertionError(f"Command unexpectedly passed: {' '.join(args)}")
    return completed


def write_vtk(path: Path) -> None:
    write_text(
        path,
        """# vtk DataFile Version 3.0
official probe set smoke
ASCII
DATASET STRUCTURED_POINTS
DIMENSIONS 2 2 3
ORIGIN 0 0 0
SPACING 1 1 1
POINT_DATA 12
VECTORS velocity float
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
1 0 0
""",
    )


def probe_args(vtk: Path, official: Path, out: Path, *extra: str) -> list[str]:
    return [
        sys.executable,
        str(REPO / "scripts" / "probe_vtk_points.py"),
        str(vtk),
        "--official",
        str(official),
        "--out",
        str(out),
        "--case",
        "ac",
        "--wind-direction-label",
        "N",
        "--wind-direction",
        "1,0,0",
        "--u-ref",
        "1",
        "--average-last-n",
        "1",
        "--min-avg-frames",
        "1",
        "--min-avg-step-span",
        "0",
        "--expected-row-count",
        "2",
        "--expected-z",
        "2.0",
        *extra,
    ]


def assert_failed_with(completed: subprocess.CompletedProcess[str], expected: str) -> None:
    message = completed.stdout + completed.stderr
    if expected not in message:
        raise AssertionError(f"Expected {expected!r} in:\n{message}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_probe_set_gate_") as tmp:
        root = Path(tmp)
        vtk = root / "u-000001000.vtk"
        official = root / "official.csv"
        out = root / "probe_audit.csv"
        metrics = root / "metrics.csv"
        write_vtk(vtk)
        write_text(
            official,
            """case,wind_direction,No.,x,y,z,Velocity_Ratio
ac,N,P1,0,0,2,1
ac,N,P2,1,1,2,1
bc,N,B1,0,0,2,1
""",
        )
        run_command(probe_args(vtk, official, out))
        with out.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 2:
            raise AssertionError(f"Expected 2 rows, got {len(rows)}")
        first = rows[0]
        expected_fields = {
            "official_probe_set_row_count": "2",
            "official_expected_row_count": "2",
            "official_probe_ids_unique": "true",
            "official_expected_z": "2",
            "official_z_match_count": "2",
            "official_z_mismatch_count": "0",
        }
        for key, expected in expected_fields.items():
            if first[key] != expected:
                raise AssertionError(f"{key}: {first[key]} != {expected}")

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
                "--probe-audit",
                str(out),
                "--official",
                str(official),
                "--out",
                str(metrics),
                "--case",
                "ac",
                "--wind-direction",
                "N",
                "--u-ref",
                "1",
            ]
        )
        with metrics.open("r", encoding="utf-8", newline="") as handle:
            metrics_rows = list(csv.DictReader(handle))
        if len(metrics_rows) != 1:
            raise AssertionError(f"Expected one metrics row, got {len(metrics_rows)}")
        metrics_row = metrics_rows[0]
        for key, expected in {
            "official_probe_set_gate": "pass",
            "official_probe_set_row_count": "2",
            "official_expected_row_count": "2",
            "official_probe_ids_unique": "true",
            "official_expected_z_m": "2",
            "official_z_match_count": "2",
            "official_z_mismatch_count": "0",
        }.items():
            if metrics_row[key] != expected:
                raise AssertionError(f"metrics {key}: {metrics_row[key]} != {expected}")

        wrong_count = run_command(probe_args(vtk, official, root / "wrong_count.csv", "--expected-row-count", "80"), expect_ok=False)
        assert_failed_with(wrong_count, "official_row_count_2_does_not_match_expected_80")

        duplicate = root / "official_duplicate.csv"
        write_text(
            duplicate,
            """case,wind_direction,No.,x,y,z,Velocity_Ratio
ac,N,P1,0,0,2,1
ac,N,P1,1,1,2,1
""",
        )
        duplicate_run = run_command(probe_args(vtk, duplicate, root / "duplicate.csv"), expect_ok=False)
        assert_failed_with(duplicate_run, "duplicate_probe_ids:P1")

        bad_z = root / "official_bad_z.csv"
        write_text(
            bad_z,
            """case,wind_direction,No.,x,y,z,Velocity_Ratio
ac,N,P1,0,0,2,1
ac,N,P2,1,1,2.5,1
""",
        )
        bad_z_run = run_command(probe_args(vtk, bad_z, root / "bad_z.csv"), expect_ok=False)
        assert_failed_with(bad_z_run, "official_z_mismatch_count_1")

    print("probe_vtk_official_set_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
