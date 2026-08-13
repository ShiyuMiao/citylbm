#!/usr/bin/env python3
"""Validate the Rhino/GHA manual load manifest contract without claiming a load."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
RHINO_LOAD_GATE = RESULTS_DIR / "rhino_gha_load_gate.json"
EVIDENCE_KIT = RESULTS_DIR / "casee_rhino_load_evidence_kit.json"
TEMPLATE = RESULTS_DIR / "rhino_gha_load_manifest.template.json"
MANUAL_MANIFEST = RESULTS_DIR / "rhino_gha_load_manifest.json"
OUT_JSON = RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json"
OUT_CSV = RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.csv"
OUT_MD = RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.md"

REQUIRED_FIELDS = [
    "checked_at",
    "operator",
    "rhino_version",
    "grasshopper_version",
    "observed_plugin_version",
    "observed_assembly_version",
    "observed_gha_sha256",
    "evidence_artifacts",
    "notes",
]
PLACEHOLDER_MARKERS = [
    "paste ",
    "manual-operator-name",
    "YYYY-MM-DD",
    "template",
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


def resolve_artifact(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def field_status(manifest: Dict[str, Any], *, allow_placeholders: bool) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for field in REQUIRED_FIELDS:
        value = manifest.get(field)
        present = value not in (None, "", [])
        text = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value or "")
        has_placeholder = any(marker in text for marker in PLACEHOLDER_MARKERS)
        preview = " ".join(text.split())[:160].rstrip()
        rows.append(
            {
                "field": field,
                "present": present,
                "placeholder_allowed": allow_placeholders,
                "placeholder_detected": has_placeholder,
                "passes": present and (allow_placeholders or not has_placeholder),
                "value_preview": preview,
            }
        )
    return rows


def evidence_artifact_status(manifest: Dict[str, Any], *, require_exists: bool) -> List[Dict[str, Any]]:
    values = manifest.get("evidence_artifacts") if isinstance(manifest.get("evidence_artifacts"), list) else []
    rows: List[Dict[str, Any]] = []
    for value in values:
        path = resolve_artifact(str(value))
        rows.append(
            {
                "artifact": str(value),
                "resolved_path": str(path),
                "exists": path.exists(),
                "required_to_exist": require_exists,
                "passes": path.exists() or not require_exists,
            }
        )
    return rows


def build_payload() -> Dict[str, Any]:
    plugin = read_json(PLUGIN_IDENTITY_GATE)
    rhino_gate = read_json(RHINO_LOAD_GATE)
    kit = read_json(EVIDENCE_KIT)
    template = read_json(TEMPLATE)
    manual = read_json(MANUAL_MANIFEST)
    expected_version = str(plugin.get("plugin_public_version") or kit.get("expected_plugin_public_version") or "")
    expected_sha = str(plugin.get("tracked_gha_sha256") or kit.get("expected_tracked_gha_sha256") or "")
    template_fields = field_status(template, allow_placeholders=True)
    manual_fields = field_status(manual, allow_placeholders=False) if manual else []
    template_artifacts = evidence_artifact_status(template, require_exists=False)
    manual_artifacts = evidence_artifact_status(manual, require_exists=True) if manual else []
    manual_present = MANUAL_MANIFEST.exists()
    manual_claim_ready = bool(
        manual_present
        and manual
        and all(row["passes"] for row in manual_fields)
        and all(row["passes"] for row in manual_artifacts)
        and manual.get("observed_plugin_version") == expected_version
        and str(manual.get("observed_gha_sha256", "")).lower() == expected_sha.lower()
    )
    checks = {
        "plugin_identity_gate_passed": plugin.get("plugin_identity_gate_passed") is True,
        "evidence_kit_ready": kit.get("rhino_load_evidence_kit_ready") is True,
        "template_exists": TEMPLATE.exists(),
        "template_required_fields_present": bool(template_fields) and all(row["present"] for row in template_fields),
        "template_allows_placeholders_only": bool(template_fields) and all(row["passes"] for row in template_fields),
        "template_lists_evidence_artifacts": bool(template_artifacts),
        "manual_manifest_absent_or_schema_checked": (not manual_present) or bool(manual_fields),
        "manual_manifest_claim_ready": manual_claim_ready,
        "rhino_load_gate_fail_closed_until_manual_ready": (
            bool(rhino_gate.get("rhino_loaded_new_gha")) is False
            or manual_claim_ready
        ),
        "formal_accuracy_claim_not_supported": True,
    }
    schema_contract_passed = (
        checks["plugin_identity_gate_passed"]
        and checks["template_exists"]
        and checks["template_required_fields_present"]
        and checks["template_allows_placeholders_only"]
        and checks["template_lists_evidence_artifacts"]
        and checks["manual_manifest_absent_or_schema_checked"]
        and checks["rhino_load_gate_fail_closed_until_manual_ready"]
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "rhino_load_manifest_schema_gate_passed": schema_contract_passed,
        "schema_contract_passed": schema_contract_passed,
        "manual_manifest_present": manual_present,
        "manual_manifest_claim_ready": manual_claim_ready,
        "claim_readiness": "author_input_needed_manual_rhino_load_manifest"
        if schema_contract_passed and not manual_claim_ready
        else ("paper_ready_rhino_load_manifest_schema" if manual_claim_ready else "blocked_rhino_load_manifest_schema"),
        "expected_plugin_public_version": expected_version,
        "expected_tracked_gha_sha256": expected_sha,
        "template_path": rel(TEMPLATE),
        "manual_manifest_path": rel(MANUAL_MANIFEST),
        "template_field_status": template_fields,
        "manual_field_status": manual_fields,
        "template_evidence_artifacts": template_artifacts,
        "manual_evidence_artifacts": manual_artifacts,
        "checks": checks,
        "formal_accuracy_claim_supported": False,
        "rhino_loaded_new_gha": bool(rhino_gate.get("rhino_loaded_new_gha")),
        "boundary": (
            "This gate validates the Rhino/GHA manual load manifest schema and evidence-file contract only. "
            "It does not create manual evidence, prove Rhino loaded the plugin, run CFD, improve official z=2 m "
            "metrics, or permit formal v0.4.0."
        ),
    }


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    rows: List[Dict[str, Any]] = []
    for row in payload["template_field_status"]:
        rows.append({"scope": "template_field", **row})
    for row in payload["manual_field_status"]:
        rows.append({"scope": "manual_field", **row})
    for row in payload["template_evidence_artifacts"]:
        rows.append(
            {
                "scope": "template_evidence",
                "field": "evidence_artifacts",
                "present": True,
                "placeholder_allowed": True,
                "placeholder_detected": False,
                "passes": row["passes"],
                "value_preview": row["artifact"],
            }
        )
    for row in payload["manual_evidence_artifacts"]:
        rows.append(
            {
                "scope": "manual_evidence",
                "field": "evidence_artifacts",
                "present": row["exists"],
                "placeholder_allowed": False,
                "placeholder_detected": False,
                "passes": row["passes"],
                "value_preview": row["artifact"],
            }
        )
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scope",
                "field",
                "present",
                "placeholder_allowed",
                "placeholder_detected",
                "passes",
                "value_preview",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Rhino/GHA Load Manifest Schema Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Schema gate passed: {payload['rhino_load_manifest_schema_gate_passed']}",
        f"- Manual manifest present: {payload['manual_manifest_present']}",
        f"- Manual manifest claim-ready: {payload['manual_manifest_claim_ready']}",
        f"- Rhino loaded new GHA: {payload['rhino_loaded_new_gha']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        "",
        "## Checks",
        "",
        "| check | passed |",
        "|---|---:|",
    ]
    for key, value in payload["checks"].items():
        lines.append(f"| `{key}` | {value} |")
    lines += [
        "",
        "## Required Template Fields",
        "",
        "| field | present | placeholder allowed | passes |",
        "|---|---:|---:|---:|",
    ]
    for row in payload["template_field_status"]:
        lines.append(f"| `{row['field']}` | {row['present']} | {row['placeholder_allowed']} | {row['passes']} |")
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload)
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "rhino_load_manifest_schema_gate_passed": payload["rhino_load_manifest_schema_gate_passed"],
                "manual_manifest_present": payload["manual_manifest_present"],
                "manual_manifest_claim_ready": payload["manual_manifest_claim_ready"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["rhino_load_manifest_schema_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
