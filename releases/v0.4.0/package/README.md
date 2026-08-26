<p align="center">
  <img src="assets/branding/citylbm-readme-icon.png" alt="CityLBM application icon" width="144">
</p>

<p align="center">
  <img src="assets/branding/citylbm-readme-header.png" alt="CityLBM - Urban Wind Simulation" width="960">
</p>

<p align="center">
  <strong>面向设计流程的城市风环境模拟工具</strong><br>
  <em>Design-oriented urban wind simulation workflow</em>
</p>

<p align="center">
  <a href="#中文">中文</a> | <a href="#english">English</a> | <a href="LICENSE">MIT License</a>
</p>

## 图标目录

CityLBM 的 README 主图标和组件图标集中如下。主图标的可编辑 Draw.io 源文件位于 [`assets/branding/citylbm-app-icon.drawio`](assets/branding/citylbm-app-icon.drawio)。下列图标是当前仓库随附的界面资源目录，不单独构成组件可用性或验证完成的声明。

| 场景与输入 | 仿真与数据 | 可视化与分析 | 工作流辅助 |
| --- | --- | --- | --- |
| <img src="src/Resources/Icons/CreateScene.png" width="42" alt="Create Scene"><br>Create Scene | <img src="src/Resources/Icons/RunSimulation.png" width="42" alt="Run Simulation"><br>Run Simulation | <img src="src/Resources/Icons/ReadVTK.png" width="42" alt="Read VTK"><br>Read VTK | <img src="src/Resources/Icons/validation.png" width="42" alt="Validation"><br>Validation |
| <img src="src/Resources/Icons/AddBuildings.png" width="42" alt="Add Buildings"><br>Add Buildings | <img src="src/Resources/Icons/SimulationStats.png" width="42" alt="Simulation Stats"><br>Simulation Stats | <img src="src/Resources/Icons/VelocityVisualization.png" width="42" alt="Velocity Visualization"><br>Velocity View | <img src="src/Resources/Icons/Lawson.png" width="42" alt="Lawson"><br>Lawson |
| <img src="src/Resources/Icons/WindCondition.png" width="42" alt="Wind Condition"><br>Wind Condition | <img src="src/Resources/Icons/GridGenerator.png" width="42" alt="Grid Generator"><br>Grid Generator | <img src="src/Resources/Icons/VTKCloudVisualization.png" width="42" alt="VTK Cloud"><br>VTK Cloud | <img src="src/Resources/Icons/DataProbe.png" width="42" alt="Data Probe"><br>Data Probe |
| <img src="src/Resources/Icons/DomainSetup.png" width="42" alt="Domain Setup"><br>Domain Setup | <img src="src/Resources/Icons/AbsoluteDomain.png" width="42" alt="Absolute Domain"><br>Absolute Domain | <img src="src/Resources/Icons/SliceVisualization.png" width="42" alt="Slice Visualization"><br>Slice View | <img src="src/Resources/Icons/Streamlines.png" width="42" alt="Streamlines"><br>Streamlines |
| <img src="src/Resources/Icons/DomainDesigner.png" width="42" alt="Domain Designer"><br>Domain Designer | <img src="src/Resources/Icons/WindSpeedGrid.png" width="42" alt="Wind Speed Grid"><br>Wind Speed Grid | <img src="src/Resources/Icons/VerticalSlice.png" width="42" alt="Vertical Slice"><br>Vertical Slice | <img src="src/Resources/Icons/Isosurface.png" width="42" alt="Isosurface"><br>Isosurface |
| <img src="src/Resources/Icons/SceneInfo.png" width="42" alt="Scene Info"><br>Scene Info |  |  |  |

---

<a id="中文"></a>
## 中文

CityLBM 是一个面向 Rhino/Grasshopper 设计流程的城市风环境模拟工作流。它连接场景定义、FluidX3D 案例生成与外部求解、VTK 结果读取和 Rhino 内可视化，使研究人员能够在同一参数化环境中组织可追溯的风环境案例。

### 当前可展示的成果

- **可运行的工作流原型**：从 Grasshopper 场景与建筑输入，到 FluidX3D 案例文件、VTK 输出和 Rhino 结果查看。
- **AIJ Case A/E 复现资产**：包含案例文件、`setup.cpp`、坐标/尺度元数据、点位结果表和工作流截图；v0.2.0 包用于复现与检查。
- **v0.3.0 验证就绪性改造**：风速与 `k` 剖面输入、元数据记录、时间平均、点位/归一化/几何尺度审计，以及原生 FluidX3D 基线预检和自动验证门禁。
- **可追溯实验链**：验证脚本与指标模板支持保存运行元数据、探针结果、哈希和门禁报告。

### 验证状态

项目处于积极开发阶段。现有 AIJ Case A/E 资产证明端到端工作流和诊断能力；其中短步数 smoke run 与诊断结果不应被解释为论文级精度验证。正式准确性结论仍需要严格原生基线、入口和边界条件证据、充分时间平均以及网格收敛记录。

v0.3.0 的交付边界见 [`docs/v0.3.0_validation_ready_status.md`](docs/v0.3.0_validation_ready_status.md)：它是验证就绪版本，不是已经完成的 Case A/E 论文级精度结果。

### v0.4.0 当前封装记录

v0.4.0 封装当前 Rhino 7 / Grasshopper 验证分支成果，停止继续向论文级精度优化推进，保留已形成的代码、脚本和诊断证据。该版本的重点是把 CityLBM 的案例生成、原生 FluidX3D 基线预检、VTK 输出完整性检查、入口剖面审计、边界审计和测点误差统计组织成可追溯工作流。

- 插件元数据、Yak manifest 和程序集版本统一为 `0.4.0`。
- Case A 已完成 full AF 表格输入的代码生成校验，`AF_caseA.csv` 的 24 行 `z, U, k` 被写入生成的 FluidX3D `setup.cpp` 和元数据。
- 原生 FluidX3D Case A 300/150 诊断跑产生 2 个完整 VTK 帧，并完成 186 个官方测点的后处理审计；随后新增 `VTK Save Start=100` 的短 canary，验证保存调度可产生 `[100, 250, 300]` 三个完整 VTK 帧。
- 当前诊断指标仍不作为发表级精度结论：`R2=-2.8714`，`Pearson=0.0163`，`RMSE ratio=3.4374`，主要阻塞包括步数/平均不足、入口 `k` 运行保持不足、边界协议证据不足和 native preconditions 未通过。
- v0.4.0 用户包可直接安装 Grasshopper 插件并生成案例；真实模拟仍需要用户在 `Run Simulation` 中指定本机可用的 FluidX3D 源码或求解器环境。

### 快速开始

1. 按 [`INSTALL.md`](INSTALL.md) 将 `CityLBM.gha` 及其依赖安装到 Grasshopper Libraries 目录。
2. 在 Rhino/Grasshopper 中使用 `Create Scene` 和相关场景组件生成案例。
3. 使用 `Run Simulation` 指向完整的本地 FluidX3D 源码或可执行环境；仅生成案例可使用 `Mode 0`。
4. 使用 `Read VTK` 与可视化组件读取输出。严格 AIJ Case E 流程见 [`docs/CaseE_run_protocol.md`](docs/CaseE_run_protocol.md)。

### 构建

```powershell
dotnet build -c Release
```

Release 构建产物位于 `bin/Release/CityLBM.gha`。当前开发分支为验证就绪性迭代，不应替代经审核的正式发布包。

---

<a id="english"></a>
## English

CityLBM is an urban wind-simulation workflow for Rhino and Grasshopper. It connects scene definition, FluidX3D case generation and external execution, VTK result reading, and in-Rhino visualization so that wind-environment cases can be organized in one traceable parametric workflow.

### What Is Available

- **Runnable workflow prototype**: Grasshopper scene and building input through FluidX3D case files, VTK output, and Rhino result inspection.
- **AIJ Case A/E reproduction assets**: case files, `setup.cpp`, coordinate and scale metadata, probe-result workbooks, and workflow screenshots. The v0.2.0 package is intended for reproduction and inspection.
- **v0.3.0 validation-readiness work**: velocity and `k` profile input, metadata capture, time averaging, probe/normalization/geometry-scale audits, native FluidX3D baseline preflight, and automated validation gates.
- **Traceable experiment chain**: validation scripts and metric templates support run metadata, probe outputs, hashes, and gate reports.

### Validation Status

CityLBM is under active academic development. Existing AIJ Case A/E assets demonstrate the end-to-end workflow and diagnostic capability. Short smoke runs and diagnostic outputs are not publication-grade accuracy validation. Final accuracy claims require a strict native baseline, inlet and boundary evidence, adequate time averaging, and documented grid convergence.

See [`docs/v0.3.0_validation_ready_status.md`](docs/v0.3.0_validation_ready_status.md) for the v0.3.0 delivery boundary: it is validation-ready, not a completed Case A/E publication-grade accuracy result.

### v0.4.0 Packaging Record

v0.4.0 packages the current Rhino 7 / Grasshopper validation branch and stops further accuracy optimization in this release line. It preserves the current code, scripts, and diagnostic evidence as a traceable workflow rather than presenting the short diagnostic runs as publication-grade validation.

- Plugin metadata, Yak manifest, and assembly versions are unified as `0.4.0`.
- Case A full-AF code generation was verified: all 24 rows from `AF_caseA.csv` are emitted into FluidX3D `setup.cpp` and metadata.
- A native FluidX3D Case A 300/150 diagnostic run produced 2 complete VTK frames and completed post-processing for 186 official probe points; a later `VTK Save Start=100` short canary verified the `[100, 250, 300]` three-frame output schedule.
- The current diagnostic metrics are not publication-grade: `R2=-2.8714`, `Pearson=0.0163`, `RMSE ratio=3.4374`. Remaining blockers include insufficient run length/averaging, incomplete runtime preservation of inlet `k`, insufficient boundary protocol evidence, and failing native preconditions.
- The v0.4.0 package can be installed directly in Grasshopper and can generate cases. Real solver execution still requires a local FluidX3D source tree or executable environment to be configured in `Run Simulation`.

### Quick Start

1. Follow [`INSTALL.md`](INSTALL.md) to install `CityLBM.gha` and its dependencies in the Grasshopper Libraries directory.
2. Create a case with `Create Scene` and the related scene components in Rhino/Grasshopper.
3. Point `Run Simulation` to a complete local FluidX3D source tree or executable environment. Use `Mode 0` for case generation only.
4. Read outputs with `Read VTK` and visualization components. See [`docs/CaseE_run_protocol.md`](docs/CaseE_run_protocol.md) for the strict AIJ Case E workflow.

### Build

```powershell
dotnet build -c Release
```

The Release artifact is written to `bin/Release/CityLBM.gha`. The current development branch focuses on validation readiness and is not a substitute for a reviewed release package.

## License

Released under the [MIT License](LICENSE).

## Author

Shiyu Miao, Dalian University of Technology<br>
miaoshiyu@mail.dlut.edu.cn
