#!/usr/bin/env python3
"""Smoke-test systematic-bias diagnostic fields in validation metrics."""

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


def assert_close(row: dict[str, str], field: str, expected: float, eps: float = 1.0e-9) -> None:
    value = float(row[field])
    if abs(value - expected) > eps:
        raise AssertionError(f"{field}: {value} != {expected}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_bias_metrics_") as tmp:
        root = Path(tmp)
        official = root / "official.csv"
        probe = root / "probe_audit.csv"
        metrics = root / "metrics.csv"

        write_text(
            official,
            """No.,x,y,z,Velocity_Ratio
P1,0,0,0,1.0
P2,1,0,0,2.0
""",
        )
        write_text(
            probe,
            """probe_id,x,y,z,compared_value,failed,validation_status,nearest_distance,normalization_valid,wind_direction_valid,Uref,compared_component,tolerance
P1,0,0,0,0.5,false,pass,0,true,true,2.0,abs_streamwise_ratio,0.1
P2,1,0,0,1.0,false,pass,0,true,true,2.0,abs_streamwise_ratio,0.1
""",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "validation_metrics_from_probe_audit.py"),
                "--probe-audit",
                str(probe),
                "--official",
                str(official),
                "--out",
                str(metrics),
                "--u-ref",
                "2.0",
                "--source-time-steps",
                "1000,2000",
                "--case",
                "CaseA",
                "--wind-direction",
                "N",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError(
                f"metrics script failed with {completed.returncode}\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )

        with metrics.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 1:
            raise AssertionError(rows)
        row = rows[0]
        assert_close(row, "U_mean_ratio_sim_to_exp", 0.5)
        assert_close(row, "U_mean_relative_bias_ratio", -0.5)
        assert_close(row, "U_best_fit_scale_to_exp", 2.0)
        assert_close(row, "U_best_fit_scale_deviation_ratio", 1.0)
        assert_close(row, "U_scaled_RMSE_ratio", 0.0)
        assert_close(row, "U_scaled_bias_ratio", 0.0)
        assert_close(row, "U_abs_bias_ratio", 0.75)
        if row["U_scale_like_error_flag"] != "true":
            raise AssertionError(row["U_scale_like_error_flag"])
        if row["systematic_bias_flag"] != "underprediction":
            raise AssertionError(row["systematic_bias_flag"])
        if "scale_like_error" not in row["bias_diagnosis"]:
            raise AssertionError(row["bias_diagnosis"])

    print("validation_metrics_bias_diagnostics_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
