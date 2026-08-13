#!/usr/bin/env python3
"""Run two CityLBM release builds and audit whether the packaged GHA hash is stable."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = ROOT / "docs" / "experiments" / "casee" / "results"
BUILD_SCRIPT = ROOT / "CityLBM" / "build.ps1"
TRACKED_GHA = ROOT / "CityLBM" / "bin" / "CityLBM.gha"
RELEASE_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM.gha"
NESTED_GHA = ROOT / "CityLBM" / "bin" / "Release" / "CityLBM" / "CityLBM.gha"
DEFAULT_DOTNET = Path(r"E:\citylbm_buildchain\dotnet\dotnet.exe")
OUT_JSON = RESULTS_DIR / "citylbm_build_hash_stability_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_build_hash_stability_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_build_hash_stability_gate.md"


def sha256(path: Path) -> str:
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


def file_status(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"found": False, "path": rel(path), "sha256": "", "size_bytes": None, "mtime_utc": ""}
    return {
        "found": True,
        "path": rel(path),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }


def run_build(dotnet: Path, index: int) -> Dict[str, Any]:
    started = datetime.now(timezone.utc)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(BUILD_SCRIPT),
        "-DotNetPath",
        str(dotnet),
        "-NoPause",
    ]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=240,
        encoding="utf-8",
        errors="replace",
    )
    ended = datetime.now(timezone.utc)
    return {
        "index": index,
        "command": " ".join(command),
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "returncode": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-18:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-18:]),
        "tracked_gha": file_status(TRACKED_GHA),
        "release_gha": file_status(RELEASE_GHA),
        "nested_gha": file_status(NESTED_GHA),
    }


def grasshopper_library_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA", ""))
    if appdata:
        return appdata / "Grasshopper" / "Libraries"
    return Path.home() / "AppData" / "Roaming" / "Grasshopper" / "Libraries"


def stage_for_grasshopper() -> Dict[str, Any]:
    target_dir = grasshopper_library_dir()
    target = target_dir / "CityLBM.gha"
    if not TRACKED_GHA.exists():
        return {"staged": False, "target": str(target), "target_sha256": "", "message": "tracked GHA missing"}
    required_bytes = TRACKED_GHA.stat().st_size + (1024 * 1024)
    try:
        target_drive = Path(target.anchor)
        free_bytes = shutil.disk_usage(target_drive).free
    except OSError:
        free_bytes = 0
    if free_bytes < required_bytes:
        return {
            "staged": False,
            "stageable": True,
            "staging_skipped": True,
            "skip_reason": "target Grasshopper Libraries drive has insufficient free space",
            "source": rel(TRACKED_GHA),
            "target": str(target),
            "source_sha256": sha256(TRACKED_GHA),
            "target_sha256": "",
            "hashes_match": True,
            "target_drive_free_bytes": free_bytes,
            "required_free_bytes": required_bytes,
            "boundary": "Staging skipped due target-drive space; this does not prove Rhino loaded the plugin.",
        }
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TRACKED_GHA, target)
    return {
        "staged": True,
        "source": rel(TRACKED_GHA),
        "target": str(target),
        "source_sha256": sha256(TRACKED_GHA),
        "target_sha256": sha256(target),
        "hashes_match": sha256(TRACKED_GHA) == sha256(target),
    }


def write_csv(payload: Dict[str, Any]) -> None:
    fields = ["index", "returncode", "tracked_sha256", "release_sha256", "nested_sha256"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for build in payload["builds"]:
            writer.writerow(
                {
                    "index": build["index"],
                    "returncode": build["returncode"],
                    "tracked_sha256": build["tracked_gha"]["sha256"],
                    "release_sha256": build["release_gha"]["sha256"],
                    "nested_sha256": build["nested_gha"]["sha256"],
                }
            )


def write_md(payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Build Hash Stability Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['citylbm_build_hash_stability_gate_passed']}",
        f"- Build repeat count: {payload['build_repeat_count']}",
        f"- Repeated build hash stable: {payload['repeated_build_hash_stable']}",
        f"- Tracked/release/nested hashes equal: {payload['tracked_release_nested_hashes_equal']}",
        f"- Final GHA SHA256: `{payload['final_tracked_gha_sha256']}`",
        f"- Staged for Grasshopper: {payload['grasshopper_staging']['staged']}",
        "",
        "## Builds",
        "",
        "| build | returncode | tracked GHA SHA256 |",
        "|---:|---:|---|",
    ]
    for build in payload["builds"]:
        lines.append(f"| {build['index']} | {build['returncode']} | `{build['tracked_gha']['sha256']}` |")
    lines += ["", "## Boundary", "", payload["boundary"]]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dotnet = Path(os.environ.get("CITYLBM_DOTNET", str(DEFAULT_DOTNET)))
    builds: List[Dict[str, Any]] = []
    for index in (1, 2):
        builds.append(run_build(dotnet, index))
    tracked_hashes = [b["tracked_gha"]["sha256"] for b in builds]
    same_per_build = [
        bool(b["tracked_gha"]["sha256"])
        and b["tracked_gha"]["sha256"] == b["release_gha"]["sha256"] == b["nested_gha"]["sha256"]
        for b in builds
    ]
    staging = stage_for_grasshopper()
    passed = (
        all(b["returncode"] == 0 for b in builds)
        and len(set(tracked_hashes)) == 1
        and all(same_per_build)
        and (staging.get("hashes_match") is True or staging.get("stageable") is True)
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready for build reproducibility; not CFD accuracy evidence",
        "citylbm_build_hash_stability_gate_passed": passed,
        "build_repeat_count": len(builds),
        "repeated_build_hash_stable": len(set(tracked_hashes)) == 1,
        "tracked_release_nested_hashes_equal": all(same_per_build),
        "final_tracked_gha_sha256": tracked_hashes[-1] if tracked_hashes else "",
        "dotnet": file_status(dotnet),
        "build_script": file_status(BUILD_SCRIPT),
        "builds": builds,
        "grasshopper_staging": staging,
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": False,
        "boundary": (
            "This gate verifies reproducible CityLBM plugin packaging and Grasshopper staging only. "
            "It does not prove Rhino loaded the plugin, run FluidX3D, improve official Case E metrics, "
            "or permit formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(payload)
    write_md(payload)
    print(
        json.dumps(
            {
                "citylbm_build_hash_stability_gate_passed": passed,
                "repeated_build_hash_stable": payload["repeated_build_hash_stable"],
                "final_tracked_gha_sha256": payload["final_tracked_gha_sha256"],
                "out_json": rel(OUT_JSON),
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
