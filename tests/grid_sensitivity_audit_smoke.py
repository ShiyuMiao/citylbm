#!/usr/bin/env python3
"""Smoke-test grid-sensitivity gating for validation metrics."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_audit(metrics: list[Path], out_json: Path, expected: int) -> dict:
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "audit_grid_sensitivity.py"),
        "--out",
        str(out_json),
        "--case",
        "ac",
        "--wind-direction",
        "N",
        "--software",
        "citylbm",
        "--max-paper-dx-m",
        "3",
        "--min-grid-sensitivity-run-count",
        "2",
        "--min-grid-refinement-ratio",
        "1.25",
        "--max-grid-rmse-change-ratio",
        "0.10",
        "--max-grid-bias-change-ratio",
        "0.05",
    ]
    for path in metrics:
        cmd.extend(["--metrics", str(path)])
    completed = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True)
    if completed.returncode != expected:
        raise AssertionError(
            f"Expected {expected}, got {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(out_json.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_grid_sensitivity_") as tmp:
        root = Path(tmp)
        passing_metrics = root / "passing_metrics.csv"
        unstable_metrics = root / "unstable_metrics.csv"
        single_metrics = root / "single_metrics.csv"
        passing_report = root / "passing_grid.json"
        unstable_report = root / "unstable_grid.json"
        single_report = root / "single_grid.json"

        write_text(
            passing_metrics,
            """case,wind_direction,software,dx_m,U_RMSE_ratio,U_bias_ratio,U_R2
ac,N,citylbm,4.0,0.235,-0.182,0.55
ac,N,citylbm,2.5,0.220,-0.160,0.60
""",
        )
        passing = run_audit([passing_metrics], passing_report, expected=0)
        if passing["grid_sensitivity_gate"] != "pass":
            raise AssertionError(passing["grid_sensitivity_gate_reasons"])
        if passing["grid_sensitivity_run_count"] != 2:
            raise AssertionError(passing)
        if abs(float(passing["grid_sensitivity_refinement_ratio"]) - 1.6) > 1.0e-12:
            raise AssertionError(passing["grid_sensitivity_refinement_ratio"])

        write_text(
            unstable_metrics,
            """case,wind_direction,software,dx_m,U_RMSE_ratio,U_bias_ratio,U_R2
ac,N,citylbm,4.0,0.360,-0.050,0.20
ac,N,citylbm,2.5,0.220,-0.160,0.60
""",
        )
        unstable = run_audit([unstable_metrics], unstable_report, expected=2)
        reasons = unstable["grid_sensitivity_gate_reasons"]
        if "grid_rmse_change_above_0.1" not in reasons:
            raise AssertionError(reasons)
        if "grid_bias_change_above_0.05" not in reasons:
            raise AssertionError(reasons)

        write_text(
            single_metrics,
            """case,wind_direction,software,dx_m,U_RMSE_ratio,U_bias_ratio,U_R2
ac,N,citylbm,2.5,0.220,-0.160,0.60
""",
        )
        single = run_audit([single_metrics], single_report, expected=2)
        reasons = single["grid_sensitivity_gate_reasons"]
        if "grid_sensitivity_run_count_below_2" not in reasons:
            raise AssertionError(reasons)
        if "grid_refinement_ratio_missing" not in reasons:
            raise AssertionError(reasons)

    print("grid_sensitivity_audit_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
