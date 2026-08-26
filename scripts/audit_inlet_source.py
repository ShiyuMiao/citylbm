#!/usr/bin/env python3
"""Audit generated setup.cpp inlet-method evidence.

This script does not run CFD. It prevents paper-grade validation from relying
only on metadata labels such as "synthetic-eddy" or "digital-filter" by
checking whether the generated source contains the expected inlet code and
whether that code is distribution-consistent or only velocity-field forcing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


MINIMUM_RECOMMENDED_SPECTRAL_MODE_COUNT = 32
STRICT_BASELINE_SPECTRAL_MODE_COUNT = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated FluidX3D setup.cpp inlet implementation evidence.")
    parser.add_argument("--setup", required=True, help="Generated setup.cpp path.")
    parser.add_argument("--defines", help="Optional generated defines.hpp path.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--out", required=True, help="Output inlet_source_audit.json.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def read_optional_text(path: Optional[Path]) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def metadata_value(metadata: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def metadata_nested_value(metadata: Dict[str, Any], *paths: Sequence[str]) -> str:
    for path in paths:
        current: Any = metadata
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        if current not in (None, ""):
            return str(current)
    return ""


def resolve_metadata_path(raw: str, metadata_path: Optional[Path]) -> Optional[Path]:
    text = str(raw or "").strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute() and metadata_path is not None:
        path = metadata_path.parent / path
    return path.resolve()


def nested_bool(metadata: Dict[str, Any], *keys: str) -> Optional[bool]:
    current: Any = metadata
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    if isinstance(current, bool):
        return current
    if isinstance(current, (int, float)):
        return bool(current)
    text = str(current).strip().lower()
    if text in {"true", "1", "yes", "y", "pass", "enabled"}:
        return True
    if text in {"false", "0", "no", "n", "fail", "disabled"}:
        return False
    return None


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def first_int_regex(text: str, pattern: str) -> Optional[int]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def first_float_regex(text: str, pattern: str) -> Optional[float]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return None
    try:
        return float(str(match.group(1)).rstrip("fF"))
    except (TypeError, ValueError):
        return None


def parse_metadata_vector(value: Any) -> List[float]:
    if isinstance(value, list):
        parsed: List[float] = []
        for item in value:
            try:
                parsed.append(float(item))
            except (TypeError, ValueError):
                return []
        return parsed if len(parsed) == 3 else []
    if isinstance(value, dict):
        keys = ("X", "Y", "Z") if any(key in value for key in ("X", "Y", "Z")) else ("x", "y", "z")
        return parse_metadata_vector([value.get(key) for key in keys])
    if isinstance(value, str):
        parts = [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
        return parse_metadata_vector(parts)
    return []


def parse_setup_wind_vector(code: str) -> List[float]:
    values = [
        first_float_regex(code, rf"\bconst\s+float\s+dir_{axis}\s*=\s*([-+0-9.eEfF]+)\s*;")
        for axis in ("x", "y", "z")
    ]
    if any(value is None for value in values):
        return []
    return [float(value) for value in values if value is not None]


def vector_close(actual: Sequence[float], expected: Sequence[float], tolerance: float = 1.0e-6) -> bool:
    return len(actual) == len(expected) == 3 and all(abs(a - b) <= tolerance for a, b in zip(actual, expected))


def strip_cpp_string_literals(text: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)


def distribution_reconstruction_evidence(code: str) -> Dict[str, Any]:
    distribution_write_pattern = re.compile(
        r"\blbm\.(?:f|f0|feq|df|ddf)\s*(?:\[[^\]]+\]|\.[A-Za-z_][A-Za-z0-9_]*\s*\[[^\]]+\])\s*=",
        flags=re.IGNORECASE,
    )
    contextual_count = 0
    write_count = 0
    for match in distribution_write_pattern.finditer(code):
        write_count += 1
        window = code[max(0, match.start() - 700) : min(len(code), match.end() + 900)]
        has_inlet_context = contains_any(
            window,
            [
                "TYPE_E",
                "syntheticTurbulentInlet",
                "windProfile",
                "inlet",
                "side_inlet",
                "sideInlet",
            ],
        )
        has_reconstruction_context = contains_any(
            window,
            [
                "calculate_f_eq",
                "feq",
                "stress_ddf",
                "reconstruct",
                "reconstruction",
                "equilibrium",
            ],
        )
        if has_inlet_context and has_reconstruction_context:
            contextual_count += 1
    return {
        "distribution_write_count": write_count,
        "inlet_distribution_reconstruction_count": contextual_count,
        "has_distribution_function_write": write_count > 0,
        "has_inlet_distribution_reconstruction": contextual_count > 0,
    }


def strip_cpp_comments(text: str) -> str:
    """Remove C/C++ comments while preserving strings and line structure."""
    output: List[str] = []
    index = 0
    in_string = False
    in_char = False
    escaped = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if in_char:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "'":
                in_char = False
            index += 1
            continue

        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue

        if char == "'":
            in_char = True
            output.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            output.append("\n")
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and not (text[index] == "*" and text[index + 1] == "/"):
                if text[index] in "\r\n":
                    output.append("\n")
                index += 1
            index += 2
            continue

        output.append(char)
        index += 1

    return "".join(output)


def main() -> int:
    args = parse_args()
    setup_path = Path(args.setup).expanduser().resolve()
    defines_path = Path(args.defines).expanduser().resolve() if args.defines else None
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else None
    out_path = Path(args.out).expanduser().resolve()
    metadata = read_json(metadata_path)

    reasons: List[str] = []
    if not setup_path.exists():
        reasons.append("setup_cpp_missing")
        source = ""
        setup_hash = ""
    else:
        source = read_optional_text(setup_path)
        setup_hash = sha256(setup_path)

    audited_source = strip_cpp_comments(source)
    implementation_source = strip_cpp_string_literals(audited_source)
    defines_source = read_optional_text(defines_path)
    audited_defines_source = strip_cpp_comments(defines_source)
    implementation_defines_source = strip_cpp_string_literals(audited_defines_source)
    audited_source_lower = audited_source.lower()
    implementation_source_lower = implementation_source.lower()
    runtime_diagnostics_source_lower = audited_source_lower
    audited_source_hash = hashlib.sha256(audited_source.encode("utf-8")).hexdigest().upper() if audited_source else ""
    defines_hash = sha256(defines_path) if defines_path and defines_path.exists() else ""
    audited_defines_source_hash = (
        hashlib.sha256(audited_defines_source.encode("utf-8")).hexdigest().upper() if audited_defines_source else ""
    )
    metadata_method = metadata_value(metadata, "SyntheticTurbulentInletMethod", "TurbulenceMethod")
    metadata_treatment = metadata_value(metadata, "SyntheticTurbulentInletDistributionTreatment")
    metadata_class = metadata_value(metadata, "PaperGradeInletMethodClass", "InletMethodClass")
    metadata_reynolds_stress_treatment = metadata_value(
        metadata,
        "InletReynoldsStressTreatment",
        "ReynoldsStressAssumption",
        "SyntheticTurbulentInletReynoldsStressTreatment",
    )
    metadata_wind_vector = parse_metadata_vector(
        metadata.get("WindDirectionUnitVector")
        or metadata.get("WindVector")
        or metadata.get("WindDirectionVector")
    )
    setup_wind_vector = parse_setup_wind_vector(implementation_source)
    wind_vector_source_matches_metadata = (
        not metadata_wind_vector
        or not setup_wind_vector
        or vector_close(setup_wind_vector, metadata_wind_vector)
    )
    if metadata_wind_vector and setup_wind_vector and not wind_vector_source_matches_metadata:
        reasons.append("setup_cpp_wind_vector_mismatch_metadata")
    metadata_length_scale_gate = metadata_value(
        metadata,
        "SyntheticTurbulentInletLengthScaleGate",
        "SyntheticTurbulenceLengthScaleGate",
        "InletLengthScaleGate",
    ).strip().lower()
    length_scale_evidence_json_raw = metadata_value(
        metadata,
        "TurbulenceLengthScaleEvidenceJson",
        "SyntheticTurbulenceLengthScaleEvidenceJson",
        "LengthScaleEvidenceJson",
    ) or metadata_nested_value(
        metadata,
        ("TurbulenceLengthScale", "EvidenceJsonPath"),
        ("SyntheticTurbulenceLengthScale", "EvidenceJsonPath"),
    )
    length_scale_evidence_sha_expected = metadata_value(
        metadata,
        "TurbulenceLengthScaleEvidenceSha256",
        "SyntheticTurbulenceLengthScaleEvidenceSha256",
        "LengthScaleEvidenceSha256",
    ) or metadata_nested_value(
        metadata,
        ("TurbulenceLengthScale", "EvidenceJsonSha256"),
        ("SyntheticTurbulenceLengthScale", "EvidenceJsonSha256"),
    )
    length_scale_evidence_json_path = resolve_metadata_path(length_scale_evidence_json_raw, metadata_path)
    length_scale_evidence_json_exists = bool(length_scale_evidence_json_path and length_scale_evidence_json_path.is_file())
    length_scale_evidence_json_sha = (
        sha256(length_scale_evidence_json_path) if length_scale_evidence_json_exists and length_scale_evidence_json_path else ""
    )
    length_scale_evidence_hash_matches = (
        not length_scale_evidence_sha_expected
        or length_scale_evidence_json_sha.lower() == length_scale_evidence_sha_expected.strip().lower()
    )
    length_scale_evidence = read_json(length_scale_evidence_json_path) if length_scale_evidence_json_exists else {}
    length_scale_evidence_gate = str(length_scale_evidence.get("gate") or "").strip().lower()
    length_scale_evidence_paper_gate = str(length_scale_evidence.get("paper_grade_gate") or "").strip().lower()
    length_scale_evidence_source_sha = str(length_scale_evidence.get("source_sha256") or "").strip()
    has_bound_length_scale_evidence = (
        length_scale_evidence_json_exists
        and length_scale_evidence_hash_matches
        and length_scale_evidence_gate == "pass"
        and length_scale_evidence_paper_gate == "pass"
        and bool(length_scale_evidence_source_sha)
    )
    synthetic_requested = any(
        token in " ".join([metadata_method, metadata_treatment, metadata_class]).lower()
        for token in ["synthetic", "stg", "digital", "filter", "sem", "dfm", "precursor", "recycling"]
    )
    synthetic_enabled = nested_bool(metadata, "SyntheticEddy", "Enabled")
    if synthetic_enabled is True:
        synthetic_requested = True

    selected_method_text = " ".join([metadata_method, metadata_treatment, metadata_class]).lower()
    synthetic_eddy_selected = (
        "synthetic-eddy" in selected_method_text
        or "synthetic_eddy" in selected_method_text
        or has_regex(implementation_source, r"\bconst\s+uint\s+turbulence_method\s*=\s*5u\b")
    )
    digital_filter_selected = (
        "digital-filter" in selected_method_text
        or "digital_filter" in selected_method_text
        or "dfm" in selected_method_text
        or has_regex(implementation_source, r"\bconst\s+uint\s+turbulence_method\s*=\s*(3u|4u|7u)\b")
    )
    if synthetic_eddy_selected or digital_filter_selected:
        synthetic_requested = True

    has_custom_table = "profile_z_m" in implementation_source_lower and "profile_u_lbm" in implementation_source_lower
    has_k_profile = "profile_k_lbm" in implementation_source_lower
    has_runtime_inlet_diagnostics_file_evidence = contains_any(
        audited_source,
        [
            "citylbm_inlet_diagnostics_csv",
            "inlet_diagnostics_csv",
            "synthetic_turbulent_inlet_diagnostics",
            "inlet_turbulence_stats",
            "casea_inlet_turbulence_stats",
            "casee_inlet_turbulence_stats",
        ],
    )
    has_runtime_inlet_diagnostics_writer_evidence = (
        contains_any(implementation_source, ["std::ofstream", "ofstream"])
        and contains_any(
            implementation_source,
            [
                "writeInletDiagnostics",
                "writeSyntheticTurbulentInletDiagnostics",
                "inlet_csv",
                "inlet_diag",
            ],
        )
    )
    has_runtime_inlet_diagnostics_csv_source = (
        has_runtime_inlet_diagnostics_file_evidence
        and has_runtime_inlet_diagnostics_writer_evidence
    )
    runtime_inlet_diagnostics_required_fields = [
        "target_k_m2s2",
        "target_r11_m2s2",
        "target_r22_m2s2",
        "target_r33_m2s2",
        "target_r12_m2s2",
        "target_r13_m2s2",
        "target_r23_m2s2",
        "mean_u_mps",
        "u_rms_mps",
        "v_rms_mps",
        "w_rms_mps",
        "k_m2s2",
        "measured_r11_m2s2",
        "measured_r22_m2s2",
        "measured_r33_m2s2",
        "measured_r12_m2s2",
        "measured_r13_m2s2",
        "measured_r23_m2s2",
        "effective_sample_z_m",
    ]
    runtime_inlet_diagnostics_present_fields = [
        field for field in runtime_inlet_diagnostics_required_fields if field in runtime_diagnostics_source_lower
    ]
    has_runtime_inlet_diagnostics_required_fields = (
        len(runtime_inlet_diagnostics_present_fields) == len(runtime_inlet_diagnostics_required_fields)
    )
    runtime_inlet_diagnostics_source_gate = (
        "pass"
        if has_runtime_inlet_diagnostics_csv_source and has_runtime_inlet_diagnostics_required_fields
        else "fail"
    )
    has_profile_origin_z_m = "profile_origin_z_m" in implementation_source_lower
    has_origin_aware_profile_height = (
        has_profile_origin_z_m
        and has_regex(
            implementation_source,
            r"z_m\s*=\s*profile_origin_z_m\s*\+\s*\(\s*\(?\s*float\s*\)?\s*z_cell\s*\+\s*0\.5f\s*\)\s*\*",
        )
    )
    has_native_synthetic_eddy_function = (
        has_regex(implementation_source, r"\bupdateSyntheticEddyPlane\s*=\s*\[")
        or has_regex(implementation_source, r"\bupdateSyntheticEddyPlane\s*\(")
    )
    has_native_turbulent_wind_function = has_regex(implementation_source, r"\bturbulentWind\s*=\s*\[")
    has_native_apply_inlet_function = (
        has_regex(implementation_source, r"\bapplyInlet\s*=\s*\[")
        or has_regex(implementation_source, r"\bapplyInlet\s*\(")
    )
    has_native_synthetic_eddy_population = contains_any(
        implementation_source,
        [
            "synthetic_eddy_count",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
            "synthetic_eddy_recycle_lx_cells",
        ],
    )
    has_native_synthetic_eddy_shape = contains_any(
        implementation_source,
        ["compactCosine", "periodicDistance", "signedHash", "hash01"],
    )
    has_native_synthetic_eddy_refresh = (
        has_regex(implementation_source, r"updateSyntheticEddyPlane\s*\(\s*t_step\s*\)")
        and (
            has_regex(implementation_source, r"updateTemporalFilter\s*\(\s*t_step\s*\)")
            or has_regex(implementation_source, r"updateDigitalFilter\s*\(\s*t_step\s*\)")
        )
    )
    native_stg_mode_count = first_int_regex(
        implementation_source,
        r"synthetic_eddy_count\s*=\s*(\d+)",
    )
    has_native_synthetic_eddy_structure_evidence = (
        synthetic_eddy_selected
        and has_native_synthetic_eddy_function
        and has_native_turbulent_wind_function
        and has_native_apply_inlet_function
        and has_native_synthetic_eddy_population
        and has_native_synthetic_eddy_shape
    )
    has_native_synthetic_eddy_temporal_refresh_evidence = (
        has_native_synthetic_eddy_structure_evidence
        and has_native_synthetic_eddy_refresh
    )
    has_native_synthetic_eddy_evidence = has_native_synthetic_eddy_temporal_refresh_evidence
    has_stg_function = (
        "applysyntheticturbulentinlet" in implementation_source_lower
        or has_native_synthetic_eddy_structure_evidence
    )
    has_stg_refresh_loop = (
        count_regex(implementation_source, r"applySyntheticTurbulentInlet\s*\(") >= 2
        or (has_native_apply_inlet_function and has_native_synthetic_eddy_refresh)
    )
    has_velocity_field_write = contains_any(implementation_source, ["lbm.u.x", "lbm.u.y", "lbm.u.z"])
    has_three_component_velocity_write = all(
        contains_any(implementation_source, [token])
        for token in ["lbm.u.x", "lbm.u.y", "lbm.u.z"]
    )
    has_type_e_boundary_flag = contains_any(implementation_source, ["TYPE_E"])
    has_flags_device_upload = has_regex(implementation_source, r"\blbm\.flags\.write_to_device\s*\(")
    has_u_device_upload = has_regex(implementation_source, r"\blbm\.u\.write_to_device\s*\(")
    has_equilibrium_boundaries_define = has_regex(
        implementation_defines_source,
        r"^\s*#\s*define\s+EQUILIBRIUM_BOUNDARIES\b",
    )
    has_reconstruct_inlet_stress_ddf_define = has_regex(
        implementation_defines_source,
        r"^\s*#\s*define\s+RECONSTRUCT_INLET_STRESS_DDF\b",
    )
    has_reconstruct_equilibrium_ddf_define = has_regex(
        implementation_defines_source,
        r"^\s*#\s*define\s+RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF\b",
    )
    has_casea_device_sem_inlet_define = has_regex(
        implementation_defines_source,
        r"^\s*#\s*define\s+CASEA_DEVICE_SEM_INLET\b",
    )
    has_casea_device_sem_stress_ddf_define = has_regex(
        implementation_defines_source,
        r"^\s*#\s*define\s+CASEA_DEVICE_SEM_STRESS_DDF\b",
    )
    has_reconstruct_inlet_stress_call = has_regex(
        implementation_source,
        r"\blbm\s*\.\s*reconstruct_inlet_stress_boundaries\s*\(",
    )
    has_reconstruct_equilibrium_call = has_regex(
        implementation_source,
        r"\blbm\s*\.\s*reconstruct_equilibrium_boundaries\s*\(",
    )
    has_casea_device_sem_inlet_call = has_regex(
        implementation_source,
        r"\blbm\s*\.\s*apply_casea_sem_inlet\s*\(",
    )
    has_casea_device_sem_stress_route = (
        has_casea_device_sem_inlet_define
        and has_casea_device_sem_stress_ddf_define
        and has_casea_device_sem_inlet_call
    )
    has_type_e_inlet_stress_reconstruction_route = (
        (
            has_reconstruct_inlet_stress_ddf_define
            and has_reconstruct_inlet_stress_call
            and has_type_e_boundary_flag
            and has_velocity_field_write
            and has_u_device_upload
        )
        or has_casea_device_sem_stress_route
    )
    has_type_e_equilibrium_reconstruction_route = (
        has_reconstruct_equilibrium_ddf_define
        and has_reconstruct_equilibrium_call
        and has_type_e_boundary_flag
        and has_velocity_field_write
        and has_u_device_upload
    )
    has_type_e_equilibrium_boundary_route = (
        has_equilibrium_boundaries_define
        and has_type_e_boundary_flag
        and has_velocity_field_write
        and has_u_device_upload
    )
    distribution_evidence = distribution_reconstruction_evidence(implementation_source)
    has_distribution_write = distribution_evidence["has_distribution_function_write"]
    has_direct_inlet_distribution_reconstruction = distribution_evidence["has_inlet_distribution_reconstruction"]
    has_inlet_distribution_reconstruction = (
        has_direct_inlet_distribution_reconstruction
        or has_type_e_inlet_stress_reconstruction_route
        or has_type_e_equilibrium_reconstruction_route
    )
    has_digital_filter_token = contains_any(implementation_source, ["digital_filter", "digital-filter", "dfm", "filter kernel"])
    has_sem_token = contains_any(
        implementation_source,
        [
            "synthetic_eddy_method",
            "sem_distribution",
            "synthetic eddy method",
            "synthetic_eddy_count",
            "updateSyntheticEddyPlane",
        ],
    )
    has_precursor_token = contains_any(implementation_source, ["precursor", "recycling_rescaling", "recycling-rescaling"])
    has_legacy_digital_filter_kernel = (
        has_regex(implementation_source, r"\bauto\s+smoothPlane\s*=\s*\[\&\]\s*\(")
        and contains_any(implementation_source, ["digital_filter_radius", "digital_filter_alpha", "weight_sum"])
    )
    has_legacy_digital_filter_state = (
        has_regex(implementation_source, r"\bauto\s+updateDigitalFilter\s*=\s*\[\&\]\s*\(\s*uint\s+t_step\s*\)")
        and all(contains_any(implementation_source, [token]) for token in ["df_ru", "df_rv", "df_rw"])
        and all(contains_any(implementation_source, [token]) for token in ["df_next_u", "df_next_v", "df_next_w"])
        and contains_any(implementation_source, ["df_initialized", "digital_filter_time_alpha", "digital_filter_time_beta"])
    )
    has_digital_filter = (
        has_regex(implementation_source, r"\b\w*(digital_filter|digitalfilter|dfm)\w*\s*\(")
        or has_regex(implementation_source, r"\b(filter_kernel|filterKernel)\w*\s*(\[|=|\{)")
        or has_regex(implementation_source, r"\bupdateDigitalFilter\s*\(")
    )
    has_digital_filter_kernel = has_regex(
        implementation_source,
        r"\b\w*(digital_filter_kernel|digitalFilterKernel|filter_kernel|filterKernel|dfm_kernel|dfmKernel)\w*\s*(\[|=|\{|\()",
    ) or has_legacy_digital_filter_kernel
    has_digital_filter_state = contains_any(
        implementation_source,
        [
            "filtered_random_field",
            "filter_state",
            "digital_filter_state",
            "temporal_filter",
            "spatial_filter",
            "inlet_fluctuation_field",
            "streamwise_filter_buffer",
            "filter_history",
        ],
    ) or has_legacy_digital_filter_state
    has_sem = (
        has_regex(implementation_source, r"\b\w*(synthetic_eddy|syntheticEddy|sem_distribution|semDistribution)\w*\s*\(")
        or has_regex(implementation_source, r"\b(sem_eddy|semEddy|eddy_center|eddyCenter)\w*\s*(\[|=|\{)")
        or has_native_synthetic_eddy_evidence
    )
    has_sem_eddy_population = contains_any(
        implementation_source,
        [
            "eddy_center",
            "eddyCenter",
            "eddy_radius",
            "eddyRadius",
            "eddy_strength",
            "eddyStrength",
            "eddy_lifetime",
            "eddyLifetime",
            "sem_eddy",
            "semEddy",
            "synthetic_eddy_count",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
        ],
    )
    has_sem_eddy_update_evidence = (
        has_regex(
            implementation_source,
            r"\b(?:sem_eddy|semEddy)\s*\[[^\]]+\]\s*\.\s*(?:eddy_center|eddyCenter|eddy_radius|eddyRadius|eddy_strength|eddyStrength|eddy_lifetime|eddyLifetime)\s*=",
        )
        or has_native_synthetic_eddy_evidence
    )
    has_native_synthetic_eddy_velocity_coupling = (
        has_native_synthetic_eddy_evidence
        and all(contains_any(implementation_source, [token]) for token in ["df_ru", "df_rv", "df_rw"])
        and all(
            contains_any(implementation_source, [token])
            for token in ["profile_u_rms_lbm", "profile_v_rms_lbm", "profile_w_rms_lbm"]
        )
        and has_three_component_velocity_write
    )
    has_sem_eddy_velocity_coupling_evidence = (
        has_regex(
            implementation_source,
            r"\b(?:fluct|u_in|ux|uy|uz)[A-Za-z0-9_]*\b[^;\n=]*=[^;\n]*(?:sem_eddy|semEddy)\s*\[[^\]]+\]\s*\.",
        )
        or has_regex(
            implementation_source,
            r"\b(?:fluct|u_in|ux|uy|uz)[A-Za-z0-9_]*\b\s*(?:\+=|-=|\*=|/=)[^;\n]*(?:sem_eddy|semEddy)\s*\[[^\]]+\]\s*\.",
        )
        or has_native_synthetic_eddy_velocity_coupling
    )
    has_precursor = has_regex(
        implementation_source,
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|recycleRescale)\w*\s*\(",
    )
    has_precursor_recycling_field = contains_any(
        implementation_source,
        [
            "precursor_velocity",
            "precursorVelocity",
            "precursor_field",
            "precursorField",
            "recycling_plane",
            "recyclingPlane",
            "recycle_plane",
            "recyclePlane",
            "recycling_buffer",
            "recyclingBuffer",
            "rescale_profile",
            "rescaleProfile",
            "inflow_database",
            "inflowDatabase",
            "stored_inflow",
            "storedInflow",
            "precursor_vtk",
            "precursorVtk",
        ],
    )
    has_distribution_consistent_digital_filter = (
        has_digital_filter
        and has_digital_filter_kernel
        and has_digital_filter_state
        and has_inlet_distribution_reconstruction
    )
    has_distribution_consistent_sem = (
        has_sem
        and has_sem_eddy_population
        and has_sem_eddy_update_evidence
        and has_sem_eddy_velocity_coupling_evidence
        and has_inlet_distribution_reconstruction
    )
    has_distribution_consistent_precursor = (
        has_precursor
        and has_precursor_recycling_field
        and has_inlet_distribution_reconstruction
    )
    advanced_token_only = (
        (has_digital_filter_token and not has_digital_filter)
        or (has_sem_token and not has_sem)
        or (has_precursor_token and not has_precursor)
    )
    has_spectral_modes = contains_any(
        implementation_source,
        [
            "citylbm_stg_mode_count",
            "citylbm_mode_wave",
            "citylbm_mode_amplitude",
        ],
    )
    stg_mode_count = first_int_regex(
        implementation_source,
        r"citylbm_stg_mode_count\s*=\s*(\d+)",
    )
    effective_stg_mode_count = stg_mode_count if stg_mode_count is not None else native_stg_mode_count
    spectral_mode_count_gate = (
        "not_applicable"
        if effective_stg_mode_count is None
        else "pass"
        if effective_stg_mode_count >= STRICT_BASELINE_SPECTRAL_MODE_COUNT
        else "diagnostic_only_low_spectral_mode_count"
    )
    has_taylor_advection = contains_any(
        implementation_source,
        ["advected_x", "advected_y", "advected_z", "frozen-turbulence", "x0 - adv"],
    )
    has_transverse_projection = contains_any(
        implementation_source,
        [
            "ak*kx/kk",
            "ak * kx / kk",
            "projected normal to their wave vector",
            "divergence-reduced",
        ],
    )
    has_citylbm_three_component_fluctuation = (
        all(
            has_regex(implementation_source, pattern)
            for pattern in [
                r"\bfluct_x\s*\+=",
                r"\bfluct_y\s*\+=",
                r"\bfluct_z\s*\+=",
            ]
        )
        and all(
            has_regex(implementation_source, pattern)
            for pattern in [
                r"mean\.x\s*\+\s*sigma\s*\*\s*fluct_x",
                r"mean\.y\s*\+\s*sigma\s*\*\s*fluct_y",
                r"mean\.z\s*\+\s*sigma\s*\*\s*fluct_z",
            ]
        )
    )
    has_three_component_fluctuation_evidence = (
        has_citylbm_three_component_fluctuation
        or has_native_synthetic_eddy_evidence
    )
    has_rms_profile_driven_three_component_native_stg = (
        has_native_synthetic_eddy_evidence
        and all(
            contains_any(implementation_source, [token])
            for token in ["profile_u_rms_lbm", "profile_v_rms_lbm", "profile_w_rms_lbm"]
        )
        and all(
            contains_any(implementation_source, [token])
            for token in ["u_rms*ru", "v_rms*rv", "w_rms*rw"]
        )
    )
    has_k_driven_three_component_stg = (
        (
            has_k_profile
            and contains_any(
                implementation_source,
                ["sigma = sqrtf", "sqrtf(0.6666667f * k_lbm)", "sqrt(2.0f * profile_k_lbm"],
            )
        )
        or has_rms_profile_driven_three_component_native_stg
    ) and has_three_component_fluctuation_evidence
    has_component_phase_decorrelation = (
        has_regex(implementation_source, r"\bwave_x\s*=.*sinf\s*\(")
        and has_regex(implementation_source, r"\bwave_y\s*=.*sinf\s*\(")
        and has_regex(implementation_source, r"\bwave_z\s*=.*sinf\s*\(")
        and has_regex(implementation_source, r"citylbm_mode_phase\s*\(\s*m\s*,\s*0\s*\)")
        and has_regex(implementation_source, r"citylbm_mode_phase\s*\(\s*m\s*,\s*1\s*\)")
        and has_regex(implementation_source, r"citylbm_mode_phase\s*\(\s*m\s*,\s*2\s*\)")
    ) or has_native_synthetic_eddy_evidence
    has_temporal_filter_state = (
        contains_any(
            implementation_source,
            [
                "citylbm_stg_temporal_ar1_rho",
                "citylbm_stg_temporal_ar1_innovation_scale",
                "deterministic_ar1_phase_blend",
            ],
        )
        and contains_any(
            implementation_source,
            [
                "citylbm_stg_prev_t_step",
                "previous_phase",
                "prev_advected_x",
                "prev_advected_y",
                "prev_advected_z",
            ],
        )
    ) or has_native_synthetic_eddy_evidence
    has_distribution_consistent_stg_lite = (
        has_stg_function
        and has_velocity_field_write
        and has_inlet_distribution_reconstruction
        and (
            has_spectral_modes
            or has_taylor_advection
            or has_transverse_projection
            or has_native_synthetic_eddy_evidence
        )
    )
    has_length_scale = contains_any(
        implementation_source,
        [
            "correlation_length",
            "citylbm_stg_lx",
            "citylbm_stg_corr_cells",
            "length_scale",
            "correlation cells",
            "synthetic_eddy_lx_cells",
            "synthetic_eddy_ly_cells",
            "synthetic_eddy_lz_cells",
            "digital_filter_radius",
            "turbulence_length_h",
        ],
    )
    reynolds_stress_diagonal_patterns = [
        r"\b(profile_r11_lbm|r11_profile|R11)\b",
        r"\b(profile_r22_lbm|r22_profile|R22)\b",
        r"\b(profile_r33_lbm|r33_profile|R33)\b",
    ]
    reynolds_stress_offdiagonal_patterns = [
        r"\b(profile_r12_lbm|r12_profile|R12)\b",
        r"\b(profile_r13_lbm|r13_profile|R13)\b",
        r"\b(profile_r23_lbm|r23_profile|R23)\b",
    ]
    has_reynolds_stress_diagonal_source_evidence = all(
        has_regex(implementation_source, pattern) for pattern in reynolds_stress_diagonal_patterns
    )
    rms_profile_patterns = [
        r"\bprofile_u_rms_lbm\b",
        r"\bprofile_v_rms_lbm\b",
        r"\bprofile_w_rms_lbm\b",
    ]
    rms_profile_usage_patterns = [
        r"\bprofile_u_rms_lbm\s*\[[^\]]+\]",
        r"\bprofile_v_rms_lbm\s*\[[^\]]+\]",
        r"\bprofile_w_rms_lbm\s*\[[^\]]+\]",
    ]
    has_measured_diagonal_rms_source_evidence = all(
        has_regex(implementation_source, pattern) for pattern in rms_profile_patterns
    )
    has_measured_diagonal_rms_usage_evidence = all(
        has_regex(implementation_source, pattern) for pattern in rms_profile_usage_patterns
    )
    has_reynolds_stress_offdiagonal_source_evidence = all(
        has_regex(implementation_source, pattern) for pattern in reynolds_stress_offdiagonal_patterns
    )
    has_reynolds_stress_full_tensor_source_evidence = (
        has_reynolds_stress_diagonal_source_evidence and has_reynolds_stress_offdiagonal_source_evidence
    )
    reynolds_stress_diagonal_usage_patterns = [
        r"\b(profile_r11_lbm|r11_profile)\s*\[[^\]]+\]",
        r"\b(profile_r22_lbm|r22_profile)\s*\[[^\]]+\]",
        r"\b(profile_r33_lbm|r33_profile)\s*\[[^\]]+\]",
    ]
    reynolds_stress_offdiagonal_usage_patterns = [
        r"\b(profile_r12_lbm|r12_profile)\s*\[[^\]]+\]",
        r"\b(profile_r13_lbm|r13_profile)\s*\[[^\]]+\]",
        r"\b(profile_r23_lbm|r23_profile)\s*\[[^\]]+\]",
    ]
    has_reynolds_stress_diagonal_usage_evidence = all(
        has_regex(implementation_source, pattern) for pattern in reynolds_stress_diagonal_usage_patterns
    )
    has_reynolds_stress_offdiagonal_usage_evidence = all(
        has_regex(implementation_source, pattern) for pattern in reynolds_stress_offdiagonal_usage_patterns
    )
    has_reynolds_stress_full_tensor_usage_evidence = (
        has_reynolds_stress_diagonal_usage_evidence and has_reynolds_stress_offdiagonal_usage_evidence
    )
    reynolds_stress_metadata_lower = metadata_reynolds_stress_treatment.lower()
    metadata_documents_isotropic_k_only = contains_any(
        reynolds_stress_metadata_lower,
        [
            "isotropic_from_k",
            "isotropic k",
            "2k/3",
            "2k_over_3",
            "no measured reynolds-stress tensor",
            "no reynolds stress tensor",
        ],
    )
    has_reynolds_stress_tensor_metadata_claim = (
        not metadata_documents_isotropic_k_only
        and contains_any(
            reynolds_stress_metadata_lower,
            ["full_tensor", "reynolds_stress_tensor", "r11", "r22", "r33"],
        )
    )
    has_documented_isotropic_k_assumption = contains_any(
        " ".join([implementation_source, metadata_reynolds_stress_treatment]),
        [
            "isotropic k",
            "isotropic_from_k",
            "2k/3",
            "2k_over_3",
            "r11=r22=r33",
            "r12=r13=r23=0",
        ],
    )
    has_isotropic_k_reynolds_stress_source_evidence = (
        has_reynolds_stress_full_tensor_source_evidence and metadata_documents_isotropic_k_only
    )
    has_measured_or_precursor_reynolds_stress_tensor_evidence = (
        has_precursor_recycling_field
        or (has_reynolds_stress_full_tensor_usage_evidence and not metadata_documents_isotropic_k_only)
    )
    has_reynolds_stress_tensor_evidence = (
        has_precursor_recycling_field
        or has_reynolds_stress_full_tensor_source_evidence
        or has_measured_diagonal_rms_source_evidence
    )
    reynolds_stress_treatment = (
        "measured_or_precursor_full_tensor"
        if has_measured_or_precursor_reynolds_stress_tensor_evidence
        else "measured_diagonal_rms_missing_offdiagonal"
        if has_measured_diagonal_rms_usage_evidence and not has_reynolds_stress_offdiagonal_source_evidence
        else "documented_isotropic_k_tensor_source"
        if has_isotropic_k_reynolds_stress_source_evidence
        else "documented_isotropic_k_only"
        if has_documented_isotropic_k_assumption
        else "missing"
    )
    has_source_length_scale_evidence = contains_any(
        implementation_source,
        [
            "aij_length_scale_verified",
            "official_length_scale_verified",
            "precursor_length_scale",
            "recycling_length_scale",
            "digital_filter_length_scale",
            "digital-filter_length_scale",
            "synthetic_eddy_length_scale",
            "synthetic-eddy_length_scale",
            "sem_length_scale",
            "dfm_length_scale",
            "validated_length_scale_model",
        ],
    )
    has_metadata_length_scale_evidence = metadata_length_scale_gate == "pass"
    has_inlet_length_scale_evidence = (
        has_source_length_scale_evidence or has_metadata_length_scale_evidence or has_bound_length_scale_evidence
    )
    if has_bound_length_scale_evidence and has_metadata_length_scale_evidence:
        inlet_length_scale_evidence_basis = "bound_evidence_json_and_metadata_gate"
    elif has_bound_length_scale_evidence:
        inlet_length_scale_evidence_basis = "bound_evidence_json"
    elif has_source_length_scale_evidence and has_metadata_length_scale_evidence:
        inlet_length_scale_evidence_basis = "source_and_metadata_gate"
    elif has_source_length_scale_evidence:
        inlet_length_scale_evidence_basis = "source_code"
    elif has_metadata_length_scale_evidence:
        inlet_length_scale_evidence_basis = "metadata_gate_only"
    else:
        inlet_length_scale_evidence_basis = "missing"
    has_update_interval = (
        "citylbm_stg_update_interval" in implementation_source_lower
        or "inlet_update_interval" in implementation_source_lower
    )
    refresh_current_time_calls = count_regex(
        implementation_source,
        r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)",
    )
    has_stg_refresh_with_current_time = refresh_current_time_calls >= 1
    native_refresh_current_time_calls = count_regex(
        implementation_source,
        r"applyInlet\s*\(\s*(current|t_step|step|now)\s*\)",
    )
    if native_refresh_current_time_calls >= 1:
        has_stg_refresh_with_current_time = True
    has_update_interval_run_control = has_regex(
        implementation_source,
        r"steps_to_run\s*=\s*[^;\n]*citylbm_stg_update_interval",
    ) or has_regex(
        implementation_source,
        r"steps_to_run\s*>\s*citylbm_stg_update_interval\s*\)\s*steps_to_run\s*=\s*citylbm_stg_update_interval",
    ) or has_regex(
        implementation_source,
        r"run_chunk\s*=\s*[^;\n]*inlet_update_interval",
    )
    has_segmented_stg_run_loop = (
        has_update_interval_run_control
        and has_regex(implementation_source, r"lbm\.run\s*\(\s*steps_to_run\s*\)")
        and (
            has_regex(
                implementation_source,
                r"applySyntheticTurbulentInlet\s*\(\s*\(?\s*uint\s*\)?\s*lbm\.get_t\s*\(\s*\)\s*\)\s*;\s*lbm\.run\s*\(\s*steps_to_run\s*\)",
            )
            or has_regex(
                implementation_source,
                r"applyInlet\s*\(\s*current\s*\).*?lbm\.run\s*\(\s*steps_to_run\s*\)",
            )
        )
    )
    has_bounded_amplitude = contains_any(
        implementation_source,
        ["citylbm_stg_max_fraction", "max_fraction", "amplitude cap"],
    )
    streamwise_min_fraction = first_float_regex(
        implementation_source,
        r"citylbm_stg_min_streamwise_fraction\s*=\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?f?)\b",
    )
    has_streamwise_clipping_control = "citylbm_stg_min_streamwise_fraction" in implementation_source_lower
    streamwise_clipping_enabled = (
        streamwise_min_fraction is not None and streamwise_min_fraction > 0.0
    )
    has_legacy_hardcoded_streamwise_clipping = has_regex(
        implementation_source,
        r"0\.05f?\s*\*\s*\(\s*mean_mag\s*>",
    )
    has_mean_preserving_inlet_correction = contains_any(
        implementation_source,
        [
            "citylbm_stg_mean_correction",
            "citylbm_stg_corrected_inlet_count",
            "citylbm_stg_layer_mean_correction",
            "citylbm_stg_layer_corrected_inlet_count",
            "mean-preserving on the inlet",
            "mean-preserving at every inlet z_cell",
        ],
    )
    has_layerwise_mean_preserving_inlet_correction = (
        contains_any(
            implementation_source,
            [
                "citylbm_stg_layer_mean_correction_x",
                "citylbm_stg_layer_mean_correction_y",
                "citylbm_stg_layer_mean_correction_z",
                "citylbm_stg_layer_corrected_inlet_count",
                "per_z_cell_inlet_layer",
                "every z_cell layer",
            ],
        )
        and has_regex(implementation_source, r"for\s*\(\s*uint\s+z_layer\s*=\s*0u\s*;\s*z_layer\s*<\s*Nz")
    )
    has_layerwise_rms_preserving_inlet_correction = (
        contains_any(
            implementation_source,
            [
                "citylbm_stg_layer_rms_scale_x",
                "citylbm_stg_layer_rms_scale_y",
                "citylbm_stg_layer_rms_scale_z",
                "citylbm_stg_layer_corrected_sum_sq_x",
                "LayerwiseRmsPreserving",
                "RMS-preserving at every inlet z_cell",
            ],
        )
        and contains_any(
            implementation_source,
            [
                "citylbm_stg_target_sigma",
                "target_sigma / rms_x",
                "target sigma=sqrt(2k/3)",
            ],
        )
    )
    has_full_tensor_covariance_preserving_mean_correction = contains_any(
        implementation_source,
        [
            "covariance whitening/re-coloring",
            "citylbm_stg_layer_tensor_whitening_valid",
            "citylbm_stg_layer_corrected_sum_xy",
            "CityLBMReynoldsCholesky target_l = citylbm_stg_target_reynolds_cholesky(z_m);",
            "target_l.l11 * w1",
            "full_tensor_cholesky_covariance_preserving_mean_correction",
            "component_rms_rescale_disabled_for_full_reynolds_stress_tensor",
        ],
    )
    has_full_tensor_component_rms_rescale_guard = (
        has_full_tensor_covariance_preserving_mean_correction
        or not (
            has_reynolds_stress_full_tensor_usage_evidence
            and has_layerwise_rms_preserving_inlet_correction
        )
    )
    has_current_citylbm_stg_codegen_route = (
        has_regex(implementation_source, r"\bauto\s+applyInlet\s*=\s*\[")
        and has_regex(implementation_source, r"\bauto\s+applySyntheticTurbulentInlet\s*=\s*\[")
        and has_layerwise_mean_preserving_inlet_correction
        and has_layerwise_rms_preserving_inlet_correction
        and has_runtime_inlet_diagnostics_required_fields
        and (has_type_e_inlet_stress_reconstruction_route or has_type_e_equilibrium_reconstruction_route)
    )
    has_legacy_runtime_diagnostic_patch_route = (
        contains_any(
            implementation_source,
            [
                "CityLBM runtime inlet diagnostics patch",
                "patch_legacy_runtime_inlet_diagnostics",
            ],
        )
        or (
            has_native_turbulent_wind_function
            and has_legacy_digital_filter_state
            and not has_regex(implementation_source, r"\bapplySyntheticTurbulentInlet\s*=")
        )
    )
    if has_current_citylbm_stg_codegen_route:
        setup_inlet_codegen_route = "current_citylbm_stg_layerwise_type_e_route"
    elif has_legacy_runtime_diagnostic_patch_route:
        setup_inlet_codegen_route = "legacy_runtime_diagnostic_patch_route"
    elif has_native_turbulent_wind_function:
        setup_inlet_codegen_route = "legacy_turbulent_wind_route"
    elif has_stg_function:
        setup_inlet_codegen_route = "unclassified_stg_route"
    else:
        setup_inlet_codegen_route = "none"
    short_canary_allowed_by_codegen_route = has_current_citylbm_stg_codegen_route
    random_source_tokens = [
        r"\brand\s*\(",
        r"\brandom\s*\(",
        r"\bstd\s*::\s*rand\s*\(",
        r"\bstd\s*::\s*random_device\b",
        r"\bstd\s*::\s*mt19937\b",
        r"\bstd\s*::\s*mt19937_64\b",
        r"\bstd\s*::\s*default_random_engine\b",
        r"\bstd\s*::\s*minstd_rand\b",
        r"\bstd\s*::\s*ranlux\d+\b",
        r"\bstd\s*::\s*normal_distribution\b",
        r"\bstd\s*::\s*uniform_real_distribution\b",
        r"\bnormal_distribution\s*<",
        r"\buniform_real_distribution\s*<",
        r"\bgaussian_noise\b",
        r"\bcurand\w*\s*\(",
        r"\bwhite_noise\b",
        r"\bper_node_random\b",
        r"\bnode_random\b",
        r"\buncorrelated_random\b",
        r"\brms_random\b",
    ]
    random_source_matches = [
        pattern for pattern in random_source_tokens if has_regex(implementation_source, pattern)
    ]
    random_inlet_context = has_regex(
        implementation_source,
        r"(applySyntheticTurbulentInlet|syntheticTurbulentInlet|TYPE_E|profile_k_lbm|sigma)\b",
    )
    has_uncorrelated_random_inlet = (
        bool(random_source_matches)
        and random_inlet_context
        and has_velocity_field_write
        and not (
            (has_spectral_modes and has_taylor_advection and has_transverse_projection)
            or has_native_synthetic_eddy_evidence
        )
    )
    if has_distribution_consistent_precursor:
        synthetic_correlation_model = "precursor_or_recycling"
    elif has_distribution_consistent_digital_filter:
        synthetic_correlation_model = "digital_filter_distribution_consistent"
    elif has_distribution_consistent_sem:
        synthetic_correlation_model = "synthetic_eddy_distribution_consistent"
    elif has_distribution_consistent_stg_lite and has_type_e_inlet_stress_reconstruction_route:
        synthetic_correlation_model = "stg_lite_correlated_type_e_inlet_stress_ddf_reconstructed"
    elif has_distribution_consistent_stg_lite:
        synthetic_correlation_model = "stg_lite_correlated_type_e_equilibrium_ddf_reconstructed"
    elif has_spectral_modes and has_taylor_advection and has_transverse_projection and has_temporal_filter_state:
        synthetic_correlation_model = "spectral_taylor_temporal_filtered_projected_velocity_field_only"
    elif has_spectral_modes and has_taylor_advection and has_transverse_projection:
        synthetic_correlation_model = "spectral_taylor_projected_velocity_field_only"
    elif has_native_synthetic_eddy_evidence and has_taylor_advection:
        synthetic_correlation_model = "native_synthetic_eddy_velocity_field_only"
    elif has_uncorrelated_random_inlet:
        synthetic_correlation_model = "uncorrelated_random_rms_velocity_field_only"
    elif has_stg_function and has_velocity_field_write:
        synthetic_correlation_model = "velocity_field_only_without_correlation_evidence"
    else:
        synthetic_correlation_model = "none"

    source_method_class = "none"
    if has_distribution_consistent_precursor:
        source_method_class = "precursor_or_recycling"
    elif has_distribution_consistent_digital_filter:
        source_method_class = "digital_filter_distribution_consistent"
    elif has_distribution_consistent_sem:
        source_method_class = "synthetic_eddy_distribution_consistent"
    elif has_distribution_consistent_stg_lite and has_type_e_inlet_stress_reconstruction_route:
        source_method_class = "stg_lite_correlated_type_e_inlet_stress_ddf_reconstructed"
    elif has_distribution_consistent_stg_lite:
        source_method_class = "stg_lite_correlated_type_e_equilibrium_ddf_reconstructed"
    elif has_stg_function and has_velocity_field_write and (
        has_spectral_modes
        or has_taylor_advection
        or has_transverse_projection
        or has_native_synthetic_eddy_evidence
    ):
        source_method_class = "stg_lite_correlated_velocity_field_only"
    elif has_stg_function and has_velocity_field_write:
        source_method_class = "stg_lite_velocity_field_only"
    elif has_precursor and has_precursor_recycling_field:
        source_method_class = "precursor_or_recycling_velocity_field_only"
    elif has_precursor:
        source_method_class = "named_method_without_precursor_recycling_field_evidence"
    elif has_digital_filter or has_sem:
        source_method_class = "named_method_without_distribution_evidence"
    elif has_velocity_field_write:
        source_method_class = "mean_profile_velocity_field_only"

    source_distribution_consistent = source_method_class in {
        "precursor_or_recycling",
        "digital_filter_distribution_consistent",
        "synthetic_eddy_distribution_consistent",
        "stg_lite_correlated_type_e_inlet_stress_ddf_reconstructed",
        "stg_lite_correlated_type_e_equilibrium_ddf_reconstructed",
    }
    inlet_distribution_route = "none"
    if has_direct_inlet_distribution_reconstruction:
        inlet_distribution_route = "direct_setup_distribution_write"
    elif has_type_e_inlet_stress_reconstruction_route:
        inlet_distribution_route = "fluidx3d_reconstruct_inlet_stress_boundaries"
    elif has_type_e_equilibrium_reconstruction_route:
        inlet_distribution_route = "fluidx3d_reconstruct_equilibrium_boundaries"
    elif has_type_e_equilibrium_boundary_route:
        inlet_distribution_route = "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u"
    elif has_velocity_field_write:
        inlet_distribution_route = "velocity_field_only_without_equilibrium_boundary_define"
    inlet_distribution_route_gate = "pass" if inlet_distribution_route in {
        "direct_setup_distribution_write",
        "fluidx3d_reconstruct_inlet_stress_boundaries",
        "fluidx3d_reconstruct_equilibrium_boundaries",
        "fluidx3d_equilibrium_boundaries_type_e_from_preset_rho_u",
    } else "fail"
    advanced_code_evidence = (
        has_distribution_consistent_digital_filter
        or has_distribution_consistent_sem
        or has_distribution_consistent_precursor
    )
    source_velocity_only = source_method_class in {
        "stg_lite_velocity_field_only",
        "stg_lite_correlated_velocity_field_only",
        "mean_profile_velocity_field_only",
        "named_method_without_distribution_evidence",
        "named_method_without_precursor_recycling_field_evidence",
        "precursor_or_recycling_velocity_field_only",
    }
    stg_lite_velocity_source = source_method_class in {
        "stg_lite_velocity_field_only",
        "stg_lite_correlated_velocity_field_only",
    }
    source_has_uncorrelated_rms_velocity_field_only = (
        source_velocity_only
        and (
            has_uncorrelated_random_inlet
            or synthetic_correlation_model == "uncorrelated_random_rms_velocity_field_only"
        )
    )
    source_has_rms_k_velocity_surrogate = (
        bool(synthetic_requested)
        and source_velocity_only
        and not source_distribution_consistent
        and (
            has_k_driven_three_component_stg
            or has_measured_diagonal_rms_usage_evidence
            or has_isotropic_k_reynolds_stress_source_evidence
            or (has_k_profile and has_stg_function and has_velocity_field_write)
        )
    )
    rms_k_velocity_surrogate_reasons: List[str] = []
    if source_has_rms_k_velocity_surrogate:
        if has_k_profile:
            rms_k_velocity_surrogate_reasons.append("uses_profile_k_lbm")
        if has_k_driven_three_component_stg:
            rms_k_velocity_surrogate_reasons.append("k_driven_three_component_stg")
        if has_measured_diagonal_rms_usage_evidence:
            rms_k_velocity_surrogate_reasons.append("measured_diagonal_rms_velocity_field_usage")
        if has_isotropic_k_reynolds_stress_source_evidence:
            rms_k_velocity_surrogate_reasons.append("isotropic_k_reynolds_stress_surrogate")
        if source_velocity_only:
            rms_k_velocity_surrogate_reasons.append("velocity_field_only")
        if not source_distribution_consistent:
            rms_k_velocity_surrogate_reasons.append("not_distribution_consistent")
    rms_k_velocity_surrogate_gate = "fail" if source_has_rms_k_velocity_surrogate else "pass"
    source_has_correlated_velocity_field_only = (
        source_velocity_only
        and not source_has_uncorrelated_rms_velocity_field_only
        and (
            "correlated" in source_method_class
            or "spectral" in synthetic_correlation_model
            or "native_synthetic_eddy" in synthetic_correlation_model
            or "precursor_or_recycling_velocity_field_only" == source_method_class
        )
    )
    if source_method_class == "digital_filter_distribution_consistent":
        turbulent_inflow_fidelity_class = "distribution_consistent_digital_filter"
    elif source_method_class == "synthetic_eddy_distribution_consistent":
        turbulent_inflow_fidelity_class = "distribution_consistent_synthetic_eddy"
    elif source_method_class == "precursor_or_recycling":
        turbulent_inflow_fidelity_class = "distribution_consistent_precursor_or_recycling"
    elif source_method_class == "stg_lite_correlated_type_e_inlet_stress_ddf_reconstructed":
        turbulent_inflow_fidelity_class = "distribution_reconstructed_stg_lite_type_e_inlet_stress"
    elif source_method_class == "stg_lite_correlated_type_e_equilibrium_ddf_reconstructed":
        turbulent_inflow_fidelity_class = "distribution_reconstructed_stg_lite_type_e_equilibrium"
    elif source_has_uncorrelated_rms_velocity_field_only:
        turbulent_inflow_fidelity_class = "uncorrelated_rms_velocity_field_only"
    elif source_has_correlated_velocity_field_only:
        turbulent_inflow_fidelity_class = "correlated_velocity_field_only"
    elif source_velocity_only:
        turbulent_inflow_fidelity_class = "velocity_field_only_without_correlation_evidence"
    elif source_method_class.startswith("named_method_without"):
        turbulent_inflow_fidelity_class = "metadata_or_name_only"
    else:
        turbulent_inflow_fidelity_class = "none"
    source_requires_distribution_reconstruction = bool(synthetic_requested or source_method_class != "none")

    if synthetic_requested and not has_stg_function and not has_digital_filter and not has_sem and not has_precursor:
        reasons.append("metadata_requests_turbulent_inlet_but_source_has_no_inlet_method")
    if has_custom_table and not has_profile_origin_z_m:
        reasons.append("custom_table_source_missing_profile_origin_z_m")
    if has_custom_table and not has_origin_aware_profile_height:
        reasons.append("custom_table_source_not_origin_aware_for_profile_height")
    if advanced_token_only:
        reasons.append("advanced_inlet_method_tokens_without_code_evidence")
    if has_digital_filter and digital_filter_selected and not has_digital_filter_kernel:
        reasons.append("digital_filter_source_missing_filter_kernel")
    if has_digital_filter and digital_filter_selected and not has_digital_filter_state:
        reasons.append("digital_filter_source_missing_spatiotemporal_filter_state")
    if (
        synthetic_eddy_selected
        and has_native_synthetic_eddy_structure_evidence
        and not has_native_synthetic_eddy_temporal_refresh_evidence
    ):
        reasons.append("native_synthetic_eddy_missing_refresh_or_digital_filter_update")
    if has_sem and synthetic_eddy_selected and not has_sem_eddy_population:
        reasons.append("sem_source_missing_eddy_population")
    if has_sem and synthetic_eddy_selected and not has_sem_eddy_update_evidence:
        reasons.append("sem_source_missing_eddy_update_evidence")
    if has_sem and synthetic_eddy_selected and not has_sem_eddy_velocity_coupling_evidence:
        reasons.append("sem_source_missing_eddy_velocity_coupling_evidence")
    if has_precursor and not has_precursor_recycling_field:
        reasons.append("precursor_recycling_source_missing_recycled_field_evidence")
    if has_precursor and has_precursor_recycling_field and not has_inlet_distribution_reconstruction:
        reasons.append("precursor_recycling_source_missing_inlet_distribution_reconstruction")
    if synthetic_requested and has_stg_function and not has_k_profile:
        reasons.append("synthetic_inlet_source_missing_profile_k_lbm")
    if synthetic_requested and stg_lite_velocity_source and not has_stg_refresh_loop:
        reasons.append("synthetic_inlet_not_refreshed_in_run_loop")
    if synthetic_requested and stg_lite_velocity_source and not has_stg_refresh_with_current_time:
        reasons.append("synthetic_inlet_missing_refresh_with_current_solver_time")
    if synthetic_requested and stg_lite_velocity_source and not has_length_scale:
        reasons.append("synthetic_inlet_missing_length_scale_source")
    if synthetic_requested and stg_lite_velocity_source and not (has_spectral_modes or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_spectral_modes")
    if (
        synthetic_requested
        and stg_lite_velocity_source
        and effective_stg_mode_count is not None
        and effective_stg_mode_count < MINIMUM_RECOMMENDED_SPECTRAL_MODE_COUNT
    ):
        reasons.append("synthetic_inlet_too_few_spectral_modes")
    if (
        synthetic_requested
        and stg_lite_velocity_source
        and effective_stg_mode_count is not None
        and effective_stg_mode_count < STRICT_BASELINE_SPECTRAL_MODE_COUNT
    ):
        reasons.append("synthetic_inlet_below_strict_baseline_spectral_modes")
    if synthetic_requested and stg_lite_velocity_source and not has_taylor_advection:
        reasons.append("synthetic_inlet_missing_temporal_advection")
    if synthetic_requested and stg_lite_velocity_source and not (has_transverse_projection or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_transverse_projection")
    if synthetic_requested and stg_lite_velocity_source and not has_three_component_fluctuation_evidence:
        reasons.append("synthetic_inlet_missing_three_component_fluctuation_evidence")
    if synthetic_requested and stg_lite_velocity_source and not has_k_driven_three_component_stg:
        reasons.append("synthetic_inlet_missing_k_driven_three_component_stg_evidence")
    if synthetic_requested and stg_lite_velocity_source and not has_component_phase_decorrelation:
        reasons.append("synthetic_inlet_missing_component_phase_decorrelation")
    if synthetic_requested and stg_lite_velocity_source and not has_temporal_filter_state:
        reasons.append("synthetic_inlet_missing_temporal_filter_state")
    if synthetic_requested and stg_lite_velocity_source and not has_update_interval:
        reasons.append("synthetic_inlet_missing_update_interval")
    if synthetic_requested and stg_lite_velocity_source and has_update_interval and not has_update_interval_run_control:
        reasons.append("synthetic_inlet_update_interval_not_used_in_run_loop")
    if synthetic_requested and stg_lite_velocity_source and not has_segmented_stg_run_loop:
        reasons.append("synthetic_inlet_refresh_not_coupled_to_segmented_lbm_run")
    if synthetic_requested and stg_lite_velocity_source and not (has_bounded_amplitude or has_native_synthetic_eddy_evidence):
        reasons.append("synthetic_inlet_missing_amplitude_cap")
    if synthetic_requested and stg_lite_velocity_source and has_legacy_hardcoded_streamwise_clipping:
        reasons.append("synthetic_inlet_uses_legacy_hardcoded_streamwise_clipping")
    if synthetic_requested and stg_lite_velocity_source and not has_mean_preserving_inlet_correction:
        reasons.append("synthetic_inlet_missing_mean_preserving_inlet_correction")
    if synthetic_requested and stg_lite_velocity_source and has_mean_preserving_inlet_correction and not has_layerwise_mean_preserving_inlet_correction:
        reasons.append("synthetic_inlet_missing_layerwise_mean_preserving_inlet_correction")
    if synthetic_requested and stg_lite_velocity_source and not has_layerwise_rms_preserving_inlet_correction:
        reasons.append("synthetic_inlet_missing_layerwise_rms_preserving_inlet_correction")
    if synthetic_requested and has_uncorrelated_random_inlet:
        reasons.append("synthetic_inlet_uses_uncorrelated_random_rms")
    metadata_claims_distribution = any(
        token in " ".join([metadata_treatment, metadata_class]).lower()
        for token in ["distribution_consistent", "digital_filter", "digital-filter", "sem", "dfm", "precursor", "recycling"]
    )
    if metadata_claims_distribution and not source_distribution_consistent:
        reasons.append("metadata_claims_distribution_consistency_without_source_evidence")
    if metadata_claims_distribution and has_distribution_write and not has_inlet_distribution_reconstruction and not has_precursor:
        reasons.append("distribution_function_write_not_tied_to_inlet_reconstruction")
    if source_method_class == "named_method_without_distribution_evidence":
        reasons.append("advanced_inlet_method_missing_distribution_evidence")
    if source_method_class == "named_method_without_precursor_recycling_field_evidence":
        reasons.append("precursor_recycling_method_missing_recycled_field_evidence")
    if has_reynolds_stress_tensor_metadata_claim and not has_reynolds_stress_tensor_evidence:
        reasons.append("metadata_claims_reynolds_stress_without_source_evidence")
    if (
        has_reynolds_stress_tensor_metadata_claim
        and has_reynolds_stress_tensor_evidence
        and not has_reynolds_stress_full_tensor_usage_evidence
    ):
        reasons.append("metadata_claims_reynolds_stress_without_tensor_usage_evidence")
    if (
        has_reynolds_stress_full_tensor_usage_evidence
        and has_layerwise_rms_preserving_inlet_correction
        and not has_full_tensor_covariance_preserving_mean_correction
    ):
        reasons.append("full_tensor_component_rms_rescale_not_covariance_preserving")

    source_gate = "pass" if not reasons else "fail"
    paper_gate_reasons: List[str] = []
    if not source_distribution_consistent:
        paper_gate_reasons.append("source_not_distribution_consistent")
    if source_velocity_only:
        paper_gate_reasons.append("source_velocity_field_only")
    if source_has_uncorrelated_rms_velocity_field_only:
        paper_gate_reasons.append("source_uncorrelated_rms_velocity_field_only")
    if source_has_rms_k_velocity_surrogate:
        paper_gate_reasons.append("source_rms_k_velocity_surrogate_without_distribution_consistent_inlet")
    if source_has_correlated_velocity_field_only:
        paper_gate_reasons.append("source_correlated_velocity_field_only_without_distribution_reconstruction")
    if synthetic_requested and not has_inlet_length_scale_evidence:
        paper_gate_reasons.append("source_missing_turbulent_length_scale_evidence")
    if synthetic_requested and not has_measured_or_precursor_reynolds_stress_tensor_evidence:
        if has_isotropic_k_reynolds_stress_source_evidence:
            paper_gate_reasons.append("source_reynolds_stress_tensor_is_isotropic_k_assumption_only")
        elif has_measured_diagonal_rms_usage_evidence:
            paper_gate_reasons.append("source_has_measured_diagonal_rms_but_missing_offdiagonal_or_precursor_tensor")
        elif has_reynolds_stress_full_tensor_source_evidence and not has_reynolds_stress_full_tensor_usage_evidence:
            paper_gate_reasons.append("source_reynolds_stress_tensor_declared_but_not_used_in_inlet")
        else:
            paper_gate_reasons.append("source_missing_measured_or_precursor_reynolds_stress_tensor_evidence")
    if (
        synthetic_requested
        and has_reynolds_stress_full_tensor_usage_evidence
        and has_layerwise_rms_preserving_inlet_correction
        and not has_full_tensor_covariance_preserving_mean_correction
    ):
        paper_gate_reasons.append("source_full_tensor_component_rms_rescale_not_covariance_preserving")
    if (
        synthetic_eddy_selected
        and has_native_synthetic_eddy_structure_evidence
        and not has_native_synthetic_eddy_temporal_refresh_evidence
    ):
        paper_gate_reasons.append("native_synthetic_eddy_missing_refresh_or_digital_filter_update")
    if synthetic_requested and runtime_inlet_diagnostics_source_gate != "pass":
        paper_gate_reasons.append("source_missing_runtime_inlet_diagnostics_csv_for_u_k_rms_preservation")
    paper_gate = "pass" if not paper_gate_reasons else "fail"
    if source_gate != "pass":
        if source_has_rms_k_velocity_surrogate:
            development_stage = "replace_rms_k_velocity_surrogate_with_distribution_consistent_inlet"
            development_reason = "The generated inlet still converts k/RMS into a velocity-field-only surrogate, so another CFD run would not isolate solver accuracy."
        elif source_has_uncorrelated_rms_velocity_field_only:
            development_stage = "replace_uncorrelated_random_inlet_before_cfd"
            development_reason = "The generated inlet still looks like uncorrelated RMS noise, so another CFD run would not isolate solver accuracy."
        elif not source_distribution_consistent:
            development_stage = "fix_distribution_consistent_inlet_source_before_cfd"
            development_reason = "The generated source has not proven distribution-consistent inlet treatment."
        else:
            development_stage = "fix_inlet_source_evidence_before_cfd"
            development_reason = "The generated source has unresolved inlet implementation evidence failures."
        development_duration_class = "code_then_short_cfd"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_source_gate_passes"
    elif paper_gate != "pass":
        if any("rms_k_velocity_surrogate" in reason for reason in paper_gate_reasons):
            development_stage = "replace_rms_k_velocity_surrogate_with_distribution_consistent_inlet"
            development_reason = "The inlet source is code-consistent enough for diagnostics, but paper-grade CFD requires a distribution-consistent digital-filter, synthetic-eddy, precursor, or recycling inlet instead of a k/RMS velocity surrogate."
        elif any("reynolds_stress" in reason or "precursor" in reason or "offdiagonal" in reason for reason in paper_gate_reasons):
            development_stage = "resolve_reynolds_stress_tensor_or_precursor_evidence"
            development_reason = "The inlet source is code-consistent enough for diagnostics, but paper-grade turbulent inflow still lacks full Reynolds-stress or precursor-equivalent evidence."
        elif any("length_scale" in reason for reason in paper_gate_reasons):
            development_stage = "resolve_turbulent_length_scale_evidence"
            development_reason = "The inlet source needs traceable turbulent length-scale evidence before paper-grade CFD."
        elif any("runtime_inlet_diagnostics" in reason for reason in paper_gate_reasons):
            development_stage = "add_runtime_inlet_diagnostics_before_long_cfd"
            development_reason = "The inlet source needs runtime inlet diagnostics for U/k/RMS preservation before long CFD can reduce uncertainty."
        else:
            development_stage = "close_paper_grade_inlet_evidence"
            development_reason = "The inlet source passes implementation checks, but paper-grade inlet evidence is incomplete."
        development_duration_class = "minutes"
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_paper_inlet_gate_passes"
    else:
        development_stage = "eligible_for_short_native_canary"
        development_reason = "The source-level inlet audit is closed; the next useful CFD evidence is a short native canary with runtime U/k/correlation diagnostics."
        development_duration_class = "short_cfd"
        development_runs_cfd_next = True
        development_next_cfd_scope = "short_native_canary_only"

    report: Dict[str, Any] = {
        "schema": "citylbm.inlet_source_audit.v1",
        "generated_at_utc": utc_now(),
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": setup_hash,
        "comment_stripped_setup_cpp_sha256": audited_source_hash,
        "defines_hpp": str(defines_path) if defines_path else "",
        "defines_hpp_sha256": defines_hash,
        "comment_stripped_defines_hpp_sha256": audited_defines_source_hash,
        "inlet_source_comment_stripped_code_audit": True,
        "advanced_inlet_evidence_uses_comment_stripped_code": True,
        "defines_hpp_audited": bool(defines_path),
        "metadata": str(metadata_path) if metadata_path else "",
        "metadata_method": metadata_method,
        "metadata_distribution_treatment": metadata_treatment,
        "metadata_method_class": metadata_class,
        "metadata_synthetic_eddy_enabled": synthetic_enabled,
        "synthetic_inlet_requested": synthetic_requested,
        "has_custom_table_profile": has_custom_table,
        "has_profile_k_lbm": has_k_profile,
        "has_runtime_inlet_diagnostics_csv_source": has_runtime_inlet_diagnostics_csv_source,
        "has_runtime_inlet_diagnostics_file_evidence": has_runtime_inlet_diagnostics_file_evidence,
        "has_runtime_inlet_diagnostics_writer_evidence": has_runtime_inlet_diagnostics_writer_evidence,
        "runtime_inlet_diagnostics_required_fields": runtime_inlet_diagnostics_required_fields,
        "runtime_inlet_diagnostics_present_fields": runtime_inlet_diagnostics_present_fields,
        "has_runtime_inlet_diagnostics_required_fields": has_runtime_inlet_diagnostics_required_fields,
        "runtime_inlet_diagnostics_source_gate": runtime_inlet_diagnostics_source_gate,
        "has_profile_origin_z_m": has_profile_origin_z_m,
        "has_origin_aware_profile_height": has_origin_aware_profile_height,
        "has_synthetic_inlet_function": has_stg_function,
        "has_synthetic_inlet_refresh_loop": has_stg_refresh_loop,
        "native_synthetic_eddy_evidence_requires_refresh": True,
        "has_native_synthetic_eddy_structure_evidence": has_native_synthetic_eddy_structure_evidence,
        "has_native_synthetic_eddy_temporal_refresh_evidence": has_native_synthetic_eddy_temporal_refresh_evidence,
        "has_native_synthetic_eddy_evidence": has_native_synthetic_eddy_evidence,
        "has_native_synthetic_eddy_function": has_native_synthetic_eddy_function,
        "has_native_turbulent_wind_function": has_native_turbulent_wind_function,
        "has_native_apply_inlet_function": has_native_apply_inlet_function,
        "has_native_synthetic_eddy_population": has_native_synthetic_eddy_population,
        "has_native_synthetic_eddy_shape": has_native_synthetic_eddy_shape,
        "has_native_synthetic_eddy_refresh": has_native_synthetic_eddy_refresh,
        "has_velocity_field_write": has_velocity_field_write,
        "has_three_component_velocity_write": has_three_component_velocity_write,
        "has_type_e_boundary_flag": has_type_e_boundary_flag,
        "has_flags_device_upload": has_flags_device_upload,
        "has_u_device_upload": has_u_device_upload,
        "has_equilibrium_boundaries_define": has_equilibrium_boundaries_define,
        "has_reconstruct_inlet_stress_ddf_define": has_reconstruct_inlet_stress_ddf_define,
        "has_reconstruct_equilibrium_ddf_define": has_reconstruct_equilibrium_ddf_define,
        "has_casea_device_sem_inlet_define": has_casea_device_sem_inlet_define,
        "has_casea_device_sem_stress_ddf_define": has_casea_device_sem_stress_ddf_define,
        "has_reconstruct_inlet_stress_call": has_reconstruct_inlet_stress_call,
        "has_reconstruct_equilibrium_call": has_reconstruct_equilibrium_call,
        "has_casea_device_sem_inlet_call": has_casea_device_sem_inlet_call,
        "has_casea_device_sem_stress_route": has_casea_device_sem_stress_route,
        "has_type_e_inlet_stress_reconstruction_route": has_type_e_inlet_stress_reconstruction_route,
        "has_type_e_equilibrium_reconstruction_route": has_type_e_equilibrium_reconstruction_route,
        "has_type_e_equilibrium_boundary_route": has_type_e_equilibrium_boundary_route,
        "inlet_distribution_route": inlet_distribution_route,
        "inlet_distribution_route_gate": inlet_distribution_route_gate,
        "has_three_component_fluctuation_evidence": has_three_component_fluctuation_evidence,
        "has_rms_profile_driven_three_component_native_stg": has_rms_profile_driven_three_component_native_stg,
        "has_k_driven_three_component_stg": has_k_driven_three_component_stg,
        "has_component_phase_decorrelation": has_component_phase_decorrelation,
        "has_temporal_filter_state": has_temporal_filter_state,
        "has_distribution_function_write": has_distribution_write,
        "distribution_function_write_count": distribution_evidence["distribution_write_count"],
        "has_direct_inlet_distribution_reconstruction": has_direct_inlet_distribution_reconstruction,
        "has_inlet_distribution_reconstruction": has_inlet_distribution_reconstruction,
        "inlet_distribution_reconstruction_count": distribution_evidence["inlet_distribution_reconstruction_count"],
        "inlet_source_advanced_code_evidence": advanced_code_evidence,
        "has_digital_filter_evidence": has_digital_filter,
        "has_digital_filter_token": has_digital_filter_token,
        "has_digital_filter_kernel_evidence": has_digital_filter_kernel,
        "has_digital_filter_state_evidence": has_digital_filter_state,
        "has_legacy_digital_filter_kernel_evidence": has_legacy_digital_filter_kernel,
        "has_legacy_digital_filter_state_evidence": has_legacy_digital_filter_state,
        "has_sem_evidence": has_sem,
        "has_sem_token": has_sem_token,
        "has_sem_eddy_population_evidence": has_sem_eddy_population,
        "has_sem_eddy_update_evidence": has_sem_eddy_update_evidence,
        "has_sem_eddy_velocity_coupling_evidence": has_sem_eddy_velocity_coupling_evidence,
        "has_precursor_or_recycling_evidence": has_precursor,
        "has_precursor_or_recycling_token": has_precursor_token,
        "has_precursor_recycling_field_evidence": has_precursor_recycling_field,
        "distribution_consistency_basis": (
            "precursor_or_recycling_field"
            if has_distribution_consistent_precursor
            else "digital_filter_kernel_state_distribution_reconstruction"
            if has_distribution_consistent_digital_filter
            else "sem_eddy_population_distribution_reconstruction"
            if has_distribution_consistent_sem
            else "stg_lite_type_e_inlet_stress_ddf_reconstruction"
            if has_distribution_consistent_stg_lite and has_type_e_inlet_stress_reconstruction_route
            else "stg_lite_type_e_equilibrium_ddf_reconstruction"
            if has_distribution_consistent_stg_lite
            else "missing"
        ),
        "advanced_inlet_method_token_only": advanced_token_only,
        "has_spectral_mode_evidence": has_spectral_modes,
        "synthetic_inlet_spectral_mode_count": effective_stg_mode_count,
        "citylbm_stg_spectral_mode_count": stg_mode_count,
        "native_synthetic_eddy_count": native_stg_mode_count,
        "minimum_recommended_spectral_mode_count": MINIMUM_RECOMMENDED_SPECTRAL_MODE_COUNT,
        "minimum_strict_baseline_spectral_mode_count": STRICT_BASELINE_SPECTRAL_MODE_COUNT,
        "synthetic_inlet_spectral_mode_count_gate": spectral_mode_count_gate,
        "has_taylor_advection_evidence": has_taylor_advection,
        "has_transverse_projection_evidence": has_transverse_projection,
        "has_length_scale_evidence": has_length_scale,
        "has_length_scale_parameter": has_length_scale,
        "metadata_length_scale_gate": metadata_length_scale_gate,
        "length_scale_evidence_json": str(length_scale_evidence_json_path) if length_scale_evidence_json_path else "",
        "length_scale_evidence_json_exists": length_scale_evidence_json_exists,
        "length_scale_evidence_json_sha256": length_scale_evidence_json_sha,
        "length_scale_evidence_json_hash_matches_metadata": length_scale_evidence_hash_matches,
        "length_scale_evidence_gate": length_scale_evidence_gate,
        "length_scale_evidence_paper_gate": length_scale_evidence_paper_gate,
        "has_bound_length_scale_evidence": has_bound_length_scale_evidence,
        "has_source_length_scale_evidence": has_source_length_scale_evidence,
        "has_metadata_length_scale_evidence": has_metadata_length_scale_evidence,
        "has_inlet_length_scale_evidence": has_inlet_length_scale_evidence,
        "inlet_length_scale_evidence_basis": inlet_length_scale_evidence_basis,
        "metadata_reynolds_stress_treatment": metadata_reynolds_stress_treatment,
        "metadata_wind_vector": metadata_wind_vector,
        "setup_cpp_wind_vector": setup_wind_vector,
        "wind_vector_source_matches_metadata": wind_vector_source_matches_metadata,
        "has_reynolds_stress_tensor_metadata_claim": has_reynolds_stress_tensor_metadata_claim,
        "has_measured_diagonal_rms_source_evidence": has_measured_diagonal_rms_source_evidence,
        "has_measured_diagonal_rms_usage_evidence": has_measured_diagonal_rms_usage_evidence,
        "has_reynolds_stress_diagonal_source_evidence": has_reynolds_stress_diagonal_source_evidence,
        "has_reynolds_stress_offdiagonal_source_evidence": has_reynolds_stress_offdiagonal_source_evidence,
        "has_reynolds_stress_full_tensor_source_evidence": has_reynolds_stress_full_tensor_source_evidence,
        "has_reynolds_stress_diagonal_usage_evidence": has_reynolds_stress_diagonal_usage_evidence,
        "has_reynolds_stress_offdiagonal_usage_evidence": has_reynolds_stress_offdiagonal_usage_evidence,
        "has_reynolds_stress_full_tensor_usage_evidence": has_reynolds_stress_full_tensor_usage_evidence,
        "has_isotropic_k_reynolds_stress_source_evidence": has_isotropic_k_reynolds_stress_source_evidence,
        "has_measured_or_precursor_reynolds_stress_tensor_evidence": has_measured_or_precursor_reynolds_stress_tensor_evidence,
        "has_reynolds_stress_tensor_evidence": has_reynolds_stress_tensor_evidence,
        "reynolds_stress_tensor_paper_grade_gate": (
            "pass" if has_measured_or_precursor_reynolds_stress_tensor_evidence else "fail"
        ),
        "has_documented_isotropic_k_assumption": has_documented_isotropic_k_assumption,
        "reynolds_stress_treatment": reynolds_stress_treatment,
        "has_update_interval": has_update_interval,
        "stg_refresh_current_time_call_count": refresh_current_time_calls,
        "native_refresh_current_time_call_count": native_refresh_current_time_calls,
        "has_synthetic_inlet_refresh_with_current_time": has_stg_refresh_with_current_time,
        "has_update_interval_run_control": has_update_interval_run_control,
        "has_segmented_stg_run_loop": has_segmented_stg_run_loop,
        "has_bounded_amplitude": has_bounded_amplitude,
        "has_streamwise_clipping_control": has_streamwise_clipping_control,
        "streamwise_min_fraction": streamwise_min_fraction,
        "streamwise_clipping_enabled": streamwise_clipping_enabled,
        "has_legacy_hardcoded_streamwise_clipping": has_legacy_hardcoded_streamwise_clipping,
        "has_mean_preserving_inlet_correction": has_mean_preserving_inlet_correction,
        "has_layerwise_mean_preserving_inlet_correction": has_layerwise_mean_preserving_inlet_correction,
        "has_layerwise_rms_preserving_inlet_correction": has_layerwise_rms_preserving_inlet_correction,
        "has_full_tensor_covariance_preserving_mean_correction": has_full_tensor_covariance_preserving_mean_correction,
        "has_full_tensor_component_rms_rescale_guard": has_full_tensor_component_rms_rescale_guard,
        "setup_inlet_codegen_route": setup_inlet_codegen_route,
        "has_current_citylbm_stg_codegen_route": has_current_citylbm_stg_codegen_route,
        "has_legacy_runtime_diagnostic_patch_route": has_legacy_runtime_diagnostic_patch_route,
        "short_canary_allowed_by_codegen_route": short_canary_allowed_by_codegen_route,
        "has_uncorrelated_random_inlet": has_uncorrelated_random_inlet,
        "uncorrelated_random_inlet_patterns": random_source_matches,
        "synthetic_inlet_correlation_model": synthetic_correlation_model,
        "inlet_source_method_class": source_method_class,
        "inlet_source_turbulent_inflow_fidelity_class": turbulent_inflow_fidelity_class,
        "inlet_source_distribution_consistent": source_distribution_consistent,
        "inlet_source_velocity_field_only": source_velocity_only,
        "inlet_source_has_correlated_velocity_field_only": source_has_correlated_velocity_field_only,
        "inlet_source_has_uncorrelated_rms_velocity_field_only": source_has_uncorrelated_rms_velocity_field_only,
        "inlet_source_has_rms_k_velocity_surrogate": source_has_rms_k_velocity_surrogate,
        "inlet_source_rms_k_surrogate_gate": rms_k_velocity_surrogate_gate,
        "inlet_source_rms_k_surrogate_reasons": rms_k_velocity_surrogate_reasons or ["not_rms_k_velocity_surrogate"],
        "inlet_source_rms_k_surrogate_reasons_csv": ";".join(
            rms_k_velocity_surrogate_reasons or ["not_rms_k_velocity_surrogate"]
        ),
        "inlet_source_requires_distribution_reconstruction": source_requires_distribution_reconstruction,
        "inlet_source_gate": source_gate,
        "inlet_source_gate_reasons": reasons or ["inlet_source_consistent_with_declared_metadata"],
        "paper_grade_inlet_source_gate": paper_gate,
        "paper_grade_inlet_source_gate_reasons": paper_gate_reasons or ["source_distribution_consistent"],
        "development_acceleration_stage": development_stage,
        "development_acceleration_duration_class": development_duration_class,
        "development_acceleration_runs_cfd_next": development_runs_cfd_next,
        "development_acceleration_next_cfd_scope": development_next_cfd_scope,
        "development_acceleration_reason": development_reason,
        "long_cfd_allowed_by_inlet_source_audit": source_gate == "pass" and paper_gate == "pass",
        "recommended_next_action": (
            "Use source evidence plus final-window VTK inlet profile/correlation audits. Do not describe a velocity-field "
            "STG-lite source as digital-filter, SEM, precursor, recycling or distribution-consistent inlet. Treat FluidX3D "
            "EQUILIBRIUM_BOUNDARIES as a kernel equilibrium TYPE_E route, not as proof of full turbulent-inflow fidelity by itself."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "inlet_source_gate={gate}; paper_grade_inlet_source_gate={paper}; method_class={method}; reasons={reasons}".format(
            gate=source_gate,
            paper=paper_gate,
            method=source_method_class,
            reasons=";".join(report["inlet_source_gate_reasons"]),
        )
    )
    return 0 if source_gate == "pass" and paper_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
