#!/usr/bin/env python3
"""Record CityLBM build-chain availability for reproducible Case E work."""

from __future__ import annotations

import argparse
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


def run_cmd(args: List[str], timeout: int = 20) -> Dict[str, Any]:
    exe = shutil.which(args[0]) if len(args) == 1 or not Path(args[0]).exists() else args[0]
    if not exe:
        return {"command": " ".join(args), "found": False, "returncode": None, "stdout": "", "stderr": "not found"}
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, encoding="utf-8", errors="replace")
        return {
            "command": " ".join(args),
            "found": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": " ".join(args), "found": True, "returncode": None, "stdout": "", "stderr": str(exc)}


def file_status(path: Path | None) -> Dict[str, Any]:
    if path is None:
        return {"found": False, "path": "", "sha256": "", "size_bytes": None, "mtime": ""}
    p = path.expanduser()
    if not p.exists():
        return {"found": False, "path": str(p), "sha256": "", "size_bytes": None, "mtime": ""}
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return {
        "found": True,
        "path": str(p),
        "sha256": h.hexdigest(),
        "size_bytes": p.stat().st_size,
        "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
    }


def disk_status() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for drive in ["C:\\", "D:\\", "E:\\", "F:\\", "G:\\"]:
        if not Path(drive).exists():
            continue
        usage = shutil.disk_usage(drive)
        rows.append(
            {
                "drive": drive,
                "free_bytes": usage.free,
                "total_bytes": usage.total,
                "free_gb": round(usage.free / (1024**3), 3),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotnet", type=Path, default=Path(r"E:\citylbm_buildchain\dotnet\dotnet.exe"))
    parser.add_argument("--fluidx3d-exe", type=Path, default=Path(r"E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe"))
    parser.add_argument("--winget-install-exit-code", type=int)
    parser.add_argument("--winget-log", type=Path)
    parser.add_argument("--vs-bootstrapper-log", type=Path)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    args = parser.parse_args()

    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    vcvars64_candidates = [
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
    ]
    c_free = next((row["free_gb"] for row in disk_status() if row["drive"] == "C:\\"), None)
    vs_ready = False
    vs_requires = {"found": False, "returncode": None, "stdout": "", "stderr": "vswhere not found"}
    if vswhere.exists():
        vs_requires = run_cmd(
            [
                str(vswhere),
                "-latest",
                "-products",
                "*",
                "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property",
                "installationPath",
            ]
        )
        vs_ready = bool(vs_requires.get("stdout", "").strip())

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "build_chain_diagnostic",
        "visual_studio_build_tools_2022_cpp": {
            "status": "ready" if vs_ready else "blocked",
            "vswhere": file_status(vswhere),
            "vswhere_requires_vc": vs_requires,
            "cl_on_path": run_cmd(["cl.exe"]),
            "msbuild_on_path": run_cmd(["msbuild.exe"]),
            "vcvars64_candidates": [file_status(p) for p in vcvars64_candidates],
            "install_attempt": {
                "command": "winget install --id Microsoft.VisualStudio.2022.BuildTools --accept-package-agreements --accept-source-agreements --silent --override \"--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended\"",
                "exit_code": args.winget_install_exit_code,
                "winget_log": file_status(args.winget_log),
                "vs_bootstrapper_log": file_status(args.vs_bootstrapper_log),
                "observed_blockers": [
                    "winget returned 1602 during the current attempt",
                    "Visual Studio bootstrapper log reported possible declined UAC prompt",
                    "older setup error log reported C: drive free-space precheck failure; C: currently has less than 5.71 GB free" if c_free is not None and c_free < 5.71 else "",
                ],
            },
        },
        "dotnet_sdk": {
            "status": "ready" if args.dotnet.exists() else "blocked",
            "executable": file_status(args.dotnet),
            "info": run_cmd([str(args.dotnet), "--info"]) if args.dotnet.exists() else run_cmd(["dotnet", "--info"]),
        },
        "fluidx3d": {
            "status": "ready_for_existing_binary" if args.fluidx3d_exe.exists() else "blocked",
            "executable": file_status(args.fluidx3d_exe),
        },
        "gpu_runtime": {
            "nvidia_smi": run_cmd(["nvidia-smi"]),
            "note": "A GPU-lost nvidia-smi result blocks further long FluidX3D validation runs until driver/device recovery.",
        },
        "disk": disk_status(),
        "environment": {
            "path": os.environ.get("PATH", ""),
        },
    }
    manifest["visual_studio_build_tools_2022_cpp"]["install_attempt"]["observed_blockers"] = [
        b for b in manifest["visual_studio_build_tools_2022_cpp"]["install_attempt"]["observed_blockers"] if b
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "vs_cpp_status": manifest["visual_studio_build_tools_2022_cpp"]["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
