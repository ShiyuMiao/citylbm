#!/usr/bin/env python3
"""Smoke-test component sensitivity input hash traceability."""

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
    probe_sha = "a" * 64
    official_sha = "b" * 64

    ok = module.component_sensitivity_input_hash_traceability(
        {
            "probe_audit_sha256": probe_sha,
            "official_sha256": official_sha,
        },
        probe_sha,
        official_sha,
    )
    if ok["gate"] != "pass":
        raise AssertionError(ok)
    if ok["probe_audit_sha256_matches_current"] is not True:
        raise AssertionError(ok)
    if ok["official_sha256_matches_current"] is not True:
        raise AssertionError(ok)

    stale = module.component_sensitivity_input_hash_traceability(
        {
            "probe_audit_sha256": "c" * 64,
            "official_sha256": "d" * 64,
        },
        probe_sha,
        official_sha,
    )
    if stale["gate"] != "fail":
        raise AssertionError(stale)
    for expected in [
        "component_sensitivity_probe_audit_hash_mismatch",
        "component_sensitivity_official_hash_mismatch",
    ]:
        if expected not in stale["reasons"]:
            raise AssertionError(stale)

    missing = module.component_sensitivity_input_hash_traceability({}, probe_sha, official_sha)
    if missing["gate"] != "pass":
        raise AssertionError(missing)
    if missing["probe_audit_sha256_matches_current"] is not None:
        raise AssertionError(missing)
    if missing["official_sha256_matches_current"] is not None:
        raise AssertionError(missing)

    incomplete = module.component_sensitivity_input_hash_traceability({"probe_audit_sha256": probe_sha}, probe_sha, official_sha)
    if incomplete["gate"] != "fail":
        raise AssertionError(incomplete)
    if "component_sensitivity_official_hash_missing" not in incomplete["reasons"]:
        raise AssertionError(incomplete)

    print("native_preconditions_component_hash_traceability_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
