#!/usr/bin/env python3
"""Run the complete post-run evidence chain for native FluidX3D/CityLBM VTK.

This script does not launch FluidX3D. It only audits an already completed run
directory and produces the artifacts required before a Case A or Case E result
can be considered for paper-grade validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


class ChainError(RuntimeError):
    """Raised when a required evidence-chain step fails."""

    def __init__(self, step: str, returncode: int) -> None:
        super().__init__(f"Step failed: {step} (exit {returncode})")
        self.step = step
        self.returncode = returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a complete validation evidence package from existing "
            "native FluidX3D/CityLBM VTK output. The CFD solver is not run."
        )
    )
    parser.add_argument("run_dir", help="Case root directory, or an output directory containing u-*.vtk.")
    parser.add_argument("--vtk-dir", default="", help="VTK directory. Defaults to <run_dir>/output when it exists.")
    parser.add_argument("--official", required=True, help="Official RS/probe CSV.")
    parser.add_argument("--af-csv", required=True, help="Official AF inlet profile CSV with z,U,k columns.")
    parser.add_argument("--metadata", required=True, help="case_metadata.json generated with the run.")
    parser.add_argument(
        "--boundary-evidence",
        default="",
        help="Optional JSON documenting AIJ-equivalent boundary/fetch/roughness evidence.",
    )
    parser.add_argument("--solver-log", default="", help="Optional solver stdout/stderr log.")
    parser.add_argument("--case", required=True, help="Case label used by the official CSV and metrics row.")
    parser.add_argument("--wind-direction-label", default="", help="Official wind-direction label, e.g. N.")
    parser.add_argument("--wind-vector", required=True, help="Airflow vector, e.g. 1,0,0 or 0,-1,0.")
    parser.add_argument("--u-ref", required=True, type=float, help="Reference velocity for normalization.")
    parser.add_argument("--z-ref", type=float, default=None, help="Reference height, if applicable.")
    parser.add_argument("--software", default="native-fluidx3d", help="Software label for the metrics/gate row.")
    parser.add_argument("--version", default="", help="Optional software/plugin version label.")
    parser.add_argument("--dx", default="", help="Optional grid spacing recorded in metrics.")
    parser.add_argument("--steps", default="", help="Optional solver step count recorded in metrics.")
    parser.add_argument("--save-interval", default="", help="Optional VTK save interval recorded in metrics.")
    parser.add_argument("--vtk-save-start-step", default="", help="Optional first VTK save step for run-configuration frame-count preflight.")
    parser.add_argument("--geometry-scale", default="", help="Optional geometry scale recorded in metrics.")
    parser.add_argument("--profile-csv", default="", help="Optional profile CSV path recorded in metrics.")
    parser.add_argument(
        "--grid-sensitivity-metrics",
        action="append",
        default=[],
        help="Metrics CSV/JSON from another matched dx run. Repeat to build grid_sensitivity_audit.json.",
    )
    parser.add_argument(
        "--paired-native-metrics",
        default="",
        help="Native FluidX3D metrics CSV/JSON used to audit paired CityLBM/native comparability.",
    )
    parser.add_argument("--average-last-n", type=int, default=40, help="Average the last N VTK frames.")
    parser.add_argument("--min-avg-frames", type=int, default=40, help="Minimum frames required by the time-average gate.")
    parser.add_argument("--min-avg-step-span", type=int, default=20000, help="Minimum solver-step span covered by the averaged final VTK window.")
    parser.add_argument("--pattern", default="u-*.vtk", help="VTK glob pattern.")
    parser.add_argument("--probe-tolerance", type=float, default=0.0, help="Max nearest-node probe distance in meters. 0 disables failure by tolerance.")
    parser.add_argument(
        "--compared-component",
        choices=["speed_ratio", "streamwise_ratio", "speed", "streamwise_velocity", "u", "v", "w"],
        default="speed_ratio",
    )
    parser.add_argument(
        "--interpolation",
        choices=["trilinear", "nearest"],
        default="trilinear",
        help="VTK probe sampling method. Trilinear is recommended for structured VTK.",
    )
    parser.add_argument("--velocity-scale", type=float, default=1.0, help="Velocity multiplier applied to VTK values.")
    parser.add_argument("--out-dir", default="", help="Output directory. Defaults to <run_dir>/validation_chain.")
    parser.add_argument("--max-mean-speed-stddev-ratio", type=float, default=0.05)
    parser.add_argument("--max-point-speed-stddev-ratio", type=float, default=0.20)
    parser.add_argument("--max-u-bias-ratio", type=float, default=0.20)
    parser.add_argument("--max-u-rmse-ratio", type=float, default=0.30)
    parser.add_argument("--min-u-r2", type=float, default=0.80)
    parser.add_argument("--min-slope", type=float, default=0.70)
    parser.add_argument("--max-slope", type=float, default=1.30)
    parser.add_argument("--max-intercept-abs", type=float, default=0.20)
    parser.add_argument("--max-k-bias-ratio", type=float, default=0.30)
    parser.add_argument("--max-empty-tunnel-u-bias-ratio", type=float, default=0.10)
    parser.add_argument("--max-empty-tunnel-k-bias-ratio", type=float, default=0.30)
    parser.add_argument("--max-official-coordinate-delta-m", type=float, default=1.0e-6)
    parser.add_argument("--max-probe-failure-fraction", type=float, default=0.0)
    parser.add_argument("--max-frontal-blockage-ratio", type=float, default=0.05)
    parser.add_argument("--max-estimated-mach", type=float, default=0.12)
    parser.add_argument("--min-lbm-tau", type=float, default=0.5001)
    parser.add_argument("--max-lbm-tau", type=float, default=2.0)
    parser.add_argument("--max-paper-dx-m", type=float, default=3.0)
    parser.add_argument("--min-grid-sensitivity-run-count", type=int, default=2)
    parser.add_argument("--min-grid-refinement-ratio", type=float, default=1.25)
    parser.add_argument("--max-grid-rmse-change-ratio", type=float, default=0.10)
    parser.add_argument("--max-grid-bias-change-ratio", type=float, default=0.05)
    parser.add_argument("--vtk-stability-sample-limit", type=int, default=20000)
    parser.add_argument(
        "--allow-velocity-only-inlet",
        action="store_true",
        help="Diagnostic override for CityLBM STG-lite velocity-field-only inlet.",
    )
    parser.add_argument(
        "--allow-diagnostic",
        action="store_true",
        help="Return success for diagnostic-only packages while preserving FAIL gate evidence.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def as_existing_path(value: str, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    return path


def add_optional(cmd: List[str], flag: str, value: Optional[Any]) -> None:
    if value is None:
        return
    text = str(value)
    if text == "":
        return
    cmd.extend([flag, text])


def run_step(name: str, cmd: Sequence[str], allow_fail: bool = False) -> Dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        list(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - started
    record: Dict[str, Any] = {
        "name": name,
        "command": list(cmd),
        "returncode": completed.returncode,
        "allow_fail": allow_fail,
        "elapsed_seconds": round(elapsed, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0 and not allow_fail:
        raise ChainError(name, completed.returncode)
    return record


def write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def json_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "pass"}
    return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def resolve_manifest_source_path(raw_path: str, manifest_path: Optional[Path]) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute() and manifest_path is not None:
        path = manifest_path.parent / path
    return path.resolve()


def native_baseline_gate_from_manifest(manifest: Dict[str, Any], manifest_path: Optional[Path]) -> str:
    if not manifest:
        return "missing_native_manifest"
    if not str(manifest.get("BaselineId") or "").strip():
        return "missing_baseline_id"
    if not json_bool(manifest.get("NativeFluidX3DPathExplicitlyProvided")):
        return "native_fluidx3d_path_not_explicit"

    source_validation = manifest.get("NativeFluidX3DSourceValidation", {})
    if not isinstance(source_validation, dict) or not json_bool(source_validation.get("IsValid")):
        return "native_fluidx3d_source_validation_failed"

    required_roles = {
        "Native FluidX3D original setup",
        "Native FluidX3D original defines",
        "Native FluidX3D lbm.hpp",
        "Native FluidX3D lbm.cpp",
    }
    records = manifest.get("RequiredSourceFiles", [])
    if not isinstance(records, list):
        return "native_source_hash_records_missing"

    by_role: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if isinstance(record, dict):
            role = str(record.get("Role") or "").strip()
            if role:
                by_role[role] = record

    for role in sorted(required_roles):
        record = by_role.get(role)
        if not record:
            return f"missing_native_source_record:{role}"
        if not json_bool(record.get("Exists")):
            return f"native_source_file_missing:{role}"
        if str(record.get("HashAlgorithm") or "").strip().upper() != "SHA256":
            return f"native_source_hash_algorithm_not_sha256:{role}"
        declared_sha = str(record.get("Sha256") or "").strip().lower()
        if not declared_sha:
            return f"native_source_hash_missing:{role}"
        declared_path = str(record.get("Path") or "").strip()
        if not declared_path:
            return f"native_source_path_missing:{role}"
        source_path = resolve_manifest_source_path(declared_path, manifest_path)
        if not source_path.exists():
            return f"native_source_path_not_found:{role}"
        actual_sha = sha256_file(source_path)
        if declared_sha != actual_sha:
            return f"native_source_hash_mismatch:{role}"

    return "pass"


def find_run_file(run_dir: Path, name: str) -> Optional[Path]:
    candidate = run_dir / name
    if candidate.exists():
        return candidate
    output_candidate = run_dir / "output" / name
    if output_candidate.exists():
        return output_candidate
    src_candidate = run_dir / "src" / name
    if src_candidate.exists():
        return src_candidate
    return None


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    run_dir = as_existing_path(args.run_dir, "run_dir")
    official = as_existing_path(args.official, "official")
    af_csv = as_existing_path(args.af_csv, "af_csv")
    metadata = as_existing_path(args.metadata, "metadata")
    solver_log = Path(args.solver_log).expanduser().resolve() if args.solver_log else None
    if solver_log is not None and not solver_log.exists():
        raise SystemExit(f"solver_log does not exist: {solver_log}")

    if args.vtk_dir:
        vtk_dir = as_existing_path(args.vtk_dir, "vtk_dir")
    else:
        default_output = run_dir / "output"
        vtk_dir = default_output if default_output.exists() else run_dir

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else run_dir / "validation_chain"
    out_dir.mkdir(parents=True, exist_ok=True)

    native_audit_json = out_dir / "native_run_audit.json"
    native_preconditions_json = out_dir / "native_preconditions_audit.json"
    inlet_source_json = out_dir / "inlet_source_audit.json"
    boundary_source_json = out_dir / "boundary_source_audit.json"
    inlet_audit_json = out_dir / "inlet_profile_audit.json"
    inlet_audit_csv = out_dir / "inlet_profile_audit.csv"
    inlet_correlation_json = out_dir / "inlet_correlation_audit.json"
    boundary_audit_json = out_dir / "boundary_protocol_audit.json"
    boundary_runtime_json = out_dir / "boundary_runtime_audit.json"
    boundary_runtime_csv = out_dir / "boundary_runtime_audit.csv"
    probe_audit_csv = out_dir / "probe_audit.csv"
    component_sensitivity_json = out_dir / "component_sensitivity_audit.json"
    component_sensitivity_csv = out_dir / "component_sensitivity_audit.csv"
    grid_sensitivity_json = out_dir / "grid_sensitivity_audit.json"
    native_citylbm_parity_json = out_dir / "native_citylbm_parity_audit.json"
    metrics_csv = out_dir / "validation_metrics.csv"
    comparison_csv = out_dir / "probe_comparison.csv"
    gate_json = out_dir / "validation_gate_report.json"
    manifest_path = out_dir / "validation_chain_manifest.json"
    native_manifest_path = find_run_file(run_dir, "native_fluidx3d_baseline_manifest.json")
    native_manifest = read_json(native_manifest_path) if native_manifest_path else {}
    native_baseline_id = str(native_manifest.get("BaselineId") or "").strip()
    native_baseline_gate = native_baseline_gate_from_manifest(native_manifest, native_manifest_path)

    manifest: Dict[str, Any] = {
        "GeneratedAtUtc": utc_now(),
        "ChainPurpose": "post_run_validation_evidence_chain",
        "DoesNotRunCfdSolver": True,
        "RunDirectory": str(run_dir),
        "VtkDirectory": str(vtk_dir),
        "OutputDirectory": str(out_dir),
        "Inputs": {
            "OfficialCsv": str(official),
            "AfCsv": str(af_csv),
            "Metadata": str(metadata),
            "BoundaryEvidence": str(Path(args.boundary_evidence).expanduser().resolve()) if args.boundary_evidence else "",
            "SolverLog": str(solver_log) if solver_log else "",
            "Case": args.case,
            "WindDirectionLabel": args.wind_direction_label,
            "WindVector": args.wind_vector,
            "Uref": args.u_ref,
            "Zref": args.z_ref,
            "Software": args.software,
            "AverageLastN": args.average_last_n,
            "VtkSaveStartStep": args.vtk_save_start_step,
            "ComparedComponent": args.compared_component,
            "Interpolation": args.interpolation,
            "GridSensitivityMetrics": [
                str(Path(item).expanduser().resolve()) for item in args.grid_sensitivity_metrics
            ],
            "PairedNativeMetrics": str(Path(args.paired_native_metrics).expanduser().resolve()) if args.paired_native_metrics else "",
        },
        "NativeBaselineGateFromManifest": native_baseline_gate,
        "Artifacts": {
            "NativeFluidX3DBaselineManifest": str(native_manifest_path) if native_manifest_path else "",
            "NativeRunAudit": str(native_audit_json),
            "NativePreconditionsAudit": str(native_preconditions_json),
            "InletSourceAuditJson": str(inlet_source_json),
            "BoundarySourceAuditJson": str(boundary_source_json),
            "InletProfileAuditJson": str(inlet_audit_json),
            "InletProfileAuditCsv": str(inlet_audit_csv),
            "InletCorrelationAuditJson": str(inlet_correlation_json),
            "BoundaryProtocolAuditJson": str(boundary_audit_json),
            "BoundaryRuntimeAuditJson": str(boundary_runtime_json),
            "BoundaryRuntimeAuditCsv": str(boundary_runtime_csv),
            "ProbeAuditCsv": str(probe_audit_csv),
            "ComponentSensitivityAuditJson": str(component_sensitivity_json),
            "ComponentSensitivityAuditCsv": str(component_sensitivity_csv),
            "GridSensitivityAuditJson": str(grid_sensitivity_json),
            "NativeCityLBMParityAuditJson": str(native_citylbm_parity_json),
            "ValidationMetricsCsv": str(metrics_csv),
            "ProbeComparisonCsv": str(comparison_csv),
            "ValidationGateReport": str(gate_json),
            "ValidationChainManifest": str(manifest_path),
        },
        "Steps": [],
        "ChainStatus": "running",
        "ExitCode": None,
    }

    py = sys.executable

    try:
        native_cmd = [
            py,
            str(script_dir / "audit_native_run.py"),
            str(run_dir),
            "--metadata",
            str(metadata),
            "--out",
            str(native_audit_json),
            "--pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-avg-frames",
            str(args.min_avg_frames),
            "--min-avg-step-span",
            str(args.min_avg_step_span),
            "--max-mean-speed-stddev-ratio",
            str(args.max_mean_speed_stddev_ratio),
            "--max-point-speed-stddev-ratio",
            str(args.max_point_speed_stddev_ratio),
            "--vtk-stability-sample-limit",
            str(args.vtk_stability_sample_limit),
        ]
        if solver_log:
            native_cmd.extend(["--solver-log", str(solver_log)])
        add_optional(native_cmd, "--time-steps", args.steps)
        add_optional(native_cmd, "--vtk-save-interval", args.save_interval)
        add_optional(native_cmd, "--vtk-save-start-step", args.vtk_save_start_step)
        manifest["Steps"].append(run_step("audit_native_run", native_cmd))
        write_manifest(manifest_path, manifest)

        setup_cpp = find_run_file(run_dir, "setup.cpp")
        if setup_cpp:
            inlet_source_cmd = [
                py,
                str(script_dir / "audit_inlet_source.py"),
                "--setup",
                str(setup_cpp),
                "--metadata",
                str(metadata),
                "--out",
                str(inlet_source_json),
            ]
            manifest["Steps"].append(run_step("audit_inlet_source", inlet_source_cmd, allow_fail=True))
            boundary_source_cmd = [
                py,
                str(script_dir / "audit_boundary_source.py"),
                "--setup",
                str(setup_cpp),
                "--metadata",
                str(metadata),
                "--out",
                str(boundary_source_json),
            ]
            manifest["Steps"].append(run_step("audit_boundary_source", boundary_source_cmd, allow_fail=True))
        else:
            missing_source_audit = {
                "generated_at_utc": utc_now(),
                "setup_cpp": "",
                "metadata": str(metadata),
                "inlet_source_gate": "fail",
                "inlet_source_gate_reasons": ["setup_cpp_missing"],
                "inlet_source_gate_reasons_csv": "setup_cpp_missing",
                "paper_grade_inlet_source_gate": "fail",
                "paper_grade_inlet_source_gate_reasons": ["setup_cpp_missing"],
                "paper_grade_inlet_source_gate_reasons_csv": "setup_cpp_missing",
                "inlet_source_method_class": "none",
                "inlet_source_distribution_consistent": False,
                "inlet_source_velocity_field_only": False,
                "setup_cpp_sha256": "",
            }
            inlet_source_json.write_text(json.dumps(missing_source_audit, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            missing_boundary_source_audit = {
                "generated_at_utc": utc_now(),
                "setup_cpp": "",
                "metadata": str(metadata),
                "boundary_source_gate": "fail",
                "boundary_source_gate_reasons": ["setup_cpp_missing"],
                "boundary_source_gate_reasons_csv": "setup_cpp_missing",
                "paper_grade_boundary_source_gate": "fail",
                "paper_grade_boundary_source_gate_reasons": ["setup_cpp_missing"],
                "paper_grade_boundary_source_gate_reasons_csv": "setup_cpp_missing",
                "boundary_source_method_class": "none",
                "boundary_source_coherent": False,
                "boundary_source_simplified": True,
                "boundary_source_wind_tunnel_equivalent": False,
                "setup_cpp_sha256": "",
            }
            boundary_source_json.write_text(
                json.dumps(missing_boundary_source_audit, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )
            manifest["Steps"].append(
                {
                    "Name": "audit_inlet_source",
                    "Command": "",
                    "StartedAtUtc": utc_now(),
                    "FinishedAtUtc": utc_now(),
                    "ReturnCode": 2,
                    "Stdout": "",
                    "Stderr": "setup.cpp missing",
                    "AllowedToFail": True,
                }
            )
            manifest["Steps"].append(
                {
                    "Name": "audit_boundary_source",
                    "Command": "",
                    "StartedAtUtc": utc_now(),
                    "FinishedAtUtc": utc_now(),
                    "ReturnCode": 2,
                    "Stdout": "",
                    "Stderr": "setup.cpp missing",
                    "AllowedToFail": True,
                }
            )
        write_manifest(manifest_path, manifest)

        boundary_cmd = [
            py,
            str(script_dir / "audit_boundary_protocol.py"),
            str(run_dir),
            "--metadata",
            str(metadata),
            "--out",
            str(boundary_audit_json),
            "--max-frontal-blockage-ratio",
            str(args.max_frontal_blockage_ratio),
        ]
        if args.boundary_evidence:
            boundary_cmd.extend(["--evidence", str(Path(args.boundary_evidence).expanduser().resolve())])
        manifest["Steps"].append(run_step("audit_boundary_protocol", boundary_cmd, allow_fail=True))
        write_manifest(manifest_path, manifest)

        inlet_cmd = [
            py,
            str(script_dir / "audit_inlet_profile_from_vtk.py"),
            str(vtk_dir),
            "--af-csv",
            str(af_csv),
            "--metadata",
            str(metadata),
            "--pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-frames",
            str(args.min_avg_frames),
            "--min-step-span",
            str(args.min_avg_step_span),
            "--wind-direction",
            args.wind_vector,
            "--plane-axis",
            "auto-inlet",
            "--out-json",
            str(inlet_audit_json),
            "--out-csv",
            str(inlet_audit_csv),
            "--max-u-mae-ratio",
            str(args.max_empty_tunnel_u_bias_ratio),
            "--max-k-mae-ratio",
            str(args.max_empty_tunnel_k_bias_ratio),
            "--velocity-scale",
            str(args.velocity_scale),
        ]
        manifest["Steps"].append(run_step("audit_inlet_profile_from_vtk", inlet_cmd))
        write_manifest(manifest_path, manifest)

        inlet_correlation_cmd = [
            py,
            str(script_dir / "audit_inlet_correlation_from_vtk.py"),
            str(vtk_dir),
            "--metadata",
            str(metadata),
            "--pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-frames",
            str(args.min_avg_frames),
            "--min-step-span",
            str(args.min_avg_step_span),
            "--wind-direction",
            args.wind_vector,
            "--plane-axis",
            "auto-inlet",
            "--out-json",
            str(inlet_correlation_json),
            "--velocity-scale",
            str(args.velocity_scale),
        ]
        manifest["Steps"].append(run_step("audit_inlet_correlation_from_vtk", inlet_correlation_cmd, allow_fail=True))
        write_manifest(manifest_path, manifest)

        boundary_runtime_cmd = [
            py,
            str(script_dir / "audit_boundary_runtime_from_vtk.py"),
            str(vtk_dir),
            "--af-csv",
            str(af_csv),
            "--wind-direction",
            args.wind_vector,
            "--pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-frames",
            str(args.min_avg_frames),
            "--min-step-span",
            str(args.min_avg_step_span),
            "--velocity-scale",
            str(args.velocity_scale),
            "--max-inlet-u-mae-ratio",
            str(args.max_empty_tunnel_u_bias_ratio),
            "--out-json",
            str(boundary_runtime_json),
            "--out-csv",
            str(boundary_runtime_csv),
        ]
        manifest["Steps"].append(run_step("audit_boundary_runtime_from_vtk", boundary_runtime_cmd, allow_fail=True))
        write_manifest(manifest_path, manifest)

        probe_cmd = [
            py,
            str(script_dir / "probe_vtk_points.py"),
            str(vtk_dir),
            "--official",
            str(official),
            "--out",
            str(probe_audit_csv),
            "--pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-avg-frames",
            str(args.min_avg_frames),
            "--min-avg-step-span",
            str(args.min_avg_step_span),
            "--case",
            args.case,
            "--wind-direction-label",
            args.wind_direction_label,
            "--wind-direction",
            args.wind_vector,
            "--u-ref",
            str(args.u_ref),
            "--compared-component",
            args.compared_component,
            "--interpolation",
            args.interpolation,
            "--tolerance",
            str(args.probe_tolerance),
            "--velocity-scale",
            str(args.velocity_scale),
        ]
        manifest["Steps"].append(run_step("probe_vtk_points", probe_cmd))
        write_manifest(manifest_path, manifest)

        component_sensitivity_cmd = [
            py,
            str(script_dir / "audit_component_sensitivity.py"),
            "--probe-audit",
            str(probe_audit_csv),
            "--official",
            str(official),
            "--out-json",
            str(component_sensitivity_json),
            "--out-csv",
            str(component_sensitivity_csv),
            "--case",
            args.case,
            "--wind-direction",
            args.wind_direction_label,
            "--selected-component",
            args.compared_component,
            "--min-source-step-span",
            str(args.min_avg_step_span),
        ]
        manifest["Steps"].append(run_step("audit_component_sensitivity", component_sensitivity_cmd, allow_fail=True))
        write_manifest(manifest_path, manifest)

        native_preconditions_cmd = [
            py,
            str(script_dir / "audit_native_preconditions.py"),
            str(run_dir),
            "--metadata",
            str(metadata),
            "--runtime-audit",
            str(native_audit_json),
            "--inlet-source-audit",
            str(inlet_source_json),
            "--inlet-profile-audit",
            str(inlet_audit_json),
            "--inlet-correlation-audit",
            str(inlet_correlation_json),
            "--boundary-source-audit",
            str(boundary_source_json),
            "--boundary-protocol-audit",
            str(boundary_audit_json),
            "--boundary-runtime-audit",
            str(boundary_runtime_json),
            "--probe-audit",
            str(probe_audit_csv),
            "--component-sensitivity-audit",
            str(component_sensitivity_json),
            "--official",
            str(official),
            "--af-csv",
            str(af_csv),
            "--case",
            args.case,
            "--wind-direction-label",
            args.wind_direction_label,
            "--software",
            args.software,
            "--wind-vector",
            args.wind_vector,
            "--u-ref",
            str(args.u_ref),
            "--expected-compared-component",
            args.compared_component,
            "--max-official-coordinate-delta-m",
            str(args.max_official_coordinate_delta_m),
            "--expected-vtk-pattern",
            args.pattern,
            "--average-last-n",
            str(args.average_last_n),
            "--min-avg-frames",
            str(args.min_avg_frames),
            "--min-avg-step-span",
            str(args.min_avg_step_span),
            "--out",
            str(native_preconditions_json),
        ]
        if native_manifest_path:
            native_preconditions_cmd.extend(["--manifest", str(native_manifest_path)])
        manifest["Steps"].append(run_step("audit_native_preconditions", native_preconditions_cmd, allow_fail=True))
        write_manifest(manifest_path, manifest)

        metrics_cmd = [
            py,
            str(script_dir / "validation_metrics_from_probe_audit.py"),
            "--probe-audit",
            str(probe_audit_csv),
            "--official",
            str(official),
            "--out",
            str(metrics_csv),
            "--comparison-out",
            str(comparison_csv),
            "--metadata",
            str(metadata),
            "--read-vtk-audit",
            str(native_audit_json),
            "--inlet-profile-audit",
            str(inlet_audit_json),
            "--inlet-correlation-audit",
            str(inlet_correlation_json),
            "--inlet-source-audit",
            str(inlet_source_json),
            "--boundary-source-audit",
            str(boundary_source_json),
            "--native-preconditions-audit",
            str(native_preconditions_json),
            "--boundary-protocol-audit",
            str(boundary_audit_json),
            "--boundary-runtime-audit",
            str(boundary_runtime_json),
            "--component-sensitivity-audit",
            str(component_sensitivity_json),
            "--case",
            args.case,
            "--wind-direction",
            args.wind_direction_label,
            "--software",
            args.software,
            "--u-ref",
            str(args.u_ref),
            "--averaging-window",
            str(args.average_last_n),
            "--profile-csv",
            str(af_csv),
        ]
        add_optional(metrics_cmd, "--version", args.version)
        add_optional(metrics_cmd, "--z-ref", args.z_ref)
        add_optional(metrics_cmd, "--dx", args.dx)
        add_optional(metrics_cmd, "--steps", args.steps)
        add_optional(metrics_cmd, "--save-interval", args.save_interval)
        add_optional(metrics_cmd, "--geometry-scale", args.geometry_scale)
        add_optional(metrics_cmd, "--native-baseline-id", native_baseline_id)
        add_optional(metrics_cmd, "--native-baseline-gate", native_baseline_gate)
        manifest["Steps"].append(run_step("validation_metrics_from_probe_audit", metrics_cmd))
        write_manifest(manifest_path, manifest)

        if args.grid_sensitivity_metrics:
            grid_cmd = [
                py,
                str(script_dir / "audit_grid_sensitivity.py"),
                "--out",
                str(grid_sensitivity_json),
                "--case",
                args.case,
                "--wind-direction",
                args.wind_direction_label,
                "--software",
                args.software,
                "--max-paper-dx-m",
                str(args.max_paper_dx_m),
                "--min-grid-sensitivity-run-count",
                str(args.min_grid_sensitivity_run_count),
                "--min-grid-refinement-ratio",
                str(args.min_grid_refinement_ratio),
                "--max-grid-rmse-change-ratio",
                str(args.max_grid_rmse_change_ratio),
                "--max-grid-bias-change-ratio",
                str(args.max_grid_bias_change_ratio),
            ]
            for metrics_item in args.grid_sensitivity_metrics:
                grid_cmd.extend(["--metrics", str(Path(metrics_item).expanduser().resolve())])
            grid_cmd.extend(["--metrics", str(metrics_csv)])
            manifest["Steps"].append(run_step("audit_grid_sensitivity", grid_cmd, allow_fail=True))
            write_manifest(manifest_path, manifest)

            metrics_with_grid_cmd = list(metrics_cmd)
            metrics_with_grid_cmd.extend(["--grid-sensitivity-audit", str(grid_sensitivity_json)])
            manifest["Steps"].append(run_step("validation_metrics_from_probe_audit_with_grid", metrics_with_grid_cmd))
            write_manifest(manifest_path, manifest)

        if args.paired_native_metrics:
            parity_cmd = [
                py,
                str(script_dir / "audit_native_citylbm_parity.py"),
                "--citylbm-metrics",
                str(metrics_csv),
                "--native-metrics",
                str(Path(args.paired_native_metrics).expanduser().resolve()),
                "--out",
                str(native_citylbm_parity_json),
                "--case",
                args.case,
                "--wind-direction",
                args.wind_direction_label,
                "--citylbm-software",
                args.software,
                "--native-software",
                "native-fluidx3d",
            ]
            manifest["Steps"].append(run_step("audit_native_citylbm_parity", parity_cmd, allow_fail=True))
            write_manifest(manifest_path, manifest)

            metrics_with_parity_cmd = list(metrics_cmd)
            if args.grid_sensitivity_metrics:
                metrics_with_parity_cmd.extend(["--grid-sensitivity-audit", str(grid_sensitivity_json)])
            metrics_with_parity_cmd.extend(["--native-citylbm-parity-audit", str(native_citylbm_parity_json)])
            manifest["Steps"].append(run_step("validation_metrics_from_probe_audit_with_native_citylbm_parity", metrics_with_parity_cmd))
            write_manifest(manifest_path, manifest)

        gate_cmd = [
            py,
            str(script_dir / "validation_gate.py"),
            str(run_dir),
            "--metrics",
            str(metrics_csv),
            "--probe-audit",
            str(probe_audit_csv),
            "--official",
            str(official),
            "--case",
            args.case,
            "--software",
            args.software,
            "--expected-vtk-pattern",
            args.pattern,
            "--min-avg-frames",
            str(args.min_avg_frames),
            "--min-avg-step-span",
            str(args.min_avg_step_span),
            "--max-mean-speed-stddev-ratio",
            str(args.max_mean_speed_stddev_ratio),
            "--max-point-speed-stddev-ratio",
            str(args.max_point_speed_stddev_ratio),
            "--max-u-bias-ratio",
            str(args.max_u_bias_ratio),
            "--max-u-rmse-ratio",
            str(args.max_u_rmse_ratio),
            "--min-u-r2",
            str(args.min_u_r2),
            "--min-slope",
            str(args.min_slope),
            "--max-slope",
            str(args.max_slope),
            "--max-intercept-abs",
            str(args.max_intercept_abs),
            "--max-k-bias-ratio",
            str(args.max_k_bias_ratio),
            "--max-empty-tunnel-u-bias-ratio",
            str(args.max_empty_tunnel_u_bias_ratio),
            "--max-empty-tunnel-k-bias-ratio",
            str(args.max_empty_tunnel_k_bias_ratio),
            "--max-official-coordinate-delta-m",
            str(args.max_official_coordinate_delta_m),
            "--max-probe-failure-fraction",
            str(args.max_probe_failure_fraction),
            "--max-frontal-blockage-ratio",
            str(args.max_frontal_blockage_ratio),
            "--max-estimated-mach",
            str(args.max_estimated_mach),
            "--min-lbm-tau",
            str(args.min_lbm_tau),
            "--max-lbm-tau",
            str(args.max_lbm_tau),
            "--max-paper-dx-m",
            str(args.max_paper_dx_m),
            "--min-grid-sensitivity-run-count",
            str(args.min_grid_sensitivity_run_count),
            "--min-grid-refinement-ratio",
            str(args.min_grid_refinement_ratio),
            "--max-grid-rmse-change-ratio",
            str(args.max_grid_rmse_change_ratio),
            "--max-grid-bias-change-ratio",
            str(args.max_grid_bias_change_ratio),
            "--expected-compared-component",
            args.compared_component,
            "--expected-uref",
            str(args.u_ref),
            "--expected-wind-vector",
            args.wind_vector,
            "--out",
            str(gate_json),
        ]
        if args.allow_velocity_only_inlet:
            gate_cmd.append("--allow-velocity-only-inlet")
        if args.allow_diagnostic:
            gate_cmd.append("--allow-diagnostic")
        # The final gate is the main diagnostic artifact. Keep the chain
        # manifest complete even when the gate fails, then return the gate code.
        gate_step = run_step("validation_gate", gate_cmd, allow_fail=True)
        manifest["Steps"].append(gate_step)

        gate_report = read_json(gate_json)
        gate_verdict = str(gate_report.get("verdict") or "").strip().upper()
        gate_failed = gate_verdict != "PASS"
        manifest["ValidationGateVerdict"] = gate_verdict or "unknown"
        manifest["PaperGrade"] = bool(gate_report.get("paper_grade")) if gate_report else False
        manifest["DiagnosticPriority"] = gate_report.get("diagnostic_priority", []) if gate_report else []
        manifest["ChainStatus"] = "diagnostic" if gate_failed and args.allow_diagnostic else ("pass" if not gate_failed else "fail")
        manifest["ExitCode"] = 0 if args.allow_diagnostic else gate_step["returncode"]
        write_manifest(manifest_path, manifest)
        return int(manifest["ExitCode"])

    except ChainError as exc:
        manifest["ChainStatus"] = "fail"
        manifest["FailedStep"] = exc.step
        manifest["ExitCode"] = exc.returncode
        write_manifest(manifest_path, manifest)
        print(str(exc), file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
