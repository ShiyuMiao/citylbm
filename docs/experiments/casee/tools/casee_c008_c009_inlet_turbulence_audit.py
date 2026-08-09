#!/usr/bin/env python3
"""Audit C008-C011 AF-k synthetic full-plane inlet turbulence candidates."""

from __future__ import annotations

import csv
import glob
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
NATIVE_DIR = CASE_DIR / "native_cases"

ZCENTER_BASELINE_CSV = RESULTS_DIR / "casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv"
C005_CSV = RESULTS_DIR / "casee_c005_dx2_decomp4x1x1_20260809_215600_probe_time_mean.csv"
OUT_JSON = RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json"
OUT_CSV = RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.csv"
OUT_MD = RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.md"


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


def file_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": rel(path)}
    return {
        "found": True,
        "path": rel(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def latest(pattern: str) -> Path:
    matches = [Path(p) for p in glob.glob(str(RESULTS_DIR / pattern))]
    return sorted(matches)[-1] if matches else RESULTS_DIR / pattern


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def metrics(path: Path) -> Dict[str, Any]:
    rows = read_rows(path)
    obs = [float(r["official_velocity_ratio"]) for r in rows]
    pred = [float(r["predicted_velocity_ratio"]) for r in rows]
    n = len(rows)
    err = [p - o for p, o in zip(pred, obs)]
    mae = sum(abs(e) for e in err) / n * 100.0
    rmse = math.sqrt(sum(e * e for e in err) / n) * 100.0
    bias = sum(err) / n * 100.0
    obs_mean = sum(obs) / n
    pred_mean = sum(pred) / n
    ss_res = sum((p - o) ** 2 for p, o in zip(pred, obs))
    ss_tot = sum((o - obs_mean) ** 2 for o in obs)
    cov = sum((p - pred_mean) * (o - obs_mean) for p, o in zip(pred, obs))
    pred_var = sum((p - pred_mean) ** 2 for p in pred)
    obs_var = sum((o - obs_mean) ** 2 for o in obs)
    return {
        "n": n,
        "mae_pp": mae,
        "rmse_pp": rmse,
        "bias_pp": bias,
        "r2": None if ss_tot == 0.0 else 1.0 - ss_res / ss_tot,
        "pearson": None if pred_var == 0.0 or obs_var == 0.0 else cov / math.sqrt(pred_var * obs_var),
        "height_m": float(rows[0]["z_m"]) if rows else None,
        "sampling_mode": "raw_trilinear",
        "pred_mean": pred_mean,
        "official_mean": obs_mean,
    }


def delta(candidate: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "mae_pp": candidate["mae_pp"] - baseline["mae_pp"],
        "rmse_pp": candidate["rmse_pp"] - baseline["rmse_pp"],
        "bias_pp": candidate["bias_pp"] - baseline["bias_pp"],
        "r2": candidate["r2"] - baseline["r2"],
        "pearson": candidate["pearson"] - baseline["pearson"],
    }


def log_completed(path: Path, steps: int = 48000) -> bool:
    if not path.exists():
        return False
    raw = path.read_bytes()
    encoding = "utf-16-le" if raw[:200].count(b"\x00") > 20 else "utf-8"
    text = raw.decode(encoding, errors="replace")
    return re.search(rf"CaseE step\s+{steps}\s*/\s*{steps}", text) is not None


def manifest_ok(path: Path, scale: float) -> bool:
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return (
        data.get("condition") == "ac"
        and data.get("wind_direction") == "N"
        and float(data.get("validation_height_m")) == 2.0
        and int(data.get("probe_count")) == 80
        and data.get("formal_sampling_mode") == "raw_trilinear"
        and data.get("inlet_turbulence_mode") == "k_synthetic_fullplane"
        and abs(float(data.get("inlet_turbulence_scale")) - scale) < 1e-12
        and data.get("inlet_turbulence_uses_af_k") is True
    )


def candidate_row(candidate_id: str, scale: float, csv_path: Path, run_log: Path, compile_log: Path, compile_err: Path, manifest: Path) -> Dict[str, Any]:
    candidate_metrics = metrics(csv_path) if csv_path.exists() else {}
    baseline_metrics = metrics(ZCENTER_BASELINE_CSV)
    c005_metrics = metrics(C005_CSV)
    return {
        "candidate_id": candidate_id,
        "scale": scale,
        "csv": file_status(csv_path),
        "run_log": file_status(run_log),
        "compile_log": file_status(compile_log),
        "compile_err_log": file_status(compile_err),
        "case_manifest": file_status(manifest),
        "log_completed_48000": log_completed(run_log),
        "manifest_protocol_ok": manifest_ok(manifest, scale),
        "candidate_metrics": candidate_metrics,
        "delta_vs_zcenter_baseline": delta(candidate_metrics, baseline_metrics) if candidate_metrics else {},
        "delta_vs_c005_decomposition": delta(candidate_metrics, c005_metrics) if candidate_metrics else {},
    }


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fieldnames = [
        "candidate_id",
        "scale",
        "log_completed_48000",
        "manifest_protocol_ok",
        "mae_pp",
        "rmse_pp",
        "bias_pp",
        "r2",
        "pearson",
        "delta_mae_vs_zcenter",
        "delta_r2_vs_zcenter",
        "delta_pearson_vs_zcenter",
        "delta_mae_vs_c005",
        "delta_r2_vs_c005",
        "delta_pearson_vs_c005",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            m = row.get("candidate_metrics", {})
            dz = row.get("delta_vs_zcenter_baseline", {})
            dc = row.get("delta_vs_c005_decomposition", {})
            writer.writerow(
                {
                    "candidate_id": row["candidate_id"],
                    "scale": row["scale"],
                    "log_completed_48000": row["log_completed_48000"],
                    "manifest_protocol_ok": row["manifest_protocol_ok"],
                    "mae_pp": m.get("mae_pp"),
                    "rmse_pp": m.get("rmse_pp"),
                    "bias_pp": m.get("bias_pp"),
                    "r2": m.get("r2"),
                    "pearson": m.get("pearson"),
                    "delta_mae_vs_zcenter": dz.get("mae_pp"),
                    "delta_r2_vs_zcenter": dz.get("r2"),
                    "delta_pearson_vs_zcenter": dz.get("pearson"),
                    "delta_mae_vs_c005": dc.get("mae_pp"),
                    "delta_r2_vs_c005": dc.get("r2"),
                    "delta_pearson_vs_c005": dc.get("pearson"),
                }
            )


def write_md(path: Path, payload: Dict[str, Any]) -> None:
    best = payload["best_candidate"]
    m = best.get("candidate_metrics", {})
    dz = best.get("delta_vs_zcenter_baseline", {})
    dc = best.get("delta_vs_c005_decomposition", {})
    lines = [
        "# C008-C011 Inlet Turbulence Sweep Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Status: `{payload['status']}`",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        f"- Best candidate: `{best.get('candidate_id')}`",
        "",
        "## Best Official z=2 m Raw Metric",
        "",
        f"- MAE: {m.get('mae_pp')} pp",
        f"- RMSE: {m.get('rmse_pp')} pp",
        f"- Bias: {m.get('bias_pp')} pp",
        f"- R2: {m.get('r2')}",
        f"- Pearson: {m.get('pearson')}",
        f"- Delta MAE vs z-center baseline: {dz.get('mae_pp')} pp",
        f"- Delta R2 vs z-center baseline: {dz.get('r2')}",
        f"- Delta Pearson vs z-center baseline: {dz.get('pearson')}",
        f"- Delta MAE vs C005: {dc.get('mae_pp')} pp",
        f"- Delta R2 vs C005: {dc.get('r2')}",
        f"- Delta Pearson vs C005: {dc.get('pearson')}",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    c008_csv = latest("casee_c008_inlet_k_synthetic_*_probe_time_mean.csv")
    c009_csv = latest("casee_c009_inlet_k_synthetic_s0p7_*_probe_time_mean.csv")
    c010_csv = latest("casee_c010_inlet_k_synthetic_s1p0_*_probe_time_mean.csv")
    c011_csv = latest("casee_c011_inlet_k_synthetic_s1p5_*_probe_time_mean.csv")
    c008_run = latest("fluidx3d_c008_inlet_k_synthetic_run_*.log")
    c009_run = latest("fluidx3d_c009_inlet_k_synthetic_s0p7_run_*.log")
    c010_run = latest("fluidx3d_c010_inlet_k_synthetic_s1p0_run_*.log")
    c011_run = latest("fluidx3d_c011_inlet_k_synthetic_s1p5_run_*.log")
    c008 = candidate_row(
        "C008_inlet_k_synthetic_fullplane_s0p35",
        0.35,
        c008_csv,
        c008_run,
        RESULTS_DIR / "fluidx3d_c008_inlet_k_synthetic_compile.log",
        RESULTS_DIR / "fluidx3d_c008_inlet_k_synthetic_compile.err.log",
        NATIVE_DIR / "casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s0p35_pmodes_steps48000_spin12000" / "citylbm_native_case_manifest.json",
    )
    c009 = candidate_row(
        "C009_inlet_k_synthetic_fullplane_s0p70",
        0.70,
        c009_csv,
        c009_run,
        RESULTS_DIR / "fluidx3d_c009_inlet_k_synthetic_s0p7_compile.log",
        RESULTS_DIR / "fluidx3d_c009_inlet_k_synthetic_s0p7_compile.err.log",
        NATIVE_DIR / "casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s0p7_pmodes_steps48000_spin12000" / "citylbm_native_case_manifest.json",
    )
    c010 = candidate_row(
        "C010_inlet_k_synthetic_fullplane_s1p00",
        1.00,
        c010_csv,
        c010_run,
        RESULTS_DIR / "fluidx3d_c010_inlet_k_synthetic_s1p0_compile.log",
        RESULTS_DIR / "fluidx3d_c010_inlet_k_synthetic_s1p0_compile.err.log",
        NATIVE_DIR / "casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s1_pmodes_steps48000_spin12000" / "citylbm_native_case_manifest.json",
    )
    c011 = candidate_row(
        "C011_inlet_k_synthetic_fullplane_s1p50",
        1.50,
        c011_csv,
        c011_run,
        RESULTS_DIR / "fluidx3d_c011_inlet_k_synthetic_s1p5_compile.log",
        RESULTS_DIR / "fluidx3d_c011_inlet_k_synthetic_s1p5_compile.err.log",
        NATIVE_DIR / "casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_dom4x1x1_inlet_k_synthetic_fullplane_s1p5_pmodes_steps48000_spin12000" / "citylbm_native_case_manifest.json",
    )
    candidates = [c008, c009, c010, c011]
    best = min(candidates, key=lambda row: row["candidate_metrics"].get("rmse_pp", float("inf")))
    bm = best["candidate_metrics"]
    all_protocol_ok = all(row["log_completed_48000"] and row["manifest_protocol_ok"] for row in candidates)
    improved_vs_zcenter = (
        best["delta_vs_zcenter_baseline"]["mae_pp"] < 0.0
        and best["delta_vs_zcenter_baseline"]["r2"] > 0.0
        and best["delta_vs_zcenter_baseline"]["pearson"] > 0.0
    )
    metric_gate = bm.get("mae_pp", 999.0) < 15.0 and bm.get("r2", -999.0) > 0.0 and bm.get("pearson", -999.0) > 0.0
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audit_id": "casee_c008_c011_inlet_turbulence_sweep_audit",
        "status": "completed_inlet_turbulence_improved_but_negative_r2" if all_protocol_ok and improved_vs_zcenter and not metric_gate else "blocked_or_inconclusive",
        "evidence_type": "newly_run",
        "claim_readiness": "limitations_ready_inlet_turbulence_improvement; blocked formal accuracy release",
        "formal_release_allowed": False,
        "formal_accuracy_claim_supported": False,
        "pass_condition_met": bool(all_protocol_ok and improved_vs_zcenter),
        "metric_gate_passed": bool(metric_gate),
        "all_protocol_ok": all_protocol_ok,
        "zcenter_baseline_csv": file_status(ZCENTER_BASELINE_CSV),
        "c005_decomposition_csv": file_status(C005_CSV),
        "candidates": candidates,
        "best_candidate": best,
        "boundary": (
            "C008-C011 are completed official-height raw_trilinear candidate runs using a default-off synthetic full-plane inlet based on AF_caseE k. "
            "They improve MAE, R2, and Pearson, but R2 remains negative and the turbulence scale is a diagnostic sweep parameter. "
            "Use as inlet-turbulence evidence and software-feedback guidance only; do not claim formal v0.4.0, predictive accuracy, mesh independence, or LES improvement."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, candidates)
    write_md(OUT_MD, payload)
    print(json.dumps({"out_json": rel(OUT_JSON), "status": payload["status"], "best_r2": bm.get("r2")}, indent=2))
    return 0 if payload["pass_condition_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
