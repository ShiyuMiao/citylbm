#!/usr/bin/env python3
"""Smoke-test native precondition coordinate delta recomputation."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def load_audit_module():
    path = REPO / "scripts" / "audit_native_preconditions.py"
    spec = importlib.util.spec_from_file_location("audit_native_preconditions", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_audit_module()
    rows = [
        {
            "probe_id": "P1",
            "x": "9.0",
            "y": "0.0",
            "z": "0.0",
            "official_coordinate_delta": "0.0",
        }
    ]
    official = {"p1": (0.0, 0.0, 0.0)}

    current = module.probe_official_coordinate_delta_summary(rows, official, "probe_id")
    if current["source"] != "current_official_csv_recomputed":
        raise AssertionError(current)
    if current["recomputed_count"] != 1:
        raise AssertionError(current)
    if current["missing_count"] != 0:
        raise AssertionError(current)
    if current["deltas"] != [9.0]:
        raise AssertionError(current)

    fallback = module.probe_official_coordinate_delta_summary(rows, {}, "probe_id")
    if fallback["source"] != "probe_audit_only":
        raise AssertionError(fallback)
    if fallback["recomputed_count"] != 0:
        raise AssertionError(fallback)
    if fallback["deltas"] != [0.0]:
        raise AssertionError(fallback)

    cases = {
        "paper_grade_probe_component_normalization": [],
        "official_probe_coordinate_mismatch": ["official_probe_coverage_ratio_not_one:0.9"],
        "probe_projection_mismatch": ["probe_out_of_tolerance_count_2"],
        "stale_or_untraceable_probe_component_window": [
            "component_source_step_span_3000_below_minimum_20000",
        ],
        "component_or_normalization_mismatch": ["probe_uref_mismatch_count_80"],
    }
    for expected, reasons in cases.items():
        actual = module.classify_probe_component_fidelity(reasons)
        if actual != expected:
            raise AssertionError((expected, actual, reasons))

    print("native_preconditions_coordinate_recompute_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
