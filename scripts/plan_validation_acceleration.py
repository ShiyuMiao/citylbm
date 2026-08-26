#!/usr/bin/env python3
"""Plan the fastest safe CityLBM/FluidX3D validation optimization loop.

The planner reads existing manifests, metrics and gate reports only. It does
not run CFD. Its purpose is to shorten development by preventing long
FluidX3D/CityLBM runs until cheap evidence gates are clean.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


PASS = "pass"
FAILISH = {"fail", "failed", "false", "blocked", "diagnostic_only", "not_ready"}

NATIVE_MANIFEST = "native_fluidx3d_baseline_manifest.json"
NATIVE_PRECONDITIONS = "native_preconditions_audit.json"
VALIDATION_GATE = "validation_gate_report.json"
FLUIDX3D_EQUILIBRIUM_BOUNDARY = "fluidx3d_equilibrium_boundary_audit.json"
INLET_SOURCE_AUDIT = "inlet_source_audit.json"
INLET_REYNOLDS_STRESS_EVIDENCE = "inlet_reynolds_stress_evidence.json"
BOUNDARY_SOURCE_AUDIT = "boundary_source_audit.json"
BOUNDARY_PROTOCOL_AUDIT = "boundary_protocol_audit.json"
COORDINATE_PROBE_PROTOCOL_AUDIT = "coordinate_probe_protocol_audit.json"
VALIDATION_PROTOCOL_AUDIT = "validation_protocol_audit.json"
NATIVE_PREFLIGHT_PACK = "native_preflight_pack_manifest.json"
TIME_AVERAGING_EVIDENCE = "time_averaging_evidence.json"
INLET_DIAGNOSTICS_CSV_AUDIT = "inlet_diagnostics_csv_audit.json"
INLET_CORRELATION_AUDIT = "inlet_correlation_audit.json"
CANARY_RUNTIME_EVIDENCE = "canary_runtime_evidence_manifest.json"
COMPONENT_SENSITIVITY_AUDIT = "component_sensitivity_audit.json"
CUSTOM_PROFILE_AF_FIDELITY_AUDIT = "custom_profile_af_fidelity_audit.json"

CASE_PRESETS: Dict[str, Dict[str, Any]] = {
    "casee": {
        "case_label": "CaseE",
        "wind_label": "N",
        "wind_vector": "0,-1,0",
        "official_condition_filter": "ac",
        "official_wind_filter": "N",
        "expected_probe_rows": 80,
        "expected_probe_z": 2.0,
        "z_ref": 15.9,
        "u_ref": 3.928296,
        "require_af_k": True,
        "canary_dx_m": 5.0,
        "paper_dx_m": 2.5,
        "canary_steps": 2000,
        "paper_steps": 40000,
        "save_interval": 1000,
        "average_last_n": 40,
        "min_step_span": 20000,
    },
    "casea": {
        "case_label": "CaseA",
        "wind_label": "N",
        "wind_vector": "1,0,0",
        "expected_probe_rows": 186,
        "expected_probe_z": None,
        "expected_probe_z_min": 0.01,
        "expected_probe_z_max": 0.28,
        "z_ref": 0.16,
        "u_ref": 4.491,
        "require_af_k": True,
        "canary_dx_m": 3.0,
        "paper_dx_m": 2.0,
        "canary_steps": 5000,
        "paper_steps": 40000,
        "save_interval": 1000,
        "average_last_n": 40,
        "min_step_span": 20000,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read CityLBM/FluidX3D validation artifacts and produce the shortest "
            "safe next-step plan. This command never launches the solver."
        )
    )
    parser.add_argument(
        "--case",
        choices=["casea", "casee", "auto"],
        default="auto",
        help="Validation case preset used for recommended commands.",
    )
    parser.add_argument(
        "--run-dir",
        action="append",
        default=[],
        help="Existing run directory. Repeat to compare multiple attempts.",
    )
    parser.add_argument("--case-dir", default="", help="Case package directory for command templates.")
    parser.add_argument("--fluidx3d-source", default="", help="Native FluidX3D source root for command templates.")
    parser.add_argument(
        "--template-preflight-dir",
        default="",
        help="Directory used for generated preflight/audit command outputs; defaults to <case-dir>\\preflight.",
    )
    parser.add_argument(
        "--solver-cwd",
        default="",
        help="Optional FluidX3D working directory for command templates; VTK output is written below this path.",
    )
    parser.add_argument("--official", default="", help="Official RS/probe CSV for command templates.")
    parser.add_argument("--af-csv", default="", help="Official AF inlet CSV for command templates.")
    parser.add_argument("--out-json", default="", help="Optional JSON plan output.")
    parser.add_argument("--out-md", default="", help="Optional Markdown plan output.")
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Return code 2 when the fastest next action is still blocking paper-grade validation.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def planned_frame_count(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int],
) -> Optional[int]:
    if time_steps is None or save_interval is None or time_steps <= 0 or save_interval <= 0:
        return None
    first_step = save_interval if save_start_step is None or save_start_step <= 0 else save_start_step
    if first_step > time_steps:
        return 0
    return ((time_steps - first_step) // save_interval) + 1


def case_runtime_settings(args: argparse.Namespace, preset: Dict[str, Any]) -> Dict[str, Any]:
    settings: Dict[str, Any] = {
        "paper_steps": int(preset["paper_steps"]),
        "save_interval": int(preset["save_interval"]),
        "save_start_step": None,
        "expected_frame_count": int(preset["average_last_n"]),
        "average_last_n": int(preset["average_last_n"]),
        "min_step_span": int(preset["min_step_span"]),
        "source": "case_preset",
    }
    if not args.case_dir:
        return settings
    metadata = load_json(Path(args.case_dir) / "case_metadata.json")
    vtk = metadata.get("VtkOutput") if isinstance(metadata.get("VtkOutput"), dict) else {}
    time_steps = as_int(metadata.get("TimeSteps") or metadata.get("SimulationSteps") or metadata.get("Steps"))
    save_interval = as_int(vtk.get("SaveIntervalSteps") or vtk.get("SaveInterval"))
    save_start = as_int(vtk.get("SaveStartStep") or vtk.get("StartStep"))
    expected_frames = as_int(vtk.get("EstimatedPostSpinupFrameCount") or vtk.get("ExpectedFrameCount"))
    if time_steps is not None and time_steps > 0:
        settings["paper_steps"] = time_steps
        settings["source"] = "case_metadata"
    if save_interval is not None and save_interval > 0:
        settings["save_interval"] = save_interval
        settings["source"] = "case_metadata"
    if save_start is not None:
        settings["save_start_step"] = save_start
        settings["source"] = "case_metadata"
    computed_frames = planned_frame_count(
        settings["paper_steps"],
        settings["save_interval"],
        settings["save_start_step"],
    )
    if expected_frames is not None:
        settings["expected_frame_count"] = expected_frames
        settings["source"] = "case_metadata"
    elif computed_frames is not None:
        settings["expected_frame_count"] = computed_frames
    return settings


def find_report(run_dir: Path, name: str) -> Optional[Path]:
    direct = run_dir / name
    if direct.exists():
        return direct
    matches = sorted(run_dir.glob(f"**/{name}"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def find_report_any(search_dirs: Sequence[Path], name: str) -> Optional[Path]:
    matches = [path for path in (find_report(directory, name) for directory in search_dirs) if path]
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(compact(item) for item in value if compact(item))
    if isinstance(value, dict):
        gate = value.get("Gate") or value.get("gate") or value.get("status") or value.get("Status")
        if gate is not None:
            return compact(gate)
        return "; ".join(f"{key}={compact(item)}" for key, item in value.items() if compact(item))
    return str(value).strip()


def gate_text(report: Dict[str, Any], key: str) -> str:
    return compact(report.get(key)).lower()


def gate_reasons(report: Dict[str, Any], key: str) -> List[str]:
    value = report.get(key)
    if not isinstance(value, dict):
        return []
    raw = value.get("Reasons") or value.get("reasons") or value.get("ReasonsCsv") or ""
    if isinstance(raw, list):
        return [compact(item) for item in raw if compact(item)]
    return [part.strip() for part in str(raw).split(";") if part.strip()]


def is_blocking(value: Any) -> bool:
    text = compact(value).lower()
    if not text:
        return False
    return text in FAILISH or "fail" in text or "diagnostic_only" in text


def is_pass(value: Any) -> bool:
    return compact(value).lower() == PASS


def canary_runtime_passed(report: Optional[Dict[str, Any]]) -> bool:
    data = report or {}
    return is_pass(data.get("Gate")) or is_pass(data.get("CanaryRuntimeGate"))


def reason_closed_by_canary_runtime(reason: Any, report: Optional[Dict[str, Any]]) -> bool:
    if not canary_runtime_passed(report):
        return False
    text = compact(reason).lower()
    closed_tokens = [
        "runtime_inlet_diagnostics_csv_missing_or_failed",
        "runtime_inlet_diagnostics_audit_missing",
        "runtime_inlet_diagnostics_gate_not_pass",
        "inlet_correlation_audit_missing",
        "inlet_correlation_frame_count_below_minimum",
        "inlet_correlation_gate_not_pass",
        "inlet_correlation_runtime_source_",
        "inlet_correlation_source_",
        "inlet_correlation_step_span_too_short",
        "inlet_k_variance_gate_not_pass",
        "inlet_tke_gate_not_pass",
    ]
    return any(token in text for token in closed_tokens)


def first_failing_gate(report: Dict[str, Any]) -> Dict[str, str]:
    for gate in report.get("gates", []):
        if not isinstance(gate, dict):
            continue
        status = gate.get("status")
        if is_blocking(status):
            return {
                "key": compact(gate.get("key") or gate.get("name") or "unknown_gate"),
                "status": compact(status),
                "evidence": compact(gate.get("evidence") or gate.get("reason")),
                "next_action": compact(gate.get("required_next_action") or gate.get("next_action")),
            }
    return {}


def collect_failures(
    manifest: Dict[str, Any],
    native: Dict[str, Any],
    gate: Dict[str, Any],
    fluidx3d_boundary: Optional[Dict[str, Any]] = None,
    inlet_source: Optional[Dict[str, Any]] = None,
    inlet_reynolds_stress: Optional[Dict[str, Any]] = None,
    boundary_source: Optional[Dict[str, Any]] = None,
    boundary_protocol: Optional[Dict[str, Any]] = None,
    coordinate_probe_protocol: Optional[Dict[str, Any]] = None,
    validation_protocol: Optional[Dict[str, Any]] = None,
    native_preflight_pack: Optional[Dict[str, Any]] = None,
    time_averaging_evidence: Optional[Dict[str, Any]] = None,
    inlet_diagnostics_csv: Optional[Dict[str, Any]] = None,
    inlet_correlation_audit: Optional[Dict[str, Any]] = None,
    canary_runtime_evidence: Optional[Dict[str, Any]] = None,
    component_sensitivity: Optional[Dict[str, Any]] = None,
    custom_profile_af_fidelity: Optional[Dict[str, Any]] = None,
) -> List[str]:
    failures: List[str] = []
    for key in [
        "ValidationProtocolAuditGate",
        "CaseMetadataPreconditionGate",
        "CaseSetupSourcePreconditionGate",
        "OfficialInputPreconditionGate",
        "PreExecutionGate",
        "PlannedSyntheticInletSamplingGate",
        "PlannedVtkScheduleGate",
        "RunnerGate",
        "ActualVtkOutputGate",
        "NativeAccuracyEvidenceGate",
        "PaperUseGate",
    ]:
        status = gate_text(manifest, key)
        if is_blocking(status):
            reasons = gate_reasons(manifest, key)
            failures.append(f"{key}:{status}" + (f" ({'; '.join(reasons[:3])})" if reasons else ""))

    for key in [
        "native_preconditions_gate",
        "accuracy_interpretation_gate",
        "native_precondition_closure_gate",
    ]:
        status = compact(native.get(key)).lower()
        if is_blocking(status):
            failures.append(f"{key}:{status}")

    first_gate = first_failing_gate(gate)
    if first_gate:
        failures.append(
            "validation_gate:{key}:{status}".format(
                key=first_gate.get("key", "unknown_gate"),
                status=first_gate.get("status", "fail"),
            )
        )
    protocol_report = validation_protocol or {}
    if protocol_report:
        for key in ["Gate", "PaperGradeGate", "PreRunGate"]:
            status = compact(protocol_report.get(key)).lower()
            if is_blocking(status):
                reasons = (
                    protocol_report.get("PreRunFailKeys")
                    if key == "PreRunGate"
                    else protocol_report.get("FailKeys")
                )
                if not isinstance(reasons, list):
                    reasons = [reasons] if reasons else []
                reason_text = "; ".join(compact(item) for item in reasons if compact(item))
                failures.append(
                    f"{VALIDATION_PROTOCOL_AUDIT}:{key}:{status}"
                    + (f" ({reason_text})" if reason_text else "")
                )
        for key in ["RiskKeys", "PreRunRiskKeys"]:
            risks = protocol_report.get(key)
            if isinstance(risks, list) and risks:
                failures.append(
                    f"{VALIDATION_PROTOCOL_AUDIT}:{key} ({'; '.join(compact(item) for item in risks if compact(item))})"
                )
    preflight_pack_report = native_preflight_pack or {}
    preflight_pack_status = compact(preflight_pack_report.get("Gate")).lower()
    if is_blocking(preflight_pack_status):
        raw_reasons = preflight_pack_report.get("Reasons") or preflight_pack_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        raw_reasons = [
            item
            for item in raw_reasons
            if not reason_closed_by_canary_runtime(item, canary_runtime_evidence)
        ]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{NATIVE_PREFLIGHT_PACK}:{preflight_pack_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    time_averaging_report = time_averaging_evidence or {}
    time_averaging_status = compact(time_averaging_report.get("Gate")).lower()
    if is_blocking(time_averaging_status):
        raw_reasons = time_averaging_report.get("Reasons") or time_averaging_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{TIME_AVERAGING_EVIDENCE}:{time_averaging_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    runtime_inlet_report = inlet_diagnostics_csv or {}
    runtime_inlet_status = compact(runtime_inlet_report.get("Gate")).lower()
    if is_blocking(runtime_inlet_status):
        raw_reasons = runtime_inlet_report.get("Reasons") or runtime_inlet_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{INLET_DIAGNOSTICS_CSV_AUDIT}:{runtime_inlet_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    runtime_inlet_gate = compact(
        (manifest.get("RuntimeInletDiagnosticsGate") or {}).get("Gate")
        if isinstance(manifest.get("RuntimeInletDiagnosticsGate"), dict)
        else ""
    ).lower()
    if is_blocking(runtime_inlet_gate):
        runtime_inlet_reasons = gate_reasons(manifest, "RuntimeInletDiagnosticsGate")
        failures.append(
            f"RuntimeInletDiagnosticsGate:{runtime_inlet_gate}"
            + (f" ({'; '.join(runtime_inlet_reasons[:3])})" if runtime_inlet_reasons else "")
        )
    inlet_correlation_report = inlet_correlation_audit or {}
    inlet_correlation_status = compact(
        inlet_correlation_report.get("inlet_correlation_gate") or inlet_correlation_report.get("Gate")
    ).lower()
    if is_blocking(inlet_correlation_status):
        raw_reasons = (
            inlet_correlation_report.get("inlet_correlation_gate_reasons")
            or inlet_correlation_report.get("Reasons")
            or inlet_correlation_report.get("reasons")
            or []
        )
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{INLET_CORRELATION_AUDIT}:{inlet_correlation_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    canary_runtime_report = canary_runtime_evidence or {}
    canary_runtime_status = compact(canary_runtime_report.get("Gate")).lower()
    if is_blocking(canary_runtime_status):
        raw_reasons = canary_runtime_report.get("Reasons") or canary_runtime_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{CANARY_RUNTIME_EVIDENCE}:{canary_runtime_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    component_report = component_sensitivity or {}
    if component_report:
        for key in [
            "component_normalization_gate",
            "component_sensitivity_gate",
            "normalization_scale_gate",
            "streamwise_sign_gate",
            "component_source_window_gate",
        ]:
            status = compact(component_report.get(key)).lower()
            if is_blocking(status):
                raw_reasons = component_report.get(f"{key}_reasons") or []
                if not isinstance(raw_reasons, list):
                    raw_reasons = [raw_reasons]
                reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
                failures.append(
                    f"{COMPONENT_SENSITIVITY_AUDIT}:{key}:{status}"
                    + (f" ({reason_text})" if reason_text else "")
                )
    custom_profile_report = custom_profile_af_fidelity or {}
    custom_profile_status = compact(
        custom_profile_report.get("custom_profile_af_fidelity_gate")
        or custom_profile_report.get("Gate")
        or custom_profile_report.get("gate")
    ).lower()
    if is_blocking(custom_profile_status):
        raw_reasons = custom_profile_report.get("Reasons") or custom_profile_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{CUSTOM_PROFILE_AF_FIDELITY_AUDIT}:{custom_profile_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    inlet_report = inlet_source or {}
    if inlet_report:
        for key in ["inlet_source_gate", "paper_grade_inlet_source_gate"]:
            status = compact(inlet_report.get(key)).lower()
            if is_blocking(status):
                reason_key = f"{key}_reasons"
                reasons = inlet_report.get(reason_key) or inlet_report.get("reasons") or []
                if not isinstance(reasons, list):
                    reasons = [reasons]
                reason_text = "; ".join(compact(item) for item in reasons if compact(item))
                failures.append(f"{key}:{status}" + (f" ({reason_text})" if reason_text else ""))
    inlet_reynolds_report = inlet_reynolds_stress or {}
    if inlet_reynolds_report:
        for key in ["paper_grade_gate", "gate"]:
            status = compact(inlet_reynolds_report.get(key)).lower()
            if is_blocking(status):
                raw_reasons = inlet_reynolds_report.get("reasons") or inlet_reynolds_report.get("Reasons") or []
                if not isinstance(raw_reasons, list):
                    raw_reasons = [raw_reasons]
                reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
                source_type = compact(inlet_reynolds_report.get("source_type"))
                failures.append(
                    f"{INLET_REYNOLDS_STRESS_EVIDENCE}:{key}:{status}"
                    + (f":{source_type}" if source_type else "")
                    + (f" ({reason_text})" if reason_text else "")
                )
    boundary_report = boundary_source or {}
    if boundary_report:
        for key in ["boundary_source_gate", "paper_grade_boundary_source_gate"]:
            status = compact(boundary_report.get(key)).lower()
            if is_blocking(status):
                reason_key = f"{key}_reasons"
                reasons = boundary_report.get(reason_key) or boundary_report.get("reasons") or []
                if not isinstance(reasons, list):
                    reasons = [reasons]
                reason_text = "; ".join(compact(item) for item in reasons if compact(item))
                failures.append(f"{key}:{status}" + (f" ({reason_text})" if reason_text else ""))
    boundary_protocol_report = boundary_protocol or {}
    boundary_protocol_status = compact(
        boundary_protocol_report.get("boundary_protocol_gate")
        or boundary_protocol_report.get("Gate")
        or boundary_protocol_report.get("gate")
    ).lower()
    if is_blocking(boundary_protocol_status):
        raw_reasons = (
            boundary_protocol_report.get("boundary_protocol_gate_reasons")
            or boundary_protocol_report.get("FailKeys")
            or boundary_protocol_report.get("Reasons")
            or boundary_protocol_report.get("reasons")
            or []
        )
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{BOUNDARY_PROTOCOL_AUDIT}:{boundary_protocol_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    coordinate_probe_report = coordinate_probe_protocol or {}
    coordinate_probe_status = compact(
        coordinate_probe_report.get("coordinate_probe_protocol_gate")
        or coordinate_probe_report.get("Gate")
        or coordinate_probe_report.get("gate")
    ).lower()
    if is_blocking(coordinate_probe_status):
        raw_reasons = (
            coordinate_probe_report.get("Reasons")
            or coordinate_probe_report.get("reasons")
            or coordinate_probe_report.get("FailKeys")
            or []
        )
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{COORDINATE_PROBE_PROTOCOL_AUDIT}:{coordinate_probe_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
    boundary_report = fluidx3d_boundary or {}
    boundary_status = compact(boundary_report.get("Gate")).lower()
    if is_blocking(boundary_status):
        raw_reasons = boundary_report.get("Reasons") or boundary_report.get("reasons") or []
        if not isinstance(raw_reasons, list):
            raw_reasons = [raw_reasons]
        reason_text = "; ".join(compact(item) for item in raw_reasons if compact(item))
        failures.append(
            f"{FLUIDX3D_EQUILIBRIUM_BOUNDARY}:{boundary_status}"
            + (f" ({reason_text})" if reason_text else "")
        )
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


def unique_paths(items: Iterable[Path]) -> List[Path]:
    seen = set()
    result = []
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def classify_next_action(
    manifest: Dict[str, Any],
    native: Dict[str, Any],
    gate: Dict[str, Any],
    fluidx3d_boundary: Optional[Dict[str, Any]] = None,
    inlet_source: Optional[Dict[str, Any]] = None,
    inlet_reynolds_stress: Optional[Dict[str, Any]] = None,
    boundary_source: Optional[Dict[str, Any]] = None,
    boundary_protocol: Optional[Dict[str, Any]] = None,
    coordinate_probe_protocol: Optional[Dict[str, Any]] = None,
    validation_protocol: Optional[Dict[str, Any]] = None,
    native_preflight_pack: Optional[Dict[str, Any]] = None,
    time_averaging_evidence: Optional[Dict[str, Any]] = None,
    inlet_diagnostics_csv: Optional[Dict[str, Any]] = None,
    inlet_correlation_audit: Optional[Dict[str, Any]] = None,
    canary_runtime_evidence: Optional[Dict[str, Any]] = None,
    component_sensitivity: Optional[Dict[str, Any]] = None,
    custom_profile_af_fidelity: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not any([manifest, native, gate, fluidx3d_boundary, inlet_source, inlet_reynolds_stress, boundary_source, boundary_protocol, coordinate_probe_protocol, validation_protocol, native_preflight_pack, time_averaging_evidence, inlet_diagnostics_csv, inlet_correlation_audit, canary_runtime_evidence, component_sensitivity, custom_profile_af_fidelity]):
        return action(
            1,
            "create_case_and_preflight",
            "minutes",
            False,
            "No validation artifacts were found.",
            "Generate a fresh case package, then run the native preflight manifest without --run.",
        )

    setup_gate = gate_text(manifest, "CaseSetupSourcePreconditionGate")
    official_gate = gate_text(manifest, "OfficialInputPreconditionGate")
    metadata_gate = gate_text(manifest, "CaseMetadataPreconditionGate")
    protocol_gate = gate_text(manifest, "ValidationProtocolAuditGate")
    pre_execution_gate = gate_text(manifest, "PreExecutionGate")
    native_preflight_pack_gate = compact((native_preflight_pack or {}).get("Gate")).lower()
    boundary_report = fluidx3d_boundary or {}
    boundary_status = compact(boundary_report.get("Gate")).lower()
    boundary_evidence = boundary_report.get("Evidence") if isinstance(boundary_report.get("Evidence"), dict) else {}
    boundary_macros = boundary_report.get("EnabledMacros") if isinstance(boundary_report.get("EnabledMacros"), dict) else {}
    source_hook_available = all(
        bool(boundary_evidence.get(key))
        for key in [
            "has_reconstruct_equilibrium_kernel",
            "has_reconstruct_feq_from_rho_u",
            "has_reconstruct_store_f",
            "has_lbm_kernel_binding",
            "has_lbm_public_call",
        ]
    )
    source_patch_possible = all(
        bool(boundary_evidence.get(key))
        for key in [
            "has_type_e_define",
            "has_equilibrium_boundaries_macro",
            "has_reconstruct_feq_from_rho_u",
            "has_reconstruct_store_f",
            "has_stream_collide_type_e_macro_velocity",
            "has_stream_collide_type_e_feq_collision",
        ]
    )
    reconstruction_macro_enabled = bool(boundary_macros.get("RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF")) or bool(
        boundary_macros.get("RECONSTRUCT_INLET_STRESS_DDF")
    )
    if is_blocking(boundary_status) and not source_hook_available and source_patch_possible:
        return action(
            1,
            "patch_fluidx3d_equilibrium_boundary_source",
            "minutes",
            False,
            "FluidX3D has TYPE_E equilibrium primitives, but the explicit source hook and LBM binding are missing.",
            "Run scripts\\patch_fluidx3d_equilibrium_boundary_source.py on the selected FluidX3D source, then rerun the boundary audit and case-level DDF enabler before any CFD run.",
        )
    if is_blocking(boundary_status) and source_hook_available and not reconstruction_macro_enabled:
        return action(
            1,
            "enable_fluidx3d_ddf_reconstruction_route",
            "minutes",
            False,
            "FluidX3D source exposes the TYPE_E/DDF reconstruction hook, but the current generated case does not enable the reconstruction macro.",
            "Regenerate or patch the case defines/setup so RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF or RECONSTRUCT_INLET_STRESS_DDF is enabled before any new CFD run.",
        )

    joined_failures = " ".join(
        collect_failures(
            manifest,
            native,
            gate,
            fluidx3d_boundary,
            inlet_source,
            inlet_reynolds_stress,
            boundary_source,
            boundary_protocol,
            coordinate_probe_protocol,
            validation_protocol,
            native_preflight_pack,
            time_averaging_evidence,
            inlet_diagnostics_csv,
            inlet_correlation_audit,
            canary_runtime_evidence,
            component_sensitivity,
            custom_profile_af_fidelity,
        )
    ).lower()
    custom_profile_report = custom_profile_af_fidelity or {}
    custom_profile_status = compact(
        custom_profile_report.get("custom_profile_af_fidelity_gate")
        or custom_profile_report.get("Gate")
        or custom_profile_report.get("gate")
    ).lower()
    if is_blocking(custom_profile_status):
        return action(
            1,
            "fix_official_af_profile_ingestion",
            "minutes",
            False,
            compact(custom_profile_report.get("Reasons"))
            or "The generated CustomProfile does not match the official AF z,U,k table.",
            "Regenerate the case with the full official AF CSV bound into CustomProfile before any new long FluidX3D run.",
        )
    inlet_report = inlet_source or {}
    inlet_acceleration_stage = compact(inlet_report.get("development_acceleration_stage")).lower()
    inlet_acceleration_runs_cfd = inlet_report.get("development_acceleration_runs_cfd_next")
    if inlet_acceleration_stage and inlet_acceleration_runs_cfd is False:
        if inlet_acceleration_stage == "resolve_reynolds_stress_tensor_or_precursor_evidence":
            reynolds_report = inlet_reynolds_stress or {}
            raw_reynolds_reasons = reynolds_report.get("reasons") or reynolds_report.get("Reasons") or []
            if not isinstance(raw_reynolds_reasons, list):
                raw_reynolds_reasons = [raw_reynolds_reasons]
            reynolds_reason_text = " ".join(compact(item) for item in raw_reynolds_reasons).lower()
            if (
                "stress_csv_sha256_missing_in_metadata" in reynolds_reason_text
                or "stress_csv_sha256_mismatch_current_metadata" in reynolds_reason_text
                or "precursor_case_metadata_sha256_missing" in reynolds_reason_text
                or "precursor_case_metadata_sha256_mismatch" in reynolds_reason_text
            ):
                return action(
                    1,
                    "bind_reynolds_stress_evidence_to_current_case",
                    "minutes",
                    False,
                    "The Reynolds-stress or precursor evidence is not explicitly bound to the current case metadata hash and source hash.",
                    "Add the matching stress CSV SHA256 or precursor case_metadata_sha256/case/wind binding to case_metadata, then rerun the no-CFD preflight.",
                )
            if (
                "stress_csv_no_valid_full_tensor_rows" in reynolds_reason_text
                or "measured_stress_tensor_requires_at_least_two_valid_heights" in reynolds_reason_text
                or "missing_offdiagonal" in reynolds_reason_text
            ):
                return action(
                    1,
                    "populate_reynolds_stress_tensor_or_precursor_template",
                    "minutes",
                    False,
                    "The evidence file is present but does not contain a usable full Reynolds-stress tensor or precursor record.",
                    "Fill the generated tensor template with measured or justified tensor values, or link a traceable precursor/equivalent-inlet evidence JSON before any paper-length run.",
                )
            return action(
                1,
                "resolve_reynolds_stress_offdiagonal_or_precursor_gap",
                "minutes",
                False,
                compact(inlet_report.get("development_acceleration_reason"))
                or "The inlet source passes implementation checks, but paper-grade turbulent inflow evidence is incomplete.",
                "Use the diagnostic inlet only for canaries. Before paper-length CFD, add a full Reynolds-stress tensor or traceable precursor/equivalent-inlet evidence and rerun audit_inlet_source.py.",
            )
        if inlet_acceleration_stage == "resolve_turbulent_length_scale_evidence":
            return action(
                1,
                "resolve_turbulent_length_scale_evidence",
                "minutes",
                False,
                compact(inlet_report.get("development_acceleration_reason"))
                or "The inlet source lacks a traceable turbulent length-scale evidence basis.",
                "Link an official, precursor, recycling or validated length-scale evidence source in metadata before launching a paper-length run.",
            )
        if inlet_acceleration_stage == "replace_uncorrelated_random_inlet_before_cfd":
            return action(
                1,
                "replace_uncorrelated_random_inlet_before_cfd",
                "code_then_short_cfd",
                False,
                compact(inlet_report.get("development_acceleration_reason"))
                or "The generated inlet still appears to use uncorrelated RMS noise.",
                "Replace the inlet with the correlated synthetic-eddy/DDF reconstruction route, then run only a short native canary.",
            )
        if "distribution_consistent" in inlet_acceleration_stage:
            inlet_route_gate = compact(inlet_report.get("inlet_distribution_route_gate")).lower()
            inlet_route = compact(inlet_report.get("inlet_distribution_route")).lower()
            gate_reasons_text = "; ".join(
                compact(item)
                for item in inlet_report.get("inlet_source_gate_reasons", [])
                if compact(item)
            )
            gate_reasons_lower = gate_reasons_text.lower()
            if inlet_route_gate == "pass" and "reconstruct" in inlet_route:
                if (
                    "custom_table_source_missing_profile_origin_z_m" in gate_reasons_lower
                    or "custom_table_source_not_origin_aware_for_profile_height" in gate_reasons_lower
                ):
                    return action(
                        1,
                        "patch_legacy_customtable_profile_origin",
                        "minutes",
                        False,
                        gate_reasons_text
                        or "The inlet DDF reconstruction path is present, but legacy CustomTable height sampling is not origin-aware.",
                        "Patch the generated legacy setup.cpp to sample AF CustomTable profiles in physical metres using domain_origin.json, then rerun audit_inlet_source.py.",
                    )
                return action(
                    1,
                    "fix_advanced_turbulence_evidence_before_cfd",
                    "code_then_short_cfd",
                    False,
                    gate_reasons_text
                    or compact(inlet_report.get("development_acceleration_reason"))
                    or "The inlet DDF reconstruction path is present, but the advanced turbulent-inlet evidence is still incomplete.",
                    "Do not repeat the DDF macro patch. Add origin-aware CustomTable profile height and real digital-filter/SEM state evidence, then rerun audit_inlet_source.py before any CFD.",
                )
            return action(
                1,
                "fix_distribution_consistent_inlet_source_before_cfd",
                "code_then_short_cfd",
                False,
                compact(inlet_report.get("development_acceleration_reason"))
                or "The inlet source has not proven distribution-consistent treatment.",
                "Fix generated setup/defines so the macroscopic inlet update is coupled to TYPE_E DDF reconstruction before any new CFD.",
            )
        return action(
            1,
            "fix_inlet_source_evidence_before_cfd",
            "minutes",
            False,
            compact(inlet_report.get("development_acceleration_reason"))
            or "The inlet source audit reports unresolved evidence blockers.",
            "Close audit_inlet_source.py blockers first; do not spend solver time until the source-level gate is clear.",
        )

    boundary_report = boundary_source or {}
    boundary_acceleration_stage = compact(boundary_report.get("development_acceleration_stage")).lower()
    boundary_acceleration_runs_cfd = boundary_report.get("development_acceleration_runs_cfd_next")
    if boundary_acceleration_stage and boundary_acceleration_runs_cfd is False:
        return action(
            1,
            "resolve_boundary_and_wall_protocol_evidence",
            compact(boundary_report.get("development_acceleration_duration_class")) or "minutes",
            False,
            compact(boundary_report.get("development_acceleration_reason"))
            or "Boundary source audit reports unresolved paper-grade source blockers.",
            "Close audit_boundary_source.py blockers first; do not spend solver time until the source-level boundary gate is clear.",
        )

    boundary_protocol_report = boundary_protocol or {}
    boundary_protocol_acceleration_stage = compact(
        boundary_protocol_report.get("development_acceleration_stage")
    ).lower()
    boundary_protocol_acceleration_runs_cfd = boundary_protocol_report.get(
        "development_acceleration_runs_cfd_next"
    )
    if boundary_protocol_acceleration_stage and boundary_protocol_acceleration_runs_cfd is False:
        return action(
            1,
            "resolve_boundary_and_wall_protocol_evidence",
            compact(boundary_protocol_report.get("development_acceleration_duration_class")) or "minutes",
            False,
            compact(boundary_protocol_report.get("development_acceleration_reason"))
            or "Boundary protocol audit reports unresolved paper-grade evidence blockers.",
            "Close audit_boundary_protocol.py blockers first; do not spend solver time until the boundary protocol gate is clear.",
        )

    if any(is_blocking(item) for item in [setup_gate, official_gate, metadata_gate, protocol_gate, pre_execution_gate, native_preflight_pack_gate]):
        if (
            "measured_diagonal_rms_missing_off_diagonal_covariances_not_paper_grade_full_tensor" in joined_failures
        ):
            return action(
                1,
                "resolve_reynolds_stress_offdiagonal_or_precursor_gap",
                "minutes",
                False,
                "The AF file provides measured diagonal RMS components, so the isotropic-k fallback is no longer the main issue; the remaining inlet evidence gap is missing off-diagonal covariance or precursor-equivalent evidence.",
                "Use the diagonal RMS path for diagnostic canaries, but collect/derive off-diagonal Reynolds-stress or a traceable precursor/equivalent-inlet evidence file before claiming paper-grade turbulent inflow.",
            )
        if (
            "source_missing_measured_or_precursor_reynolds_stress_tensor_evidence" in joined_failures
            or "isotropic_k_assumption_only_not_paper_grade_reynolds_stress" in joined_failures
            or "inlet_reynolds_stress:" in joined_failures
        ):
            return action(
                1,
                "resolve_inlet_reynolds_stress_evidence",
                "minutes",
                False,
                "The native inlet source is distribution-consistent, but the paper-grade gate lacks measured or precursor Reynolds-stress tensor evidence.",
                "Either add a traceable Reynolds-stress tensor/precursor evidence file, or explicitly keep this as an isotropic-k diagnostic route before spending time on a long CFD run.",
            )
        if any(token in joined_failures for token in ["inlet", "profile_k", "turbulence", "synthetic", "correlation", "velocity_only"]):
            return action(
                1,
                "fix_turbulent_inlet_evidence",
                "code_then_short_cfd",
                True,
                "Pre-run protocol gates show inlet U/k/turbulence fidelity is blocking the native baseline.",
                "Fix the native inlet source first: AF z,U,k binding, correlated turbulence evidence and distribution-consistency or an explicit precursor/SEM route.",
            )
        if any(token in joined_failures for token in ["boundary", "roughness", "wall", "fetch", "outlet", "side_top"]):
            return action(
                1,
                "fix_boundary_and_wall_protocol",
                "code_then_short_cfd",
                True,
                "Pre-run protocol gates show boundary or wall-treatment evidence is blocking the native baseline.",
                "Close boundary-source and rough-wall/development evidence before launching another long CFD run.",
            )
        return action(
            1,
            "fix_codegen_inputs_before_solver",
            "minutes",
            False,
            "Cheap preflight gates are not clean; launching FluidX3D would waste time.",
            "Fix setup.cpp metadata, AF/RS/Uref/wind-vector binding, protocol audit or source parity first.",
        )

    coordinate_report = coordinate_probe_protocol or {}
    coordinate_acceleration_stage = compact(coordinate_report.get("development_acceleration_stage")).lower()
    coordinate_acceleration_runs_cfd = coordinate_report.get("development_acceleration_runs_cfd_next")
    if coordinate_acceleration_stage and coordinate_acceleration_runs_cfd is False:
        return action(
            1,
            "resolve_coordinate_probe_uref_protocol",
            compact(coordinate_report.get("development_acceleration_duration_class")) or "minutes",
            False,
            compact(coordinate_report.get("development_acceleration_reason"))
            or "Coordinate/probe/Uref protocol audit reports unresolved blockers.",
            "Close audit_coordinate_probe_protocol.py blockers first; rerun postprocessing on the same VTK if available before launching new CFD.",
        )

    time_report = time_averaging_evidence or {}
    time_acceleration_stage = compact(time_report.get("development_acceleration_stage")).lower()
    time_acceleration_runs_cfd = time_report.get("development_acceleration_runs_cfd_next")
    if time_acceleration_stage and time_acceleration_runs_cfd is False:
        return action(
            1,
            "verify_time_averaging_schedule",
            compact(time_report.get("development_acceleration_duration_class")) or "minutes",
            False,
            compact(time_report.get("development_acceleration_reason"))
            or "The planned averaging schedule cannot produce a paper-grade final window.",
            "Increase time steps, save interval/start, expected frame count or average-last-n before launching the next CFD run.",
        )
    if time_acceleration_stage == "collect_longer_actual_vtk_average_window":
        return action(
            2,
            "increase_time_averaging_before_physics_tuning",
            compact(time_report.get("development_acceleration_duration_class")) or "medium_cfd",
            True,
            compact(time_report.get("development_acceleration_reason"))
            or "The actual VTK output window is too short for paper-grade averaging.",
            "Resume or rerun the native case until build_time_averaging_evidence.py reports a passing actual VTK final window.",
        )

    actual_vtk_gate = gate_text(manifest, "ActualVtkOutputGate")
    run_gate = gate_text(manifest.get("Run", {}) if isinstance(manifest.get("Run"), dict) else {}, "Gate")
    run_requested = manifest.get("Run", {}).get("Requested") if isinstance(manifest.get("Run"), dict) else None
    if not run_requested or actual_vtk_gate in {"not_applicable", ""} or is_blocking(actual_vtk_gate) or is_blocking(run_gate):
        return action(
            2,
            "launch_native_canary_or_resume_solver",
            "short_cfd",
            True,
            "Preflight is clean enough, but no fresh VTK evidence is available.",
            "Run a short native FluidX3D canary first; promote to the paper-length run only if VTK hashes and field sanity checks pass.",
        )

    component_report = component_sensitivity or {}
    if component_report:
        component_source_window_gate = compact(component_report.get("component_source_window_gate")).lower()
        component_gate = compact(component_report.get("component_normalization_gate")).lower()
        component_choice_gate = compact(component_report.get("component_sensitivity_gate")).lower()
        normalization_gate = compact(component_report.get("normalization_scale_gate")).lower()
        streamwise_gate = compact(component_report.get("streamwise_sign_gate")).lower()
        if is_blocking(component_source_window_gate):
            return action(
                3,
                "increase_time_averaging_before_physics_tuning",
                "medium_cfd",
                True,
                "The component/Uref audit exists, but it is based on an insufficient or stale VTK source window.",
                "Regenerate probe_audit.csv and component_sensitivity_audit.json from a longer final VTK window before tuning physics.",
            )
        if any(is_blocking(item) for item in [component_gate, component_choice_gate, normalization_gate, streamwise_gate]):
            return action(
                2,
                "fix_probe_component_normalization",
                "minutes",
                False,
                "Existing VTK evidence suggests velocity component, wind-vector sign or Uref scaling can explain the validation error.",
                "Fix postprocessing/metadata and rerun component_sensitivity_audit.py on the same VTK before launching new CFD.",
            )

    first_gate = first_failing_gate(gate)
    first_key = first_gate.get("key", "").lower()
    native_top = compact(native.get("native_top_blocking_priority_key")).lower()
    joined = " ".join([first_key, native_top, joined_failures]).lower()

    if any(token in joined for token in ["time", "avg", "window", "stationarity", "vtk"]):
        return action(
            3,
            "increase_time_averaging_before_physics_tuning",
            "medium_cfd",
            True,
            "The current result is dominated by insufficient final-window evidence.",
            "Increase steps/save schedule to meet the final-window frame and step-span gate before changing physics.",
        )
    if any(
        token in joined
        for token in [
            "inlet_diagnostics",
            "mean_u_rel_error",
            "k_rel_error",
            "rms_rel_error",
            "reynolds_stress",
            "crossflow_ratio",
        ]
    ):
        return action(
            2,
            "fix_runtime_inlet_statistics_before_long_run",
            "short_cfd",
            True,
            "The short run emitted inlet diagnostics, and the measured runtime inlet statistics do not preserve the requested AF U/k/RMS/Reynolds-stress profile.",
            "Tune or fix the inlet generator with short canaries until audit_inlet_diagnostics_csv.py passes; do not launch a paper-length run yet.",
        )
    if any(token in joined for token in ["inlet", "profile_k", "turbulence", "synthetic", "correlation", "velocity_only"]):
        return action(
            3,
            "fix_turbulent_inlet_evidence",
            "code_then_short_cfd",
            True,
            "The dominant blocker is inlet U/k/turbulence fidelity.",
            "Implement or verify correlated U,k inlet behavior in native FluidX3D first, then migrate the same source into CityLBM.",
        )
    if any(token in joined for token in ["boundary", "roughness", "wall", "fetch", "outlet", "side_top"]):
        return action(
            4,
            "fix_boundary_and_wall_protocol",
            "code_then_short_cfd",
            True,
            "The dominant blocker is boundary, roughness or wall-treatment evidence.",
            "Close boundary-source and runtime boundary-face gates before interpreting remaining probe error.",
        )
    if any(token in joined for token in ["probe", "component", "normalization", "coordinate", "uref", "wind"]):
        return action(
            2,
            "fix_probe_component_normalization",
            "minutes",
            False,
            "Probe mapping, velocity component or normalization is still ambiguous.",
            "Fix postprocessing/metadata and rerun the evidence chain on the same VTK before launching new CFD.",
        )
    if "mean_velocity" in joined or "systematic_bias" in joined or "accuracy" in joined:
        return action(
            5,
            "run_targeted_native_sensitivity",
            "medium_cfd",
            True,
            "Prerequisites appear closer to closed, but accuracy still fails.",
            "Run one-factor native sensitivity tests for dx, inlet length scale, wall roughness and averaging; migrate only improving settings.",
        )

    verdict = compact(gate.get("verdict")).lower()
    if verdict == PASS:
        return action(
            6,
            "migrate_verified_native_settings_to_citylbm",
            "code_then_parity",
            True,
            "The native validation gate passed.",
            "Freeze the native manifest, migrate the same settings into CityLBM, then run native-CityLBM parity.",
        )

    return action(
        3,
        "summarize_unknown_blocker",
        "minutes",
        False,
        "Artifacts exist, but the highest-priority blocker is not classified.",
        "Run summarize_validation_blockers.py and inspect the first failing gate before adding new simulations.",
    )


def action(rank: int, phase: str, duration_class: str, runs_cfd: bool, reason: str, next_action: str) -> Dict[str, Any]:
    return {
        "rank": rank,
        "phase": phase,
        "duration_class": duration_class,
        "runs_cfd": runs_cfd,
        "reason": reason,
        "next_action": next_action,
    }


def supplemental_actions_from_failures(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    joined = " ".join(
        failure
        for run in runs
        for failure in run.get("failures", [])
        if isinstance(failure, str)
    ).lower()
    items: List[Dict[str, Any]] = []
    coordinate_reports = [
        run.get("coordinate_probe_protocol", {})
        for run in runs
        if isinstance(run.get("coordinate_probe_protocol", {}), dict)
    ]
    coordinate_report_present = any(report for report in coordinate_reports)
    coordinate_report_blocked = any(
        is_blocking(report.get("coordinate_probe_protocol_gate") or report.get("Gate") or report.get("gate"))
        for report in coordinate_reports
    )
    time_averaging_reports = [
        run.get("time_averaging_evidence", {})
        for run in runs
        if isinstance(run.get("time_averaging_evidence", {}), dict)
    ]
    time_averaging_report_passed = any(compact(report.get("Gate")).lower() == PASS for report in time_averaging_reports)
    runtime_inlet_reports = [
        run.get("inlet_diagnostics_csv", {})
        for run in runs
        if isinstance(run.get("inlet_diagnostics_csv", {}), dict)
    ]
    runtime_inlet_report_blocked = any(
        is_blocking(report.get("Gate") or report.get("gate") or report.get("status"))
        for report in runtime_inlet_reports
    )
    component_reports = [
        run.get("component_sensitivity", {})
        for run in runs
        if isinstance(run.get("component_sensitivity", {}), dict)
    ]
    component_report_blocked = any(
        is_blocking(report.get("component_normalization_gate"))
        or is_blocking(report.get("component_sensitivity_gate"))
        or is_blocking(report.get("normalization_scale_gate"))
        or is_blocking(report.get("streamwise_sign_gate"))
        for report in component_reports
    )
    coordinate_text_blocked_without_report = (
        not coordinate_report_present
        and any(token in joined for token in ["coordinate_probe", "probe_projection", "uref", "component", "official_probe"])
    )
    if coordinate_report_blocked or coordinate_text_blocked_without_report or component_report_blocked:
        items.append(
            action(
                2,
                "resolve_coordinate_probe_uref_protocol",
                "minutes",
                False,
                "Coordinate axes, probe rows, wind vector, velocity component or Uref identity is blocking interpretation.",
                "Run audit_coordinate_probe_protocol.py and audit_component_sensitivity.py, then fix metadata, official probe subset or normalization before any long CFD run.",
            )
        )
    if any(
        token in joined
        for token in [
            "boundary_protocol",
            "boundary_source",
            "boundary",
            "roughness",
            "rough_wall",
            "wall",
            "fetch",
            "outlet",
            "side_top",
        ]
    ):
        items.append(
            action(
                3,
                "resolve_boundary_and_wall_protocol_evidence",
                "minutes",
                False,
                "Boundary, outlet, side/top or rough-wall evidence is also blocking paper-grade validation.",
                "Prepare a traceable AIJ-equivalent boundary-protocol evidence JSON and link it in case_metadata before any long CFD run.",
            )
        )
    if not time_averaging_report_passed and any(token in joined for token in ["vtk", "time", "average", "averaging", "step_span"]):
        items.append(
            action(
                4,
                "verify_time_averaging_schedule",
                "minutes",
                False,
                "The artifacts mention VTK/time-window risk; this can be checked before solver tuning.",
                "Confirm save interval, expected frame count, final-window span and stale-VTK hashes before running the next canary.",
            )
        )
    if runtime_inlet_report_blocked or any(
        token in joined
        for token in [
            "runtimeinletdiagnosticsgate",
            "inlet_diagnostics",
            "mean_u_rel_error",
            "k_rel_error",
            "rms_rel_error",
            "reynolds_stress",
        ]
    ):
        items.append(
            action(
                2,
                "audit_runtime_inlet_csv_after_each_canary",
                "seconds",
                False,
                "Runtime inlet statistics can be checked from CSV without waiting for expensive VTK postprocessing.",
                "Run audit_inlet_diagnostics_csv.py after every short canary and stop if U/k/RMS/Reynolds-stress preservation fails.",
            )
        )
    return items


def infer_case(args_case: str, runs: List[Dict[str, Any]]) -> str:
    if args_case != "auto":
        return args_case
    for run in runs:
        for source in [run.get("validation_gate", {}), run.get("native_manifest", {})]:
            text = json.dumps(source, ensure_ascii=True).lower()
            if "casee" in text or "case e" in text:
                return "casee"
            if "casea" in text or "case a" in text:
                return "casea"
    return "casee"


def shell_quote(value: str) -> str:
    if not value:
        return "\"\""
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def safe_case_slug(label: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(label).strip())
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "case"


def template_case_file(case_dir: str, candidates: Sequence[str], fallback: str) -> str:
    if not case_dir or case_dir == "<case_dir>":
        return f"<case_dir>\\{fallback}"
    base = Path(case_dir)
    for candidate in candidates:
        path = base / candidate
        if path.is_file():
            return str(path)
    return str(base / fallback)


def metadata_for_templates(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.case_dir:
        return {}
    return load_json(Path(args.case_dir) / "case_metadata.json")


def first_text(data: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def get_nested(data: Dict[str, Any], path: Sequence[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_nested_text(data: Dict[str, Any], paths: Sequence[Sequence[str]]) -> str:
    for path in paths:
        value = get_nested(data, path)
        if value is None:
            continue
        text = str(value).strip()
        if text and text != "{}":
            return text
    return ""


def template_official_inputs(args: argparse.Namespace) -> Dict[str, str]:
    metadata = metadata_for_templates(args)
    official = args.official or first_nested_text(
        metadata,
        [
            ("OfficialRS",),
            ("OfficialRSCsv",),
            ("OfficialMeasurementCsv",),
            ("OfficialProbeCsv",),
            ("official_inputs", "RS_caseE.csv", "path"),
            ("official_inputs", "RS_caseA.csv", "path"),
            ("official_inputs", "RS", "path"),
        ],
    )
    af_csv = args.af_csv or first_nested_text(
        metadata,
        [
            ("OfficialAF",),
            ("OfficialAFCsv",),
            ("AfCsv",),
            ("InletProfileCsv",),
            ("official_inputs", "AF_caseE.csv", "path"),
            ("official_inputs", "AF_caseA.csv", "path"),
            ("official_inputs", "AF", "path"),
        ],
    )
    return {
        "official": official or "<official_RS_csv>",
        "af_csv": af_csv or "<official_AF_csv>",
    }


def expected_frame_count(time_steps: int, save_interval: int, save_start_step: Optional[int] = None) -> int:
    if time_steps <= 0 or save_interval <= 0:
        return 0
    first_step = save_start_step if save_start_step is not None else save_interval
    if first_step <= 0:
        first_step = save_interval
    if first_step > time_steps:
        return 0
    return ((time_steps - first_step) // save_interval) + 1


def template_preflight_dir(args: argparse.Namespace, case_dir: str) -> str:
    if args.template_preflight_dir:
        return str(Path(args.template_preflight_dir))
    if args.case_dir:
        return str(Path(case_dir) / "preflight")
    return "<case_dir>\\preflight"


def default_case_metadata(args: argparse.Namespace, case_dir: str) -> str:
    return str(Path(case_dir) / "case_metadata.json") if args.case_dir else "<case_dir>\\case_metadata.json"


def preferred_runner_metadata(args: argparse.Namespace, case_dir: str, runs: Optional[Sequence[Dict[str, Any]]] = None) -> str:
    fallback = default_case_metadata(args, case_dir)
    for run in runs or []:
        pack = run.get("native_preflight_pack")
        if not isinstance(pack, dict):
            continue
        artifacts = pack.get("Artifacts")
        if not isinstance(artifacts, dict):
            continue
        for key in ("InletBoundMetadata", "CoordinateProbeBoundMetadata"):
            candidate = artifacts.get(key)
            if not candidate:
                continue
            path = Path(str(candidate)).expanduser()
            if path.exists():
                return str(path.resolve())
    return fallback


def command_templates(
    args: argparse.Namespace,
    preset: Dict[str, Any],
    runs: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    case_dir = args.case_dir or "<case_dir>"
    fluidx3d_source = args.fluidx3d_source or "<fluidx3d_source>"
    official_inputs = template_official_inputs(args)
    official = official_inputs["official"]
    af_csv = official_inputs["af_csv"]
    runtime = case_runtime_settings(args, preset)
    manifest = str(Path(case_dir) / NATIVE_MANIFEST) if args.case_dir else "<case_dir>\\native_fluidx3d_baseline_manifest.json"
    metadata = default_case_metadata(args, case_dir)
    runner_metadata = preferred_runner_metadata(args, case_dir, runs)
    preflight_dir = template_preflight_dir(args, case_dir)
    inlet_reynolds_stress_template = str(Path(preflight_dir) / "inlet_reynolds_stress_tensor_template.csv")
    bound_metadata = str(Path(preflight_dir) / "case_metadata.reynolds_bound.json")
    length_scale_evidence = str(Path(preflight_dir) / "turbulence_length_scale_evidence.json")
    length_scale_bound_metadata = str(Path(preflight_dir) / "case_metadata.length_scale_bound.json")
    coordinate_probe_protocol = str(Path(preflight_dir) / "coordinate_probe_protocol_audit.json")
    custom_profile_af_fidelity = str(Path(preflight_dir) / CUSTOM_PROFILE_AF_FIDELITY_AUDIT)
    custom_profile_af_fidelity_csv = str(Path(preflight_dir) / "custom_profile_af_fidelity_audit.csv")
    inlet_source = (
        str(Path(preflight_dir) / "inlet_source_audit.json")
        if args.case_dir or args.template_preflight_dir
        else "<case_dir>\\preflight\\inlet_source_audit.json"
    )

    def base_command(
        steps: int,
        frame_count: int,
        average_last_n: int,
        min_vtk_frames: int,
        min_step_span: int,
        save_start_step: Optional[int],
    ) -> List[str]:
        command = [
        sys.executable,
        "scripts\\run_native_fluidx3d_case.py",
        "--case-dir",
        case_dir,
        "--fluidx3d-source",
        fluidx3d_source,
        "--out",
        manifest,
        "--metadata",
        runner_metadata,
        "--inlet-source-audit",
        inlet_source,
        "--coordinate-probe-protocol-audit",
        coordinate_probe_protocol,
        "--expected-aij-case",
        str(preset["case_label"]),
        "--official",
        official,
        "--af-csv",
        af_csv,
        "--time-steps",
        str(steps),
        "--vtk-save-interval",
        str(runtime["save_interval"]),
        "--expected-vtk-frame-count",
        str(frame_count),
        "--average-last-n",
        str(average_last_n),
        "--min-vtk-frames",
        str(min_vtk_frames),
        "--min-vtk-step-span",
        str(min_step_span),
        ]
        if save_start_step is not None:
            command.extend(["--vtk-save-start-step", str(save_start_step)])
        if preset.get("wind_label"):
            command.extend(["--expected-wind-direction", str(preset["wind_label"])])
        if preset.get("official_condition_filter"):
            command.extend(["--official-condition-filter", str(preset["official_condition_filter"])])
        if preset.get("official_wind_filter"):
            command.extend(["--official-wind-filter", str(preset["official_wind_filter"])])
        if preset.get("expected_probe_rows"):
            command.extend(["--expected-probe-row-count", str(preset["expected_probe_rows"])])
        if preset.get("expected_probe_z") is not None:
            command.extend(["--expected-probe-z", str(preset["expected_probe_z"])])
        if preset.get("expected_probe_z_min") is not None:
            command.extend(["--expected-probe-z-min", str(preset["expected_probe_z_min"])])
        if preset.get("expected_probe_z_max") is not None:
            command.extend(["--expected-probe-z-max", str(preset["expected_probe_z_max"])])
        if preset.get("z_ref") is not None:
            command.extend(["--z-ref", str(preset["z_ref"])])
        if preset.get("u_ref") is not None:
            command.extend(["--expected-uref", str(preset["u_ref"])])
        if preset.get("wind_vector"):
            command.extend(["--expected-wind-vector", str(preset["wind_vector"])])
        if preset.get("require_af_k"):
            command.append("--require-af-k")
        if args.solver_cwd:
            command.extend(["--solver-cwd", args.solver_cwd])
        return command

    paper_frame_count = int(runtime["expected_frame_count"])
    canary_steps = int(preset["canary_steps"])
    canary_frame_count = expected_frame_count(
        canary_steps,
        int(runtime["save_interval"]),
        None,
    )
    canary_average_last_n = max(1, canary_frame_count)
    base = base_command(
        int(runtime["paper_steps"]),
        paper_frame_count,
        int(runtime["average_last_n"]),
        int(runtime["average_last_n"]),
        int(runtime["min_step_span"]),
        runtime.get("save_start_step"),
    )
    canary_base = base_command(
        canary_steps,
        canary_frame_count,
        canary_average_last_n,
        1,
        0,
        None,
    )
    codegen_gate_parts = [
        sys.executable,
        "scripts\\run_codegen_preflight_canary.py",
        "--expected-aij-case",
        str(preset["case_label"]),
        "--expected-wind-direction",
        str(preset["wind_label"]),
        "--expected-wind-vector",
        str(preset["wind_vector"]),
        "--time-steps",
        str(runtime["paper_steps"]),
        "--vtk-save-interval",
        str(runtime["save_interval"]),
        "--expected-vtk-frame-count",
        str(runtime["expected_frame_count"]),
        "--average-last-n",
        str(runtime["average_last_n"]),
        "--min-vtk-frames",
        str(runtime["average_last_n"]),
        "--min-vtk-step-span",
        str(runtime["min_step_span"]),
        "--allow-diagnostic",
    ]
    if runtime.get("save_start_step") is not None:
        codegen_gate_parts.extend(["--vtk-save-start-step", str(runtime["save_start_step"])])
    if preset.get("official_condition_filter"):
        codegen_gate_parts.extend(["--official-condition-filter", str(preset["official_condition_filter"])])
    if preset.get("official_wind_filter"):
        codegen_gate_parts.extend(["--official-wind-filter", str(preset["official_wind_filter"])])
    if preset.get("expected_probe_rows"):
        codegen_gate_parts.extend(["--expected-probe-row-count", str(preset["expected_probe_rows"])])
    if preset.get("expected_probe_z") is not None:
        codegen_gate_parts.extend(["--expected-probe-z", str(preset["expected_probe_z"])])
    if preset.get("expected_probe_z_min") is not None:
        codegen_gate_parts.extend(["--expected-probe-z-min", str(preset["expected_probe_z_min"])])
    if preset.get("expected_probe_z_max") is not None:
        codegen_gate_parts.extend(["--expected-probe-z-max", str(preset["expected_probe_z_max"])])
    if preset.get("z_ref") is not None:
        codegen_gate_parts.extend(["--z-ref", str(preset["z_ref"])])
    if preset.get("u_ref") is not None:
        codegen_gate_parts.extend(["--expected-uref", str(preset["u_ref"])])
    if preset.get("require_af_k"):
        codegen_gate_parts.append("--require-af-k")
    if args.official:
        codegen_gate_parts.extend(["--official", official])
    if args.af_csv:
        codegen_gate_parts.extend(["--af-csv", af_csv])
    if args.solver_cwd:
        codegen_gate_parts.extend(["--solver-cwd", args.solver_cwd])
    codegen_quick_parts = codegen_gate_parts + ["--quick"]
    preflight_pack_parts = [
        sys.executable,
        "scripts\\run_native_preflight_pack.py",
        "--case-dir",
        case_dir,
        "--fluidx3d-source",
        fluidx3d_source,
        "--out-dir",
        preflight_dir,
        "--manifest-out",
        manifest,
        "--metadata",
        metadata,
        "--expected-aij-case",
        str(preset["case_label"]),
        "--time-steps",
        str(runtime["paper_steps"]),
        "--vtk-save-interval",
        str(runtime["save_interval"]),
        "--expected-vtk-frame-count",
        str(runtime["expected_frame_count"]),
        "--average-last-n",
        str(runtime["average_last_n"]),
        "--min-vtk-frames",
        str(runtime["average_last_n"]),
        "--min-vtk-step-span",
        str(runtime["min_step_span"]),
        "--patch-metadata-identity",
        "--allow-diagnostic",
    ]
    if runtime.get("save_start_step") is not None:
        preflight_pack_parts.extend(["--vtk-save-start-step", str(runtime["save_start_step"])])
    if preset.get("wind_label"):
        preflight_pack_parts.extend(["--expected-wind-direction", str(preset["wind_label"])])
    if preset.get("wind_vector"):
        preflight_pack_parts.extend(["--expected-wind-vector", str(preset["wind_vector"])])
    if preset.get("official_condition_filter"):
        preflight_pack_parts.extend(["--official-condition-filter", str(preset["official_condition_filter"])])
    if preset.get("official_wind_filter"):
        preflight_pack_parts.extend(["--official-wind-filter", str(preset["official_wind_filter"])])
    if preset.get("expected_probe_rows"):
        preflight_pack_parts.extend(["--expected-probe-row-count", str(preset["expected_probe_rows"])])
    if preset.get("expected_probe_z") is not None:
        preflight_pack_parts.extend(["--expected-probe-z", str(preset["expected_probe_z"])])
    if preset.get("expected_probe_z_min") is not None:
        preflight_pack_parts.extend(["--expected-probe-z-min", str(preset["expected_probe_z_min"])])
    if preset.get("expected_probe_z_max") is not None:
        preflight_pack_parts.extend(["--expected-probe-z-max", str(preset["expected_probe_z_max"])])
    if preset.get("z_ref") is not None:
        preflight_pack_parts.extend(["--z-ref", str(preset["z_ref"])])
    if preset.get("u_ref") is not None:
        preflight_pack_parts.extend(["--expected-uref", str(preset["u_ref"])])
    if preset.get("require_af_k"):
        preflight_pack_parts.append("--require-af-k")
    if official:
        preflight_pack_parts.extend(["--official", official])
    if af_csv:
        preflight_pack_parts.extend(["--af-csv", af_csv])
    if args.solver_cwd:
        preflight_pack_parts.extend(["--solver-cwd", args.solver_cwd])
    preflight = " ".join(shell_quote(part) for part in base)
    canary = " ".join(shell_quote(part) for part in canary_base + ["--install", "--build", "--run", "--allow-diagnostic-execution"])
    paper = " ".join(shell_quote(part) for part in base + ["--install", "--build", "--run"])
    return {
        "current_codegen_full_gate": " ".join(shell_quote(part) for part in codegen_gate_parts),
        "current_codegen_quick_gate": " ".join(shell_quote(part) for part in codegen_quick_parts),
        "preflight_pack_no_cfd": " ".join(shell_quote(part) for part in preflight_pack_parts),
        "bind_reynolds_stress_metadata": " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\bind_inlet_reynolds_stress_metadata.py",
                "--metadata",
                metadata,
                "--stress-csv",
                inlet_reynolds_stress_template,
                "--out",
                bound_metadata,
                "--source-note",
                "Identity binding only; keep diagnostic until full tensor or precursor audit passes.",
            ]
        ),
        "bind_turbulence_length_scale_metadata": " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\bind_turbulence_length_scale_metadata.py",
                "--metadata",
                metadata,
                "--evidence-json",
                length_scale_evidence,
                "--out",
                length_scale_bound_metadata,
                "--source-note",
                "Identity binding only; keep diagnostic until official, precursor or calibrated length-scale evidence passes.",
            ]
        ),
        "audit_custom_profile_against_af": " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\audit_custom_profile_against_af.py",
                "--metadata",
                runner_metadata,
                "--af-csv",
                af_csv,
                "--out-json",
                custom_profile_af_fidelity,
                "--out-csv",
                custom_profile_af_fidelity_csv,
                "--require-k",
            ]
        ),
        "preflight_no_cfd": preflight,
        "diagnostic_canary_cfd": canary,
        "paper_candidate_cfd": paper,
    }


def parallel_batches(
    args: argparse.Namespace,
    preset: Dict[str, Any],
    runs: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    case_dir = args.case_dir or "<case_dir>"
    official_inputs = template_official_inputs(args)
    official = official_inputs["official"]
    af_csv = official_inputs["af_csv"]
    runtime = case_runtime_settings(args, preset)
    setup_cpp = template_case_file(case_dir, ["src/setup.cpp", "setup.cpp"], "src\\setup.cpp")
    defines_hpp = template_case_file(case_dir, ["src/defines.hpp", "defines.hpp"], "src\\defines.hpp")
    metadata = default_case_metadata(args, case_dir)
    domain_origin = str(Path(case_dir) / "domain_origin.json") if args.case_dir else "<case_dir>\\domain_origin.json"
    preflight_dir = template_preflight_dir(args, case_dir)
    inlet_source = str(Path(preflight_dir) / "inlet_source_audit.json")
    inlet_reynolds_stress = str(Path(preflight_dir) / "inlet_reynolds_stress_evidence.json")
    inlet_reynolds_stress_template = str(Path(preflight_dir) / "inlet_reynolds_stress_tensor_template.csv")
    precursor_evidence_template = str(Path(preflight_dir) / "equivalent_precursor_evidence_template.json")
    turbulence_length_scale_evidence = str(Path(preflight_dir) / "turbulence_length_scale_evidence.json")
    boundary_source = str(Path(preflight_dir) / "boundary_source_audit.json")
    fluidx3d_equilibrium_boundary = str(Path(preflight_dir) / "fluidx3d_equilibrium_boundary_audit.json")
    boundary_protocol = str(Path(preflight_dir) / "boundary_protocol_audit.json")
    boundary_protocol_template = str(Path(preflight_dir) / "boundary_protocol_evidence_template.json")
    coordinate_probe_protocol = str(Path(preflight_dir) / "coordinate_probe_protocol_audit.json")
    coordinate_probe_bound_metadata = str(Path(preflight_dir) / "case_metadata.coordinate_probe_bound.json")
    protocol = str(Path(case_dir) / "validation_protocol_audit.json") if args.case_dir else "<case_dir>\\validation_protocol_audit.json"
    native_preconditions = str(Path(preflight_dir) / "native_preconditions_audit.json")
    case_slug = safe_case_slug(str(preset["case_label"]))
    diagnostics_base = args.solver_cwd or args.fluidx3d_source or "<solver_cwd_or_fluidx3d_source>"
    inlet_diagnostics_csv = str(Path(diagnostics_base) / f"{case_slug}_inlet_turbulence_stats.csv")
    inlet_diagnostics_json = str(Path(preflight_dir) / INLET_DIAGNOSTICS_CSV_AUDIT)
    inlet_diagnostics_summary = str(Path(preflight_dir) / "inlet_diagnostics_csv_summary.csv")
    templates = command_templates(args, preset, runs)

    no_cfd_commands = [
        templates["preflight_pack_no_cfd"],
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\patch_fluidx3d_equilibrium_boundary_source.py",
                "--fluidx3d-source",
                args.fluidx3d_source or "<fluidx3d_source>",
                "--out",
                str(Path(preflight_dir) / "patch_fluidx3d_equilibrium_boundary_source_manifest.json")
                if args.case_dir
                else "<case_dir>\\preflight\\patch_fluidx3d_equilibrium_boundary_source_manifest.json",
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\enable_fluidx3d_ddf_reconstruction_route.py",
                "--case-dir",
                case_dir,
                "--defines",
                defines_hpp,
                "--fluidx3d-source",
                args.fluidx3d_source or "<fluidx3d_source>",
                "--out",
                str(Path(preflight_dir) / "enable_ddf_reconstruction_route_manifest.json")
                if args.case_dir
                else "<case_dir>\\preflight\\enable_ddf_reconstruction_route_manifest.json",
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\bind_coordinate_probe_protocol_metadata.py",
                "--metadata",
                metadata,
                "--case-dir",
                case_dir,
                "--setup",
                setup_cpp,
                "--out",
                coordinate_probe_bound_metadata,
                "--case-label",
                str(preset["case_label"]),
                "--wind-direction",
                str(preset.get("wind_label") or ""),
                "--wind-vector",
                str(preset.get("wind_vector") or ""),
                "--probe-count",
                str(preset.get("expected_probe_rows") or 0),
                "--z-ref",
                str(preset.get("z_ref") or ""),
                "--uref",
                str(preset.get("u_ref") or ""),
                "--official-rs",
                official,
                "--official-af",
                af_csv,
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\audit_inlet_source.py",
                "--setup",
                setup_cpp,
                "--defines",
                defines_hpp,
                "--metadata",
                metadata,
                "--out",
                inlet_source,
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\create_boundary_protocol_evidence_template.py",
                case_dir,
                "--metadata",
                metadata,
                "--out",
                boundary_protocol_template,
                "--case",
                str(preset["case_label"]),
                "--wind-direction",
                str(preset.get("wind_label") or "standard"),
                "--force",
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\create_inlet_reynolds_stress_template.py",
                "--metadata",
                metadata,
                "--af-csv",
                af_csv,
                "--out-csv",
                inlet_reynolds_stress_template,
                "--out-precursor-json",
                precursor_evidence_template,
                "--case",
                str(preset["case_label"]),
                "--wind-direction",
                str(preset.get("wind_label") or "standard"),
                "--force",
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\create_turbulence_length_scale_evidence_template.py",
                "--metadata",
                metadata,
                "--out",
                turbulence_length_scale_evidence,
                "--case",
                str(preset["case_label"]),
                "--wind-direction",
                str(preset.get("wind_label") or "standard"),
                "--force",
            ]
        ),
        templates["bind_turbulence_length_scale_metadata"],
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\build_inlet_reynolds_stress_evidence.py",
                "--af-csv",
                af_csv,
                "--metadata",
                metadata,
                "--case",
                str(preset["case_label"]),
                "--source-type",
                "auto",
                "--stress-csv",
                inlet_reynolds_stress_template,
                "--precursor-evidence",
                precursor_evidence_template,
                "--out",
                inlet_reynolds_stress,
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\audit_boundary_source.py",
                "--setup",
                setup_cpp,
                "--metadata",
                metadata,
                "--out",
                boundary_source,
            ]
        ),
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\audit_fluidx3d_equilibrium_boundary.py",
                "--fluidx3d-source",
                args.fluidx3d_source or "<fluidx3d_source>",
                "--out",
                fluidx3d_equilibrium_boundary,
            ]
        ),
        templates["preflight_no_cfd"],
        templates["bind_reynolds_stress_metadata"],
    ]
    no_cfd_commands.insert(
        1,
        " ".join(
            shell_quote(part)
            for part in [
                sys.executable,
                "scripts\\patch_legacy_customtable_profile_origin.py",
                "--case-dir",
                case_dir,
                "--setup",
                setup_cpp,
                "--domain-origin",
                domain_origin,
                "--out",
                str(Path(preflight_dir) / "patch_legacy_customtable_profile_origin_manifest.json")
                if args.case_dir
                else "<case_dir>\\preflight\\patch_legacy_customtable_profile_origin_manifest.json",
            ]
        ),
    )
    boundary_protocol_parts = [
        sys.executable,
        "scripts\\audit_boundary_protocol.py",
        case_dir,
        "--metadata",
        metadata,
        "--out",
        boundary_protocol,
        "--expected-aij-case",
        str(preset["case_label"]),
    ]
    if preset.get("wind_label"):
        boundary_protocol_parts.extend(["--expected-wind-direction", str(preset["wind_label"])])
    no_cfd_commands.insert(2, " ".join(shell_quote(part) for part in boundary_protocol_parts))

    coordinate_probe_parts = [
        sys.executable,
        "scripts\\audit_coordinate_probe_protocol.py",
        case_dir,
        "--metadata",
        metadata,
        "--out",
        coordinate_probe_protocol,
        "--expected-aij-case",
        str(preset["case_label"]),
    ]
    if preset.get("wind_label"):
        coordinate_probe_parts.extend(["--expected-wind-direction", str(preset["wind_label"])])
    if preset.get("wind_vector"):
        coordinate_probe_parts.extend(["--expected-wind-vector", str(preset["wind_vector"])])
    if official:
        coordinate_probe_parts.extend(["--official", official])
    if af_csv:
        coordinate_probe_parts.extend(["--af-csv", af_csv])
    if preset.get("official_condition_filter"):
        coordinate_probe_parts.extend(["--official-condition-filter", str(preset["official_condition_filter"])])
    if preset.get("official_wind_filter"):
        coordinate_probe_parts.extend(["--official-wind-filter", str(preset["official_wind_filter"])])
    if preset.get("expected_probe_rows"):
        coordinate_probe_parts.extend(["--expected-probe-row-count", str(preset["expected_probe_rows"])])
    if preset.get("expected_probe_z") is not None:
        coordinate_probe_parts.extend(["--expected-probe-z", str(preset["expected_probe_z"])])
    if preset.get("expected_probe_z_min") is not None:
        coordinate_probe_parts.extend(["--expected-probe-z-min", str(preset["expected_probe_z_min"])])
    if preset.get("expected_probe_z_max") is not None:
        coordinate_probe_parts.extend(["--expected-probe-z-max", str(preset["expected_probe_z_max"])])
    if preset.get("z_ref") is not None:
        coordinate_probe_parts.extend(["--z-ref", str(preset["z_ref"])])
    if preset.get("u_ref") is not None:
        coordinate_probe_parts.extend(["--expected-uref", str(preset["u_ref"])])
    no_cfd_commands.insert(3, " ".join(shell_quote(part) for part in coordinate_probe_parts))

    protocol_parts = [
        sys.executable,
        "scripts\\write_validation_protocol_audit.py",
        "--case-dir",
        case_dir,
        "--metadata",
        metadata,
        "--out",
        protocol,
        "--case",
        str(preset["case_label"]),
        "--inlet-source-audit",
        inlet_source,
        "--inlet-reynolds-stress-evidence",
        inlet_reynolds_stress,
        "--boundary-source-audit",
        boundary_source,
    ]
    if preset.get("wind_label"):
        protocol_parts.extend(["--wind-direction-label", str(preset["wind_label"])])
    if preset.get("wind_vector"):
        protocol_parts.extend(["--wind-vector", str(preset["wind_vector"])])
    no_cfd_commands.insert(3, " ".join(shell_quote(part) for part in protocol_parts))

    native_precondition_parts = [
        sys.executable,
        "scripts\\audit_native_preconditions.py",
        case_dir,
        "--manifest",
        str(Path(case_dir) / NATIVE_MANIFEST) if args.case_dir else "<case_dir>\\native_fluidx3d_baseline_manifest.json",
        "--metadata",
        metadata,
        "--inlet-source-audit",
        inlet_source,
        "--boundary-source-audit",
        boundary_source,
        "--boundary-protocol-audit",
        boundary_protocol,
        "--official",
        official,
        "--af-csv",
        af_csv,
        "--case",
        str(preset["case_label"]),
        "--average-last-n",
        str(runtime["average_last_n"]),
        "--min-avg-frames",
        str(runtime["average_last_n"]),
        "--min-avg-step-span",
        str(runtime["min_step_span"]),
        "--out",
        native_preconditions,
    ]
    if preset.get("wind_label"):
        native_precondition_parts.extend(["--wind-direction-label", str(preset["wind_label"])])
    if preset.get("wind_vector"):
        native_precondition_parts.extend(["--wind-vector", str(preset["wind_vector"])])
    precondition_command = " ".join(shell_quote(part) for part in native_precondition_parts)
    inlet_diagnostics_command = " ".join(
        shell_quote(part)
        for part in [
            sys.executable,
            "scripts\\audit_inlet_diagnostics_csv.py",
            inlet_diagnostics_csv,
            "--out-json",
            inlet_diagnostics_json,
            "--out-csv",
            inlet_diagnostics_summary,
            "--require-k",
            "--require-rms",
            "--require-reynolds-stress",
        ]
    )
    blocker_summary_command = " ".join(
        shell_quote(part)
        for part in [
            sys.executable,
            "scripts\\summarize_validation_blockers.py",
            "--run-dir",
            case_dir,
            "--native-manifest",
            str(Path(case_dir) / NATIVE_MANIFEST) if args.case_dir else "<case_dir>\\native_fluidx3d_baseline_manifest.json",
            "--native-preconditions",
            native_preconditions,
        ]
    )

    return [
        {
            "rank": 0,
            "name": "no_cfd_source_and_protocol_preflight",
            "runs_cfd": False,
            "can_run_in_parallel": True,
            "purpose": "Close cheap setup.cpp, inlet, boundary and protocol identity failures before any long FluidX3D run.",
            "commands": no_cfd_commands,
            "promotion_gate": "Do not launch CFD until inlet-source, boundary-source, official-input and protocol pre-run gates are clean enough for the selected diagnostic or paper route.",
            "stop_if": [
                "inlet_source_velocity_field_only_without_distribution_reconstruction",
                "inlet_reynolds_stress_evidence_missing_offdiagonal_or_precursor",
                "fluidx3d_source_reconstruct_hook_patch_failed",
                "fluidx3d_type_e_ddf_route_not_proven",
                "boundary_source_simplified_without_AIJ_boundary_evidence",
                "coordinate_probe_protocol_or_Uref_identity_mismatch",
                "validation_protocol_prerun_gate_not_ready",
                "official_AF_or_RS_identity_mismatch",
            ],
        },
        {
            "rank": 1,
            "name": "short_native_canary",
            "runs_cfd": True,
            "can_run_in_parallel": False,
            "purpose": "Run only a short native FluidX3D canary after no-CFD gates identify no blocking source or protocol errors.",
            "commands": [templates["diagnostic_canary_cfd"], inlet_diagnostics_command, precondition_command, blocker_summary_command],
            "promotion_gate": "Promote to paper-length CFD only if new VTK hashes, source parity, inlet/boundary runtime audits and probe projection gates are interpretable.",
            "stop_if": [
                "fresh_VTK_missing_or_stale",
                "runtime_inlet_diagnostics_csv_missing_or_failed",
                "inlet_U_or_k_profile_not_preserved",
                "boundary_runtime_profile_not_preserved",
                "probe_projection_or_Uref_component_mismatch",
            ],
        },
        {
            "rank": 2,
            "name": "paper_candidate_native_run",
            "runs_cfd": True,
            "can_run_in_parallel": False,
            "purpose": "Spend long solver time only after the canary closes the protocol-level blockers.",
            "commands": [templates["paper_candidate_cfd"]],
            "promotion_gate": "Only after this native chain passes should the same setup be migrated to CityLBM and compared as a native-CityLBM parity test.",
            "stop_if": [
                "R2_or_bias_interpreted_before_native_preconditions_pass",
                "systematic_bias_about_minus_0.20_to_minus_0.35_without_closed_inlet_boundary_probe_gates",
            ],
        },
    ]


def acceleration_summary(sequence: List[Dict[str, Any]], batches: List[Dict[str, Any]]) -> Dict[str, Any]:
    fastest = sequence[0] if sequence else {}
    first_phase = str(fastest.get("phase") or "")
    first_runs_cfd = bool(fastest.get("runs_cfd")) if "runs_cfd" in fastest else False
    no_cfd_batch = next(
        (
            batch
            for batch in batches
            if batch.get("runs_cfd") is False and batch.get("can_run_in_parallel") is True
        ),
        {},
    )
    canary_batch = next((batch for batch in batches if batch.get("name") == "short_native_canary"), {})
    paper_batch = next((batch for batch in batches if batch.get("name") == "paper_candidate_native_run"), {})

    if not sequence:
        next_batch_name = ""
        next_command = ""
        policy = "no_recommendation"
    elif first_phase == "bind_reynolds_stress_evidence_to_current_case":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "bind_inlet_reynolds_stress_metadata.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "bind_current_case_evidence_before_preflight"
    elif first_phase == "fix_advanced_turbulence_evidence_before_cfd":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "audit_inlet_source.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "fix_inlet_source_code_then_rerun_audit"
    elif first_phase == "patch_legacy_customtable_profile_origin":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "patch_legacy_customtable_profile_origin.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "patch_legacy_customtable_origin_then_rerun_inlet_audit"
    elif first_phase == "patch_fluidx3d_equilibrium_boundary_source":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "patch_fluidx3d_equilibrium_boundary_source.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "patch_fluidx3d_boundary_source_then_rerun_preflight"
    elif first_phase == "enable_fluidx3d_ddf_reconstruction_route":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "enable_fluidx3d_ddf_reconstruction_route.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "enable_boundary_ddf_route_then_rerun_preflight"
    elif first_phase == "resolve_turbulent_length_scale_evidence":
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "create_turbulence_length_scale_evidence_template.py" in str(command)),
            str(commands[0]) if commands else "",
        )
        policy = "create_or_bind_turbulence_length_scale_evidence_before_cfd"
    elif first_phase in {
        "resolve_reynolds_stress_offdiagonal_or_precursor_gap",
        "populate_reynolds_stress_tensor_or_precursor_template",
    }:
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = next(
            (str(command) for command in commands if "run_native_preflight_pack.py" in str(command)),
            next(
                (str(command) for command in commands if "create_inlet_reynolds_stress_template.py" in str(command)),
                next(
                    (str(command) for command in commands if "build_inlet_reynolds_stress_evidence.py" in str(command)),
                    str(commands[0]) if commands else "",
                ),
            ),
        )
        policy = "create_or_fill_reynolds_stress_or_precursor_evidence_before_cfd"
    elif not first_runs_cfd:
        commands = no_cfd_batch.get("commands") if isinstance(no_cfd_batch.get("commands"), list) else []
        next_batch_name = str(no_cfd_batch.get("name") or "no_cfd_source_and_protocol_preflight")
        next_command = str(commands[0]) if commands else ""
        policy = "run_no_cfd_preflight_first"
    elif first_phase in {
        "launch_native_canary_or_resume_solver",
        "fix_runtime_inlet_statistics_before_long_run",
        "fix_turbulent_inlet_evidence",
    }:
        commands = canary_batch.get("commands") if isinstance(canary_batch.get("commands"), list) else []
        next_batch_name = str(canary_batch.get("name") or "short_native_canary")
        next_command = str(commands[0]) if commands else ""
        policy = "run_short_native_canary_only"
    elif first_phase == "run_targeted_native_sensitivity":
        commands = canary_batch.get("commands") if isinstance(canary_batch.get("commands"), list) else []
        next_batch_name = str(canary_batch.get("name") or "short_native_canary")
        next_command = str(commands[0]) if commands else ""
        policy = "run_one_factor_short_native_sensitivity"
    elif first_phase == "migrate_verified_native_settings_to_citylbm":
        next_batch_name = "citylbm_parity_after_native_pass"
        next_command = ""
        policy = "migrate_after_native_evidence_freeze"
    else:
        commands = paper_batch.get("commands") if isinstance(paper_batch.get("commands"), list) else []
        next_batch_name = str(paper_batch.get("name") or "paper_candidate_native_run")
        next_command = str(commands[0]) if commands else ""
        policy = "paper_candidate_only_after_prior_gates_pass"

    return {
        "fastest_phase": first_phase,
        "fastest_runs_cfd": first_runs_cfd,
        "next_execution_policy": policy,
        "next_batch_name": next_batch_name,
        "next_command": next_command,
        "no_cfd_parallel_command_count": len(no_cfd_batch.get("commands", []))
        if isinstance(no_cfd_batch.get("commands"), list)
        else 0,
        "long_cfd_allowed_now": policy == "paper_candidate_only_after_prior_gates_pass",
        "development_time_saved_by": [
            "stop_before_solver_when_source_protocol_or_probe_gates_fail",
            "run_parallel_no_cfd_audits_before_any_canary",
            "use_short_native_canary_before_paper_length_vtk_generation",
            "migrate_to_citylbm_only_after_native_fluidx3d_evidence_passes",
        ],
    }


def latest_run_gate(runs: Sequence[Dict[str, Any]], key: str) -> str:
    for run in runs:
        value = run.get(key)
        if isinstance(value, dict):
            gate = compact(value.get("Gate"))
            if gate:
                return gate
    return "missing"


def analyze_run(run_dir: Path, evidence_dirs: Optional[Sequence[Path]] = None) -> Dict[str, Any]:
    search_dirs = unique_paths([*(evidence_dirs or []), run_dir])
    manifest_path = find_report_any(search_dirs, NATIVE_MANIFEST)
    native_path = find_report_any(search_dirs, NATIVE_PRECONDITIONS)
    gate_path = find_report_any(search_dirs, VALIDATION_GATE)
    fluidx3d_boundary_path = find_report_any(search_dirs, FLUIDX3D_EQUILIBRIUM_BOUNDARY)
    inlet_source_path = find_report_any(search_dirs, INLET_SOURCE_AUDIT)
    inlet_reynolds_stress_path = find_report_any(search_dirs, INLET_REYNOLDS_STRESS_EVIDENCE)
    boundary_source_path = find_report_any(search_dirs, BOUNDARY_SOURCE_AUDIT)
    boundary_protocol_path = find_report_any(search_dirs, BOUNDARY_PROTOCOL_AUDIT)
    coordinate_probe_protocol_path = find_report_any(search_dirs, COORDINATE_PROBE_PROTOCOL_AUDIT)
    validation_protocol_path = find_report_any(search_dirs, VALIDATION_PROTOCOL_AUDIT)
    native_preflight_pack_path = find_report_any(search_dirs, NATIVE_PREFLIGHT_PACK)
    time_averaging_evidence_path = find_report_any(search_dirs, TIME_AVERAGING_EVIDENCE)
    inlet_diagnostics_csv_path = find_report_any(search_dirs, INLET_DIAGNOSTICS_CSV_AUDIT)
    component_sensitivity_path = find_report_any(search_dirs, COMPONENT_SENSITIVITY_AUDIT)
    inlet_correlation_audit_path = find_report_any(search_dirs, INLET_CORRELATION_AUDIT)
    canary_runtime_evidence_path = find_report_any(search_dirs, CANARY_RUNTIME_EVIDENCE)
    custom_profile_af_fidelity_path = find_report_any(search_dirs, CUSTOM_PROFILE_AF_FIDELITY_AUDIT)
    manifest = load_json(manifest_path)
    native = load_json(native_path)
    gate = load_json(gate_path)
    fluidx3d_boundary = load_json(fluidx3d_boundary_path)
    inlet_source = load_json(inlet_source_path)
    inlet_reynolds_stress = load_json(inlet_reynolds_stress_path)
    boundary_source = load_json(boundary_source_path)
    boundary_protocol = load_json(boundary_protocol_path)
    coordinate_probe_protocol = load_json(coordinate_probe_protocol_path)
    validation_protocol = load_json(validation_protocol_path)
    native_preflight_pack = load_json(native_preflight_pack_path)
    time_averaging_evidence = load_json(time_averaging_evidence_path)
    inlet_diagnostics_csv = load_json(inlet_diagnostics_csv_path)
    inlet_correlation_audit = load_json(inlet_correlation_audit_path)
    canary_runtime_evidence = load_json(canary_runtime_evidence_path)
    component_sensitivity = load_json(component_sensitivity_path)
    custom_profile_af_fidelity = load_json(custom_profile_af_fidelity_path)
    next_action = classify_next_action(
        manifest,
        native,
        gate,
        fluidx3d_boundary,
        inlet_source,
        inlet_reynolds_stress,
        boundary_source,
        boundary_protocol,
        coordinate_probe_protocol,
        validation_protocol,
        native_preflight_pack,
        time_averaging_evidence,
        inlet_diagnostics_csv,
        inlet_correlation_audit,
        canary_runtime_evidence,
        component_sensitivity,
        custom_profile_af_fidelity,
    )
    return {
        "run_dir": str(run_dir),
        "artifacts": {
            "native_manifest": str(manifest_path) if manifest_path else "",
            "native_preconditions": str(native_path) if native_path else "",
            "validation_gate": str(gate_path) if gate_path else "",
            "fluidx3d_equilibrium_boundary": str(fluidx3d_boundary_path) if fluidx3d_boundary_path else "",
            "inlet_source": str(inlet_source_path) if inlet_source_path else "",
            "inlet_reynolds_stress": str(inlet_reynolds_stress_path) if inlet_reynolds_stress_path else "",
            "boundary_source": str(boundary_source_path) if boundary_source_path else "",
            "boundary_protocol": str(boundary_protocol_path) if boundary_protocol_path else "",
            "coordinate_probe_protocol": str(coordinate_probe_protocol_path) if coordinate_probe_protocol_path else "",
            "validation_protocol": str(validation_protocol_path) if validation_protocol_path else "",
            "native_preflight_pack": str(native_preflight_pack_path) if native_preflight_pack_path else "",
            "time_averaging_evidence": str(time_averaging_evidence_path) if time_averaging_evidence_path else "",
            "inlet_diagnostics_csv": str(inlet_diagnostics_csv_path) if inlet_diagnostics_csv_path else "",
            "inlet_correlation_audit": str(inlet_correlation_audit_path) if inlet_correlation_audit_path else "",
            "canary_runtime_evidence": str(canary_runtime_evidence_path) if canary_runtime_evidence_path else "",
            "component_sensitivity": str(component_sensitivity_path) if component_sensitivity_path else "",
            "custom_profile_af_fidelity": str(custom_profile_af_fidelity_path) if custom_profile_af_fidelity_path else "",
        },
        "native_manifest": manifest,
        "native_preconditions": native,
        "validation_gate": gate,
        "fluidx3d_equilibrium_boundary": fluidx3d_boundary,
        "inlet_source": inlet_source,
        "inlet_reynolds_stress": inlet_reynolds_stress,
        "boundary_source": boundary_source,
        "boundary_protocol": boundary_protocol,
        "coordinate_probe_protocol": coordinate_probe_protocol,
        "validation_protocol": validation_protocol,
        "native_preflight_pack": native_preflight_pack,
        "time_averaging_evidence": time_averaging_evidence,
        "inlet_diagnostics_csv": inlet_diagnostics_csv,
        "inlet_correlation_audit": inlet_correlation_audit,
        "canary_runtime_evidence": canary_runtime_evidence,
        "component_sensitivity": component_sensitivity,
        "custom_profile_af_fidelity": custom_profile_af_fidelity,
        "failures": collect_failures(
            manifest,
            native,
            gate,
            fluidx3d_boundary,
            inlet_source,
            inlet_reynolds_stress,
            boundary_source,
            boundary_protocol,
            coordinate_probe_protocol,
            validation_protocol,
            native_preflight_pack,
            time_averaging_evidence,
            inlet_diagnostics_csv,
            inlet_correlation_audit,
            canary_runtime_evidence,
            component_sensitivity,
            custom_profile_af_fidelity,
        ),
        "recommended_next_action": next_action,
    }


def build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    run_dirs = list(args.run_dir)
    if not run_dirs and args.template_preflight_dir:
        run_dirs.append(args.template_preflight_dir)
    elif not run_dirs and args.case_dir:
        run_dirs.append(str(Path(args.case_dir) / "preflight"))
    evidence_dirs: List[Path] = []
    if args.case_dir:
        evidence_dirs.append((Path(args.case_dir).expanduser().resolve() / "preflight").resolve())
    if args.template_preflight_dir:
        evidence_dirs.append(Path(args.template_preflight_dir).expanduser().resolve())
    runs = [analyze_run(Path(item).expanduser().resolve(), evidence_dirs) for item in run_dirs]
    case_key = infer_case(args.case, runs)
    preset = CASE_PRESETS[case_key]
    if runs:
        next_items = sorted(
            [run["recommended_next_action"] for run in runs],
            key=lambda item: (int(item["rank"]), str(item["phase"])),
        )
    else:
        next_items = [classify_next_action({}, {}, {})]

    sequence = unique_actions(
        next_items
        + supplemental_actions_from_failures(runs)
        + [
            action(
                10,
                "native_first_then_citylbm",
                "policy",
                False,
                "CityLBM should only inherit settings that improve the native FluidX3D baseline.",
                "Do not tune CityLBM against AIJ before native FluidX3D passes the same input, averaging and probe gates.",
            ),
            action(
                11,
                "batch_only_after_single_case_passes",
                "policy",
                False,
                "Batching many directions before one strict case passes multiplies bad evidence.",
                "Keep Case E ac+N as the first strict chain; add Case A/E batches only after this gate is stable.",
            ),
        ]
    )
    batches = parallel_batches(args, preset, runs)
    summary = acceleration_summary(sequence, batches)
    if runs:
        summary["canary_runtime_evidence_gate"] = latest_run_gate(runs, "canary_runtime_evidence")
    else:
        summary["canary_runtime_evidence_gate"] = "missing"
    return {
        "schema": "citylbm.validation_acceleration_plan.v1",
        "generated_at": utc_now(),
        "case": case_key,
        "preset": preset,
        "runs": runs,
        "recommended_sequence": sequence,
        "command_templates": command_templates(args, preset, runs),
        "parallel_batches": batches,
        "acceleration_summary": summary,
    }


def unique_actions(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for item in sorted(items, key=lambda value: (int(value.get("rank", 999)), str(value.get("phase", "")))):
        key = str(item.get("phase", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def write_outputs(plan: Dict[str, Any], args: argparse.Namespace) -> None:
    if args.out_json:
        out = Path(args.out_json).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.out_md:
        out = Path(args.out_md).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(plan), encoding="utf-8")


def render_markdown(plan: Dict[str, Any]) -> str:
    summary = plan.get("acceleration_summary", {})
    lines = [
        "# CityLBM Validation Acceleration Plan",
        "",
        f"- Generated: {plan['generated_at']}",
        f"- Case preset: {plan['case']}",
        "",
        "## Development Time Compression",
        "",
        f"- Fastest phase: {summary.get('fastest_phase', '')}",
        f"- Next execution policy: {summary.get('next_execution_policy', '')}",
        f"- Next batch: {summary.get('next_batch_name', '')}",
        f"- Long CFD allowed now: {str(summary.get('long_cfd_allowed_now', False)).lower()}",
        f"- Canary runtime evidence gate: {summary.get('canary_runtime_evidence_gate', 'missing')}",
        f"- Parallel no-CFD command count: {summary.get('no_cfd_parallel_command_count', 0)}",
    ]
    if summary.get("next_command"):
        lines.extend(["", "### Next Command To Run First", "", "```powershell", str(summary["next_command"]), "```"])
    saved_by = summary.get("development_time_saved_by")
    if isinstance(saved_by, list) and saved_by:
        lines.append("- Time saved by:")
        for item in saved_by:
            lines.append(f"  - {item}")
    lines.extend(
        [
        "",
        "## Fastest Next Actions",
        ]
    )
    for item in plan["recommended_sequence"]:
        lines.extend(
            [
                "",
                f"### {item['rank']}. {item['phase']}",
                f"- Duration class: {item['duration_class']}",
                f"- Runs CFD: {str(item['runs_cfd']).lower()}",
                f"- Reason: {item['reason']}",
                f"- Next action: {item['next_action']}",
            ]
        )
    lines.extend(["", "## Command Templates"])
    for name, command in plan["command_templates"].items():
        lines.extend(["", f"### {name}", "", "```powershell", command, "```"])
    lines.extend(["", "## Parallel Development Batches"])
    for batch in plan.get("parallel_batches", []):
        lines.extend(
            [
                "",
                f"### {batch['rank']}. {batch['name']}",
                f"- Runs CFD: {str(batch['runs_cfd']).lower()}",
                f"- Can run in parallel: {str(batch['can_run_in_parallel']).lower()}",
                f"- Purpose: {batch['purpose']}",
                f"- Promotion gate: {batch['promotion_gate']}",
                "- Commands:",
            ]
        )
        for command in batch.get("commands", []):
            lines.extend(["", "```powershell", command, "```"])
        if batch.get("stop_if"):
            lines.append("- Stop if:")
            for item in batch["stop_if"]:
                lines.append(f"  - {item}")
    if plan["runs"]:
        lines.extend(["", "## Run Findings"])
        for run in plan["runs"]:
            lines.extend(["", f"### {run['run_dir']}"])
            failures = run.get("failures", [])
            if failures:
                lines.append("- Failures:")
                for failure in failures[:12]:
                    lines.append(f"  - {failure}")
            else:
                lines.append("- Failures: none detected from available artifacts")
    lines.append("")
    return "\n".join(lines)


def print_plan(plan: Dict[str, Any]) -> None:
    print(f"Validation acceleration plan: {plan['case']}")
    summary = plan.get("acceleration_summary", {})
    if summary:
        print(
            "Fast-track: {policy}; next_batch={batch}; long_cfd_allowed={allowed}".format(
                policy=summary.get("next_execution_policy", ""),
                batch=summary.get("next_batch_name", ""),
                allowed=str(summary.get("long_cfd_allowed_now", False)).lower(),
            )
        )
    for item in plan["recommended_sequence"]:
        print(
            "- rank {rank}: {phase} [{duration}] CFD={cfd} :: {action}".format(
                rank=item["rank"],
                phase=item["phase"],
                duration=item["duration_class"],
                cfd=str(item["runs_cfd"]).lower(),
                action=item["next_action"],
            )
        )


def main() -> int:
    args = parse_args()
    plan = build_plan(args)
    write_outputs(plan, args)
    print_plan(plan)
    fastest = plan["recommended_sequence"][0] if plan["recommended_sequence"] else {}
    if args.fail_on_blockers and fastest.get("phase") not in {
        "migrate_verified_native_settings_to_citylbm",
        "native_first_then_citylbm",
    }:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
