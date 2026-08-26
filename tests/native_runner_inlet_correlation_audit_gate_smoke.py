"""Smoke-test native runner gating from inlet_correlation_audit.json."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
sys.path.insert(0, str(REPO / "tests"))

from native_fluidx3d_runner_smoke import create_case, create_source, load_json, write  # noqa: E402


def run_cmd(args: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def write_inlet_correlation_audit(path: Path, *, gate: str) -> None:
    if gate == "pass":
        reasons = ["inlet_correlation_evidence_present"]
        k_gate = "pass"
        k_reasons = ["k_variance_evidence_present"]
        tke_gate = "pass"
        tke_reasons = ["tke_evidence_present"]
        temporal = 0.65
        spatial = 0.42
    else:
        reasons = [
            "temporal_lag1_correlation_below_0.05",
            "spatial_adjacent_correlation_below_0.02",
        ]
        k_gate = "fail"
        k_reasons = ["k_variance_ratio_below_0.5"]
        tke_gate = "fail"
        tke_reasons = ["tke_to_k_ratio_below_0.5"]
        temporal = 0.0
        spatial = 0.0
    report = {
        "schema": "citylbm.inlet_correlation_audit.v1",
        "inlet_correlation_gate": gate,
        "inlet_correlation_gate_reasons": reasons,
        "inlet_k_variance_gate": k_gate,
        "inlet_k_variance_gate_reasons": k_reasons,
        "inlet_tke_gate": tke_gate,
        "inlet_tke_gate_reasons": tke_reasons,
        "temporal_lag1_correlation": temporal,
        "spatial_adjacent_correlation": spatial,
        "inlet_streamwise_variance_to_k_ratio": 1.0 if gate == "pass" else 0.1,
        "inlet_tke_to_k_ratio": 1.0 if gate == "pass" else 0.1,
    }
    write(path, json.dumps(report, indent=2))


def base_runner_args(case_dir: Path, source_root: Path, out_path: Path) -> list[str]:
    return [
        sys.executable,
        str(RUNNER),
        "--case-dir",
        str(case_dir),
        "--fluidx3d-source",
        str(source_root),
        "--out",
        str(out_path),
        "--baseline-id",
        "smoke-casea-native-inlet-correlation-audit",
        "--expected-aij-case",
        "CaseA",
        "--expected-wind-direction",
        "N",
        "--time-steps",
        "40000",
        "--vtk-save-interval",
        "1000",
        "--expected-vtk-frame-count",
        "40",
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        pass_audit = temp / "preflight" / "inlet_correlation_pass.json"
        write_inlet_correlation_audit(pass_audit, gate="pass")
        pass_manifest = temp / "pass" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(base_runner_args(case_dir, source_root, pass_manifest) + ["--inlet-correlation-audit", str(pass_audit)])
        passed = load_json(pass_manifest)
        if passed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(passed["RunnerGate"])
        if passed["InletCorrelationAuditGate"]["Gate"] != "pass":
            raise AssertionError(passed["InletCorrelationAuditGate"])
        if passed["InletCorrelationAuditGate"]["InletKVarianceGate"] != "pass":
            raise AssertionError(passed["InletCorrelationAuditGate"])

        fail_audit = temp / "preflight" / "inlet_correlation_fail.json"
        write_inlet_correlation_audit(fail_audit, gate="fail")
        fail_manifest = temp / "fail" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, fail_manifest)
            + ["--inlet-correlation-audit", str(fail_audit)],
            expected_returncode=2,
        )
        failed = load_json(fail_manifest)
        for reason in [
            "inlet_correlation_gate_not_pass:fail",
            "inlet_k_variance_gate_not_pass:fail",
            "inlet_tke_gate_not_pass:fail",
            "temporal_lag1_correlation_below_0.05",
            "inlet_k_variance:k_variance_ratio_below_0.5",
            "inlet_tke:tke_to_k_ratio_below_0.5",
        ]:
            if reason not in failed["RunnerGate"]["Reasons"]:
                raise AssertionError(failed["RunnerGate"])

        missing_manifest = temp / "missing" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(base_runner_args(case_dir, source_root, missing_manifest))
        missing = load_json(missing_manifest)
        if missing["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(missing["RunnerGate"])
        if missing["InletCorrelationAuditGate"]["Gate"] != "not_applicable":
            raise AssertionError(missing["InletCorrelationAuditGate"])
        if "inlet_correlation_gate_not_pass:not_applicable" not in missing["PaperUseGate"]["Reasons"]:
            raise AssertionError(missing["PaperUseGate"])

    print("native_runner_inlet_correlation_audit_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
