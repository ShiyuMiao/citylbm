#!/usr/bin/env python3
"""Smoke-test AF-derived Uref checks in native preconditions."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_native_af_uref_") as tmp:
        root = Path(tmp)
        run_dir = root / "run"
        run_dir.mkdir()
        af_csv = root / "AF.csv"
        metadata = root / "case_metadata.json"
        inlet_source_audit = run_dir / "inlet_source_audit.json"
        out_json = root / "native_preconditions_audit.json"
        write_text(af_csv, "z(m),U(m/s),k(m2/s2)\n10,3.0,0.1\n20,5.0,0.2\n")
        write_text(metadata, '{"ReferenceWindSpeedMps": 3.0, "WindProfile": "CustomTable"}\n')
        write_text(
            inlet_source_audit,
            json.dumps(
                {
                    "inlet_source_gate": "pass",
                    "paper_grade_inlet_source_gate": "fail",
                    "inlet_source_distribution_route_gate": "fail",
                    "inlet_source_distribution_consistent": False,
                    "inlet_source_has_distribution_function_write": False,
                    "inlet_source_has_inlet_distribution_reconstruction": False,
                    "inlet_source_velocity_field_only": True,
                    "inlet_source_method_class": "stg_lite_correlated_velocity_field_only",
                    "inlet_source_turbulent_inflow_fidelity_class": "correlated_velocity_field_only",
                    "inlet_source_has_correlated_velocity_field_only": True,
                    "inlet_source_has_uncorrelated_rms_velocity_field_only": False,
                    "synthetic_inlet_correlation_model": "spectral_taylor_projected_velocity_field_only",
                    "has_synthetic_inlet_function": True,
                    "has_three_component_velocity_write": True,
                    "has_three_component_fluctuation_evidence": True,
                    "has_k_driven_three_component_stg": True,
                    "has_mean_preserving_inlet_correction": True,
                    "has_layerwise_mean_preserving_inlet_correction": True,
                    "has_streamwise_clipping_control": True,
                    "streamwise_min_fraction": 0.05,
                    "streamwise_clipping_enabled": True,
                    "has_legacy_hardcoded_streamwise_clipping": True,
                    "inlet_source_gate_reasons": [
                        "synthetic_inlet_uses_legacy_hardcoded_streamwise_clipping",
                    ],
                    "paper_grade_inlet_source_gate_reasons": [
                        "source_not_distribution_consistent",
                        "source_velocity_field_only",
                        "source_correlated_velocity_field_only_without_distribution_reconstruction",
                    ],
                },
                indent=2,
            ),
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "audit_native_preconditions.py"),
                str(run_dir),
                "--metadata",
                str(metadata),
                "--af-csv",
                str(af_csv),
                "--u-ref",
                "3.0",
                "--z-ref",
                "15.0",
                "--out",
                str(out_json),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 2:
            raise AssertionError(
                f"audit_native_preconditions returned {completed.returncode}, expected 2 for failing preconditions\n"
                f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
            )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        reasons = report.get("native_preconditions_gate_reasons", [])
        if "uref_af_profile_mismatch" not in reasons:
            raise AssertionError(reasons)
        if "inlet_source_streamwise_clipping_enabled" not in reasons:
            raise AssertionError(reasons)
        if "inlet_source_uses_legacy_hardcoded_streamwise_clipping" not in reasons:
            raise AssertionError(reasons)
        for expected in [
            "paper_grade_inlet_source_gate_not_pass",
            "inlet_source_not_distribution_consistent",
            "inlet_source_velocity_field_only",
        ]:
            if expected not in reasons:
                raise AssertionError(reasons)
        if report.get("inlet_source_method_class") != "stg_lite_correlated_velocity_field_only":
            raise AssertionError(report.get("inlet_source_method_class"))
        if report.get("inlet_source_turbulent_inflow_fidelity_class") != "correlated_velocity_field_only":
            raise AssertionError(report.get("inlet_source_turbulent_inflow_fidelity_class"))
        if report.get("inlet_source_has_correlated_velocity_field_only") is not True:
            raise AssertionError(report)
        if report.get("af_uref_at_zref_mps") != 4.0:
            raise AssertionError(report.get("af_uref_at_zref_mps"))
        if report.get("inlet_source_has_streamwise_clipping_control") is not True:
            raise AssertionError(report)
        if report.get("inlet_source_streamwise_min_fraction") != 0.05:
            raise AssertionError(report.get("inlet_source_streamwise_min_fraction"))
        if report.get("inlet_source_streamwise_clipping_enabled") is not True:
            raise AssertionError(report)
        if report.get("inlet_source_has_legacy_hardcoded_streamwise_clipping") is not True:
            raise AssertionError(report)
        if report.get("native_preconditions_protocol_identity_gate") != "fail":
            raise AssertionError(report.get("native_preconditions_protocol_identity_gate"))

    print("native_preconditions_af_uref_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
