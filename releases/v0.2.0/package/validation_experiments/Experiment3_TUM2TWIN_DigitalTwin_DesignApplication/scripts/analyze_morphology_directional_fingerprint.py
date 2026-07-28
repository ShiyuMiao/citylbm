from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kruskal, spearmanr


ROOT = Path.cwd()
FIG = ROOT / "figures"
REP = ROOT / "reports"
PAPER = ROOT / "paper_text"
MAN = ROOT / "manifests"


FEATURES = [
    "footprint_area_m2",
    "mean_height_m",
    "height_to_sqrt_area",
    "compactness_p2_over_a",
    "elongation_ratio",
    "local_built_fraction_r30m",
    "sector_enclosure_ratio_r50m",
    "relative_enclosure_score",
]

PRETTY_FEATURES = {
    "footprint_area_m2": "footprint area",
    "mean_height_m": "mean height",
    "height_to_sqrt_area": "H/sqrt(A)",
    "compactness_p2_over_a": "compactness",
    "elongation_ratio": "elongation",
    "local_built_fraction_r30m": "built fraction 30 m",
    "sector_enclosure_ratio_r50m": "sector enclosure 50 m",
    "relative_enclosure_score": "relative enclosure",
}

CLASS_ORDER = [
    "persistent_shelter",
    "mixed_low_speed_context",
    "near_to_context_recovery",
    "directionally_reactive",
]

CLASS_COLORS = {
    "persistent_shelter": "#5e6472",
    "mixed_low_speed_context": "#7aa6c2",
    "near_to_context_recovery": "#2a9d8f",
    "directionally_reactive": "#e76f51",
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upsert_csv_row(path: Path, key_field: str, row: dict[str, object], fieldnames: list[str]) -> None:
    rows: list[dict[str, object]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    rows = [item for item in rows if item.get(key_field) != row[key_field]]
    rows.append(row)
    write_csv(path, rows, fieldnames)


def build_component_fingerprint() -> pd.DataFrame:
    wind = pd.read_csv(FIG / "basic_morphology_wind_response_by_component.csv")
    stage = pd.read_csv(FIG / "morphology_stage_transition_by_component.csv")[
        ["component_id", "stage_transition_class", "archetype", "context_recovery_delta_vr"]
    ]
    local = wind[wind["analysis_zone"] == "local_context_20_50m"].copy()
    if local.empty:
        raise ValueError("No local_context_20_50m rows found")

    agg = (
        local.groupby("component_id")
        .agg(
            evidence_type=("evidence_type", "first"),
            local_context_mean_vr=("mean_vr", "mean"),
            local_context_min_vr=("mean_vr", "min"),
            local_context_max_vr=("mean_vr", "max"),
            local_context_range_vr=("mean_vr", lambda s: float(s.max() - s.min())),
            local_context_std_vr=("mean_vr", "std"),
            local_context_p95_mean_vr=("p95_vr", "mean"),
            local_context_stagnation_mean=("stagnation_ratio_vr_lt_0p2", "mean"),
            sample_open_cells=("sample_open_cells", "mean"),
            enclosure_class=("enclosure_class", "first"),
            footprint_area_m2=("footprint_area_m2", "first"),
            mean_height_m=("mean_height_m", "first"),
            height_to_sqrt_area=("height_to_sqrt_area", "first"),
            compactness_p2_over_a=("compactness_p2_over_a", "first"),
            elongation_ratio=("elongation_ratio", "first"),
            local_built_fraction_r30m=("local_built_fraction_r30m", "first"),
            sector_enclosure_ratio_r50m=("sector_enclosure_ratio_r50m", "first"),
            relative_enclosure_score=("relative_enclosure_score", "first"),
        )
        .reset_index()
    )
    best = local.loc[local.groupby("component_id")["mean_vr"].idxmax(), ["component_id", "wind_deg", "mean_vr"]]
    best = best.rename(columns={"wind_deg": "best_wind_deg", "mean_vr": "best_wind_mean_vr"})
    worst = local.loc[local.groupby("component_id")["mean_vr"].idxmin(), ["component_id", "wind_deg", "mean_vr"]]
    worst = worst.rename(columns={"wind_deg": "worst_wind_deg", "mean_vr": "worst_wind_mean_vr"})
    out = agg.merge(best, on="component_id").merge(worst, on="component_id")
    out["directional_reactivity_ratio"] = out["local_context_range_vr"] / (
        out["local_context_mean_vr"] + 1e-12
    )
    out = out.merge(stage, on="component_id", how="left")
    out["evidence_type"] = "newly_run"
    return out


def build_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target in [
        "local_context_mean_vr",
        "local_context_range_vr",
        "directional_reactivity_ratio",
    ]:
        for feature in FEATURES:
            rho, p_value = spearmanr(df[feature], df[target], nan_policy="omit")
            rows.append(
                {
                    "evidence_type": "newly_run + blocked",
                    "target": target,
                    "feature": feature,
                    "spearman_rho": float(rho),
                    "p_value": float(p_value),
                    "n_components": int(df[[feature, target]].dropna().shape[0]),
                    "claim_boundary": "sample-internal morphology screening; not field-validated causality",
                }
            )
    return pd.DataFrame(rows)


def build_stage_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    rows = []
    for klass in CLASS_ORDER:
        sub = df[df["stage_transition_class"] == klass]
        if sub.empty:
            continue
        rows.append(
            {
                "evidence_type": "newly_run + blocked",
                "stage_transition_class": klass,
                "n_components": int(len(sub)),
                "mean_local_context_vr": float(sub["local_context_mean_vr"].mean()),
                "median_local_context_vr": float(sub["local_context_mean_vr"].median()),
                "mean_directional_range_vr": float(sub["local_context_range_vr"].mean()),
                "median_directional_range_vr": float(sub["local_context_range_vr"].median()),
                "mean_directional_reactivity_ratio": float(sub["directional_reactivity_ratio"].mean()),
                "median_directional_reactivity_ratio": float(sub["directional_reactivity_ratio"].median()),
                "mean_recovery_delta_vr": float(sub["context_recovery_delta_vr"].mean()),
                "median_recovery_delta_vr": float(sub["context_recovery_delta_vr"].median()),
            }
        )
    summary = pd.DataFrame(rows)
    groups_range = [
        group["local_context_range_vr"].dropna().values
        for _, group in df.groupby("stage_transition_class")
        if len(group) >= 2
    ]
    groups_ratio = [
        group["directional_reactivity_ratio"].dropna().values
        for _, group in df.groupby("stage_transition_class")
        if len(group) >= 2
    ]
    stats = {
        "kruskal_range_stat": float(kruskal(*groups_range).statistic),
        "kruskal_range_p": float(kruskal(*groups_range).pvalue),
        "kruskal_ratio_stat": float(kruskal(*groups_ratio).statistic),
        "kruskal_ratio_p": float(kruskal(*groups_ratio).pvalue),
    }
    return summary, stats


def build_wind_summary(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["best_wind_deg"].value_counts().sort_index()
    rows = []
    for wind_deg, count in counts.items():
        rows.append(
            {
                "evidence_type": "newly_run + blocked",
                "best_wind_deg": int(wind_deg),
                "component_count": int(count),
                "component_share": float(count / len(df)),
            }
        )
    return pd.DataFrame(rows)


def plot_panel(df: pd.DataFrame, corr: pd.DataFrame, stage: pd.DataFrame, wind: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans"})
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.2))

    ax = axes[0, 0]
    for klass in CLASS_ORDER:
        sub = df[df["stage_transition_class"] == klass]
        if sub.empty:
            continue
        ax.scatter(
            sub["local_context_mean_vr"],
            sub["local_context_range_vr"],
            s=np.clip(sub["footprint_area_m2"] / 35.0, 18, 150),
            alpha=0.74,
            color=CLASS_COLORS[klass],
            label=klass.replace("_", " "),
            edgecolor="white",
            linewidth=0.35,
        )
    ax.set_xlabel("20-50 m mean VR")
    ax.set_ylabel("Directional range of mean VR")
    ax.set_title("A. Component directional fingerprint")
    ax.legend(frameon=False, fontsize=6, loc="upper left")

    ax = axes[0, 1]
    stage_plot = stage.set_index("stage_transition_class").reindex(CLASS_ORDER).dropna()
    colors = [CLASS_COLORS[i] for i in stage_plot.index]
    ax.bar(
        [i.replace("_", "\n") for i in stage_plot.index],
        stage_plot["mean_directional_range_vr"],
        color=colors,
    )
    ax.set_ylabel("Mean directional range VR")
    ax.set_title("B. Directional range by transition class")
    ax.tick_params(axis="x", labelsize=6)

    ax = axes[1, 0]
    corr_plot = corr[corr["target"].isin(["local_context_range_vr", "directional_reactivity_ratio"])].copy()
    corr_plot["label"] = corr_plot["feature"].map(PRETTY_FEATURES)
    top = (
        corr_plot.assign(abs_rho=corr_plot["spearman_rho"].abs())
        .sort_values("abs_rho", ascending=False)
        .groupby("target")
        .head(5)
    )
    targets = ["local_context_range_vr", "directional_reactivity_ratio"]
    x = np.arange(len(top["label"].unique()))
    labels = list(dict.fromkeys(top["label"].tolist()))
    width = 0.35
    for idx, target in enumerate(targets):
        vals = []
        for label in labels:
            row = top[(top["target"] == target) & (top["label"] == label)]
            vals.append(float(row["spearman_rho"].iloc[0]) if not row.empty else 0.0)
        ax.bar(x + (idx - 0.5) * width, vals, width=width, label=target.replace("_", " "))
    ax.axhline(0, color="#333333", lw=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("Spearman rho")
    ax.set_title("C. Morphology correlations with directionality")
    ax.legend(frameon=False, fontsize=6)

    ax = axes[1, 1]
    ax.bar(wind["best_wind_deg"].astype(str), wind["component_count"], color="#457b9d")
    ax.set_xlabel("Best-response inflow direction (deg)")
    ax.set_ylabel("Component count")
    ax.set_title("D. Best-response direction counts")

    fig.suptitle("Morphology directional fingerprint in the 20-50 m local-context band", y=0.995)
    fig.tight_layout()
    fig.savefig(FIG / "morphology_directional_fingerprint_panel.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_report(
    df: pd.DataFrame,
    corr: pd.DataFrame,
    stage: pd.DataFrame,
    wind: pd.DataFrame,
    stats: dict[str, float],
) -> str:
    range_mean = df["local_context_range_vr"].mean()
    reactivity_mean = df["directional_reactivity_ratio"].mean()
    corr_range = corr[corr["target"] == "local_context_range_vr"].copy()
    corr_range["abs_rho"] = corr_range["spearman_rho"].abs()
    top_range = corr_range.sort_values("abs_rho", ascending=False).head(3)
    persistent = stage.set_index("stage_transition_class").loc["persistent_shelter"]
    recovery = stage.set_index("stage_transition_class").loc["near_to_context_recovery"]
    reactive = stage.set_index("stage_transition_class").loc["directionally_reactive"]
    best_winds = wind.sort_values("component_count", ascending=False).head(4)

    return f"""# Morphology Directional Fingerprint Analysis

evidence_type: newly_run + blocked

## Scope

This analysis reuses the archived FluidX3D-derived `basic_morphology_wind_response_by_component.csv` and the stage-transition component table. It does not run new CFD and does not claim field-validated directional causality. The target is a sample-internal design-screening descriptor for the 20-50 m local-context band.

## Component-Level Directionality

- Retained components: `{len(df)}`
- Inflow directions: `8`
- Mean 20-50 m directional range of mean VR: `{range_mean:.6f}`
- Mean directional reactivity ratio, defined as `(max_direction_mean_VR - min_direction_mean_VR) / mean_direction_mean_VR`: `{reactivity_mean:.3f}`

## Morphology Correlations With Directional Range

{top_range[['feature', 'spearman_rho', 'p_value', 'n_components']].to_markdown(index=False)}

The strongest monotonic associations with directional range are negative for mean height and sector/local enclosure. This means the components that remain strongly enclosed or vertically massive tend to suppress not only the mean local-context VR, but also the directional spread that would otherwise reveal wind-sector access.

## Stage-Class Separation

{stage.to_markdown(index=False)}

Kruskal-Wallis test for directional range across stage classes: statistic `{stats['kruskal_range_stat']:.3f}`, p-value `{stats['kruskal_range_p']:.4g}`.
Kruskal-Wallis test for directional reactivity ratio across stage classes: statistic `{stats['kruskal_ratio_stat']:.3f}`, p-value `{stats['kruskal_ratio_p']:.4g}`.

Persistent-shelter components have mean directional range `{persistent['mean_directional_range_vr']:.6f}`, while near-to-context recovery components reach `{recovery['mean_directional_range_vr']:.6f}` and directionally reactive components reach `{reactive['mean_directional_range_vr']:.6f}`. This supports a more detailed interpretation: useful ventilation recovery in this digital-twin block appears when the local context is not only less sheltered on average, but also able to respond differently to inflow sectors.

## Best-Response Directions

{best_winds.to_markdown(index=False)}

The best-response direction is not concentrated in a single inflow direction. This is consistent with a complex campus block where local recovery is controlled by local geometry and access paths rather than a single global canyon alignment.

## Claim Boundary

The result can be used to argue that directionality is an additional building-form screening layer beyond mean VR and recovery delta. It cannot be written as a universal design rule, wind-rose compliance result, field-validated causal mechanism, or proof that one morphology variable controls the wind field.

## Output Artifacts

- `figures/morphology_directional_fingerprint_by_component.csv`
- `figures/morphology_directional_fingerprint_feature_correlations.csv`
- `figures/morphology_directional_fingerprint_stage_summary.csv`
- `figures/morphology_directional_fingerprint_best_wind_summary.csv`
- `figures/morphology_directional_fingerprint_panel.png`
- `paper_text/morphology_directional_fingerprint_conclusion_zh.md`
- `paper_text/morphology_directional_fingerprint_conclusion_en.md`
- `manifests/morphology_directional_fingerprint_claims.csv`
"""


def build_paper_text_zh(df: pd.DataFrame, corr: pd.DataFrame, stage: pd.DataFrame, stats: dict[str, float]) -> str:
    range_mean = df["local_context_range_vr"].mean()
    reactivity_mean = df["directional_reactivity_ratio"].mean()
    corr_range = corr[corr["target"] == "local_context_range_vr"].set_index("feature")
    persistent = stage.set_index("stage_transition_class").loc["persistent_shelter"]
    recovery = stage.set_index("stage_transition_class").loc["near_to_context_recovery"]
    reactive = stage.set_index("stage_transition_class").loc["directionally_reactive"]
    return f"""# 寤虹瓚褰㈡€佹柟鍚戞€ф寚绾圭粨璁烘

evidence_type: newly_run + blocked

涓轰簡杩涗竴姝ユ妸寤虹瓚褰㈠紡涓庨鐜鐨勫叧绯讳粠鈥滃钩鍧囬閫熷樊寮傗€濇帹杩涘埌鈥滄潵娴佹柟鍚戝搷搴斿樊寮傗€濓紝鏈爺绌跺湪 101 涓繚鐣欏缓绛戝崟鍏冧笂璁＄畻 20-50 m 灞€鍦扮幆澧冨甫鐨勬柟鍚戞€ф寚绾癸紝鍖呮嫭鍏鍚?mean VR 鐨勬渶澶?-鏈€灏忚寖鍥淬€佹柟鍚戝搷搴旀瘮鍊间互鍙婃渶浣?鏈€寮卞搷搴旈鍚戙€傜粨鏋滄樉绀猴紝20-50 m 甯︾殑骞冲潎鏂瑰悜鑼冨洿涓?`{range_mean:.6f}`锛屽钩鍧囨柟鍚戝搷搴旀瘮鍊间负 `{reactivity_mean:.3f}`銆傛柟鍚戣寖鍥翠笌骞冲潎楂樺害鐨?Spearman rho 涓?`{corr_range.loc['mean_height_m','spearman_rho']:.3f}`锛屼笌 50 m 鎵囧尯鍥村悎搴︾殑 rho 涓?`{corr_range.loc['sector_enclosure_ratio_r50m','spearman_rho']:.3f}`锛屼笌缁煎悎鍥村悎寰楀垎鐨?rho 涓?`{corr_range.loc['relative_enclosure_score','spearman_rho']:.3f}`銆傝繖璇存槑鍦ㄨ鏍″洯琛楀尯涓紝杈冨己鍥村悎鍜岀珫鍚戜綋閲忎笉浠呭帇浣庡眬鍦板钩鍧?VR锛屼篃浼氬帇浣庢潵娴佹柟鍚戣兘澶熷甫鏉ョ殑鍝嶅簲宸紓銆?

闃舵绫诲瀷涔嬮棿鐨勬柟鍚戞€у樊寮傛洿鏄庢樉銆俻ersistent shelter 绫荤殑骞冲潎鏂瑰悜鑼冨洿浠?`{persistent['mean_directional_range_vr']:.6f}`锛宯ear-to-context recovery 绫讳负 `{recovery['mean_directional_range_vr']:.6f}`锛宒irectionally reactive 绫讳负 `{reactive['mean_directional_range_vr']:.6f}`锛屼笉鍚岄樁娈电被鍨嬮棿 Kruskal-Wallis p 值涓?`{stats['kruskal_range_p']:.4g}`銆傚洜姝わ紝鏈疄楠屽湪浼犵粺鈥滆璋峰洿鍚堝鑷磋繎鍦伴伄钄解€濅箣澶栨彁渚涚殑鏂拌鐭ユ槸锛氭湁鏁堢殑鏍″洯灞€鍦伴€氶鎭㈠涓嶅彧浣撶幇涓?20-50 m 骞冲潎 VR 鎻愰珮锛岃繕浣撶幇涓哄涓嶅悓鏉ユ祦鎵囧尯鐨勫搷搴旇兘鍔涘寮恒€備笉鍏锋湁杩欑鏂瑰悜鎬ф寚绾圭殑寮€鏁炴垨瀛旈殭锛屽彲鑳戒粎鏄綆閫熻儗鏅腑鐨勫舰寮忎笂寮€鏁烇紝杩欎篃瑙ｉ噴浜?S1/S2 涓轰粈涔堟病鏈夊湪鍏ㄥ眬琛屼汉灞傚甫鏉ユ鍚戞仮澶嶃€?

璇ョ粨璁哄彧鑳戒綔涓烘暟瀛楀鐢熸牱鏈唴绛涙煡璇佹嵁锛屼笉鏄疄娴嬮獙璇佺殑鍥犳灉鏈哄埗銆侀€氱敤璁捐闃堝€兼垨姝ｅ紡椋庣帿鐟板勾搴﹁垝閫傝瘎浠枫€?
"""


def build_paper_text_en(df: pd.DataFrame, corr: pd.DataFrame, stage: pd.DataFrame, stats: dict[str, float]) -> str:
    range_mean = df["local_context_range_vr"].mean()
    reactivity_mean = df["directional_reactivity_ratio"].mean()
    corr_range = corr[corr["target"] == "local_context_range_vr"].set_index("feature")
    persistent = stage.set_index("stage_transition_class").loc["persistent_shelter"]
    recovery = stage.set_index("stage_transition_class").loc["near_to_context_recovery"]
    reactive = stage.set_index("stage_transition_class").loc["directionally_reactive"]
    return f"""# Morphology Directional Fingerprint Conclusion

evidence_type: newly_run + blocked

To move the building-form interpretation beyond mean wind-speed differences, this addendum computes a directional fingerprint for the 101 retained building components in the 20-50 m local-context band. The fingerprint includes the max-minus-min range of the eight-direction mean VR, a directional reactivity ratio and the best/worst response directions. The mean directional range is `{range_mean:.6f}`, and the mean directional reactivity ratio is `{reactivity_mean:.3f}`. The directional range is negatively associated with mean height (Spearman rho `{corr_range.loc['mean_height_m','spearman_rho']:.3f}`), 50 m sector enclosure (rho `{corr_range.loc['sector_enclosure_ratio_r50m','spearman_rho']:.3f}`) and the relative enclosure score (rho `{corr_range.loc['relative_enclosure_score','spearman_rho']:.3f}`). In this campus-core sample, stronger enclosure and vertical massing therefore suppress not only the local mean VR, but also the directional spread through which wind-sector access can appear.

The separation across stage-transition classes is stronger than a single-variable correlation. Persistent-shelter components have mean directional range `{persistent['mean_directional_range_vr']:.6f}`, near-to-context recovery components reach `{recovery['mean_directional_range_vr']:.6f}`, and directionally reactive components reach `{reactive['mean_directional_range_vr']:.6f}`; the Kruskal-Wallis p-value across classes is `{stats['kruskal_range_p']:.4g}`. This supports a refined insight beyond the traditional canyon-shelter interpretation: useful campus-scale pedestrian ventilation recovery is visible not only as a higher 20-50 m mean VR, but also as the ability of the local context to respond differently to inflow sectors. Openings or porosity without this directional fingerprint may remain formal openness inside a low-speed background, which helps explain the negative S1/S2 design-sensitivity results.

This conclusion is a FluidX3D digital-twin screening finding. It must not be written as a field-validated causal mechanism, universal morphology threshold, wind-rose compliance result or formal annual comfort/safety assessment.
"""


def upsert_evidence_inventory() -> None:
    path = MAN / "evidence_inventory.csv"
    rows = pd.read_csv(path).to_dict("records")
    additions = [
        {
            "claim": "Morphology directional fingerprint analysis links 20-50 m local-context wind directionality to enclosure, vertical massing and stage-transition classes.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_directional_fingerprint_by_component.csv; figures/morphology_directional_fingerprint_feature_correlations.csv; figures/morphology_directional_fingerprint_panel.png; reports/morphology_directional_fingerprint_analysis.md",
        },
        {
            "claim": "Persistent-shelter components suppress both mean local-context VR and directional range, while recovery/reactive components show stronger wind-sector response.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_directional_fingerprint_stage_summary.csv; paper_text/morphology_directional_fingerprint_conclusion_zh.md; paper_text/morphology_directional_fingerprint_conclusion_en.md",
        },
    ]
    for item in additions:
        matched = False
        for row in rows:
            if row["claim"] == item["claim"]:
                row.update(item)
                matched = True
                break
        if not matched:
            rows.append(item)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def upsert_key_result_matrix(corr: pd.DataFrame, stage: pd.DataFrame, stats: dict[str, float], df: pd.DataFrame) -> None:
    corr_range = corr[corr["target"] == "local_context_range_vr"].set_index("feature")
    persistent = stage.set_index("stage_transition_class").loc["persistent_shelter"]
    recovery = stage.set_index("stage_transition_class").loc["near_to_context_recovery"]
    reactive = stage.set_index("stage_transition_class").loc["directionally_reactive"]
    value = (
        f"range mean {df['local_context_range_vr'].mean():.6f}; "
        f"stage ranges persistent/recovery/reactive "
        f"{persistent['mean_directional_range_vr']:.6f} / "
        f"{recovery['mean_directional_range_vr']:.6f} / "
        f"{reactive['mean_directional_range_vr']:.6f}; "
        f"stage Kruskal p {stats['kruskal_range_p']:.3g}; "
        f"rho mean_height {corr_range.loc['mean_height_m','spearman_rho']:.3f}, "
        f"sector_enclosure {corr_range.loc['sector_enclosure_ratio_r50m','spearman_rho']:.3f}"
    )
    upsert_csv_row(
        FIG / "final_integrated_key_result_matrix.csv",
        "claim_layer",
        {
            "evidence_type": "newly_run + blocked",
            "claim_layer": "Morphology directional fingerprint",
            "metric": "20-50 m directional range / stage-class separation / enclosure-height correlations",
            "value": value,
            "source_artifact": "figures/morphology_directional_fingerprint_by_component.csv; figures/morphology_directional_fingerprint_feature_correlations.csv; figures/morphology_directional_fingerprint_stage_summary.csv",
            "paper_safe_claim": "Wind recovery is better interpreted as local-context mean recovery plus wind-sector directional reactivity; persistent shelter suppresses both. This is sample-internal screening evidence, not a field-validated causal rule.",
        },
        [
            "evidence_type",
            "claim_layer",
            "metric",
            "value",
            "source_artifact",
            "paper_safe_claim",
        ],
    )


def main() -> None:
    for folder in [FIG, REP, PAPER, MAN]:
        folder.mkdir(parents=True, exist_ok=True)
    df = build_component_fingerprint()
    corr = build_correlations(df)
    stage, stats = build_stage_summary(df)
    wind = build_wind_summary(df)

    df.to_csv(FIG / "morphology_directional_fingerprint_by_component.csv", index=False, encoding="utf-8", lineterminator="\n")
    corr.to_csv(FIG / "morphology_directional_fingerprint_feature_correlations.csv", index=False, encoding="utf-8", lineterminator="\n")
    stage.to_csv(FIG / "morphology_directional_fingerprint_stage_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    wind.to_csv(FIG / "morphology_directional_fingerprint_best_wind_summary.csv", index=False, encoding="utf-8", lineterminator="\n")

    plot_panel(df, corr, stage, wind)

    claims = [
        {
            "claim": "20-50 m local-context directional range is negatively associated with mean height and sector enclosure in the retained component sample.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_directional_fingerprint_feature_correlations.csv; reports/morphology_directional_fingerprint_analysis.md",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim": "Stage-transition classes differ strongly in directional range and directional reactivity.",
            "evidence_type": "newly_run + blocked",
            "source": "figures/morphology_directional_fingerprint_stage_summary.csv; figures/morphology_directional_fingerprint_panel.png",
            "claim_readiness": "paper_ready_with_boundary",
        },
        {
            "claim": "Directional fingerprinting refines the S1/S2 negative design interpretation: porosity without wind-sector response can remain low-speed openness.",
            "evidence_type": "newly_run + blocked",
            "source": "paper_text/morphology_directional_fingerprint_conclusion_zh.md; paper_text/morphology_directional_fingerprint_conclusion_en.md",
            "claim_readiness": "paper_ready_with_boundary",
        },
    ]
    write_csv(
        MAN / "morphology_directional_fingerprint_claims.csv",
        claims,
        ["claim", "evidence_type", "source", "claim_readiness"],
    )

    write_text(REP / "morphology_directional_fingerprint_analysis.md", build_report(df, corr, stage, wind, stats))
    write_text(PAPER / "morphology_directional_fingerprint_conclusion_zh.md", build_paper_text_zh(df, corr, stage, stats))
    write_text(PAPER / "morphology_directional_fingerprint_conclusion_en.md", build_paper_text_en(df, corr, stage, stats))

    upsert_evidence_inventory()
    upsert_key_result_matrix(corr, stage, stats, df)

    print("components", len(df))
    print("mean_directional_range_vr", f"{df['local_context_range_vr'].mean():.6f}")
    print("kruskal_range_p", f"{stats['kruskal_range_p']:.4g}")
    print("wrote morphology directional fingerprint outputs")


if __name__ == "__main__":
    main()
