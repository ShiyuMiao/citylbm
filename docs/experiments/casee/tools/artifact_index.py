#!/usr/bin/env python3
"""Create a lightweight artifact index for Case E paper and release evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Set


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_CSV = RESULTS_DIR / "casee_artifact_index.csv"
OUT_JSON = RESULTS_DIR / "casee_artifact_index.json"
OUT_MD = RESULTS_DIR / "casee_artifact_index.md"
EVIDENCE_INVENTORY = CASE_DIR / "evidence_inventory.csv"


EXPLICIT_ARTIFACTS = [
    "README.md",
    "CHANGELOG.md",
    "CityLBM/README.md",
    "CityLBM/bin/CityLBM.gha",
    "docs/releases/v0.4.0-rc30.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md",
    "docs/experiments/casee/data_manifest.csv",
    "docs/experiments/casee/casee_preset.json",
    "docs/experiments/casee/casee_protocol.md",
    "docs/experiments/casee/native_fluidx3d_run_matrix.csv",
    "docs/experiments/casee/evidence_inventory.csv",
    "docs/experiments/casea/results/casea_smoke_regression.json",
    "docs/experiments/casea/results/casea_vtk_manifest.csv",
]

RESULT_PATTERNS = [
    "casee_*.csv",
    "casee_*.json",
    "casee_*.md",
    "casee_*.png",
    "casee_*.svg",
    "casee_*.xlsx",
    "dx1_feasibility_estimate.*",
    "environment_manifest.json",
    "release_gate.json",
    "casee_manuscript_results_table.*",
    "casee_paper_results_figure.*",
    "citylbm_paper_results_packet.*",
    "citylbm_manifest_output_gate.*",
    "citylbm_software_feedback_matrix.*",
    "build_chain_manifest.json",
    "plugin_identity_gate.json",
    "rhino_gha_load_gate.*",
    "casee_reproducibility_suite.json",
    "casee_reproducibility_suite.md",
    "casee_paper_appendix_manifest.json",
    "casee_official_run_preflight.*",
    "casee_environment_recovery_runbook.*",
    "casee_failure_mode_atlas.*",
    "casee_default_policy_gate.*",
    "casee_remaining_blockers.*",
    "casee_next_experiment_runbook.*",
    "citylbm_build_check.log",
    "fluidx3d_*_run*.log",
    "fluidx3d_*_compile.log",
]

OFFICIAL_DATA_PATTERNS = [
    "AF_caseE.csv",
    "BD_caseE.stl",
    "RS_caseE.csv",
    "MP_caseE.png",
    "readme_caseE.md",
    "LF_caseE.xls",
]

TOOL_SCRIPTS = [
    "artifact_index.py",
    "build_chain_audit.py",
    "casee_blocker_remediation_plan.py",
    "casee_next_experiment_runbook.py",
    "casee_official_run_preflight.py",
    "casee_environment_recovery_runbook.py",
    "casee_failure_mode_atlas.py",
    "casee_default_policy_gate.py",
    "casee_manuscript_results_table.py",
    "casee_paper_results_figure.py",
    "citylbm_paper_results_packet.py",
    "citylbm_manifest_output_gate.py",
    "citylbm_software_feedback_matrix.py",
    "casee_audit.py",
    "casee_probe_modes_audit.py",
    "casee_probe_mode_metrics.py",
    "casee_spatial_alignment_diagnostic.py",
    "casee_voxel_probe_audit.py",
    "generate_native_casee.py",
    "manuscript_evidence_summary.py",
    "paper_appendix_generator.py",
    "paper_evidence_gate.py",
    "plugin_identity_gate.py",
    "rhino_gha_load_gate.py",
    "reproducibility_suite.py",
    "release_gate.py",
]

FIELDNAMES = [
    "path",
    "category",
    "release_asset_role",
    "source_evidence_type",
    "claim_readiness",
    "git_tracked",
    "size_bytes",
    "sha256",
    "mtime_utc",
    "paper_use",
    "limitations",
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def tracked_files() -> Set[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence_map() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for row in read_csv(EVIDENCE_INVENTORY):
        source = (row.get("source_path") or "").replace("\\", "/")
        if source:
            out[source] = row
    return out


def collect_paths() -> List[Path]:
    paths: Dict[str, Path] = {}
    self_outputs = {OUT_CSV.resolve(), OUT_JSON.resolve(), OUT_MD.resolve()}
    for item in EXPLICIT_ARTIFACTS:
        p = ROOT / item
        if p.exists():
            paths[rel(p)] = p
    official_dir = CASE_DIR / "official_data"
    for pattern in OFFICIAL_DATA_PATTERNS:
        for p in official_dir.glob(pattern):
            if p.is_file():
                paths[rel(p)] = p
    for pattern in RESULT_PATTERNS:
        for p in RESULTS_DIR.glob(pattern):
            if p.is_file():
                if p.resolve() in self_outputs:
                    continue
                paths[rel(p)] = p
    tool_dir = CASE_DIR / "tools"
    for item in TOOL_SCRIPTS:
        p = tool_dir / item
        if p.exists():
            paths[rel(p)] = p
    return [paths[key] for key in sorted(paths)]


def category(path: str) -> str:
    if path.endswith("CityLBM.gha"):
        return "software_asset"
    if path.startswith("docs/experiments/casee/official_data/"):
        return "official_data"
    if path.startswith("docs/experiments/casee/tools/"):
        return "reproducibility_script"
    if path.startswith("docs/releases/"):
        return "release_notes"
    if path.endswith(".png"):
        return "figure"
    if path.endswith(".xlsx"):
        return "summary_workbook"
    if path.endswith(".log"):
        return "run_or_build_log"
    if path.endswith(".csv"):
        return "table_or_metric_csv"
    if path.endswith(".json"):
        return "manifest_or_gate_json"
    if path.endswith(".md"):
        return "report_or_protocol_markdown"
    return "other"


def release_asset_role(path: str, cat: str, size_bytes: int) -> str:
    if cat == "official_data" and path.endswith(("BD_caseE.stl", "LF_caseE.xls")):
        return "external_reference_hash_only"
    if cat == "run_or_build_log" and size_bytes > 250_000:
        return "optional_log_asset"
    if cat in {
        "software_asset",
        "figure",
        "summary_workbook",
        "table_or_metric_csv",
        "manifest_or_gate_json",
        "report_or_protocol_markdown",
        "release_notes",
        "reproducibility_script",
    }:
        return "lightweight_release_asset"
    return "hash_record_only"


def claim_readiness(path: str, cat: str, inventory_row: Dict[str, str]) -> str:
    if path.endswith("release_gate.json"):
        return "blocked_formal_release_gate"
    if "casee_remaining_blockers" in path or "casee_blocker_remediation_plan" in path:
        return "blocked_followup_plan"
    if "casee_next_experiment_runbook" in path:
        return "blocked_followup_runbook"
    if "rhino_gha_load_gate" in path:
        return "blocked_manual_rhino_load"
    if "casee_official_run_preflight" in path:
        return "blocked_official_followup_preflight"
    if "casee_environment_recovery_runbook" in path:
        return "blocked_environment_recovery_runbook"
    if "casee_failure_mode_atlas" in path:
        return "limitations_ready_failure_mode_atlas"
    if "casee_default_policy_gate" in path:
        return "paper_ready_default_policy_boundary"
    if "casee_manuscript_results_table" in path:
        return "paper_ready_manuscript_results_table"
    if "casee_paper_results_figure" in path:
        return "paper_ready_figure_negative_validation"
    if "citylbm_paper_results_packet" in path:
        return "paper_ready_cross_experiment_results_packet"
    if "citylbm_manifest_output_gate" in path:
        return "paper_ready_manifest_traceability"
    if "citylbm_software_feedback_matrix" in path:
        return "paper_ready_software_feedback_boundary"
    if "paper_evidence_gate" in path or "plugin_identity_gate" in path or "reproducibility_suite" in path:
        return "paper_ready_traceability"
    if "reproducibility_appendix" in path or "paper_appendix_manifest" in path or "paper_appendix_generator" in path:
        return "paper_ready_reproducibility_appendix"
    if path.endswith("casee_metrics.csv") or path.endswith("casee_validation_report.md"):
        return "limitations_ready_negative_validation"
    if "probe_mode" in path or "voxel_probe" in path or "spatial_alignment" in path or "dx1_feasibility" in path:
        return "limitations_ready_diagnostic"
    if cat == "software_asset":
        return "paper_ready_software_identity"
    if cat == "official_data":
        return "paper_ready_protocol_input"
    if inventory_row.get("verification_status") == "blocked":
        return "blocked"
    return "paper_ready_reproducibility"


def paper_use(path: str, readiness: str) -> str:
    if readiness == "blocked_formal_release_gate":
        return "Use to state that formal v0.4.0 is not allowed."
    if readiness == "blocked_followup_plan":
        return "Use to document the concrete blockers and next validation actions."
    if readiness == "blocked_followup_runbook":
        return "Use to document future commands and formal-result policy."
    if readiness == "blocked_manual_rhino_load":
        return "Use to document the fail-closed Rhino/Grasshopper new-GHA loading gate."
    if readiness == "blocked_official_followup_preflight":
        return "Use to document why another official native Case E follow-up run is or is not currently allowed."
    if readiness == "blocked_environment_recovery_runbook":
        return "Use to document the environment recovery actions needed before more official long runs."
    if readiness == "limitations_ready_failure_mode_atlas":
        return "Use to structure limitations and software-feedback discussion without claiming formal accuracy."
    if readiness == "paper_ready_default_policy_boundary":
        return "Use to distinguish formal defaults from diagnostic-only software switches."
    if readiness == "paper_ready_manuscript_results_table":
        return "Use as the manuscript-facing Case E result table with formal and diagnostic boundaries."
    if readiness == "paper_ready_figure_negative_validation":
        return "Use as a paper figure for negative validation and limitations only."
    if readiness == "paper_ready_cross_experiment_results_packet":
        return "Use to organize Experiments 1, 2, and 3 results into manuscript-ready and limitations-only rows."
    if readiness == "paper_ready_manifest_traceability":
        return "Use to show Run Simulation exposes the run manifest path for paper and reviewer traceability."
    if readiness == "paper_ready_software_feedback_boundary":
        return "Use to trace how experiment findings are converted into defaults, diagnostic switches, and blockers."
    if "negative_validation" in readiness:
        return "Use as official z=2 m negative validation evidence."
    if "diagnostic" in readiness:
        return "Use for limitations and error-mechanism discussion only."
    if "protocol_input" in readiness:
        return "Use to document official AIJ Case E inputs and protocol."
    if "software_identity" in readiness:
        return "Use to identify the built rc plugin artifact, not CFD accuracy."
    if "traceability" in readiness:
        return "Use to prove claim-boundary and artifact traceability checks."
    if "reproducibility_appendix" in readiness:
        return "Use as a paper-facing reproducibility appendix, not as accuracy proof."
    return "Use as reproducibility support, not as standalone accuracy proof."


def limitations(path: str, readiness: str) -> str:
    if "diagnostic" in readiness:
        return "Diagnostic only; do not report as formal official z=2 m accuracy."
    if "negative_validation" in readiness:
        return "Formal metric fails; do not claim predictive accuracy."
    if "software_identity" in readiness:
        return "Rhino/Grasshopper loading remains independently unverified."
    if readiness == "blocked_formal_release_gate":
        return "Formal v0.4.0 tag remains prohibited."
    if readiness == "blocked_followup_plan":
        return "Planning evidence only; does not improve or replace official z=2 m metrics."
    if readiness == "blocked_followup_runbook":
        return "Future-run command matrix only; not solver-output evidence."
    if readiness == "blocked_manual_rhino_load":
        return "Manual Rhino/Grasshopper evidence is absent or incomplete; do not state the new GHA was loaded."
    if readiness == "blocked_official_followup_preflight":
        return "Preflight evidence only; does not add solver output or improve the official metric."
    if readiness == "blocked_environment_recovery_runbook":
        return "Operational recovery guidance only; does not install tools, run CFD, or improve metrics."
    if readiness == "limitations_ready_failure_mode_atlas":
        return "Synthesis of existing diagnostics only; does not add a new solver result."
    if readiness == "paper_ready_default_policy_boundary":
        return "Default-policy boundary only; does not improve or replace official z=2 m metrics."
    if readiness == "paper_ready_manuscript_results_table":
        return "Manuscript result formatting only; formal official row remains negative validation and diagnostic rows remain limitations-only."
    if readiness == "paper_ready_figure_negative_validation":
        return "Figure formatting only; diagnostic rows cannot be reported as formal validation."
    if readiness == "paper_ready_cross_experiment_results_packet":
        return "Manuscript organization evidence only; does not add new CFD results or formal validation."
    if readiness == "paper_ready_manifest_traceability":
        return "Manifest-output traceability only; does not prove Rhino loaded the new GHA or CFD accuracy."
    if readiness == "paper_ready_software_feedback_boundary":
        return "Software-feedback boundary only; does not add solver output or justify formal accuracy."
    if path.endswith("BD_caseE.stl"):
        return "Official raw geometry should be referenced by hash; avoid duplicating large source data in manuscript."
    return ""


def build_rows() -> List[Dict[str, object]]:
    tracked = tracked_files()
    emap = evidence_map()
    rows: List[Dict[str, object]] = []
    for path in collect_paths():
        rpath = rel(path)
        cat = category(rpath)
        inv = emap.get(rpath, {})
        readiness = claim_readiness(rpath, cat, inv)
        size = path.stat().st_size
        source_type = inv.get("type") or ("newly_run" if rpath.endswith(("casee_artifact_index.csv", "casee_artifact_index.json", "casee_artifact_index.md")) else "preexisting_artifact")
        rows.append(
            {
                "path": rpath,
                "category": cat,
                "release_asset_role": release_asset_role(rpath, cat, size),
                "source_evidence_type": source_type,
                "claim_readiness": readiness,
                "git_tracked": str(rpath in tracked).lower(),
                "size_bytes": size,
                "sha256": sha256(path),
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "paper_use": paper_use(rpath, readiness),
                "limitations": limitations(rpath, readiness),
            }
        )
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, rows: List[Dict[str, object]], summary: Dict[str, object]) -> None:
    by_role: Dict[str, int] = {}
    by_readiness: Dict[str, int] = {}
    for row in rows:
        by_role[str(row["release_asset_role"])] = by_role.get(str(row["release_asset_role"]), 0) + 1
        by_readiness[str(row["claim_readiness"])] = by_readiness.get(str(row["claim_readiness"]), 0) + 1

    lines = [
        "# Case E Artifact Index",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Artifact count: {summary['artifact_count']}",
        f"- Total size bytes: {summary['total_size_bytes']}",
        f"- Lightweight release assets: {summary['lightweight_release_asset_count']}",
        f"- Optional log assets: {summary['optional_log_asset_count']}",
        f"- Hash-only external references: {summary['external_reference_hash_only_count']}",
        "",
        "## Release Asset Roles",
        "",
    ]
    for key in sorted(by_role):
        lines.append(f"- {key}: {by_role[key]}")
    lines += ["", "## Claim Readiness", ""]
    for key in sorted(by_readiness):
        lines.append(f"- {key}: {by_readiness[key]}")
    lines += [
        "",
        "## Key Artifacts",
        "",
        "| path | role | readiness | sha256 |",
        "|---|---|---|---|",
    ]
    key_rows = [
        row
        for row in rows
        if str(row["path"]).endswith(
            (
                "CityLBM.gha",
                "release_gate.json",
                "casee_metrics.csv",
                "casee_validation_report.md",
                "casee_paper_evidence_gate.json",
                "casee_paper_appendix_manifest.json",
                "casee_reproducibility_suite.json",
                "casee_official_run_preflight.json",
                "casee_official_run_preflight.md",
                "casee_environment_recovery_runbook.json",
                "casee_environment_recovery_runbook.md",
                "casee_failure_mode_atlas.json",
                "casee_failure_mode_atlas.md",
                "casee_failure_mode_atlas.png",
                "casee_default_policy_gate.json",
                "casee_default_policy_gate.md",
                "casee_default_policy_gate.csv",
                "casee_manuscript_results_table.json",
                "casee_manuscript_results_table.md",
                "casee_manuscript_results_table.csv",
                "casee_paper_results_figure.svg",
                "casee_paper_results_figure.png",
                "casee_paper_results_figure_source.csv",
                "casee_paper_results_figure_qa.json",
                "casee_paper_results_figure_qa.md",
                "citylbm_paper_results_packet.json",
                "citylbm_paper_results_packet.md",
                "citylbm_paper_results_packet.csv",
                "citylbm_manifest_output_gate.json",
                "citylbm_manifest_output_gate.md",
                "citylbm_manifest_output_gate.csv",
                "citylbm_software_feedback_matrix.json",
                "citylbm_software_feedback_matrix.md",
                "citylbm_software_feedback_matrix.csv",
                "casee_remaining_blockers.json",
                "casee_remaining_blockers.md",
                "casee_next_experiment_runbook.json",
                "casee_next_experiment_runbook.md",
                "plugin_identity_gate.json",
                "rhino_gha_load_gate.json",
                "rhino_gha_load_gate.md",
                "casee_v04_reproducibility_appendix_en.md",
                "casee_v04_reproducibility_appendix_zh.md",
                "casee_manuscript_claim_matrix.csv",
                "casee_zcenter_probe_mode_metrics.csv",
                "casee_zcenter_voxel_probe_audit_groups.csv",
                "v0.4.0-rc30.md",
            )
        )
    ]
    for row in key_rows:
        lines.append(f"| `{row['path']}` | {row['release_asset_role']} | {row['claim_readiness']} | `{row['sha256']}` |")
    lines += [
        "",
        "## Boundary",
        "",
        "This index supports reproducibility and manuscript traceability. It does not upgrade the formal AIJ Case E official z=2 m metric, which remains a negative validation result until the release gate passes.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(rows),
        "total_size_bytes": sum(int(row["size_bytes"]) for row in rows),
        "lightweight_release_asset_count": sum(1 for row in rows if row["release_asset_role"] == "lightweight_release_asset"),
        "optional_log_asset_count": sum(1 for row in rows if row["release_asset_role"] == "optional_log_asset"),
        "external_reference_hash_only_count": sum(1 for row in rows if row["release_asset_role"] == "external_reference_hash_only"),
        "formal_accuracy_claim_supported": False,
        "formal_accuracy_claim_blocker": "official z=2 m metric gate fails; use release_gate.json for current metrics",
    }
    write_csv(OUT_CSV, rows)
    OUT_JSON.write_text(json.dumps({"summary": summary, "artifacts": rows}, indent=2), encoding="utf-8")
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
