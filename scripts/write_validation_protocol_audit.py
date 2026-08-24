#!/usr/bin/env python3
"""Write an explicit validation_protocol_audit.json from case metadata.

This script is a preflight helper. It does not run FluidX3D and must not turn
missing physics evidence into a paper-grade pass.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from audit_native_preconditions import REQUIRED_PROTOCOL_ITEM_KEYS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create validation_protocol_audit.json with explicit pass/risk/fail statuses."
    )
    parser.add_argument("--case-dir", required=True, help="Case directory containing case_metadata.json.")
    parser.add_argument("--metadata", default="", help="Optional explicit case_metadata.json path.")
    parser.add_argument("--out", default="", help="Output JSON path; defaults to case_dir/validation_protocol_audit.json.")
    parser.add_argument("--case", default="", help="Canonical AIJ case label to write, e.g. CaseA.")
    parser.add_argument("--wind-direction-label", default="", help="Canonical wind direction label, e.g. N.")
    parser.add_argument("--wind-vector", default="", help="Wind unit vector, e.g. 1,0,0 or 0,-1,0.")
    parser.add_argument(
        "--inlet-source-audit",
        default="",
        help="Optional inlet_source_audit.json from audit_inlet_source.py.",
    )
    parser.add_argument(
        "--boundary-source-audit",
        default="",
        help="Optional boundary_source_audit.json from audit_boundary_source.py.",
    )
    parser.add_argument(
        "--patch-metadata-identity",
        action="store_true",
        help="Write explicit AijCase/WindDirection/WindDirectionUnitVector fields into case_metadata.json.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


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


def as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_any(source: Dict[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in source:
            return source.get(key)
    return None


def get_nested(source: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


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


def item(key: str, status: str, evidence: str, action: str = "") -> Dict[str, str]:
    return {
        "Key": key,
        "Status": status,
        "Evidence": evidence,
        "RequiredAction": action,
    }


def status_summary(items: Iterable[Dict[str, str]]) -> Tuple[str, List[str], List[str], List[str]]:
    fail = [entry["Key"] for entry in items if entry.get("Status") == "fail"]
    risk = [entry["Key"] for entry in items if entry.get("Status") == "risk"]
    partial = [entry["Key"] for entry in items if entry.get("Status") == "partial"]
    gate = "ready_for_validation_run" if not fail and not risk and not partial else "diagnostic_only"
    return gate, fail, risk, partial


def audit_status(value: Any) -> str:
    return str(value or "").strip().lower()


def summarize_inlet_audit(inlet_audit: Dict[str, Any]) -> Dict[str, Any]:
    method_class = str(inlet_audit.get("inlet_source_method_class") or "").strip()
    fidelity_class = str(inlet_audit.get("inlet_source_turbulent_inflow_fidelity_class") or "").strip()
    paper_gate = audit_status(inlet_audit.get("paper_grade_inlet_source_gate"))
    source_gate = audit_status(inlet_audit.get("inlet_source_gate"))
    distribution_consistent = as_bool(inlet_audit.get("inlet_source_distribution_consistent"))
    velocity_only = as_bool(inlet_audit.get("inlet_source_velocity_field_only"))
    uncorrelated_rms = as_bool(inlet_audit.get("inlet_source_has_uncorrelated_rms_velocity_field_only"))
    paper_methods = {
        "digital_filter_distribution_consistent",
        "synthetic_eddy_distribution_consistent",
        "precursor_or_recycling",
    }
    paper_fidelity = {
        "distribution_consistent_digital_filter",
        "distribution_consistent_synthetic_eddy",
        "distribution_consistent_precursor_or_recycling",
    }
    inlet_is_paper_grade = (
        paper_gate == "pass"
        and source_gate != "fail"
        and distribution_consistent is True
        and velocity_only is not True
        and uncorrelated_rms is not True
        and (method_class in paper_methods or fidelity_class in paper_fidelity)
    )
    inlet_is_velocity_only = (
        velocity_only is True
        or uncorrelated_rms is True
        or distribution_consistent is False
        or paper_gate == "fail"
        or source_gate == "fail"
    )
    evidence = (
        f"InletSourceGate={source_gate or 'missing'}; PaperGradeInletSourceGate={paper_gate or 'missing'}; "
        f"MethodClass={method_class or 'missing'}; FidelityClass={fidelity_class or 'missing'}; "
        f"DistributionConsistent={distribution_consistent}; VelocityFieldOnly={velocity_only}; "
        f"UncorrelatedRmsVelocityFieldOnly={uncorrelated_rms}"
    )
    return {
        "paper_grade": inlet_is_paper_grade,
        "velocity_only_or_failed": inlet_is_velocity_only,
        "evidence": evidence,
    }


def summarize_boundary_audit(boundary_audit: Dict[str, Any]) -> Dict[str, Any]:
    source_gate = audit_status(boundary_audit.get("boundary_source_gate"))
    paper_gate = audit_status(boundary_audit.get("paper_grade_boundary_source_gate"))
    fidelity_class = str(boundary_audit.get("boundary_source_fidelity_class") or "").strip()
    method_class = str(boundary_audit.get("boundary_source_method_class") or "").strip()
    wind_tunnel_equivalent = as_bool(boundary_audit.get("boundary_source_wind_tunnel_equivalent"))
    simplified = as_bool(boundary_audit.get("boundary_source_simplified"))
    rough_wall = as_bool(boundary_audit.get("has_paper_grade_rough_wall_source"))
    development = as_bool(boundary_audit.get("has_paper_grade_development_source"))
    paper_grade = (
        source_gate == "pass"
        and paper_gate == "pass"
        and wind_tunnel_equivalent is True
        and simplified is not True
        and fidelity_class == "wind_tunnel_equivalent_complete"
    )
    evidence = (
        f"BoundarySourceGate={source_gate or 'missing'}; PaperGradeBoundarySourceGate={paper_gate or 'missing'}; "
        f"MethodClass={method_class or 'missing'}; FidelityClass={fidelity_class or 'missing'}; "
        f"WindTunnelEquivalent={wind_tunnel_equivalent}; Simplified={simplified}; "
        f"RoughWallSource={rough_wall}; DevelopmentSource={development}"
    )
    return {
        "paper_grade": paper_grade,
        "rough_wall": rough_wall,
        "development": development,
        "evidence": evidence,
    }


def protocol_items(
    metadata: Dict[str, Any],
    args: argparse.Namespace,
    inlet_audit: Optional[Dict[str, Any]] = None,
    boundary_audit: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    official_af = str(get_any(metadata, ["OfficialAF", "official_af"]) or "").strip()
    official_af_hash = str(get_any(metadata, ["OfficialAFSha256", "official_af_sha256"]) or "").strip()
    official_rs_hash = str(get_any(metadata, ["OfficialRSSha256", "official_rs_sha256"]) or "").strip()
    turbulence_method = str(get_any(metadata, ["TurbulenceMethod", "turbulence_method"]) or "").strip()
    turbulence_scale = as_float(get_any(metadata, ["TurbulenceScale", "turbulence_scale"]))
    inlet_update_interval = as_float(get_any(metadata, ["InletUpdateInterval", "SyntheticTurbulenceUpdateInterval"]))
    reynolds = as_float(get_any(metadata, ["ReH", "EstimatedReynoldsNumber", "estimated_reynolds_number"]))
    target_reynolds = as_float(get_any(metadata, ["TargetReH", "target_reynolds_number"]))
    tau = as_float(get_any(metadata, ["Tau", "tau"]))
    uref = as_float(get_any(metadata, ["Uref", "URef", "u_ref"]))
    zref = as_float(get_any(metadata, ["Zref", "ZRef", "z_ref"]))
    dx = as_float(get_any(metadata, ["Dx", "dx"]))
    probe_count = as_float(get_any(metadata, ["ProbeCount", "probe_count"]))
    wind_label = str(args.wind_direction_label or get_any(metadata, ["WindDirection", "WindDirectionLabel"]) or "").strip()
    wind_vector = parse_vector(args.wind_vector) or parse_vector(str(get_any(metadata, ["WindDirectionUnitVector"]) or ""))

    vtk = get_nested(metadata, "VtkOutput")
    estimated_vtk_frames = as_float(get_any(vtk, ["EstimatedPostSpinupFrameCount", "EstimatedFrameCount"]))
    save_start = as_float(get_any(vtk, ["SaveStartStep", "save_start_step"]))
    save_interval = as_float(get_any(vtk, ["SaveIntervalSteps", "SaveInterval", "save_interval"]))

    boundary = get_nested(metadata, "BoundaryProtocol")
    roughness = get_nested(metadata, "RoughnessLayout")
    precursor = get_nested(metadata, "EquivalentPrecursor")
    boundary_admissible = as_bool(get_any(boundary, ["PaperBoundaryAdmissible", "paper_boundary_admissible"]))
    boundary_documented = as_bool(get_any(boundary, ["BoundarySourceDocumented", "boundary_source_documented"]))
    roughness_admissible = as_bool(get_any(roughness, ["PaperSourceAdmissible", "paper_source_admissible"]))
    precursor_admissible = as_bool(get_any(precursor, ["PaperAdmissible", "paper_admissible"]))
    reconstruct_stress = as_bool(get_any(get_nested(metadata, "ReconstructInletStressDdf"), ["Enabled"]))
    preserve_boundary_fneq = as_bool(get_any(get_nested(metadata, "PreserveBoundaryFneq"), ["Enabled"]))
    reconstruct_boundary_ddf = as_bool(get_any(get_nested(metadata, "ReconstructBoundaryDdf"), ["Enabled"]))
    inlet_summary = summarize_inlet_audit(inlet_audit) if inlet_audit else {}
    boundary_summary = summarize_boundary_audit(boundary_audit) if boundary_audit else {}

    if inlet_audit:
        inlet_k_status = (
            "pass"
            if official_af_hash
            and turbulence_method
            and turbulence_scale is not None
            and as_bool(inlet_audit.get("has_profile_k_lbm")) is True
            else "fail"
        )
        inlet_k_evidence = (
            f"TurbulenceMethod={turbulence_method or 'missing'}; TurbulenceScale={turbulence_scale}; "
            f"OfficialAFSha256={official_af_hash or 'missing'}; "
            f"HasProfileKLbm={as_bool(inlet_audit.get('has_profile_k_lbm'))}; "
            f"HasKDrivenThreeComponentSTG={as_bool(inlet_audit.get('has_k_driven_three_component_stg'))}"
        )
        length_scale_status = "pass" if as_bool(inlet_audit.get("has_inlet_length_scale_evidence")) is True else "risk"
        length_scale_evidence = (
            f"HasInletLengthScaleEvidence={as_bool(inlet_audit.get('has_inlet_length_scale_evidence'))}; "
            f"MetadataLengthScaleGate={inlet_audit.get('metadata_length_scale_gate') or 'missing'}"
        )
        stress_tensor_present = as_bool(inlet_audit.get("has_reynolds_stress_tensor_evidence"))
        measured_or_precursor_tensor = as_bool(
            inlet_audit.get("has_measured_or_precursor_reynolds_stress_tensor_evidence")
        )
        full_tensor_source = as_bool(inlet_audit.get("has_reynolds_stress_full_tensor_source_evidence"))
        isotropic_tensor_source = as_bool(inlet_audit.get("has_isotropic_k_reynolds_stress_source_evidence"))
        documented_isotropic = as_bool(inlet_audit.get("has_documented_isotropic_k_assumption"))
        stress_status = (
            "pass"
            if measured_or_precursor_tensor is True
            else "partial"
            if isotropic_tensor_source is True or full_tensor_source is True or documented_isotropic is True
            else "risk"
        )
        stress_evidence = (
            f"HasReynoldsStressTensorEvidence={stress_tensor_present}; "
            f"HasMeasuredOrPrecursorTensorEvidence={measured_or_precursor_tensor}; "
            f"HasFullTensorSourceEvidence={full_tensor_source}; "
            f"HasIsotropicKTensorSourceEvidence={isotropic_tensor_source}; "
            f"HasDocumentedIsotropicKAssumption={documented_isotropic}; "
            f"ReynoldsStressTreatment={inlet_audit.get('reynolds_stress_treatment') or 'missing'}"
        )
        distribution_status = (
            "pass"
            if inlet_summary.get("paper_grade") is True
            else "fail"
            if inlet_summary.get("velocity_only_or_failed") is True
            else "risk"
        )
        distribution_evidence = str(inlet_summary.get("evidence") or "")
    else:
        inlet_k_status = "pass" if official_af_hash and turbulence_method and turbulence_scale is not None else "fail"
        inlet_k_evidence = (
            f"TurbulenceMethod={turbulence_method or 'missing'}; TurbulenceScale={turbulence_scale}; "
            f"OfficialAFSha256={official_af_hash or 'missing'}"
        )
        length_scale_status = "risk" if turbulence_method else "fail"
        length_scale_evidence = f"TurbulenceMethod={turbulence_method or 'missing'}; length-scale evidence is metadata-only at preflight."
        stress_status = "risk" if turbulence_method else "fail"
        stress_evidence = f"StressDdfReconstruction={reconstruct_stress}; turbulence source={turbulence_method or 'missing'}"
        distribution_status = "risk" if reconstruct_stress or preserve_boundary_fneq or reconstruct_boundary_ddf else "fail"
        distribution_evidence = (
            f"ReconstructInletStressDdf={reconstruct_stress}; PreserveBoundaryFneq={preserve_boundary_fneq}; "
            f"ReconstructBoundaryDdf={reconstruct_boundary_ddf}"
        )

    if boundary_audit:
        boundary_status = "pass" if boundary_summary.get("paper_grade") is True else "fail"
        boundary_evidence = str(boundary_summary.get("evidence") or "")
        roughness_status = (
            "pass"
            if boundary_summary.get("rough_wall") is True and boundary_summary.get("development") is True
            else "fail"
        )
        roughness_evidence = str(boundary_summary.get("evidence") or "")
    else:
        boundary_status = "pass" if boundary_admissible and boundary_documented else "fail"
        boundary_evidence = (
            f"BoundaryMode={get_any(metadata, ['BoundaryMode']) or 'missing'}; "
            f"PaperBoundaryAdmissible={boundary_admissible}; BoundarySourceDocumented={boundary_documented}"
        )
        roughness_status = "pass" if roughness_admissible or precursor_admissible else "fail"
        roughness_evidence = (
            f"RoughnessPaperSourceAdmissible={roughness_admissible}; "
            f"EquivalentPrecursorPaperAdmissible={precursor_admissible}"
        )

    items: List[Dict[str, str]] = [
        item(
            "inlet_mean_profile",
            "pass" if official_af and official_af_hash else "fail",
            f"OfficialAF={official_af or 'missing'}; OfficialAFSha256={official_af_hash or 'missing'}",
            "Archive the official AF CSV path and hash.",
        ),
        item(
            "inlet_turbulence_k",
            inlet_k_status,
            inlet_k_evidence,
            "Read and preserve AF k/TKE evidence before native baseline promotion.",
        ),
        item(
            "inlet_turbulence_length_scale",
            length_scale_status,
            length_scale_evidence,
            "Prove length-scale/correlation from final-window inlet VTK or precursor evidence.",
        ),
        item(
            "inlet_reynolds_stress_tensor",
            stress_status,
            stress_evidence,
            "Document Reynolds-stress assumption and prove distribution-consistent inlet treatment.",
        ),
        item(
            "inlet_temporal_sampling",
            "pass" if inlet_update_interval is not None and inlet_update_interval > 0 else "fail",
            f"InletUpdateInterval={inlet_update_interval}",
            "Record inlet refresh interval and final-window refresh count.",
        ),
        item(
            "inlet_distribution_consistency",
            distribution_status,
            distribution_evidence,
            "Use distribution-consistent DFM/SEM/precursor evidence, not velocity-field-only perturbations.",
        ),
        item(
            "native_fluidx3d_baseline",
            "fail",
            "case metadata is generated_case_not_run; no solver manifest with current VTK hashes is present.",
            "Run native FluidX3D only after protocol preconditions are ready.",
        ),
        item(
            "boundary_conditions",
            boundary_status,
            boundary_evidence,
            "Archive AIJ-equivalent boundary source evidence for inlet/outlet/side/top/floor treatment.",
        ),
        item(
            "wall_roughness_model",
            roughness_status,
            roughness_evidence,
            "Provide source-driven roughness layout or a passing equivalent precursor/recycling baseline.",
        ),
        item(
            "lbm_stability_scaling",
            "pass" if tau is not None and tau > 0.5 and reynolds is not None and dx is not None else "fail",
            f"Tau={tau}; ReH={reynolds}; TargetReH={target_reynolds}; Dx={dx}",
            "Keep Mach/tau/Re scaling within documented ranges and archive solver log after run.",
        ),
        item(
            "time_averaging",
            "risk" if estimated_vtk_frames is not None and estimated_vtk_frames >= 40 else "fail",
            f"EstimatedPostSpinupFrameCount={estimated_vtk_frames}; SaveStartStep={save_start}; SaveInterval={save_interval}",
            "Prove actual final-window VTK frame hashes and stationarity after native run.",
        ),
        item(
            "wind_direction_sign",
            "pass" if wind_label and wind_vector else "fail",
            f"WindDirection={wind_label or 'missing'}; WindDirectionUnitVector={wind_vector or 'missing'}",
            "Write explicit wind label and vector into case metadata.",
        ),
        item(
            "coordinate_transform",
            "pass" if dx is not None else "fail",
            f"Dx={dx}; coordinate transform still requires runtime probe audit.",
            "Verify domain origin, VTK spacing and official coordinates against probe audit.",
        ),
        item(
            "probe_projection",
            "risk" if probe_count and probe_count > 0 else "fail",
            f"ProbeCount={probe_count}; OfficialRSSha256={official_rs_hash or 'missing'}",
            "Regenerate probe_audit.csv from final-window VTK with official probe IDs.",
        ),
        item(
            "normalization_basis",
            "pass" if uref is not None and zref is not None else "fail",
            f"Uref={uref}; Zref={zref}",
            "Verify Uref against AF profile and component normalization during postprocess.",
        ),
        item(
            "systematic_bias_gate",
            "fail",
            "no newly-run native metrics exist for the current case.",
            "Interpret bias only after native run, probe extraction and grid/time sensitivity pass.",
        ),
        item(
            "grid_resolution",
            "risk" if dx is not None else "fail",
            f"Dx={dx}; grid sensitivity is not yet a multi-dx result.",
            "Run matched grid sensitivity before paper-grade accuracy claims.",
        ),
    ]

    known = {entry["Key"] for entry in items}
    for key in REQUIRED_PROTOCOL_ITEM_KEYS:
        if key not in known:
            items.append(item(key, "fail", "missing from writer mapping", "Add explicit protocol evidence mapping."))
    return items


def patch_metadata_identity(path: Path, metadata: Dict[str, Any], args: argparse.Namespace) -> bool:
    changed = False
    if args.case and metadata.get("AijCase") != args.case:
        metadata["AijCase"] = args.case
        changed = True
    if args.wind_direction_label and metadata.get("WindDirection") != args.wind_direction_label:
        metadata["WindDirection"] = args.wind_direction_label
        changed = True
    wind_vector = parse_vector(args.wind_vector)
    if wind_vector is not None and metadata.get("WindDirectionUnitVector") != wind_vector:
        metadata["WindDirectionUnitVector"] = wind_vector
        changed = True
    if changed:
        write_json(path, metadata)
    return changed


def main() -> int:
    args = parse_args()
    case_dir = Path(args.case_dir).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve() if args.metadata else case_dir / "case_metadata.json"
    out_path = Path(args.out).expanduser().resolve() if args.out else case_dir / "validation_protocol_audit.json"

    metadata = read_json(metadata_path)
    if not metadata:
        raise SystemExit(f"metadata missing or empty: {metadata_path}")
    inlet_audit_path = Path(args.inlet_source_audit).expanduser().resolve() if args.inlet_source_audit else None
    boundary_audit_path = Path(args.boundary_source_audit).expanduser().resolve() if args.boundary_source_audit else None
    inlet_audit = read_json(inlet_audit_path) if inlet_audit_path else {}
    boundary_audit = read_json(boundary_audit_path) if boundary_audit_path else {}
    if inlet_audit_path and not inlet_audit:
        raise SystemExit(f"inlet source audit missing or empty: {inlet_audit_path}")
    if boundary_audit_path and not boundary_audit:
        raise SystemExit(f"boundary source audit missing or empty: {boundary_audit_path}")

    metadata_patched = False
    if args.patch_metadata_identity:
        metadata_patched = patch_metadata_identity(metadata_path, metadata, args)
        metadata = read_json(metadata_path)

    items = protocol_items(metadata, args, inlet_audit=inlet_audit, boundary_audit=boundary_audit)
    gate, fail_keys, risk_keys, partial_keys = status_summary(items)
    audit = {
        "Schema": "citylbm.validation_protocol_audit.v1",
        "GeneratedAtUtc": utc_now(),
        "EvidenceType": "generated_protocol_preflight_not_solver_result",
        "DoesNotRunCfdSolver": True,
        "Gate": gate,
        "CaseDir": str(case_dir),
        "CaseMetadataPath": str(metadata_path),
        "InletSourceAuditPath": str(inlet_audit_path) if inlet_audit_path else "",
        "BoundarySourceAuditPath": str(boundary_audit_path) if boundary_audit_path else "",
        "MetadataIdentityPatched": metadata_patched,
        "AijCase": args.case or metadata.get("AijCase") or metadata.get("Case") or "",
        "WindDirection": args.wind_direction_label or metadata.get("WindDirection") or "",
        "WindDirectionUnitVector": parse_vector(args.wind_vector)
        or parse_vector(str(metadata.get("WindDirectionUnitVector") or ""))
        or [],
        "FailKeys": fail_keys,
        "RiskKeys": risk_keys,
        "PartialKeys": partial_keys,
        "Items": items,
        "RequiredItemKeys": REQUIRED_PROTOCOL_ITEM_KEYS,
        "PromotionRule": (
            "This file only closes protocol-content traceability. Items marked fail/risk/partial "
            "must be resolved by native FluidX3D runtime, inlet, boundary, probe and grid evidence "
            "before any paper-grade accuracy claim."
        ),
    }
    write_json(out_path, audit)
    print(f"wrote {out_path}")
    print(f"gate: {gate}; fail={len(fail_keys)} risk={len(risk_keys)} partial={len(partial_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
