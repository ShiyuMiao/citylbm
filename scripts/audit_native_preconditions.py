#!/usr/bin/env python3
"""Audit whether a native FluidX3D run package is a strict baseline.

This script does not run CFD and does not judge AIJ accuracy. It checks that a
native FluidX3D baseline manifest is explicit, hash-traceable, and consistent
with the current run package and final-window VTK audit before the result is
used to diagnose CityLBM accuracy.
"""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit native FluidX3D strict-baseline preconditions.")
    parser.add_argument("run_dir", help="Run/case directory containing native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--manifest", help="Optional explicit native_fluidx3d_baseline_manifest.json.")
    parser.add_argument("--metadata", help="case_metadata.json used for the run.")
    parser.add_argument("--runtime-audit", help="native_run_audit.json/read_vtk_audit.json for the final VTK window.")
    parser.add_argument("--af-csv", help="Official AF CSV used by the run.")
    parser.add_argument("--case", default="", help="Expected case label.")
    parser.add_argument("--software", default="", help="Expected software label.")
    parser.add_argument("--wind-vector", default="", help="Expected wind vector, e.g. 0,-1,0.")
    parser.add_argument("--u-ref", type=float, default=None, help="Expected reference wind speed in m/s.")
    parser.add_argument("--u-ref-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--expected-vtk-pattern", default="u-*.vtk")
    parser.add_argument("--average-last-n", type=int, default=10)
    parser.add_argument("--min-avg-frames", type=int, default=10)
    parser.add_argument("--min-avg-step-span", type=int, default=1000)
    parser.add_argument("--out", required=True, help="Output audit JSON.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256_file(path: Optional[Path]) -> str:
    if not path or not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


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


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.exists():
        raise SystemExit(f"run_dir does not exist: {run_dir}")
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else find_first(run_dir, ["native_fluidx3d_baseline_manifest.json"])
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else find_first(run_dir, ["case_metadata.json"])
    runtime_audit_path = Path(args.runtime_audit).expanduser().resolve() if args.runtime_audit else find_first(run_dir, ["native_run_audit.json", "read_vtk_audit.json"])
    setup_path = find_first(run_dir, ["setup.cpp"])
    defines_path = find_first(run_dir, ["defines.hpp"])
    domain_origin_path = find_first(run_dir, ["domain_origin.json"])
    protocol_audit_path = find_first(run_dir, ["validation_protocol_audit.json"])

    manifest = read_json(manifest_path)
    metadata = read_json(metadata_path)
    runtime_audit = read_json(runtime_audit_path)
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
    if not frame_candidates or min(frame_candidates) < args.min_avg_frames:
        reasons.append("planned_vtk_frame_count_below_minimum")

    runtime_pattern = str(runtime_audit.get("vtk_pattern") or "").strip()
    if not runtime_audit:
        reasons.append("runtime_audit_missing")
    elif runtime_pattern != args.expected_vtk_pattern:
        reasons.append("runtime_vtk_pattern_mismatch")

    runtime_avg = as_int(runtime_audit.get("average_last_n_requested"))
    if runtime_avg is None:
        runtime_avg = as_int(runtime_audit.get("averaged_frame_count"))
    if runtime_avg is None or runtime_avg < args.min_avg_frames or runtime_avg != args.average_last_n:
        reasons.append("runtime_average_window_mismatch_or_too_short")

    runtime_step_span = as_int(runtime_audit.get("source_step_span"))
    planned_span = expected_final_window_span(
        shared_steps or metadata_steps,
        shared_save_interval or metadata_save_interval,
        as_int(runtime_audit.get("requested_vtk_save_start_step")),
        args.average_last_n,
    )
    if runtime_step_span is None or runtime_step_span < args.min_avg_step_span:
        reasons.append("runtime_average_step_span_too_short")
    if planned_span is None or planned_span < args.min_avg_step_span:
        reasons.append("planned_average_step_span_too_short")

    time_gate = str(runtime_audit.get("time_averaging_gate") or "").strip().lower()
    requested_frame_gate = str(runtime_audit.get("requested_vtk_frame_gate") or "").strip().lower()
    time_average_gate = "pass" if time_gate == "pass" and requested_frame_gate == "pass" else "fail"
    if time_average_gate != "pass":
        reasons.append("runtime_time_averaging_gate_not_pass")

    expected_vector = parse_vector(args.wind_vector)
    actual_vector = shared_wind_vector(shared)
    wind_delta = vector_delta(actual_vector, expected_vector) if expected_vector else None
    if expected_vector and (wind_delta is None or wind_delta > args.wind_vector_tolerance):
        reasons.append("wind_vector_mismatch")

    shared_u_ref = as_float(shared.get("ReferenceWindSpeedMps"))
    metadata_u_ref = as_float(metadata.get("ReferenceWindSpeedMps") or metadata.get("WindSpeed"))
    u_ref = shared_u_ref if shared_u_ref is not None else metadata_u_ref
    if args.u_ref is not None and (u_ref is None or abs(u_ref - args.u_ref) > args.u_ref_tolerance):
        reasons.append("uref_mismatch")

    af_csv = Path(args.af_csv).expanduser().resolve() if args.af_csv else None
    af_sha = sha256_file(af_csv)
    manifest_af_sha = str(shared.get("WindProfileCsvSha256") or "").strip().lower()
    if af_csv:
        if not af_sha:
            reasons.append("af_csv_missing")
        elif manifest_af_sha and manifest_af_sha != af_sha:
            reasons.append("af_csv_hash_mismatch")
    if str(shared.get("WindProfile") or "").strip().lower() != "customtable":
        reasons.append("wind_profile_not_customtable")

    protocol_identity_gate = "pass" if not any(
        reason in reasons
        for reason in [
            "wind_vector_mismatch",
            "uref_mismatch",
            "af_csv_missing",
            "af_csv_hash_mismatch",
            "wind_profile_not_customtable",
            "metadata_manifest_time_steps_mismatch",
            "metadata_manifest_save_interval_mismatch",
        ]
    ) else "fail"

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
        "expected_vtk_pattern": args.expected_vtk_pattern,
        "runtime_vtk_pattern": runtime_pattern,
        "average_last_n_required": args.average_last_n,
        "runtime_average_last_n": runtime_avg,
        "min_avg_frames": args.min_avg_frames,
        "min_avg_step_span": args.min_avg_step_span,
        "planned_frame_count_min": min(frame_candidates) if frame_candidates else None,
        "planned_final_window_step_span": planned_span,
        "runtime_source_step_span": runtime_step_span,
        "runtime_time_averaging_gate": time_gate,
        "runtime_requested_vtk_frame_gate": requested_frame_gate,
        "native_preconditions_protocol_identity_gate": protocol_identity_gate,
        "native_preconditions_time_average_gate": time_average_gate,
        "native_preconditions_manifest_sha256": sha256_file(manifest_path),
        "native_preconditions_setup_sha256": setup_sha,
        "native_preconditions_defines_sha256": defines_sha,
        "native_preconditions_metadata_sha256": metadata_sha,
        "native_preconditions_runtime_audit_sha256": runtime_audit_sha,
        "native_preconditions_af_csv_sha256": af_sha,
        "role_audits": role_audits,
        "native_preconditions_gate": "pass" if not reasons else "fail",
        "native_preconditions_gate_reasons": reasons,
        "native_preconditions_gate_reasons_csv": ";".join(reasons),
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return 0 if not reasons else 2


if __name__ == "__main__":
    raise SystemExit(main())
