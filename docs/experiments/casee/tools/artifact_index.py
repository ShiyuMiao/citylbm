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
    "docs/releases/v0.4.0-rc15.md",
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
    "casee_*.xlsx",
    "dx1_feasibility_estimate.*",
    "environment_manifest.json",
    "release_gate.json",
    "build_chain_manifest.json",
    "plugin_identity_gate.json",
    "casee_reproducibility_suite.json",
    "casee_reproducibility_suite.md",
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
    "casee_audit.py",
    "casee_probe_modes_audit.py",
    "casee_probe_mode_metrics.py",
    "casee_spatial_alignment_diagnostic.py",
    "casee_voxel_probe_audit.py",
    "generate_native_casee.py",
    "manuscript_evidence_summary.py",
    "paper_evidence_gate.py",
    "plugin_identity_gate.py",
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
    if "paper_evidence_gate" in path or "plugin_identity_gate" in path or "reproducibility_suite" in path:
        return "paper_ready_traceability"
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
                "plugin_identity_gate.json",
                "casee_manuscript_claim_matrix.csv",
                "casee_zcenter_probe_mode_metrics.csv",
                "casee_zcenter_voxel_probe_audit_groups.csv",
                "v0.4.0-rc13.md",
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
