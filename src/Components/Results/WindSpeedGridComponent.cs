using System;
using System.Drawing;
using System.Collections.Generic;
using System.Linq;
using Grasshopper.Kernel;
using Rhino.Geometry;
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 风速栅格可视化组件
    /// 将切片点云按照网格分辨率划分为均匀栅格，
    /// 每个栅格格子中间显示该格子内平均风速（黑色文字）。
    /// 每个格子按风速大小填充颜色。
    /// </summary>
    public class WindSpeedGridComponent : GH_Component
    {
        // ── 渲染缓存 ──────────────────────────────────────────────
        private List<WindGridCell> _cells = new List<WindGridCell>();
        private double _minSpeed, _maxSpeed;
        private int _decimals = 2;   // 速度数字小数位

        // 格子信息
        private struct WindGridCell
        {
            public Point3d Center;      // 格子中心（世界坐标）
            public double Speed;        // 平均风速
            public Color FillColor;     // 填充颜色
            public string Label;        // 速度文字
        }

        public WindSpeedGridComponent()
            : base("Wind Speed Grid", "WSGrid",
                   "将 VTK 切片结果可视化为风速栅格，\n每个格子中间显示黑色风速数值。",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt",
                "切片点坐标（来自 Velocity Slice 或 Vertical Slice 的 Slice Points 输出）",
                GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V",
                "切片速度向量（来自 Slice Velocity 输出）",
                GH_ParamAccess.list);
            pManager.AddNumberParameter("Cell Size", "CS",
                "栅格格子边长（m）。设为 0 则自动估算。",
                GH_ParamAccess.item, 0.0);
            pManager.AddColourParameter("Color Low", "CL",
                "低速填充颜色", GH_ParamAccess.item, Color.FromArgb(180, 0, 0, 255));
            pManager.AddColourParameter("Color High", "CH",
                "高速填充颜色", GH_ParamAccess.item, Color.FromArgb(180, 255, 0, 0));
            pManager.AddIntegerParameter("Decimals", "Dec",
                "速度数字小数位数（默认 2）",
                GH_ParamAccess.item, 2);
            pManager.AddBooleanParameter("Show Grid", "SG",
                "是否显示栅格边框线（默认开）",
                GH_ParamAccess.item, true);
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddMeshParameter("Grid Mesh", "Mesh",
                "风速栅格彩色网格（可直接显示）", GH_ParamAccess.item);
            pManager.AddTextParameter("Cell Labels", "Labels",
                "每个格子的速度标签（用于调试）", GH_ParamAccess.list);
            pManager.AddPointParameter("Label Points", "LPts",
                "每个格子中心点（对应 Cell Labels）", GH_ParamAccess.list);
            pManager.AddNumberParameter("Min Speed", "Min",
                "切片内最小风速（m/s）", GH_ParamAccess.item);
            pManager.AddNumberParameter("Max Speed", "Max",
                "切片内最大风速（m/s）", GH_ParamAccess.item);
            pManager.AddTextParameter("Info", "I",
                "栅格统计信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            var points = new List<Point3d>();
            var velocities = new List<Vector3d>();
            double cellSize = 0.0;
            Color colorLow = Color.FromArgb(180, 0, 0, 255);
            Color colorHigh = Color.FromArgb(180, 255, 0, 0);
            int decimals = 2;
            bool showGrid = true;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetData(2, ref cellSize);
            DA.GetData(3, ref colorLow);
            DA.GetData(4, ref colorHigh);
            DA.GetData(5, ref decimals);
            DA.GetData(6, ref showGrid);

            if (points.Count == 0 || velocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "没有输入数据");
                return;
            }
            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "点数与速度数不匹配");
                return;
            }

            _decimals = Math.Max(0, Math.Min(4, decimals));

            // ── 自动估算格子大小 ─────────────────────────────────
            if (cellSize <= 0)
                cellSize = EstimateGridSpacing(points) * 1.01; // 略大于点间距以填满

            // ── 推断切面方向（平面法向量） ───────────────────────
            // 计算点云在 XY / XZ / YZ 三个投影面上的方差，方差最小的维度是法向量方向
            BoundingBox bbox = new BoundingBox(points);
            double rangeX = bbox.Max.X - bbox.Min.X;
            double rangeY = bbox.Max.Y - bbox.Min.Y;
            double rangeZ = bbox.Max.Z - bbox.Min.Z;

            // 法向量方向 = 变化最小的轴
            Vector3d normal;
            Vector3d axisU, axisV;
            if (rangeZ <= rangeX && rangeZ <= rangeY)
            {
                // 水平切片：法向 Z
                normal = Vector3d.ZAxis;
                axisU = Vector3d.XAxis;
                axisV = Vector3d.YAxis;
            }
            else if (rangeY <= rangeX)
            {
                // Y=常数的竖直切片：法向 Y
                normal = Vector3d.YAxis;
                axisU = Vector3d.XAxis;
                axisV = Vector3d.ZAxis;
            }
            else
            {
                // X=常数的竖直切片：法向 X
                normal = Vector3d.XAxis;
                axisU = Vector3d.YAxis;
                axisV = Vector3d.ZAxis;
            }

            // 切面原点（用点云中心）
            Point3d origin = bbox.Center;

            // ── 构建栅格索引 ─────────────────────────────────────
            // key = (gu, gv)，value = 累积速度大小 + 计数
            var gridAcc = new Dictionary<(int, int), (double sumSpeed, int count, Point3d repPt)>();

            foreach (var pair in points.Zip(velocities, (p, v) => (p, v)))
            {
                Point3d pt = pair.p;
                Vector3d vel = pair.v;
                double speed = vel.Length;

                // 投影到切面局部坐标
                Vector3d delta = pt - origin;
                double u = delta * axisU;
                double v2 = delta * axisV;

                int gu = (int)Math.Floor(u / cellSize);
                int gv = (int)Math.Floor(v2 / cellSize);
                var key = (gu, gv);

                if (gridAcc.TryGetValue(key, out var acc))
                    gridAcc[key] = (acc.sumSpeed + speed, acc.count + 1, acc.repPt);
                else
                    gridAcc[key] = (speed, 1, pt);
            }

            if (gridAcc.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "栅格化结果为空");
                return;
            }

            // ── 计算速度范围 ─────────────────────────────────────
            var allSpeeds = gridAcc.Values.Select(v => v.sumSpeed / v.count).ToList();
            _minSpeed = allSpeeds.Min();
            _maxSpeed = allSpeeds.Max();
            double speedRange = _maxSpeed - _minSpeed;
            if (speedRange < 1e-10) speedRange = 1.0;

            // ── 构建输出网格 + 标签 ──────────────────────────────
            Mesh gridMesh = new Mesh();
            var labelList = new List<string>();
            var labelPts = new List<Point3d>();
            _cells = new List<WindGridCell>();

            string fmt = "F" + _decimals;

            foreach (var kv in gridAcc)
            {
                int gu = kv.Key.Item1;
                int gv = kv.Key.Item2;
                double avgSpeed = kv.Value.sumSpeed / kv.Value.count;
                double t = (avgSpeed - _minSpeed) / speedRange;
                Color fill = InterpolateColor(colorLow, colorHigh, t);

                // 格子四角（世界坐标）
                // 中心 = origin + (gu+0.5)*cellSize*axisU + (gv+0.5)*cellSize*axisV
                double uCenter = (gu + 0.5) * cellSize;
                double vCenter = (gv + 0.5) * cellSize;
                Point3d cellCenter = origin
                    + axisU * uCenter
                    + axisV * vCenter;

                // 四个角点
                Point3d p00 = origin + axisU * (gu * cellSize)       + axisV * (gv * cellSize);
                Point3d p10 = origin + axisU * ((gu + 1) * cellSize) + axisV * (gv * cellSize);
                Point3d p11 = origin + axisU * ((gu + 1) * cellSize) + axisV * ((gv + 1) * cellSize);
                Point3d p01 = origin + axisU * (gu * cellSize)       + axisV * ((gv + 1) * cellSize);

                int vi = gridMesh.Vertices.Count;
                gridMesh.Vertices.Add(p00);
                gridMesh.Vertices.Add(p10);
                gridMesh.Vertices.Add(p11);
                gridMesh.Vertices.Add(p01);
                gridMesh.Faces.AddFace(vi, vi + 1, vi + 2, vi + 3);

                // 顶点着色（全部用格子颜色）
                gridMesh.VertexColors.SetColor(vi,     fill);
                gridMesh.VertexColors.SetColor(vi + 1, fill);
                gridMesh.VertexColors.SetColor(vi + 2, fill);
                gridMesh.VertexColors.SetColor(vi + 3, fill);

                // 标签
                string label = avgSpeed.ToString(fmt);
                labelList.Add(label);
                labelPts.Add(cellCenter);

                // 保存到缓存（用于 DrawViewportWires 显示文字）
                _cells.Add(new WindGridCell
                {
                    Center = cellCenter,
                    Speed = avgSpeed,
                    FillColor = fill,
                    Label = label
                });
            }

            gridMesh.Normals.ComputeNormals();
            gridMesh.Compact();

            string info = $"风速栅格统计\n" +
                          $"  格子边长: {cellSize:F2} m\n" +
                          $"  格子数量: {_cells.Count}\n" +
                          $"  速度范围: {_minSpeed.ToString(fmt)} ~ {_maxSpeed.ToString(fmt)} m/s\n" +
                          $"  切面法向: ({normal.X:F1},{normal.Y:F1},{normal.Z:F1})";

            DA.SetData(0, gridMesh);
            DA.SetDataList(1, labelList);
            DA.SetDataList(2, labelPts);
            DA.SetData(3, _minSpeed);
            DA.SetData(4, _maxSpeed);
            DA.SetData(5, info);
        }

        // ── 视口文字绘制 ─────────────────────────────────────────
        // DrawViewportWires 在每次视口刷新时被调用，在格子中心叠加黑色文字
        public override void DrawViewportWires(IGH_PreviewArgs args)
        {
            base.DrawViewportWires(args);

            if (_cells == null || _cells.Count == 0) return;

            foreach (var cell in _cells)
            {
                // 用黑色文字显示速度（DrawDot：背景透明，文字黑色）
                args.Display.DrawDot(cell.Center, cell.Label,
                    Color.Transparent,
                    Color.Black);
            }
        }

        // ── 辅助方法 ─────────────────────────────────────────────
        private double EstimateGridSpacing(List<Point3d> points)
        {
            if (points.Count < 2) return 1.0;
            BoundingBox bbox = new BoundingBox(points);
            double dx = bbox.Max.X - bbox.Min.X;
            double dy = bbox.Max.Y - bbox.Min.Y;
            double dz = bbox.Max.Z - bbox.Min.Z;
            double area = Math.Max(dx * dy, Math.Max(dx * dz, dy * dz));
            if (area < 1e-10) area = dx + dy + dz;
            return Math.Max(0.1, Math.Sqrt(area / points.Count));
        }

        private Color InterpolateColor(Color c1, Color c2, double t)
        {
            t = Math.Max(0, Math.Min(1, t));
            int r = (int)(c1.R + t * (c2.R - c1.R));
            int g = (int)(c1.G + t * (c2.G - c1.G));
            int b = (int)(c1.B + t * (c2.B - c1.B));
            int a = (int)(c1.A + t * (c2.A - c1.A));
            return Color.FromArgb(
                Math.Max(0, Math.Min(255, a)),
                Math.Max(0, Math.Min(255, r)),
                Math.Max(0, Math.Min(255, g)),
                Math.Max(0, Math.Min(255, b)));
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("WindSpeedGrid.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("B2C3D4E5-F6A7-8901-BCDE-F12345678901"); }
        }
    }
}
