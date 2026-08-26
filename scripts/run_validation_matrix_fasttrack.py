#!/usr/bin/env python3
"""Run fast-track validation gates for multiple AIJ cases in parallel.

This is a development-time compressor. It does not launch paper-length CFD.
Each selected case delegates to run_validation_fasttrack.py, then this script
collects the next command and gate status into one aggregate manifest.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


MIN_DEFAULT_OUTPUT_FREE_BYTES = 2 * 1024 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run CityLBM validation fast-track gates for Case A and/or Case E "
            "in parallel, then write one aggregate manifest."
        )
    )
    parser.add_argument("--fluidx3d-source", required=True)
    parser.add_argument("--casea-dir", default="")
    parser.add_argument("--casee-dir", default="")
    parser.add_argument("--casea-official", default="")
    parser.add_argument("--casea-af-csv", default="")
    parser.add_argument("--casee-official", default="")
    parser.add_argument("--casee-af-csv", default="")
    parser.add_argument(
        "--solver-root",
        default="",
        help="Optional root for later per-case solver working directories.",
    )
    parser.add_argument("--out-root", default="")
    parser.add_argument(
        "--case-jobs",
        type=int,
        default=0,
        help="Maximum number of cases to run concurrently. Defaults to all selected cases.",
    )
    parser.add_argument(
        "--child-jobs",
        type=int,
        default=0,
        help="Worker count passed to each per-case no-CFD fasttrack.",
    )
    parser.add_argument("--serial-child", action="store_true")
    parser.add_argument("--patch-metadata-identity", action="store_true")
    parser.add_argument(
        "--fail-on-long-cfd-blocked",
        action="store_true",
        help="Return 2 when any selected case still blocks paper-length CFD.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def disk_free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    return int(shutil.disk_usage(str(probe)).free)


def default_out_root(repo: Path, stamp: str, min_free_bytes: int = MIN_DEFAULT_OUTPUT_FREE_BYTES) -> Tuple[Path, Dict[str, Any]]:
    repo_free = disk_free_bytes(repo)
    name = f"matrix_fasttrack_{stamp}"
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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def add_optional(command: List[str], flag: str, value: Any) -> None:
    text = str(value or "").strip()
    if text:
        command.extend([flag, text])


def selected_cases(args: argparse.Namespace) -> List[Dict[str, str]]:
    cases: List[Dict[str, str]] = []
    if args.casea_dir.strip():
        cases.append(
            {
                "case": "casea",
                "case_dir": args.casea_dir,
                "official": args.casea_official,
                "af_csv": args.casea_af_csv,
            }
        )
    if args.casee_dir.strip():
        cases.append(
            {
                "case": "casee",
                "case_dir": args.casee_dir,
                "official": args.casee_official,
                "af_csv": args.casee_af_csv,
            }
        )
    return cases


def case_solver_cwd(args: argparse.Namespace, case_name: str) -> str:
    if not args.solver_root.strip():
        return ""
    return str(Path(args.solver_root).expanduser().resolve() / case_name)


def build_case_command(
    *,
    repo: Path,
    args: argparse.Namespace,
    case_spec: Dict[str, str],
    out_root: Path,
) -> List[str]:
    case_name = case_spec["case"]
    command = [
        sys.executable,
        str(repo / "scripts" / "run_validation_fasttrack.py"),
        "--case",
        case_name,
        "--case-dir",
        str(Path(case_spec["case_dir"]).expanduser().resolve()),
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()),
        "--out-root",
        str(out_root / case_name),
    ]
    add_optional(command, "--official", case_spec.get("official"))
    add_optional(command, "--af-csv", case_spec.get("af_csv"))
    add_optional(command, "--solver-cwd", case_solver_cwd(args, case_name))
    if args.child_jobs > 0:
        command.extend(["--jobs", str(args.child_jobs)])
    if args.serial_child:
        command.append("--serial")
    if args.patch_metadata_identity:
        command.append("--patch-metadata-identity")
    if args.fail_on_long_cfd_blocked:
        command.append("--fail-on-long-cfd-blocked")
    return command


def run_case(case_spec: Dict[str, str], command: Sequence[str]) -> Dict[str, Any]:
    completed = subprocess.run(
        list(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out_root = Path(command[command.index("--out-root") + 1])
    manifest_path = out_root / "validation_fasttrack_manifest.json"
    manifest = read_json(manifest_path)
    return {
        "case": case_spec["case"],
        "case_dir": str(Path(case_spec["case_dir"]).expanduser().resolve()),
        "return_code": completed.returncode,
        "command": list(command),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "manifest": str(manifest_path),
        "manifest_found": manifest_path.is_file(),
        "preflight_gate": manifest.get("preflight_gate", ""),
        "diagnostic_canary_allowed_now": bool(manifest.get("diagnostic_canary_allowed_now")),
        "long_cfd_allowed_now": bool(manifest.get("long_cfd_allowed_now")),
        "next_execution_policy": manifest.get("next_execution_policy", ""),
        "next_batch_name": manifest.get("next_batch_name", ""),
        "next_command": manifest.get("next_command", ""),
        "preflight_reasons": manifest.get("preflight_reasons", []),
        "artifacts": manifest.get("artifacts", {}),
    }


def case_workers(selected_count: int, requested: int) -> int:
    if selected_count <= 1:
        return 1
    if requested > 0:
        return max(1, min(requested, selected_count))
    return selected_count


def aggregate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    long_ready = [item["case"] for item in results if item.get("long_cfd_allowed_now")]
    canary_ready = [item["case"] for item in results if item.get("diagnostic_canary_allowed_now")]
    blocked = [item["case"] for item in results if not item.get("long_cfd_allowed_now")]
    failed = [item["case"] for item in results if int(item.get("return_code", 1)) not in {0, 2}]
    first_blocker: Optional[Dict[str, Any]] = None
    for item in results:
        if item.get("long_cfd_allowed_now"):
            continue
        first_blocker = {
            "case": item.get("case"),
            "next_execution_policy": item.get("next_execution_policy"),
            "next_batch_name": item.get("next_batch_name"),
            "next_command": item.get("next_command"),
            "preflight_reasons": item.get("preflight_reasons", [])[:8]
            if isinstance(item.get("preflight_reasons"), list)
            else [],
        }
        break
    return {
        "selected_case_count": len(results),
        "failed_case_processes": failed,
        "diagnostic_canary_ready_cases": canary_ready,
        "long_cfd_ready_cases": long_ready,
        "long_cfd_blocked_cases": blocked,
        "all_long_cfd_ready": len(blocked) == 0 and not failed,
        "first_blocker": first_blocker or {},
        "time_saved_by": [
            "parallel_case_fasttracks",
            "parallel_no_cfd_audits_inside_each_case",
            "single_manifest_for_next_action_selection",
            "long_cfd_started_only_after_preflight_and_canary_gates",
        ],
    }


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    cases = selected_cases(args)
    if not cases:
        print("No cases selected. Provide --casea-dir and/or --casee-dir.", file=sys.stderr)
        return 2

    if args.out_root.strip():
        out_root = Path(args.out_root).expanduser().resolve()
        output_placement = {"mode": "explicit_out_root"}
    else:
        out_root, output_placement = default_out_root(repo, timestamp())
    out_root.mkdir(parents=True, exist_ok=True)

    commands = [
        build_case_command(repo=repo, args=args, case_spec=case_spec, out_root=out_root)
        for case_spec in cases
    ]
    workers = case_workers(len(cases), args.case_jobs)
    results_by_index: Dict[int, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_case, case_spec, command): index
            for index, (case_spec, command) in enumerate(zip(cases, commands))
        }
        for future in concurrent.futures.as_completed(futures):
            results_by_index[futures[future]] = future.result()
    results = [results_by_index[index] for index in range(len(cases))]

    manifest = {
        "schema": "citylbm.validation_matrix_fasttrack.v1",
        "generated_at_utc": utc_now(),
        "purpose": "shorten_validation_development_by_running_case_fasttracks_in_parallel",
        "fluidx3d_source": str(Path(args.fluidx3d_source).expanduser().resolve()),
        "out_root": str(out_root),
        "output_placement": output_placement,
        "case_workers": workers,
        "child_jobs": args.child_jobs,
        "cases": results,
        "summary": aggregate_summary(results),
    }
    manifest_path = out_root / "validation_matrix_fasttrack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    summary = manifest["summary"]
    print(f"validation_matrix_fasttrack_manifest={manifest_path}")
    print(f"out_root={out_root}")
    print(f"case_workers={workers}")
    print(f"diagnostic_canary_ready_cases={','.join(summary['diagnostic_canary_ready_cases'])}")
    print(f"long_cfd_ready_cases={','.join(summary['long_cfd_ready_cases'])}")
    print(f"long_cfd_blocked_cases={','.join(summary['long_cfd_blocked_cases'])}")
    blocker = summary.get("first_blocker") or {}
    if blocker.get("next_command"):
        print("next_command=" + str(blocker["next_command"]))

    failed = summary["failed_case_processes"]
    if failed:
        return 1
    if args.fail_on_long_cfd_blocked and not summary["all_long_cfd_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
