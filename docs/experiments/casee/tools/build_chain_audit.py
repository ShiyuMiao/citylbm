#!/usr/bin/env python3
"""Record CityLBM build-chain availability for reproducible Case E work."""

from __future__ import annotations

import argparse
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
OUT_JSON = RESULTS_DIR / "build_chain_manifest.json"
OUT_CSV = RESULTS_DIR / "build_chain_manifest.csv"
OUT_MD = RESULTS_DIR / "build_chain_manifest.md"


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


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def tail_text(path: Path | None, max_lines: int = 80) -> str:
    text = read_text(path)
    if not text:
        return ""
    return "\n".join(text.splitlines()[-max_lines:])


def latest_winget_log() -> Path | None:
    diag_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Packages" / "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe" / "LocalState" / "DiagOutputDir"
    if not diag_dir.exists():
        return None
    candidates = sorted(diag_dir.glob("WinGet-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        text = read_text(path)
        if "Microsoft.VisualStudio.2022.BuildTools" in text or "vs_BuildTools.exe" in text:
            return path
    return candidates[0] if candidates else None


def latest_vs_bootstrapper_log() -> Path | None:
    candidates = [
        Path(os.environ.get("TEMP", "")) / "dd_vs_BuildTools_decompression_log.txt",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "dd_vs_BuildTools_decompression_log.txt",
    ]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        return None
    return sorted(existing, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def log_status(path: Path | None) -> Dict[str, Any]:
    text = read_text(path)
    return {
        **file_status(path),
        "tail": tail_text(path),
        "exit_1602_detected": "1602" in text,
        "uac_declined_detected": "declined UAC" in text or "0x80070642" in text,
        "buildtools_installer_detected": "BuildTools" in text or "vs_BuildTools" in text,
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


def write_csv(path: Path, manifest: Dict[str, Any]) -> None:
    rows = [
        {
            "component": "visual_studio_build_tools_2022_cpp",
            "status": manifest["visual_studio_build_tools_2022_cpp"]["status"],
            "evidence": manifest["visual_studio_build_tools_2022_cpp"]["vswhere_requires_vc"].get("command", ""),
            "limitation": "; ".join(manifest["visual_studio_build_tools_2022_cpp"]["install_attempt"].get("observed_blockers", [])),
        },
        {
            "component": "dotnet_sdk",
            "status": manifest["dotnet_sdk"]["status"],
            "evidence": manifest["dotnet_sdk"]["info"].get("command", ""),
            "limitation": "",
        },
        {
            "component": "citylbm_build_script",
            "status": manifest["citylbm_build_script"]["status"],
            "evidence": manifest["citylbm_build_script"]["smoke_build"].get("command", ""),
            "limitation": manifest["citylbm_build_script"].get("note", ""),
        },
        {
            "component": "mingw_gpp",
            "status": manifest["mingw_gpp"]["status"],
            "evidence": manifest["mingw_gpp"]["version"].get("command", ""),
            "limitation": manifest["mingw_gpp"].get("note", ""),
        },
        {
            "component": "fluidx3d",
            "status": manifest["fluidx3d"]["status"],
            "evidence": manifest["fluidx3d"]["executable"].get("path", ""),
            "limitation": "",
        },
        {
            "component": "gpu_runtime",
            "status": manifest["gpu_runtime"]["status"],
            "evidence": manifest["gpu_runtime"]["nvidia_smi"].get("command", ""),
            "limitation": manifest["gpu_runtime"].get("note", ""),
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["component", "status", "evidence", "limitation"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, manifest: Dict[str, Any]) -> None:
    vs = manifest["visual_studio_build_tools_2022_cpp"]
    dotnet = manifest["dotnet_sdk"]
    build_script = manifest["citylbm_build_script"]
    gpp = manifest["mingw_gpp"]
    fluidx3d = manifest["fluidx3d"]
    gpu = manifest["gpu_runtime"]
    lines = [
        "# CityLBM Build-Chain Manifest",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Build chain ready: {manifest['build_chain_ready']}",
        f"- Operational with fallback: {manifest['build_chain_operational_with_fallback']}",
        f"- Claim readiness: `{manifest['claim_readiness']}`",
        f"- VS Build Tools C++: `{vs['status']}`",
        f"- MinGW/g++ fallback: `{gpp['status']}`",
        f"- Native source compile path: `{manifest['native_source_compile_path']}`",
        f"- .NET SDK: `{dotnet['status']}`",
        f"- CityLBM build script: `{build_script['status']}`",
        f"- FluidX3D binary: `{fluidx3d['status']}`",
        f"- GPU runtime: `{gpu['status']}`",
        "",
        "## Latest VS Build Tools Attempt",
        "",
        f"- Command: `{vs['install_attempt']['command']}`",
        f"- Exit code: {vs['install_attempt']['exit_code']}",
        f"- Winget log: `{vs['install_attempt']['winget_log'].get('path', '')}`",
        f"- VS bootstrapper log: `{vs['install_attempt']['vs_bootstrapper_log'].get('path', '')}`",
        "",
        "Observed blockers:",
    ]
    for item in vs["install_attempt"].get("observed_blockers", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "## Disk",
        "",
        "| drive | free GB | total bytes |",
        "|---|---:|---:|",
    ]
    for row in manifest["disk"]:
        lines.append(f"| `{row['drive']}` | {row['free_gb']} | {row['total_bytes']} |")
    lines += [
        "",
        "## Boundary",
        "",
        manifest["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotnet", type=Path, default=Path(r"E:\citylbm_buildchain\dotnet\dotnet.exe"))
    parser.add_argument("--fluidx3d-exe", type=Path, default=Path(r"E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe"))
    parser.add_argument("--winget-install-exit-code", type=int)
    parser.add_argument("--winget-log", type=Path)
    parser.add_argument("--vs-bootstrapper-log", type=Path)
    parser.add_argument("--out", type=Path, default=OUT_JSON)
    parser.add_argument("--out-csv", type=Path, default=OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()

    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    vcvars64_candidates = [
        Path(r"E:\citylbm_buildchain\VSBuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
    ]
    c_free = next((row["free_gb"] for row in disk_status() if row["drive"] == "C:\\"), None)
    winget_log = args.winget_log or latest_winget_log()
    vs_bootstrapper_log = args.vs_bootstrapper_log or latest_vs_bootstrapper_log()
    winget_text = read_text(winget_log)
    vs_log_text = read_text(vs_bootstrapper_log)
    inferred_exit_code = args.winget_install_exit_code
    if inferred_exit_code is None and "1602" in (winget_text + vs_log_text):
        inferred_exit_code = 1602
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

    dotnet_ready = args.dotnet.exists()
    build_script_path = ROOT / "CityLBM" / "build.ps1"
    build_script_text = read_text(build_script_path)
    build_script_supports_portable_dotnet = (
        "Resolve-CityLBMDotNet" in build_script_text
        and "CITYLBM_DOTNET" in build_script_text
        and "E:\\citylbm_buildchain\\dotnet\\dotnet.exe" in build_script_text
    )
    build_script_supports_no_pause = "-NoPause" in build_script_text or "[switch]$NoPause" in build_script_text
    build_script_smoke = run_cmd(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(build_script_path),
            "-DotNetPath",
            str(args.dotnet),
            "-NoPause",
        ],
        timeout=180,
    ) if dotnet_ready and build_script_path.exists() else {
        "command": f"powershell -NoProfile -ExecutionPolicy Bypass -File {build_script_path} -DotNetPath {args.dotnet} -NoPause",
        "found": build_script_path.exists(),
        "returncode": None,
        "stdout": "",
        "stderr": "dotnet executable or build.ps1 missing",
    }
    build_script_ready = (
        build_script_path.exists()
        and build_script_supports_portable_dotnet
        and build_script_supports_no_pause
        and build_script_smoke.get("returncode") == 0
    )
    gpp_version = run_cmd(["g++.exe", "--version"])
    gpp_ready = bool(gpp_version.get("returncode") == 0)
    fluidx3d_ready = args.fluidx3d_exe.exists()
    nvidia_smi = run_cmd(["nvidia-smi"])
    gpu_ready = nvidia_smi.get("returncode") == 0 and "GPU is lost" not in (nvidia_smi.get("stdout", "") + nvidia_smi.get("stderr", ""))
    observed_blockers = [
        "winget returned 1602 during the current attempt" if inferred_exit_code == 1602 else "",
        "Visual Studio bootstrapper log reported possible declined UAC prompt" if "declined UAC" in vs_log_text or "0x80070642" in vs_log_text else "",
        "vswhere does not find Microsoft.VisualStudio.Component.VC.Tools.x86.x64" if not vs_ready else "",
        "cl.exe is not on PATH" if not run_cmd(["cl.exe"]).get("found") else "",
        "msbuild.exe is not on PATH" if not run_cmd(["msbuild.exe"]).get("found") else "",
        "C: drive free space is below 8 GB; Visual Studio may still require more system-drive cache space" if c_free is not None and c_free < 8.0 else "",
    ]
    native_source_compile_ready = bool(vs_ready or gpp_ready)
    build_chain_ready = bool(vs_ready and dotnet_ready and fluidx3d_ready and gpu_ready)
    build_chain_operational_with_fallback = bool(dotnet_ready and native_source_compile_ready and fluidx3d_ready and gpu_ready)
    native_source_compile_path = "visual_studio_cpp" if vs_ready else ("mingw_gpp_fallback" if gpp_ready else "blocked")
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "build_chain_ready" if build_chain_ready else "blocked_build_chain_diagnostic",
        "build_chain_ready": build_chain_ready,
        "build_chain_operational_with_fallback": build_chain_operational_with_fallback,
        "native_source_compile_ready": native_source_compile_ready,
        "native_source_compile_path": native_source_compile_path,
        "visual_studio_build_tools_2022_cpp": {
            "status": "ready" if vs_ready else "blocked",
            "vswhere": file_status(vswhere),
            "vswhere_requires_vc": vs_requires,
            "cl_on_path": run_cmd(["cl.exe"]),
            "msbuild_on_path": run_cmd(["msbuild.exe"]),
            "vcvars64_candidates": [file_status(p) for p in vcvars64_candidates],
            "install_attempt": {
                "command": (
                    "winget install --id Microsoft.VisualStudio.2022.BuildTools --source winget "
                    "--accept-package-agreements --accept-source-agreements --silent "
                    "--location E:\\citylbm_buildchain\\VSBuildTools --override "
                    "\"--wait --quiet --norestart --installPath E:\\citylbm_buildchain\\VSBuildTools "
                    "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended "
                    "--add Microsoft.VisualStudio.Component.VC.CMake.Project "
                    "--add Microsoft.VisualStudio.Component.Windows11SDK.26100\""
                ),
                "exit_code": inferred_exit_code,
                "winget_log": log_status(winget_log),
                "vs_bootstrapper_log": log_status(vs_bootstrapper_log),
                "observed_blockers": observed_blockers,
            },
        },
        "dotnet_sdk": {
            "status": "ready" if dotnet_ready else "blocked",
            "executable": file_status(args.dotnet),
            "info": run_cmd([str(args.dotnet), "--info"]) if dotnet_ready else run_cmd(["dotnet", "--info"]),
        },
        "citylbm_build_script": {
            "status": "ready" if build_script_ready else "blocked",
            "script": file_status(build_script_path),
            "supports_portable_dotnet": build_script_supports_portable_dotnet,
            "supports_no_pause": build_script_supports_no_pause,
            "smoke_build": build_script_smoke,
            "packaged_gha": file_status(ROOT / "CityLBM" / "bin" / "Release" / "CityLBM" / "CityLBM.gha"),
            "note": "Plugin build reproducibility only; this does not provide VS C++ Build Tools, GPU recovery, or CFD accuracy evidence.",
        },
        "mingw_gpp": {
            "status": "ready" if gpp_ready else "blocked",
            "version": gpp_version,
            "note": "Used only as a native FluidX3D source build fallback when VS/MSBuild is unavailable; this is not accuracy evidence.",
        },
        "fluidx3d": {
            "status": "ready_for_existing_binary" if fluidx3d_ready else "blocked",
            "executable": file_status(args.fluidx3d_exe),
        },
        "gpu_runtime": {
            "status": "ready" if gpu_ready else "blocked",
            "nvidia_smi": nvidia_smi,
            "note": "GPU runtime is available for scheduling checks only; it does not improve official Case E metrics.",
        },
        "disk": disk_status(),
        "environment": {
            "path": os.environ.get("PATH", ""),
        },
        "boundary": (
            "This manifest records build-chain and runtime readiness only. It does not install tools by itself, "
            "does not add CFD output, and does not support formal accuracy or v0.4.0 release claims."
        ),
    }
    manifest["visual_studio_build_tools_2022_cpp"]["install_attempt"]["observed_blockers"] = [
        b for b in manifest["visual_studio_build_tools_2022_cpp"]["install_attempt"]["observed_blockers"] if b
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_csv(args.out_csv, manifest)
    write_markdown(args.out_md, manifest)
    print(json.dumps({"out": str(args.out), "build_chain_ready": build_chain_ready, "vs_cpp_status": manifest["visual_studio_build_tools_2022_cpp"]["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
