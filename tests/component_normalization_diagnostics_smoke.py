#!/usr/bin/env python3
"""Smoke-test component and normalization diagnostics for scale-like bias."""

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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_audit(probe: Path, official: Path, out_json: Path, expected: int) -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "audit_component_sensitivity.py"),
            "--probe-audit",
            str(probe),
            "--official",
            str(official),
            "--out-json",
            str(out_json),
            "--selected-component",
            "speed_ratio",
            "--min-source-step-span",
            "100",
            "--expected-source-time-steps",
            "1000,1100",
        ],
        cwd=str(REPO),
        text=True,
        capture_output=True,
    )
    if completed.returncode != expected:
        raise AssertionError(
            f"Expected {expected}, got {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(out_json.read_text(encoding="utf-8"))


def base_probe_row(probe_id: str, vtk_a: Path, vtk_b: Path) -> dict[str, str]:
    hashes = f"{sha256(vtk_a)};{sha256(vtk_b)}"
    return {
        "probe_id": probe_id,
        "failed": "false",
        "out_of_tolerance": "false",
        "compared_component": "speed_ratio",
        "vtk_source_time_steps": "1000,1100",
        "vtk_source_step_span": "100",
        "minimum_validation_average_step_span": "100",
        "vtk_source_files": f"{vtk_a};{vtk_b}",
        "vtk_source_sha256": hashes,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_component_norm_diag_") as tmp:
        root = Path(tmp)
        vtk_a = root / "u-000001000.vtk"
        vtk_b = root / "u-000001100.vtk"
        official = root / "official.csv"
        wrong_component_probe = root / "wrong_component_probe.csv"
        scale_like_probe = root / "scale_like_probe.csv"
        reversed_streamwise_probe = root / "reversed_streamwise_probe.csv"
        wrong_component_report = root / "wrong_component.json"
        scale_like_report = root / "scale_like.json"
        reversed_streamwise_report = root / "reversed_streamwise.json"

        write_text(vtk_a, "frame 1000\n")
        write_text(vtk_b, "frame 1100\n")
        write_text(
            official,
            "No.,Velocity_Ratio\nP1,1.0\nP2,0.8\nP3,0.6\n",
        )

        wrong_rows = []
        for probe_id, official_value, wrong_speed in [
            ("P1", "1.0", "0.20"),
            ("P2", "0.8", "0.20"),
            ("P3", "0.6", "0.20"),
        ]:
            row = base_probe_row(probe_id, vtk_a, vtk_b)
            row.update({"speed_ratio": wrong_speed, "streamwise_ratio": official_value})
            wrong_rows.append(row)
        write_csv(wrong_component_probe, wrong_rows)

        wrong_component = run_audit(wrong_component_probe, official, wrong_component_report, expected=2)
        if wrong_component["component_source_window_gate"] != "pass":
            raise AssertionError(wrong_component["component_source_window_gate_reasons"])
        if wrong_component["component_sensitivity_gate"] != "fail":
            raise AssertionError(wrong_component["component_sensitivity_gate"])
        if wrong_component["best_component_by_rmse"] != "streamwise_ratio":
            raise AssertionError(wrong_component["best_component_by_rmse"])
        if not any(
            reason.startswith("alternative_component_streamwise_ratio_improves_rmse_by_")
            for reason in wrong_component["component_sensitivity_gate_reasons"]
        ):
            raise AssertionError(wrong_component["component_sensitivity_gate_reasons"])

        scale_rows = []
        for probe_id, official_value, low_speed in [
            ("P1", "1.0", "0.66"),
            ("P2", "0.8", "0.528"),
            ("P3", "0.6", "0.396"),
        ]:
            row = base_probe_row(probe_id, vtk_a, vtk_b)
            row.update({"speed_ratio": low_speed, "streamwise_ratio": low_speed})
            scale_rows.append(row)
        write_csv(scale_like_probe, scale_rows)

        scale_like = run_audit(scale_like_probe, official, scale_like_report, expected=2)
        if scale_like["component_sensitivity_gate"] != "pass":
            raise AssertionError(scale_like["component_sensitivity_gate_reasons"])
        if scale_like["normalization_scale_gate"] != "fail":
            raise AssertionError(scale_like["normalization_scale_gate"])
        if scale_like["component_normalization_gate"] != "fail":
            raise AssertionError(scale_like["component_normalization_gate"])
        if abs(float(scale_like["selected_best_fit_scale_to_exp"]) - 1.515151515) > 1.0e-6:
            raise AssertionError(scale_like["selected_best_fit_scale_to_exp"])
        if not any(
            reason.startswith("best_fit_scale_") and reason.endswith("_suggests_uref_or_unit_error")
            for reason in scale_like["normalization_scale_gate_reasons"]
        ):
            raise AssertionError(scale_like["normalization_scale_gate_reasons"])

        reversed_rows = []
        for probe_id, official_value, reversed_streamwise in [
            ("P1", "1.0", "-1.0"),
            ("P2", "0.8", "-0.8"),
            ("P3", "0.6", "-0.6"),
        ]:
            row = base_probe_row(probe_id, vtk_a, vtk_b)
            row.update({"speed_ratio": official_value, "streamwise_ratio": reversed_streamwise})
            reversed_rows.append(row)
        write_csv(reversed_streamwise_probe, reversed_rows)

        reversed_streamwise = run_audit(
            reversed_streamwise_probe,
            official,
            reversed_streamwise_report,
            expected=2,
        )
        if reversed_streamwise["component_sensitivity_gate"] != "pass":
            raise AssertionError(reversed_streamwise["component_sensitivity_gate_reasons"])
        if reversed_streamwise["normalization_scale_gate"] != "pass":
            raise AssertionError(reversed_streamwise["normalization_scale_gate_reasons"])
        if reversed_streamwise["streamwise_sign_gate"] != "fail":
            raise AssertionError(reversed_streamwise["streamwise_sign_gate"])
        if reversed_streamwise["component_normalization_gate"] != "fail":
            raise AssertionError(reversed_streamwise["component_normalization_gate"])
        if abs(float(reversed_streamwise["streamwise_negative_fraction"]) - 1.0) > 1.0e-12:
            raise AssertionError(reversed_streamwise["streamwise_negative_fraction"])
        if not any(
            "suggests_wind_vector_or_component_sign_error" in reason
            for reason in reversed_streamwise["streamwise_sign_gate_reasons"]
        ):
            raise AssertionError(reversed_streamwise["streamwise_sign_gate_reasons"])

    print("component_normalization_diagnostics_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
