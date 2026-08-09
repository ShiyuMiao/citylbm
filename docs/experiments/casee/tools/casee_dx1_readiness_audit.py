#!/usr/bin/env python3
"""Audit dx=1 m Case E readiness without launching a long FluidX3D run."""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_dx1_readiness_audit.json"
OUT_CSV = RESULTS_DIR / "casee_dx1_readiness_audit.csv"
OUT_MD = RESULTS_DIR / "casee_dx1_readiness_audit.md"

DOMAIN = {
    "origin_x": -300.0,
    "origin_y": -500.0,
    "origin_z": 0.0,
    "size_x": 600.0,
    "size_y": 800.0,
    "size_z": 240.0,
}

DX1_COMMAND = (
    "python docs/experiments/casee/tools/generate_native_casee.py --dx 1 "
    "--steps 48000 --spinup 12000 --sample-dt 4000 --ground-offset-cells 1 "
    "--origin-z-offset-m 0.5 --nu-lbm 0.001"
)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    fieldnames = [
        "domain_basis",
        "scenario",
        "dx_m",
        "nx",
        "ny",
        "nz",
        "cell_count",
        "decomposition",
        "bytes_per_cell",
        "required_total_gib",
        "required_per_gpu_gib",
        "gpu_count",
        "min_free_gib",
        "headroom_fraction",
        "headroom_ok",
        "readiness",
        "evidence_type",
        "claim_boundary",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_command(args: List[str]) -> Dict[str, Any]:
    exe = shutil.which(args[0])
    if exe is None:
        return {"command": " ".join(args), "found": False, "returncode": None, "stdout": "", "stderr": "not found"}
    proc = subprocess.run(args, text=True, capture_output=True, timeout=30, encoding="utf-8", errors="replace")
    return {
        "command": " ".join(args),
        "found": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def parse_gpu_query(raw: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in csv.reader(raw.splitlines(), skipinitialspace=True):
        if len(item) < 6:
            continue
        try:
            rows.append(
                {
                    "index": int(item[0]),
                    "name": item[1],
                    "memory_total_mib": float(item[2]),
                    "memory_free_mib": float(item[3]),
                    "temperature_c": float(item[4]),
                    "utilization_gpu_percent": float(item[5]),
                }
            )
        except ValueError:
            continue
    return rows


def dx1_generator_domain(dx: float = 1.0, ground_offset_cells: int = 1, origin_z_offset_m: float = 0.5) -> Dict[str, Any]:
    origin_z = DOMAIN["origin_z"] - ground_offset_cells * dx + origin_z_offset_m
    nx = math.ceil(DOMAIN["size_x"] / dx)
    ny = math.ceil(DOMAIN["size_y"] / dx)
    nz = math.ceil((DOMAIN["size_z"] - origin_z) / dx)
    return {
        "domain_basis": "current_generator_fixed_domain",
        "dx_m": dx,
        "origin_z_m": origin_z,
        "nx": nx,
        "ny": ny,
        "nz": nz,
        "cell_count": nx * ny * nz,
        "decomposition": "2x2x1",
        "gpu_domains": 4,
    }


def dx1_conservative_domain() -> Dict[str, Any]:
    rows = read_csv(RESULTS_DIR / "dx1_feasibility_estimate.csv")
    row = next((item for item in rows if item.get("dx_m") == "1"), {})
    dims = [int(v) for v in str(row.get("illustrative_domain_cells_nx_ny_nz", "0x0x0")).split("x")]
    return {
        "domain_basis": "conservative_stl_padding_estimate",
        "dx_m": 1.0,
        "origin_z_m": "",
        "nx": dims[0],
        "ny": dims[1],
        "nz": dims[2],
        "cell_count": int(row.get("illustrative_domain_cell_count", 0) or 0),
        "decomposition": "2x2x1",
        "gpu_domains": 4,
    }


def memory_rows(domain: Dict[str, Any], gpu_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    min_free_gib = min((gpu["memory_free_mib"] / 1024.0 for gpu in gpu_rows), default=0.0)
    gpu_count = len(gpu_rows)
    required_devices = int(domain["gpu_domains"])
    scenarios = [
        ("optimistic_fp16s_core", 256),
        ("moderate_fp16s_plus_overhead", 512),
        ("conservative_runtime_overhead", 1024),
    ]
    out: List[Dict[str, Any]] = []
    for scenario, bytes_per_cell in scenarios:
        required_total_gib = float(domain["cell_count"]) * bytes_per_cell / (1024.0**3)
        required_per_gpu_gib = required_total_gib / max(required_devices, 1)
        headroom_fraction = (min_free_gib / required_per_gpu_gib - 1.0) if required_per_gpu_gib > 0 else -1.0
        headroom_ok = gpu_count >= required_devices and min_free_gib >= required_per_gpu_gib * 1.25
        out.append(
            {
                "domain_basis": domain["domain_basis"],
                "scenario": scenario,
                "dx_m": domain["dx_m"],
                "nx": domain["nx"],
                "ny": domain["ny"],
                "nz": domain["nz"],
                "cell_count": domain["cell_count"],
                "decomposition": domain["decomposition"],
                "bytes_per_cell": bytes_per_cell,
                "required_total_gib": round(required_total_gib, 3),
                "required_per_gpu_gib": round(required_per_gpu_gib, 3),
                "gpu_count": gpu_count,
                "min_free_gib": round(min_free_gib, 3),
                "headroom_fraction": round(headroom_fraction, 3),
                "headroom_ok": headroom_ok,
                "readiness": "memory_headroom_ok" if headroom_ok else "high_risk_or_blocked",
                "evidence_type": "newly_run",
                "claim_boundary": "memory/readiness audit only; not solver output, accuracy evidence, or mesh-independence evidence",
            }
        )
    return out


def summarize(
    rows: List[Dict[str, Any]],
    gpu_rows: List[Dict[str, Any]],
    build_chain: Dict[str, Any],
    preflight: Dict[str, Any],
    release_gate: Dict[str, Any],
) -> Dict[str, Any]:
    generator_moderate = next(
        row
        for row in rows
        if row["domain_basis"] == "current_generator_fixed_domain" and row["scenario"] == "moderate_fp16s_plus_overhead"
    )
    generator_conservative = next(
        row
        for row in rows
        if row["domain_basis"] == "current_generator_fixed_domain" and row["scenario"] == "conservative_runtime_overhead"
    )
    conservative_estimate = next(
        row
        for row in rows
        if row["domain_basis"] == "conservative_stl_padding_estimate" and row["scenario"] == "moderate_fp16s_plus_overhead"
    )
    dx1_memory_headroom_ok = bool(generator_moderate["headroom_ok"] and generator_conservative["headroom_ok"])
    dx1_readiness = "ready_for_user_confirmed_dry_run" if dx1_memory_headroom_ok else "high_risk_blocked_until_dry_run"
    build_vs = build_chain.get("visual_studio_build_tools_2022_cpp") or {}
    fluidx = build_chain.get("fluidx3d") or {}
    dotnet = build_chain.get("dotnet_sdk") or {}
    gpu_ready = bool(gpu_rows) and all(gpu["memory_free_mib"] > 0 for gpu in gpu_rows)
    return {
        "dx1_readiness_audit_passed": True,
        "dx1_readiness": dx1_readiness,
        "dx1_memory_headroom_ok": dx1_memory_headroom_ok,
        "generator_moderate_required_per_gpu_gib": generator_moderate["required_per_gpu_gib"],
        "generator_moderate_headroom_fraction": generator_moderate["headroom_fraction"],
        "generator_conservative_required_per_gpu_gib": generator_conservative["required_per_gpu_gib"],
        "conservative_padding_moderate_required_per_gpu_gib": conservative_estimate["required_per_gpu_gib"],
        "gpu_count": len(gpu_rows),
        "gpu_min_free_gib": generator_moderate["min_free_gib"],
        "dotnet_ready": dotnet.get("status") == "ready",
        "fluidx3d_ready": fluidx.get("status") == "ready_for_existing_binary",
        "gpu_runtime_ready": gpu_ready,
        "vs_cpp_ready": build_vs.get("status") == "ready",
        "official_followup_run_allowed": preflight.get("official_followup_run_allowed"),
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "official_z2m_metrics": release_gate.get("metrics", {}),
        "run_started": False,
        "run_allowed_without_user_confirmation": False,
        "generated_case_committed": False,
        "formal_accuracy_claim_supported": False,
        "recommended_next_action": (
            "Do not start dx=1 full FluidX3D automatically. First run an interactive/dry allocation test or reduce domain/decomposition; "
            "only a completed official z=2 m raw_trilinear 80-probe CSV may update metrics."
        ),
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    summary = payload["summary"]
    metrics = summary["official_z2m_metrics"]
    lines = [
        "# Case E dx=1 m Readiness Audit",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- dx=1 readiness: `{summary['dx1_readiness']}`",
        f"- dx=1 memory headroom ok: {summary['dx1_memory_headroom_ok']}",
        f"- Run started: {summary['run_started']}",
        f"- Run allowed without user confirmation: {summary['run_allowed_without_user_confirmation']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        "",
        "## Current Official z=2 m Metric",
        "",
        f"- MAE: {metrics.get('mae_pp')} pp",
        f"- R2: {metrics.get('r2')}",
        f"- Pearson: {metrics.get('pearson')}",
        f"- Formal release allowed: {summary['formal_release_allowed']}",
        "",
        "## dx=1 Command Under Audit",
        "",
        f"`{payload['dx1_command']}`",
        "",
        "## GPU And Memory Summary",
        "",
        f"- GPU count: {summary['gpu_count']}",
        f"- Minimum free memory: {summary['gpu_min_free_gib']} GiB",
        f"- Current generator moderate per-GPU requirement: {summary['generator_moderate_required_per_gpu_gib']} GiB",
        f"- Current generator moderate headroom: {summary['generator_moderate_headroom_fraction']}",
        f"- Current generator conservative per-GPU requirement: {summary['generator_conservative_required_per_gpu_gib']} GiB",
        f"- Conservative padding moderate per-GPU requirement: {summary['conservative_padding_moderate_required_per_gpu_gib']} GiB",
        "",
        "## Memory Scenarios",
        "",
        "| basis | scenario | cells | required/GPU GiB | min free GiB | headroom ok |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in payload["memory_scenarios"]:
        lines.append(
            f"| {row['domain_basis']} | {row['scenario']} | {row['cell_count']} | "
            f"{row['required_per_gpu_gib']} | {row['min_free_gib']} | {row['headroom_ok']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "This audit is newly-run readiness evidence. It is not a FluidX3D solver run, not a Case E accuracy result, and not mesh-independence evidence.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    gpu_query = run_command(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,temperature.gpu,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    gpu_rows = parse_gpu_query(str(gpu_query.get("stdout", ""))) if gpu_query.get("returncode") == 0 else []
    domains = [dx1_generator_domain(), dx1_conservative_domain()]
    rows = [item for domain in domains for item in memory_rows(domain, gpu_rows)]
    build_chain = read_json(RESULTS_DIR / "build_chain_manifest.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    summary = summarize(rows, gpu_rows, build_chain, preflight, release_gate)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "newly_run",
        "claim_readiness": "limitations_ready_dx1_feasibility",
        "dx1_command": DX1_COMMAND,
        "gpu_query": gpu_query,
        "gpu_rows": gpu_rows,
        "domains": domains,
        "memory_scenarios": rows,
        "summary": summary,
        "boundary": "Readiness audit only; no generated case was committed and no FluidX3D solver run was started.",
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"dx1_readiness": summary["dx1_readiness"], "out_json": str(OUT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
