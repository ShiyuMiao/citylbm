#!/usr/bin/env python3
"""Generate a prioritized AIJ Case E official z=2 m follow-up sweep plan."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[4]
CASE_DIR = ROOT / "docs" / "experiments" / "casee"
RESULTS_DIR = CASE_DIR / "results"
OUT_JSON = RESULTS_DIR / "casee_candidate_sweep_plan.json"
OUT_CSV = RESULTS_DIR / "casee_candidate_sweep_plan.csv"
OUT_MD = RESULTS_DIR / "casee_candidate_sweep_plan.md"
CURRENT_BASELINE_CASE = CASE_DIR / "native_cases" / "casee_native_dx2_yn_sgs_gshift1_zoff1_nu0p001_pmodes_steps48000_spin12000"


FIELDNAMES = [
    "candidate_id",
    "priority",
    "candidate_class",
    "executable_now",
    "blocking_gates",
    "evidence_type",
    "dx_m",
    "steps",
    "spinup",
    "sample_dt",
    "ground_offset_cells",
    "origin_z_offset_m",
    "nu_lbm",
    "domain_decomposition",
    "command",
    "expected_artifacts",
    "rationale",
    "formal_result_policy",
    "pass_condition",
    "default_promotion_allowed",
    "forbidden_claim",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def deployed_fluidx3d_root(build_chain: Dict[str, Any]) -> Path | None:
    exe = ((build_chain.get("fluidx3d") or {}).get("executable") or {}).get("path")
    if not exe:
        return None
    exe_path = Path(str(exe))
    if exe_path.name.lower() != "fluidx3d.exe":
        return None
    if exe_path.parent.name.lower() == "bin":
        return exe_path.parent.parent
    return exe_path.parent


def deployed_baseline_matches(build_chain: Dict[str, Any]) -> bool:
    root = deployed_fluidx3d_root(build_chain)
    if root is None:
        return False
    pairs = [
        (root / "src" / "setup.cpp", CURRENT_BASELINE_CASE / "setup.cpp"),
        (root / "src" / "defines.hpp", CURRENT_BASELINE_CASE / "defines.hpp"),
        (root / "buildings.stl", CURRENT_BASELINE_CASE / "buildings.stl"),
    ]
    return all(left.exists() and right.exists() and sha256(left) == sha256(right) for left, right in pairs)


def csv_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "; ".join(str(v) for v in value)
    return str(value)


def native_command(
    *,
    dx: float,
    steps: int,
    spinup: int,
    sample_dt: int,
    ground_offset_cells: int,
    origin_z_offset_m: float,
    nu_lbm: float,
    domain: str = "2x2x1",
) -> str:
    dx_text = str(int(dx)) if float(dx).is_integer() else str(dx)
    cmd = [
        "python docs/experiments/casee/tools/generate_native_casee.py",
        f"--dx {dx_text}",
        f"--steps {steps}",
        f"--spinup {spinup}",
        f"--sample-dt {sample_dt}",
        f"--ground-offset-cells {ground_offset_cells}",
        f"--origin-z-offset-m {origin_z_offset_m}",
        f"--nu-lbm {nu_lbm}",
    ]
    parts = domain.lower().split("x")
    if len(parts) == 3:
        cmd.extend([f"--domain-x {parts[0]}", f"--domain-y {parts[1]}", f"--domain-z {parts[2]}"])
    return " ".join(cmd)


def candidate(
    *,
    candidate_id: str,
    priority: int,
    candidate_class: str,
    executable_now: bool,
    blocking_gates: Iterable[str],
    evidence_type: str,
    dx_m: float | str,
    steps: int | str,
    spinup: int | str,
    sample_dt: int | str,
    ground_offset_cells: int | str,
    origin_z_offset_m: float | str,
    nu_lbm: float | str,
    domain_decomposition: str,
    command: str,
    expected_artifacts: Iterable[str],
    rationale: str,
    formal_result_policy: str,
    pass_condition: str,
    default_promotion_allowed: bool,
    forbidden_claim: str,
) -> Dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "priority": priority,
        "candidate_class": candidate_class,
        "executable_now": executable_now,
        "blocking_gates": list(blocking_gates),
        "evidence_type": evidence_type,
        "dx_m": dx_m,
        "steps": steps,
        "spinup": spinup,
        "sample_dt": sample_dt,
        "ground_offset_cells": ground_offset_cells,
        "origin_z_offset_m": origin_z_offset_m,
        "nu_lbm": nu_lbm,
        "domain_decomposition": domain_decomposition,
        "command": command,
        "expected_artifacts": list(expected_artifacts),
        "rationale": rationale,
        "formal_result_policy": formal_result_policy,
        "pass_condition": pass_condition,
        "default_promotion_allowed": default_promotion_allowed,
        "forbidden_claim": forbidden_claim,
    }


def build_candidates(
    release_gate: Dict[str, Any],
    preflight: Dict[str, Any],
    dx1_readiness: Dict[str, Any],
    build_chain: Dict[str, Any],
    failure_atlas: Dict[str, Any],
) -> List[Dict[str, Any]]:
    metrics = release_gate.get("metrics") or {}
    blocked_gates = list(preflight.get("blocked_gates") or [])
    official_followup_allowed = bool(preflight.get("official_followup_run_allowed"))
    gpu_status = str((build_chain.get("gpu_runtime") or {}).get("status", ""))
    fluidx_status = str(
        (build_chain.get("fluidx3d") or build_chain.get("fluidx3d_binary") or build_chain.get("fluidx3d_executable") or {}).get("status", "")
    )
    gpu_ready = gpu_status.startswith("ready")
    fluidx_ready = fluidx_status.startswith("ready")
    native_source_compile_ready = bool(build_chain.get("native_source_compile_ready"))
    current_binary_rerun_available = bool(official_followup_allowed and gpu_ready and fluidx_ready and deployed_baseline_matches(build_chain))
    dx1_summary = dx1_readiness.get("summary") or {}
    dx1_headroom_ok = dx1_summary.get("dx1_memory_headroom_ok") is True
    common_forbidden = (
        "Do not claim predictive accuracy, mesh independence, LES improvement, or formal v0.4.0 readiness "
        "from this candidate unless the official release gate later passes."
    )
    formal_policy = (
        "Only the completed 80-probe official z=2 m raw_trilinear casee_probe_time_mean.csv may feed release_gate.json. "
        "Diagnostic sampling columns and z offsets cannot substitute for the formal result."
    )
    baseline_mae = metrics.get("mae_pp")
    baseline_r2 = metrics.get("r2")
    low_risk_phrase = "failure atlas" if failure_atlas.get("failure_modes") else "current diagnostics"
    c002_audit = read_json(RESULTS_DIR / "casee_c002_longer_mean_audit.json")
    c003_audit = read_json(RESULTS_DIR / "casee_c003_zorigin_ablation_audit.json")
    c004_audit = read_json(RESULTS_DIR / "casee_c004_dx3_low_cost_audit.json")
    c005_audit = read_json(RESULTS_DIR / "casee_c005_decomposition_audit.json")
    c008_audit = read_json(RESULTS_DIR / "casee_c008_c009_inlet_turbulence_audit.json")
    c014_residual = read_json(RESULTS_DIR / "casee_c014_residual_structure_audit.json")
    c016_leakage_guard = read_json(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json")
    c002_completed = c002_audit.get("evidence_type") == "newly_run"
    c003_completed = c003_audit.get("evidence_type") == "newly_run"
    c004_completed = c004_audit.get("evidence_type") == "newly_run"
    c005_completed = c005_audit.get("evidence_type") == "newly_run"
    c008_completed = c008_audit.get("evidence_type") == "newly_run"
    residual_groups = {item.get("group"): item for item in c014_residual.get("groups", [])}
    residual_affine = (c014_residual.get("affine_upper_bound") or {}).get("metrics") or {}
    residual_completed = c014_residual.get("status") == "completed_residual_structure_audit"
    c016_guard_passed = c016_leakage_guard.get("guard_passed") is True
    executable_native = official_followup_allowed and gpu_ready and fluidx_ready and native_source_compile_ready
    source_compile_blockers = [gate for gate in blocked_gates if gate not in {"rhino_gha_load", "vs_cpp_build_tools"}]
    if not gpu_ready:
        source_compile_blockers.append("gpu_runtime")
    if not fluidx_ready:
        source_compile_blockers.append("fluidx3d_binary")
    if not native_source_compile_ready:
        source_compile_blockers.append("native_source_compile_path")
    if not official_followup_allowed:
        source_compile_blockers.append("official_followup_preflight")
    current_binary_blockers = [gate for gate in source_compile_blockers if gate != "native_source_compile_path"]
    if not current_binary_rerun_available:
        current_binary_blockers.append("current_deployed_binary_not_matching_baseline")

    rows = [
        candidate(
            candidate_id="C001_dx2_zcenter_replicate_best_known",
            priority=1,
            candidate_class="current_compiled_binary_rerun",
            executable_now=current_binary_rerun_available,
            blocking_gates=current_binary_blockers,
            evidence_type="planned_or_completed_rerun",
            dx_m=2.0,
            steps=48000,
            spinup=12000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="1x1x1",
            command="cd E:/citylbm_buildchain/FluidX3D && ./bin/FluidX3D.exe",
            expected_artifacts=[
                "docs/experiments/casee/native_cases/<candidate>/citylbm_native_case_manifest.json",
                "docs/experiments/casee/results/casee_native_dx2_zcenter_rerun_<stamp>_probe_time_mean.csv",
                "docs/experiments/casee/results/casee_zcenter_rerun_consistency.json",
            ],
            rationale=(
                f"Rerun the currently deployed compiled z-center baseline before changing implementation; current MAE={baseline_mae}, R2={baseline_r2}."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Reproduces n=80 raw_trilinear official z=2 m metrics within audit tolerance.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C002_dx2_longer_mean_stability",
            priority=2,
            candidate_class="time_mean_stability",
            executable_now=executable_native,
            blocking_gates=source_compile_blockers,
            evidence_type=str(c002_audit.get("evidence_type", "planned_run")) if c002_completed else "planned_run",
            dx_m=2.0,
            steps=96000,
            spinup=24000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="2x2x1",
            command=native_command(
                dx=2,
                steps=96000,
                spinup=24000,
                sample_dt=2000,
                ground_offset_cells=1,
                origin_z_offset_m=1.0,
                nu_lbm=0.001,
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_c002_longer_mean_audit.json",
                "docs/experiments/casee/results/casee_c002_longer_mean_audit.md",
                "docs/experiments/casee/results/casee_c002_dx2_longer_mean_<stamp>_probe_time_mean.csv",
            ],
            rationale=(
                "Completed: longer averaging worsened the official metric. "
                f"status={c002_audit.get('status')}; R2={(c002_audit.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_R2={(c002_audit.get('metric_delta_vs_baseline') or {}).get('r2')}."
                if c002_completed
                else "Test whether negative R2 is partly caused by insufficient averaging rather than geometry/probe physics."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Pearson remains positive and R2 moves toward zero without diagnostic sampling substitution.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C003_dx2_no_zcenter_ablation",
            priority=3,
            candidate_class="protocol_ablation",
            executable_now=executable_native,
            blocking_gates=source_compile_blockers,
            evidence_type=str(c003_audit.get("evidence_type", "planned_run")) if c003_completed else "planned_run",
            dx_m=2.0,
            steps=48000,
            spinup=12000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=0.0,
            nu_lbm=0.001,
            domain_decomposition="2x2x1",
            command=native_command(
                dx=2,
                steps=48000,
                spinup=12000,
                sample_dt=2000,
                ground_offset_cells=1,
                origin_z_offset_m=0.0,
                nu_lbm=0.001,
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.json",
                "docs/experiments/casee/results/casee_c003_zorigin_ablation_audit.md",
                "docs/experiments/casee/results/casee_c003_dx2_no_zcenter_<stamp>_probe_time_mean.csv",
            ],
            rationale=(
                "Completed: removing z-center worsened the official metric and confirms z-origin sensitivity. "
                f"status={c003_audit.get('status')}; R2={(c003_audit.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_R2_vs_zcenter={(c003_audit.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}."
                if c003_completed
                else "Separate effective-ground and z-center sensitivity from actual wall/inlet physics."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Shows whether z-origin sensitivity is a diagnostic limitation rather than a stable accuracy fix.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C004_dx3_low_cost_direction_check",
            priority=4,
            candidate_class="low_cost_regression",
            executable_now=executable_native,
            blocking_gates=source_compile_blockers,
            evidence_type=str(c004_audit.get("evidence_type", "planned_run")) if c004_completed else "planned_run",
            dx_m=3.0,
            steps=48000,
            spinup=12000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=0.0,
            nu_lbm=0.001,
            domain_decomposition="2x2x1",
            command=native_command(
                dx=3,
                steps=48000,
                spinup=12000,
                sample_dt=2000,
                ground_offset_cells=1,
                origin_z_offset_m=0.0,
                nu_lbm=0.001,
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.json",
                "docs/experiments/casee/results/casee_c004_dx3_low_cost_audit.md",
                "docs/experiments/casee/results/casee_c004_dx3_low_cost_<stamp>_probe_time_mean.csv",
            ],
            rationale=(
                "Completed: dx=3 kept positive Pearson correlation but worsened MAE/R2 versus the z-center baseline. "
                f"status={c004_audit.get('status')}; R2={(c004_audit.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_R2_vs_zcenter={(c004_audit.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}."
                if c004_completed
                else "Cheaper control run for wind-direction, inlet, and lattice convention regression before expensive sweeps."
            ),
            formal_result_policy=formal_policy,
            pass_condition="No reversal of Pearson sign and no protocol mismatch in manifest/logs.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C005_dx2_domain_decomposition_ablation",
            priority=5,
            candidate_class="runtime_ablation",
            executable_now=executable_native,
            blocking_gates=source_compile_blockers,
            evidence_type=str(c005_audit.get("evidence_type", "planned_run")) if c005_completed else "planned_run",
            dx_m=2.0,
            steps=48000,
            spinup=12000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="4x1x1",
            command=native_command(
                dx=2,
                steps=48000,
                spinup=12000,
                sample_dt=2000,
                ground_offset_cells=1,
                origin_z_offset_m=1.0,
                nu_lbm=0.001,
                domain="4x1x1",
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_c005_decomposition_audit.json",
                "docs/experiments/casee/results/casee_c005_decomposition_audit.md",
                "docs/experiments/casee/results/casee_c005_dx2_decomp4x1x1_<stamp>_probe_time_mean.csv",
            ],
            rationale=(
                "Completed: 4x1x1 domain decomposition improved MAE/R2 but changed the result beyond reproducibility tolerances "
                "and reduced Pearson versus the z-center baseline. "
                f"status={c005_audit.get('status')}; R2={(c005_audit.get('candidate_metrics') or {}).get('r2')}; "
                f"delta_R2_vs_zcenter={(c005_audit.get('metric_delta_vs_zcenter_baseline') or {}).get('r2')}."
                if c005_completed
                else "Check whether GPU decomposition affects stability or output reproducibility before long runs."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Raw_trilinear metrics remain consistent with C001 within expected numerical variability.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C006_dx1_dry_allocation_then_short_smoke",
            priority=6,
            candidate_class="high_resolution_preflight",
            executable_now=False,
            blocking_gates=["user_confirmation_required", "dx1_memory_headroom"] + ([] if dx1_headroom_ok else ["gpu_memory_headroom_lt_25pct"]),
            evidence_type="blocked_until_user_confirmed_dry_run",
            dx_m=1.0,
            steps=48000,
            spinup=12000,
            sample_dt=4000,
            ground_offset_cells=1,
            origin_z_offset_m=0.5,
            nu_lbm=0.001,
            domain_decomposition="2x2x1",
            command=native_command(
                dx=1,
                steps=48000,
                spinup=12000,
                sample_dt=4000,
                ground_offset_cells=1,
                origin_z_offset_m=0.5,
                nu_lbm=0.001,
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_dx1_readiness_audit.json",
                "docs/experiments/casee/native_cases/<candidate>/citylbm_native_case_manifest.json",
            ],
            rationale="dx=1 m is the most direct grid-resolution follow-up but current memory headroom is high risk.",
            formal_result_policy=formal_policy,
            pass_condition="Only proceed after dry allocation confirms memory headroom and the user approves a long run.",
            default_promotion_allowed=False,
            forbidden_claim="Do not claim mesh independence from a dry allocation or single dx=1 run.",
        ),
        candidate(
            candidate_id="C007_default_off_wall_physics_implementation",
            priority=7,
            candidate_class="default_off_wall_followup_codegen",
            executable_now=False,
            blocking_gates=source_compile_blockers,
            evidence_type="blocked_until_gpu_ready",
            dx_m=2.0,
            steps=48000,
            spinup=12000,
            sample_dt=2000,
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="4x1x1",
            command=(
                "python docs/experiments/casee/tools/generate_native_casee.py --dx 2 --steps 48000 --spinup 12000 "
                "--sample-dt 2000 --ground-offset-cells 1 --origin-z-offset-m 1.0 --nu-lbm 0.001 "
                "--domain-x 4 --domain-y 1 --domain-z 1 --wall-model voxel_dilation --wall-dilation-cells 1 --no-subgrid"
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_wall_followup_codegen_gate.json",
                "docs/experiments/casee/native_cases/<candidate>/citylbm_native_case_manifest.json",
                "docs/experiments/casee/native_cases/<candidate>/casee_probe_time_mean.csv",
                "docs/experiments/casee/results/<candidate>_official_metrics.csv",
            ],
            rationale=f"{low_risk_phrase} points to near-wall and solid-corner errors. A default-off native voxel-dilation wall follow-up generator now exists, but it remains blocked by GPU/preflight and cannot be promoted before official metrics improve.",
            formal_result_policy=formal_policy,
            pass_condition="MAE clearly below the current near-20 pp level, R2>0, Pearson>0, Case A smoke regression passes.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C008_C015_full_plane_inlet_turbulence_sgs_sweep",
            priority=8,
            candidate_class="default_off_inlet_followup_codegen",
            executable_now=executable_native,
            blocking_gates=source_compile_blockers,
            evidence_type=str(c008_audit.get("evidence_type", "planned_run")) if c008_completed else "blocked_until_gpu_ready",
            dx_m="2.0",
            steps=">=48000",
            spinup=">=12000",
            sample_dt="<=2000",
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="4x1x1",
            command=(
                "python docs/experiments/casee/tools/generate_native_casee.py --dx 2 --steps 48000 --spinup 12000 "
                "--sample-dt 2000 --ground-offset-cells 1 --origin-z-offset-m 1.0 --nu-lbm 0.001 "
                "--domain-x 4 --domain-y 1 --domain-z 1 --inlet-turbulence-mode k_synthetic_fullplane "
                "--inlet-turbulence-scale 2.00 --no-subgrid"
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_inlet_followup_codegen_gate.json",
                "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.json",
                "docs/experiments/casee/results/casee_c008_c009_inlet_turbulence_audit.md",
                "docs/experiments/casee/native_cases/<candidate>/citylbm_native_case_manifest.json",
                "docs/experiments/casee/native_cases/<candidate>/casee_probe_time_mean.csv",
                "docs/experiments/casee/results/<candidate>_official_metrics.csv",
            ],
            rationale=(
                "Completed: C008-C015 AF-k synthetic full-plane inlet and SGS ablation candidates substantially improved official-height MAE/R2/Pearson, "
                "but R2 remains negative. C014 no-SGS scale 2.00 is the best diagnostic candidate and C015 scale 2.50 rolls back, so the sweep is diagnostic-only. "
                f"status={c008_audit.get('status')}; best_R2={((c008_audit.get('best_candidate') or {}).get('candidate_metrics') or {}).get('r2')}; "
                f"best_MAE={((c008_audit.get('best_candidate') or {}).get('candidate_metrics') or {}).get('mae_pp')}."
                if c008_completed
                else "The generator already provides a default-off AF_caseE-k full-plane inlet follow-up. It remains blocked by GPU/preflight and cannot support default promotion before official metrics pass."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Official raw_trilinear metric improves without relying on non-raw sampling or z-height substitution.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
        candidate(
            candidate_id="C016_residual_targeted_wall_inlet_channel_response",
            priority=9,
            candidate_class="default_off_c016_residual_target_codegen",
            executable_now=False,
            blocking_gates=source_compile_blockers + ([] if c016_guard_passed else ["c016_calibration_leakage_guard_not_passed"]),
            evidence_type="blocked_until_gpu_ready" if residual_completed else "blocked_until_residual_audit",
            dx_m="2.0",
            steps=">=48000",
            spinup=">=12000",
            sample_dt="<=2000",
            ground_offset_cells=1,
            origin_z_offset_m=1.0,
            nu_lbm=0.001,
            domain_decomposition="4x1x1",
            command=(
                "python docs/experiments/casee/tools/generate_native_casee.py --dx 2 --steps 48000 --spinup 12000 "
                "--sample-dt 2000 --ground-offset-cells 1 --origin-z-offset-m 1.0 --nu-lbm 0.001 "
                "--domain-x 4 --domain-y 1 --domain-z 1 --inlet-turbulence-mode k_synthetic_fullplane "
                "--inlet-turbulence-scale 2.00 --residual-target-mode c014_channel_response --residual-target-scale 1.00 --no-subgrid"
            ),
            expected_artifacts=[
                "docs/experiments/casee/results/casee_c016_codegen_gate.json",
                "docs/experiments/casee/results/casee_c014_residual_structure_audit.json",
                "docs/experiments/casee/native_cases/<c016>/citylbm_native_case_manifest.json",
                "docs/experiments/casee/native_cases/<c016>/casee_probe_time_mean.csv",
                "docs/experiments/casee/results/<c016>_probe_time_mean.csv",
                "docs/experiments/casee/results/<c016>_official_metrics.json",
            ],
            rationale=(
                "C014 is the current best diagnostic candidate but residual structure blocks a formal accuracy claim: "
                f"downstream_R2={(residual_groups.get('downstream_y_lt_0_inferred') or {}).get('r2')}; "
                f"official_high_bias_pp={(residual_groups.get('official_high_ge_0p6') or {}).get('bias_pp')}; "
                f"posthoc_affine_upper_bound_R2={residual_affine.get('r2')}. "
                "The next useful implementation must recover high-speed corridor probes without overpredicting sheltered low-speed probes. "
                f"C016 leakage guard passed={c016_guard_passed}; official RS targets must not be used for post-hoc calibration."
            ),
            formal_result_policy=formal_policy,
            pass_condition="Official raw_trilinear z=2 m R2 becomes positive, Pearson remains positive, MAE stays below C014, and Case A smoke regression passes.",
            default_promotion_allowed=False,
            forbidden_claim=common_forbidden,
        ),
    ]
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row[key]) for key in FIELDNAMES})


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    metrics = payload["current_official_metrics"]
    lines = [
        "# Case E Candidate Sweep Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- Plan generated: {payload['candidate_sweep_plan_generated']}",
        f"- Evidence type: `{payload['evidence_type']}`",
        f"- Claim readiness: `{payload['claim_readiness']}`",
        f"- Formal accuracy claim supported: {payload['formal_accuracy_claim_supported']}",
        f"- Formal release allowed: {payload['formal_release_allowed']}",
        f"- Candidate count: {payload['candidate_count']}",
        f"- Executable-now count: {payload['executable_now_count']}",
        "",
        "## Current Official z=2 m Metric",
        "",
        f"- MAE: {metrics.get('mae_pp')} pp",
        f"- R2: {metrics.get('r2')}",
        f"- Pearson: {metrics.get('pearson')}",
        f"- Sampling mode: `{metrics.get('sampling_mode')}`",
        "",
        "## Candidates",
        "",
        "| priority | candidate | executable now | class | blocking gates | pass condition |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in payload["candidates"]:
        lines.append(
            f"| {row['priority']} | `{row['candidate_id']}` | {row['executable_now']} | "
            f"{row['candidate_class']} | `{'; '.join(row['blocking_gates'])}` | {row['pass_condition']} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        payload["boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    release_gate = read_json(RESULTS_DIR / "release_gate.json")
    preflight = read_json(RESULTS_DIR / "casee_official_run_preflight.json")
    dx1_readiness = read_json(RESULTS_DIR / "casee_dx1_readiness_audit.json")
    build_chain = read_json(RESULTS_DIR / "build_chain_manifest.json")
    failure_atlas = read_json(RESULTS_DIR / "casee_failure_mode_atlas.json")
    candidates = build_candidates(release_gate, preflight, dx1_readiness, build_chain, failure_atlas)
    passed = len(candidates) >= 8 and any(row["candidate_id"] == "C001_dx2_zcenter_replicate_best_known" for row in candidates)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_sweep_plan_generated": passed,
        "evidence_type": "newly_run",
        "claim_readiness": "paper_ready_followup_plan; blocked formal accuracy release",
        "formal_accuracy_claim_supported": False,
        "formal_release_allowed": release_gate.get("formal_release_allowed"),
        "recommended_tag": release_gate.get("recommended_tag"),
        "current_official_metrics": release_gate.get("metrics") or {},
        "candidate_count": len(candidates),
        "executable_now_count": sum(1 for row in candidates if row["executable_now"]),
        "candidates": candidates,
        "source_artifacts": [
            rel(RESULTS_DIR / "release_gate.json"),
            rel(RESULTS_DIR / "casee_official_run_preflight.json"),
            rel(RESULTS_DIR / "casee_dx1_readiness_audit.json"),
            rel(RESULTS_DIR / "build_chain_manifest.json"),
            rel(RESULTS_DIR / "casee_failure_mode_atlas.json"),
            rel(RESULTS_DIR / "casee_c016_residual_target_leakage_guard.json"),
        ],
        "boundary": (
            "This plan ranks future official z=2 m follow-up candidates and records their commands, blockers, "
            "and pass conditions. It does not start FluidX3D, does not add solver-output evidence, and does not "
            "support formal v0.4.0 or predictive-accuracy claims."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(OUT_CSV, candidates)
    write_markdown(OUT_MD, payload)
    print(json.dumps({"candidate_sweep_plan_generated": passed, "out_json": rel(OUT_JSON)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
