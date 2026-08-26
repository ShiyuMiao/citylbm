#!/usr/bin/env python3
"""Build a traceable inlet Reynolds-stress evidence file.

This helper does not run CFD. It separates paper-grade full tensor or
precursor evidence from the common diagnostic fallback where only AF k(z) is
available and the tensor is assumed isotropic.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


STRESS_COMPONENTS = ["r11", "r22", "r33", "r12", "r13", "r23"]
PAPER_GRADE_STRESS_QUALITIES = {
    "paper_grade",
    "measured_full_tensor",
    "precursor_validated",
    "ready_for_validation_run",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create inlet_reynolds_stress_evidence.json.")
    parser.add_argument("--af-csv", default="", help="AF CSV with z,U,k and optional u_rms/v_rms/w_rms columns.")
    parser.add_argument("--stress-csv", default="", help="Measured or precursor-derived z,R11,R22,R33,R12,R13,R23 CSV.")
    parser.add_argument("--precursor-evidence", default="", help="Optional equivalent_precursor_evidence.json.")
    parser.add_argument("--metadata", default="", help="Optional case_metadata.json for traceability.")
    parser.add_argument("--case", default="", help="Expected AIJ case label, e.g. CaseA.")
    parser.add_argument("--wind-direction-label", default="", help="Expected wind direction label, e.g. N.")
    parser.add_argument(
        "--source-type",
        choices=["auto", "isotropic_from_k", "measured_diagonal_rms", "measured_tensor", "precursor"],
        default="auto",
        help="Evidence interpretation. auto prefers precursor, full tensor, diagonal RMS, then isotropic_from_k.",
    )
    parser.add_argument(
        "--require-run-binding",
        action="store_true",
        help=(
            "Require paper-grade tensor/precursor evidence to be explicitly bound "
            "to the current metadata hash, case label, wind label and source hash."
        ),
    )
    parser.add_argument("--out", required=True, help="Output inlet_reynolds_stress_evidence.json.")
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
    if path is None or not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def get_nested(data: Dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_metadata_value(metadata: Dict[str, Any], candidates: Sequence[Sequence[str]]) -> Any:
    for path in candidates:
        value = get_nested(metadata, *path)
        if value not in (None, ""):
            return value
    return None


def metadata_stress_evidence_quality(metadata: Dict[str, Any]) -> str:
    value = first_metadata_value(
        metadata,
        [
            ("InletReynoldsStress", "EvidenceQuality"),
            ("InletReynoldsStress", "Quality"),
            ("InletReynoldsStressEvidenceQuality",),
            ("ReynoldsStressEvidenceQuality",),
        ],
    )
    return str(value or "").strip()


def resolve_optional_path(raw: Any, metadata_path: Optional[Path]) -> Optional[Path]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute() and metadata_path is not None:
        path = metadata_path.parent / path
    return path.resolve()


def discovered_path(
    explicit: str,
    metadata: Dict[str, Any],
    metadata_path: Optional[Path],
    candidates: Sequence[Sequence[str]],
) -> Dict[str, Any]:
    explicit_text = explicit.strip()
    if explicit_text:
        source = "argument"
        raw: Any = explicit_text
        path = Path(explicit_text).expanduser().resolve()
    else:
        source = "metadata"
        raw = first_metadata_value(metadata, candidates)
        path = resolve_optional_path(raw, metadata_path)
    return {
        "source": source if raw not in (None, "") else "missing",
        "raw": str(raw) if raw not in (None, "") else "",
        "path": str(path) if path else "",
        "exists": bool(path and path.exists()),
    }


def as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def normalize_name(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def identity_token(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip().lower() if ch.isalnum())


def pick_column(fieldnames: Sequence[str], candidates: Iterable[str]) -> str:
    lookup = {normalize_name(name): name for name in fieldnames}
    for candidate in candidates:
        match = lookup.get(normalize_name(candidate))
        if match:
            return match
    return ""


def load_csv_rows(path: Optional[Path]) -> List[Dict[str, str]]:
    if path is None or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def summarize_values(values: Sequence[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def reynolds_stress_tensor_reasons(values: Dict[str, float]) -> List[str]:
    r11 = values["r11"]
    r22 = values["r22"]
    r33 = values["r33"]
    r12 = values["r12"]
    r13 = values["r13"]
    r23 = values["r23"]
    scale = max(abs(value) for value in values.values()) or 1.0
    minor_tolerance = 1.0e-10 * max(scale * scale, 1.0)
    determinant_tolerance = 1.0e-10 * max(scale * scale * scale, 1.0)
    reasons: List[str] = []
    if r11 < -minor_tolerance:
        reasons.append("stress_tensor_negative_r11")
    if r22 < -minor_tolerance:
        reasons.append("stress_tensor_negative_r22")
    if r33 < -minor_tolerance:
        reasons.append("stress_tensor_negative_r33")
    minor_12 = r11 * r22 - r12 * r12
    minor_13 = r11 * r33 - r13 * r13
    minor_23 = r22 * r33 - r23 * r23
    determinant = (
        r11 * r22 * r33
        + 2.0 * r12 * r13 * r23
        - r11 * r23 * r23
        - r22 * r13 * r13
        - r33 * r12 * r12
    )
    if minor_12 < -minor_tolerance:
        reasons.append("stress_tensor_r11_r22_minor_not_positive_semidefinite")
    if minor_13 < -minor_tolerance:
        reasons.append("stress_tensor_r11_r33_minor_not_positive_semidefinite")
    if minor_23 < -minor_tolerance:
        reasons.append("stress_tensor_r22_r33_minor_not_positive_semidefinite")
    if determinant < -determinant_tolerance:
        reasons.append("stress_tensor_determinant_not_positive_semidefinite")
    return reasons


def analyze_stress_csv(path: Optional[Path]) -> Dict[str, Any]:
    rows = load_csv_rows(path)
    if not rows:
        return {"present": False, "row_count": 0, "valid_row_count": 0, "reasons": ["stress_csv_missing_or_empty"]}
    fieldnames = list(rows[0].keys())
    z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
    component_cols = {
        name: pick_column(fieldnames, [name, name.upper(), f"profile_{name}", f"{name}_profile"])
        for name in STRESS_COMPONENTS
    }
    missing = [name for name, col in component_cols.items() if not col]
    valid = 0
    numeric_valid = 0
    invalid_tensor_count = 0
    invalid_tensor_reasons: List[str] = []
    component_values: Dict[str, List[float]] = {name: [] for name in STRESS_COMPONENTS}
    for row in rows:
        z = as_float(row.get(z_col)) if z_col else None
        values = {name: as_float(row.get(col)) for name, col in component_cols.items() if col}
        if z is None or len(values) != len(STRESS_COMPONENTS) or any(value is None for value in values.values()):
            continue
        numeric_values = {name: float(value) for name, value in values.items() if value is not None}
        numeric_valid += 1
        tensor_reasons = reynolds_stress_tensor_reasons(numeric_values)
        if tensor_reasons:
            invalid_tensor_count += 1
            invalid_tensor_reasons.extend(tensor_reasons)
            continue
        valid += 1
        for name, value in numeric_values.items():
            component_values[name].append(value)
    reasons: List[str] = []
    if not z_col:
        reasons.append("stress_csv_z_column_missing")
    for name in missing:
        reasons.append(f"stress_csv_component_missing:{name}")
    if valid <= 0:
        reasons.append("stress_csv_no_valid_full_tensor_rows")
    if invalid_tensor_count:
        reasons.append(f"stress_csv_invalid_positive_semidefinite_tensor_rows:{invalid_tensor_count}")
        reasons.extend(sorted(set(invalid_tensor_reasons)))
    return {
        "present": True,
        "path": str(path) if path else "",
        "sha256": sha256(path) if path and path.is_file() else "",
        "row_count": len(rows),
        "numeric_full_tensor_row_count": numeric_valid,
        "valid_row_count": valid,
        "invalid_positive_semidefinite_tensor_row_count": invalid_tensor_count,
        "z_column": z_col,
        "component_columns": component_cols,
        "component_summary": {name: summarize_values(values) for name, values in component_values.items()},
        "reasons": reasons,
    }


def analyze_isotropic_from_af(path: Optional[Path]) -> Dict[str, Any]:
    rows = load_csv_rows(path)
    if not rows:
        return {"present": False, "row_count": 0, "valid_row_count": 0, "reasons": ["af_csv_missing_or_empty"]}
    fieldnames = list(rows[0].keys())
    z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
    k_col = pick_column(fieldnames, ["k", "k_m2_s2", "k(m2/s2)", "tke", "turbulent_kinetic_energy"])
    valid = 0
    k_values: List[float] = []
    r_diag_values: List[float] = []
    sample: List[Dict[str, float]] = []
    for row in rows:
        z = as_float(row.get(z_col)) if z_col else None
        k = as_float(row.get(k_col)) if k_col else None
        if z is None or k is None or k < 0.0:
            continue
        r_diag = 2.0 * k / 3.0
        valid += 1
        k_values.append(k)
        r_diag_values.append(r_diag)
        if len(sample) < 5:
            sample.append({"z_m": z, "k_m2_s2": k, "r11_r22_r33_m2_s2": r_diag, "r12_r13_r23_m2_s2": 0.0})
    reasons: List[str] = []
    if not z_col:
        reasons.append("af_csv_z_column_missing")
    if not k_col:
        reasons.append("af_csv_k_column_missing")
    if valid <= 0:
        reasons.append("af_csv_no_valid_k_rows")
    return {
        "present": True,
        "path": str(path) if path else "",
        "sha256": sha256(path) if path and path.is_file() else "",
        "row_count": len(rows),
        "valid_row_count": valid,
        "z_column": z_col,
        "k_column": k_col,
        "k_summary": summarize_values(k_values),
        "isotropic_r11_r22_r33_summary": summarize_values(r_diag_values),
        "sample": sample,
        "reasons": reasons,
    }


def analyze_diagonal_rms_from_af(path: Optional[Path]) -> Dict[str, Any]:
    rows = load_csv_rows(path)
    if not rows:
        return {"present": False, "row_count": 0, "valid_row_count": 0, "reasons": ["af_csv_missing_or_empty"]}
    fieldnames = list(rows[0].keys())
    z_col = pick_column(fieldnames, ["z", "z_m", "z(m)", "height", "height_m"])
    rms_cols = {
        "u_rms": pick_column(fieldnames, ["u_rms", "u_rms(m/s)", "urms", "uprime_rms", "u_prime_rms"]),
        "v_rms": pick_column(fieldnames, ["v_rms", "v_rms(m/s)", "vrms", "vprime_rms", "v_prime_rms"]),
        "w_rms": pick_column(fieldnames, ["w_rms", "w_rms(m/s)", "wrms", "wprime_rms", "w_prime_rms"]),
    }
    missing = [name for name, col in rms_cols.items() if not col]
    valid = 0
    component_values: Dict[str, List[float]] = {"r11": [], "r22": [], "r33": []}
    sample: List[Dict[str, float]] = []
    for row in rows:
        z = as_float(row.get(z_col)) if z_col else None
        u_rms = as_float(row.get(rms_cols["u_rms"])) if rms_cols["u_rms"] else None
        v_rms = as_float(row.get(rms_cols["v_rms"])) if rms_cols["v_rms"] else None
        w_rms = as_float(row.get(rms_cols["w_rms"])) if rms_cols["w_rms"] else None
        if z is None or u_rms is None or v_rms is None or w_rms is None:
            continue
        if u_rms < 0.0 or v_rms < 0.0 or w_rms < 0.0:
            continue
        r11 = u_rms * u_rms
        r22 = v_rms * v_rms
        r33 = w_rms * w_rms
        valid += 1
        component_values["r11"].append(r11)
        component_values["r22"].append(r22)
        component_values["r33"].append(r33)
        if len(sample) < 5:
            sample.append(
                {
                    "z_m": z,
                    "u_rms_mps": u_rms,
                    "v_rms_mps": v_rms,
                    "w_rms_mps": w_rms,
                    "r11_m2_s2": r11,
                    "r22_m2_s2": r22,
                    "r33_m2_s2": r33,
                    "r12_r13_r23_m2_s2": 0.0,
                }
            )
    reasons: List[str] = []
    if not z_col:
        reasons.append("af_csv_z_column_missing")
    for name in missing:
        reasons.append(f"af_csv_rms_component_missing:{name}")
    if valid <= 0:
        reasons.append("af_csv_no_valid_diagonal_rms_rows")
    return {
        "present": True,
        "path": str(path) if path else "",
        "sha256": sha256(path) if path and path.is_file() else "",
        "row_count": len(rows),
        "valid_row_count": valid,
        "z_column": z_col,
        "rms_columns": rms_cols,
        "diagonal_component_summary": {
            name: summarize_values(values) for name, values in component_values.items()
        },
        "sample": sample,
        "reasons": reasons,
    }


def metadata_stress_csv_sha256(metadata: Dict[str, Any]) -> str:
    value = first_metadata_value(
        metadata,
        [
            ("InletReynoldsStress", "TensorCsvSha256"),
            ("InletReynoldsStress", "StressCsvSha256"),
            ("InletReynoldsStress", "CsvSha256"),
            ("InletReynoldsStress", "MeasuredTensorCsvSha256"),
            ("InletReynoldsStressTensorCsvSha256",),
            ("MeasuredReynoldsStressCsvSha256",),
            ("ReynoldsStressTensorCsvSha256",),
        ],
    )
    return str(value or "").strip()


def stress_csv_binding_reasons(
    metadata: Dict[str, Any],
    stress: Dict[str, Any],
    metadata_path: Optional[Path],
) -> List[str]:
    if metadata_path is None:
        return ["case_metadata_missing_for_stress_csv_binding"]
    expected_hash = metadata_stress_csv_sha256(metadata)
    actual_hash = str(stress.get("sha256") or "").strip()
    if not expected_hash:
        return ["stress_csv_sha256_missing_in_metadata"]
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        return ["stress_csv_sha256_in_metadata_invalid"]
    if not actual_hash:
        return ["stress_csv_sha256_missing"]
    if expected_hash.lower() != actual_hash.lower():
        return ["stress_csv_sha256_mismatch_current_metadata"]
    return []


def precursor_gate(
    data: Dict[str, Any],
    *,
    metadata_sha: str = "",
    expected_case: str = "",
    expected_wind_direction: str = "",
    require_run_binding: bool = False,
) -> Dict[str, Any]:
    if not data:
        return {"present": False, "gate": "not_applicable", "reasons": ["precursor_evidence_missing"]}
    admissible = str(
        data.get("PaperAdmissible")
        or data.get("paper_admissible")
        or data.get("Gate")
        or data.get("gate")
        or ""
    ).strip().lower()
    hash_value = str(
        data.get("Sha256") or data.get("sha256") or data.get("SourceVtkSha256") or data.get("source_vtk_sha256") or ""
    ).strip()
    has_hash = bool(re.fullmatch(r"[0-9a-fA-F]{64}", hash_value))
    method = str(data.get("source_turbulence_method") or data.get("SourceTurbulenceMethod") or "").strip()
    boundary_mode = str(data.get("source_boundary_mode") or data.get("SourceBoundaryMode") or "").strip()
    evidence_metadata_sha = str(
        data.get("case_metadata_sha256")
        or data.get("CaseMetadataSha256")
        or data.get("metadata_sha256")
        or data.get("MetadataSha256")
        or ""
    ).strip()
    evidence_case = str(data.get("aij_case") or data.get("AijCase") or data.get("case") or data.get("Case") or "").strip()
    evidence_wind = str(
        data.get("wind_direction")
        or data.get("WindDirection")
        or data.get("wind_direction_label")
        or data.get("WindDirectionLabel")
        or ""
    ).strip()
    reasons: List[str] = []
    if admissible not in {"true", "pass", "paper_grade", "ready_for_validation_run"}:
        reasons.append(f"precursor_not_paper_admissible:{admissible or 'missing'}")
    if not has_hash:
        reasons.append("precursor_sha256_evidence_missing_or_invalid")
    if not method or method.lower().startswith("todo"):
        reasons.append("precursor_turbulence_method_missing")
    if not boundary_mode or boundary_mode.lower().startswith("todo"):
        reasons.append("precursor_boundary_mode_missing")
    if require_run_binding:
        if not metadata_sha:
            reasons.append("case_metadata_missing_for_precursor_binding")
        elif not evidence_metadata_sha:
            reasons.append("precursor_case_metadata_sha256_missing")
        elif not re.fullmatch(r"[0-9a-fA-F]{64}", evidence_metadata_sha):
            reasons.append("precursor_case_metadata_sha256_invalid")
        elif evidence_metadata_sha.lower() != metadata_sha.lower():
            reasons.append("precursor_case_metadata_sha256_mismatch")
        if expected_case and identity_token(evidence_case) != identity_token(expected_case):
            reasons.append("precursor_aij_case_mismatch")
        if expected_wind_direction and identity_token(evidence_wind) != identity_token(expected_wind_direction):
            reasons.append("precursor_wind_direction_mismatch")
    return {
        "present": True,
        "gate": "pass" if not reasons else "fail",
        "reasons": reasons,
        "paper_admissible": admissible,
        "has_hash_evidence": has_hash,
        "source_turbulence_method": method,
        "source_boundary_mode": boundary_mode,
        "case_metadata_sha256": evidence_metadata_sha,
        "case_metadata_sha256_matches_current": bool(metadata_sha and evidence_metadata_sha)
        and evidence_metadata_sha.lower() == metadata_sha.lower(),
        "aij_case": evidence_case,
        "wind_direction": evidence_wind,
    }


def main() -> int:
    args = parse_args()
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata.strip() else None
    out_path = Path(args.out).expanduser().resolve()

    metadata = read_json(metadata_path)
    metadata_sha = sha256(metadata_path) if metadata_path and metadata_path.is_file() else ""
    af_discovery = discovered_path(
        args.af_csv,
        metadata,
        metadata_path,
        [
            ("OfficialAF",),
            ("official_af",),
            ("InputFiles", "OfficialAF"),
            ("InputFiles", "AF"),
        ],
    )
    stress_discovery = discovered_path(
        args.stress_csv,
        metadata,
        metadata_path,
        [
            ("InletReynoldsStress", "TensorCsv"),
            ("InletReynoldsStress", "StressCsv"),
            ("InletReynoldsStress", "Csv"),
            ("InletReynoldsStress", "MeasuredTensorCsv"),
            ("InletReynoldsStressCsv",),
            ("InletReynoldsStressTensorCsv",),
            ("MeasuredReynoldsStressCsv",),
            ("ReynoldsStressTensorCsv",),
        ],
    )
    precursor_discovery = discovered_path(
        args.precursor_evidence,
        metadata,
        metadata_path,
        [
            ("EquivalentPrecursor", "EvidenceJson"),
            ("EquivalentPrecursor", "evidence_json"),
            ("PrecursorEvidenceJson",),
            ("EquivalentPrecursorEvidenceJson",),
        ],
    )
    af_path = Path(af_discovery["path"]) if af_discovery["path"] else None
    stress_path = Path(stress_discovery["path"]) if stress_discovery["path"] else None
    precursor_path = Path(precursor_discovery["path"]) if precursor_discovery["path"] else None
    stress = analyze_stress_csv(stress_path)
    isotropic = analyze_isotropic_from_af(af_path)
    diagonal_rms = analyze_diagonal_rms_from_af(af_path)
    precursor_data = read_json(precursor_path)
    expected_case = args.case.strip() or str(metadata.get("AijCase") or metadata.get("Case") or "")
    expected_wind_direction = args.wind_direction_label.strip() or str(metadata.get("WindDirection") or "")
    precursor = precursor_gate(
        precursor_data,
        metadata_sha=metadata_sha,
        expected_case=expected_case,
        expected_wind_direction=expected_wind_direction,
        require_run_binding=args.require_run_binding,
    )

    source_type = args.source_type
    if source_type == "auto":
        stress_ready = stress.get("valid_row_count", 0) >= 2 and not stress.get("reasons")
        diagonal_ready = diagonal_rms.get("valid_row_count", 0) >= 2 and not diagonal_rms.get("reasons")
        isotropic_ready = isotropic.get("valid_row_count", 0) > 0 and not isotropic.get("reasons")
        if precursor.get("gate") == "pass":
            source_type = "precursor"
        elif stress_ready:
            source_type = "measured_tensor"
        elif diagonal_ready:
            source_type = "measured_diagonal_rms"
        elif isotropic_ready:
            source_type = "isotropic_from_k"
        elif stress_discovery.get("exists"):
            source_type = "measured_tensor"
        elif precursor_discovery.get("exists"):
            source_type = "precursor"
        else:
            source_type = "isotropic_from_k"

    reasons: List[str] = []
    paper_grade = False
    if source_type == "precursor":
        reasons.extend(str(reason) for reason in precursor.get("reasons", []))
        paper_grade = precursor.get("gate") == "pass"
    elif source_type == "measured_tensor":
        reasons.extend(str(reason) for reason in stress.get("reasons", []))
        if stress.get("valid_row_count", 0) < 2:
            reasons.append("measured_stress_tensor_requires_at_least_two_valid_heights")
        if args.require_run_binding:
            reasons.extend(stress_csv_binding_reasons(metadata, stress, metadata_path))
            stress_quality = metadata_stress_evidence_quality(metadata).lower()
            if stress_quality not in PAPER_GRADE_STRESS_QUALITIES:
                reasons.append(f"stress_csv_evidence_quality_not_paper_grade:{stress_quality or 'missing'}")
        paper_grade = not reasons
    elif source_type == "measured_diagonal_rms":
        reasons.extend(str(reason) for reason in diagonal_rms.get("reasons", []))
        if diagonal_rms.get("valid_row_count", 0) < 2:
            reasons.append("measured_diagonal_rms_requires_at_least_two_valid_heights")
        if diagonal_rms.get("valid_row_count", 0) > 0:
            reasons.append("measured_diagonal_rms_missing_off_diagonal_covariances_not_paper_grade_full_tensor")
        paper_grade = False
    else:
        reasons.extend(str(reason) for reason in isotropic.get("reasons", []))
        if isotropic.get("valid_row_count", 0) > 0:
            reasons.append("isotropic_k_assumption_only_not_paper_grade_reynolds_stress")
        paper_grade = False

    diagnostic_source_has_rows = (
        source_type == "isotropic_from_k" and isotropic.get("valid_row_count", 0) > 0
    ) or (
        source_type == "measured_diagonal_rms" and diagonal_rms.get("valid_row_count", 0) > 0
    )
    gate = "pass" if paper_grade else "diagnostic_only" if diagnostic_source_has_rows else "fail"
    report: Dict[str, Any] = {
        "schema": "citylbm.inlet_reynolds_stress_evidence.v1",
        "generated_at_utc": utc_now(),
        "gate": gate,
        "paper_grade_gate": "pass" if paper_grade else "fail",
        "source_type": source_type,
        "case": expected_case,
        "wind_direction": expected_wind_direction,
        "metadata": str(metadata_path) if metadata_path else "",
        "metadata_sha256": metadata_sha,
        "run_binding_required": args.require_run_binding,
        "stress_csv_metadata_sha256": metadata_stress_csv_sha256(metadata),
        "stress_csv_metadata_evidence_quality": metadata_stress_evidence_quality(metadata),
        "discovery": {
            "af_csv": af_discovery,
            "stress_csv": stress_discovery,
            "precursor_evidence": precursor_discovery,
        },
        "af_csv": isotropic,
        "af_diagonal_rms": diagonal_rms,
        "stress_csv": stress,
        "precursor_evidence": {
            **precursor,
            "path": str(precursor_path) if precursor_path else "",
            "sha256": sha256(precursor_path) if precursor_path and precursor_path.is_file() else "",
        },
        "tensor_components": STRESS_COMPONENTS,
        "reasons": reasons or ["paper_grade_reynolds_stress_evidence_present"],
        "recommended_next_action": (
            "Use measured/precursor full Reynolds-stress evidence for paper-grade validation. "
            "AF u_rms/v_rms/w_rms gives traceable diagonal stress and is stronger than isotropic k, "
            "but missing off-diagonal covariances or precursor evidence remains diagnostic only."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        "inlet_reynolds_stress_evidence_gate={gate}; paper_grade_gate={paper}; source_type={source}; reasons={reasons}".format(
            gate=report["gate"],
            paper=report["paper_grade_gate"],
            source=source_type,
            reasons=";".join(report["reasons"]),
        )
    )
    return 0 if gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
