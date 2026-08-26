#!/usr/bin/env python3
"""Prepare and optionally run a strict native FluidX3D validation case.

This runner is intentionally conservative. By default it only validates the
FluidX3D source root and CityLBM-generated case package, then writes a manifest.
Use --install, --build, and --run explicitly on the experiment workstation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


REQUIRED_SOURCE_FILES = [
    ("Native FluidX3D original setup", Path("src") / "setup.cpp"),
    ("Native FluidX3D original defines", Path("src") / "defines.hpp"),
    ("Native FluidX3D lbm.hpp", Path("src") / "lbm.hpp"),
    ("Native FluidX3D lbm.cpp", Path("src") / "lbm.cpp"),
]

REQUIRED_CASE_FILES = [
    ("Case metadata", Path("case_metadata.json")),
    ("Domain origin", Path("domain_origin.json")),
    ("Validation protocol audit", Path("validation_protocol_audit.json")),
]

REQUIRED_CASE_FILE_CANDIDATES = [
    ("FluidX3D setup", [Path("src") / "setup.cpp", Path("setup.cpp")]),
    ("FluidX3D defines", [Path("src") / "defines.hpp", Path("defines.hpp")]),
]

OPTIONAL_CASE_FILES = [
    ("Buildings STL", Path("buildings.stl")),
    ("Boundary evidence", Path("boundary_conditions.json")),
    ("Roughness layout", Path("roughness_layout.csv")),
    ("Equivalent precursor evidence", Path("equivalent_precursor_evidence.json")),
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

PAPER_GRADE_PROTOCOL_AUDIT_GATES = {
    "pass",
    "paper_grade",
    "paper_grade_candidate",
    "ready_for_validation_run",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a strict native FluidX3D run manifest, with optional install/build/run steps."
    )
    parser.add_argument("--case-dir", required=True, help="CityLBM-generated native case directory.")
    parser.add_argument("--fluidx3d-source", required=True, help="Explicit native FluidX3D source root.")
    parser.add_argument("--solver-cwd", default="", help="Optional FluidX3D run working directory.")
    parser.add_argument("--out", required=True, help="Output native_fluidx3d_baseline_manifest.json path.")
    parser.add_argument(
        "--metadata",
        default="",
        help="Optional case metadata JSON. Defaults to case_dir/case_metadata.json.",
    )
    parser.add_argument(
        "--validation-protocol-audit",
        default="",
        help=(
            "Optional validation_protocol_audit.json path. "
            "Defaults to case_dir/validation_protocol_audit.json."
        ),
    )
    parser.add_argument("--inlet-source-audit", default="", help="Optional inlet source audit JSON recorded with the manifest.")
    parser.add_argument("--boundary-source-audit", default="", help="Optional boundary source audit JSON recorded with the manifest.")
    parser.add_argument(
        "--coordinate-probe-protocol-audit",
        default="",
        help="Optional coordinate_probe_protocol_audit.json gate for axes, probe subset and Uref protocol.",
    )
    parser.add_argument(
        "--inlet-correlation-audit",
        default="",
        help="Optional inlet_correlation_audit.json from real VTK frames. Required for paper-grade turbulent-inlet claims.",
    )
    parser.add_argument("--baseline-id", default="", help="Stable ID for this native baseline.")
    parser.add_argument("--install", action="store_true", help="Replace FluidX3D src/setup.cpp and src/defines.hpp from case.")
    parser.add_argument("--build", action="store_true", help="Build the native FluidX3D source tree after install/preflight.")
    parser.add_argument("--run", action="store_true", help="Run FluidX3D.exe after build/preflight.")
    parser.add_argument(
        "--disable-graphics-for-run",
        action="store_true",
        help="Comment out GRAPHICS/INTERACTIVE_GRAPHICS in installed defines.hpp so validation runs write batch VTK.",
    )
    parser.add_argument("--msbuild", default="", help="Optional MSBuild executable path.")
    parser.add_argument("--configuration", default="Release", help="MSBuild configuration.")
    parser.add_argument("--platform", default="x64", help="MSBuild platform.")
    parser.add_argument(
        "--platform-toolset",
        default="",
        help="Optional MSBuild PlatformToolset override, e.g. v143 for VS2022 when the source project still requests v142.",
    )
    parser.add_argument(
        "--windows-sdk-version",
        default="auto",
        help=(
            "Optional MSBuild WindowsTargetPlatformVersion. Use 'auto' to pin the newest installed "
            "Windows 10 SDK and avoid MSBuild probing inaccessible per-user SDK folders; use an empty "
            "string to keep MSBuild default probing."
        ),
    )
    parser.add_argument("--exe", default="", help="Optional FluidX3D executable path.")
    parser.add_argument("--timeout-seconds", type=int, default=0, help="Optional solver timeout, 0 disables timeout.")
    parser.add_argument("--expected-aij-case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--expected-wind-direction", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument("--official", default="", help="Optional official RS/probe CSV preflighted before CFD execution.")
    parser.add_argument("--af-csv", default="", help="Optional official AF inlet profile CSV with z,U,k columns.")
    parser.add_argument("--official-condition-filter", default="", help="Optional official RS condition/state filter, e.g. ac for AIJ Case E.")
    parser.add_argument("--official-wind-filter", default="", help="Optional official RS wind-direction filter. Defaults to --expected-wind-direction.")
    parser.add_argument("--expected-probe-row-count", type=int, default=0, help="Expected official rows after case/wind filtering.")
    parser.add_argument("--expected-probe-z", type=float, default=None, help="Expected official probe height in meters, e.g. 2.0 for Case E.")
    parser.add_argument("--expected-probe-z-min", type=float, default=None, help="Minimum official probe height for multi-height cases.")
    parser.add_argument("--expected-probe-z-max", type=float, default=None, help="Maximum official probe height for multi-height cases.")
    parser.add_argument("--expected-probe-z-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--z-ref", type=float, default=None, help="Reference height used to bind --expected-uref to AF U(z_ref).")
    parser.add_argument("--expected-uref", type=float, default=None, help="Expected reference velocity in m/s for normalization.")
    parser.add_argument("--uref-af-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--expected-wind-vector", default="", help="Expected airflow vector x,y,z, e.g. 0,-1,0.")
    parser.add_argument("--wind-vector-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--require-af-k", action="store_true", help="Require AF CSV to contain a valid k(m2/s2) column.")
    parser.add_argument("--time-steps", type=int, default=None, help="Planned solver steps recorded in SharedRunConditions.")
    parser.add_argument("--vtk-save-interval", type=int, default=None, help="Planned VTK save interval.")
    parser.add_argument(
        "--vtk-save-start-step",
        type=int,
        default=None,
        help="First solver step planned for VTK output. If omitted, reads VtkOutput.SaveStartStep from case metadata when present.",
    )
    parser.add_argument("--expected-vtk-frame-count", type=int, default=None, help="Planned VTK frame count.")
    parser.add_argument("--average-last-n", type=int, default=40, help="Required final VTK averaging-window frame count.")
    parser.add_argument("--min-vtk-frames", type=int, default=40, help="Minimum planned VTK frames for strict validation.")
    parser.add_argument("--min-vtk-step-span", type=int, default=20000, help="Minimum planned final-window solver-step span.")
    parser.add_argument("--min-stg-refreshes", type=int, default=200, help="Minimum planned synthetic-inlet refreshes in the final averaging window.")
    parser.add_argument(
        "--min-flow-throughs",
        type=float,
        default=3.0,
        help="Minimum planned domain flow-through count before a native run can support paper-grade validation.",
    )
    parser.add_argument(
        "--allow-diagnostic-execution",
        action="store_true",
        help="Allow install/build/run even when strict preflight gates are diagnostic_only. Use only for debugging, never for paper-grade claims.",
    )
    parser.add_argument("--output-dir", default="", help="Directory to inspect for u-*.vtk after run.")
    parser.add_argument("--vtk-pattern", default="u-*.vtk", help="VTK glob pattern.")
    parser.add_argument("--inlet-diagnostics-csv", default="", help="Optional runtime inlet turbulence diagnostics CSV.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_or_empty(path: Optional[Path]) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    return sha256(path)


def json_load(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def parse_grid_dimensions_from_defines(path: Path) -> Optional[Tuple[int, int, int]]:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    values: Dict[str, int] = {}
    for axis in ("SX", "SY", "SZ"):
        match = re.search(rf"^\s*#\s*define\s+{axis}\s+(\d+)\s*u?\b", text, re.MULTILINE)
        if not match:
            return None
        values[axis] = int(match.group(1))
    return values["SX"], values["SY"], values["SZ"]


def planned_vtk_bytes_for_grid(dimensions: Optional[Tuple[int, int, int]], frame_count: Optional[int]) -> Dict[str, Any]:
    if dimensions is None or frame_count is None or frame_count <= 0:
        return {"Gate": "not_applicable", "EstimatedRequiredBytes": 0, "Dimensions": dimensions, "FrameCount": frame_count}
    cell_count = int(dimensions[0]) * int(dimensions[1]) * int(dimensions[2])
    bytes_per_frame = cell_count * 3 * 4
    estimated = int(math.ceil(bytes_per_frame * int(frame_count) * 1.05))
    return {
        "Gate": "pass",
        "Dimensions": list(dimensions),
        "FrameCount": int(frame_count),
        "CellCount": cell_count,
        "BytesPerFrame": bytes_per_frame,
        "SafetyFactor": 1.05,
        "EstimatedRequiredBytes": estimated,
    }


def audit_output_disk_space(
    output_dir: Path,
    dimensions: Optional[Tuple[int, int, int]],
    frame_count: Optional[int],
    *,
    require_for_run: bool,
    free_bytes_override: Optional[int] = None,
) -> Dict[str, Any]:
    estimate = planned_vtk_bytes_for_grid(dimensions, frame_count)
    if not require_for_run:
        return {**estimate, "Gate": "not_applicable", "Reasons": [], "ReasonsCsv": ""}
    required = int(estimate.get("EstimatedRequiredBytes") or 0)
    free_bytes = free_bytes_override
    if free_bytes is None:
        probe = output_dir
        while not probe.exists() and probe.parent != probe:
            probe = probe.parent
        free_bytes = shutil.disk_usage(probe).free if probe.exists() else 0
    reasons: List[str] = []
    if required <= 0:
        reasons.append("estimated_vtk_bytes_unavailable")
    elif int(free_bytes) < required:
        reasons.append(f"free_bytes_{int(free_bytes)}_below_estimated_vtk_bytes_{required}")
    return {
        **estimate,
        "Gate": "pass" if not reasons else "blocked",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "OutputDir": str(output_dir),
        "FreeBytes": int(free_bytes),
    }


def as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return None


def as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None
        if not parsed.is_integer():
            return None
        return int(parsed)


def as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        try:
            parsed = float(str(value).strip())
        except (TypeError, ValueError):
            return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def normalized_name(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def normalized_identity(value: Any) -> str:
    return normalized_name(value)


def find_column(fieldnames: Sequence[str], candidates: Sequence[str]) -> str:
    normalized = {normalized_name(name): name for name in fieldnames}
    for candidate in candidates:
        match = normalized.get(normalized_name(candidate))
        if match:
            return match
    return ""


def read_csv_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return rows, fieldnames


def parse_vector(value: Any) -> Optional[Tuple[float, float, float]]:
    if value is None or value == "":
        return None
    if isinstance(value, dict):
        values = [
            as_float(value.get("X", value.get("x"))),
            as_float(value.get("Y", value.get("y"))),
            as_float(value.get("Z", value.get("z"))),
        ]
        if any(item is None for item in values):
            return None
        return (float(values[0]), float(values[1]), float(values[2]))
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        values = [as_float(item) for item in value[:3]]
    else:
        text = str(value).strip().strip("()[]")
        parts = [part for part in re.split(r"[,\s;]+", text) if part]
        if len(parts) < 3:
            return None
        values = [as_float(part) for part in parts[:3]]
    if any(item is None for item in values):
        return None
    return (float(values[0]), float(values[1]), float(values[2]))


def vectors_match(
    actual: Optional[Tuple[float, float, float]],
    expected: Optional[Tuple[float, float, float]],
    tolerance: float,
) -> bool:
    if actual is None or expected is None:
        return False
    return all(abs(actual[i] - expected[i]) <= tolerance for i in range(3))


def metadata_value(metadata: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in metadata:
            return metadata.get(key)
    return None


def metadata_bool(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[bool]:
    return as_bool(metadata_value(metadata, keys))


def metadata_int(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[int]:
    return as_int(metadata_value(metadata, keys))


def metadata_float(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[float]:
    return as_float(metadata_value(metadata, keys))


def metadata_vtk_save_start_step(metadata: Dict[str, Any]) -> Optional[int]:
    direct = metadata_int(metadata, ["VtkSaveStartStep", "vtk_save_start_step", "SaveStartStep"])
    if direct is not None:
        return direct
    vtk_output = metadata.get("VtkOutput") or metadata.get("vtk_output")
    if isinstance(vtk_output, dict):
        return as_int(metadata_value(vtk_output, ["SaveStartStep", "save_start_step", "VtkSaveStartStep"]))
    return None


def resolve_runtime_inlet_diagnostics_path(
    explicit: str,
    metadata: Dict[str, Any],
    *,
    case_dir: Path,
    solver_cwd: Path,
    output_dir: Path,
    run_requested: bool,
    output_dir_requested: bool,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    explicit_text = str(explicit or "").strip()
    if explicit_text:
        path = Path(explicit_text).expanduser().resolve()
        return path, {
            "Requested": True,
            "Source": "argument",
            "Raw": explicit_text,
            "Path": str(path),
            "Candidates": [str(path)],
            "Reason": "explicit_argument",
        }

    raw = str(
        metadata_value(
            metadata,
            [
                "RuntimeInletDiagnosticsCsv",
                "runtime_inlet_diagnostics_csv",
                "InletDiagnosticsCsv",
                "inlet_diagnostics_csv",
            ],
        )
        or ""
    ).strip()
    if not raw:
        return None, {
            "Requested": False,
            "Source": "missing",
            "Raw": "",
            "Path": "",
            "Candidates": [],
            "Reason": "metadata_runtime_inlet_diagnostics_csv_missing",
        }

    raw_path = Path(raw).expanduser()
    if raw_path.is_absolute():
        candidates = [raw_path.resolve()]
    else:
        candidates = [
            (solver_cwd / raw_path).resolve(),
            (output_dir / raw_path).resolve(),
            (case_dir / "output" / raw_path).resolve(),
            (case_dir / raw_path).resolve(),
        ]
    existing = next((candidate for candidate in candidates if candidate.is_file()), None)
    selected = existing or candidates[0]
    should_request = run_requested or output_dir_requested or existing is not None
    return (selected if should_request else None), {
        "Requested": should_request,
        "Source": "metadata",
        "Raw": raw,
        "Path": str(selected) if should_request else "",
        "Candidates": [str(candidate) for candidate in candidates],
        "ExistingCandidate": str(existing) if existing is not None else "",
        "Reason": "run_or_output_requested" if should_request else "not_requested_without_run_or_existing_csv",
    }


def synthetic_inlet_expects_runtime_diagnostics(metadata: Dict[str, Any]) -> bool:
    injected = metadata_bool(
        metadata,
        [
            "SyntheticTurbulentInletInjected",
            "SyntheticTurbulentInletRequested",
            "SyntheticInletInjected",
            "SyntheticInletRequested",
        ],
    )
    writer = str(
        metadata_value(
            metadata,
            [
                "RuntimeInletDiagnosticsWriter",
                "runtime_inlet_diagnostics_writer",
                "InletDiagnosticsWriter",
                "inlet_diagnostics_writer",
            ],
        )
        or ""
    ).strip().lower()
    return injected is True or (bool(writer) and writer not in {"not_applicable", "none", "false"})


def pending_runtime_inlet_diagnostics(path: Optional[Path]) -> Dict[str, Any]:
    return {
        "Gate": "pending_run",
        "Requested": path is not None,
        "Reasons": [],
        "ReasonsCsv": "",
        "CsvPath": str(path) if path is not None else "",
        "PreRunOnly": True,
    }


def protocol_items(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["Items", "items", "ProtocolItems", "protocol_items"]:
        value = audit.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def protocol_item_key(item: Dict[str, Any]) -> str:
    return str(item.get("Key") or item.get("key") or "").strip()


def protocol_item_status(item: Dict[str, Any]) -> str:
    return str(item.get("Status") or item.get("status") or "").strip().lower()


def audit_key_list(audit: Dict[str, Any], key: str) -> List[str]:
    value = audit.get(key)
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def audit_validation_protocol(path: Path) -> Dict[str, Any]:
    audit = json_load(path)
    items = protocol_items(audit)
    by_key = {protocol_item_key(item): protocol_item_status(item) for item in items if protocol_item_key(item)}
    audit_gate = str(audit.get("Gate") or audit.get("gate") or "").strip().lower()
    paper_grade_gate = str(audit.get("PaperGradeGate") or audit.get("paper_grade_gate") or "").strip().lower()
    pre_run_gate = str(audit.get("PreRunGate") or audit.get("pre_run_gate") or "").strip().lower()
    missing_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key not in by_key]
    empty_status_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key in by_key and not by_key[key]]
    fail_keys = [key for key, status in by_key.items() if status == "fail"]
    risk_keys = [key for key, status in by_key.items() if status == "risk"]
    partial_keys = [key for key, status in by_key.items() if status == "partial"]
    pre_run_fail_keys = audit_key_list(audit, "PreRunFailKeys") if "PreRunFailKeys" in audit else fail_keys
    pre_run_risk_keys = audit_key_list(audit, "PreRunRiskKeys") if "PreRunRiskKeys" in audit else risk_keys
    pre_run_partial_keys = audit_key_list(audit, "PreRunPartialKeys") if "PreRunPartialKeys" in audit else partial_keys
    reasons = []
    if not audit or not items:
        reasons.append("validation_protocol_audit_missing_or_empty")
    reasons.extend(f"validation_protocol_item_missing:{key}" for key in missing_keys)
    reasons.extend(f"validation_protocol_item_status_missing:{key}" for key in empty_status_keys)
    reasons.extend(f"validation_protocol_prerun_item_fail:{key}" for key in pre_run_fail_keys)
    reasons.extend(f"validation_protocol_prerun_item_risk:{key}" for key in pre_run_risk_keys)
    reasons.extend(f"validation_protocol_prerun_item_partial:{key}" for key in pre_run_partial_keys)
    if not audit_gate and not pre_run_gate:
        reasons.append("validation_protocol_audit_gate_missing")
    if not pre_run_gate:
        pre_run_gate = audit_gate
    if pre_run_gate not in PAPER_GRADE_PROTOCOL_AUDIT_GATES:
        reasons.append(f"validation_protocol_prerun_gate_not_ready:{pre_run_gate or 'missing'}")
    return {
        "Path": str(path.resolve()),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "AuditGate": audit_gate,
        "PaperGradeGate": paper_grade_gate,
        "PreRunGate": pre_run_gate,
        "AllowedAuditGates": sorted(PAPER_GRADE_PROTOCOL_AUDIT_GATES),
        "AijCase": str(audit.get("AijCase") or audit.get("AIJCase") or audit.get("Case") or "").strip(),
        "WindDirection": str(
            audit.get("WindDirection")
            or audit.get("WindDirectionLabel")
            or audit.get("wind_direction")
            or ""
        ).strip(),
        "WindDirectionUnitVector": audit.get("WindDirectionUnitVector") or audit.get("wind_vector") or [],
        "ItemCount": len(items),
        "RequiredItemKeys": REQUIRED_PROTOCOL_ITEM_KEYS,
        "Statuses": by_key,
        "MissingKeys": missing_keys,
        "EmptyStatusKeys": empty_status_keys,
        "FailKeys": fail_keys,
        "RiskKeys": risk_keys,
        "PartialKeys": partial_keys,
        "PreRunFailKeys": pre_run_fail_keys,
        "PreRunRiskKeys": pre_run_risk_keys,
        "PreRunPartialKeys": pre_run_partial_keys,
    }


def audit_case_metadata_preconditions(metadata: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []

    paper_inlet_gate = str(
        metadata_value(
            metadata,
            [
                "PaperGradeTurbulentInletPrerequisiteGate",
                "PaperGradeInletPrerequisiteGate",
                "PaperGradeInletMethodGate",
            ],
        )
        or ""
    ).strip().lower()
    paper_boundary_gate = str(
        metadata_value(
            metadata,
            [
                "PaperGradeBoundaryPrerequisiteGate",
                "PaperGradeBoundaryMethodGate",
            ],
        )
        or ""
    ).strip().lower()
    inlet_distribution_reconstruction = metadata_bool(
        metadata,
        [
            "InletDistributionFunctionReconstruction",
            "SyntheticTurbulentInletDistributionFunctionReconstruction",
        ],
    )
    synthetic_injected = metadata_bool(
        metadata,
        ["SyntheticTurbulentInletInjected", "SyntheticTurbulenceInjected"],
    )
    distribution_treatment = str(
        metadata_value(
            metadata,
            [
                "SyntheticTurbulentInletDistributionTreatment",
                "InletDistributionTreatment",
            ],
        )
        or ""
    ).strip().lower()
    inlet_paper_status = str(
        metadata_value(
            metadata,
            [
                "SyntheticTurbulentInletPaperGradeStatus",
                "PaperGradeTurbulentInletStatus",
            ],
        )
        or ""
    ).strip().lower()
    boundary_paper_status = str(
        metadata_value(
            metadata,
            [
                "BoundaryConditionPaperGradeStatus",
                "BoundaryVelocityInitializationPaperGradeStatus",
            ],
        )
        or ""
    ).strip().lower()
    boundary_non_reflecting = metadata_bool(metadata, ["BoundaryNonReflectingOutletImplemented"])
    boundary_wind_tunnel = metadata_bool(metadata, ["BoundarySideTopWindTunnelEquivalentImplemented"])
    boundary_rough_wall = metadata_bool(metadata, ["BoundaryRoughWallFunctionImplemented"])
    boundary_precursor = metadata_bool(metadata, ["BoundaryPrecursorOrRecyclingImplemented"])
    boundary_blockage_fetch = metadata_bool(metadata, ["BoundaryBlockageFetchEvidenceArchived"])

    if not paper_inlet_gate:
        reasons.append("case_metadata_paper_grade_turbulent_inlet_prerequisite_missing")
    elif paper_inlet_gate not in {"pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"case_metadata_paper_grade_turbulent_inlet_prerequisite_not_pass:{paper_inlet_gate}")
    if not paper_boundary_gate:
        reasons.append("case_metadata_paper_grade_boundary_prerequisite_missing")
    elif paper_boundary_gate not in {"pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"case_metadata_paper_grade_boundary_prerequisite_not_pass:{paper_boundary_gate}")
    if synthetic_injected is None:
        reasons.append("case_metadata_synthetic_turbulent_inlet_injected_missing")
    if synthetic_injected is True and inlet_distribution_reconstruction is not True:
        reasons.append("case_metadata_synthetic_inlet_without_distribution_reconstruction")
    if "velocity_field_only" in distribution_treatment or "no_distribution_function_reconstruction" in distribution_treatment:
        reasons.append("case_metadata_inlet_distribution_treatment_velocity_field_only")
    if inlet_paper_status and "diagnostic_only" in inlet_paper_status:
        reasons.append("case_metadata_turbulent_inlet_status_diagnostic_only")
    if boundary_paper_status and "diagnostic" in boundary_paper_status:
        reasons.append("case_metadata_boundary_status_diagnostic_only")

    boundary_fields = [
        ("non_reflecting_outlet", boundary_non_reflecting),
        ("side_top_wind_tunnel_equivalence", boundary_wind_tunnel),
        ("rough_wall_function", boundary_rough_wall),
        ("precursor_or_recycling", boundary_precursor),
        ("blockage_fetch_evidence", boundary_blockage_fetch),
    ]
    for key, value in boundary_fields:
        if value is None:
            reasons.append(f"case_metadata_boundary_evidence_missing:{key}")
        elif value is False:
            reasons.append(f"case_metadata_boundary_evidence_false:{key}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "PaperGradeTurbulentInletPrerequisiteGate": paper_inlet_gate,
        "PaperGradeBoundaryPrerequisiteGate": paper_boundary_gate,
        "SyntheticTurbulentInletInjected": synthetic_injected,
        "InletDistributionFunctionReconstruction": inlet_distribution_reconstruction,
        "SyntheticTurbulentInletDistributionTreatment": distribution_treatment,
        "SyntheticTurbulentInletPaperGradeStatus": inlet_paper_status,
        "BoundaryConditionPaperGradeStatus": boundary_paper_status,
    }


def path_record(role: str, path: Path) -> Dict[str, Any]:
    exists = path.exists() and path.is_file()
    return {
        "Role": role,
        "Path": str(path.resolve()),
        "Exists": exists,
        "HashAlgorithm": "SHA256",
        "Sha256": sha256(path) if exists else "",
    }


def first_existing_path(base: Path, candidates: Sequence[Path]) -> Optional[Path]:
    return next((base / rel for rel in candidates if (base / rel).is_file()), None)


def setup_source_has_step_limit(source: str, steps: int) -> bool:
    if steps <= 0:
        return True
    escaped = re.escape(str(steps))
    return bool(
        re.search(rf"\blbm\.run\s*\(\s*{escaped}\s*u?\s*\)", source)
        or re.search(rf"\blbm\.get_t\s*\(\s*\)\s*<\s*{escaped}\s*u?\b", source)
        or re.search(rf"\bremaining\s*=\s*{escaped}\s*u?\s*-", source)
        or re.search(rf"\b(?:const\s+)?(?:uint|int|ulong|unsigned\s+int)\s+\w*steps\w*\s*=\s*{escaped}\s*u?\s*;", source, re.IGNORECASE)
    )


def setup_source_has_save_interval(source: str, save_interval: int) -> bool:
    if save_interval <= 0:
        return True
    escaped = re.escape(str(save_interval))
    return bool(
        re.search(rf"\bsteps_to_run\s*=\s*remaining\s*<\s*{escaped}\s*u?\b", source)
        or re.search(rf"\b(?:const\s+)?(?:uint|int|ulong|unsigned\s+int)\s+\w*(?:save_)?interval\w*\s*=\s*{escaped}\s*u?\s*;", source, re.IGNORECASE)
    )


def audit_case_setup_source_preconditions(
    case_dir: Path,
    metadata: Dict[str, Any],
    *,
    expected_time_steps: int,
    expected_save_interval: int,
) -> Dict[str, Any]:
    reasons: List[str] = []
    setup_path = first_existing_path(case_dir, [Path("src") / "setup.cpp", Path("setup.cpp")])
    source = ""
    if setup_path is None or not setup_path.is_file():
        reasons.append("case_setup_cpp_missing")
    else:
        source = setup_path.read_text(encoding="utf-8", errors="replace")

    wind_profile = str(
        metadata_value(metadata, ["WindProfile", "wind_profile", "WindProfileType"]) or ""
    ).strip().lower()
    synthetic_requested = metadata_bool(
        metadata,
        ["SyntheticTurbulentInletRequested", "SyntheticTurbulenceRequested"],
    )
    synthetic_injected = metadata_bool(
        metadata,
        ["SyntheticTurbulentInletInjected", "SyntheticTurbulenceInjected"],
    )
    custom_required = wind_profile == "customtable" or synthetic_requested is True or synthetic_injected is True

    if source:
        has_profile_z = "profile_z_m" in source
        has_profile_u = "profile_u_lbm" in source
        has_profile_k = "profile_k_lbm" in source
        has_custom_table = (
            "CustomTable" in source
            or "custom table" in source.lower()
            or (has_profile_z and has_profile_u)
        )
        has_power_law = "PowerLaw" in source or "powf(z / z_ref" in source
        has_stg_function = "syntheticTurbulentInlet" in source
        has_stg_apply = "applySyntheticTurbulentInlet" in source

        if custom_required and not has_custom_table:
            reasons.append("case_setup_source_not_customtable")
        if custom_required and has_power_law and not has_profile_z:
            reasons.append("case_setup_source_stale_powerlaw_profile")
        if custom_required and not has_profile_z:
            reasons.append("case_setup_source_missing_profile_z_m")
        if custom_required and not has_profile_u:
            reasons.append("case_setup_source_missing_profile_u_lbm")
        if (synthetic_requested is True or synthetic_injected is True) and not has_profile_k:
            reasons.append("case_setup_source_missing_profile_k_lbm")
        if synthetic_injected is True and not has_stg_function:
            reasons.append("case_setup_source_missing_synthetic_turbulent_inlet_function")
        if synthetic_injected is True and not has_stg_apply:
            reasons.append("case_setup_source_missing_synthetic_turbulent_inlet_refresh_loop")
        if expected_time_steps > 0 and not setup_source_has_step_limit(source, expected_time_steps):
            reasons.append(f"case_setup_source_time_steps_mismatch_expected_{expected_time_steps}")
        if expected_save_interval > 0 and not setup_source_has_save_interval(source, expected_save_interval):
            reasons.append(f"case_setup_source_save_interval_mismatch_expected_{expected_save_interval}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "SetupPath": str(setup_path.resolve()) if setup_path is not None else "",
        "SetupSha256": sha256_or_empty(setup_path),
        "ExpectedTimeSteps": expected_time_steps,
        "ExpectedSaveInterval": expected_save_interval,
        "WindProfile": wind_profile,
        "CustomTableRequired": custom_required,
        "SyntheticRequested": synthetic_requested,
        "SyntheticInjected": synthetic_injected,
    }


def af_profile_audit(
    af_path: Optional[Path],
    *,
    z_ref: Optional[float],
    expected_uref: Optional[float],
    uref_tolerance: float,
    require_k: bool,
) -> Dict[str, Any]:
    reasons: List[str] = []
    rows: List[Dict[str, str]] = []
    fieldnames: List[str] = []
    z_col = ""
    u_col = ""
    k_col = ""
    u_at_z_ref: Optional[float] = None
    k_valid_count = 0

    if af_path is None:
        if z_ref is not None or expected_uref is not None or require_k:
            reasons.append("af_csv_missing_for_requested_preflight")
    elif not af_path.is_file():
        reasons.append("af_csv_path_not_found")
    else:
        rows, fieldnames = read_csv_rows(af_path)
        z_col = find_column(fieldnames, ["z", "z(m)", "height", "height_m"])
        u_col = find_column(fieldnames, ["U", "U(m/s)", "u", "u_mps", "velocity", "velocity_mps"])
        k_col = find_column(fieldnames, ["k", "k(m2/s2)", "k_m2_s2", "tke", "turbulent_kinetic_energy"])
        if not z_col:
            reasons.append("af_csv_z_column_missing")
        if not u_col:
            reasons.append("af_csv_u_column_missing")
        if require_k and not k_col:
            reasons.append("af_csv_k_column_missing")

        samples: List[Tuple[float, float]] = []
        for row in rows:
            z = as_float(row.get(z_col)) if z_col else None
            u = as_float(row.get(u_col)) if u_col else None
            k = as_float(row.get(k_col)) if k_col else None
            if z is not None and u is not None:
                samples.append((z, u))
            if k is not None and k >= 0.0:
                k_valid_count += 1
        if require_k and k_col and k_valid_count != len(rows):
            reasons.append(f"af_csv_valid_k_count_{k_valid_count}_does_not_match_row_count_{len(rows)}")
        if z_ref is not None or expected_uref is not None:
            if len(samples) < 2:
                reasons.append("af_csv_insufficient_z_u_rows_for_uref_audit")
            elif z_ref is None:
                reasons.append("z_ref_missing_for_uref_af_audit")
            elif expected_uref is None:
                reasons.append("expected_uref_missing_for_af_audit")
            else:
                samples.sort(key=lambda item: item[0])
                if z_ref <= samples[0][0]:
                    u_at_z_ref = samples[0][1]
                elif z_ref >= samples[-1][0]:
                    u_at_z_ref = samples[-1][1]
                else:
                    for (z0, u0), (z1, u1) in zip(samples, samples[1:]):
                        if z0 <= z_ref <= z1:
                            weight = 0.0 if abs(z1 - z0) <= 1.0e-12 else (z_ref - z0) / (z1 - z0)
                            u_at_z_ref = u0 + (u1 - u0) * weight
                            break
                if u_at_z_ref is None:
                    reasons.append("af_csv_uref_interpolation_failed")
                elif abs(expected_uref - u_at_z_ref) > uref_tolerance:
                    reasons.append(
                        f"expected_uref_{expected_uref:.12g}_does_not_match_af_u_at_zref_{u_at_z_ref:.12g}"
                    )

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(af_path.resolve()) if af_path is not None else "",
        "Exists": bool(af_path and af_path.is_file()),
        "Sha256": sha256_or_empty(af_path),
        "RowCount": len(rows),
        "Columns": fieldnames,
        "ZColumn": z_col,
        "UColumn": u_col,
        "KColumn": k_col,
        "ValidKCount": k_valid_count,
        "Zref": z_ref,
        "ExpectedUref": expected_uref,
        "UrefFromAfAtZref": u_at_z_ref,
        "UrefAfTolerance": uref_tolerance,
        "RequireK": require_k,
    }


def official_probe_input_audit(
    official_path: Optional[Path],
    *,
    expected_case: str,
    official_condition_filter: str,
    expected_wind: str,
    official_wind_filter: str,
    expected_row_count: int,
    expected_z: Optional[float],
    expected_z_min: Optional[float],
    expected_z_max: Optional[float],
    expected_z_tolerance: float,
) -> Dict[str, Any]:
    reasons: List[str] = []
    rows: List[Dict[str, str]] = []
    fieldnames: List[str] = []
    filtered_rows: List[Dict[str, str]] = []
    id_col = ""
    case_col = ""
    wind_col = ""
    z_col = ""
    assumed_single_case_file = False
    assumed_single_wind_file = False
    effective_condition = official_condition_filter.strip() or expected_case
    effective_wind = official_wind_filter.strip() or expected_wind

    preflight_requested = (
        expected_row_count > 0
        or expected_z is not None
        or bool(effective_condition)
        or bool(effective_wind)
    )
    if official_path is None:
        if preflight_requested:
            reasons.append("official_csv_missing_for_requested_preflight")
    elif not official_path.is_file():
        reasons.append("official_csv_path_not_found")
    else:
        rows, fieldnames = read_csv_rows(official_path)
        id_col = find_column(fieldnames, ["No.", "No", "probe_id", "id", "point", "point_id"])
        case_col = find_column(fieldnames, ["case", "Case", "condition", "Condition", "bc_ac", "Configuration"])
        wind_col = find_column(fieldnames, ["wind", "Wind", "wind_direction", "Wind_direction", "WindDirection", "Direction", "dir"])
        z_col = find_column(fieldnames, ["z", "z(m)", "Z", "height", "height_m"])
        filtered_rows = list(rows)
        if effective_condition and case_col:
            token = normalized_identity(effective_condition)
            filtered_rows = [row for row in filtered_rows if normalized_identity(row.get(case_col)) == token]
        elif effective_condition and not case_col:
            assumed_single_case_file = True
        if effective_wind and wind_col:
            token = normalized_identity(effective_wind)
            filtered_rows = [row for row in filtered_rows if normalized_identity(row.get(wind_col)) == token]
        elif effective_wind and not wind_col:
            assumed_single_wind_file = True
        if expected_row_count > 0 and len(filtered_rows) != expected_row_count:
            reasons.append(f"official_filtered_row_count_{len(filtered_rows)}_does_not_match_expected_{expected_row_count}")
        if not id_col:
            reasons.append("official_probe_id_column_missing")
        else:
            ids = [normalized_identity(row.get(id_col)) for row in filtered_rows if normalized_identity(row.get(id_col))]
            if len(ids) != len(filtered_rows):
                reasons.append("official_probe_id_missing_in_filtered_rows")
            if len(set(ids)) != len(ids):
                reasons.append("official_probe_ids_not_unique_after_normalization")
        if expected_z is not None:
            if not z_col:
                reasons.append("official_z_column_missing")
            else:
                z_values = [as_float(row.get(z_col)) for row in filtered_rows]
                z_missing = sum(1 for value in z_values if value is None)
                z_mismatch = sum(
                    1
                    for value in z_values
                    if value is not None and abs(value - expected_z) > expected_z_tolerance
                )
                if z_missing:
                    reasons.append(f"official_z_missing_count_{z_missing}")
                if z_mismatch:
                    reasons.append(f"official_z_mismatch_count_{z_mismatch}")
        if expected_z_min is not None or expected_z_max is not None:
            if not z_col:
                reasons.append("official_z_column_missing")
            else:
                z_values = [as_float(row.get(z_col)) for row in filtered_rows]
                z_missing = sum(1 for value in z_values if value is None)
                z_below = sum(
                    1
                    for value in z_values
                    if value is not None
                    and expected_z_min is not None
                    and value < expected_z_min - expected_z_tolerance
                )
                z_above = sum(
                    1
                    for value in z_values
                    if value is not None
                    and expected_z_max is not None
                    and value > expected_z_max + expected_z_tolerance
                )
                if z_missing:
                    reasons.append(f"official_z_missing_count_{z_missing}")
                if z_below:
                    reasons.append(f"official_z_below_min_count_{z_below}")
                if z_above:
                    reasons.append(f"official_z_above_max_count_{z_above}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(official_path.resolve()) if official_path is not None else "",
        "Exists": bool(official_path and official_path.is_file()),
        "Sha256": sha256_or_empty(official_path),
        "RowCount": len(rows),
        "FilteredRowCount": len(filtered_rows),
        "Columns": fieldnames,
        "ProbeIdColumn": id_col,
        "CaseColumn": case_col,
        "WindDirectionColumn": wind_col,
        "AssumedSingleCaseFile": assumed_single_case_file,
        "AssumedSingleWindFile": assumed_single_wind_file,
        "ZColumn": z_col,
        "ExpectedCase": expected_case,
        "OfficialConditionFilter": official_condition_filter,
        "EffectiveConditionFilter": effective_condition,
        "ExpectedWindDirection": expected_wind,
        "OfficialWindFilter": official_wind_filter,
        "EffectiveWindFilter": effective_wind,
        "ExpectedRowCount": expected_row_count,
        "ExpectedZ": expected_z,
        "ExpectedZMin": expected_z_min,
        "ExpectedZMax": expected_z_max,
        "ExpectedZTolerance": expected_z_tolerance,
    }


def audit_official_input_preconditions(
    official_path: Optional[Path],
    af_path: Optional[Path],
    metadata: Dict[str, Any],
    validation_protocol: Dict[str, Any],
    *,
    expected_case: str,
    official_condition_filter: str,
    expected_wind: str,
    official_wind_filter: str,
    expected_probe_row_count: int,
    expected_probe_z: Optional[float],
    expected_probe_z_min: Optional[float],
    expected_probe_z_max: Optional[float],
    expected_probe_z_tolerance: float,
    z_ref: Optional[float],
    expected_uref: Optional[float],
    uref_af_tolerance: float,
    expected_wind_vector_text: str,
    wind_vector_tolerance: float,
    require_af_k: bool,
) -> Dict[str, Any]:
    requested = any(
        [
            official_path is not None,
            af_path is not None,
            expected_probe_row_count > 0,
            expected_probe_z is not None,
            expected_probe_z_min is not None,
            expected_probe_z_max is not None,
            z_ref is not None,
            expected_uref is not None,
            bool(expected_wind_vector_text.strip()),
            require_af_k,
        ]
    )
    if not requested:
        return {"Gate": "not_applicable", "Reasons": [], "ReasonsCsv": ""}

    af_gate = af_profile_audit(
        af_path,
        z_ref=z_ref,
        expected_uref=expected_uref,
        uref_tolerance=uref_af_tolerance,
        require_k=require_af_k,
    )
    official_gate = official_probe_input_audit(
        official_path,
        expected_case=expected_case,
        official_condition_filter=official_condition_filter,
        expected_wind=expected_wind,
        official_wind_filter=official_wind_filter,
        expected_row_count=expected_probe_row_count,
        expected_z=expected_probe_z,
        expected_z_min=expected_probe_z_min,
        expected_z_max=expected_probe_z_max,
        expected_z_tolerance=expected_probe_z_tolerance,
    )

    reasons: List[str] = []
    reasons.extend(f"af:{reason}" for reason in af_gate["Reasons"])
    reasons.extend(f"official:{reason}" for reason in official_gate["Reasons"])

    expected_vector = parse_vector(expected_wind_vector_text)
    metadata_vector = parse_vector(
        metadata_value(metadata, ["WindDirectionUnitVector", "WindVector", "wind_vector", "WindDirectionVector"])
    )
    protocol_vector = parse_vector(validation_protocol.get("WindDirectionUnitVector") or validation_protocol.get("wind_vector"))
    actual_vector = metadata_vector or protocol_vector
    if expected_wind_vector_text.strip():
        if expected_vector is None:
            reasons.append("expected_wind_vector_parse_failed")
        elif actual_vector is None:
            reasons.append("wind_vector_missing_in_metadata_and_protocol")
        elif not vectors_match(actual_vector, expected_vector, wind_vector_tolerance):
            reasons.append("wind_vector_mismatch")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "OfficialProbeAudit": official_gate,
        "AfProfileAudit": af_gate,
        "ExpectedWindVector": expected_vector,
        "MetadataWindVector": metadata_vector,
        "ProtocolWindVector": protocol_vector,
        "EffectiveWindVector": actual_vector,
        "WindVectorTolerance": wind_vector_tolerance,
    }


def case_file_record(role: str, case_dir: Path, candidates: Sequence[Path]) -> Dict[str, Any]:
    path = first_existing_path(case_dir, candidates)
    if path is not None:
        record = path_record(role, path)
        record["CandidatePaths"] = [rel.as_posix() for rel in candidates]
        record["SelectedRelativePath"] = path.relative_to(case_dir).as_posix()
        return record
    fallback = case_dir / candidates[0]
    record = path_record(role, fallback)
    record["CandidatePaths"] = [rel.as_posix() for rel in candidates]
    record["SelectedRelativePath"] = ""
    return record


def optional_path_record(role: str, path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return None
    return path_record(role, path)


def detect_build_system(source_root: Path) -> Dict[str, Any]:
    solution_files = sorted(source_root.glob("*.sln"))
    has_makefile = (source_root / "Makefile").exists()
    has_cmake = (source_root / "CMakeLists.txt").exists()
    return {
        "HasSolution": bool(solution_files),
        "SolutionFiles": [str(path.resolve()) for path in solution_files],
        "HasMakefile": has_makefile,
        "MakefilePath": str((source_root / "Makefile").resolve()) if has_makefile else "",
        "HasCMakeLists": has_cmake,
        "CMakeListsPath": str((source_root / "CMakeLists.txt").resolve()) if has_cmake else "",
    }


def validate_source_root(source_root: Path) -> Dict[str, Any]:
    missing: List[str] = []
    for _, rel in REQUIRED_SOURCE_FILES:
        if not (source_root / rel).is_file():
            missing.append(rel.as_posix())
    build = detect_build_system(source_root)
    if not (build["HasSolution"] or build["HasMakefile"] or build["HasCMakeLists"]):
        missing.append("FluidX3D.sln|Makefile|CMakeLists.txt")
    return {
        **build,
        "HasSrcDirectory": (source_root / "src").is_dir(),
        "HasSetupCpp": (source_root / "src" / "setup.cpp").is_file(),
        "HasDefinesHpp": (source_root / "src" / "defines.hpp").is_file(),
        "HasLbmHpp": (source_root / "src" / "lbm.hpp").is_file(),
        "HasLbmCpp": (source_root / "src" / "lbm.cpp").is_file(),
        "MissingRequiredItems": missing,
        "IsValid": not missing,
    }


def collect_required_files(
    source_root: Path,
    case_dir: Path,
    *,
    metadata_path: Path,
    validation_protocol_path: Path,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for role, rel in REQUIRED_SOURCE_FILES:
        records.append(path_record(role, source_root / rel))
    for role, candidates in REQUIRED_CASE_FILE_CANDIDATES:
        records.append(case_file_record(role, case_dir, candidates))
    for role, rel in REQUIRED_CASE_FILES:
        if role == "Validation protocol audit":
            path = validation_protocol_path
        elif role == "Case metadata":
            path = metadata_path
        else:
            path = case_dir / rel
        records.append(path_record(role, path))
    for role, rel in OPTIONAL_CASE_FILES:
        record = optional_path_record(role, case_dir / rel)
        if record is not None:
            records.append(record)
    return records


def collect_native_source_files(source_root: Path, prefix: str) -> List[Dict[str, Any]]:
    return [path_record(f"{prefix} {role}", source_root / rel) for role, rel in REQUIRED_SOURCE_FILES]


def collect_effective_run_source_files(source_root: Path) -> List[Dict[str, Any]]:
    roles = [
        ("Effective FluidX3D setup", Path("src") / "setup.cpp"),
        ("Effective FluidX3D defines", Path("src") / "defines.hpp"),
        ("Effective FluidX3D lbm.hpp", Path("src") / "lbm.hpp"),
        ("Effective FluidX3D lbm.cpp", Path("src") / "lbm.cpp"),
    ]
    return [path_record(role, source_root / rel) for role, rel in roles]


def setup_mismatch_allowed_by_run_plan_override(metadata: Dict[str, Any]) -> bool:
    override = metadata.get("RunPlanOverride")
    if not isinstance(override, dict):
        return False
    if str(override.get("AppliedBy") or "") != "prepare_native_empty_tunnel_case.py":
        return False
    return as_int(override.get("TimeSteps")) > 0 and as_int(override.get("VtkSaveInterval")) > 0


def audit_case_to_source_parity(
    case_dir: Path,
    source_root: Path,
    metadata: Optional[Dict[str, Any]] = None,
    *,
    allow_pending_install_mismatch: bool = False,
) -> Dict[str, Any]:
    metadata = metadata or {}
    setup_override_allowed = setup_mismatch_allowed_by_run_plan_override(metadata)
    pairs = [
        ("setup", first_existing_path(case_dir, [Path("src") / "setup.cpp", Path("setup.cpp")]), source_root / "src" / "setup.cpp"),
        ("defines", first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")]), source_root / "src" / "defines.hpp"),
    ]
    records: List[Dict[str, Any]] = []
    reasons: List[str] = []
    notes: List[str] = []
    for role, case_path, source_path in pairs:
        case_exists = case_path is not None and case_path.is_file()
        source_exists = source_path.is_file()
        case_hash = sha256(case_path) if case_exists and case_path is not None else ""
        source_hash = sha256(source_path) if source_exists else ""
        match = bool(case_hash and source_hash and case_hash == source_hash)
        run_plan_override_mismatch = role == "setup" and setup_override_allowed and case_exists and source_exists and not match
        pending_install_mismatch = allow_pending_install_mismatch and case_exists and source_exists and not match
        allowed_mismatch = run_plan_override_mismatch or pending_install_mismatch
        if not case_exists:
            reasons.append(f"case_{role}_missing")
        if not source_exists:
            reasons.append(f"source_{role}_missing")
        if case_exists and source_exists and not match and not allowed_mismatch:
            reasons.append(f"case_{role}_hash_mismatch_source")
        if run_plan_override_mismatch:
            notes.append("case_setup_hash_mismatch_source_allowed_by_run_plan_override")
        elif pending_install_mismatch:
            notes.append(f"case_{role}_hash_mismatch_source_pending_install_preflight")
        records.append(
            {
                "Role": role,
                "CasePath": str(case_path.resolve()) if case_path is not None else "",
                "CaseSha256": case_hash,
                "SourcePath": str(source_path.resolve()),
                "SourceSha256": source_hash,
                "Match": match,
                "AllowedMismatch": allowed_mismatch,
                "PendingInstallOnly": pending_install_mismatch,
            }
        )
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Notes": notes,
        "NotesCsv": ";".join(notes),
        "Pairs": records,
    }


def read_case_value(metadata: Dict[str, Any], keys: Sequence[str]) -> str:
    for key in keys:
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def case_identity(metadata: Dict[str, Any]) -> Tuple[str, str]:
    case = read_case_value(metadata, ["AijCase", "AIJCase", "case", "Case", "CaseName"])
    wind = read_case_value(metadata, ["WindDirection", "WindDirectionLabel", "wind_direction", "windDirection"])
    return case, wind


def effective_identity(metadata_case: str, metadata_wind: str, validation_protocol: Dict[str, Any]) -> Dict[str, str]:
    protocol_case = str(validation_protocol.get("AijCase") or "").strip()
    protocol_wind = str(validation_protocol.get("WindDirection") or "").strip()
    return {
        "Case": metadata_case or protocol_case,
        "CaseSource": "case_metadata" if metadata_case else "validation_protocol_audit" if protocol_case else "",
        "WindDirection": metadata_wind or protocol_wind,
        "WindDirectionSource": (
            "case_metadata" if metadata_wind else "validation_protocol_audit" if protocol_wind else ""
        ),
        "ProtocolAijCase": protocol_case,
        "ProtocolWindDirection": protocol_wind,
    }


def identity_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def identity_matches(expected: str, actual: str) -> bool:
    expected_token = identity_token(expected)
    actual_token = identity_token(actual)
    if not expected_token:
        return True
    if not actual_token:
        return False
    return expected_token == actual_token or expected_token in actual_token


def copy_if_present(src: Path, dst: Path) -> Optional[Dict[str, Any]]:
    if not src.exists() or not src.is_file():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return {
        "Source": str(src.resolve()),
        "Target": str(dst.resolve()),
        "Sha256": sha256(dst),
    }


def install_case(case_dir: Path, source_root: Path, backup_root: Path) -> Dict[str, Any]:
    backup_root.mkdir(parents=True, exist_ok=True)
    backups: List[Dict[str, Any]] = []
    installed: List[Dict[str, Any]] = []
    install_sources = [
        ("src/setup.cpp", first_existing_path(case_dir, [Path("src") / "setup.cpp", Path("setup.cpp")])),
        ("src/defines.hpp", first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")])),
    ]
    for role, src in install_sources:
        rel = Path(role)
        dst = source_root / rel
        if dst.exists():
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(dst), str(backup))
            backups.append({"Role": rel.as_posix(), "Path": str(backup.resolve()), "Sha256": sha256(backup)})
        copied = copy_if_present(src, dst) if src is not None else None
        if copied is not None:
            copied["Role"] = rel.as_posix()
            installed.append(copied)
    for name in ["case_metadata.json", "domain_origin.json", "buildings.stl", "roughness_layout.csv", "equivalent_precursor_evidence.json"]:
        copied = copy_if_present(case_dir / name, source_root / name)
        if copied is not None:
            copied["Role"] = name
            installed.append(copied)
    return {"Backups": backups, "InstalledFiles": installed}


def source_reconstruction_capabilities(source_root: Path) -> Dict[str, bool]:
    kernel_text = (source_root / "src" / "kernel.cpp").read_text(encoding="utf-8", errors="replace") if (source_root / "src" / "kernel.cpp").is_file() else ""
    lbm_cpp_text = (source_root / "src" / "lbm.cpp").read_text(encoding="utf-8", errors="replace") if (source_root / "src" / "lbm.cpp").is_file() else ""
    lbm_hpp_text = (source_root / "src" / "lbm.hpp").read_text(encoding="utf-8", errors="replace") if (source_root / "src" / "lbm.hpp").is_file() else ""
    return {
        "SupportsInletStressDdf": bool(
            re.search(r"\bkernel\s+void\s+reconstruct_inlet_stress_boundaries\s*\(", kernel_text)
            and re.search(r"\bLBM::reconstruct_inlet_stress_boundaries\s*\(", lbm_cpp_text)
            and re.search(r"\bvoid\s+reconstruct_inlet_stress_boundaries\s*\(", lbm_hpp_text)
        ),
        "SupportsEquilibriumDdf": bool(
            re.search(r"\bkernel\s+void\s+reconstruct_equilibrium_boundaries\s*\(", kernel_text)
            and re.search(r"\bLBM::reconstruct_equilibrium_boundaries\s*\(", lbm_cpp_text)
            and re.search(r"\bvoid\s+reconstruct_equilibrium_boundaries\s*\(", lbm_hpp_text)
        ),
    }


def macro_is_active(text: str, macro: str) -> bool:
    return bool(re.search(rf"(?m)^\s*#\s*define\s+{re.escape(macro)}\b", text))


def comment_out_macro(text: str, macro: str, reason: str) -> Tuple[str, bool]:
    pattern = re.compile(rf"(?m)^(\s*)#\s*define\s+{re.escape(macro)}\b(.*)$")
    if not pattern.search(text):
        return text, False
    return pattern.sub(rf"\1// #define {macro}\2  // disabled by CityLBM native runner: {reason}", text), True


def ensure_active_macro(text: str, macro: str, comment: str, insert_after: str) -> Tuple[str, bool]:
    if macro_is_active(text, macro):
        return text, False
    commented = re.compile(rf"(?m)^(\s*)//\s*#\s*define\s+{re.escape(macro)}\b.*$")
    replacement = rf"\1#define {macro}  // {comment}"
    if commented.search(text):
        return commented.sub(replacement, text, count=1), True
    anchor = re.compile(rf"(?m)^(\s*#\s*define\s+{re.escape(insert_after)}\b.*)$")
    if anchor.search(text):
        return anchor.sub(rf"\1\n#define {macro}  // {comment}", text, count=1), True
    return text.rstrip() + f"\n#define {macro}  // {comment}\n", True


def adapt_case_reconstruction_macros(case_dir: Path, source_root: Path) -> Dict[str, Any]:
    defines_path = first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")])
    result: Dict[str, Any] = {
        "Requested": True,
        "Path": str(defines_path.resolve()) if defines_path is not None else "",
        "Exists": defines_path is not None and defines_path.is_file(),
        "Modified": False,
        "Sha256Before": sha256_or_empty(defines_path),
        "Sha256After": "",
        "Capabilities": source_reconstruction_capabilities(source_root),
        "AppliedActions": [],
        "Gate": "pass",
        "Reasons": [],
        "ReasonsCsv": "",
    }
    if defines_path is None or not defines_path.is_file():
        result["Gate"] = "fail"
        result["Reasons"] = ["case_defines_missing"]
        result["ReasonsCsv"] = "case_defines_missing"
        return result

    text = defines_path.read_text(encoding="utf-8", errors="replace")
    updated = text
    capabilities = result["Capabilities"]
    has_unsupported_stress = (
        macro_is_active(updated, "RECONSTRUCT_INLET_STRESS_DDF")
        or macro_is_active(updated, "CASEA_DEVICE_SEM_STRESS_DDF")
    ) and not capabilities["SupportsInletStressDdf"]
    if has_unsupported_stress and capabilities["SupportsEquilibriumDdf"]:
        updated, changed = comment_out_macro(
            updated,
            "RECONSTRUCT_INLET_STRESS_DDF",
            "selected FluidX3D source lacks reconstruct_inlet_stress_boundaries",
        )
        if changed:
            result["AppliedActions"].append("disabled_RECONSTRUCT_INLET_STRESS_DDF")
        updated, changed = comment_out_macro(
            updated,
            "CASEA_DEVICE_SEM_STRESS_DDF",
            "selected FluidX3D source lacks inlet stress reconstruction hooks",
        )
        if changed:
            result["AppliedActions"].append("disabled_CASEA_DEVICE_SEM_STRESS_DDF")
        updated, changed = ensure_active_macro(
            updated,
            "RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF",
            "CityLBM native runner fallback: rebuild TYPE_E DDFs after STG refresh",
            "EQUILIBRIUM_BOUNDARIES",
        )
        if changed:
            result["AppliedActions"].append("enabled_RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF")
    elif has_unsupported_stress:
        updated, changed = comment_out_macro(
            updated,
            "RECONSTRUCT_INLET_STRESS_DDF",
            "selected FluidX3D source lacks all reconstruction hooks",
        )
        if changed:
            result["AppliedActions"].append("disabled_RECONSTRUCT_INLET_STRESS_DDF")
        updated, changed = comment_out_macro(
            updated,
            "CASEA_DEVICE_SEM_STRESS_DDF",
            "selected FluidX3D source lacks all reconstruction hooks",
        )
        if changed:
            result["AppliedActions"].append("disabled_CASEA_DEVICE_SEM_STRESS_DDF")
        result["Gate"] = "diagnostic_only"
        result["Reasons"] = ["unsupported_inlet_stress_ddf_no_equilibrium_fallback"]
        result["ReasonsCsv"] = "unsupported_inlet_stress_ddf_no_equilibrium_fallback"

    if updated != text:
        defines_path.write_text(updated, encoding="utf-8")
        result["Modified"] = True
    result["Sha256After"] = sha256_or_empty(defines_path)
    return result


def materialize_solver_workdir_inputs(case_dir: Path, source_root: Path, solver_cwd: Path) -> List[Dict[str, Any]]:
    if solver_cwd.resolve() == source_root.resolve():
        return []
    records: List[Dict[str, Any]] = []
    for name in [
        "buildings.stl",
        "roughness_layout.csv",
        "boundary_conditions.json",
        "equivalent_precursor_evidence.json",
        "case_metadata.json",
        "domain_origin.json",
    ]:
        src = first_existing_path(source_root, [Path(name)])
        if src is None:
            src = first_existing_path(case_dir, [Path(name)])
        copied = copy_if_present(src, solver_cwd / name) if src is not None else None
        if copied is not None:
            copied["Role"] = f"solver_cwd/{name}"
            records.append(copied)
    return records


def disable_graphics_macros_for_run(source_root: Path) -> Dict[str, Any]:
    defines_path = source_root / "src" / "defines.hpp"
    result: Dict[str, Any] = {
        "Requested": True,
        "Path": str(defines_path.resolve()),
        "Exists": defines_path.is_file(),
        "Modified": False,
        "Sha256Before": sha256_or_empty(defines_path),
        "Sha256After": "",
        "DisabledMacros": [],
        "Gate": "not_applicable",
    }
    if not defines_path.is_file():
        result["Gate"] = "fail"
        result["Reason"] = "defines_hpp_missing"
        return result
    source = defines_path.read_text(encoding="utf-8", errors="replace")
    disabled: List[str] = []

    def repl(match: re.Match[str]) -> str:
        macro = match.group(1)
        disabled.append(macro)
        return f"// #define {macro}  // disabled by CityLBM batch VTK canary"

    updated = re.sub(r"(?m)^\s*#define\s+(GRAPHICS|INTERACTIVE_GRAPHICS)\b.*$", repl, source)
    if updated != source:
        defines_path.write_text(updated, encoding="utf-8")
        result["Modified"] = True
    result["DisabledMacros"] = disabled
    result["Sha256After"] = sha256_or_empty(defines_path)
    result["Gate"] = "pass"
    return result


def common_msbuild_candidates() -> List[Path]:
    roots = [
        Path("C:/Program Files/Microsoft Visual Studio"),
        Path("C:/Program Files (x86)/Microsoft Visual Studio"),
    ]
    years = ["2022", "2019", "2017"]
    editions = ["Community", "Professional", "Enterprise", "BuildTools"]
    bin_dirs = [
        Path("MSBuild") / "Current" / "Bin" / "MSBuild.exe",
        Path("MSBuild") / "Current" / "Bin" / "amd64" / "MSBuild.exe",
        Path("MSBuild") / "15.0" / "Bin" / "MSBuild.exe",
        Path("MSBuild") / "15.0" / "Bin" / "amd64" / "MSBuild.exe",
    ]
    return [
        root / year / edition / bin_dir
        for root in roots
        for year in years
        for edition in editions
        for bin_dir in bin_dirs
    ]


def find_msbuild(explicit: str) -> str:
    if explicit:
        return explicit
    found = shutil.which("msbuild")
    if found:
        return found
    for candidate in common_msbuild_candidates():
        if candidate.is_file():
            return str(candidate)
    return ""


def latest_windows_sdk_version() -> str:
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    include_root = Path(program_files_x86) / "Windows Kits" / "10" / "Include"
    if not include_root.is_dir():
        return ""
    versions = sorted(
        child.name
        for child in include_root.iterdir()
        if child.is_dir() and re.match(r"^\d+\.\d+\.\d+\.\d+$", child.name)
    )
    return versions[-1] if versions else ""


def resolve_windows_sdk_version(requested: str) -> str:
    value = requested.strip()
    if not value:
        return ""
    if value.lower() == "auto":
        return latest_windows_sdk_version()
    return value


def patch_windows_sdk_project_files(source_root: Path, sdk_version: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "RequestedVersion": sdk_version,
        "Gate": "not_requested",
        "Files": [],
        "Reasons": [],
    }
    version = sdk_version.strip()
    if not version:
        return record

    vcxprojs = sorted(source_root.glob("*.vcxproj"))
    if not vcxprojs:
        record["Gate"] = "not_found"
        record["Reasons"].append("vcxproj_not_found")
        return record

    changed = False
    for project_path in vcxprojs:
        before = project_path.read_text(encoding="utf-8", errors="replace")
        after = before
        file_record: Dict[str, Any] = {
            "Path": str(project_path),
            "Sha256Before": sha256_or_empty(project_path),
            "Changed": False,
        }
        if re.search(r"<WindowsTargetPlatformVersion>.*?</WindowsTargetPlatformVersion>", after):
            after = re.sub(
                r"<WindowsTargetPlatformVersion>.*?</WindowsTargetPlatformVersion>",
                f"<WindowsTargetPlatformVersion>{version}</WindowsTargetPlatformVersion>",
                after,
                count=1,
            )
        else:
            after = re.sub(
                r'(<PropertyGroup\s+Label="Globals"\s*>\s*)',
                rf"\1\n    <WindowsTargetPlatformVersion>{version}</WindowsTargetPlatformVersion>",
                after,
                count=1,
            )
        if after != before:
            project_path.write_text(after, encoding="utf-8")
            changed = True
            file_record["Changed"] = True
        file_record["Sha256After"] = sha256_or_empty(project_path)
        record["Files"].append(file_record)

    record["Gate"] = "pass"
    record["Modified"] = changed
    return record


def build_command(
    source_root: Path,
    msbuild: str,
    configuration: str,
    platform: str,
    platform_toolset: str = "",
    windows_sdk_version: str = "",
) -> List[str]:
    solutions = sorted(source_root.glob("*.sln"))
    if msbuild and solutions:
        command = [msbuild, str(solutions[0]), f"/p:Configuration={configuration}", f"/p:Platform={platform}"]
        if platform_toolset.strip():
            command.append(f"/p:PlatformToolset={platform_toolset.strip()}")
        if windows_sdk_version.strip():
            command.append(f"/p:WindowsTargetPlatformVersion={windows_sdk_version.strip()}")
        return command
    if (source_root / "Makefile").exists():
        return ["make"]
    return []


def run_process(command: Sequence[str], cwd: Path, timeout: int) -> Dict[str, Any]:
    if not command:
        return {
            "Command": [],
            "ReturnCode": None,
            "ElapsedSeconds": 0.0,
            "Stdout": "",
            "Stderr": "",
            "TimedOut": False,
            "Gate": "not_requested",
        }
    start = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout if timeout > 0 else None,
            check=False,
        )
        elapsed = time.monotonic() - start
        return {
            "Command": list(command),
            "ReturnCode": completed.returncode,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": completed.stdout,
            "Stderr": completed.stderr,
            "TimedOut": False,
            "Gate": "pass" if completed.returncode == 0 else "fail",
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        return {
            "Command": list(command),
            "ReturnCode": None,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": exc.stdout or "",
            "Stderr": exc.stderr or "",
            "TimedOut": True,
            "Gate": "fail",
        }
    except FileNotFoundError as exc:
        elapsed = time.monotonic() - start
        missing = str(command[0]) if command else ""
        return {
            "Command": list(command),
            "ReturnCode": None,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": "",
            "Stderr": f"{missing}: {exc}" if missing else str(exc),
            "TimedOut": False,
            "Gate": "fail",
            "ExceptionType": "FileNotFoundError",
        }
    except OSError as exc:
        elapsed = time.monotonic() - start
        return {
            "Command": list(command),
            "ReturnCode": None,
            "ElapsedSeconds": round(elapsed, 3),
            "Stdout": "",
            "Stderr": str(exc),
            "TimedOut": False,
            "Gate": "fail",
            "ExceptionType": exc.__class__.__name__,
        }


def generate_inlet_source_audit_if_needed(
    *,
    requested_path: Optional[Path],
    run_requested: bool,
    case_dir: Path,
    metadata_path: Path,
    manifest_out_path: Path,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    if requested_path is not None:
        return requested_path, {
            "Requested": False,
            "Generated": False,
            "Reason": "explicit_inlet_source_audit_path",
            "Path": str(requested_path),
        }
    if not run_requested:
        return None, {
            "Requested": False,
            "Generated": False,
            "Reason": "run_not_requested",
            "Path": "",
        }

    setup_path = first_existing_path(case_dir, [Path("src") / "setup.cpp", Path("setup.cpp")])
    defines_path = first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")])
    if setup_path is None:
        return None, {
            "Requested": True,
            "Generated": False,
            "Reason": "case_setup_cpp_missing",
            "Path": "",
        }

    script_path = Path(__file__).resolve().parent / "audit_inlet_source.py"
    out_path = manifest_out_path.parent / "inlet_source_audit_auto.json"
    command = [
        sys.executable,
        str(script_path),
        "--setup",
        str(setup_path),
        "--metadata",
        str(metadata_path),
        "--out",
        str(out_path),
    ]
    if defines_path is not None:
        command.extend(["--defines", str(defines_path)])

    process = run_process(command, Path(__file__).resolve().parents[1], timeout=0)
    return out_path, {
        "Requested": True,
        "Generated": out_path.is_file(),
        "Reason": "generated_from_case_source_before_run",
        "Path": str(out_path),
        "SetupPath": str(setup_path),
        "DefinesPath": str(defines_path) if defines_path is not None else "",
        "Command": process["Command"],
        "ReturnCode": process["ReturnCode"],
        "Gate": process["Gate"],
        "Stdout": process["Stdout"],
        "Stderr": process["Stderr"],
        "Sha256": sha256_or_empty(out_path),
    }


def generate_boundary_source_audit_if_needed(
    *,
    requested_path: Optional[Path],
    run_requested: bool,
    case_dir: Path,
    metadata_path: Path,
    manifest_out_path: Path,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    if requested_path is not None:
        return requested_path, {
            "Requested": False,
            "Generated": False,
            "Reason": "explicit_boundary_source_audit_path",
            "Path": str(requested_path),
        }
    if not run_requested:
        return None, {
            "Requested": False,
            "Generated": False,
            "Reason": "run_not_requested",
            "Path": "",
        }

    setup_path = first_existing_path(case_dir, [Path("src") / "setup.cpp", Path("setup.cpp")])
    defines_path = first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")])
    if setup_path is None:
        return None, {
            "Requested": True,
            "Generated": False,
            "Reason": "case_setup_cpp_missing",
            "Path": "",
        }

    script_path = Path(__file__).resolve().parent / "audit_boundary_source.py"
    out_path = manifest_out_path.parent / "boundary_source_audit_auto.json"
    command = [
        sys.executable,
        str(script_path),
        "--setup",
        str(setup_path),
        "--metadata",
        str(metadata_path),
        "--out",
        str(out_path),
    ]
    if defines_path is not None:
        command.extend(["--defines", str(defines_path)])

    process = run_process(command, Path(__file__).resolve().parents[1], timeout=0)
    return out_path, {
        "Requested": True,
        "Generated": out_path.is_file(),
        "Reason": "generated_from_case_source_before_run",
        "Path": str(out_path),
        "SetupPath": str(setup_path),
        "DefinesPath": str(defines_path) if defines_path is not None else "",
        "Command": process["Command"],
        "ReturnCode": process["ReturnCode"],
        "Gate": process["Gate"],
        "Stdout": process["Stdout"],
        "Stderr": process["Stderr"],
        "Sha256": sha256_or_empty(out_path),
    }


def generate_coordinate_probe_protocol_audit_if_needed(
    *,
    requested_path: Optional[Path],
    run_requested: bool,
    case_dir: Path,
    metadata_path: Path,
    manifest_out_path: Path,
    official_path: Optional[Path],
    af_path: Optional[Path],
    args: argparse.Namespace,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    if requested_path is not None:
        return requested_path, {
            "Requested": False,
            "Generated": False,
            "Reason": "explicit_coordinate_probe_protocol_audit_path",
            "Path": str(requested_path),
        }
    if not run_requested:
        return None, {
            "Requested": False,
            "Generated": False,
            "Reason": "run_not_requested",
            "Path": "",
        }
    if not metadata_path.is_file():
        return None, {
            "Requested": True,
            "Generated": False,
            "Reason": "case_metadata_missing",
            "Path": "",
        }

    script_path = Path(__file__).resolve().parent / "audit_coordinate_probe_protocol.py"
    out_path = manifest_out_path.parent / "coordinate_probe_protocol_audit_auto.json"
    command = [
        sys.executable,
        str(script_path),
        str(case_dir),
        "--metadata",
        str(metadata_path),
        "--out",
        str(out_path),
    ]
    if official_path is not None:
        command.extend(["--official", str(official_path)])
    if af_path is not None:
        command.extend(["--af-csv", str(af_path)])
    if args.expected_aij_case.strip():
        command.extend(["--expected-aij-case", args.expected_aij_case.strip()])
    if args.expected_wind_direction.strip():
        command.extend(["--expected-wind-direction", args.expected_wind_direction.strip()])
    if args.expected_wind_vector.strip():
        command.extend(["--expected-wind-vector", args.expected_wind_vector.strip()])
    if args.expected_probe_row_count:
        command.extend(["--expected-probe-row-count", str(args.expected_probe_row_count)])
    if args.expected_probe_z is not None:
        command.extend(["--expected-probe-z", str(args.expected_probe_z)])
    if args.expected_probe_z_min is not None:
        command.extend(["--expected-probe-z-min", str(args.expected_probe_z_min)])
    if args.expected_probe_z_max is not None:
        command.extend(["--expected-probe-z-max", str(args.expected_probe_z_max)])
    if args.official_condition_filter.strip():
        command.extend(["--official-condition-filter", args.official_condition_filter.strip()])
    official_wind_filter = args.official_wind_filter.strip() or args.expected_wind_direction.strip()
    if official_wind_filter:
        command.extend(["--official-wind-filter", official_wind_filter])
    if args.z_ref is not None:
        command.extend(["--z-ref", str(args.z_ref)])
    if args.expected_uref is not None:
        command.extend(["--expected-uref", str(args.expected_uref)])
    command.extend(["--uref-tolerance", str(args.uref_af_tolerance)])
    command.extend(["--probe-z-tolerance", str(args.expected_probe_z_tolerance)])

    process = run_process(command, Path(__file__).resolve().parents[1], timeout=0)
    return out_path, {
        "Requested": True,
        "Generated": out_path.is_file(),
        "Reason": "generated_from_case_metadata_and_official_inputs_before_run",
        "Path": str(out_path),
        "MetadataPath": str(metadata_path),
        "OfficialPath": str(official_path) if official_path is not None else "",
        "AfPath": str(af_path) if af_path is not None else "",
        "Command": process["Command"],
        "ReturnCode": process["ReturnCode"],
        "Gate": process["Gate"],
        "Stdout": process["Stdout"],
        "Stderr": process["Stderr"],
        "Sha256": sha256_or_empty(out_path),
    }


def find_executable(source_root: Path, explicit: str) -> Optional[Path]:
    if explicit:
        path = Path(explicit).expanduser()
        return path.resolve() if path.exists() else path
    candidates = [
        source_root / "bin" / "FluidX3D.exe",
        source_root / "x64" / "Release" / "FluidX3D.exe",
        source_root / "Release" / "FluidX3D.exe",
        source_root / "FluidX3D.exe",
    ]
    return next((path.resolve() for path in candidates if path.exists()), candidates[0].resolve())


def collect_vtk_files(output_dir: Path, pattern: str) -> List[Dict[str, Any]]:
    if not output_dir.exists():
        return []
    files = sorted(output_dir.glob(pattern))
    nested = output_dir / "output"
    if nested.exists():
        files.extend(sorted(nested.glob(pattern)))
    unique = {str(path.resolve()).lower(): path for path in files}
    records = [path_record("VTK velocity field", path) for path in unique.values() if path.is_file()]
    for record in records:
        record["SourceTimeStep"] = parse_vtk_time_step(Path(str(record.get("Path") or "")))
    return sorted(
        records,
        key=lambda record: (
            record["SourceTimeStep"] is None,
            record["SourceTimeStep"] if record["SourceTimeStep"] is not None else 0,
            str(record.get("Path") or ""),
        ),
    )


def audit_vtk_payload(path: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "PayloadCheckable": False,
        "PayloadComplete": None,
        "PayloadExpectedBytes": None,
        "PayloadActualBytes": None,
    }
    try:
        data = path.read_bytes()
    except OSError:
        result["PayloadComplete"] = False
        result["PayloadActualBytes"] = 0
        return result

    point_count: Optional[int] = None
    component_count: Optional[int] = None
    scalar_type = ""
    data_offset: Optional[int] = None
    offset = 0
    lines: List[Tuple[str, int]] = []
    for raw_line in data.splitlines(keepends=True):
        line_start = offset
        offset += len(raw_line)
        try:
            line = raw_line.decode("ascii", errors="ignore").strip()
        except UnicodeDecodeError:
            break
        lines.append((line, offset))
        upper = line.upper()
        parts = line.split()
        if len(parts) >= 2 and upper.startswith("POINT_DATA"):
            try:
                point_count = int(parts[1])
            except ValueError:
                point_count = None
        elif len(parts) >= 3 and upper.startswith("VECTORS"):
            component_count = 3
            scalar_type = parts[2].lower()
            data_offset = offset
            break
        elif len(parts) >= 3 and upper.startswith("SCALARS"):
            scalar_type = parts[2].lower()
            component_count = 1
            if len(parts) >= 4:
                try:
                    component_count = int(parts[3])
                except ValueError:
                    component_count = 1
            continue
        elif upper.startswith("LOOKUP_TABLE") and scalar_type and component_count is not None:
            data_offset = offset
            break
        if line_start > 65536:
            break

    bytes_per_value = {
        "char": 1,
        "unsigned_char": 1,
        "short": 2,
        "unsigned_short": 2,
        "int": 4,
        "unsigned_int": 4,
        "float": 4,
        "double": 8,
    }.get(scalar_type)
    if point_count is None or component_count is None or bytes_per_value is None or data_offset is None:
        return result

    expected_bytes = point_count * component_count * bytes_per_value
    actual_bytes = max(len(data) - data_offset, 0)
    result.update(
        {
            "PayloadCheckable": True,
            "PayloadComplete": actual_bytes >= expected_bytes,
            "PayloadExpectedBytes": expected_bytes,
            "PayloadActualBytes": actual_bytes,
        }
    )
    return result


def vtk_record_step_hash_pairs(vtk_records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pairs: List[Dict[str, Any]] = []
    for record in vtk_records:
        step = record.get("SourceTimeStep")
        digest = str(record.get("Sha256") or "").strip().upper()
        path = str(record.get("Path") or "").strip()
        if not isinstance(step, int) or not digest:
            continue
        pairs.append(
            {
                "TimeStep": step,
                "Sha256": digest,
                "StepHash": f"{step}:{digest}",
                "Path": path,
            }
        )
    return sorted(pairs, key=lambda item: (int(item["TimeStep"]), str(item["Path"])))


def parse_vtk_time_step(path: Path) -> Optional[int]:
    match = re.search(r"(\d+)(?=\.vtk$)", path.name.lower())
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def planned_frame_count(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int] = None,
) -> Optional[int]:
    steps = planned_vtk_steps(time_steps, save_interval, save_start_step)
    if steps is None:
        return None
    return len(steps)


def planned_vtk_steps(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int] = None,
) -> Optional[List[int]]:
    if time_steps is None or save_interval is None or time_steps <= 0 or save_interval <= 0:
        return None
    if save_start_step is not None and save_start_step < 0:
        return None
    first_step = save_interval if save_start_step is None or save_start_step <= 0 else save_start_step
    if first_step > time_steps:
        return []
    steps = list(range(first_step, time_steps + 1, save_interval))
    if not steps or steps[-1] != time_steps:
        steps.append(time_steps)
    return steps


def planned_final_window_span(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int],
    average_last_n: int,
) -> Optional[int]:
    saved_steps = planned_vtk_steps(time_steps, save_interval, save_start_step)
    if not saved_steps:
        return None
    selected = min(len(saved_steps), max(average_last_n, 1))
    if selected <= 1:
        return 0
    return saved_steps[-1] - saved_steps[-selected]


def required_average_last_n_for_step_span(
    save_interval: Optional[int],
    min_frames: int,
    min_step_span: int,
) -> int:
    if save_interval is None or save_interval <= 0 or min_step_span <= 0:
        return max(1, min_frames)
    return max(min_frames, int(math.ceil(min_step_span / float(save_interval))) + 1)


def audit_planned_vtk_schedule(
    time_steps: Optional[int],
    save_interval: Optional[int],
    save_start_step: Optional[int],
    expected_frame_count: Optional[int],
    average_last_n: int,
    min_frames: int,
    min_step_span: int,
) -> Dict[str, Any]:
    computed_frame_count = planned_frame_count(time_steps, save_interval, save_start_step)
    final_window_span = planned_final_window_span(time_steps, save_interval, save_start_step, average_last_n)
    recommended_average_last_n = required_average_last_n_for_step_span(save_interval, min_frames, min_step_span)
    recommended_minimum_time_steps: Optional[int] = None
    if save_interval is not None and save_interval > 0:
        first_step = save_interval if save_start_step is None or save_start_step <= 0 else save_start_step
        recommended_minimum_time_steps = first_step + (recommended_average_last_n - 1) * save_interval
    reasons: List[str] = []
    if time_steps is None or time_steps <= 0:
        reasons.append("time_steps_missing_or_invalid")
    if save_interval is None or save_interval <= 0:
        reasons.append("vtk_save_interval_missing_or_invalid")
    if save_start_step is not None and save_start_step < 0:
        reasons.append("vtk_save_start_step_invalid")
    if computed_frame_count is None:
        reasons.append("planned_vtk_frame_count_unavailable")
    elif computed_frame_count < min_frames:
        reasons.append(f"planned_vtk_frame_count_{computed_frame_count}_below_minimum_{min_frames}")
    if average_last_n <= 0:
        reasons.append("average_last_n_missing_or_invalid")
    elif average_last_n < min_frames:
        reasons.append(f"average_last_n_{average_last_n}_below_minimum_{min_frames}")
    if expected_frame_count is None:
        reasons.append("expected_vtk_frame_count_missing")
    elif computed_frame_count is not None and expected_frame_count != computed_frame_count:
        reasons.append(f"expected_vtk_frame_count_{expected_frame_count}_does_not_match_computed_{computed_frame_count}")
    if final_window_span is None:
        reasons.append("planned_final_window_step_span_unavailable")
    elif final_window_span < min_step_span:
        reasons.append(f"planned_final_window_step_span_{final_window_span}_below_minimum_{min_step_span}")
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "ComputedFrameCount": computed_frame_count,
        "SaveStartStep": save_start_step,
        "AverageLastN": average_last_n,
        "RecommendedAverageLastNForStepSpan": recommended_average_last_n,
        "RecommendedMinimumTimeStepsForCurrentSaveInterval": recommended_minimum_time_steps,
        "AdaptiveAverageWindowPolicy": "increase AverageLastN when SaveInterval is too small for the minimum final-window step span",
        "MinimumFrameCount": min_frames,
        "FinalWindowStepSpan": final_window_span,
        "MinimumStepSpan": min_step_span,
    }


def audit_actual_vtk_output(
    vtk_records: Sequence[Dict[str, Any]],
    expected_frame_count: Optional[int],
    expected_steps: Optional[Sequence[int]],
    average_last_n: int,
    min_frames: int,
    min_step_span: int,
    require_actual_output: bool,
) -> Dict[str, Any]:
    reasons: List[str] = []
    actual_count = len(vtk_records)
    parsed_records = [
        record
        for record in vtk_records
        if isinstance(record.get("SourceTimeStep"), int)
    ]
    sorted_records = sorted(
        parsed_records,
        key=lambda record: (int(record["SourceTimeStep"]), str(record.get("Path") or "")),
    )
    parsed_steps = [int(record["SourceTimeStep"]) for record in sorted_records]
    unparsable_count = actual_count - len(parsed_steps)
    sorted_steps = parsed_steps
    unique_step_count = len(set(sorted_steps))
    source_steps_strictly_increasing = len(sorted_steps) == unique_step_count
    selected_count = min(len(sorted_steps), max(average_last_n, 1))
    selected_records = sorted_records[-selected_count:] if selected_count > 0 else []
    selected_steps = [int(record["SourceTimeStep"]) for record in selected_records]
    source_step_span = selected_steps[-1] - selected_steps[0] if len(selected_steps) > 1 else 0
    selected_diffs = [b - a for a, b in zip(selected_steps, selected_steps[1:])]
    source_step_spacing_uniform = len(set(selected_diffs)) <= 1
    source_step_spacing = selected_diffs[0] if source_step_spacing_uniform and selected_diffs else None
    source_step_hash_pairs = vtk_record_step_hash_pairs(sorted_records)
    selected_step_hash_pairs = vtk_record_step_hash_pairs(selected_records)
    source_hashes = [str(item["Sha256"]) for item in source_step_hash_pairs]
    selected_hashes = [str(item["Sha256"]) for item in selected_step_hash_pairs]
    source_step_hash_csv = ";".join(str(item["StepHash"]) for item in source_step_hash_pairs)
    selected_step_hash_csv = ";".join(str(item["StepHash"]) for item in selected_step_hash_pairs)
    missing_hash_count = len(sorted_records) - len(source_hashes)
    payload_audits = {
        int(record["SourceTimeStep"]): audit_vtk_payload(Path(str(record.get("Path") or "")))
        for record in sorted_records
    }
    incomplete_payload_steps = [
        step
        for step, payload in payload_audits.items()
        if payload.get("PayloadCheckable") is True and payload.get("PayloadComplete") is False
    ]
    selected_payload_audits = {
        int(record["SourceTimeStep"]): payload_audits.get(int(record["SourceTimeStep"]), {})
        for record in selected_records
    }
    selected_incomplete_payload_steps = [
        step
        for step, payload in selected_payload_audits.items()
        if payload.get("PayloadCheckable") is True and payload.get("PayloadComplete") is False
    ]
    expected_step_list = list(expected_steps) if expected_steps is not None else None
    expected_selected_steps = (
        expected_step_list[-min(len(expected_step_list), max(average_last_n, 1)) :]
        if expected_step_list
        else None
    )
    if not require_actual_output:
        return {
            "Gate": "not_applicable",
            "Reasons": [],
            "ReasonsCsv": "",
            "ActualFrameCount": actual_count,
            "ExpectedFrameCount": expected_frame_count,
            "ActualSourceTimeSteps": sorted_steps,
            "ActualSourceTimeStepsCsv": ";".join(str(step) for step in sorted_steps),
            "ActualSourceVtkSha256": source_hashes,
            "ActualSourceVtkSha256Csv": ";".join(source_hashes),
            "ActualSourceStepHashPairs": source_step_hash_pairs,
            "ActualSourceStepHashPairsCsv": source_step_hash_csv,
            "SelectedFinalWindowTimeSteps": selected_steps,
            "SelectedFinalWindowTimeStepsCsv": ";".join(str(step) for step in selected_steps),
            "SelectedFinalWindowVtkSha256": selected_hashes,
            "SelectedFinalWindowVtkSha256Csv": ";".join(selected_hashes),
            "SelectedFinalWindowStepHashPairs": selected_step_hash_pairs,
            "SelectedFinalWindowStepHashPairsCsv": selected_step_hash_csv,
            "SelectedFinalWindowStepSpan": source_step_span,
            "ExpectedSourceTimeSteps": expected_step_list,
            "ExpectedSelectedFinalWindowTimeSteps": expected_selected_steps,
            "SourceVtkSha256Count": len(source_hashes),
            "SourceVtkSha256MissingCount": missing_hash_count,
            "SelectedFinalWindowVtkSha256Count": len(selected_hashes),
            "VtkPayloadIncompleteTimeSteps": incomplete_payload_steps,
            "SelectedFinalWindowPayloadIncompleteTimeSteps": selected_incomplete_payload_steps,
            "AverageLastN": average_last_n,
            "MinimumFrameCount": min_frames,
            "MinimumStepSpan": min_step_span,
            "ActualOutputRequired": False,
        }

    if actual_count <= 0:
        reasons.append("actual_vtk_output_missing")
    if actual_count < min_frames:
        reasons.append(f"actual_vtk_frame_count_{actual_count}_below_minimum_{min_frames}")
    if selected_count < min_frames:
        reasons.append(f"actual_vtk_final_window_frame_count_{selected_count}_below_minimum_{min_frames}")
    if expected_frame_count is not None and actual_count != expected_frame_count:
        reasons.append(
            f"actual_vtk_frame_count_{actual_count}_does_not_match_expected_{expected_frame_count}"
        )
    if unparsable_count:
        reasons.append(f"actual_vtk_source_time_steps_unparseable_count_{unparsable_count}")
    if missing_hash_count:
        reasons.append(f"actual_vtk_sha256_missing_count_{missing_hash_count}")
    if incomplete_payload_steps:
        reasons.append(f"actual_vtk_payload_incomplete_count_{len(incomplete_payload_steps)}")
    if selected_incomplete_payload_steps:
        reasons.append(
            f"actual_vtk_final_window_payload_incomplete_count_{len(selected_incomplete_payload_steps)}"
        )
    if len(source_hashes) != len(sorted_steps):
        reasons.append(
            f"actual_vtk_sha256_count_{len(source_hashes)}_does_not_match_parsed_time_steps_{len(sorted_steps)}"
        )
    if not source_steps_strictly_increasing:
        reasons.append("actual_vtk_source_time_steps_not_unique_or_strictly_increasing")
    if selected_steps and source_step_span < min_step_span:
        reasons.append(f"actual_vtk_final_window_step_span_{source_step_span}_below_minimum_{min_step_span}")
    if expected_step_list is not None and sorted_steps != expected_step_list:
        reasons.append("actual_vtk_source_time_steps_do_not_match_planned_schedule")
    if expected_selected_steps is not None and selected_steps != expected_selected_steps:
        reasons.append("actual_vtk_final_window_steps_do_not_match_planned_final_window")
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "ActualFrameCount": actual_count,
        "ExpectedFrameCount": expected_frame_count,
        "ActualSourceTimeSteps": sorted_steps,
        "ActualSourceTimeStepsCsv": ";".join(str(step) for step in sorted_steps),
        "ActualSourceVtkSha256": source_hashes,
        "ActualSourceVtkSha256Csv": ";".join(source_hashes),
        "ActualSourceStepHashPairs": source_step_hash_pairs,
        "ActualSourceStepHashPairsCsv": source_step_hash_csv,
        "ExpectedSourceTimeSteps": expected_step_list,
        "SelectedFinalWindowTimeSteps": selected_steps,
        "SelectedFinalWindowTimeStepsCsv": ";".join(str(step) for step in selected_steps),
        "SelectedFinalWindowVtkSha256": selected_hashes,
        "SelectedFinalWindowVtkSha256Csv": ";".join(selected_hashes),
        "SelectedFinalWindowStepHashPairs": selected_step_hash_pairs,
        "SelectedFinalWindowStepHashPairsCsv": selected_step_hash_csv,
        "SelectedFinalWindowStepSpan": source_step_span,
        "ExpectedSelectedFinalWindowTimeSteps": expected_selected_steps,
        "SourceTimeStepUnparsableCount": unparsable_count,
        "SourceTimeStepUniqueCount": unique_step_count,
        "SourceVtkSha256Count": len(source_hashes),
        "SourceVtkSha256MissingCount": missing_hash_count,
        "SelectedFinalWindowVtkSha256Count": len(selected_hashes),
        "VtkPayloadAudit": payload_audits,
        "VtkPayloadIncompleteTimeSteps": incomplete_payload_steps,
        "SelectedFinalWindowPayloadAudit": selected_payload_audits,
        "SelectedFinalWindowPayloadIncompleteTimeSteps": selected_incomplete_payload_steps,
        "SourceStepsStrictlyIncreasing": source_steps_strictly_increasing,
        "SourceStepSpacingUniform": source_step_spacing_uniform,
        "SourceStepSpacing": source_step_spacing,
        "AverageLastN": average_last_n,
        "MinimumFrameCount": min_frames,
        "MinimumStepSpan": min_step_span,
        "ActualOutputRequired": True,
    }


def audit_planned_synthetic_inlet_sampling(
    metadata: Dict[str, Any],
    final_window_step_span: Optional[int],
    default_min_refreshes: int,
) -> Dict[str, Any]:
    requested = metadata_bool(metadata, ["SyntheticTurbulentInletRequested", "SyntheticTurbulenceRequested"])
    injected = metadata_bool(metadata, ["SyntheticTurbulentInletInjected", "SyntheticTurbulenceInjected"])
    active = requested is True or injected is True
    update_interval = metadata_int(metadata, ["SyntheticTurbulenceUpdateInterval", "SyntheticTurbulentInletUpdateInterval"])
    metadata_minimum = metadata_int(metadata, ["SyntheticTurbulenceMinimumRecommendedRefreshes"])
    minimum_refreshes = metadata_minimum if metadata_minimum is not None and metadata_minimum > 0 else max(default_min_refreshes, 0)
    metadata_expected = metadata_int(metadata, ["SyntheticTurbulenceExpectedFinalWindowRefreshCount"])
    computed_refreshes: Optional[int] = None
    reasons: List[str] = []

    if not active:
        return {
            "Gate": "not_applicable",
            "Reasons": [],
            "ReasonsCsv": "",
            "SyntheticInletRequested": requested,
            "SyntheticInletInjected": injected,
            "SyntheticInletActive": False,
            "UpdateInterval": update_interval,
            "FinalWindowStepSpan": final_window_step_span,
            "ComputedRefreshCount": computed_refreshes,
            "MetadataExpectedRefreshCount": metadata_expected,
            "MinimumRefreshCount": minimum_refreshes,
        }

    if update_interval is None or update_interval <= 0:
        reasons.append("synthetic_inlet_update_interval_missing_or_invalid")
    elif final_window_step_span is None:
        reasons.append("planned_stg_final_window_step_span_unavailable")
    else:
        computed_refreshes = final_window_step_span // update_interval
        if computed_refreshes < minimum_refreshes:
            reasons.append(f"planned_stg_refresh_count_{computed_refreshes}_below_minimum_{minimum_refreshes}")

    if metadata_expected is not None and computed_refreshes is not None and metadata_expected != computed_refreshes:
        reasons.append(f"metadata_stg_refresh_count_{metadata_expected}_does_not_match_computed_{computed_refreshes}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "SyntheticInletRequested": requested,
        "SyntheticInletInjected": injected,
        "SyntheticInletActive": True,
        "UpdateInterval": update_interval,
        "FinalWindowStepSpan": final_window_step_span,
        "ComputedRefreshCount": computed_refreshes,
        "MetadataExpectedRefreshCount": metadata_expected,
        "MinimumRefreshCount": minimum_refreshes,
    }


def dominant_flow_axis(wind_vector: Optional[Tuple[float, float, float]]) -> Tuple[str, int]:
    if wind_vector is None:
        return "max_dimension_fallback", -1
    abs_components = [abs(float(component)) for component in wind_vector]
    axis_index = max(range(3), key=lambda index: abs_components[index])
    return ("x", "y", "z")[axis_index], axis_index


def estimate_reference_velocity_lbm(metadata: Dict[str, Any]) -> Tuple[Optional[float], str]:
    direct = metadata_float(metadata, ["ReferenceVelocityLbm", "ReferenceWindSpeedLbm", "UrefLbm"])
    if direct is not None and direct > 0.0:
        return direct, "metadata_reference_velocity_lbm"

    reference_mps = metadata_float(metadata, ["ReferenceWindSpeedMps", "UrefMps", "Uref"])
    mps_to_lbm = metadata_float(metadata, ["VelocityScaleMpsToLbm"])
    if reference_mps is not None and reference_mps > 0.0 and mps_to_lbm is not None and mps_to_lbm > 0.0:
        return reference_mps * mps_to_lbm, "reference_mps_times_velocity_scale_mps_to_lbm"

    lbm_to_mps = metadata_float(metadata, ["VelocityScaleLbmToMps"])
    if reference_mps is not None and reference_mps > 0.0 and lbm_to_mps is not None and lbm_to_mps > 0.0:
        return reference_mps / lbm_to_mps, "reference_mps_divided_by_velocity_scale_lbm_to_mps"

    profile_scale = metadata_float(metadata, ["ProfileScaleSpeedMps"])
    target_max_lbm = metadata_float(metadata, ["TargetMaxProfileVelocityLbm"])
    if (
        reference_mps is not None
        and reference_mps > 0.0
        and profile_scale is not None
        and profile_scale > 0.0
        and target_max_lbm is not None
        and target_max_lbm > 0.0
    ):
        return reference_mps / profile_scale * target_max_lbm, "reference_mps_over_profile_scale_times_target_max_lbm"

    return None, "missing_reference_velocity_lbm_inputs"


def audit_planned_flow_through_time(
    metadata: Dict[str, Any],
    grid_dimensions: Optional[Tuple[int, int, int]],
    time_steps: Optional[int],
    minimum_flow_throughs: float,
) -> Dict[str, Any]:
    if minimum_flow_throughs <= 0.0:
        return {
            "Gate": "not_applicable",
            "Reasons": [],
            "ReasonsCsv": "",
            "MinimumFlowThroughCount": minimum_flow_throughs,
        }

    reasons: List[str] = []
    wind_vector = parse_vector(
        metadata_value(metadata, ["WindDirectionUnitVector", "WindVector", "wind_vector", "WindDirectionVector"])
    )
    axis_name, axis_index = dominant_flow_axis(wind_vector)
    domain_length_cells: Optional[int] = None
    if grid_dimensions is None:
        reasons.append("flow_through_grid_dimensions_unavailable")
    elif axis_index < 0:
        domain_length_cells = max(grid_dimensions)
        reasons.append("flow_through_wind_vector_missing_using_max_dimension")
    else:
        domain_length_cells = int(grid_dimensions[axis_index])

    reference_velocity_lbm, reference_source = estimate_reference_velocity_lbm(metadata)
    one_flow_through_steps: Optional[int] = None
    minimum_time_steps: Optional[int] = None
    planned_flow_through_count: Optional[float] = None
    if reference_velocity_lbm is None or reference_velocity_lbm <= 0.0:
        reasons.append("flow_through_reference_velocity_lbm_missing_or_invalid")
    elif domain_length_cells is not None:
        one_flow_through_steps = int(math.ceil(domain_length_cells / reference_velocity_lbm))
        minimum_time_steps = int(math.ceil(one_flow_through_steps * minimum_flow_throughs))
        if time_steps is not None and time_steps > 0:
            planned_flow_through_count = time_steps / float(one_flow_through_steps)

    if time_steps is None or time_steps <= 0:
        reasons.append("flow_through_time_steps_missing_or_invalid")
    elif minimum_time_steps is not None and time_steps < minimum_time_steps:
        reasons.append(f"planned_time_steps_{time_steps}_below_minimum_flowthrough_steps_{minimum_time_steps}")

    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "GridDimensions": grid_dimensions,
        "WindVector": wind_vector,
        "DominantAxis": axis_name,
        "DomainLengthCells": domain_length_cells,
        "ReferenceVelocityLbm": reference_velocity_lbm,
        "ReferenceVelocitySource": reference_source,
        "EstimatedOneFlowThroughSteps": one_flow_through_steps,
        "MinimumFlowThroughCount": minimum_flow_throughs,
        "RecommendedMinimumTimeStepsForFlowThrough": minimum_time_steps,
        "PlannedFlowThroughCount": planned_flow_through_count,
    }


def runner_gate(reasons: Iterable[str]) -> Dict[str, Any]:
    reason_list = [reason for reason in reasons if reason]
    return {
        "Gate": "pass" if not reason_list else "diagnostic_only",
        "Reasons": reason_list,
        "ReasonsCsv": ";".join(reason_list),
    }


def split_reasons(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(";") if part.strip()]


def inlet_source_failure_reasons(report: Dict[str, Any]) -> List[str]:
    benign_reasons = {
        "inlet_source_consistent_with_declared_metadata",
        "source_distribution_consistent",
    }
    reasons: List[str] = []
    reasons.extend(split_reasons(report.get("paper_grade_inlet_source_gate_reasons")))
    reasons.extend(split_reasons(report.get("Reasons")))
    return [reason for reason in dict.fromkeys(reasons) if reason and reason not in benign_reasons]


def boundary_source_failure_reasons(report: Dict[str, Any]) -> List[str]:
    benign_reasons = {
        "boundary_source_consistent_with_declared_metadata",
        "boundary_source_wind_tunnel_equivalent",
    }
    reasons: List[str] = []
    reasons.extend(split_reasons(report.get("boundary_source_gate_reasons")))
    reasons.extend(split_reasons(report.get("paper_grade_boundary_source_gate_reasons")))
    reasons.extend(split_reasons(report.get("Reasons")))
    return [reason for reason in dict.fromkeys(reasons) if reason and reason not in benign_reasons]


def native_accuracy_evidence_gate(
    run_record: Dict[str, Any],
    actual_vtk_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Gate native accuracy interpretation separately from dry-run preflight."""
    reasons: List[str] = []

    run_requested = bool(run_record.get("Requested"))
    run_gate = str(run_record.get("Gate") or "").strip().lower()
    actual_vtk_gate = str(actual_vtk_output.get("Gate") or "").strip().lower()
    actual_output_required = actual_vtk_output.get("ActualOutputRequired") is True
    actual_frame_count = as_int(actual_vtk_output.get("ActualFrameCount"))
    selected_hash_count = as_int(actual_vtk_output.get("SelectedFinalWindowVtkSha256Count"))

    if not run_requested:
        reasons.append("native_run_not_requested")
    elif run_gate != "pass":
        reasons.append(f"native_run_gate_not_pass:{run_gate or 'missing'}")

    if not actual_output_required:
        reasons.append("actual_vtk_output_not_required_by_this_invocation")
    if actual_vtk_gate != "pass":
        reasons.append(f"actual_vtk_output_gate_not_pass:{actual_vtk_gate or 'missing'}")
    for reason in split_reasons(actual_vtk_output.get("Reasons")):
        reasons.append(f"actual_vtk_output_reason:{reason}")
    if actual_frame_count is None or actual_frame_count <= 0:
        reasons.append("actual_vtk_frame_count_missing_or_zero")
    if selected_hash_count is None or selected_hash_count <= 0:
        reasons.append("selected_final_window_vtk_hashes_missing")

    return {
        "Gate": "pass" if not reasons else "fail",
        "Reasons": reasons or ["native_run_and_vtk_evidence_present"],
        "ReasonsCsv": ";".join(reasons or ["native_run_and_vtk_evidence_present"]),
        "RunRequested": run_requested,
        "RunGate": run_gate,
        "ActualVtkOutputRequired": actual_output_required,
        "ActualVtkOutputGate": actual_vtk_gate,
        "ActualFrameCount": actual_frame_count,
        "SelectedFinalWindowVtkSha256Count": selected_hash_count,
    }


def audit_inlet_source_report(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"Gate": "not_applicable", "Reasons": [], "ReasonsCsv": "", "Path": "", "Exists": False}
    report = json_load(path)
    if not report:
        reason = "inlet_source_audit_missing_or_unreadable"
        return {
            "Gate": "diagnostic_only",
            "Reasons": [reason],
            "ReasonsCsv": reason,
            "Path": str(path),
            "Exists": path.is_file(),
        }
    paper_gate = str(report.get("paper_grade_inlet_source_gate") or report.get("Gate") or "").strip().lower()
    reasons: List[str] = []
    if paper_gate not in {"pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"paper_grade_inlet_source_gate_not_pass:{paper_gate or 'missing'}")
    reasons.extend(inlet_source_failure_reasons(report))
    reasons = list(dict.fromkeys(reasons))
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(path),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "PaperGradeInletSourceGate": paper_gate,
    }


def audit_boundary_source_report(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"Gate": "not_applicable", "Reasons": [], "ReasonsCsv": "", "Path": "", "Exists": False}
    report = json_load(path)
    if not report:
        reason = "boundary_source_audit_missing_or_unreadable"
        return {
            "Gate": "diagnostic_only",
            "Reasons": [reason],
            "ReasonsCsv": reason,
            "Path": str(path),
            "Exists": path.is_file(),
        }
    source_gate = str(report.get("boundary_source_gate") or "").strip().lower()
    paper_gate = str(report.get("paper_grade_boundary_source_gate") or report.get("Gate") or "").strip().lower()
    reasons: List[str] = []
    if source_gate and source_gate != "pass":
        reasons.append(f"boundary_source_gate_not_pass:{source_gate}")
    elif not source_gate:
        reasons.append("boundary_source_gate_not_pass:missing")
    if paper_gate not in {"pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"paper_grade_boundary_source_gate_not_pass:{paper_gate or 'missing'}")
    reasons.extend(boundary_source_failure_reasons(report))
    reasons = list(dict.fromkeys(reasons))
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(path),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "BoundarySourceGate": source_gate,
        "PaperGradeBoundarySourceGate": paper_gate,
    }


def audit_coordinate_probe_protocol_report(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"Gate": "not_applicable", "Reasons": [], "ReasonsCsv": "", "Path": "", "Exists": False}
    report = json_load(path)
    if not report:
        reason = "coordinate_probe_protocol_audit_missing_or_unreadable"
        return {
            "Gate": "diagnostic_only",
            "Reasons": [reason],
            "ReasonsCsv": reason,
            "Path": str(path),
            "Exists": path.is_file(),
            "Sha256": sha256_or_empty(path),
        }
    protocol_gate = str(report.get("coordinate_probe_protocol_gate") or report.get("Gate") or "").strip().lower()
    long_cfd_allowed = report.get("long_cfd_allowed_by_coordinate_probe_protocol")
    reasons: List[str] = []
    if protocol_gate not in {"pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"coordinate_probe_protocol_gate_not_pass:{protocol_gate or 'missing'}")
    if long_cfd_allowed is not True:
        reasons.append(f"long_cfd_allowed_by_coordinate_probe_protocol_not_true:{long_cfd_allowed}")
    reasons.extend(split_reasons(report.get("Reasons")))
    reasons = list(dict.fromkeys(reasons))
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(path),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "CoordinateProbeProtocolGate": protocol_gate,
        "LongCfdAllowed": long_cfd_allowed,
        "DevelopmentAccelerationStage": report.get("development_acceleration_stage", ""),
        "DevelopmentAccelerationNextCfdScope": report.get("development_acceleration_next_cfd_scope", ""),
    }


def audit_inlet_correlation_report(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"Gate": "not_applicable", "Reasons": [], "ReasonsCsv": "", "Path": "", "Exists": False}
    report = json_load(path)
    if not report:
        reason = "inlet_correlation_audit_missing_or_unreadable"
        return {
            "Gate": "diagnostic_only",
            "Reasons": [reason],
            "ReasonsCsv": reason,
            "Path": str(path),
            "Exists": path.is_file(),
            "Sha256": sha256_or_empty(path),
        }
    correlation_gate = str(report.get("inlet_correlation_gate") or report.get("Gate") or "").strip().lower()
    k_variance_gate = str(report.get("inlet_k_variance_gate") or "").strip().lower()
    tke_gate = str(report.get("inlet_tke_gate") or "").strip().lower()
    reasons: List[str] = []
    if correlation_gate != "pass":
        reasons.append(f"inlet_correlation_gate_not_pass:{correlation_gate or 'missing'}")
    if k_variance_gate != "pass":
        reasons.append(f"inlet_k_variance_gate_not_pass:{k_variance_gate or 'missing'}")
    if tke_gate != "pass":
        reasons.append(f"inlet_tke_gate_not_pass:{tke_gate or 'missing'}")
    benign_reasons = {
        "inlet_correlation_evidence_present",
        "k_variance_evidence_present",
        "tke_evidence_present",
    }
    reasons.extend(
        reason
        for reason in split_reasons(report.get("inlet_correlation_gate_reasons"))
        if reason not in benign_reasons
    )
    if k_variance_gate != "pass":
        reasons.extend(
            f"inlet_k_variance:{reason}"
            for reason in split_reasons(report.get("inlet_k_variance_gate_reasons"))
            if reason not in benign_reasons
        )
    if tke_gate != "pass":
        reasons.extend(
            f"inlet_tke:{reason}"
            for reason in split_reasons(report.get("inlet_tke_gate_reasons"))
            if reason not in benign_reasons
        )
    reasons = list(dict.fromkeys(reasons))
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "Path": str(path),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "InletCorrelationGate": correlation_gate,
        "InletKVarianceGate": k_variance_gate,
        "InletTkeGate": tke_gate,
        "TemporalLag1Correlation": report.get("temporal_lag1_correlation"),
        "SpatialAdjacentCorrelation": report.get("spatial_adjacent_correlation"),
        "InletStreamwiseVarianceToKRatio": report.get("inlet_streamwise_variance_to_k_ratio"),
        "InletTkeToKRatio": report.get("inlet_tke_to_k_ratio"),
    }


def audit_runtime_inlet_diagnostics_csv(path: Optional[Path]) -> Dict[str, Any]:
    requested = path is not None
    if path is None:
        return {"Gate": "not_applicable", "Requested": False, "Reasons": [], "ReasonsCsv": "", "CsvPath": ""}
    reasons: List[str] = []
    rows: List[Dict[str, str]] = []
    fieldnames: List[str] = []
    if not path.is_file():
        reasons.append("runtime_inlet_diagnostics_csv_missing")
    else:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except OSError:
            reasons.append("runtime_inlet_diagnostics_csv_unreadable")
    required = {"step", "profile_index", "target_k_m2s2", "k_m2s2"}
    missing = sorted(required - set(fieldnames))
    if missing:
        reasons.extend(f"runtime_inlet_diagnostics_column_missing:{name}" for name in missing)
    if path.is_file() and not rows:
        reasons.append("runtime_inlet_diagnostics_csv_empty")

    profile_ids = sorted({row.get("profile_index", "").strip() for row in rows if row.get("profile_index", "").strip()})
    step_values = [as_int(row.get("step")) for row in rows]
    valid_steps = [int(value) for value in step_values if value is not None]
    parsed = {
        "RowCount": len(rows),
        "ProfileCount": len(profile_ids),
        "ProfileIds": profile_ids,
        "StepMin": min(valid_steps) if valid_steps else None,
        "StepMax": max(valid_steps) if valid_steps else None,
        "Columns": fieldnames,
    }
    return {
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Requested": requested,
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "CsvPath": str(path),
        "CsvSha256": sha256_or_empty(path),
        "AuditJsonPath": "",
        "AuditJsonSha256": "",
        "ParsedAudit": parsed,
    }


def paper_use_gate(
    diagnostic_override_allowed: bool,
    *,
    official_input: Dict[str, Any],
    inlet_source: Dict[str, Any],
    boundary_source: Dict[str, Any],
    coordinate_probe_protocol: Dict[str, Any],
    inlet_correlation: Dict[str, Any],
    planned_vtk_schedule: Dict[str, Any],
    flow_through_time: Dict[str, Any],
    actual_vtk_output: Dict[str, Any],
    runtime_inlet_diagnostics: Dict[str, Any],
    native_accuracy_gate: Dict[str, Any],
) -> Dict[str, Any]:
    checks = [
        ("official_input", official_input, "Gate"),
        ("inlet_source", inlet_source, "Gate"),
        ("boundary_source", boundary_source, "Gate"),
        ("coordinate_probe_protocol", coordinate_probe_protocol, "Gate"),
        ("inlet_correlation", inlet_correlation, "Gate"),
        ("planned_vtk_schedule", planned_vtk_schedule, "Gate"),
        ("flow_through_time", flow_through_time, "Gate"),
        ("actual_vtk_output", actual_vtk_output, "Gate"),
        ("runtime_inlet_diagnostics", runtime_inlet_diagnostics, "Gate"),
        ("native_accuracy_evidence", native_accuracy_gate, "Gate"),
    ]
    reasons: List[str] = []
    if diagnostic_override_allowed:
        reasons.append("diagnostic_execution_override_used")
    for label, payload, gate_key in checks:
        gate = str(payload.get(gate_key) or "").strip().lower()
        if gate != "pass":
            reasons.append(f"{label}_gate_not_pass:{gate or 'missing'}")
        for reason in split_reasons(payload.get("Reasons")):
            reasons.append(f"{label}:{reason}")
    reasons = list(dict.fromkeys(reasons))
    return {
        "Gate": "pass" if not reasons else "fail",
        "PaperUsable": not reasons,
        "Reasons": reasons or ["native_result_is_paper_usable"],
        "ReasonsCsv": ";".join(reasons or ["native_result_is_paper_usable"]),
        "Interpretation": (
            "paper_grade_accuracy_evidence"
            if not reasons
            else "debug_or_diagnostic_only_do_not_use_for_r2_or_paper_accuracy_claim"
        ),
    }


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    solver_cwd = Path(args.solver_cwd).expanduser().resolve() if args.solver_cwd.strip() else source_root
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    official_path = Path(args.official).expanduser().resolve() if args.official else None
    af_path = Path(args.af_csv).expanduser().resolve() if args.af_csv else None
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else (solver_cwd / "output" if args.run else case_dir)
    if args.run:
        solver_cwd.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata.strip() else case_dir / "case_metadata.json"
    validation_protocol_path = (
        Path(args.validation_protocol_audit).expanduser().resolve()
        if args.validation_protocol_audit.strip()
        else case_dir / "validation_protocol_audit.json"
    )
    inlet_source_audit_path = (
        Path(args.inlet_source_audit).expanduser().resolve()
        if args.inlet_source_audit.strip()
        else None
    )
    boundary_source_audit_path = (
        Path(args.boundary_source_audit).expanduser().resolve()
        if args.boundary_source_audit.strip()
        else None
    )
    coordinate_probe_protocol_audit_path = (
        Path(args.coordinate_probe_protocol_audit).expanduser().resolve()
        if args.coordinate_probe_protocol_audit.strip()
        else None
    )
    inlet_correlation_audit_path = (
        Path(args.inlet_correlation_audit).expanduser().resolve()
        if args.inlet_correlation_audit.strip()
        else None
    )
    metadata = json_load(metadata_path)
    inlet_diagnostics_path, runtime_inlet_diagnostics_resolution = resolve_runtime_inlet_diagnostics_path(
        args.inlet_diagnostics_csv,
        metadata,
        case_dir=case_dir,
        solver_cwd=solver_cwd,
        output_dir=output_dir,
        run_requested=args.run,
        output_dir_requested=bool(args.output_dir.strip()),
    )
    case_label, wind_label = case_identity(metadata)
    validation_protocol = audit_validation_protocol(validation_protocol_path)
    identity = effective_identity(case_label, wind_label, validation_protocol)
    metadata_preconditions = audit_case_metadata_preconditions(metadata)
    setup_source_preconditions = audit_case_setup_source_preconditions(
        case_dir,
        metadata,
        expected_time_steps=args.time_steps,
        expected_save_interval=args.vtk_save_interval,
    )
    inlet_source_audit_path, auto_inlet_source_audit = generate_inlet_source_audit_if_needed(
        requested_path=inlet_source_audit_path,
        run_requested=args.run,
        case_dir=case_dir,
        metadata_path=metadata_path,
        manifest_out_path=out_path,
    )
    boundary_source_audit_path, auto_boundary_source_audit = generate_boundary_source_audit_if_needed(
        requested_path=boundary_source_audit_path,
        run_requested=args.run,
        case_dir=case_dir,
        metadata_path=metadata_path,
        manifest_out_path=out_path,
    )
    (
        coordinate_probe_protocol_audit_path,
        auto_coordinate_probe_protocol_audit,
    ) = generate_coordinate_probe_protocol_audit_if_needed(
        requested_path=coordinate_probe_protocol_audit_path,
        run_requested=args.run,
        case_dir=case_dir,
        metadata_path=metadata_path,
        manifest_out_path=out_path,
        official_path=official_path,
        af_path=af_path,
        args=args,
    )
    official_input_preconditions = audit_official_input_preconditions(
        official_path,
        af_path,
        metadata,
        validation_protocol,
        expected_case=args.expected_aij_case.strip(),
        official_condition_filter=args.official_condition_filter,
        expected_wind=args.expected_wind_direction.strip(),
        official_wind_filter=args.official_wind_filter,
        expected_probe_row_count=args.expected_probe_row_count,
        expected_probe_z=args.expected_probe_z,
        expected_probe_z_min=args.expected_probe_z_min,
        expected_probe_z_max=args.expected_probe_z_max,
        expected_probe_z_tolerance=args.expected_probe_z_tolerance,
        z_ref=args.z_ref,
        expected_uref=args.expected_uref,
        uref_af_tolerance=args.uref_af_tolerance,
        expected_wind_vector_text=args.expected_wind_vector,
        wind_vector_tolerance=args.wind_vector_tolerance,
        require_af_k=args.require_af_k,
    )
    inlet_source_audit = audit_inlet_source_report(inlet_source_audit_path)
    boundary_source_audit = audit_boundary_source_report(boundary_source_audit_path)
    coordinate_probe_protocol_audit = audit_coordinate_probe_protocol_report(coordinate_probe_protocol_audit_path)
    inlet_correlation_audit = audit_inlet_correlation_report(inlet_correlation_audit_path)
    runtime_inlet_diagnostics_expected = synthetic_inlet_expects_runtime_diagnostics(metadata)
    runtime_inlet_diagnostics = (
        pending_runtime_inlet_diagnostics(inlet_diagnostics_path)
        if args.run
        else audit_runtime_inlet_diagnostics_csv(inlet_diagnostics_path)
    )
    vtk_save_start_step = (
        args.vtk_save_start_step
        if args.vtk_save_start_step is not None
        else metadata_vtk_save_start_step(metadata)
    )
    expected_case = args.expected_aij_case.strip()
    expected_wind = args.expected_wind_direction.strip()
    source_validation = validate_source_root(source_root)
    pre_install_native_source_files = collect_native_source_files(source_root, "Pre-install")
    execution_requested = args.install or args.build or args.run
    allow_pending_install_mismatch = not execution_requested
    pre_install_case_source_parity = audit_case_to_source_parity(
        case_dir,
        source_root,
        metadata,
        allow_pending_install_mismatch=allow_pending_install_mismatch,
    )

    reasons: List[str] = []
    if not case_dir.is_dir():
        reasons.append("case_dir_missing")
    if not source_root.is_dir():
        reasons.append("native_source_root_missing")
    if not source_validation["IsValid"]:
        reasons.append("native_source_validation_failed")
    for role, candidates in REQUIRED_CASE_FILE_CANDIDATES:
        if first_existing_path(case_dir, candidates) is None:
            reasons.append(f"case_required_file_missing:{role}")
    for role, rel in REQUIRED_CASE_FILES:
        if role == "Validation protocol audit":
            path = validation_protocol_path
        elif role == "Case metadata":
            path = metadata_path
        else:
            path = case_dir / rel
        if not path.is_file():
            reasons.append(f"case_required_file_missing:{role}")
    if validation_protocol["Gate"] != "pass":
        reasons.extend(str(reason) for reason in validation_protocol["Reasons"])
    if metadata_preconditions["Gate"] != "pass":
        reasons.extend(str(reason) for reason in metadata_preconditions["Reasons"])
    if setup_source_preconditions["Gate"] != "pass":
        reasons.extend(str(reason) for reason in setup_source_preconditions["Reasons"])
    if official_input_preconditions["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in official_input_preconditions["Reasons"])
    if inlet_source_audit["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in inlet_source_audit["Reasons"])
    if args.run and not auto_inlet_source_audit.get("Generated") and inlet_source_audit_path is None:
        reasons.append("run_requested_without_inlet_source_audit")
    if boundary_source_audit["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in boundary_source_audit["Reasons"])
    if args.run and not auto_boundary_source_audit.get("Generated") and boundary_source_audit_path is None:
        reasons.append("run_requested_without_boundary_source_audit")
    if coordinate_probe_protocol_audit["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in coordinate_probe_protocol_audit["Reasons"])
    if args.run and not auto_coordinate_probe_protocol_audit.get("Generated") and coordinate_probe_protocol_audit_path is None:
        reasons.append("run_requested_without_coordinate_probe_protocol_audit")
    if inlet_correlation_audit["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in inlet_correlation_audit["Reasons"])
    if args.run:
        if runtime_inlet_diagnostics_expected and inlet_diagnostics_path is None:
            reasons.append("run_requested_without_runtime_inlet_diagnostics_path")
    elif runtime_inlet_diagnostics["Gate"] not in {"pass", "not_applicable"}:
        reasons.extend(str(reason) for reason in runtime_inlet_diagnostics["Reasons"])
    effective_case_label = identity["Case"]
    effective_wind_label = identity["WindDirection"]
    if expected_case and not effective_case_label:
        reasons.append("case_label_missing_in_metadata")
    elif not identity_matches(expected_case, effective_case_label):
        reasons.append(f"case_label_mismatch:{effective_case_label}")
    if expected_wind and not effective_wind_label:
        reasons.append("wind_direction_missing_in_metadata")
    elif not identity_matches(expected_wind, effective_wind_label):
        reasons.append(f"wind_direction_mismatch:{effective_wind_label}")

    vtk_schedule = audit_planned_vtk_schedule(
        args.time_steps,
        args.vtk_save_interval,
        vtk_save_start_step,
        args.expected_vtk_frame_count,
        args.average_last_n,
        args.min_vtk_frames,
        args.min_vtk_step_span,
    )
    if vtk_schedule["Gate"] != "pass":
        reasons.extend(str(reason) for reason in vtk_schedule["Reasons"])
    defines_for_output = first_existing_path(case_dir, [Path("src") / "defines.hpp", Path("defines.hpp")])
    if defines_for_output is None:
        source_defines = source_root / "src" / "defines.hpp"
        defines_for_output = source_defines if source_defines.is_file() else None
    grid_dimensions = parse_grid_dimensions_from_defines(defines_for_output) if defines_for_output is not None else None
    flow_through_time = audit_planned_flow_through_time(
        metadata,
        grid_dimensions,
        args.time_steps,
        args.min_flow_throughs,
    )
    if flow_through_time["Gate"] == "diagnostic_only":
        reasons.extend(str(reason) for reason in flow_through_time["Reasons"])
    output_disk_space = audit_output_disk_space(
        output_dir,
        grid_dimensions,
        vtk_schedule["ComputedFrameCount"],
        require_for_run=args.run,
    )
    if output_disk_space["Gate"] == "blocked":
        reasons.extend(f"output_disk_space:{reason}" for reason in output_disk_space["Reasons"])
    if args.run and bool(args.output_dir.strip()):
        expected_relative_output = (solver_cwd / "output").resolve()
        if output_dir.resolve() != expected_relative_output:
            reasons.append("output_dir_not_solver_cwd_output_for_generated_setup_relative_output")
    if args.run and bool(args.output_dir.strip()) and not args.disable_graphics_for_run:
        reasons.append("run_requested_without_disable_graphics_for_batch_vtk")
    synthetic_sampling = audit_planned_synthetic_inlet_sampling(
        metadata,
        vtk_schedule["FinalWindowStepSpan"],
        args.min_stg_refreshes,
    )
    if synthetic_sampling["Gate"] == "diagnostic_only":
        reasons.extend(str(reason) for reason in synthetic_sampling["Reasons"])
    if (args.build or args.run) and not args.install and pre_install_case_source_parity["Gate"] != "pass":
        reasons.append("execution_requested_without_install_or_case_source_parity")
        reasons.extend(f"pre_install_case_source_parity:{reason}" for reason in pre_install_case_source_parity["Reasons"])

    pre_execution_gate = runner_gate(reasons)
    disk_space_allows_run = output_disk_space["Gate"] != "blocked"
    execution_allowed = (pre_execution_gate["Gate"] == "pass" or args.allow_diagnostic_execution) and disk_space_allows_run
    if execution_requested and not execution_allowed and disk_space_allows_run:
        reasons.append("execution_requested_but_preflight_gate_diagnostic_only")
    if args.run and not disk_space_allows_run:
        reasons.append("execution_requested_but_output_disk_space_blocked")

    install_record: Dict[str, Any] = {
        "Requested": args.install,
        "Performed": False,
        "Backups": [],
        "InstalledFiles": [],
        "Gate": "not_requested",
    }
    reconstruction_adaptation: Dict[str, Any] = {"Requested": args.install, "Gate": "not_requested"}
    if args.install:
        if not execution_allowed:
            install_record["Gate"] = "blocked"
            reconstruction_adaptation["Gate"] = "blocked"
        elif source_validation["IsValid"] and case_dir.is_dir():
            reconstruction_adaptation = adapt_case_reconstruction_macros(case_dir, source_root)
            install_data = install_case(case_dir, source_root, out_path.parent / "native_source_backups")
            install_record.update(install_data)
            install_record["Performed"] = True
            install_record["Gate"] = "pass"
        else:
            install_record["Gate"] = "fail"
            reconstruction_adaptation["Gate"] = "fail"
            reasons.append("install_requested_but_preflight_failed")

    post_install_case_source_parity = audit_case_to_source_parity(
        case_dir,
        source_root,
        metadata,
        allow_pending_install_mismatch=allow_pending_install_mismatch,
    )
    case_to_run_source_parity = post_install_case_source_parity if args.install else pre_install_case_source_parity
    if args.install and install_record["Gate"] == "pass" and post_install_case_source_parity["Gate"] != "pass":
        reasons.append("post_install_case_source_parity_failed")
        reasons.extend(f"post_install_case_source_parity:{reason}" for reason in post_install_case_source_parity["Reasons"])

    graphics_batch_record: Dict[str, Any] = {"Requested": args.disable_graphics_for_run, "Gate": "not_requested"}
    if args.disable_graphics_for_run:
        if not execution_allowed:
            graphics_batch_record["Gate"] = "blocked"
        else:
            graphics_batch_record = disable_graphics_macros_for_run(source_root)
            if graphics_batch_record["Gate"] != "pass":
                reasons.append("disable_graphics_for_run_failed")

    runtime_workdir_inputs: List[Dict[str, Any]] = []
    if args.run and execution_allowed:
        runtime_workdir_inputs = materialize_solver_workdir_inputs(case_dir, source_root, solver_cwd)

    msbuild = find_msbuild(args.msbuild)
    windows_sdk_version = resolve_windows_sdk_version(args.windows_sdk_version)
    windows_sdk_patch_record: Dict[str, Any] = {"RequestedVersion": windows_sdk_version, "Gate": "not_requested"}
    if args.build and execution_allowed:
        windows_sdk_patch_record = patch_windows_sdk_project_files(source_root, windows_sdk_version)
    command = build_command(
        source_root,
        msbuild,
        args.configuration,
        args.platform,
        args.platform_toolset,
        windows_sdk_version,
    )
    build_record: Dict[str, Any] = {
        "Requested": args.build,
        "MSBuild": msbuild,
        "WindowsSdkVersionRequested": args.windows_sdk_version,
        "WindowsSdkVersionResolved": windows_sdk_version,
        "Command": command,
        "ReturnCode": None,
        "ElapsedSeconds": 0.0,
        "Stdout": "",
        "Stderr": "",
        "TimedOut": False,
        "Gate": "not_requested",
    }
    if args.build:
        if not execution_allowed:
            build_record["Gate"] = "blocked"
        elif not command:
            build_record["Gate"] = "fail"
            reasons.append("build_requested_but_no_build_command")
        else:
            build_record.update(run_process(command, source_root, args.timeout_seconds))
            if build_record["Gate"] != "pass":
                reasons.append("build_failed")

    exe_path = find_executable(source_root, args.exe)
    run_record: Dict[str, Any] = {
        "Requested": args.run,
        "Executable": str(exe_path) if exe_path is not None else "",
        "ExecutableSha256": sha256_or_empty(exe_path),
        "Command": [str(exe_path)] if exe_path is not None else [],
        "ReturnCode": None,
        "ElapsedSeconds": 0.0,
        "Stdout": "",
        "Stderr": "",
        "TimedOut": False,
        "Gate": "not_requested",
    }
    if args.run:
        if not execution_allowed:
            run_record["Gate"] = "blocked"
        elif args.build and build_record["Gate"] != "pass":
            run_record["Gate"] = "blocked"
            reasons.append("run_blocked_because_build_failed")
        elif exe_path is None or not exe_path.exists():
            run_record["Gate"] = "fail"
            reasons.append("run_requested_but_executable_missing")
        else:
            run_record.update(run_process([str(exe_path)], solver_cwd, args.timeout_seconds))
            if run_record["Gate"] != "pass":
                reasons.append("run_failed")

    vtk_records = collect_vtk_files(output_dir, args.vtk_pattern)
    actual_output_required = (args.run and run_record["Gate"] == "pass") or bool(args.output_dir.strip())
    if args.run and run_record["Gate"] == "pass" and not vtk_records:
        reasons.append("run_requested_but_no_vtk_output_found")

    actual_vtk_output = audit_actual_vtk_output(
        vtk_records,
        vtk_schedule["ComputedFrameCount"],
        planned_vtk_steps(args.time_steps, args.vtk_save_interval, vtk_save_start_step),
        args.average_last_n,
        args.min_vtk_frames,
        args.min_vtk_step_span,
        actual_output_required,
    )
    if actual_vtk_output["Gate"] == "diagnostic_only":
        reasons.extend(str(reason) for reason in actual_vtk_output["Reasons"])
    if args.run:
        if run_record["Gate"] == "pass":
            runtime_inlet_diagnostics = audit_runtime_inlet_diagnostics_csv(inlet_diagnostics_path)
            if runtime_inlet_diagnostics["Gate"] not in {"pass", "not_applicable"}:
                reasons.extend(str(reason) for reason in runtime_inlet_diagnostics["Reasons"])
        else:
            runtime_inlet_diagnostics = {
                "Gate": "diagnostic_only",
                "Requested": inlet_diagnostics_path is not None,
                "Reasons": ["runtime_inlet_diagnostics_not_audited_because_run_did_not_pass"],
                "ReasonsCsv": "runtime_inlet_diagnostics_not_audited_because_run_did_not_pass",
                "CsvPath": str(inlet_diagnostics_path) if inlet_diagnostics_path is not None else "",
                "PreRunOnly": False,
            }
    native_accuracy_gate = native_accuracy_evidence_gate(run_record, actual_vtk_output)
    paper_gate = paper_use_gate(
        args.allow_diagnostic_execution,
        official_input=official_input_preconditions,
        inlet_source=inlet_source_audit,
        boundary_source=boundary_source_audit,
        coordinate_probe_protocol=coordinate_probe_protocol_audit,
        inlet_correlation=inlet_correlation_audit,
        planned_vtk_schedule=vtk_schedule,
        flow_through_time=flow_through_time,
        actual_vtk_output=actual_vtk_output,
        runtime_inlet_diagnostics=runtime_inlet_diagnostics,
        native_accuracy_gate=native_accuracy_gate,
    )

    source_validation = validate_source_root(source_root)
    required_files = collect_required_files(
        source_root,
        case_dir,
        metadata_path=metadata_path,
        validation_protocol_path=validation_protocol_path,
    )
    effective_run_source_files = collect_effective_run_source_files(source_root)
    baseline_id = args.baseline_id.strip() or f"native-fluidx3d-{case_label or 'case'}-{wind_label or 'wind'}-{utc_now()}"
    manifest = {
        "Schema": "citylbm.native_fluidx3d_run_manifest.v1",
        "GeneratedAtUtc": utc_now(),
        "BaselineId": baseline_id,
        "Gate": "required_before_paper_grade_accuracy_claim",
        "NativeFluidX3DPathExplicitlyProvided": True,
        "NativeFluidX3DSourcePath": str(source_root),
        "FluidX3DSolverWorkingDirectory": str(solver_cwd),
        "NativeFluidX3DSourceValidation": source_validation,
        "CaseDir": str(case_dir),
        "CaseMetadataPath": str(metadata_path.resolve()),
        "CaseMetadataSha256": sha256_or_empty(metadata_path),
        "ValidationProtocolAuditPath": str(validation_protocol_path),
        "ValidationProtocolAuditSha256": sha256_or_empty(validation_protocol_path),
        "InletSourceAuditPath": str(inlet_source_audit_path) if inlet_source_audit_path is not None else "",
        "InletSourceAuditSha256": sha256_or_empty(inlet_source_audit_path),
        "InletSourceAuditGate": inlet_source_audit,
        "AutoInletSourceAudit": auto_inlet_source_audit,
        "BoundarySourceAuditPath": str(boundary_source_audit_path) if boundary_source_audit_path is not None else "",
        "BoundarySourceAuditSha256": sha256_or_empty(boundary_source_audit_path),
        "BoundarySourceAuditGate": boundary_source_audit,
        "AutoBoundarySourceAudit": auto_boundary_source_audit,
        "CoordinateProbeProtocolAuditPath": str(coordinate_probe_protocol_audit_path) if coordinate_probe_protocol_audit_path is not None else "",
        "CoordinateProbeProtocolAuditSha256": sha256_or_empty(coordinate_probe_protocol_audit_path),
        "CoordinateProbeProtocolAuditGate": coordinate_probe_protocol_audit,
        "AutoCoordinateProbeProtocolAudit": auto_coordinate_probe_protocol_audit,
        "InletCorrelationAuditPath": str(inlet_correlation_audit_path) if inlet_correlation_audit_path is not None else "",
        "InletCorrelationAuditSha256": sha256_or_empty(inlet_correlation_audit_path),
        "InletCorrelationAuditGate": inlet_correlation_audit,
        "CaseMetadataAijCase": case_label,
        "CaseMetadataWindDirection": wind_label,
        "ValidationProtocolAijCase": identity["ProtocolAijCase"],
        "ValidationProtocolWindDirection": identity["ProtocolWindDirection"],
        "EffectiveAijCase": effective_case_label,
        "EffectiveAijCaseSource": identity["CaseSource"],
        "EffectiveWindDirection": effective_wind_label,
        "EffectiveWindDirectionSource": identity["WindDirectionSource"],
        "ExpectedAijCase": expected_case,
        "ExpectedWindDirection": expected_wind,
        "PreInstallNativeSourceFiles": pre_install_native_source_files,
        "EffectiveRunSourceFiles": effective_run_source_files,
        "PreInstallCaseToSourceParityGate": pre_install_case_source_parity,
        "PostInstallCaseToSourceParityGate": post_install_case_source_parity,
        "CaseToRunSourceParityGate": case_to_run_source_parity,
        "RequiredSourceFiles": required_files,
        "ValidationProtocolAuditGate": validation_protocol,
        "CaseMetadataPreconditionGate": metadata_preconditions,
        "CaseSetupSourcePreconditionGate": setup_source_preconditions,
        "OfficialInputPreconditionGate": official_input_preconditions,
        "PreExecutionGate": pre_execution_gate,
        "DiagnosticExecutionOverrideAllowed": args.allow_diagnostic_execution,
        "Install": install_record,
        "ReconstructionMacroAdaptation": reconstruction_adaptation,
        "WindowsSdkProjectPatch": windows_sdk_patch_record,
        "BatchVtkGraphicsOverride": graphics_batch_record,
        "RuntimeWorkingDirectoryInputs": runtime_workdir_inputs,
        "Build": build_record,
        "Run": run_record,
        "SharedRunConditions": {
            "TimeSteps": args.time_steps,
            "SaveInterval": args.vtk_save_interval,
            "SaveStartStep": vtk_save_start_step,
            "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
            "ComputedVtkFrameCount": vtk_schedule["ComputedFrameCount"],
            "AverageLastN": args.average_last_n,
            "RecommendedAverageLastNForStepSpan": vtk_schedule["RecommendedAverageLastNForStepSpan"],
            "RecommendedMinimumTimeStepsForCurrentSaveInterval": vtk_schedule["RecommendedMinimumTimeStepsForCurrentSaveInterval"],
            "ExpectedFinalWindowStepSpan": vtk_schedule["FinalWindowStepSpan"],
            "MinimumValidationAverageFrames": args.min_vtk_frames,
            "MinimumValidationAverageStepSpan": args.min_vtk_step_span,
            "MinimumSyntheticInletRefreshes": args.min_stg_refreshes,
            "MinimumFlowThroughCount": args.min_flow_throughs,
            "RecommendedMinimumTimeStepsForFlowThrough": flow_through_time.get("RecommendedMinimumTimeStepsForFlowThrough"),
            "EstimatedOneFlowThroughSteps": flow_through_time.get("EstimatedOneFlowThroughSteps"),
            "PlannedFlowThroughCount": flow_through_time.get("PlannedFlowThroughCount"),
            "VtkPattern": args.vtk_pattern,
        },
        "PlannedVtkScheduleGate": vtk_schedule,
        "FlowThroughTimeGate": flow_through_time,
        "OutputDiskSpaceGate": output_disk_space,
        "OutputDefinesPath": str(defines_for_output) if defines_for_output is not None else "",
        "ActualVtkOutputGate": actual_vtk_output,
        "RuntimeInletDiagnosticsResolution": runtime_inlet_diagnostics_resolution,
        "RuntimeInletDiagnosticsGate": runtime_inlet_diagnostics,
        "NativeAccuracyEvidenceGate": native_accuracy_gate,
        "PaperUseGate": paper_gate,
        "PlannedSyntheticInletSamplingGate": synthetic_sampling,
        "OutputDir": str(output_dir),
        "VtkPattern": args.vtk_pattern,
        "VtkFiles": vtk_records,
        "VtkFileCount": len(vtk_records),
        "RunnerGate": runner_gate(reasons),
    }
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"wrote {out_path}")
    gate = manifest["RunnerGate"]["Gate"]
    if gate != "pass":
        print(f"runner gate: {gate} ({manifest['RunnerGate']['ReasonsCsv']})")
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
