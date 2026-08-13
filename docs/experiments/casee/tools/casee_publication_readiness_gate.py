#!/usr/bin/env python3
"""Audit Case E publication readiness without allowing formal accuracy claims."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
PAPER_DRAFTS = ROOT / "academic-paper-writer" / "paper-drafts"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"

OUT_JSON = RESULTS_DIR / "casee_publication_readiness_gate.json"
OUT_CSV = RESULTS_DIR / "casee_publication_readiness_gate.csv"
OUT_MD = RESULTS_DIR / "casee_publication_readiness_gate.md"

FIELDNAMES = [
    "item_id",
    "reviewer_question",
    "status",
    "evidence_type",
    "source_paths",
    "paper_location",
    "allowed_statement",
    "must_not_claim",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def exists_all(paths: Iterable[Path]) -> bool:
    return all(path.exists() for path in paths)


def row(
    *,
    item_id: str,
    reviewer_question: str,
    status: str,
    evidence_type: str,
    source_paths: Iterable[Path],
    paper_location: str,
    allowed_statement: str,
    must_not_claim: str,
) -> Dict[str, Any]:
    paths = list(source_paths)
    return {
        "item_id": item_id,
        "reviewer_question": reviewer_question,
        "status": status,
        "evidence_type": evidence_type,
        "source_paths": "; ".join(rel(path) for path in paths),
        "source_paths_exist": exists_all(paths),
        "paper_location": paper_location,
        "allowed_statement": allowed_statement,
        "must_not_claim": must_not_claim,
    }


def build_rows() -> List[Dict[str, Any]]:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    paper_gate = read_json(RESULTS_DIR / "casee_paper_evidence_gate.json")
    claim_gate = read_json(RESULTS_DIR / "casee_claim_support_gate.json")
    figure_gate = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    appendix = read_json(RESULTS_DIR / "casee_paper_appendix_manifest.json")
    artifact_index = read_json(RESULTS_DIR / "casee_artifact_index.json")
    release_assets = read_json(RESULTS_DIR / "casee_release_asset_manifest.json")
    vs_cpp_recovery = read_json(RESULTS_DIR / "vs_cpp_recovery_gate.json")
    gha_install = read_json(RESULTS_DIR / "citylbm_gha_install_audit.json")

    metrics = release_gate.get("metrics") or {}
    claim_summary = claim_gate.get("summary") or {}
    artifact_summary = artifact_index.get("summary") or {}
    release_asset_summary = release_assets.get("summary") or {}
    release_note = ROOT / "docs" / "releases" / f"{release_gate.get('recommended_tag', 'v0.4.0-rc')}.md"

    return [
        row(
            item_id="PR001",
            reviewer_question="Is the official AIJ Case E validation protocol explicit and reproducible?",
            status="paper_ready_protocol",
            evidence_type="newly_run",
            source_paths=[
                CASE_DIR / "casee_protocol.md",
                RESULTS_DIR / "casee_manuscript_claim_matrix.csv",
                RESULTS_DIR / "casee_claim_support_gate.json",
            ],
            paper_location="Methods / Validation protocol",
            allowed_statement="Case E is evaluated under the official ac+N, z=2 m, 80-probe, raw_trilinear protocol.",
            must_not_claim="Do not infer accuracy success from protocol setup alone.",
        ),
        row(
            item_id="PR002",
            reviewer_question="What is the formal official z=2 m result?",
            status="limitations_ready_negative_validation",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "release_gate.json",
                RESULTS_DIR / "casee_metrics.csv",
                RESULTS_DIR / "casee_validation_report.md",
            ],
            paper_location="Results / Validation",
            allowed_statement=(
                f"The formal official z=2 m result remains negative: MAE={metrics.get('mae_pp')} pp, "
                f"R2={metrics.get('r2')}, Pearson={metrics.get('pearson')}."
            ),
            must_not_claim="Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness.",
        ),
        row(
            item_id="PR003",
            reviewer_question="Are diagnostic improvements separated from formal validation?",
            status="paper_ready_claim_boundary",
            evidence_type=str(claim_summary.get("evidence_type", "missing")),
            source_paths=[
                RESULTS_DIR / "casee_claim_support_gate.json",
                RESULTS_DIR / "casee_claim_support_gate.csv",
                RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json",
                RESULTS_DIR / "casee_c014_residual_structure_audit.json",
            ],
            paper_location="Results / Diagnostics and Discussion",
            allowed_statement="C014 is the strongest diagnostic candidate, but it remains limitations-only because formal R2 is negative.",
            must_not_claim="Do not report diagnostic sampling, inlet tuning, no-SGS, affine calibration, or residual subsets as official validation.",
        ),
        row(
            item_id="PR004",
            reviewer_question="Can a reviewer trace every reported metric to commands, logs, and CSV files?",
            status="paper_ready_provenance",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "casee_solver_run_provenance_ledger.json",
                RESULTS_DIR / "casee_solver_run_provenance_ledger.csv",
                RESULTS_DIR / "casee_artifact_index.json",
            ],
            paper_location="Reproducibility appendix",
            allowed_statement="The solver-run ledger maps Case E metrics to run commands/configs, logs, CSV outputs, hashes, and claim boundaries.",
            must_not_claim="Do not use provenance completeness as evidence of accuracy success.",
        ),
        row(
            item_id="PR005",
            reviewer_question="Are paper figures source-backed and claim-safe?",
            status="paper_ready_figure",
            evidence_type=str(figure_gate.get("evidence_type", "missing")),
            source_paths=[
                RESULTS_DIR / "casee_paper_results_figure_qa.json",
                RESULTS_DIR / "casee_paper_results_figure_source.csv",
                RESULTS_DIR / "casee_paper_results_figure.svg",
                RESULTS_DIR / "casee_paper_results_figure.png",
            ],
            paper_location="Figure / Results",
            allowed_statement="The figure can show negative validation and limitations-only diagnostic improvements.",
            must_not_claim="Do not visually imply that diagnostic bars are formal accuracy validation.",
        ),
        row(
            item_id="PR006",
            reviewer_question="Is the reproducibility appendix generated from current evidence?",
            status="paper_ready_appendix",
            evidence_type=str(appendix.get("evidence_type", "missing")),
            source_paths=[
                RESULTS_DIR / "casee_paper_appendix_manifest.json",
                PAPER_DRAFTS / "casee_v04_reproducibility_appendix_en.md",
                PAPER_DRAFTS / "casee_v04_reproducibility_appendix_zh.md",
            ],
            paper_location="Supplementary / Reproducibility appendix",
            allowed_statement="The appendix can document commands, artifacts, release boundary, and environment limitations.",
            must_not_claim="Do not describe the appendix as resolving the official accuracy failure.",
        ),
        row(
            item_id="PR007",
            reviewer_question="Has the software feedback been constrained to validated defaults, diagnostic switches, and manifest-level publication dependencies?",
            status="paper_ready_software_boundary",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "citylbm_software_feedback_matrix.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
                RESULTS_DIR / "citylbm_manifest_schema_gate.json",
                RESULTS_DIR / "citylbm_gha_install_audit.json",
                RUN_COMPONENT,
                ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs",
            ],
            paper_location="Software implications / Limitations",
            allowed_statement="CityLBM converts evidence into formal defaults, diagnostic-only switches, manifest-level publication dependencies, a Run Simulation Publication Gate output, GHA staging audit, and release blockers.",
            must_not_claim="Do not promote benchmark-tuned diagnostics or manifest publication readiness to default accuracy models.",
        ),
        row(
            item_id="PR008",
            reviewer_question="What still blocks a formal accuracy-oriented release?",
            status="blocked_formal_release",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "release_gate.json",
                RESULTS_DIR / "casee_official_run_preflight.json",
                RESULTS_DIR / "rhino_gha_load_gate.json",
                RESULTS_DIR / "citylbm_gha_install_audit.json",
                RESULTS_DIR / "build_chain_manifest.json",
                RESULTS_DIR / "vs_cpp_recovery_gate.json",
            ],
            paper_location="Limitations / Future work",
            allowed_statement="Formal release remains blocked by the official z=2 m metric gate, missing Rhino/GHA load evidence, current GHA staging status, current GPU/runtime recovery needs, and unresolved VS C++ Build Tools recovery blockers.",
            must_not_claim="Do not create a formal v0.4.0 tag or state that the optimized plugin satisfies research-grade accuracy.",
        ),
        row(
            item_id="PR009",
            reviewer_question="Is the entire publication packet reproducible from scripts?",
            status="paper_ready_scripted_packet",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "casee_reproducibility_suite.json",
                RESULTS_DIR / "casee_paper_evidence_gate.json",
                RESULTS_DIR / "casee_artifact_index.json",
            ],
            paper_location="Reproducibility statement",
            allowed_statement="The current publication packet is script-generated and passes the paper evidence and claim-support gates.",
            must_not_claim="Do not treat a passing publication gate as a passing CFD accuracy gate.",
        ),
        row(
            item_id="PR010",
            reviewer_question="Are release assets lightweight and traceable?",
            status="paper_ready_release_assets",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "casee_artifact_index.json",
                RESULTS_DIR / "casee_release_asset_manifest.json",
                release_note,
            ],
            paper_location="Data and code availability",
            allowed_statement=(
                f"The artifact index records {artifact_summary.get('artifact_count')} artifacts and "
                f"{artifact_summary.get('lightweight_release_asset_count')} lightweight release assets; "
                f"the curated release manifest selects {release_asset_summary.get('upload_asset_count')} upload assets "
                f"and keeps {release_asset_summary.get('excluded_or_hash_only_count')} raw/large assets excluded or hash-only."
            ),
            must_not_claim="Do not commit large VTK/raw geometry duplicates as manuscript evidence.",
        ),
    ]


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    paper_gate = read_json(RESULTS_DIR / "casee_paper_evidence_gate.json")
    claim_gate = read_json(RESULTS_DIR / "casee_claim_support_gate.json")
    figure_gate = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    appendix = read_json(RESULTS_DIR / "casee_paper_appendix_manifest.json")
    suite = read_json(RESULTS_DIR / "casee_reproducibility_suite.json")
    feedback = read_json(RESULTS_DIR / "citylbm_software_feedback_matrix.json")
    ledger = read_json(RESULTS_DIR / "casee_solver_run_provenance_ledger.json")
    release_assets = read_json(RESULTS_DIR / "casee_release_asset_manifest.json")
    vs_cpp_recovery = read_json(RESULTS_DIR / "vs_cpp_recovery_gate.json")
    gha_install = read_json(RESULTS_DIR / "citylbm_gha_install_audit.json")
    suite_ok = suite.get("suite_passed") is True or suite.get("publication_gate_provisional") is True

    metrics = release_gate.get("metrics") or {}
    r2 = metrics.get("r2")
    status_counts: Dict[str, int] = {}
    for item in rows:
        status = str(item["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    passed = (
        all(bool(item["source_paths_exist"]) for item in rows)
        and release_gate.get("formal_release_allowed") is False
        and r2 is not None
        and float(r2) < 0.0
        and paper_gate.get("paper_evidence_gate_passed") is True
        and (claim_gate.get("summary") or {}).get("claim_support_gate_passed") is True
        and (claim_gate.get("summary") or {}).get("no_formal_accuracy_claims") is True
        and figure_gate.get("figure_gate_passed") is True
        and figure_gate.get("formal_accuracy_claim_supported") is False
        and appendix.get("formal_release_allowed") is False
        and suite_ok
        and (feedback.get("summary") or {}).get("software_feedback_matrix_passed") is True
        and ledger.get("ledger_passed") is True
        and (release_assets.get("summary") or {}).get("release_asset_manifest_passed") is True
        and (release_assets.get("summary") or {}).get("formal_accuracy_claim_supported") is False
        and (vs_cpp_recovery.get("summary") or {}).get("vs_cpp_recovery_gate_passed") is True
        and (vs_cpp_recovery.get("summary") or {}).get("formal_accuracy_claim_supported") is False
        and gha_install.get("install_audit_passed") is True
        and gha_install.get("formal_accuracy_claim_supported") is False
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "publication_readiness_gate_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_publication_packet; blocked formal accuracy release",
        "row_count": len(rows),
        "status_counts": status_counts,
        "all_source_paths_exist": all(bool(item["source_paths_exist"]) for item in rows),
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "recommended_tag": release_gate.get("recommended_tag"),
        "official_z2m_metrics": metrics,
        "paper_evidence_gate_passed": paper_gate.get("paper_evidence_gate_passed"),
        "claim_support_gate_passed": (claim_gate.get("summary") or {}).get("claim_support_gate_passed"),
        "figure_gate_passed": figure_gate.get("figure_gate_passed"),
        "suite_passed": suite.get("suite_passed"),
        "suite_provisional": suite.get("publication_gate_provisional") is True,
        "release_asset_manifest_passed": (release_assets.get("summary") or {}).get("release_asset_manifest_passed"),
        "vs_cpp_recovery_gate_passed": (vs_cpp_recovery.get("summary") or {}).get("vs_cpp_recovery_gate_passed"),
        "gha_install_audit_passed": gha_install.get("install_audit_passed"),
        "formal_accuracy_claim_supported": False,
        "boundary": (
            "This gate audits whether the current Case E material is publication-ready as a negative-validation "
            "and limitations package. It does not add CFD output, improve official metrics, or permit a formal release."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in rows:
            writer.writerow({key: item[key] for key in FIELDNAMES})


def write_markdown(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    metrics = summary.get("official_z2m_metrics") or {}
    lines = [
        "# Case E Publication Readiness Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Publication readiness gate passed: {summary['publication_readiness_gate_passed']}",
        f"- Claim readiness: `{summary['claim_readiness']}`",
        f"- Formal release allowed: {summary['formal_release_allowed']}",
        f"- Recommended tag: `{summary['recommended_tag']}`",
        f"- Official MAE: {metrics.get('mae_pp')} pp",
        f"- Official R2: {metrics.get('r2')}",
        f"- Official Pearson: {metrics.get('pearson')}",
        "",
        "## Reviewer Audit",
        "",
        "| id | reviewer question | status | paper location | allowed statement | must not claim |",
        "|---|---|---|---|---|---|",
    ]
    for item in rows:
        lines.append(
            f"| `{item['item_id']}` | {item['reviewer_question']} | {item['status']} | "
            f"{item['paper_location']} | {item['allowed_statement']} | {item['must_not_claim']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = summarize(rows)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": [
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "casee_paper_evidence_gate.json"),
            rel(RESULTS_DIR / "casee_claim_support_gate.json"),
            rel(RESULTS_DIR / "casee_paper_results_figure_qa.json"),
            rel(RESULTS_DIR / "casee_paper_appendix_manifest.json"),
            rel(RESULTS_DIR / "casee_reproducibility_suite.json"),
            rel(RESULTS_DIR / "citylbm_software_feedback_matrix.json"),
            rel(RESULTS_DIR / "casee_solver_run_provenance_ledger.json"),
            rel(RESULTS_DIR / "casee_release_asset_manifest.json"),
            rel(RESULTS_DIR / "vs_cpp_recovery_gate.json"),
            rel(RESULTS_DIR / "citylbm_gha_install_audit.json"),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"publication_readiness_gate_passed": summary["publication_readiness_gate_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["publication_readiness_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
