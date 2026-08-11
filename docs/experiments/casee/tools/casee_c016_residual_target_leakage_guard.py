#!/usr/bin/env python3
"""Guard C016 residual-target follow-ups against calibration leakage.

The C014 residual audit is useful for designing the next physics hypothesis,
but the same official 80 RS_caseE probes cannot be used to tune a correction
and then reported as independent validation. This script makes that boundary
machine-checkable for the release and paper evidence gates.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"

C014_AUDIT = RESULTS_DIR / "casee_c014_residual_structure_audit.json"
RELEASE_GATE = RESULTS_DIR / "release_gate.json"
RUN_COMPONENT = ROOT / "CityLBM" / "src" / "Components" / "Simulation" / "RunSimulationComponent.cs"
FLUIDX = ROOT / "CityLBM" / "src" / "Core" / "FluidX3DInterface.cs"

OUT_JSON = RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json"
OUT_CSV = RESULTS_DIR / "casee_c016_residual_target_leakage_guard.csv"
OUT_MD = RESULTS_DIR / "casee_c016_residual_target_leakage_guard.md"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def row(
    guard_id: str,
    passed: bool,
    risk: str,
    policy: str,
    paper_use: str,
    mitigation: str,
    source_paths: List[Path],
) -> Dict[str, Any]:
    return {
        "guard_id": guard_id,
        "passed": passed,
        "evidence_type": "newly_run",
        "risk": risk,
        "policy": policy,
        "paper_use": paper_use,
        "mitigation": mitigation,
        "source_paths": "; ".join(rel(path) for path in source_paths),
        "source_paths_exist": all(path.exists() for path in source_paths),
    }


def build_rows(c014: Dict[str, Any], release_gate: Dict[str, Any]) -> List[Dict[str, Any]]:
    component = read_text(RUN_COMPONENT)
    fluidx = read_text(FLUIDX)
    affine = (c014.get("affine_upper_bound") or {}).get("metrics") or {}
    c014_metrics = c014.get("c014_metrics") or {}
    groups = {item.get("group"): item for item in c014.get("groups", [])}
    high_bias = (groups.get("official_high_ge_0p6") or {}).get("bias_pp")
    downstream_r2 = (groups.get("downstream_y_lt_0_inferred") or {}).get("r2")
    formal_allowed = release_gate.get("formal_release_allowed") is True

    return [
        row(
            "c016_residual_diagnosis_is_not_validation",
            c014.get("formal_accuracy_claim_supported") is False
            and c014_metrics.get("r2") is not None
            and float(c014_metrics.get("r2")) < 0.0,
            "C014 residual patterns can be mistaken for validation evidence.",
            "Residual diagnostics may motivate C016 hypotheses but cannot be cited as formal accuracy validation.",
            "Use to justify why residual-target work is a follow-up design, not a result.",
            "Require a future independent official z=2 m raw_trilinear run before any validation claim.",
            [C014_AUDIT],
        ),
        row(
            "posthoc_affine_upper_bound_blocked",
            affine.get("r2") is not None and float(affine.get("r2")) > 0.0,
            "A post-hoc affine transform fitted on the official 80 probes can make R2 look positive.",
            "Post-hoc fitting on RS_caseE official targets is calibration leakage and is forbidden as validation.",
            "Use as a protocol-risk example in limitations.",
            "If calibration is studied, report it only as an upper-bound diagnostic and validate on a separate benchmark or withheld probes.",
            [C014_AUDIT],
        ),
        row(
            "official_probe_targets_not_training_data",
            release_gate.get("metrics", {}).get("n") == 80
            and release_gate.get("metrics", {}).get("sampling_mode") == "raw_trilinear"
            and formal_allowed is False,
            "The same 80 official probes define the release gate and cannot also train/tune C016.",
            "RS_caseE targets are validation data for this project, not model-fitting data.",
            "Use to explain why C016 must be pre-registered before the next run.",
            "Freeze C016 settings before running FluidX3D and record them in the native case manifest.",
            [RELEASE_GATE],
        ),
        row(
            "citylbm_residual_controls_default_off",
            "Diagnostic Residual Target Mode" in component
            and "DiagnosticResidualTargetMode" in fluidx
            and "DiagnosticResidualTargetScale { get; set; } = 0.0" in fluidx
            and "diagnostic_residual_target_allowed_as_default_accuracy_model" in fluidx
            and "diagnostic_residual_target_changes_solver_defaults" in fluidx,
            "A diagnostic residual-target hook could be misread as a default accuracy model.",
            "CityLBM must keep residual-target controls default-off until an official independent metric gate passes.",
            "Use to document software safeguards against overclaiming.",
            "Keep residT/residS default-off and block default promotion in manifests and policy gates.",
            [RUN_COMPONENT, FLUIDX],
        ),
        row(
            "range_compression_target_is_physics_hypothesis",
            high_bias is not None and downstream_r2 is not None,
            "High-speed underprediction and downstream error can tempt direct residual correction.",
            "C016 may target range compression only through a pre-registered wall/inlet/channel-response hypothesis.",
            "Use to motivate the next candidate without reporting corrected metrics.",
            "Do not use observed residuals as per-probe correction factors in the official metric.",
            [C014_AUDIT],
        ),
    ]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fields = [
        "guard_id",
        "passed",
        "evidence_type",
        "risk",
        "policy",
        "paper_use",
        "mitigation",
        "source_paths",
        "source_paths_exist",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in rows:
            writer.writerow(item)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    c014 = payload["c014_summary"]
    lines = [
        "# Case E C016 Residual-Target Leakage Guard",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Guard passed: {payload['guard_passed']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        "",
        "## C014 Context",
        "",
        f"- C014 MAE: {c014.get('mae_pp')} pp",
        f"- C014 R2: {c014.get('r2')}",
        f"- C014 Pearson: {c014.get('pearson')}",
        f"- Post-hoc affine upper-bound R2: {payload['posthoc_affine_upper_bound'].get('r2')}",
        "",
        "## Guards",
        "",
        "| guard | passed | policy | mitigation |",
        "|---|---:|---|---|",
    ]
    for item in payload["guards"]:
        lines.append(f"| `{item['guard_id']}` | {item['passed']} | {item['policy']} | {item['mitigation']} |")
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    c014 = read_json(C014_AUDIT)
    release_gate = read_json(RELEASE_GATE)
    rows = build_rows(c014, release_gate)
    passed = all(bool(item["passed"]) and bool(item["source_paths_exist"]) for item in rows)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "guard_passed": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_protocol_risk_guard" if passed else "blocked_protocol_risk_guard",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "recommended_tag": release_gate.get("recommended_tag"),
        "c014_summary": c014.get("c014_metrics") or {},
        "posthoc_affine_upper_bound": (c014.get("affine_upper_bound") or {}).get("metrics") or {},
        "allowed_uses": [
            "pre-register C016 wall/inlet/channel-response hypotheses",
            "document residual-structure limitations",
            "define future independent official z=2 m raw_trilinear pass conditions",
        ],
        "forbidden_uses": [
            "fit residual corrections on the same 80 official RS_caseE probes and report them as validation",
            "use post-hoc affine calibration as official z=2 m accuracy evidence",
            "promote residT/residS or no-SGS/inlet settings as defaults before the release gate passes",
            "claim predictive accuracy, mesh independence, or LES improvement from C016 planning evidence",
        ],
        "guards": rows,
        "boundary": (
            "This guard is a protocol-risk and software-feedback artifact. It does not run FluidX3D, "
            "does not change official metrics, and does not support a formal v0.4.0 release. "
            "It prevents C016 residual-target work from becoming calibration leakage."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, rows)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"guard_passed": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
