#!/usr/bin/env python3
"""Smoke-test STG-lite component RMS normalization evidence in the setup generator."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    source = (REPO / "src" / "Core" / "FluidX3DInterface.cs").read_text(encoding="utf-8")

    required_tokens = [
        "ComputeSyntheticTurbulenceComponentNorms",
        "SyntheticModeWave",
        "SyntheticModeAmplitude",
        "citylbm_stg_norm_x",
        "citylbm_stg_norm_y",
        "citylbm_stg_norm_z",
        "fluct_x *= citylbm_stg_norm_x",
        "fluct_y *= citylbm_stg_norm_y",
        "fluct_z *= citylbm_stg_norm_z",
        "citylbm_stg_temporal_ar1_rho",
        "citylbm_stg_temporal_ar1_innovation_scale",
        "citylbm_stg_temporal_step_scale",
        "citylbm_stg_temporal_ar1_rho = 0.650000f",
        "citylbm_stg_temporal_step_scale = 1.500000f",
        "citylbm_stg_prev_refresh_index",
        "previous_phase",
        "citylbm_stg_target_sigma",
        "SyntheticTurbulentInletComponentRmsNormalization",
        "sqrt(2/sum(projected_unit_mode_component^2))",
        "citylbm_stg_layer_mean_correction_x",
        "citylbm_stg_layer_mean_correction_y",
        "citylbm_stg_layer_mean_correction_z",
        "citylbm_stg_layer_corrected_inlet_count",
        "citylbm_stg_layer_corrected_sum_sq_x",
        "citylbm_stg_layer_corrected_sum_xy",
        "citylbm_stg_layer_rms_scale_x",
        "target_sigma.x / rms_x",
        "citylbm_stg_layer_tensor_whitening_valid",
        "CityLBMReynoldsCholesky target_l = citylbm_stg_target_reynolds_cholesky(z_m);",
        "u_in.x = mean.x + citylbm_stg_scale * target_l.l11 * w1;",
        "SyntheticTurbulentInletMeanPreservingScope",
        "SyntheticTurbulentInletLayerwiseRmsPreservingCorrection",
        "SyntheticTurbulentInletFullTensorCovariancePreservingCorrection",
        "per_z_cell_inlet_layer",
    ]
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise AssertionError(f"missing STG-lite normalization tokens: {missing}")

    if "const float citylbm_stg_norm = sqrtf(6.0f / (float)citylbm_stg_mode_count);" in source:
        raise AssertionError("single-component STG normalization was reintroduced")
    if "citylbm_stg_temporal_step_scale = 0.050000f" in source or "advect_steps * 0.05f" in source:
        raise AssertionError("slow 0.05 STG temporal advection was reintroduced")
    if "rho_0.97" in source or "temporal_step_scale_0.05" in source:
        raise AssertionError("over-smoothed rho_0.97 STG temporal metadata was reintroduced")

    print("synthetic_inlet_component_norm_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
