#!/usr/bin/env python3
"""Smoke-test component sensitivity source-window provenance gating."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_command(args: list[str], expected: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != expected:
        raise AssertionError(
            f"Expected {expected}, got {completed.returncode}: {' '.join(args)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def write_probe(path: Path, vtk_a: Path, vtk_b: Path, bad_hash: bool = False) -> None:
    hashes = [sha256(vtk_a), sha256(vtk_b)]
    if bad_hash:
        hashes[1] = "0" * 64
    rows = [
        {
            "probe_id": "P1",
            "failed": "false",
            "out_of_tolerance": "false",
            "speed_ratio": "1.0",
            "streamwise_ratio": "1.0",
            "compared_component": "speed_ratio",
            "vtk_source_time_steps": "1000,1100",
            "vtk_source_step_span": "100",
            "minimum_validation_average_step_span": "100",
            "vtk_source_files": f"{vtk_a};{vtk_b}",
            "vtk_source_sha256": ";".join(hashes),
        },
        {
            "probe_id": "P2",
            "failed": "false",
            "out_of_tolerance": "false",
            "speed_ratio": "0.5",
            "streamwise_ratio": "0.5",
            "compared_component": "speed_ratio",
            "vtk_source_time_steps": "1000,1100",
            "vtk_source_step_span": "100",
            "minimum_validation_average_step_span": "100",
            "vtk_source_files": f"{vtk_a};{vtk_b}",
            "vtk_source_sha256": ";".join(hashes),
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_component_source_gate_") as tmp:
        root = Path(tmp)
        vtk_a = root / "u-000001000.vtk"
        vtk_b = root / "u-000001100.vtk"
        official = root / "official.csv"
        probe = root / "probe.csv"
        bad_probe = root / "probe_bad_hash.csv"
        report = root / "component.json"
        bad_report = root / "component_bad_hash.json"

        write_text(vtk_a, "frame 1000\n")
        write_text(vtk_b, "frame 1100\n")
        write_text(official, "No.,Velocity_Ratio\nP1,1.0\nP2,0.5\n")
        write_probe(probe, vtk_a, vtk_b)
        write_probe(bad_probe, vtk_a, vtk_b, bad_hash=True)

        base_cmd = [
            sys.executable,
            str(REPO / "scripts" / "audit_component_sensitivity.py"),
            "--official",
            str(official),
            "--selected-component",
            "speed_ratio",
            "--min-source-step-span",
            "100",
            "--expected-source-time-steps",
            "1000,1100",
        ]
        run_command(
            base_cmd
            + [
                "--probe-audit",
                str(probe),
                "--out-json",
                str(report),
            ]
        )
        passed = json.loads(report.read_text(encoding="utf-8"))
        if passed["component_source_window_gate"] != "pass":
            raise AssertionError(passed["component_source_window_gate_reasons"])

        run_command(
            base_cmd
            + [
                "--probe-audit",
                str(bad_probe),
                "--out-json",
                str(bad_report),
            ],
            expected=2,
        )
        failed = json.loads(bad_report.read_text(encoding="utf-8"))
        reasons = failed["component_source_window_gate_reasons"]
        if "source_vtk_file_hash_mismatch" not in reasons:
            raise AssertionError(reasons)

    print("component_source_window_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
