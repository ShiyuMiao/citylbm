# FluidX3D 设置指南

CityLBM 使用 [FluidX3D](https://github.com/ProjectPhysX/FluidX3D) 作为 LBM 求解器。本文档指导你完成 FluidX3D 的下载、编译和配置。

---

## 1. 下载 FluidX3D

```bash
git clone https://github.com/ProjectPhysX/FluidX3D.git
```

或直接下载 ZIP：
https://github.com/ProjectPhysX/FluidX3D/archive/refs/heads/master.zip

建议将 FluidX3D 放在固定位置，例如：
- `D:\FluidX3D`
- `C:\FluidX3D`

---

## 2. 安装编译环境

### 2.1 Visual Studio 2022

FluidX3D 是 C++/CUDA 项目，需要 Visual Studio：

1. 下载 [Visual Studio 2022 Community](https://visualstudio.microsoft.com/downloads/)（免费）
2. 安装时勾选以下工作负载：
   - **使用 C++ 的桌面开发** (Desktop development with C++)
3. 在"单个组件"中确保勾选：
   - MSVC v143 - VS 2022 C++ x64/x86 生成工具
   - Windows 11 SDK（或 Windows 10 SDK）
   - C++ ATL for latest v143 build tools (x86 & x64)

### 2.2 NVIDIA CUDA（如果使用 GPU 加速）

FluidX3D 默认使用 CUDA 加速，需要：

1. NVIDIA 显卡（GTX 1060 及以上推荐）
2. 最新显卡驱动
3. CUDA Toolkit（通常随显卡驱动安装，或单独安装）

检查 CUDA 是否可用：
```bash
nvidia-smi
```

> 如果没有 NVIDIA GPU，FluidX3D 也支持 CPU 模式（性能较低）。

---

## 3. 编译 FluidX3D

### 方法一：Visual Studio GUI

1. 打开 `FluidX3D.sln`
2. 顶部工具栏选择 **Release** 配置和 **x64** 平台
3. 菜单 `Build` → `Build Solution`（或按 `Ctrl+Shift+B`）
4. 等待编译完成（首次约 2-5 分钟）

### 方法二：命令行 (MSBuild)

```bash
cd FluidX3D
msbuild FluidX3D.sln /p:Configuration=Release /p:Platform=x64
```

### 编译输出

编译成功后，可执行文件位于：
```
FluidX3D/bin/FluidX3D.exe
```

### 验证编译

```bash
cd FluidX3D/bin
FluidX3D.exe
```

如果能正常运行（可能因为没有 case 文件而立即退出），说明编译成功。

---

## 4. 配置 CityLBM 连接 FluidX3D

### 方法一：组件参数（推荐）

在 Grasshopper 的 `Run Simulation` 组件中，找到 **FluidX3D Path** 输入端，填入 FluidX3D 的根目录路径，例如：
```
D:\FluidX3D
```

### 方法二：配置文件

编辑 CityLBM 目录下的 `citylbm.config`：
```ini
[FluidX3D]
InstallPath = D:\FluidX3D
```

### 方法三：环境变量

设置系统环境变量：
```
变量名: FLUIDX3D_PATH
变量值: D:\FluidX3D
```

CityLBM 会按以下优先级搜索 FluidX3D：
1. 组件参数中填写的路径
2. `citylbm.config` 中的路径
3. `FLUIDX3D_PATH` 环境变量
4. 常见安装位置（`%USERPROFILE%\FluidX3D`、`D:\FluidX3D` 等）

---

## 5. 运行模拟

配置完成后，在 Grasshopper 中：

1. 构建完整工作流：`Create Scene → Add Buildings → Generate Grid → Run Simulation`
2. 在 `Run Simulation` 组件中：
   - **Mode**: 选择 `3`（异步后台运行，推荐）或 `1`（全自动同步）
   - **FluidX3D Path**: 填写路径
   - **Run**: 设为 `True`
3. 等待模拟完成（组件会实时显示进度 0-100%）
4. 使用 `Read VTK` 读取结果

---

## 常见问题

### Q: 编译 FluidX3D 失败 - 找不到 CUDA

**A:** 确保：
- 已安装 NVIDIA 显卡驱动（最新版）
- Visual Studio 安装了 C++ 桌面开发工作负载
- 尝试在 FluidX3D 的 `defines.hpp` 中禁用 CUDA（改为 CPU 模式）

### Q: CityLBM 找不到 FluidX3D

**A:** 检查：
- 路径是否正确（指向 FluidX3D 根目录，不是 bin 子目录）
- 目录下是否存在 `FluidX3D.sln` 或 `src/` 子目录
- 尝试使用绝对路径而非相对路径

### Q: 模拟运行后没有 VTK 输出

**A:** 检查：
- FluidX3D 编译是否成功（`bin/FluidX3D.exe` 是否存在）
- `defines.hpp` 中的 `SAVE_VTK` 宏是否启用
- CityLBM 组件的 `Save Interval` 是否设置合理

### Q: 没有 NVIDIA GPU 怎么办？

**A:** FluidX3D 可以在没有 GPU 的机器上以 CPU 模式运行，但性能会大幅下降。修改 FluidX3D 的 `defines.hpp`，将 `COMPUTE` 相关宏改为 CPU 模式。

---

## 参考资料

- FluidX3D GitHub: https://github.com/ProjectPhysX/FluidX3D
- FluidX3D Wiki: https://github.com/ProjectPhysX/FluidX3D/wiki
- FluidX3D 论文: https://doi.org/10.1016/j.cpc.2023.108765
