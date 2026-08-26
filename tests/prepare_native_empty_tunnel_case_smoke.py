#!/usr/bin/env python3
"""Smoke-test native empty-tunnel case preparation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "prepare_native_empty_tunnel_case.py"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def create_case(case_dir: Path) -> None:
    write(
        case_dir / "src" / "setup.cpp",
        """#include "lbm.hpp"

void main_setup() {
    const float citylbm_dx_m = 0.00600000f;
    const float citylbm_u_ref_si = 4.49100000f;
    const float citylbm_u_ref_lbm = 0.10000000f;
    const float profile_z_cells[3] = { 10.00000000f, 26.66666667f, 50.00000000f };
    const float profile_u_lbm[3] = { 0.08000000f, 0.10000000f, 0.12000000f };
    const uint vtk_save_interval = 1000u;
    const uint vtk_save_start_step = 10000u;
    const bool empty_tunnel = false;
    if(!empty_tunnel) {
        read_stl("buildings.stl");
    }
    const uint total_steps = 60000u;
}
""",
    )
    write(case_dir / "src" / "defines.hpp", "#define SX 10u\n#define SY 10u\n#define SZ 10u\n")
    write(case_dir / "buildings.stl", "solid smoke\nendsolid smoke\n")
    write(case_dir / "domain_origin.json", '{"Origin":[0,0,0]}\n')
    write(case_dir / "case_metadata.json", '{"Case":"CaseA","TimeSteps":60000,"VelocityScaleLbmToMps":53,"Validation":{}}\n')


def create_legacy_generated_case(case_dir: Path) -> None:
    write(
        case_dir / "src" / "setup.cpp",
        """#include "lbm.hpp"

void main_setup() {
    const float citylbm_dx_m = 2.00000000f;
    // 导入建筑物 STL（体素化为固体壁面 TYPE_S）
    float3 stl_offset = float3(30.0000f, 60.0000f, 2.0000f);  // -DomainOrigin/Dx
    lbm.voxelize_stl("buildings.stl", stl_offset, float3x3(1.0f));
    const uint total_steps = 60000u;
}
""",
    )
    write(case_dir / "src" / "defines.hpp", "#define SX 10u\n#define SY 10u\n#define SZ 10u\n")
    write(case_dir / "buildings.stl", "solid smoke\nendsolid smoke\n")
    write(case_dir / "domain_origin.json", '{"Origin":[0,0,0]}\n')
    write(case_dir / "case_metadata.json", '{"Case":"CaseE","TimeSteps":60000,"Validation":{}}\n')


def create_short_generated_case(case_dir: Path) -> None:
    write(
        case_dir / "setup.cpp",
        """#include "lbm.hpp"

void main_setup() {
    const float citylbm_dx_m = 2.00000000f;
    const float citylbm_u_ref_si = 3.92829600f;
    const float citylbm_u_ref_lbm = 0.10000000f;
    const uint citylbm_stg_update_interval = 25u;
    const bool empty_tunnel = false;
    const uint Nx = lbm.get_Nx(), Ny = lbm.get_Ny(), Nz = lbm.get_Nz();
    while(lbm.get_t() < 1000u) {
        uint remaining = 1000u - (uint)lbm.get_t();
        uint steps_to_run = remaining < citylbm_stg_update_interval ? remaining : citylbm_stg_update_interval;
        lbm.run(steps_to_run);
    }
    while(lbm.get_t() < 1000u) {
        uint remaining = 1000u - (uint)lbm.get_t();
        uint steps_to_run = remaining < 100u ? remaining : 100u;
        uint save_remainder = (uint)lbm.get_t() % 100u;
        uint until_next_save = save_remainder == 0u ? 100u : 100u - save_remainder;
        if(steps_to_run > until_next_save) steps_to_run = until_next_save;
        if(steps_to_run > citylbm_stg_update_interval) steps_to_run = citylbm_stg_update_interval;
        lbm.run(steps_to_run);
        if((uint)lbm.get_t() % 100u == 0u || (uint)lbm.get_t() >= 1000u) {
            lbm.u.write_device_to_vtk("output/", true);
        }
    }
}
""",
    )
    write(case_dir / "defines.hpp", "#define SX 10u\n#define SY 10u\n#define SZ 10u\n")
    write(case_dir / "buildings.stl", "solid smoke\nendsolid smoke\n")
    write(case_dir / "domain_origin.json", '{"Origin":[0,0,0]}\n')
    write(
        case_dir / "case_metadata.json",
        json.dumps(
            {
                "Case": "CaseE",
                "TimeSteps": 1000,
                "SaveInterval": 100,
                "ExpectedVtkFrameCount": 10,
                "PaperRecommendedAveragingFrames": 40,
                "PaperRecommendedAverageStepSpan": 20000,
                "ExpectedPaperAverageStepSpan": 900,
                "PaperRecommendedAdaptiveAveragingFrames": 201,
                "ExpectedAdaptivePaperAverageStepSpan": 900,
                "SyntheticTurbulentInletRequested": True,
                "SyntheticTurbulentInletInjected": True,
                "SyntheticTurbulenceUpdateInterval": 25,
                "SyntheticTurbulenceMinimumRecommendedRefreshes": 200,
                "SyntheticTurbulenceExpectedFinalWindowRefreshCount": 36,
                "SyntheticTurbulentInletTemporalSamplingGate": "diagnostic_only_insufficient_stg_refreshes_in_average_window",
                "Validation": {},
            },
            indent=2,
        )
        + "\n",
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="citylbm_empty_tunnel_") as raw:
        temp = Path(raw)
        source_case = temp / "source_case"
        empty_case = temp / "empty_case"
        manifest_path = temp / "empty_manifest.json"
        af_csv = temp / "AF_caseA.csv"
        official = temp / "RS_caseA.csv"
        create_case(source_case)
        write(af_csv, "z,U,k\n0.1,1.0,0.01\n")
        write(official, "No.,x,y,z,V\n1,0,0,0.02,1.0\n")

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(source_case),
                "--out-dir",
                str(empty_case),
                "--fluidx3d-source",
                str(temp / "FluidX3D"),
                "--solver-cwd",
                str(temp / "SolverCwd"),
                "--manifest-out",
                str(manifest_path),
                "--baseline-id",
                "casea-empty-smoke",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "1,0,0",
                "--official",
                str(official),
                "--official-condition-filter",
                "CaseA",
                "--official-wind-filter",
                "N",
                "--af-csv",
                str(af_csv),
                "--expected-probe-row-count",
                "80",
                "--expected-probe-z",
                "0.02",
                "--average-last-n",
                "40",
                "--min-vtk-step-span",
                "20000",
                "--require-af-k",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise AssertionError((completed.returncode, completed.stdout, completed.stderr))

        source_setup = (source_case / "src" / "setup.cpp").read_text(encoding="utf-8")
        copied_setup = (empty_case / "src" / "setup.cpp").read_text(encoding="utf-8")
        if "const bool empty_tunnel = false;" not in source_setup:
            raise AssertionError(source_setup)
        if "const bool empty_tunnel = true;" not in copied_setup:
            raise AssertionError(copied_setup)

        manifest = load_json(manifest_path)
        if manifest["Schema"] != "citylbm.native_empty_tunnel_case.v1":
            raise AssertionError(manifest)
        if manifest["EmptyTunnelFlagStatus"] != "changed_false_to_true":
            raise AssertionError(manifest)
        if not manifest["GeometryVoxelizationDisabledByEmptyTunnelFlag"]:
            raise AssertionError(manifest)
        if not manifest["BuildingsStlRetainedForTraceability"]:
            raise AssertionError(manifest)
        if manifest["Expected"]["RequireAfK"] is not True:
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["AijCase"] != "CaseA":
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["WindVector"] != "1,0,0":
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["OfficialConditionFilter"] != "CaseA":
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["OfficialWindFilter"] != "N":
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["TimeSteps"] != 60000:
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["VtkSaveInterval"] != 1000:
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["VtkSaveStartStep"] != 10000:
            raise AssertionError(manifest["Expected"])
        if manifest["Expected"]["ExpectedVtkFrameCount"] != 51:
            raise AssertionError(manifest["Expected"])
        if abs(manifest["Expected"]["Uref"] - 4.491) > 1.0e-9:
            raise AssertionError(manifest["Expected"])
        if abs(manifest["Expected"]["ZRef"] - 0.16000000002) > 1.0e-6:
            raise AssertionError(manifest["Expected"])
        if "ExpectedUref" not in manifest["InferredDefaults"]:
            raise AssertionError(manifest["InferredDefaults"])
        if manifest["SourceHashes"]["SetupCpp"] == manifest["CopiedHashes"]["SetupCpp"]:
            raise AssertionError("setup hash should change after empty_tunnel switch")
        if manifest["SourceHashes"]["DefinesHpp"] != manifest["CopiedHashes"]["DefinesHpp"]:
            raise AssertionError("defines hash should remain unchanged")

        commands = manifest["Commands"]
        for key in [
            "PreflightNoCfd",
            "InstallBuildRunFluidX3D",
            "RunnerPreflightOnly",
            "AuditInletDiagnosticsCsvAfterRun",
            "AuditInletProfileAfterRun",
            "AuditInletCorrelationAfterRun",
            "ValidationChainAfterRun",
        ]:
            command = commands[key]["Command"]
            if not command:
                raise AssertionError(f"empty command: {key}")
        if "run_native_fluidx3d_case.py" not in commands["InstallBuildRunFluidX3D"]["Command"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--install" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--run" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--disable-graphics-for-run" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--require-af-k" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--official-condition-filter" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--official-wind-filter" not in commands["PreflightNoCfd"]["Argv"]:
            raise AssertionError(commands["PreflightNoCfd"])
        if "--vtk-save-start-step" not in commands["PreflightNoCfd"]["Argv"]:
            raise AssertionError(commands["PreflightNoCfd"])
        if "--official-condition-filter" not in commands["ValidationChainAfterRun"]["Argv"]:
            raise AssertionError(commands["ValidationChainAfterRun"])
        if "--expected-uref" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if "--vtk-save-start-step" not in commands["InstallBuildRunFluidX3D"]["Argv"]:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        expected_vtk_dir = str((temp / "SolverCwd" / "output").resolve())
        run_argv = commands["InstallBuildRunFluidX3D"]["Argv"]
        if run_argv[run_argv.index("--output-dir") + 1] != expected_vtk_dir:
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if run_argv[run_argv.index("--solver-cwd") + 1] != str((temp / "SolverCwd").resolve()):
            raise AssertionError(commands["InstallBuildRunFluidX3D"])
        if manifest["Expected"]["VelocityScale"] != "53":
            raise AssertionError(manifest["Expected"])
        profile_argv = commands["AuditInletProfileAfterRun"]["Argv"]
        if profile_argv[2] != expected_vtk_dir:
            raise AssertionError(commands["AuditInletProfileAfterRun"])
        if "--metadata" not in profile_argv:
            raise AssertionError(commands["AuditInletProfileAfterRun"])
        if profile_argv[profile_argv.index("--velocity-scale") + 1] != "53":
            raise AssertionError(commands["AuditInletProfileAfterRun"])
        diagnostics_argv = commands["AuditInletDiagnosticsCsvAfterRun"]["Argv"]
        if "audit_inlet_diagnostics_csv.py" not in commands["AuditInletDiagnosticsCsvAfterRun"]["Command"]:
            raise AssertionError(commands["AuditInletDiagnosticsCsvAfterRun"])
        if str(temp / "SolverCwd" / "casea_inlet_turbulence_stats.csv") not in diagnostics_argv:
            raise AssertionError(commands["AuditInletDiagnosticsCsvAfterRun"])
        if "--require-k" not in diagnostics_argv:
            raise AssertionError(commands["AuditInletDiagnosticsCsvAfterRun"])
        if "--require-rms" not in diagnostics_argv:
            raise AssertionError(commands["AuditInletDiagnosticsCsvAfterRun"])
        correlation_argv = commands["AuditInletCorrelationAfterRun"]["Argv"]
        if correlation_argv[2] != expected_vtk_dir:
            raise AssertionError(commands["AuditInletCorrelationAfterRun"])
        if "--metadata" not in correlation_argv:
            raise AssertionError(commands["AuditInletCorrelationAfterRun"])
        if correlation_argv[correlation_argv.index("--velocity-scale") + 1] != "53":
            raise AssertionError(commands["AuditInletCorrelationAfterRun"])
        if "audit_inlet_profile_from_vtk.py" not in commands["AuditInletProfileAfterRun"]["Command"]:
            raise AssertionError(commands["AuditInletProfileAfterRun"])
        if "audit_inlet_correlation_from_vtk.py" not in commands["AuditInletCorrelationAfterRun"]["Command"]:
            raise AssertionError(commands["AuditInletCorrelationAfterRun"])
        if "--require-k-variance-check" not in commands["AuditInletCorrelationAfterRun"]["Argv"]:
            raise AssertionError(commands["AuditInletCorrelationAfterRun"])
        if "--native-manifest" not in commands["ValidationChainAfterRun"]["Argv"]:
            raise AssertionError(commands["ValidationChainAfterRun"])
        if "--u-ref" not in commands["ValidationChainAfterRun"]["Argv"]:
            raise AssertionError(commands["ValidationChainAfterRun"])

        completed_again = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(source_case),
                "--out-dir",
                str(empty_case),
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if completed_again.returncode == 0:
            raise AssertionError("existing destination should not be overwritten")

        range_empty_case = temp / "empty_case_range"
        range_manifest_path = temp / "empty_manifest_range.json"
        range_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(source_case),
                "--out-dir",
                str(range_empty_case),
                "--manifest-out",
                str(range_manifest_path),
                "--fluidx3d-source",
                str(temp / "FluidX3D"),
                "--expected-aij-case",
                "CaseA",
                "--expected-probe-z-min",
                "0.01",
                "--expected-probe-z-max",
                "0.28",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if range_run.returncode != 0:
            raise AssertionError((range_run.returncode, range_run.stdout, range_run.stderr))
        range_manifest = load_json(range_manifest_path)
        expected_range = range_manifest["Expected"]
        if expected_range["ExpectedProbeZ"] is not None:
            raise AssertionError(expected_range)
        if abs(expected_range["ExpectedProbeZMin"] - 0.01) > 1.0e-9:
            raise AssertionError(expected_range)
        if abs(expected_range["ExpectedProbeZMax"] - 0.28) > 1.0e-9:
            raise AssertionError(expected_range)
        for key in ["PreflightNoCfd", "RunnerPreflightOnly"]:
            argv = range_manifest["Commands"][key]["Argv"]
            if "--expected-probe-z-min" not in argv or "--expected-probe-z-max" not in argv:
                raise AssertionError(range_manifest["Commands"][key])

        conflicting = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(source_case),
                "--out-dir",
                str(temp / "empty_case_conflict"),
                "--expected-probe-z",
                "0.16",
                "--expected-probe-z-min",
                "0.01",
                "--expected-probe-z-max",
                "0.28",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if conflicting.returncode == 0:
            raise AssertionError("conflicting probe z arguments should fail")

        legacy_source_case = temp / "legacy_source_case"
        legacy_empty_case = temp / "legacy_empty_case"
        legacy_manifest_path = temp / "legacy_empty_manifest.json"
        create_legacy_generated_case(legacy_source_case)
        legacy_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(legacy_source_case),
                "--out-dir",
                str(legacy_empty_case),
                "--manifest-out",
                str(legacy_manifest_path),
                "--fluidx3d-source",
                str(temp / "FluidX3D"),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--official",
                str(official),
                "--official-condition-filter",
                "ac",
                "--official-wind-filter",
                "N",
                "--af-csv",
                str(af_csv),
                "--expected-probe-z",
                "2.0",
                "--require-af-k",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if legacy_run.returncode != 0:
            raise AssertionError((legacy_run.returncode, legacy_run.stdout, legacy_run.stderr))
        legacy_setup = (legacy_empty_case / "src" / "setup.cpp").read_text(encoding="utf-8")
        if "const bool empty_tunnel = true;" not in legacy_setup:
            raise AssertionError(legacy_setup)
        if "if(!empty_tunnel)" not in legacy_setup:
            raise AssertionError(legacy_setup)
        if "    lbm.voxelize_stl(\"buildings.stl\", stl_offset, float3x3(1.0f));" not in legacy_setup:
            raise AssertionError(legacy_setup)
        legacy_manifest = load_json(legacy_manifest_path)
        if legacy_manifest["EmptyTunnelFlagStatus"] != "injected_true_and_guarded_voxelize_stl":
            raise AssertionError(legacy_manifest)
        if legacy_manifest["Expected"]["OfficialConditionFilter"] != "ac":
            raise AssertionError(legacy_manifest["Expected"])

        override_source_case = temp / "override_source_case"
        override_empty_case = temp / "override_empty_case"
        override_manifest_path = temp / "override_empty_manifest.json"
        create_short_generated_case(override_source_case)
        override_run = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--case-dir",
                str(override_source_case),
                "--out-dir",
                str(override_empty_case),
                "--manifest-out",
                str(override_manifest_path),
                "--fluidx3d-source",
                str(temp / "FluidX3D"),
                "--expected-aij-case",
                "CaseE",
                "--expected-wind-direction",
                "N",
                "--expected-wind-vector",
                "0,-1,0",
                "--time-steps",
                "60000",
                "--vtk-save-interval",
                "1000",
                "--vtk-save-start-step",
                "10000",
                "--expected-vtk-frame-count",
                "51",
                "--average-last-n",
                "40",
                "--min-vtk-step-span",
                "20000",
            ],
            cwd=str(REPO),
            text=True,
            capture_output=True,
        )
        if override_run.returncode != 0:
            raise AssertionError((override_run.returncode, override_run.stdout, override_run.stderr))
        override_setup = (override_empty_case / "setup.cpp").read_text(encoding="utf-8")
        for expected in [
            "while(lbm.get_t() < 60000u)",
            "uint remaining = 60000u - (uint)lbm.get_t();",
            "uint steps_to_run = remaining < 1000u ? remaining : 1000u;",
            "uint save_remainder = (uint)lbm.get_t() % 1000u;",
            "uint until_next_save = save_remainder == 0u ? 1000u : 1000u - save_remainder;",
            "if(((uint)lbm.get_t() >= 10000u && (uint)lbm.get_t() % 1000u == 0u) || (uint)lbm.get_t() >= 60000u) {",
        ]:
            if expected not in override_setup:
                raise AssertionError(override_setup)
        for stale in [
            "while(lbm.get_t() < 1000u)",
            "uint remaining = 1000u - (uint)lbm.get_t();",
            "uint save_remainder = (uint)lbm.get_t() % 100u;",
            "metadata_stg_refresh_count_36",
        ]:
            if stale in override_setup:
                raise AssertionError(override_setup)
        override_metadata = load_json(override_empty_case / "case_metadata.json")
        if override_metadata["TimeSteps"] != 60000:
            raise AssertionError(override_metadata)
        if override_metadata["SaveInterval"] != 1000:
            raise AssertionError(override_metadata)
        if override_metadata["ExpectedVtkFrameCount"] != 51:
            raise AssertionError(override_metadata)
        if override_metadata["VtkOutput"]["SaveStartStep"] != 10000:
            raise AssertionError(override_metadata)
        if override_metadata["ExpectedAdaptivePaperAverageStepSpan"] != 39000:
            raise AssertionError(override_metadata)
        if override_metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] != 1560:
            raise AssertionError(override_metadata)
        if override_metadata["SyntheticTurbulentInletTemporalSamplingGate"] != "pass":
            raise AssertionError(override_metadata)
        override_manifest = load_json(override_manifest_path)
        if override_manifest["RunPlanPatch"]["Applied"] is not True:
            raise AssertionError(override_manifest["RunPlanPatch"])
        if override_manifest["MetadataRunPlanOverride"]["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] != 1560:
            raise AssertionError(override_manifest["MetadataRunPlanOverride"])

    print("prepare_native_empty_tunnel_case_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
