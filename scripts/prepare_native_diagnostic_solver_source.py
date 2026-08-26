#!/usr/bin/env python3
"""Clone a FluidX3D source tree for short diagnostic builds.

The clone intentionally excludes old binaries and CFD outputs so a failed build
cannot accidentally run a stale executable from a previous validation attempt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


SKIP_DIR_NAMES = {
    ".git",
    ".citylbm_backup",
    "bin",
    "obj",
    "output",
    "temp",
    "native_source_backups",
    "__pycache__",
}
SKIP_DIR_PREFIXES = ("output_",)
SKIP_SUFFIXES = {".exe", ".dll", ".pdb", ".ilk", ".obj", ".vtk", ".vtu", ".pvtu", ".pvd"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clone a native FluidX3D source tree for diagnostic canary builds.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--out-source-root", required=True)
    parser.add_argument("--manifest-out", default="")
    parser.add_argument("--platform-toolset", default="v143")
    parser.add_argument("--allow-existing", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    for part in rel.parts:
        lower = part.lower()
        if lower in SKIP_DIR_NAMES or lower.startswith(SKIP_DIR_PREFIXES):
            return True
    return path.is_file() and path.suffix.lower() in SKIP_SUFFIXES


def copy_source_tree(source: Path, target: Path, allow_existing: bool) -> Dict[str, Any]:
    if not source.is_dir():
        return {"Gate": "fail", "Reasons": ["source_root_missing"], "FilesCopied": 0, "BytesCopied": 0}
    if target.exists() and not allow_existing and any(target.iterdir()):
        return {"Gate": "fail", "Reasons": ["target_source_root_exists"], "FilesCopied": 0, "BytesCopied": 0}

    files_copied = 0
    bytes_copied = 0
    skipped = 0
    for src in source.rglob("*"):
        if should_skip(src, source):
            skipped += 1
            continue
        rel = src.relative_to(source)
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files_copied += 1
        bytes_copied += dst.stat().st_size

    return {
        "Gate": "pass",
        "Reasons": [],
        "FilesCopied": files_copied,
        "BytesCopied": bytes_copied,
        "SkippedItems": skipped,
    }


def patch_platform_toolset(source_root: Path, platform_toolset: str) -> Dict[str, Any]:
    if not platform_toolset.strip():
        return {"Gate": "not_requested", "Reasons": [], "PatchedFiles": []}

    patched: List[Dict[str, Any]] = []
    reasons: List[str] = []
    for project in sorted(source_root.glob("*.vcxproj")):
        before = project.read_text(encoding="utf-8", errors="replace")
        after, count = re.subn(
            r"<PlatformToolset>[^<]+</PlatformToolset>",
            f"<PlatformToolset>{platform_toolset.strip()}</PlatformToolset>",
            before,
        )
        if count == 0:
            reasons.append(f"platform_toolset_missing:{project.name}")
            continue
        if after != before:
            project.write_text(after, encoding="utf-8")
        patched.append(
            {
                "Path": str(project.resolve()),
                "ReplacementCount": count,
                "Changed": after != before,
                "Sha256": sha256(project),
            }
        )

    if not patched and not reasons:
        return {
            "Gate": "not_applicable",
            "Reasons": [],
            "PatchedFiles": [],
            "Note": "No Visual Studio project file was found; skipping platform toolset patch.",
        }
    return {"Gate": "pass" if not reasons else "fail", "Reasons": reasons, "PatchedFiles": patched}


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    out_source_root = Path(args.out_source_root).expanduser().resolve()
    manifest_out = (
        Path(args.manifest_out).expanduser().resolve()
        if args.manifest_out
        else out_source_root / "diagnostic_solver_source_manifest.json"
    )

    reasons: List[str] = []
    copy_result = copy_source_tree(source_root, out_source_root, args.allow_existing)
    reasons.extend(str(reason) for reason in copy_result.get("Reasons", []))
    toolset_result: Dict[str, Any] = {"Gate": "not_run", "Reasons": []}
    if not reasons:
        toolset_result = patch_platform_toolset(out_source_root, args.platform_toolset)
        reasons.extend(str(reason) for reason in toolset_result.get("Reasons", []))

    manifest = {
        "Schema": "citylbm.native_diagnostic_solver_source.v1",
        "GeneratedAtUtc": utc_now(),
        "SourceRoot": str(source_root),
        "DiagnosticSourceRoot": str(out_source_root),
        "PlatformToolset": args.platform_toolset,
        "Copy": copy_result,
        "PlatformToolsetPatch": toolset_result,
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
    }
    write_json(manifest_out, manifest)
    print(f"diagnostic_solver_source_gate={manifest['Gate']}; manifest={manifest_out}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if not reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
