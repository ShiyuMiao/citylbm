#!/usr/bin/env python3
"""Verify Run Simulation exposes the run manifest path and preserves claim-boundary fields."""

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
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"
OUT_JSON = RESULTS_DIR / "citylbm_manifest_output_gate.json"
OUT_CSV = RESULTS_DIR / "citylbm_manifest_output_gate.csv"
OUT_MD = RESULTS_DIR / "citylbm_manifest_output_gate.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def has_regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.S) is not None


def check(check_id: str, passed: bool, source: Path, paper_use: str, failure_action: str) -> Dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": passed,
        "evidence_type": "newly_run",
        "source_path": rel(source),
        "paper_use": paper_use,
        "failure_action": failure_action,
    }


def build_checks() -> List[Dict[str, Any]]:
    component = read_text(RUN_COMPONENT)
    fluidx = read_text(FLUIDX)
    return [
        check(
            "run_component_has_manifest_output",
            'AddTextParameter("Manifest Path", "Man"' in component,
            RUN_COMPONENT,
            "Use to show Grasshopper exposes the generated run manifest path.",
            "Restore the Manifest Path output parameter.",
        ),
        check(
            "run_component_has_claim_gate_output",
            'AddTextParameter("Claim Gate", "Gate"' in component,
            RUN_COMPONENT,
            "Use to show Grasshopper exposes the formal accuracy claim boundary beside run status.",
            "Restore the Claim Gate output parameter.",
        ),
        check(
            "run_component_has_publication_gate_output",
            'AddTextParameter("Publication Gate", "Pub"' in component,
            RUN_COMPONENT,
            "Use to show Grasshopper exposes the manuscript/publication-readiness boundary beside run status.",
            "Restore the Publication Gate output parameter.",
        ),
        check(
            "manifest_path_helper_exists",
            "ManifestPathForCase" in component and "citylbm_run_manifest.json" in component,
            RUN_COMPONENT,
            "Use to trace the component output to the generated manifest filename.",
            "Restore ManifestPathForCase and the citylbm_run_manifest.json filename.",
        ),
        check(
            "claim_gate_helper_exists",
            "ClaimGateSummary" in component
            and "Formal v0.4.0 requires release_gate.json pass" in component
            and "residual-target modes are limitations-only" in component,
            RUN_COMPONENT,
            "Use to show the component emits an explicit no-overclaim boundary for Case E runs.",
            "Restore ClaimGateSummary and its formal-release boundary text.",
        ),
        check(
            "publication_gate_helper_exists",
            "PublicationGateSummary" in component
            and "casee_publication_readiness_gate.json" in component
            and "solver-run provenance ledger" in component,
            RUN_COMPONENT,
            "Use to show the component emits explicit manuscript-readiness dependencies for Case E runs.",
            "Restore PublicationGateSummary and its publication-readiness boundary text.",
        ),
        check(
            "mode0_sets_manifest_output",
            has_regex(component, r"RunMode0_GenerateOnly.*?DA\.SetData\(6,\s*result\.Success\s*\?\s*ManifestPathForCase"),
            RUN_COMPONENT,
            "Use to show Generate Only mode returns the manifest path.",
            "Set output index 6 after successful Mode 0 generation.",
        ),
        check(
            "mode0_sets_claim_gate_output",
            has_regex(component, r"RunMode0_GenerateOnly.*?DA\.SetData\(7,\s*ClaimGateSummary\(settings,\s*result\.Success\)"),
            RUN_COMPONENT,
            "Use to show Generate Only mode returns the claim-gate boundary.",
            "Set output index 7 after Mode 0 generation.",
        ),
        check(
            "mode0_sets_publication_gate_output",
            has_regex(component, r"RunMode0_GenerateOnly.*?DA\.SetData\(8,\s*PublicationGateSummary\(settings,\s*result\.Success\)"),
            RUN_COMPONENT,
            "Use to show Generate Only mode returns the publication-readiness boundary.",
            "Set output index 8 after Mode 0 generation.",
        ),
        check(
            "mode1_sets_manifest_output",
            has_regex(component, r"RunMode1_FullAuto.*?DA\.SetData\(6,\s*result\.Success\s*\?\s*ManifestPathForCase"),
            RUN_COMPONENT,
            "Use to show full-auto mode returns the manifest path.",
            "Set output index 6 after successful Mode 1 execution.",
        ),
        check(
            "mode1_sets_claim_gate_output",
            has_regex(component, r"RunMode1_FullAuto.*?DA\.SetData\(7,\s*ClaimGateSummary\(settings,\s*result\.Success\)"),
            RUN_COMPONENT,
            "Use to show full-auto mode returns the claim-gate boundary.",
            "Set output index 7 after Mode 1 execution.",
        ),
        check(
            "mode1_sets_publication_gate_output",
            has_regex(component, r"RunMode1_FullAuto.*?DA\.SetData\(8,\s*PublicationGateSummary\(settings,\s*result\.Success\)"),
            RUN_COMPONENT,
            "Use to show full-auto mode returns the publication-readiness boundary.",
            "Set output index 8 after Mode 1 execution.",
        ),
        check(
            "mode2_sets_manifest_output",
            has_regex(component, r"RunMode2_DeployOnly.*?DA\.SetData\(6,\s*ManifestPathForCase\(caseDir\)"),
            RUN_COMPONENT,
            "Use to show deploy-only mode returns the generated manifest path.",
            "Set output index 6 after Mode 2 case generation.",
        ),
        check(
            "mode2_sets_claim_gate_output",
            has_regex(component, r"RunMode2_DeployOnly.*?DA\.SetData\(7,\s*ClaimGateSummary\(settings,\s*deployResult\.Success\)"),
            RUN_COMPONENT,
            "Use to show deploy-only mode returns the claim-gate boundary.",
            "Set output index 7 after Mode 2 deployment.",
        ),
        check(
            "mode2_sets_publication_gate_output",
            has_regex(component, r"RunMode2_DeployOnly.*?DA\.SetData\(8,\s*PublicationGateSummary\(settings,\s*deployResult\.Success\)"),
            RUN_COMPONENT,
            "Use to show deploy-only mode returns the publication-readiness boundary.",
            "Set output index 8 after Mode 2 deployment.",
        ),
        check(
            "async_sets_manifest_output",
            has_regex(component, r"OutputAsyncResult.*?DA\.SetData\(6,\s*result\.Success\s*\?\s*ManifestPathForCase"),
            RUN_COMPONENT,
            "Use to show background mode returns the manifest path after completion.",
            "Set output index 6 in OutputAsyncResult.",
        ),
        check(
            "async_sets_claim_gate_output",
            has_regex(component, r"OutputAsyncResult.*?DA\.SetData\(7,\s*result\.Success"),
            RUN_COMPONENT,
            "Use to show background mode returns the claim-gate boundary after completion.",
            "Set output index 7 in OutputAsyncResult.",
        ),
        check(
            "async_sets_publication_gate_output",
            has_regex(component, r"OutputAsyncResult.*?DA\.SetData\(8,\s*result\.Success"),
            RUN_COMPONENT,
            "Use to show background mode returns the publication-readiness boundary after completion.",
            "Set output index 8 in OutputAsyncResult.",
        ),
        check(
            "fluidx_writes_run_manifest",
            'Path.Combine(caseDir, "citylbm_run_manifest.json")' in fluidx and "WriteRunManifest" in fluidx,
            FLUIDX,
            "Use to show the exposed path points to a file written by the solver interface.",
            "Restore WriteRunManifest output to citylbm_run_manifest.json.",
        ),
        check(
            "manifest_contains_claim_boundary",
            "release_claim_boundary" in fluidx
            and "formal_sampling_mode" in fluidx
            and "diagnostic_modes_allowed_as_formal_result" in fluidx
            and "z_plus_half_allowed_as_formal_result" in fluidx
            and "diagnostic_wall_model_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_roughness_length_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_inlet_turbulence_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_residual_target_allowed_as_default_accuracy_model" in fluidx,
            FLUIDX,
            "Use to show the manifest records formal protocol and diagnostic boundaries.",
            "Restore claim-boundary fields in the run manifest.",
        ),
        check(
            "manifest_contains_wall_roughness_residual_followup_fields",
            "diagnostic_wall_model" in fluidx
            and "diagnostic_wall_model_is_default" in fluidx
            and "diagnostic_roughness_length_m" in fluidx
            and "diagnostic_wall_roughness_changes_solver_defaults" in fluidx
            and "diagnostic_inlet_turbulence_mode" in fluidx
            and "diagnostic_inlet_turbulence_scale" in fluidx
            and "diagnostic_inlet_turbulence_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_residual_target_mode" in fluidx
            and "diagnostic_residual_target_scale" in fluidx
            and "diagnostic_residual_target_changes_solver_defaults" in fluidx,
            FLUIDX,
            "Use to show run manifests trace wall/roughness/inlet/residual-target follow-up switches without promoting solver defaults.",
            "Restore wall/roughness/inlet/residual-target follow-up fields in WriteRunManifest.",
        ),
        check(
            "manifest_contains_paper_readiness_boundary",
            "paper_readiness" in fluidx
            and "paper_allowed_uses" in fluidx
            and "paper_forbidden_claims" in fluidx
            and "accuracy_claim_requires_external_release_gate" in fluidx,
            FLUIDX,
            "Use to show the manifest records paper-use and forbidden-claim boundaries.",
            "Restore paper_readiness, paper_allowed_uses, and paper_forbidden_claims in the run manifest.",
        ),
        check(
            "manifest_contains_publication_readiness_contract",
            "publication_readiness_contract" in fluidx
            and "requires_publication_readiness_gate_json" in fluidx
            and "requires_claim_support_gate_json" in fluidx
            and "requires_solver_run_provenance_ledger" in fluidx
            and "publication_ready_as_negative_validation_packet_from_manifest_alone" in fluidx
            and "formal_accuracy_pass_from_manifest" in fluidx,
            FLUIDX,
            "Use to show the generated manifest carries reviewer-facing publication-readiness dependencies without claiming accuracy from the manifest alone.",
            "Restore publication_readiness_contract fields in the run manifest.",
        ),
        check(
            "manifest_contains_formal_accuracy_gate_contract",
            "formal_accuracy_gate" in fluidx
            and "formal_accuracy_claim_allowed_from_manifest_alone" in fluidx
            and "requires_release_gate_json" in fluidx
            and "requires_casea_smoke_regression" in fluidx
            and "required_formal_sampling_mode" in fluidx
            and "diagnostic_substitutes_allowed" in fluidx,
            FLUIDX,
            "Use to show each generated run manifest records the formal v0.4.0 accuracy-gate contract.",
            "Restore formal_accuracy_gate fields in the run manifest.",
        ),
    ]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = ["check_id", "passed", "evidence_type", "source_path", "paper_use", "failure_action"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Manifest Output Gate",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Manifest output gate passed: {payload['manifest_output_gate_passed']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## Checks",
        "",
        "| check | passed | source | paper use |",
        "|---|---:|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| `{row['check_id']}` | {row['passed']} | `{row['source_path']}` | {row['paper_use']} |")
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
        "manifest_output_gate_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_manifest_traceability" if passed else "blocked_manifest_traceability",
        "formal_accuracy_claim_supported": False,
        "checks": checks,
        "boundary": (
            "This gate verifies software traceability only: Run Simulation exposes the generated "
            "citylbm_run_manifest.json path, exposes the claim-gate and publication-gate "
            "boundaries in Grasshopper, and records claim-boundary and formal accuracy-gate fields. It does not validate "
            "CFD accuracy or Rhino loading of the new GHA."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, checks)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"manifest_output_gate_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
