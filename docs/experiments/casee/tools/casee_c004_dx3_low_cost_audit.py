#!/usr/bin/env python3
"""Audit C004 dx=3 low-cost Case E direction/convention regression."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
DATA_DIR = CASE_DIR / "official_data"
RESULTS_DIR = CASE_DIR / "results"
CASE_DIR_C004 = CASE_DIR / "native_cases" / "casee_native_dx3_yn_sgs_gshift1_zoff0_nu0p001_pmodes_steps48000_spin12000"
ZCENTER_BASELINE_CSV = RESULTS_DIR / "casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv"
PREEXISTING_DX3_CSV = RESULTS_DIR / "casee_native_dx3_probe_time_mean.csv"
OUT_JSON = RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json"
OUT_CSV = RESULTS_DIR / "casee_c004_dx3_low_cost_audit.csv"
OUT_MD = RESULTS_DIR / "casee_c004_dx3_low_cost_audit.md"


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


def file_status(path: Path | None) -> Dict[str, Any]:
    if path is None:
        return {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime_utc": ""}
    return {
        "found": path.exists(),
        "path": rel(path),
        "sha256": sha256(path) if path.exists() else "",
        "size_bytes": path.stat().st_size if path.exists() else None,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat() if path.exists() else "",
    }


def latest(pattern: str) -> Path | None:
    candidates = sorted(RESULTS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def official_refs() -> Dict[int, float]:
    refs: Dict[int, float] = {}
    with (DATA_DIR / "RS_caseE.csv").open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("case") != "ac" or row.get("Wind_direction") != "N":
                continue
            if abs(float(row.get("z(m)", "nan")) - 2.0) > 1e-9:
                continue
            refs[int(row["No."])] = float(row["Velocity_Ratio"])
    if len(refs) != 80:
        raise SystemExit(f"Expected 80 official ac+N z=2 m probes, found {len(refs)}")
    return refs


def metrics(path: Path) -> Dict[str, Any]:
    rows = read_rows(path)
    refs = official_refs()
    official = [refs[int(row["No."])] for row in rows]
    pred = [float(row["predicted_velocity_ratio"]) for row in rows]
    residuals = [p - o for p, o in zip(pred, official)]
    n = len(rows)
    mean_o = sum(official) / n
    mean_p = sum(pred) / n
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((o - mean_o) ** 2 for o in official)
    var_o = sum((o - mean_o) ** 2 for o in official)
    var_p = sum((p - mean_p) ** 2 for p in pred)
    cov = sum((o - mean_o) * (p - mean_p) for o, p in zip(official, pred))
    return {
        "n": n,
        "mae_pp": sum(abs(r) for r in residuals) / n * 100.0,
        "rmse_pp": math.sqrt(ss_res / n) * 100.0,
        "bias_pp": sum(residuals) / n * 100.0,
        "r2": 1.0 - ss_res / ss_tot if ss_tot else None,
        "pearson": cov / math.sqrt(var_o * var_p) if var_o and var_p else None,
        "height_m": 2.0,
        "sampling_mode": "raw_trilinear",
    }


def decode_log(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-16-le"):
        text = raw.decode(encoding, errors="replace")
        if "CaseE step" in text:
            return text
    return raw.replace(b"\x00", b"").decode("utf-8", errors="replace")


def delta(candidate: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mae_pp": candidate["mae_pp"] - baseline["mae_pp"],
        "rmse_pp": candidate["rmse_pp"] - baseline["rmse_pp"],
        "bias_pp": candidate["bias_pp"] - baseline["bias_pp"],
        "r2": candidate["r2"] - baseline["r2"],
        "pearson": candidate["pearson"] - baseline["pearson"],
    }


def manifest_protocol_ok(path: Path) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return (
        data.get("dx_m") == 3.0
        and data.get("steps") == 48000
        and data.get("spinup") == 12000
        and data.get("sample_dt") == 2000
        and data.get("condition") == "ac"
        and data.get("wind_direction") == "N"
        and data.get("solver_wind_y") == -1.0
        and data.get("ground_offset_cells") == 1
        and data.get("origin_z_offset_m") == 0.0
        and data.get("nu_lbm") == 0.001
        and data.get("probe_count") == 80
        and data.get("formal_sampling_mode") == "raw_trilinear"
    )


def main() -> int:
    candidate_csv = latest("casee_c004_dx3_low_cost_*_probe_time_mean.csv")
    run_log = latest("fluidx3d_c004_dx3_low_cost_run_*.log")
    err_log = latest("fluidx3d_c004_dx3_low_cost_run_*.err.log")
    compile_log = RESULTS_DIR / "fluidx3d_c004_dx3_low_cost_compile.log"
    compile_err = RESULTS_DIR / "fluidx3d_c004_dx3_low_cost_compile.err.log"
    manifest = CASE_DIR_C004 / "citylbm_native_case_manifest.json"
    missing = [
        name
        for name, path in {
            "candidate_csv": candidate_csv,
            "zcenter_baseline_csv": ZCENTER_BASELINE_CSV,
            "preexisting_dx3_csv": PREEXISTING_DX3_CSV,
            "run_log": run_log,
            "compile_log": compile_log,
            "case_manifest": manifest,
        }.items()
        if path is None or not path.exists()
    ]

    if missing:
        payload: Dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidate_id": "C004_dx3_low_cost_direction_check",
            "status": "blocked_missing_artifacts",
            "missing_artifacts": missing,
            "evidence_type": "blocked",
            "claim_readiness": "blocked_c004_audit",
            "formal_release_allowed": False,
            "formal_accuracy_claim_supported": False,
            "boundary": "C004 has no auditable result until generated setup, compile log, run log, and 80-probe CSV exist.",
        }
    else:
        assert candidate_csv is not None
        zcenter_metrics = metrics(ZCENTER_BASELINE_CSV)
        preexisting_metrics = metrics(PREEXISTING_DX3_CSV)
        candidate_metrics = metrics(candidate_csv)
        log_completed = "CaseE step 48000 / 48000" in decode_log(run_log)
        protocol_ok = manifest_protocol_ok(manifest)
        probe_count_ok = candidate_metrics["n"] == 80
        pearson_positive = candidate_metrics["pearson"] is not None and candidate_metrics["pearson"] > 0.0
        no_direction_reversal = pearson_positive and protocol_ok
        improved_vs_zcenter = (
            candidate_metrics["mae_pp"] < zcenter_metrics["mae_pp"]
            and candidate_metrics["r2"] > zcenter_metrics["r2"]
            and candidate_metrics["pearson"] > zcenter_metrics["pearson"]
        )
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "candidate_id": "C004_dx3_low_cost_direction_check",
            "status": "completed_low_cost_positive_correlation" if no_direction_reversal else "completed_low_cost_regression_warning",
            "evidence_type": "newly_run",
            "claim_readiness": "limitations_ready_dx3_low_cost_regression; blocked formal accuracy release",
            "formal_release_allowed": False,
            "formal_accuracy_claim_supported": False,
            "pass_condition_met": no_direction_reversal,
            "log_completed_48000": log_completed,
            "probe_count_ok": probe_count_ok,
            "manifest_protocol_ok": protocol_ok,
            "pearson_positive": pearson_positive,
            "improved_vs_zcenter_baseline": improved_vs_zcenter,
            "zcenter_baseline_csv": file_status(ZCENTER_BASELINE_CSV),
            "preexisting_dx3_csv": file_status(PREEXISTING_DX3_CSV),
            "candidate_csv": file_status(candidate_csv),
            "run_log": file_status(run_log),
            "run_err_log": file_status(err_log),
            "compile_log": file_status(compile_log),
            "compile_err_log": file_status(compile_err),
            "case_manifest": file_status(manifest),
            "zcenter_baseline_metrics": zcenter_metrics,
            "preexisting_dx3_metrics": preexisting_metrics,
            "candidate_metrics": candidate_metrics,
            "metric_delta_vs_zcenter_baseline": delta(candidate_metrics, zcenter_metrics),
            "metric_delta_vs_preexisting_dx3": delta(candidate_metrics, preexisting_metrics),
            "boundary": (
                "C004 is a completed dx=3 low-cost official z=2 m raw_trilinear control run. "
                "It checks direction/protocol consistency and coarse-grid behavior only. It does not "
                "support formal v0.4.0, mesh independence, or a default accuracy upgrade."
            ),
        }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    fields = [
        "candidate_id",
        "status",
        "evidence_type",
        "log_completed_48000",
        "probe_count_ok",
        "manifest_protocol_ok",
        "mae_pp",
        "r2",
        "pearson",
        "delta_mae_vs_zcenter_pp",
        "delta_r2_vs_zcenter",
        "delta_pearson_vs_zcenter",
        "pearson_positive",
        "pass_condition_met",
        "formal_release_allowed",
        "claim_readiness",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        m = payload.get("candidate_metrics", {})
        d = payload.get("metric_delta_vs_zcenter_baseline", {})
        writer.writerow(
            {
                "candidate_id": payload["candidate_id"],
                "status": payload["status"],
                "evidence_type": payload["evidence_type"],
                "log_completed_48000": payload.get("log_completed_48000"),
                "probe_count_ok": payload.get("probe_count_ok"),
                "manifest_protocol_ok": payload.get("manifest_protocol_ok"),
                "mae_pp": m.get("mae_pp"),
                "r2": m.get("r2"),
                "pearson": m.get("pearson"),
                "delta_mae_vs_zcenter_pp": d.get("mae_pp"),
                "delta_r2_vs_zcenter": d.get("r2"),
                "delta_pearson_vs_zcenter": d.get("pearson"),
                "pearson_positive": payload.get("pearson_positive"),
                "pass_condition_met": payload.get("pass_condition_met"),
                "formal_release_allowed": payload.get("formal_release_allowed"),
                "claim_readiness": payload.get("claim_readiness"),
            }
        )

    m = payload.get("candidate_metrics", {})
    d = payload.get("metric_delta_vs_zcenter_baseline", {})
    lines = [
        "# C004 dx=3 Low-Cost Direction Check Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- 48000-step log complete: {payload.get('log_completed_48000')}",
        f"- Manifest protocol ok: {payload.get('manifest_protocol_ok')}",
        f"- Pass condition met: {payload.get('pass_condition_met')}",
        f"- Formal release allowed: {payload.get('formal_release_allowed')}",
        "",
        "## Official z=2 m raw_trilinear metric",
        "",
        f"- MAE: {m.get('mae_pp')} pp",
        f"- R2: {m.get('r2')}",
        f"- Pearson: {m.get('pearson')}",
        "",
        "## Delta vs current z-center baseline",
        "",
        f"- MAE delta: {d.get('mae_pp')} pp",
        f"- R2 delta: {d.get('r2')}",
        f"- Pearson delta: {d.get('pearson')}",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out_json": rel(OUT_JSON), "status": payload["status"], "r2": m.get("r2")}, indent=2))
    return 0 if payload.get("evidence_type") == "newly_run" and payload.get("log_completed_48000") and payload.get("probe_count_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
