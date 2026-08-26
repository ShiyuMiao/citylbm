#!/usr/bin/env python3
"""Run or inspect the native empty-tunnel inlet-validation workflow.

This is a thin orchestrator around commands already stored in an
empty_tunnel_manifest.json. It does not invent results: without --execute it
only reports status and the exact next command. The long FluidX3D stage also
requires --allow-long-run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


COMMAND_KEYS = {
    "preflight": ["PreflightNoCfd"],
    "run": ["InstallBuildRunFluidX3D"],
    "profile": ["AuditInletProfileAfterRun"],
    "correlation": ["AuditInletCorrelationAfterRun"],
    "audits": ["AuditInletProfileAfterRun", "AuditInletCorrelationAfterRun"],
    "chain": ["ValidationChainAfterRun"],
}

REQUIRED_FLAGS = {
    "PreflightNoCfd": ["--case-dir", "--fluidx3d-source", "--out-dir", "--manifest-out"],
    "InstallBuildRunFluidX3D": [
        "--case-dir",
        "--fluidx3d-source",
        "--out",
        "--install",
        "--build",
        "--run",
        "--disable-graphics-for-run",
        "--solver-cwd",
        "--output-dir",
    ],
    "AuditInletProfileAfterRun": ["--af-csv", "--out-json", "--average-last-n", "--min-frames", "--min-step-span"],
    "AuditInletCorrelationAfterRun": ["--out-json", "--average-last-n", "--min-frames", "--min-step-span"],
    "ValidationChainAfterRun": ["--native-manifest", "--metadata", "--official", "--af-csv", "--case", "--wind-vector", "--u-ref"],
}

PASS_GATES = {"pass", "paper_grade", "paper_grade_candidate", "ready_for_validation_run"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect or run a native empty-tunnel inlet-validation workflow.")
    parser.add_argument("--manifest", required=True, help="empty_tunnel_manifest.json from prepare_native_empty_tunnel_case.py.")
    parser.add_argument(
        "--stage",
        default="status",
        choices=["status", "preflight", "run", "profile", "correlation", "audits", "chain", "all"],
        help="Workflow stage to inspect/run. Default only reports status.",
    )
    parser.add_argument("--execute", action="store_true", help="Actually execute the selected non-long stage commands.")
    parser.add_argument(
        "--allow-long-run",
        action="store_true",
        help="Required together with --execute before the FluidX3D install/build/run stage is launched.",
    )
    parser.add_argument("--out-json", default="", help="Optional status/execution report JSON.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def argv_for(manifest: Dict[str, Any], key: str) -> List[str]:
    command = manifest.get("Commands", {}).get(key, {})
    argv = command.get("Argv", [])
    return [str(item) for item in argv] if isinstance(argv, list) else []


def flag_value(argv: Sequence[str], flag: str) -> str:
    for index, item in enumerate(argv):
        if item == flag and index + 1 < len(argv):
            return argv[index + 1]
    return ""


def has_flag(argv: Sequence[str], flag: str) -> bool:
    return flag in argv


def first_positional_after_script(argv: Sequence[str]) -> str:
    if len(argv) < 3:
        return ""
    for item in argv[2:]:
        if not item.startswith("-"):
            return item
    return ""


def path_from_flag(argv: Sequence[str], flag: str) -> Optional[Path]:
    value = flag_value(argv, flag)
    if not value:
        return None
    return Path(value).expanduser().resolve()


def gate_from_json(path: Optional[Path], keys: Iterable[str]) -> str:
    if path is None or not path.is_file():
        return "missing"
    data = read_json(path)
    for key in keys:
        value = data.get(key)
        if value is not None:
            return str(value).strip().lower()
    return "missing_gate"


def reasons_from_json(path: Optional[Path], keys: Iterable[str]) -> List[str]:
    if path is None or not path.is_file():
        return []
    data = read_json(path)
    reasons: List[str] = []
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            reasons.extend(str(item) for item in value)
    return reasons


def validate_command(key: str, argv: Sequence[str]) -> List[str]:
    if not argv:
        return [f"{key}:missing_argv"]
    missing: List[str] = []
    for flag in REQUIRED_FLAGS.get(key, []):
        if flag.startswith("--") and flag in {"--install", "--build", "--run"}:
            if not has_flag(argv, flag):
                missing.append(f"{key}:missing_flag:{flag}")
        elif not flag_value(argv, flag):
            missing.append(f"{key}:missing_value:{flag}")
    return missing


def count_vtk(vtk_dir: Optional[Path], pattern: str) -> int:
    if vtk_dir is None or not vtk_dir.is_dir():
        return 0
    return len([path for path in vtk_dir.glob(pattern) if path.is_file()])


def setup_empty_tunnel(setup: Optional[Path]) -> Optional[bool]:
    if setup is None or not setup.is_file():
        return None
    try:
        text = setup.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    if "const bool empty_tunnel = true;" in text:
        return True
    if "const bool empty_tunnel = false;" in text:
        return False
    return None


def manifest_paths(manifest: Dict[str, Any]) -> Dict[str, Optional[Path]]:
    preflight_argv = argv_for(manifest, "PreflightNoCfd")
    run_argv = argv_for(manifest, "InstallBuildRunFluidX3D")
    profile_argv = argv_for(manifest, "AuditInletProfileAfterRun")
    correlation_argv = argv_for(manifest, "AuditInletCorrelationAfterRun")
    chain_argv = argv_for(manifest, "ValidationChainAfterRun")
    case_dir = Path(str(manifest.get("EmptyTunnelCaseDir") or "")).expanduser().resolve()
    preflight_dir = path_from_flag(preflight_argv, "--out-dir")
    vtk_dir = path_from_flag(run_argv, "--output-dir")
    if vtk_dir is None:
        profile_positional = first_positional_after_script(profile_argv)
        vtk_dir = Path(profile_positional).expanduser().resolve() if profile_positional else case_dir / "output"
    chain_out = path_from_flag(chain_argv, "--out-dir")
    if chain_out is None and case_dir:
        chain_out = case_dir / "validation_chain"
    return {
        "CaseDir": case_dir,
        "Setup": Path(str(manifest.get("SetupPath") or "")).expanduser().resolve(),
        "PreflightManifest": preflight_dir / "native_preflight_pack_manifest.json" if preflight_dir else None,
        "NativeManifest": path_from_flag(run_argv, "--out"),
        "VtkDir": vtk_dir,
        "ProfileAudit": path_from_flag(profile_argv, "--out-json"),
        "CorrelationAudit": path_from_flag(correlation_argv, "--out-json"),
        "ValidationChainManifest": chain_out / "validation_chain_manifest.json" if chain_out else None,
    }


def workflow_status(manifest_path: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
    paths = manifest_paths(manifest)
    expected = manifest.get("Expected", {}) if isinstance(manifest.get("Expected"), dict) else {}
    pattern = str(expected.get("VtkPattern") or "u-*.vtk")
    expected_frames = int(expected.get("ExpectedVtkFrameCount") or 0)
    min_frames = int(expected.get("MinVtkFrames") or expected_frames or 0)
    vtk_frames = count_vtk(paths["VtkDir"], pattern)
    profile_gate = gate_from_json(paths["ProfileAudit"], ["inlet_profile_gate", "Gate"])
    correlation_gate = gate_from_json(paths["CorrelationAudit"], ["inlet_correlation_gate", "Gate"])
    preflight_gate = gate_from_json(paths["PreflightManifest"], ["Gate"])
    chain_gate = gate_from_json(paths["ValidationChainManifest"], ["ChainStatus", "ValidationGateVerdict", "Gate"])
    setup_flag = setup_empty_tunnel(paths["Setup"])

    validation_errors: List[str] = []
    for key in REQUIRED_FLAGS:
        validation_errors.extend(validate_command(key, argv_for(manifest, key)))

    next_stage = "done"
    if setup_flag is not True:
        next_stage = "fix_empty_tunnel_case"
    elif preflight_gate == "missing":
        next_stage = "preflight"
    elif preflight_gate not in PASS_GATES:
        next_stage = "inspect_preflight_failures"
    elif vtk_frames < max(1, min_frames):
        next_stage = "run"
    elif profile_gate == "missing":
        next_stage = "profile"
    elif correlation_gate == "missing":
        next_stage = "correlation"
    elif profile_gate not in PASS_GATES or correlation_gate not in PASS_GATES:
        next_stage = "inspect_inlet_failures"
    elif chain_gate == "missing":
        next_stage = "chain"
    elif chain_gate not in PASS_GATES:
        next_stage = "inspect_validation_chain_failures"
    else:
        next_stage = "building_case_can_start_after_boundary_preconditions"

    paper_grade_ready = (
        setup_flag is True
        and preflight_gate in PASS_GATES
        and vtk_frames >= max(1, min_frames)
        and profile_gate in PASS_GATES
        and correlation_gate in PASS_GATES
        and chain_gate in PASS_GATES
        and not validation_errors
    )
    return {
        "Schema": "citylbm.native_empty_tunnel_workflow_status.v1",
        "GeneratedAtUtc": utc_now(),
        "Manifest": str(manifest_path),
        "EmptyTunnelCaseDir": str(paths["CaseDir"]) if paths["CaseDir"] else "",
        "SetupEmptyTunnel": setup_flag,
        "PreflightGate": preflight_gate,
        "PreflightReasons": reasons_from_json(paths["PreflightManifest"], ["Reasons", "reasons"]),
        "VtkDir": str(paths["VtkDir"]) if paths["VtkDir"] else "",
        "VtkPattern": pattern,
        "VtkFrameCount": vtk_frames,
        "ExpectedVtkFrameCount": expected_frames,
        "MinVtkFrames": min_frames,
        "InletProfileGate": profile_gate,
        "InletProfileReasons": reasons_from_json(paths["ProfileAudit"], ["inlet_profile_gate_reasons", "Reasons"]),
        "InletCorrelationGate": correlation_gate,
        "InletCorrelationReasons": reasons_from_json(paths["CorrelationAudit"], ["inlet_correlation_gate_reasons", "Reasons"]),
        "ValidationChainGate": chain_gate,
        "CommandValidationErrors": validation_errors,
        "NextStage": next_stage,
        "LongRunRequired": next_stage == "run",
        "PaperGradeReady": paper_grade_ready,
    }


def stage_keys(stage: str, allow_long_run: bool) -> List[str]:
    if stage == "status":
        return []
    if stage == "all":
        keys = ["PreflightNoCfd"]
        if allow_long_run:
            keys.append("InstallBuildRunFluidX3D")
        keys.extend(["AuditInletProfileAfterRun", "AuditInletCorrelationAfterRun", "ValidationChainAfterRun"])
        return keys
    return COMMAND_KEYS[stage]


def run_command(key: str, argv: Sequence[str]) -> Dict[str, Any]:
    started_at = utc_now()
    start = time.time()
    completed = subprocess.run(
        list(argv),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "Key": key,
        "Command": list(argv),
        "StartedAtUtc": started_at,
        "FinishedAtUtc": utc_now(),
        "ElapsedSeconds": round(time.time() - start, 3),
        "ReturnCode": completed.returncode,
        "Stdout": completed.stdout,
        "Stderr": completed.stderr,
    }


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = read_json(manifest_path)
    if not manifest:
        raise SystemExit(f"manifest missing or invalid: {manifest_path}")

    status = workflow_status(manifest_path, manifest)
    selected = stage_keys(args.stage, args.allow_long_run)
    execution: List[Dict[str, Any]] = []
    errors: List[str] = list(status["CommandValidationErrors"])

    if args.stage == "run" and args.execute and not args.allow_long_run:
        errors.append("run_stage_requires_--allow-long-run")
    if args.stage == "all" and args.execute and not args.allow_long_run:
        errors.append("all_stage_skips_long_run_without_--allow-long-run")

    if args.execute and not errors:
        for key in selected:
            argv = argv_for(manifest, key)
            if key == "InstallBuildRunFluidX3D" and not args.allow_long_run:
                execution.append({"Key": key, "Skipped": True, "Reason": "long_run_not_allowed"})
                continue
            execution.append(run_command(key, argv))
        status = workflow_status(manifest_path, manifest)
    elif selected:
        for key in selected:
            execution.append({"Key": key, "DryRun": True, "Command": argv_for(manifest, key)})

    report = {
        "Schema": "citylbm.native_empty_tunnel_workflow_report.v1",
        "GeneratedAtUtc": utc_now(),
        "Stage": args.stage,
        "Execute": bool(args.execute),
        "AllowLongRun": bool(args.allow_long_run),
        "Status": status,
        "Execution": execution,
        "Errors": errors,
    }
    if args.out_json:
        write_json(Path(args.out_json).expanduser().resolve(), report)

    print(
        "empty_tunnel_workflow stage={stage}; next={next_stage}; vtk_frames={frames}; "
        "profile={profile}; correlation={correlation}; chain={chain}; execute={execute}".format(
            stage=args.stage,
            next_stage=status["NextStage"],
            frames=status["VtkFrameCount"],
            profile=status["InletProfileGate"],
            correlation=status["InletCorrelationGate"],
            chain=status["ValidationChainGate"],
            execute=args.execute,
        )
    )
    if errors:
        print("errors=" + ";".join(errors))
        return 3
    if args.execute and any(int(item.get("ReturnCode", 0)) != 0 for item in execution if "ReturnCode" in item):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
