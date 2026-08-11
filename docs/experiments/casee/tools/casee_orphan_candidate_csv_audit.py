#!/usr/bin/env python3
"""Audit local untracked Case E candidate probe CSVs without promoting them."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
NATIVE_DIR = CASE_DIR / "native_cases"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_orphan_candidate_csv_audit.json"
OUT_CSV = RESULTS_DIR / "casee_orphan_candidate_csv_audit.csv"
OUT_MD = RESULTS_DIR / "casee_orphan_candidate_csv_audit.md"

SAMPLING_COLUMNS = [
    "predicted_velocity_ratio",
    "nearest_valid_velocity_ratio",
    "fluid_weighted_velocity_ratio",
    "vertical_valid_above_velocity_ratio",
    "z_plus_half_velocity_ratio",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def git_untracked_paths() -> set[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    out: set[str] = set()
    for line in proc.stdout.splitlines():
        if line.startswith("?? "):
            out.add(line[3:].replace("\\", "/"))
    return out


def git_tracked(path: Path) -> bool:
    proc = subprocess.run(["git", "ls-files", "--error-unmatch", rel(path)], cwd=ROOT, text=True, capture_output=True)
    return proc.returncode == 0


def metric_rows(path: Path) -> List[Dict[str, Any]]:
    rows = read_csv(path)
    if not rows:
        return []
    y = [float(row["official_velocity_ratio"]) for row in rows]
    ybar = sum(y) / len(y)
    out: List[Dict[str, Any]] = []
    for column in SAMPLING_COLUMNS:
        if column not in rows[0]:
            continue
        pred = [float(row[column]) for row in rows]
        n = len(pred)
        pred_mean = sum(pred) / n
        mae = sum(abs(a - b) for a, b in zip(y, pred)) / n * 100.0
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(y, pred)) / n) * 100.0
        bias = sum((b - a) for a, b in zip(y, pred)) / n * 100.0
        ssres = sum((a - b) ** 2 for a, b in zip(y, pred))
        sst = sum((a - ybar) ** 2 for a in y)
        r2 = 1.0 - ssres / sst if sst else float("nan")
        cov = sum((a - ybar) * (b - pred_mean) for a, b in zip(y, pred))
        sy = math.sqrt(sum((a - ybar) ** 2 for a in y))
        sp = math.sqrt(sum((b - pred_mean) ** 2 for b in pred))
        pearson = cov / (sy * sp) if sy and sp else float("nan")
        out.append(
            {
                "sampling_column": column,
                "n": n,
                "mae_pp": mae,
                "rmse_pp": rmse,
                "bias_pp": bias,
                "r2": r2,
                "pearson": pearson,
                "pred_mean": pred_mean,
                "official_mean": ybar,
            }
        )
    return out


def candidate_paths() -> List[Path]:
    if not NATIVE_DIR.exists():
        return []
    return sorted(NATIVE_DIR.glob("casee_native_dx2_*k_synthetic_fullplane*steps48000_spin12000/casee_probe_time_mean.csv"))


def log_files(directory: Path) -> List[Path]:
    patterns = ["*.log", "*run*.txt", "*run*.log", "fluidx3d*.log"]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(directory.glob(pattern))
    return sorted(set(found))


def build_rows() -> List[Dict[str, Any]]:
    untracked = git_untracked_paths()
    rows: List[Dict[str, Any]] = []
    for path in candidate_paths():
        manifest_path = path.parent / "citylbm_native_case_manifest.json"
        manifest = read_json(manifest_path)
        logs = log_files(path.parent)
        path_rel = rel(path)
        csv_untracked = path_rel in untracked or any(path_rel.startswith(item.rstrip("/") + "/") for item in untracked)
        for metric in metric_rows(path):
            formal = metric["sampling_column"] == "predicted_velocity_ratio"
            rows.append(
                {
                    "run_id": path.parent.name,
                    "csv_path": path_rel,
                    "csv_sha256": sha256(path),
                    "csv_git_tracked": git_tracked(path),
                    "csv_untracked_now": csv_untracked,
                    "manifest_path": rel(manifest_path),
                    "manifest_exists": manifest_path.exists(),
                    "manifest_evidence_boundary": manifest.get("evidence_boundary", ""),
                    "run_log_count": len(logs),
                    "run_logs": "; ".join(rel(item) for item in logs),
                    "dx_m": manifest.get("dx_m"),
                    "steps": manifest.get("steps"),
                    "spinup": manifest.get("spinup"),
                    "subgrid_enabled": manifest.get("subgrid_enabled"),
                    "inlet_turbulence_scale": manifest.get("inlet_turbulence_scale"),
                    "validation_height_m": manifest.get("validation_height_m"),
                    "probe_count_manifest": manifest.get("probe_count"),
                    "formal_sampling_mode": manifest.get("formal_sampling_mode"),
                    "sampling_column": metric["sampling_column"],
                    "n": metric["n"],
                    "mae_pp": metric["mae_pp"],
                    "rmse_pp": metric["rmse_pp"],
                    "bias_pp": metric["bias_pp"],
                    "r2": metric["r2"],
                    "pearson": metric["pearson"],
                    "paper_use": "local_candidate_diagnostic_only",
                    "claim_readiness": "blocked_missing_complete_run_log" if not logs else "limitations_ready_local_candidate",
                    "formal_result_allowed": bool(formal and logs and metric["n"] == 80 and metric["r2"] > 0.0),
                }
            )
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    fieldnames = list(rows[0].keys()) if rows else [
        "run_id",
        "csv_path",
        "sampling_column",
        "n",
        "mae_pp",
        "r2",
        "pearson",
        "claim_readiness",
        "formal_result_allowed",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    formal_rows = [row for row in rows if row.get("sampling_column") == "predicted_velocity_ratio"]
    best_raw = min(formal_rows, key=lambda row: float(row["mae_pp"]), default={})
    best_any = min(rows, key=lambda row: float(row["mae_pp"]), default={})
    any_formal_allowed = any(bool(row.get("formal_result_allowed")) for row in rows)
    complete_logs = sum(1 for row in formal_rows if int(row.get("run_log_count") or 0) > 0)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "orphan_candidate_csv_audit_passed": True,
        "candidate_csv_count": len({row["csv_path"] for row in rows}),
        "metric_row_count": len(rows),
        "formal_raw_candidate_count": len(formal_rows),
        "formal_raw_candidates_with_logs": complete_logs,
        "best_raw_run_id": best_raw.get("run_id", ""),
        "best_raw_mae_pp": best_raw.get("mae_pp"),
        "best_raw_r2": best_raw.get("r2"),
        "best_raw_pearson": best_raw.get("pearson"),
        "best_any_sampling_column": best_any.get("sampling_column", ""),
        "best_any_mae_pp": best_any.get("mae_pp"),
        "best_any_r2": best_any.get("r2"),
        "any_formal_result_allowed": any_formal_allowed,
        "claim_readiness": "limitations_ready_local_candidate_inventory; blocked formal promotion",
        "formal_accuracy_claim_supported": False,
        "boundary": (
            "This audit inventories local untracked/preexisting candidate CSVs only. It does not commit the raw CSVs, "
            "does not prove FluidX3D completed without complete run logs, does not update release_gate.json, and does "
            "not permit formal v0.4.0 or official z=2 m accuracy claims."
        ),
    }


def write_markdown(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines = [
        "# Case E Orphan Candidate CSV Audit",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Audit passed: {summary['orphan_candidate_csv_audit_passed']}",
        f"- Candidate CSVs: {summary['candidate_csv_count']}",
        f"- Formal raw candidates with complete logs: {summary['formal_raw_candidates_with_logs']}",
        f"- Any formal result allowed: {summary['any_formal_result_allowed']}",
        f"- Best raw run: `{summary['best_raw_run_id']}`",
        f"- Best raw MAE: {summary['best_raw_mae_pp']} pp",
        f"- Best raw R2: {summary['best_raw_r2']}",
        "",
        "## Formal Raw Rows",
        "",
        "| run | tracked? | logs | MAE pp | R2 | Pearson | readiness |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        if row["sampling_column"] != "predicted_velocity_ratio":
            continue
        lines.append(
            f"| `{row['run_id']}` | {row['csv_git_tracked']} | {row['run_log_count']} | "
            f"{float(row['mae_pp']):.3f} | {float(row['r2']):.4f} | {float(row['pearson']):.4f} | "
            f"`{row['claim_readiness']}` |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    summary = summarize(rows)
    OUT_JSON.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"orphan_candidate_csv_audit_passed": True, "candidate_csv_count": summary["candidate_csv_count"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
