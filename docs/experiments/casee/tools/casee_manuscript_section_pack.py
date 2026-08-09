#!/usr/bin/env python3
"""Generate a claim-safe manuscript section pack for AIJ Case E."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PAPER_DIR = ROOT / "academic-paper-writer" / "paper-drafts"

RESULTS_TABLE = RESULTS_DIR / "casee_manuscript_results_table.csv"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
OUT_MD = PAPER_DIR / "casee_v04_manuscript_section_pack_en.md"
OUT_JSON = RESULTS_DIR / "casee_manuscript_section_pack.json"
OUT_QA_MD = RESULTS_DIR / "casee_manuscript_section_pack_qa.md"

FORBIDDEN_UNQUALIFIED = [
    "CityLBM v0.4.0 has passed",
    "validated predictive accuracy",
    "research-grade predictive accuracy",
    "mesh independence",
    "LES improvement",
    "diagnostic mode is the official result",
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


def row_by_id(rows: List[Dict[str, str]], row_id: str) -> Dict[str, str]:
    for row in rows:
        if row.get("row_id") == row_id:
            return row
    return {}


def source_note(*paths: str) -> str:
    joined = "; ".join(f"`{path}`" for path in paths if path)
    return f"(newly_run; source: {joined})"


def build_markdown(rows: List[Dict[str, str]], release_gate: Dict[str, Any]) -> str:
    formal = row_by_id(rows, "formal_official_z2m")
    diagnostic = row_by_id(rows, "best_diagnostic_sampling")
    risk = row_by_id(rows, "near_wall_risk_gradient")
    trace = row_by_id(rows, "software_traceability_status")
    boundary = row_by_id(rows, "release_boundary_status")

    metrics = release_gate.get("metrics") or {}
    generated_at = datetime.now(timezone.utc).isoformat()
    formal_source = source_note("docs/experiments/casee/results/release_gate.json")
    diagnostic_source = source_note(diagnostic.get("source_paths", ""))
    risk_source = source_note(risk.get("source_paths", ""))
    trace_source = source_note(trace.get("source_paths", ""))
    boundary_source = source_note("docs/experiments/casee/results/release_gate.json")

    lines = [
        "# AIJ Case E Manuscript Section Pack",
        "",
        f"Generated: {generated_at}",
        "evidence_type: newly_run",
        "claim_readiness: paper_ready_negative_validation_and_limitations",
        "",
        "## Methods Paragraph",
        "",
        (
            "AIJ Case E was evaluated under the official `ac+N` condition with wind direction `N` "
            "and the CityLBM convention `wind vector = (0, -1, 0)`. The formal benchmark protocol "
            "uses `BD_caseE.stl`, scale factor 250, Uref = 3.928296 m/s, zref = 15.9 m, the official "
            "pedestrian height z = 2 m, and the 80 probes selected from `RS_caseE.csv` where "
            "`case=ac` and `Wind_direction=N`. The formal sampling mode is `raw_trilinear`; "
            "`z_plus_half`, `vertical_valid_above`, non-raw interpolation modes, and z-origin offsets "
            f"are retained only as diagnostic controls. {formal_source}"
        ),
        "",
        "## Results Paragraph",
        "",
        (
            "Under this official z = 2 m protocol, the current CityLBM release-candidate result is "
            f"MAE = {formal.get('mae_pp')} percentage points, RMSE = {formal.get('rmse_pp')} percentage points, "
            f"bias = {formal.get('bias_pp')} percentage points, R2 = {formal.get('r2')}, and "
            f"Pearson = {formal.get('pearson')} across n = {formal.get('n')} probes. "
            "Because the formal R2 remains negative, the result is a negative validation outcome and "
            f"does not support a formal benchmark-accuracy claim. {formal_source}"
        ),
        "",
        "## Diagnostic Paragraph",
        "",
        (
            "Diagnostic sampling identifies protocol sensitivity without replacing the formal metric. "
            f"The best diagnostic row reports MAE = {diagnostic.get('mae_pp')} percentage points, "
            f"R2 = {diagnostic.get('r2')}, and Pearson = {diagnostic.get('pearson')} for "
            f"n = {diagnostic.get('n')} probes. This row is useful for explaining near-wall sampling "
            f"and solid-corner effects, but it is not the official z = 2 m result. {diagnostic_source}"
        ),
        "",
        "## Limitations Paragraph",
        "",
        (
            "The remaining error is concentrated in near-wall and solid-corner probe-risk groups. "
            f"The z-center audit reports {risk.get('mae_pp')} percentage points for the low- and high-risk "
            f"groups, with {risk.get('n')} probes in those groups. This supports a limitation focused on "
            "wall treatment, voxelized boundaries, and probe-protocol sensitivity rather than a claim of "
            f"validated accuracy. {risk_source}"
        ),
        "",
        "## Software Implications Paragraph",
        "",
        (
            "The software changes should be described as traceability and misuse-prevention improvements. "
            "CityLBM now exposes the run manifest path, records the formal accuracy-gate contract, and "
            "shows a Grasshopper `Claim Gate` output so workflow completion is not confused with benchmark "
            f"accuracy. These additions do not change the official Case E metric. {trace_source}"
        ),
        "",
        "## Release Boundary Paragraph",
        "",
        (
            f"The formal release gate remains closed: `formal_release_allowed={release_gate.get('formal_release_allowed')}`, "
            f"with recommended tag `{release_gate.get('recommended_tag')}`. A formal `v0.4.0` release requires "
            "official z = 2 m R2 to become positive, Pearson to remain positive, MAE to improve clearly below "
            "the present near-21 percentage-point level, Case A smoke regression to remain intact, Rhino/Grasshopper "
            f"to load the new GHA, and metrics to trace to command, log, CSV, figure, and report artifacts. {boundary_source}"
        ),
        "",
        "## Manuscript Sentence Bank",
        "",
        f"- {formal.get('paper_sentence')} {formal_source}",
        f"- {diagnostic.get('paper_sentence')} {diagnostic_source}",
        f"- {risk.get('paper_sentence')} {risk_source}",
        f"- {trace.get('paper_sentence')} {trace_source}",
        f"- {boundary.get('paper_sentence')} {boundary_source}",
        "",
        "## Forbidden Wording",
        "",
        "- Do not state that CityLBM has passed AIJ Case E benchmark-accuracy validation.",
        "- Do not state that diagnostic sampling is the official z = 2 m result.",
        "- Do not state that the current evidence proves mesh independence or LES improvement.",
        "- Do not state that the current manifest or Claim Gate output proves CFD accuracy.",
    ]
    return "\n".join(lines) + "\n"


def scan_text(text: str) -> List[str]:
    violations: List[str] = []
    for pattern in FORBIDDEN_UNQUALIFIED:
        lower = pattern.lower()
        for line in text.splitlines():
            candidate = line.lower()
            if lower not in candidate:
                continue
            if "do not " in candidate or "does not " in candidate or "not " in candidate:
                continue
            violations.append(pattern)
    return sorted(set(violations))


def build_payload(text: str, rows: List[Dict[str, str]], release_gate: Dict[str, Any]) -> Dict[str, Any]:
    required_rows = {
        "formal_official_z2m",
        "best_diagnostic_sampling",
        "near_wall_risk_gradient",
        "software_traceability_status",
        "release_boundary_status",
    }
    present_rows = {row.get("row_id", "") for row in rows}
    metrics = release_gate.get("metrics") or {}
    violations = scan_text(text)
    checks = {
        "results_table_exists": RESULTS_TABLE.exists(),
        "release_gate_exists": RELEASE_GATE.exists(),
        "required_rows_present": required_rows.issubset(present_rows),
        "formal_release_blocked": release_gate.get("formal_release_allowed") is False,
        "formal_r2_negative": float(metrics.get("r2", 0.0)) < 0.0,
        "evidence_notes_present": text.count("(newly_run; source:") >= 6,
        "forbidden_success_wording_absent": not violations,
        "diagnostic_marked_nonformal": "not the official z = 2 m result" in text,
        "claim_gate_marked_not_accuracy": "do not change the official Case E metric" in text,
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "section_pack_passed": all(checks.values()),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_negative_validation_and_limitations",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "recommended_tag": release_gate.get("recommended_tag"),
        "official_z2m_metrics": metrics,
        "output_markdown": str(OUT_MD.relative_to(ROOT).as_posix()),
        "checks": checks,
        "forbidden_success_wording_violations": violations,
        "source_artifacts": [
            "docs/experiments/casee/results/casee_manuscript_results_table.csv",
            "docs/experiments/casee/results/release_gate.json",
            "docs/experiments/casee/results/citylbm_manifest_output_gate.json",
            "docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv",
            "docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv",
        ],
        "boundary": (
            "This section pack is suitable for negative-validation and limitations prose only. "
            "It does not support a formal predictive-accuracy claim."
        ),
    }


def write_qa_markdown(payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Manuscript Section Pack QA",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Section pack passed: {payload['section_pack_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        f"- Recommended tag: `{payload['recommended_tag']}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += ["", "## Boundary", "", payload["boundary"]]
    OUT_QA_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = read_csv(RESULTS_TABLE)
    release_gate = read_json(RELEASE_GATE)
    text = build_markdown(rows, release_gate)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(text, encoding="utf-8")
    payload = build_payload(text, rows, release_gate)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_qa_markdown(payload)
    print(json.dumps({"section_pack_passed": payload["section_pack_passed"], "out_md": str(OUT_MD.relative_to(ROOT).as_posix())}, indent=2))
    return 0 if payload["section_pack_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
