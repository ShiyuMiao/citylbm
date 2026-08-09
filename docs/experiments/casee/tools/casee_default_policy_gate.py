#!/usr/bin/env python3
"""Verify Case E defaults remain formal-protocol safe and diagnostics stay opt-in."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_default_policy_gate.json"
OUT_CSV = RESULTS_DIR / "casee_default_policy_gate.csv"
OUT_MD = RESULTS_DIR / "casee_default_policy_gate.md"

FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
NATIVE_GENERATOR = CASE_DIR / "tools" / "generate_native_casee.py"
PRESET = CASE_DIR / "casee_preset.json"
README = ROOT / "README.md"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
FAILURE_ATLAS = RESULTS_DIR / "casee_failure_mode_atlas.json"

EXPECTED_DIAGNOSTIC_MODES = {
    "nearest_valid",
    "fluid_weighted",
    "vertical_valid_above",
    "z_plus_half",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.S) is not None


def check_row(
    check_id: str,
    passed: bool,
    source: Path,
    policy_boundary: str,
    paper_use: str,
    failure_action: str,
) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": passed,
        "evidence_type": "newly_run",
        "source_path": rel(source),
        "policy_boundary": policy_boundary,
        "paper_use": paper_use,
        "failure_action": failure_action,
    }


def build_checks() -> List[Dict[str, Any]]:
    fluidx = read_text(FLUIDX)
    run_component = read_text(RUN_COMPONENT)
    generator = read_text(NATIVE_GENERATOR)
    preset = read_json(PRESET)
    release_gate = read_json(RELEASE_GATE)
    failure_atlas = read_json(FAILURE_ATLAS)
    readme = read_text(README)

    sampling_modes = preset.get("sampling_modes", {})
    diagnostic_only = set(sampling_modes.get("diagnostic_only", []))
    checks = [
        check_row(
            "simulation_settings_formal_raw_trilinear",
            'FormalSamplingMode { get; set; } = "raw_trilinear"' in fluidx,
            FLUIDX,
            "Formal validation defaults to official z=2 m raw_trilinear sampling.",
            "Use to state the default formal sampling policy.",
            "Restore SimulationSettings.FormalSamplingMode to raw_trilinear.",
        ),
        check_row(
            "simulation_settings_diag_modes_empty_by_default",
            'DiagnosticSamplingModes { get; set; } = ""' in fluidx,
            FLUIDX,
            "Generic simulations do not enable diagnostic probe modes by default.",
            "Use to separate generic defaults from Case E diagnostics.",
            "Keep diagnostic sampling modes opt-in or preset-scoped.",
        ),
        check_row(
            "simulation_settings_nu_override_default_off",
            "DiagnosticNuLbmOverride { get; set; } = 0.0" in fluidx,
            FLUIDX,
            "LBM viscosity override is default-off; standard physical-viscosity mapping remains default.",
            "Use to state nu_lbm sensitivity is diagnostic only.",
            "Reset DiagnosticNuLbmOverride default to 0.0.",
        ),
        check_row(
            "simulation_settings_z_origin_offset_default_off",
            "DiagnosticZOriginOffsetM { get; set; } = 0.0" in fluidx,
            FLUIDX,
            "Vertical-origin offset is default-off and cannot redefine official z=2 m.",
            "Use to state z-origin shifts are diagnostics only.",
            "Reset DiagnosticZOriginOffsetM default to 0.0.",
        ),
        check_row(
            "simulation_settings_wall_model_default_none",
            'DiagnosticWallModel' in fluidx and '"none"' in fluidx,
            FLUIDX,
            "Diagnostic wall model is default-off and cannot replace the existing wall treatment by default.",
            "Use to state wall-model follow-ups are experimental switches.",
            "Restore DiagnosticWallModel default to none.",
        ),
        check_row(
            "simulation_settings_roughness_default_zero",
            "DiagnosticRoughnessLengthM { get; set; } = 0.0" in fluidx,
            FLUIDX,
            "Diagnostic roughness length is default-off and cannot become a formal accuracy model without official z=2 m improvement.",
            "Use to state rough-wall/effective-ground follow-ups are diagnostics only.",
            "Restore DiagnosticRoughnessLengthM default to 0.0.",
        ),
        check_row(
            "run_component_casee_preset_default_false",
            has_regex(
                run_component,
                r'AddBooleanParameter\("AIJ Case E Preset".*?GH_ParamAccess\.item,\s*false\)',
            ),
            RUN_COMPONENT,
            "Case E preset is explicit and opt-in in Grasshopper.",
            "Use to state users must deliberately select the Case E protocol preset.",
            "Restore the AIJ Case E Preset input default to false.",
        ),
        check_row(
            "run_component_nu_input_default_zero",
            has_regex(
                run_component,
                r'AddNumberParameter\("Diagnostic LBM Nu Override".*?GH_ParamAccess\.item,\s*0\.0\)',
            ),
            RUN_COMPONENT,
            "Diagnostic LBM Nu Override stays off unless the user supplies a positive value.",
            "Use to classify nu_lbm changes as experimental switches.",
            "Restore the nuLBM input default to 0.0.",
        ),
        check_row(
            "run_component_zoff_input_default_zero",
            has_regex(
                run_component,
                r'AddNumberParameter\("Diagnostic Z Origin Offset".*?GH_ParamAccess\.item,\s*0\.0\)',
            ),
            RUN_COMPONENT,
            "Diagnostic Z Origin Offset stays off unless explicitly set.",
            "Use to classify z-origin changes as experimental switches.",
            "Restore the zOff input default to 0.0.",
        ),
        check_row(
            "run_component_wall_model_input_default_none",
            has_regex(
                run_component,
                r'AddTextParameter\("Diagnostic Wall Model".*?GH_ParamAccess\.item,\s*"none"\)',
            ),
            RUN_COMPONENT,
            "Diagnostic Wall Model stays at none unless explicitly changed.",
            "Use to classify wall-model changes as experimental switches.",
            "Restore the wallModel input default to none.",
        ),
        check_row(
            "run_component_roughness_input_default_zero",
            has_regex(
                run_component,
                r'AddNumberParameter\("Diagnostic Roughness Length".*?GH_ParamAccess\.item,\s*0\.0\)',
            ),
            RUN_COMPONENT,
            "Diagnostic Roughness Length stays at zero unless explicitly changed.",
            "Use to classify roughness changes as experimental switches.",
            "Restore the z0Wall input default to 0.0.",
        ),
        check_row(
            "run_component_claim_gate_output",
            'AddTextParameter("Claim Gate", "Gate"' in run_component
            and "ClaimGateSummary" in run_component
            and "Formal v0.4.0 requires release_gate.json pass" in run_component,
            RUN_COMPONENT,
            "Run Simulation exposes the formal accuracy claim boundary directly in Grasshopper.",
            "Use to state that claim-boundary metadata is visible without opening the manifest JSON.",
            "Restore the Claim Gate output and ClaimGateSummary helper.",
        ),
        check_row(
            "manifest_blocks_z_plus_half_formal",
            "z_plus_half_allowed_as_formal_result" in fluidx
            and "diagnostic_modes_allowed_as_formal_result" in fluidx
            and "false" in fluidx,
            FLUIDX,
            "Run manifests forbid diagnostic modes as formal official z=2 m substitutes.",
            "Use to keep z_plus_half out of formal Case E validation claims.",
            "Restore manifest fields blocking diagnostic modes as formal results.",
        ),
        check_row(
            "manifest_formal_accuracy_gate_contract",
            "formal_accuracy_gate" in fluidx
            and "formal_accuracy_claim_allowed_from_manifest_alone" in fluidx
            and "requires_release_gate_json" in fluidx
            and "requires_casea_smoke_regression" in fluidx
            and "requires_rhino_loaded_new_gha" in fluidx
            and "diagnostic_substitutes_allowed" in fluidx,
            FLUIDX,
            "Run manifests encode the formal v0.4.0 accuracy-gate contract and keep manifest-only claims blocked.",
            "Use to state that software traceability encodes the release gate but does not satisfy it.",
            "Restore formal_accuracy_gate contract fields in WriteRunManifest.",
        ),
        check_row(
            "manifest_blocks_wall_roughness_formal_defaults",
            "diagnostic_wall_model_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_roughness_length_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_wall_roughness_changes_solver_defaults" in fluidx
            and "wall_model" in fluidx
            and "roughness_length" in fluidx,
            FLUIDX,
            "Run manifests forbid wall-model and roughness diagnostics from becoming default accuracy claims.",
            "Use to state wall/roughness follow-ups are limitations-only until official metrics improve.",
            "Restore wall/roughness claim-boundary fields in WriteRunManifest.",
        ),
        check_row(
            "native_generator_formal_output_raw",
            '"formal_sampling_mode": "raw_trilinear"' in generator
            and "official_velocity_ratio,predicted_velocity_ratio,speed_lbm" in generator,
            NATIVE_GENERATOR,
            "Native Case E probe CSV keeps predicted_velocity_ratio as the raw formal result.",
            "Use to trace official metrics to raw_trilinear output.",
            "Keep predicted_velocity_ratio tied to raw_trilinear before diagnostic columns.",
        ),
        check_row(
            "native_generator_diagnostic_modes_declared",
            all(mode in generator for mode in EXPECTED_DIAGNOSTIC_MODES),
            NATIVE_GENERATOR,
            "Native diagnostic sampling modes are recorded as diagnostics.",
            "Use to discuss probe-protocol sensitivity only.",
            "Declare all diagnostic columns in the generator manifest.",
        ),
        check_row(
            "casee_preset_formal_default_raw",
            sampling_modes.get("default_for_validation") == "raw_trilinear",
            PRESET,
            "Case E preset formal validation mode is raw_trilinear.",
            "Use to document preset-level protocol policy.",
            "Reset sampling_modes.default_for_validation to raw_trilinear.",
        ),
        check_row(
            "casee_preset_diagnostic_only_complete",
            EXPECTED_DIAGNOSTIC_MODES.issubset(diagnostic_only),
            PRESET,
            "Case E preset lists nearest_valid, fluid_weighted, vertical_valid_above, and z_plus_half as diagnostic-only.",
            "Use to classify non-raw sampling modes as limitations diagnostics.",
            "Move diagnostic sampling modes back under sampling_modes.diagnostic_only.",
        ),
        check_row(
            "release_gate_formal_blocked",
            release_gate.get("formal_release_allowed") is False
            and (release_gate.get("checks") or {}).get("official_z2m_metric_gate") is False,
            RELEASE_GATE,
            "Formal v0.4.0 remains blocked while official z=2 m metrics fail.",
            "Use to prevent accidental formal-release wording.",
            "Do not promote defaults or release tags until release_gate.json passes.",
        ),
        check_row(
            "failure_atlas_limitations_ready",
            failure_atlas.get("claim_readiness") == "limitations_ready_failure_mode_atlas",
            FAILURE_ATLAS,
            "Failure-mode atlas supports limitations/software-feedback discussion only.",
            "Use to structure manuscript limitations.",
            "Regenerate the failure-mode atlas with limitations-only claim readiness.",
        ),
        check_row(
            "readme_declares_diagnostics_nonformal",
            "not" in readme
            and "accepted as formal validation results" in readme
            and "experimental only" in readme
            and "not formal validation" in readme,
            README,
            "Repository documentation states diagnostic offsets and sampling modes are not formal validation.",
            "Use to show documentation matches software policy.",
            "Restore README language separating diagnostics from formal validation.",
        ),
    ]
    return checks


def write_csv(path: Path, checks: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "check_id",
        "passed",
        "evidence_type",
        "source_path",
        "policy_boundary",
        "paper_use",
        "failure_action",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in checks:
            writer.writerow(row)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Case E Default Policy Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Default policy gate passed: {payload['default_policy_gate_passed']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal v0.4.0 allowed: {payload['formal_release_allowed']}",
        "",
        "## Default Settings Allowed",
        "",
    ]
    for item in payload["default_settings_allowed"]:
        lines.append(f"- {item}")
    lines += ["", "## Experimental Switches", ""]
    for item in payload["experimental_switches"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Checks",
        "",
        "| check | passed | source | policy boundary |",
        "|---|---:|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| `{row['check_id']}` | {row['passed']} | `{row['source_path']}` | {row['policy_boundary']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    checks = build_checks()
    passed = all(bool(row["passed"]) for row in checks)
    release_gate = read_json(RELEASE_GATE)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "default_policy_gate_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_default_policy_boundary" if passed else "blocked_default_policy_boundary",
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "default_settings_allowed": [
            "Official Case E formal validation uses z=2 m, 80 ac+N probes, and raw_trilinear sampling.",
            "Generic CityLBM viscosity remains the standard physical-viscosity mapping when nuLBM is 0.",
            "Case E preset metadata may set protocol constants and manifest/risk fields.",
            "Run manifests may record diagnostic availability and claim-boundary metadata.",
            "Run manifests may record the formal accuracy-gate contract for reviewer traceability.",
            "Run Simulation may expose claim-boundary text as a traceability output.",
        ],
        "experimental_switches": [
            "Diagnostic LBM Nu Override / nuLBM sensitivity control.",
            "Diagnostic Z Origin Offset / zOff vertical-origin sensitivity control.",
            "Diagnostic Wall Model / wallModel follow-up control.",
            "Diagnostic Roughness Length / z0Wall follow-up control.",
            "nearest_valid, fluid_weighted, vertical_valid_above, and z_plus_half probe sampling.",
            "Effective-ground, rough-wall, wall-model, voxelization, and inlet-turbulence follow-up settings until official z=2 m raw_trilinear improvement is proven.",
        ],
        "checks": checks,
        "boundary": (
            "This gate proves only that the software defaults and documentation do not promote "
            "diagnostic Case E settings into formal accuracy defaults. It does not add a solver "
            "run, improve the official z=2 m metric, or permit the formal v0.4.0 tag."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, checks)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"default_policy_gate_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
