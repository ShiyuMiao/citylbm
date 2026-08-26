#!/usr/bin/env python3
"""Summarize the highest-priority blockers in CityLBM validation reports.

The script reads existing JSON artifacts only. It does not run CFD or modify
run folders; its purpose is to shorten the optimization loop by making the next
blocking action visible without opening long audit reports.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


NATIVE_AUDIT_NAME = "native_preconditions_audit.json"
VALIDATION_GATE_NAME = "validation_gate_report.json"
NATIVE_MANIFEST_NAME = "native_fluidx3d_baseline_manifest.json"


def load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Missing input file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return data


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        return [part.strip() for part in value.split(";") if part.strip()]
    return [value]


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "; ".join(compact(item) for item in value if compact(item))
    if isinstance(value, dict):
        pairs = []
        for key, item in value.items():
            text = compact(item)
            if text:
                pairs.append(f"{key}={text}")
        return "; ".join(pairs)
    return str(value).strip()


def status_is_blocking(value: Any) -> bool:
    text = compact(value).strip().lower()
    if not text:
        return False
    return text in {
        "fail",
        "failed",
        "false",
        "blocked",
        "not_ready",
        "not ready",
        "diagnostic_only",
        "diagnostic only",
        "risk",
    } or (
        "fail" in text
    )


def gate_failures(report: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    for key in ("failing_gates", "failed_gates"):
        for item in as_list(report.get(key)):
            text = compact(item)
            if text:
                failures.append(text)

    for item in as_list(report.get("gates")):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status_is_blocking(status):
            key = compact(item.get("key") or item.get("name") or "unknown_gate")
            evidence = compact(item.get("evidence") or item.get("reason"))
            failures.append(f"{key}: {compact(status)}" + (f" - {evidence}" if evidence else ""))
    return unique(failures)


def unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def find_report(run_dir: Path, name: str) -> Optional[Path]:
    direct = run_dir / name
    if direct.exists():
        return direct
    matches = sorted(run_dir.glob(f"**/{name}"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def append_limited(lines: List[str], title: str, values: Iterable[Any], max_items: int) -> None:
    items = [compact(value) for value in values]
    items = [item for item in items if item]
    if not items:
        return
    lines.append(title)
    for item in items[:max_items]:
        lines.append(f"- {item}")
    if len(items) > max_items:
        lines.append(f"- ... {len(items) - max_items} more")


def summarize_native(path: Path, report: Dict[str, Any], max_reasons: int) -> tuple[List[str], bool]:
    lines = [f"Native preconditions: {path}"]
    blocking = False

    gate = report.get("native_preconditions_gate") or report.get("native_precondition_closure_gate")
    if gate is not None:
        lines.append(f"- gate: {compact(gate)}")
        blocking = blocking or status_is_blocking(gate)

    accuracy_gate = report.get("accuracy_interpretation_gate")
    closure_gate = report.get("native_precondition_closure_gate")
    if accuracy_gate is not None:
        lines.append(f"- accuracy interpretation: {compact(accuracy_gate)}")
        blocking = blocking or status_is_blocking(accuracy_gate)
    if closure_gate is not None and closure_gate != gate:
        lines.append(f"- precondition closure: {compact(closure_gate)}")
        blocking = blocking or status_is_blocking(closure_gate)

    top_key = compact(report.get("native_top_blocking_priority_key"))
    if top_key:
        blocking = True
        lines.append(f"- top blocker: {top_key}")
        diagnosis = compact(report.get("native_top_blocking_priority_diagnosis"))
        action = compact(report.get("native_top_blocking_priority_next_action"))
        if diagnosis:
            lines.append(f"- diagnosis: {diagnosis}")
        if action:
            lines.append(f"- next action: {action}")
        append_limited(
            lines,
            "- reasons:",
            as_list(report.get("native_top_blocking_priority_reasons")),
            max_reasons,
        )

    append_limited(lines, "- failing gates:", gate_failures(report), max_reasons)
    return lines, blocking


def summarize_validation(path: Path, report: Dict[str, Any], max_reasons: int) -> tuple[List[str], bool]:
    lines = [f"Validation gate: {path}"]
    blocking = False

    verdict = report.get("verdict") or report.get("validation_gate") or report.get("status")
    if verdict is not None:
        lines.append(f"- verdict: {compact(verdict)}")
        blocking = blocking or status_is_blocking(verdict)

    if "paper_grade" in report:
        paper_grade = report.get("paper_grade")
        lines.append(f"- paper grade: {compact(paper_grade)}")
        blocking = blocking or paper_grade is False

    priorities = [item for item in as_list(report.get("diagnostic_priority")) if isinstance(item, dict)]
    if priorities:
        first = priorities[0]
        key = compact(first.get("key") or first.get("name"))
        if key:
            blocking = True
            lines.append(f"- top diagnostic: {key}")
        diagnosis = compact(first.get("diagnosis") or first.get("reason"))
        action = compact(first.get("required_next_action") or first.get("next_action"))
        if diagnosis:
            lines.append(f"- diagnosis: {diagnosis}")
        if action:
            lines.append(f"- next action: {action}")

    failures = gate_failures(report)
    if failures:
        blocking = True
        append_limited(lines, "- failing gates:", failures, max_reasons)
    return lines, blocking


def gate_text(report: Dict[str, Any], key: str) -> str:
    value = report.get(key)
    if isinstance(value, dict):
        return compact(value.get("Gate") or value.get("gate") or value.get("Status") or value.get("status"))
    return compact(value)


def gate_reasons(report: Dict[str, Any], key: str) -> List[str]:
    value = report.get(key)
    if not isinstance(value, dict):
        return []
    return as_list(
        value.get("Reasons")
        or value.get("reasons")
        or value.get("ReasonsCsv")
        or value.get("reasons_csv")
    )


def summarize_native_manifest(
    path: Path,
    report: Dict[str, Any],
    max_reasons: int,
) -> tuple[List[str], bool]:
    lines = [f"Native runner manifest: {path}"]
    blocking = False

    runner_gate = gate_text(report, "RunnerGate")
    accuracy_gate = gate_text(report, "NativeAccuracyEvidenceGate")
    protocol_gate = gate_text(report, "ValidationProtocolAuditGate")
    protocol_details = report.get("ValidationProtocolAuditGate")
    protocol_paper_grade_gate = ""
    protocol_pre_run_gate = ""
    if isinstance(protocol_details, dict):
        protocol_paper_grade_gate = compact(protocol_details.get("PaperGradeGate"))
        protocol_pre_run_gate = compact(protocol_details.get("PreRunGate"))
    metadata_gate = gate_text(report, "CaseMetadataPreconditionGate")
    setup_source_gate = gate_text(report, "CaseSetupSourcePreconditionGate")
    official_input_gate = gate_text(report, "OfficialInputPreconditionGate")
    synthetic_gate = gate_text(report, "PlannedSyntheticInletSamplingGate")
    runtime_inlet_gate = gate_text(report, "RuntimeInletDiagnosticsGate")
    vtk_gate = gate_text(report, "PlannedVtkScheduleGate")
    actual_vtk_gate = gate_text(report, "ActualVtkOutputGate")

    for label, value in [
        ("runner gate", runner_gate),
        ("accuracy evidence", accuracy_gate),
        ("protocol audit", protocol_gate),
        ("metadata preconditions", metadata_gate),
        ("setup source preconditions", setup_source_gate),
        ("official input preconditions", official_input_gate),
        ("planned synthetic inlet", synthetic_gate),
        ("runtime inlet diagnostics", runtime_inlet_gate),
        ("planned VTK schedule", vtk_gate),
        ("actual VTK output", actual_vtk_gate),
    ]:
        if value:
            lines.append(f"- {label}: {value}")
            blocking = blocking or status_is_blocking(value)
            if label == "protocol audit":
                if protocol_pre_run_gate:
                    lines.append(f"- protocol pre-run gate: {protocol_pre_run_gate}")
                    blocking = blocking or status_is_blocking(protocol_pre_run_gate)
                if protocol_paper_grade_gate:
                    lines.append(f"- protocol paper-grade gate: {protocol_paper_grade_gate}")
                    blocking = blocking or status_is_blocking(protocol_paper_grade_gate)

    shared = report.get("SharedRunConditions")
    schedule = report.get("PlannedVtkScheduleGate")
    if isinstance(shared, dict):
        recommended_steps = compact(shared.get("RecommendedMinimumTimeStepsForCurrentSaveInterval"))
        if recommended_steps:
            lines.append(f"- recommended minimum steps for current save interval: {recommended_steps}")
    if isinstance(schedule, dict):
        recommended_average_last_n = compact(schedule.get("RecommendedAverageLastNForStepSpan"))
        expected_span = compact(schedule.get("FinalWindowStepSpan"))
        if recommended_average_last_n:
            lines.append(f"- recommended AverageLastN: {recommended_average_last_n}")
        if expected_span:
            lines.append(f"- planned final-window step span: {expected_span}")

    if runner_gate and runner_gate.lower() != "pass":
        lines.append("- accelerated next stage: fix native runner/source/case setup before launching CFD")
    elif protocol_gate and protocol_gate.lower() != "pass":
        lines.append("- accelerated next stage: close AIJ protocol evidence before launching CFD")
    elif metadata_gate and metadata_gate.lower() != "pass":
        lines.append("- accelerated next stage: regenerate case metadata from the corrected CityLBM setup")
    elif setup_source_gate and setup_source_gate.lower() != "pass":
        lines.append("- accelerated next stage: regenerate setup.cpp from CustomTable AF/k inputs before launching CFD")
    elif official_input_gate and official_input_gate.lower() not in {"pass", "not_applicable"}:
        lines.append("- accelerated next stage: fix AF/RS/Uref/wind-vector inputs before launching CFD")
    elif synthetic_gate and synthetic_gate.lower() != "pass":
        lines.append("- accelerated next stage: fix inlet sampling plan before launching CFD")
    elif runtime_inlet_gate and runtime_inlet_gate.lower() not in {"pass", "not_applicable"}:
        lines.append("- accelerated next stage: fix runtime inlet U/k/RMS preservation with short canaries before any paper-length run")
    elif vtk_gate and vtk_gate.lower() != "pass":
        lines.append("- accelerated next stage: increase time steps, save interval, or AverageLastN before launching CFD")
    elif accuracy_gate and accuracy_gate.lower() == "pass":
        lines.append("- accelerated next stage: run post-run validation chain and compare probes")
    elif actual_vtk_gate in {"not_applicable", "missing", ""}:
        lines.append("- accelerated next stage: preflight is clean enough to launch the real FluidX3D run")
    else:
        lines.append("- accelerated next stage: inspect VTK output evidence and run validation chain")

    for key in [
        "RunnerGate",
        "NativeAccuracyEvidenceGate",
        "ValidationProtocolAuditGate",
        "CaseMetadataPreconditionGate",
        "CaseSetupSourcePreconditionGate",
        "OfficialInputPreconditionGate",
        "PlannedSyntheticInletSamplingGate",
        "RuntimeInletDiagnosticsGate",
        "PlannedVtkScheduleGate",
        "ActualVtkOutputGate",
    ]:
        append_limited(lines, f"- {key} reasons:", gate_reasons(report, key), max_reasons)

    return lines, blocking


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=Path("."),
        help="Run directory used to auto-find validation JSON reports.",
    )
    parser.add_argument("--native-preconditions", type=Path, help=f"Path to {NATIVE_AUDIT_NAME}.")
    parser.add_argument("--validation-gate", type=Path, help=f"Path to {VALIDATION_GATE_NAME}.")
    parser.add_argument("--native-manifest", type=Path, help=f"Path to {NATIVE_MANIFEST_NAME}.")
    parser.add_argument("--max-reasons", type=int, default=8, help="Maximum listed reasons per section.")
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Exit with code 2 when a blocking validation item is found.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    run_dir = args.run_dir.resolve()
    native_path = args.native_preconditions or find_report(run_dir, NATIVE_AUDIT_NAME)
    validation_path = args.validation_gate or find_report(run_dir, VALIDATION_GATE_NAME)
    native_manifest_path = args.native_manifest or find_report(run_dir, NATIVE_MANIFEST_NAME)

    if native_path is None and validation_path is None and native_manifest_path is None:
        print(f"No validation reports found under {run_dir}", file=sys.stderr)
        return 1

    sections: List[str] = []
    blockers = False
    if native_manifest_path is not None:
        lines, blocking = summarize_native_manifest(
            native_manifest_path,
            load_json(native_manifest_path),
            args.max_reasons,
        )
        sections.extend(lines)
        blockers = blockers or blocking
    if native_path is not None:
        if sections:
            sections.append("")
        lines, blocking = summarize_native(native_path, load_json(native_path), args.max_reasons)
        sections.extend(lines)
        blockers = blockers or blocking
    if validation_path is not None:
        if sections:
            sections.append("")
        lines, blocking = summarize_validation(
            validation_path, load_json(validation_path), args.max_reasons
        )
        sections.extend(lines)
        blockers = blockers or blocking

    print("\n".join(sections))
    if args.fail_on_blockers and blockers:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
