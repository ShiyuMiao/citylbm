#!/usr/bin/env python3
"""Audit the Grasshopper Plugin Identity component used for Rhino load evidence."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
PLUGIN = ROOT / "CityLBM" / "src" / "CityLBMPlugin.cs"
COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Results" / "PluginIdentityComponent.cs"
OUT_JSON = RESULTS_DIR / "citylbm_plugin_identity_component_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_plugin_identity_component_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_plugin_identity_component_gate.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def extract_const(text: str, name: str) -> str:
    match = re.search(rf'const\s+string\s+{name}\s*=\s*"([^"]+)"', text)
    return "" if match is None else match.group(1)


def build_payload() -> Dict[str, Any]:
    plugin_text = read_text(PLUGIN)
    component_text = read_text(COMPONENT)
    public_version = extract_const(plugin_text, "PluginVersion")
    assembly_version = extract_const(plugin_text, "PluginAssemblyVersion")
    checks = {
        "component_source_exists": COMPONENT.exists(),
        "plugin_public_version_exported": "public const string PluginVersion" in plugin_text,
        "plugin_assembly_version_exported": "public const string PluginAssemblyVersion" in plugin_text,
        "component_uses_plugin_version_constant": "CityLBMPlugin.PluginVersion" in component_text,
        "component_uses_assembly_version_constant": "CityLBMPlugin.PluginAssemblyVersion" in component_text,
        "component_outputs_gha_path": 'AddTextParameter("GHA Path"' in component_text,
        "component_outputs_gha_sha256": 'AddTextParameter("GHA SHA256"' in component_text,
        "component_outputs_manifest_template": 'AddTextParameter("Manifest Template"' in component_text,
        "component_outputs_claim_boundary": 'AddTextParameter("Boundary"' in component_text,
        "component_computes_sha256": "SHA256.Create()" in component_text and "ComputeSha256" in component_text,
        "component_manifest_warns_manual_evidence": "Add screenshot/log evidence before using this as rhino_gha_load_manifest.json" in component_text,
        "component_boundary_blocks_accuracy_claims": "not CFD accuracy evidence" in component_text
        and "must not change official AIJ Case E z=2 m metrics" in component_text,
        "component_guid_present": "ComponentGuid" in component_text and "7B5126DD-4C5F-4C27-8E4C-142792314E55" in component_text,
    }
    passed = all(checks.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_software_identity_component" if passed else "blocked_identity_component_gate",
        "plugin_identity_component_gate_passed": passed,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "plugin_public_version": public_version,
        "plugin_assembly_version": assembly_version,
        "component_source_path": rel(COMPONENT),
        "checks": checks,
        "boundary": (
            "This gate checks the Grasshopper component that reports loaded plugin identity for manual Rhino evidence. "
            "It does not prove Rhino loaded the plugin, does not run CFD, and does not improve official Case E metrics."
        ),
    }


def write_csv(path: Path, checks: Dict[str, bool]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "passed"])
        writer.writeheader()
        for key, value in checks.items():
            writer.writerow({"check": key, "passed": value})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Plugin Identity Component Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['plugin_identity_component_gate_passed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Component source: `{payload['component_source_path']}`",
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
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload["checks"])
    write_markdown(OUT_MD, payload)
    print(json.dumps({"plugin_identity_component_gate_passed": payload["plugin_identity_component_gate_passed"], "out_json": str(OUT_JSON)}, indent=2))
    return 0 if payload["plugin_identity_component_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
