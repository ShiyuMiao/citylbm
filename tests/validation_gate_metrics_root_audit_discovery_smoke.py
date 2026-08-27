#!/usr/bin/env python3
"""Smoke-test validation_gate finds audits beside metrics/probe files."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


AUDIT_NAMES = {
    "validation_protocol_audit": "validation_protocol_audit.json",
    "inlet_source_audit": "inlet_source_audit.json",
    "boundary_source_audit": "boundary_source_audit.json",
    "inlet_correlation_audit": "inlet_correlation_audit.json",
    "boundary_protocol_audit": "boundary_protocol_audit.json",
    "boundary_runtime_audit": "boundary_runtime_audit.json",
    "component_sensitivity_audit": "component_sensitivity_audit.json",
    "native_preconditions_audit": "native_preconditions_audit.json",
    "native_fluidx3d_baseline_manifest": "native_fluidx3d_baseline_manifest.json",
}


def write_json(path: Path, data: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data or {}, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_validation_gate_roots_") as tmp:
        root = Path(tmp)
        solver_cwd = root / "solver_cwd"
        chain = root / "validation_chain_casea"
        metrics = chain / "validation_metrics.csv"
        probe = chain / "probe_audit.csv"
        report_path = root / "validation_gate_report.json"
        solver_cwd.mkdir(parents=True)

        write_json(solver_cwd / "case_metadata.json", {"Software": "native-fluidx3d"})
        for name in AUDIT_NAMES.values():
            write_json(chain / name)
        write_json(chain / "native_run_audit.json")
        write_csv(metrics, [{"case": "CaseA", "software": "native-fluidx3d"}])
        write_csv(probe, [{"probe_id": "P1", "failed": "false", "compared_component": "speed_ratio"}])

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_gate.py"),
                str(solver_cwd),
                "--metrics",
                str(metrics),
                "--probe-audit",
                str(probe),
                "--out",
                str(report_path),
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 2:
            raise AssertionError(
                f"Expected validation failure with discovered artifacts, got {completed.returncode}\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        artifacts = report.get("artifacts", {})
        for key, filename in AUDIT_NAMES.items():
            expected = str((chain / filename).resolve())
            if artifacts.get(key) != expected:
                raise AssertionError({"key": key, "expected": expected, "actual": artifacts.get(key)})
        if artifacts.get("runtime_audit") != str((chain / "native_run_audit.json").resolve()):
            raise AssertionError(artifacts)
        if artifacts.get("metrics") != str(metrics.resolve()):
            raise AssertionError(artifacts)
        if artifacts.get("probe_audit") != str(probe.resolve()):
            raise AssertionError(artifacts)

    print("validation_gate_metrics_root_audit_discovery_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
