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
        "SyntheticTurbulentInletComponentRmsNormalization",
        "sqrt(2/sum(projected_unit_mode_component^2))",
    ]
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise AssertionError(f"missing STG-lite normalization tokens: {missing}")

    if "const float citylbm_stg_norm = sqrtf(6.0f / (float)citylbm_stg_mode_count);" in source:
        raise AssertionError("single-component STG normalization was reintroduced")

    print("synthetic_inlet_component_norm_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
