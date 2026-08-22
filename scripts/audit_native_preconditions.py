#!/usr/bin/env python3
"""Audit whether a native FluidX3D run package is a strict baseline.

This script does not run CFD and does not judge AIJ accuracy. It checks that a
native FluidX3D baseline manifest is explicit, hash-traceable, and consistent
with the current run package and final-window VTK audit before the result is
used to diagnose CityLBM accuracy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REQUIRED_NATIVE_ROLES = [
    "Native FluidX3D original setup",
    "Native FluidX3D original defines",
    "Native FluidX3D lbm.hpp",
    "Native FluidX3D lbm.cpp",
]

REQUIRED_RUN_ROLES = [
    "FluidX3D setup",
    "FluidX3D defines",
    "Case metadata",
    "Domain origin",
    "Validation protocol audit",
]

REQUIRED_BOUNDARY_SUPPORT_FIELDS = [
    "inlet_boundary_supported",
    "outlet_boundary_supported",
    "lateral_boundary_supported",
    "top_boundary_supported",
    "ground_wall_treatment_supported",
    "roughness_treatment_supported",
    "floor_roughness_source_supported",
    "blockage_source_supported",
    "fetch_clearance_source_supported",
    "outlet_reflection_check_supported",
    "side_top_boundary_check_supported",
]

REQUIRED_PROTOCOL_ITEM_KEYS = [
    "inlet_mean_profile",
    "inlet_turbulence_k",
    "inlet_turbulence_length_scale",
    "inlet_reynolds_stress_tensor",
    "inlet_temporal_sampling",
    "inlet_distribution_consistency",
    "native_fluidx3d_baseline",
    "boundary_conditions",
    "wall_roughness_model",
    "lbm_stability_scaling",
    "time_averaging",
    "wind_direction_sign",
    "coordinate_transform",
    "probe_projection",
    "normalization_basis",
    "systematic_bias_gate",
    "grid_resolution",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit native FluidX3D strict-baseline preconditions.")
    parser.add_argument("run_dir", help="Run/case directory containing native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--manifest", help="Optional explicit native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--metadata", help="case_metadata.json used for the run.")
    parser.add_argument("--runtime-audit", help="native_run_audit.json/read_vtk_audit.json for the final VTK window.")
    parser.add_argument("--inlet-source-audit", help="inlet_source_audit.json from generated setup.cpp.")
    parser.add_argument("--inlet-profile-audit", help="inlet_profile_audit.json from final-window VTK.")
    parser.add_argument("--inlet-correlation-audit", help="inlet_correlation_audit.json from final-window VTK.")
    parser.add_argument("--boundary-source-audit", help="boundary_source_audit.json from generated setup.cpp.")
    parser.add_argument("--boundary-protocol-audit", help="boundary_protocol_audit.json with AIJ-equivalent evidence.")
    parser.add_argument("--boundary-runtime-audit", help="boundary_runtime_audit.json from final-window VTK boundary faces.")
    parser.add_argument("--probe-audit", help="probe_audit.csv used for metrics.")
    parser.add_argument("--component-sensitivity-audit", help="component_sensitivity_audit.json for component/Uref checks.")
    parser.add_argument("--official", help="Official RS/probe CSV used to recompute per-probe coordinate closure.")
    parser.add_argument("--af-csv", help="Official AF CSV used by the run.")
    parser.add_argument("--case", default="", help="Expected case label.")
    parser.add_argument("--wind-direction-label", default="", help="Official wind-direction label, e.g. N.")
    parser.add_argument("--software", default="", help="Expected software label.")
    parser.add_argument("--wind-vector", default="", help="Expected wind vector, e.g. 0,-1,0.")
    parser.add_argument("--u-ref", type=float, default=None, help="Expected reference wind speed in m/s.")
    parser.add_argument("--z-ref", type=float, default=None, help="Reference height used to derive Uref from the AF profile.")
    parser.add_argument("--expected-compared-component", default="", help="Expected probe comparison component.")
    parser.add_argument("--u-ref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--expected-vtk-pattern", default="u-*.vtk")
    parser.add_argument("--average-last-n", type=int, default=40)
    parser.add_argument("--min-avg-frames", type=int, default=40)
    parser.add_argument("--min-avg-step-span", type=int, default=20000)
    parser.add_argument("--out", required=True, help="Output audit JSON.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_native_diagnostic_priority(reasons: List[str]) -> List[Dict[str, Any]]:
    reason_set = set(reasons)

    groups = [
        (
            0,
            "validation_protocol_content",
            [
                "validation_protocol",
                "protocol_item",
                "protocol_audit",
            ],
            "The validation protocol audit must be complete before native baseline preconditions can support paper-grade evidence.",
            "Regenerate validation_protocol_audit.json from the current case and verify every required protocol item has an explicit non-fail status.",
        ),
        (
            1,
            "turbulent_inlet_method_and_u_k_preservation",
            [
                "inlet",
                "custom_profile",
                "profile_k",
                "profile_u",
                "af_csv",
                "paper_grade_inlet_source",
                "distribution_consistent",
                "velocity_field_only",
                "uncorrelated",
                "random",
                "rms",
                "method_class",
                "correlation",
            ],
            "The native baseline must first prove the AIJ AF U(z)/k(z) inlet and correlated turbulence source; RMS/k velocity perturbations alone remain diagnostic.",
            "Fix the native setup/inlet audits before interpreting probe error or comparing against CityLBM.",
        ),
        (
            2,
            "boundary_roughness_blockage",
            [
                "boundary",
                "roughness",
                "blockage",
                "clearance",
                "fetch",
                "outlet_reflection",
                "side_top",
                "ground_wall",
            ],
            "Boundary-condition evidence must show AIJ-equivalent inlet, outlet, lateral/top, floor and roughness treatment.",
            "Archive structured boundary evidence and non-empty hashed support files before promoting the baseline.",
        ),
        (
            3,
            "time_averaging_stationarity",
            [
                "runtime",
                "time",
                "step_span",
                "step_spacing",
                "average",
                "vtk_hash",
                "fresh",
                "source_step",
            ],
            "The final VTK window must be fresh, hash-traceable and long enough for a stable mean-flow comparison.",
            "Rerun or re-audit with the required final-window frame count and solver-step span.",
        ),
        (
            4,
            "coordinate_component_normalization",
            [
                "probe",
                "component",
                "normalization",
                "wind_vector",
                "uref",
                "official",
                "coordinate",
                "compared",
            ],
            "Probe IDs, coordinates, wind sign, compared component and Uref must match the official RS table.",
            "Fix the probe audit and component/Uref sensitivity audit before interpreting residual bias.",
        ),
        (
            5,
            "systematic_bias_after_prerequisites",
            [
                "systematic",
                "bias",
                "r2",
                "slope",
                "intercept",
                "underprediction",
                "overprediction",
            ],
            "Systematic bias is interpretable only after the previous protocol gates are closed.",
            "Treat remaining bias as a physics/protocol issue and compare paired native FluidX3D and CityLBM runs.",
        ),
    ]
    priorities: List[Dict[str, Any]] = []
    matched: set[str] = set()
    for rank, key, tokens, diagnosis, action in groups:
        matching_reasons = sorted(reason for reason in reason_set if any(token in reason for token in tokens))
        matched.update(matching_reasons)
        if matching_reasons:
            priorities.append(
                {
                    "rank": rank,
                    "key": key,
                    "reason_count": len(matching_reasons),
                    "reasons": matching_reasons,
                    "diagnosis": diagnosis,
                    "next_action": action,
                }
            )
    unmatched = sorted(reason_set - matched)
    if unmatched:
        priorities.append(
            {
                "rank": 6,
                "key": "other_precondition_evidence",
                "reason_count": len(unmatched),
                "reasons": unmatched,
                "diagnosis": "Additional traceability or packaging preconditions remain open.",
                "next_action": "Close these residual audit reasons after the five primary CFD-validation risks are handled.",
            }
        )
    return priorities


def build_native_precondition_closure(reasons: List[str]) -> Dict[str, Any]:
    reason_set = set(reasons)
    stage_specs = [
        (
            0,
            "validation_protocol_content",
            [
                "validation_protocol",
                "protocol_item",
                "protocol_audit",
            ],
            "Complete validation protocol audit.",
        ),
        (
            1,
            "turbulent_inlet_method_and_u_k_preservation",
            [
                "inlet",
                "custom_profile",
                "profile_k",
                "profile_u",
                "af_csv",
                "paper_grade_inlet_source",
                "distribution_consistent",
                "velocity_field_only",
                "uncorrelated",
                "random",
                "rms",
                "method_class",
                "correlation",
            ],
            "Prove AF U(z)/k(z), correlated turbulent inlet and distribution-consistent inlet treatment.",
        ),
        (
            2,
            "boundary_roughness_blockage",
            [
                "boundary",
                "roughness",
                "blockage",
                "clearance",
                "fetch",
                "outlet_reflection",
                "side_top",
                "ground_wall",
            ],
            "Prove AIJ-equivalent boundary, floor roughness, fetch, clearance and blockage treatment.",
        ),
        (
            3,
            "time_averaging_stationarity",
            [
                "runtime",
                "time",
                "step_span",
                "step_spacing",
                "average",
                "vtk_hash",
                "fresh",
                "source_step",
            ],
            "Prove fresh final-window VTK hashes, frame count, uniform spacing and solver-step span.",
        ),
        (
            4,
            "coordinate_component_normalization",
            [
                "probe",
                "component",
                "normalization",
                "wind_vector",
                "uref",
                "official",
                "coordinate",
                "compared",
            ],
            "Prove RS probe IDs/coordinates, wind sign, compared component and Uref normalization.",
        ),
        (
            5,
            "grid_resolution_and_systematic_bias",
            [
                "grid",
                "resolution",
                "dx",
                "systematic",
                "bias",
                "r2",
                "slope",
                "intercept",
                "underprediction",
                "overprediction",
            ],
            "Only interpret grid sensitivity and systematic bias after protocol stages 0-4 are closed.",
        ),
    ]
    stages: List[Dict[str, Any]] = []
    for rank, key, tokens, required_evidence in stage_specs:
        stage_reasons = sorted(
            reason for reason in reason_set if any(token in reason for token in tokens)
        )
        stages.append(
            {
                "rank": rank,
                "key": key,
                "status": "pass" if not stage_reasons else "fail",
                "reason_count": len(stage_reasons),
                "reasons": stage_reasons,
                "required_evidence": required_evidence,
            }
        )
    failed_stages = [stage for stage in stages if stage["status"] != "pass"]
    top_stage = failed_stages[0] if failed_stages else {}
    return {
        "gate": "pass" if not failed_stages else "fail",
        "stage_count": len(stages),
        "closed_stage_count": len(stages) - len(failed_stages),
        "failed_stage_count": len(failed_stages),
        "failed_stage_keys": [stage["key"] for stage in failed_stages],
        "failed_stage_keys_csv": ";".join(stage["key"] for stage in failed_stages),
        "top_blocking_stage_key": top_stage.get("key", ""),
        "top_blocking_stage_rank": top_stage.get("rank"),
        "top_blocking_stage_reason_count": top_stage.get("reason_count"),
        "top_blocking_stage_reasons": top_stage.get("reasons", []),
        "top_blocking_stage_reasons_csv": ";".join(
            str(reason) for reason in top_stage.get("reasons", [])
        ),
        "stages": stages,
    }


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def load_protocol_items(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["Items", "items", "ProtocolItems", "protocol_items"]:
        value = audit.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def audit_protocol_content(
    audit: Dict[str, Any],
    required_keys: Iterable[str] = REQUIRED_PROTOCOL_ITEM_KEYS,
) -> Dict[str, Any]:
    items = load_protocol_items(audit)
    statuses = {
        str(item.get("Key") or item.get("key") or "").strip(): str(
            item.get("Status") or item.get("status") or ""
        ).strip().lower()
        for item in items
        if str(item.get("Key") or item.get("key") or "").strip()
    }
    required = list(required_keys)
    missing = [key for key in required if key not in statuses]
    missing_status = [key for key in required if key in statuses and not statuses[key]]
    failed = [key for key, status in statuses.items() if status == "fail"]
    reasons: List[str] = []
    if not audit or not items:
        reasons.append("validation_protocol_audit_missing_or_empty")
    reasons.extend(f"validation_protocol_item_missing:{key}" for key in missing)
    reasons.extend(f"validation_protocol_item_status_missing:{key}" for key in missing_status)
    reasons.extend(f"validation_protocol_item_fail:{key}" for key in failed)
    return {
        "gate": "pass" if not reasons else "fail",
        "item_count": len(items),
        "required_item_count": len(required),
        "audit_gate": str(audit.get("Gate") or audit.get("gate") or ""),
        "missing_keys": missing,
        "missing_status_keys": missing_status,
        "failed_keys": failed,
        "risk_keys": [key for key, status in statuses.items() if status == "risk"],
        "partial_keys": [key for key, status in statuses.items() if status == "partial"],
        "statuses": statuses,
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
    }


def read_csv_rows(path: Optional[Path]) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Optional[Path]) -> str:
    if not path or not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def component_sensitivity_input_hash_traceability(
    component_sensitivity_audit: Dict[str, Any],
    probe_audit_sha256: str,
    official_sha256: str,
) -> Dict[str, Any]:
    """Check that component sensitivity was generated from current probe/official inputs."""
    reasons: List[str] = []
    component_probe_sha = str(component_sensitivity_audit.get("probe_audit_sha256") or "").strip().lower()
    component_official_sha = str(component_sensitivity_audit.get("official_sha256") or "").strip().lower()
    probe_matches: Optional[bool] = None
    official_matches: Optional[bool] = None

    if component_sensitivity_audit and probe_audit_sha256:
        probe_matches = component_probe_sha == probe_audit_sha256
        if not component_probe_sha:
            reasons.append("component_sensitivity_probe_audit_hash_missing")
        elif not probe_matches:
            reasons.append("component_sensitivity_probe_audit_hash_mismatch")

    if component_sensitivity_audit and official_sha256:
        official_matches = component_official_sha == official_sha256
        if not component_official_sha:
            reasons.append("component_sensitivity_official_hash_missing")
        elif not official_matches:
            reasons.append("component_sensitivity_official_hash_mismatch")

    return {
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
        "reasons_csv": ";".join(reasons),
        "probe_audit_sha256": probe_audit_sha256,
        "official_sha256": official_sha256,
        "component_probe_audit_sha256": component_probe_sha,
        "component_official_sha256": component_official_sha,
        "probe_audit_sha256_matches_current": probe_matches,
        "official_sha256_matches_current": official_matches,
    }


def find_first(base: Path, names: Iterable[str]) -> Optional[Path]:
    for name in names:
        for root in [base, base / "output", base / "src", base / "validation_chain"]:
            candidate = root / name
            if candidate.exists():
                return candidate.resolve()
    parent = base.parent
    if parent != base:
        for name in names:
            candidate = parent / name
            if candidate.exists():
                return candidate.resolve()
    return None


def as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "pass"}:
            return True
        if text in {"false", "0", "no", "fail"}:
            return False
    return None


def as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_vector(text: str) -> Optional[Tuple[float, float, float]]:
    cleaned = str(text or "").strip().strip("()[]")
    if not cleaned:
        return None
    parts = [part.strip() for part in cleaned.replace(";", ",").split(",") if part.strip()]
    if len(parts) != 3:
        parts = [part.strip() for part in cleaned.split() if part.strip()]
    if len(parts) != 3:
        return None
    values = [as_float(part) for part in parts]
    if any(value is None for value in values):
        return None
    return (values[0], values[1], values[2])  # type: ignore[index]


def unit_vector(vector: Optional[Tuple[float, float, float]]) -> Optional[Tuple[float, float, float]]:
    if vector is None:
        return None
    norm = math.sqrt(sum(component * component for component in vector))
    if norm <= 1.0e-12:
        return None
    return tuple(component / norm for component in vector)


def vector_delta(a: Optional[Tuple[float, float, float]], b: Optional[Tuple[float, float, float]]) -> Optional[float]:
    au = unit_vector(a)
    bu = unit_vector(b)
    if au is None or bu is None:
        return None
    return math.sqrt(sum((left - right) * (left - right) for left, right in zip(au, bu)))


def manifest_record(manifest: Dict[str, Any], role: str) -> Dict[str, Any]:
    records = manifest.get("RequiredSourceFiles", [])
    if not isinstance(records, list):
        return {}
    for record in records:
        if isinstance(record, dict) and str(record.get("Role") or "").strip() == role:
            return record
    return {}


def resolve_record_path(record: Dict[str, Any], manifest_path: Optional[Path]) -> Optional[Path]:
    raw_path = str(record.get("Path") or "").strip()
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and manifest_path is not None:
        path = manifest_path.parent / path
    return path.resolve()


def audit_role(manifest: Dict[str, Any], manifest_path: Optional[Path], role: str) -> Dict[str, Any]:
    record = manifest_record(manifest, role)
    declared_sha = str(record.get("Sha256") or "").strip().lower()
    declared_exists = as_bool(record.get("Exists"))
    declared_algorithm = str(record.get("HashAlgorithm") or "").strip().upper()
    path = resolve_record_path(record, manifest_path)
    actual_sha = sha256_file(path)
    reasons: List[str] = []
    if not record:
        reasons.append("record_missing")
    if declared_exists is not True:
        reasons.append("exists_not_true")
    if declared_algorithm != "SHA256":
        reasons.append("hash_algorithm_not_sha256")
    if not declared_sha:
        reasons.append("sha256_missing")
    if path is None or not path.exists():
        reasons.append("path_missing")
    if declared_sha and actual_sha and declared_sha != actual_sha:
        reasons.append("sha256_mismatch")
    return {
        "role": role,
        "path": str(path) if path else "",
        "declared_exists": declared_exists,
        "declared_sha256": declared_sha,
        "actual_sha256": actual_sha,
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
    }


def shared_wind_vector(shared: Dict[str, Any]) -> Optional[Tuple[float, float, float]]:
    raw = shared.get("WindDirectionUnitVector")
    if isinstance(raw, dict):
        values = [as_float(raw.get(key)) for key in ["X", "Y", "Z"]]
        if all(value is not None for value in values):
            return (values[0], values[1], values[2])  # type: ignore[index]
    if isinstance(raw, str):
        return parse_vector(raw)
    return None


def expected_final_window_span(time_steps: Optional[int], save_interval: Optional[int], save_start_step: Optional[int], average_last_n: int) -> Optional[int]:
    if time_steps is None or save_interval is None or save_interval <= 0:
        return None
    first = save_start_step if save_start_step is not None else save_interval
    steps = list(range(first, time_steps + 1, save_interval))
    if not steps:
        return None
    final = steps[-max(1, average_last_n) :]
    if len(final) < 2:
        return 0
    return final[-1] - final[0]


def source_step_span_from_steps(steps: List[int]) -> Optional[int]:
    if len(steps) < 2:
        return None
    ordered = sorted(steps)
    return ordered[-1] - ordered[0]


def source_steps_strictly_increasing(steps: List[int]) -> bool:
    return len(steps) >= 2 and all(right > left for left, right in zip(steps, steps[1:]))


def source_steps_uniformly_spaced(steps: List[int]) -> bool:
    if len(steps) < 2:
        return False
    spacings = [right - left for left, right in zip(steps, steps[1:])]
    return all(spacing > 0 for spacing in spacings) and len(set(spacings)) == 1


def count_below_minimum_reason(label: str, value: Optional[int], minimum: int) -> str:
    if value is None:
        return f"{label}_missing"
    if value < minimum:
        return f"{label}_{value}_below_minimum_{minimum}"
    return ""


def reason_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    token = "".join(char if char.isascii() and (char.isalnum() or char in "._+-") else "_" for char in text)
    token = "_".join(part for part in token.split("_") if part)
    return token or "missing"


def count_reason(label: str, count: int) -> str:
    return f"{label}_{count}"


def split_scalar_list(value: Any, separators: Tuple[str, ...] = (",", ";")) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    for separator in separators[1:]:
        text = text.replace(separator, separators[0])
    return [part.strip() for part in text.split(separators[0]) if part.strip()]


def parse_int_list(value: Any) -> List[int]:
    output: List[int] = []
    for item in split_scalar_list(value):
        parsed = as_int(item)
        if parsed is not None:
            output.append(parsed)
    return output


def parse_hash_list(value: Any) -> List[str]:
    return [item.lower() for item in split_scalar_list(value) if item]


def audit_source_steps(audit: Dict[str, Any]) -> List[int]:
    return parse_int_list(audit.get("source_time_steps") or audit.get("source_time_steps_csv"))


def audit_source_hashes(audit: Dict[str, Any]) -> List[str]:
    hashes = parse_hash_list(audit.get("source_vtk_sha256") or audit.get("source_vtk_sha256_csv"))
    if hashes:
        return hashes
    records = audit.get("selected_vtk_files")
    if isinstance(records, list):
        return [
            str(record.get("sha256") or "").strip().lower()
            for record in records
            if isinstance(record, dict) and str(record.get("sha256") or "").strip()
        ]
    return []


def runtime_source_hashes(runtime_audit: Dict[str, Any], runtime_steps: List[int]) -> List[str]:
    records = runtime_audit.get("freshness_selected_vtk_files")
    if isinstance(records, list) and records:
        return [
            str(record.get("sha256") or "").strip().lower()
            for record in records
            if isinstance(record, dict) and str(record.get("sha256") or "").strip()
        ]
    records = runtime_audit.get("vtk_files")
    if not isinstance(records, list):
        return []
    selected_steps = set(runtime_steps)
    output: List[Tuple[int, str]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        step = as_int(record.get("time_step"))
        digest = str(record.get("sha256") or "").strip().lower()
        if step is not None and step in selected_steps and digest:
            output.append((step, digest))
    return [digest for _, digest in sorted(output)]


def append_source_window_reasons(
    reasons: List[str],
    label: str,
    audit: Dict[str, Any],
    runtime_steps: List[int],
    runtime_hashes: List[str],
) -> Dict[str, Any]:
    audit_steps = audit_source_steps(audit)
    audit_hashes = audit_source_hashes(audit)
    steps_match = bool(runtime_steps) and audit_steps == runtime_steps
    hashes_match = bool(runtime_hashes) and bool(audit_hashes) and set(audit_hashes) == set(runtime_hashes)
    if audit:
        if not runtime_steps:
            reasons.append(f"{label}_runtime_source_time_steps_missing")
        elif not audit_steps:
            reasons.append(f"{label}_source_time_steps_missing")
        elif not steps_match:
            reasons.append(f"{label}_source_time_steps_mismatch")
        if not runtime_hashes:
            reasons.append(f"{label}_runtime_source_vtk_hashes_missing")
        elif not audit_hashes:
            reasons.append(f"{label}_source_vtk_hashes_missing")
        elif not hashes_match:
            reasons.append(f"{label}_source_vtk_hashes_mismatch")
    return {
        f"{label}_source_time_steps": audit_steps,
        f"{label}_source_time_steps_match_runtime": steps_match,
        f"{label}_source_vtk_sha256": audit_hashes,
        f"{label}_source_vtk_sha256_match_runtime": hashes_match,
    }


def append_source_step_span_reasons(
    reasons: List[str],
    label: str,
    audit: Dict[str, Any],
    min_step_span: int,
) -> Dict[str, Any]:
    audit_steps = audit_source_steps(audit)
    reported = as_int(audit.get("source_step_span"))
    computed = source_step_span_from_steps(audit_steps)
    effective = computed if computed is not None else reported
    matches_steps = reported is not None and computed is not None and reported == computed
    increasing = source_steps_strictly_increasing(audit_steps)
    uniform = source_steps_uniformly_spaced(audit_steps)
    reported_increasing = as_bool(audit.get("source_steps_strictly_increasing"))
    reported_uniform = as_bool(audit.get("source_step_spacing_uniform"))
    if audit:
        if reported is None:
            reasons.append(f"{label}_source_step_span_missing")
        if computed is None:
            reasons.append(f"{label}_source_time_steps_span_missing")
        elif reported is not None and reported != computed:
            reasons.append(f"{label}_source_step_span_mismatch_time_steps")
        if not increasing:
            reasons.append(f"{label}_source_steps_not_strictly_increasing")
        if not uniform:
            reasons.append(f"{label}_source_step_spacing_not_uniform")
        if reported_increasing is not None and reported_increasing != increasing:
            reasons.append(f"{label}_source_steps_increasing_flag_mismatch")
        if reported_uniform is not None and reported_uniform != uniform:
            reasons.append(f"{label}_source_step_spacing_flag_mismatch")
    if effective is None or effective < min_step_span:
        reasons.append(f"{label}_step_span_too_short")
    return {
        f"{label}_reported_source_step_span": reported,
        f"{label}_source_step_span_from_time_steps": computed,
        f"{label}_source_step_span": effective,
        f"{label}_source_step_span_matches_time_steps": matches_steps,
        f"{label}_source_steps_strictly_increasing": increasing,
        f"{label}_source_step_spacing_uniform": uniform,
        f"{label}_reported_source_steps_strictly_increasing": reported_increasing,
        f"{label}_reported_source_step_spacing_uniform": reported_uniform,
    }


def append_setup_hash_reason(reasons: List[str], label: str, audit: Dict[str, Any], setup_sha: str) -> Dict[str, Any]:
    audit_sha = str(audit.get("setup_cpp_sha256") or "").strip().lower()
    match = bool(audit_sha) and bool(setup_sha) and audit_sha == setup_sha
    if audit:
        if not audit_sha:
            reasons.append(f"{label}_setup_cpp_sha256_missing")
        elif not setup_sha:
            reasons.append(f"{label}_current_setup_cpp_missing")
        elif not match:
            reasons.append(f"{label}_setup_cpp_sha256_mismatch")
    return {
        f"{label}_setup_cpp_sha256": audit_sha,
        f"{label}_setup_cpp_sha256_matches_current": match,
    }


def probe_unique_values(rows: List[Dict[str, str]], *fields: str) -> List[str]:
    return sorted({row_value(row, *fields) for row in rows if row_value(row, *fields)})


def probe_unique_int_values(rows: List[Dict[str, str]], *fields: str) -> List[int]:
    values = []
    for row in rows:
        value = as_int(row_value(row, *fields))
        if value is not None:
            values.append(value)
    return sorted(set(values))


def row_value(row: Dict[str, str], *fields: str) -> str:
    lowered = {key.lower(): value for key, value in row.items()}
    for field in fields:
        if field in row:
            return str(row.get(field) or "").strip()
        value = lowered.get(field.lower())
        if value is not None:
            return str(value or "").strip()
    return ""


def normalized_column_key(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def find_csv_column(rows: List[Dict[str, str]], candidates: Iterable[str]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    normalized = {normalized_column_key(column): column for column in columns}
    for candidate in candidates:
        found = normalized.get(normalized_column_key(candidate))
        if found:
            return found
    return ""


def find_column_by_fieldnames(fieldnames: Iterable[str], candidates: Iterable[str]) -> str:
    normalized = {normalized_column_key(column): column for column in fieldnames}
    for candidate in candidates:
        found = normalized.get(normalized_column_key(candidate))
        if found:
            return found
    return ""


def af_u_at_reference_height(path: Optional[Path], z_ref: Optional[float]) -> Optional[float]:
    if path is None or z_ref is None or not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return None
        z_column = find_column_by_fieldnames(reader.fieldnames, ["z", "z(m)", "height", "height_m"])
        u_column = find_column_by_fieldnames(reader.fieldnames, ["U", "U(m/s)", "u_mps", "velocity", "velocity_mps"])
        if not z_column or not u_column:
            return None
        samples: List[Tuple[float, float]] = []
        for row in reader:
            z = as_float(row.get(z_column))
            u = as_float(row.get(u_column))
            if z is not None and u is not None:
                samples.append((z, u))
    if len(samples) < 2:
        return None
    samples.sort(key=lambda item: item[0])
    if z_ref <= samples[0][0]:
        return samples[0][1]
    if z_ref >= samples[-1][0]:
        return samples[-1][1]
    for (z0, u0), (z1, u1) in zip(samples, samples[1:]):
        if z0 <= z_ref <= z1:
            if abs(z1 - z0) <= 1.0e-12:
                return u0
            return u0 + (u1 - u0) * ((z_ref - z0) / (z1 - z0))
    return None


def filter_official_rows(
    rows: List[Dict[str, str]],
    case: str,
    wind_direction: str,
) -> Tuple[List[Dict[str, str]], Optional[str]]:
    filtered = rows
    case_text = str(case or "").strip().lower()
    wind_text = str(wind_direction or "").strip().lower()
    if case_text:
        case_col = find_csv_column(filtered, ["case", "Case", "condition", "Condition", "bcac"])
        if not case_col:
            return [], "official_case_filter_column_missing"
        filtered = [
            row
            for row in filtered
            if str(row.get(case_col) or "").strip().lower() == case_text
        ]
        if not filtered:
            return [], "official_case_filter_no_rows"
    if wind_text:
        wind_col = find_csv_column(
            filtered,
            ["Wind_direction", "wind_direction", "direction", "Direction", "wind", "Wind"],
        )
        if not wind_col:
            return [], "official_wind_direction_filter_column_missing"
        filtered = [
            row
            for row in filtered
            if str(row.get(wind_col) or "").strip().lower() == wind_text
        ]
        if not filtered:
            return [], "official_wind_direction_filter_no_rows"
    return filtered, None


def build_official_coordinate_lookup(
    official_path: Optional[Path],
    case: str,
    wind_direction: str,
) -> Tuple[Dict[str, Tuple[float, float, float]], Optional[str]]:
    rows = read_csv_rows(official_path)
    if not official_path:
        return {}, "official_csv_not_provided"
    if not rows:
        return {}, "official_csv_missing_or_empty"
    rows, filter_error = filter_official_rows(rows, case, wind_direction)
    if filter_error:
        return {}, filter_error
    id_column = find_csv_column(rows, ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"])
    x_column = find_csv_column(rows, ["x", "X", "x_m", "X_m", "X(m)", "x(m)"])
    y_column = find_csv_column(rows, ["y", "Y", "y_m", "Y_m", "Y(m)", "y(m)"])
    z_column = find_csv_column(rows, ["z", "Z", "z_m", "Z_m", "Z(m)", "z(m)"])
    if not id_column:
        return {}, "official_id_column_missing"
    if not x_column or not y_column or not z_column:
        return {}, "official_coordinate_columns_missing"

    lookup: Dict[str, Tuple[float, float, float]] = {}
    duplicate_ids = set()
    invalid_count = 0
    for row in rows:
        probe_id = normalized_column_key(str(row.get(id_column) or "").strip())
        if not probe_id:
            continue
        x = as_float(row.get(x_column))
        y = as_float(row.get(y_column))
        z = as_float(row.get(z_column))
        if x is None or y is None or z is None:
            invalid_count += 1
            continue
        if probe_id in lookup:
            duplicate_ids.add(probe_id)
        lookup[probe_id] = (x, y, z)
    if duplicate_ids:
        return {}, "official_duplicate_ids_after_normalization"
    if invalid_count:
        return {}, f"official_invalid_coordinate_count:{invalid_count}"
    if not lookup:
        return {}, "official_coordinate_lookup_empty"
    return lookup, None


def probe_official_coordinate_delta_summary(
    valid_probe_rows: List[Dict[str, str]],
    official_coordinates: Dict[str, Tuple[float, float, float]],
    probe_id_column: str,
) -> Dict[str, Any]:
    coordinate_deltas: List[float] = []
    recomputed_count = 0
    use_current_official = bool(official_coordinates and probe_id_column)
    for row in valid_probe_rows:
        coordinate_delta: Optional[float] = None
        if use_current_official:
            probe_id = normalized_column_key(str(row.get(probe_id_column) or "").strip())
            official_coordinate = official_coordinates.get(probe_id)
            if official_coordinate is not None:
                probe_x = as_float(row_value(row, "x", "X"))
                probe_y = as_float(row_value(row, "y", "Y"))
                probe_z = as_float(row_value(row, "z", "Z"))
                if probe_x is not None and probe_y is not None and probe_z is not None:
                    coordinate_delta = max(
                        abs(probe_x - official_coordinate[0]),
                        abs(probe_y - official_coordinate[1]),
                        abs(probe_z - official_coordinate[2]),
                    )
                    recomputed_count += 1
        else:
            coordinate_delta = as_float(row_value(row, "official_coordinate_delta", "OfficialCoordinateDelta"))
        if coordinate_delta is not None:
            coordinate_deltas.append(coordinate_delta)
    return {
        "deltas": coordinate_deltas,
        "recomputed_count": recomputed_count,
        "missing_count": len(valid_probe_rows) - len(coordinate_deltas),
        "source": "current_official_csv_recomputed" if use_current_official else "probe_audit_only",
        "requires_current_official_recompute": use_current_official,
    }


def probe_row_failed(row: Dict[str, str]) -> bool:
    failed = as_bool(row_value(row, "failed", "Failed"))
    out_of_tolerance = as_bool(row_value(row, "out_of_tolerance", "OutOfTolerance"))
    status = row_value(row, "validation_status", "ValidationStatus", "status", "Status").lower()
    return (
        failed is True
        or out_of_tolerance is True
        or any(token in status for token in ["fail", "invalid", "out_of_tolerance", "out-of-tolerance"])
    )


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else find_first(run_dir, ["case_metadata.json"])
    runtime_audit_path = Path(args.runtime_audit).expanduser().resolve() if args.runtime_audit else find_first(run_dir, ["native_run_audit.json", "read_vtk_audit.json"])
    inlet_source_audit_path = Path(args.inlet_source_audit).expanduser().resolve() if args.inlet_source_audit else find_first(run_dir, ["inlet_source_audit.json"])
    inlet_profile_audit_path = Path(args.inlet_profile_audit).expanduser().resolve() if args.inlet_profile_audit else find_first(run_dir, ["inlet_profile_audit.json"])
    inlet_correlation_audit_path = Path(args.inlet_correlation_audit).expanduser().resolve() if args.inlet_correlation_audit else find_first(run_dir, ["inlet_correlation_audit.json"])
    boundary_source_audit_path = Path(args.boundary_source_audit).expanduser().resolve() if args.boundary_source_audit else find_first(run_dir, ["boundary_source_audit.json"])
    boundary_protocol_audit_path = Path(args.boundary_protocol_audit).expanduser().resolve() if args.boundary_protocol_audit else find_first(run_dir, ["boundary_protocol_audit.json"])
    boundary_runtime_audit_path = Path(args.boundary_runtime_audit).expanduser().resolve() if args.boundary_runtime_audit else find_first(run_dir, ["boundary_runtime_audit.json"])
    probe_audit_path = Path(args.probe_audit).expanduser().resolve() if args.probe_audit else find_first(run_dir, ["probe_audit.csv"])
    component_sensitivity_audit_path = Path(args.component_sensitivity_audit).expanduser().resolve() if args.component_sensitivity_audit else find_first(run_dir, ["component_sensitivity_audit.json"])
    official_path = Path(args.official).expanduser().resolve() if args.official else None
    setup_path = find_first(run_dir, ["setup.cpp"])
    defines_path = find_first(run_dir, ["defines.hpp"])
    domain_origin_path = find_first(run_dir, ["domain_origin.json"])
    protocol_audit_path = find_first(run_dir, ["validation_protocol_audit.json"])

    manifest = read_json(manifest_path)
    metadata = read_json(metadata_path)
    runtime_audit = read_json(runtime_audit_path)
    inlet_source_audit = read_json(inlet_source_audit_path)
    inlet_profile_audit = read_json(inlet_profile_audit_path)
    inlet_correlation_audit = read_json(inlet_correlation_audit_path)
    boundary_source_audit = read_json(boundary_source_audit_path)
    boundary_protocol_audit = read_json(boundary_protocol_audit_path)
    boundary_runtime_audit = read_json(boundary_runtime_audit_path)
    validation_protocol_audit = read_json(protocol_audit_path)
    protocol_content_audit = audit_protocol_content(validation_protocol_audit)
    probe_rows = read_csv_rows(probe_audit_path)
    component_sensitivity_audit = read_json(component_sensitivity_audit_path)
    probe_audit_sha = sha256_file(probe_audit_path)
    official_sha = sha256_file(official_path)
    component_hash_traceability = component_sensitivity_input_hash_traceability(
        component_sensitivity_audit,
        probe_audit_sha,
        official_sha,
    )
    reasons: List[str] = []

    if not manifest:
        reasons.append("native_manifest_missing_or_empty")
    if not str(manifest.get("BaselineId") or "").strip():
        reasons.append("baseline_id_missing")
    if str(manifest.get("Gate") or "").strip() != "required_before_paper_grade_accuracy_claim":
        reasons.append("manifest_gate_unexpected")
    if as_bool(manifest.get("NativeFluidX3DPathExplicitlyProvided")) is not True:
        reasons.append("native_fluidx3d_path_not_explicit")
    source_validation = manifest.get("NativeFluidX3DSourceValidation", {})
    if not isinstance(source_validation, dict) or as_bool(source_validation.get("IsValid")) is not True:
        reasons.append("native_fluidx3d_source_validation_failed")

    role_audits = [audit_role(manifest, manifest_path, role) for role in REQUIRED_NATIVE_ROLES + REQUIRED_RUN_ROLES]
    failed_roles = [item["role"] for item in role_audits if item["gate"] != "pass"]
    if failed_roles:
        reasons.append("required_source_file_hash_gate_failed:" + ";".join(failed_roles))

    setup_sha = sha256_file(setup_path)
    defines_sha = sha256_file(defines_path)
    metadata_sha = sha256_file(metadata_path)
    domain_origin_sha = sha256_file(domain_origin_path)
    protocol_audit_sha = sha256_file(protocol_audit_path)
    runtime_audit_sha = sha256_file(runtime_audit_path)
    run_hash_checks = {
        "FluidX3D setup": setup_sha,
        "FluidX3D defines": defines_sha,
        "Case metadata": metadata_sha,
        "Domain origin": domain_origin_sha,
        "Validation protocol audit": protocol_audit_sha,
    }
    for role, actual_sha in run_hash_checks.items():
        declared_sha = str(manifest_record(manifest, role).get("Sha256") or "").strip().lower()
        if not actual_sha:
            reasons.append(f"current_run_file_missing:{role}")
        elif not declared_sha or declared_sha != actual_sha:
            reasons.append(f"current_run_file_hash_mismatch:{role}")
    if protocol_content_audit["gate"] != "pass":
        reasons.extend(str(reason) for reason in protocol_content_audit["reasons"])

    shared = manifest.get("SharedRunConditions", {})
    if not isinstance(shared, dict):
        shared = {}
        reasons.append("shared_run_conditions_missing")

    metadata_steps = as_int(metadata.get("TimeSteps"))
    metadata_save_interval = as_int(metadata.get("SaveInterval"))
    shared_steps = as_int(shared.get("TimeSteps"))
    shared_save_interval = as_int(shared.get("SaveInterval"))
    if metadata_steps is not None and shared_steps is not None and metadata_steps != shared_steps:
        reasons.append("metadata_manifest_time_steps_mismatch")
    if metadata_save_interval is not None and shared_save_interval is not None and metadata_save_interval != shared_save_interval:
        reasons.append("metadata_manifest_save_interval_mismatch")

    shared_frame_count = as_int(shared.get("ExpectedVtkFrameCount"))
    metadata_frame_count = as_int(metadata.get("ExpectedVtkFrameCount"))
    requested_frame_count = as_int(runtime_audit.get("requested_vtk_frame_count"))
    frame_candidates = [value for value in [shared_frame_count, metadata_frame_count, requested_frame_count] if value is not None]
    planned_frame_count_min = min(frame_candidates) if frame_candidates else None
    planned_frame_shortfall_reason = count_below_minimum_reason(
        "planned_vtk_frame_count",
        planned_frame_count_min,
        args.min_avg_frames,
    )
    if planned_frame_shortfall_reason:
        reasons.append("planned_vtk_frame_count_below_minimum")
        reasons.append(planned_frame_shortfall_reason)

    runtime_pattern = str(runtime_audit.get("vtk_pattern") or "").strip()
    if not runtime_audit:
        reasons.append("runtime_audit_missing")
    elif runtime_pattern != args.expected_vtk_pattern:
        reasons.append("runtime_vtk_pattern_mismatch")

    runtime_avg = as_int(runtime_audit.get("average_last_n_requested"))
    if runtime_avg is None:
        runtime_avg = as_int(runtime_audit.get("averaged_frame_count"))
    runtime_average_shortfall_reason = count_below_minimum_reason(
        "runtime_average_window_frame_count",
        runtime_avg,
        args.min_avg_frames,
    )
    if runtime_avg is None or runtime_avg < args.min_avg_frames or runtime_avg != args.average_last_n:
        reasons.append("runtime_average_window_mismatch_or_too_short")
        if runtime_average_shortfall_reason:
            reasons.append(runtime_average_shortfall_reason)
        if runtime_avg is not None and runtime_avg != args.average_last_n:
            reasons.append(f"runtime_average_window_{runtime_avg}_does_not_match_required_{args.average_last_n}")

    runtime_steps = audit_source_steps(runtime_audit)
    runtime_hashes = runtime_source_hashes(runtime_audit, runtime_steps)
    runtime_selected_last_window = as_bool(runtime_audit.get("selected_last_window"))
    runtime_hash_count = len(runtime_hashes)
    runtime_hash_unique_count = len(set(runtime_hashes))
    runtime_step_span_reported = as_int(runtime_audit.get("source_step_span"))
    runtime_step_span_from_steps = source_step_span_from_steps(runtime_steps)
    runtime_step_span = runtime_step_span_from_steps if runtime_step_span_from_steps is not None else runtime_step_span_reported
    runtime_steps_increasing = source_steps_strictly_increasing(runtime_steps)
    runtime_steps_uniform = source_steps_uniformly_spaced(runtime_steps)
    runtime_reported_steps_increasing = as_bool(runtime_audit.get("source_steps_strictly_increasing"))
    runtime_reported_steps_uniform = as_bool(runtime_audit.get("source_step_spacing_uniform"))
    planned_span = expected_final_window_span(
        shared_steps or metadata_steps,
        shared_save_interval or metadata_save_interval,
        as_int(runtime_audit.get("requested_vtk_save_start_step")),
        args.average_last_n,
    )
    if runtime_audit:
        if runtime_step_span_reported is None:
            reasons.append("runtime_source_step_span_missing")
        if runtime_step_span_from_steps is None:
            reasons.append("runtime_source_time_steps_span_missing")
        elif runtime_step_span_reported is not None and runtime_step_span_reported != runtime_step_span_from_steps:
            reasons.append("runtime_source_step_span_mismatch_time_steps")
        if not runtime_steps_increasing:
            reasons.append("runtime_source_steps_not_strictly_increasing")
        if not runtime_steps_uniform:
            reasons.append("runtime_source_step_spacing_not_uniform")
        if runtime_reported_steps_increasing is not None and runtime_reported_steps_increasing != runtime_steps_increasing:
            reasons.append("runtime_source_steps_increasing_flag_mismatch")
        if runtime_reported_steps_uniform is not None and runtime_reported_steps_uniform != runtime_steps_uniform:
            reasons.append("runtime_source_step_spacing_flag_mismatch")
        if runtime_selected_last_window is not True:
            reasons.append("runtime_selected_last_window_not_true")
        if runtime_hash_count != len(runtime_steps):
            reasons.append("runtime_source_vtk_hash_count_mismatch_time_steps")
        if runtime_hash_count < args.min_avg_frames:
            reasons.append("runtime_source_vtk_hash_count_below_min_avg_frames")
        if runtime_hash_unique_count != runtime_hash_count:
            reasons.append("runtime_source_vtk_hashes_not_unique")
        if any(len(value) != 64 for value in runtime_hashes):
            reasons.append("runtime_source_vtk_hash_not_sha256")
    runtime_step_shortfall_reason = count_below_minimum_reason(
        "runtime_average_step_span",
        runtime_step_span,
        args.min_avg_step_span,
    )
    planned_step_shortfall_reason = count_below_minimum_reason(
        "planned_average_step_span",
        planned_span,
        args.min_avg_step_span,
    )
    if runtime_step_shortfall_reason:
        reasons.append("runtime_average_step_span_too_short")
        reasons.append(runtime_step_shortfall_reason)
    if planned_step_shortfall_reason:
        reasons.append("planned_average_step_span_too_short")
        reasons.append(planned_step_shortfall_reason)

    time_gate = str(runtime_audit.get("time_averaging_gate") or "").strip().lower()
    requested_frame_gate = str(runtime_audit.get("requested_vtk_frame_gate") or "").strip().lower()
    time_average_gate = "pass" if time_gate == "pass" and requested_frame_gate == "pass" else "fail"
    if time_average_gate != "pass":
        reasons.append("runtime_time_averaging_gate_not_pass")

    if runtime_audit:
        if not runtime_steps:
            reasons.append("runtime_source_time_steps_missing")
        if not runtime_hashes:
            reasons.append("runtime_source_vtk_hashes_missing")

    expected_vector = parse_vector(args.wind_vector)
    actual_vector = shared_wind_vector(shared)
    wind_delta = vector_delta(actual_vector, expected_vector) if expected_vector else None
    if expected_vector and (wind_delta is None or wind_delta > args.wind_vector_tolerance):
        reasons.append("wind_vector_mismatch")

    shared_u_ref = as_float(shared.get("ReferenceWindSpeedMps"))
    metadata_u_ref = as_float(metadata.get("ReferenceWindSpeedMps") or metadata.get("WindSpeed"))
    u_ref = shared_u_ref if shared_u_ref is not None else metadata_u_ref
    af_csv = Path(args.af_csv).expanduser().resolve() if args.af_csv else None
    u_ref_from_af = af_u_at_reference_height(af_csv, args.z_ref)
    if args.u_ref is not None and (u_ref is None or abs(u_ref - args.u_ref) > args.u_ref_tolerance):
        reasons.append("uref_mismatch")
    if (
        args.u_ref is not None
        and u_ref_from_af is not None
        and abs(args.u_ref - u_ref_from_af) > args.u_ref_tolerance
    ):
        reasons.append("uref_af_profile_mismatch")
        reasons.append(
            f"uref_af_profile_delta_{reason_token(f'{abs(args.u_ref - u_ref_from_af):.12g}')}"
        )
    if (
        u_ref is not None
        and u_ref_from_af is not None
        and abs(u_ref - u_ref_from_af) > args.u_ref_tolerance
    ):
        reasons.append("metadata_uref_af_profile_mismatch")

    af_sha = sha256_file(af_csv)
    manifest_af_sha = str(shared.get("WindProfileCsvSha256") or "").strip().lower()
    if af_csv:
        if not af_sha:
            reasons.append("af_csv_missing")
        elif manifest_af_sha and manifest_af_sha != af_sha:
            reasons.append("af_csv_hash_mismatch")
    if str(shared.get("WindProfile") or "").strip().lower() != "customtable":
        reasons.append("wind_profile_not_customtable")

    inlet_source_gate = str(inlet_source_audit.get("inlet_source_gate") or "").strip().lower()
    paper_inlet_source_gate = str(inlet_source_audit.get("paper_grade_inlet_source_gate") or "").strip().lower()
    inlet_distribution_consistent = as_bool(inlet_source_audit.get("inlet_source_distribution_consistent"))
    inlet_velocity_only = as_bool(inlet_source_audit.get("inlet_source_velocity_field_only"))
    inlet_source_method_class = str(inlet_source_audit.get("inlet_source_method_class") or "").strip()
    inlet_correlation_model = str(inlet_source_audit.get("synthetic_inlet_correlation_model") or "").strip()
    inlet_has_uncorrelated_random = as_bool(inlet_source_audit.get("has_uncorrelated_random_inlet"))
    inlet_uncorrelated_random_patterns = split_scalar_list(
        inlet_source_audit.get("uncorrelated_random_inlet_patterns")
    )
    inlet_recommended_next_action = str(inlet_source_audit.get("recommended_next_action") or "").strip()
    inlet_has_three_component_velocity_write = as_bool(
        inlet_source_audit.get("has_three_component_velocity_write")
    )
    inlet_has_three_component_fluctuation_evidence = as_bool(
        inlet_source_audit.get("has_three_component_fluctuation_evidence")
    )
    inlet_has_k_driven_three_component_stg = as_bool(
        inlet_source_audit.get("has_k_driven_three_component_stg")
    )
    inlet_has_mean_preserving_correction = as_bool(
        inlet_source_audit.get("has_mean_preserving_inlet_correction")
    )
    inlet_has_layerwise_mean_preserving_correction = as_bool(
        inlet_source_audit.get("has_layerwise_mean_preserving_inlet_correction")
    )
    inlet_stg_evidence_required = (
        "stg" in inlet_source_method_class.lower()
        or "stg" in inlet_correlation_model.lower()
        or as_bool(inlet_source_audit.get("has_synthetic_inlet_function")) is True
    )
    inlet_source_reasons = split_scalar_list(inlet_source_audit.get("inlet_source_gate_reasons"))
    paper_inlet_source_reasons = split_scalar_list(inlet_source_audit.get("paper_grade_inlet_source_gate_reasons"))
    if not inlet_source_audit:
        reasons.append("inlet_source_audit_missing")
    if inlet_source_gate != "pass":
        reasons.append("inlet_source_gate_not_pass")
    if paper_inlet_source_gate != "pass":
        reasons.append("paper_grade_inlet_source_gate_not_pass")
    if inlet_distribution_consistent is not True:
        reasons.append("inlet_source_not_distribution_consistent")
    if inlet_velocity_only is True:
        reasons.append("inlet_source_velocity_field_only")
    if inlet_stg_evidence_required and inlet_has_three_component_velocity_write is not True:
        reasons.append("inlet_source_missing_three_component_velocity_write_evidence")
    if inlet_stg_evidence_required and inlet_has_three_component_fluctuation_evidence is not True:
        reasons.append("inlet_source_missing_three_component_fluctuation_evidence")
    if inlet_stg_evidence_required and inlet_has_k_driven_three_component_stg is not True:
        reasons.append("inlet_source_missing_k_driven_three_component_stg_evidence")
    if inlet_stg_evidence_required and inlet_has_mean_preserving_correction is not True:
        reasons.append("inlet_source_missing_mean_preserving_inlet_correction")
    if inlet_stg_evidence_required and inlet_has_layerwise_mean_preserving_correction is not True:
        reasons.append("inlet_source_missing_layerwise_mean_preserving_inlet_correction")
    if (
        inlet_has_uncorrelated_random is True
        or inlet_correlation_model == "uncorrelated_random_rms_velocity_field_only"
        or "synthetic_inlet_uses_uncorrelated_random_rms" in inlet_source_reasons
    ):
        reasons.append("inlet_source_uses_uncorrelated_random_rms")
    inlet_source_hash_check = append_setup_hash_reason(reasons, "inlet_source", inlet_source_audit, setup_sha)

    inlet_profile_gate = str(inlet_profile_audit.get("inlet_profile_gate") or "").strip().upper()
    inlet_u_profile_gate = str(inlet_profile_audit.get("inlet_u_profile_gate") or "").strip().upper()
    inlet_k_profile_gate = str(inlet_profile_audit.get("inlet_k_profile_gate") or "").strip().upper()
    inlet_profile_time_gate = str(inlet_profile_audit.get("time_averaging_gate") or "").strip().upper()
    inlet_profile_frame_count = as_int(inlet_profile_audit.get("frame_count"))
    if not inlet_profile_audit:
        reasons.append("inlet_profile_audit_missing")
    if inlet_profile_gate != "PASS":
        reasons.append("inlet_profile_gate_not_pass")
    if inlet_u_profile_gate != "PASS":
        reasons.append("inlet_u_profile_gate_not_pass")
    if inlet_k_profile_gate != "PASS":
        reasons.append("inlet_k_profile_gate_not_pass")
    if inlet_profile_time_gate != "PASS":
        reasons.append("inlet_profile_time_averaging_gate_not_pass")
    if inlet_profile_frame_count is None or inlet_profile_frame_count < args.min_avg_frames:
        reasons.append("inlet_profile_frame_count_below_minimum")
    inlet_profile_span_check = append_source_step_span_reasons(
        reasons,
        "inlet_profile",
        inlet_profile_audit,
        args.min_avg_step_span,
    )
    inlet_profile_window_check = append_source_window_reasons(
        reasons,
        "inlet_profile",
        inlet_profile_audit,
        runtime_steps,
        runtime_hashes,
    )
    inlet_profile_af_sha = str(inlet_profile_audit.get("af_csv_sha256") or "").strip().lower()
    inlet_profile_af_hash_matches = bool(inlet_profile_af_sha) and (
        (bool(af_sha) and inlet_profile_af_sha == af_sha)
        or (bool(manifest_af_sha) and inlet_profile_af_sha == manifest_af_sha)
    )
    if inlet_profile_audit:
        if not inlet_profile_af_sha:
            reasons.append("inlet_profile_af_csv_sha256_missing")
        elif not inlet_profile_af_hash_matches:
            reasons.append("inlet_profile_af_csv_sha256_mismatch")

    inlet_correlation_gate = str(inlet_correlation_audit.get("inlet_correlation_gate") or "").strip().upper()
    inlet_k_variance_gate = str(inlet_correlation_audit.get("inlet_k_variance_gate") or "").strip().upper()
    inlet_k_variance_ratio = as_float(inlet_correlation_audit.get("inlet_streamwise_variance_to_k_ratio"))
    inlet_k_variance_target = as_float(inlet_correlation_audit.get("inlet_streamwise_variance_target_from_k"))
    inlet_correlation_frame_count = as_int(inlet_correlation_audit.get("frame_count"))
    if not inlet_correlation_audit:
        reasons.append("inlet_correlation_audit_missing")
    if inlet_correlation_gate != "PASS":
        reasons.append("inlet_correlation_gate_not_pass")
    if inlet_k_variance_gate != "PASS":
        reasons.append("inlet_k_variance_gate_not_pass")
    if inlet_correlation_frame_count is None or inlet_correlation_frame_count < args.min_avg_frames:
        reasons.append("inlet_correlation_frame_count_below_minimum")
    inlet_correlation_span_check = append_source_step_span_reasons(
        reasons,
        "inlet_correlation",
        inlet_correlation_audit,
        args.min_avg_step_span,
    )
    inlet_correlation_window_check = append_source_window_reasons(
        reasons,
        "inlet_correlation",
        inlet_correlation_audit,
        runtime_steps,
        runtime_hashes,
    )

    boundary_source_gate = str(boundary_source_audit.get("boundary_source_gate") or "").strip().lower()
    paper_boundary_source_gate = str(boundary_source_audit.get("paper_grade_boundary_source_gate") or "").strip().lower()
    boundary_source_equivalent = as_bool(boundary_source_audit.get("boundary_source_wind_tunnel_equivalent"))
    boundary_source_simplified = as_bool(boundary_source_audit.get("boundary_source_simplified"))
    boundary_source_missing_paper_evidence = split_scalar_list(
        boundary_source_audit.get("missing_paper_grade_source_evidence")
    )
    if not boundary_source_audit:
        reasons.append("boundary_source_audit_missing")
    if boundary_source_gate != "pass":
        reasons.append("boundary_source_gate_not_pass")
    if paper_boundary_source_gate != "pass":
        reasons.append("paper_grade_boundary_source_gate_not_pass")
    if boundary_source_equivalent is not True:
        reasons.append("boundary_source_not_wind_tunnel_equivalent")
    if boundary_source_simplified is True:
        reasons.append("boundary_source_simplified")
    for field in boundary_source_missing_paper_evidence:
        reasons.append(f"boundary_source_missing_paper_grade_evidence_{field}")
    boundary_source_hash_check = append_setup_hash_reason(reasons, "boundary_source", boundary_source_audit, setup_sha)

    boundary_protocol_gate = str(boundary_protocol_audit.get("boundary_protocol_gate") or "").strip().lower()
    boundary_evidence_gate = str(boundary_protocol_audit.get("boundary_evidence_gate") or "").strip().lower()
    boundary_run_identity_gate = str(boundary_protocol_audit.get("boundary_run_identity_gate") or "").strip().lower()
    boundary_run_identity_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_run_identity_gate_reasons"))
    boundary_evidence_metadata_hash_matches = as_bool(
        boundary_protocol_audit.get("evidence_metadata_sha256_matches_current")
    )
    boundary_evidence_hashed = as_bool(boundary_protocol_audit.get("boundary_evidence_files_all_hashed"))
    boundary_equivalence_supported = as_bool(boundary_protocol_audit.get("boundary_equivalence_supported"))
    boundary_evidence_class_supported = as_bool(boundary_protocol_audit.get("boundary_evidence_class_supported"))
    boundary_condition_fields_supported = as_bool(
        boundary_protocol_audit.get("boundary_condition_fields_supported")
    )
    boundary_clearance_numeric_gate = str(boundary_protocol_audit.get("clearance_numeric_gate") or "").strip().lower()
    boundary_blockage_gate = str(boundary_protocol_audit.get("blockage_gate") or "").strip().lower()
    boundary_protocol_reasons = split_scalar_list(boundary_protocol_audit.get("boundary_protocol_gate_reasons"))
    boundary_condition_support_reasons = split_scalar_list(
        boundary_protocol_audit.get("boundary_condition_support_reasons")
    )
    boundary_clearance_reasons = split_scalar_list(
        boundary_protocol_audit.get("clearance_numeric_gate_reasons")
    )
    boundary_missing_evidence_fields = split_scalar_list(boundary_protocol_audit.get("missing_evidence_fields"))
    boundary_unsupported_condition_fields = split_scalar_list(
        boundary_protocol_audit.get("unsupported_boundary_condition_fields")
    )
    if not boundary_unsupported_condition_fields:
        prefix = "unsupported_boundary_condition_fields:"
        for support_reason in boundary_condition_support_reasons:
            if support_reason.startswith(prefix):
                boundary_unsupported_condition_fields = split_scalar_list(support_reason[len(prefix) :])
                break
    boundary_evidence_files_missing = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_missing"))
    boundary_evidence_files_empty = split_scalar_list(boundary_protocol_audit.get("boundary_evidence_files_empty"))
    boundary_evidence_files_unreadable = split_scalar_list(
        boundary_protocol_audit.get("boundary_evidence_files_unreadable")
    )
    boundary_required_support_fields_missing_or_false = [
        field for field in REQUIRED_BOUNDARY_SUPPORT_FIELDS if as_bool(boundary_protocol_audit.get(field)) is not True
    ]
    if not boundary_protocol_audit:
        reasons.append("boundary_protocol_audit_missing")
    if boundary_protocol_gate != "pass":
        reasons.append("boundary_protocol_gate_not_pass")
    if boundary_evidence_gate != "pass":
        reasons.append("boundary_evidence_gate_not_pass")
    if boundary_run_identity_gate != "pass":
        reasons.append("boundary_run_identity_gate_not_pass")
    if boundary_evidence_metadata_hash_matches is not True:
        reasons.append("boundary_evidence_metadata_sha256_not_bound_to_current_run")
    if boundary_evidence_hashed is not True:
        reasons.append("boundary_evidence_files_not_hashed")
    if boundary_protocol_audit:
        if boundary_equivalence_supported is not True:
            reasons.append("boundary_equivalence_not_supported")
        if boundary_evidence_class_supported is not True:
            reasons.append("boundary_evidence_class_not_supported")
        if boundary_condition_fields_supported is not True:
            reasons.append("boundary_condition_fields_not_supported")
        if boundary_clearance_numeric_gate != "pass":
            reasons.append("boundary_clearance_numeric_gate_not_pass")
        if boundary_blockage_gate != "pass":
            reasons.append("boundary_blockage_gate_not_pass")
        if boundary_missing_evidence_fields:
            reasons.append("boundary_missing_evidence_fields_present")
            for field in boundary_missing_evidence_fields:
                reasons.append(f"boundary_missing_evidence_field_{field}")
        if boundary_unsupported_condition_fields:
            reasons.append("boundary_unsupported_condition_fields_present")
            for field in boundary_unsupported_condition_fields:
                reasons.append(f"boundary_condition_field_{field}_not_supported")
        if boundary_required_support_fields_missing_or_false:
            reasons.append("boundary_required_support_fields_missing_or_false")
            for field in boundary_required_support_fields_missing_or_false:
                reasons.append(f"boundary_required_support_field_{field}_not_supported")
        for clearance_reason in boundary_clearance_reasons:
            if clearance_reason != "clearance_numeric_evidence_complete":
                reasons.append(f"boundary_clearance_{clearance_reason}")
        for path in boundary_evidence_files_missing:
            reasons.append(f"boundary_evidence_file_missing_{Path(path).name or 'unnamed'}")
        for path in boundary_evidence_files_empty:
            reasons.append(f"boundary_evidence_file_empty_{Path(path).name or 'unnamed'}")
        for path in boundary_evidence_files_unreadable:
            reasons.append(f"boundary_evidence_file_unreadable_{Path(path).name or 'unnamed'}")
        for identity_reason in boundary_run_identity_reasons:
            if identity_reason != "boundary_evidence_bound_to_current_run":
                reasons.append(f"boundary_identity_{identity_reason}")

    boundary_runtime_gate = str(boundary_runtime_audit.get("boundary_runtime_gate") or "").strip().lower()
    boundary_runtime_traceability_gate = str(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate") or ""
    ).strip().lower()
    boundary_runtime_profile_gate = str(
        boundary_runtime_audit.get("boundary_runtime_profile_preservation_gate") or ""
    ).strip().lower()
    boundary_runtime_inlet_gate = str(boundary_runtime_audit.get("boundary_runtime_inlet_gate") or "").strip().lower()
    boundary_runtime_side_top_gate = str(boundary_runtime_audit.get("boundary_runtime_side_top_gate") or "").strip().lower()
    boundary_runtime_outlet_gate = str(boundary_runtime_audit.get("boundary_runtime_outlet_gate") or "").strip().lower()
    boundary_runtime_reasons = split_scalar_list(boundary_runtime_audit.get("boundary_runtime_gate_reasons"))
    boundary_runtime_traceability_reasons = split_scalar_list(
        boundary_runtime_audit.get("boundary_runtime_traceability_gate_reasons")
    )
    if not boundary_runtime_audit:
        reasons.append("boundary_runtime_audit_missing")
    else:
        if boundary_runtime_gate != "pass":
            reasons.append("boundary_runtime_gate_not_pass")
        if boundary_runtime_traceability_gate != "pass":
            reasons.append("boundary_runtime_traceability_gate_not_pass")
        if boundary_runtime_profile_gate != "pass":
            reasons.append("boundary_runtime_profile_preservation_gate_not_pass")
        if boundary_runtime_inlet_gate != "pass":
            reasons.append("boundary_runtime_inlet_gate_not_pass")
        if boundary_runtime_side_top_gate != "pass":
            reasons.append("boundary_runtime_side_top_gate_not_pass")
        if boundary_runtime_outlet_gate != "pass":
            reasons.append("boundary_runtime_outlet_gate_not_pass")
        for reason in boundary_runtime_reasons:
            if reason != "boundary_runtime_faces_preserve_af_profile":
                reasons.append(f"boundary_runtime_{reason}")
        for reason in boundary_runtime_traceability_reasons:
            if reason != "boundary_runtime_window_traceable":
                reasons.append(f"boundary_runtime_traceability_{reason}")

    expected_component = str(args.expected_compared_component or "").strip()
    failed_probe_rows = [row for row in probe_rows if probe_row_failed(row)]
    valid_probe_rows = [row for row in probe_rows if not probe_row_failed(row)]
    compared_components = {
        row_value(row, "compared_component", "ComparedComponent")
        for row in valid_probe_rows
        if row_value(row, "compared_component", "ComparedComponent")
    }
    compared_component_values_csv = ";".join(sorted(compared_components))
    compared_component_mismatch_reason = ""
    if not probe_rows:
        reasons.append("probe_audit_missing_or_empty")
    if probe_rows and not valid_probe_rows:
        reasons.append("probe_audit_has_no_valid_rows")
    if failed_probe_rows:
        reasons.append("probe_audit_has_failed_rows")
    if expected_component and compared_components != {expected_component}:
        reasons.append("probe_compared_component_mismatch")
        compared_component_mismatch_reason = (
            f"probe_compared_component_{reason_token(compared_component_values_csv)}"
            f"_expected_{reason_token(expected_component)}"
        )
        reasons.append(compared_component_mismatch_reason)

    official_coordinates, official_coordinate_error = build_official_coordinate_lookup(
        official_path,
        args.case,
        args.wind_direction_label,
    )
    probe_id_column = find_csv_column(valid_probe_rows, ["probe_id", "ProbeId", "ProbeID", "No.", "No", "number", "point_id", "PointId", "id", "ID"])
    official_probe_ids = set(official_coordinates.keys())
    probe_ids: List[str] = []
    seen_probe_ids = set()
    duplicate_probe_ids = set()
    missing_probe_id_count = 0
    if valid_probe_rows and not probe_id_column:
        reasons.append("probe_id_column_missing")
    for row in valid_probe_rows:
        probe_id = normalized_column_key(str(row.get(probe_id_column) or "").strip()) if probe_id_column else ""
        if not probe_id:
            missing_probe_id_count += 1
            continue
        if probe_id in seen_probe_ids:
            duplicate_probe_ids.add(probe_id)
        seen_probe_ids.add(probe_id)
        probe_ids.append(probe_id)
    unmatched_probe_ids = sorted(set(probe_ids) - official_probe_ids) if official_probe_ids else sorted(set(probe_ids))
    missing_official_probe_ids = sorted(official_probe_ids - set(probe_ids)) if official_probe_ids else []
    duplicate_probe_ids_sorted = sorted(duplicate_probe_ids)
    official_probe_coverage_ratio = (
        len(official_probe_ids & set(probe_ids)) / len(official_probe_ids)
        if official_probe_ids
        else None
    )
    official_probe_coverage_reason = ""
    if valid_probe_rows:
        if official_coordinate_error:
            reasons.append("probe_official_identity_error:" + official_coordinate_error)
        if missing_probe_id_count:
            reasons.append("probe_id_missing")
            reasons.append(count_reason("probe_id_missing_count", missing_probe_id_count))
        if duplicate_probe_ids:
            reasons.append("probe_id_duplicate")
            reasons.append(count_reason("probe_id_duplicate_count", len(duplicate_probe_ids)))
        if unmatched_probe_ids:
            reasons.append("probe_unmatched_official_ids")
            reasons.append(count_reason("probe_unmatched_official_id_count", len(unmatched_probe_ids)))
        if missing_official_probe_ids or official_probe_coverage_ratio != 1.0:
            reasons.append("probe_official_probe_coverage_incomplete")
            official_probe_coverage_reason = (
                f"probe_official_coverage_{len(official_probe_ids & set(probe_ids))}"
                f"_of_{len(official_probe_ids)}"
            )
            reasons.append(official_probe_coverage_reason)
    coordinate_summary = probe_official_coordinate_delta_summary(
        valid_probe_rows,
        official_coordinates,
        probe_id_column,
    )
    official_coordinate_deltas = coordinate_summary["deltas"]
    official_coordinate_recomputed_count = coordinate_summary["recomputed_count"]
    missing_official_coordinate_delta_count = coordinate_summary["missing_count"]
    official_coordinate_delta_source = coordinate_summary["source"]
    requires_current_official_recompute = coordinate_summary["requires_current_official_recompute"]
    max_official_coordinate_delta = max(official_coordinate_deltas) if official_coordinate_deltas else None
    official_coordinate_delta_violation_count = sum(
        1 for value in official_coordinate_deltas if abs(value) > args.max_official_coordinate_delta_m
    )
    probe_projection_issue_reason = ""
    probe_component_uref_issue_reason = compared_component_mismatch_reason
    normalization_missing_count = 0
    normalization_invalid_count = 0
    wind_missing_count = 0
    wind_invalid_count = 0
    uref_missing_count = 0
    uref_mismatch_count = 0
    nearest_distance_missing_count = 0
    tolerance_missing_or_disabled_count = 0
    probe_out_of_tolerance_count = 0
    for row in valid_probe_rows:
        normalized = as_bool(row_value(row, "normalization_valid", "NormalizationValid"))
        if normalized is None:
            normalization_missing_count += 1
        elif normalized is not True:
            normalization_invalid_count += 1
        wind_valid = as_bool(row_value(row, "wind_direction_valid", "WindDirectionValid"))
        if wind_valid is None:
            wind_missing_count += 1
        elif wind_valid is not True:
            wind_invalid_count += 1
        row_uref = as_float(row_value(row, "u_ref", "Uref", "U_ref"))
        if row_uref is None:
            uref_missing_count += 1
        elif args.u_ref is not None and abs(row_uref - args.u_ref) > args.u_ref_tolerance:
            uref_mismatch_count += 1
        if as_float(row_value(row, "nearest_distance", "NearestDistance")) is None:
            nearest_distance_missing_count += 1
        tolerance = as_float(row_value(row, "tolerance", "Tolerance"))
        if tolerance is None or tolerance <= 0.0:
            tolerance_missing_or_disabled_count += 1
        if as_bool(row_value(row, "out_of_tolerance", "OutOfTolerance")) is True:
            probe_out_of_tolerance_count += 1
    if valid_probe_rows:
        if missing_official_coordinate_delta_count:
            reasons.append("probe_official_coordinate_delta_missing")
            reasons.append(
                count_reason("probe_official_coordinate_delta_missing_count", missing_official_coordinate_delta_count)
            )
        if requires_current_official_recompute and official_coordinate_recomputed_count != len(valid_probe_rows):
            reasons.append("probe_official_coordinate_delta_current_official_recompute_incomplete")
            reasons.append(
                count_reason(
                    "probe_official_coordinate_delta_recomputed_count",
                    official_coordinate_recomputed_count,
                )
            )
        if official_coordinate_delta_violation_count:
            reasons.append("probe_official_coordinate_delta_exceeds_threshold")
            reasons.append(
                count_reason(
                    "probe_official_coordinate_delta_violation_count",
                    official_coordinate_delta_violation_count,
                )
            )
        if normalization_missing_count:
            reasons.append("probe_normalization_valid_missing")
            reasons.append(count_reason("probe_normalization_valid_missing_count", normalization_missing_count))
        if normalization_invalid_count:
            reasons.append("probe_normalization_invalid")
            reasons.append(count_reason("probe_normalization_invalid_count", normalization_invalid_count))
        if wind_missing_count:
            reasons.append("probe_wind_direction_valid_missing")
            reasons.append(count_reason("probe_wind_direction_valid_missing_count", wind_missing_count))
        if wind_invalid_count:
            reasons.append("probe_wind_direction_invalid")
            reasons.append(count_reason("probe_wind_direction_invalid_count", wind_invalid_count))
        if uref_missing_count:
            reasons.append("probe_uref_missing")
            reasons.append(count_reason("probe_uref_missing_count", uref_missing_count))
        if uref_mismatch_count:
            reasons.append("probe_uref_mismatch")
            uref_reason = count_reason("probe_uref_mismatch_count", uref_mismatch_count)
            reasons.append(uref_reason)
            probe_component_uref_issue_reason = ";".join(
                reason for reason in [probe_component_uref_issue_reason, uref_reason] if reason
            )
        if nearest_distance_missing_count:
            reasons.append("probe_nearest_distance_missing")
            reasons.append(count_reason("probe_nearest_distance_missing_count", nearest_distance_missing_count))
        if tolerance_missing_or_disabled_count:
            reasons.append("probe_tolerance_missing_or_disabled")
            tolerance_reason = count_reason("probe_tolerance_missing_or_disabled_count", tolerance_missing_or_disabled_count)
            reasons.append(tolerance_reason)
            probe_projection_issue_reason = ";".join(
                reason for reason in [probe_projection_issue_reason, tolerance_reason] if reason
            )
        if probe_out_of_tolerance_count:
            reasons.append("probe_out_of_tolerance")
            out_of_tolerance_reason = count_reason("probe_out_of_tolerance_count", probe_out_of_tolerance_count)
            reasons.append(out_of_tolerance_reason)
            probe_projection_issue_reason = ";".join(
                reason for reason in [probe_projection_issue_reason, out_of_tolerance_reason] if reason
            )
    probe_source_steps_values = probe_unique_values(
        probe_rows,
        "vtk_source_time_steps",
        "VtkSourceTimeSteps",
        "source_time_steps",
        "SourceTimeSteps",
    )
    probe_source_hash_values = probe_unique_values(
        probe_rows,
        "vtk_source_sha256",
        "VtkSourceSha256",
        "source_vtk_sha256",
        "SourceVtkSha256",
    )
    probe_source_step_span_values = probe_unique_int_values(
        probe_rows,
        "vtk_source_step_span",
        "VtkSourceStepSpan",
        "source_step_span",
        "SourceStepSpan",
    )
    probe_minimum_step_span_values = probe_unique_int_values(
        probe_rows,
        "minimum_validation_average_step_span",
        "MinimumValidationAverageStepSpan",
        "vtk_minimum_validation_average_step_span",
        "VtkMinimumValidationAverageStepSpan",
    )
    probe_source_steps = parse_int_list(probe_source_steps_values[0]) if len(probe_source_steps_values) == 1 else []
    probe_source_hashes = parse_hash_list(probe_source_hash_values[0]) if len(probe_source_hash_values) == 1 else []
    probe_source_step_span = probe_source_step_span_values[0] if len(probe_source_step_span_values) == 1 else None
    probe_minimum_step_span = probe_minimum_step_span_values[0] if len(probe_minimum_step_span_values) == 1 else None
    probe_source_steps_match = bool(runtime_steps) and probe_source_steps == runtime_steps
    probe_source_hashes_match = bool(runtime_hashes) and bool(probe_source_hashes) and set(probe_source_hashes) == set(runtime_hashes)
    probe_source_steps_increasing = source_steps_strictly_increasing(probe_source_steps)
    probe_source_steps_uniform = source_steps_uniformly_spaced(probe_source_steps)
    probe_source_step_span_match = (
        runtime_step_span is not None
        and probe_source_step_span is not None
        and probe_source_step_span == runtime_step_span
    )
    if probe_rows:
        if len(probe_source_steps_values) != 1:
            reasons.append("probe_source_time_steps_inconsistent_or_missing")
        elif not probe_source_steps_match:
            reasons.append("probe_source_time_steps_mismatch")
        if not probe_source_steps_increasing:
            reasons.append("probe_source_steps_not_strictly_increasing")
        if not probe_source_steps_uniform:
            reasons.append("probe_source_step_spacing_not_uniform")
        if len(probe_source_hash_values) != 1:
            reasons.append("probe_source_vtk_hashes_inconsistent_or_missing")
        elif not probe_source_hashes_match:
            reasons.append("probe_source_vtk_hashes_mismatch")
        if len(probe_source_step_span_values) != 1:
            reasons.append("probe_source_step_span_inconsistent_or_missing")
        else:
            if probe_source_step_span < args.min_avg_step_span:
                reasons.append("probe_source_step_span_too_short")
            if not probe_source_step_span_match:
                reasons.append("probe_source_step_span_mismatch")
        if len(probe_minimum_step_span_values) != 1:
            reasons.append("probe_minimum_step_span_inconsistent_or_missing")
        elif probe_minimum_step_span != args.min_avg_step_span:
            reasons.append("probe_minimum_step_span_mismatch")

    component_gate = str(component_sensitivity_audit.get("component_normalization_gate") or "").strip().lower()
    component_sensitivity_gate = str(component_sensitivity_audit.get("component_sensitivity_gate") or "").strip().lower()
    normalization_scale_gate = str(component_sensitivity_audit.get("normalization_scale_gate") or "").strip().lower()
    component_source_window_gate = str(component_sensitivity_audit.get("component_source_window_gate") or "").strip().lower()
    if not component_sensitivity_audit:
        reasons.append("component_sensitivity_audit_missing")
    reasons.extend(component_hash_traceability["reasons"])
    if component_gate != "pass":
        reasons.append("component_normalization_gate_not_pass")
    if component_sensitivity_gate != "pass":
        reasons.append("component_sensitivity_gate_not_pass")
    if normalization_scale_gate != "pass":
        reasons.append("normalization_scale_gate_not_pass")
    if component_source_window_gate != "pass":
        reasons.append("component_source_window_gate_not_pass")

    protocol_identity_gate = "pass" if not any(
        reason in reasons
        for reason in [
            "wind_vector_mismatch",
            "uref_mismatch",
            "uref_af_profile_mismatch",
            "metadata_uref_af_profile_mismatch",
            "af_csv_missing",
            "af_csv_hash_mismatch",
            "wind_profile_not_customtable",
            "metadata_manifest_time_steps_mismatch",
            "metadata_manifest_save_interval_mismatch",
        ]
    ) else "fail"

    native_diagnostic_priority = build_native_diagnostic_priority(reasons)
    native_top_priority = native_diagnostic_priority[0] if native_diagnostic_priority else {}
    native_precondition_closure = build_native_precondition_closure(reasons)

    result = {
        "generated_at_utc": utc_now(),
        "run_dir": str(run_dir),
        "manifest": str(manifest_path) if manifest_path else "",
        "metadata": str(metadata_path) if metadata_path else "",
        "runtime_audit": str(runtime_audit_path) if runtime_audit_path else "",
        "setup_cpp": str(setup_path) if setup_path else "",
        "defines_hpp": str(defines_path) if defines_path else "",
        "domain_origin": str(domain_origin_path) if domain_origin_path else "",
        "validation_protocol_audit": str(protocol_audit_path) if protocol_audit_path else "",
        "baseline_id": str(manifest.get("BaselineId") or "").strip(),
        "case": args.case,
        "software": args.software,
        "expected_wind_vector": args.wind_vector,
        "actual_wind_vector": actual_vector,
        "wind_vector_delta": wind_delta,
        "expected_uref_mps": args.u_ref,
        "actual_uref_mps": u_ref,
        "expected_zref_m": args.z_ref,
        "af_uref_at_zref_mps": u_ref_from_af,
        "uref_af_profile_delta_mps": (
            abs(args.u_ref - u_ref_from_af)
            if args.u_ref is not None and u_ref_from_af is not None
            else None
        ),
        "metadata_uref_af_profile_delta_mps": (
            abs(u_ref - u_ref_from_af)
            if u_ref is not None and u_ref_from_af is not None
            else None
        ),
        "expected_vtk_pattern": args.expected_vtk_pattern,
        "runtime_vtk_pattern": runtime_pattern,
        "average_last_n_required": args.average_last_n,
        "runtime_average_last_n": runtime_avg,
        "min_avg_frames": args.min_avg_frames,
        "min_avg_step_span": args.min_avg_step_span,
        "planned_frame_count_min": planned_frame_count_min,
        "planned_frame_count_shortfall_reason": planned_frame_shortfall_reason,
        "runtime_average_window_shortfall_reason": runtime_average_shortfall_reason,
        "planned_final_window_step_span": planned_span,
        "planned_average_step_span_shortfall_reason": planned_step_shortfall_reason,
        "runtime_source_step_span": runtime_step_span,
        "runtime_average_step_span_shortfall_reason": runtime_step_shortfall_reason,
        "runtime_reported_source_step_span": runtime_step_span_reported,
        "runtime_source_step_span_from_time_steps": runtime_step_span_from_steps,
        "runtime_source_step_span_matches_time_steps": (
            runtime_step_span_reported is not None
            and runtime_step_span_from_steps is not None
            and runtime_step_span_reported == runtime_step_span_from_steps
        ),
        "runtime_source_steps_strictly_increasing": runtime_steps_increasing,
        "runtime_source_step_spacing_uniform": runtime_steps_uniform,
        "runtime_reported_source_steps_strictly_increasing": runtime_reported_steps_increasing,
        "runtime_reported_source_step_spacing_uniform": runtime_reported_steps_uniform,
        "runtime_selected_last_window": runtime_selected_last_window,
        "runtime_source_time_steps": runtime_steps,
        "runtime_source_vtk_sha256": runtime_hashes,
        "runtime_source_vtk_sha256_count": runtime_hash_count,
        "runtime_source_vtk_sha256_unique_count": runtime_hash_unique_count,
        "runtime_time_averaging_gate": time_gate,
        "runtime_requested_vtk_frame_gate": requested_frame_gate,
        "inlet_source_audit": str(inlet_source_audit_path) if inlet_source_audit_path else "",
        "inlet_profile_audit": str(inlet_profile_audit_path) if inlet_profile_audit_path else "",
        "inlet_correlation_audit": str(inlet_correlation_audit_path) if inlet_correlation_audit_path else "",
        "boundary_source_audit": str(boundary_source_audit_path) if boundary_source_audit_path else "",
        "boundary_protocol_audit": str(boundary_protocol_audit_path) if boundary_protocol_audit_path else "",
        "boundary_runtime_audit": str(boundary_runtime_audit_path) if boundary_runtime_audit_path else "",
        "probe_audit": str(probe_audit_path) if probe_audit_path else "",
        "component_sensitivity_audit": str(component_sensitivity_audit_path) if component_sensitivity_audit_path else "",
        "official_measurement_csv": str(official_path) if official_path else "",
        "probe_audit_sha256": probe_audit_sha,
        "official_measurement_sha256": official_sha,
        "component_sensitivity_probe_audit_sha256": component_hash_traceability["component_probe_audit_sha256"],
        "component_sensitivity_official_sha256": component_hash_traceability["component_official_sha256"],
        "component_sensitivity_probe_audit_sha256_matches_current": component_hash_traceability[
            "probe_audit_sha256_matches_current"
        ],
        "component_sensitivity_official_sha256_matches_current": component_hash_traceability[
            "official_sha256_matches_current"
        ],
        "component_sensitivity_hash_traceability_gate": component_hash_traceability["gate"],
        "component_sensitivity_hash_traceability_gate_reasons": component_hash_traceability["reasons"],
        "component_sensitivity_hash_traceability_gate_reasons_csv": component_hash_traceability["reasons_csv"],
        "inlet_source_gate": inlet_source_gate,
        "paper_grade_inlet_source_gate": paper_inlet_source_gate,
        "inlet_source_distribution_consistent": inlet_distribution_consistent,
        "inlet_source_velocity_field_only": inlet_velocity_only,
        "inlet_source_method_class": inlet_source_method_class,
        "inlet_synthetic_correlation_model": inlet_correlation_model,
        "inlet_source_has_uncorrelated_random_inlet": inlet_has_uncorrelated_random,
        "inlet_source_uncorrelated_random_patterns": inlet_uncorrelated_random_patterns,
        "inlet_source_uncorrelated_random_patterns_csv": ";".join(inlet_uncorrelated_random_patterns),
        "inlet_source_recommended_next_action": inlet_recommended_next_action,
        "inlet_source_stg_evidence_required": inlet_stg_evidence_required,
        "inlet_source_has_three_component_velocity_write": inlet_has_three_component_velocity_write,
        "inlet_source_has_three_component_fluctuation_evidence": inlet_has_three_component_fluctuation_evidence,
        "inlet_source_has_k_driven_three_component_stg": inlet_has_k_driven_three_component_stg,
        "inlet_source_has_mean_preserving_inlet_correction": inlet_has_mean_preserving_correction,
        "inlet_source_has_layerwise_mean_preserving_inlet_correction": inlet_has_layerwise_mean_preserving_correction,
        "inlet_source_gate_reasons": inlet_source_reasons,
        "inlet_source_gate_reasons_csv": ";".join(inlet_source_reasons),
        "paper_grade_inlet_source_gate_reasons": paper_inlet_source_reasons,
        "paper_grade_inlet_source_gate_reasons_csv": ";".join(paper_inlet_source_reasons),
        **inlet_source_hash_check,
        "inlet_profile_gate": inlet_profile_gate,
        "inlet_u_profile_gate": inlet_u_profile_gate,
        "inlet_k_profile_gate": inlet_k_profile_gate,
        "inlet_profile_af_csv_sha256": inlet_profile_af_sha,
        "inlet_profile_af_csv_sha256_matches_expected": inlet_profile_af_hash_matches,
        **inlet_profile_span_check,
        **inlet_profile_window_check,
        "inlet_correlation_gate": inlet_correlation_gate,
        "inlet_k_variance_gate": inlet_k_variance_gate,
        "inlet_streamwise_variance_target_from_k": inlet_k_variance_target,
        "inlet_streamwise_variance_to_k_ratio": inlet_k_variance_ratio,
        **inlet_correlation_span_check,
        **inlet_correlation_window_check,
        "boundary_source_gate": boundary_source_gate,
        "paper_grade_boundary_source_gate": paper_boundary_source_gate,
        "boundary_source_wind_tunnel_equivalent": boundary_source_equivalent,
        "boundary_source_simplified": boundary_source_simplified,
        "boundary_source_missing_paper_grade_source_evidence": boundary_source_missing_paper_evidence,
        "boundary_source_missing_paper_grade_source_evidence_csv": ";".join(boundary_source_missing_paper_evidence),
        **boundary_source_hash_check,
        "boundary_protocol_gate": boundary_protocol_gate,
        "boundary_evidence_gate": boundary_evidence_gate,
        "boundary_run_identity_gate": boundary_run_identity_gate,
        "boundary_run_identity_gate_reasons": boundary_run_identity_reasons,
        "boundary_run_identity_gate_reasons_csv": ";".join(boundary_run_identity_reasons),
        "boundary_evidence_metadata_sha256_matches_current": boundary_evidence_metadata_hash_matches,
        "boundary_evidence_aij_case": str(boundary_protocol_audit.get("evidence_aij_case") or ""),
        "boundary_evidence_wind_direction": str(boundary_protocol_audit.get("evidence_wind_direction") or ""),
        "boundary_evidence_files_all_hashed": boundary_evidence_hashed,
        "boundary_equivalence_supported": boundary_equivalence_supported,
        "boundary_evidence_class_supported": boundary_evidence_class_supported,
        "boundary_condition_fields_supported": boundary_condition_fields_supported,
        "boundary_clearance_numeric_gate": boundary_clearance_numeric_gate,
        "boundary_blockage_gate": boundary_blockage_gate,
        "boundary_protocol_gate_reasons": boundary_protocol_reasons,
        "boundary_protocol_gate_reasons_csv": ";".join(boundary_protocol_reasons),
        "boundary_missing_evidence_fields": boundary_missing_evidence_fields,
        "boundary_missing_evidence_fields_csv": ";".join(boundary_missing_evidence_fields),
        "boundary_unsupported_condition_fields": boundary_unsupported_condition_fields,
        "boundary_unsupported_condition_fields_csv": ";".join(boundary_unsupported_condition_fields),
        "boundary_condition_support_reasons": boundary_condition_support_reasons,
        "boundary_condition_support_reasons_csv": ";".join(boundary_condition_support_reasons),
        "boundary_clearance_numeric_gate_reasons": boundary_clearance_reasons,
        "boundary_clearance_numeric_gate_reasons_csv": ";".join(boundary_clearance_reasons),
        "boundary_evidence_files_missing": boundary_evidence_files_missing,
        "boundary_evidence_files_missing_csv": ";".join(boundary_evidence_files_missing),
        "boundary_evidence_files_empty": boundary_evidence_files_empty,
        "boundary_evidence_files_empty_csv": ";".join(boundary_evidence_files_empty),
        "boundary_evidence_files_unreadable": boundary_evidence_files_unreadable,
        "boundary_evidence_files_unreadable_csv": ";".join(boundary_evidence_files_unreadable),
        "boundary_required_support_fields_missing_or_false": boundary_required_support_fields_missing_or_false,
        "boundary_required_support_fields_missing_or_false_csv": ";".join(boundary_required_support_fields_missing_or_false),
        "boundary_runtime_gate": boundary_runtime_gate,
        "boundary_runtime_gate_reasons": boundary_runtime_reasons,
        "boundary_runtime_gate_reasons_csv": ";".join(boundary_runtime_reasons),
        "boundary_runtime_traceability_gate": boundary_runtime_traceability_gate,
        "boundary_runtime_traceability_gate_reasons": boundary_runtime_traceability_reasons,
        "boundary_runtime_traceability_gate_reasons_csv": ";".join(boundary_runtime_traceability_reasons),
        "boundary_runtime_profile_preservation_gate": boundary_runtime_profile_gate,
        "boundary_runtime_inlet_gate": boundary_runtime_inlet_gate,
        "boundary_runtime_side_top_gate": boundary_runtime_side_top_gate,
        "boundary_runtime_outlet_gate": boundary_runtime_outlet_gate,
        "boundary_runtime_max_u_mae_ratio": boundary_runtime_audit.get("max_boundary_u_mae_ratio", ""),
        "boundary_runtime_inlet_u_mae_ratio": boundary_runtime_audit.get("inlet_u_mae_ratio", ""),
        "boundary_runtime_outlet_u_mae_ratio": boundary_runtime_audit.get("outlet_u_mae_ratio", ""),
        "boundary_runtime_side_top_max_u_mae_ratio": boundary_runtime_audit.get("side_top_max_u_mae_ratio", ""),
        "boundary_runtime_max_negative_streamwise_fraction": boundary_runtime_audit.get("max_boundary_negative_streamwise_fraction", ""),
        "boundary_runtime_source_step_span": boundary_runtime_audit.get("source_step_span", ""),
        "boundary_runtime_frame_count": boundary_runtime_audit.get("frame_count", ""),
        "probe_audit_row_count": len(probe_rows),
        "probe_audit_valid_row_count": len(valid_probe_rows),
        "probe_audit_failed_row_count": len(failed_probe_rows),
        "probe_audit_compared_components": sorted(compared_components),
        "probe_audit_compared_components_csv": compared_component_values_csv,
        "expected_compared_component": expected_component,
        "probe_compared_component_mismatch_reason": compared_component_mismatch_reason,
        "probe_id_column": probe_id_column,
        "probe_missing_id_count": missing_probe_id_count,
        "probe_duplicate_id_count": len(duplicate_probe_ids),
        "probe_duplicate_ids_csv": ";".join(duplicate_probe_ids_sorted),
        "probe_unique_id_count": len(seen_probe_ids),
        "official_probe_id_count": len(official_probe_ids),
        "matched_official_probe_id_count": len(official_probe_ids & set(probe_ids)),
        "missing_official_probe_id_count": len(missing_official_probe_ids),
        "missing_official_probe_ids_csv": ";".join(missing_official_probe_ids),
        "unmatched_probe_id_count": len(unmatched_probe_ids),
        "unmatched_probe_ids_csv": ";".join(unmatched_probe_ids),
        "official_probe_coverage_ratio": official_probe_coverage_ratio,
        "probe_official_coverage_reason": official_probe_coverage_reason,
        "probe_official_coordinate_delta_count": len(official_coordinate_deltas),
        "probe_official_coordinate_delta_source": official_coordinate_delta_source,
        "probe_official_coordinate_delta_recomputed_count": official_coordinate_recomputed_count,
        "probe_official_coordinate_delta_recompute_error": official_coordinate_error,
        "probe_missing_official_coordinate_delta_count": missing_official_coordinate_delta_count,
        "probe_max_official_coordinate_delta_m": max_official_coordinate_delta,
        "probe_official_coordinate_delta_violation_count": official_coordinate_delta_violation_count,
        "probe_max_official_coordinate_delta_threshold_m": args.max_official_coordinate_delta_m,
        "probe_normalization_missing_count": normalization_missing_count,
        "probe_normalization_invalid_count": normalization_invalid_count,
        "probe_wind_direction_missing_count": wind_missing_count,
        "probe_wind_direction_invalid_count": wind_invalid_count,
        "probe_uref_missing_count": uref_missing_count,
        "probe_uref_mismatch_count": uref_mismatch_count,
        "probe_nearest_distance_missing_count": nearest_distance_missing_count,
        "probe_tolerance_missing_or_disabled_count": tolerance_missing_or_disabled_count,
        "probe_out_of_tolerance_count": probe_out_of_tolerance_count,
        "probe_projection_issue_reason": probe_projection_issue_reason,
        "probe_component_uref_issue_reason": probe_component_uref_issue_reason,
        "probe_source_time_steps": probe_source_steps,
        "probe_source_time_steps_match_runtime": probe_source_steps_match,
        "probe_source_steps_strictly_increasing": probe_source_steps_increasing,
        "probe_source_step_spacing_uniform": probe_source_steps_uniform,
        "probe_source_step_span": probe_source_step_span,
        "probe_source_step_span_match_runtime": probe_source_step_span_match,
        "probe_minimum_validation_average_step_span": probe_minimum_step_span,
        "probe_source_vtk_sha256": probe_source_hashes,
        "probe_source_vtk_sha256_match_runtime": probe_source_hashes_match,
        "component_normalization_gate": component_gate,
        "component_sensitivity_gate": component_sensitivity_gate,
        "normalization_scale_gate": normalization_scale_gate,
        "component_source_window_gate": component_source_window_gate,
        "component_source_window_gate_reasons": component_sensitivity_audit.get(
            "component_source_window_gate_reasons", []
        ),
        "component_source_window_gate_reasons_csv": ";".join(
            str(reason) for reason in component_sensitivity_audit.get("component_source_window_gate_reasons", [])
        )
        if isinstance(component_sensitivity_audit.get("component_source_window_gate_reasons"), list)
        else str(component_sensitivity_audit.get("component_source_window_gate_reasons", "")),
        "component_source_time_steps": str(component_sensitivity_audit.get("component_source_time_steps") or ""),
        "component_source_step_span": component_sensitivity_audit.get("component_source_step_span"),
        "component_minimum_source_step_span": component_sensitivity_audit.get("component_minimum_source_step_span"),
        "component_source_sha256": str(component_sensitivity_audit.get("component_source_sha256") or ""),
        "native_preconditions_protocol_identity_gate": protocol_identity_gate,
        "native_preconditions_time_average_gate": time_average_gate,
        "native_preconditions_manifest_sha256": sha256_file(manifest_path),
        "native_preconditions_setup_sha256": setup_sha,
        "native_preconditions_defines_sha256": defines_sha,
        "native_preconditions_metadata_sha256": metadata_sha,
        "native_preconditions_runtime_audit_sha256": runtime_audit_sha,
        "native_preconditions_protocol_audit_sha256": protocol_audit_sha,
        "validation_protocol_content_gate": protocol_content_audit["gate"],
        "validation_protocol_content_gate_reasons": protocol_content_audit["reasons"],
        "validation_protocol_content_gate_reasons_csv": protocol_content_audit["reasons_csv"],
        "validation_protocol_content_item_count": protocol_content_audit["item_count"],
        "validation_protocol_content_required_item_count": protocol_content_audit["required_item_count"],
        "validation_protocol_content_audit_gate": protocol_content_audit["audit_gate"],
        "validation_protocol_content_missing_keys": protocol_content_audit["missing_keys"],
        "validation_protocol_content_missing_keys_csv": ";".join(protocol_content_audit["missing_keys"]),
        "validation_protocol_content_missing_status_keys": protocol_content_audit["missing_status_keys"],
        "validation_protocol_content_missing_status_keys_csv": ";".join(
            protocol_content_audit["missing_status_keys"]
        ),
        "validation_protocol_content_failed_keys": protocol_content_audit["failed_keys"],
        "validation_protocol_content_failed_keys_csv": ";".join(protocol_content_audit["failed_keys"]),
        "validation_protocol_content_risk_keys": protocol_content_audit["risk_keys"],
        "validation_protocol_content_risk_keys_csv": ";".join(protocol_content_audit["risk_keys"]),
        "validation_protocol_content_partial_keys": protocol_content_audit["partial_keys"],
        "validation_protocol_content_partial_keys_csv": ";".join(protocol_content_audit["partial_keys"]),
        "native_preconditions_af_csv_sha256": af_sha,
        "role_audits": role_audits,
        "native_preconditions_gate": "pass" if not reasons else "fail",
        "native_preconditions_gate_reasons": reasons,
        "native_preconditions_gate_reasons_csv": ";".join(reasons),
        "native_precondition_closure_gate": native_precondition_closure["gate"],
        "native_precondition_closed_stage_count": native_precondition_closure["closed_stage_count"],
        "native_precondition_failed_stage_count": native_precondition_closure["failed_stage_count"],
        "native_precondition_failed_stage_keys": native_precondition_closure["failed_stage_keys"],
        "native_precondition_failed_stage_keys_csv": native_precondition_closure["failed_stage_keys_csv"],
        "native_precondition_top_blocking_stage_key": native_precondition_closure["top_blocking_stage_key"],
        "native_precondition_top_blocking_stage_rank": native_precondition_closure["top_blocking_stage_rank"],
        "native_precondition_top_blocking_stage_reason_count": native_precondition_closure["top_blocking_stage_reason_count"],
        "native_precondition_top_blocking_stage_reasons": native_precondition_closure["top_blocking_stage_reasons"],
        "native_precondition_top_blocking_stage_reasons_csv": native_precondition_closure["top_blocking_stage_reasons_csv"],
        "native_precondition_closure": native_precondition_closure["stages"],
        "native_top_blocking_priority_rank": native_top_priority.get("rank"),
        "native_top_blocking_priority_key": native_top_priority.get("key", ""),
        "native_top_blocking_priority_reason_count": native_top_priority.get("reason_count"),
        "native_top_blocking_priority_reasons": native_top_priority.get("reasons", []),
        "native_top_blocking_priority_reasons_csv": ";".join(
            str(reason) for reason in native_top_priority.get("reasons", [])
        ),
        "native_top_blocking_priority_diagnosis": native_top_priority.get("diagnosis", ""),
        "native_top_blocking_priority_next_action": native_top_priority.get("next_action", ""),
        "native_diagnostic_priority_order": [
            "validation_protocol_content",
            "turbulent_inlet_method_and_u_k_preservation",
            "boundary_roughness_blockage",
            "time_averaging_stationarity",
            "coordinate_component_normalization",
            "systematic_bias_after_prerequisites",
        ],
        "native_diagnostic_priority": native_diagnostic_priority,
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0 if not reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
