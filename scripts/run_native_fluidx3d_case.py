#!/usr/bin/env python3
"""Prepare and optionally run a strict native FluidX3D validation case.

This runner is intentionally conservative. By default it only validates the
FluidX3D source root and CityLBM-generated case package, then writes a manifest.
Use --install, --build, and --run explicitly on the experiment workstation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
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
    parser.add_argument("--out", required=True, help="Output native_fluidx3d_baseline_manifest.json path.")
    parser.add_argument(
        "--validation-protocol-audit",
        default="",
        help=(
            "Optional validation_protocol_audit.json path. "
            "Defaults to case_dir/validation_protocol_audit.json."
        ),
    )
    parser.add_argument("--baseline-id", default="", help="Stable ID for this native baseline.")
    parser.add_argument("--install", action="store_true", help="Replace FluidX3D src/setup.cpp and src/defines.hpp from case.")
    parser.add_argument("--build", action="store_true", help="Build the native FluidX3D source tree after install/preflight.")
    parser.add_argument("--run", action="store_true", help="Run FluidX3D.exe after build/preflight.")
    parser.add_argument("--msbuild", default="", help="Optional MSBuild executable path.")
    parser.add_argument("--configuration", default="Release", help="MSBuild configuration.")
    parser.add_argument("--platform", default="x64", help="MSBuild platform.")
    parser.add_argument("--exe", default="", help="Optional FluidX3D executable path.")
    parser.add_argument("--timeout-seconds", type=int, default=0, help="Optional solver timeout, 0 disables timeout.")
    parser.add_argument("--expected-aij-case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--expected-wind-direction", default="", help="Expected wind direction label, e.g. N.")
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
        "--allow-diagnostic-execution",
        action="store_true",
        help="Allow install/build/run even when strict preflight gates are diagnostic_only. Use only for debugging, never for paper-grade claims.",
    )
    parser.add_argument("--output-dir", default="", help="Directory to inspect for u-*.vtk after run.")
    parser.add_argument("--vtk-pattern", default="u-*.vtk", help="VTK glob pattern.")
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


def metadata_value(metadata: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in metadata:
            return metadata.get(key)
    return None


def metadata_bool(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[bool]:
    return as_bool(metadata_value(metadata, keys))


def metadata_int(metadata: Dict[str, Any], keys: Sequence[str]) -> Optional[int]:
    return as_int(metadata_value(metadata, keys))


def metadata_vtk_save_start_step(metadata: Dict[str, Any]) -> Optional[int]:
    direct = metadata_int(metadata, ["VtkSaveStartStep", "vtk_save_start_step", "SaveStartStep"])
    if direct is not None:
        return direct
    vtk_output = metadata.get("VtkOutput") or metadata.get("vtk_output")
    if isinstance(vtk_output, dict):
        return as_int(metadata_value(vtk_output, ["SaveStartStep", "save_start_step", "VtkSaveStartStep"]))
    return None


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


def audit_validation_protocol(path: Path) -> Dict[str, Any]:
    audit = json_load(path)
    items = protocol_items(audit)
    by_key = {protocol_item_key(item): protocol_item_status(item) for item in items if protocol_item_key(item)}
    audit_gate = str(audit.get("Gate") or audit.get("gate") or "").strip().lower()
    missing_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key not in by_key]
    empty_status_keys = [key for key in REQUIRED_PROTOCOL_ITEM_KEYS if key in by_key and not by_key[key]]
    fail_keys = [key for key, status in by_key.items() if status == "fail"]
    risk_keys = [key for key, status in by_key.items() if status == "risk"]
    partial_keys = [key for key, status in by_key.items() if status == "partial"]
    reasons = []
    if not audit or not items:
        reasons.append("validation_protocol_audit_missing_or_empty")
    reasons.extend(f"validation_protocol_item_missing:{key}" for key in missing_keys)
    reasons.extend(f"validation_protocol_item_status_missing:{key}" for key in empty_status_keys)
    reasons.extend(f"validation_protocol_item_fail:{key}" for key in fail_keys)
    reasons.extend(f"validation_protocol_item_risk:{key}" for key in risk_keys)
    reasons.extend(f"validation_protocol_item_partial:{key}" for key in partial_keys)
    if not audit_gate:
        reasons.append("validation_protocol_audit_gate_missing")
    elif audit_gate not in PAPER_GRADE_PROTOCOL_AUDIT_GATES:
        reasons.append(f"validation_protocol_audit_gate_not_paper_grade:{audit_gate}")
    return {
        "Path": str(path.resolve()),
        "Exists": path.is_file(),
        "Sha256": sha256_or_empty(path),
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": reasons,
        "ReasonsCsv": ";".join(reasons),
        "AuditGate": audit_gate,
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


def collect_required_files(source_root: Path, case_dir: Path, validation_protocol_path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for role, rel in REQUIRED_SOURCE_FILES:
        records.append(path_record(role, source_root / rel))
    for role, candidates in REQUIRED_CASE_FILE_CANDIDATES:
        records.append(case_file_record(role, case_dir, candidates))
    for role, rel in REQUIRED_CASE_FILES:
        path = validation_protocol_path if role == "Validation protocol audit" else case_dir / rel
        records.append(path_record(role, path))
    for role, rel in OPTIONAL_CASE_FILES:
        record = optional_path_record(role, case_dir / rel)
        if record is not None:
            records.append(record)
    return records


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


def find_msbuild(explicit: str) -> str:
    if explicit:
        return explicit
    found = shutil.which("msbuild")
    return found or ""


def build_command(source_root: Path, msbuild: str, configuration: str, platform: str) -> List[str]:
    solutions = sorted(source_root.glob("*.sln"))
    if msbuild and solutions:
        return [msbuild, str(solutions[0]), f"/p:Configuration={configuration}", f"/p:Platform={platform}"]
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


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    source_root = Path(args.fluidx3d_source).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_path = case_dir / "case_metadata.json"
    validation_protocol_path = (
        Path(args.validation_protocol_audit).expanduser().resolve()
        if args.validation_protocol_audit.strip()
        else case_dir / "validation_protocol_audit.json"
    )
    metadata = json_load(metadata_path)
    case_label, wind_label = case_identity(metadata)
    validation_protocol = audit_validation_protocol(validation_protocol_path)
    identity = effective_identity(case_label, wind_label, validation_protocol)
    metadata_preconditions = audit_case_metadata_preconditions(metadata)
    vtk_save_start_step = (
        args.vtk_save_start_step
        if args.vtk_save_start_step is not None
        else metadata_vtk_save_start_step(metadata)
    )
    expected_case = args.expected_aij_case.strip()
    expected_wind = args.expected_wind_direction.strip()
    source_validation = validate_source_root(source_root)

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
        path = validation_protocol_path if role == "Validation protocol audit" else case_dir / rel
        if not path.is_file():
            reasons.append(f"case_required_file_missing:{role}")
    if validation_protocol["Gate"] != "pass":
        reasons.extend(str(reason) for reason in validation_protocol["Reasons"])
    if metadata_preconditions["Gate"] != "pass":
        reasons.extend(str(reason) for reason in metadata_preconditions["Reasons"])
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
    synthetic_sampling = audit_planned_synthetic_inlet_sampling(
        metadata,
        vtk_schedule["FinalWindowStepSpan"],
        args.min_stg_refreshes,
    )
    if synthetic_sampling["Gate"] == "diagnostic_only":
        reasons.extend(str(reason) for reason in synthetic_sampling["Reasons"])

    pre_execution_gate = runner_gate(reasons)
    execution_requested = args.install or args.build or args.run
    execution_allowed = pre_execution_gate["Gate"] == "pass" or args.allow_diagnostic_execution
    if execution_requested and not execution_allowed:
        reasons.append("execution_requested_but_preflight_gate_diagnostic_only")

    install_record: Dict[str, Any] = {
        "Requested": args.install,
        "Performed": False,
        "Backups": [],
        "InstalledFiles": [],
        "Gate": "not_requested",
    }
    if args.install:
        if not execution_allowed:
            install_record["Gate"] = "blocked"
        elif source_validation["IsValid"] and case_dir.is_dir():
            install_data = install_case(case_dir, source_root, out_path.parent / "native_source_backups")
            install_record.update(install_data)
            install_record["Performed"] = True
            install_record["Gate"] = "pass"
        else:
            install_record["Gate"] = "fail"
            reasons.append("install_requested_but_preflight_failed")

    msbuild = find_msbuild(args.msbuild)
    command = build_command(source_root, msbuild, args.configuration, args.platform)
    build_record: Dict[str, Any] = {
        "Requested": args.build,
        "MSBuild": msbuild,
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
        elif exe_path is None or not exe_path.exists():
            run_record["Gate"] = "fail"
            reasons.append("run_requested_but_executable_missing")
        else:
            run_record.update(run_process([str(exe_path)], source_root, args.timeout_seconds))
            if run_record["Gate"] != "pass":
                reasons.append("run_failed")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else case_dir
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
    native_accuracy_gate = native_accuracy_evidence_gate(run_record, actual_vtk_output)

    source_validation = validate_source_root(source_root)
    required_files = collect_required_files(source_root, case_dir, validation_protocol_path)
    baseline_id = args.baseline_id.strip() or f"native-fluidx3d-{case_label or 'case'}-{wind_label or 'wind'}-{utc_now()}"
    manifest = {
        "Schema": "citylbm.native_fluidx3d_run_manifest.v1",
        "GeneratedAtUtc": utc_now(),
        "BaselineId": baseline_id,
        "Gate": "required_before_paper_grade_accuracy_claim",
        "NativeFluidX3DPathExplicitlyProvided": True,
        "NativeFluidX3DSourcePath": str(source_root),
        "NativeFluidX3DSourceValidation": source_validation,
        "CaseDir": str(case_dir),
        "CaseMetadataPath": str(metadata_path.resolve()),
        "CaseMetadataSha256": sha256_or_empty(metadata_path),
        "ValidationProtocolAuditPath": str(validation_protocol_path),
        "ValidationProtocolAuditSha256": sha256_or_empty(validation_protocol_path),
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
        "RequiredSourceFiles": required_files,
        "ValidationProtocolAuditGate": validation_protocol,
        "CaseMetadataPreconditionGate": metadata_preconditions,
        "PreExecutionGate": pre_execution_gate,
        "DiagnosticExecutionOverrideAllowed": args.allow_diagnostic_execution,
        "Install": install_record,
        "Build": build_record,
        "Run": run_record,
        "SharedRunConditions": {
            "TimeSteps": args.time_steps,
            "SaveInterval": args.vtk_save_interval,
            "SaveStartStep": vtk_save_start_step,
            "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
            "ComputedVtkFrameCount": vtk_schedule["ComputedFrameCount"],
            "AverageLastN": args.average_last_n,
            "ExpectedFinalWindowStepSpan": vtk_schedule["FinalWindowStepSpan"],
            "MinimumValidationAverageFrames": args.min_vtk_frames,
            "MinimumValidationAverageStepSpan": args.min_vtk_step_span,
            "MinimumSyntheticInletRefreshes": args.min_stg_refreshes,
            "VtkPattern": args.vtk_pattern,
        },
        "PlannedVtkScheduleGate": vtk_schedule,
        "ActualVtkOutputGate": actual_vtk_output,
        "NativeAccuracyEvidenceGate": native_accuracy_gate,
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
