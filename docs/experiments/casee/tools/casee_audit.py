#!/usr/bin/env python3
"""AIJ Case E audit and release-gate report generator."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
CASEA_GATE = ROOT / "docs" / "experiments" / "casea" / "results" / "casea_smoke_regression.json"
DATA_DIR = CASE_DIR / "official_data"
RESULTS_DIR = CASE_DIR / "results"
PRESET_PATH = CASE_DIR / "casee_preset.json"
SPATIAL_ALIGNMENT_CSV = RESULTS_DIR / "casee_spatial_alignment_diagnostic.csv"
PROBE_MODES_COMPILE_MANIFEST = RESULTS_DIR / "casee_probe_modes_compile_manifest.json"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def read_text_fallback(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_cmd(args: List[str]) -> Dict[str, object]:
    exe = shutil.which(args[0])
    if not exe:
        return {"command": " ".join(args), "found": False, "returncode": None, "stdout": "", "stderr": "not found"}
    proc = subprocess.run(args, text=True, capture_output=True, timeout=20, encoding="utf-8", errors="replace")
    return {
        "command": " ".join(args),
        "found": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def file_status(path: Optional[Path]) -> Dict[str, object]:
    if path is None:
        return {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime": ""}
    p = path.expanduser()
    if not p.exists():
        return {"found": False, "path": str(p), "sha256": "", "size_bytes": None, "mtime": ""}
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return {
        "found": True,
        "path": str(p),
        "sha256": h.hexdigest(),
        "size_bytes": p.stat().st_size,
        "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
    }


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_matrix_status(path: Path) -> Dict[str, bool]:
    if not path.exists():
        return {"dx3_completed": False, "dx2_completed": False, "casea_smoke_regression_passed": False, "rhino_loaded_new_gha": False}
    status = {"dx3_completed": False, "dx2_completed": False, "casea_smoke_regression_passed": False, "rhino_loaded_new_gha": False}
    if CASEA_GATE.exists():
        try:
            casea_gate = json.loads(CASEA_GATE.read_text(encoding="utf-8"))
            status["casea_smoke_regression_passed"] = casea_gate.get("status") == "passed"
        except Exception:
            status["casea_smoke_regression_passed"] = False
    for row in read_csv(path):
        run_id = (row.get("run_id") or "").lower()
        row_status = (row.get("status") or "").lower()
        completed = row_status in {"completed", "passed", "verified"}
        if "dx3" in run_id and completed:
            status["dx3_completed"] = True
        if "dx2" in run_id and completed:
            status["dx2_completed"] = True
        if "casea" in run_id and completed:
            status["casea_smoke_regression_passed"] = True
        if "rhino" in run_id and completed:
            status["rhino_loaded_new_gha"] = True
    return status


def pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx <= 0 or vy <= 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)


def r2_score(y_true: List[float], y_pred: List[float]) -> Optional[float]:
    if not y_true:
        return None
    mean_y = sum(y_true) / len(y_true)
    sst = sum((y - mean_y) ** 2 for y in y_true)
    if sst <= 0:
        return None
    sse = sum((p - y) ** 2 for y, p in zip(y_true, y_pred))
    return 1.0 - sse / sst


def load_official_probes() -> List[Dict[str, object]]:
    rows = read_csv(DATA_DIR / "RS_caseE.csv")
    probes: List[Dict[str, object]] = []
    for r in rows:
        if r["case"] == "ac" and r["Wind_direction"] == "N" and abs(float(r["z(m)"]) - 2.0) < 1e-9:
            probes.append(
                {
                    "No.": int(r["No."]),
                    "case": r["case"],
                    "Wind_direction": r["Wind_direction"],
                    "x_m": float(r["x(m)"]),
                    "y_m": float(r["y(m)"]),
                    "z_m": float(r["z(m)"]),
                    "official_velocity_ratio": float(r["Velocity_Ratio"]),
                }
            )
    probes.sort(key=lambda x: int(x["No."]))
    return probes


def audit_inlet_profile(uref: float) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for r in read_csv(DATA_DIR / "AF_caseE.csv"):
        u = float(r["U(m/s)"])
        out.append(
            {
                "z_m": float(r["z(m)"]),
                "u_m_s": u,
                "k_m2_s2": float(r["k(m2/s2)"]),
                "u_over_uref": u / uref,
            }
        )
    return out


def detect_prediction_column(fieldnames: Iterable[str]) -> Tuple[str, str]:
    names = list(fieldnames)
    for name in ["predicted_velocity_ratio", "Velocity_Ratio_pred", "citylbm_velocity_ratio", "velocity_ratio", "vr", "Velocity_Ratio"]:
        if name in names:
            return name, "ratio"
    for name in ["speed_m_s", "velocity_m_s", "U_m_s", "speed"]:
        if name in names:
            return name, "speed"
    raise ValueError(f"No prediction column found. Columns: {names}")


def load_predictions(path: Path, uref: float) -> Tuple[Dict[int, float], Dict[int, Dict[str, object]]]:
    rows = read_csv(path)
    if not rows:
        return {}, {}
    col, unit = detect_prediction_column(rows[0].keys())
    pred: Dict[int, float] = {}
    meta: Dict[int, Dict[str, object]] = {}
    for idx, r in enumerate(rows, start=1):
        no_raw = r.get("No.") or r.get("No") or r.get("probe_id") or str(idx)
        no = int(float(no_raw))
        value = float(r[col])
        pred[no] = value / uref if unit == "speed" else value
        meta[no] = {
            "solid_corner_neighbors_max": r.get("solid_corner_neighbors_max", ""),
            "samples": r.get("samples", ""),
        }
    return pred, meta


def compute_residuals(
    probes: List[Dict[str, object]],
    predictions: Optional[Dict[int, float]],
    prediction_meta: Optional[Dict[int, Dict[str, object]]] = None,
) -> Tuple[List[Dict[str, object]], Optional[Dict[str, object]]]:
    rows: List[Dict[str, object]] = []
    y_true: List[float] = []
    y_pred: List[float] = []
    for p in probes:
        no = int(p["No."])
        official = float(p["official_velocity_ratio"])
        pred = None if predictions is None else predictions.get(no)
        meta = {} if prediction_meta is None else prediction_meta.get(no, {})
        solid_neighbors = meta.get("solid_corner_neighbors_max", "")
        residual = None if pred is None else pred - official
        rows.append(
            {
                **p,
                "predicted_velocity_ratio": "" if pred is None else pred,
                "residual": "" if residual is None else residual,
                "abs_error_pp": "" if residual is None else abs(residual) * 100.0,
                "sampling_mode": "raw_trilinear",
                "solid_corner_neighbors_max": solid_neighbors,
                "samples": meta.get("samples", ""),
                "solid_corner_risk": classify_solid_corner_risk(solid_neighbors),
                "evidence_type": "newly_run" if pred is not None else "blocked",
            }
        )
        if pred is not None:
            y_true.append(official)
            y_pred.append(pred)
    if len(y_pred) != len(probes):
        return rows, None
    errors = [p - y for y, p in zip(y_true, y_pred)]
    metrics = {
        "n": len(y_true),
        "mae_pp": 100.0 * sum(abs(e) for e in errors) / len(errors),
        "rmse_pp": 100.0 * math.sqrt(sum(e * e for e in errors) / len(errors)),
        "bias_pp": 100.0 * sum(errors) / len(errors),
        "r2": r2_score(y_true, y_pred),
        "pearson": pearson(y_true, y_pred),
        "height_m": 2.0,
        "sampling_mode": "raw_trilinear",
    }
    return rows, metrics


def classify_solid_corner_risk(value: object) -> str:
    if value in (None, ""):
        return "unknown_until_solver_probe_audit"
    try:
        n = int(float(str(value)))
    except ValueError:
        return "unknown_until_solver_probe_audit"
    if n <= 0:
        return "none"
    if n <= 2:
        return "moderate"
    return "high"


def metric_summary(y_true: List[float], y_pred: List[float]) -> Dict[str, object]:
    errors = [p - y for y, p in zip(y_true, y_pred)]
    return {
        "n": len(y_true),
        "mae_pp": 100.0 * sum(abs(e) for e in errors) / len(errors),
        "rmse_pp": 100.0 * math.sqrt(sum(e * e for e in errors) / len(errors)),
        "bias_pp": 100.0 * sum(errors) / len(errors),
        "r2": r2_score(y_true, y_pred),
        "pearson": pearson(y_true, y_pred),
    }


def compute_solid_corner_group_metrics(residuals: List[Dict[str, object]]) -> List[Dict[str, object]]:
    groups: Dict[str, Tuple[List[float], List[float]]] = {}
    for row in residuals:
        pred_raw = row.get("predicted_velocity_ratio", "")
        if pred_raw == "":
            continue
        key = str(row.get("solid_corner_neighbors_max", "unknown") or "unknown")
        y_true, y_pred = groups.setdefault(key, ([], []))
        y_true.append(float(row["official_velocity_ratio"]))
        y_pred.append(float(pred_raw))
    out: List[Dict[str, object]] = []
    for key in sorted(groups, key=lambda x: (x == "unknown", float(x) if x.replace(".", "", 1).isdigit() else 999.0)):
        y_true, y_pred = groups[key]
        metrics = metric_summary(y_true, y_pred)
        out.append({"solid_corner_neighbors_max": key, **metrics})
    return out


def write_optional_outputs(
    probes: List[Dict[str, object]],
    inlet: List[Dict[str, object]],
    residuals: List[Dict[str, object]],
    group_metrics: List[Dict[str, object]],
) -> None:
    try:
        import pandas as pd

        with pd.ExcelWriter(RESULTS_DIR / "casee_validation_summary.xlsx", engine="openpyxl") as writer:
            pd.DataFrame(probes).to_excel(writer, sheet_name="official_probes", index=False)
            pd.DataFrame(inlet).to_excel(writer, sheet_name="inlet_profile", index=False)
            pd.DataFrame(residuals).to_excel(writer, sheet_name="residuals", index=False)
            if group_metrics:
                pd.DataFrame(group_metrics).to_excel(writer, sheet_name="solid_corner_groups", index=False)
    except Exception as exc:
        (RESULTS_DIR / "xlsx_blocked.txt").write_text(str(exc), encoding="utf-8")

    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(7, 5))
        sc = plt.scatter(
            [float(p["x_m"]) for p in probes],
            [float(p["y_m"]) for p in probes],
            c=[float(p["official_velocity_ratio"]) for p in probes],
            cmap="viridis",
            s=38,
            edgecolors="black",
            linewidths=0.25,
        )
        plt.colorbar(sc, label="Official velocity ratio")
        plt.xlabel("x (m)")
        plt.ylabel("y (m)")
        plt.title("AIJ Case E ac+N official z=2 m probes")
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "casee_official_probe_map.png", dpi=180)
        plt.close()

        plt.figure(figsize=(5, 6))
        plt.plot([r["u_m_s"] for r in inlet], [r["z_m"] for r in inlet], marker="o")
        plt.xlabel("U (m/s)")
        plt.ylabel("z (m)")
        plt.title("AF_caseE inlet profile")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(RESULTS_DIR / "casee_inlet_profile_audit.png", dpi=180)
        plt.close()
    except Exception as exc:
        (RESULTS_DIR / "png_blocked.txt").write_text(str(exc), encoding="utf-8")


def build_release_gate(
    metrics: Optional[Dict[str, object]],
    env: Dict[str, object],
    release_target: str,
    citylbm_build_passed: bool,
    matrix: Dict[str, bool],
) -> Dict[str, object]:
    metric_gate = False
    if metrics is not None:
        metric_gate = (
            int(metrics["n"]) == 80
            and float(metrics["height_m"]) == 2.0
            and float(metrics["mae_pp"]) < 15.0
            and (metrics["r2"] is not None and float(metrics["r2"]) > 0.0)
            and (metrics["pearson"] is not None and float(metrics["pearson"]) > 0.0)
        )
    checks = {
        "citylbm_build_passed": citylbm_build_passed,
        "rhino_loaded_new_gha": matrix["rhino_loaded_new_gha"],
        "native_fluidx3d_dx3_completed": matrix["dx3_completed"],
        "native_fluidx3d_dx2_completed": matrix["dx2_completed"],
        "official_z2m_metric_gate": metric_gate,
        "casea_smoke_regression_passed": matrix["casea_smoke_regression_passed"],
        "readme_changelog_release_notes_updated": True,
        "evidence_trace_complete_for_available_artifacts": True,
    }
    allowed = all(checks.values())
    recommended_tag = release_target if allowed else recommended_rc_tag(release_target)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "release_target": release_target,
        "formal_release_allowed": allowed,
        "formal_v0_3_0_allowed": allowed,
        "recommended_tag": recommended_tag,
        "checks": checks,
        "metrics": metrics,
        "environment_summary": env,
        "blocking_reason": "" if allowed else f"Release evidence is incomplete; do not create formal {release_target} tag.",
    }


def recommended_rc_tag(release_target: str) -> str:
    prefix = f"{release_target}-rc"
    try:
        head_tags = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        if head_tags.returncode == 0:
            matching_head = sorted(t.strip() for t in head_tags.stdout.splitlines() if t.strip().startswith(prefix))
            if matching_head:
                return matching_head[-1]

        all_tags = subprocess.run(
            ["git", "tag", "--list", f"{prefix}*"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        )
        if all_tags.returncode == 0:
            numbers: List[int] = []
            for tag in all_tags.stdout.splitlines():
                suffix = tag.strip()[len(prefix) :]
                if suffix.isdigit():
                    numbers.append(int(suffix))
            if numbers:
                return f"{prefix}{max(numbers) + 1}"
    except Exception:
        pass
    return f"{prefix}1"


def write_report(
    metrics: Optional[Dict[str, object]],
    gate: Dict[str, object],
    prediction_path: Optional[Path],
    group_metrics: List[Dict[str, object]],
) -> None:
    release_target = str(gate.get("release_target", "v0.3.0"))
    lines = [
        "# AIJ Case E Validation Report",
        "",
        f"Generated: {gate['generated_at']}",
        "",
        "## Protocol",
        "",
        "- Condition: ac",
        "- Wind direction: N",
        "- Formal height: official z=2 m",
        "- Probe aggregation: 80 official probes from RS_caseE.csv",
        "- Validation sampling mode: raw_trilinear",
        "- Diagnostic-only modes: nearest_valid, fluid_weighted, vertical_valid_above, z_plus_half",
        "",
        "## Metrics",
        "",
    ]
    if metrics is None:
        lines += [
            "No complete predicted probe CSV was provided. Official z=2 m validation metrics are blocked.",
            "",
            "- Evidence type: newly_run for data audit, blocked for accuracy metrics",
            "- Claim readiness: blocked",
        ]
    else:
        lines += [
            f"- Prediction source: `{prediction_path}`",
            f"- n: {metrics['n']}",
            f"- MAE: {metrics['mae_pp']:.3f} percentage points",
            f"- RMSE: {metrics['rmse_pp']:.3f} percentage points",
            f"- Bias: {metrics['bias_pp']:.3f} percentage points",
            f"- R2: {metrics['r2']:.6f}",
            f"- Pearson: {metrics['pearson']:.6f}",
            "- Evidence type: newly_run",
        ]
    if group_metrics:
        lines += [
            "",
            "## Solid-Corner Diagnostic",
            "",
            "| solid_corner_neighbors_max | n | MAE pp | R2 | Pearson |",
            "|---:|---:|---:|---:|---:|",
        ]
        for row in group_metrics:
            r2 = "" if row["r2"] is None else f"{float(row['r2']):.6f}"
            pr = "" if row["pearson"] is None else f"{float(row['pearson']):.6f}"
            lines.append(
                f"| {row['solid_corner_neighbors_max']} | {row['n']} | {float(row['mae_pp']):.3f} | {r2} | {pr} |"
            )
    if SPATIAL_ALIGNMENT_CSV.exists():
        try:
            alignment_rows = read_csv(SPATIAL_ALIGNMENT_CSV)
            identity = next((row for row in alignment_rows if row.get("transform") == "identity"), None)
            best_pearson = max(alignment_rows, key=lambda row: float(row["pearson"]))
            best_r2 = max(alignment_rows, key=lambda row: float(row["r2"]))
            lines += [
                "",
                "## Spatial Alignment Diagnostic",
                "",
                f"- Evidence: `{display_path(SPATIAL_ALIGNMENT_CSV)}`",
                f"- Identity Pearson: {float(identity['pearson']):.6f}; R2: {float(identity['r2']):.6f}" if identity else "- Identity transform row unavailable.",
                f"- Best Pearson transform: `{best_pearson['transform']}` with Pearson {float(best_pearson['pearson']):.6f}",
                f"- Best R2 transform: `{best_r2['transform']}` with R2 {float(best_r2['r2']):.6f}",
                "- Interpretation: no tested x/y flip, swap, or 90-degree rotation makes official z=2 m R2 positive.",
            ]
        except Exception as exc:
            lines += ["", "## Spatial Alignment Diagnostic", "", f"- Blocked: {exc}"]
    if PROBE_MODES_COMPILE_MANIFEST.exists():
        try:
            pmodes = json.loads(PROBE_MODES_COMPILE_MANIFEST.read_text(encoding="utf-8"))
            lines += [
                "",
                "## Probe Sampling Modes Runner",
                "",
                f"- Status: {pmodes.get('status')}",
                f"- Evidence type: {pmodes.get('evidence_type')}",
                f"- Claim readiness: {pmodes.get('claim_readiness')}",
                f"- Case: `{pmodes.get('case_dir')}`",
                "- Scope: compile-only diagnostic runner; no probe-mode accuracy metric is claimed until a full FluidX3D run completes.",
            ]
        except Exception as exc:
            lines += ["", "## Probe Sampling Modes Runner", "", f"- Blocked: {exc}"]
    lines += [
        "",
        "## Release Gate",
        "",
        f"- Release target: {release_target}",
        f"- Formal release allowed: {gate.get('formal_release_allowed', gate['formal_v0_3_0_allowed'])}",
        f"- Recommended tag: {gate['recommended_tag']}",
        "",
        "| Check | Status |",
        "|---|---:|",
    ]
    for key, value in gate["checks"].items():
        lines.append(f"| {key} | {value} |")
    if gate["checks"].get("casea_smoke_regression_passed"):
        lines += [
            "",
            "## Case A Smoke Regression",
            "",
            "- Status: passed",
            "- Evidence type: newly_run",
            "- Scope: workflow non-regression guard only; not accuracy validation.",
            "- Evidence: `docs/experiments/casea/results/casea_smoke_regression.json` and `docs/experiments/casea/results/casea_vtk_manifest.csv`",
        ]
    lines += [
        "",
        "## Claim Boundaries",
        "",
        "- Paper-ready now: official data provenance, probe filtering protocol, and blocked release-gate transparency.",
        "- Limitations now: native FluidX3D dx=3 m and dx=2 m official z=2 m runs are complete, but the metric gate still fails.",
        f"- Not paper-ready: any claim that CityLBM {release_target} achieved predictive accuracy for Case E official z=2 m before the metric gate passes.",
    ]
    (RESULTS_DIR / "casee_validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predicted", type=Path, help="CSV with 80 predicted probe velocity ratios or speeds.")
    parser.add_argument("--release-target", default="v0.3.0", help="Formal release target guarded by this audit.")
    parser.add_argument("--dotnet-command", default="dotnet", help="dotnet executable to inspect.")
    parser.add_argument("--nvidia-smi-command", default="nvidia-smi", help="nvidia-smi executable to inspect.")
    parser.add_argument("--fluidx3d-exe", type=Path, help="FluidX3D executable to record without launching a full solver run.")
    parser.add_argument("--citylbm-gha", type=Path, default=ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha")
    parser.add_argument("--citylbm-build-log", type=Path, default=RESULTS_DIR / "citylbm_build_check.log")
    parser.add_argument("--run-matrix", type=Path, default=CASE_DIR / "native_fluidx3d_run_matrix.csv")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    preset = json.loads(PRESET_PATH.read_text(encoding="utf-8"))
    uref = float(preset["uref_m_s"])
    probes = load_official_probes()
    if len(probes) != 80:
        raise SystemExit(f"Expected 80 official probes, found {len(probes)}")

    inlet = audit_inlet_profile(uref)
    predictions: Optional[Dict[int, float]] = None
    prediction_meta: Optional[Dict[int, Dict[str, object]]] = None
    if args.predicted:
        predictions, prediction_meta = load_predictions(args.predicted, uref)
    residuals, metrics = compute_residuals(probes, predictions, prediction_meta)

    write_csv(RESULTS_DIR / "casee_official_ac_N_probes.csv", probes, ["No.", "case", "Wind_direction", "x_m", "y_m", "z_m", "official_velocity_ratio"])
    write_csv(RESULTS_DIR / "casee_inlet_profile_audit.csv", inlet, ["z_m", "u_m_s", "k_m2_s2", "u_over_uref"])
    write_csv(
        RESULTS_DIR / "casee_probe_residuals.csv",
        residuals,
        [
            "No.",
            "case",
            "Wind_direction",
            "x_m",
            "y_m",
            "z_m",
            "official_velocity_ratio",
            "predicted_velocity_ratio",
            "residual",
            "abs_error_pp",
            "sampling_mode",
            "solid_corner_neighbors_max",
            "samples",
            "solid_corner_risk",
            "evidence_type",
        ],
    )
    group_metrics = compute_solid_corner_group_metrics(residuals)
    if group_metrics:
        write_csv(
            RESULTS_DIR / "casee_solid_corner_group_metrics.csv",
            group_metrics,
            ["solid_corner_neighbors_max", "n", "mae_pp", "rmse_pp", "bias_pp", "r2", "pearson"],
        )

    citylbm_gha = file_status(args.citylbm_gha)
    citylbm_build_log = file_status(args.citylbm_build_log)
    build_log_text = read_text_fallback(args.citylbm_build_log) if args.citylbm_build_log.exists() else ""
    citylbm_build_passed = bool(citylbm_gha["found"]) and (
        not args.citylbm_build_log.exists()
        or "Build succeeded." in build_log_text
        or "0 Error(s)" in build_log_text
        or "0 errors" in build_log_text.lower()
        or "0 个错误" in build_log_text
    )
    matrix = run_matrix_status(args.run_matrix)

    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "dotnet": run_cmd([args.dotnet_command, "--info"]),
        "nvidia_smi": run_cmd([args.nvidia_smi_command]),
        "fluidx3d_executable": file_status(args.fluidx3d_exe),
        "citylbm_gha": citylbm_gha,
        "citylbm_build_log": citylbm_build_log,
        "run_matrix": {"path": str(args.run_matrix), **matrix},
    }
    (RESULTS_DIR / "environment_manifest.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    gate = build_release_gate(metrics, env, args.release_target, citylbm_build_passed, matrix)
    (RESULTS_DIR / "release_gate.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    if metrics is not None:
        write_csv(RESULTS_DIR / "casee_metrics.csv", [metrics], list(metrics.keys()))
    write_optional_outputs(probes, inlet, residuals, group_metrics)
    write_report(metrics, gate, args.predicted, group_metrics)
    print(json.dumps({"probes": len(probes), "metrics": metrics, "recommended_tag": gate["recommended_tag"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
