#!/usr/bin/env python3
"""Generate manuscript-facing claim boundaries for AIJ Case E evidence."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def metric_row(rows: List[Dict[str, str]], mode: str) -> Dict[str, str]:
    for row in rows:
        if row.get("sampling_mode") == mode:
            return row
    raise SystemExit(f"Missing sampling mode {mode}")


def group_row(rows: List[Dict[str, str]], group: str) -> Dict[str, str]:
    for row in rows:
        if row.get("group") == group:
            return row
    raise SystemExit(f"Missing group {group}")


def fmt(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def build_claims(
    gate: Dict[str, Any],
    probe_modes: List[Dict[str, str]],
    zcenter_modes: List[Dict[str, str]],
    voxel_groups: List[Dict[str, str]],
    zcenter_voxel_groups: List[Dict[str, str]],
    build_chain: Dict[str, Any],
    c002_longer_mean: Dict[str, Any],
    c003_zorigin_ablation: Dict[str, Any],
    c004_dx3_low_cost: Dict[str, Any],
    c005_decomposition: Dict[str, Any],
    c008_c009_inlet: Dict[str, Any],
) -> List[Dict[str, Any]]:
    baseline_raw = metric_row(probe_modes, "raw_trilinear")
    zcenter_raw = metric_row(zcenter_modes, "raw_trilinear")
    zcenter_vva = metric_row(zcenter_modes, "vertical_valid_above")
    voxel_low = group_row(voxel_groups, "low")
    voxel_high = group_row(voxel_groups, "high")
    zcenter_low = group_row(zcenter_voxel_groups, "low")
    zcenter_high = group_row(zcenter_voxel_groups, "high")
    checks = gate.get("checks", {})
    vs_cpp = build_chain.get("visual_studio_build_tools_2022_cpp", {})
    gpu = build_chain.get("gpu_runtime", {}).get("nvidia_smi", {})
    claims: List[Dict[str, Any]] = [
        {
            "claim_id": "C001",
            "claim_readiness": "paper_ready",
            "evidence_type": "newly_run",
            "section": "Methods / Validation protocol",
            "claim": "AIJ Case E validation uses the official ac+N, z=2 m, 80-probe protocol.",
            "supporting_metrics": "n=80; height=2 m; sampling=raw_trilinear",
            "source_paths": "docs/experiments/casee/results/casee_official_ac_N_probes.csv; docs/experiments/casee/casee_protocol.md",
            "allowed_use": "Use as protocol definition and reproducibility evidence.",
            "forbidden_use": "Do not imply accuracy success from protocol setup alone.",
            "protocol_risks": "single benchmark case; official pedestrian-height sampling is near-wall sensitive",
        },
        {
            "claim_id": "C002",
            "claim_readiness": "limitations_ready",
            "evidence_type": "newly_run",
            "section": "Results / Case E validation",
            "claim": "The current formal official z=2 m Case E validation does not meet the release accuracy gate.",
            "supporting_metrics": f"MAE={fmt(gate['metrics']['mae_pp'])} pp; R2={fmt(gate['metrics']['r2'], 6)}; Pearson={fmt(gate['metrics']['pearson'], 6)}",
            "source_paths": "docs/experiments/casee/results/release_gate.json; docs/experiments/casee/results/casee_metrics.csv",
            "allowed_use": "Use as a transparent negative validation result.",
            "forbidden_use": "Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness.",
            "protocol_risks": "metric gate fails; Rhino new GHA loading unverified",
        },
        {
            "claim_id": "C003",
            "claim_readiness": "weaken_claim",
            "evidence_type": "newly_run",
            "section": "Results / Diagnostic improvement",
            "claim": "Z-center lattice alignment improved the formal raw_trilinear diagnostic relative to the previous dx=2 probe-mode run, but R2 remained negative.",
            "supporting_metrics": (
                f"previous raw MAE={fmt(baseline_raw['mae_pp'])} pp, R2={fmt(baseline_raw['r2'], 6)}, Pearson={fmt(baseline_raw['pearson'], 6)}; "
                f"z-center raw MAE={fmt(zcenter_raw['mae_pp'])} pp, R2={fmt(zcenter_raw['r2'], 6)}, Pearson={fmt(zcenter_raw['pearson'], 6)}"
            ),
            "source_paths": "docs/experiments/casee/results/casee_probe_mode_metrics.csv; docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv",
            "allowed_use": "Use as diagnostic evidence that vertical lattice placement affects Case E measurements.",
            "forbidden_use": "Do not describe z-origin offset as a validated default model.",
            "protocol_risks": "diagnostic parameter tuned on the benchmark; single run; no independent validation",
        },
        {
            "claim_id": "C004",
            "claim_readiness": "limitations_ready",
            "evidence_type": "newly_run",
            "section": "Discussion / Near-wall limitations",
            "claim": "Error is concentrated at high protocol-risk probes near walls or solid interpolation corners.",
            "supporting_metrics": (
                f"baseline low-risk MAE={fmt(voxel_low['raw_mae_pp'])} pp, high-risk MAE={fmt(voxel_high['raw_mae_pp'])} pp; "
                f"z-center low-risk MAE={fmt(zcenter_low['raw_mae_pp'])} pp, high-risk MAE={fmt(zcenter_high['raw_mae_pp'])} pp"
            ),
            "source_paths": "docs/experiments/casee/results/casee_voxel_probe_audit_groups.csv; docs/experiments/casee/results/casee_zcenter_voxel_probe_audit_groups.csv",
            "allowed_use": "Use to motivate wall-model, voxelization, and official probe-protocol limitations.",
            "forbidden_use": "Do not remove high-risk probes to report a formal validation metric.",
            "protocol_risks": "risk grouping is diagnostic; formal metric remains all 80 official probes",
        },
        {
            "claim_id": "C005",
            "claim_readiness": "limitations_ready",
            "evidence_type": "newly_run",
            "section": "Discussion / Probe sampling diagnostics",
            "claim": "Diagnostic sampling can reduce Case E MAE, but no diagnostic mode makes official z=2 m R2 positive.",
            "supporting_metrics": f"best z-center diagnostic mode=vertical_valid_above; MAE={fmt(zcenter_vva['mae_pp'])} pp; R2={fmt(zcenter_vva['r2'], 6)}; Pearson={fmt(zcenter_vva['pearson'], 6)}",
            "source_paths": "docs/experiments/casee/results/casee_zcenter_probe_mode_metrics.csv",
            "allowed_use": "Use as sensitivity evidence.",
            "forbidden_use": "Do not use vertical_valid_above or z_plus_half as the formal official z=2 m result.",
            "protocol_risks": "alternative sampling is diagnostic only and benchmark-specific",
        },
        {
            "claim_id": "C006",
            "claim_readiness": "paper_ready",
            "evidence_type": "newly_run",
            "section": "Reproducibility / Build",
            "claim": "The current CityLBM source builds in Release configuration on the available .NET SDK toolchain.",
            "supporting_metrics": f"citylbm_build_passed={checks.get('citylbm_build_passed')}; Case A smoke regression={checks.get('casea_smoke_regression_passed')}",
            "source_paths": "docs/experiments/casee/results/citylbm_build_check.log; docs/experiments/casea/results/casea_smoke_regression.json",
            "allowed_use": "Use as build and workflow non-regression evidence.",
            "forbidden_use": "Do not use build success as CFD accuracy validation.",
            "protocol_risks": "Rhino/Grasshopper loading of the new GHA remains unverified",
        },
        {
            "claim_id": "C007",
            "claim_readiness": "weaken_claim",
            "evidence_type": "newly_run",
            "section": "Reproducibility / Build chain",
            "claim": "Visual Studio Build Tools 2022 C++ remains unavailable, but GPU runtime and the audited native-source fallback path are available for additional native validation attempts.",
            "supporting_metrics": (
                f"VS C++ status={vs_cpp.get('status')}; "
                f"native_source_compile_path={build_chain.get('native_source_compile_path')}; "
                f"nvidia-smi returncode={gpu.get('returncode')}"
            ),
            "source_paths": "docs/experiments/casee/results/build_chain_manifest.json",
            "allowed_use": "Use as a reproducibility limitation and fallback-build statement.",
            "forbidden_use": "Do not claim the VS C++ build-chain requirement is fully installed.",
            "protocol_risks": "VS installation failed; fallback compiler evidence does not itself add solver-output accuracy",
        },
        {
            "claim_id": "C008",
            "claim_readiness": "blocked",
            "evidence_type": "newly_run",
            "section": "Release",
            "claim": "Formal CityLBM v0.4.0 release is not allowed by the release gate.",
            "supporting_metrics": f"formal_release_allowed={gate.get('formal_release_allowed')}; recommended_tag={gate.get('recommended_tag')}",
            "source_paths": "docs/experiments/casee/results/release_gate.json",
            "allowed_use": "Use to justify rc-only release status.",
            "forbidden_use": "Do not create or cite a formal v0.4.0 tag before the gate passes.",
            "protocol_risks": "accuracy gate and Rhino-load gate fail",
        },
    ]
    if c002_longer_mean:
        candidate = c002_longer_mean.get("candidate_metrics", {})
        delta = c002_longer_mean.get("metric_delta_vs_baseline", {})
        claims.append(
            {
                "claim_id": "C009",
                "claim_readiness": "limitations_ready",
                "evidence_type": c002_longer_mean.get("evidence_type", "newly_run"),
                "section": "Results / Follow-up candidate audit",
                "claim": "Extending the dx=2 m z-center candidate to 96000 steps did not improve the official z=2 m Case E metric.",
                "supporting_metrics": (
                    f"status={c002_longer_mean.get('status')}; "
                    f"MAE={fmt(candidate['mae_pp'])} pp; R2={fmt(candidate['r2'], 6)}; Pearson={fmt(candidate['pearson'], 6)}; "
                    f"delta_MAE={fmt(delta['mae_pp'])} pp; delta_R2={fmt(delta['r2'], 6)}"
                ),
                "source_paths": "docs/experiments/casee/results/casee_c002_longer_mean_audit.json; docs/experiments/casee/results/casee_c002_longer_mean_audit.md",
                "allowed_use": "Use as negative follow-up evidence that longer averaging alone is not the current accuracy bottleneck.",
                "forbidden_use": "Do not promote C002 settings to CityLBM defaults or claim official z=2 m accuracy improvement.",
                "protocol_risks": "single follow-up candidate; formal metric remains negative and worsened relative to the z-center baseline",
            }
        )
    if c003_zorigin_ablation:
        candidate = c003_zorigin_ablation.get("candidate_metrics", {})
        delta = c003_zorigin_ablation.get("metric_delta_vs_zcenter_baseline", {})
        claims.append(
            {
                "claim_id": "C010",
                "claim_readiness": "limitations_ready",
                "evidence_type": c003_zorigin_ablation.get("evidence_type", "newly_run"),
                "section": "Results / Z-origin ablation",
                "claim": "Removing the z-center alignment worsened the official z=2 m raw-trilinear metric, confirming z-origin sensitivity rather than a validated default model.",
                "supporting_metrics": (
                    f"status={c003_zorigin_ablation.get('status')}; "
                    f"MAE={fmt(candidate['mae_pp'])} pp; R2={fmt(candidate['r2'], 6)}; Pearson={fmt(candidate['pearson'], 6)}; "
                    f"delta_MAE_vs_zcenter={fmt(delta['mae_pp'])} pp; delta_R2_vs_zcenter={fmt(delta['r2'], 6)}"
                ),
                "source_paths": "docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json; docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.md",
                "allowed_use": "Use as negative ablation evidence for near-wall/probe-protocol sensitivity.",
                "forbidden_use": "Do not claim z-center is a validated default accuracy model or that C003 supports formal v0.4.0.",
                "protocol_risks": "single ablation run; z-origin was benchmark-diagnostic and remains default-off/non-formal",
            }
        )
    if c004_dx3_low_cost:
        candidate = c004_dx3_low_cost.get("candidate_metrics", {})
        delta = c004_dx3_low_cost.get("metric_delta_vs_zcenter_baseline", {})
        claims.append(
            {
                "claim_id": "C011",
                "claim_readiness": "limitations_ready",
                "evidence_type": c004_dx3_low_cost.get("evidence_type", "newly_run"),
                "section": "Results / dx=3 control",
                "claim": "The dx=3 m low-cost control retained positive Pearson correlation but did not improve the official z=2 m Case E metric.",
                "supporting_metrics": (
                    f"status={c004_dx3_low_cost.get('status')}; "
                    f"MAE={fmt(candidate['mae_pp'])} pp; R2={fmt(candidate['r2'], 6)}; Pearson={fmt(candidate['pearson'], 6)}; "
                    f"delta_MAE_vs_zcenter={fmt(delta['mae_pp'])} pp; delta_R2_vs_zcenter={fmt(delta['r2'], 6)}"
                ),
                "source_paths": "docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json; docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.md",
                "allowed_use": "Use as low-cost direction/protocol regression evidence and coarse-grid limitation evidence.",
                "forbidden_use": "Do not claim dx=3 improves official z=2 m accuracy or proves mesh independence.",
                "protocol_risks": "single low-cost control; coarser grid; formal accuracy gate remains failed",
            }
        )
    if c005_decomposition:
        candidate = c005_decomposition.get("candidate_metrics", {})
        delta = c005_decomposition.get("metric_delta_vs_zcenter_baseline", {})
        claims.append(
            {
                "claim_id": "C012",
                "claim_readiness": "limitations_ready",
                "evidence_type": c005_decomposition.get("evidence_type", "newly_run"),
                "section": "Results / Runtime decomposition sensitivity",
                "claim": "The 4x1x1 domain-decomposition ablation improved MAE and R2 relative to the z-center baseline but remained negative and failed reproducibility-consistency thresholds.",
                "supporting_metrics": (
                    f"status={c005_decomposition.get('status')}; "
                    f"MAE={fmt(candidate['mae_pp'])} pp; R2={fmt(candidate['r2'], 6)}; Pearson={fmt(candidate['pearson'], 6)}; "
                    f"delta_MAE_vs_zcenter={fmt(delta['mae_pp'])} pp; delta_R2_vs_zcenter={fmt(delta['r2'], 6)}; "
                    f"delta_Pearson_vs_zcenter={fmt(delta['pearson'], 6)}"
                ),
                "source_paths": "docs/experiments/casee/results/casee_c005_decomposition_audit.json; docs/experiments/casee/results/casee_c005_decomposition_audit.md",
                "allowed_use": "Use as runtime/decomposition sensitivity evidence and as a pointer to the current best negative MAE/R2 diagnostic candidate.",
                "forbidden_use": "Do not promote 4x1x1 decomposition as a default accuracy model or claim formal v0.4.0 validation.",
                "protocol_risks": "single decomposition ablation; R2 remains negative; Pearson worsened; consistency thresholds failed",
            }
        )
    if c008_c009_inlet:
        best = c008_c009_inlet.get("best_candidate", {})
        candidate = best.get("candidate_metrics", {})
        delta = best.get("delta_vs_zcenter_baseline", {})
        claims.append(
            {
                "claim_id": "C013",
                "claim_readiness": "limitations_ready",
                "evidence_type": c008_c009_inlet.get("evidence_type", "newly_run"),
                "section": "Results / Inlet turbulence follow-up",
                "claim": "Using AF_caseE k in a default-off synthetic full-plane inlet substantially improved the official-height raw-trilinear metric, but R2 remained negative.",
                "supporting_metrics": (
                    f"status={c008_c009_inlet.get('status')}; best={best.get('candidate_id')}; "
                    f"MAE={fmt(candidate['mae_pp'])} pp; R2={fmt(candidate['r2'], 6)}; Pearson={fmt(candidate['pearson'], 6)}; "
                    f"delta_MAE_vs_zcenter={fmt(delta['mae_pp'])} pp; delta_R2_vs_zcenter={fmt(delta['r2'], 6)}"
                ),
                "source_paths": "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json; docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md",
                "allowed_use": "Use as the strongest current diagnostic improvement evidence and as motivation for a physically validated inlet-turbulence model.",
                "forbidden_use": "Do not claim formal predictive accuracy, LES improvement, or default promotion from the synthetic inlet scale sweep.",
                "protocol_risks": "single benchmark; diagnostic turbulence scale sweep; R2 remains negative; domain decomposition sensitivity remains present",
            }
        )
    return claims


def write_markdown(path: Path, claims: List[Dict[str, Any]], gate: Dict[str, Any]) -> None:
    metrics = gate["metrics"]
    lines = [
        "# AIJ Case E Manuscript Evidence Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Current Formal Metric",
        "",
        "- Protocol: AIJ Case E `ac+N`, official z=2 m, 80 probes, formal `raw_trilinear` sampling.",
        f"- MAE: {fmt(metrics['mae_pp'])} pp.",
        f"- RMSE: {fmt(metrics['rmse_pp'])} pp.",
        f"- Bias: {fmt(metrics['bias_pp'])} pp.",
        f"- R2: {fmt(metrics['r2'], 6)}.",
        f"- Pearson: {fmt(metrics['pearson'], 6)}.",
        f"- Formal release allowed: {gate.get('formal_release_allowed')}.",
        f"- Recommended tag: `{gate.get('recommended_tag')}`.",
        "",
        "## Claim Matrix",
        "",
        "| claim_id | readiness | section | allowed claim | evidence |",
        "|---|---|---|---|---|",
    ]
    for claim in claims:
        lines.append(
            f"| {claim['claim_id']} | {claim['claim_readiness']} | {claim['section']} | "
            f"{claim['claim']} | `{claim['source_paths']}` |"
        )
    lines += [
        "",
        "## Results Paragraph Draft",
        "",
        "AIJ Case E was evaluated under the official `ac+N` protocol using 80 pedestrian-height probes at z=2 m and formal raw-trilinear sampling. "
        f"The latest z-center diagnostic run produced MAE = {fmt(metrics['mae_pp'])} percentage points, RMSE = {fmt(metrics['rmse_pp'])} percentage points, "
        f"bias = {fmt(metrics['bias_pp'])} percentage points, R2 = {fmt(metrics['r2'], 6)}, and Pearson = {fmt(metrics['pearson'], 6)} "
        "(newly_run; see `docs/experiments/casee/results/release_gate.json`). "
        "Because R2 remains negative and the release gate fails, this result should be reported as a transparent diagnostic/negative validation outcome rather than a predictive-accuracy result.",
        "",
        "## Limitations Paragraph Draft",
        "",
        "The dominant remaining limitation is near-wall and probe-protocol fidelity. "
        "Voxel/probe audits show substantially lower MAE for low-risk probes than for high-risk probes, while alternative diagnostic sampling modes reduce MAE but still do not make R2 positive. "
        "Therefore, the current evidence supports claims about workflow reproducibility, protocol transparency, and identified wall/voxelization/probe-sampling limitations, but it does not support formal mesh-independence, LES-improvement, or research-grade predictive-accuracy claims.",
        "",
        "## Forbidden Claims",
        "",
        "- CityLBM v0.4.0 has achieved validated predictive accuracy for AIJ Case E.",
        "- z_plus_half, vertical_valid_above, or any z-offset diagnostic is the formal official z=2 m validation result.",
        "- The current branch demonstrates mesh independence or LES improvement.",
        "- The native Windows C++/GPU validation chain is fully ready for additional long runs.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-gate", type=Path, default=RESULTS_DIR / "release_gate.json")
    parser.add_argument("--probe-mode-metrics", type=Path, default=RESULTS_DIR / "casee_probe_mode_metrics.csv")
    parser.add_argument("--zcenter-metrics", type=Path, default=RESULTS_DIR / "casee_zcenter_probe_mode_metrics.csv")
    parser.add_argument("--voxel-groups", type=Path, default=RESULTS_DIR / "casee_voxel_probe_audit_groups.csv")
    parser.add_argument("--zcenter-voxel-groups", type=Path, default=RESULTS_DIR / "casee_zcenter_voxel_probe_audit_groups.csv")
    parser.add_argument("--build-chain", type=Path, default=RESULTS_DIR / "build_chain_manifest.json")
    parser.add_argument("--c002-longer-mean", type=Path, default=RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    parser.add_argument("--c003-zorigin-ablation", type=Path, default=RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    parser.add_argument("--c004-dx3-low-cost", type=Path, default=RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    parser.add_argument("--c005-decomposition", type=Path, default=RESULTS_DIR / "casee_c005_decomposition_audit.json")
    parser.add_argument("--c008-c009-inlet", type=Path, default=RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json")
    parser.add_argument("--out-csv", type=Path, default=RESULTS_DIR / "casee_manuscript_claim_matrix.csv")
    parser.add_argument("--out-md", type=Path, default=RESULTS_DIR / "casee_manuscript_evidence_summary.md")
    parser.add_argument("--out-json", type=Path, default=RESULTS_DIR / "casee_manuscript_claim_matrix.json")
    args = parser.parse_args()

    gate = json.loads(args.release_gate.read_text(encoding="utf-8"))
    build_chain = json.loads(args.build_chain.read_text(encoding="utf-8"))
    c002_longer_mean = json.loads(args.c002_longer_mean.read_text(encoding="utf-8")) if args.c002_longer_mean.exists() else {}
    c003_zorigin_ablation = json.loads(args.c003_zorigin_ablation.read_text(encoding="utf-8")) if args.c003_zorigin_ablation.exists() else {}
    c004_dx3_low_cost = json.loads(args.c004_dx3_low_cost.read_text(encoding="utf-8")) if args.c004_dx3_low_cost.exists() else {}
    c005_decomposition = json.loads(args.c005_decomposition.read_text(encoding="utf-8")) if args.c005_decomposition.exists() else {}
    c008_c009_inlet = json.loads(args.c008_c009_inlet.read_text(encoding="utf-8")) if args.c008_c009_inlet.exists() else {}
    claims = build_claims(
        gate,
        read_csv(args.probe_mode_metrics),
        read_csv(args.zcenter_metrics),
        read_csv(args.voxel_groups),
        read_csv(args.zcenter_voxel_groups),
        build_chain,
        c002_longer_mean,
        c003_zorigin_ablation,
        c004_dx3_low_cost,
        c005_decomposition,
        c008_c009_inlet,
    )
    fieldnames = [
        "claim_id",
        "claim_readiness",
        "evidence_type",
        "section",
        "claim",
        "supporting_metrics",
        "source_paths",
        "allowed_use",
        "forbidden_use",
        "protocol_risks",
    ]
    write_csv(args.out_csv, claims, fieldnames)
    args.out_json.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "claims": claims}, indent=2), encoding="utf-8")
    write_markdown(args.out_md, claims, gate)
    print(json.dumps({"claims": len(claims), "out_csv": str(args.out_csv), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
