#!/usr/bin/env python3
"""Smoke-test the native FluidX3D runner manifest and install path."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "scripts" / "run_native_fluidx3d_case.py"
PROTOCOL_STATUSES = {
    "inlet_mean_profile": "pass",
    "inlet_turbulence_k": "pass",
    "inlet_turbulence_length_scale": "pass",
    "inlet_reynolds_stress_tensor": "pass",
    "inlet_temporal_sampling": "pass",
    "inlet_distribution_consistency": "pass",
    "native_fluidx3d_baseline": "pass",
    "boundary_conditions": "pass",
    "wall_roughness_model": "pass",
    "lbm_stability_scaling": "pass",
    "time_averaging": "pass",
    "wind_direction_sign": "pass",
    "coordinate_transform": "pass",
    "probe_projection": "pass",
    "normalization_basis": "pass",
    "systematic_bias_gate": "pass",
    "grid_resolution": "pass",
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run_cmd(args: list[str], expected_returncode: int = 0) -> subprocess.CompletedProcess[str]:
    args = list(args)
    if str(RUNNER) in args and "--min-flow-throughs" not in args:
        args.extend(["--min-flow-throughs", "0"])
    completed = subprocess.run(args, text=True, capture_output=True, check=False)
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"unexpected return code {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def create_source(root: Path) -> None:
    write(root / "FluidX3D.sln", "Microsoft Visual Studio Solution File\n")
    write(
        root / "FluidX3D.vcxproj",
        "<Project><PropertyGroup><PlatformToolset>v142</PlatformToolset></PropertyGroup></Project>\n",
    )
    write(root / "src" / "setup.cpp", "// original native setup\n")
    write(root / "src" / "defines.hpp", "// original native defines\n")
    write(root / "src" / "lbm.hpp", "// lbm header\n")
    write(root / "src" / "lbm.cpp", "// lbm source\n")


def create_equilibrium_reconstruction_source(root: Path) -> None:
    create_source(root)
    write(
        root / "src" / "kernel.cpp",
        """
kernel void reconstruct_equilibrium_boundaries(global fpxx* fi, const global float* rho, const global float* u, const global uchar* flags, const ulong t) {
    const uxx n = get_global_id(0);
}
""".lstrip(),
    )
    write(
        root / "src" / "lbm.hpp",
        "class LBM { public: void reconstruct_equilibrium_boundaries(); };\n",
    )
    write(
        root / "src" / "lbm.cpp",
        "void LBM::reconstruct_equilibrium_boundaries() {}\n",
    )


def validation_protocol_audit(status_overrides: dict | None = None) -> dict:
    status_overrides = status_overrides or {}
    return {
        "SchemaVersion": 1,
        "Gate": "ready_for_validation_run",
        "AijCase": "CaseA",
        "WindDirection": "N",
        "WindDirectionUnitVector": [1.0, 0.0, 0.0],
        "Items": [
            {"Key": key, "Status": status_overrides.get(key, status), "Evidence": "smoke"}
            for key, status in PROTOCOL_STATUSES.items()
        ],
    }


def create_case(
    root: Path,
    *,
    citylbm_root_layout: bool = False,
    time_steps: int = 40000,
    save_interval: int = 1000,
) -> None:
    setup_path = root / "setup.cpp" if citylbm_root_layout else root / "src" / "setup.cpp"
    defines_path = root / "defines.hpp" if citylbm_root_layout else root / "src" / "defines.hpp"
    write(
        setup_path,
        f"""
// CityLBM smoke setup
// WindProfile: CustomTable
const float profile_z_m[] = {{0.0f, 10.0f}};
const float profile_u_lbm[] = {{0.01f, 0.02f}};
const float profile_k_lbm[] = {{0.0001f, 0.0002f}};
float3 syntheticTurbulentInlet(uint x, uint y, uint z, uint t) {{ return float3(0.01f, 0.0f, 0.0f); }}
void main_setup() {{
    LBM lbm(SX, SY, SZ, 0.01666667f);
    while(lbm.get_t() < {time_steps}u) {{
        uint remaining = {time_steps}u - (uint)lbm.get_t();
        uint steps_to_run = remaining < {save_interval}u ? remaining : {save_interval}u;
        applySyntheticTurbulentInlet((uint)lbm.get_t());
        lbm.run(steps_to_run);
    }}
}}
""".lstrip(),
    )
    write(
        defines_path,
        """
#define SX 100u
#define SY 60u
#define SZ 40u
""".lstrip(),
    )
    metadata = {
        "AijCase": "CaseA",
        "WindDirection": "N",
        "WindDirectionUnitVector": [1.0, 0.0, 0.0],
        "ReferenceWindSpeedMps": 5.0,
        "VelocityScaleMpsToLbm": 0.02,
        "WindProfile": "CustomTable",
        "SyntheticTurbulentInletRequested": True,
        "SyntheticTurbulentInletInjected": True,
        "InletDistributionFunctionReconstruction": True,
        "SyntheticTurbulentInletDistributionTreatment": "distribution_function_reconstructed",
        "PaperGradeTurbulentInletPrerequisiteGate": "ready_for_validation_run",
        "PaperGradeBoundaryPrerequisiteGate": "ready_for_validation_run",
        "BoundaryNonReflectingOutletImplemented": True,
        "BoundarySideTopWindTunnelEquivalentImplemented": True,
        "BoundaryRoughWallFunctionImplemented": True,
        "BoundaryPrecursorOrRecyclingImplemented": True,
        "BoundaryBlockageFetchEvidenceArchived": True,
        "SyntheticTurbulenceUpdateInterval": 100,
        "SyntheticTurbulenceMinimumRecommendedRefreshes": 200,
        "SyntheticTurbulenceExpectedFinalWindowRefreshCount": 390,
    }
    write(root / "case_metadata.json", json.dumps(metadata, indent=2))
    write(root / "domain_origin.json", json.dumps({"origin": [0, 0, 0]}, indent=2))
    write(root / "validation_protocol_audit.json", json.dumps(validation_protocol_audit(), indent=2))
    write(root / "buildings.stl", "solid smoke\nendsolid smoke\n")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        source_root = temp / "FluidX3D"
        case_dir = temp / "case"
        create_source(source_root)
        create_case(case_dir)

        sdk_pin_source = temp / "sdk_pin_source"
        sdk_pin_case = temp / "sdk_pin_case"
        create_source(sdk_pin_source)
        write(
            sdk_pin_source / "FluidX3D.vcxproj",
            """
<Project>
  <PropertyGroup Label="Globals">
    <WindowsTargetPlatformVersion>10.0</WindowsTargetPlatformVersion>
  </PropertyGroup>
  <PropertyGroup>
    <PlatformToolset>v142</PlatformToolset>
  </PropertyGroup>
</Project>
""".lstrip(),
        )
        create_case(sdk_pin_case)
        sdk_pin_manifest = temp / "sdk_pin" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(sdk_pin_case),
                "--fluidx3d-source",
                str(sdk_pin_source),
                "--out",
                str(sdk_pin_manifest),
                "--baseline-id",
                "smoke-casea-native-sdk-pin",
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
                "--msbuild",
                sys.executable,
                "--platform-toolset",
                "v143",
                "--windows-sdk-version",
                "10.0.99999.0",
                "--install",
                "--build",
                "--allow-diagnostic-execution",
            ],
            expected_returncode=2,
        )
        sdk_pin_result = load_json(sdk_pin_manifest)
        if "/p:WindowsTargetPlatformVersion=10.0.99999.0" not in sdk_pin_result["Build"]["Command"]:
            raise AssertionError(sdk_pin_result["Build"])
        if sdk_pin_result["Build"]["WindowsSdkVersionResolved"] != "10.0.99999.0":
            raise AssertionError(sdk_pin_result["Build"])
        if sdk_pin_result["WindowsSdkProjectPatch"]["Gate"] != "pass":
            raise AssertionError(sdk_pin_result["WindowsSdkProjectPatch"])
        if not sdk_pin_result["WindowsSdkProjectPatch"]["Modified"]:
            raise AssertionError(sdk_pin_result["WindowsSdkProjectPatch"])
        if "10.0.99999.0" not in (sdk_pin_source / "FluidX3D.vcxproj").read_text(encoding="utf-8"):
            raise AssertionError((sdk_pin_source / "FluidX3D.vcxproj").read_text(encoding="utf-8"))

        dry_manifest = temp / "dry" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(dry_manifest),
                "--baseline-id",
                "smoke-casea-native",
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
                "--min-flow-throughs",
                "0",
            ]
        )
        dry = load_json(dry_manifest)
        if dry["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(dry["RunnerGate"])
        if dry["NativeFluidX3DPathExplicitlyProvided"] is not True:
            raise AssertionError("native path was not marked explicit")
        if dry["NativeFluidX3DSourceValidation"]["IsValid"] is not True:
            raise AssertionError(dry["NativeFluidX3DSourceValidation"])
        if dry["ValidationProtocolAuditGate"]["Gate"] != "pass":
            raise AssertionError(dry["ValidationProtocolAuditGate"])
        if dry["CaseMetadataPreconditionGate"]["Gate"] != "pass":
            raise AssertionError(dry["CaseMetadataPreconditionGate"])
        if dry["CaseSetupSourcePreconditionGate"]["Gate"] != "pass":
            raise AssertionError(dry["CaseSetupSourcePreconditionGate"])
        if dry["ValidationProtocolAuditGate"]["Statuses"]["inlet_distribution_consistency"] != "pass":
            raise AssertionError(dry["ValidationProtocolAuditGate"])
        if dry["PlannedSyntheticInletSamplingGate"]["Gate"] != "pass":
            raise AssertionError(dry["PlannedSyntheticInletSamplingGate"])
        if dry["PlannedSyntheticInletSamplingGate"]["ComputedRefreshCount"] != 390:
            raise AssertionError(dry["PlannedSyntheticInletSamplingGate"])
        if dry["PlannedVtkScheduleGate"]["RecommendedAverageLastNForStepSpan"] != 40:
            raise AssertionError(dry["PlannedVtkScheduleGate"])
        if dry["SharedRunConditions"]["RecommendedMinimumTimeStepsForCurrentSaveInterval"] != 40000:
            raise AssertionError(dry["SharedRunConditions"])
        if dry["ActualVtkOutputGate"]["Gate"] != "not_applicable":
            raise AssertionError(dry["ActualVtkOutputGate"])
        dry_accuracy_gate = dry["NativeAccuracyEvidenceGate"]
        if dry_accuracy_gate["Gate"] != "fail":
            raise AssertionError(dry_accuracy_gate)
        for reason in (
            "native_run_not_requested",
            "actual_vtk_output_not_required_by_this_invocation",
            "actual_vtk_output_gate_not_pass:not_applicable",
        ):
            if reason not in dry_accuracy_gate["Reasons"]:
                raise AssertionError(dry_accuracy_gate)
        dry_paper_gate = dry["PaperUseGate"]
        if dry_paper_gate["Gate"] != "fail" or dry_paper_gate["PaperUsable"] is not False:
            raise AssertionError(dry_paper_gate)
        if "native_accuracy_evidence:native_run_not_requested" not in dry_paper_gate["Reasons"]:
            raise AssertionError(dry_paper_gate)
        if dry["Install"]["Performed"] is not False:
            raise AssertionError(dry["Install"])
        if dry["PreInstallNativeSourceFiles"][0]["Role"] != "Pre-install Native FluidX3D original setup":
            raise AssertionError(dry["PreInstallNativeSourceFiles"])
        if dry["PreInstallCaseToSourceParityGate"]["Gate"] != "pass":
            raise AssertionError(dry["PreInstallCaseToSourceParityGate"])
        if dry["CaseToRunSourceParityGate"]["Gate"] != "pass":
            raise AssertionError(dry["CaseToRunSourceParityGate"])
        dry_pairs = {pair["Role"]: pair for pair in dry["CaseToRunSourceParityGate"]["Pairs"]}
        for role in ["setup", "defines"]:
            if dry_pairs[role]["Match"] is not False or dry_pairs[role]["AllowedMismatch"] is not True:
                raise AssertionError(dry_pairs[role])
            if dry_pairs[role]["PendingInstallOnly"] is not True:
                raise AssertionError(dry_pairs[role])
        for note in [
            "case_setup_hash_mismatch_source_pending_install_preflight",
            "case_defines_hash_mismatch_source_pending_install_preflight",
        ]:
            if note not in dry["CaseToRunSourceParityGate"]["Notes"]:
                raise AssertionError(dry["CaseToRunSourceParityGate"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// original native setup\n":
            raise AssertionError("dry-run modified source setup.cpp")
        roles = {record["Role"] for record in dry["RequiredSourceFiles"]}
        for role in [
            "Native FluidX3D original setup",
            "Native FluidX3D original defines",
            "Native FluidX3D lbm.hpp",
            "Native FluidX3D lbm.cpp",
            "FluidX3D setup",
            "FluidX3D defines",
            "Case metadata",
            "Domain origin",
            "Validation protocol audit",
        ]:
            if role not in roles:
                raise AssertionError(f"missing manifest role: {role}")

        override_case_dir = temp / "run_plan_override_case"
        create_case(override_case_dir)
        write(override_case_dir / "src" / "defines.hpp", "// original native defines\n")
        override_metadata_path = override_case_dir / "case_metadata.json"
        override_metadata = load_json(override_metadata_path)
        override_metadata["RunPlanOverride"] = {
            "AppliedBy": "prepare_native_empty_tunnel_case.py",
            "TimeSteps": 40000,
            "VtkSaveInterval": 1000,
            "VtkSaveStartStep": 0,
        }
        write(override_metadata_path, json.dumps(override_metadata, indent=2))
        override_manifest = temp / "run_plan_override" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(override_case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(override_manifest),
                "--baseline-id",
                "smoke-casea-run-plan-override",
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
                "--min-flow-throughs",
                "0",
            ]
        )
        override_result = load_json(override_manifest)
        override_parity = override_result["PreInstallCaseToSourceParityGate"]
        if override_parity["Gate"] != "pass":
            raise AssertionError(override_parity)
        if "case_setup_hash_mismatch_source_allowed_by_run_plan_override" not in override_parity["Notes"]:
            raise AssertionError(override_parity)
        setup_pair = [pair for pair in override_parity["Pairs"] if pair["Role"] == "setup"][0]
        if setup_pair["Match"] is not False or setup_pair["AllowedMismatch"] is not True:
            raise AssertionError(setup_pair)
        defines_pair = [pair for pair in override_parity["Pairs"] if pair["Role"] == "defines"][0]
        if defines_pair["Match"] is not True or defines_pair["AllowedMismatch"] is not False:
            raise AssertionError(defines_pair)

        const_case_dir = temp / "const_case"
        create_case(const_case_dir)
        write(
            const_case_dir / "src" / "setup.cpp",
            """
// CityLBM const-style smoke setup
// WindProfile: CustomTable
const float profile_z_m[] = {0.0f, 10.0f};
const float profile_u_lbm[] = {0.01f, 0.02f};
const float profile_k_lbm[] = {0.0001f, 0.0002f};
float3 syntheticTurbulentInlet(uint x, uint y, uint z, uint t) { return float3(0.01f, 0.0f, 0.0f); }
void applySyntheticTurbulentInlet(uint t) {}
void main_setup() {
    LBM lbm(SX, SY, SZ, 0.01666667f);
    const uint vtk_save_interval = 1000u;
    const uint total_steps = 60000u;
    while(lbm.get_t() < total_steps) {
        const uint current = (uint)lbm.get_t();
        const uint remaining = total_steps - current;
        const uint steps_to_run = remaining < vtk_save_interval ? remaining : vtk_save_interval;
        applySyntheticTurbulentInlet(current);
        lbm.run(steps_to_run);
        const uint now = (uint)lbm.get_t();
        if(vtk_save_interval > 0u && now % vtk_save_interval == 0u) {}
    }
}
""".lstrip(),
        )
        const_manifest = temp / "const_case_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(const_case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(const_manifest),
                "--baseline-id",
                "smoke-casea-native-const-style",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "60000",
                "--vtk-save-interval",
                "1000",
                "--vtk-save-start-step",
                "10000",
                "--expected-vtk-frame-count",
                "51",
            ]
        )
        const_result = load_json(const_manifest)
        if const_result["CaseSetupSourcePreconditionGate"]["Gate"] != "pass":
            raise AssertionError(const_result["CaseSetupSourcePreconditionGate"])

        official = temp / "official_casea.csv"
        af_csv = temp / "af_casea.csv"
        write(
            official,
            "No.,case,wind,z,Velocity_Ratio\n"
            "1,CaseA,N,2.0,0.8\n"
            "2,CaseA,N,2.0,1.1\n"
            "3,CaseA,S,2.0,0.9\n",
        )
        write(af_csv, "z(m),U(m/s),k(m2/s2)\n0,0.0,0.01\n10,4.0,0.02\n")
        official_manifest = temp / "official_inputs" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(official_manifest),
                "--baseline-id",
                "smoke-casea-native-official-inputs",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--official",
                str(official),
                "--af-csv",
                str(af_csv),
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "2.0",
                "--z-ref",
                "10",
                "--expected-uref",
                "4.0",
                "--expected-wind-vector",
                "1,0,0",
                "--require-af-k",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ]
        )
        official_result = load_json(official_manifest)
        if official_result["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(official_result["RunnerGate"])
        if official_result["OfficialInputPreconditionGate"]["Gate"] != "pass":
            raise AssertionError(official_result["OfficialInputPreconditionGate"])

        single_case_official = temp / "official_casea_single_file.csv"
        write(
            single_case_official,
            "No.,x(m),y(m),z(m),U(m/s)\n"
            "1,0.0,0.0,2.0,0.8\n"
            "2,1.0,0.0,2.0,1.1\n",
        )
        single_case_manifest = temp / "official_single_case_inputs" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(single_case_manifest),
                "--baseline-id",
                "smoke-casea-native-single-case-official-inputs",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--official",
                str(single_case_official),
                "--af-csv",
                str(af_csv),
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "2.0",
                "--z-ref",
                "10",
                "--expected-uref",
                "4.0",
                "--expected-wind-vector",
                "1,0,0",
                "--require-af-k",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ]
        )
        single_case_result = load_json(single_case_manifest)
        single_official_gate = single_case_result["OfficialInputPreconditionGate"]["OfficialProbeAudit"]
        if single_case_result["OfficialInputPreconditionGate"]["Gate"] != "pass":
            raise AssertionError(single_case_result["OfficialInputPreconditionGate"])
        if single_official_gate["AssumedSingleCaseFile"] is not True:
            raise AssertionError(single_official_gate)
        if single_official_gate["AssumedSingleWindFile"] is not True:
            raise AssertionError(single_official_gate)

        bad_official_manifest = temp / "bad_official_inputs" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(bad_official_manifest),
                "--baseline-id",
                "smoke-casea-native-bad-official-inputs",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--official",
                str(official),
                "--af-csv",
                str(af_csv),
                "--expected-probe-row-count",
                "2",
                "--expected-probe-z",
                "1.5",
                "--z-ref",
                "10",
                "--expected-uref",
                "3.0",
                "--expected-wind-vector",
                "0,-1,0",
                "--require-af-k",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
            ],
            expected_returncode=2,
        )
        bad_official = load_json(bad_official_manifest)
        if bad_official["OfficialInputPreconditionGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(bad_official["OfficialInputPreconditionGate"])
        for reason in [
            "af:expected_uref_3_does_not_match_af_u_at_zref_4",
            "official:official_z_mismatch_count_2",
            "wind_vector_mismatch",
        ]:
            if reason not in bad_official["RunnerGate"]["Reasons"]:
                raise AssertionError(bad_official["RunnerGate"])

        nondiv_case = temp / "nondiv_case"
        create_case(nondiv_case, time_steps=40500)
        nondiv_metadata_path = nondiv_case / "case_metadata.json"
        nondiv_metadata = load_json(nondiv_metadata_path)
        nondiv_metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] = 385
        write(nondiv_metadata_path, json.dumps(nondiv_metadata, indent=2))
        nondiv_manifest = temp / "nondiv" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(nondiv_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(nondiv_manifest),
                "--baseline-id",
                "smoke-casea-native-nondivisible-window",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40500",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "41",
            ]
        )
        nondiv = load_json(nondiv_manifest)
        if nondiv["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(nondiv["RunnerGate"])
        if nondiv["SharedRunConditions"]["ComputedVtkFrameCount"] != 41:
            raise AssertionError(nondiv["SharedRunConditions"])
        if nondiv["SharedRunConditions"]["ExpectedFinalWindowStepSpan"] != 38500:
            raise AssertionError(nondiv["SharedRunConditions"])
        if nondiv["PlannedSyntheticInletSamplingGate"]["ComputedRefreshCount"] != 385:
            raise AssertionError(nondiv["PlannedSyntheticInletSamplingGate"])

        save_start_case = temp / "save_start_case"
        create_case(save_start_case, time_steps=60000)
        save_start_metadata_path = save_start_case / "case_metadata.json"
        save_start_metadata = load_json(save_start_metadata_path)
        save_start_metadata["VtkOutput"] = {
            "SaveIntervalSteps": 1000,
            "SaveStartStep": 10000,
            "EstimatedPostSpinupFrameCount": 51,
        }
        write(save_start_metadata_path, json.dumps(save_start_metadata, indent=2))
        save_start_manifest = temp / "save_start" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(save_start_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(save_start_manifest),
                "--baseline-id",
                "smoke-casea-native-save-start",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "60000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "51",
            ]
        )
        save_start = load_json(save_start_manifest)
        if save_start["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(save_start["RunnerGate"])
        if save_start["SharedRunConditions"]["SaveStartStep"] != 10000:
            raise AssertionError(save_start["SharedRunConditions"])
        if save_start["SharedRunConditions"]["ComputedVtkFrameCount"] != 51:
            raise AssertionError(save_start["SharedRunConditions"])
        if save_start["SharedRunConditions"]["ExpectedFinalWindowStepSpan"] != 39000:
            raise AssertionError(save_start["SharedRunConditions"])

        install_manifest = temp / "install" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(install_manifest),
                "--baseline-id",
                "smoke-casea-native-install",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--install",
            ]
        )
        installed = load_json(install_manifest)
        if installed["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(installed["RunnerGate"])
        if installed["Install"]["Performed"] is not True:
            raise AssertionError(installed["Install"])
        if installed["PostInstallCaseToSourceParityGate"]["Gate"] != "pass":
            raise AssertionError(installed["PostInstallCaseToSourceParityGate"])
        if installed["CaseToRunSourceParityGate"]["Gate"] != "pass":
            raise AssertionError(installed["CaseToRunSourceParityGate"])
        effective = {record["Role"]: record for record in installed["EffectiveRunSourceFiles"]}
        if effective["Effective FluidX3D setup"]["Sha256"] != sha256_file(case_dir / "src" / "setup.cpp"):
            raise AssertionError(effective["Effective FluidX3D setup"])
        if len(installed["Install"]["Backups"]) != 2:
            raise AssertionError(installed["Install"])
        installed_setup = (source_root / "src" / "setup.cpp").read_text(encoding="utf-8")
        if "profile_z_m" not in installed_setup or "applySyntheticTurbulentInlet" not in installed_setup:
            raise AssertionError("install did not replace setup.cpp")
        if not (install_manifest.parent / "native_source_backups").exists():
            raise AssertionError("backup directory was not created")

        fallback_source = temp / "FluidX3D_equilibrium_only"
        fallback_case = temp / "fallback_case"
        create_equilibrium_reconstruction_source(fallback_source)
        create_case(fallback_case)
        write(
            fallback_case / "src" / "defines.hpp",
            "#define EQUILIBRIUM_BOUNDARIES\n"
            "#define RECONSTRUCT_INLET_STRESS_DDF\n"
            "#define INLET_STRESS_U_REF_LBM 0.10000000f\n",
        )
        fallback_manifest = temp / "fallback_install" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(fallback_case),
                "--fluidx3d-source",
                str(fallback_source),
                "--out",
                str(fallback_manifest),
                "--baseline-id",
                "smoke-casea-native-install-equilibrium-fallback",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "40",
                "--install",
            ]
        )
        fallback = load_json(fallback_manifest)
        adaptation = fallback["ReconstructionMacroAdaptation"]
        if adaptation["Gate"] != "pass" or adaptation["Modified"] is not True:
            raise AssertionError(adaptation)
        for action in ["disabled_RECONSTRUCT_INLET_STRESS_DDF", "enabled_RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF"]:
            if action not in adaptation["AppliedActions"]:
                raise AssertionError(adaptation)
        fallback_case_defines = (fallback_case / "src" / "defines.hpp").read_text(encoding="utf-8")
        fallback_source_defines = (fallback_source / "src" / "defines.hpp").read_text(encoding="utf-8")
        if "#define RECONSTRUCT_EQUILIBRIUM_BOUNDARY_DDF" not in fallback_source_defines:
            raise AssertionError(fallback_source_defines)
        if "\n#define RECONSTRUCT_INLET_STRESS_DDF" in "\n" + fallback_source_defines:
            raise AssertionError(fallback_source_defines)
        if fallback_case_defines != fallback_source_defines:
            raise AssertionError((fallback_case_defines, fallback_source_defines))
        if fallback["PostInstallCaseToSourceParityGate"]["Gate"] != "pass":
            raise AssertionError(fallback["PostInstallCaseToSourceParityGate"])

        stale_setup_case = temp / "stale_setup_case"
        create_case(stale_setup_case)
        write(
            stale_setup_case / "src" / "setup.cpp",
            """
// WindProfile: PowerLaw
float3 windProfile(uint z_cell) { return float3(0.0f, -0.1f, 0.0f); }
void main_setup() {
    LBM lbm(SX, SY, SZ, 0.01666667f);
    while(lbm.get_t() < 2000u) {
        uint remaining = 2000u - (uint)lbm.get_t();
        uint steps_to_run = remaining < 1000u ? remaining : 1000u;
        lbm.run(steps_to_run);
    }
}
""".lstrip(),
        )
        stale_setup_manifest = temp / "stale_setup" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(stale_setup_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(stale_setup_manifest),
                "--baseline-id",
                "smoke-casea-native-stale-setup",
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
            ],
            expected_returncode=2,
        )
        stale_setup = load_json(stale_setup_manifest)
        if stale_setup["CaseSetupSourcePreconditionGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(stale_setup["CaseSetupSourcePreconditionGate"])
        for reason in [
            "case_setup_source_not_customtable",
            "case_setup_source_stale_powerlaw_profile",
            "case_setup_source_missing_profile_z_m",
            "case_setup_source_missing_profile_u_lbm",
            "case_setup_source_missing_profile_k_lbm",
            "case_setup_source_missing_synthetic_turbulent_inlet_function",
            "case_setup_source_missing_synthetic_turbulent_inlet_refresh_loop",
            "case_setup_source_time_steps_mismatch_expected_40000",
        ]:
            if reason not in stale_setup["RunnerGate"]["Reasons"]:
                raise AssertionError(stale_setup["RunnerGate"])

        stale_source_root = temp / "FluidX3D_stale_source"
        stale_case = temp / "stale_case"
        create_source(stale_source_root)
        create_case(stale_case)
        stale_manifest = temp / "stale" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(stale_case),
                "--fluidx3d-source",
                str(stale_source_root),
                "--out",
                str(stale_manifest),
                "--baseline-id",
                "smoke-casea-native-stale-source",
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
                "--build",
            ],
            expected_returncode=2,
        )
        stale = load_json(stale_manifest)
        if stale["PreExecutionGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(stale["PreExecutionGate"])
        if stale["Build"]["Gate"] != "blocked":
            raise AssertionError(stale["Build"])
        for reason in [
            "execution_requested_without_install_or_case_source_parity",
            "pre_install_case_source_parity:case_setup_hash_mismatch_source",
            "pre_install_case_source_parity:case_defines_hash_mismatch_source",
        ]:
            if reason not in stale["RunnerGate"]["Reasons"]:
                raise AssertionError(stale["RunnerGate"])
        if (stale_source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// original native setup\n":
            raise AssertionError("stale-source preflight unexpectedly modified setup.cpp")

        citylbm_layout_source = temp / "FluidX3D_citylbm_layout"
        citylbm_layout_case = temp / "citylbm_layout_case"
        create_source(citylbm_layout_source)
        create_case(citylbm_layout_case, citylbm_root_layout=True)

        citylbm_layout_manifest = temp / "citylbm_layout" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(citylbm_layout_case),
                "--fluidx3d-source",
                str(citylbm_layout_source),
                "--out",
                str(citylbm_layout_manifest),
                "--baseline-id",
                "smoke-casea-native-citylbm-layout",
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
                "--install",
            ]
        )
        citylbm_layout = load_json(citylbm_layout_manifest)
        if citylbm_layout["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(citylbm_layout["RunnerGate"])
        by_role = {record["Role"]: record for record in citylbm_layout["RequiredSourceFiles"]}
        if by_role["FluidX3D setup"]["SelectedRelativePath"] != "setup.cpp":
            raise AssertionError(by_role["FluidX3D setup"])
        if by_role["FluidX3D defines"]["SelectedRelativePath"] != "defines.hpp":
            raise AssertionError(by_role["FluidX3D defines"])
        if citylbm_layout["Install"]["Performed"] is not True:
            raise AssertionError(citylbm_layout["Install"])
        citylbm_layout_setup = (citylbm_layout_source / "src" / "setup.cpp").read_text(encoding="utf-8")
        if "profile_z_m" not in citylbm_layout_setup or "applySyntheticTurbulentInlet" not in citylbm_layout_setup:
            raise AssertionError("CityLBM root-layout setup.cpp was not installed into native src/setup.cpp")
        installed_defines = (citylbm_layout_source / "src" / "defines.hpp").read_text(encoding="utf-8")
        expected_defines = (citylbm_layout_case / "defines.hpp").read_text(encoding="utf-8")
        if installed_defines != expected_defines:
            raise AssertionError("CityLBM root-layout defines.hpp was not installed into native src/defines.hpp")

        short_manifest = temp / "short" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(short_manifest),
                "--baseline-id",
                "smoke-casea-native-short",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "5000",
                "--vtk-save-interval",
                "1000",
                "--expected-vtk-frame-count",
                "5",
            ],
            expected_returncode=2,
        )
        short = load_json(short_manifest)
        if short["RunnerGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(short["RunnerGate"])
        if "planned_vtk_frame_count_5_below_minimum_40" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "planned_final_window_step_span_4000_below_minimum_20000" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "planned_stg_refresh_count_40_below_minimum_200" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])
        if "metadata_stg_refresh_count_390_does_not_match_computed_40" not in short["RunnerGate"]["Reasons"]:
            raise AssertionError(short["RunnerGate"])

        small_interval_manifest = temp / "small_interval" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(small_interval_manifest),
                "--baseline-id",
                "smoke-casea-native-small-save-interval",
                "--expected-aij-case",
                "CaseA",
                "--expected-wind-direction",
                "N",
                "--time-steps",
                "40000",
                "--vtk-save-interval",
                "100",
                "--expected-vtk-frame-count",
                "400",
            ],
            expected_returncode=2,
        )
        small_interval = load_json(small_interval_manifest)
        if small_interval["PlannedVtkScheduleGate"]["RecommendedAverageLastNForStepSpan"] != 201:
            raise AssertionError(small_interval["PlannedVtkScheduleGate"])
        if small_interval["SharedRunConditions"]["RecommendedMinimumTimeStepsForCurrentSaveInterval"] != 20100:
            raise AssertionError(small_interval["SharedRunConditions"])
        if small_interval["PlannedVtkScheduleGate"]["FinalWindowStepSpan"] != 3900:
            raise AssertionError(small_interval["PlannedVtkScheduleGate"])
        if "planned_final_window_step_span_3900_below_minimum_20000" not in small_interval["RunnerGate"]["Reasons"]:
            raise AssertionError(small_interval["RunnerGate"])

        incomplete_protocol_case = temp / "incomplete_protocol_case"
        create_case(incomplete_protocol_case)
        write(
            incomplete_protocol_case / "validation_protocol_audit.json",
            json.dumps(
                validation_protocol_audit(
                    {
                        "inlet_turbulence_k": "partial",
                        "boundary_conditions": "risk",
                    }
                ),
                indent=2,
            ),
        )
        incomplete_protocol_manifest = temp / "incomplete_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(incomplete_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(incomplete_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-incomplete-protocol",
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
            ],
            expected_returncode=2,
        )
        incomplete_protocol = load_json(incomplete_protocol_manifest)
        for reason in [
            "validation_protocol_prerun_item_partial:inlet_turbulence_k",
            "validation_protocol_prerun_item_risk:boundary_conditions",
        ]:
            if reason not in incomplete_protocol["RunnerGate"]["Reasons"]:
                raise AssertionError(incomplete_protocol["RunnerGate"])

        bad_gate_case = temp / "bad_gate_case"
        create_case(bad_gate_case)
        bad_gate_audit = validation_protocol_audit()
        bad_gate_audit["Gate"] = "not_paper_grade"
        write(bad_gate_case / "validation_protocol_audit.json", json.dumps(bad_gate_audit, indent=2))
        bad_gate_manifest = temp / "bad_gate" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(bad_gate_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(bad_gate_manifest),
                "--baseline-id",
                "smoke-casea-native-bad-protocol-gate",
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
            ],
            expected_returncode=2,
        )
        bad_gate = load_json(bad_gate_manifest)
        if "validation_protocol_prerun_gate_not_ready:not_paper_grade" not in bad_gate["RunnerGate"]["Reasons"]:
            raise AssertionError(bad_gate["RunnerGate"])

        diagnostic_metadata_case = temp / "diagnostic_metadata_case"
        create_case(diagnostic_metadata_case)
        diagnostic_metadata_path = diagnostic_metadata_case / "case_metadata.json"
        diagnostic_metadata = load_json(diagnostic_metadata_path)
        diagnostic_metadata.update(
            {
                "PaperGradeTurbulentInletPrerequisiteGate": "fail",
                "PaperGradeBoundaryPrerequisiteGate": "fail",
                "InletDistributionFunctionReconstruction": False,
                "SyntheticTurbulentInletDistributionTreatment": (
                    "velocity_field_only_no_distribution_function_reconstruction"
                ),
                "SyntheticTurbulentInletPaperGradeStatus": (
                    "diagnostic_only_until_distribution_reconstruction"
                ),
                "BoundaryConditionPaperGradeStatus": (
                    "diagnostic_only_until_boundary_source_and_aij_protocol_evidence_pass"
                ),
                "BoundaryNonReflectingOutletImplemented": False,
                "BoundarySideTopWindTunnelEquivalentImplemented": False,
                "BoundaryRoughWallFunctionImplemented": False,
                "BoundaryPrecursorOrRecyclingImplemented": False,
                "BoundaryBlockageFetchEvidenceArchived": False,
            }
        )
        write(diagnostic_metadata_path, json.dumps(diagnostic_metadata, indent=2))
        diagnostic_metadata_manifest = temp / "diagnostic_metadata" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(diagnostic_metadata_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(diagnostic_metadata_manifest),
                "--baseline-id",
                "smoke-casea-native-diagnostic-metadata",
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
            ],
            expected_returncode=2,
        )
        diagnostic_metadata_result = load_json(diagnostic_metadata_manifest)
        if diagnostic_metadata_result["ValidationProtocolAuditGate"]["Gate"] != "pass":
            raise AssertionError(diagnostic_metadata_result["ValidationProtocolAuditGate"])
        if diagnostic_metadata_result["CaseMetadataPreconditionGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(diagnostic_metadata_result["CaseMetadataPreconditionGate"])
        for reason in [
            "case_metadata_paper_grade_turbulent_inlet_prerequisite_not_pass:fail",
            "case_metadata_paper_grade_boundary_prerequisite_not_pass:fail",
            "case_metadata_synthetic_inlet_without_distribution_reconstruction",
            "case_metadata_inlet_distribution_treatment_velocity_field_only",
            "case_metadata_boundary_status_diagnostic_only",
            "case_metadata_boundary_evidence_false:rough_wall_function",
        ]:
            if reason not in diagnostic_metadata_result["RunnerGate"]["Reasons"]:
                raise AssertionError(diagnostic_metadata_result["RunnerGate"])

        blocked_execution_case = temp / "blocked_execution_case"
        create_case(blocked_execution_case)
        write(blocked_execution_case / "src" / "defines.hpp", "#define SX 32u\n#define SY 32u\n#define SZ 16u\n")
        write(source_root / "src" / "setup.cpp", "// native preflight protected setup\n")
        blocked_audit = validation_protocol_audit({"boundary_conditions": "risk"})
        write(blocked_execution_case / "validation_protocol_audit.json", json.dumps(blocked_audit, indent=2))
        blocked_execution_manifest = temp / "blocked_execution" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(blocked_execution_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(blocked_execution_manifest),
                "--baseline-id",
                "smoke-casea-native-blocked-execution",
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
                "--install",
                "--build",
                "--run",
            ],
            expected_returncode=2,
        )
        blocked_execution = load_json(blocked_execution_manifest)
        if blocked_execution["PreExecutionGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(blocked_execution["PreExecutionGate"])
        if blocked_execution["Install"]["Gate"] != "blocked":
            raise AssertionError(blocked_execution["Install"])
        if blocked_execution["Build"]["Gate"] != "blocked":
            raise AssertionError(blocked_execution["Build"])
        if blocked_execution["Run"]["Gate"] != "blocked":
            raise AssertionError(blocked_execution["Run"])
        if blocked_execution["ActualVtkOutputGate"]["Gate"] != "not_applicable":
            raise AssertionError(blocked_execution["ActualVtkOutputGate"])
        if blocked_execution["Install"]["Performed"] is not False:
            raise AssertionError(blocked_execution["Install"])
        if (source_root / "src" / "setup.cpp").read_text(encoding="utf-8") != "// native preflight protected setup\n":
            raise AssertionError("blocked preflight unexpectedly modified source setup.cpp")
        if "execution_requested_but_preflight_gate_diagnostic_only" not in blocked_execution["RunnerGate"]["Reasons"]:
            raise AssertionError(blocked_execution["RunnerGate"])
        if "run_requested_but_executable_missing" in blocked_execution["RunnerGate"]["Reasons"]:
            raise AssertionError(blocked_execution["RunnerGate"])
        if "actual_vtk_output_missing" in blocked_execution["RunnerGate"]["Reasons"]:
            raise AssertionError(blocked_execution["RunnerGate"])

        stale_exe_after_build_failure_source = temp / "FluidX3D_stale_exe_after_build_failure"
        stale_exe_after_build_failure_case = temp / "stale_exe_after_build_failure_case"
        create_source(stale_exe_after_build_failure_source)
        create_case(stale_exe_after_build_failure_case)
        write(stale_exe_after_build_failure_case / "src" / "defines.hpp", "#define SX 32u\n#define SY 32u\n#define SZ 16u\n")
        stale_exe = stale_exe_after_build_failure_source / "bin" / "FluidX3D.exe"
        write(stale_exe, "this stale executable must not run\n")
        stale_exe_manifest = temp / "stale_exe_after_build_failure" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(stale_exe_after_build_failure_case),
                "--fluidx3d-source",
                str(stale_exe_after_build_failure_source),
                "--out",
                str(stale_exe_manifest),
                "--baseline-id",
                "smoke-casea-native-stale-exe-build-failure",
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
                "--msbuild",
                sys.executable,
                "--platform-toolset",
                "v143",
                "--install",
                "--build",
                "--run",
                "--allow-diagnostic-execution",
            ],
            expected_returncode=2,
        )
        stale_exe_result = load_json(stale_exe_manifest)
        if stale_exe_result["Build"]["Gate"] != "fail":
            raise AssertionError(stale_exe_result["Build"])
        if stale_exe_result["Run"]["Gate"] != "blocked":
            raise AssertionError(stale_exe_result["Run"])
        if "run_blocked_because_build_failed" not in stale_exe_result["RunnerGate"]["Reasons"]:
            raise AssertionError(stale_exe_result["RunnerGate"])
        if stale_exe_result["Run"]["ReturnCode"] is not None:
            raise AssertionError(stale_exe_result["Run"])

        slow_refresh_case = temp / "slow_refresh_case"
        create_case(slow_refresh_case)
        slow_metadata_path = slow_refresh_case / "case_metadata.json"
        slow_metadata = load_json(slow_metadata_path)
        slow_metadata["SyntheticTurbulenceUpdateInterval"] = 500
        slow_metadata["SyntheticTurbulenceExpectedFinalWindowRefreshCount"] = 78
        write(slow_metadata_path, json.dumps(slow_metadata, indent=2))
        slow_refresh_manifest = temp / "slow_refresh" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(slow_refresh_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(slow_refresh_manifest),
                "--baseline-id",
                "smoke-casea-native-slow-stg-refresh",
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
            ],
            expected_returncode=2,
        )
        slow_refresh = load_json(slow_refresh_manifest)
        if slow_refresh["PlannedVtkScheduleGate"]["Gate"] != "pass":
            raise AssertionError(slow_refresh["PlannedVtkScheduleGate"])
        if slow_refresh["PlannedSyntheticInletSamplingGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(slow_refresh["PlannedSyntheticInletSamplingGate"])
        if "planned_stg_refresh_count_78_below_minimum_200" not in slow_refresh["RunnerGate"]["Reasons"]:
            raise AssertionError(slow_refresh["RunnerGate"])

        partial_output = temp / "partial_output"
        write(partial_output / "u-000001000.vtk", "# vtk DataFile Version 3.0\nsmoke\n")
        partial_output_manifest = temp / "partial_output_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(partial_output_manifest),
                "--baseline-id",
                "smoke-casea-native-partial-output",
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
                "--output-dir",
                str(partial_output),
            ],
            expected_returncode=2,
        )
        partial_output_result = load_json(partial_output_manifest)
        if partial_output_result["ActualVtkOutputGate"]["Gate"] != "diagnostic_only":
            raise AssertionError(partial_output_result["ActualVtkOutputGate"])
        partial_accuracy_gate = partial_output_result["NativeAccuracyEvidenceGate"]
        if partial_accuracy_gate["Gate"] != "fail":
            raise AssertionError(partial_accuracy_gate)
        if "native_run_not_requested" not in partial_accuracy_gate["Reasons"]:
            raise AssertionError(partial_accuracy_gate)
        if "actual_vtk_output_gate_not_pass:diagnostic_only" not in partial_accuracy_gate["Reasons"]:
            raise AssertionError(partial_accuracy_gate)
        if "actual_vtk_frame_count_1_below_minimum_40" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])
        if "actual_vtk_frame_count_1_does_not_match_expected_40" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])
        if "actual_vtk_final_window_frame_count_1_below_minimum_40" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])
        if "actual_vtk_final_window_step_span_0_below_minimum_20000" not in partial_output_result["RunnerGate"]["Reasons"]:
            raise AssertionError(partial_output_result["RunnerGate"])
        if partial_output_result["ActualVtkOutputGate"]["ActualSourceTimeSteps"] != [1000]:
            raise AssertionError(partial_output_result["ActualVtkOutputGate"])
        partial_actual = partial_output_result["ActualVtkOutputGate"]
        partial_hash = sha256_file(partial_output / "u-000001000.vtk")
        if partial_actual["SelectedFinalWindowVtkSha256"] != [partial_hash]:
            raise AssertionError(partial_actual)
        if partial_actual["SelectedFinalWindowStepHashPairs"][0]["StepHash"] != f"1000:{partial_hash}":
            raise AssertionError(partial_actual)
        if partial_actual["SelectedFinalWindowVtkSha256Count"] != 1:
            raise AssertionError(partial_actual)

        short_window_output = temp / "short_window_output"
        for step in range(1000, 5000, 100):
            write(short_window_output / f"u-{step:09d}.vtk", f"# vtk DataFile Version 3.0\nsmoke {step}\n")
        short_window_output_manifest = temp / "short_window_output_manifest" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(case_dir),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(short_window_output_manifest),
                "--baseline-id",
                "smoke-casea-native-short-window-output",
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
                "--output-dir",
                str(short_window_output),
            ],
            expected_returncode=2,
        )
        short_window_output_result = load_json(short_window_output_manifest)
        actual_gate = short_window_output_result["ActualVtkOutputGate"]
        if actual_gate["ActualFrameCount"] != 40:
            raise AssertionError(actual_gate)
        if actual_gate["SelectedFinalWindowStepSpan"] != 3900:
            raise AssertionError(actual_gate)
        if actual_gate["SourceVtkSha256Count"] != 40:
            raise AssertionError(actual_gate)
        if actual_gate["SelectedFinalWindowVtkSha256Count"] != 40:
            raise AssertionError(actual_gate)
        if len(actual_gate["SelectedFinalWindowStepHashPairs"]) != 40:
            raise AssertionError(actual_gate)
        first_selected_hash = sha256_file(short_window_output / "u-000001000.vtk")
        last_selected_hash = sha256_file(short_window_output / "u-000004900.vtk")
        if actual_gate["SelectedFinalWindowStepHashPairs"][0]["StepHash"] != f"1000:{first_selected_hash}":
            raise AssertionError(actual_gate)
        if actual_gate["SelectedFinalWindowStepHashPairs"][-1]["StepHash"] != f"4900:{last_selected_hash}":
            raise AssertionError(actual_gate)
        if actual_gate["SelectedFinalWindowVtkSha256"][0] != first_selected_hash:
            raise AssertionError(actual_gate)
        if actual_gate["SelectedFinalWindowVtkSha256"][-1] != last_selected_hash:
            raise AssertionError(actual_gate)
        for reason in [
            "actual_vtk_final_window_step_span_3900_below_minimum_20000",
            "actual_vtk_source_time_steps_do_not_match_planned_schedule",
            "actual_vtk_final_window_steps_do_not_match_planned_final_window",
        ]:
            if reason not in short_window_output_result["RunnerGate"]["Reasons"]:
                raise AssertionError(short_window_output_result["RunnerGate"])

        missing_protocol_case = temp / "missing_protocol_case"
        create_case(missing_protocol_case)
        (missing_protocol_case / "validation_protocol_audit.json").unlink()
        missing_protocol_manifest = temp / "missing_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(missing_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(missing_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-missing-protocol",
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
            ],
            expected_returncode=2,
        )
        missing_protocol = load_json(missing_protocol_manifest)
        if "case_required_file_missing:Validation protocol audit" not in missing_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(missing_protocol["RunnerGate"])

        sidecar_protocol_case = temp / "sidecar_protocol_case"
        create_case(sidecar_protocol_case)
        (sidecar_protocol_case / "validation_protocol_audit.json").unlink()
        sidecar_protocol = temp / "sidecar_audits" / "validation_protocol_audit.json"
        write(sidecar_protocol, json.dumps(validation_protocol_audit(), indent=2))
        sidecar_protocol_manifest = temp / "sidecar_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(sidecar_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(sidecar_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-sidecar-protocol",
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
                "--validation-protocol-audit",
                str(sidecar_protocol),
            ]
        )
        sidecar_protocol_result = load_json(sidecar_protocol_manifest)
        if sidecar_protocol_result["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(sidecar_protocol_result["RunnerGate"])
        if sidecar_protocol_result["ValidationProtocolAuditPath"] != str(sidecar_protocol.resolve()):
            raise AssertionError(sidecar_protocol_result["ValidationProtocolAuditPath"])
        if sidecar_protocol_result["ValidationProtocolAuditSha256"] != sha256_file(sidecar_protocol):
            raise AssertionError(sidecar_protocol_result["ValidationProtocolAuditSha256"])
        sidecar_records = {
            record["Role"]: record for record in sidecar_protocol_result["RequiredSourceFiles"]
        }
        protocol_record = sidecar_records["Validation protocol audit"]
        if protocol_record["Path"] != str(sidecar_protocol.resolve()):
            raise AssertionError(protocol_record)
        if protocol_record["Exists"] is not True:
            raise AssertionError(protocol_record)

        sidecar_identity_case = temp / "sidecar_identity_case"
        create_case(sidecar_identity_case)
        (sidecar_identity_case / "validation_protocol_audit.json").unlink()
        sidecar_identity_metadata_path = sidecar_identity_case / "case_metadata.json"
        sidecar_identity_metadata = load_json(sidecar_identity_metadata_path)
        sidecar_identity_metadata.pop("AijCase", None)
        sidecar_identity_metadata.pop("WindDirection", None)
        write(sidecar_identity_metadata_path, json.dumps(sidecar_identity_metadata, indent=2))
        sidecar_identity_audit = temp / "sidecar_identity_audits" / "validation_protocol_audit.json"
        write(sidecar_identity_audit, json.dumps(validation_protocol_audit(), indent=2))
        sidecar_identity_manifest = temp / "sidecar_identity" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(sidecar_identity_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(sidecar_identity_manifest),
                "--baseline-id",
                "smoke-casea-native-sidecar-identity",
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
                "--validation-protocol-audit",
                str(sidecar_identity_audit),
            ]
        )
        sidecar_identity_result = load_json(sidecar_identity_manifest)
        if sidecar_identity_result["RunnerGate"]["Gate"] != "pass":
            raise AssertionError(sidecar_identity_result["RunnerGate"])
        if sidecar_identity_result["EffectiveAijCase"] != "CaseA":
            raise AssertionError(sidecar_identity_result)
        if sidecar_identity_result["EffectiveAijCaseSource"] != "validation_protocol_audit":
            raise AssertionError(sidecar_identity_result)
        if sidecar_identity_result["EffectiveWindDirection"] != "N":
            raise AssertionError(sidecar_identity_result)
        if sidecar_identity_result["EffectiveWindDirectionSource"] != "validation_protocol_audit":
            raise AssertionError(sidecar_identity_result)

        empty_protocol_case = temp / "empty_protocol_case"
        create_case(empty_protocol_case)
        write(empty_protocol_case / "validation_protocol_audit.json", json.dumps({"items": []}, indent=2))
        empty_protocol_manifest = temp / "empty_protocol" / "native_fluidx3d_baseline_manifest.json"
        run_cmd(
            [
                sys.executable,
                str(RUNNER),
                "--case-dir",
                str(empty_protocol_case),
                "--fluidx3d-source",
                str(source_root),
                "--out",
                str(empty_protocol_manifest),
                "--baseline-id",
                "smoke-casea-native-empty-protocol",
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
            ],
            expected_returncode=2,
        )
        empty_protocol = load_json(empty_protocol_manifest)
        if "validation_protocol_audit_missing_or_empty" not in empty_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(empty_protocol["RunnerGate"])
        if "validation_protocol_item_missing:inlet_distribution_consistency" not in empty_protocol["RunnerGate"]["Reasons"]:
            raise AssertionError(empty_protocol["RunnerGate"])

    print("native_fluidx3d_runner_smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
