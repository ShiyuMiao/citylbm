#!/usr/bin/env python3
"""Preflight gate for the next official AIJ Case E z=2 m follow-up run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
DATA_DIR = CASE_DIR / "official_data"
OUT_JSON = RESULTS_DIR / "casee_official_run_preflight.json"
OUT_CSV = RESULTS_DIR / "casee_official_run_preflight.csv"
OUT_MD = RESULTS_DIR / "casee_official_run_preflight.md"

OFFICIAL_FILES = [
    "AF_caseE.csv",
    "BD_caseE.stl",
    "RS_caseE.csv",
    "MP_caseE.png",
    "readme_caseE.md",
    "LF_caseE.xls",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(args: List[str], timeout: int = 20) -> Dict[str, Any]:
    exe = shutil.which(args[0]) if not Path(args[0]).exists() else args[0]
    if not exe:
        return {"command": " ".join(args), "found": False, "returncode": None, "stdout": "", "stderr": "not found"}
    try:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout, encoding="utf-8", errors="replace")
        return {
            "command": " ".join(args),
            "found": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"command": " ".join(args), "found": True, "returncode": None, "stdout": "", "stderr": str(exc)}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def official_manifest_status() -> Dict[str, Any]:
    rows = read_csv(CASE_DIR / "data_manifest.csv")
    by_name = {row.get("file_name", ""): row for row in rows}
    file_checks: List[Dict[str, Any]] = []
    for name in OFFICIAL_FILES:
        row = by_name.get(name, {})
        path = ROOT / str(row.get("relative_path", DATA_DIR / name))
        exists = path.exists()
        actual_sha = sha256(path) if exists else ""
        expected_sha = str(row.get("sha256", ""))
        file_checks.append(
            {
                "file_name": name,
                "path": rel(path) if exists else str(path),
                "exists": exists,
                "sha256_matches_manifest": bool(expected_sha) and actual_sha == expected_sha,
                "md5_verified": row.get("md5_verified") == "yes",
                "size_bytes_manifest": row.get("bytes", ""),
                "downloaded_at": row.get("downloaded_at", ""),
            }
        )
    ready = len(file_checks) == len(OFFICIAL_FILES) and all(
        item["exists"] and item["sha256_matches_manifest"] and item["md5_verified"] for item in file_checks
    )
    return {"ready": ready, "file_checks": file_checks}


def official_probe_status() -> Dict[str, Any]:
    rows = read_csv(DATA_DIR / "RS_caseE.csv")
    probes = [
        row
        for row in rows
        if row.get("case") == "ac"
        and row.get("Wind_direction") == "N"
        and abs(float(row.get("z(m)", "nan")) - 2.0) < 1e-9
    ]
    return {
        "ready": len(probes) == 80,
        "case": "ac",
        "wind_direction": "N",
        "validation_height_m": 2.0,
        "probe_count": len(probes),
        "expected_probe_count": 80,
        "formal_sampling_mode": "raw_trilinear",
    }


def disk_status() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for drive in ["C:\\", "D:\\", "E:\\", "F:\\", "G:\\"]:
        if not Path(drive).exists():
            continue
        usage = shutil.disk_usage(drive)
        rows.append({"drive": drive, "free_gb": round(usage.free / (1024**3), 3), "total_gb": round(usage.total / (1024**3), 3)})
    return rows


def build_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    gates = payload["gates"]
    rows = []
    for gate_id, gate in gates.items():
        rows.append(
            {
                "gate_id": gate_id,
                "status": "pass" if gate["passed"] else "blocked",
                "severity": gate["severity"],
                "evidence_type": gate["evidence_type"],
                "source": gate["source"],
                "required_action": gate["required_action"],
                "paper_policy": gate["paper_policy"],
            }
        )
    return rows


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fields = ["gate_id", "status", "severity", "evidence_type", "source", "required_action", "paper_policy"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metrics = payload["current_official_metric"]
    lines = [
        "# Case E Official Run Preflight",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Official follow-up run allowed now: {payload['official_followup_run_allowed']}",
        f"- Formal v0.4.0 release allowed: {payload['formal_release_allowed']}",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        "",
        "## Current Official z=2 m Metric",
        "",
        f"- MAE: {metrics.get('mae_pp')} pp",
        f"- R2: {metrics.get('r2')}",
        f"- Pearson: {metrics.get('pearson')}",
        "",
        "## Gates",
        "",
        "| gate | status | severity | required action |",
        "|---|---:|---|---|",
    ]
    for gate_id, gate in payload["gates"].items():
        lines.append(
            f"| `{gate_id}` | {'pass' if gate['passed'] else 'blocked'} | "
            f"{gate['severity']} | {gate['required_action']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dotnet", type=Path, default=Path(r"E:\citylbm_buildchain\dotnet\dotnet.exe"))
    parser.add_argument("--fluidx3d-exe", type=Path, default=Path(r"E:\citylbm_buildchain\FluidX3D\bin\FluidX3D.exe"))
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--build-chain", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    parser.add_argument("--plugin-gate", type=Path, default=RESULTS_DIR / "plugin_identity_gate.json")
    parser.add_argument("--rhino-gate", type=Path, default=RESULTS_DIR / "rhino_gha_load_gate.json")
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--out-csv", type=Path, default=OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    args = parser.parse_args()

    release_gate = read_json(args.release_gate)
    build_chain = read_json(args.build_chain)
    plugin_gate = read_json(args.plugin_gate)
    rhino_gate = read_json(args.rhino_gate)
    official_data = official_manifest_status()
    probes = official_probe_status()
    nvidia = run_cmd(["nvidia-smi"], timeout=20)
    dotnet = run_cmd([str(args.dotnet), "--version"], timeout=20) if args.dotnet.exists() else run_cmd(["dotnet", "--version"], timeout=20)
    fluidx3d_exists = args.fluidx3d_exe.exists()
    gpu_ready = bool(nvidia.get("returncode") == 0 and "GPU is lost" not in (nvidia.get("stdout", "") + nvidia.get("stderr", "")))
    vs_status = (build_chain.get("visual_studio_build_tools_2022_cpp") or {}).get("status")

    gates = {
        "official_data_manifest": {
            "passed": official_data["ready"],
            "severity": "critical",
            "evidence_type": "newly_run",
            "source": "docs/experiments/casee/data_manifest.csv",
            "required_action": "Re-download and hash-check Zenodo Case E files if this fails.",
            "paper_policy": "Protocol input evidence only.",
        },
        "official_probe_protocol": {
            "passed": probes["ready"],
            "severity": "critical",
            "evidence_type": "newly_run",
            "source": "docs/experiments/casee/official_data/RS_caseE.csv",
            "required_action": "Keep formal validation locked to ac+N z=2 m with 80 raw_trilinear probes.",
            "paper_policy": "Required for any official metric claim.",
        },
        "citylbm_build": {
            "passed": bool((release_gate.get("checks") or {}).get("citylbm_build_passed")),
            "severity": "critical",
            "evidence_type": "preexisting_artifact",
            "source": "docs/experiments/casee/results/release_gate.json",
            "required_action": "Run reproducibility_suite.py or dotnet build until the Release build passes.",
            "paper_policy": "Build evidence only.",
        },
        "plugin_identity": {
            "passed": bool(plugin_gate.get("plugin_identity_gate_passed")),
            "severity": "major",
            "evidence_type": "preexisting_artifact",
            "source": "docs/experiments/casee/results/plugin_identity_gate.json",
            "required_action": "Regenerate plugin_identity_gate.py after rebuilding CityLBM.gha.",
            "paper_policy": "Software identity evidence only.",
        },
        "rhino_gha_load": {
            "passed": bool(rhino_gate.get("rhino_loaded_new_gha")),
            "severity": "major",
            "evidence_type": "preexisting_artifact",
            "source": "docs/experiments/casee/results/rhino_gha_load_gate.json",
            "required_action": "Create a real Rhino/Grasshopper load manifest with version/hash screenshot or log evidence.",
            "paper_policy": "Required for formal plugin-load claims; not required for native-only CFD preflight.",
        },
        "dotnet_sdk": {
            "passed": bool(dotnet.get("returncode") == 0),
            "severity": "major",
            "evidence_type": "newly_run",
            "source": dotnet.get("command", ""),
            "required_action": "Restore the local .NET SDK path or install .NET SDK before rebuilding CityLBM.",
            "paper_policy": "Build-chain evidence only.",
        },
        "fluidx3d_binary": {
            "passed": fluidx3d_exists,
            "severity": "critical",
            "evidence_type": "newly_run",
            "source": str(args.fluidx3d_exe),
            "required_action": "Restore or rebuild FluidX3D.exe before scheduling native Case E.",
            "paper_policy": "Runtime availability evidence only.",
        },
        "gpu_runtime": {
            "passed": gpu_ready,
            "severity": "critical",
            "evidence_type": "newly_run",
            "source": "nvidia-smi",
            "required_action": "Recover/reboot the NVIDIA device until nvidia-smi returns 0 without GPU-lost errors.",
            "paper_policy": "Blocks new long FluidX3D runs; not accuracy evidence.",
        },
        "vs_cpp_build_tools": {
            "passed": vs_status == "ready",
            "severity": "major",
            "evidence_type": "preexisting_artifact",
            "source": "docs/experiments/casee/results/build_chain_manifest.json",
            "required_action": "Free C: space, approve UAC, and install Visual Studio Build Tools 2022 C++ workload.",
            "paper_policy": "Native build-chain limitation unless ready.",
        },
        "casea_smoke_regression": {
            "passed": bool((release_gate.get("checks") or {}).get("casea_smoke_regression_passed")),
            "severity": "major",
            "evidence_type": "preexisting_artifact",
            "source": "docs/experiments/casea/results/casea_smoke_regression.json",
            "required_action": "Rerun Case A smoke regression after any default solver change.",
            "paper_policy": "Regression guard only, not Case E accuracy evidence.",
        },
    }
    followup_required = [
        "official_data_manifest",
        "official_probe_protocol",
        "citylbm_build",
        "dotnet_sdk",
        "fluidx3d_binary",
        "gpu_runtime",
        "casea_smoke_regression",
    ]
    official_followup_run_allowed = all(gates[item]["passed"] for item in followup_required)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "blocked_official_followup_preflight" if not official_followup_run_allowed else "ready_for_next_official_followup_run",
        "official_followup_run_allowed": official_followup_run_allowed,
        "formal_release_allowed": bool(release_gate.get("formal_release_allowed")),
        "current_official_metric": release_gate.get("metrics", {}),
        "gates": gates,
        "official_data": official_data,
        "official_probe_protocol": probes,
        "runtime_observations": {
            "nvidia_smi": nvidia,
            "dotnet_version": dotnet,
            "fluidx3d_exe": {"path": str(args.fluidx3d_exe), "exists": fluidx3d_exists},
            "vs_cpp_status": vs_status,
            "disk": disk_status(),
        },
        "blocked_gates": [gate_id for gate_id, gate in gates.items() if not gate["passed"]],
        "boundary": (
            "This preflight controls whether another official native Case E follow-up can be scheduled. "
            "It is not solver-output evidence, does not change official z=2 m metrics, and does not allow formal v0.4.0."
        ),
    }
    rows = build_rows(payload)
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, payload)
    print(
        json.dumps(
            {
                "official_followup_run_allowed": official_followup_run_allowed,
                "formal_release_allowed": payload["formal_release_allowed"],
                "blocked_gates": payload["blocked_gates"],
                "out_json": str(args.out_json),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
