#!/usr/bin/env python3
"""Run the shortest repeatable CityLBM validation development loop.

The loop is deliberately staged:
1. generate or reuse current CityLBM codegen artifacts;
2. run no-CFD preflight gates;
3. plan, and optionally execute, a short native FluidX3D canary only when the
   diagnostic canary gate passes.

It is an optimization-speed tool, not a paper-grade validation shortcut.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

MIN_DEFAULT_OUTPUT_FREE_BYTES = 2 * 1024 * 1024 * 1024
DEV_RUNTIME_DEFAULTS: Dict[str, Any] = {
    "time_steps": 2000,
    "vtk_save_interval": 100,
    "vtk_save_start_step": 100,
    "expected_vtk_frame_count": 20,
    "average_last_n": 10,
    "min_vtk_frames": 10,
    "min_vtk_step_span": 900,
}
STARTUP_CANARY_RUNTIME_DEFAULTS: Dict[str, Any] = {
    "time_steps": 100,
    "vtk_save_interval": 100,
    "vtk_save_start_step": 100,
    "expected_vtk_frame_count": 1,
    "average_last_n": 1,
    "min_vtk_frames": 1,
    "min_vtk_step_span": 0,
}
CORRELATION_CANARY_RUNTIME_DEFAULTS: Dict[str, Any] = {
    "time_steps": 500,
    "vtk_save_interval": 100,
    "vtk_save_start_step": 100,
    "expected_vtk_frame_count": 5,
    "average_last_n": 5,
    "min_vtk_frames": 5,
    "min_vtk_step_span": 400,
    "diagnostic_canary_stg_update_interval": 5,
}
PAPER_RUNTIME_DEFAULTS: Dict[str, Any] = {
    "time_steps": 40000,
    "vtk_save_interval": 1000,
    "vtk_save_start_step": None,
    "expected_vtk_frame_count": 40,
    "average_last_n": 40,
    "min_vtk_frames": 40,
    "min_vtk_step_span": 20000,
}


CASE_PRESETS: Dict[str, Dict[str, Any]] = {
    "casea": {
        "default_case_name": "casea_full_reynolds_stress_tensor",
        "expected_aij_case": "CaseA",
        "expected_wind_direction": "N",
        "expected_wind_vector": "1,0,0",
        "expected_probe_row_count": 186,
        "z_ref": 0.16,
        "expected_uref": 4.491,
        "expected_probe_z_min": 0.01,
        "expected_probe_z_max": 0.28,
        "official_candidates": [
            "{repo}/releases/v0.2.0/package/examples/AIJ_CaseA/official_data/RS-caseA.csv",
            "{repo}/releases/v0.2.0/package/examples/AIJ_CaseA/official_data/RS_caseA.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/casea_v020_rerun_20260716/official_data/RS-caseA.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/native_fluidx3d_casea_strict_20260721/official_data/RS-caseA.csv",
        ],
        "af_candidates": [
            "{repo}/releases/v0.2.0/package/examples/AIJ_CaseA/official_data/AF_caseA.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/casea_v020_rerun_20260716/official_data/AF_caseA.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/native_fluidx3d_casea_strict_20260721/official_data/AF_caseA.csv",
        ],
    },
    "casee": {
        "default_case_name": "stg_full_reynolds_stress_tensor",
        "expected_aij_case": "CaseE",
        "expected_wind_direction": "N",
        "expected_wind_vector": "0,-1,0",
        "expected_probe_row_count": 80,
        "expected_probe_z": 2.0,
        "z_ref": 15.9,
        "expected_uref": 3.928296,
        "official_condition_filter": "ac",
        "official_wind_filter": "N",
        "official_candidates": [
            "{repo}/releases/v0.2.0/package/examples/AIJ_CaseE/official_data/RS_caseE.csv",
            "{workspace}/CityLBM_v0.2.0_Food4Rhino/package/examples/AIJ_CaseE/official_data/RS_caseE.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/[VERIFY]_AIJCASEE/official_data/RS_caseE.csv",
        ],
        "af_candidates": [
            "{repo}/releases/v0.2.0/package/examples/AIJ_CaseE/official_data/AF_caseE.csv",
            "{workspace}/CityLBM_v0.2.0_Food4Rhino/package/examples/AIJ_CaseE/official_data/AF_caseE.csv",
            "{workspace}/citylbm_v0.2.0_portable/validation/[VERIFY]_AIJCASEE/official_data/AF_caseE.csv",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-command preflight plus optional short native FluidX3D canary for CityLBM validation development."
    )
    parser.add_argument("--case", choices=sorted(CASE_PRESETS), default="casea")
    parser.add_argument("--case-name", default="", help="Defaults to the selected case preset's generated smoke case.")
    parser.add_argument(
        "--case-dir",
        default="",
        help="Existing CityLBM-generated case directory to audit directly instead of regenerating a temp CodegenSmoke case.",
    )
    parser.add_argument("--fluidx3d-source", required=True)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--official", default="")
    parser.add_argument("--af-csv", default="")
    parser.add_argument("--length-scale-source", default="", help="Optional official, precursor or calibrated length-scale source file.")
    parser.add_argument(
        "--length-scale-source-type",
        default="official_aij",
        choices=[
            "digital_filter_calibration",
            "literature",
            "official_aij",
            "precursor",
            "recycling",
            "sem_calibration",
            "synthetic_eddy_calibration",
            "wind_tunnel_document",
        ],
        help="Traceable source type for turbulence length-scale evidence.",
    )
    parser.add_argument("--length-scale-source-note", default="", help="Short length-scale evidence provenance note.")
    parser.add_argument("--length-scale-paper-admissible", action="store_true")
    parser.add_argument(
        "--strict-official-inputs",
        action="store_true",
        help="Require official probe/AF identity gates. Enabled automatically when --official or --af-csv is supplied.",
    )
    parser.add_argument(
        "--require-actual-geometry",
        action="store_true",
        help="Require non-smoke geometry before allowing a validation canary. Enabled automatically with strict official inputs.",
    )
    parser.add_argument("--quick", action="store_true", help="Reuse existing temp codegen case.")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-codegen", action="store_true")
    parser.add_argument(
        "--paper-defaults",
        action="store_true",
        help="Use the long paper-candidate averaging window defaults instead of the short development canary defaults.",
    )
    parser.add_argument(
        "--startup-canary",
        action="store_true",
        help="Use a one-frame solver-startup canary. This is faster than the development canary and is not accuracy evidence.",
    )
    parser.add_argument(
        "--correlation-canary",
        action="store_true",
        help="Use a five-frame inlet-correlation canary. This is still diagnostic, but can exercise VTK-based correlation audits.",
    )
    parser.add_argument("--time-steps", type=int, default=None)
    parser.add_argument("--vtk-save-interval", type=int, default=None)
    parser.add_argument("--vtk-save-start-step", type=int, default=None)
    parser.add_argument("--expected-vtk-frame-count", type=int, default=None)
    parser.add_argument("--average-last-n", type=int, default=None)
    parser.add_argument("--min-vtk-frames", type=int, default=None)
    parser.add_argument("--min-vtk-step-span", type=int, default=None)
    parser.add_argument(
        "--diagnostic-canary-stg-update-interval",
        type=int,
        default=None,
        help=(
            "Diagnostic-only override for citylbm_stg_update_interval in the short native canary. "
            "Used to test inlet refresh sensitivity without changing paper-default codegen."
        ),
    )
    parser.add_argument(
        "--diagnostic-canary-stg-intensity-scale",
        type=float,
        default=None,
        help=(
            "Diagnostic-only override for citylbm_stg_scale in the short native canary. "
            "Use for inlet energy sensitivity checks without changing CityLBM defaults."
        ),
    )
    parser.add_argument(
        "--diagnostic-canary-stg-temporal-step-scale",
        type=float,
        default=None,
        help=(
            "Diagnostic-only override for citylbm_stg_temporal_step_scale in the short native canary. "
            "Use for temporal-correlation sensitivity checks without changing CityLBM defaults."
        ),
    )
    parser.add_argument("--execute-canary", action="store_true", help="Actually install/build/run the short native canary.")
    parser.add_argument("--install-only", action="store_true", help="With --execute-canary, install case into FluidX3D only.")
    parser.add_argument("--canary-timeout-seconds", type=int, default=600)
    parser.add_argument("--canary-average-last-n", type=int, default=1)
    parser.add_argument("--canary-min-vtk-frames", type=int, default=1)
    parser.add_argument("--canary-min-vtk-step-span", type=int, default=0)
    parser.add_argument("--allow-diagnostic", action="store_true", help="Return 0 when paper gates remain diagnostic.")
    args = parser.parse_args()
    apply_runtime_defaults(args)
    return args


def apply_runtime_defaults(args: argparse.Namespace) -> None:
    selected_modes = [
        name
        for name, selected in [
            ("--paper-defaults", args.paper_defaults),
            ("--startup-canary", args.startup_canary),
            ("--correlation-canary", args.correlation_canary),
        ]
        if selected
    ]
    if len(selected_modes) > 1:
        raise SystemExit("Runtime default modes are mutually exclusive: " + ", ".join(selected_modes))
    if args.paper_defaults:
        defaults = PAPER_RUNTIME_DEFAULTS
        mode = "paper_candidate"
    elif args.startup_canary:
        defaults = STARTUP_CANARY_RUNTIME_DEFAULTS
        mode = "startup_canary"
    elif args.correlation_canary:
        defaults = CORRELATION_CANARY_RUNTIME_DEFAULTS
        mode = "correlation_canary"
    else:
        defaults = DEV_RUNTIME_DEFAULTS
        mode = "development_canary"
    for key, value in defaults.items():
        if getattr(args, key) is None:
            setattr(args, key, value)
    if args.diagnostic_canary_stg_update_interval is not None and args.diagnostic_canary_stg_update_interval <= 0:
        raise SystemExit("--diagnostic-canary-stg-update-interval must be positive")
    if args.diagnostic_canary_stg_intensity_scale is not None and args.diagnostic_canary_stg_intensity_scale <= 0.0:
        raise SystemExit("--diagnostic-canary-stg-intensity-scale must be positive")
    if (
        args.diagnostic_canary_stg_temporal_step_scale is not None
        and args.diagnostic_canary_stg_temporal_step_scale <= 0.0
    ):
        raise SystemExit("--diagnostic-canary-stg-temporal-step-scale must be positive")
    args.runtime_default_mode = mode


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def disk_free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    return int(shutil.disk_usage(str(probe)).free)


def default_out_dir(repo: Path, case: str, stamp: str, min_free_bytes: int = MIN_DEFAULT_OUTPUT_FREE_BYTES) -> tuple[Path, Dict[str, Any]]:
    repo_free = disk_free_bytes(repo)
    name = f"{case}_dev_loop_{stamp}"
    if repo_free >= min_free_bytes:
        return repo / "validation_runs" / name, {
            "Mode": "repo_validation_runs",
            "RepoFreeBytes": repo_free,
            "MinDefaultOutputFreeBytes": min_free_bytes,
        }
    return Path(tempfile.gettempdir()) / "CityLBM_validation_runs" / name, {
        "Mode": "temp_due_to_low_repo_disk_free",
        "RepoFreeBytes": repo_free,
        "MinDefaultOutputFreeBytes": min_free_bytes,
        "TempRoot": tempfile.gettempdir(),
    }


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def run_step(name: str, cmd: Sequence[str], cwd: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        list(cmd),
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "Name": name,
        "Command": list(cmd),
        "ReturnCode": completed.returncode,
        "Stdout": completed.stdout,
        "Stderr": completed.stderr,
    }


def add_optional(command: List[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text:
        command.extend([flag, text])


def resolve_candidate_path(repo: Path, template: str) -> Path:
    workspace = repo.parent
    text = template.replace("{repo}", str(repo)).replace("{workspace}", str(workspace))
    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        candidate = repo / candidate
    return candidate.resolve()


def first_existing_candidate(repo: Path, candidates: Sequence[str]) -> Tuple[str, str]:
    for template in candidates:
        candidate = resolve_candidate_path(repo, template)
        if candidate.is_file():
            return str(candidate), template
    return "", ""


def resolve_official_input_paths(
    args: argparse.Namespace, repo: Path, preset: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    official_source = "none"
    af_source = "none"
    official_template = ""
    af_template = ""
    if args.official.strip():
        official_path = str(Path(args.official).expanduser().resolve())
        official_source = "cli"
    else:
        official_path, official_template = first_existing_candidate(repo, preset.get("official_candidates", []))
        if official_path:
            official_source = "auto_candidate"
    if args.af_csv.strip():
        af_path = str(Path(args.af_csv).expanduser().resolve())
        af_source = "cli"
    else:
        af_path, af_template = first_existing_candidate(repo, preset.get("af_candidates", []))
        if af_path:
            af_source = "auto_candidate"
    return official_path, af_path, {
        "OfficialPath": official_path,
        "OfficialSource": official_source,
        "OfficialCandidateTemplate": official_template,
        "AfCsvPath": af_path,
        "AfCsvSource": af_source,
        "AfCsvCandidateTemplate": af_template,
    }


def gate_value(report: Dict[str, Any], key: str) -> str:
    value = report.get(key)
    if isinstance(value, dict):
        value = value.get("Gate") or value.get("gate")
    return str(value or "").strip().lower()


def report_gate(report: Dict[str, Any]) -> str:
    for key in ["Gate", "gate", "inlet_correlation_gate", "inlet_diagnostics_csv_gate"]:
        value = report.get(key)
        if isinstance(value, dict):
            value = value.get("Gate") or value.get("gate")
        if value is not None:
            return str(value).strip().lower()
    return ""


def suggested_commands(manifest: Dict[str, Any], names: Sequence[str]) -> List[Tuple[str, List[str]]]:
    triage = manifest.get("DevelopmentTriage") if isinstance(manifest.get("DevelopmentTriage"), dict) else {}
    commands = triage.get("SuggestedCommands") if isinstance(triage.get("SuggestedCommands"), list) else []
    wanted = set(names)
    selected: List[Tuple[str, List[str]]] = []
    for item in commands:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "")
        command = item.get("Command")
        if name in wanted and isinstance(command, list) and all(isinstance(part, str) for part in command):
            selected.append((name, list(command)))
    return selected


def command_option(command: Sequence[str], flag: str) -> str:
    try:
        index = list(command).index(flag)
    except ValueError:
        return ""
    if index + 1 >= len(command):
        return ""
    return str(command[index + 1]).strip()


def post_canary_runtime_gate(post_canary_audits: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    required = {
        "audit_runtime_inlet_diagnostics_after_canary",
        "audit_inlet_correlation_after_canary",
    }
    seen: Dict[str, str] = {}
    for audit in post_canary_audits:
        name = str(audit.get("Name") or "")
        if name in required:
            seen[name] = str(audit.get("Gate") or "").strip().lower()
    missing = sorted(required.difference(seen))
    failed = [f"{name}:{gate or 'missing'}" for name, gate in seen.items() if gate != "pass"]
    reasons = [f"missing:{name}" for name in missing] + [f"not_pass:{item}" for item in failed]
    return {
        "Gate": "pass" if not reasons else "fail",
        "RequiredAudits": sorted(required),
        "ObservedAudits": seen,
        "Reasons": reasons,
    }


def build_loop_next_optimization_target(
    preflight_pack: Dict[str, Any],
    post_canary_audits: Sequence[Dict[str, Any]],
    codegen_manifest: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    codegen = codegen_manifest if isinstance(codegen_manifest, dict) else {}
    geometry_gate = codegen.get("ActualValidationGeometryGate")
    if isinstance(geometry_gate, dict) and geometry_gate.get("Required") and str(geometry_gate.get("Gate") or "").lower() != "pass":
        return {
            "Schema": "citylbm.validation_dev_loop_next_target.v1",
            "Key": "actual_validation_geometry_missing",
            "Rank": 0,
            "Reasons": list(geometry_gate.get("Reasons") or []),
            "Diagnosis": "The selected AIJ validation route is still using a smoke or missing geometry case, so CFD accuracy would be meaningless.",
            "NextAction": "Generate the case from the actual AIJ geometry in Rhino/Grasshopper, then rerun this dev loop before launching FluidX3D.",
            "RequiredExperiment": "actual_aij_geometry_codegen_preflight_first",
            "DiagnosticCanaryGate": "blocked_by_actual_geometry_gate",
            "ShortDiagnosticCanaryAllowed": False,
            "AccuracyInterpretationAllowed": False,
            "AccuracyInterpretationGate": "fail",
            "ActualValidationGeometryGate": geometry_gate,
            "ShortRuntimeCanaryEvidenceGate": post_canary_runtime_gate(post_canary_audits),
            "ShortRuntimeCanaryInterpretation": "No runtime canary should be executed until the actual AIJ geometry gate passes.",
        }
    route_gate = str(codegen.get("ShortCanaryRouteCheckGate") or "").strip().lower()
    if route_gate and route_gate != "pass":
        route_reasons = [
            str(reason)
            for reason in codegen.get("Reasons", [])
            if str(reason).startswith("short_canary_route_check")
        ]
        return {
            "Schema": "citylbm.validation_dev_loop_next_target.v1",
            "Key": "current_codegen_route_required",
            "Rank": 1,
            "Reasons": route_reasons,
            "Diagnosis": (
                "The selected case geometry may be valid, but setup.cpp/metadata do not follow the current "
                "CityLBM validation route, so inlet turbulence diagnostics and native canary evidence would be stale."
            ),
            "NextAction": (
                "Regenerate the explicit AIJ case with the current CityLBM source so setup.cpp includes runtime "
                "inlet diagnostics, current STG route metadata, and source-audit markers; then rerun the no-CFD preflight."
            ),
            "RequiredExperiment": "current_citylbm_codegen_for_existing_aij_geometry",
            "DiagnosticCanaryGate": "blocked_by_stale_or_incomplete_codegen_route",
            "ShortDiagnosticCanaryAllowed": False,
            "AccuracyInterpretationAllowed": False,
            "AccuracyInterpretationGate": "fail",
            "ActualValidationGeometryGate": geometry_gate,
            "ShortCanaryRouteCheckGate": route_gate,
            "ShortRuntimeCanaryEvidenceGate": post_canary_runtime_gate(post_canary_audits),
            "ShortRuntimeCanaryInterpretation": "No runtime canary should be executed until the source-route gate passes.",
        }
    target = preflight_pack.get("NextOptimizationTarget")
    if not isinstance(target, dict) or not target:
        triage = preflight_pack.get("DevelopmentTriage") if isinstance(preflight_pack.get("DevelopmentTriage"), dict) else {}
        target = triage.get("NextOptimizationTarget") if isinstance(triage.get("NextOptimizationTarget"), dict) else {}
    result = dict(target) if isinstance(target, dict) else {}
    if not result:
        result = {
            "Schema": "citylbm.validation_dev_loop_next_target.v1",
            "Key": "preflight_next_target_missing",
            "Diagnosis": "Native preflight did not expose a next optimization target.",
            "NextAction": "Fix run_native_preflight_pack.py or native_preconditions_audit generation before interpreting CFD.",
        }
    result["Schema"] = "citylbm.validation_dev_loop_next_target.v1"
    runtime_gate = post_canary_runtime_gate(post_canary_audits)
    result["ShortRuntimeCanaryEvidenceGate"] = runtime_gate
    if post_canary_audits and runtime_gate["Gate"] == "pass" and result.get("Key") == "turbulent_inlet_method_and_u_k_preservation":
        result["ShortRuntimeCanaryInterpretation"] = (
            "The diagnostic canary preserved inlet U/k/TKE/correlation in the sampled VTK window; "
            "the remaining inlet blocker is paper-grade inlet provenance, length scale, Reynolds stress or precursor evidence."
        )
        result["NextAction"] = (
            "Bind paper-admissible turbulent length-scale and Reynolds-stress/precursor evidence, then run a paper-length "
            "empty-tunnel inlet preservation case before interpreting Case A/E probe accuracy."
        )
        result["RequiredExperiment"] = "paper_length_empty_tunnel_inlet_preservation_with_bound_inlet_evidence"
    elif post_canary_audits and runtime_gate["Gate"] != "pass":
        result["ShortRuntimeCanaryInterpretation"] = (
            "The diagnostic canary did not close inlet runtime preservation; fix the generated setup/native boundary route before longer runs."
        )
        result["NextAction"] = "Fix the failing post-canary inlet diagnostics before spending time on long CFD."
    else:
        result["ShortRuntimeCanaryInterpretation"] = "No executed short runtime canary evidence is attached to this dev-loop manifest."
    return result


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[1]
    preset = CASE_PRESETS[args.case]
    case_name = args.case_name.strip() or str(preset["default_case_name"])
    official_path, af_csv_path, official_resolution = resolve_official_input_paths(args, repo, preset)
    strict_official_inputs = bool(args.strict_official_inputs or official_path or af_csv_path)
    require_actual_geometry = bool(args.require_actual_geometry or strict_official_inputs)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_placement: Dict[str, Any]
    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser().resolve()
        output_placement = {"Mode": "explicit_out_dir"}
    else:
        out_dir, output_placement = default_out_dir(repo, args.case, stamp)
    out_dir.mkdir(parents=True, exist_ok=True)
    codegen_manifest = out_dir / "codegen_preflight_canary_manifest.json"
    native_canary_manifest = out_dir / "native_short_canary_manifest.json"
    loop_manifest = out_dir / "validation_dev_loop_manifest.json"

    py = sys.executable
    codegen_cmd = [
        py,
        str(repo / "scripts" / "run_codegen_preflight_canary.py"),
        "--case-name",
        case_name,
        "--fluidx3d-source",
        str(Path(args.fluidx3d_source).expanduser().resolve()),
        "--out-dir",
        str(out_dir),
        "--manifest-out",
        str(codegen_manifest),
        "--expected-aij-case",
        preset["expected_aij_case"],
        "--expected-wind-direction",
        preset["expected_wind_direction"],
        "--expected-wind-vector",
        preset["expected_wind_vector"],
        "--time-steps",
        str(args.time_steps),
        "--vtk-save-interval",
        str(args.vtk_save_interval),
        "--expected-vtk-frame-count",
        str(args.expected_vtk_frame_count),
        "--average-last-n",
        str(args.average_last_n),
        "--min-vtk-frames",
        str(args.min_vtk_frames),
        "--min-vtk-step-span",
        str(args.min_vtk_step_span),
        "--allow-diagnostic",
    ]
    add_optional(codegen_cmd, "--case-dir", args.case_dir)
    add_optional(codegen_cmd, "--official", official_path)
    add_optional(codegen_cmd, "--af-csv", af_csv_path)
    add_optional(codegen_cmd, "--official-condition-filter", preset.get("official_condition_filter"))
    add_optional(codegen_cmd, "--official-wind-filter", preset.get("official_wind_filter"))
    add_optional(codegen_cmd, "--length-scale-source", args.length_scale_source)
    add_optional(codegen_cmd, "--length-scale-source-type", args.length_scale_source_type)
    add_optional(codegen_cmd, "--length-scale-source-note", args.length_scale_source_note)
    add_optional(codegen_cmd, "--vtk-save-start-step", args.vtk_save_start_step)
    add_optional(codegen_cmd, "--diagnostic-canary-stg-update-interval", args.diagnostic_canary_stg_update_interval)
    add_optional(codegen_cmd, "--diagnostic-canary-stg-intensity-scale", args.diagnostic_canary_stg_intensity_scale)
    add_optional(
        codegen_cmd,
        "--diagnostic-canary-stg-temporal-step-scale",
        args.diagnostic_canary_stg_temporal_step_scale,
    )
    if strict_official_inputs:
        codegen_cmd.extend(["--expected-probe-row-count", str(preset["expected_probe_row_count"])])
        codegen_cmd.extend(["--z-ref", str(preset["z_ref"])])
        codegen_cmd.extend(["--expected-uref", str(preset["expected_uref"])])
        codegen_cmd.append("--require-af-k")
    if require_actual_geometry:
        codegen_cmd.append("--require-actual-geometry")
        add_optional(codegen_cmd, "--expected-probe-z", preset.get("expected_probe_z"))
        add_optional(codegen_cmd, "--expected-probe-z-min", preset.get("expected_probe_z_min"))
        add_optional(codegen_cmd, "--expected-probe-z-max", preset.get("expected_probe_z_max"))
    if args.quick:
        codegen_cmd.append("--quick")
    if args.skip_build:
        codegen_cmd.append("--skip-build")
    if args.skip_codegen:
        codegen_cmd.append("--skip-codegen")
    if args.length_scale_paper_admissible:
        codegen_cmd.append("--length-scale-paper-admissible")

    steps: List[Dict[str, Any]] = [run_step("codegen_preflight_canary", codegen_cmd, repo)]
    codegen = read_json(codegen_manifest)
    preflight_pack = read_json(Path(str(codegen.get("NativePreflightPackManifest") or "")))
    diagnostic_canary_ready = gate_value(codegen, "DiagnosticCanaryGate") == "pass"

    canary_cmd: List[str] = []
    if diagnostic_canary_ready:
        canary_cmd = [
            py,
            str(repo / "scripts" / "run_native_canary_from_codegen_manifest.py"),
            "--codegen-manifest",
            str(codegen_manifest),
            "--out-dir",
            str(out_dir / "native_short_canary"),
            "--manifest-out",
            str(native_canary_manifest),
            "--timeout-seconds",
            str(args.canary_timeout_seconds),
            "--time-steps",
            str(args.time_steps),
            "--vtk-save-interval",
            str(args.vtk_save_interval),
            "--expected-vtk-frame-count",
            str(args.expected_vtk_frame_count),
            "--average-last-n",
            str(args.average_last_n),
            "--min-vtk-frames",
            str(args.min_vtk_frames),
            "--min-vtk-step-span",
            str(args.min_vtk_step_span),
        ]
        if args.execute_canary:
            canary_cmd.append("--execute")
        if args.install_only:
            canary_cmd.append("--install-only")
        steps.append(run_step("native_short_canary_plan_or_execute", canary_cmd, repo))

    native_canary = read_json(native_canary_manifest)
    post_canary_audits: List[Dict[str, Any]] = []
    if args.execute_canary and native_canary and gate_value(native_canary, "Gate") == "pass":
        for audit_name, audit_cmd in suggested_commands(
            preflight_pack,
            ["audit_runtime_inlet_diagnostics_after_canary", "audit_inlet_correlation_after_canary"],
        ):
            audit_step = run_step(audit_name, audit_cmd, repo)
            audit_step["NonBlockingDiagnostic"] = True
            steps.append(audit_step)
            audit_manifest_path = command_option(audit_cmd, "--out-json")
            audit_manifest = read_json(Path(audit_manifest_path)) if audit_manifest_path else {}
            post_canary_audits.append(
                {
                    "Name": audit_name,
                    "ReturnCode": audit_step["ReturnCode"],
                    "Manifest": audit_manifest_path,
                    "Gate": report_gate(audit_manifest),
                    "Reasons": audit_manifest.get("Reasons")
                    or audit_manifest.get("inlet_correlation_gate_reasons")
                    or audit_manifest.get("reasons")
                    or [],
                }
            )
    reasons: List[str] = []
    for step in steps:
        if step.get("NonBlockingDiagnostic"):
            continue
        if int(step["ReturnCode"]) not in {0, 2}:
            reasons.append(f"step_failed:{step['Name']}:{step['ReturnCode']}")
    if not diagnostic_canary_ready:
        reasons.append(f"diagnostic_canary_gate_not_pass:{gate_value(codegen, 'DiagnosticCanaryGate') or 'missing'}")
    if args.execute_canary and native_canary and gate_value(native_canary, "Gate") != "pass":
        reasons.append(f"native_short_canary_not_pass:{gate_value(native_canary, 'Gate') or 'missing'}")
    runtime_canary_evidence_gate = post_canary_runtime_gate(post_canary_audits)
    if (
        args.execute_canary
        and native_canary
        and gate_value(native_canary, "Gate") == "pass"
        and not args.startup_canary
        and runtime_canary_evidence_gate["Gate"] != "pass"
    ):
        reasons.append(f"post_canary_runtime_evidence_not_pass:{runtime_canary_evidence_gate['Gate']}")

    loop = {
        "Schema": "citylbm.validation_dev_loop.v1",
        "GeneratedAtUtc": utc_now(),
        "Purpose": "shorten_development_by_chaining_codegen_preflight_and_optional_short_native_canary",
        "Case": args.case,
        "CaseName": case_name,
        "OutDir": str(out_dir),
        "OutputPlacement": output_placement,
        "RuntimeDefaultMode": args.runtime_default_mode,
        "Gate": "pass" if not reasons else "diagnostic_only",
        "Reasons": list(dict.fromkeys(reasons)),
        "DiagnosticCanaryReady": diagnostic_canary_ready,
        "ExecutedCanary": bool(args.execute_canary),
        "StrictOfficialInputs": strict_official_inputs,
        "RequireActualGeometry": require_actual_geometry,
        "OfficialInputResolution": official_resolution,
        "LengthScaleEvidencePlan": {
            "Source": str(args.length_scale_source or "").strip(),
            "SourceType": args.length_scale_source_type,
            "SourceNote": str(args.length_scale_source_note or "").strip(),
            "PaperAdmissible": bool(args.length_scale_paper_admissible),
        },
        "TimeAveragingPlan": {
            "TimeSteps": args.time_steps,
            "VtkSaveInterval": args.vtk_save_interval,
            "VtkSaveStartStep": args.vtk_save_start_step,
            "ExpectedVtkFrameCount": args.expected_vtk_frame_count,
            "AverageLastN": args.average_last_n,
            "MinimumVtkFrames": args.min_vtk_frames,
            "MinimumStepSpan": args.min_vtk_step_span,
        },
        "DiagnosticCanaryPlan": {
            "SyntheticTurbulenceUpdateInterval": args.diagnostic_canary_stg_update_interval,
            "SyntheticTurbulenceIntensityScale": args.diagnostic_canary_stg_intensity_scale,
            "SyntheticTurbulenceTemporalStepScale": args.diagnostic_canary_stg_temporal_step_scale,
            "ExpectedFinalWindowRefreshCount": (
                None
                if args.diagnostic_canary_stg_update_interval in (None, 0)
                else args.min_vtk_step_span // args.diagnostic_canary_stg_update_interval
            ),
        },
        "Artifacts": {
            "CodegenManifest": str(codegen_manifest),
            "NativePreflightPackManifest": str(codegen.get("NativePreflightPackManifest") or ""),
            "NativeCanaryManifest": str(native_canary_manifest) if native_canary_manifest.exists() else "",
        },
        "PostCanaryAudits": post_canary_audits,
        "NextOptimizationTarget": build_loop_next_optimization_target(preflight_pack, post_canary_audits, codegen),
        "NextAction": (
            "Use PostCanaryAudits to pick the next source-level fix; do not use the short canary as paper accuracy evidence."
            if args.execute_canary and native_canary and gate_value(native_canary, "Gate") == "pass"
            else (
                "Run the same command with --execute-canary for a short native FluidX3D runtime check."
                if diagnostic_canary_ready and not args.execute_canary
                else "Fix the listed preflight reasons before running FluidX3D."
            )
        ),
        "Steps": steps,
    }
    write_json(loop_manifest, loop)
    print(f"validation_dev_loop_gate={loop['Gate']}; manifest={loop_manifest}")
    print(f"out_dir={out_dir}")
    print(f"output_placement={output_placement.get('Mode', '')}")
    print(f"diagnostic_canary_ready={str(diagnostic_canary_ready).lower()}")
    print("next_action=" + loop["NextAction"])
    return 0 if loop["Gate"] == "pass" or args.allow_diagnostic else 2


if __name__ == "__main__":
    raise SystemExit(main())
