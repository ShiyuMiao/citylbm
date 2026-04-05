# CityLBM v1.0 — 云图可视化使用指南

## 概述

**VTK 云图可视化组件** (`VTK Cloud Map`) 是 CityLBM v1.0 的新增功能，支持将 FluidX3D 模拟结果以彩色云图形式展示。

---

## 组件位置

在 Grasshopper 中找到：
```
CityLBM → Results → VTK Cloud Map
```

---

## 输入参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| **Points** | Point list | 网格点坐标 | - |
| **Velocity** | Vector list | 速度向量（可选） | - |
| **Scalar Field** | Number list | 标量场数据（压力/温度等） | - |
| **Mode** | Integer | 显示模式 (0-3) | 0 |
| **Grid Size** | Number | 网格尺寸（用于切片模式） | 1.0 |
| **Contour Count** | Integer | 等值线数量 | 10 |
| **Color Low** | Color | 低值颜色 | Blue |
| **Color High** | Color | 高值颜色 | Red |
| **Use Gradient** | Boolean | 使用彩虹渐变 | True |

---

## 显示模式详解

### Mode 0: 点云着色 (默认)

**用途**: 快速查看整个计算域的标量分布

**特点**:
- 每个网格点显示为小方块
- 根据值大小着色
- 适合全域概览

**示例代码**:
```
Mode = 0
Grid Size = 忽略
```

**适用场景**: 快速检查模拟结果完整性

---

### Mode 1: 网格切片

**用途**: 在指定平面或规则网格上显示标量分布

**特点**:
- 生成结构化网格
- 网格面根据值着色
- 适合创建等值面

**参数**:
- `Grid Size`: 网格间距（建议与计算网格间距相同或更大）

**示例代码**:
```
Mode = 1
Grid Size = 2.0  # 每隔 2 米采样一个网格点
```

**适用场景**: 
- 生成等温线/等压线
- 创建可视化切片

---

### Mode 2: 等值线

**用途**: 提取特定值的等值线

**特点**:
- 自动生成多条等值线
- 每条线代表一个值级别
- 可用于轮廓分析

**参数**:
- `Contour Count`: 等值线数量

**示例代码**:
```
Mode = 2
Contour Count = 15  # 生成 15 条等值线
```

**适用场景**:
- 分析风速等级分布
- 确定舒适度区域

---

### Mode 3: 流线

**用途**: 显示流体运动轨迹

**特点**:
- 基于速度向量追踪
- 流线颜色表示流速大小
- 展现流动方向

**参数**:
- `Velocity`: 必需输入速度向量
- `Scalar Field`: 用于着色（通常为速度大小）

**示例代码**:
```
Mode = 3
Velocity = <连接从 Read VTK 的速度输出>
Scalar Field = <连接速度大小或其他标量>
```

**适用场景**:
- 风流可视化
- 涡流识别

---

## 输出参数

| 参数 | 类型 | 说明 |
|------|------|------|
| **Mesh** | Mesh | 可视化网格（可直接在 Rhino 显示） |
| **Colors** | Color list | 每个顶点的颜色 |
| **Contours** | Curve list | 等值线（仅 Mode 2） |
| **Min Value** | Number | 标量最小值 |
| **Max Value** | Number | 标量最大值 |
| **Legend** | Text | 图例信息（包括值范围和颜色映射） |

---

## 完整工作流示例

### Step 1: 读取 VTK 结果

```
Read VTK
├─ VTK Path: C:\Temp\CityLBM\MyScene\output
├─ Time Step: -1 (读取所有)
└─ 输出:
   ├─ Points: 网格点
   ├─ Velocity: 速度向量
   └─ Pressure: 压力值
```

### Step 2: 创建云图

```
VTK Cloud Map
├─ Points: <连接 Read VTK 的 Points>
├─ Velocity: <连接 Read VTK 的 Velocity>
├─ Scalar Field: <连接压力值 或 计算速度大小>
├─ Mode: 1 (网格切片)
├─ Grid Size: 2.0
├─ Color Low: Blue
├─ Color High: Red
└─ 输出:
   ├─ Mesh: 可视化网格
   ├─ Colors: 顶点颜色
   └─ Legend: 图例
```

### Step 3: 显示结果

**方式 A: 直接在 Rhino 中显示**
```
将 Mesh 输出连接到 GH Canvas，Rhino 会自动渲染
```

**方式 B: 使用 Custom Display 组件**
```
- 连接 Mesh 到 Display 组件
- 设置颜色为 Colors 输出
- 在 Rhino 中即时显示
```

**方式 C: 导出为 3D 模型**
```
- Mesh 输出连接到 Bake 组件
- 在 Rhino 中烘焙为实际对象
- 可导出为 3DM / STEP / STL
```

---

## 颜色映射说明

### Use Gradient = True (推荐)

使用 **彩虹渐变**（自动忽略 Color Low/High）:
```
  蓝 → 青 → 绿 → 黄 → 红
 最小  ↓   ↓   ↓   ↓  最大
```

**优点**:
- 直观的值分布识别
- 符合物理上的温度色带习惯

### Use Gradient = False

使用 **自定义线性插值**:
```
Color Low ──────────────── Color High
  最小值                        最大值
```

**优点**:
- 自定义颜色
- 适合印刷/报告

---

## 实用技巧

### 1. 隐藏不感兴趣的值

在 Read VTK 和 Cloud Map 之间插入过滤组件：

```
Read VTK
  ↓
Filter (Cull)
  ├─ 移除无效点
  ├─ 移除超出范围值
  ↓
VTK Cloud Map
```

### 2. 组合多个标量场

```
# 计算多个标量的混合结果
Velocity Magnitude = sqrt(Vx² + Vy² + Vz²)
Pressure Ratio = (P - P_min) / (P_max - P_min)
Scalar Field = Velocity Magnitude * Pressure Ratio
  ↓
VTK Cloud Map
```

### 3. 生成高质量渲染

```
VTK Cloud Map (Mode 1, 细网格)
  ↓
Mesh → Display
  ├─ 启用阴影
  ├─ 设置光源
  ├─ 调整材质反射率
  ↓
screenshot / 导出
```

---

## 常见问题

### Q: 为什么没有看到颜色？
**A**: 
1. 检查 `Scalar Field` 输入是否连接
2. 检查 `Use Gradient` 是否为 True
3. 查看 `Legend` 输出检查值范围

### Q: Mode 2 (等值线) 没有输出曲线？
**A**: 当前版本的等值线功能为简化实现。完整版本可在 v1.1 中获得。

### Q: 如何调整点云的大小？
**A**: 在 Mode 0 中，点大小由组件自动计算。可通过调整 Grid Size 间接控制采样密度。

### Q: Mesh 太大导致 Rhino 卡顿？
**A**: 
1. 增大 Grid Size 减少网格面数
2. 使用 Mode 0 (点云) 代替 Mode 1
3. 使用 Mesh Simplify 组件简化网格

---

## 颜色科学知识

### 风速感知的最佳颜色方案

| 颜色 | 风速等级 | 体感 |
|------|---------|------|
| 蓝色 | < 2 m/s | 舒适 |
| 绿色 | 2-4 m/s | 较舒适 |
| 黄色 | 4-6 m/s | 不舒适 |
| 橙色 | 6-8 m/s | 不适宜 |
| 红色 | > 8 m/s | 危险 |

**彩虹渐变完美对应这一规律！**

---

## v1.1 计划增强

- [ ] Marching Squares 等值线算法
- [ ] 体积渲染支持
- [ ] 等值面（3D）生成
- [ ] 动画导出（时间序列）
- [ ] 自定义 LUT (Look-Up Table)

---

**下一步**: 打开 Rhino 并在 Grasshopper 中测试新组件！

🌬️ **祝风环境分析顺利！**
