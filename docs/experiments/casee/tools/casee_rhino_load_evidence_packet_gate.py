#!/usr/bin/env python3
"""Create a fail-closed Rhino/GHA manual load evidence packet gate."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
PLUGIN_IDENTITY_GATE = RESULTS_DIR / "plugin_identity_gate.json"
GHA_INSTALL_AUDIT = RESULTS_DIR / "citylbm_gha_install_audit.json"
RHINO_LOAD_GATE = RESULTS_DIR / "rhino_gha_load_gate.json"
EVIDENCE_KIT = RESULTS_DIR / "casee_rhino_load_evidence_kit.json"
SCHEMA_GATE = RESULTS_DIR / "rhino_gha_load_manifest_schema_gate.json"
MANUAL_MANIFEST = RESULTS_DIR / "rhino_gha_load_manifest.json"
EXPECTED_MANIFEST = RESULTS_DIR / "rhino_gha_load_manifest.expected.json"
OUT_JSON = RESULTS_DIR / "casee_rhino_load_evidence_packet_gate.json"
OUT_CSV = RESULTS_DIR / "casee_rhino_load_evidence_packet_gate.csv"
OUT_MD = RESULTS_DIR / "casee_rhino_load_evidence_packet_gate.md"

REQUIRED_OUTPUTS = [
    OUT_JSON,
    OUT_CSV,
    OUT_MD,
    EXPECTED_MANIFEST,
]

REQUIRED_MANUAL_FIELDS = [
    "checked_at",
    "operator",
    "rhino_version",
    "grasshopper_version",
    "observed_plugin_version",
    "observed_assembly_version",
    "observed_gha_path",
    "observed_gha_sha256",
    "evidence_artifacts",
    "notes",
]

EXPECTED_EVIDENCE_ARTIFACTS = [
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_screenshot.png",
    "docs/experiments/casee/results/rhino_loaded_citylbm_v040rc_log.txt",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_artifact(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def expected_manifest_payload(expected_version: str, expected_sha: str, expected_gha_path: str) -> Dict[str, Any]:
    return {
        "packet_generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "purpose": "Expected values and required manual evidence for a real Rhino/Grasshopper CityLBM load check.",
        "manual_manifest_path": rel(MANUAL_MANIFEST),
        "required_fields": REQUIRED_MANUAL_FIELDS,
        "expected_plugin_public_version": expected_version,
        "expected_assembly_version": "0.4.0.0",
        "expected_gha_path": expected_gha_path,
        "expected_gha_sha256": expected_sha,
        "required_evidence_artifacts": EXPECTED_EVIDENCE_ARTIFACTS,
        "required_grasshopper_observation": [
            "CityLBM Plugin Identity component is present in the Grasshopper canvas.",
            "Plugin Identity output reports the loaded public version.",
            "Plugin Identity output reports the loaded GHA path.",
            "Plugin Identity output reports the loaded GHA SHA256.",
            "Reported SHA256 matches CityLBM/bin/CityLBM.gha.",
        ],
        "post_capture_commands": [
            "python docs/experiments/casee/tools/rhino_gha_load_gate.py",
            "python docs/experiments/casee/tools/rhino_gha_load_manifest_schema_gate.py",
            "python docs/experiments/casee/tools/casee_audit.py --release-target v0.4.0",
            "python docs/experiments/casee/tools/reproducibility_suite.py --release-target v0.4.0",
        ],
        "forbidden_interpretation": [
            "Do not treat this expected manifest as proof that Rhino loaded CityLBM.",
            "Do not use Rhino/GHA load evidence as CFD accuracy evidence.",
            "Do not claim formal v0.4.0 until official z=2 m raw_trilinear metrics pass.",
        ],
    }


def manual_manifest_status(manual: Dict[str, Any], expected_version: str, expected_sha: str) -> Dict[str, Any]:
    present = MANUAL_MANIFEST.exists()
    missing_fields = [field for field in REQUIRED_MANUAL_FIELDS if not manual.get(field)]
    artifacts = manual.get("evidence_artifacts") if isinstance(manual.get("evidence_artifacts"), list) else []
    missing_artifacts = [
        rel(path) if str(path).startswith(str(ROOT)) else str(path)
        for path in (resolve_artifact(str(item)) for item in artifacts)
        if not path.exists()
    ]
    version_matches = bool(expected_version) and manual.get("observed_plugin_version") == expected_version
    sha_matches = bool(expected_sha) and str(manual.get("observed_gha_sha256", "")).lower() == expected_sha.lower()
    claim_ready = bool(present and not missing_fields and artifacts and not missing_artifacts and version_matches and sha_matches)
    return {
        "manual_manifest_present": present,
        "missing_manual_fields": missing_fields,
        "listed_evidence_artifacts": artifacts,
        "missing_evidence_artifacts": missing_artifacts,
        "observed_plugin_version_matches_expected": version_matches,
        "observed_gha_sha256_matches_expected": sha_matches,
        "manual_evidence_claim_ready": claim_ready,
    }


def checklist_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = payload["checks"]
    manual = payload["manual_manifest_status"]
    rows = [
        {
            "item_id": "RGLP-A01",
            "stage": "automated_prerequisite",
            "requirement": "Plugin Identity gate passed for the packaged CityLBM GHA.",
            "status": checks["plugin_identity_gate_passed"],
            "evidence_path": rel(PLUGIN_IDENTITY_GATE),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Software identity prerequisite.",
            "limitations": "Does not prove Rhino loaded the plugin.",
        },
        {
            "item_id": "RGLP-A02",
            "stage": "automated_prerequisite",
            "requirement": "Tracked GHA exists and has a SHA256 expected value.",
            "status": checks["tracked_gha_sha_available"],
            "evidence_path": rel(TRACKED_GHA),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Exact plugin artifact traceability.",
            "limitations": "Does not prove the artifact was loaded by Rhino.",
        },
        {
            "item_id": "RGLP-A03",
            "stage": "automated_prerequisite",
            "requirement": "Current tracked GHA is staged in a Grasshopper Libraries directory.",
            "status": checks["gha_install_audit_passed"],
            "evidence_path": rel(GHA_INSTALL_AUDIT),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Install-staging prerequisite.",
            "limitations": "Staging is not process-load evidence.",
        },
        {
            "item_id": "RGLP-A04",
            "stage": "automated_prerequisite",
            "requirement": "Rhino manual evidence kit is ready.",
            "status": checks["rhino_evidence_kit_ready"],
            "evidence_path": rel(EVIDENCE_KIT),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Operator handoff protocol.",
            "limitations": "Does not create manual evidence.",
        },
        {
            "item_id": "RGLP-A05",
            "stage": "automated_prerequisite",
            "requirement": "Manual manifest schema gate passes fail-closed.",
            "status": checks["schema_gate_passed"],
            "evidence_path": rel(SCHEMA_GATE),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Reviewer-facing manifest contract.",
            "limitations": "Schema evidence is not a real Rhino session.",
        },
        {
            "item_id": "RGLP-M01",
            "stage": "manual_required",
            "requirement": "Create rhino_gha_load_manifest.json from a real Rhino/Grasshopper session.",
            "status": manual["manual_manifest_present"],
            "evidence_path": rel(MANUAL_MANIFEST),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Required before claiming loaded new GHA.",
            "limitations": "Absent on this machine during automated suite execution.",
        },
        {
            "item_id": "RGLP-M02",
            "stage": "manual_required",
            "requirement": "Screenshot/log artifacts listed in the manual manifest exist.",
            "status": bool(manual["listed_evidence_artifacts"]) and not manual["missing_evidence_artifacts"],
            "evidence_path": "; ".join(EXPECTED_EVIDENCE_ARTIFACTS),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Reviewer-visible proof of loaded component outputs.",
            "limitations": "Evidence must show path, version, and SHA256, not only a toolbar icon.",
        },
        {
            "item_id": "RGLP-M03",
            "stage": "manual_required",
            "requirement": "Observed plugin version and GHA SHA256 match expected values.",
            "status": manual["observed_plugin_version_matches_expected"] and manual["observed_gha_sha256_matches_expected"],
            "evidence_path": rel(MANUAL_MANIFEST),
            "required_for_rhino_load_claim": True,
            "required_for_formal_release": True,
            "paper_use": "Prevents old-GHA evidence contamination.",
            "limitations": "Cannot be satisfied by a template.",
        },
        {
            "item_id": "RGLP-B01",
            "stage": "boundary",
            "requirement": "Formal CFD accuracy remains unsupported by this packet.",
            "status": checks["formal_accuracy_claim_not_supported"],
            "evidence_path": rel(RHINO_LOAD_GATE),
            "required_for_rhino_load_claim": False,
            "required_for_formal_release": False,
            "paper_use": "Limitations and protocol-risk text.",
            "limitations": "Official z=2 m raw_trilinear metrics are unchanged.",
        },
    ]
    return rows


def build_payload() -> Dict[str, Any]:
    plugin = read_json(PLUGIN_IDENTITY_GATE)
    install = read_json(GHA_INSTALL_AUDIT)
    rhino_gate = read_json(RHINO_LOAD_GATE)
    kit = read_json(EVIDENCE_KIT)
    schema = read_json(SCHEMA_GATE)
    manual = read_json(MANUAL_MANIFEST)
    expected_version = str(plugin.get("plugin_public_version") or kit.get("expected_plugin_public_version") or "0.4.0-rc")
    expected_sha = str(plugin.get("tracked_gha_sha256") or kit.get("expected_tracked_gha_sha256") or sha256(TRACKED_GHA))
    staged_path = str((install.get("recommended_target") or {}).get("path") or "")
    expected_gha_path = staged_path or rel(TRACKED_GHA)
    expected_payload = expected_manifest_payload(expected_version, expected_sha, expected_gha_path)
    manual_status = manual_manifest_status(manual, expected_version, expected_sha)
    checks = {
        "plugin_identity_gate_passed": plugin.get("plugin_identity_gate_passed") is True,
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "tracked_gha_sha_available": bool(expected_sha),
        "gha_install_audit_passed": install.get("install_audit_passed") is True,
        "rhino_evidence_kit_ready": kit.get("rhino_load_evidence_kit_ready") is True,
        "schema_gate_passed": schema.get("rhino_load_manifest_schema_gate_passed") is True,
        "rhino_load_gate_fail_closed_or_manual_ready": (
            rhino_gate.get("rhino_loaded_new_gha") is False or manual_status["manual_evidence_claim_ready"]
        ),
        "formal_accuracy_claim_not_supported": True,
    }
    packet_ready = (
        checks["plugin_identity_gate_passed"]
        and checks["tracked_gha_exists"]
        and checks["tracked_gha_sha_available"]
        and checks["gha_install_audit_passed"]
        and checks["rhino_evidence_kit_ready"]
        and checks["schema_gate_passed"]
        and checks["rhino_load_gate_fail_closed_or_manual_ready"]
        and checks["formal_accuracy_claim_not_supported"]
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "rhino_load_evidence_packet_gate_passed": packet_ready,
        "manual_rhino_load_claim_ready": manual_status["manual_evidence_claim_ready"],
        "rhino_loaded_new_gha": bool(rhino_gate.get("rhino_loaded_new_gha")),
        "claim_readiness": "author_input_needed_manual_rhino_load_packet"
        if packet_ready and not manual_status["manual_evidence_claim_ready"]
        else ("paper_ready_rhino_load_identity_packet" if manual_status["manual_evidence_claim_ready"] else "blocked_rhino_load_evidence_packet"),
        "expected_manifest_path": rel(EXPECTED_MANIFEST),
        "manual_manifest_path": rel(MANUAL_MANIFEST),
        "expected_plugin_public_version": expected_version,
        "expected_gha_sha256": expected_sha,
        "expected_gha_path": expected_gha_path,
        "manual_manifest_status": manual_status,
        "checks": checks,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "expected_manifest": expected_payload,
        "boundary": (
            "This gate packages the manual Rhino/GHA load evidence requirements and expected values. "
            "It does not prove Rhino loaded the plugin unless a real manual manifest and evidence artifacts pass, "
            "does not run FluidX3D, and does not improve official Case E z=2 m metrics."
        ),
    }
    payload["checklist_rows"] = checklist_rows(payload)
    return payload


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = [
        "item_id",
        "stage",
        "requirement",
        "status",
        "evidence_path",
        "required_for_rhino_load_claim",
        "required_for_formal_release",
        "paper_use",
        "limitations",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Rhino/GHA Load Evidence Packet Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Packet gate passed: {payload['rhino_load_evidence_packet_gate_passed']}",
        f"- Manual Rhino load claim-ready: {payload['manual_rhino_load_claim_ready']}",
        f"- Rhino loaded new GHA: {payload['rhino_loaded_new_gha']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Expected plugin version: `{payload['expected_plugin_public_version']}`",
        f"- Expected GHA SHA256: `{payload['expected_gha_sha256']}`",
        "",
        "## Checklist",
        "",
        "| item | stage | status | requirement |",
        "|---|---|---:|---|",
    ]
    for row in payload["checklist_rows"]:
        lines.append(f"| `{row['item_id']}` | `{row['stage']}` | {row['status']} | {row['requirement']} |")
    missing_fields = payload["manual_manifest_status"]["missing_manual_fields"]
    missing_artifacts = payload["manual_manifest_status"]["missing_evidence_artifacts"]
    if missing_fields:
        lines += ["", "Missing manual manifest fields:"]
        lines.extend(f"- `{item}`" for item in missing_fields)
    if missing_artifacts:
        lines += ["", "Missing manual evidence artifacts:"]
        lines.extend(f"- `{item}`" for item in missing_artifacts)
    lines += [
        "",
        "## Expected Manifest",
        "",
        f"- Expected manifest: `{payload['expected_manifest_path']}`",
        f"- Manual manifest: `{payload['manual_manifest_path']}`",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    EXPECTED_MANIFEST.write_text(json.dumps(payload["expected_manifest"], indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["checklist_rows"])
    write_markdown(OUT_MD, payload)
    outputs_exist = all(path.exists() for path in REQUIRED_OUTPUTS)
    payload["checks"]["required_packet_outputs_exist"] = outputs_exist
    payload["rhino_load_evidence_packet_gate_passed"] = bool(payload["rhino_load_evidence_packet_gate_passed"] and outputs_exist)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["checklist_rows"])
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "rhino_load_evidence_packet_gate_passed": payload["rhino_load_evidence_packet_gate_passed"],
                "manual_rhino_load_claim_ready": payload["manual_rhino_load_claim_ready"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if payload["rhino_load_evidence_packet_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
