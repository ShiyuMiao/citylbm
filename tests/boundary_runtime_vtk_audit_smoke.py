#!/usr/bin/env python3
"""Smoke test for boundary-runtime VTK audit on a uniform empty-tunnel field."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def write_vtk(path: Path, vector: tuple[float, float, float]) -> None:
    nx, ny, nz = 3, 3, 3
    payload = "\n".join(
        f"{vector[0]:.6f} {vector[1]:.6f} {vector[2]:.6f}"
        for _ in range(nx * ny * nz)
    )
    path.write_text(
        "\n".join(
            [
                "# vtk DataFile Version 3.0",
                "CityLBM boundary runtime smoke",
                "ASCII",
                "DATASET STRUCTURED_POINTS",
                f"DIMENSIONS {nx} {ny} {nz}",
                "ORIGIN 0 0 0",
                "SPACING 1 1 1",
                f"POINT_DATA {nx * ny * nz}",
                "VECTORS velocity float",
                payload,
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    script = repo / "scripts" / "audit_boundary_runtime_from_vtk.py"
    with tempfile.TemporaryDirectory(prefix="citylbm_boundary_runtime_") as tmp:
        tmp_dir = Path(tmp)
        vtk_dir = tmp_dir / "vtk"
        vtk_dir.mkdir()
        for step in [1000, 2000, 3000]:
            write_vtk(vtk_dir / f"u-{step:09d}.vtk", (1.0, 0.0, 0.0))
        af_csv = tmp_dir / "AF.csv"
        af_csv.write_text("z,U,k\n0,1,0.1\n1,1,0.1\n2,1,0.1\n", encoding="utf-8")
        report = tmp_dir / "boundary_runtime_audit.json"
        summary_csv = tmp_dir / "boundary_runtime_audit.csv"

        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                str(vtk_dir),
                "--af-csv",
                str(af_csv),
                "--wind-direction",
                "1,0,0",
                "--average-last-n",
                "3",
                "--min-frames",
                "3",
                "--min-step-span",
                "2000",
                "--out-json",
                str(report),
                "--out-csv",
                str(summary_csv),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + "\n" + completed.stderr)
        data = json.loads(report.read_text(encoding="utf-8"))
        require(data.get("boundary_runtime_gate") == "pass", data)
        require(data.get("boundary_runtime_traceability_gate") == "pass", data)
        require(data.get("boundary_runtime_inlet_gate") == "pass", data)
        require(data.get("boundary_runtime_side_top_gate") == "pass", data)
        require(data.get("boundary_runtime_side_top_normal_leakage_gate") == "pass", data)
        require(data.get("max_side_top_normal_velocity_ratio") == 0.0, data)
        require(data.get("boundary_runtime_outlet_gate") == "pass", data)
        require(len(data.get("faces", [])) == 5, data)
        require(summary_csv.exists(), data)

        bad_vtk_dir = tmp_dir / "vtk_bad"
        bad_vtk_dir.mkdir()
        for step in [1000, 2000, 3000]:
            write_vtk(bad_vtk_dir / f"u-{step:09d}.vtk", (1.0, 0.3, 0.0))
        bad_report = tmp_dir / "boundary_runtime_audit_bad.json"
        bad_completed = subprocess.run(
            [
                sys.executable,
                str(script),
                str(bad_vtk_dir),
                "--af-csv",
                str(af_csv),
                "--wind-direction",
                "1,0,0",
                "--average-last-n",
                "3",
                "--min-frames",
                "3",
                "--min-step-span",
                "2000",
                "--out-json",
                str(bad_report),
            ],
            cwd=str(repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if bad_completed.returncode == 0:
            raise AssertionError(bad_completed.stdout + "\n" + bad_completed.stderr)
        bad_data = json.loads(bad_report.read_text(encoding="utf-8"))
        require(bad_data.get("boundary_runtime_gate") == "fail", bad_data)
        require(bad_data.get("boundary_runtime_side_top_gate") == "pass", bad_data)
        require(bad_data.get("boundary_runtime_side_top_normal_leakage_gate") == "fail", bad_data)
        require(float(bad_data.get("max_side_top_normal_velocity_ratio")) > 0.1, bad_data)

    print("boundary_runtime_vtk_audit_smoke passed")
    return 0


def require(condition: bool, data: dict) -> None:
    if not condition:
        raise AssertionError(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
