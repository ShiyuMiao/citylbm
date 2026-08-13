#!/usr/bin/env python3
"""Create and audit a deterministic lightweight release bundle for Case E."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
RELEASE_ASSET_MANIFEST = RESULTS_DIR / "casee_release_asset_manifest.json"
OUT_ZIP = RESULTS_DIR / "casee_release_bundle.zip"
OUT_JSON = RESULTS_DIR / "casee_release_bundle_manifest.json"
OUT_CSV = RESULTS_DIR / "casee_release_bundle_manifest.csv"
OUT_MD = RESULTS_DIR / "casee_release_bundle_manifest.md"
RAW_EXTENSIONS = {".vtk", ".vti", ".vtp", ".vtu", ".stl", ".3dm"}
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
DYNAMIC_RESULT_PREFIXES = (
    "docs/experiments/casee/results/",
    "academic-paper-writer/paper-drafts/",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def selected_assets(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [row for row in manifest.get("assets", []) if row.get("include_in_release_upload") is True]
    return sorted(rows, key=lambda row: str(row.get("path", "")))


def build_zip(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    bundle_rows: List[Dict[str, Any]] = []
    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for row in rows:
            path_text = str(row.get("path", ""))
            full = ROOT / path_text
            data = full.read_bytes()
            digest = sha256_bytes(data)
            strict_match_required = not any(path_text.startswith(prefix) for prefix in DYNAMIC_RESULT_PREFIXES)
            info = zipfile.ZipInfo(path_text, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
            bundle_rows.append(
                {
                    "path": path_text,
                    "size_bytes": len(data),
                    "sha256": digest,
                    "manifest_sha256": row.get("sha256", ""),
                    "sha256_matches_manifest": digest == str(row.get("sha256", "")),
                    "strict_manifest_match_required": strict_match_required,
                    "asset_kind": row.get("asset_kind", ""),
                }
            )
    return bundle_rows


def write_csv(rows: List[Dict[str, Any]]) -> None:
    fields = [
        "path",
        "asset_kind",
        "size_bytes",
        "sha256",
        "manifest_sha256",
        "sha256_matches_manifest",
        "strict_manifest_match_required",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def write_md(payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Case E Release Bundle Gate",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Bundle gate passed: {summary['casee_release_bundle_gate_passed']}",
        f"- Recommended tag: `{summary['recommended_tag']}`",
        f"- Formal release allowed: {summary['formal_release_allowed']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Bundle path: `{summary['bundle_path']}`",
        f"- Bundle size bytes: {summary['bundle_size_bytes']}",
        f"- Bundle SHA256: `{summary['bundle_sha256']}`",
        f"- Bundled assets: {summary['bundled_asset_count']}",
        f"- Raw/large files excluded: {summary['raw_or_large_files_excluded']}",
        "",
        "## Bundled Assets",
        "",
        "| path | kind | size | sha256 ok |",
        "|---|---|---:|---:|",
    ]
    for row in payload["assets"]:
        lines.append(
            f"| `{row['path']}` | {row['asset_kind']} | {row['size_bytes']} | {row['sha256_matches_manifest']} |"
        )
    lines += ["", "## Boundary", "", summary["boundary"]]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    manifest = read_json(RELEASE_ASSET_MANIFEST)
    manifest_summary = manifest.get("summary", {})
    rows = selected_assets(manifest)
    missing = [row for row in rows if not (ROOT / str(row.get("path", ""))).exists()]
    forbidden = [
        row
        for row in rows
        if Path(str(row.get("path", ""))).suffix.lower() in RAW_EXTENSIONS
        or str(row.get("release_asset_role", "")) in {"external_reference_hash_only", "optional_log_asset"}
    ]
    bundle_rows: List[Dict[str, Any]] = []
    if not missing and not forbidden:
        bundle_rows = build_zip(rows)
    sha_matches = all(row.get("sha256_matches_manifest") is True for row in bundle_rows)
    strict_sha_matches = all(
        row.get("sha256_matches_manifest") is True
        for row in bundle_rows
        if row.get("strict_manifest_match_required") is True
    )
    bundle_exists = OUT_ZIP.exists()
    passed = (
        manifest_summary.get("release_asset_manifest_passed") is True
        and bool(rows)
        and not missing
        and not forbidden
        and bundle_exists
        and strict_sha_matches
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_release_bundle; not accuracy evidence",
        "casee_release_bundle_gate_passed": passed,
        "recommended_tag": manifest_summary.get("recommended_tag"),
        "formal_release_allowed": manifest_summary.get("formal_release_allowed"),
        "formal_accuracy_claim_supported": False,
        "bundle_path": rel(OUT_ZIP),
        "bundle_size_bytes": OUT_ZIP.stat().st_size if bundle_exists else 0,
        "bundle_sha256": sha256(OUT_ZIP) if bundle_exists else "",
        "bundled_asset_count": len(bundle_rows),
        "manifest_upload_asset_count": manifest_summary.get("upload_asset_count"),
        "missing_asset_count": len(missing),
        "forbidden_asset_count": len(forbidden),
        "all_bundled_hashes_match_manifest": sha_matches,
        "all_strict_bundled_hashes_match_manifest": strict_sha_matches,
        "dynamic_result_hash_mismatch_count": sum(
            1
            for row in bundle_rows
            if row.get("strict_manifest_match_required") is False
            and row.get("sha256_matches_manifest") is not True
        ),
        "raw_or_large_files_excluded": not forbidden,
        "zip_timestamp_utc": "2026-01-01T00:00:00Z",
        "boundary": (
            "This bundle packages the curated lightweight release assets only. It excludes raw geometry, VTK, "
            "and hash-only external references, and does not create a GitHub Release, add CFD output, or support "
            "formal accuracy claims."
        ),
    }
    payload = {"summary": summary, "assets": bundle_rows, "missing_assets": missing, "forbidden_assets": forbidden}
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(bundle_rows)
    write_md(payload)
    print(
        json.dumps(
            {
                "casee_release_bundle_gate_passed": passed,
                "bundle_path": rel(OUT_ZIP),
                "bundle_sha256": summary["bundle_sha256"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
