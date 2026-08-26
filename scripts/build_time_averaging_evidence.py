#!/usr/bin/env python3
"""Build fast no-CFD evidence for native VTK time-averaging readiness."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_native_fluidx3d_case import (  # noqa: E402
    audit_actual_vtk_output,
    audit_planned_vtk_schedule,
    collect_vtk_files,
    planned_vtk_steps,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a fast evidence file for planned and optional actual VTK final-window averaging."
    )
    parser.add_argument("--case-dir", required=True, help="Native case directory.")
    parser.add_argument("--out", required=True, help="Output JSON evidence path.")
    parser.add_argument("--output-dir", default="", help="Directory containing u-*.vtk. Defaults to <case-dir>/output.")
    parser.add_argument("--vtk-pattern", default="u-*.vtk")
    parser.add_argument("--time-steps", type=int, required=True)
    parser.add_argument("--vtk-save-interval", type=int, required=True)
    parser.add_argument("--vtk-save-start-step", type=int, default=None)
    parser.add_argument("--expected-vtk-frame-count", type=int, default=None)
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-vtk-frames", type=int, default=40)
    parser.add_argument("--min-vtk-step-span", type=int, default=20000)
    parser.add_argument(
        "--require-actual-vtk",
        action="store_true",
        help="Fail/diagnose if the output directory does not contain the required actual VTK files.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def planned_selected_steps(steps: Optional[Sequence[int]], average_last_n: int) -> List[int]:
    if not steps:
        return []
    count = min(len(steps), max(average_last_n, 1))
    return list(steps[-count:])


def collect_reasons(prefix: str, gate: Dict[str, Any]) -> List[str]:
    if str(gate.get("Gate") or "").strip().lower() in {"pass", "not_applicable"}:
        return []
    return [f"{prefix}:{reason}" for reason in gate.get("Reasons", []) if str(reason).strip()]


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else case_dir / "output"

    planned_steps = planned_vtk_steps(args.time_steps, args.vtk_save_interval, args.vtk_save_start_step)
    selected_planned_steps = planned_selected_steps(planned_steps, args.average_last_n)
    planned_gate = audit_planned_vtk_schedule(
        args.time_steps,
        args.vtk_save_interval,
        args.vtk_save_start_step,
        args.expected_vtk_frame_count,
        args.average_last_n,
        args.min_vtk_frames,
        args.min_vtk_step_span,
    )
    vtk_records = collect_vtk_files(output_dir, args.vtk_pattern)
    actual_gate = audit_actual_vtk_output(
        vtk_records,
        planned_gate["ComputedFrameCount"],
        planned_steps,
        args.average_last_n,
        args.min_vtk_frames,
        args.min_vtk_step_span,
        args.require_actual_vtk,
    )
    reasons = collect_reasons("planned_vtk_schedule", planned_gate)
    reasons.extend(collect_reasons("actual_vtk_output", actual_gate))
    reasons = list(dict.fromkeys(reasons))
    gate = "pass" if not reasons else "diagnostic_only"
    has_planned_blocker = any(reason.startswith("planned_vtk_schedule:") for reason in reasons)
    has_actual_blocker = any(reason.startswith("actual_vtk_output:") for reason in reasons)
    if gate == "pass":
        development_stage = "eligible_for_short_native_canary"
        development_duration = "short_cfd"
        development_runs_cfd_next = True
        development_next_cfd_scope = "short_native_canary_only"
        development_reason = "The planned final-window VTK schedule satisfies the requested frame-count and step-span gate."
    elif has_planned_blocker:
        development_stage = "revise_time_averaging_schedule_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_planned_time_averaging_gate_passes"
        development_reason = "The requested time-step/save schedule cannot produce a paper-grade final averaging window."
    elif has_actual_blocker:
        development_stage = "collect_longer_actual_vtk_average_window"
        development_duration = "medium_cfd"
        development_runs_cfd_next = True
        development_next_cfd_scope = "resume_or_rerun_until_actual_vtk_window_passes"
        development_reason = "The planned schedule is acceptable, but the actual VTK files do not yet provide the required final averaging window."
    else:
        development_stage = "fix_time_averaging_evidence_before_cfd"
        development_duration = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_time_averaging_gate_passes"
        development_reason = "Time-averaging evidence is diagnostic-only for an uncategorized reason."
    evidence = {
        "Schema": "citylbm.time_averaging_evidence.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "fast_no_cfd_time_average_and_vtk_freshness_gate",
        "CaseDir": str(case_dir),
        "OutputDir": str(output_dir),
        "VtkPattern": args.vtk_pattern,
        "Gate": gate,
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "TimeSteps": args.time_steps,
        "VtkSaveInterval": args.vtk_save_interval,
        "VtkSaveStartStep": args.vtk_save_start_step,
        "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
        "AverageLastN": args.average_last_n,
        "MinimumFrameCount": args.min_vtk_frames,
        "MinimumStepSpan": args.min_vtk_step_span,
        "PlannedVtkSteps": list(planned_steps) if planned_steps is not None else None,
        "PlannedSelectedFinalWindowSteps": selected_planned_steps,
        "PlannedVtkScheduleGate": planned_gate,
        "ActualVtkOutputGate": actual_gate,
        "development_acceleration_stage": development_stage,
        "development_acceleration_duration_class": development_duration,
        "development_acceleration_runs_cfd_next": development_runs_cfd_next,
        "development_acceleration_next_cfd_scope": development_next_cfd_scope,
        "development_acceleration_reason": development_reason,
        "long_cfd_allowed_by_time_averaging_evidence": gate == "pass",
        "NextAction": (
            "Proceed to native FluidX3D run only if Gate=pass and the same schedule is used."
            if gate == "pass"
            else "Increase time steps, VTK frame count or averaging window before spending time on a long native run."
        ),
    }
    write_json(out_path, evidence)
    print(f"time_averaging_evidence_gate={gate}; out={out_path}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate == "pass" or not args.require_actual_vtk else 2


if __name__ == "__main__":
    raise SystemExit(main())
