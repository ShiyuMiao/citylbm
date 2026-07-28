from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
from scipy.stats import kruskal


ROOT = Path.cwd()
FIG = ROOT / "figures"

FIELDS = [
    "evidence_type",
    "claim_layer",
    "metric",
    "value",
    "source_artifact",
    "paper_safe_claim",
]


def fmt(value: object, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def row_by_metric(df: pd.DataFrame, metric: str) -> pd.Series:
    row = df[df["metric"] == metric]
    if row.empty:
        raise ValueError(f"missing metric: {metric}")
    return row.iloc[0]


def upsert(row: dict[str, object]) -> None:
    path = FIG / "final_integrated_key_result_matrix.csv"
    rows: list[dict[str, object]] = []
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    rows = [item for item in rows if item.get("claim_layer") != row["claim_layer"]]
    rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def add_effect_size_row() -> None:
    df = pd.read_csv(FIG / "experiment3_effect_size_uncertainty_summary.csv")
    z2 = row_by_metric(df, "z2_mean_vr")
    stag = row_by_metric(df, "z2_stagnation_ratio")
    vert = row_by_metric(df, "z40_minus_z2_mean_vr")
    s2 = row_by_metric(df, "s2_z2_delta_global_mean_vr")
    value = (
        f"{fmt(z2['estimate'])} [{fmt(z2['interval_low'])},{fmt(z2['interval_high'])}] / "
        f"{fmt(stag['estimate'])} [{fmt(stag['interval_low'])},{fmt(stag['interval_high'])}] / "
        f"{fmt(vert['estimate'])} [{fmt(vert['interval_low'])},{fmt(vert['interval_high'])}] / "
        f"{fmt(s2['interval_low'], 6)} to {fmt(s2['interval_high'], 6)}"
    )
    upsert(
        {
            "evidence_type": "newly_run + blocked",
            "claim_layer": "Effect-size uncertainty",
            "metric": "z~2 m mean VR CI / z~2 m stagnation CI / z40-z2 VR delta CI / S2 z~2 m delta range",
            "value": value,
            "source_artifact": "figures/experiment3_effect_size_uncertainty_summary.csv",
            "paper_safe_claim": "Core low-speed, vertical recovery and S1/S2 negative-sensitivity conclusions are stable within archived direction-sample uncertainty, not measurement or grid-convergence uncertainty.",
        }
    )


def add_directional_anisotropy_row() -> None:
    df = pd.read_csv(FIG / "experiment3_directional_anisotropy_summary.csv")
    z2 = row_by_metric(df, "z2_mean_vr")
    stag = row_by_metric(df, "z2_stagnation_ratio")
    vert = row_by_metric(df, "z40_minus_z2_mean_vr")
    s2_common = row_by_metric(df, "s2_common_delta_vr_mean")
    value = (
        f"{fmt(z2['anisotropy_index'])} / {fmt(stag['anisotropy_index'])} / "
        f"{fmt(vert['range'])} / {int(s2_common['max_wind_deg'])} deg"
    )
    upsert(
        {
            "evidence_type": "newly_run + preexisting_artifact + blocked",
            "claim_layer": "Directional anisotropy",
            "metric": "z~2 m VR anisotropy / stagnation anisotropy / vertical recovery range / S2 strongest common-open direction",
            "value": value,
            "source_artifact": "figures/experiment3_directional_anisotropy_summary.csv; figures/experiment3_directional_response_by_wind.csv",
            "paper_safe_claim": "Low-speed sheltering is quasi-omnidirectional, while local design response is direction-sensitive and not globally restorative.",
        }
    )


def add_archetype_row() -> None:
    summary = pd.read_csv(FIG / "morphology_form_response_archetype_summary.csv")
    by_component = pd.read_csv(FIG / "morphology_form_response_archetype_by_component.csv")
    top = summary.sort_values("recovery_rank").iloc[0]
    bottom = summary.sort_values("recovery_rank").iloc[-1]
    groups = [
        group["context_recovery_delta_vr"].dropna().values
        for _, group in by_component.groupby("archetype")
        if len(group) >= 2
    ]
    p_value = float(kruskal(*groups).pvalue)
    value = (
        f"{top['archetype']} / {bottom['archetype']} / "
        f"{p_value:.4g} / {fmt(top['context_recovery_delta_vr'], 4)} vs "
        f"{fmt(bottom['context_recovery_delta_vr'], 4)}"
    )
    upsert(
        {
            "evidence_type": "newly_run + blocked",
            "claim_layer": "Building-form response archetypes",
            "metric": "strongest archetype / weakest archetype / Kruskal p / recovery delta contrast",
            "value": value,
            "source_artifact": "figures/morphology_form_response_archetype_summary.csv; reports/morphology_form_response_archetype_analysis.md",
            "paper_safe_claim": "The campus-core wind-response differences are better framed as combined morphology archetypes involving relative vertical massing, elongation and local enclosure than as a single footprint, height or porosity effect.",
        }
    )


def main() -> None:
    add_effect_size_row()
    add_directional_anisotropy_row()
    add_archetype_row()
    matrix = pd.read_csv(FIG / "final_integrated_key_result_matrix.csv")
    print("key_result_rows_after_addendum_upsert", len(matrix))


if __name__ == "__main__":
    main()
