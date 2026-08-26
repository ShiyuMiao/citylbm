#!/usr/bin/env python3
"""Fast gate for deciding whether a generated case may enter a short canary.

This script intentionally does not prepare FluidX3D sources, launch Rhino, or
run CFD. It reuses audit_inlet_source.py and reports only whether the generated
CityLBM setup route is the current synthetic-turbulence codegen route that can
support a short native FluidX3D diagnostic canary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether a CityLBM case may enter a short diagnostic canary.")
    parser.add_argument("--case-dir", required=True, help="Generated CityLBM/FluidX3D case directory.")
    parser.add_argument("--metadata", default="", help="case_metadata.json. Defaults to <case-dir>/case_metadata.json.")
    parser.add_argument("--out", default="", help="Output JSON. Defaults to <case-dir>/short_canary_route_check.json.")
    parser.add_argument(
        "--audit-out",
        default="",
        help="Optional inlet source audit output path. Defaults beside --out.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def first_existing(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for candidate in candidates:
        path = root / candidate
        if path.is_file():
            return path.resolve()
    return None


def compact_inlet_audit(data: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "inlet_source_gate",
        "runtime_inlet_diagnostics_source_gate",
        "paper_grade_inlet_source_gate",
        "paper_grade_inlet_source_gate_reasons",
        "setup_inlet_codegen_route",
        "has_current_citylbm_stg_codegen_route",
        "has_legacy_runtime_diagnostic_patch_route",
        "short_canary_allowed_by_codegen_route",
        "development_acceleration_stage",
        "development_acceleration_runs_cfd_next",
        "long_cfd_allowed_by_inlet_source_audit",
    ]
    return {key: data.get(key) for key in keys if key in data}


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    repo = Path(__file__).resolve().parents[1]
    case_dir = Path(args.case_dir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out else case_dir / "short_canary_route_check.json"
    audit_out = Path(args.audit_out).expanduser().resolve() if args.audit_out else out_path.with_name("short_canary_inlet_source_audit.json")
    metadata = Path(args.metadata).expanduser().resolve() if args.metadata else case_dir / "case_metadata.json"
    setup = first_existing(case_dir, ["src/setup.cpp", "setup.cpp"])
    defines = first_existing(case_dir, ["src/defines.hpp", "defines.hpp"])

    reasons = []
    audit = {}
    command = []
    audit_return_code: Optional[int] = None
    stdout = ""
    stderr = ""

    if not setup:
        reasons.append("setup_cpp_missing")
    if not defines:
        reasons.append("defines_hpp_missing")

    if setup and defines:
        command = [
            sys.executable,
            str(repo / "scripts" / "audit_inlet_source.py"),
            "--setup",
            str(setup),
            "--defines",
            str(defines),
            "--out",
            str(audit_out),
        ]
        if metadata.is_file():
            command.extend(["--metadata", str(metadata)])
        completed = subprocess.run(
            command,
            cwd=str(repo),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        audit_return_code = completed.returncode
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        audit = read_json(audit_out)
        if completed.returncode not in (0, 2):
            reasons.append(f"audit_inlet_source_failed:{completed.returncode}")
        if not audit:
            reasons.append("inlet_source_audit_json_missing_or_invalid")

    inlet_gate = str(audit.get("inlet_source_gate") or "").strip()
    runtime_gate = str(audit.get("runtime_inlet_diagnostics_source_gate") or "").strip()
    route = str(audit.get("setup_inlet_codegen_route") or "missing").strip()
    short_allowed = audit.get("short_canary_allowed_by_codegen_route") is True

    if audit and inlet_gate != "pass":
        reasons.append(f"inlet_source_gate_not_pass:{inlet_gate or 'missing'}")
    if audit and runtime_gate != "pass":
        reasons.append(f"runtime_inlet_diagnostics_source_gate_not_pass:{runtime_gate or 'missing'}")
    if audit and not short_allowed:
        reasons.append(f"setup_codegen_route_not_current_citylbm:{route or 'missing'}")

    gate = "pass" if not reasons else "fail"
    report = {
        "Schema": "citylbm.short_canary_route_check.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "fast_seconds_scale_gate_before_preflight_or_native_canary",
        "CaseDir": str(case_dir),
        "Setup": str(setup) if setup else "",
        "Defines": str(defines) if defines else "",
        "Metadata": str(metadata) if metadata.is_file() else "",
        "Gate": gate,
        "ShortDiagnosticCanaryAllowed": gate == "pass",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "ElapsedSeconds": round(time.perf_counter() - started, 4),
        "InletSourceAudit": compact_inlet_audit(audit),
        "InletSourceAuditPath": str(audit_out),
        "AuditCommand": command,
        "AuditReturnCode": audit_return_code,
        "AuditStdout": stdout,
        "AuditStderr": stderr,
        "NextAction": (
            "Run the short diagnostic native canary, then audit runtime inlet diagnostics before any long run."
            if gate == "pass"
            else "Regenerate the case from the current CityLBM codegen route before spending time on FluidX3D/Rhino execution."
        ),
        "EvidenceUseClass": "development_acceleration_only_not_paper_accuracy_evidence",
    }
    write_json(out_path, report)
    print(f"short_canary_route_gate={gate}; route={route}; elapsed_s={report['ElapsedSeconds']}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
