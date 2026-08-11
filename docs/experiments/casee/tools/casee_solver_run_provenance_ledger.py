#!/usr/bin/env python3
"""Build a paper-facing provenance ledger for AIJ Case E solver results.

The manuscript needs one table that answers: which command/config produced a
metric, which CSV/log supports it, whether it is a solver run or a diagnostic
audit, and what claim boundary applies. This script consolidates the existing
Case E evidence without changing any metric values.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"

OUT_JSON = RESULTS_DIR / "casee_solver_run_provenance_ledger.json"
OUT_CSV = RESULTS_DIR / "casee_solver_run_provenance_ledger.csv"
OUT_MD = RESULTS_DIR / "casee_solver_run_provenance_ledger.md"

DEFAULT_OFFICIAL_CSV = RESULTS_DIR / "casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv"

FIELDNAMES = [
    "run_id",
    "result_kind",
    "evidence_type",
    "solver_output_evidence_type",
    "claim_readiness",
    "command",
    "case_manifest_path",
    "csv_path",
    "csv_sha256",
    "run_log_path",
    "run_log_sha256",
    "log_completed",
    "manifest_protocol_ok",
    "n",
    "mae_pp",
    "rmse_pp",
    "bias_pp",
    "r2",
    "pearson",
    "height_m",
    "sampling_mode",
    "release_gate_input",
    "default_promotion_allowed",
    "paper_use",
    "limitations",
    "provenance_complete",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path | str | None) -> str:
    if path is None or str(path) == "":
        return ""
    p = Path(str(path))
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return str(path)


def file_info(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": rel(path), "sha256": "", "size_bytes": 0, "mtime_utc": ""}
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return {
        "found": True,
        "path": rel(path),
        "sha256": h.hexdigest(),
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def artifact_path(item: Dict[str, Any] | str | None) -> str:
    if not item:
        return ""
    if isinstance(item, str):
        return item
    return str(item.get("path") or "")


def artifact_sha(item: Dict[str, Any] | str | None) -> str:
    if not item:
        return ""
    if isinstance(item, str):
        path = ROOT / item if not Path(item).is_absolute() else Path(item)
        return str(file_info(path).get("sha256") or "")
    return str(item.get("sha256") or "")


def metric_value(metrics: Dict[str, Any], key: str) -> Any:
    value = metrics.get(key)
    return "" if value is None else value


def make_row(
    *,
    run_id: str,
    result_kind: str,
    evidence_type: str,
    solver_output_evidence_type: str,
    claim_readiness: str,
    command: str,
    metrics: Dict[str, Any],
    csv_artifact: Dict[str, Any] | None = None,
    run_log: Dict[str, Any] | None = None,
    case_manifest: Dict[str, Any] | None = None,
    log_completed: bool | str = "",
    manifest_protocol_ok: bool | str = "",
    release_gate_input: bool = False,
    default_promotion_allowed: bool = False,
    paper_use: str,
    limitations: str,
) -> Dict[str, Any]:
    csv_path = artifact_path(csv_artifact)
    run_log_path = artifact_path(run_log)
    manifest_path = artifact_path(case_manifest)
    metric_complete = all(key in metrics for key in ["n", "mae_pp", "rmse_pp", "bias_pp", "r2", "pearson"])
    provenance_complete = bool(metric_complete and csv_path)
    if result_kind == "solver_run":
        provenance_complete = provenance_complete and bool(run_log_path) and bool(log_completed)
    return {
        "run_id": run_id,
        "result_kind": result_kind,
        "evidence_type": evidence_type,
        "solver_output_evidence_type": solver_output_evidence_type,
        "claim_readiness": claim_readiness,
        "command": command,
        "case_manifest_path": manifest_path,
        "csv_path": csv_path,
        "csv_sha256": artifact_sha(csv_artifact),
        "run_log_path": run_log_path,
        "run_log_sha256": artifact_sha(run_log),
        "log_completed": log_completed,
        "manifest_protocol_ok": manifest_protocol_ok,
        "n": metric_value(metrics, "n"),
        "mae_pp": metric_value(metrics, "mae_pp"),
        "rmse_pp": metric_value(metrics, "rmse_pp"),
        "bias_pp": metric_value(metrics, "bias_pp"),
        "r2": metric_value(metrics, "r2"),
        "pearson": metric_value(metrics, "pearson"),
        "height_m": metric_value(metrics, "height_m"),
        "sampling_mode": metric_value(metrics, "sampling_mode"),
        "release_gate_input": release_gate_input,
        "default_promotion_allowed": default_promotion_allowed,
        "paper_use": paper_use,
        "limitations": limitations,
        "provenance_complete": provenance_complete,
    }


def candidate_command_map() -> Dict[str, str]:
    plan = read_json(RESULTS_DIR / "casee_candidate_sweep_plan.json")
    return {str(row.get("candidate_id")): str(row.get("command", "")) for row in plan.get("candidates", [])}


def build_rows() -> List[Dict[str, Any]]:
    commands = candidate_command_map()
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    zcenter = read_json(RESULTS_DIR / "casee_zcenter_rerun_consistency.json")
    c002 = read_json(RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    c003 = read_json(RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    c004 = read_json(RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    c005 = read_json(RESULTS_DIR / "casee_c005_decomposition_audit.json")
    c008 = read_json(RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json")
    c014 = read_json(RESULTS_DIR / "casee_c014_residual_structure_audit.json")
    c016 = read_json(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json")

    rows: List[Dict[str, Any]] = []
    official_csv = file_info(DEFAULT_OFFICIAL_CSV)
    rows.append(
        make_row(
            run_id="release_gate_current_official_z2m",
            result_kind="metric_recompute",
            evidence_type="newly_run",
            solver_output_evidence_type="preexisting_artifact",
            claim_readiness="limitations_ready_negative_validation",
            command=(
                "python docs/experiments/casee/tools/casee_audit.py "
                "--predicted docs/experiments/casee/results/casee_native_dx2_zcenter_gshift1_nu001_pmodes_probe_time_mean.csv "
                "--release-target v0.4.0"
            ),
            metrics=release_gate.get("metrics") or {},
            csv_artifact=official_csv,
            release_gate_input=True,
            paper_use="Use as the current official z=2 m negative validation metric.",
            limitations="Metric is recomputed from an existing solver CSV; formal release remains blocked.",
        )
    )

    rows.append(
        make_row(
            run_id="C001_dx2_zcenter_replicate_best_known",
            result_kind="solver_run",
            evidence_type=str(zcenter.get("evidence_type", "missing")),
            solver_output_evidence_type=str(zcenter.get("evidence_type", "missing")),
            claim_readiness=str(zcenter.get("claim_readiness", "blocked")),
            command=commands.get("C001_dx2_zcenter_replicate_best_known", "cd E:/citylbm_buildchain/FluidX3D && ./bin/FluidX3D.exe"),
            metrics=zcenter.get("rerun_metrics") or {},
            csv_artifact=zcenter.get("rerun_csv") or {},
            run_log=zcenter.get("rerun_log") or {},
            log_completed=zcenter.get("log_completed_48000", ""),
            manifest_protocol_ok="not_recorded",
            release_gate_input=False,
            paper_use="Use as reproducibility evidence for the negative z-center metric.",
            limitations="Reproduces failure; not an accuracy improvement.",
        )
    )

    for audit, command_id in [
        (c002, "C002_dx2_longer_mean_stability"),
        (c003, "C003_dx2_no_zcenter_ablation"),
        (c004, "C004_dx3_low_cost_direction_check"),
        (c005, "C005_dx2_domain_decomposition_ablation"),
    ]:
        candidate_id = str(audit.get("candidate_id") or command_id)
        rows.append(
            make_row(
                run_id=candidate_id,
                result_kind="solver_run",
                evidence_type=str(audit.get("evidence_type", "missing")),
                solver_output_evidence_type=str(audit.get("evidence_type", "missing")),
                claim_readiness=str(audit.get("claim_readiness", "blocked")),
                command=commands.get(command_id, ""),
                metrics=audit.get("candidate_metrics") or {},
                csv_artifact=audit.get("candidate_csv") or {},
                run_log=audit.get("run_log") or {},
                case_manifest=audit.get("case_manifest") or {},
                log_completed=audit.get("log_completed_96000", audit.get("log_completed_48000", "")),
                manifest_protocol_ok=audit.get("manifest_protocol_ok", "not_recorded"),
                release_gate_input=False,
                paper_use="Use as a completed diagnostic/ablation candidate with official z=2 m raw_trilinear metrics.",
                limitations="Diagnostic candidate only; default promotion and formal accuracy claims are blocked.",
            )
        )

    for candidate in c008.get("candidates", []):
        cid = str(candidate.get("candidate_id", "unknown_inlet_candidate"))
        rows.append(
            make_row(
                run_id=cid,
                result_kind="solver_run",
                evidence_type=str(c008.get("evidence_type", "missing")),
                solver_output_evidence_type=str(c008.get("evidence_type", "missing")),
                claim_readiness=str(c008.get("claim_readiness", "blocked")),
                command=commands.get("C008_C015_full_plane_inlet_turbulence_sgs_sweep", ""),
                metrics=candidate.get("candidate_metrics") or {},
                csv_artifact=candidate.get("csv") or {},
                run_log=candidate.get("run_log") or {},
                case_manifest=candidate.get("case_manifest") or {},
                log_completed=candidate.get("log_completed_48000", ""),
                manifest_protocol_ok=candidate.get("manifest_protocol_ok", ""),
                release_gate_input=False,
                paper_use="Use as AF-k full-plane inlet/SGS diagnostic sweep evidence.",
                limitations="R2 remains negative; inlet/no-SGS settings are diagnostic-only and not LES improvement evidence.",
            )
        )

    c014_source_csv = c014.get("source_csv") or {}
    rows.append(
        make_row(
            run_id="C014_residual_structure_audit",
            result_kind="diagnostic_audit",
            evidence_type=str(c014.get("evidence_type", "missing")),
            solver_output_evidence_type=str(c014.get("solver_output_evidence_type", "preexisting_artifact")),
            claim_readiness=str(c014.get("claim_readiness", "blocked")),
            command="python docs/experiments/casee/tools/casee_c014_residual_structure_audit.py",
            metrics=c014.get("c014_metrics") or {},
            csv_artifact=c014_source_csv,
            log_completed="not_a_solver_run",
            manifest_protocol_ok="not_a_solver_run",
            release_gate_input=False,
            paper_use="Use as residual-structure limitations and C016 design evidence.",
            limitations="Audit over an existing C014 solver CSV; post-hoc affine calibration is not validation.",
        )
    )

    rows.append(
        make_row(
            run_id="C016_residual_target_leakage_guard",
            result_kind="protocol_guard",
            evidence_type=str(c016.get("evidence_type", "missing")),
            solver_output_evidence_type="not_a_solver_run",
            claim_readiness=str(c016.get("claim_readiness", "blocked")),
            command="python docs/experiments/casee/tools/casee_c016_residual_target_leakage_guard.py",
            metrics={},
            log_completed="not_a_solver_run",
            manifest_protocol_ok="not_a_solver_run",
            release_gate_input=False,
            paper_use="Use as protocol-risk control against residual calibration leakage.",
            limitations="No CFD metric is produced; it is a guard for future C016 follow-up design.",
        )
    )

    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Solver Run Provenance Ledger",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Ledger passed: {payload['ledger_passed']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Solver run rows: {payload['solver_run_count']}",
        f"- Diagnostic/protocol rows: {payload['non_solver_count']}",
        "",
        "## Rows",
        "",
        "| run | kind | evidence | MAE pp | R2 | Pearson | csv | log | claim |",
        "|---|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['run_id']}` | {row['result_kind']} | {row['evidence_type']} / {row['solver_output_evidence_type']} | "
            f"{row['mae_pp']} | {row['r2']} | {row['pearson']} | `{row['csv_path']}` | `{row['run_log_path']}` | {row['claim_readiness']} |"
        )
    lines += [
        "",
        "## Protocol Risks",
        "",
        "- Official validation remains z = 2 m, 80 probes, raw_trilinear sampling.",
        "- Rows without solver logs are diagnostic/protocol artifacts, not CFD runs.",
        "- C014 residual and C016 guard rows cannot be used as formal accuracy metrics.",
        "- Formal v0.4.0 remains blocked until release_gate.json passes.",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    solver_rows = [row for row in rows if row["result_kind"] == "solver_run"]
    release_rows = [row for row in rows if row["release_gate_input"] is True]
    completed_solver_rows = [row for row in solver_rows if row["provenance_complete"] is True]
    no_forbidden_default = not any(row["default_promotion_allowed"] for row in rows if row["result_kind"] != "metric_recompute")
    passed = (
        len(rows) >= 15
        and len(solver_rows) >= 13
        and len(completed_solver_rows) >= 13
        and len(release_rows) == 1
        and no_forbidden_default
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ledger_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_provenance_ledger" if passed else "blocked_provenance_ledger",
        "formal_accuracy_claim_supported": False,
        "row_count": len(rows),
        "solver_run_count": len(solver_rows),
        "non_solver_count": len(rows) - len(solver_rows),
        "completed_solver_run_count": len(completed_solver_rows),
        "release_gate_input_count": len(release_rows),
        "no_default_promotion": no_forbidden_default,
        "rows": rows,
        "boundary": (
            "This ledger consolidates provenance for existing Case E metrics. It does not create new CFD output, "
            "does not alter metrics, and does not support formal v0.4.0 while the official release gate is blocked."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"ledger_passed": passed, "out_json": rel(OUT_JSON), "row_count": len(rows)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
