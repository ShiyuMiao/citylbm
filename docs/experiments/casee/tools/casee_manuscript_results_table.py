#!/usr/bin/env python3
"""Create manuscript-facing Case E result rows with explicit claim boundaries."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_manuscript_results_table.json"
OUT_CSV = RESULTS_DIR / "casee_manuscript_results_table.csv"
OUT_MD = RESULTS_DIR / "casee_manuscript_results_table.md"

FIELDNAMES = [
    "row_id",
    "section",
    "result_role",
    "claim_boundary",
    "evidence_type",
    "source_paths",
    "n",
    "mae_pp",
    "rmse_pp",
    "bias_pp",
    "r2",
    "pearson",
    "paper_sentence",
    "limitations_sentence",
    "forbidden_claim",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def fmt(value: Any, digits: int = 3) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.{digits}f}"


def fmt_any(value: Any, digits: int = 3) -> str:
    if value in (None, ""):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def find_row(rows: Iterable[Dict[str, str]], key: str, value: str) -> Dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def result_row(
    *,
    row_id: str,
    section: str,
    result_role: str,
    claim_boundary: str,
    evidence_type: str,
    source_paths: Iterable[Path],
    n: Any = "",
    mae_pp: Any = "",
    rmse_pp: Any = "",
    bias_pp: Any = "",
    r2: Any = "",
    pearson: Any = "",
    paper_sentence: str,
    limitations_sentence: str,
    forbidden_claim: str,
) -> Dict[str, str]:
    return {
        "row_id": row_id,
        "section": section,
        "result_role": result_role,
        "claim_boundary": claim_boundary,
        "evidence_type": evidence_type,
        "source_paths": "; ".join(rel(path) for path in source_paths),
        "n": str(n),
        "mae_pp": fmt_any(mae_pp),
        "rmse_pp": fmt_any(rmse_pp),
        "bias_pp": fmt_any(bias_pp),
        "r2": fmt_any(r2, 6),
        "pearson": fmt_any(pearson, 6),
        "paper_sentence": paper_sentence,
        "limitations_sentence": limitations_sentence,
        "forbidden_claim": forbidden_claim,
    }


def build_rows() -> List[Dict[str, str]]:
    release_gate_path = RESULTS_DIR / "release_gate.json"
    zcenter_modes_path = RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv"
    probe_modes_path = RESULTS_DIR / "casee_probe_mode_metrics.csv"
    zcenter_voxel_path = RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv"
    voxel_path = RESULTS_DIR / "casee_voxel_probe_audit_groups.csv"
    manifest_gate_path = RESULTS_DIR / "citylbm_manifest_output_gate.json"
    paper_packet_path = RESULTS_DIR / "citylbm_paper_results_packet.json"

    release_gate = read_json(release_gate_path)
    metrics = release_gate.get("metrics") or {}
    zcenter_modes = read_csv(zcenter_modes_path)
    probe_modes = read_csv(probe_modes_path)
    zcenter_voxel = read_csv(zcenter_voxel_path)
    voxel = read_csv(voxel_path)
    manifest_gate = read_json(manifest_gate_path)
    paper_packet = read_json(paper_packet_path)

    zcenter_best = min(
        [row for row in zcenter_modes if row.get("claim_boundary") == "diagnostic"],
        key=lambda row: float(row["mae_pp"]),
        default={},
    )
    prior_best = min(
        [row for row in probe_modes if row.get("claim_boundary") == "diagnostic"],
        key=lambda row: float(row["mae_pp"]),
        default={},
    )
    low = find_row(zcenter_voxel, "group", "low")
    high = find_row(zcenter_voxel, "group", "high")
    prior_high = find_row(voxel, "group", "high")

    rows = [
        result_row(
            row_id="formal_official_z2m",
            section="Results / Benchmark validation",
            result_role="formal_gate_input",
            claim_boundary="limitations_ready_negative_validation",
            evidence_type="newly_run",
            source_paths=[release_gate_path, RESULTS_DIR / "casee_metrics.csv", RESULTS_DIR / "casee_validation_report.md"],
            n=metrics.get("n", ""),
            mae_pp=metrics.get("mae_pp", ""),
            rmse_pp=metrics.get("rmse_pp", ""),
            bias_pp=metrics.get("bias_pp", ""),
            r2=metrics.get("r2", ""),
            pearson=metrics.get("pearson", ""),
            paper_sentence=(
                "Under the official AIJ Case E z=2 m protocol, the current CityLBM rc result remains a negative validation "
                f"(MAE {fmt(metrics.get('mae_pp'))} pp, R2 {fmt(metrics.get('r2'), 6)}, Pearson {fmt(metrics.get('pearson'), 6)})."
            ),
            limitations_sentence="This row must be reported as benchmark failure/limitation evidence, not as predictive-accuracy validation.",
            forbidden_claim="CityLBM passes AIJ Case E official z=2 m accuracy validation.",
        ),
        result_row(
            row_id="best_diagnostic_sampling",
            section="Discussion / Probe protocol sensitivity",
            result_role="diagnostic_only",
            claim_boundary="limitations_ready_diagnostic",
            evidence_type="newly_run",
            source_paths=[zcenter_modes_path],
            n=zcenter_best.get("n", ""),
            mae_pp=zcenter_best.get("mae_pp", ""),
            rmse_pp=zcenter_best.get("rmse_pp", ""),
            bias_pp=zcenter_best.get("bias_pp", ""),
            r2=zcenter_best.get("r2", ""),
            pearson=zcenter_best.get("pearson", ""),
            paper_sentence=(
                f"The best diagnostic sampling row is `{zcenter_best.get('sampling_mode', '')}`, with MAE "
                f"{fmt(zcenter_best.get('mae_pp'))} pp and Pearson {fmt(zcenter_best.get('pearson'), 6)}."
            ),
            limitations_sentence="Diagnostic sampling may explain near-wall sensitivity but cannot replace the formal raw_trilinear official z=2 m result.",
            forbidden_claim="vertical_valid_above, z_plus_half, or another diagnostic mode is the official validation result.",
        ),
        result_row(
            row_id="diagnostic_improvement_direction",
            section="Discussion / Solver-feedback direction",
            result_role="diagnostic_only",
            claim_boundary="limitations_ready_diagnostic",
            evidence_type="newly_run",
            source_paths=[probe_modes_path, zcenter_modes_path],
            n=prior_best.get("n", ""),
            mae_pp=prior_best.get("mae_pp", ""),
            rmse_pp=prior_best.get("rmse_pp", ""),
            bias_pp=prior_best.get("bias_pp", ""),
            r2=prior_best.get("r2", ""),
            pearson=prior_best.get("pearson", ""),
            paper_sentence=(
                f"Compared with the earlier diagnostic best MAE {fmt(prior_best.get('mae_pp'))} pp, z-center diagnostics reduce "
                f"the diagnostic lower bound to {fmt(zcenter_best.get('mae_pp'))} pp."
            ),
            limitations_sentence="The directional improvement is not a mesh-independence result and all diagnostic R2 values remain negative.",
            forbidden_claim="The diagnostic improvement proves LES improvement or mesh independence.",
        ),
        result_row(
            row_id="near_wall_risk_gradient",
            section="Limitations / Near-wall and solid-corner probes",
            result_role="risk_stratification",
            claim_boundary="limitations_ready_diagnostic",
            evidence_type="newly_run",
            source_paths=[zcenter_voxel_path, voxel_path],
            n=f"low={low.get('n', '')}; high={high.get('n', '')}",
            mae_pp=f"low={fmt(low.get('raw_mae_pp'))}; high={fmt(high.get('raw_mae_pp'))}",
            paper_sentence=(
                f"In the z-center audit, low-risk probes have raw MAE {fmt(low.get('raw_mae_pp'))} pp, whereas "
                f"high-risk probes have raw MAE {fmt(high.get('raw_mae_pp'))} pp."
            ),
            limitations_sentence=(
                f"The earlier high-risk group raw MAE was {fmt(prior_high.get('raw_mae_pp'))} pp; these rows support near-wall/probe-risk limitations only."
            ),
            forbidden_claim="The probe-risk gradient is independent field validation.",
        ),
        result_row(
            row_id="software_traceability_status",
            section="Methods / Reproducibility",
            result_role="software_traceability",
            claim_boundary="paper_ready_manifest_traceability",
            evidence_type=str(manifest_gate.get("evidence_type", "newly_run")),
            source_paths=[manifest_gate_path, ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"],
            n=len(manifest_gate.get("checks", [])),
            paper_sentence="CityLBM exposes and audits the run manifest path so protocol and claim-boundary metadata are traceable from the Grasshopper workflow.",
            limitations_sentence="Manifest traceability does not prove Rhino loaded the new GHA and does not improve CFD accuracy.",
            forbidden_claim="A manifest path output proves benchmark accuracy.",
        ),
        result_row(
            row_id="release_boundary_status",
            section="Release boundary",
            result_role="formal_release_gate",
            claim_boundary="blocked_formal_release_gate",
            evidence_type="newly_run",
            source_paths=[release_gate_path, paper_packet_path],
            paper_sentence=(
                f"The formal release gate remains closed (`formal_release_allowed={release_gate.get('formal_release_allowed')}`), "
                f"and the recommended tag is `{release_gate.get('recommended_tag')}`."
            ),
            limitations_sentence="Formal v0.4.0 must not be created until official z=2 m metrics and load/runtime gates pass.",
            forbidden_claim="The current rc is a formal v0.4.0 accuracy release.",
        ),
    ]
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    ids = {row["row_id"] for row in rows}
    diagnostic_safe = all(
        row["claim_boundary"] != "formal_gate_input"
        for row in rows
        if row["result_role"] == "diagnostic_only"
    )
    formal = next((row for row in rows if row["row_id"] == "formal_official_z2m"), {})
    passed = (
        {"formal_official_z2m", "best_diagnostic_sampling", "near_wall_risk_gradient", "release_boundary_status"}.issubset(ids)
        and diagnostic_safe
        and formal.get("r2", "") != ""
        and float(formal["r2"]) < 0.0
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manuscript_results_table_passed": passed,
        "row_count": len(rows),
        "formal_accuracy_claim_supported": False,
        "formal_v0_4_0_allowed": False,
        "claim_readiness": "paper_ready_manuscript_results_table",
        "boundary": (
            "This table converts existing Case E metrics into manuscript rows. It preserves the formal official z=2 m "
            "negative-validation result and keeps all diagnostic sampling rows in limitations."
        ),
    }


def write_markdown(path: Path, rows: List[Dict[str, str]], summary: Dict[str, Any]) -> None:
    lines = [
        "# Case E Manuscript Results Table",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Table passed: {summary['manuscript_results_table_passed']}",
        f"- Row count: {summary['row_count']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {summary['formal_v0_4_0_allowed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        "",
        "## Rows",
        "",
        "| row | boundary | n | MAE pp | R2 | Pearson | paper sentence |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['row_id']}` | {row['claim_boundary']} | {row['n']} | {row['mae_pp']} | "
            f"{row['r2']} | {row['pearson']} | {row['paper_sentence']} |"
        )
    lines += [
        "",
        "## Limitations And Forbidden Claims",
        "",
        "| row | limitations sentence | forbidden claim |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['row_id']}` | {row['limitations_sentence']} | {row['forbidden_claim']} |")
    lines += ["", "## Boundary", "", summary["boundary"]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = summarize(rows)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": sorted({path for row in rows for path in row["source_paths"].split("; ") if path}),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"manuscript_results_table_passed": summary["manuscript_results_table_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["manuscript_results_table_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
