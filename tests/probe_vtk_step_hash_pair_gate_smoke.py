#!/usr/bin/env python3
"""Smoke-test probe VTK source time-step/hash pair provenance gating."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
HASH_A = "a" * 64
HASH_B = "b" * 64


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != 0:
        raise AssertionError(
            f"Command failed with {completed.returncode}: {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def write_probe(path: Path, source_hashes: str) -> None:
    rows = [
        {
            "probe_id": "P1",
            "x": "0",
            "y": "0",
            "z": "2",
            "compared_value": "1.0",
            "failed": "false",
            "validation_status": "pass",
            "nearest_distance": "0",
            "normalization_valid": "true",
            "wind_direction_valid": "true",
            "Uref": "1.0",
            "compared_component": "speed_ratio",
            "tolerance": "0.1",
            "inside_vtk_grid_extent": "true",
            "vtk_source_time_steps": "1000,1100",
            "vtk_source_step_span": "100",
            "minimum_validation_average_step_span": "100",
            "vtk_source_sha256": source_hashes,
            "official_probe_set_row_count": "2",
            "official_expected_row_count": "2",
            "official_probe_ids_unique": "true",
            "official_missing_probe_id_count": "0",
            "official_duplicate_probe_ids": "",
            "official_expected_z": "2",
            "official_expected_z_tolerance": "0",
            "official_z_match_count": "2",
            "official_z_mismatch_count": "0",
        },
        {
            "probe_id": "P2",
            "x": "1",
            "y": "0",
            "z": "2",
            "compared_value": "0.8",
            "failed": "false",
            "validation_status": "pass",
            "nearest_distance": "0",
            "normalization_valid": "true",
            "wind_direction_valid": "true",
            "Uref": "1.0",
            "compared_component": "speed_ratio",
            "tolerance": "0.1",
            "inside_vtk_grid_extent": "true",
            "vtk_source_time_steps": "1000,1100",
            "vtk_source_step_span": "100",
            "minimum_validation_average_step_span": "100",
            "vtk_source_sha256": source_hashes,
            "official_probe_set_row_count": "2",
            "official_expected_row_count": "2",
            "official_probe_ids_unique": "true",
            "official_missing_probe_id_count": "0",
            "official_duplicate_probe_ids": "",
            "official_expected_z": "2",
            "official_expected_z_tolerance": "0",
            "official_z_match_count": "2",
            "official_z_mismatch_count": "0",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def metrics_command(probe: Path, official: Path, read_vtk: Path, out: Path) -> list[str]:
    return [
        sys.executable,
        str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
        "--probe-audit",
        str(probe),
        "--official",
        str(official),
        "--read-vtk-audit",
        str(read_vtk),
        "--out",
        str(out),
        "--case",
        "CaseE",
        "--wind-direction",
        "N",
        "--u-ref",
        "1.0",
    ]


def read_metric(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise AssertionError(f"Expected one metrics row, got {len(rows)}")
    return rows[0]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_probe_step_hash_gate_") as tmp:
        root = Path(tmp)
        official = root / "official.csv"
        read_vtk = root / "read_vtk_audit.json"
        probe_pass = root / "probe_pass.csv"
        probe_bad_pair = root / "probe_bad_pair.csv"
        metrics_pass = root / "metrics_pass.csv"
        metrics_bad_pair = root / "metrics_bad_pair.csv"

        write_text(
            official,
            """case,wind_direction,No.,x,y,z,Velocity_Ratio
CaseE,N,P1,0,0,2,1.0
CaseE,N,P2,1,0,2,0.8
""",
        )
        write_json(
            read_vtk,
            {
                "source_time_steps": [1000, 1100],
                "source_vtk_sha256": [HASH_A, HASH_B],
                "source_step_span": 100,
                "minimum_validation_average_step_span": 100,
            },
        )
        write_probe(probe_pass, f"{HASH_A};{HASH_B}")
        write_probe(probe_bad_pair, f"{HASH_B};{HASH_A}")

        run_command(metrics_command(probe_pass, official, read_vtk, metrics_pass))
        row = read_metric(metrics_pass)
        expected_pairs = f"1000:{HASH_A};1100:{HASH_B}"
        if row["probe_vtk_source_window_gate"] != "pass":
            raise AssertionError(row["probe_vtk_source_window_reasons"])
        if row["probe_vtk_expected_source_step_hash_pairs"] != expected_pairs:
            raise AssertionError(row["probe_vtk_expected_source_step_hash_pairs"])
        if row["probe_vtk_source_step_hash_pairs"] != expected_pairs:
            raise AssertionError(row["probe_vtk_source_step_hash_pairs"])
        if row["probe_vtk_source_step_hash_pair_set_count"] != "1":
            raise AssertionError(row["probe_vtk_source_step_hash_pair_set_count"])

        run_command(metrics_command(probe_bad_pair, official, read_vtk, metrics_bad_pair))
        bad_row = read_metric(metrics_bad_pair)
        reasons = bad_row["probe_vtk_source_window_reasons"]
        if bad_row["probe_vtk_source_window_gate"] != "fail":
            raise AssertionError(bad_row["probe_vtk_source_window_gate"])
        if "probe_source_step_hash_pairs_do_not_match_metrics_source_window" not in reasons:
            raise AssertionError(reasons)
        if "probe_source_step_hash_pair_mismatch:2" not in reasons:
            raise AssertionError(reasons)

    print("probe_vtk_step_hash_pair_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
