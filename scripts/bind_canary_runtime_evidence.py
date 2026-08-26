#!/usr/bin/env python3
"""Bind short native canary runtime evidence into one audit manifest.

This manifest is intentionally diagnostic-only. A passing result means the
short native run produced fresh VTK frames and measurable inlet statistics; it
does not make the run suitable for paper-grade AIJ accuracy claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PASS = "pass"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bind post-canary runtime audits into one diagnostic evidence file.")
    parser.add_argument("--run-dir", default="", help="Fast-track/preflight output directory.")
    parser.add_argument("--native-canary-manifest", default="", help="native_diagnostic_canary_manifest.json path.")
    parser.add_argument("--runtime-inlet-diagnostics-audit", default="", help="runtime_inlet_diagnostics_csv_audit.json path.")
    parser.add_argument("--inlet-correlation-audit", default="", help="inlet_correlation_audit.json path.")
    parser.add_argument("--out", default="", help="Output JSON path; defaults to <run-dir>/canary_runtime_evidence_manifest.json.")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def sha256_file(path: Optional[Path]) -> str:
    if path is None or not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ["Gate", "gate", "Status", "status"]:
            if key in value:
                return compact(value[key])
        return ""
    return str(value).strip()


def as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def artifact_path(preflight: Dict[str, Any], key: str) -> str:
    artifacts = preflight.get("Artifacts") if isinstance(preflight.get("Artifacts"), dict) else {}
    return str(artifacts.get(key, "")).strip()


def resolve_path(run_dir: Path, explicit: str, preflight: Dict[str, Any], artifact_key: str, fallback_name: str) -> Path:
    if explicit.strip():
        return Path(explicit).expanduser().resolve()
    from_manifest = artifact_path(preflight, artifact_key)
    if from_manifest:
        return Path(from_manifest).expanduser().resolve()
    return (run_dir / fallback_name).resolve()


def file_record(path: Path) -> Dict[str, Any]:
    return {
        "Path": str(path),
        "Exists": path.exists(),
        "Sha256": sha256_file(path),
    }


def gate_is_pass(value: Any) -> bool:
    return compact(value).lower() == PASS


def build_manifest(
    run_dir: Path,
    native_path: Path,
    diagnostics_path: Path,
    correlation_path: Path,
) -> Dict[str, Any]:
    native = read_json(native_path)
    diagnostics = read_json(diagnostics_path)
    correlation = read_json(correlation_path)

    native_accuracy = native.get("NativeAccuracyEvidenceGate")
    if not isinstance(native_accuracy, dict):
        native_accuracy = {}
    run = native.get("Run") if isinstance(native.get("Run"), dict) else {}
    vtk_files = native.get("VtkFiles") if isinstance(native.get("VtkFiles"), list) else []
    existing_vtk_files = [item for item in vtk_files if isinstance(item, dict) and item.get("Exists")]
    selected_vtk_hashes = [str(item.get("Sha256", "")).strip() for item in existing_vtk_files if item.get("Sha256")]

    native_run_gate = compact(run.get("Gate") or native_accuracy.get("RunGate")).lower()
    native_vtk_gate = compact(native_accuracy.get("ActualVtkOutputGate")).lower()
    native_accuracy_gate = compact(native_accuracy.get("Gate")).lower()
    diagnostics_gate = compact(diagnostics.get("Gate")).lower()
    correlation_gate = compact(correlation.get("inlet_correlation_gate") or correlation.get("Gate")).lower()
    k_variance_gate = compact(correlation.get("inlet_k_variance_gate")).lower()
    tke_gate = compact(correlation.get("inlet_tke_gate")).lower()

    reasons: List[str] = []
    if not native_path.exists():
        reasons.append("native_canary_manifest_missing")
    if native_run_gate != PASS:
        reasons.append(f"native_run_gate_not_pass:{native_run_gate or 'missing'}")
    if native_accuracy_gate != PASS:
        reasons.append(f"native_accuracy_evidence_gate_not_pass:{native_accuracy_gate or 'missing'}")
    if native_vtk_gate != PASS:
        reasons.append(f"actual_vtk_output_gate_not_pass:{native_vtk_gate or 'missing'}")
    if not selected_vtk_hashes:
        reasons.append("selected_vtk_hashes_missing")
    if not diagnostics_path.exists():
        reasons.append("runtime_inlet_diagnostics_audit_missing")
    if diagnostics_gate != PASS:
        reasons.append(f"runtime_inlet_diagnostics_gate_not_pass:{diagnostics_gate or 'missing'}")
    if not correlation_path.exists():
        reasons.append("inlet_correlation_audit_missing")
    if correlation_gate != PASS:
        reasons.append(f"inlet_correlation_gate_not_pass:{correlation_gate or 'missing'}")
    if k_variance_gate and k_variance_gate != PASS:
        reasons.append(f"inlet_k_variance_gate_not_pass:{k_variance_gate}")
    if tke_gate and tke_gate != PASS:
        reasons.append(f"inlet_tke_gate_not_pass:{tke_gate}")

    gate = PASS if not reasons else "fail"
    return {
        "Schema": "citylbm.canary_runtime_evidence.v1",
        "GeneratedAtUtc": utc_now(),
        "Gate": gate,
        "Reasons": reasons if reasons else ["canary_runtime_evidence_present"],
        "ReasonsCsv": ";".join(reasons) if reasons else "canary_runtime_evidence_present",
        "EvidenceType": "newly_run_or_bound_runtime_artifact",
        "UseClass": "diagnostic_only_not_for_paper_accuracy_claims",
        "PaperUseGate": "fail",
        "PaperUseReason": (
            "A short canary proves runtime inlet/VTK evidence only. It does not close paper-grade "
            "AIJ boundary, averaging, Reynolds-stress tensor, length-scale or probe-error gates."
        ),
        "RunDir": str(run_dir),
        "Files": {
            "NativeCanaryManifest": file_record(native_path),
            "RuntimeInletDiagnosticsAudit": file_record(diagnostics_path),
            "InletCorrelationAudit": file_record(correlation_path),
        },
        "NativeRun": {
            "RunGate": native_run_gate,
            "NativeAccuracyEvidenceGate": native_accuracy_gate,
            "ActualVtkOutputGate": native_vtk_gate,
            "ActualFrameCount": as_int(native_accuracy.get("ActualFrameCount")) or len(existing_vtk_files),
            "SelectedFinalWindowVtkSha256Count": as_int(native_accuracy.get("SelectedFinalWindowVtkSha256Count"))
            or len(selected_vtk_hashes),
            "VtkFileCount": as_int(native.get("VtkFileCount")) or len(existing_vtk_files),
            "SelectedVtkSha256": selected_vtk_hashes,
        },
        "RuntimeInletDiagnostics": {
            "Gate": diagnostics_gate,
            "CsvPath": diagnostics.get("CsvPath", ""),
            "CsvSha256": diagnostics.get("CsvSha256", ""),
            "SelectedSteps": diagnostics.get("SelectedSteps", []),
            "Metrics": diagnostics.get("Metrics", {}),
        },
        "InletCorrelation": {
            "Gate": correlation_gate,
            "KVarianceGate": k_variance_gate,
            "TkeGate": tke_gate,
            "SourceTimeSteps": correlation.get("source_time_steps", []),
            "SourceStepSpan": correlation.get("source_step_span"),
            "TemporalLag1MeanCorrelation": correlation.get("temporal_lag1_mean_correlation"),
            "TemporalLag1AbsMeanCorrelation": correlation.get("temporal_lag1_abs_mean_correlation"),
            "TemporalIntegralPositiveLagCount": correlation.get("temporal_integral_positive_lag_count"),
            "SpatialAdjacentMeanCorrelation": correlation.get("spatial_adjacent_mean_correlation"),
            "SpatialIntegralPositiveLagCount": correlation.get("spatial_integral_positive_lag_count"),
            "MeanTkeFromComponents": correlation.get("mean_turbulent_kinetic_energy_from_components"),
            "InletTkeToKRatio": correlation.get("inlet_tke_to_k_ratio"),
            "StreamwiseVarianceToKRatio": correlation.get("inlet_streamwise_variance_to_k_ratio"),
        },
    }


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve() if args.run_dir.strip() else Path.cwd().resolve()
    preflight = read_json(run_dir / "native_preflight_pack_manifest.json")
    native_path = resolve_path(
        run_dir,
        args.native_canary_manifest,
        preflight,
        "NativeDiagnosticCanaryManifest",
        "native_diagnostic_canary_manifest.json",
    )
    diagnostics_path = resolve_path(
        run_dir,
        args.runtime_inlet_diagnostics_audit,
        preflight,
        "RuntimeInletDiagnosticsAudit",
        "runtime_inlet_diagnostics_csv_audit.json",
    )
    correlation_path = resolve_path(
        run_dir,
        args.inlet_correlation_audit,
        preflight,
        "InletCorrelationAudit",
        "inlet_correlation_audit.json",
    )
    out = Path(args.out).expanduser().resolve() if args.out.strip() else (run_dir / "canary_runtime_evidence_manifest.json")
    manifest = build_manifest(run_dir, native_path, diagnostics_path, correlation_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"canary_runtime_evidence_gate={manifest['Gate']}; manifest={out}")
    if manifest["Gate"] != PASS:
        print("reasons=" + str(manifest.get("ReasonsCsv", "")))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
