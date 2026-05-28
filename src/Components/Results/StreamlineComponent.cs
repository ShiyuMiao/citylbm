using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Threading.Tasks;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Types;
using Rhino.Geometry;
using CityLBM.Rendering;
using CityLBM.Utils;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 风场流线组件 - 优化版
    /// 默认显示三维风场流线，风速大的地方流线更长
    /// 输入直接与 ReadVTK 输出端相连
    /// </summary>
    public class StreamlineComponent : GH_Component
    {
        private WindFieldConduit _conduit;
        private bool _conduitEnabled = false;
        private Task<List<Polyline>> _traceTask;
        private List<double> _cachedSpeeds;

        // 缓存数据用于自动种子点生成
        private List<Point3d> _cachedPoints;
        private List<Vector3d> _cachedVelocities;
        private BoundingBox _cachedBounds;

        public StreamlineComponent()
            : base("Wind Streamlines", "Streamlines",
                   "三维风场流线可视化 - 风速大的地方流线更长。输入直接连接 ReadVTK 的 Points 和 Velocity",
                   "CityLBM", "Results")
        {
        }

        public override Guid ComponentGuid => new Guid("A7B3C9D2-E5F1-4A8B-9C6D-2E4F8A1B5C3D");

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            // 主要输入 - 直接来自 ReadVTK
            pManager.AddPointParameter("Points", "Pt", "速度场网格点坐标（来自 Read VTK 的 Points 输出）", GH_ParamAccess.list);
            pManager.AddVectorParameter("Velocity", "V", "速度向量（来自 Read VTK 的 Velocity 输出）", GH_ParamAccess.list);
            
            // 可选参数
            pManager.AddPointParameter("Seed Points", "Seeds", "自定义流线播种点（可选，默认在入口生成）", GH_ParamAccess.list);
            pManager.AddIntegerParameter("Seed Count", "N", "流线数量（默认 50 条）", GH_ParamAccess.item, 50);
            pManager.AddNumberParameter("Step Size", "H", "积分步长（m，默认 2.0）", GH_ParamAccess.item, 2.0);
            pManager.AddIntegerParameter("Max Steps", "Max", "最大积分步数（默认 1000，保证流线从入口到出口）", GH_ParamAccess.item, 1000);
            pManager.AddNumberParameter("Min Speed", "Min", "最小速度阈值（低于此值停止追踪，默认 0.05）", GH_ParamAccess.item, 0.05);
            pManager.AddNumberParameter("Line Width", "W", "流线线宽（默认 2.0）", GH_ParamAccess.item, 2.0);
            pManager.AddBooleanParameter("Show", "Show", "是否显示流线（默认 true）", GH_ParamAccess.item, true);
            pManager.AddBooleanParameter("Use Adaptive", "Adapt", "使用自适应步长（风速大时步长更大，默认 true）", GH_ParamAccess.item, true);
            pManager.AddIntegerParameter("Seed Mode", "Mode", "种子点生成模式：0=入口边界（默认）, 1=全域均匀, 2=高风速区域", GH_ParamAccess.item, 0);

            // 设置可选参数
            pManager[2].Optional = true; // Seeds
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddCurveParameter("Streamlines", "SL", "流线曲线", GH_ParamAccess.list);
            pManager.AddNumberParameter("Speeds", "Spd", "每条流线的平均速度", GH_ParamAccess.list);
            pManager.AddTextParameter("Info", "Info", "流线统计信息", GH_ParamAccess.item);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // ── 输入参数 ───────────────────────────────────────────────
            List<Point3d> points = new List<Point3d>();
            List<Vector3d> velocities = new List<Vector3d>();
            List<Point3d> customSeeds = new List<Point3d>();
            int seedCount = 50;
            double stepSize = 2.0;
            int maxSteps = 1000;
            double minSpeed = 0.05;
            double lineWidth = 2.0;
            bool show = true;
            bool useAdaptive = true;
            int seedMode = 0;

            if (!DA.GetDataList(0, points)) return;
            if (!DA.GetDataList(1, velocities)) return;
            DA.GetDataList(2, customSeeds);
            DA.GetData(3, ref seedCount);
            DA.GetData(4, ref stepSize);
            DA.GetData(5, ref maxSteps);
            DA.GetData(6, ref minSpeed);
            DA.GetData(7, ref lineWidth);
            DA.GetData(8, ref show);
            DA.GetData(9, ref useAdaptive);
            DA.GetData(10, ref seedMode);

            // 参数校验
            if (points.Count != velocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Points 和 Velocity 数量不匹配");
                return;
            }
            if (points.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "没有输入数据，请连接 ReadVTK 的输出");
                return;
            }

            // 缓存数据
            _cachedPoints = points;
            _cachedVelocities = velocities;
            _cachedBounds = new BoundingBox(points);

            // ── Conduit 生命周期管理 ────────────────────────────────────
            EnsureConduit();

            if (!show)
            {
                _conduit.Clear();
                _conduit.Enabled = false;
                _conduitEnabled = false;
                DA.SetData(2, "流线显示已关闭");
                return;
            }

            if (!_conduitEnabled)
            {
                _conduit.Enabled = true;
                _conduitEnabled = true;
            }

            // 更新 Conduit 可视化参数
            _conduit.LineWidth = (float)lineWidth;

            // ── 生成种子点 ──────────────────────────────────────────────
            List<Point3d> seeds;
            if (customSeeds != null && customSeeds.Count > 0)
            {
                seeds = customSeeds;
            }
            else
            {
                // 根据模式自动生成种子点
                seeds = GenerateSeedsByMode(points, velocities, seedCount, _cachedBounds, seedMode);
            }

            if (seeds.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "未能生成有效的播种点");
                return;
            }

            // ── 后台计算流线 ────────────────────────────────────────────
            if (_traceTask == null || _traceTask.IsCompleted)
            {
                var bounds = _cachedBounds;
                bounds.Inflate(1.0);

                _traceTask = Task.Run(() =>
                {
                    return StreamlineTracer.TraceAdaptive(
                        seeds, points, velocities,
                        stepSize, maxSteps, bounds, minSpeed, useAdaptive);
                });

                _traceTask.ContinueWith(t =>
                {
                    if (!t.IsFaulted && t.Result != null)
                    {
                        _cachedSpeeds = StreamlineTracer.ComputeAverageSpeeds(
                            t.Result, points, velocities);

                        Rhino.RhinoApp.InvokeOnUiThread((Action)(() =>
                        {
                            _conduit.SetStreamlines(t.Result, _cachedSpeeds);
                            Rhino.RhinoDoc.ActiveDoc?.Views.Redraw();
                        }));
                    }
                });

                AddRuntimeMessage(GH_RuntimeMessageLevel.Remark, $"⏳ 正在计算 {seeds.Count} 条流线...");
            }

            // ── 输出 ────────────────────────────────────────────────────
            List<Polyline> streamlines = null;
            if (_traceTask.IsCompleted && !_traceTask.IsFaulted)
            {
                streamlines = _traceTask.Result;
            }

            if (streamlines != null)
            {
                var curves = streamlines.Select(pl => (Curve)pl.ToNurbsCurve()).ToList();
                DA.SetDataList(0, curves);

                if (_cachedSpeeds != null)
                    DA.SetDataList(1, _cachedSpeeds);

                double avgLen = streamlines.Average(pl => pl.Length);
                double maxLen = streamlines.Max(pl => pl.Length);
                double avgSpeed = _cachedSpeeds?.Average() ?? 0;
                
                string[] modeNames = { "入口边界", "全域均匀", "高风速区" };
                string modeName = modeNames[Math.Min(seedMode, 2)];
                
                DA.SetData(2, $"流线: {streamlines.Count} | 模式: {modeName} | 平均长度: {avgLen:F1}m | 最大长度: {maxLen:F1}m | 平均风速: {avgSpeed:F2}m/s");
            }
            else
            {
                DA.SetData(2, "计算中...");
            }
        }

        /// <summary>
        /// 根据模式生成种子点
        /// Mode 0: 入口边界 - 在来风方向的边界生成种子，展示风从入口到出口的流动
        /// Mode 1: 全域均匀 - 在整个计算域均匀分布
        /// Mode 2: 高风速区域 - 在速度大的区域生成更多种子
        /// </summary>
        private List<Point3d> GenerateSeedsByMode(
            List<Point3d> points, 
            List<Vector3d> velocities, 
            int targetCount,
            BoundingBox bounds,
            int mode)
        {
            switch (mode)
            {
                case 0:
                    return GenerateInletSeeds(points, velocities, targetCount, bounds);
                case 1:
                    return GenerateUniformSeeds(points, velocities, targetCount, bounds);
                case 2:
                    return GenerateHighSpeedSeeds(points, velocities, targetCount, bounds);
                default:
                    return GenerateInletSeeds(points, velocities, targetCount, bounds);
            }
        }

        /// <summary>
        /// 在入口边界生成种子点 - 自动检测来风方向
        /// </summary>
        private List<Point3d> GenerateInletSeeds(
            List<Point3d> points, 
            List<Vector3d> velocities, 
            int targetCount,
            BoundingBox bounds)
        {
            var seeds = new List<Point3d>();
            
            // 1. 分析整体风向，确定入口边界
            Vector3d avgWind = new Vector3d(0, 0, 0);
            foreach (var v in velocities)
                avgWind += v;
            avgWind /= velocities.Count;
            avgWind.Unitize();
            
            // 2. 确定入口边界 - 风向的反方向
            double absX = Math.Abs(avgWind.X);
            double absY = Math.Abs(avgWind.Y);
            
            bool inletIsX = absX >= absY;
            bool inletIsMin = inletIsX ? (avgWind.X > 0) : (avgWind.Y > 0);
            
            // 3. 在入口边界附近筛选点
            double tolerance = 0.1;
            var inletPoints = new List<Point3d>();
            
            if (inletIsX)
            {
                double inletX = inletIsMin ? bounds.Min.X : bounds.Max.X;
                inletPoints = points.Where((p, i) => 
                    Math.Abs(p.X - inletX) < tolerance && velocities[i].Length > 0.01)
                    .ToList();
            }
            else
            {
                double inletY = inletIsMin ? bounds.Min.Y : bounds.Max.Y;
                inletPoints = points.Where((p, i) => 
                    Math.Abs(p.Y - inletY) < tolerance && velocities[i].Length > 0.01)
                    .ToList();
            }
            
            // 4. 如果边界点不够，扩展到边界附近区域
            if (inletPoints.Count < targetCount)
            {
                tolerance = bounds.Diagonal.Length * 0.1;
                if (inletIsX)
                {
                    double inletX = inletIsMin ? bounds.Min.X : bounds.Max.X;
                    inletPoints = points.Where((p, i) => 
                        Math.Abs(p.X - inletX) < tolerance && velocities[i].Length > 0.01)
                        .ToList();
                }
                else
                {
                    double inletY = inletIsMin ? bounds.Min.Y : bounds.Max.Y;
                    inletPoints = points.Where((p, i) => 
                        Math.Abs(p.Y - inletY) < tolerance && velocities[i].Length > 0.01)
                        .ToList();
                }
            }
            
            // 5. 空间均匀采样
            if (inletPoints.Count > 0)
            {
                double cellSize = Math.Pow(bounds.Volume / points.Count, 1.0 / 3.0) * 2.0;
                var usedCells = new HashSet<long>();
                var random = new Random(42);
                
                inletPoints = inletPoints.OrderBy(x => random.Next()).ToList();
                
                foreach (var pt in inletPoints)
                {
                    if (seeds.Count >= targetCount) break;
                    
                    long cellHash = GetCellHash(pt, cellSize);
                    if (!usedCells.Contains(cellHash))
                    {
                        seeds.Add(pt);
                        usedCells.Add(cellHash);
                    }
                }
            }
            
            // 6. 如果种子不够，补充全域点
            if (seeds.Count < targetCount)
            {
                var additional = GenerateUniformSeeds(points, velocities, targetCount - seeds.Count, bounds);
                seeds.AddRange(additional.Take(targetCount - seeds.Count));
            }
            
            return seeds;
        }

        /// <summary>
        /// 全域均匀生成种子点
        /// </summary>
        private List<Point3d> GenerateUniformSeeds(
            List<Point3d> points, 
            List<Vector3d> velocities, 
            int targetCount,
            BoundingBox bounds)
        {
            var seeds = new List<Point3d>();
            double cellSize = Math.Pow(bounds.Volume / points.Count, 1.0 / 3.0) * 2.0;
            var usedCells = new HashSet<long>();
            var random = new Random(42);
            
            var indices = Enumerable.Range(0, points.Count).OrderBy(x => random.Next()).ToList();
            
            foreach (int idx in indices)
            {
                if (seeds.Count >= targetCount) break;
                if (velocities[idx].Length < 0.01) continue;
                
                var pt = points[idx];
                long cellHash = GetCellHash(pt, cellSize);
                
                if (!usedCells.Contains(cellHash))
                {
                    seeds.Add(pt);
                    usedCells.Add(cellHash);
                }
            }
            
            return seeds;
        }

        /// <summary>
        /// 在高风速区域生成种子点
        /// </summary>
        private List<Point3d> GenerateHighSpeedSeeds(
            List<Point3d> points, 
            List<Vector3d> velocities, 
            int targetCount,
            BoundingBox bounds)
        {
            var seeds = new List<Point3d>();
            var speeds = velocities.Select(v => v.Length).ToList();
            
            // 按速度排序，取前 30% 的点作为候选
            var indexedSpeeds = speeds.Select((s, i) => new { Speed = s, Index = i })
                                      .OrderByDescending(x => x.Speed)
                                      .ToList();
            
            int candidateCount = Math.Min(indexedSpeeds.Count, targetCount * 3);
            var candidates = indexedSpeeds.Take(candidateCount).ToList();
            
            double cellSize = Math.Pow(bounds.Volume / points.Count, 1.0 / 3.0) * 3.0;
            var usedCells = new HashSet<long>();
            
            foreach (var candidate in candidates)
            {
                if (seeds.Count >= targetCount) break;
                
                var pt = points[candidate.Index];
                long cellHash = GetCellHash(pt, cellSize);
                
                if (!usedCells.Contains(cellHash))
                {
                    seeds.Add(pt);
                    usedCells.Add(cellHash);
                }
            }
            
            return seeds;
        }

        private long GetCellHash(Point3d p, double cellSize)
        {
            long ix = (long)(p.X / cellSize);
            long iy = (long)(p.Y / cellSize);
            long iz = (long)(p.Z / cellSize);
            return (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791);
        }

        private void EnsureConduit()
        {
            if (_conduit == null)
            {
                _conduit = new WindFieldConduit();
            }
        }

        public override void RemovedFromDocument(GH_Document document)
        {
            DisableConduit();
            base.RemovedFromDocument(document);
        }

        public override void DocumentContextChanged(GH_Document document, GH_DocumentContext context)
        {
            if (context == GH_DocumentContext.Close ||
                context == GH_DocumentContext.Unloaded)
            {
                DisableConduit();
            }
            base.DocumentContextChanged(document, context);
        }

        private void DisableConduit()
        {
            if (_conduit != null)
            {
                _conduit.Enabled = false;
                _conduit.Clear();
                _conduit = null;
                _conduitEnabled = false;
            }
        }

        protected override Bitmap Icon => IconLoader.Load("Streamlines.png");
    }
}
