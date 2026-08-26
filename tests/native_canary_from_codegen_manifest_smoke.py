#!/usr/bin/env python3
"""Smoke-test short native canary wrapper planning."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_native_canary_from_codegen_manifest.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_native_canary_wrapper_") as raw:
        temp = Path(raw)
        case_dir = temp / "case"
        source_root = temp / "FluidX3D"
        preflight_dir = temp / "preflight"
        out_dir = temp / "canary"
        case_dir.mkdir()
        (source_root / "src").mkdir(parents=True)
        write(case_dir / "setup.cpp", "// setup\n")
        write(case_dir / "defines.hpp", "// defines\n")
        write(
            case_dir / "case_metadata.json",
            json.dumps({"TimeSteps": 1000, "SaveInterval": 100, "ExpectedVtkFrameCount": 10}, indent=2),
        )
        write(source_root / "src" / "setup.cpp", "// native setup\n")
        write(source_root / "src" / "defines.hpp", "// native defines\n")
        validation_audit = preflight_dir / "validation_protocol_audit.json"
        inlet_audit = preflight_dir / "inlet_source_audit.json"
        write(validation_audit, "{}\n")
        write(inlet_audit, "{}\n")
        preflight_manifest = preflight_dir / "native_preflight_pack_manifest.json"
        write(
            preflight_manifest,
            json.dumps(
                {
                    "Artifacts": {
                        "ValidationProtocolAudit": str(validation_audit),
                        "InletSourceAudit": str(inlet_audit),
                    }
                },
                indent=2,
            ),
        )
        codegen_manifest = temp / "codegen_preflight_canary_manifest.json"
        write(
            codegen_manifest,
            json.dumps(
                {
                    "CaseName": "stg_codegen_smoke",
                    "CaseDir": str(case_dir),
                    "FluidX3DSource": str(source_root),
                    "OutDir": str(preflight_dir),
                    "DiagnosticCanaryGate": {"Gate": "pass", "Reasons": []},
                    "NativePreflightPackManifest": str(preflight_manifest),
                },
                indent=2,
            ),
        )
        manifest_out = out_dir / "native_canary_manifest.json"
        planned = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--codegen-manifest",
                str(codegen_manifest),
                "--out-dir",
                str(out_dir),
                "--manifest-out",
                str(manifest_out),
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if planned.returncode != 0:
            raise AssertionError((planned.returncode, planned.stdout, planned.stderr))
        data = load(manifest_out)
        if data["Gate"] != "planned":
            raise AssertionError(data)
        if data["Execute"] is not False:
            raise AssertionError(data)
        if "--install" in data["Command"] or "--build" in data["Command"] or "--run" in data["Command"]:
            raise AssertionError(data["Command"])
        for expected in [
            "--allow-diagnostic-execution",
            "--validation-protocol-audit",
            str(validation_audit),
            "--inlet-source-audit",
            str(inlet_audit),
            "--expected-wind-vector",
            "1,0,0",
        ]:
            if expected not in data["Command"]:
                raise AssertionError(data["Command"])
        if data["PaperUsePolicy"] != "never_use_short_canary_for_accuracy_or_paper_metrics":
            raise AssertionError(data)
        if data["ShortCanaryRunConditions"]["TimeSteps"] != 1000:
            raise AssertionError(data)
        if data["ShortCanaryRunConditions"]["SaveInterval"] != 100:
            raise AssertionError(data)
        if data["ShortCanaryRunConditions"]["ExpectedVtkFrameCount"] != 10:
            raise AssertionError(data)

        casee_codegen_manifest = temp / "casee_codegen_preflight_canary_manifest.json"
        casee_data = load(codegen_manifest)
        casee_data["ExpectedAijCase"] = "CaseE"
        casee_data["ExpectedWindDirection"] = "N"
        casee_data["ExpectedWindVector"] = "0,-1,0"
        write(casee_codegen_manifest, json.dumps(casee_data, indent=2))
        casee_manifest_out = out_dir / "casee_native_canary_manifest.json"
        casee_planned = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--codegen-manifest",
                str(casee_codegen_manifest),
                "--manifest-out",
                str(casee_manifest_out),
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if casee_planned.returncode != 0:
            raise AssertionError((casee_planned.returncode, casee_planned.stdout, casee_planned.stderr))
        casee_wrapper = load(casee_manifest_out)
        for expected in ["--expected-aij-case", "CaseE", "--expected-wind-vector", "0,-1,0"]:
            if expected not in casee_wrapper["Command"]:
                raise AssertionError(casee_wrapper["Command"])

        mismatch_manifest_out = out_dir / "mismatch_native_canary_manifest.json"
        mismatch = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--codegen-manifest",
                str(codegen_manifest),
                "--manifest-out",
                str(mismatch_manifest_out),
                "--execute",
                "--time-steps",
                "2000",
                "--vtk-save-interval",
                "500",
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if mismatch.returncode != 2:
            raise AssertionError((mismatch.returncode, mismatch.stdout, mismatch.stderr))
        mismatch_data = load(mismatch_manifest_out)
        if mismatch_data["Gate"] != "fail":
            raise AssertionError(mismatch_data)
        if mismatch_data["Steps"][-1]["Stderr"] != "blocked_by_wrapper_preconditions":
            raise AssertionError(mismatch_data)
        for expected_reason in [
            "requested_time_steps_2000_does_not_match_generated_case_time_steps_1000",
            "requested_vtk_save_interval_500_does_not_match_generated_case_save_interval_100",
        ]:
            if expected_reason not in mismatch_data["Reasons"]:
                raise AssertionError(mismatch_data)

        bad_codegen_manifest = temp / "bad_codegen_preflight_canary_manifest.json"
        bad_data = load(codegen_manifest)
        bad_data["DiagnosticCanaryGate"] = {"Gate": "fail", "Reasons": ["smoke"]}
        write(bad_codegen_manifest, json.dumps(bad_data, indent=2))
        bad_manifest_out = out_dir / "bad_native_canary_manifest.json"
        blocked = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--codegen-manifest",
                str(bad_codegen_manifest),
                "--manifest-out",
                str(bad_manifest_out),
            ],
            cwd=str(REPO),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if blocked.returncode != 2:
            raise AssertionError((blocked.returncode, blocked.stdout, blocked.stderr))
        blocked_data = load(bad_manifest_out)
        if blocked_data["Gate"] != "fail":
            raise AssertionError(blocked_data)
        if "diagnostic_canary_gate_not_pass:fail" not in blocked_data["Reasons"]:
            raise AssertionError(blocked_data)

    print("native_canary_from_codegen_manifest_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
