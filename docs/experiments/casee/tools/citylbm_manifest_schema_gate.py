#!/usr/bin/env python3
"""Verify the generated CityLBM run manifest has a stable Case E claim contract."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
DEFAULT_POLICY_GATE = RESULTS_DIR / "casee_default_policy_gate.json"
MANIFEST_OUTPUT_GATE = RESULTS_DIR / "citylbm_manifest_output_gate.json"
OUT_JSON = RESULTS_DIR / "citylbm_manifest_schema_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_manifest_schema_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_manifest_schema_gate.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_csharp_json_literals(text: str) -> str:
    return text.replace(r"\"", '"')


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def check_row(
    check_id: str,
    passed: bool,
    source: Path,
    schema_area: str,
    paper_use: str,
    failure_action: str,
) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": passed,
        "evidence_type": "newly_run",
        "source_path": rel(source),
        "schema_area": schema_area,
        "paper_use": paper_use,
        "failure_action": failure_action,
    }


def all_in(text: str, needles: List[str]) -> bool:
    return all(needle in text for needle in needles)


def build_checks() -> List[Dict[str, Any]]:
    fluidx = normalize_csharp_json_literals(read_text(FLUIDX))
    component = read_text(RUN_COMPONENT)
    release_gate = read_json(RELEASE_GATE)
    default_policy = read_json(DEFAULT_POLICY_GATE)
    manifest_output = read_json(MANIFEST_OUTPUT_GATE)
    metrics = release_gate.get("metrics") or {}
    return [
        check_row(
            "manifest_writer_emits_named_file",
            'Path.Combine(caseDir, "citylbm_run_manifest.json")' in fluidx and "WriteRunManifest" in fluidx,
            FLUIDX,
            "file_identity",
            "Use to identify the per-run manifest file in the reproducibility appendix.",
            "Restore WriteRunManifest output to citylbm_run_manifest.json.",
        ),
        check_row(
            "grasshopper_exposes_manifest_and_claim_gate",
            'AddTextParameter("Manifest Path", "Man"' in component
            and 'AddTextParameter("Claim Gate", "Gate"' in component
            and "ClaimGateSummary" in component,
            RUN_COMPONENT,
            "ui_traceability",
            "Use to show Grasshopper exposes both the manifest path and no-overclaim text.",
            "Restore Manifest Path and Claim Gate outputs on Run Simulation.",
        ),
        check_row(
            "top_level_manifest_sections_present",
            all_in(
                fluidx,
                [
                    '"generated_at"',
                    '"scene_name"',
                    '"protocol_name"',
                    '"evidence_boundary"',
                    '"diagnostic_settings_are_default_safe"',
                    '"release_claim_boundary"',
                    '"publication_readiness_contract"',
                    '"formal_accuracy_gate"',
                    '"grid"',
                    '"wind"',
                    '"simulation"',
                    '"validation"',
                    '"inputs"',
                ],
            ),
            FLUIDX,
            "top_level_sections",
            "Use to describe the manifest as a complete protocol and evidence-boundary record.",
            "Restore all required top-level manifest sections.",
        ),
        check_row(
            "official_casee_contract_fields_present",
            all_in(
                fluidx,
                [
                    '"required_case_condition": "ac"',
                    '"required_wind_direction": "N"',
                    '"required_wind_vector": [0.0, -1.0, 0.0]',
                    '"required_validation_height_m": 2.0',
                    '"required_probe_count": 80',
                    '"required_formal_sampling_mode": "raw_trilinear"',
                    '"required_metric_trend"',
                ],
            ),
            FLUIDX,
            "formal_casee_contract",
            "Use to state that generated manifests preserve the official ac+N z=2 m protocol contract.",
            "Restore official Case E formal accuracy gate fields.",
        ),
        check_row(
            "diagnostic_substitutes_are_blocked",
            all_in(
                fluidx,
                [
                    '"diagnostic_modes_allowed_as_formal_result": false',
                    '"diagnostic_substitutes_allowed": false',
                    '"z_plus_half"',
                    '"vertical_valid_above"',
                    '"nearest_valid"',
                    '"fluid_weighted"',
                    '"z_origin_offset"',
                    '"wall_model"',
                    '"roughness_length"',
                    '"inlet_turbulence_scale"',
                    '"residual_target_mode"',
                    '"residual_target_scale"',
                ],
            ),
            FLUIDX,
            "diagnostic_boundary",
            "Use to keep diagnostic sampling, offsets, wall models, roughness, inlet turbulence, and residual targets out of formal result claims.",
            "Restore diagnostic substitute blocking fields.",
        ),
        check_row(
            "wall_roughness_residual_default_safe_fields_present",
            all_in(
                fluidx,
                [
                    '"diagnostic_wall_model"',
                    '"diagnostic_wall_model_is_default"',
                    '"diagnostic_roughness_length_m"',
                    '"diagnostic_roughness_length_is_default"',
                    '"diagnostic_wall_roughness_changes_solver_defaults": false',
                    '"diagnostic_wall_model_allowed_as_default_accuracy_model": false',
                    '"diagnostic_roughness_length_allowed_as_default_accuracy_model": false',
                    '"diagnostic_inlet_turbulence_mode"',
                    '"diagnostic_inlet_turbulence_scale"',
                    '"diagnostic_inlet_turbulence_is_default"',
                    '"diagnostic_inlet_turbulence_uses_af_k"',
                    '"diagnostic_inlet_turbulence_allowed_as_default_accuracy_model": false',
                    '"diagnostic_residual_target_mode"',
                    '"diagnostic_residual_target_scale"',
                    '"diagnostic_residual_target_is_default"',
                    '"diagnostic_residual_target_changes_solver_defaults": false',
                    '"diagnostic_residual_target_allowed_as_default_accuracy_model": false',
                ],
            ),
            FLUIDX,
            "wall_roughness_residual_boundary",
            "Use to document wall/roughness/inlet/residual-target follow-up controls as default-off traceability fields.",
            "Restore wall/roughness/inlet/residual-target manifest fields and default-promotion blockers.",
        ),
        check_row(
            "probe_protocol_risk_fields_present",
            all_in(
                fluidx,
                [
                    '"probe_protocol_risk"',
                    '"formal_height_m"',
                    '"grid_z_float"',
                    '"formal_height_between_lattice_layers"',
                    '"formal_result_must_use_official_height"',
                    '"z_plus_half_allowed_as_formal_result": false',
                ],
            ),
            FLUIDX,
            "probe_protocol_risk",
            "Use to trace near-wall probe-position risks without redefining official z=2 m validation.",
            "Restore probe_protocol_risk manifest fields.",
        ),
        check_row(
            "paper_forbidden_claims_present",
            all_in(
                fluidx,
                [
                    '"paper_readiness"',
                    '"paper_allowed_uses"',
                    '"paper_forbidden_claims"',
                    '"predictive_accuracy_pass"',
                    '"mesh_independence"',
                    '"les_improvement"',
                    '"diagnostic_sampling_as_formal_result"',
                ],
            ),
            FLUIDX,
            "paper_claim_boundary",
            "Use to show generated manifests carry paper-use limits and forbidden claim classes.",
            "Restore paper readiness and forbidden-claim fields.",
        ),
        check_row(
            "publication_readiness_contract_present",
            all_in(
                fluidx,
                [
                    '"publication_readiness_contract"',
                    '"manifest_claim_role": "protocol_and_software_traceability_only"',
                    '"publication_ready_as_negative_validation_packet_from_manifest_alone": false',
                    '"requires_publication_readiness_gate_json": true',
                    '"requires_claim_support_gate_json": true',
                    '"requires_solver_run_provenance_ledger": true',
                    '"requires_paper_figure_qa": true',
                    '"requires_reproducibility_suite": true',
                    '"publication_forbidden_claims"',
                    '"formal_accuracy_pass_from_manifest"',
                    '"diagnostic_candidate_as_formal_result"',
                    '"posthoc_calibration_as_validation"',
                ],
            ),
            FLUIDX,
            "publication_readiness_contract",
            "Use to show each generated manifest records the external publication-readiness gates required before manuscript use.",
            "Restore publication_readiness_contract fields in WriteRunManifest.",
        ),
        check_row(
            "default_policy_gate_passed",
            default_policy.get("default_policy_gate_passed") is True,
            DEFAULT_POLICY_GATE,
            "upstream_gate",
            "Use to show source defaults remain claim-safe before interpreting manifest schema.",
            "Run casee_default_policy_gate.py and fix failed default-policy checks.",
        ),
        check_row(
            "manifest_output_gate_passed",
            manifest_output.get("manifest_output_gate_passed") is True,
            MANIFEST_OUTPUT_GATE,
            "upstream_gate",
            "Use to show the UI and manifest output contract is already passing.",
            "Run citylbm_manifest_output_gate.py and fix failed output checks.",
        ),
        check_row(
            "formal_release_still_blocked_by_metrics",
            release_gate.get("formal_release_allowed") is False
            and metrics.get("sampling_mode") == "raw_trilinear"
            and abs(float(metrics.get("height_m", 0.0)) - 2.0) <= 1e-9
            and float(metrics.get("r2", 0.0)) < 0.0,
            RELEASE_GATE,
            "release_boundary",
            "Use to prove this schema gate cannot be cited as formal accuracy success.",
            "Do not publish a formal tag until release_gate.json passes official z=2 m metrics.",
        ),
    ]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "check_id",
        "passed",
        "evidence_type",
        "source_path",
        "schema_area",
        "paper_use",
        "failure_action",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Manifest Schema Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Manifest schema gate passed: {payload['manifest_schema_gate_passed']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Contract version: `{payload['manifest_contract_version']}`",
        "",
        "## Checks",
        "",
        "| check | passed | schema area | source |",
        "|---|---:|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| `{row['check_id']}` | {row['passed']} | `{row['schema_area']}` | `{row['source_path']}` |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    checks = build_checks()
    passed = all(bool(row["passed"]) for row in checks)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_contract_version": "casee_manifest_contract_v2",
        "manifest_schema_gate_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_manifest_schema_boundary" if passed else "blocked_manifest_schema_boundary",
        "formal_accuracy_claim_supported": False,
        "checks": checks,
        "required_manifest_sections": [
            "release_claim_boundary",
            "publication_readiness_contract",
            "formal_accuracy_gate",
            "grid",
            "wind",
            "simulation",
            "validation",
            "inputs",
        ],
        "required_formal_protocol": {
            "case_condition": "ac",
            "wind_direction": "N",
            "wind_vector": [0.0, -1.0, 0.0],
            "validation_height_m": 2.0,
            "probe_count": 80,
            "formal_sampling_mode": "raw_trilinear",
        },
        "boundary": (
            "This gate verifies the static schema and claim contract for generated "
            "CityLBM run manifests. It is paper-ready traceability evidence, not CFD "
            "solver-output evidence, and it cannot support a formal accuracy claim."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, checks)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"manifest_schema_gate_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
