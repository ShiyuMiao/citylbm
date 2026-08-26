#!/usr/bin/env python3
"""Smoke-test native manifest case-to-source parity gate."""

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


def require(condition: bool, detail: object) -> None:
    if not condition:
        raise AssertionError(detail)


def pair(role: str, digest: str, *, match: bool = True) -> dict:
    return {
        "Role": role,
        "CaseSha256": digest,
        "SourceSha256": digest if match else "f" * 64,
        "Match": match,
    }


def main() -> int:
    module = load_audit_module()
    setup_sha = "a" * 64
    defines_sha = "b" * 64

    missing = module.manifest_case_to_run_source_parity({})
    require(missing["gate"] == "fail", missing)
    require("case_to_run_source_parity_gate_missing" in missing["reasons"], missing)

    mismatch = module.manifest_case_to_run_source_parity(
        {
            "CaseToRunSourceParityGate": {
                "Gate": "diagnostic_only",
                "Reasons": ["case_setup_hash_mismatch_source"],
                "Pairs": [pair("setup", setup_sha, match=False), pair("defines", defines_sha)],
            }
        }
    )
    require(mismatch["gate"] == "fail", mismatch)
    for expected in [
        "case_to_run_source_parity_gate_not_pass:diagnostic_only",
        "case_to_run_source_parity_reason:case_setup_hash_mismatch_source",
        "case_to_run_source_parity_pair_not_matched:setup",
    ]:
        require(expected in mismatch["reasons"], mismatch)

    passing = module.manifest_case_to_run_source_parity(
        {
            "CaseToRunSourceParityGate": {
                "Gate": "pass",
                "Reasons": [],
                "Pairs": [pair("setup", setup_sha), pair("defines", defines_sha)],
            }
        }
    )
    require(passing["gate"] == "pass", passing)
    require(passing["matched_pair_count"] == 2, passing)

    run_plan_override = module.manifest_case_to_run_source_parity(
        {
            "CaseToRunSourceParityGate": {
                "Gate": "pass",
                "Reasons": [],
                "Pairs": [
                    {
                        "Role": "setup",
                        "CaseSha256": setup_sha,
                        "SourceSha256": "f" * 64,
                        "Match": False,
                        "AllowedMismatch": True,
                    },
                    pair("defines", defines_sha),
                ],
            }
        }
    )
    require(run_plan_override["gate"] == "pass", run_plan_override)
    require(run_plan_override["matched_pair_count"] == 2, run_plan_override)
    require(run_plan_override["allowed_mismatch_pair_count"] == 1, run_plan_override)

    print("native_preconditions_source_parity_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
