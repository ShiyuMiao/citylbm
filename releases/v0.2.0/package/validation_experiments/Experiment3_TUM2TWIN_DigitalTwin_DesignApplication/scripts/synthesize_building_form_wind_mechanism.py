from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path.cwd()
FIG = ROOT / "figures"
MAN = ROOT / "manifests"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
DRAFT = ROOT.parents[4] / "academic-paper-writer" / "paper-drafts"


FEATURE_LABELS = {
    "footprint_area_m2": "footprint area",
    "mean_height_m": "mean height",
    "height_to_sqrt_area": "height/sqrt(area)",
    "compactness_p2_over_a": "perimeter^2/area",
    "elongation_ratio": "elongation ratio",
    "local_built_fraction_r30m": "local built fraction r30m",
    "sector_enclosure_ratio_r50m": "sector enclosure r50m",
    "relative_enclosure_score": "combined enclosure score",
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv(path: Path, rows_to_add: list[dict[str, str]], key: str, fieldnames: list[str]) -> None:
    rows = read_csv_rows(path)
    existing = {row.get(key, ""): row for row in rows}
    for row in rows_to_add:
        existing[row[key]] = row
    write_csv(path, list(existing.values()), fieldnames)


def f3(value: object) -> str:
    return f"{float(value):.3f}"


def f4(value: object) -> str:
    return f"{float(value):.4f}"


def pick(df: pd.DataFrame, **kwargs: str) -> pd.Series:
    mask = pd.Series([True] * len(df))
    for key, value in kwargs.items():
        mask &= df[key] == value
    out = df[mask]
    if out.empty:
        raise ValueError(f"missing row for {kwargs}")
    return out.iloc[0]


def classify_feature(local_mean_rho: float, local_range_rho: float, recovery_rho: float) -> tuple[str, str]:
    if local_mean_rho <= -0.30 and local_range_rho <= -0.30:
        return (
            "primary_shelter_suppressor",
            "higher values are associated with lower local-context mean VR and weaker wind-sector response",
        )
    if local_mean_rho <= -0.20 or local_range_rho <= -0.20:
        return (
            "secondary_shelter_suppressor",
            "higher values are associated with lower recovery or reduced directional response, but the effect is weaker",
        )
    if recovery_rho >= 0.20 and abs(local_mean_rho) < 0.15:
        return (
            "conditional_recovery_descriptor",
            "the variable is weak as a direct predictor but helps distinguish high-recovery subgroups",
        )
    return (
        "weak_direct_predictor",
        "the variable should not be used alone as a deterministic wind-response predictor",
    )


def build_parameter_matrix() -> pd.DataFrame:
    robust = pd.read_csv(FIG / "basic_morphology_multivariate_robustness.csv")
    direction = pd.read_csv(FIG / "morphology_directional_fingerprint_feature_correlations.csv")
    recovery = pd.read_csv(FIG / "morphology_recovery_top_bottom_contrast.csv")
    rows: list[dict[str, object]] = []
    for feature, label in FEATURE_LABELS.items():
        local_mean = pick(direction, target="local_context_mean_vr", feature=feature)
        local_range = pick(direction, target="local_context_range_vr", feature=feature)
        reactivity = pick(direction, target="directional_reactivity_ratio", feature=feature)
        recovery_row = recovery[recovery["feature"] == feature].iloc[0]
        robust_mean = pick(
            robust,
            analysis_zone="local_context_20_50m",
            target="directional_mean_vr",
            feature=feature,
        )
        robust_range = pick(
            robust,
            analysis_zone="local_context_20_50m",
            target="directional_range_mean_vr",
            feature=feature,
        )
        role, mechanism = classify_feature(
            float(local_mean["spearman_rho"]),
            float(local_range["spearman_rho"]),
            float(recovery_row["spearman_rho_with_recovery_delta"]),
        )
        rows.append(
            {
                "evidence_type": "newly_run + blocked",
                "feature": feature,
                "feature_label": label,
                "mechanism_role": role,
                "local_context_mean_vr_spearman_rho": float(local_mean["spearman_rho"]),
                "local_context_mean_vr_p": float(local_mean["p_value"]),
                "local_context_range_vr_spearman_rho": float(local_range["spearman_rho"]),
                "local_context_range_vr_p": float(local_range["p_value"]),
                "directional_reactivity_ratio_spearman_rho": float(reactivity["spearman_rho"]),
                "recovery_delta_spearman_rho": float(recovery_row["spearman_rho_with_recovery_delta"]),
                "top_minus_bottom_recovery_feature_delta": float(recovery_row["top_minus_bottom"]),
                "local_mean_ridge_coef": float(robust_mean["ridge_standardized_coef"]),
                "local_mean_permutation_r2_drop": float(robust_mean["permutation_r2_drop"]),
                "local_range_ridge_coef": float(robust_range["ridge_standardized_coef"]),
                "local_range_permutation_r2_drop": float(robust_range["permutation_r2_drop"]),
                "paper_safe_mechanism": mechanism,
                "claim_boundary": "sample-internal FluidX3D/digital-twin screening; not field-validated causality or universal threshold",
            }
        )
    return pd.DataFrame(rows)


def build_stage_matrix() -> pd.DataFrame:
    summary = pd.read_csv(FIG / "morphology_stage_transition_summary.csv")
    stage = pd.read_csv(FIG / "morphology_directional_fingerprint_stage_summary.csv")
    arche = pd.read_csv(FIG / "morphology_form_response_archetype_summary.csv")
    rows = [
        {
            "evidence_type": "newly_run",
            "mechanism_layer": "stage_saturation",
            "indicator": "near_facade_0_20m_mean_vr / stagnation",
            "value": f"{f4(pick(summary, metric='near_facade_0_20m_mean_vr')['mean'])} / {f4(pick(summary, metric='near_facade_stagnation_ratio')['mean'])}",
            "interpretation": "the immediate facade-adjacent band is almost fully low-speed and is a weak discriminator of form differences",
        },
        {
            "evidence_type": "newly_run",
            "mechanism_layer": "local_context_recovery",
            "indicator": "local_context_20_50m_mean_vr / local_minus_near_delta",
            "value": f"{f4(pick(summary, metric='local_context_20_50m_mean_vr')['mean'])} / {f4(pick(summary, metric='local_minus_near_recovery_delta_vr')['mean'])}",
            "interpretation": "the 20-50 m band exposes morphology-differentiated recovery that is hidden near the facade",
        },
        {
            "evidence_type": "newly_run + blocked",
            "mechanism_layer": "directional_reactivity",
            "indicator": "persistent/recovery/reactive local-context directional range",
            "value": (
                f"{f4(pick(stage, stage_transition_class='persistent_shelter')['mean_directional_range_vr'])} / "
                f"{f4(pick(stage, stage_transition_class='near_to_context_recovery')['mean_directional_range_vr'])} / "
                f"{f4(pick(stage, stage_transition_class='directionally_reactive')['mean_directional_range_vr'])}"
            ),
            "interpretation": "useful recovery includes wind-sector response, not only higher mean VR",
        },
        {
            "evidence_type": "newly_run + blocked",
            "mechanism_layer": "archetype_contrast",
            "indicator": "best/worst archetype recovery delta",
            "value": (
                f"{arche.sort_values('recovery_rank').iloc[0]['archetype']} "
                f"{f4(arche.sort_values('recovery_rank').iloc[0]['context_recovery_delta_vr'])} / "
                f"{arche.sort_values('recovery_rank').iloc[-1]['archetype']} "
                f"{f4(arche.sort_values('recovery_rank').iloc[-1]['context_recovery_delta_vr'])}"
            ),
            "interpretation": "combined morphology groups explain wind response better than single size or shape variables",
        },
    ]
    return pd.DataFrame(rows)


def create_panel(param: pd.DataFrame, stage: pd.DataFrame) -> None:
    order = param.sort_values("local_context_mean_vr_spearman_rho")["feature_label"].tolist()
    plot_df = param.set_index("feature_label").loc[order]
    stage_df = pd.read_csv(FIG / "morphology_directional_fingerprint_stage_summary.csv")
    arche = pd.read_csv(FIG / "morphology_form_response_archetype_summary.csv").sort_values("recovery_rank")

    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9})
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))

    ax = axes[0]
    y = range(len(plot_df))
    ax.barh(y, plot_df["local_context_mean_vr_spearman_rho"], color="#4C78A8", label="mean VR")
    ax.scatter(plot_df["local_context_range_vr_spearman_rho"], y, color="#F58518", label="directional range", zorder=3)
    ax.axvline(0, color="#444444", linewidth=0.8)
    ax.set_yticks(list(y))
    ax.set_yticklabels(order)
    ax.set_xlabel("Spearman rho")
    ax.set_title("Morphology vs 20-50 m wind response")
    ax.legend(frameon=False, loc="lower right")

    ax = axes[1]
    x = range(len(stage_df))
    ax.bar(x, stage_df["mean_local_context_vr"], color="#54A24B", label="mean VR")
    ax.plot(x, stage_df["mean_directional_range_vr"], color="#E45756", marker="o", label="directional range")
    ax.set_xticks(list(x))
    ax.set_xticklabels(stage_df["stage_transition_class"], rotation=35, ha="right")
    ax.set_title("Stage classes")
    ax.set_ylabel("VR")
    ax.legend(frameon=False)

    ax = axes[2]
    ax.barh(arche["archetype"], arche["context_recovery_delta_vr"], color="#72B7B2")
    ax.set_xlabel("20-50 m minus 0-20 m VR")
    ax.set_title("Archetype recovery contrast")
    ax.invert_yaxis()

    fig.suptitle("Experiment 3 building-form wind-environment mechanism synthesis", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "building_form_wind_mechanism_synthesis_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def upsert_manifests() -> None:
    evidence_rows = [
        {
            "claim": "Building-form wind mechanism synthesis integrates stage saturation, local-context recovery, directional reactivity and morphology descriptors from archived FluidX3D/morphology statistics.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "reports/building_form_wind_mechanism_synthesis.md; figures/building_form_wind_mechanism_parameter_matrix.csv",
        },
        {
            "claim": "Building-form mechanism conclusion paragraphs were drafted as sample-internal screening evidence rather than field-validated causal or universal threshold claims.",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "paper_text/building_form_wind_mechanism_conclusion_zh.md; paper_text/building_form_wind_mechanism_conclusion_en.md",
        },
    ]
    upsert_csv(MAN / "evidence_inventory.csv", evidence_rows, "claim", ["claim", "evidence_type", "source"])

    claim_rows = [
        {
            "claim": "The 20-50 m local-context band is the main diagnostic scale for building-form differences in the screened campus block.",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/building_form_wind_mechanism_stage_matrix.csv; figures/morphology_stage_transition_summary.csv",
            "paper_safe_claim": "Near-facade sheltering is saturated, while 20-50 m local context reveals recovery differences.",
            "claim_boundary": "sample-internal screening; not a universal buffer-distance rule",
        },
        {
            "claim": "Enclosure, vertical massing and wind-sector reactivity are more informative than single footprint or plan-shape variables.",
            "evidence_type": "newly_run + blocked",
            "source_artifact": "figures/building_form_wind_mechanism_parameter_matrix.csv; figures/morphology_directional_fingerprint_feature_correlations.csv",
            "paper_safe_claim": "Mean height, sector enclosure and combined enclosure show the strongest negative links with local-context VR/range; footprint and elongation are conditional descriptors.",
            "claim_boundary": "screening descriptor evidence; not field-validated causality",
        },
    ]
    write_csv(
        MAN / "building_form_wind_mechanism_claims.csv",
        claim_rows,
        ["claim", "evidence_type", "source_artifact", "paper_safe_claim", "claim_boundary"],
    )

    key_row = {
        "evidence_type": "newly_run + preexisting_artifact + blocked",
        "claim_layer": "Building-form wind mechanism synthesis",
        "metric": "near/local VR / enclosure-height correlations / stage directional range / best subgroup rule",
        "value": "0.0032/0.0056; rho sector=-0.396, height=-0.351; persistent/recovery/reactive range=0.0016/0.0189/0.0214; best rule n=5 recovery=0.0065",
        "source_artifact": "figures/building_form_wind_mechanism_parameter_matrix.csv; reports/building_form_wind_mechanism_synthesis.md",
        "paper_safe_claim": "The campus wind response is best interpreted as a staged morphology mechanism: near-facade low-speed saturation, 20-50 m local-context recovery, and wind-sector directional reactivity.",
    }
    upsert_csv(
        FIG / "final_integrated_key_result_matrix.csv",
        [key_row],
        "claim_layer",
        ["evidence_type", "claim_layer", "metric", "value", "source_artifact", "paper_safe_claim"],
    )

    if (DRAFT / "experiment3_claim_verification.csv").exists():
        rows = read_csv_rows(DRAFT / "experiment3_claim_verification.csv")
        fieldnames = list(rows[0].keys()) if rows else ["claim_layer", "evidence_type", "source", "value", "paper_safe_claim", "claim_readiness"]
        row = {
            "claim_layer": "module_claim_R3f",
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "source": "figures/building_form_wind_mechanism_parameter_matrix.csv; reports/building_form_wind_mechanism_synthesis.md",
            "value": "paper_ready_with_boundary",
            "paper_safe_claim": "Building-form effects should be framed as a staged screening mechanism across near-facade sheltering, local-context recovery and directional reactivity.",
            "claim_readiness": "paper_ready_with_boundary",
        }
        rows = [item for item in rows if item.get("claim_layer") != "module_claim_R3f"]
        rows.append({name: row.get(name, "") for name in fieldnames})
        write_csv(DRAFT / "experiment3_claim_verification.csv", rows, fieldnames)


def write_reports(param: pd.DataFrame, stage: pd.DataFrame) -> None:
    top_suppressors = param.sort_values("local_context_mean_vr_spearman_rho").head(4)
    conditional = param[param["mechanism_role"] == "conditional_recovery_descriptor"]
    stage_text = "\n".join(
        f"- {row['mechanism_layer']}: {row['indicator']} = {row['value']} ({row['interpretation']})"
        for _, row in stage.iterrows()
    )
    suppressor_text = "\n".join(
        f"- {row['feature_label']}: rho_mean={f3(row['local_context_mean_vr_spearman_rho'])}, "
        f"rho_range={f3(row['local_context_range_vr_spearman_rho'])}, role={row['mechanism_role']}"
        for _, row in top_suppressors.iterrows()
    )
    conditional_text = "\n".join(
        f"- {row['feature_label']}: recovery rho={f3(row['recovery_delta_spearman_rho'])}, "
        f"local mean rho={f3(row['local_context_mean_vr_spearman_rho'])}"
        for _, row in conditional.iterrows()
    ) or "- No conditional descriptors passed the current rule."

    report = f"""# Building-Form Wind-Environment Mechanism Synthesis

evidence_type: newly_run + preexisting_artifact + blocked

## Purpose

This synthesis turns the existing morphology, FluidX3D and directional-fingerprint
outputs into a paper-facing architectural mechanism model. It does not add a
new CFD run. It integrates the same 101 retained building components and asks
which basic morphology descriptors are useful for explaining the screened
campus wind response.

## Mechanism Layers

{stage_text}

## Strongest Suppression Descriptors

{suppressor_text}

## Conditional Form Descriptors

{conditional_text}

## Paper-Ready New Understanding

The main new understanding is a scale-dependent mechanism rather than a single
parameter law. The 0-20 m facade-adjacent band is nearly saturated by low speed,
so it is useful for identifying pedestrian sheltering but weak for separating
building types. The 20-50 m local-context band reveals whether the local
configuration recovers wind speed and whether that recovery has a wind-sector
fingerprint. In this band, mean height, sector enclosure and combined enclosure
are the most consistent suppressors of mean VR and directional range. Footprint
area, elongation and perimeter-area compactness are weak direct predictors, but
they become useful when read as conditional descriptors of low-relative-height,
elongated or articulated recovery subgroups.

## Claim Boundary

Supported: sample-internal digital-twin screening interpretation of building
form, local enclosure and directional response for the TUM Downtown core campus
block.

Not supported: universal morphology thresholds, field-validated causal laws,
annual wind-comfort compliance, pollutant dispersion or transferable design
optimization rules without additional cases and measurements.
"""
    write_text(REP / "building_form_wind_mechanism_synthesis.md", report)

    zh = """# 建筑形式-风环境机制结论段落

evidence_type: newly_run + preexisting_artifact + blocked

本实验在传统街道峡谷和建筑围合研究结论的基础上，得到的新增认识不是某一个建筑形态参数可以单独决定风环境，而是校园核心街区的风环境响应具有明显的尺度分层。0-20 m 近立面带几乎处于低风速饱和状态，适合识别行人层遮蔽和滞风风险，但对建筑形式差异的区分能力有限。相比之下，20-50 m 局地形态上下文带能够揭示被近立面低速饱和掩盖的风速恢复差异，并进一步显示这种恢复是否具有来流扇区响应。换言之，数字孪生风环境分析不应只问“建筑越高或越密是否越差”，而应同时判断低速遮蔽是否能从近立面阶段过渡到局地恢复阶段，以及恢复是否与有效风向通道相耦合。

从形态参数看，平均高度、50 m 扇区围合度和复合围合分数是最稳定的抑制性描述符，它们与 20-50 m 局地平均风速比和方向性响应范围均呈负相关。相反，建筑 footprint、延展率和周长-面积紧凑度并不是可靠的单变量预测器；它们的价值主要体现在条件组合中。例如，较低相对竖向尺度、较强平面线性和特定局地围合状态共同出现时，更容易形成从近立面遮蔽向局地风速恢复的转变。这一结果把传统“围合削弱通风”的一般认识推进到真实校园数字孪生场景中：通风恢复不仅取决于开敞或孔隙面积，还取决于相对竖向体量、局地围合连续性、动量入口和风向扇区反应之间是否匹配。

上述结论应作为 FluidX3D/数字孪生筛查证据使用，而不是实测验证后的因果定律或通用设计阈值。它的论文价值在于为校园更新和建筑群微气候设计提供一种可审计的解释框架：先识别近立面低速饱和，再在 20-50 m 局地上下文中比较形态恢复能力，最后检查恢复是否具有方向性风场响应。"""
    en = """# Building-Form Wind-Environment Mechanism Conclusion

evidence_type: newly_run + preexisting_artifact + blocked

The added insight of Experiment 3 is not that a single morphology variable controls the wind field. Instead, the real campus block exhibits a scale-dependent response mechanism. The 0-20 m facade-adjacent band is almost saturated by low-speed sheltering, so it is useful for detecting pedestrian stagnation but weak for distinguishing building-form effects. The 20-50 m local-context band exposes the recovery signal hidden by the near-facade saturation and shows whether that recovery carries a wind-sector fingerprint. Digital-twin wind analysis should therefore ask not only whether buildings are high or dense, but whether local flow can transition from near-facade sheltering to contextual recovery and whether that recovery is aligned with effective inflow sectors.

Among the basic descriptors, mean height, 50 m sector enclosure and the combined enclosure score are the most consistent suppressors of local-context mean VR and directional range. In contrast, footprint area, elongation and perimeter-area compactness are weak as direct single-variable predictors. Their value is conditional: low relative vertical scale, elongated plan form and particular local enclosure states jointly identify subgroups with stronger near-to-context recovery. This refines the traditional enclosure-ventilation argument for a real digital-twin campus block. Ventilation recovery depends not simply on open area or porosity, but on the coupling among relative vertical massing, plan continuity, momentum-entry paths and wind-sector reactivity.

This conclusion should be used as FluidX3D/digital-twin screening evidence rather than as a field-validated causal law or universal design threshold. Its contribution is an auditable interpretation framework for campus wind design: identify near-facade low-speed saturation, compare morphology-dependent recovery in the 20-50 m local-context band, and then test whether the recovery has directional wind-response support."""
    write_text(PAPER / "building_form_wind_mechanism_conclusion_zh.md", zh)
    write_text(PAPER / "building_form_wind_mechanism_conclusion_en.md", en)


def main() -> None:
    for folder in [FIG, MAN, REP, PAPER, DRAFT]:
        folder.mkdir(parents=True, exist_ok=True)
    param = build_parameter_matrix()
    stage = build_stage_matrix()
    param.to_csv(FIG / "building_form_wind_mechanism_parameter_matrix.csv", index=False, encoding="utf-8", lineterminator="\n")
    stage.to_csv(FIG / "building_form_wind_mechanism_stage_matrix.csv", index=False, encoding="utf-8", lineterminator="\n")
    create_panel(param, stage)
    write_reports(param, stage)
    upsert_manifests()
    print("building_form_mechanism_parameters", len(param))
    print("building_form_mechanism_layers", len(stage))
    print("wrote building-form wind mechanism synthesis")


if __name__ == "__main__":
    main()
