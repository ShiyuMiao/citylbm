#!/usr/bin/env python3
"""Create a curated lightweight GitHub Release asset manifest for Case E."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
ARTIFACT_INDEX = RESULTS_DIR / "casee_artifact_index.json"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
OUT_JSON = RESULTS_DIR / "casee_release_asset_manifest.json"
OUT_CSV = RESULTS_DIR / "casee_release_asset_manifest.csv"
OUT_MD = RESULTS_DIR / "casee_release_asset_manifest.md"

RAW_EXTENSIONS = {".vtk", ".vti", ".vtp", ".vtu", ".stl", ".3dm"}
MAX_SINGLE_ASSET_BYTES = 25 * 1024 * 1024
MAX_TOTAL_ASSET_BYTES = 100 * 1024 * 1024

ALWAYS_INCLUDE = {
    "README.md",
    "CHANGELOG.md",
    "CityLBM/bin/CityLBM.gha",
    "docs/releases/v0.4.0-rc70.md",
    "docs/releases/v0.4.0-rc71.md",
    "docs/releases/v0.4.0-rc72.md",
    "docs/releases/v0.4.0-rc73.md",
    "docs/releases/v0.4.0-rc74.md",
    "docs/releases/v0.4.0-rc75.md",
    "docs/releases/v0.4.0-rc76.md",
    "docs/releases/v0.4.0-rc77.md",
    "docs/releases/v0.4.0-rc78.md",
    "docs/releases/v0.4.0-rc79.md",
    "docs/releases/v0.4.0-rc80.md",
    "docs/releases/v0.4.0-rc81.md",
    "docs/releases/v0.4.0-rc82.md",
    "docs/releases/v0.4.0-rc83.md",
    "docs/experiments/casea/results/casea_smoke_regression.json",
    "docs/experiments/casea/results/casea_vtk_manifest.csv",
    "docs/experiments/casee/data_manifest.csv",
    "docs/experiments/casee/casee_preset.json",
    "docs/experiments/casee/casee_protocol.md",
    "docs/experiments/casee/evidence_inventory.csv",
    "docs/experiments/casee/native_fluidx3d_run_matrix.csv",
    "docs/experiments/casee/results/build_chain_manifest.json",
    "docs/experiments/casee/results/build_chain_manifest.csv",
    "docs/experiments/casee/results/build_chain_manifest.md",
    "docs/experiments/casee/results/citylbm_build_hash_stability_gate.json",
    "docs/experiments/casee/results/citylbm_build_hash_stability_gate.csv",
    "docs/experiments/casee/results/citylbm_build_hash_stability_gate.md",
    "docs/experiments/casee/results/vs_cpp_recovery_gate.json",
    "docs/experiments/casee/results/vs_cpp_recovery_gate.csv",
    "docs/experiments/casee/results/vs_cpp_recovery_gate.md",
    "docs/experiments/casee/results/vs_cpp_buildtools_recovery_probe.json",
    "docs/experiments/casee/results/environment_manifest.json",
    "docs/experiments/casee/results/release_gate.json",
    "docs/experiments/casee/results/casee_metrics.csv",
    "docs/experiments/casee/results/casee_validation_report.md",
    "docs/experiments/casee/results/casee_validation_summary.xlsx",
    "docs/experiments/casee/results/casee_reproducibility_suite.json",
    "docs/experiments/casee/results/casee_reproducibility_suite.md",
    "docs/experiments/casee/results/casee_paper_evidence_gate.json",
    "docs/experiments/casee/results/casee_paper_evidence_gate.md",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.json",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.csv",
    "docs/experiments/casee/results/casee_postrun_official_audit_handoff.md",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.json",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_component_gate.md",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.json",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.csv",
    "docs/experiments/casee/results/citylbm_casee_postrun_audit_binary_gate.md",
    "docs/experiments/casee/results/casee_claim_support_gate.json",
    "docs/experiments/casee/results/casee_claim_support_gate.md",
    "docs/experiments/casee/results/casee_publication_readiness_gate.json",
    "docs/experiments/casee/results/casee_publication_readiness_gate.md",
    "docs/experiments/casee/results/casee_artifact_index.json",
    "docs/experiments/casee/results/casee_artifact_index.csv",
    "docs/experiments/casee/results/casee_artifact_index.md",
    "docs/experiments/casee/results/citylbm_software_feedback_matrix.json",
    "docs/experiments/casee/results/citylbm_software_feedback_matrix.md",
    "docs/experiments/casee/results/citylbm_manifest_output_gate.json",
    "docs/experiments/casee/results/citylbm_manifest_output_gate.md",
    "docs/experiments/casee/results/citylbm_manifest_schema_gate.json",
    "docs/experiments/casee/results/citylbm_manifest_schema_gate.md",
    "docs/experiments/casee/results/casee_default_policy_gate.json",
    "docs/experiments/casee/results/casee_default_policy_gate.md",
    "docs/experiments/casee/results/casee_wall_followup_codegen_gate.json",
    "docs/experiments/casee/results/casee_wall_followup_codegen_gate.csv",
    "docs/experiments/casee/results/casee_wall_followup_codegen_gate.md",
    "docs/experiments/casee/results/casee_inlet_followup_codegen_gate.json",
    "docs/experiments/casee/results/casee_inlet_followup_codegen_gate.csv",
    "docs/experiments/casee/results/casee_inlet_followup_codegen_gate.md",
    "docs/experiments/casee/results/casee_c016_codegen_gate.json",
    "docs/experiments/casee/results/casee_c016_codegen_gate.csv",
    "docs/experiments/casee/results/casee_c016_codegen_gate.md",
    "docs/experiments/casee/results/casee_native_codegen_smoke_gate.json",
    "docs/experiments/casee/results/casee_native_codegen_smoke_gate.csv",
    "docs/experiments/casee/results/casee_native_codegen_smoke_gate.md",
    "docs/experiments/casee/results/casee_manuscript_results_table.json",
    "docs/experiments/casee/results/casee_manuscript_results_table.csv",
    "docs/experiments/casee/results/casee_manuscript_results_table.md",
    "docs/experiments/casee/results/casee_paper_results_figure.png",
    "docs/experiments/casee/results/casee_paper_results_figure.svg",
    "docs/experiments/casee/results/casee_paper_results_figure_source.csv",
    "docs/experiments/casee/results/casee_paper_results_figure_qa.json",
    "docs/experiments/casee/results/casee_solver_run_provenance_ledger.json",
    "docs/experiments/casee/results/casee_solver_run_provenance_ledger.csv",
    "docs/experiments/casee/results/casee_solver_run_provenance_ledger.md",
    "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json",
    "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.csv",
    "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md",
    "docs/experiments/casee/results/casee_c014_residual_structure_audit.json",
    "docs/experiments/casee/results/casee_c014_residual_structure_audit.csv",
    "docs/experiments/casee/results/casee_c014_residual_structure_audit.md",
    "docs/experiments/casee/results/rhino_gha_load_gate.json",
    "docs/experiments/casee/results/rhino_gha_load_gate.md",
    "docs/experiments/casee/results/citylbm_gha_install_audit.json",
    "docs/experiments/casee/results/citylbm_gha_install_audit.csv",
    "docs/experiments/casee/results/citylbm_gha_install_audit.md",
    "docs/experiments/casee/results/github_release_publication_gate.json",
    "docs/experiments/casee/results/github_release_publication_gate.csv",
    "docs/experiments/casee/results/github_release_publication_gate.md",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.json",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.csv",
    "docs/experiments/casee/results/casee_workspace_hygiene_gate.md",
    "academic-paper-writer/paper-drafts/casee_v04_manuscript_section_pack_en.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_en.md",
    "academic-paper-writer/paper-drafts/casee_v04_reproducibility_appendix_zh.md",
}


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def file_metadata(path: str) -> Dict[str, Any]:
    full = ROOT / path
    digest = hashlib.sha256()
    with full.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": path,
        "size_bytes": full.stat().st_size,
        "sha256": digest.hexdigest(),
        "git_tracked": "generated_or_unindexed",
    }


def write_text_retry(path: Path, text: str, *, attempts: int = 6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.2 * (attempt + 1))
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(path)
        return
    except OSError:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if last_error is not None:
            raise last_error
        raise


def release_asset_kind(path: str) -> str:
    if path.endswith("CityLBM.gha"):
        return "compiled_plugin"
    if path.startswith("docs/releases/"):
        return "release_notes"
    if path.endswith(".png") or path.endswith(".svg"):
        return "figure"
    if path.endswith(".xlsx"):
        return "workbook_summary"
    if path.endswith(".csv"):
        return "csv_table"
    if path.endswith(".json"):
        return "json_manifest_or_gate"
    if path.endswith(".md"):
        return "markdown_report_or_protocol"
    return "other_lightweight_asset"


def is_raw_or_large_forbidden(path: str, size_bytes: int, role: str) -> bool:
    suffix = Path(path).suffix.lower()
    return suffix in RAW_EXTENSIONS or role in {"external_reference_hash_only", "optional_log_asset"} or size_bytes > MAX_SINGLE_ASSET_BYTES


def selected_paths(recommended_tag: str) -> set[str]:
    paths = set(ALWAYS_INCLUDE)
    if recommended_tag:
        paths.add(f"docs/releases/{recommended_tag}.md")
    return paths


def build_rows(artifact_index: Dict[str, Any], recommended_tag: str) -> List[Dict[str, Any]]:
    wanted = selected_paths(recommended_tag)
    rows: List[Dict[str, Any]] = []
    for item in artifact_index.get("artifacts", []):
        path = str(item.get("path", ""))
        size = int(item.get("size_bytes") or 0)
        role = str(item.get("release_asset_role", ""))
        include = path in wanted
        forbidden = is_raw_or_large_forbidden(path, size, role)
        if include or forbidden:
            rows.append(
                {
                    "path": path,
                    "include_in_release_upload": bool(include and not forbidden),
                    "asset_kind": release_asset_kind(path),
                    "release_asset_role": role,
                    "claim_readiness": item.get("claim_readiness", ""),
                    "size_bytes": size,
                    "sha256": item.get("sha256", ""),
                    "git_tracked": item.get("git_tracked", ""),
                    "paper_use": item.get("paper_use", ""),
                    "limitations": item.get("limitations", ""),
                    "exclusion_reason": "" if include and not forbidden else exclusion_reason(path, role, size, include),
                }
            )
    present = {row["path"] for row in rows}
    for path in sorted(wanted - present):
        if (ROOT / path).exists():
            meta = file_metadata(path)
            rows.append(
                {
                    "path": path,
                    "include_in_release_upload": True,
                    "asset_kind": release_asset_kind(path),
                    "release_asset_role": "lightweight_release_asset",
                    "claim_readiness": "paper_ready_release_asset_manifest",
                    "size_bytes": meta["size_bytes"],
                    "sha256": meta["sha256"],
                    "git_tracked": meta["git_tracked"],
                    "paper_use": "Use as a generated release upload manifest artifact.",
                    "limitations": "Generated after the artifact index scan; hash is computed directly from disk.",
                    "exclusion_reason": "",
                }
            )
            continue
        rows.append(
            {
                "path": path,
                "include_in_release_upload": False,
                "asset_kind": release_asset_kind(path),
                "release_asset_role": "missing",
                "claim_readiness": "missing",
                "size_bytes": 0,
                "sha256": "",
                "git_tracked": "false",
                "paper_use": "",
                "limitations": "",
                "exclusion_reason": "required release asset is missing from artifact index",
            }
        )
    return sorted(rows, key=lambda row: (not bool(row["include_in_release_upload"]), str(row["path"])))


def exclusion_reason(path: str, role: str, size_bytes: int, wanted: bool) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in RAW_EXTENSIONS:
        return "raw geometry or VTK output must stay external/hash-only"
    if role == "external_reference_hash_only":
        return "official raw data is hash-only, not an upload asset"
    if role == "optional_log_asset":
        return "large log is optional, not part of the curated upload set"
    if size_bytes > MAX_SINGLE_ASSET_BYTES:
        return "single asset exceeds curated release size limit"
    if not wanted:
        return "not selected for the curated release upload set"
    return ""


def has_asset(rows: Iterable[Dict[str, Any]], predicate) -> bool:
    return any(row["include_in_release_upload"] and predicate(row) for row in rows)


def summarize(rows: List[Dict[str, Any]], release_gate: Dict[str, Any]) -> Dict[str, Any]:
    upload_rows = [row for row in rows if row["include_in_release_upload"]]
    excluded_rows = [row for row in rows if not row["include_in_release_upload"]]
    upload_total = sum(int(row["size_bytes"]) for row in upload_rows)
    checks = {
        "has_compiled_gha": has_asset(upload_rows, lambda row: row["path"].endswith("CityLBM.gha")),
        "has_release_note": has_asset(upload_rows, lambda row: row["path"].startswith("docs/releases/")),
        "has_validation_report": has_asset(upload_rows, lambda row: row["path"].endswith("casee_validation_report.md")),
        "has_metrics_csv": has_asset(upload_rows, lambda row: row["path"].endswith("casee_metrics.csv")),
        "has_summary_xlsx": has_asset(upload_rows, lambda row: row["path"].endswith(".xlsx")),
        "has_figures": has_asset(upload_rows, lambda row: row["path"].endswith(".png"))
        and has_asset(upload_rows, lambda row: row["path"].endswith(".svg")),
        "has_data_manifest": has_asset(upload_rows, lambda row: row["path"].endswith("data_manifest.csv")),
        "has_environment_manifest": has_asset(upload_rows, lambda row: row["path"].endswith("environment_manifest.json")),
        "has_claim_and_publication_gates": has_asset(upload_rows, lambda row: "casee_claim_support_gate" in row["path"])
        and has_asset(upload_rows, lambda row: "casee_publication_readiness_gate" in row["path"]),
        "has_reproducibility_suite": has_asset(upload_rows, lambda row: "casee_reproducibility_suite" in row["path"]),
        "excludes_raw_geometry_and_vtk": not any(
            row["include_in_release_upload"] and Path(str(row["path"])).suffix.lower() in RAW_EXTENSIONS
            for row in rows
        ),
        "upload_size_within_limit": upload_total <= MAX_TOTAL_ASSET_BYTES,
        "formal_accuracy_claim_supported": False,
    }
    required_true_checks = {key: value for key, value in checks.items() if key != "formal_accuracy_claim_supported"}
    passed = all(bool(value) for value in required_true_checks.values()) and checks["formal_accuracy_claim_supported"] is False
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "recommended_tag": release_gate.get("recommended_tag"),
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "formal_accuracy_claim_supported": False,
        "release_asset_manifest_passed": passed,
        "upload_asset_count": len(upload_rows),
        "excluded_or_hash_only_count": len(excluded_rows),
        "upload_total_size_bytes": upload_total,
        "max_total_asset_bytes": MAX_TOTAL_ASSET_BYTES,
        "checks": checks,
        "boundary": (
            "This manifest is a curated GitHub Release upload plan. It records lightweight assets and hash-only exclusions; "
            "it does not create a GitHub Release, add CFD output, or support formal accuracy claims."
        ),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "path",
        "include_in_release_upload",
        "asset_kind",
        "release_asset_role",
        "claim_readiness",
        "size_bytes",
        "sha256",
        "git_tracked",
        "paper_use",
        "limitations",
        "exclusion_reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: OSError | None = None
    for attempt in range(6):
        try:
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow({key: row.get(key, "") for key in fieldnames})
            return
        except OSError as exc:
            last_error = exc
            time.sleep(0.2 * (attempt + 1))
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with tmp_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
        tmp_path.replace(path)
        return
    except OSError:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        if last_error is not None:
            raise last_error
        raise


def write_markdown(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    upload_rows = [row for row in rows if row["include_in_release_upload"]]
    lines = [
        "# Case E Release Asset Manifest",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Release asset manifest passed: {summary['release_asset_manifest_passed']}",
        f"- Recommended tag: `{summary['recommended_tag']}`",
        f"- Formal release allowed: {summary['formal_release_allowed']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Upload assets: {summary['upload_asset_count']}",
        f"- Excluded/hash-only assets: {summary['excluded_or_hash_only_count']}",
        f"- Upload total size bytes: {summary['upload_total_size_bytes']}",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in summary["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Curated Upload Assets",
        "",
        "| path | kind | size | sha256 |",
        "|---|---|---:|---|",
    ]
    for row in upload_rows:
        lines.append(f"| `{row['path']}` | {row['asset_kind']} | {row['size_bytes']} | `{row['sha256']}` |")
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    write_text_retry(path, "\n".join(lines) + "\n")


def main() -> int:
    artifact_index = read_json(ARTIFACT_INDEX)
    release_gate = read_json(RELEASE_GATE)
    rows = build_rows(artifact_index, str(release_gate.get("recommended_tag", "")))
    summary = summarize(rows, release_gate)
    payload = {"summary": summary, "assets": rows}
    write_text_retry(OUT_JSON, json.dumps(payload, indent=2))
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, summary, rows)
    print(json.dumps({"release_asset_manifest_passed": summary["release_asset_manifest_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["release_asset_manifest_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
