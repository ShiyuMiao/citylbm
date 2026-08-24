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


def protocol_items(metadata: Dict[str, Any], args: argparse.Namespace) -> List[Dict[str, str]]:
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

    items: List[Dict[str, str]] = [
        item(
            "inlet_mean_profile",
            "pass" if official_af and official_af_hash else "fail",
            f"OfficialAF={official_af or 'missing'}; OfficialAFSha256={official_af_hash or 'missing'}",
            "Archive the official AF CSV path and hash.",
        ),
        item(
            "inlet_turbulence_k",
            "pass" if official_af_hash and turbulence_method and turbulence_scale is not None else "fail",
            f"TurbulenceMethod={turbulence_method or 'missing'}; TurbulenceScale={turbulence_scale}; OfficialAFSha256={official_af_hash or 'missing'}",
            "Read and preserve AF k/TKE evidence before native baseline promotion.",
        ),
        item(
            "inlet_turbulence_length_scale",
            "risk" if turbulence_method else "fail",
            f"TurbulenceMethod={turbulence_method or 'missing'}; length-scale evidence is metadata-only at preflight.",
            "Prove length-scale/correlation from final-window inlet VTK or precursor evidence.",
        ),
        item(
            "inlet_reynolds_stress_tensor",
            "risk" if turbulence_method else "fail",
            f"StressDdfReconstruction={reconstruct_stress}; turbulence source={turbulence_method or 'missing'}",
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
            "risk" if reconstruct_stress or preserve_boundary_fneq or reconstruct_boundary_ddf else "fail",
            f"ReconstructInletStressDdf={reconstruct_stress}; PreserveBoundaryFneq={preserve_boundary_fneq}; ReconstructBoundaryDdf={reconstruct_boundary_ddf}",
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
            "pass" if boundary_admissible and boundary_documented else "fail",
            f"BoundaryMode={get_any(metadata, ['BoundaryMode']) or 'missing'}; PaperBoundaryAdmissible={boundary_admissible}; BoundarySourceDocumented={boundary_documented}",
            "Archive AIJ-equivalent boundary source evidence for inlet/outlet/side/top/floor treatment.",
        ),
        item(
            "wall_roughness_model",
            "pass" if roughness_admissible or precursor_admissible else "fail",
            f"RoughnessPaperSourceAdmissible={roughness_admissible}; EquivalentPrecursorPaperAdmissible={precursor_admissible}",
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

    metadata_patched = False
    if args.patch_metadata_identity:
        metadata_patched = patch_metadata_identity(metadata_path, metadata, args)
        metadata = read_json(metadata_path)

    items = protocol_items(metadata, args)
    gate, fail_keys, risk_keys, partial_keys = status_summary(items)
    audit = {
        "Schema": "citylbm.validation_protocol_audit.v1",
        "GeneratedAtUtc": utc_now(),
        "EvidenceType": "generated_protocol_preflight_not_solver_result",
        "DoesNotRunCfdSolver": True,
        "Gate": gate,
        "CaseDir": str(case_dir),
        "CaseMetadataPath": str(metadata_path),
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
