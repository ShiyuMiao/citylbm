# 成果与 VTK 解读 / Results and VTK Guide

> 盘点日期：2026-08-24。本页只整理已存在的本地档案和脚本，不代表本次重新运行或重新验证。

## 已归档成果

| 资产 | 已核验内容 | 使用边界 |
| --- | --- | --- |
| `releases/v0.2.0` | AIJ Case A/E 示例、案例配置、元数据、工作流截图及结果表 | 用于安装、流程复现和界面展示；不能单独证明通用精度。 |
| AIJ Case A 原始场 | `u-000001000.vtk` 与 `u-000002000.vtk` 两个速度场快照；后者 SHA256 为 `8771704F3E44EF05155664C6D4248D4DD0D67ED0843DFC4AB57AA6CDB0373E3B` | 原始 VTK 未提交到 GitHub，保留于本地验证档案，避免仓库膨胀。 |
| AIJ Case A 后处理 | 90 个中心线剖面采样点、内嵌 AIJ 对照值、Excel 导出脚本及既有对比表 | 现有表记录平均绝对误差 `37.35%`；它是历史处理结果，且不替代单位、收敛和边界条件复核。 |
| 开发期诊断序列 | 另有多组 Case A 原生/诊断输出序列 | 只有通过配置、入口、边界、探针、时间平均和网格门禁的序列，才可进入正式验证比较。 |

本地 AIJ Case A 归档根目录：

```text
F:\Grade2master2\CITYLBM开发文件\citylbm_v0.2.0_portable\validation\【验证】AIJCASEA_u-000002000
```

关键文件：

```text
case/buildings.stl                         建筑几何
case/defines.hpp                           FluidX3D 编译/运行参数
case/setup.cpp                             CityLBM 生成的求解案例
case/domain_origin.json                    物理域与 VTK 网格坐标映射
case/output/u-000001000.vtk                第 1000 步速度场快照
case/output/u-000002000.vtk                第 2000 步速度场快照
postprocess/AIJ_CaseA_export_excel.py      90 点采样与 Excel 导出
postprocess/AIJ_CaseA_validation_from_existing_vtk.xlsx
checksums.sha256                           插件与 u-000002000.vtk 的校验值
```

## VTK 文件中有什么

`u-000001000.vtk` 的头信息为 legacy VTK 3.0、`BINARY`、`DATASET STRUCTURED_POINTS`：

| 字段 | 当前归档值 | 含义 |
| --- | --- | --- |
| `DIMENSIONS` | `229 115 69` | 网格点数 `Nx x Ny x Nz`，共 `1,817,115` 点。 |
| `ORIGIN` | `(-114, -57, -34)` | VTK 格点坐标原点。 |
| `SPACING` | `(1, 1, 1)` | VTK 格点间距，以格点单位记录。 |
| `POINT_DATA` | `1,817,115` | 与三维网格点数一致。 |
| `SCALARS data float 3` | 三个 `float32` 数值/点 | 归档脚本将其按三分量速度场读取；旧式 VTK 使用 `SCALARS` 加分量数来表达该字段。 |

二进制数据是大端序。随附的 `AIJ_CaseA_export_excel.py` 已按此约定读取，在小端机器上会进行字节交换。不要用文本编辑器打开或修改 `.vtk` 文件。

## 坐标、速度与采样

`case/domain_origin.json` 给出设计物理坐标与 VTK 格点坐标的关系：物理域为 `x=-200..600`、`y=-200..200`、`z=0..240`，设计网格尺度 `Dx=3.5`。对物理坐标 `(x, y, z)`，随附脚本使用：

```text
x_vtk = -114 + (x - (-200)) / 3.5
y_vtk =  -57 + (y - (-200)) / 3.5
z_vtk =  -34 + (z - 0)      / 3.5
```

脚本以三线性插值读取 `data` 的首分量，取中心线 `y=0`，并在 `x/H = -1.5, -0.5, 0, 0.5, 1, 2, 3, 4, 5.5` 的 10 个高度点采样，共 90 点。它以 `U_H=5.0` 归一化，输出 `U_sim/U_H` 与内嵌 AIJ 基准值的差值。

**单位限制：** 该归档只有 `domain_origin.json`，未见 `case_metadata.json`、`VelocityOutputUnits` 或 `VelocityScaleLbmToMps`。脚本会因此默认速度缩放为 `1.0`，并把输出列标为 `m/s`。在重新检查 `setup.cpp` 与物理-格子单位换算前，应把数值理解为“按历史脚本处理的速度值”，不能直接作为已确认的 SI 速度或最终误差。

## 如何查看和解读

1. 在 ParaView 打开一个 `.vtk` 文件；其 `data` 字段应显示为 3 分量点数据。
2. 用 `Slice` 放置与案例一致的中心线或水平面，用 `Calculator` 计算速度模长：`mag(data)`。若需比较流向速度，明确选择首分量并记录坐标方向。
3. 对两个快照使用相同的色标范围、切面位置与坐标映射；否则视觉差异不可比较。
4. 需要 Rhino/Grasshopper 展示时，先用 `Read VTK` 读取，再以 `Velocity View`、`Slice View`、`Vertical Slice` 或 `Streamlines` 展示。显示结果应同时保留快照文件名、切面位置和色标范围。
5. 需要数值复核时，运行归档脚本并显式传入 VTK：

```powershell
python .\postprocess\AIJ_CaseA_export_excel.py `
  --vtk .\case\output\u-000002000.vtk `
  --output .\postprocess\AIJ_CaseA_validation_rechecked.xlsx
```

6. 在报告任何 AIJ 指标前，复核 `H`、`U_H`、首分量的流向定义、速度单位缩放、官方点位位置和足够的时间平均窗口。

## 不能从这两个文件得出的结论

- `u-000001000.vtk` 与 `u-000002000.vtk` 是两个快照，不证明稳态或充分时间平均。
- VTK 存在、可以读取或得到 Excel，不证明 AIJ Case A 的论文级准确性。
- 未完成原生基线、入口与边界条件核对、网格收敛和统一归一化前，不能用现有误差支持真实城区预测、设计优化或模型优越性结论。

## English Quick Reference

The archived AIJ Case A package contains two legacy binary `STRUCTURED_POINTS` VTK velocity snapshots, coordinate metadata, and a 90-point comparison script. The script reads `data float 3` as a three-component velocity field, maps physical coordinates through `domain_origin.json`, and samples the streamwise first component by trilinear interpolation. The archive does not include a confirmed velocity-unit scale. Treat the existing workbook as a historical diagnostic record, not as final validation. Before any accuracy claim, confirm units, flow direction, boundary/inlet settings, adequate averaging, official probe locations, and grid convergence.
