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
    "U_Pearson_r",
    "U_regression_slope",
    "U_regression_intercept",
    "U_mean_ratio_sim_to_exp",
    "k_RMSE_ratio",
    "k_bias_ratio",
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
        "U_Pearson_r": values.get("U_Pearson_r", 0.85),
        "U_regression_slope": values["U_regression_slope"],
        "U_regression_intercept": values["U_regression_intercept"],
        "U_mean_ratio_sim_to_exp": values.get("U_mean_ratio_sim_to_exp", 1.0),
        "k_RMSE_ratio": values.get("k_RMSE_ratio", 0.20),
        "k_bias_ratio": values.get("k_bias_ratio", -0.10),
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)


def write_preconditions(path: Path, gate: str = "pass") -> None:
    failed = gate != "pass"
    path.write_text(
        json.dumps(
            {
                "native_preconditions_gate": gate,
                "native_precondition_closure_gate": gate,
                "native_preconditions_protocol_identity_gate": gate,
                "native_preconditions_time_average_evidence_gate": gate,
                "native_inlet_equivalence_gate": gate,
                "native_boundary_equivalence_gate": gate,
                "native_probe_component_equivalence_gate": gate,
                "native_precondition_failed_stage_count": 1 if failed else 0,
                "native_precondition_top_blocking_stage_key": (
                    "turbulent_inlet_method_and_u_k_preservation" if failed else ""
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run_delta_audit(
    city: Path,
    native: Path,
    preconditions: Path,
    out: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_native_citylbm_accuracy_delta.py"),
            "--citylbm-metrics",
            str(city),
            "--native-metrics",
            str(native),
            "--native-preconditions-audit",
            str(preconditions),
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
        max_native_citylbm_pearson_r_drop=0.05,
        max_native_citylbm_slope_delta=0.10,
        max_native_citylbm_intercept_delta=0.05,
        max_native_citylbm_k_rmse_delta=0.10,
        max_native_citylbm_k_abs_bias_delta=0.10,
    )


def main() -> int:
    gate_module = load_module("validation_gate", REPO / "scripts" / "validation_gate.py")
    native_good = {
        "U_RMSE_ratio": 0.20,
        "U_bias_ratio": -0.10,
        "U_R2": 0.80,
        "U_Pearson_r": 0.86,
        "U_regression_slope": 0.95,
        "U_regression_intercept": 0.02,
        "k_RMSE_ratio": 0.20,
        "k_bias_ratio": -0.10,
    }

    with tempfile.TemporaryDirectory(prefix="citylbm_accuracy_delta_") as tmp:
        tmp_path = Path(tmp)
        native = tmp_path / "native.csv"
        city = tmp_path / "city.csv"
        preconditions = tmp_path / "native_preconditions_audit.json"
        failing_preconditions = tmp_path / "native_preconditions_audit_fail.json"
        out = tmp_path / "native_citylbm_accuracy_delta_audit.json"
        write_preconditions(preconditions)
        write_preconditions(failing_preconditions, gate="fail")

        write_metrics(native, "native-fluidx3d", native_good)
        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.215,
                "U_bias_ratio": -0.11,
                "U_R2": 0.78,
                "U_Pearson_r": 0.84,
                "U_regression_slope": 0.97,
                "U_regression_intercept": 0.03,
                "k_RMSE_ratio": 0.23,
                "k_bias_ratio": -0.12,
            },
        )
        passed = run_delta_audit(city, native, preconditions, out)
        if passed.returncode != 0:
            raise AssertionError((passed.returncode, passed.stdout, passed.stderr))
        report = json.loads(out.read_text(encoding="utf-8"))
        if report["native_citylbm_accuracy_delta_gate"] != "pass":
            raise AssertionError(report)
        if report["accuracy_interpretation"] != "citylbm_matches_publishable_native_baseline":
            raise AssertionError(report)
        if report["native_preconditions_accuracy_gate"] != "pass":
            raise AssertionError(report)
        status = gate_module.native_citylbm_accuracy_delta_status(report, default_gate_args())
        if not status["ok"]:
            raise AssertionError(status)

        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.215,
                "U_bias_ratio": -0.11,
                "U_R2": 0.78,
                "U_Pearson_r": 0.75,
                "U_regression_slope": 0.97,
                "U_regression_intercept": 0.03,
                "k_RMSE_ratio": 0.23,
                "k_bias_ratio": -0.12,
            },
        )
        pearson_failed = run_delta_audit(city, native, preconditions, out)
        if pearson_failed.returncode == 0:
            raise AssertionError((pearson_failed.returncode, pearson_failed.stdout, pearson_failed.stderr))
        pearson_report = json.loads(out.read_text(encoding="utf-8"))
        if pearson_report["citylbm_additional_error_flag"] is not True:
            raise AssertionError(pearson_report)
        if not any(
            reason.startswith("citylbm_pearson_r_drop")
            for reason in pearson_report["citylbm_additional_error_reasons"]
        ):
            raise AssertionError(pearson_report)
        pearson_status = gate_module.native_citylbm_accuracy_delta_status(
            pearson_report,
            default_gate_args(),
        )
        if pearson_status["ok"]:
            raise AssertionError(pearson_status)

        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.30,
                "U_bias_ratio": -0.20,
                "U_R2": 0.60,
                "U_Pearson_r": 0.70,
                "U_regression_slope": 0.70,
                "U_regression_intercept": 0.20,
                "k_RMSE_ratio": 0.45,
                "k_bias_ratio": -0.28,
            },
        )
        failed = run_delta_audit(city, native, preconditions, out)
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
                "U_Pearson_r": 0.60,
                "U_regression_slope": 0.55,
                "U_regression_intercept": 0.25,
                "k_RMSE_ratio": 0.80,
                "k_bias_ratio": -0.60,
            },
        )
        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.41,
                "U_bias_ratio": -0.35,
                "U_R2": 0.29,
                "U_Pearson_r": 0.59,
                "U_regression_slope": 0.56,
                "U_regression_intercept": 0.26,
                "k_RMSE_ratio": 0.82,
                "k_bias_ratio": -0.61,
            },
        )
        native_bad_failed = run_delta_audit(city, native_bad, preconditions, out)
        if native_bad_failed.returncode == 0:
            raise AssertionError((native_bad_failed.returncode, native_bad_failed.stdout, native_bad_failed.stderr))
        native_bad_report = json.loads(out.read_text(encoding="utf-8"))
        if native_bad_report["native_citylbm_accuracy_delta_gate"] != "fail":
            raise AssertionError(native_bad_report)
        if native_bad_report["native_accuracy_gate"] != "fail":
            raise AssertionError(native_bad_report)
        if native_bad_report["accuracy_interpretation"] != "citylbm_matches_native_but_native_protocol_or_physics_limited":
            raise AssertionError(native_bad_report)
        if native_bad_report["citylbm_additional_error_flag"] is not False:
            raise AssertionError(native_bad_report)
        if not any(
            reason.startswith("native_accuracy_gate_not_pass")
            for reason in native_bad_report["native_citylbm_accuracy_delta_gate_reasons"]
        ):
            raise AssertionError(native_bad_report)
        native_bad_status = gate_module.native_citylbm_accuracy_delta_status(
            native_bad_report,
            default_gate_args(),
        )
        if native_bad_status["ok"]:
            raise AssertionError(native_bad_status)

        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.215,
                "U_bias_ratio": -0.11,
                "U_R2": 0.78,
                "U_Pearson_r": 0.84,
                "U_regression_slope": 0.97,
                "U_regression_intercept": 0.03,
                "k_RMSE_ratio": 0.23,
                "k_bias_ratio": -0.12,
            },
        )
        precondition_failed = run_delta_audit(city, native, failing_preconditions, out)
        if precondition_failed.returncode == 0:
            raise AssertionError((precondition_failed.returncode, precondition_failed.stdout, precondition_failed.stderr))
        precondition_report = json.loads(out.read_text(encoding="utf-8"))
        if precondition_report["native_preconditions_accuracy_gate"] != "fail":
            raise AssertionError(precondition_report)
        if precondition_report["accuracy_interpretation"] != "native_preconditions_not_closed":
            raise AssertionError(precondition_report)
        if precondition_report["citylbm_additional_error_flag"] is not False:
            raise AssertionError(precondition_report)
        if "native_preconditions_not_closed" not in precondition_report["native_citylbm_accuracy_delta_gate_reasons"]:
            raise AssertionError(precondition_report)

        write_metrics(
            city,
            "citylbm",
            {
                "U_RMSE_ratio": 0.215,
                "U_bias_ratio": -0.11,
                "U_R2": 0.78,
                "U_Pearson_r": 0.84,
                "U_regression_slope": 0.97,
                "U_regression_intercept": 0.03,
                "k_RMSE_ratio": 0.42,
                "k_bias_ratio": -0.31,
            },
        )
        k_failed = run_delta_audit(city, native, preconditions, out)
        if k_failed.returncode == 0:
            raise AssertionError((k_failed.returncode, k_failed.stdout, k_failed.stderr))
        k_report = json.loads(out.read_text(encoding="utf-8"))
        if k_report["citylbm_additional_error_flag"] is not True:
            raise AssertionError(k_report)
        if not any(
            reason.startswith("citylbm_k_")
            for reason in k_report["citylbm_additional_error_reasons"]
        ):
            raise AssertionError(k_report)

    print("validation_gate_native_citylbm_accuracy_delta_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
