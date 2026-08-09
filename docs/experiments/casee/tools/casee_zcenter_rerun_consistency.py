#!/usr/bin/env python3
"""Audit the latest compiled z-center Case E rerun against the baseline CSV."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
DATA_DIR = CASE_DIR / "official_data"
BASELINE_CSV = RESULTS_DIR / "casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv"
OUT_JSON = RESULTS_DIR / "casee_zcenter_rerun_consistency.json"
OUT_CSV = RESULTS_DIR / "casee_zcenter_rerun_consistency.csv"
OUT_MD = RESULTS_DIR / "casee_zcenter_rerun_consistency.md"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_status(path: Path) -> Dict[str, Any]:
    return {
        "found": path.exists(),
        "path": rel(path) if path.exists() and path.is_relative_to(ROOT) else str(path),
        "sha256": sha256(path) if path.exists() else "",
        "size_bytes": path.stat().st_size if path.exists() else None,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else "",
    }


def latest_rerun_csv() -> Path | None:
    candidates = sorted(
        RESULTS_DIR.glob("casee_native_dx2_zcenter_rerun_*_probe_time_mean.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def companion_log(csv_path: Path, suffix: str) -> Path:
    name = csv_path.name
    stamp = name.removeprefix("casee_native_dx2_zcenter_rerun_").removesuffix("_probe_time_mean.csv")
    return RESULTS_DIR / f"fluidx3d_dx2_zcenter_rerun_{stamp}{suffix}"


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_float(row: Dict[str, str], key: str) -> float:
    return float(row[key])


def official_reference_by_probe() -> Dict[int, float]:
    refs: Dict[int, float] = {}
    with (DATA_DIR / "RS_caseE.csv").open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("case") != "ac" or row.get("Wind_direction") != "N":
                continue
            if abs(float(row.get("z(m)", "nan")) - 2.0) > 1e-9:
                continue
            refs[int(row["No."])] = float(row["Velocity_Ratio"])
    if len(refs) != 80:
        raise SystemExit(f"Expected 80 official ac+N z=2 m reference probes, found {len(refs)}")
    return refs


def metrics(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    refs = official_reference_by_probe()
    official = [refs[int(r["No."])] for r in rows]
    pred = [to_float(r, "predicted_velocity_ratio") for r in rows]
    residuals = [p - o for p, o in zip(pred, official)]
    n = len(rows)
    mae = sum(abs(r) for r in residuals) / n * 100.0
    rmse = math.sqrt(sum(r * r for r in residuals) / n) * 100.0
    bias = sum(residuals) / n * 100.0
    mean_o = sum(official) / n
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((o - mean_o) ** 2 for o in official)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None
    mean_p = sum(pred) / n
    cov = sum((o - mean_o) * (p - mean_p) for o, p in zip(official, pred))
    var_o = sum((o - mean_o) ** 2 for o in official)
    var_p = sum((p - mean_p) ** 2 for p in pred)
    pearson = cov / math.sqrt(var_o * var_p) if var_o > 0 and var_p > 0 else None
    return {
        "n": n,
        "mae_pp": mae,
        "rmse_pp": rmse,
        "bias_pp": bias,
        "r2": r2,
        "pearson": pearson,
        "height_m": 2.0,
        "sampling_mode": "raw_trilinear",
    }


def max_abs_delta(a: List[Dict[str, str]], b: List[Dict[str, str]], columns: Iterable[str]) -> Dict[str, float]:
    deltas: Dict[str, float] = {}
    for column in columns:
        deltas[column] = max(abs(float(ra[column]) - float(rb[column])) for ra, rb in zip(a, b))
    return deltas


def log_completed(path: Path) -> bool:
    if not path.exists():
        return False
    raw = path.read_bytes()
    candidates = [
        raw.decode("utf-8", errors="replace"),
        raw.decode("utf-16-le", errors="replace"),
        raw.replace(b"\x00", b"").decode("utf-8", errors="replace"),
    ]
    return any("CaseE step 48000 / 48000" in text for text in candidates)


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    rows = [
        {
            "audit_id": "zcenter_rerun_consistency",
            "status": payload["status"],
            "evidence_type": payload["evidence_type"],
            "baseline_csv": payload["baseline_csv"]["path"],
            "rerun_csv": payload["rerun_csv"]["path"],
            "log_completed_48000": payload["log_completed_48000"],
            "csv_sha256_equal": payload["csv_sha256_equal"],
            "max_predicted_ratio_delta": payload["max_abs_column_delta"].get("predicted_velocity_ratio"),
            "mae_pp": payload["rerun_metrics"].get("mae_pp"),
            "r2": payload["rerun_metrics"].get("r2"),
            "pearson": payload["rerun_metrics"].get("pearson"),
            "formal_release_allowed": payload["formal_release_allowed"],
            "claim_readiness": payload["claim_readiness"],
        }
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    m = payload["rerun_metrics"]
    lines = [
        "# Case E z-center Rerun Consistency",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- 48000-step log complete: {payload['log_completed_48000']}",
        f"- CSV SHA256 equal to baseline: {payload['csv_sha256_equal']}",
        "",
        "## Official z=2 m raw_trilinear rerun metric",
        "",
        f"- MAE: {m.get('mae_pp')} pp",
        f"- R2: {m.get('r2')}",
        f"- Pearson: {m.get('pearson')}",
        "",
        "## Artifacts",
        "",
        f"- Baseline CSV: `{payload['baseline_csv']['path']}`",
        f"- Rerun CSV: `{payload['rerun_csv']['path']}`",
        f"- Rerun log: `{payload['rerun_log']['path']}`",
        f"- Rerun stderr log: `{payload['rerun_err_log']['path']}`",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rerun_csv = latest_rerun_csv()
    baseline_found = BASELINE_CSV.exists()
    rerun_found = rerun_csv is not None and rerun_csv.exists()
    if not baseline_found or not rerun_found:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "blocked_missing_rerun_or_baseline",
            "evidence_type": "blocked",
            "claim_readiness": "blocked_rerun_consistency",
            "formal_release_allowed": False,
            "formal_accuracy_claim_supported": False,
            "baseline_csv": file_status(BASELINE_CSV),
            "rerun_csv": file_status(rerun_csv) if rerun_csv else {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime_utc": ""},
            "rerun_log": {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime_utc": ""},
            "rerun_err_log": {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime_utc": ""},
            "log_completed_48000": False,
            "csv_sha256_equal": False,
            "row_count_equal": False,
            "max_abs_column_delta": {},
            "rerun_metrics": {},
            "boundary": "No rerun consistency result is available until a completed FluidX3D rerun CSV and log exist.",
        }
    else:
        assert rerun_csv is not None
        baseline_rows = read_rows(BASELINE_CSV)
        rerun_rows = read_rows(rerun_csv)
        log_path = companion_log(rerun_csv, ".log")
        err_path = companion_log(rerun_csv, ".err.log")
        deltas = max_abs_delta(
            baseline_rows,
            rerun_rows,
            [
                "official_velocity_ratio",
                "predicted_velocity_ratio",
                "nearest_valid_velocity_ratio",
                "fluid_weighted_velocity_ratio",
                "vertical_valid_above_velocity_ratio",
                "z_plus_half_velocity_ratio",
            ],
        )
        csv_equal = sha256(BASELINE_CSV) == sha256(rerun_csv)
        completed = log_completed(log_path)
        consistent = csv_equal and completed and len(baseline_rows) == len(rerun_rows) == 80
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "passed_reproduced_failed_metric" if consistent else "blocked_inconsistent_rerun",
            "evidence_type": "newly_run" if consistent else "blocked",
            "claim_readiness": "paper_ready_reproducibility; blocked formal accuracy release" if consistent else "blocked_rerun_consistency",
            "formal_release_allowed": False,
            "formal_accuracy_claim_supported": False,
            "baseline_csv": file_status(BASELINE_CSV),
            "rerun_csv": file_status(rerun_csv),
            "rerun_log": file_status(log_path),
            "rerun_err_log": file_status(err_path),
            "log_completed_48000": completed,
            "csv_sha256_equal": csv_equal,
            "row_count_equal": len(baseline_rows) == len(rerun_rows) == 80,
            "max_abs_column_delta": deltas,
            "rerun_metrics": metrics(rerun_rows),
            "boundary": (
                "This audit shows the current compiled z-center diagnostic reproduces the same official z=2 m "
                "raw_trilinear failure metric. It supports reproducibility and limitations claims only; it does "
                "not improve accuracy, does not support mesh independence, and does not allow formal v0.4.0."
            ),
        }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"out_json": str(OUT_JSON), "status": payload["status"], "r2": payload["rerun_metrics"].get("r2")}, indent=2))
    return 0 if payload["status"] == "passed_reproduced_failed_metric" else 1


if __name__ == "__main__":
    raise SystemExit(main())
