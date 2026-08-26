#!/usr/bin/env python3
"""Run the fastest safe CityLBM validation iteration.

This command intentionally keeps long CFD outside the automatic path. It runs
the parallel no-CFD preflight pack, then turns the resulting artifacts into a
single acceleration plan and manifest so each code change has one repeatable
go/no-go check.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

MIN_DEFAULT_OUTPUT_FREE_BYTES = 2 * 1024 * 1024 * 1024


CASE_PRESETS: Dict[str, Dict[str, Any]] = {
    "casea": {
        "expected_aij_case": "CaseA",
        "expected_wind_direction": "N",
        "expected_wind_vector": "1,0,0",
        "expected_probe_row_count": 186,
        "expected_probe_z_min": 0.01,
        "expected_probe_z_max": 0.28,
        "z_ref": 0.16,
        "expected_uref": 4.491,
    },
    "casee": {
        "expected_aij_case": "CaseE",
        "expected_wind_direction": "N",
        "expected_wind_vector": "0,-1,0",
        "official_condition_filter": "ac",
        "official_wind_filter": "N",
        "expected_probe_row_count": 80,
        "expected_probe_z": 2.0,
        "z_ref": 15.9,
        "expected_uref": 3.928296,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run CityLBM/FluidX3D validation fast-track gates: parallel no-CFD "
            "preflight plus next-step acceleration plan. This does not launch "
            "a long solver run."
        )
    )
    parser.add_argument("--case", choices=sorted(CASE_PRESETS), required=True)
    parser.add_argument("--case-dir", required=True, help="CityLBM generated native case directory.")
    parser.add_argument("--fluidx3d-source", required=True, help="Explicit native FluidX3D source root.")
    parser.add_argument("--solver-cwd", default="", help="Optional later FluidX3D working directory.")
    parser.add_argument("--official", default="", help="Official RS/probe CSV.")
    parser.add_argument("--af-csv", default="", help="Official AF inlet CSV.")
    parser.add_argument(
        "--out-root",
        default="",
        help=(
            "Output root. Defaults to <repo>/validation_runs/<case>_fasttrack_<timestamp> "
            "when the repo drive has enough free space; otherwise uses the system temp drive."
        ),
    )
    parser.add_argument("--jobs", type=int, default=0, help="Worker count for independent no-CFD checks.")
    parser.add_argument("--serial", action="store_true", help="Run preflight steps sequentially for debugging.")
    parser.add_argument(
        "--patch-metadata-identity",
        action="store_true",
        help="Patch case metadata identity fields before auditing.",
    )
    parser.add_argument(
        "--fail-on-long-cfd-blocked",
        action="store_true",
        help="Return code 2 when the resulting plan does not allow a paper-length CFD run yet.",
    )
    return parser.parse_args()


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def disk_free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    return int(shutil.disk_usage(str(probe)).free)


def default_out_root(repo: Path, case: str, stamp: str, min_free_bytes: int = MIN_DEFAULT_OUTPUT_FREE_BYTES) -> tuple[Path, Dict[str, Any]]:
    repo_free = disk_free_bytes(repo)
    name = f"{case}_fasttrack_{stamp}"
    if repo_free >= min_free_bytes:
        return repo / "validation_runs" / name, {
            "mode": "repo_validation_runs",
            "repo_free_bytes": repo_free,
            "min_default_output_free_bytes": min_free_bytes,
        }
    return Path(tempfile.gettempdir()) / "CityLBM_validation_runs" / name, {
        "mode": "temp_due_to_low_repo_disk_free",
        "repo_free_bytes": repo_free,
        "min_default_output_free_bytes": min_free_bytes,
        "temp_root": tempfile.gettempdir(),
    }


def run_command(name: str, command: List[str]) -> Dict[str, Any]:
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "name": name,
        "command": command,
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def add_optional(command: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value)
    if text:
        command.extend([flag, text])


def shell_quote(value: Any) -> str:
    text = str(value)
    escaped = text.replace('"', '\\"')
    return f'"{escaped}"'


def command_line(command: Any) -> str:
    if isinstance(command, list):
        return " ".join(shell_quote(part) for part in command)
    return str(command)


def build_local_bind_command(args: argparse.Namespace, out_root: Path) -> str:
    command = [
        sys.executable,
        "scripts\\bind_inlet_reynolds_stress_metadata.py",
        "--metadata",
        str(Path(args.case_dir).expanduser().resolve() / "case_metadata.json"),
        "--stress-csv",
        str(out_root / "inlet_reynolds_stress_tensor_template.csv"),
        "--out",
        str(out_root / "case_metadata.reynolds_bound.json"),
        "--source-note",
        "Identity binding only; keep diagnostic until full tensor or precursor audit passes.",
    ]
    return " ".join(shell_quote(part) for part in command)


def canary_runtime_bind_command(out_root: Path) -> Dict[str, Any]:
    command = [
        sys.executable,
        "scripts\\bind_canary_runtime_evidence.py",
        "--run-dir",
        str(out_root),
        "--out",
        str(out_root / "canary_runtime_evidence_manifest.json"),
    ]
    return {
        "name": "bind_canary_runtime_evidence_after_audits",
        "use_class": "diagnostic_runtime_evidence_binding_not_for_paper_accuracy_claims",
        "prerequisite": "run_native_diagnostic_canary and both post-canary inlet audits completed",
        "command": command,
        "command_line": command_line(command),
    }


def suggested_commands(preflight_manifest: Dict[str, Any], names: List[str]) -> List[Dict[str, Any]]:
    triage = preflight_manifest.get("DevelopmentTriage", {})
    raw_commands = triage.get("SuggestedCommands", []) if isinstance(triage, dict) else []
    if not isinstance(raw_commands, list):
        return []
    name_set = set(names)
    by_name = {
        str(item.get("Name", "")): item
        for item in raw_commands
        if isinstance(item, dict) and str(item.get("Name", "")) in name_set
    }
    selected: List[Dict[str, Any]] = []
    for name in names:
        item = by_name.get(name)
        if not item:
            continue
        command = item.get("Command", [])
        selected.append(
            {
                "name": name,
                "use_class": item.get("UseClass", ""),
                "prerequisite": item.get("Prerequisite", ""),
                "command": command,
                "command_line": command_line(command),
            }
        )
    return selected


def build_next_step_plan(
    args: argparse.Namespace,
    out_root: Path,
    summary: Dict[str, Any],
    preflight_manifest: Dict[str, Any],
    diagnostic_canary_allowed: bool,
    long_cfd_allowed: bool,
) -> Dict[str, Any]:
    planned_next_command = str(summary.get("next_command", ""))
    if "bind_inlet_reynolds_stress_metadata.py" in planned_next_command:
        planned_next_command = build_local_bind_command(args, out_root)

    result: Dict[str, Any] = {
        "next_execution_policy": summary.get("next_execution_policy", ""),
        "next_batch_name": summary.get("next_batch_name", ""),
        "next_command": planned_next_command,
        "next_commands": [],
        "post_canary_audit_commands": [],
        "original_next_execution_policy": summary.get("next_execution_policy", ""),
        "original_next_batch_name": summary.get("next_batch_name", ""),
        "original_next_command": planned_next_command,
    }
    if long_cfd_allowed or not diagnostic_canary_allowed:
        return result

    canary_commands = suggested_commands(
        preflight_manifest,
        [
            "run_native_diagnostic_canary",
            "audit_runtime_inlet_diagnostics_after_canary",
            "audit_inlet_correlation_after_canary",
        ],
    )
    if not canary_commands:
        return result

    result["next_execution_policy"] = "run_short_native_canary_then_post_audits"
    result["next_batch_name"] = "short_native_canary"
    result["next_command"] = canary_commands[0]["command_line"]
    bind_command = canary_runtime_bind_command(out_root)
    result["next_commands"] = canary_commands + [bind_command]
    result["post_canary_audit_commands"] = canary_commands[1:] + [bind_command]
    return result


def build_preflight_command(args: argparse.Namespace, repo: Path, out_root: Path) -> List[str]:
    preset = CASE_PRESETS[args.case]
    command = [
        sys.executable,
        str(repo / "scripts" / "run_native_preflight_pack.py"),
        "--case-dir",
        str(Path(args.case_dir).expanduser().resolve()),
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()),
        "--out-dir",
        str(out_root),
        "--manifest-out",
        str(out_root / "native_fluidx3d_baseline_manifest.json"),
        "--expected-aij-case",
        preset["expected_aij_case"],
        "--expected-wind-direction",
        preset["expected_wind_direction"],
        "--expected-wind-vector",
        preset["expected_wind_vector"],
        "--expected-probe-row-count",
        str(preset["expected_probe_row_count"]),
        "--z-ref",
        str(preset["z_ref"]),
        "--expected-uref",
        str(preset["expected_uref"]),
        "--require-af-k",
        "--allow-diagnostic",
    ]
    add_optional(command, "--solver-cwd", args.solver_cwd)
    add_optional(command, "--official", args.official)
    add_optional(command, "--af-csv", args.af_csv)
    add_optional(command, "--official-condition-filter", preset.get("official_condition_filter"))
    add_optional(command, "--official-wind-filter", preset.get("official_wind_filter"))
    add_optional(command, "--expected-probe-z", preset.get("expected_probe_z"))
    add_optional(command, "--expected-probe-z-min", preset.get("expected_probe_z_min"))
    add_optional(command, "--expected-probe-z-max", preset.get("expected_probe_z_max"))
    if args.jobs > 0:
        command.extend(["--jobs", str(args.jobs)])
    if args.serial:
        command.append("--serial")
    if args.patch_metadata_identity:
        command.append("--patch-metadata-identity")
    return command


def build_plan_command(args: argparse.Namespace, repo: Path, out_root: Path) -> List[str]:
    command = [
        sys.executable,
        str(repo / "scripts" / "plan_validation_acceleration.py"),
        "--case",
        args.case,
        "--run-dir",
        str(out_root),
        "--case-dir",
        str(Path(args.case_dir).expanduser().resolve()),
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()),
        "--template-preflight-dir",
        str(out_root),
        "--out-json",
        str(out_root / "validation_acceleration_plan.json"),
        "--out-md",
        str(out_root / "validation_acceleration_plan.md"),
    ]
    add_optional(command, "--solver-cwd", args.solver_cwd)
    add_optional(command, "--official", args.official)
    add_optional(command, "--af-csv", args.af_csv)
    return command


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.out_root:
        out_root = Path(args.out_root).expanduser().resolve()
        output_placement = {"mode": "explicit_out_root"}
    else:
        out_root, output_placement = default_out_root(repo, args.case, timestamp())
    out_root.mkdir(parents=True, exist_ok=True)

    steps: List[Dict[str, Any]] = []
    preflight = run_command("run_native_preflight_pack", build_preflight_command(args, repo, out_root))
    steps.append(preflight)
    plan = run_command("plan_validation_acceleration", build_plan_command(args, repo, out_root))
    steps.append(plan)

    preflight_manifest = read_json(out_root / "native_preflight_pack_manifest.json")
    acceleration_plan = read_json(out_root / "validation_acceleration_plan.json")
    summary = acceleration_plan.get("acceleration_summary", {})
    diagnostic_canary = preflight_manifest.get("DiagnosticCanaryGate", {})
    long_cfd_allowed = bool(summary.get("long_cfd_allowed_now"))
    diagnostic_canary_allowed = str(diagnostic_canary.get("Gate", "")).lower() == "pass"
    next_step_plan = build_next_step_plan(
        args=args,
        out_root=out_root,
        summary=summary,
        preflight_manifest=preflight_manifest,
        diagnostic_canary_allowed=diagnostic_canary_allowed,
        long_cfd_allowed=long_cfd_allowed,
    )
    failed_steps = [step for step in steps if int(step["return_code"]) not in {0, 2}]
    manifest = {
        "schema": "citylbm.validation_fasttrack.v1",
        "case": args.case,
        "case_dir": str(Path(args.case_dir).expanduser().resolve()),
        "fluidx3d_source": str(Path(args.fluidx3d_source).expanduser().resolve()),
        "out_root": str(out_root),
        "output_placement": output_placement,
        "long_cfd_allowed_now": long_cfd_allowed,
        "diagnostic_canary_allowed_now": diagnostic_canary_allowed,
        "next_execution_policy": next_step_plan["next_execution_policy"],
        "next_batch_name": next_step_plan["next_batch_name"],
        "next_command": next_step_plan["next_command"],
        "next_commands": next_step_plan["next_commands"],
        "post_canary_audit_commands": next_step_plan["post_canary_audit_commands"],
        "original_next_execution_policy": next_step_plan["original_next_execution_policy"],
        "original_next_batch_name": next_step_plan["original_next_batch_name"],
        "original_next_command": next_step_plan["original_next_command"],
        "preflight_gate": preflight_manifest.get("Gate", ""),
        "preflight_reasons": preflight_manifest.get("Reasons", []),
        "diagnostic_canary_gate": diagnostic_canary,
        "artifacts": {
            "preflight_manifest": str(out_root / "native_preflight_pack_manifest.json"),
            "acceleration_plan_json": str(out_root / "validation_acceleration_plan.json"),
            "acceleration_plan_md": str(out_root / "validation_acceleration_plan.md"),
        },
        "steps": steps,
    }
    fasttrack_manifest = out_root / "validation_fasttrack_manifest.json"
    fasttrack_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"validation_fasttrack_manifest={fasttrack_manifest}")
    print(f"out_root={out_root}")
    print(f"output_placement={output_placement.get('mode', '')}")
    print(f"preflight_gate={manifest['preflight_gate']}")
    print(f"diagnostic_canary_allowed_now={str(diagnostic_canary_allowed).lower()}")
    print(f"long_cfd_allowed_now={str(long_cfd_allowed).lower()}")
    if manifest["next_command"]:
        print("next_command=" + str(manifest["next_command"]))
    if manifest["post_canary_audit_commands"]:
        print(f"post_canary_audit_command_count={len(manifest['post_canary_audit_commands'])}")
    if failed_steps:
        return 1
    if args.fail_on_long_cfd_blocked and not long_cfd_allowed:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
