#!/usr/bin/env python3
"""Smoke-test that official probe sampling refuses VTK without explicit grid metadata."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_probe(vtk: Path, official: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "probe_vtk_points.py"),
            str(vtk),
            "--official",
            str(official),
            "--out",
            str(out),
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
        ],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def assert_failed_with(completed: subprocess.CompletedProcess[str], expected: str) -> None:
    if completed.returncode == 0:
        raise AssertionError("probe_vtk_points.py unexpectedly accepted invalid VTK metadata")
    message = completed.stdout + completed.stderr
    if expected not in message:
        raise AssertionError(f"Expected {expected!r} in:\n{message}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_probe_grid_metadata_") as tmp:
        root = Path(tmp)
        official = root / "official.csv"
        write_text(official, "No.,x,y,z,Velocity_Ratio\nP1,0,0,0,1\n")

        missing_origin = root / "u-000001000_missing_origin.vtk"
        write_text(
            missing_origin,
            """# vtk DataFile Version 3.0
missing origin
ASCII
DATASET STRUCTURED_POINTS
DIMENSIONS 1 1 1
SPACING 1 1 1
POINT_DATA 1
VECTORS velocity float
1 0 0
""",
        )
        assert_failed_with(
            run_probe(missing_origin, official, root / "missing_origin.csv"),
            "VTK ORIGIN missing",
        )

        missing_spacing = root / "u-000001000_missing_spacing.vtk"
        write_text(
            missing_spacing,
            """# vtk DataFile Version 3.0
missing spacing
ASCII
DATASET STRUCTURED_POINTS
DIMENSIONS 1 1 1
ORIGIN 0 0 0
POINT_DATA 1
VECTORS velocity float
1 0 0
""",
        )
        assert_failed_with(
            run_probe(missing_spacing, official, root / "missing_spacing.csv"),
            "VTK SPACING missing",
        )

    print("probe_vtk_requires_grid_metadata_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
