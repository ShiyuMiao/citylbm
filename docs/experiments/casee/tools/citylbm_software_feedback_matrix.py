#!/usr/bin/env python3
"""Map Experiments 1-3 evidence into CityLBM software-feedback decisions."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASEE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASEE_DIR / "results"
CASEA_RESULTS = ROOT / "docs" / "experiments" / "casea" / "results"
PAPER_DRAFTS = ROOT / "academic-paper-writer" / "paper-drafts"
FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
REPRO_SUITE = CASEE_DIR / "tools" / "reproducibility_suite.py"
RELEASE_GATE_SCRIPT = CASEE_DIR / "tools" / "casee_audit.py"

OUT_JSON = RESULTS_DIR / "citylbm_software_feedback_matrix.json"
OUT_CSV = RESULTS_DIR / "citylbm_software_feedback_matrix.csv"
OUT_MD = RESULTS_DIR / "citylbm_software_feedback_matrix.md"

FIELDNAMES = [
    "feedback_id",
    "experiment",
    "finding",
    "evidence_type",
    "source_paths",
    "decision_class",
    "citylbm_status",
    "implementation_evidence",
    "default_setting_allowed",
    "paper_use",
    "limitations",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def exists_all(paths: Iterable[Path]) -> bool:
    return all(path.exists() for path in paths)


def row(
    *,
    feedback_id: str,
    experiment: str,
    finding: str,
    evidence_type: str,
    source_paths: Iterable[Path],
    decision_class: str,
    citylbm_status: str,
    implementation_evidence: str,
    default_setting_allowed: bool,
    paper_use: str,
    limitations: str,
) -> Dict[str, Any]:
    paths = list(source_paths)
    return {
        "feedback_id": feedback_id,
        "experiment": experiment,
        "finding": finding,
        "evidence_type": evidence_type,
        "source_paths": "; ".join(rel(path) for path in paths),
        "source_paths_exist": exists_all(paths),
        "decision_class": decision_class,
        "citylbm_status": citylbm_status,
        "implementation_evidence": implementation_evidence,
        "default_setting_allowed": default_setting_allowed,
        "paper_use": paper_use,
        "limitations": limitations,
    }


def exp3_claim(rows: List[Dict[str, str]], claim_id: str) -> Dict[str, str]:
    for item in rows:
        if item.get("claim_or_asset") == claim_id:
            return item
    return {}


def build_rows() -> List[Dict[str, Any]]:
    fluidx = read_text(FLUIDX)
    run_component = read_text(RUN_COMPONENT)
    suite = read_text(REPRO_SUITE)
    audit = read_text(RELEASE_GATE_SCRIPT)
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    default_policy = read_json(RESULTS_DIR / "casee_default_policy_gate.json")
    paper_packet = read_json(RESULTS_DIR / "citylbm_paper_results_packet.json")
    manifest_output = read_json(RESULTS_DIR / "citylbm_manifest_output_gate.json")
    manuscript_table = read_json(RESULTS_DIR / "casee_manuscript_results_table.json")
    paper_figure = read_json(RESULTS_DIR / "casee_paper_results_figure_qa.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    exp3_rows = read_csv(PAPER_DRAFTS / "experiment3_claim_verification.csv")

    metrics = release_gate.get("metrics") or {}
    rows: List[Dict[str, Any]] = []

    rows.append(
        row(
            feedback_id="SF001",
            experiment="Experiment 1 / AIJ Case A",
            finding="Case A smoke regression guards the Rhino/GH -> FluidX3D -> VTK workflow but is not accuracy validation.",
            evidence_type="newly_run",
            source_paths=[
                CASEA_RESULTS / "casea_smoke_regression.json",
                CASEA_RESULTS / "casea_vtk_manifest.csv",
                CASEE_DIR / "tools" / "reproducibility_suite.py",
            ],
            decision_class="default_quality_gate",
            citylbm_status="implemented_as_release_gate_requirement"
            if (release_gate.get("checks") or {}).get("casea_smoke_regression_passed") is True
            and "casea_smoke_regression_passed" in audit
            else "missing_release_gate_integration",
            implementation_evidence="release_gate and reproducibility_suite require Case A smoke regression before formal release.",
            default_setting_allowed=True,
            paper_use="Use as workflow non-regression evidence.",
            limitations="Do not use as wind-field accuracy validation.",
        )
    )

    rows.append(
        row(
            feedback_id="SF002",
            experiment="Experiment 2 / AIJ Case E",
            finding=(
                f"Official z=2 m validation remains negative: MAE={metrics.get('mae_pp')} pp, "
                f"R2={metrics.get('r2')}, Pearson={metrics.get('pearson')}."
            ),
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "release_gate.json",
                RESULTS_DIR / "casee_metrics.csv",
                RESULTS_DIR / "casee_validation_report.md",
            ],
            decision_class="blocked_default_accuracy_upgrade",
            citylbm_status="formal_release_blocked" if release_gate.get("formal_release_allowed") is False else "formal_release_allowed",
            implementation_evidence="release_gate.json and paper_evidence_gate keep formal v0.4.0 blocked.",
            default_setting_allowed=False,
            paper_use="Use as negative validation and motivation for limitations.",
            limitations="Cannot claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF003",
            experiment="Experiment 2 / AIJ Case E",
            finding="The formal Case E protocol must remain z=2 m, 80 ac+N probes, and raw_trilinear sampling.",
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "casee_preset.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
                FLUIDX,
            ],
            decision_class="formal_protocol_default",
            citylbm_status="implemented" if default_policy.get("default_policy_gate_passed") is True else "blocked",
            implementation_evidence="SimulationSettings.FormalSamplingMode defaults to raw_trilinear and manifests block diagnostic substitutes.",
            default_setting_allowed=True,
            paper_use="Use as method/protocol policy.",
            limitations="Protocol correctness alone is not accuracy evidence.",
        )
    )

    rows.append(
        row(
            feedback_id="SF004",
            experiment="Experiment 2 / AIJ Case E",
            finding="Diagnostic nu_lbm sensitivity is useful for investigation but has not produced a formal official z=2 m pass.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_ground_nu_diagnostic_comparison.csv",
            ],
            decision_class="diagnostic_switch",
            citylbm_status="implemented_default_off"
            if "Diagnostic LBM Nu Override" in run_component and "DiagnosticNuLbmOverride { get; set; } = 0.0" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence="Grasshopper nuLBM input defaults to 0 and SimulationSettings defaults to 0.0.",
            default_setting_allowed=False,
            paper_use="Use as sensitivity diagnostic evidence.",
            limitations="Do not promote tuned nu_lbm as a default accuracy model.",
        )
    )

    rows.append(
        row(
            feedback_id="SF005",
            experiment="Experiment 2 / AIJ Case E",
            finding="Vertical-origin and probe sampling diagnostics expose near-wall/protocol sensitivity but remain non-formal.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv",
                RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv",
            ],
            decision_class="diagnostic_switch",
            citylbm_status="implemented_default_off"
            if "Diagnostic Z Origin Offset" in run_component
            and "DiagnosticZOriginOffsetM { get; set; } = 0.0" in fluidx
            and "z_plus_half_allowed_as_formal_result" in fluidx
            else "missing_or_not_default_off",
            implementation_evidence="Grasshopper zOff defaults to 0 and run manifests forbid z_plus_half as formal output.",
            default_setting_allowed=False,
            paper_use="Use for near-wall/probe-protocol limitations.",
            limitations="Do not report z_plus_half, vertical_valid_above, or z-offset results as official validation.",
        )
    )

    rows.append(
        row(
            feedback_id="SF006",
            experiment="Experiment 2 / AIJ Case E",
            finding="The next official Case E run is blocked by runtime and load-identity gates.",
            evidence_type="newly_run",
            source_paths=[
                RESULTS_DIR / "casee_official_run_preflight.json",
                RESULTS_DIR / "casee_environment_recovery_runbook.json",
                RESULTS_DIR / "rhino_gha_load_gate.json",
            ],
            decision_class="blocked_followup_run",
            citylbm_status="blocked_until_external_recovery"
            if preflight.get("official_followup_run_allowed") is False
            else "ready_for_next_official_run",
            implementation_evidence=f"blocked_gates={','.join(preflight.get('blocked_gates', []))}",
            default_setting_allowed=False,
            paper_use="Use to explain why no new official long run is reported in this rc.",
            limitations="Operational readiness evidence only; not solver-output evidence.",
        )
    )

    rows.append(
        row(
            feedback_id="SF007",
            experiment="Experiment 3 / TUM2TWIN digital-twin application",
            finding=exp3_claim(exp3_rows, "module_claim_M1").get(
                "paper_use",
                "Digital-twin layers should remain separated into visual, semantic/collision, and CFD/LBM inputs.",
            ),
            evidence_type=exp3_claim(exp3_rows, "module_claim_M1").get("evidence_type", "preexisting_artifact"),
            source_paths=[
                PAPER_DRAFTS / "experiment3_claim_verification.csv",
                ROOT / "releases" / "v0.2.0" / "package" / "validation_experiments" / "Experiment3_TUM2TWIN_DigitalTwin_DesignApplication",
            ],
            decision_class="application_workflow_policy",
            citylbm_status="paper_ready_workflow_guidance",
            implementation_evidence="Experiment 3 archive and claim verification document the layer separation policy.",
            default_setting_allowed=True,
            paper_use="Use as CityLBM-compatible digital-twin workflow evidence.",
            limitations="Does not prove Case E benchmark accuracy or CityLBM-GH end-to-end execution for Experiment 3.",
        )
    )

    rows.append(
        row(
            feedback_id="SF008",
            experiment="Experiment 3 / TUM2TWIN digital-twin application",
            finding=exp3_claim(exp3_rows, "module_claim_R3").get(
                "paper_use",
                "Morphology variables are screening descriptors rather than high-accuracy predictors.",
            ),
            evidence_type=exp3_claim(exp3_rows, "module_claim_R3").get("evidence_type", "preexisting_artifact"),
            source_paths=[
                PAPER_DRAFTS / "experiment3_claim_verification.csv",
                RESULTS_DIR / "citylbm_paper_results_packet.json",
            ],
            decision_class="paper_interpretation_layer",
            citylbm_status="paper_ready_with_boundary"
            if (paper_packet.get("summary") or {}).get("paper_results_packet_passed") is True
            else "blocked",
            implementation_evidence="citylbm_paper_results_packet keeps Experiment 3 screening evidence separate from Case E accuracy evidence.",
            default_setting_allowed=False,
            paper_use="Use as design-screening interpretation evidence.",
            limitations="Sample-internal screening only; no field validation or annual comfort compliance.",
        )
    )

    rows.append(
        row(
            feedback_id="SF009",
            experiment="CityLBM traceability layer",
            finding="Run Simulation exposes the generated citylbm_run_manifest.json path as a Grasshopper output for direct reviewer tracing.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if manifest_output.get("manifest_output_gate_passed") is True
            and 'AddTextParameter("Manifest Path", "Man"' in run_component
            else "blocked",
            implementation_evidence="Manifest Path output points to citylbm_run_manifest.json and the manifest records formal/diagnostic claim boundaries.",
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence for run manifests and protocol metadata.",
            limitations="Traceability output only; does not prove Rhino loaded the new GHA or improve official z=2 m accuracy.",
        )
    )

    rows.append(
        row(
            feedback_id="SF010",
            experiment="Experiment 2 / AIJ Case E paper-readiness layer",
            finding="Run manifests and manuscript result rows now record allowed paper uses and forbidden accuracy claims.",
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_manuscript_results_table.json",
            ],
            decision_class="paper_traceability_output",
            citylbm_status="implemented"
            if manifest_output.get("manifest_output_gate_passed") is True
            and (manuscript_table.get("summary") or {}).get("manuscript_results_table_passed") is True
            and "paper_readiness" in fluidx
            else "blocked",
            implementation_evidence="citylbm_run_manifest.json includes paper_readiness fields and casee_manuscript_results_table separates formal and diagnostic rows.",
            default_setting_allowed=True,
            paper_use="Use to move Case E results into manuscript tables without overstating formal accuracy.",
            limitations="Paper-readiness metadata does not change the official z=2 m metric or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF011",
            experiment="Experiment 2 / AIJ Case E paper-figure layer",
            finding="The manuscript result table is exported as an editable SVG/PNG/source-CSV figure bundle with QA checks.",
            evidence_type="newly_run",
            source_paths=[
                CASEE_DIR / "tools" / "casee_paper_results_figure.py",
                RESULTS_DIR / "casee_paper_results_figure_qa.json",
                RESULTS_DIR / "casee_paper_results_figure.svg",
                RESULTS_DIR / "casee_paper_results_figure_source.csv",
            ],
            decision_class="paper_figure_output",
            citylbm_status="implemented"
            if paper_figure.get("figure_gate_passed") is True
            and paper_figure.get("formal_accuracy_claim_supported") is False
            else "blocked",
            implementation_evidence="casee_paper_results_figure_qa.json verifies source CSV, editable SVG, PNG export, and negative-validation claim boundary.",
            default_setting_allowed=True,
            paper_use="Use as a paper figure for negative validation and limitations only.",
            limitations="Figure output does not add CFD results, improve official z=2 m metrics, or justify formal accuracy claims.",
        )
    )

    rows.append(
        row(
            feedback_id="SF012",
            experiment="Experiment 2 / AIJ Case E manifest gate contract",
            finding="Generated run manifests now encode the formal v0.4.0 accuracy-gate contract and keep manifest-only accuracy claims blocked.",
            evidence_type="newly_run",
            source_paths=[
                FLUIDX,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if "formal_accuracy_gate" in fluidx
            and "formal_accuracy_claim_allowed_from_manifest_alone" in fluidx
            and manifest_output.get("manifest_output_gate_passed") is True
            and default_policy.get("default_policy_gate_passed") is True
            else "blocked",
            implementation_evidence="WriteRunManifest emits formal_accuracy_gate with required official protocol, release-gate, Case A, Rhino/GHA, R2/Pearson, and diagnostic-substitute constraints.",
            default_setting_allowed=True,
            paper_use="Use as software traceability evidence that each generated case records the formal release-gate contract.",
            limitations="Manifest-gate metadata does not add solver output, improve official z=2 m metrics, or permit formal v0.4.0.",
        )
    )

    rows.append(
        row(
            feedback_id="SF013",
            experiment="Experiment 2 / AIJ Case E Grasshopper claim boundary",
            finding="Run Simulation now exposes a Claim Gate output so users can see the formal accuracy boundary beside run status and manifest path.",
            evidence_type="newly_run",
            source_paths=[
                RUN_COMPONENT,
                RESULTS_DIR / "citylbm_manifest_output_gate.json",
                RESULTS_DIR / "casee_default_policy_gate.json",
            ],
            decision_class="software_traceability_output",
            citylbm_status="implemented"
            if 'AddTextParameter("Claim Gate", "Gate"' in run_component
            and "ClaimGateSummary" in run_component
            and manifest_output.get("manifest_output_gate_passed") is True
            and default_policy.get("default_policy_gate_passed") is True
            else "blocked",
            implementation_evidence="RunSimulationComponent adds Claim Gate output index 7 and sets it in generate, deploy, full-auto, async, cancelled, running, and no-run states.",
            default_setting_allowed=True,
            paper_use="Use as software misuse-prevention evidence: successful execution is separated from formal benchmark accuracy.",
            limitations="UI claim-boundary text does not add solver output, improve official z=2 m metrics, or prove Rhino loaded the new GHA.",
        )
    )

    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for item in rows:
            writer.writerow({key: item[key] for key in FIELDNAMES})


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_decision: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    for item in rows:
        by_decision[item["decision_class"]] = by_decision.get(item["decision_class"], 0) + 1
        by_status[item["citylbm_status"]] = by_status.get(item["citylbm_status"], 0) + 1
    required_ids = {"SF001", "SF002", "SF003", "SF004", "SF005", "SF006", "SF007", "SF008", "SF009", "SF010", "SF011", "SF012", "SF013"}
    found_ids = {str(item["feedback_id"]) for item in rows}
    sources_exist = all(bool(item["source_paths_exist"]) for item in rows)
    no_forbidden_default = all(
        bool(item["default_setting_allowed"])
        for item in rows
        if item["decision_class"] in {"default_quality_gate", "formal_protocol_default", "application_workflow_policy", "software_traceability_output", "paper_traceability_output", "paper_figure_output"}
    ) and not any(
        bool(item["default_setting_allowed"])
        for item in rows
        if item["decision_class"] in {"diagnostic_switch", "blocked_default_accuracy_upgrade", "blocked_followup_run", "paper_interpretation_layer"}
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "feedback_count": len(rows),
        "decision_class_counts": by_decision,
        "citylbm_status_counts": by_status,
        "required_feedback_rows_present": required_ids.issubset(found_ids),
        "all_source_paths_exist": sources_exist,
        "no_forbidden_default_promotion": no_forbidden_default,
        "software_feedback_matrix_passed": required_ids.issubset(found_ids) and sources_exist and no_forbidden_default,
        "formal_accuracy_claim_supported": False,
        "formal_v0_4_0_allowed": False,
        "boundary": (
            "This matrix converts audited experiment findings into software policy, diagnostic switch, "
            "and blocker decisions. It does not add CFD results or upgrade the official Case E metric."
        ),
    }


def write_markdown(path: Path, rows: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines = [
        "# CityLBM Software Feedback Matrix",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Matrix passed: {summary['software_feedback_matrix_passed']}",
        f"- Feedback rows: {summary['feedback_count']}",
        f"- All source paths exist: {summary['all_source_paths_exist']}",
        f"- No forbidden default promotion: {summary['no_forbidden_default_promotion']}",
        f"- Formal accuracy claim supported: {summary['formal_accuracy_claim_supported']}",
        f"- Formal v0.4.0 allowed: {summary['formal_v0_4_0_allowed']}",
        "",
        "## Decision Counts",
        "",
    ]
    for key in sorted(summary["decision_class_counts"]):
        lines.append(f"- {key}: {summary['decision_class_counts'][key]}")
    lines += [
        "",
        "## Feedback Rows",
        "",
        "| id | experiment | decision | status | default? | finding |",
        "|---|---|---|---|---:|---|",
    ]
    for item in rows:
        lines.append(
            f"| `{item['feedback_id']}` | {item['experiment']} | {item['decision_class']} | "
            f"{item['citylbm_status']} | {item['default_setting_allowed']} | {item['finding']} |"
        )
    lines += [
        "",
        "## Paper Boundary",
        "",
        "| id | paper use | limitations |",
        "|---|---|---|",
    ]
    for item in rows:
        lines.append(f"| `{item['feedback_id']}` | {item['paper_use']} | {item['limitations']} |")
    lines += [
        "",
        "## Boundary",
        "",
        summary["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = build_rows()
    summary = summarize(rows)
    payload = {
        "summary": summary,
        "rows": rows,
        "source_artifacts": [
            rel(CASEA_RESULTS / "casea_smoke_regression.json"),
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "casee_default_policy_gate.json"),
            rel(RESULTS_DIR / "casee_official_run_preflight.json"),
            rel(RESULTS_DIR / "citylbm_paper_results_packet.json"),
            rel(RESULTS_DIR / "citylbm_manifest_output_gate.json"),
            rel(RESULTS_DIR / "casee_manuscript_results_table.json"),
            rel(RESULTS_DIR / "casee_paper_results_figure_qa.json"),
            rel(PAPER_DRAFTS / "experiment3_claim_verification.csv"),
            rel(FLUIDX),
            rel(RUN_COMPONENT),
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, rows, summary)
    print(json.dumps({"software_feedback_matrix_passed": summary["software_feedback_matrix_passed"], "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if summary["software_feedback_matrix_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
