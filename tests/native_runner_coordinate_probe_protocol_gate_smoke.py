"""Smoke-test native runner gating from coordinate_probe_protocol_audit.json."""

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


def write_coordinate_audit(path: Path, *, gate: str) -> None:
    if gate == "pass":
        reasons: list[str] = []
        long_cfd_allowed = True
        stage = "eligible_for_short_native_canary"
        next_scope = "short_native_canary_only"
    else:
        reasons = [
            "velocity_component_U_not_mapped_to_fluidx3d_u.x",
            "official_probe_row_count_mismatch:40!=80",
        ]
        long_cfd_allowed = False
        stage = "fix_coordinate_axis_component_mapping_before_cfd"
        next_scope = "none_until_coordinate_component_gate_passes"
    report = {
        "Schema": "citylbm.coordinate_probe_protocol_audit.v1",
        "Gate": gate,
        "coordinate_probe_protocol_gate": gate,
        "Reasons": reasons,
        "long_cfd_allowed_by_coordinate_probe_protocol": long_cfd_allowed,
        "development_acceleration_stage": stage,
        "development_acceleration_next_cfd_scope": next_scope,
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
        "smoke-casea-native-coordinate-probe-audit",
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

        pass_audit = temp / "preflight" / "coordinate_probe_protocol_pass.json"
        write_coordinate_audit(pass_audit, gate="pass")
        pass_manifest = temp / "pass" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(base_runner_args(case_dir, source_root, pass_manifest) + ["--coordinate-probe-protocol-audit", str(pass_audit)])
        passed = load_json(pass_manifest)
        if passed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(passed["RunnerGate"])
        if passed["CoordinateProbeProtocolAuditGate"]["Gate"] != "pass":
            raise AssertionError(passed["CoordinateProbeProtocolAuditGate"])
        if passed["CoordinateProbeProtocolAuditGate"]["DevelopmentAccelerationStage"] != "eligible_for_short_native_canary":
            raise AssertionError(passed["CoordinateProbeProtocolAuditGate"])

        fail_audit = temp / "preflight" / "coordinate_probe_protocol_fail.json"
        write_coordinate_audit(fail_audit, gate="fail")
        fail_manifest = temp / "fail" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            base_runner_args(case_dir, source_root, fail_manifest)
            + ["--coordinate-probe-protocol-audit", str(fail_audit)],
            expected_returncode=2,
        )
        failed = load_json(fail_manifest)
        for reason in [
            "coordinate_probe_protocol_gate_not_pass:fail",
            "long_cfd_allowed_by_coordinate_probe_protocol_not_true:False",
            "velocity_component_U_not_mapped_to_fluidx3d_u.x",
            "official_probe_row_count_mismatch:40!=80",
        ]:
            if reason not in failed["RunnerGate"]["Reasons"]:
                raise AssertionError(failed["RunnerGate"])

        missing_manifest = temp / "missing" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(base_runner_args(case_dir, source_root, missing_manifest) + ["--run"], expected_returncode=2)
        missing = load_json(missing_manifest)
        if "run_requested_without_coordinate_probe_protocol_audit" not in missing["RunnerGate"]["Reasons"]:
            raise AssertionError(missing["RunnerGate"])

    print("native_runner_coordinate_probe_protocol_gate_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
