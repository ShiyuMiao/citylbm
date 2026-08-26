#!/usr/bin/env python3
"""Smoke-test runtime inlet diagnostics CSV audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "audit_inlet_diagnostics_csv.py"
HEADER_LEGACY = (
    "step,profile_index,z_m,z_cell,target_U_mps,target_u_rms_mps,target_v_rms_mps,"
    "target_w_rms_mps,target_k_m2s2,mean_U_mps,mean_V_mps,mean_W_mps,u_rms_mps,"
    "v_rms_mps,w_rms_mps,k_m2s2,samples_y,effective_sample_z_cell,effective_sample_z_m\n"
)
HEADER = (
    "step,profile_index,z_m,z_cell,target_U_mps,target_u_rms_mps,target_v_rms_mps,"
    "target_w_rms_mps,target_k_m2s2,target_r11_m2s2,target_r22_m2s2,target_r33_m2s2,"
    "target_r12_m2s2,target_r13_m2s2,target_r23_m2s2,mean_U_mps,mean_V_mps,mean_W_mps,"
    "u_rms_mps,v_rms_mps,w_rms_mps,k_m2s2,mean_x_mps,mean_y_mps,mean_z_mps,"
    "x_rms_mps,y_rms_mps,z_rms_mps,measured_r11_m2s2,measured_r22_m2s2,"
    "measured_r33_m2s2,measured_r12_m2s2,measured_r13_m2s2,measured_r23_m2s2,"
    "samples_y,effective_sample_z_cell,effective_sample_z_m\n"
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def row(step: int, profile: int, target_u: float, mean_u: float, k: float, ksim: float) -> str:
    z_m = 0.1 + profile * 0.1
    return (
        f"{step},{profile},{z_m:.3f},{profile},"
        f"{target_u},0.2,0.15,0.1,{k},0.04,0.0225,0.01,0.0,0.0,0.0,"
        f"{mean_u},0.01,0.01,0.2,0.15,0.1,{ksim},{mean_u},0.01,0.01,"
        "0.2,0.15,0.1,0.0405,0.022,0.0102,0.0,0.0,0.0,"
        f"8,1.0,{z_m:.3f}\n"
    )


def legacy_row(step: int, profile: int, target_u: float, mean_u: float, k: float, ksim: float) -> str:
    z_m = 0.1 + profile * 0.1
    return (
        f"{step},{profile},{z_m:.3f},{profile},"
        f"{target_u},0.2,0.15,0.1,{k},{mean_u},0.01,0.01,0.2,0.15,0.1,{ksim},"
        f"8,1.0,{z_m:.3f}\n"
    )


def aligned_row(
    step: int,
    profile: int,
    z_m: float,
    effective_z_m: float,
    target_u: float,
    mean_u: float,
    target_k: float,
    measured_k: float,
) -> str:
    return (
        f"{step},{profile},{z_m:.3f},{profile},{target_u},0.2,0.2,0.2,{target_k},"
        "0.04,0.04,0.04,0.0,0.0,0.0,"
        f"{mean_u},0.0,0.0,0.2,0.2,0.2,{measured_k},{mean_u},0.0,0.0,"
        "0.04,0.04,0.04,0.04,0.04,0.04,0.0,0.0,0.0,"
        f"8,1.0,{effective_z_m:.3f}\n"
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_inlet_diag_") as raw:
        temp = Path(raw)
        good_csv = temp / "casea_inlet_turbulence_stats.csv"
        good_json = temp / "good.json"
        good_summary = temp / "good_summary.csv"
        rows = [HEADER]
        for step in (100, 200, 300):
            rows.append(row(step, 0, 1.0, 1.02, 0.05, 0.052))
            rows.append(row(step, 1, 1.5, 1.46, 0.08, 0.079))
        write(good_csv, "".join(rows))

        good = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(good_csv),
                "--out-json",
                str(good_json),
                "--out-csv",
                str(good_summary),
                "--require-k",
                "--require-rms",
                "--require-reynolds-stress",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if good.returncode != 0:
            raise AssertionError((good.returncode, good.stdout, good.stderr))
        good_audit = load(good_json)
        if good_audit["Gate"] != "pass":
            raise AssertionError(good_audit)
        if good_audit["ProfileCount"] != 2:
            raise AssertionError(good_audit)
        if good_audit["Metrics"]["ReynoldsStressGate"] != "pass":
            raise AssertionError(good_audit)
        if not good_summary.is_file():
            raise AssertionError("summary csv missing")

        lowercase_csv = temp / "lowercase.csv"
        lowercase_json = temp / "lowercase.json"
        lowercase_summary = temp / "lowercase_summary.csv"
        write(lowercase_csv, "".join(rows).replace("target_U_mps", "target_u_mps").replace("mean_U_mps", "mean_u_mps").replace("mean_V_mps", "mean_v_mps").replace("mean_W_mps", "mean_w_mps"))
        lowercase = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(lowercase_csv),
                "--out-json",
                str(lowercase_json),
                "--out-csv",
                str(lowercase_summary),
                "--require-k",
                "--require-rms",
                "--require-reynolds-stress",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if lowercase.returncode != 0:
            raise AssertionError((lowercase.returncode, lowercase.stdout, lowercase.stderr))
        lowercase_audit = load(lowercase_json)
        if lowercase_audit["Gate"] != "pass":
            raise AssertionError(lowercase_audit)
        if lowercase_audit["ColumnAliases"].get("target_U_mps") != "target_u_mps":
            raise AssertionError(lowercase_audit)

        aligned_csv = temp / "aligned.csv"
        aligned_json = temp / "aligned.json"
        aligned_summary = temp / "aligned_summary.csv"
        aligned_rows = [HEADER]
        for step in (100, 200, 300):
            aligned_rows.append(aligned_row(step, 0, 1.0, 3.0, 1.0, 2.0, 0.06, 0.12))
            aligned_rows.append(aligned_row(step, 1, 3.0, 3.0, 2.0, 2.0, 0.12, 0.12))
        write(aligned_csv, "".join(aligned_rows))
        aligned = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(aligned_csv),
                "--out-json",
                str(aligned_json),
                "--out-csv",
                str(aligned_summary),
                "--require-k",
                "--require-rms",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if aligned.returncode != 0:
            raise AssertionError((aligned.returncode, aligned.stdout, aligned.stderr))
        aligned_audit = load(aligned_json)
        metrics = aligned_audit["Metrics"]
        if metrics["MeanUGateComparison"] != "effective_sample_z":
            raise AssertionError(aligned_audit)
        if metrics["MaxMeanURelError"] <= 0.9:
            raise AssertionError(aligned_audit)
        if metrics["MaxMeanURelErrorEffectiveSampleZ"] > 1.0e-9:
            raise AssertionError(aligned_audit)
        if metrics["MaxSampleZOffsetM"] < 1.9:
            raise AssertionError(aligned_audit)

        legacy_csv = temp / "legacy.csv"
        legacy_json = temp / "legacy.json"
        write(
            legacy_csv,
            HEADER_LEGACY
            + legacy_row(100, 0, 1.0, 1.0, 0.05, 0.05)
            + legacy_row(200, 0, 1.0, 1.0, 0.05, 0.05)
            + legacy_row(300, 0, 1.0, 1.0, 0.05, 0.05),
        )
        legacy = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(legacy_csv),
                "--out-json",
                str(legacy_json),
                "--require-reynolds-stress",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if legacy.returncode == 0:
            raise AssertionError((legacy.returncode, legacy.stdout, legacy.stderr))
        legacy_audit = load(legacy_json)
        legacy_reasons = ";".join(legacy_audit["Reasons"])
        if "missing_reynolds_stress_column:target_r11_m2s2" not in legacy_reasons:
            raise AssertionError(legacy_audit)

        bad_csv = temp / "bad.csv"
        bad_json = temp / "bad.json"
        write(
            bad_csv,
            HEADER
            + row(100, 0, 1.0, 0.4, 0.05, 0.001)
            + row(200, 0, 1.0, 0.4, 0.05, 0.001)
            + row(300, 0, 1.0, 0.4, 0.05, 0.001),
        )
        bad = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(bad_csv),
                "--out-json",
                str(bad_json),
                "--require-k",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if bad.returncode == 0:
            raise AssertionError((bad.returncode, bad.stdout, bad.stderr))
        bad_audit = load(bad_json)
        if bad_audit["Gate"] != "fail":
            raise AssertionError(bad_audit)
        reasons = ";".join(bad_audit["Reasons"])
        if "mean_u_rel_error_above" not in reasons or "k_rel_error_above" not in reasons:
            raise AssertionError(bad_audit)

    print("inlet_diagnostics_csv_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
