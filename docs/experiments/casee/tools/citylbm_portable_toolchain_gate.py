#!/usr/bin/env python3
"""Gate the local portable CityLBM build-chain activation script."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
SCRIPT = CASE_DIR / "tools" / "citylbm_portable_toolchain_activate.ps1"
RAW_JSON = RESULTS_DIR / "citylbm_portable_toolchain_activation.json"
OUT_JSON = RESULTS_DIR / "citylbm_portable_toolchain_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_portable_toolchain_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_portable_toolchain_gate.md"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_activation(out_json: Path) -> Dict[str, Any]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-OutJson",
        str(out_json),
        "-NoPause",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-20:]),
    }


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    activation = payload.get("activation") or {}
    rows: List[Dict[str, Any]] = [
        {
            "component": "portable_toolchain",
            "ready": activation.get("portable_toolchain_ready"),
            "status": activation.get("claim_readiness", ""),
            "boundary": payload.get("boundary", ""),
        },
        {
            "component": "dotnet",
            "ready": ((activation.get("dotnet") or {}).get("ready")),
            "status": ((activation.get("dotnet") or {}).get("env_CITYLBM_DOTNET", "")),
            "boundary": "Portable .NET evidence only.",
        },
        {
            "component": "fluidx3d",
            "ready": ((activation.get("fluidx3d") or {}).get("ready_for_existing_binary")),
            "status": ((activation.get("fluidx3d") or {}).get("env_CITYLBM_FLUIDX3D_EXE", "")),
            "boundary": "Binary presence only; no solver run.",
        },
        {
            "component": "mingw_gpp",
            "ready": ((activation.get("mingw_gpp") or {}).get("ready")),
            "status": ((activation.get("mingw_gpp") or {}).get("executable") or {}).get("path", ""),
            "boundary": "Native compile fallback only.",
        },
        {
            "component": "visual_studio_cpp",
            "ready": ((activation.get("visual_studio_cpp") or {}).get("ready")),
            "status": "blocked" if not ((activation.get("visual_studio_cpp") or {}).get("ready")) else "ready",
            "boundary": "Still governed by VS C++ recovery gate.",
        },
        {
            "component": "gpu_runtime",
            "ready": ((activation.get("gpu_runtime") or {}).get("ready")),
            "status": "blocked" if not ((activation.get("gpu_runtime") or {}).get("ready")) else "ready",
            "boundary": "Still required before long FluidX3D runs.",
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["component", "ready", "status", "boundary"])
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    activation = payload.get("activation") or {}
    dotnet = activation.get("dotnet") or {}
    fluidx = activation.get("fluidx3d") or {}
    gpp = activation.get("mingw_gpp") or {}
    vs = activation.get("visual_studio_cpp") or {}
    gpu = activation.get("gpu_runtime") or {}
    lines = [
        "# CityLBM Portable Toolchain Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Gate passed: {payload['portable_toolchain_gate_passed']}",
        f"- Portable toolchain ready: {activation.get('portable_toolchain_ready')}",
        f"- .NET ready: {dotnet.get('ready')}",
        f"- FluidX3D binary ready: {fluidx.get('ready_for_existing_binary')}",
        f"- MinGW/g++ fallback ready: {gpp.get('ready')}",
        f"- VS C++ ready: {vs.get('ready')}",
        f"- GPU runtime ready: {gpu.get('ready')}",
        f"- Process PATH entries added: `{'; '.join(activation.get('process_path_entries_added') or [])}`",
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--raw-json", type=Path, default=RAW_JSON)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run = {"command": "", "returncode": 0, "stdout_tail": "", "stderr_tail": ""}
    if not args.skip_run:
        run = run_activation(args.raw_json)
    activation = read_json(args.raw_json)
    checks = {
        "script_exists": SCRIPT.exists(),
        "activation_returncode_zero": run.get("returncode") == 0,
        "raw_activation_json_written": args.raw_json.exists(),
        "portable_toolchain_ready": activation.get("portable_toolchain_ready") is True,
        "dotnet_ready": ((activation.get("dotnet") or {}).get("ready")) is True,
        "fluidx3d_binary_ready": ((activation.get("fluidx3d") or {}).get("ready_for_existing_binary")) is True,
        "mingw_gpp_ready": ((activation.get("mingw_gpp") or {}).get("ready")) is True,
        "install_not_attempted": activation.get("install_attempted") is False,
        "formal_accuracy_claim_not_supported": activation.get("formal_accuracy_claim_supported") is False,
        "boundary_safe": "does not" in str(activation.get("boundary", "")).lower()
        and "improve Case E metrics" in str(activation.get("boundary", "")),
    }
    gate_passed = all(checks.values())
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "portable_toolchain_gate_passed": gate_passed,
        "claim_readiness": "portable_toolchain_ready" if gate_passed else "portable_toolchain_blocked",
        "checks": checks,
        "run": run,
        "activation": activation,
        "formal_accuracy_claim_supported": False,
        "boundary": (
            "Portable toolchain activation evidence only. This gate proves the local portable .NET, "
            "FluidX3D binary, and MinGW/g++ paths can be activated for the current process; it does not "
            "install VS C++ Build Tools, recover GPU runtime, run FluidX3D, improve official z=2 m metrics, "
            "or permit formal v0.4.0."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, payload)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"portable_toolchain_gate_passed": gate_passed, "out_json": str(OUT_JSON)}, indent=2))
    return 0 if gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
