#!/usr/bin/env python3
"""Verify CityLBM plugin version identity matches the release-candidate evidence line."""

from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PLUGIN = ROOT / "CityLBM" / "src" / "CityLBMPlugin.cs"
README = ROOT / "README.md"
CITYLBM_README = ROOT / "CityLBM" / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
RELEASE_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha"
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"


def contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(encoding="utf-8", errors="replace")


def extract_const(text: str, name: str) -> str:
    match = re.search(rf'const\s+string\s+{name}\s*=\s*"([^"]+)"', text)
    return "" if match is None else match.group(1)


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    plugin_text = PLUGIN.read_text(encoding="utf-8", errors="replace")
    release_gate = json.loads(RELEASE_GATE.read_text(encoding="utf-8")) if RELEASE_GATE.exists() else {}
    recommended_tag = str(release_gate.get("recommended_tag", "v0.4.0-rc"))
    release_notes = ROOT / "docs" / "releases" / f"{recommended_tag}.md"
    public_version = extract_const(plugin_text, "PluginVersion")
    assembly_version = extract_const(plugin_text, "PluginAssemblyVersion")
    tracked_gha_sha256 = sha256(TRACKED_GHA)
    release_gha_sha256 = sha256(RELEASE_GHA)
    checks = {
        "plugin_public_version_is_rc": public_version == "0.4.0-rc",
        "plugin_assembly_version_is_numeric_v040": assembly_version == "0.4.0.0",
        "plugin_no_old_public_version": '"0.1.0"' not in plugin_text and '"0.1.0.0"' not in plugin_text,
        "tracked_gha_exists": TRACKED_GHA.exists(),
        "release_gha_exists": RELEASE_GHA.exists(),
        "tracked_gha_matches_release_build": bool(tracked_gha_sha256) and tracked_gha_sha256 == release_gha_sha256,
        "root_readme_mentions_paper_gate": contains(README, "paper_evidence_gate.py"),
        "root_readme_mentions_recommended_release_notes": contains(README, f"docs/releases/{recommended_tag}.md"),
        "citylbm_readme_mentions_rc_status": contains(CITYLBM_README, "CityLBM v0.4.0-rc Status"),
        "changelog_has_recommended_tag": contains(CHANGELOG, f"## {recommended_tag}"),
        "release_notes_exist": release_notes.exists(),
        "release_notes_blocks_formal_v040": release_notes.exists() and (
            contains(release_notes, "Formal `v0.4.0` remains blocked")
            or contains(release_notes, "not a formal `v0.4.0` release")
        ),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommended_tag": recommended_tag,
        "plugin_public_version": public_version,
        "plugin_assembly_version": assembly_version,
        "tracked_gha_sha256": tracked_gha_sha256,
        "release_gha_sha256": release_gha_sha256,
        "plugin_identity_gate_passed": all(checks.values()),
        "checks": checks,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready for software identity; not accuracy evidence",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "plugin_identity_gate.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["plugin_identity_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
