#!/usr/bin/env python3
"""Smoke-test VTK probe component projection and sensitivity audit."""

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


def assert_close(actual: str, expected: float, eps: float = 1.0e-9) -> None:
    value = float(actual)
    if abs(value - expected) > eps:
        raise AssertionError(f"{actual} != {expected}")


def run_command(args: list[str]) -> None:
    completed = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != 0:
        raise AssertionError(
            f"Command failed with {completed.returncode}: {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_probe_projection_") as tmp:
        root = Path(tmp)
        vtk = root / "u-000001000.vtk"
        official = root / "official.csv"
        mapped_official = root / "mapped_official.csv"
        probe_audit = root / "probe_audit.csv"
        mapped_probe_audit = root / "mapped_probe_audit.csv"
        physical_probe_audit = root / "physical_probe_audit.csv"
        sensitivity_json = root / "component_sensitivity.json"
        physical_official = root / "physical_official.csv"
        physical_sensitivity_json = root / "physical_component_sensitivity.json"
        domain_origin = root / "domain_origin.json"

        write_text(
            vtk,
            """# vtk DataFile Version 3.0
component projection smoke
ASCII
DATASET STRUCTURED_POINTS
DIMENSIONS 2 2 1
ORIGIN 0 0 0
SPACING 1 1 1
POINT_DATA 4
VECTORS velocity float
0 -2 0
0 2 0
2 0 0
0 -1 0
""",
        )
        write_text(
            official,
            """No.,x,y,z,Velocity_Ratio
P1,0,0,0,1
P2,1,0,0,1
P3,0,1,0,0
P4,1,1,0,0.5
""",
        )
        write_text(
            mapped_official,
            """No.,x,y,z,Velocity_Ratio
M1,0.5,0,0,1
""",
        )
        write_text(
            physical_official,
            """No.,x,y,z,U(m/s)
P1,0,0,0,2
P2,1,0,0,-2
P3,0,1,0,0
P4,1,1,0,1
""",
        )
        write_text(
            domain_origin,
            """{
  "DomainMinX": 0.0,
  "DomainMinY": 0.0,
  "DomainMinZ": 0.0,
  "Dx": 0.5
}
""",
        )

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "probe_vtk_points.py"),
                str(vtk),
                "--official",
                str(official),
                "--out",
                str(probe_audit),
                "--wind-direction",
                "0,-1,0",
                "--u-ref",
                "2",
                "--compared-component",
                "abs_streamwise_ratio",
                "--interpolation",
                "nearest",
                "--average-last-n",
                "1",
                "--min-avg-frames",
                "1",
                "--min-avg-step-span",
                "0",
            ]
        )

        with probe_audit.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 4:
            raise AssertionError(f"Expected 4 probe rows, got {len(rows)}")
        first, second, third, fourth = rows
        assert_close(first["streamwise_ratio"], 1.0)
        assert_close(second["streamwise_ratio"], -1.0)
        assert_close(second["abs_streamwise_ratio"], 1.0)
        assert_close(third["lateral_ratio"], 1.0)
        assert_close(fourth["compared_value"], 0.5)
        if first["component_projection_basis"] != "speed_or_velocity_dot_airflow_unit_vector":
            raise AssertionError("Missing component projection basis evidence.")

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "probe_vtk_points.py"),
                str(vtk),
                "--official",
                str(mapped_official),
                "--out",
                str(mapped_probe_audit),
                "--wind-direction",
                "0,1,0",
                "--u-ref",
                "2",
                "--compared-component",
                "abs_streamwise_ratio",
                "--interpolation",
                "nearest",
                "--average-last-n",
                "1",
                "--min-avg-frames",
                "1",
                "--min-avg-step-span",
                "0",
                "--domain-origin",
                str(domain_origin),
            ]
        )
        with mapped_probe_audit.open("r", encoding="utf-8", newline="") as handle:
            mapped_rows = list(csv.DictReader(handle))
        mapped_first = mapped_rows[0]
        if mapped_first["coordinate_mapping"] != "domain_origin_json_world_m_to_vtk_lattice":
            raise AssertionError("Missing domain-origin coordinate mapping evidence.")
        assert_close(mapped_first["x"], 1.0)
        assert_close(mapped_first["nearest_grid_x"], 1.0)
        assert_close(mapped_first["compared_value"], 1.0)

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_component_sensitivity.py"),
                "--probe-audit",
                str(probe_audit),
                "--official",
                str(official),
                "--out-json",
                str(sensitivity_json),
                "--selected-component",
                "abs_streamwise_ratio",
                "--case",
                "CaseA",
                "--wind-direction",
                "N",
            ]
        )
        report = json.loads(sensitivity_json.read_text(encoding="utf-8"))
        if report["best_component_by_rmse"] != "abs_streamwise_ratio":
            raise AssertionError(report["best_component_by_rmse"])
        if report["component_normalization_gate"] != "pass":
            raise AssertionError(report["component_normalization_gate"])

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "probe_vtk_points.py"),
                str(vtk),
                "--official",
                str(physical_official),
                "--out",
                str(physical_probe_audit),
                "--wind-direction",
                "0,-1,0",
                "--u-ref",
                "2",
                "--compared-component",
                "streamwise_velocity",
                "--interpolation",
                "nearest",
                "--average-last-n",
                "1",
                "--min-avg-frames",
                "1",
                "--min-avg-step-span",
                "0",
            ]
        )

        run_command(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_component_sensitivity.py"),
                "--probe-audit",
                str(physical_probe_audit),
                "--official",
                str(physical_official),
                "--out-json",
                str(physical_sensitivity_json),
                "--selected-component",
                "streamwise_velocity",
                "--case",
                "CaseA",
                "--wind-direction",
                "N",
            ]
        )
        physical_report = json.loads(physical_sensitivity_json.read_text(encoding="utf-8"))
        if physical_report["official_value_column"] != "U(m/s)":
            raise AssertionError(physical_report["official_value_column"])
        if physical_report["selected_component"] != "streamwise_velocity":
            raise AssertionError(physical_report["selected_component"])

    print("probe_vtk_component_projection_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
