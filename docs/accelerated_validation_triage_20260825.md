# CityLBM 加速验证诊断记录 2026-08-25

## 当前结论

本轮优化目标是缩短 CityLBM/FluidX3D 验证开发时间，优先避免长时间 CFD 运行后才发现入口、采样或旧链路问题。

当前 `v0.2.1` 源码可编译，Release 构建通过：

- 命令：`dotnet build -c Release`
- 结果：0 warnings, 0 errors
- 输出：`bin\Release\CityLBM.dll`
- SHA256：`FFE91DF0638DB1B2C3935EE65EA209A7F1659033A39DC98EE6A06EEB1EF1A823`

当前代码生成 smoke 通过：

- 命令：`dotnet run -c Release --project .\tests\CodegenSmoke\CodegenSmoke.csproj`
- 结果：`Codegen smoke passed.`
- 生成目录：`C:\Users\MSY\AppData\Local\Temp\CityLBM\stg_codegen_smoke`

新版生成的 `setup.cpp` 已包含以下关键入口机制：

- `applySyntheticTurbulentInlet`
- `citylbm_stg_layer_rms_scale_x/y/z`
- `writeSyntheticTurbulentInletDiagnostics`
- `RECONSTRUCT_INLET_STRESS_DDF`

因此，后续精度验证应优先使用新版 CityLBM 生成的 native case，而不是继续使用旧 legacy/diagnostic setup 作为精度依据。

## 已修复的快迭代问题

`scripts\audit_inlet_diagnostics_csv.py` 已改为同时报告两套入口误差：

- 按 AF 表格原始高度 `z_m` 比较的误差
- 按实际网格采样高度 `effective_sample_z_m` 比较的误差

门控现在优先使用 `effective_sample_z_m` 的 U/k/RMS 误差，避免把网格层采样偏移误判成入口物理模型错误。

新增字段包括：

- `profile_z_m`
- `effective_sample_z_m`
- `sample_z_offset_m`
- `target_U_effective_mps`
- `mean_U_rel_error_effective`
- `target_k_effective_m2s2`
- `k_rel_error_effective`
- `target_*_rms_effective_mps`
- `*_rms_rel_error_effective`

`scripts\audit_inlet_source.py` 现在额外输出入口生成路线：

- `setup_inlet_codegen_route`
- `has_current_citylbm_stg_codegen_route`
- `has_legacy_runtime_diagnostic_patch_route`
- `short_canary_allowed_by_codegen_route`

`scripts\run_native_preflight_pack.py` 已把 `short_canary_allowed_by_codegen_route` 接入 `DiagnosticCanaryGate`。如果 case 仍是旧 `legacy_runtime_diagnostic_patch_route`，preflight 会给出：

`setup_codegen_route_not_current_citylbm:legacy_runtime_diagnostic_patch_route`

这会阻止继续启动短 CFD canary，要求先用当前 Release 插件重新生成 native case。

`scripts\run_codegen_preflight_canary.py` 也已接入 `check_short_canary_route.py`。执行顺序变为：

1. 可选 `dotnet build`
2. 可选 `CodegenSmoke`
3. `check_short_canary_route`
4. 只有 route gate 通过后才运行完整 `run_native_preflight_pack`

这样在 `--quick / --skip-codegen` 复用旧 temp case 时，可以先以约 `0.5 s` 拦截 legacy case，避免直接进入分钟级完整 preflight。

## 新增秒级 canary 路线门禁

为进一步缩短开发循环，新增：

`scripts\check_short_canary_route.py`

用途：

- 不打开 Rhino
- 不复制 FluidX3D 源码
- 不启动 CFD
- 只复用 `audit_inlet_source.py` 审计 `setup.cpp / defines.hpp / case_metadata.json`
- 秒级判断该 case 是否来自当前 CityLBM codegen 路线，是否允许进入短 diagnostic canary

推荐放在每次 Case A/E 重跑前执行：

```powershell
python .\scripts\check_short_canary_route.py --case-dir "<generated_case_dir>"
```

当前新版 codegen smoke 结果：

- case：`C:\Users\MSY\AppData\Local\Temp\CityLBM\stg_codegen_smoke`
- route：`current_citylbm_stg_layerwise_type_e_route`
- gate：`pass`
- elapsed：约 `0.50 s`

旧 Case E diagnostic setup 结果：

- route：`legacy_runtime_diagnostic_patch_route`
- gate：`fail`
- reason：`setup_codegen_route_not_current_citylbm:legacy_runtime_diagnostic_patch_route`
- elapsed：约 `0.53 s`

这一步把“是否值得进入短 canary”的判断从完整 preflight 的分钟级准备，压缩到秒级。通过后仍然只能启动短 canary；不能把该门禁本身作为论文精度证据。

## 新增生成链路一致性修复

`tests\CodegenSmoke\Program.cs` 的 full Reynolds-stress tensor 开发 case 现在与普通生成链路一致，额外写出：

- `buildings.stl`
- `domain_origin.json`
- `native_fluidx3d_baseline_manifest.json`

同时 `tests\CodegenSmoke\CodegenSmoke.csproj` 改为 `ProjectReference` 主项目，避免 smoke test 使用过期的 `tests\CodegenSmoke\bin\Release\net48\CityLBM.dll`。

`src\Core\FluidX3DInterface.cs` 现在在 metadata/native manifest 中写入可审计的 AIJ 身份字段：

- `AijCase`
- `CaseName`

该字段只从明确的场景名 token 推断，例如 `CaseA / AIJ_CaseA / CaseE / AIJ_CaseE`，无法推断时保留空值。

`scripts\run_native_fluidx3d_case.py` 的 `parse_vector()` 已支持 metadata 中的 `{X,Y,Z}` 对象格式，避免把 CityLBM 输出的 `WindDirectionUnitVector` 误判为缺失。

复测结果：

- full-tensor CaseE smoke metadata：`AijCase=CaseE`，`WindDirection=N`，`WindDirectionUnitVector=(0,-1,0)`
- native runner dry check 不再包含：
  - `case_required_file_missing:Domain origin`
  - `wind_vector_missing_in_metadata_and_protocol`
  - `case_label_missing_in_metadata`
- `run_codegen_preflight_canary.py --quick` 的 manifest 已记录：
  - `ShortCanaryRouteCheckGate=pass`
  - `Steps=check_short_canary_route, run_native_preflight_pack`

剩余阻塞主要来自 smoke case 本身只有 `1000` 步和 `10` 个 planned VTK frame，因此仍出现：

- `planned_vtk_frame_count_10_below_minimum_40`
- `planned_final_window_step_span_900_below_minimum_20000`
- `planned_stg_refresh_count_36_below_minimum_200`

这些是预期的论文级前置阻塞，不应通过降低门槛消除；正式 Case A/E 需要使用 `time_steps >= 40000`、`save_interval <= 1000`、最终平均窗口至少 `40` 帧且跨越至少 `20000` 步。

## 新增官方输入自动发现

`scripts\run_validation_dev_loop.py` 现在为 Case A/E 内置官方 AF/RS 候选路径。若命令行没有显式传入 `--official` 或 `--af-csv`，脚本会自动查找可用官方数据，并在找到任一官方输入后自动启用 `--strict-official-inputs`。

当前 Case E no-CFD 快速链路：

```powershell
python .\scripts\run_validation_dev_loop.py --case casee --fluidx3d-source "C:\Users\MSY\AppData\Local\Temp\CityLBM\fake_fluidx3d_source_full_reynolds_tensor" --quick --out-dir "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_official_auto_20260825" --allow-diagnostic
```

自动绑定结果：

- `OfficialSource = auto_candidate`
- `OfficialPath = releases\v0.2.0\package\examples\AIJ_CaseE\official_data\RS_caseE.csv`
- `AfCsvSource = auto_candidate`
- `AfCsvPath = releases\v0.2.0\package\examples\AIJ_CaseE\official_data\AF_caseE.csv`
- 严格门禁已传入：`ac + N`、`80` 个测点、`z = 2.0 m`、`Uref = 3.928296 @ 15.9 m`、`--require-af-k`

该链路仍为 `diagnostic_only`，但原因已经从“官方输入可能缺失”收敛为真实物理/协议阻塞：

- `source_missing_turbulent_length_scale_evidence`
- `isotropic_k_assumption_only_not_paper_grade_reynolds_stress`
- `boundary_source_not_wind_tunnel_equivalent`
- `boundary_protocol` 仍缺 AIJ 等价边界证据

新增输出：

- `validation_runs\casee_dev_loop_official_auto_20260825\validation_dev_loop_manifest.json`
- `validation_runs\casee_dev_loop_official_auto_20260825\codegen_preflight_canary_manifest.json`
- `validation_runs\casee_dev_loop_official_auto_20260825\native_preflight_pack_manifest.json`
- `validation_acceleration_plan_fasttrack_20260825_official_auto_gate.json`
- `validation_acceleration_plan_fasttrack_20260825_official_auto_gate.md`

规划器给出的最快下一步为：

1. 先创建或绑定 `turbulence_length_scale` 证据。
2. 每次短 canary 后自动运行 `audit_inlet_diagnostics_csv.py`，不通过则不进入长算例。
3. 补齐 AIJ 等价边界/墙面协议证据。
4. 坚持 native FluidX3D 先通过同一套输入、平均和测点门禁，再迁移到 CityLBM。

## 新增长度尺度与时间窗口透传

发现的链路断点：

- `run_native_preflight_pack.py` 已支持 `--length-scale-source`、`--length-scale-source-type`、`--length-scale-source-note` 和 `--length-scale-paper-admissible`。
- 但上游 `run_codegen_preflight_canary.py` 和 `run_validation_dev_loop.py` 未接收或透传这些参数。
- 结果是即使准备了官方/precursor/校准长度尺度证据，一键快速链路仍会在 native preflight 中表现为 `length_scale_source_file_missing`。

已修复：

- `scripts\run_codegen_preflight_canary.py` 现在接收并传给 `run_native_preflight_pack.py`：
  - `--length-scale-source`
  - `--length-scale-source-type`
  - `--length-scale-source-note`
  - `--length-scale-paper-admissible`
- `scripts\run_validation_dev_loop.py` 现在接收并传给 `run_codegen_preflight_canary.py`：
  - 上述长度尺度证据参数
  - `--time-steps`
  - `--vtk-save-interval`
  - `--vtk-save-start-step`
  - `--expected-vtk-frame-count`
  - `--average-last-n`
  - `--min-vtk-frames`
  - `--min-vtk-step-span`

Case E 快速验证命令：

```powershell
python .\scripts\run_validation_dev_loop.py --case casee --fluidx3d-source "C:\Users\MSY\AppData\Local\Temp\CityLBM\fake_fluidx3d_source_full_reynolds_tensor" --quick --out-dir "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_time_passthrough_20260825" --time-steps 60000 --vtk-save-interval 500 --vtk-save-start-step 10000 --expected-vtk-frame-count 101 --average-last-n 80 --min-vtk-frames 60 --min-vtk-step-span 30000 --allow-diagnostic
```

验证结果：

- dev-loop manifest 已记录：
  - `TimeSteps = 60000`

## 2026-08-26 快速优化链路固化

为缩短每次底层修改后的反馈时间，新增：

`scripts\run_casee_fast_dev_loop.ps1`

用途：

- 默认以 Rhino/CityLBM 生成链路后的 Case E `stg_full_reynolds_stress_tensor` 为对象。
- 默认调用当前 workspace 的 `citylbm_v0.2.0_portable\validation\parallel_experiments\FluidX3D-master`。
- 默认把短 canary 和 VTK 输出写入 `C:\Users\MSY\AppData\Local\Temp`，避免当前 `F:` 盘 0 bytes 剩余空间阻塞开发。
- 执行顺序为：`CodegenSmoke` -> `run_validation_dev_loop.py --case casee --quick --execute-canary` -> post-canary 入口诊断和 VTK 相关性审计。

推荐开发命令：

```powershell
powershell.exe -ExecutionPolicy Bypass -File "F:\Grade2master2\CITYLBM开发文件\v0.2.1\scripts\run_casee_fast_dev_loop.ps1"
```

若刚刚已经运行过 `CodegenSmoke`，可临时加 `-SkipCodegenSmoke`，但该选项只用于开发提速，不能作为 fresh codegen 证据。

本轮真实快速链路输出：

- dev-loop manifest：`C:\Users\MSY\AppData\Local\Temp\citylbm_casee_fast_dev_loop_post_target_20260826\validation_dev_loop_manifest.json`
- VTK 输出目录：`C:\Users\MSY\AppData\Local\Temp\citylbm_casee_fast_dev_loop_post_target_20260826\diagnostic_solver_cwd\output`
- VTK 帧数：20 帧，`u-000000025.vtk` 到 `u-000000500.vtk`
- `validation_dev_loop_gate = pass`
- `diagnostic_canary_ready = true`
- post-canary 入口诊断：pass
- post-canary VTK 入口相关性：pass

关键入口审计值：

- `inlet_streamwise_variance_to_k_ratio = 1.0085512364648228`
- `inlet_tke_to_k_ratio = 1.1408474926505336`
- `temporal_lag1_mean_correlation = 0.8889398182281337`
- `inlet_correlation_gate = pass`

注意：这仍是 500 步 diagnostic canary，只能证明当前入口扰动和 VTK 输出不再是“完全无相关随机噪声/旧结果复用”。它不能证明 Case E 精度已经达到论文可靠程度。

## 2026-08-26 下一步优化目标字段

为避免每次人工翻阅多个 JSON，`run_native_preflight_pack.py` 现在在 manifest 顶层写入：

- `NextOptimizationTarget`
- `DevelopmentTriage.NextOptimizationTarget`

`run_validation_dev_loop.py` 也会在最终 dev-loop manifest 写入：

- `NextOptimizationTarget`
- `NextOptimizationTarget.ShortRuntimeCanaryEvidenceGate`
- `NextOptimizationTarget.ShortRuntimeCanaryInterpretation`

本轮 Case E 快速链路的自动判断为：

- `Key = turbulent_inlet_method_and_u_k_preservation`
- `ShortRuntimeCanaryEvidenceGate.Gate = pass`
- `AccuracyInterpretationAllowed = false`
- `RequiredExperiment = paper_length_empty_tunnel_inlet_preservation_with_bound_inlet_evidence`

解释：

- 入口短 canary 已证明 U/k/TKE/correlation 在短窗口内可以保存。
- 论文级 blocker 仍然是入口来源证据：湍流长度尺度、完整 Reynolds stress 或 precursor/recycling/digital-filter/SEM 等价证据尚未闭合。
- 因此下一步不应直接调 Case E 测点误差，而应先做 paper-length empty-tunnel inlet preservation，并绑定可发表的入口湍流证据。

本轮回归验证：

- `tests\native_preflight_pack_smoke.py`：pass
- `tests\validation_dev_loop_smoke.py`：pass
- `scripts\run_casee_fast_dev_loop.ps1 -SkipCodegenSmoke`：pass，真实生成短 canary VTK
  - `VtkSaveInterval = 500`
  - `VtkSaveStartStep = 10000`
  - `ExpectedVtkFrameCount = 101`
  - `AverageLastN = 80`
  - `MinimumVtkFrames = 60`
  - `MinimumStepSpan = 30000`
- native preflight manifest 中 `TimeAveragingPlan.Sources` 均为 `cli`，说明长时间平均计划没有在上游丢失。
- 因本次没有提供真实长度尺度源，`LengthScaleEvidencePlan.Source` 仍为空，不能消除长度尺度 paper-grade 阻塞。

新增输出：

- `validation_runs\casee_dev_loop_time_passthrough_20260825\validation_dev_loop_manifest.json`
- `validation_runs\casee_dev_loop_time_passthrough_20260825\native_preflight_pack_manifest.json`
- `validation_acceleration_plan_fasttrack_20260825_time_passthrough.json`
- `validation_acceleration_plan_fasttrack_20260825_time_passthrough.md`

这一步的作用是缩短后续开发时间：之后只需在最外层 dev-loop 命令补入真实长度尺度证据文件，即可一次性传到 native preflight，无需分别修改中间脚本或手工编辑 metadata。

## Case E canary 结果解释

已复审的短 canary 路径：

`C:\Users\MSY\AppData\Local\Temp\CityLBM_validation_runs\ddf_setup_patch_20260825_092526\casee_ddf_setup\preflight\after_vtk_canary_injection_v4`

新的入口诊断结果：

- 原始高度最大 `mean_U` 相对误差：约 `15.94%`
- 按有效采样高度最大 `mean_U` 相对误差：约 `2.91%`
- 按有效采样高度最大 `k` 相对误差：约 `172.68%`
- 按有效采样高度最大 RMS 相对误差：约 `91.41%`
- 最大采样高度偏移：`11.5 m`

解释：

- `mean_U` 主要是采样高度口径问题，修正审计口径后已不再是首要阻塞。
- `k/RMS` 仍是入口湍流阻塞，不能作为论文级验证通过。
- 该 canary 的 `setup.cpp` 属于旧 legacy/diagnostic 链路，入口函数是 `turbulentWind()` 直接刷新入口，未使用新版 C# 生成的逐层 RMS rescale 逻辑。
- 因此，该 canary 只能证明 native build/run/VTK 输出链路可用，不能代表新版 CityLBM 的最终模拟精度。
- 新 route 审计已确认该旧 setup 为 `legacy_runtime_diagnostic_patch_route`，`short_canary_allowed_by_codegen_route = false`。
- 新版 codegen smoke 生成的 setup 为 `current_citylbm_stg_layerwise_type_e_route`，`short_canary_allowed_by_codegen_route = true`。

## 最快下一步

1. 用当前 Release 插件重新生成 Case A native case，必须确认生成的 `setup.cpp` 含有 `applySyntheticTurbulentInlet` 和 `citylbm_stg_layer_rms_scale_x/y/z`。
2. 先运行短 canary：
   - `dx = 3 m`
   - `time_steps = 2000`
   - `save_interval = 500`
   - 启用 runtime inlet diagnostics
3. 入口诊断必须先满足：
   - `MaxMeanURelErrorEffectiveSampleZ <= 0.10`
   - `MaxKRelErrorEffectiveSampleZ <= 0.35`
   - `MaxRmsRelErrorEffectiveSampleZ <= 0.35`
4. 只有入口 canary 通过后，再启动长步数 Case A。
5. Case A 达到合理误差后，再按同一套设置进入 Case E SCI 级验证。

## 已通过的窄测试

- `python .\tests\inlet_diagnostics_csv_smoke.py`
- `python .\tests\native_runner_inlet_diagnostics_csv_gate_smoke.py`
- `python .\tests\patch_legacy_runtime_inlet_diagnostics_smoke.py`
- `python .\tests\native_preflight_pack_smoke.py`
- `python .\tests\inlet_source_generated_codegen_audit_smoke.py`
- `python .\tests\inlet_source_legacy_digital_filter_audit_smoke.py`
- `python .\tests\short_canary_route_check_smoke.py`
- `python .\tests\native_fluidx3d_runner_smoke.py`
- `dotnet build -c Release`
- `dotnet run -c Release --project .\tests\CodegenSmoke\CodegenSmoke.csproj`

## 本轮加速改动：自动诊断 DDF 副本路线

目的：缩短“改 CityLBM -> 生成 setup.cpp -> 审计 -> 判断能否短跑”的周期，避免在原生 FluidX3D/CityLBM 边界 DDF 路线未闭合时启动长时 CFD。

已实现：

- `run_native_preflight_pack.py` 现在会自动创建诊断 FluidX3D 源码副本，并在副本上执行：
  - `patch_fluidx3d_equilibrium_boundary_source.py`
  - `enable_fluidx3d_ddf_reconstruction_route.py`
  - `audit_fluidx3d_equilibrium_boundary.py`
- `DiagnosticCanaryGate` 对短 canary 使用诊断副本的 `DiagnosticDdfReconstructionRoute`，但论文级 `Gate` 仍保留原始 FluidX3D 源码、边界协议、入口湍流和时间平均的严格限制。
- `prepare_native_diagnostic_solver_source.py` 对没有 `.vcxproj` 的 Makefile/最小源树不再误判失败。
- `prepare_native_diagnostic_canary_case.py` 现在同时支持旧式 `lbm.run(N)` 和当前 CityLBM 生成的 `while(lbm.get_t() < N)` 分段循环调度。
- CodegenSmoke 的 fake FluidX3D 源树已补齐最小 `TYPE_E / DDF reconstruction` 审计证据，用于秒级本地门禁，不作为真实 CFD 精度证据。

本轮新验证命令：

```powershell
dotnet run -c Release --project .\tests\CodegenSmoke\CodegenSmoke.csproj
python .\tests\native_preflight_pack_smoke.py
python .\tests\codegen_preflight_canary_smoke.py
python .\tests\validation_dev_loop_smoke.py
python .\tests\plan_validation_acceleration_smoke.py
dotnet build -c Release
```

Case E no-CFD 加速链复核：

```powershell
python .\scripts\run_validation_dev_loop.py --case casee --fluidx3d-source "C:\Users\MSY\AppData\Local\Temp\CityLBM\fake_fluidx3d_source_full_reynolds_tensor" --quick --out-dir "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_accelerated_ddf3_20260825" --time-steps 60000 --vtk-save-interval 500 --vtk-save-start-step 10000 --expected-vtk-frame-count 101 --average-last-n 80 --min-vtk-frames 60 --min-vtk-step-span 30000 --allow-diagnostic
```

结果：

- `validation_dev_loop_gate = pass`
- `diagnostic_canary_ready = true`
- 下一步可以在同一命令后追加 `--execute-canary` 启动短原生 FluidX3D 诊断运行。

注意：这一步只缩短开发排错时间，不等价于论文级精度通过。论文级 Case A/E 仍必须补齐真实 FluidX3D 源码哈希、入口长度尺度/雷诺应力证据、运行时入口相关性审计、长时间平均和 AIJ 边界协议证据。

## 本轮加速改动：短跑后入口相关性审计命令

目的：把“真实短 canary 跑完后该审计什么”固定到 manifest，减少人工拼命令和漏检。入口 `U/k/RMS` 只证明幅值大致对齐，论文级湍流入流还必须检查 VTK 帧中的时间相关、空间相关、`k` 方差比和 TKE 比。

已实现：

- `run_native_preflight_pack.py` 新增 `InletCorrelationAudit` 输出路径。
- 当 `DiagnosticCanaryGate = pass` 时，`DevelopmentTriage.SuggestedCommands` 会同时给出：
  - `run_native_diagnostic_canary`
  - `audit_runtime_inlet_diagnostics_after_canary`
  - `audit_inlet_correlation_after_canary`
- `audit_inlet_correlation_after_canary` 自动使用短跑输出目录 `output\u-*.vtk`、诊断 case 的 `case_metadata.json`、AIJ `AF_caseE.csv`，并强制 `--require-k-variance-check`。

本轮新验证命令：

```powershell
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\inlet_correlation_integral_scale_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\native_preflight_pack_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\validation_dev_loop_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\native_runner_inlet_correlation_audit_gate_smoke.py
```

Case E no-CFD 加速链复核：

```powershell
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\scripts\run_validation_dev_loop.py --case casee --fluidx3d-source "C:\Users\MSY\AppData\Local\Temp\CityLBM\fake_fluidx3d_source_full_reynolds_tensor" --quick --out-dir "F:\Grade2master2\CITYLBM开发文件\v0.2.1\validation_runs\casee_dev_loop_accelerated_correlation_20260826" --time-steps 60000 --vtk-save-interval 500 --vtk-save-start-step 10000 --expected-vtk-frame-count 101 --average-last-n 80 --min-vtk-frames 60 --min-vtk-step-span 30000 --allow-diagnostic
```

结果：

- `validation_dev_loop_gate = pass`
- `diagnostic_canary_ready = true`
- `native_preflight_pack_manifest.json` 已生成 `audit_inlet_correlation_after_canary` 建议命令。

注意：当前仍是 no-CFD 快速链复核，真实精度还不能声称已改善。下一步必须追加 `--execute-canary` 对短原生 FluidX3D 运行生成的真实 VTK 做入口相关性审计；只有该审计与 runtime inlet diagnostics 同时通过后，才进入长步数 Case A/Case E 精度验证。

## 2026-08-26 加速改动：Case E paper-length empty-tunnel 前置链

目的：把最耗时的论文级验证拆成可快速失败的前置链。先从 CityLBM 生成的 Case E `setup.cpp/defines.hpp/buildings.stl` 派生 empty-tunnel 入口保持实验，确认 AF 表格、`k(m2/s2)`、风向、步数、VTK 平均窗口和原生 FluidX3D 命令全部一致，再决定是否启动长时 CFD。

已实现：

- `FluidX3DInterface.cs` 新生成的 `setup.cpp` 会在建筑体素化前写入 `const bool empty_tunnel = false`，并用 `if(!empty_tunnel)` 包住 `lbm.voxelize_stl(...)`。
- `prepare_native_empty_tunnel_case.py` 对旧的 CityLBM 已生成 case 也可自动插入 `empty_tunnel=true`，并只跳过建筑 STL 体素化，不改入口、边界、步数和 AF/k 相关设置。
- 新增 `run_casee_empty_tunnel_paper_preflight.ps1`，一条命令完成：
  - 读取最新 CityLBM Case E 生成目录；
  - 生成 empty-tunnel 入口保持实验包；
  - 执行 no-CFD preflight；
  - 只有显式加 `-AllowLongRun` 才会启动长时原生 FluidX3D。

本轮新验证命令：

```powershell
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\prepare_native_empty_tunnel_case_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\run_native_empty_tunnel_workflow_smoke.py
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_casee_empty_tunnel_paper_preflight.ps1 -OutDir "C:\Users\MSY\AppData\Local\Temp\citylbm_casee_empty_tunnel_script_preflight_20260826" -SolverCwd "C:\Users\MSY\AppData\Local\Temp\citylbm_casee_empty_tunnel_script_preflight_solver_20260826"
```

结果：

- `prepare_native_empty_tunnel_case_smoke passed`
- `run_native_empty_tunnel_workflow_smoke passed`
- `empty_tunnel_workflow stage=preflight; next=run; vtk_frames=0; profile=missing; correlation=missing; chain=missing; execute=True`
- 最新 manifest：`C:\Users\MSY\AppData\Local\Temp\citylbm_casee_empty_tunnel_script_preflight_20260826\empty_tunnel_manifest.json`

当前阻塞：

- F 盘剩余空间为 0，不能把编译输出或长算例输出放在 F 盘。
- 当前 `dotnet run --project .\tests\CodegenSmoke\CodegenSmoke.csproj -c Release` 受本机 .NET Framework 4.8 targeting pack 缺失/编译环境影响；脚本级烟测已通过，但完整 C# 生成器 smoke 需要恢复构建环境后再跑。
- 这一步只证明长算例前置链路被加速和约束，并不证明 Case E 精度已经达到论文级。论文级结论仍需启动 `-AllowLongRun`，得到 40+ 个后期 VTK 平均帧，并通过入口 profile、入口相关性、probe chain 和 AIJ 实测对比。

## 2026-08-26 加速修正：Case E ac+N 筛选和预检失败拦截

目的：避免把 AIJ Case E 全量 `RS_caseE.csv` 的 2560 行误当成 `ac+N` 验证测点，避免长时间 FluidX3D 跑完后才发现官方表筛选、测点编号或时间平均计划错误。

已实现：

- `prepare_native_empty_tunnel_case.py` 新增并传递 `--official-condition-filter` 与 `--official-wind-filter`。
- `run_casee_empty_tunnel_paper_preflight.ps1` 默认固定 `OfficialConditionFilter=ac`、`OfficialWindFilter=N`。
- `run_native_validation_chain.py` 与 `audit_native_preconditions.py` 接收官方表筛选参数，保持 `case=CaseE` 作为报告标签，同时用 `condition=ac`、`wind=N` 做实测表过滤。
- `run_native_empty_tunnel_workflow.py` 先检查 no-CFD preflight gate，再决定是否进入长跑；若预检失败，下一步为 `inspect_preflight_failures`。
- workflow 在执行阶段后会重新计算状态，控制台输出不再停留在执行前的旧 `NextStage`。
- `prepare_native_empty_tunnel_case.py` 现在把 `--vtk-save-start-step` 传给 no-CFD preflight，避免 `ExpectedVtkFrameCount=51` 被误判成 60。

本轮新验证命令：

```powershell
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" -m py_compile .\scripts\audit_coordinate_probe_protocol.py .\scripts\prepare_native_empty_tunnel_case.py .\scripts\run_native_empty_tunnel_workflow.py .\scripts\run_native_validation_chain.py .\scripts\audit_native_preconditions.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\prepare_native_empty_tunnel_case_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\run_native_empty_tunnel_workflow_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\coordinate_probe_protocol_audit_smoke.py
& "C:\Users\MSY\AppData\Local\Programs\Python\Python310\python.exe" .\tests\native_preflight_pack_smoke.py
dotnet build -c Release
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_casee_empty_tunnel_paper_preflight.ps1 -OutDir "C:\Users\MSY\AppData\Local\Temp\citylbm_casee_empty_tunnel_filtered_preflight2_20260826" -SolverCwd "C:\Users\MSY\AppData\Local\Temp\citylbm_casee_empty_tunnel_filtered_solver2_20260826"
```

结果：

- Python syntax check passed.
- `prepare_native_empty_tunnel_case_smoke passed`
- `run_native_empty_tunnel_workflow_smoke passed`
- `coordinate_probe_protocol_audit_smoke passed`
- `native_preflight_pack_smoke passed`
- `dotnet build -c Release` 成功，0 warnings / 0 errors。
- Case E coordinate-probe protocol gate 通过：
  - `condition_filter = ac`
  - `wind_filter = N`
  - filtered `row_count = 80`
  - `unique_id_count = 80`
  - `duplicate_ids = []`
  - `invalid_coordinate_count = 0`
  - `expected_z = 2.0`
  - `af_u_at_zref_mps = 3.928296`
- Time averaging gate 通过：
  - `TimeSteps = 60000`
  - `VtkSaveInterval = 1000`
  - `VtkSaveStartStep = 10000`
  - `ExpectedVtkFrameCount = 51`
  - `AverageLastN = 40`
  - `MinimumStepSpan = 20000`
- workflow 当前真实状态：`next=inspect_preflight_failures`，不是 `run`。

当前结论：

- 这次修复缩短开发时间的核心价值是：Case E 的数据筛选、测点身份、Uref/AF 和时间平均计划已可在 no-CFD 阶段快速验证。
- 还不能启动论文级长跑，因为 `LongCfdAllowedNow=false`。当前第一优化目标仍是 `turbulent_inlet_method_and_u_k_preservation`，其次是 `boundary_roughness_blockage`。
- 如果只需要开发迭代，可启动短 diagnostic canary；如果要 SCI 论文级结果，必须先补齐入口湍流长度尺度/雷诺应力证据和 AIJ 边界等效性证据，再启动 `-AllowLongRun`。
