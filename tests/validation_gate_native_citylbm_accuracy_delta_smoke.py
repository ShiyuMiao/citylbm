#!/usr/bin/env python3
"""Smoke-test paired native FluidX3D vs CityLBM accuracy-delta gating."""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


REPO = Path(__file__).resolve().parents[1]


FIELDS = [
    "case",
    "wind_direction",
    "software",
    "U_MAE_ratio",
    "U_RMSE_ratio",
    "U_bias_ratio",
    "U_R2",
    "U_regression_slope",
    "U_regression_intercept",
    "U_mean_ratio_sim_to_exp",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_metrics(path: Path, software: str, values: dict[str, float]) -> None:
    row = {
        "case": "CaseA",
        "wind_direction": "N",
        "software": software,
        "U_MAE_ratio": values.get("U_MAE_ratio", 0.15),
        "U_RMSE_ratio": values["U_RMSE_ratio"],
        "U_bias_ratio": values["U_bias_ratio"],
        "U_R2": values["U_R2"],
        "U_regression_slope": values["U_regression_slope"],
        "U_regression_intercept": values["U_regression_intercept"],
        "U_mean_ratio_sim_to_exp": values.get("U_mean_ratio_sim_to_exp", 1.0),
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)


def run_delta_audit(city: Path, native: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_native_citylbm_accuracy_delta.py"),
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


def default_gate_args() -> SimpleNamespace:
    return SimpleNamespace(
        max_native_citylbm_rmse_delta=0.03,
        max_native_citylbm_abs_bias_delta=0.03,
        max_native_citylbm_r2_drop=0.05,
        max_native_citylbm_slope_delta=0.10,
        max_native_citylbm_intercept_delta=0.05,
    )


def main() -> int:
    gate_module = load_module("validation_gate", REPO / "scripts" / "validation_gate.py")
    native_good = {
        "U_RMSE_ratio": 0.20,
        "U_bias_ratio": -0.10,
        "U_R2": 0.80,
        "U_regression_slope": 0.95,
        "U_regression_intercept": 0.02,
    }

    with tempfile.TemporaryDirectory(prefix="citylbm_accuracy_delta_") as tmp:
        tmp_path = Path(tmp)
        native = tmp_path / "native.csv"
        city = tmp_path / "city.csv"
        out = tmp_path / "native_citylbm_accuracy_delta_audit.json"

        write_metrics(native, "native-fluidx3d", native_good)
        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.215,
                "U_bias_ratio": -0.11,
                "U_R2": 0.78,
                "U_regression_slope": 0.97,
                "U_regression_intercept": 0.03,
            },
        )
        passed = run_delta_audit(city, native, out)
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr))
        report = json.loads(out.read_text(encoding="utf-8"))
        if report["native_citylbm_accuracy_delta_gate"] != "pass":
            raise AssertionError(report)
        if report["accuracy_interpretation"] != "citylbm_matches_publishable_native_baseline":
            raise AssertionError(report)
        status = gate_module.native_citylbm_accuracy_delta_status(report, default_gate_args())
        if not status["ok"]:
            raise AssertionError(status)

        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.30,
                "U_bias_ratio": -0.20,
                "U_R2": 0.60,
                "U_regression_slope": 0.70,
                "U_regression_intercept": 0.20,
            },
        )
        failed = run_delta_audit(city, native, out)
        if failed.returncode == 0:
            raise AssertionError((failed.returncode, failed.stdout, failed.stderr))
        bad_report = json.loads(out.read_text(encoding="utf-8"))
        if bad_report["native_citylbm_accuracy_delta_gate"] != "fail":
            raise AssertionError(bad_report)
        if bad_report["citylbm_additional_error_flag"] is not True:
            raise AssertionError(bad_report)
        bad_status = gate_module.native_citylbm_accuracy_delta_status(
            bad_report,
            default_gate_args(),
        )
        if bad_status["ok"]:
            raise AssertionError(bad_status)

        native_bad = tmp_path / "native_bad.csv"
        write_metrics(
            native_bad,
            "native-fluidx3d",
            {
                "U_RMSE_ratio": 0.40,
                "U_bias_ratio": -0.34,
                "U_R2": 0.30,
                "U_regression_slope": 0.55,
                "U_regression_intercept": 0.25,
            },
        )
        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.41,
                "U_bias_ratio": -0.35,
                "U_R2": 0.29,
                "U_regression_slope": 0.56,
                "U_regression_intercept": 0.26,
            },
        )
        native_bad_passed = run_delta_audit(city, native_bad, out)
        if native_bad_passed.returncode != 0:
            raise AssertionError((native_bad_passed.returncode, native_bad_passed.stdout, native_bad_passed.stderr))
        native_bad_report = json.loads(out.read_text(encoding="utf-8"))
        if native_bad_report["native_accuracy_gate"] != "fail":
            raise AssertionError(native_bad_report)
        if native_bad_report["accuracy_interpretation"] != "citylbm_matches_native_but_native_protocol_or_physics_limited":
            raise AssertionError(native_bad_report)
        native_bad_status = gate_module.native_citylbm_accuracy_delta_status(
            native_bad_report,
            default_gate_args(),
        )
        if not native_bad_status["ok"]:
            raise AssertionError(native_bad_status)

    print("validation_gate_native_citylbm_accuracy_delta_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
