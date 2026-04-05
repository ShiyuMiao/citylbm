# CityLBM - 城市风环境模拟 Grasshopper 插件

**版本:** v0.1.0wip (Work In Progress)  
**最后更新:** 2026-04-04

> **注意：** 这是 CityLBM 的早期内测版本（WIP），已达到最小可用状态。功能可能不完善，使用过程中遇到问题欢迎反馈。

---

## 简介

CityLBM 是一个基于**格子玻尔兹曼方法 (LBM)** 的城市风环境模拟 Grasshopper 插件。它集成了 [FluidX3D](https://github.com/ProjectPhysX/FluidX3D) 高性能 GPU 求解器，为城市规划师和建筑设计师提供高效的城市风场模拟工具。

### 核心特性

- **场景管理** - 在 Grasshopper 中直接创建风场模拟场景，设置风向、风速
- **建筑导入** - 从 Rhino/Grasshopper 直接导入建筑物几何体
- **网格生成** - 自动生成笛卡尔网格，标记建筑障碍物和边界条件
- **LBM 求解** - 集成 FluidX3D GPU 加速求解器，支持自动部署、编译和运行
- **异步模拟** - 后台运行模拟，实时显示进度（推荐 Mode 3）
- **结果可视化** - VTK 云图、速度箭头、水平切片、模拟统计
- **多 Rhino 版本** - 自动检测 Rhino 6/7/8 并适配

---

## 系统要求

| 组件 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 |
| **Rhino** | Rhino 6 / 7 / 8 |
| **Grasshopper** | 随 Rhino 安装 |
| **.NET SDK** | .NET 6.0 或更高（仅编译需要，使用预编译版不需要） |
| **GPU** | NVIDIA 显卡（运行模拟需要，用于 FluidX3D CUDA 加速） |
| **FluidX3D** | [GitHub 下载](https://github.com/ProjectPhysX/FluidX3D)（运行模拟需要） |
| **Visual Studio** | VS 2022 + C++ 桌面开发（编译 FluidX3D 需要） |

---

## 快速安装

### 方法一：使用预编译插件（推荐）

1. **下载 `CityLBM.gha`**
   - 位于 `bin/CityLBM.gha`

2. **安装到 Grasshopper**
   - 方法 A：在 Grasshopper 中菜单 `File` → `Special Folders` → `Components Folder`，将 `CityLBM.gha` 复制进去
   - 方法 B：手动复制到 `%APPDATA%\Grasshopper\Libraries\`

3. **重启 Rhino 和 Grasshopper**
   - 在组件面板中找到 **CityLBM** 标签页

### 方法二：从源码编译

```bash
# 1. 克隆仓库
git clone https://github.com/ShiyuMiao/citylbm.git
cd citylbm/CityLBM

# 2. 恢复依赖
dotnet restore

# 3. 编译（Release 模式，自动 ILRepack 合并依赖）
dotnet build -c Release

# 4. 输出文件
# bin/Release/CityLBM.gha  ← 复制到 Grasshopper Libraries
```

> 编译需要本机已安装 Rhino（用于引用 RhinoCommon.dll 和 Grasshopper.dll）。项目文件会自动检测 Rhino 6/7/8 的安装路径。

---

## FluidX3D 设置

CityLBM 依赖 [FluidX3D](https://github.com/ProjectPhysX/FluidX3D) 作为 LBM 求解器。详细设置步骤请参阅 [FluidX3D 设置指南](./FluidX3D设置指南.md)。

### 快速步骤

1. 下载 FluidX3D：`git clone https://github.com/ProjectPhysX/FluidX3D.git`
2. 安装 Visual Studio 2022，勾选"使用 C++ 的桌面开发"
3. 编译 FluidX3D（用 VS 打开 `FluidX3D.sln`，Build → Release x64）
4. 在 CityLBM 的 `citylbm.config` 或组件参数中填写 FluidX3D 路径

---

## 工作流程

```
┌──────────────┐    ┌──────────────┐    ┌────────────────┐
│ Create Scene │───→│ Add Buildings│───→│ Generate Grid  │
│  设置风场     │    │  导入建筑     │    │  生成计算网格   │
└──────────────┘    └──────────────┘    └───────┬────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │   Run Simulation       │
                                    │  Mode 0: 仅生成 Case   │
                                    │  Mode 1: 全自动同步    │
                                    │  Mode 2: 仅部署        │
                                    │  Mode 3: 异步后台(推荐)│
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │     Read VTK          │
                                    │   读取模拟结果         │
                                    └───────────┬───────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
            ┌───────▼───────┐          ┌────────▼────────┐        ┌────────▼────────┐
            │ VTK Cloud Map │          │ Velocity Arrows │        │ Velocity Slice  │
            │   速度云图     │          │   速度箭头       │        │   水平切片      │
            └───────────────┘          └─────────────────┘        └─────────────────┘
```

---

## 组件列表

### 场景管理 (Scene)

| 组件 | 说明 |
|------|------|
| **Create Scene** | 创建模拟场景，设置风向、风速、域扩展比 |
| **Add Buildings** | 向场景添加建筑物 Mesh |
| **Scene Info** | 显示场景统计信息（建筑数量、域边界等） |

### 模拟 (Simulation)

| 组件 | 说明 |
|------|------|
| **Generate Grid** | 生成笛卡尔计算网格，自动标记障碍物和边界 |
| **Run Simulation** | 运行 LBM 模拟（4 种模式），自动部署到 FluidX3D |

### 结果 (Results)

| 组件 | 说明 |
|------|------|
| **Read VTK** | 读取 FluidX3D 输出的 VTK 文件，支持降采样 |
| **VTK Cloud Map** | 速度场彩色云图可视化（水平/多层切片） |
| **Velocity Arrows** | 速度场箭头可视化（自适应缩放） |
| **Velocity Slice** | 速度场水平切片可视化 |
| **Simulation Stats** | 模拟结果统计分析 |

---

## 使用示例

### 1. 最小可用流程（仅查看，不运行模拟）

```
Rhino 中创建建筑 → Mesh 组件 → Create Scene → Add Buildings → Scene Info
```

### 2. 完整模拟流程

```
Create Scene → Add Buildings → Generate Grid → Run Simulation (Mode 3) → Read VTK → VTK Cloud Map
```

**Run Simulation 关键参数：**
- **Mode**: `3`（异步后台运行，推荐）
- **FluidX3D Path**: FluidX3D 源码根目录路径
- **Viscosity**: 空气运动粘度，默认 `1.5e-5` m²/s
- **Time Steps**: 模拟步数，默认 `5000`
- **Save Interval**: VTK 输出间隔，默认 `500`

**VTK Cloud Map 关键参数：**
- **Mode**: `0` = 单层切片, `1` = 多层切片
- **Slice Z**: 切片高度（Mode 0）
- **Slice Count**: 多层切片数量（Mode 1）
- **Color Low / Color High**: 颜色映射范围

---

## 项目结构

```
CityLBM/
├── src/
│   ├── CityLBMPlugin.cs              # 插件入口
│   ├── Components/
│   │   ├── SceneMgmt/                # 场景管理组件
│   │   │   ├── CreateSceneComponent.cs
│   │   │   ├── AddBuildingsComponent.cs
│   │   │   └── SceneInfoComponent.cs
│   │   ├── Simulation/               # 模拟组件
│   │   │   ├── GridGeneratorComponent.cs
│   │   │   └── RunSimulationComponent.cs
│   │   └── Results/                  # 结果可视化组件
│   │       ├── ReadVTKComponent.cs
│   │       ├── VTKCloudVisualizationComponent.cs
│   │       ├── VelocityVisualizationComponent.cs
│   │       ├── SliceVisualizationComponent.cs
│   │       └── SimulationStatsComponent.cs
│   ├── Core/
│   │   ├── Scene.cs                  # 场景数据模型
│   │   ├── GridGenerator.cs          # 笛卡尔网格生成器
│   │   └── FluidX3DInterface.cs      # FluidX3D 集成接口
│   └── Utils/
│       └── GHSceneHelper.cs          # GH 数据类型包装
├── bin/
│   └── CityLBM.gha                   # 预编译插件（ILRepack 合并依赖）
├── docs/                             # 用户文档
├── examples/                         # 示例文件
├── tools/                            # 辅助脚本
├── CityLBM.csproj                    # 项目配置
├── CityLBM.sln                       # VS 解决方案
├── citylbm.config                    # 配置文件模板
├── build.ps1 / compile.bat           # 编译脚本
├── deploy.bat                        # 一键编译部署
├── FluidX3D设置指南.md               # FluidX3D 安装配置
└── README.md
```

---

## 配置文件

`citylbm.config` 文件（放在 CityLBM 目录下）：

```ini
[FluidX3D]
# FluidX3D 源码根目录
InstallPath = D:\FluidX3D

[Simulation]
DefaultTimeSteps = 5000
DefaultSaveInterval = 500
DefaultViscosity = 1.5e-5

[Output]
# 工作目录，留空使用系统临时目录
WorkingDirectory = 

[MSBuild]
# Visual Studio 路径，留空自动检测
VisualStudioPath = 
```

也可以在 Run Simulation 组件中直接填写 FluidX3D 路径，优先级高于配置文件。

---

## 已知限制

- 仅支持 Windows 平台
- 模拟需要 NVIDIA GPU（FluidX3D 使用 CUDA）
- 建筑几何以 STL 格式传递给 FluidX3D
- VTK 读取支持 ASCII 和 Binary 格式
- 首次运行模拟需编译 FluidX3D（约 2-5 分钟）

---

## 技术栈

- **C# / .NET Framework 4.8** - Grasshopper 插件开发
- **RhinoCommon / Grasshopper SDK** - Rhino 几何和 GH 组件框架
- **FluidX3D (C++/CUDA)** - GPU 加速 LBM 求解器
- **ILRepack** - 合并依赖到单个 .gha 文件
- **Newtonsoft.Json** - JSON 序列化
- **NLog** - 日志记录

---

## 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件

---

## 致谢

- [FluidX3D](https://github.com/ProjectPhysX/FluidX3D) - 高性能开源 LBM 求解器
- [Rhino & Grasshopper](https://www.rhino3d.com/) - 参数化设计平台
