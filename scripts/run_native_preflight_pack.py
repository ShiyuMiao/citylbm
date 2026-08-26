#!/usr/bin/env python3
"""Create a no-CFD native validation preflight evidence package.

This script intentionally does not launch FluidX3D. It runs the fast source and
protocol audits that decide whether a case is worth a long native CFD run.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fast no-CFD preflight audits for a native FluidX3D validation case.")
    parser.add_argument("--case-dir", required=True, help="CityLBM-generated native case directory.")
    parser.add_argument("--fluidx3d-source", required=True, help="Explicit native FluidX3D source root.")
    parser.add_argument(
        "--solver-cwd",
        default="",
        help="Optional FluidX3D run working directory used by later native-run commands.",
    )
    parser.add_argument("--out-dir", default="", help="Preflight output directory. Defaults to <case-dir>/preflight.")
    parser.add_argument("--manifest-out", default="", help="Native runner manifest path. Defaults to <case-dir>/native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--metadata", default="", help="case_metadata.json. Defaults to <case-dir>/case_metadata.json.")
    parser.add_argument("--expected-aij-case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--expected-wind-direction", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument("--expected-wind-vector", default="", help="Expected airflow vector x,y,z, e.g. 0,-1,0.")
    parser.add_argument("--official-condition-filter", default="", help="Optional official RS condition/state filter, e.g. ac for AIJ Case E.")
    parser.add_argument("--official-wind-filter", default="", help="Optional official RS wind-direction filter. Defaults to --expected-wind-direction.")
    parser.add_argument(
        "--patch-metadata-identity",
        action="store_true",
        help="Write expected AIJ case, wind label and wind vector into case_metadata.json before audits.",
    )
    parser.add_argument("--official", default="", help="Optional official RS/probe CSV.")
    parser.add_argument("--af-csv", default="", help="Optional official AF inlet profile CSV with z,U,k columns.")
    parser.add_argument("--length-scale-source", default="", help="Optional official, precursor or calibrated length-scale source file.")
    parser.add_argument(
        "--length-scale-source-type",
        default="official_aij",
        choices=[
            "digital_filter_calibration",
            "literature",
            "official_aij",
            "precursor",
            "recycling",
            "sem_calibration",
            "synthetic_eddy_calibration",
            "wind_tunnel_document",
        ],
        help="Traceable source type for turbulence length-scale evidence.",
    )
    parser.add_argument("--length-scale-source-note", default="", help="Short length-scale evidence provenance note.")
    parser.add_argument("--length-scale-paper-admissible", action="store_true")
    parser.add_argument("--expected-probe-row-count", type=int, default=0)
    parser.add_argument("--expected-probe-z", type=float, default=None)
    parser.add_argument("--expected-probe-z-min", type=float, default=None)
    parser.add_argument("--expected-probe-z-max", type=float, default=None)
    parser.add_argument("--z-ref", type=float, default=None)
    parser.add_argument("--expected-uref", type=float, default=None)
    parser.add_argument(
        "--time-steps",
        type=int,
        default=None,
        help="Planned solver steps. Defaults to TimeSteps from case_metadata.json, then 40000.",
    )
    parser.add_argument(
        "--vtk-save-interval",
        type=int,
        default=None,
        help="VTK save interval in steps. Defaults to VtkOutput.SaveIntervalSteps from metadata, then 1000.",
    )
    parser.add_argument("--vtk-save-start-step", type=int, default=None)
    parser.add_argument(
        "--expected-vtk-frame-count",
        type=int,
        default=None,
        help="Expected planned VTK frame count. Defaults to metadata estimate or computed schedule.",
    )
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-vtk-frames", type=int, default=40)
    parser.add_argument("--min-vtk-step-span", type=int, default=20000)
    parser.add_argument("--diagnostic-canary-time-steps", type=int, default=500)
    parser.add_argument("--diagnostic-canary-spinup-steps", type=int, default=100)
    parser.add_argument("--diagnostic-canary-vtk-save-interval", type=int, default=100)
    parser.add_argument("--diagnostic-canary-average-last-n", type=int, default=5)
    parser.add_argument("--diagnostic-canary-min-vtk-frames", type=int, default=5)
    parser.add_argument("--diagnostic-canary-min-step-span", type=int, default=400)
    parser.add_argument(
        "--diagnostic-canary-stg-update-interval",
        type=int,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_update_interval in the short canary clone.",
    )
    parser.add_argument(
        "--diagnostic-canary-stg-intensity-scale",
        type=float,
        default=None,
        help="Optional diagnostic-only override for citylbm_stg_scale in the short canary clone.",
    )
    parser.add_argument(
        "--diagnostic-canary-stg-temporal-step-scale",
        type=float,
        default=1.5,
        help="Optional diagnostic-only override for citylbm_stg_temporal_step_scale in the short canary clone.",
    )
    parser.add_argument("--diagnostic-canary-platform-toolset", default="v143")
    parser.add_argument("--require-af-k", action="store_true")
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="Maximum workers for independent no-CFD audit steps. Defaults to a bounded CPU-based value.",
    )
    parser.add_argument(
        "--serial",
        action="store_true",
        help="Run all no-CFD audit steps sequentially for debugging.",
    )
    parser.add_argument(
        "--allow-diagnostic",
        action="store_true",
        help="Return 0 even when gates are diagnostic/fail, while preserving evidence.",
    )
    args = parser.parse_args()
    if args.diagnostic_canary_stg_update_interval is not None and args.diagnostic_canary_stg_update_interval <= 0:
        raise SystemExit("--diagnostic-canary-stg-update-interval must be positive")
    if args.diagnostic_canary_stg_intensity_scale is not None and args.diagnostic_canary_stg_intensity_scale <= 0.0:
        raise SystemExit("--diagnostic-canary-stg-intensity-scale must be positive")
    if (
        args.diagnostic_canary_stg_temporal_step_scale is not None
        and args.diagnostic_canary_stg_temporal_step_scale <= 0.0
    ):
        raise SystemExit("--diagnostic-canary-stg-temporal-step-scale must be positive")
    return args


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


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def metadata_vtk_save_start_step(metadata: Dict[str, Any]) -> Optional[int]:
    vtk = metadata.get("VtkOutput") if isinstance(metadata.get("VtkOutput"), dict) else {}
    return as_int(vtk.get("SaveStartStep") or vtk.get("StartStep"))


def metadata_vtk_save_interval(metadata: Dict[str, Any]) -> Optional[int]:
    vtk = metadata.get("VtkOutput") if isinstance(metadata.get("VtkOutput"), dict) else {}
    return as_int(
        vtk.get("SaveIntervalSteps")
        or vtk.get("SaveInterval")
        or vtk.get("IntervalSteps")
        or metadata.get("VtkSaveInterval")
        or metadata.get("SaveInterval")
    )


def metadata_expected_vtk_frame_count(metadata: Dict[str, Any]) -> Optional[int]:
    vtk = metadata.get("VtkOutput") if isinstance(metadata.get("VtkOutput"), dict) else {}
    return as_int(
        vtk.get("EstimatedPostSpinupFrameCount")
        or vtk.get("ExpectedFrameCount")
        or vtk.get("FrameCount")
        or metadata.get("ExpectedVtkFrameCount")
    )


def nested_metadata_text(metadata: Dict[str, Any], *paths: Sequence[str]) -> str:
    for path in paths:
        current: Any = metadata
        for key in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(key)
        if current is None:
            continue
        text = str(current).strip()
        if text and text != "{}":
            return text
    return ""


def resolved_official_inputs(args: argparse.Namespace, metadata: Dict[str, Any]) -> Dict[str, Any]:
    official = str(args.official or "").strip()
    official_source = "cli" if official else "missing"
    if not official:
        official = nested_metadata_text(
            metadata,
            ("OfficialRS",),
            ("OfficialRSCsv",),
            ("OfficialMeasurementCsv",),
            ("OfficialProbeCsv",),
            ("official_inputs", "RS_caseE.csv", "path"),
            ("official_inputs", "RS_caseA.csv", "path"),
            ("official_inputs", "RS", "path"),
        )
        official_source = "metadata" if official else "missing"
    af_csv = str(args.af_csv or "").strip()
    af_source = "cli" if af_csv else "missing"
    if not af_csv:
        af_csv = nested_metadata_text(
            metadata,
            ("OfficialAF",),
            ("OfficialAFCsv",),
            ("AfCsv",),
            ("InletProfileCsv",),
            ("official_inputs", "AF_caseE.csv", "path"),
            ("official_inputs", "AF_caseA.csv", "path"),
            ("official_inputs", "AF", "path"),
        )
        af_source = "metadata" if af_csv else "missing"
    return {
        "Official": official,
        "AfCsv": af_csv,
        "Sources": {
            "Official": official_source,
            "AfCsv": af_source,
        },
    }


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


def resolved_time_averaging_plan(args: argparse.Namespace, metadata: Dict[str, Any]) -> Dict[str, Any]:
    time_steps = args.time_steps if args.time_steps is not None else as_int(metadata.get("TimeSteps"))
    if time_steps is None:
        time_steps = 40000
    vtk_save_interval = args.vtk_save_interval
    if vtk_save_interval is None:
        vtk_save_interval = metadata_vtk_save_interval(metadata)
    if vtk_save_interval is None:
        vtk_save_interval = 1000
    vtk_save_start_step = args.vtk_save_start_step
    if vtk_save_start_step is None:
        vtk_save_start_step = metadata_vtk_save_start_step(metadata)
    expected_vtk_frame_count = args.expected_vtk_frame_count
    expected_source = "cli"
    if expected_vtk_frame_count is None:
        expected_vtk_frame_count = metadata_expected_vtk_frame_count(metadata)
        expected_source = "metadata"
    if expected_vtk_frame_count is None:
        expected_vtk_frame_count = planned_frame_count(time_steps, vtk_save_interval, vtk_save_start_step)
        expected_source = "computed"
    return {
        "TimeSteps": time_steps,
        "VtkSaveInterval": vtk_save_interval,
        "VtkSaveStartStep": vtk_save_start_step,
        "ExpectedVtkFrameCount": expected_vtk_frame_count,
        "AverageLastN": args.average_last_n,
        "MinimumVtkFrames": args.min_vtk_frames,
        "MinimumStepSpan": args.min_vtk_step_span,
        "Sources": {
            "TimeSteps": "cli" if args.time_steps is not None else ("metadata" if as_int(metadata.get("TimeSteps")) is not None else "default"),
            "VtkSaveInterval": "cli" if args.vtk_save_interval is not None else ("metadata" if metadata_vtk_save_interval(metadata) is not None else "default"),
            "VtkSaveStartStep": "cli" if args.vtk_save_start_step is not None else ("metadata" if metadata_vtk_save_start_step(metadata) is not None else "default_none"),
            "ExpectedVtkFrameCount": expected_source,
        },
    }


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def first_existing(base: Path, names: Sequence[str]) -> Optional[Path]:
    for name in names:
        path = base / name
        if path.is_file():
            return path.resolve()
    return None


def runtime_inlet_diagnostics_name(metadata: Dict[str, Any], setup_path: Optional[Path]) -> str:
    for key in [
        "RuntimeInletDiagnosticsCsv",
        "runtime_inlet_diagnostics_csv",
        "InletDiagnosticsCsv",
        "inlet_diagnostics_csv",
    ]:
        value = str(metadata.get(key) or "").strip()
        if value:
            return value

    if setup_path is not None and setup_path.is_file():
        source = setup_path.read_text(encoding="utf-8-sig", errors="replace")
        match = re.search(r'citylbm_inlet_diagnostics_csv\s*=\s*"([^"]+)"', source)
        if match:
            return match.group(1).strip()

    return "citylbm_inlet_turbulence_stats.csv"


def add_optional(cmd: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value)
    if text == "":
        return
    cmd.extend([flag, text])


def set_option(cmd: Sequence[str], flag: str, value: Any) -> List[str]:
    updated = list(cmd)
    text = str(value)
    if flag in updated:
        index = updated.index(flag)
        if index + 1 < len(updated):
            updated[index + 1] = text
        else:
            updated.append(text)
    else:
        updated.extend([flag, text])
    return updated


def append_flag_once(cmd: Sequence[str], flag: str) -> List[str]:
    updated = list(cmd)
    if flag not in updated:
        updated.append(flag)
    return updated


def parse_vector(text: str) -> Optional[List[float]]:
    raw = str(text or "").strip().replace("(", "").replace(")", "")
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 3:
        return None
    values: List[float] = []
    for part in parts:
        try:
            values.append(float(part))
        except ValueError:
            return None
    return values


def patch_metadata_identity(path: Path, metadata: Dict[str, Any], args: argparse.Namespace) -> bool:
    changed = False
    if args.expected_aij_case and metadata.get("AijCase") != args.expected_aij_case:
        metadata["AijCase"] = args.expected_aij_case
        changed = True
    if args.expected_wind_direction and metadata.get("WindDirection") != args.expected_wind_direction:
        metadata["WindDirection"] = args.expected_wind_direction
        changed = True
    wind_vector = parse_vector(args.expected_wind_vector)
    if wind_vector is not None and metadata.get("WindDirectionUnitVector") != wind_vector:
        metadata["WindDirectionUnitVector"] = wind_vector
        changed = True
    if changed:
        write_json(path, metadata)
    return changed


def run_step(name: str, cmd: Sequence[str], allow_fail: bool = True) -> Dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - started
    return {
        "Name": name,
        "Command": list(cmd),
        "ReturnCode": completed.returncode,
        "AllowFail": allow_fail,
        "ElapsedSeconds": round(elapsed, 3),
        "Stdout": completed.stdout,
        "Stderr": completed.stderr,
    }


def default_jobs(count: int, requested: int, serial: bool) -> int:
    if serial or count <= 1:
        return 1
    if requested > 0:
        return max(1, min(requested, count))
    cpu = 4
    try:
        import os

        cpu = os.cpu_count() or cpu
    except OSError:
        pass
    return max(1, min(count, cpu, 6))


def run_steps_parallel(
    step_specs: Sequence[Sequence[Any]],
    *,
    jobs: int,
    serial: bool,
) -> List[Dict[str, Any]]:
    if not step_specs:
        return []
    if serial or jobs <= 1 or len(step_specs) == 1:
        return [run_step(str(name), cmd, bool(allow_fail)) for name, cmd, allow_fail in step_specs]

    results_by_index: Dict[int, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = {
            executor.submit(run_step, str(name), cmd, bool(allow_fail)): index
            for index, (name, cmd, allow_fail) in enumerate(step_specs)
        }
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            results_by_index[index] = future.result()
    return [results_by_index[index] for index in range(len(step_specs))]


def gate_value(data: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            nested = value.get("Gate") or value.get("gate")
            if nested is not None:
                return str(nested).strip().lower()
        if value is not None:
            return str(value).strip().lower()
    return ""


def collect_gate_reasons(label: str, data: Dict[str, Any], *, gate_keys: Sequence[str]) -> List[str]:
    gate = gate_value(data, *gate_keys)
    if gate in {"pass", "ready_for_validation_run", "paper_grade", "paper_grade_candidate"}:
        return []
    reasons: List[str] = []
    reason_keys = [
        "Reasons",
        "reasons",
        "paper_grade_inlet_source_gate_reasons",
        "paper_grade_boundary_source_gate_reasons",
    ]
    reason_keys.extend(f"{key}_reasons" for key in gate_keys)
    for key in reason_keys:
        value = data.get(key)
        if isinstance(value, list):
            reasons.extend(f"{label}:{item}" for item in value if str(item).strip())
    if not reasons:
        reasons.append(f"{label}:gate_not_pass:{gate or 'missing'}")
    return reasons


def truthy(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def build_diagnostic_canary_gate(loaded: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Decide whether a short native FluidX3D run is worth launching.

    This is deliberately weaker than the paper-grade gate. It only admits a
    canary run when source/protocol defects that would make the short run
    uninterpretable are closed.
    """
    inlet = loaded.get("InletSourceAudit", {})
    inlet_stress = loaded.get("InletReynoldsStressEvidence", {})
    boundary = loaded.get("BoundarySourceAudit", {})
    fluid_boundary_source = "FluidX3DEquilibriumBoundaryAudit"
    fluid_boundary = loaded.get("FluidX3DEquilibriumBoundaryAudit", {})
    diagnostic_fluid_boundary = loaded.get("DiagnosticDdfReconstructionRoute", {})
    if diagnostic_fluid_boundary:
        fluid_boundary_source = "DiagnosticDdfReconstructionRoute"
        fluid_boundary = diagnostic_fluid_boundary
    coordinate = loaded.get("CoordinateProbeProtocolAudit", {})
    time_avg = loaded.get("TimeAveragingEvidence", {})
    validation = loaded.get("ValidationProtocolAudit", {})

    reasons: List[str] = []
    limitations: List[str] = []

    if gate_value(inlet, "inlet_source_gate") != "pass":
        reasons.append(f"inlet_source_gate_not_pass:{gate_value(inlet, 'inlet_source_gate') or 'missing'}")
    if gate_value(inlet, "runtime_inlet_diagnostics_source_gate") != "pass":
        reasons.append(
            "runtime_inlet_diagnostics_source_gate_not_pass:"
            f"{gate_value(inlet, 'runtime_inlet_diagnostics_source_gate') or 'missing'}"
        )
    if not truthy(inlet.get("short_canary_allowed_by_codegen_route")):
        reasons.append(
            "setup_codegen_route_not_current_citylbm:"
            f"{inlet.get('setup_inlet_codegen_route') or 'missing'}"
        )
    inlet_paper_gate = gate_value(inlet, "paper_grade_inlet_source_gate")
    if inlet_paper_gate != "pass":
        paper_reasons = inlet.get("paper_grade_inlet_source_gate_reasons") or []
        hard_inlet_reasons = {
            "source_not_distribution_consistent",
            "source_velocity_field_only",
            "source_correlated_velocity_field_only_without_distribution_reconstruction",
            "source_reynolds_stress_tensor_declared_but_not_used_in_inlet",
        }
        for reason in paper_reasons:
            if reason in hard_inlet_reasons:
                reasons.append(f"inlet_paper_hard_blocker:{reason}")
        if not any(str(reason).startswith("inlet_paper_hard_blocker:") for reason in reasons):
            limitations.append(f"inlet_not_paper_grade:{inlet_paper_gate or 'missing'}")

    inlet_stress_source = str(inlet_stress.get("source_type") or "").strip()
    inlet_stress_gate = gate_value(inlet_stress, "gate", "Gate")
    inlet_stress_paper_gate = gate_value(inlet_stress, "paper_grade_gate", "PaperGradeGate")
    if inlet_stress_source == "measured_diagonal_rms":
        limitations.append("inlet_reynolds_stress_diagonal_rms_only_missing_offdiagonal_covariances")
    elif inlet_stress_source == "isotropic_from_k":
        limitations.append("inlet_reynolds_stress_isotropic_k_only")
    elif inlet_stress_source in {"measured_tensor", "precursor"} and inlet_stress_paper_gate != "pass":
        limitations.append(
            f"inlet_reynolds_stress_paper_gate_not_pass:{inlet_stress_paper_gate or 'missing'}"
        )
    elif not inlet_stress_source:
        limitations.append(f"inlet_reynolds_stress_evidence_missing_or_unclassified:{inlet_stress_gate or 'missing'}")

    if gate_value(fluid_boundary, "Gate") != "pass":
        reasons.append(f"fluidx3d_equilibrium_boundary_gate_not_pass:{gate_value(fluid_boundary, 'Gate') or 'missing'}")

    if not truthy(boundary.get("boundary_source_coherent")):
        reasons.append("boundary_source_not_coherent")
    if not truthy(boundary.get("has_type_e_velocity_initialization_before_device_upload")):
        reasons.append("type_e_boundary_velocity_initialization_not_uploaded")
    if gate_value(boundary, "boundary_source_gate") != "pass":
        reasons.append(f"boundary_source_gate_not_pass:{gate_value(boundary, 'boundary_source_gate') or 'missing'}")
    if gate_value(boundary, "paper_grade_boundary_source_gate") != "pass":
        limitations.append(
            f"boundary_not_paper_grade:{gate_value(boundary, 'paper_grade_boundary_source_gate') or 'missing'}"
        )

    if gate_value(coordinate, "coordinate_probe_protocol_gate", "Gate") != "pass":
        reasons.append(
            "coordinate_probe_protocol_gate_not_pass:"
            f"{gate_value(coordinate, 'coordinate_probe_protocol_gate', 'Gate') or 'missing'}"
        )
    if gate_value(time_avg, "Gate") != "pass":
        limitations.append(f"time_averaging_plan_not_paper_grade:{gate_value(time_avg, 'Gate') or 'missing'}")

    pre_run_gate = gate_value(validation, "PreRunGate")
    if pre_run_gate not in {"ready_for_validation_run", "pass", "diagnostic_only"}:
        reasons.append(f"validation_pre_run_gate_not_usable:{pre_run_gate or 'missing'}")
    if gate_value(validation, "PaperGradeGate", "Gate") != "pass":
        limitations.append(
            f"validation_not_paper_grade:{gate_value(validation, 'PaperGradeGate', 'Gate') or 'missing'}"
        )

    return {
        "Gate": "pass" if not reasons else "fail",
        "Purpose": "short_native_fluidx3d_canary_before_long_validation_run",
        "EvidenceUseClass": {
            "InletStressSourceType": inlet_stress_source or "missing",
            "InletStressGate": inlet_stress_gate or "missing",
            "InletStressPaperGradeGate": inlet_stress_paper_gate or "missing",
            "InletStressCanSupportPaperValidation": inlet_stress_paper_gate == "pass",
            "BoundaryCanSupportPaperValidation": gate_value(boundary, "paper_grade_boundary_source_gate") == "pass",
            "ShortCanaryBoundaryGateSource": fluid_boundary_source,
            "ValidationCanSupportPaperValidation": gate_value(validation, "PaperGradeGate", "Gate") == "pass",
        },
        "Interpretation": (
            "Can start a short diagnostic native FluidX3D run; do not report accuracy as paper-grade."
            if not reasons
            else "Do not start the short native FluidX3D canary yet."
        ),
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Limitations": limitations,
        "LimitationsCsv": ";".join(limitations),
    }


def build_next_optimization_target(
    native_preconditions: Dict[str, Any],
    diagnostic_canary: Dict[str, Any],
) -> Dict[str, Any]:
    """Expose the native precondition audit's top blocker as a stable field.

    The full audit already contains detailed per-stage evidence. This compact
    field lets wrappers and CI choose the next experiment without reparsing
    long free-form reason lists.
    """
    priorities = native_preconditions.get("native_diagnostic_priority")
    top = priorities[0] if isinstance(priorities, list) and priorities else {}
    key = str(
        top.get("key")
        or native_preconditions.get("native_top_blocking_priority_key")
        or native_preconditions.get("native_rerun_prescription_top_key")
        or ""
    ).strip()
    diagnosis = str(
        top.get("diagnosis")
        or native_preconditions.get("native_top_blocking_priority_diagnosis")
        or ""
    ).strip()
    next_action = str(
        top.get("next_action")
        or native_preconditions.get("native_top_blocking_priority_next_action")
        or native_preconditions.get("native_rerun_prescription_summary")
        or ""
    ).strip()
    experiment = str(
        native_preconditions.get("native_rerun_prescription_experiment")
        or ""
    ).strip()
    accuracy_allowed = bool(native_preconditions.get("native_accuracy_interpretation_allowed"))
    canary_gate = str(diagnostic_canary.get("Gate") or "missing").strip().lower()

    if not key and accuracy_allowed:
        key = "ready_for_accuracy_interpretation"
        diagnosis = "All native precondition stages are closed."
        next_action = "Run or interpret the native paper-length FluidX3D candidate under the same hashes."
    elif not key:
        key = "native_preconditions_missing"
        diagnosis = "Native precondition audit did not produce a top blocking priority."
        next_action = "Fix native_preconditions_audit generation before launching or interpreting CFD."

    return {
        "Schema": "citylbm.next_optimization_target.v1",
        "Key": key,
        "Rank": top.get("rank") if isinstance(top, dict) else None,
        "ReasonCount": top.get("reason_count") if isinstance(top, dict) else None,
        "Reasons": top.get("reasons", []) if isinstance(top, dict) else [],
        "Diagnosis": diagnosis,
        "NextAction": next_action,
        "RequiredExperiment": experiment,
        "DiagnosticCanaryGate": canary_gate,
        "ShortDiagnosticCanaryAllowed": canary_gate == "pass",
        "AccuracyInterpretationAllowed": accuracy_allowed,
        "AccuracyInterpretationGate": native_preconditions.get("native_accuracy_interpretation_gate", "missing"),
    }


def build_development_triage(
    loaded: Dict[str, Dict[str, Any]],
    diagnostic_canary: Dict[str, Any],
    reasons: Sequence[str],
    *,
    diagnostic_canary_case_command: Optional[Sequence[str]] = None,
    diagnostic_canary_command: Optional[Sequence[str]] = None,
    inlet_diagnostics_audit_command: Optional[Sequence[str]] = None,
    inlet_correlation_audit_command: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Summarize what blocks the next run without requiring manual reason parsing."""
    patch = loaded.get("LegacyRuntimeInletDiagnosticsPatch", {})
    diagnostic_source_patch = loaded.get("DiagnosticFluidX3DSourcePatch", {})
    diagnostic_ddf_route = loaded.get("DiagnosticDdfReconstructionRoute", {})
    inlet = loaded.get("InletSourceAudit", {})
    stress = loaded.get("InletReynoldsStressEvidence", {})
    length_scale = loaded.get("TurbulenceLengthScaleEvidence", {})
    boundary = loaded.get("BoundaryProtocolAudit", {})
    coordinate = loaded.get("CoordinateProbeProtocolAudit", {})
    time_avg = loaded.get("TimeAveragingEvidence", {})
    native_preconditions = loaded.get("NativePreconditionsAudit", {})
    next_optimization_target = build_next_optimization_target(native_preconditions, diagnostic_canary)

    auto_fixes: List[Dict[str, Any]] = []
    if patch:
        auto_fixes.append(
            {
                "Name": "legacy_runtime_inlet_diagnostics_patch",
                "Gate": patch.get("Gate", "missing"),
                "Changed": bool(patch.get("Changed")),
                "AlreadyPatched": bool(patch.get("AlreadyPatched")),
                "Artifact": patch.get("Setup", ""),
                "Outcome": (
                    "runtime_inlet_diagnostics_source_gate_can_be_audited"
                    if patch.get("Gate") == "pass"
                    else "runtime_inlet_diagnostics_patch_failed"
                ),
            }
        )
    if diagnostic_source_patch or diagnostic_ddf_route:
        auto_fixes.append(
            {
                "Name": "diagnostic_fluidx3d_ddf_reconstruction_route",
                "SourcePatchGate": diagnostic_source_patch.get("Gate", "missing"),
                "CaseRouteGate": diagnostic_ddf_route.get("Gate", "missing"),
                "SourceChanged": bool(diagnostic_source_patch.get("Changed")),
                "CaseChanged": bool(diagnostic_ddf_route.get("Changed")),
                "Artifact": diagnostic_ddf_route.get("DefinesPath", ""),
                "Outcome": (
                    "short_canary_boundary_ddf_route_ready"
                    if diagnostic_ddf_route.get("Gate") == "pass"
                    else "short_canary_boundary_ddf_route_not_ready"
                ),
            }
        )

    external_evidence: List[Dict[str, Any]] = []
    inlet_reasons = inlet.get("paper_grade_inlet_source_gate_reasons") or []
    if not isinstance(inlet_reasons, list):
        inlet_reasons = [inlet_reasons]
    stress_reasons = stress.get("reasons") or stress.get("Reasons") or []
    if not isinstance(stress_reasons, list):
        stress_reasons = [stress_reasons]
    length_reasons = length_scale.get("reasons") or length_scale.get("Reasons") or []
    if not isinstance(length_reasons, list):
        length_reasons = [length_reasons]
    boundary_reasons = boundary.get("boundary_protocol_gate_reasons") or boundary.get("Reasons") or []
    if not isinstance(boundary_reasons, list):
        boundary_reasons = [boundary_reasons]

    if any("reynolds" in str(item).lower() or "offdiagonal" in str(item).lower() for item in inlet_reasons + stress_reasons):
        external_evidence.append(
            {
                "Name": "full_reynolds_stress_tensor_or_precursor",
                "RequiredBefore": "paper_length_cfd",
                "CurrentSourceType": stress.get("source_type", "missing"),
                "Gate": stress.get("paper_grade_gate", stress.get("gate", "missing")),
                "Reason": "AF k/diagonal RMS can support diagnostic canaries, but not paper-grade turbulent-inlet evidence without full tensor or precursor binding.",
            }
        )
    if length_reasons or any("length_scale" in str(item).lower() for item in inlet_reasons):
        external_evidence.append(
            {
                "Name": "turbulent_length_scale_source",
                "RequiredBefore": "paper_length_cfd",
                "Gate": length_scale.get("paper_grade_gate", length_scale.get("Gate", "missing")),
                "Reason": "Digital-filter/SEM inlet needs a traceable integral length-scale, precursor, recycling, or calibrated source.",
            }
        )
    if boundary_reasons:
        external_evidence.append(
            {
                "Name": "aij_equivalent_boundary_protocol",
                "RequiredBefore": "paper_length_cfd",
                "Gate": boundary.get("boundary_protocol_gate", boundary.get("Gate", "missing")),
                "Reason": "Boundary, roughness, blockage, fetch and outlet/side/top evidence must be source-backed and hash-bound.",
            }
        )

    coordinate_gate = gate_value(coordinate, "coordinate_probe_protocol_gate", "Gate")
    time_gate = gate_value(time_avg, "Gate")
    short_canary_allowed = diagnostic_canary.get("Gate") == "pass"
    long_cfd_allowed = not reasons
    diagnostics_csv_name = "runtime inlet diagnostics CSV"
    if inlet_diagnostics_audit_command and len(inlet_diagnostics_audit_command) >= 3:
        diagnostics_csv_name = Path(str(inlet_diagnostics_audit_command[2])).name or diagnostics_csv_name
    if long_cfd_allowed:
        next_action = "Run the native paper-length FluidX3D candidate with the same metadata and hashes."
    elif short_canary_allowed:
        next_action = (
            f"Run only a short diagnostic native canary, then audit {diagnostics_csv_name} and inlet VTK correlation; "
            "do not use the accuracy as paper-grade until external evidence items pass."
        )
    else:
        next_action = "Do not launch CFD yet; close DiagnosticCanaryGate reasons first."

    suggested_commands: List[Dict[str, Any]] = []
    if short_canary_allowed and diagnostic_canary_case_command:
        suggested_commands.append(
            {
                "Name": "prepare_native_diagnostic_canary_case",
                "Command": list(diagnostic_canary_case_command),
                "UseClass": "create_short_runtime_clone_not_for_paper_accuracy_claims",
                "Prerequisite": "run after no-CFD preflight has patched runtime inlet diagnostics",
            }
        )
    if short_canary_allowed and diagnostic_canary_command:
        suggested_commands.append(
            {
                "Name": "run_native_diagnostic_canary",
                "Command": list(diagnostic_canary_command),
                "UseClass": "diagnostic_only_not_for_paper_accuracy_claims",
                "Prerequisite": "case setup.cpp already uses a short diagnostic step count; this command does not rewrite solver steps",
            }
        )
    if short_canary_allowed and inlet_diagnostics_audit_command:
        suggested_commands.append(
            {
                "Name": "audit_runtime_inlet_diagnostics_after_canary",
                "Command": list(inlet_diagnostics_audit_command),
                "UseClass": "diagnostic_inlet_u_k_rms_preservation_check",
                "Prerequisite": f"run_native_diagnostic_canary produced {diagnostics_csv_name}",
            }
        )
    if short_canary_allowed and inlet_correlation_audit_command:
        suggested_commands.append(
            {
                "Name": "audit_inlet_correlation_after_canary",
                "Command": list(inlet_correlation_audit_command),
                "UseClass": "diagnostic_inlet_time_space_correlation_and_k_tke_check",
                "Prerequisite": "run_native_diagnostic_canary produced post-spinup u-*.vtk frames",
            }
        )

    return {
        "Schema": "citylbm.native_preflight_development_triage.v1",
        "AutomaticCodeFixes": auto_fixes,
        "ExternalEvidenceRequired": external_evidence,
        "ShortDiagnosticCanaryAllowed": short_canary_allowed,
        "LongCfdAllowedNow": long_cfd_allowed,
        "PaperGradeBlocked": not long_cfd_allowed,
        "CoordinateProbeGate": coordinate_gate or "missing",
        "TimeAveragingGate": time_gate or "missing",
        "DiagnosticCanaryGate": diagnostic_canary.get("Gate", "missing"),
        "NextOptimizationTarget": next_optimization_target,
        "SuggestedCommands": suggested_commands,
        "FastestNextAction": next_action,
    }


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    script_dir = repo / "scripts"
    py = sys.executable
    case_dir = Path(args.case_dir).expanduser().resolve()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    solver_cwd = Path(args.solver_cwd).expanduser().resolve() if args.solver_cwd.strip() else None
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else case_dir / "preflight"
    metadata = Path(args.metadata).expanduser().resolve() if args.metadata else case_dir / "case_metadata.json"
    metadata_json = read_json(metadata)
    metadata_identity_patched = False
    if args.patch_metadata_identity and metadata_json:
        metadata_identity_patched = patch_metadata_identity(metadata, metadata_json, args)
        metadata_json = read_json(metadata)
    time_averaging_plan = resolved_time_averaging_plan(args, metadata_json)
    official_input_plan = resolved_official_inputs(args, metadata_json)
    manifest_out = (
        Path(args.manifest_out).expanduser().resolve()
        if args.manifest_out
        else case_dir / "native_fluidx3d_baseline_manifest.json"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    setup = first_existing(case_dir, ["src/setup.cpp", "setup.cpp"])
    defines = first_existing(case_dir, ["src/defines.hpp", "defines.hpp"])
    inlet_source = out_dir / "inlet_source_audit.json"
    inlet_reynolds_stress = out_dir / "inlet_reynolds_stress_evidence.json"
    boundary_source = out_dir / "boundary_source_audit.json"
    fluidx3d_equilibrium_boundary = out_dir / "fluidx3d_equilibrium_boundary_audit.json"
    diagnostic_fluidx3d_source_patch = out_dir / "diagnostic_fluidx3d_equilibrium_boundary_source_patch.json"
    diagnostic_ddf_reconstruction_route = out_dir / "diagnostic_ddf_reconstruction_route.json"
    diagnostic_fluidx3d_equilibrium_boundary = out_dir / "diagnostic_fluidx3d_equilibrium_boundary_audit.json"
    boundary_protocol_template = out_dir / "boundary_protocol_evidence_template.json"
    boundary_protocol = out_dir / "boundary_protocol_audit.json"
    coordinate_probe_bound_metadata = out_dir / "case_metadata.coordinate_probe_bound.json"
    inlet_bound_metadata = out_dir / "case_metadata.inlet_bound.json"
    coordinate_probe_protocol = out_dir / "coordinate_probe_protocol_audit.json"
    inlet_reynolds_stress_template = out_dir / "inlet_reynolds_stress_tensor_template.csv"
    inlet_precursor_template = out_dir / "equivalent_precursor_evidence_template.json"
    turbulence_length_scale_evidence = out_dir / "turbulence_length_scale_evidence.json"
    time_averaging_evidence = out_dir / "time_averaging_evidence.json"
    validation_protocol = out_dir / "validation_protocol_audit.json"
    native_preconditions = out_dir / "native_preconditions_audit.json"
    runtime_inlet_diagnostics_patch = out_dir / "patch_legacy_runtime_inlet_diagnostics_manifest.json"
    diagnostic_canary_case_dir = out_dir / "diagnostic_canary_case"
    diagnostic_canary_case_manifest = out_dir / "diagnostic_canary_case_manifest.json"
    diagnostic_solver_source_root = out_dir / "diagnostic_fluidx3d_source"
    diagnostic_solver_source_manifest = out_dir / "diagnostic_solver_source_manifest.json"
    native_diagnostic_canary_manifest = out_dir / "native_diagnostic_canary_manifest.json"
    diagnostic_solver_cwd = solver_cwd if solver_cwd else out_dir / "diagnostic_solver_cwd"
    runtime_inlet_diagnostics_csv = diagnostic_solver_cwd / runtime_inlet_diagnostics_name(metadata_json, setup)
    runtime_inlet_diagnostics_audit = out_dir / "runtime_inlet_diagnostics_csv_audit.json"
    runtime_inlet_diagnostics_summary = out_dir / "runtime_inlet_diagnostics_csv_summary.csv"
    inlet_correlation_audit = out_dir / "inlet_correlation_audit.json"
    preflight_manifest = out_dir / "native_preflight_pack_manifest.json"

    steps: List[Dict[str, Any]] = []
    initial_step_specs: List[Sequence[Any]] = []
    bind_coordinate_cmd = [
        py,
        str(script_dir / "bind_coordinate_probe_protocol_metadata.py"),
        "--metadata",
        str(metadata),
        "--case-dir",
        str(case_dir),
        "--out",
        str(coordinate_probe_bound_metadata),
        "--sampling-method",
        "nearest-valid",
    ]
    if setup is not None:
        bind_coordinate_cmd.extend(["--setup", str(setup)])
    add_optional(bind_coordinate_cmd, "--case-label", args.expected_aij_case)
    add_optional(bind_coordinate_cmd, "--wind-direction", args.expected_wind_direction)
    add_optional(bind_coordinate_cmd, "--wind-vector", args.expected_wind_vector)
    add_optional(bind_coordinate_cmd, "--probe-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
    add_optional(bind_coordinate_cmd, "--z-ref", args.z_ref)
    add_optional(bind_coordinate_cmd, "--uref", args.expected_uref)
    add_optional(bind_coordinate_cmd, "--official-rs", official_input_plan["Official"])
    add_optional(bind_coordinate_cmd, "--official-af", official_input_plan["AfCsv"])
    steps.append(run_step("bind_coordinate_probe_protocol_metadata", bind_coordinate_cmd))
    metadata_for_coordinate_probe = coordinate_probe_bound_metadata if coordinate_probe_bound_metadata.is_file() else metadata

    if setup is not None:
        boundary_cmd = [
            py,
            str(script_dir / "audit_boundary_source.py"),
            "--setup",
            str(setup),
            "--metadata",
            str(metadata),
            "--out",
            str(boundary_source),
        ]
        if defines is not None:
            boundary_cmd.extend(["--defines", str(defines)])
        initial_step_specs.append(("audit_boundary_source", boundary_cmd, True))
    else:
        write_json(inlet_source, {"paper_grade_inlet_source_gate": "fail", "Reasons": ["setup_cpp_missing"]})
        write_json(boundary_source, {"paper_grade_boundary_source_gate": "fail", "Reasons": ["setup_cpp_missing"]})
        steps.append({"Name": "audit_inlet_source", "Command": [], "ReturnCode": 2, "AllowFail": True, "ElapsedSeconds": 0.0, "Stdout": "", "Stderr": "setup_cpp_missing"})
        steps.append({"Name": "audit_boundary_source", "Command": [], "ReturnCode": 2, "AllowFail": True, "ElapsedSeconds": 0.0, "Stdout": "", "Stderr": "setup_cpp_missing"})

    fluidx3d_boundary_cmd = [
        py,
        str(script_dir / "audit_fluidx3d_equilibrium_boundary.py"),
        "--fluidx3d-source",
        str(source_root),
        "--out",
        str(fluidx3d_equilibrium_boundary),
    ]
    initial_step_specs.append(("audit_fluidx3d_equilibrium_boundary", fluidx3d_boundary_cmd, True))

    boundary_template_cmd = [
        py,
        str(script_dir / "create_boundary_protocol_evidence_template.py"),
        str(case_dir),
        "--metadata",
        str(metadata),
        "--out",
        str(boundary_protocol_template),
        "--force",
    ]
    add_optional(boundary_template_cmd, "--case", args.expected_aij_case)
    add_optional(boundary_template_cmd, "--wind-direction", args.expected_wind_direction)
    initial_step_specs.append(("create_boundary_protocol_evidence_template", boundary_template_cmd, True))

    coordinate_probe_protocol_cmd = [
        py,
            str(script_dir / "audit_coordinate_probe_protocol.py"),
            str(case_dir),
            "--metadata",
            str(metadata_for_coordinate_probe),
            "--out",
            str(coordinate_probe_protocol),
    ]
    add_optional(coordinate_probe_protocol_cmd, "--expected-aij-case", args.expected_aij_case)
    add_optional(coordinate_probe_protocol_cmd, "--expected-wind-direction", args.expected_wind_direction)
    add_optional(coordinate_probe_protocol_cmd, "--expected-wind-vector", args.expected_wind_vector)
    add_optional(coordinate_probe_protocol_cmd, "--official", official_input_plan["Official"])
    add_optional(coordinate_probe_protocol_cmd, "--af-csv", official_input_plan["AfCsv"])
    add_optional(coordinate_probe_protocol_cmd, "--official-condition-filter", args.official_condition_filter)
    add_optional(coordinate_probe_protocol_cmd, "--official-wind-filter", args.official_wind_filter)
    add_optional(coordinate_probe_protocol_cmd, "--expected-probe-row-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
    add_optional(coordinate_probe_protocol_cmd, "--expected-probe-z", args.expected_probe_z)
    add_optional(coordinate_probe_protocol_cmd, "--expected-probe-z-min", args.expected_probe_z_min)
    add_optional(coordinate_probe_protocol_cmd, "--expected-probe-z-max", args.expected_probe_z_max)
    add_optional(coordinate_probe_protocol_cmd, "--z-ref", args.z_ref)
    add_optional(coordinate_probe_protocol_cmd, "--expected-uref", args.expected_uref)
    initial_step_specs.append(("audit_coordinate_probe_protocol", coordinate_probe_protocol_cmd, True))

    inlet_reynolds_stress_template_cmd = [
        py,
        str(script_dir / "create_inlet_reynolds_stress_template.py"),
        "--metadata",
        str(metadata),
        "--out-csv",
        str(inlet_reynolds_stress_template),
        "--out-precursor-json",
        str(inlet_precursor_template),
        "--force",
    ]
    add_optional(inlet_reynolds_stress_template_cmd, "--af-csv", official_input_plan["AfCsv"])
    add_optional(inlet_reynolds_stress_template_cmd, "--case", args.expected_aij_case)
    add_optional(inlet_reynolds_stress_template_cmd, "--wind-direction", args.expected_wind_direction)
    initial_step_specs.append(("create_inlet_reynolds_stress_template", inlet_reynolds_stress_template_cmd, True))

    length_scale_evidence_cmd = [
        py,
        str(script_dir / "create_turbulence_length_scale_evidence_template.py"),
        "--metadata",
        str(metadata),
        "--source-type",
        args.length_scale_source_type,
        "--out",
        str(turbulence_length_scale_evidence),
        "--force",
    ]
    add_optional(length_scale_evidence_cmd, "--source-path", args.length_scale_source)
    add_optional(length_scale_evidence_cmd, "--source-note", args.length_scale_source_note)
    add_optional(length_scale_evidence_cmd, "--case", args.expected_aij_case)
    add_optional(length_scale_evidence_cmd, "--wind-direction", args.expected_wind_direction)
    if args.length_scale_paper_admissible:
        length_scale_evidence_cmd.append("--paper-admissible")
    initial_step_specs.append(("create_turbulence_length_scale_evidence", length_scale_evidence_cmd, True))

    time_averaging_cmd = [
        py,
        str(script_dir / "build_time_averaging_evidence.py"),
        "--case-dir",
        str(case_dir),
        "--out",
        str(time_averaging_evidence),
        "--time-steps",
        str(time_averaging_plan["TimeSteps"]),
        "--vtk-save-interval",
        str(time_averaging_plan["VtkSaveInterval"]),
        "--average-last-n",
        str(time_averaging_plan["AverageLastN"]),
        "--min-vtk-frames",
        str(time_averaging_plan["MinimumVtkFrames"]),
        "--min-vtk-step-span",
        str(time_averaging_plan["MinimumStepSpan"]),
    ]
    add_optional(time_averaging_cmd, "--expected-vtk-frame-count", time_averaging_plan["ExpectedVtkFrameCount"])
    add_optional(time_averaging_cmd, "--vtk-save-start-step", time_averaging_plan["VtkSaveStartStep"])
    initial_step_specs.append(("build_time_averaging_evidence", time_averaging_cmd, True))

    initial_jobs = default_jobs(len(initial_step_specs), args.jobs, args.serial)
    steps.extend(run_steps_parallel(initial_step_specs, jobs=initial_jobs, serial=args.serial))

    bind_length_scale_cmd = [
        py,
        str(script_dir / "bind_turbulence_length_scale_metadata.py"),
        "--metadata",
        str(metadata_for_coordinate_probe),
        "--evidence-json",
        str(turbulence_length_scale_evidence),
        "--out",
        str(inlet_bound_metadata),
        "--source-note",
        "Bound by native preflight pack before inlet-source audit; diagnostic evidence remains diagnostic.",
    ]
    steps.append(run_step("bind_turbulence_length_scale_metadata", bind_length_scale_cmd))
    metadata_for_inlet_audit = inlet_bound_metadata if inlet_bound_metadata.is_file() else metadata_for_coordinate_probe

    bind_reynolds_stress_cmd = [
        py,
        str(script_dir / "bind_inlet_reynolds_stress_metadata.py"),
        "--metadata",
        str(metadata_for_inlet_audit),
        "--stress-csv",
        str(inlet_reynolds_stress_template),
        "--out",
        str(inlet_bound_metadata),
        "--source-note",
        "Template identity bound by native preflight pack; not paper-grade until full tensor or precursor evidence passes.",
    ]
    steps.append(run_step("bind_inlet_reynolds_stress_metadata", bind_reynolds_stress_cmd))
    metadata_for_inlet_audit = inlet_bound_metadata if inlet_bound_metadata.is_file() else metadata_for_inlet_audit

    if setup is not None:
        runtime_inlet_patch_cmd = [
            py,
            str(script_dir / "patch_legacy_runtime_inlet_diagnostics.py"),
            "--setup",
            str(setup),
            "--out",
            str(runtime_inlet_diagnostics_patch),
        ]
        steps.append(run_step("patch_legacy_runtime_inlet_diagnostics", runtime_inlet_patch_cmd))

        inlet_cmd = [
            py,
            str(script_dir / "audit_inlet_source.py"),
            "--setup",
            str(setup),
            "--metadata",
            str(metadata_for_inlet_audit),
            "--out",
            str(inlet_source),
        ]
        if defines is not None:
            inlet_cmd.extend(["--defines", str(defines)])
        steps.append(run_step("audit_inlet_source", inlet_cmd))
    else:
        write_json(inlet_source, {"paper_grade_inlet_source_gate": "fail", "Reasons": ["setup_cpp_missing"]})
        write_json(
            runtime_inlet_diagnostics_patch,
            {"Gate": "fail", "Reasons": ["setup_cpp_missing"], "AlreadyPatched": False, "Changed": False},
        )

    boundary_protocol_cmd = [
        py,
        str(script_dir / "audit_boundary_protocol.py"),
        str(case_dir),
        "--metadata",
        str(metadata),
        "--evidence",
        str(boundary_protocol_template),
        "--out",
        str(boundary_protocol),
    ]
    add_optional(boundary_protocol_cmd, "--expected-aij-case", args.expected_aij_case)
    add_optional(boundary_protocol_cmd, "--expected-wind-direction", args.expected_wind_direction)
    steps.append(run_step("audit_boundary_protocol", boundary_protocol_cmd))

    inlet_reynolds_stress_cmd = [
        py,
        str(script_dir / "build_inlet_reynolds_stress_evidence.py"),
        "--metadata",
        str(metadata_for_inlet_audit),
        "--case",
        args.expected_aij_case,
        "--wind-direction-label",
        args.expected_wind_direction,
        "--source-type",
        "auto",
        "--stress-csv",
        str(inlet_reynolds_stress_template),
        "--precursor-evidence",
        str(inlet_precursor_template),
        "--require-run-binding",
        "--out",
        str(inlet_reynolds_stress),
    ]
    add_optional(inlet_reynolds_stress_cmd, "--af-csv", official_input_plan["AfCsv"])
    steps.append(run_step("build_inlet_reynolds_stress_evidence", inlet_reynolds_stress_cmd))

    validation_protocol_cmd = [
        py,
        str(script_dir / "write_validation_protocol_audit.py"),
        "--case-dir",
        str(case_dir),
        "--metadata",
        str(metadata_for_inlet_audit),
        "--out",
        str(validation_protocol),
        "--inlet-source-audit",
        str(inlet_source),
        "--inlet-reynolds-stress-evidence",
        str(inlet_reynolds_stress),
        "--boundary-source-audit",
        str(boundary_source),
        "--boundary-protocol-audit",
        str(boundary_protocol),
        "--coordinate-probe-protocol-audit",
        str(coordinate_probe_protocol),
        "--time-averaging-evidence",
        str(time_averaging_evidence),
    ]
    add_optional(validation_protocol_cmd, "--case", args.expected_aij_case)
    add_optional(validation_protocol_cmd, "--wind-direction-label", args.expected_wind_direction)
    add_optional(validation_protocol_cmd, "--wind-vector", args.expected_wind_vector)
    steps.append(run_step("write_validation_protocol_audit", validation_protocol_cmd))

    native_runner_cmd = [
        py,
        str(script_dir / "run_native_fluidx3d_case.py"),
        "--case-dir",
        str(case_dir),
        "--fluidx3d-source",
        str(source_root),
        "--metadata",
        str(metadata_for_inlet_audit),
        "--out",
        str(manifest_out),
        "--validation-protocol-audit",
        str(validation_protocol),
        "--inlet-source-audit",
        str(inlet_source),
        "--boundary-source-audit",
        str(boundary_source),
        "--coordinate-probe-protocol-audit",
        str(coordinate_probe_protocol),
        "--time-steps",
        str(time_averaging_plan["TimeSteps"]),
        "--vtk-save-interval",
        str(time_averaging_plan["VtkSaveInterval"]),
        "--average-last-n",
        str(time_averaging_plan["AverageLastN"]),
        "--min-vtk-frames",
        str(time_averaging_plan["MinimumVtkFrames"]),
        "--min-vtk-step-span",
        str(time_averaging_plan["MinimumStepSpan"]),
    ]
    add_optional(native_runner_cmd, "--expected-vtk-frame-count", time_averaging_plan["ExpectedVtkFrameCount"])
    add_optional(native_runner_cmd, "--expected-aij-case", args.expected_aij_case)
    add_optional(native_runner_cmd, "--expected-wind-direction", args.expected_wind_direction)
    add_optional(native_runner_cmd, "--expected-wind-vector", args.expected_wind_vector)
    add_optional(native_runner_cmd, "--official", official_input_plan["Official"])
    add_optional(native_runner_cmd, "--af-csv", official_input_plan["AfCsv"])
    add_optional(native_runner_cmd, "--official-condition-filter", args.official_condition_filter)
    add_optional(native_runner_cmd, "--official-wind-filter", args.official_wind_filter)
    add_optional(native_runner_cmd, "--expected-probe-row-count", args.expected_probe_row_count if args.expected_probe_row_count else None)
    add_optional(native_runner_cmd, "--expected-probe-z", args.expected_probe_z)
    add_optional(native_runner_cmd, "--expected-probe-z-min", args.expected_probe_z_min)
    add_optional(native_runner_cmd, "--expected-probe-z-max", args.expected_probe_z_max)
    add_optional(native_runner_cmd, "--z-ref", args.z_ref)
    add_optional(native_runner_cmd, "--expected-uref", args.expected_uref)
    add_optional(native_runner_cmd, "--solver-cwd", str(solver_cwd) if solver_cwd else "")
    add_optional(native_runner_cmd, "--vtk-save-start-step", time_averaging_plan["VtkSaveStartStep"])
    if args.require_af_k:
        native_runner_cmd.append("--require-af-k")
    steps.append(run_step("run_native_fluidx3d_case_preflight", native_runner_cmd))

    diagnostic_canary_frame_count = planned_frame_count(
        args.diagnostic_canary_time_steps,
        args.diagnostic_canary_vtk_save_interval,
        args.diagnostic_canary_spinup_steps,
    )
    effective_diagnostic_average_last_n = min(args.diagnostic_canary_average_last_n, diagnostic_canary_frame_count)
    effective_diagnostic_min_vtk_frames = min(args.diagnostic_canary_min_vtk_frames, diagnostic_canary_frame_count)

    diagnostic_canary_case_cmd = [
        py,
        str(script_dir / "prepare_native_diagnostic_canary_case.py"),
        "--source-case-dir",
        str(case_dir),
        "--out-case-dir",
        str(diagnostic_canary_case_dir),
        "--manifest-out",
        str(diagnostic_canary_case_manifest),
        "--time-steps",
        str(args.diagnostic_canary_time_steps),
        "--spinup-steps",
        str(args.diagnostic_canary_spinup_steps),
        "--vtk-save-interval",
        str(args.diagnostic_canary_vtk_save_interval),
        "--average-last-n",
        str(effective_diagnostic_average_last_n),
        "--allow-existing",
    ]
    add_optional(
        diagnostic_canary_case_cmd,
        "--synthetic-turbulence-update-interval",
        args.diagnostic_canary_stg_update_interval,
    )
    add_optional(
        diagnostic_canary_case_cmd,
        "--synthetic-turbulence-intensity-scale",
        args.diagnostic_canary_stg_intensity_scale,
    )
    add_optional(
        diagnostic_canary_case_cmd,
        "--synthetic-turbulence-temporal-step-scale",
        args.diagnostic_canary_stg_temporal_step_scale,
    )
    steps.append(run_step("prepare_native_diagnostic_canary_case", diagnostic_canary_case_cmd))

    diagnostic_solver_source_cmd = [
        py,
        str(script_dir / "prepare_native_diagnostic_solver_source.py"),
        "--source-root",
        str(source_root),
        "--out-source-root",
        str(diagnostic_solver_source_root),
        "--manifest-out",
        str(diagnostic_solver_source_manifest),
        "--platform-toolset",
        str(args.diagnostic_canary_platform_toolset),
        "--allow-existing",
    ]
    steps.append(run_step("prepare_native_diagnostic_solver_source", diagnostic_solver_source_cmd))

    diagnostic_source_patch_cmd = [
        py,
        str(script_dir / "patch_fluidx3d_equilibrium_boundary_source.py"),
        "--fluidx3d-source",
        str(diagnostic_solver_source_root),
        "--out",
        str(diagnostic_fluidx3d_source_patch),
    ]
    steps.append(run_step("patch_diagnostic_fluidx3d_equilibrium_boundary_source", diagnostic_source_patch_cmd))

    diagnostic_ddf_route_cmd = [
        py,
        str(script_dir / "enable_fluidx3d_ddf_reconstruction_route.py"),
        "--case-dir",
        str(diagnostic_canary_case_dir),
        "--fluidx3d-source",
        str(diagnostic_solver_source_root),
        "--out",
        str(diagnostic_ddf_reconstruction_route),
    ]
    steps.append(run_step("enable_diagnostic_ddf_reconstruction_route", diagnostic_ddf_route_cmd))

    diagnostic_fluidx3d_boundary_cmd = [
        py,
        str(script_dir / "audit_fluidx3d_equilibrium_boundary.py"),
        "--fluidx3d-source",
        str(diagnostic_solver_source_root),
        "--out",
        str(diagnostic_fluidx3d_equilibrium_boundary),
    ]
    steps.append(run_step("audit_diagnostic_fluidx3d_equilibrium_boundary", diagnostic_fluidx3d_boundary_cmd))

    diagnostic_canary_cmd = set_option(native_runner_cmd, "--out", native_diagnostic_canary_manifest)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--fluidx3d-source", diagnostic_solver_source_root)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--case-dir", diagnostic_canary_case_dir)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--metadata", diagnostic_canary_case_dir / "case_metadata.json")
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--time-steps", args.diagnostic_canary_time_steps)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--vtk-save-interval", args.diagnostic_canary_vtk_save_interval)
    diagnostic_canary_cmd = set_option(
        diagnostic_canary_cmd,
        "--expected-vtk-frame-count",
        diagnostic_canary_frame_count,
    )
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--vtk-save-start-step", args.diagnostic_canary_spinup_steps)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--average-last-n", effective_diagnostic_average_last_n)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--min-vtk-frames", effective_diagnostic_min_vtk_frames)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--min-vtk-step-span", args.diagnostic_canary_min_step_span)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--solver-cwd", diagnostic_solver_cwd)
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--output-dir", diagnostic_solver_cwd / "output")
    diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--inlet-diagnostics-csv", runtime_inlet_diagnostics_csv)
    if args.diagnostic_canary_platform_toolset.strip():
        diagnostic_canary_cmd = set_option(diagnostic_canary_cmd, "--platform-toolset", args.diagnostic_canary_platform_toolset)
    for flag in ["--install", "--build", "--run", "--disable-graphics-for-run", "--allow-diagnostic-execution"]:
        diagnostic_canary_cmd = append_flag_once(diagnostic_canary_cmd, flag)

    runtime_inlet_diagnostics_audit_cmd = [
        py,
        str(script_dir / "audit_inlet_diagnostics_csv.py"),
        str(runtime_inlet_diagnostics_csv),
        "--out-json",
        str(runtime_inlet_diagnostics_audit),
        "--out-csv",
        str(runtime_inlet_diagnostics_summary),
        "--min-steps",
        "3",
        "--average-last-n-steps",
        "3",
        "--require-k",
        "--require-rms",
    ]
    inlet_correlation_audit_cmd = [
        py,
        str(script_dir / "audit_inlet_correlation_from_vtk.py"),
        str(diagnostic_solver_cwd / "output"),
        "--out-json",
        str(inlet_correlation_audit),
        "--metadata",
        str(diagnostic_canary_case_dir / "case_metadata.json"),
        "--average-last-n",
        str(effective_diagnostic_average_last_n),
        "--min-frames",
        str(effective_diagnostic_min_vtk_frames),
        "--min-step-span",
        str(args.diagnostic_canary_min_step_span),
        "--wind-direction",
        args.expected_wind_vector or "1,0,0",
        "--require-k-variance-check",
    ]
    add_optional(inlet_correlation_audit_cmd, "--af-csv", official_input_plan["AfCsv"])

    native_preconditions_cmd = [
        py,
        str(script_dir / "audit_native_preconditions.py"),
        str(case_dir),
        "--metadata",
        str(metadata_for_inlet_audit),
        "--manifest",
        str(manifest_out),
        "--inlet-source-audit",
        str(inlet_source),
        "--boundary-source-audit",
        str(boundary_source),
        "--boundary-protocol-audit",
        str(boundary_protocol),
        "--average-last-n",
        str(args.average_last_n),
        "--min-avg-frames",
        str(args.min_vtk_frames),
        "--min-avg-step-span",
        str(args.min_vtk_step_span),
        "--out",
        str(native_preconditions),
    ]
    add_optional(native_preconditions_cmd, "--case", args.expected_aij_case)
    add_optional(native_preconditions_cmd, "--wind-direction-label", args.expected_wind_direction)
    add_optional(native_preconditions_cmd, "--wind-vector", args.expected_wind_vector)
    add_optional(native_preconditions_cmd, "--official", official_input_plan["Official"])
    add_optional(native_preconditions_cmd, "--af-csv", official_input_plan["AfCsv"])
    add_optional(native_preconditions_cmd, "--u-ref", args.expected_uref)
    add_optional(native_preconditions_cmd, "--z-ref", args.z_ref)
    steps.append(run_step("audit_native_preconditions", native_preconditions_cmd))

    artifacts = {
        "InletSourceAudit": str(inlet_source),
        "InletReynoldsStressEvidence": str(inlet_reynolds_stress),
        "BoundarySourceAudit": str(boundary_source),
        "FluidX3DEquilibriumBoundaryAudit": str(fluidx3d_equilibrium_boundary),
        "DiagnosticFluidX3DSourcePatch": str(diagnostic_fluidx3d_source_patch),
        "DiagnosticDdfReconstructionRoute": str(diagnostic_ddf_reconstruction_route),
        "DiagnosticFluidX3DEquilibriumBoundaryAudit": str(diagnostic_fluidx3d_equilibrium_boundary),
        "BoundaryProtocolEvidenceTemplate": str(boundary_protocol_template),
        "BoundaryProtocolAudit": str(boundary_protocol),
        "CoordinateProbeBoundMetadata": str(coordinate_probe_bound_metadata),
        "InletBoundMetadata": str(inlet_bound_metadata),
        "CoordinateProbeProtocolAudit": str(coordinate_probe_protocol),
        "InletReynoldsStressTensorTemplate": str(inlet_reynolds_stress_template),
        "EquivalentPrecursorEvidenceTemplate": str(inlet_precursor_template),
        "TurbulenceLengthScaleEvidence": str(turbulence_length_scale_evidence),
        "TimeAveragingEvidence": str(time_averaging_evidence),
        "ValidationProtocolAudit": str(validation_protocol),
        "LegacyRuntimeInletDiagnosticsPatch": str(runtime_inlet_diagnostics_patch),
        "NativeFluidX3DManifest": str(manifest_out),
        "DiagnosticCanaryCase": str(diagnostic_canary_case_dir),
        "DiagnosticCanaryCaseManifest": str(diagnostic_canary_case_manifest),
        "DiagnosticSolverSourceRoot": str(diagnostic_solver_source_root),
        "DiagnosticSolverSourceManifest": str(diagnostic_solver_source_manifest),
        "DiagnosticCanarySolverCwd": str(diagnostic_solver_cwd),
        "NativeDiagnosticCanaryManifest": str(native_diagnostic_canary_manifest),
        "RuntimeInletDiagnosticsCsv": str(runtime_inlet_diagnostics_csv),
        "RuntimeInletDiagnosticsAudit": str(runtime_inlet_diagnostics_audit),
        "RuntimeInletDiagnosticsSummary": str(runtime_inlet_diagnostics_summary),
        "InletCorrelationAudit": str(inlet_correlation_audit),
        "NativePreconditionsAudit": str(native_preconditions),
        "PreflightPackManifest": str(preflight_manifest),
    }
    loaded = {
        key: read_json(Path(path))
        for key, path in artifacts.items()
        if key not in {
            "PreflightPackManifest",
            "RuntimeInletDiagnosticsCsv",
            "RuntimeInletDiagnosticsSummary",
            "DiagnosticCanaryCase",
            "DiagnosticSolverSourceRoot",
            "DiagnosticCanarySolverCwd",
        }
    }
    diagnostic_canary = build_diagnostic_canary_gate(loaded)
    reasons: List[str] = []
    reasons.extend(collect_gate_reasons("inlet_source", loaded.get("InletSourceAudit", {}), gate_keys=["paper_grade_inlet_source_gate"]))
    reasons.extend(collect_gate_reasons("inlet_reynolds_stress", loaded.get("InletReynoldsStressEvidence", {}), gate_keys=["paper_grade_gate", "gate"]))
    reasons.extend(collect_gate_reasons("turbulence_length_scale", loaded.get("TurbulenceLengthScaleEvidence", {}), gate_keys=["paper_grade_gate", "gate"]))
    reasons.extend(collect_gate_reasons("boundary_source", loaded.get("BoundarySourceAudit", {}), gate_keys=["paper_grade_boundary_source_gate"]))
    reasons.extend(collect_gate_reasons("fluidx3d_equilibrium_boundary", loaded.get("FluidX3DEquilibriumBoundaryAudit", {}), gate_keys=["Gate"]))
    reasons.extend(
        collect_gate_reasons(
            "boundary_protocol",
            loaded.get("BoundaryProtocolAudit", {}),
            gate_keys=["boundary_protocol_gate", "Gate", "ProtocolEvidenceGate"],
        )
    )
    reasons.extend(
        collect_gate_reasons(
            "coordinate_probe_protocol",
            loaded.get("CoordinateProbeProtocolAudit", {}),
            gate_keys=["coordinate_probe_protocol_gate", "Gate"],
        )
    )
    reasons.extend(collect_gate_reasons("time_averaging", loaded.get("TimeAveragingEvidence", {}), gate_keys=["Gate"]))
    reasons.extend(collect_gate_reasons("validation_protocol", loaded.get("ValidationProtocolAudit", {}), gate_keys=["PreRunGate", "Gate"]))
    reasons.extend(collect_gate_reasons("native_runner", loaded.get("NativeFluidX3DManifest", {}), gate_keys=["RunnerGate"]))
    reasons.extend(collect_gate_reasons("native_preconditions", loaded.get("NativePreconditionsAudit", {}), gate_keys=["Gate"]))
    reasons.extend(f"step_failed:{step['Name']}:{step['ReturnCode']}" for step in steps if int(step["ReturnCode"]) != 0)
    reasons = list(dict.fromkeys(reasons))

    gate = "pass" if not reasons else "diagnostic_only"
    development_triage = build_development_triage(
        loaded,
        diagnostic_canary,
        reasons,
        diagnostic_canary_case_command=diagnostic_canary_case_cmd,
        diagnostic_canary_command=diagnostic_canary_cmd,
        inlet_diagnostics_audit_command=runtime_inlet_diagnostics_audit_cmd,
        inlet_correlation_audit_command=inlet_correlation_audit_cmd,
    )
    manifest = {
        "Schema": "citylbm.native_preflight_pack.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "fast_no_cfd_gate_before_long_native_fluidx3d_validation_run",
        "CaseDir": str(case_dir),
        "FluidX3DSource": str(source_root),
        "DiagnosticFluidX3DSource": str(diagnostic_solver_source_root),
        "FluidX3DSolverWorkingDirectory": str(solver_cwd) if solver_cwd else "",
        "OutDir": str(out_dir),
        "Gate": gate,
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Execution": {
            "Mode": "serial_no_cfd_preflight" if args.serial else "parallel_no_cfd_preflight",
            "InitialParallelStepCount": len(initial_step_specs),
            "InitialParallelJobs": initial_jobs,
        },
        "TimeAveragingPlan": time_averaging_plan,
        "OfficialInputPlan": official_input_plan,
        "DiagnosticCanaryGate": diagnostic_canary,
        "NextOptimizationTarget": development_triage.get("NextOptimizationTarget", {}),
        "DevelopmentTriage": development_triage,
        "Artifacts": artifacts,
        "Steps": steps,
        "MetadataIdentityPatched": metadata_identity_patched,
        "NextAction": (
            "Preflight passed; native FluidX3D candidate run may start under the same hashes and inputs."
            if gate == "pass"
            else (
                "Paper-grade preflight is not closed, but a short diagnostic canary may start if DiagnosticCanaryGate=pass."
                if diagnostic_canary["Gate"] == "pass"
                else "Do not run CFD yet; fix DiagnosticCanaryGate reasons first."
            )
        ),
    }
    write_json(preflight_manifest, manifest)
    print(f"native_preflight_pack_gate={gate}; manifest={preflight_manifest}")
    if reasons:
        print("reasons=" + ";".join(reasons))
    return 0 if gate == "pass" or args.allow_diagnostic else 2


if __name__ == "__main__":
    raise SystemExit(main())
