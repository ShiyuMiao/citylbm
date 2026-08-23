#!/usr/bin/env python3
"""Smoke-test critical native/CityLBM parity field coverage."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_metrics(path: Path, software: str, audit_module, *, missing_field: str = "") -> None:
    fields = sorted(
        {
            "software",
            *audit_module.TEXT_FIELDS,
            *audit_module.GATE_FIELDS,
            *audit_module.HASH_FIELDS,
            *audit_module.NUMERIC_FIELDS,
        }
    )
    row = {field: "same" for field in fields}
    row.update(
        {
            "software": software,
            "case": "CaseA",
            "wind_direction": "N",
        }
    )
    for field in audit_module.GATE_FIELDS:
        row[field] = "pass"
    for field in audit_module.HASH_FIELDS:
        row[field] = "a" * 64
    for field in audit_module.NUMERIC_FIELDS:
        row[field] = "1"
    if missing_field:
        row[missing_field] = ""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def run_parity_audit(audit_script: Path, city: Path, native: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(audit_script),
            "--citylbm-metrics",
            str(city),
            "--native-metrics",
            str(native),
            "--out",
            str(out),
            "--case",
            "CaseA",
            "--wind-direction",
            "N",
        ],
        cwd=str(REPO),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    gate_module = load_module("validation_gate", REPO / "scripts" / "validation_gate.py")
    audit_module = load_module(
        "audit_native_citylbm_parity",
        REPO / "scripts" / "audit_native_citylbm_parity.py",
    )

    with tempfile.TemporaryDirectory(prefix="citylbm_parity_critical_") as tmp:
        tmp_path = Path(tmp)
        city = tmp_path / "city.csv"
        native = tmp_path / "native.csv"
        out = tmp_path / "native_citylbm_parity_audit.json"
        write_metrics(city, "citylbm", audit_module)
        write_metrics(native, "native-fluidx3d", audit_module)
        passed = run_parity_audit(REPO / "scripts" / "audit_native_citylbm_parity.py", city, native, out)
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr))
        report = json.loads(out.read_text(encoding="utf-8"))
        if report["critical_parity_field_gate"] != "pass":
            raise AssertionError(report)
        for field in [
            "synthetic_temporal_sampling_gate",
            "synthetic_expected_final_window_refresh_count",
            "inlet_source_has_k_driven_three_component_stg",
            "boundary_runtime_side_top_normal_leakage_gate",
        ]:
            if field not in report["required_critical_fields"]:
                raise AssertionError((field, report["required_critical_fields"]))
        status = gate_module.native_citylbm_parity_critical_status(report)
        if not status["ok"]:
            raise AssertionError(status)

        legacy = dict(report)
        for key in [
            "critical_parity_field_gate",
            "required_critical_fields",
            "required_critical_field_count",
            "matched_critical_field_count",
            "missing_critical_fields",
        ]:
            legacy.pop(key, None)
        legacy_status = gate_module.native_citylbm_parity_critical_status(legacy)
        if legacy_status["ok"]:
            raise AssertionError(legacy_status)
        if "critical_parity_field_gate_not_pass:missing" not in legacy_status["reasons"]:
            raise AssertionError(legacy_status)

        bad_native = tmp_path / "native_missing_synthetic_gate.csv"
        bad_out = tmp_path / "bad_native_citylbm_parity_audit.json"
        write_metrics(
            bad_native,
            "native-fluidx3d",
            audit_module,
            missing_field="synthetic_temporal_sampling_gate",
        )
        failed = run_parity_audit(REPO / "scripts" / "audit_native_citylbm_parity.py", city, bad_native, bad_out)
        if failed.returncode == 0:
            raise AssertionError((failed.returncode, failed.stdout, failed.stderr))
        bad_report = json.loads(bad_out.read_text(encoding="utf-8"))
        if bad_report["critical_parity_field_gate"] != "fail":
            raise AssertionError(bad_report)
        if "synthetic_temporal_sampling_gate" not in bad_report["missing_critical_fields"]:
            raise AssertionError(bad_report)

    print("validation_gate_native_citylbm_parity_critical_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
