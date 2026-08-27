<table align="center">
  <tr>
    <td width="112" valign="middle">
      <img src="assets/branding/citylbm-readme-icon.png" alt="CityLBM application icon" width="96">
    </td>
    <td valign="middle" align="center">
      <h1>CityLBM</h1>
      <strong>面向设计流程的城市风环境模拟工作流</strong><br>
      <em>Design-oriented urban wind simulation workflow</em>
    </td>
  </tr>
</table>

<p align="center">
  <a href="#中文介绍">中文</a> | <a href="#english-overview">English</a> | <a href="LICENSE">MIT License</a>
</p>

## 图标目录 / Icon Catalogue

主图标的可编辑 Draw.io 源文件位于 [`assets/branding/citylbm-app-icon.drawio`](assets/branding/citylbm-app-icon.drawio)。以下为仓库随附的界面图标目录；它们用于说明工作流界面，不单独构成组件可用性、求解器性能或验证完成的声明。

| 场景与输入 / Scene | 仿真与数据 / Simulation | 可视化 / Visualization | 分析与辅助 / Analysis |
| --- | --- | --- | --- |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/CreateScene.png" width="42" alt="Create Scene"><br>Create Scene | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/RunSimulation.png" width="42" alt="Run Simulation"><br>Run Simulation | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/ReadVTK.png" width="42" alt="Read VTK"><br>Read VTK | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/validation.png" width="42" alt="Validation"><br>Validation |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/AddBuildings.png" width="42" alt="Add Buildings"><br>Add Buildings | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/SimulationStats.png" width="42" alt="Simulation Stats"><br>Simulation Stats | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/VelocityVisualization.png" width="42" alt="Velocity Visualization"><br>Velocity View | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/Lawson.png" width="42" alt="Lawson"><br>Lawson |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/WindCondition.png" width="42" alt="Wind Condition"><br>Wind Condition | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/GridGenerator.png" width="42" alt="Grid Generator"><br>Grid Generator | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/VTKCloudVisualization.png" width="42" alt="VTK Cloud"><br>VTK Cloud | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/DataProbe.png" width="42" alt="Data Probe"><br>Data Probe |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/DomainSetup.png" width="42" alt="Domain Setup"><br>Domain Setup | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/AbsoluteDomain.png" width="42" alt="Absolute Domain"><br>Absolute Domain | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/SliceVisualization.png" width="42" alt="Slice Visualization"><br>Slice View | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/Streamlines.png" width="42" alt="Streamlines"><br>Streamlines |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/DomainDesigner.png" width="42" alt="Domain Designer"><br>Domain Designer | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/WindSpeedGrid.png" width="42" alt="Wind Speed Grid"><br>Wind Speed Grid | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/VerticalSlice.png" width="42" alt="Vertical Slice"><br>Vertical Slice | <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/Isosurface.png" width="42" alt="Isosurface"><br>Isosurface |
| <img src="https://raw.githubusercontent.com/ShiyuMiao/citylbm/main/assets/icons/SceneInfo.png" width="42" alt="Scene Info"><br>Scene Info |  |  |  |

---

<a id="中文介绍"></a>
## 中文介绍

CityLBM 是面向 Rhino/Grasshopper 参数化设计流程的城市风环境模拟工作流。它将场景定义、建筑几何、FluidX3D 案例生成与外部求解、VTK 结果读取和 Rhino 内可视化串联起来，用于组织可追溯的城市风环境研究与设计探索。

### 可展示内容

- **设计工作流**：从 Grasshopper 场景与建筑输入，到 FluidX3D 案例文件、VTK 输出和 Rhino 结果查看。
- **案例资产**：仓库的 `releases/v0.2.0` 包含 AIJ Case A/E 的示例文件、`setup.cpp`、元数据、结果表和工作流截图。
- **验证工程化**：开发分支增加了速度与 `k` 剖面输入、运行元数据、时间平均、点位与归一化审计、原生 FluidX3D 基线预检和自动门禁。
- **可追溯性**：验证脚本和指标模板面向保存案例配置、探针结果、哈希及门禁报告。

### 版本进展对比

| 版本 | 状态 | 相对前版的主要进展 | 适合展示的内容 | 不应作出的结论 |
| --- | --- | --- | --- | --- |
| **v0.2.0** | 已发布的用户包 | 稳定的 Grasshopper 场景、案例生成和 VTK 可视化工作流；独立 `Lawson` 伴随组件；AIJ Case A/E 示例与校验文件 | 安装流程、界面图标、示例工作流、案例文件与复现步骤 | 不将示例结果视为通用精度、设计优化或舒适度结论 |
| **v0.2.1** | 开发迭代 | 补充 AIJ Case A 工作流资料和辅助脚本，推进 FluidX3D 接入、VTK 可视化与界面图标整理 | 研究工作流演进、案例准备和组件界面 | 不作为独立的已审核公开发布包 |
| **v0.3.0** | 验证就绪开发分支 | 支持 `z, U, k` 自定义入口剖面、案例/坐标元数据、显式多帧时间平均、指标计算，以及入口、边界、探针、归一化和原生基线门禁 | 可追溯验证框架、协议、审计脚本与下一轮严格实验设计 | 不宣称 AIJ 论文级准确性、网格无关性、LES 优势或真实城区预测能力 |

### 当前验证边界

AIJ Case A/E 的现有资产证明端到端工作流和诊断能力。短步数 smoke run、历史诊断结果或代码构建成功均不等同于论文级精度验证。正式准确性结论仍需要严格原生基线、入口和边界条件证据、充分时间平均、官方高度点位比对及网格收敛记录。

### 成果与 VTK 解读

AIJ Case A 的归档包包含 `u-000001000.vtk`、`u-000002000.vtk`、坐标映射、90 点采样脚本和既有对比表。文件结构、坐标换算、ParaView/Rhino 查看方式，以及速度单位与验证边界见 [`docs/RESULTS_AND_VTK_GUIDE.md`](docs/RESULTS_AND_VTK_GUIDE.md)。原始 VTK 体积较大，保留在本地验证档案而不直接纳入仓库。

### 交互风场预览

[`docs/wind-field`](docs/wind-field) 提供无需后端的 Three.js 浏览器预览：它加载由 Case A VTK 下采样生成的速度点与流向线段，可旋转查看三维风场。页面源码和生成脚本随仓库提交；启用静态站点托管后即可直接发布，原始 VTK 不会上传。

### 使用方式

1. 按 [`INSTALL.md`](INSTALL.md) 安装 `CityLBM.gha` 及依赖。
2. 在 Rhino/Grasshopper 中使用场景组件定义建筑、计算域和风况。
3. 生成 FluidX3D 案例，并在已配置的本地求解环境中运行。
4. 使用 `Read VTK` 与可视化组件读取结果；示例位于 [`releases/v0.2.0`](releases/v0.2.0)。

---

<a id="english-overview"></a>
## English Overview

CityLBM is an urban wind-simulation workflow for Rhino and Grasshopper. It connects scene definition, building geometry, FluidX3D case generation and external execution, VTK result reading, and in-Rhino visualization for traceable urban wind research and design exploration.

### What This Repository Shows

- **Design workflow**: Grasshopper scene and building input through FluidX3D case files, VTK output, and Rhino result inspection.
- **Case assets**: `releases/v0.2.0` includes AIJ Case A/E examples, `setup.cpp`, metadata, result workbooks, and workflow screenshots.
- **Validation engineering**: the development branch adds velocity and `k` profile input, run metadata, time averaging, probe and normalization audits, native FluidX3D baseline preflight, and automated gates.
- **Traceability**: validation scripts and metric templates are intended to retain case configurations, probe outputs, hashes, and gate reports.

### Version Progress at a Glance

| Version | Status | Main progress | Appropriate showcase | Claim boundary |
| --- | --- | --- | --- | --- |
| **v0.2.0** | Released user package | Stable Grasshopper scene, case-generation, and VTK-visualization workflow; separate Lawson companion; AIJ Case A/E examples and checks | Installation, icon system, example workflows, case assets, and reproduction steps | Example outputs are not general accuracy, optimization, or comfort conclusions |
| **v0.2.1** | Development iteration | Added AIJ Case A workflow material and helper scripts; advanced FluidX3D integration, VTK visualization, and icon organization | Workflow evolution, case preparation, and component interface | Not an independently reviewed public release package |
| **v0.3.0** | Validation-readiness development branch | `z, U, k` inlet profiles, case/coordinate metadata, explicit multi-frame averaging, metrics, and inlet/boundary/probe/normalization/native-baseline gates | Traceable validation framework, protocol, audit scripts, and strict-experiment planning | No claim of publication-grade AIJ accuracy, grid independence, LES superiority, or real-district predictive capability |

### Validation Boundary

Existing AIJ Case A/E assets demonstrate the end-to-end workflow and diagnostic capability. Short smoke runs, historic diagnostic outputs, or a successful code build are not publication-grade accuracy validation. Final accuracy claims require a strict native baseline, inlet and boundary evidence, adequate time averaging, official-height probe comparison, and documented grid convergence.

### Results and VTK Guide

The archived AIJ Case A package contains `u-000001000.vtk`, `u-000002000.vtk`, coordinate mapping, a 90-point sampling script, and an existing comparison workbook. See [`docs/RESULTS_AND_VTK_GUIDE.md`](docs/RESULTS_AND_VTK_GUIDE.md) for file structure, coordinate conversion, ParaView/Rhino inspection, velocity-unit limits, and validation boundaries. The raw VTK snapshots remain in the local validation archive because of their size.

### Interactive Wind-Field Preview

[`docs/wind-field`](docs/wind-field) contains a backend-free Three.js preview. It loads downsampled Case A velocity points and flow-direction segments for an orbitable 3D view. The page source and generation script are versioned with the repository; it is ready for static hosting without publishing the raw VTK.

### Usage

1. Follow [`INSTALL.md`](INSTALL.md) to install `CityLBM.gha` and dependencies.
2. Define buildings, the computational domain, and wind conditions with the Rhino/Grasshopper scene components.
3. Generate a FluidX3D case and run it in a configured local solver environment.
4. Read results with `Read VTK` and visualization components; examples are under [`releases/v0.2.0`](releases/v0.2.0).

## License

Released under the [MIT License](LICENSE).

## Author

Shiyu Miao, Dalian University of Technology<br>
miaoshiyu@mail.dlut.edu.cn
