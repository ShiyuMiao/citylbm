#!/usr/bin/env python3
"""Audit generated setup.cpp boundary-condition implementation evidence.

This script does not run CFD. It checks the generated FluidX3D setup.cpp so a
validation package cannot rely only on boundary metadata or evidence labels
while the source still uses a simplified TYPE_E box-boundary setup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit generated FluidX3D setup.cpp boundary implementation evidence.")
    parser.add_argument("--setup", required=True, help="Generated setup.cpp path.")
    parser.add_argument("--defines", help="Optional generated defines.hpp path. Defaults to the setup.cpp directory.")
    parser.add_argument("--metadata", help="Optional case_metadata.json.")
    parser.add_argument("--out", required=True, help="Output boundary_source_audit.json.")
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


def nested(mapping: Dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def count_regex(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE))


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def read_float_constant(text: str, name: str) -> Optional[float]:
    match = re.search(
        rf"\bconst\s+float\s+{re.escape(name)}\s*=\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)f?\s*;",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def find_all_indices(text: str, token: str) -> List[int]:
    indices: List[int] = []
    start = 0
    while True:
        index = text.find(token, start)
        if index < 0:
            return indices
        indices.append(index)
        start = index + len(token)


def first_index_after(indices: Iterable[int], marker: int) -> int:
    after = [index for index in indices if index > marker]
    return min(after) if after else -1


def strip_cpp_string_literals(text: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)


def find_type_e_velocity_initialization(code: str) -> Dict[str, Any]:
    guard_match = re.search(
        r"if\s*\(\s*lbm\.flags\s*\[\s*n\s*\]\s*!=\s*TYPE_E\s*\)\s*return\s*;",
        code,
        flags=re.IGNORECASE,
    )
    if not guard_match:
        direct_matches = list(
            re.finditer(
                r"if\s*\([^)]*(?:x\s*==\s*0u|x\s*==\s*Nx\s*-\s*1u|z\s*==\s*Nz\s*-\s*1u|y\s*==\s*0u|y\s*==\s*Ny\s*-\s*1u)[^)]*\)\s*\{.{0,700}?lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E;.{0,700}?lbm\.u\.x\s*\[\s*n\s*\]\s*=.{0,700}?lbm\.u\.y\s*\[\s*n\s*\]\s*=.{0,700}?lbm\.u\.z\s*\[\s*n\s*\]\s*=",
                code,
                flags=re.IGNORECASE | re.DOTALL,
            )
        )
        if direct_matches:
            combined = "\n".join(match.group(0) for match in direct_matches)
            return {
                "guard": True,
                "coordinates": True,
                "velocity_write": True,
                "profile": bool(re.search(r"\b(?:windProfile|turbulentWind|recycledRescaledWind)\s*\(", combined)),
                "uniform": False,
                "block_start_index": direct_matches[0].start(),
                "mode": "direct_coordinate_branch",
            }
        return {
            "guard": False,
            "coordinates": False,
            "velocity_write": False,
            "profile": False,
            "uniform": False,
            "block_start_index": -1,
            "mode": "missing",
        }

    window = code[guard_match.start() : guard_match.start() + 1200]
    has_coordinates = bool(re.search(r"lbm\.coordinates\s*\(\s*n\s*,\s*x\s*,\s*y\s*,\s*z\s*\)", window))
    has_profile = bool(re.search(r"float3\s+u_e\s*=\s*windProfile\s*\(\s*z\s*\)", window))
    has_uniform = all(
        re.search(rf"lbm\.u\.{axis}\s*\[\s*n\s*\]\s*=\s*u_{axis}\s*;", window)
        for axis in ["x", "y", "z"]
    )
    has_profile_write = all(
        re.search(rf"lbm\.u\.{axis}\s*\[\s*n\s*\]\s*=\s*u_e\.{axis}\s*;", window)
        for axis in ["x", "y", "z"]
    )
    return {
        "guard": True,
        "coordinates": has_coordinates,
        "velocity_write": has_profile_write or has_uniform,
        "profile": has_profile and has_profile_write,
        "uniform": has_uniform,
        "block_start_index": guard_match.start(),
        "mode": "guarded_type_e_block",
    }


def strip_cpp_comments(text: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", without_block)


def strip_negated_boundary_claims(text: str) -> str:
    """Remove common negative statements so they are not read as advanced claims."""
    cleaned = text
    negative_patterns = [
        r"\bno\s+[\w\-/ ]{0,60}?(?:non[_ -]?reflecting|rough[_ -]?wall|wall[_ -]?function|precursor|recycling)[\w\-/ ]{0,30}",
        r"\bwithout\s+[\w\-/ ]{0,60}?(?:non[_ -]?reflecting|rough[_ -]?wall|wall[_ -]?function|precursor|recycling)[\w\-/ ]{0,30}",
        r"\bnot\s+[\w\-/ ]{0,60}?(?:non[_ -]?reflecting|rough[_ -]?wall|wall[_ -]?function|precursor|recycling)[\w\-/ ]{0,30}",
    ]
    for pattern in negative_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return cleaned


def extract_cpp_comments(text: str) -> str:
    comments = re.findall(r"/\*.*?\*/|//.*", text, flags=re.DOTALL)
    return "\n".join(comments)


def count_empty_advanced_boundary_method_stubs(text: str) -> int:
    return count_regex(
        text,
        (
            r"\b(?:void|float|float3|uint|int|bool|auto)\s+"
            r"\w*(?:non_reflecting|nonReflecting|convective_outlet|convectiveOutlet|"
            r"absorbing_outlet|absorbingOutlet|radiation_boundary|radiationBoundary|"
            r"periodic_boundary|periodicBoundary|rough_wall|roughWall|wall_function|"
            r"wallFunction|log_law|logLaw|precursor|recycling_rescaling|"
            r"recyclingRescaling|recycle_rescale|recycleRescale)\w*"
            r"\s*\([^;{}]*\)\s*\{\s*\}"
        ),
    )


def call_indices_excluding_definitions(text: str, pattern: str) -> List[int]:
    indices: List[int] = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL):
        prefix = text[max(0, match.start() - 48) : match.start()]
        if re.search(r"\b(?:void|float|float3|uint|int|bool|auto)\s+$", prefix):
            continue
        indices.append(match.start())
    return indices


def has_contextual_boundary_call(
    text: str,
    call_pattern: str,
    required_patterns: Iterable[str],
    before: int = 650,
    after: int = 260,
) -> bool:
    for index in call_indices_excluding_definitions(text, call_pattern):
        window = text[max(0, index - before) : index + after]
        if all(has_regex(window, pattern) for pattern in required_patterns):
            return True
    return False


def main() -> int:
    args = parse_args()
    setup_path = Path(args.setup).expanduser().resolve()
    defines_path = (
        Path(args.defines).expanduser().resolve()
        if args.defines
        else setup_path.with_name("defines.hpp")
    )
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else None
    out_path = Path(args.out).expanduser().resolve()
    metadata = read_json(metadata_path)

    reasons: List[str] = []
    if not setup_path.exists():
        reasons.append("setup_cpp_missing")
        source = ""
        setup_hash = ""
    else:
        source = setup_path.read_text(encoding="utf-8-sig", errors="replace")
        setup_hash = sha256(setup_path)
    if defines_path.exists():
        defines_source = defines_path.read_text(encoding="utf-8-sig", errors="replace")
        defines_hash = sha256(defines_path)
    else:
        defines_source = ""
        defines_hash = ""

    code = strip_cpp_comments(source)
    comments = extract_cpp_comments(source)
    implementation_code = strip_cpp_string_literals(code)
    defines_implementation_code = strip_cpp_string_literals(strip_cpp_comments(defines_source))
    implementation_and_defines = implementation_code + "\n" + defines_implementation_code
    lower = implementation_and_defines.lower()
    boundary_summary = str(metadata.get("BoundaryConditionSummary") or "")
    boundary_types = nested(metadata, "BoundaryProtocolAudit", "BoundaryTypes")
    boundary_types_text = json.dumps(boundary_types, ensure_ascii=True) if isinstance(boundary_types, dict) else ""
    metadata_boundary_text = " ".join([boundary_summary, boundary_types_text]).lower()
    metadata_boundary_claim_text = strip_negated_boundary_claims(metadata_boundary_text)
    boundary_velocity_treatment_text = " ".join(
        str(metadata.get(key) or "")
        for key in [
            "BoundaryTypeEVelocityInitializationTreatment",
            "BoundaryVelocityInitializationMethod",
            "BoundaryOutletTreatment",
            "BoundarySideTopTreatment",
            "BoundaryFixedMeanVelocityOutletRisk",
        ]
    ).lower()

    has_equilibrium_boundaries = "equilibrium_boundaries" in lower
    has_type_e_define = "#define type_e" in lower or "type_e 0x02" in lower
    has_type_s_define = "#define type_s" in lower or "type_s 0x01" in lower
    has_type_e_symbol = "type_e" in lower
    has_type_s_symbol = "type_s" in lower
    type_e_assignment_count = count_regex(implementation_code, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E")
    type_s_assignment_count = count_regex(implementation_code, r"lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_S")
    has_ground_no_slip = "if(z == 0u)" in implementation_code and "TYPE_S" in implementation_code
    has_building_voxel_solid = (
        ("voxelize_stl" in lower or "voxelize_mesh_on_device" in lower)
        and "type_s" in lower
    )
    type_e_velocity_initialization = find_type_e_velocity_initialization(implementation_code)
    has_type_e_velocity_initialization = (
        type_e_velocity_initialization["guard"]
        and type_e_velocity_initialization["coordinates"]
        and type_e_velocity_initialization["velocity_write"]
    )
    has_profile_type_e_velocity_initialization = (
        has_type_e_velocity_initialization and type_e_velocity_initialization["profile"]
    )
    has_uniform_type_e_velocity_initialization = (
        has_type_e_velocity_initialization and type_e_velocity_initialization["uniform"]
    )
    has_fixed_mean_type_e_boundary_velocity = (
        has_type_e_velocity_initialization
        and (has_profile_type_e_velocity_initialization or has_uniform_type_e_velocity_initialization)
    )
    fixed_mean_boundary_metadata = contains_any(
        boundary_velocity_treatment_text,
        [
            "fixed_mean_velocity_equilibrium",
            "all_type_e_boundaries_initialized",
            "outlet_lateral_top_initialized",
            "outlet_lateral_top_mean_velocity_equilibrium",
        ],
    )
    has_fixed_mean_outlet_lateral_top_treatment = (
        has_fixed_mean_type_e_boundary_velocity or fixed_mean_boundary_metadata
    )
    has_profile_maintenance_buffer = (
        "boundary_profile_maintenance" in lower
        and "apply_boundary_profile_maintenance_buffer" in lower
        and has_regex(implementation_code, r"\blbm\.F\.[xyz]\s*\[\s*n\s*\]\s*\+=")
    )
    fixed_mean_outlet_lateral_top_treatment_gate = (
        "diagnostic_only_with_profile_maintenance_buffer"
        if has_profile_maintenance_buffer
        else ("diagnostic_only" if has_fixed_mean_outlet_lateral_top_treatment else "missing")
    )
    type_e_velocity_initialization_index = int(type_e_velocity_initialization["block_start_index"])
    flags_write_to_device_indices = find_all_indices(implementation_code, "lbm.flags.write_to_device()")
    u_write_to_device_indices = find_all_indices(implementation_code, "lbm.u.write_to_device()")
    flags_write_to_device_index = first_index_after(
        flags_write_to_device_indices,
        type_e_velocity_initialization_index,
    )
    u_write_to_device_index = first_index_after(
        u_write_to_device_indices,
        type_e_velocity_initialization_index,
    )
    has_flags_device_upload_after_type_e_velocity_initialization = (
        has_type_e_velocity_initialization
        and flags_write_to_device_index >= 0
        and type_e_velocity_initialization_index >= 0
        and type_e_velocity_initialization_index < flags_write_to_device_index
    )
    has_u_device_upload_after_type_e_velocity_initialization = (
        has_type_e_velocity_initialization
        and u_write_to_device_index >= 0
        and type_e_velocity_initialization_index >= 0
        and type_e_velocity_initialization_index < u_write_to_device_index
    )
    has_type_e_velocity_initialization_before_device_upload = (
        has_flags_device_upload_after_type_e_velocity_initialization
        and has_u_device_upload_after_type_e_velocity_initialization
    )
    has_profile_inlet = contains_any(implementation_code, ["windProfile(z)", "profile_u_lbm", "profile_z_m"])
    has_outlet_type_e = bool(
        re.search(
            r"if\s*\([^)]*(Nx-1u|0u|Ny-1u)[^)]*\)\s*\{\s*lbm\.flags\s*\[\s*n\s*\]\s*=\s*TYPE_E;\s*return;",
            implementation_code,
        )
    )
    has_lateral_type_e = contains_any(
        implementation_code,
        [
            "if(y == 0u || y == Ny-1u) { lbm.flags[n] = TYPE_E; return; }",
            "if(x == 0u || x == Nx-1u) { lbm.flags[n] = TYPE_E; return; }",
        ],
    )
    has_top_type_e = "if(z == Nz-1u) { lbm.flags[n] = TYPE_E; return; }" in implementation_code
    has_non_reflecting_outlet_token = contains_any(
        implementation_code,
        [
            "non_reflecting",
            "non-reflecting",
            "convective_outlet",
            "convective outlet",
            "absorbing outlet",
            "sponge layer",
            "sponge_layer",
            "radiation boundary",
            "pressure outlet validated",
        ],
    )
    has_periodic_side_top_token = contains_any(
        implementation_code,
        ["periodic boundary", "periodic_x", "periodic_y", "periodic_z"],
    )
    generated_rough_wall_drag_alpha = read_float_constant(implementation_code, "rough_wall_drag_alpha")
    generated_rough_wall_drag_z_max_cells = read_float_constant(implementation_code, "rough_wall_drag_z_max_cells")
    generated_rough_wall_drag_declared = (
        generated_rough_wall_drag_alpha is not None
        or generated_rough_wall_drag_z_max_cells is not None
    )
    generated_rough_wall_drag_active = (
        (generated_rough_wall_drag_alpha or 0.0) > 0.0
        and (generated_rough_wall_drag_z_max_cells or 0.0) > 0.0
    )
    has_named_rough_wall_function_token = contains_any(
        implementation_code,
        [
            "rough_wall_function",
            "roughWallFunction",
            "wall_function",
            "wallFunction",
            "log-law",
            "log_law",
            "aerodynamic roughness boundary",
            "apply_rough_wall",
            "applyRoughWall",
        ],
    )
    has_rough_wall_function_token = (
        has_named_rough_wall_function_token or generated_rough_wall_drag_active
    )
    has_precursor_or_recycling_token = contains_any(
        implementation_code,
        ["precursor", "recycling_rescaling", "recycling-rescaling"],
    )
    has_non_reflecting_outlet_method = (
        has_regex(
            implementation_code,
            r"\b\w*(non_reflecting|nonReflecting|convective_outlet|convectiveOutlet|absorbing_outlet|absorbingOutlet|radiation_boundary|radiationBoundary)\w*\s*\(",
        )
        or has_regex(implementation_code, r"\b(sponge_layer|spongeLayer)\w*\s*(\[|=|\{|\()")
    )
    non_reflecting_outlet_call_count = count_regex(
        implementation_code,
        r"\b\w*(non_reflecting|nonReflecting|convective_outlet|convectiveOutlet|absorbing_outlet|absorbingOutlet|radiation_boundary|radiationBoundary|sponge_layer|spongeLayer)\w*\s*\(",
    )
    non_reflecting_outlet_call_pattern = (
        r"\b\w*(non_reflecting|nonReflecting|convective_outlet|convectiveOutlet|"
        r"absorbing_outlet|absorbingOutlet|radiation_boundary|radiationBoundary|"
        r"sponge_layer|spongeLayer)\w*\s*\("
    )
    has_non_reflecting_outlet_state_evidence = contains_any(
        implementation_code,
        [
            "sponge_strength",
            "sponge_sigma",
            "sponge_start",
            "sponge_length",
            "outlet_sponge",
            "absorbing_zone",
            "damping_zone",
            "convective_speed",
            "outlet_buffer",
            "outlet_previous",
            "pressure_outlet",
            "rho_outlet",
            "radiation_coefficient",
            "characteristic_outlet",
        ],
    ) or has_regex(
        implementation_code,
        r"\b(sponge|absorbing|damping|radiation|convective)\w*\s*(\[|=|\{)",
    )
    has_non_reflecting_outlet_face_application_evidence = has_contextual_boundary_call(
        implementation_code,
        non_reflecting_outlet_call_pattern,
        [
            r"\bTYPE_E\b",
            r"(?:x\s*==\s*0u?|x\s*==\s*Nx\s*-\s*1u?|y\s*==\s*0u?|y\s*==\s*Ny\s*-\s*1u?)",
        ],
    )
    has_non_reflecting_outlet_application_evidence = has_non_reflecting_outlet_face_application_evidence
    has_non_reflecting_outlet = (
        has_non_reflecting_outlet_method
        and has_non_reflecting_outlet_state_evidence
        and has_non_reflecting_outlet_application_evidence
    )
    has_periodic_side_top_method = has_regex(
        implementation_code,
        r"\b(periodic_[xyz]|periodicX|periodicY|periodicZ|set_periodic|setPeriodic|periodic_boundary|periodicBoundary)\w*\s*(\[|=|\{|\()",
    )
    periodic_side_top_call_count = count_regex(
        implementation_code,
        r"\b(periodic_[xyz]|periodicX|periodicY|periodicZ|set_periodic|setPeriodic|periodic_boundary|periodicBoundary)\w*\s*\(",
    )
    periodic_side_top_call_pattern = (
        r"\b(periodic_[xyz]|periodicX|periodicY|periodicZ|set_periodic|setPeriodic|"
        r"periodic_boundary|periodicBoundary)\w*\s*\("
    )
    has_periodic_pair_mapping_evidence = contains_any(
        implementation_code,
        [
            "periodic_pair",
            "periodicPair",
            "wrap_index",
            "wrapIndex",
            "wrapped_neighbor",
            "wrappedNeighbor",
            "opposite_face",
            "oppositeFace",
            "periodic_neighbor",
            "periodicNeighbor",
        ],
    ) or has_regex(
        implementation_code,
        r"%\s*N[xyz]\b|\(\s*\w+\s*\+\s*N[xyz]\s*[-+]",
    )
    has_periodic_side_top_face_application_evidence = has_contextual_boundary_call(
        implementation_code,
        periodic_side_top_call_pattern,
        [
            r"\bTYPE_E\b",
            r"(?:x\s*==\s*0u?|x\s*==\s*Nx\s*-\s*1u?|y\s*==\s*0u?|y\s*==\s*Ny\s*-\s*1u?|z\s*==\s*Nz\s*-\s*1u?)",
        ],
    )
    has_periodic_side_top_application_evidence = has_periodic_side_top_face_application_evidence
    has_periodic_side_top = (
        has_periodic_side_top_method
        and has_periodic_pair_mapping_evidence
        and has_periodic_side_top_application_evidence
    )
    has_named_rough_wall_function_method = has_regex(
        implementation_code,
        r"\b\w*(rough_wall_function|roughWallFunction|wall_function|wallFunction|log_law|logLaw|apply_rough_wall|applyRoughWall)\w*\s*\(",
    )
    has_rough_wall_function_method = (
        has_named_rough_wall_function_method or generated_rough_wall_drag_active
    )
    rough_wall_call_count = count_regex(
        implementation_code,
        r"\b\w*(rough_wall|roughWall|wall_function|wallFunction|log_law|logLaw|apply_rough_wall|applyRoughWall)\w*\s*\(",
    )
    rough_wall_call_pattern = (
        r"\b\w*(rough_wall|roughWall|wall_function|wallFunction|log_law|logLaw|"
        r"apply_rough_wall|applyRoughWall)\w*\s*\("
    )
    has_rough_wall_parameter_evidence = contains_any(
        implementation_code,
        [
            "roughness_height",
            "roughnessHeight",
            "roughness_length",
            "roughnessLength",
            "aerodynamic_roughness",
            "sand_grain",
            "ks_lbm",
            "ksLbm",
            "wall_shear",
            "wallShear",
            "friction_velocity",
            "frictionVelocity",
            "u_star",
            "uStar",
        ],
    ) or generated_rough_wall_drag_active
    has_rough_wall_action_evidence = contains_any(
        implementation_code,
        [
            "rough_wall_drag",
            "roughWallDrag",
            "roughness_drag",
            "roughnessDrag",
            "wall_function_shear",
            "wallFunctionShear",
            "equivalent_rough_wall_drag",
            "equivalentRoughWallDrag",
            "wall_shear_force",
            "wallShearForce",
            "applyRoughWall",
            "apply_rough_wall",
        ],
    ) or has_regex(
        implementation_code,
        r"\blbm\.(force|F)\.[xyz]\s*\[\s*n\s*\]\s*[+\-]?=",
    )
    if not has_rough_wall_function_method:
        has_rough_wall_action_evidence = False
    has_rough_wall_face_application_evidence = generated_rough_wall_drag_active or has_contextual_boundary_call(
        implementation_code,
        rough_wall_call_pattern,
        [
            r"(?:\bTYPE_S\b|ground|floor|wall)",
            r"(?:z\s*==\s*0u?|ground|floor)",
        ],
    )
    has_rough_wall_function = (
        has_rough_wall_function_method
        and has_rough_wall_parameter_evidence
        and has_rough_wall_action_evidence
        and has_rough_wall_face_application_evidence
    )
    has_precursor_or_recycling_method = has_regex(
        implementation_code,
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|recycleRescale)\w*\s*\(",
    )
    precursor_or_recycling_call_count = count_regex(
        implementation_code,
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|recycleRescale)\w*\s*\(",
    )
    precursor_or_recycling_call_pattern = (
        r"\b\w*(precursor|recycling_rescaling|recyclingRescaling|recycle_rescale|"
        r"recycleRescale)\w*\s*\("
    )
    has_precursor_or_recycling_field_evidence = contains_any(
        implementation_code,
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
            "precursor_snapshot",
            "precursorSnapshot",
            "precursor_vtk",
            "precursorVtk",
        ],
    )
    has_precursor_or_recycling_face_application_evidence = has_contextual_boundary_call(
        implementation_code,
        precursor_or_recycling_call_pattern,
        [
            r"\bTYPE_E\b",
            r"(?:x\s*==\s*0u?|x\s*==\s*Nx\s*-\s*1u?|y\s*==\s*0u?|y\s*==\s*Ny\s*-\s*1u?)",
        ],
    )
    has_precursor_or_recycling_application_evidence = has_precursor_or_recycling_face_application_evidence
    has_precursor_or_recycling = (
        has_precursor_or_recycling_method
        and has_precursor_or_recycling_field_evidence
        and has_precursor_or_recycling_application_evidence
    )
    empty_advanced_method_stub_count = count_empty_advanced_boundary_method_stubs(implementation_code)
    has_empty_advanced_method_stub = empty_advanced_method_stub_count > 0
    has_paper_grade_outlet_source = has_non_reflecting_outlet
    has_paper_grade_side_top_source = has_periodic_side_top
    has_paper_grade_rough_wall_source = has_rough_wall_function
    has_paper_grade_development_source = has_precursor_or_recycling
    paper_grade_required_source_evidence = {
        "non_reflecting_or_validated_outlet_state": has_paper_grade_outlet_source,
        "side_top_boundary_pair_mapping": has_paper_grade_side_top_source,
        "rough_wall_or_wall_function_action": has_paper_grade_rough_wall_source,
        "precursor_or_recycling_development_field": has_paper_grade_development_source,
    }
    missing_paper_grade_source_evidence = [
        key for key, supported in paper_grade_required_source_evidence.items() if supported is not True
    ]
    advanced_boundary_token_only = (
        (has_non_reflecting_outlet_token and not has_non_reflecting_outlet)
        or (has_periodic_side_top_token and not has_periodic_side_top)
        or (has_rough_wall_function_token and not has_rough_wall_function)
        or (has_precursor_or_recycling_token and not has_precursor_or_recycling)
    )
    has_boundary_source_comment = contains_any(comments, ["BoundaryProtocolAudit", "TYPE_E", "TYPE_S"])
    comments_contain_boundary_tokens = contains_any(
        comments,
        ["type_e", "type_s", "non_reflecting", "rough_wall", "precursor", "recycling_rescaling"],
    )

    simplified_type_e_box = (
        type_e_assignment_count >= 3
        and has_outlet_type_e
        and (has_lateral_type_e or has_top_type_e)
        and not has_non_reflecting_outlet
        and not has_periodic_side_top
        and not has_precursor_or_recycling
    )
    no_slip_solid_only = has_ground_no_slip and has_building_voxel_solid and not has_rough_wall_function

    source_boundary_coherent = (
        has_type_e_symbol
        and has_type_s_symbol
        and type_e_assignment_count > 0
        and type_s_assignment_count > 0
        and has_ground_no_slip
        and has_building_voxel_solid
    )
    source_advanced_code_evidence = (
        has_paper_grade_outlet_source
        and has_paper_grade_side_top_source
        and has_paper_grade_rough_wall_source
        and has_paper_grade_development_source
        and not has_empty_advanced_method_stub
    )
    has_complete_wind_tunnel_boundary_source = (
        source_advanced_code_evidence
        and source_boundary_coherent
        and not missing_paper_grade_source_evidence
    )
    has_empty_advanced_boundary_method_stub_only = (
        not missing_paper_grade_source_evidence and has_empty_advanced_method_stub
    )

    if has_complete_wind_tunnel_boundary_source:
        source_class = "wind_tunnel_equivalent_boundary_source"
    elif has_empty_advanced_boundary_method_stub_only:
        source_class = "advanced_boundary_empty_stub_only"
    elif not missing_paper_grade_source_evidence and not source_boundary_coherent:
        source_class = "advanced_boundary_without_coherent_type_e_type_s_setup"
    elif has_precursor_or_recycling:
        source_class = "precursor_or_recycling_boundary_partial"
    elif has_non_reflecting_outlet and (has_periodic_side_top or has_rough_wall_function):
        source_class = "advanced_boundary_source_evidence"
    elif has_profile_maintenance_buffer and has_rough_wall_function:
        source_class = "profile_maintenance_buffer_diagnostic"
    elif (
        has_non_reflecting_outlet_method
        or has_periodic_side_top_method
        or has_rough_wall_function_method
        or has_precursor_or_recycling_method
    ):
        source_class = "named_boundary_method_without_field_evidence"
    elif simplified_type_e_box:
        source_class = "simplified_type_e_box"
    elif type_e_assignment_count > 0:
        source_class = "partial_type_e_boundary_source"
    elif type_s_assignment_count > 0:
        source_class = "solid_only_boundary_source"
    else:
        source_class = "none"

    if has_complete_wind_tunnel_boundary_source:
        source_fidelity_class = "wind_tunnel_equivalent_complete"
    elif has_empty_advanced_boundary_method_stub_only:
        source_fidelity_class = "advanced_boundary_empty_stub_only"
    elif source_class == "advanced_boundary_without_coherent_type_e_type_s_setup":
        source_fidelity_class = "advanced_boundary_without_coherent_type_e_type_s_setup"
    elif source_class in {
        "precursor_or_recycling_boundary_partial",
        "advanced_boundary_source_evidence",
        "named_boundary_method_without_field_evidence",
    }:
        source_fidelity_class = "advanced_boundary_incomplete"
    elif source_class == "profile_maintenance_buffer_diagnostic":
        source_fidelity_class = "diagnostic_profile_maintenance_buffer"
    else:
        source_fidelity_class = source_class

    source_wind_tunnel_equivalent = has_complete_wind_tunnel_boundary_source
    source_simplified = source_class in {
        "simplified_type_e_box",
        "partial_type_e_boundary_source",
        "solid_only_boundary_source",
        "none",
    }
    simplified_wind_tunnel_surrogate_reasons: List[str] = []
    if source_simplified:
        simplified_wind_tunnel_surrogate_reasons.append(f"source_class_is_simplified:{source_class}")
    if simplified_type_e_box:
        simplified_wind_tunnel_surrogate_reasons.append("simplified_type_e_box")
    if no_slip_solid_only:
        simplified_wind_tunnel_surrogate_reasons.append("no_slip_solid_only_without_rough_wall_or_precursor")
    if has_fixed_mean_outlet_lateral_top_treatment and not has_non_reflecting_outlet:
        simplified_wind_tunnel_surrogate_reasons.append(
            "fixed_mean_outlet_lateral_top_without_non_reflecting_source"
        )
    if not source_wind_tunnel_equivalent:
        simplified_wind_tunnel_surrogate_reasons.append("not_wind_tunnel_equivalent")
    for missing_key in missing_paper_grade_source_evidence:
        simplified_wind_tunnel_surrogate_reasons.append(f"missing_{missing_key}")
    has_simplified_wind_tunnel_surrogate = bool(simplified_wind_tunnel_surrogate_reasons)
    simplified_wind_tunnel_surrogate_gate = (
        "fail" if has_simplified_wind_tunnel_surrogate else "pass"
    )

    metadata_claims_advanced = any(
        token in metadata_boundary_claim_text
        for token in [
            "non_reflecting",
            "non-reflecting",
            "validated_boundary_model",
            "wind_tunnel_protocol_matched",
            "precursor_boundary",
            "recycling_boundary",
        ]
    )

    if not source_boundary_coherent:
        reasons.append("boundary_source_missing_coherent_type_e_type_s_setup")
    if type_e_assignment_count > 0 and source_class in {"simplified_type_e_box", "partial_type_e_boundary_source"}:
        if not has_type_e_velocity_initialization:
            reasons.append("type_e_boundary_velocity_initialization_missing_or_incomplete")
        if has_profile_inlet and not has_profile_type_e_velocity_initialization:
            reasons.append("profile_type_e_boundary_velocity_initialization_missing")
        if has_type_e_velocity_initialization and not has_type_e_velocity_initialization_before_device_upload:
            reasons.append("type_e_boundary_velocity_initialization_not_uploaded_after_initialization")
    if metadata_claims_advanced and not source_wind_tunnel_equivalent:
        reasons.append("metadata_claims_advanced_boundary_without_source_evidence")
    if advanced_boundary_token_only:
        reasons.append("advanced_boundary_tokens_without_code_evidence")
    if has_non_reflecting_outlet_method and not has_non_reflecting_outlet_state_evidence:
        reasons.append("non_reflecting_boundary_source_missing_state_evidence")
    if (
        has_non_reflecting_outlet_method
        and has_non_reflecting_outlet_state_evidence
        and not has_non_reflecting_outlet_application_evidence
    ):
        reasons.append("non_reflecting_boundary_source_missing_application_evidence")
    if (
        has_non_reflecting_outlet_method
        and has_non_reflecting_outlet_state_evidence
        and not has_non_reflecting_outlet_face_application_evidence
    ):
        reasons.append("non_reflecting_boundary_source_missing_outlet_face_application_evidence")
    if has_periodic_side_top_method and not has_periodic_pair_mapping_evidence:
        reasons.append("periodic_boundary_source_missing_pair_mapping_evidence")
    if has_periodic_side_top_method and has_periodic_pair_mapping_evidence and not has_periodic_side_top_application_evidence:
        reasons.append("periodic_boundary_source_missing_application_evidence")
    if has_periodic_side_top_method and has_periodic_pair_mapping_evidence and not has_periodic_side_top_face_application_evidence:
        reasons.append("periodic_boundary_source_missing_side_top_face_application_evidence")
    if has_rough_wall_function_method and not has_rough_wall_parameter_evidence:
        reasons.append("rough_wall_boundary_source_missing_roughness_parameter_evidence")
    if has_rough_wall_function_method and not has_rough_wall_action_evidence:
        reasons.append("rough_wall_boundary_source_missing_wall_action_evidence")
    if has_rough_wall_function_method and has_rough_wall_parameter_evidence and has_rough_wall_action_evidence and not has_rough_wall_face_application_evidence:
        reasons.append("rough_wall_boundary_source_missing_application_evidence")
        reasons.append("rough_wall_boundary_source_missing_ground_face_application_evidence")
    if has_precursor_or_recycling_method and not has_precursor_or_recycling_field_evidence:
        reasons.append("precursor_recycling_boundary_source_missing_recycled_field_evidence")
    if has_precursor_or_recycling_method and has_precursor_or_recycling_field_evidence and not has_precursor_or_recycling_application_evidence:
        reasons.append("precursor_recycling_boundary_source_missing_application_evidence")
    if has_precursor_or_recycling_method and has_precursor_or_recycling_field_evidence and not has_precursor_or_recycling_face_application_evidence:
        reasons.append("precursor_recycling_boundary_source_missing_inlet_face_application_evidence")
    if has_empty_advanced_method_stub:
        reasons.append("advanced_boundary_method_empty_stub_definition")

    source_gate = "pass" if not reasons else "fail"
    paper_reasons: List[str] = []
    if not source_wind_tunnel_equivalent:
        paper_reasons.append("boundary_source_not_wind_tunnel_equivalent")
    if source_fidelity_class != "wind_tunnel_equivalent_complete":
        paper_reasons.append(f"boundary_source_fidelity_class_not_paper_grade:{source_fidelity_class}")
    if not source_advanced_code_evidence:
        paper_reasons.append("boundary_source_missing_advanced_code_evidence")
    if not source_boundary_coherent:
        paper_reasons.append("boundary_source_not_coherent_type_e_type_s_setup")
    if source_simplified:
        paper_reasons.append("boundary_source_simplified_type_e_or_solid_only")
    if no_slip_solid_only:
        paper_reasons.append("ground_and_buildings_no_slip_without_rough_wall_or_precursor")
    if has_fixed_mean_outlet_lateral_top_treatment and not has_non_reflecting_outlet:
        paper_reasons.append(
            "outlet_lateral_top_fixed_mean_velocity_equilibrium_not_validated_pressure_or_non_reflecting_boundary"
        )
    if source_class == "named_boundary_method_without_field_evidence":
        paper_reasons.append("boundary_method_named_without_concrete_state_or_field_evidence")
    if has_empty_advanced_method_stub:
        paper_reasons.append("advanced_boundary_method_empty_stub_definition")
    for missing_key in missing_paper_grade_source_evidence:
        paper_reasons.append(f"missing_{missing_key}")
    if simplified_wind_tunnel_surrogate_gate != "pass":
        paper_reasons.append("boundary_source_simplified_wind_tunnel_surrogate_gate_not_pass")
    if has_simplified_wind_tunnel_surrogate:
        paper_reasons.append("boundary_source_has_simplified_wind_tunnel_surrogate")
    for surrogate_reason in simplified_wind_tunnel_surrogate_reasons:
        paper_reasons.append(f"boundary_source_simplified_wind_tunnel_surrogate_reason:{surrogate_reason}")
    paper_gate = "pass" if not paper_reasons else "fail"

    if source_gate != "pass":
        if not source_boundary_coherent:
            development_stage = "fix_boundary_source_coherence_before_cfd"
            development_duration = "minutes"
            development_reason = "Boundary source lacks a coherent TYPE_E/TYPE_S setup."
        elif has_empty_advanced_method_stub or source_class in {
            "advanced_boundary_empty_stub_only",
            "named_boundary_method_without_field_evidence",
            "advanced_boundary_without_coherent_type_e_type_s_setup",
        }:
            development_stage = "implement_boundary_methods_before_cfd"
            development_duration = "code_then_short_cfd"
            development_reason = "Boundary method names or stubs exist, but concrete field/state application evidence is missing."
        else:
            development_stage = "fix_boundary_source_before_cfd"
            development_duration = "minutes"
            development_reason = "Boundary source audit reports implementation blockers."
        development_runs_cfd_next = False
        development_next_cfd_scope = "none_until_boundary_source_gate_passes"
    elif paper_gate != "pass":
        if source_class == "profile_maintenance_buffer_diagnostic":
            development_stage = "eligible_for_short_diagnostic_native_canary"
            development_duration = "code_then_short_cfd"
            development_reason = "Boundary source has coherent TYPE_E/TYPE_S setup plus diagnostic rough-wall and profile-maintenance FORCE_FIELD buffers; use only a short canary to check numerical direction before paper-length runs."
            development_runs_cfd_next = True
            development_next_cfd_scope = "short_native_canary_only_no_paper_metrics"
        elif simplified_wind_tunnel_surrogate_gate != "pass":
            development_stage = "replace_simplified_wind_tunnel_surrogate_boundary_before_cfd"
            development_duration = "code_then_short_cfd"
            development_reason = "The current source is a simplified wind-tunnel surrogate boundary, so long CFD would not address the protocol-level error."
            development_runs_cfd_next = False
            development_next_cfd_scope = "none_until_paper_grade_boundary_source_gate_passes"
        else:
            development_stage = "resolve_boundary_wall_protocol_evidence"
            development_duration = "minutes"
            development_reason = "Boundary source passes implementation checks, but paper-grade wind-tunnel-equivalent outlet, side/top, rough-wall, or development-field evidence is incomplete."
            development_runs_cfd_next = False
            development_next_cfd_scope = "none_until_paper_grade_boundary_source_gate_passes"
    else:
        development_stage = "eligible_for_short_native_canary"
        development_duration = "short_cfd"
        development_reason = "Boundary source audit is paper-grade; proceed only to a short native canary before any paper-length run."
        development_runs_cfd_next = True
        development_next_cfd_scope = "short_native_canary_only"

    report: Dict[str, Any] = {
        "schema": "citylbm.boundary_source_audit.v1",
        "generated_at_utc": utc_now(),
        "setup_cpp": str(setup_path),
        "setup_cpp_sha256": setup_hash,
        "defines_hpp": str(defines_path) if defines_path.exists() else "",
        "defines_hpp_sha256": defines_hash,
        "defines_hpp_used": bool(defines_source),
        "metadata": str(metadata_path) if metadata_path else "",
        "metadata_boundary_summary": boundary_summary,
        "metadata_boundary_types": boundary_types if isinstance(boundary_types, dict) else {},
        "metadata_claims_advanced_boundary": metadata_claims_advanced,
        "has_equilibrium_boundaries_define": has_equilibrium_boundaries,
        "has_type_e_define": has_type_e_define,
        "has_type_s_define": has_type_s_define,
        "has_type_e_symbol": has_type_e_symbol,
        "has_type_s_symbol": has_type_s_symbol,
        "type_e_assignment_count": type_e_assignment_count,
        "type_s_assignment_count": type_s_assignment_count,
        "has_profile_inlet": has_profile_inlet,
        "has_outlet_type_e": has_outlet_type_e,
        "has_lateral_type_e": has_lateral_type_e,
        "has_top_type_e": has_top_type_e,
        "has_type_e_velocity_initialization": has_type_e_velocity_initialization,
        "has_type_e_velocity_initialization_guard": type_e_velocity_initialization["guard"],
        "has_type_e_velocity_initialization_coordinates": type_e_velocity_initialization["coordinates"],
        "has_type_e_velocity_initialization_velocity_write": type_e_velocity_initialization["velocity_write"],
        "type_e_velocity_initialization_mode": type_e_velocity_initialization.get("mode", ""),
        "type_e_velocity_initialization_source_index": type_e_velocity_initialization_index,
        "flags_write_to_device_source_index": flags_write_to_device_index,
        "u_write_to_device_source_index": u_write_to_device_index,
        "has_type_e_velocity_initialization_before_device_upload": has_type_e_velocity_initialization_before_device_upload,
        "has_flags_device_upload_after_type_e_velocity_initialization": has_flags_device_upload_after_type_e_velocity_initialization,
        "has_u_device_upload_after_type_e_velocity_initialization": has_u_device_upload_after_type_e_velocity_initialization,
        "has_profile_type_e_velocity_initialization": has_profile_type_e_velocity_initialization,
        "has_uniform_type_e_velocity_initialization": has_uniform_type_e_velocity_initialization,
        "has_fixed_mean_type_e_boundary_velocity": has_fixed_mean_type_e_boundary_velocity,
        "fixed_mean_boundary_metadata": fixed_mean_boundary_metadata,
        "has_fixed_mean_outlet_lateral_top_treatment": has_fixed_mean_outlet_lateral_top_treatment,
        "has_profile_maintenance_buffer": has_profile_maintenance_buffer,
        "fixed_mean_outlet_lateral_top_treatment_gate": fixed_mean_outlet_lateral_top_treatment_gate,
        "has_ground_no_slip": has_ground_no_slip,
        "has_building_voxel_solid": has_building_voxel_solid,
        "has_non_reflecting_outlet_evidence": has_non_reflecting_outlet,
        "has_non_reflecting_outlet_method": has_non_reflecting_outlet_method,
        "has_non_reflecting_outlet_state_evidence": has_non_reflecting_outlet_state_evidence,
        "has_non_reflecting_outlet_application_evidence": has_non_reflecting_outlet_application_evidence,
        "has_non_reflecting_outlet_face_application_evidence": has_non_reflecting_outlet_face_application_evidence,
        "non_reflecting_outlet_call_count": non_reflecting_outlet_call_count,
        "has_non_reflecting_outlet_token": has_non_reflecting_outlet_token,
        "has_periodic_side_top_evidence": has_periodic_side_top,
        "has_periodic_side_top_method": has_periodic_side_top_method,
        "has_periodic_pair_mapping_evidence": has_periodic_pair_mapping_evidence,
        "has_periodic_side_top_application_evidence": has_periodic_side_top_application_evidence,
        "has_periodic_side_top_face_application_evidence": has_periodic_side_top_face_application_evidence,
        "periodic_side_top_call_count": periodic_side_top_call_count,
        "has_periodic_side_top_token": has_periodic_side_top_token,
        "has_rough_wall_function_evidence": has_rough_wall_function,
        "has_rough_wall_function_method": has_rough_wall_function_method,
        "has_rough_wall_parameter_evidence": has_rough_wall_parameter_evidence,
        "has_rough_wall_action_evidence": has_rough_wall_action_evidence,
        "has_rough_wall_application_evidence": has_rough_wall_face_application_evidence,
        "has_rough_wall_ground_face_application_evidence": has_rough_wall_face_application_evidence,
        "rough_wall_call_count": rough_wall_call_count,
        "has_rough_wall_function_token": has_rough_wall_function_token,
        "has_named_rough_wall_function_token": has_named_rough_wall_function_token,
        "has_named_rough_wall_function_method": has_named_rough_wall_function_method,
        "generated_rough_wall_drag_declared": generated_rough_wall_drag_declared,
        "generated_rough_wall_drag_active": generated_rough_wall_drag_active,
        "generated_rough_wall_drag_alpha": generated_rough_wall_drag_alpha,
        "generated_rough_wall_drag_z_max_cells": generated_rough_wall_drag_z_max_cells,
        "has_precursor_or_recycling_boundary_evidence": has_precursor_or_recycling,
        "has_precursor_or_recycling_boundary_method": has_precursor_or_recycling_method,
        "has_precursor_or_recycling_boundary_field_evidence": has_precursor_or_recycling_field_evidence,
        "has_precursor_or_recycling_boundary_application_evidence": has_precursor_or_recycling_application_evidence,
        "has_precursor_or_recycling_boundary_inlet_face_application_evidence": (
            has_precursor_or_recycling_face_application_evidence
        ),
        "precursor_or_recycling_call_count": precursor_or_recycling_call_count,
        "has_precursor_or_recycling_boundary_token": has_precursor_or_recycling_token,
        "has_empty_advanced_boundary_method_stub": has_empty_advanced_method_stub,
        "empty_advanced_boundary_method_stub_count": empty_advanced_method_stub_count,
        "has_paper_grade_outlet_source": has_paper_grade_outlet_source,
        "has_paper_grade_side_top_source": has_paper_grade_side_top_source,
        "has_paper_grade_rough_wall_source": has_paper_grade_rough_wall_source,
        "has_paper_grade_development_source": has_paper_grade_development_source,
        "paper_grade_required_source_evidence": paper_grade_required_source_evidence,
        "missing_paper_grade_source_evidence": missing_paper_grade_source_evidence,
        "advanced_boundary_token_only": advanced_boundary_token_only,
        "advanced_boundary_evidence_uses_comment_stripped_code": True,
        "all_boundary_implementation_evidence_uses_comment_stripped_code": True,
        "comments_contain_boundary_tokens": comments_contain_boundary_tokens,
        "boundary_source_advanced_code_evidence": source_advanced_code_evidence,
        "boundary_source_fidelity_class": source_fidelity_class,
        "boundary_source_has_complete_wind_tunnel_evidence": has_complete_wind_tunnel_boundary_source,
        "boundary_source_has_empty_advanced_method_stub_only": has_empty_advanced_boundary_method_stub_only,
        "has_boundary_source_comment": has_boundary_source_comment,
        "boundary_source_method_class": source_class,
        "boundary_source_coherent": source_boundary_coherent,
        "boundary_source_simplified": source_simplified,
        "boundary_source_has_simplified_wind_tunnel_surrogate": has_simplified_wind_tunnel_surrogate,
        "boundary_source_simplified_wind_tunnel_surrogate_gate": simplified_wind_tunnel_surrogate_gate,
        "boundary_source_simplified_wind_tunnel_surrogate_reasons": (
            simplified_wind_tunnel_surrogate_reasons or ["not_simplified_wind_tunnel_surrogate"]
        ),
        "boundary_source_simplified_wind_tunnel_surrogate_reasons_csv": ";".join(
            simplified_wind_tunnel_surrogate_reasons or ["not_simplified_wind_tunnel_surrogate"]
        ),
        "boundary_source_wind_tunnel_equivalent": source_wind_tunnel_equivalent,
        "boundary_source_gate": source_gate,
        "boundary_source_gate_reasons": reasons or ["boundary_source_consistent_with_declared_metadata"],
        "boundary_source_gate_reasons_csv": ";".join(reasons or ["boundary_source_consistent_with_declared_metadata"]),
        "paper_grade_boundary_source_gate": paper_gate,
        "paper_grade_boundary_source_gate_reasons": paper_reasons or ["boundary_source_wind_tunnel_equivalent"],
        "paper_grade_boundary_source_gate_reasons_csv": ";".join(paper_reasons or ["boundary_source_wind_tunnel_equivalent"]),
        "development_acceleration_stage": development_stage,
        "development_acceleration_duration_class": development_duration,
        "development_acceleration_runs_cfd_next": development_runs_cfd_next,
        "development_acceleration_next_cfd_scope": development_next_cfd_scope,
        "development_acceleration_reason": development_reason,
        "long_cfd_allowed_by_boundary_source_audit": source_gate == "pass" and paper_gate == "pass",
        "recommended_next_action": (
            "For paper-grade AIJ validation, replace or justify the simplified TYPE_E outlet/lateral/top setup "
            "with archived wind-tunnel-equivalent boundary evidence, non-reflecting/precursor/recycling boundaries, "
            "and a rough-wall or documented floor-roughness treatment."
        ),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "boundary_source_gate="
        f"{source_gate}; paper_grade_boundary_source_gate={paper_gate}; "
        f"method_class={source_class}; reasons={';'.join(report['boundary_source_gate_reasons'])}"
    )
    return 0 if source_gate == "pass" and paper_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
