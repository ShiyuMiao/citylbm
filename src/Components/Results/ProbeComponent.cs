using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using Grasshopper.Kernel;
using Rhino.Geometry;
using CityLBM.Rendering;
using CityLBM.Utils;
using CityLBM.Core;

namespace CityLBM.Components.Results
{
    /// <summary>
    /// 三维交互式数据探针组件
    /// 在模型中实时测量风速和压力，支持拖拽实时更新
    /// </summary>
    public class ProbeComponent : GH_Component
    {
        private ProbeConduit _conduit;
        private bool _conduitEnabled = false;

        // 缓存的数据
        private List<Point3d> _fieldPoints = new List<Point3d>();
        private List<Vector3d> _fieldVelocities = new List<Vector3d>();
        private List<double> _fieldPressures = new List<double>();
        private VelocityField _velocityField;
        private bool _dataValid = false;

        // 探针位置缓存（用于检测变化）
        private List<Point3d> _lastProbePositions = new List<Point3d>();
        private Vector3d _lastWindDirection = Vector3d.Unset;
        private double _lastUref = double.NaN;
        private string _lastProbeIdKey = null;
        private string _lastComparedComponent = null;
        private double _lastProbeTolerance = double.NaN;
        private bool _forceUpdate = true;

        public ProbeComponent()
            : base("Data Probe", "Probe",
                   "三维交互式数据探针：在模型中实时测量风速和压力。\n" +
                   "支持在 Rhino 中拖动探针点，悬浮文字实时更新（60fps）。\n" +
                   "使用空间哈希加速最近邻搜索。",
                   "CityLBM", "Results")
        {
        }

        protected override void RegisterInputParams(GH_Component.GH_InputParamManager pManager)
        {
            pManager.AddPointParameter("Points", "Pt",
                "速度场点坐标（来自 Read VTK 组件的 Points 输出）。",
                GH_ParamAccess.list);

            pManager.AddVectorParameter("Velocity", "V",
                "速度向量（来自 Read VTK 组件的 Velocity 输出）。",
                GH_ParamAccess.list);

            pManager.AddPointParameter("Probe Points", "P",
                "探针位置点。支持多个探针点。可在 Rhino 中拖动这些点实时更新测量值。",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Pressure", "Pr",
                "压力值（来自 Read VTK 组件的 Pressure 输出，可选）。",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Search Radius", "R",
                "搜索半径（米）。用于最近邻搜索，默认自动计算。",
                GH_ParamAccess.item, 0.0);

            pManager.AddBooleanParameter("Show Vectors", "SV",
                "是否显示速度向量箭头。",
                GH_ParamAccess.item, true);

            pManager.AddBooleanParameter("Enable Preview", "E",
                "是否启用视口预览。",
                GH_ParamAccess.item, true);

            pManager.AddVectorParameter("Wind Direction", "WD",
                "来流风向量（可选）。用于显示风向参考，帮助理解速度方向与来流的关系。",
                GH_ParamAccess.item);

            // 可选参数
            pManager.AddNumberParameter("Uref", "Uref",
                "Reference velocity for validation ratios. Used for probe post-processing only; it does not replace the inlet profile.",
                GH_ParamAccess.item, 0.0);

            pManager.AddTextParameter("Probe IDs", "IDs",
                "Optional official measurement point IDs. Used only in validation audit rows.",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Tolerance", "Tol",
                "Optional probe-to-VTK nearest sample tolerance in model units. Values > 0 flag out-of-tolerance probes.",
                GH_ParamAccess.item, 0.0);

            pManager.AddTextParameter("Compared Component", "Comp",
                "Validation component written to the audit table: speed_ratio, streamwise_ratio, speed, streamwise, x, y or z.",
                GH_ParamAccess.item, "speed_ratio");

            pManager[3].Optional = true;
            pManager[4].Optional = true;
            pManager[7].Optional = true;
            pManager[8].Optional = true;
            pManager[9].Optional = true;
            pManager[10].Optional = true;
            pManager[11].Optional = true;
        }

        protected override void RegisterOutputParams(GH_Component.GH_OutputParamManager pManager)
        {
            pManager.AddTextParameter("Probe Info", "Info",
                "探针测量结果摘要。",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Speed", "V",
                "各探针点的风速大小 (m/s)。",
                GH_ParamAccess.list);

            pManager.AddVectorParameter("Velocity", "Vel",
                "各探针点的速度向量 (m/s)。",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Pressure", "P",
                "各探针点的压力值 (Pa)。",
                GH_ParamAccess.list);

            pManager.AddPointParameter("Probe Position", "Pos",
                "探针实际位置（与输入对应）。",
                GH_ParamAccess.list);
            pManager.AddNumberParameter("Speed Ratio", "VR",
                "Speed magnitude divided by Uref. Values are NaN when Uref <= 0.",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Streamwise Ratio", "SR",
                "Velocity component along Wind Direction divided by Uref. Values are NaN when Uref <= 0 or Wind Direction is missing.",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Nearest Distance", "D",
                "Distance from each probe point to the nearest VTK sample considered by the spatial hash interpolation.",
                GH_ParamAccess.list);

            pManager.AddTextParameter("Audit CSV", "CSV",
                "Per-probe audit rows for validation: coordinates, velocity components, ratios, interpolation distance and method.",
                GH_ParamAccess.list);

            pManager.AddTextParameter("Validation Status", "Status",
                "Per-probe validation status: ok, fail_no_vtk_neighbor, fail_out_of_tolerance or fail_invalid_compared_value.",
                GH_ParamAccess.list);

            pManager.AddNumberParameter("Compared Value", "CV",
                "Per-probe value for the selected Compared Component.",
                GH_ParamAccess.list);

            pManager.AddTextParameter("Probe ID", "ID",
                "Official or generated probe ID used in the audit table.",
                GH_ParamAccess.list);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            // 获取输入
            List<Point3d> fieldPoints = new List<Point3d>();
            List<Vector3d> fieldVelocities = new List<Vector3d>();
            List<Point3d> probePoints = new List<Point3d>();
            List<double> fieldPressures = new List<double>();
            double searchRadius = 0.0;
            bool showVectors = true;
            bool enablePreview = true;
            double uref = 0.0;
            List<string> probeIds = new List<string>();
            double probeTolerance = 0.0;
            string comparedComponentInput = "speed_ratio";

            if (!DA.GetDataList(0, fieldPoints) || fieldPoints.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "请连接 Points 输入");
                CleanupConduit();
                return;
            }

            if (!DA.GetDataList(1, fieldVelocities) || fieldVelocities.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "请连接 Velocity 输入");
                CleanupConduit();
                return;
            }

            if (!DA.GetDataList(2, probePoints) || probePoints.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Warning, "请至少输入一个探针点");
                CleanupConduit();
                return;
            }

            DA.GetDataList(3, fieldPressures);
            DA.GetData(4, ref searchRadius);
            DA.GetData(5, ref showVectors);
            DA.GetData(6, ref enablePreview);
            
            // 获取风向（可选）
            Vector3d windDirection = Vector3d.Zero;
            DA.GetData(7, ref windDirection);
            DA.GetData(8, ref uref);
            DA.GetDataList(9, probeIds);
            DA.GetData(10, ref probeTolerance);
            DA.GetData(11, ref comparedComponentInput);
            if (probeTolerance < 0)
            {
                probeTolerance = 0.0;
            }

            string comparedComponent = NormalizeComparedComponent(comparedComponentInput);
            bool hasWindDirection = windDirection.IsValid && windDirection.Length > 1e-9;
            if (hasWindDirection)
            {
                windDirection.Unitize();
            }
            else
            {
                windDirection = Vector3d.Zero;
            }

            // 验证数据一致性
            if (fieldPoints.Count != fieldVelocities.Count)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error,
                    $"Points ({fieldPoints.Count}) 和 Velocity ({fieldVelocities.Count}) 数量不匹配");
                return;
            }

            // 更新字段数据
            bool dataChanged = UpdateFieldData(fieldPoints, fieldVelocities, fieldPressures);

            // 检测探针位置是否变化
            bool probesMoved = HaveProbesMoved(probePoints);
            bool validationConfigChanged = HasValidationConfigChanged(
                windDirection,
                uref,
                probeIds,
                comparedComponent,
                probeTolerance);

            // 如果数据或探针位置变化，需要重新计算
            if (dataChanged || probesMoved || validationConfigChanged || _forceUpdate)
            {
                _forceUpdate = false;

                // 构建速度场加速结构（如果数据变化）
                if (dataChanged || _velocityField == null)
                {
                    if (_fieldPoints.Count > 0 && _fieldVelocities.Count > 0)
                    {
                        _velocityField = new VelocityField(_fieldPoints, _fieldVelocities);
                        _dataValid = true;
                    }
                    else
                    {
                        _dataValid = false;
                    }
                }

                // 计算搜索半径（如果未指定）
                if (searchRadius <= 0 && _dataValid)
                {
                    // 基于点密度估算
                    var bounds = new BoundingBox(_fieldPoints);
                    double volume = Math.Max(bounds.Volume, 1.0);
                    double avgSpacing = Math.Pow(volume / _fieldPoints.Count, 1.0 / 3.0);
                    searchRadius = avgSpacing * 2.0;
                }

                // 测量各探针点
                var probeResults = new List<ProbeMeasurement>();
                var conduitData = new List<ProbeConduit.ProbeData>();

                for (int i = 0; i < probePoints.Count; i++)
                {
                    var measurement = MeasureAtPoint(probePoints[i], searchRadius, i);
                    probeResults.Add(measurement);

                    // 准备 Conduit 数据
                    conduitData.Add(new ProbeConduit.ProbeData
                    {
                        Position = probePoints[i],
                        Velocity = measurement.Velocity,
                        Pressure = measurement.Pressure,
                        HasPressure = measurement.HasPressure,
                        Label = $"Probe {i + 1}",
                        WindDirection = windDirection
                    });
                }

                // 更新 Conduit
                if (enablePreview && _dataValid)
                {
                    InitializeConduit();
                    _conduit.SetProbes(conduitData);

                    if (!_conduitEnabled)
                    {
                        _conduit.Enabled = true;
                        _conduitEnabled = true;
                    }
                }
                else
                {
                    CleanupConduit();
                }

                // 输出结果
                var infoList = new List<string>();
                var speeds = new List<double>();
                var velocities = new List<Vector3d>();
                var pressures = new List<double>();
                var speedRatios = new List<double>();
                var streamwiseRatios = new List<double>();
                var nearestDistances = new List<double>();
                var validationStatuses = new List<string>();
                var comparedValues = new List<double>();
                var outputProbeIds = new List<string>();
                var auditRows = new List<string>
                {
                    "probe_id,probe_index,x,y,z,u,v,w,speed,streamwise_velocity,Uref,speed_ratio,streamwise_ratio,nearest_distance,nearby_point_count,method,compared_component,compared_value,tolerance,out_of_tolerance,failed"
                };

                foreach (var result in probeResults)
                {
                    infoList.Add(result.ToString());
                    speeds.Add(result.Speed);
                    velocities.Add(result.Velocity);
                    pressures.Add(result.HasPressure ? result.Pressure : 0);
                    nearestDistances.Add(result.NearestDistance);

                    double streamwiseVelocity = double.NaN;
                    if (hasWindDirection)
                    {
                        streamwiseVelocity =
                            result.Velocity.X * windDirection.X +
                            result.Velocity.Y * windDirection.Y +
                            result.Velocity.Z * windDirection.Z;
                    }

                    double speedRatio = double.NaN;
                    double streamwiseRatio = double.NaN;
                    if (uref > 0)
                    {
                        speedRatio = result.Speed / uref;
                        if (!double.IsNaN(streamwiseVelocity))
                        {
                            streamwiseRatio = streamwiseVelocity / uref;
                        }
                    }

                    string probeId = GetProbeId(probeIds, result.Index);
                    double comparedValue = GetComparedValue(result, streamwiseVelocity, uref, comparedComponent);
                    bool outOfTolerance = probeTolerance > 0.0 &&
                        (!IsFinite(result.NearestDistance) || result.NearestDistance > probeTolerance);
                    bool failed = result.NearbyPointCount <= 0 || outOfTolerance || !IsFinite(comparedValue);
                    string validationStatus = GetValidationStatus(result, outOfTolerance, comparedValue);

                    speedRatios.Add(speedRatio);
                    streamwiseRatios.Add(streamwiseRatio);
                    validationStatuses.Add(validationStatus);
                    comparedValues.Add(comparedValue);
                    outputProbeIds.Add(probeId);
                    auditRows.Add(FormatAuditRow(
                        result,
                        probeId,
                        streamwiseVelocity,
                        uref,
                        speedRatio,
                        streamwiseRatio,
                        comparedComponent,
                        comparedValue,
                        probeTolerance,
                        outOfTolerance,
                        failed));
                }

                int failedCount = 0;
                foreach (string status in validationStatuses)
                {
                    if (!string.Equals(status, "ok", StringComparison.OrdinalIgnoreCase))
                    {
                        failedCount++;
                    }
                }

                if (failedCount > 0)
                {
                    AddRuntimeMessage(
                        GH_RuntimeMessageLevel.Warning,
                        $"{failedCount} probe(s) failed validation audit. Check VTK coverage, probe tolerance, and selected compared component.");
                }

                DA.SetDataList(0, infoList);
                DA.SetDataList(1, speeds);
                DA.SetDataList(2, velocities);
                DA.SetDataList(3, pressures);
                DA.SetDataList(4, probePoints);
                DA.SetDataList(5, speedRatios);
                DA.SetDataList(6, streamwiseRatios);
                DA.SetDataList(7, nearestDistances);
                DA.SetDataList(8, auditRows);
                DA.SetDataList(9, validationStatuses);
                DA.SetDataList(10, comparedValues);
                DA.SetDataList(11, outputProbeIds);

                // 更新缓存
                _lastProbePositions = new List<Point3d>(probePoints);
                StoreValidationConfig(windDirection, uref, probeIds, comparedComponent, probeTolerance);
            }
            else
            {
                // 数据未变化，仅刷新 Conduit
                if (enablePreview && _conduitEnabled && _conduit != null)
                {
                    // 强制重绘
                    Rhino.RhinoDoc.ActiveDoc?.Views?.Redraw();
                }
            }
        }

        /// <summary>
        /// 更新场数据
        /// </summary>
        private bool UpdateFieldData(List<Point3d> points, List<Vector3d> velocities, List<double> pressures)
        {
            bool changed = false;

            // 检查点数据是否变化
            if (_fieldPoints.Count != points.Count)
            {
                changed = true;
            }
            else
            {
                double tolerance = 1e-6;
                for (int i = 0; i < points.Count && !changed; i++)
                {
                    if (_fieldPoints[i].DistanceTo(points[i]) > tolerance)
                    {
                        changed = true;
                        break;
                    }
                }
            }

            // 检查速度数据是否变化
            if (!changed && _fieldVelocities.Count != velocities.Count)
            {
                changed = true;
            }

            // 更新数据
            _fieldPoints = new List<Point3d>(points);
            _fieldVelocities = new List<Vector3d>(velocities);
            _fieldPressures = pressures != null ? new List<double>(pressures) : new List<double>();

            return changed;
        }

        /// <summary>
        /// 检测探针位置是否变化
        /// </summary>
        private bool HaveProbesMoved(List<Point3d> currentProbes)
        {
            if (_lastProbePositions.Count != currentProbes.Count)
                return true;

            double tolerance = 0.001; // 1mm 容差
            for (int i = 0; i < currentProbes.Count; i++)
            {
                if (_lastProbePositions[i].DistanceTo(currentProbes[i]) > tolerance)
                    return true;
            }

            return false;
        }

        private bool HasValidationConfigChanged(
            Vector3d windDirection,
            double uref,
            List<string> probeIds,
            string comparedComponent,
            double probeTolerance)
        {
            string probeIdKey = string.Join("|", probeIds ?? new List<string>());

            if (!_lastWindDirection.IsValid || (_lastWindDirection - windDirection).Length > 1e-9)
                return true;
            if (Math.Abs(_lastUref - uref) > 1e-12)
                return true;
            if (!string.Equals(_lastProbeIdKey, probeIdKey, StringComparison.Ordinal))
                return true;
            if (!string.Equals(_lastComparedComponent, comparedComponent, StringComparison.OrdinalIgnoreCase))
                return true;
            if (Math.Abs(_lastProbeTolerance - probeTolerance) > 1e-12)
                return true;

            return false;
        }

        private void StoreValidationConfig(
            Vector3d windDirection,
            double uref,
            List<string> probeIds,
            string comparedComponent,
            double probeTolerance)
        {
            _lastWindDirection = windDirection;
            _lastUref = uref;
            _lastProbeIdKey = string.Join("|", probeIds ?? new List<string>());
            _lastComparedComponent = comparedComponent;
            _lastProbeTolerance = probeTolerance;
        }

        /// <summary>
        /// 在指定位置测量风场数据
        /// </summary>
        private ProbeMeasurement MeasureAtPoint(Point3d point, double searchRadius, int index)
        {
            var measurement = new ProbeMeasurement
            {
                Index = index,
                Position = point,
                Velocity = Vector3d.Zero,
                Pressure = 0,
                HasPressure = false,
                InterpolationMethod = "None"
            };

            if (!_dataValid || _velocityField == null)
            {
                measurement.InterpolationMethod = "No field data";
                return measurement;
            }

            // 使用空间哈希插值获取速度
            measurement.Velocity = _velocityField.Interpolate(point, searchRadius);
            measurement.InterpolationMethod = "IDW";
            measurement.NearestDistance = _velocityField.GetNearestDistance(point, searchRadius);
            measurement.NearbyPointCount = _velocityField.GetNearbyCount(point, searchRadius);

            // 压力插值（如果有压力数据）
            if (_fieldPressures.Count > 0 && _fieldPoints.Count > 0)
            {
                measurement.Pressure = InterpolateScalar(point, _fieldPoints, _fieldPressures);
                measurement.HasPressure = true;
            }

            return measurement;
        }

        /// <summary>
        /// 标量场 IDW 插值
        /// </summary>
        private static string FormatAuditRow(
            ProbeMeasurement result,
            string probeId,
            double streamwiseVelocity,
            double uref,
            double speedRatio,
            double streamwiseRatio,
            string comparedComponent,
            double comparedValue,
            double probeTolerance,
            bool outOfTolerance,
            bool failed)
        {
            return string.Join(",",
                EscapeCsv(probeId),
                result.Index + 1,
                FormatDouble(result.Position.X),
                FormatDouble(result.Position.Y),
                FormatDouble(result.Position.Z),
                FormatDouble(result.Velocity.X),
                FormatDouble(result.Velocity.Y),
                FormatDouble(result.Velocity.Z),
                FormatDouble(result.Speed),
                FormatDouble(streamwiseVelocity),
                FormatDouble(uref),
                FormatDouble(speedRatio),
                FormatDouble(streamwiseRatio),
                FormatDouble(result.NearestDistance),
                result.NearbyPointCount,
                EscapeCsv(result.InterpolationMethod),
                EscapeCsv(comparedComponent),
                FormatDouble(comparedValue),
                FormatDouble(probeTolerance),
                outOfTolerance ? "true" : "false",
                failed ? "true" : "false");
        }

        private static string GetProbeId(List<string> probeIds, int index)
        {
            if (probeIds != null && index >= 0 && index < probeIds.Count && !string.IsNullOrWhiteSpace(probeIds[index]))
            {
                return probeIds[index].Trim();
            }

            return (index + 1).ToString(CultureInfo.InvariantCulture);
        }

        private static string NormalizeComparedComponent(string component)
        {
            string value = (component ?? string.Empty).Trim().ToLowerInvariant();
            switch (value)
            {
                case "speed":
                case "speed_magnitude":
                case "magnitude":
                case "mag":
                    return "speed";
                case "streamwise":
                case "wind":
                case "along_wind":
                    return "streamwise";
                case "streamwise_ratio":
                case "wind_ratio":
                case "along_wind_ratio":
                    return "streamwise_ratio";
                case "x":
                case "u":
                case "u_x":
                    return "x";
                case "y":
                case "v":
                case "u_y":
                    return "y";
                case "z":
                case "w":
                case "u_z":
                    return "z";
                case "speed_ratio":
                case "ratio":
                default:
                    return "speed_ratio";
            }
        }

        private static double GetComparedValue(
            ProbeMeasurement result,
            double streamwiseVelocity,
            double uref,
            string comparedComponent)
        {
            switch (NormalizeComparedComponent(comparedComponent))
            {
                case "speed":
                    return result.Speed;
                case "streamwise":
                    return streamwiseVelocity;
                case "streamwise_ratio":
                    return uref > 0.0 && IsFinite(streamwiseVelocity) ? streamwiseVelocity / uref : double.NaN;
                case "x":
                    return result.Velocity.X;
                case "y":
                    return result.Velocity.Y;
                case "z":
                    return result.Velocity.Z;
                case "speed_ratio":
                default:
                    return uref > 0.0 ? result.Speed / uref : double.NaN;
            }
        }

        private static string GetValidationStatus(ProbeMeasurement result, bool outOfTolerance, double comparedValue)
        {
            if (result.NearbyPointCount <= 0)
                return "fail_no_vtk_neighbor";
            if (outOfTolerance)
                return "fail_out_of_tolerance";
            if (!IsFinite(comparedValue))
                return "fail_invalid_compared_value";

            return "ok";
        }

        private static bool IsFinite(double value)
        {
            return !double.IsNaN(value) && !double.IsInfinity(value);
        }

        private static string EscapeCsv(string value)
        {
            if (value == null)
                return string.Empty;

            if (value.IndexOfAny(new[] { ',', '"', '\r', '\n' }) < 0)
                return value;

            return "\"" + value.Replace("\"", "\"\"") + "\"";
        }

        private static string FormatDouble(double value)
        {
            return double.IsNaN(value) || double.IsInfinity(value)
                ? "NaN"
                : value.ToString("G17", CultureInfo.InvariantCulture);
        }

        private double InterpolateScalar(Point3d p, List<Point3d> points, List<double> values)
        {
            if (points.Count == 0) return 0;

            // 找最近的几个点进行 IDW 插值
            double weightSum = 0;
            double valueSum = 0;
            int count = 0;

            for (int i = 0; i < points.Count && count < 8; i++)
            {
                double dist = p.DistanceTo(points[i]);
                if (dist < 1e-10)
                    return values[i]; // 精确命中

                if (dist < 50.0) // 只考虑 50m 内的点
                {
                    double w = 1.0 / (dist * dist);
                    weightSum += w;
                    valueSum += values[i] * w;
                    count++;
                }
            }

            return weightSum > 0 ? valueSum / weightSum : 0;
        }

        /// <summary>
        /// 初始化 DisplayConduit
        /// </summary>
        private void InitializeConduit()
        {
            if (_conduit == null)
            {
                _conduit = new ProbeConduit();
            }
        }

        /// <summary>
        /// 组件从文档移除时清理 Conduit
        /// </summary>
        public override void RemovedFromDocument(GH_Document document)
        {
            CleanupConduit();
            base.RemovedFromDocument(document);
        }

        /// <summary>
        /// 文档关闭时清理
        /// </summary>
        public override void DocumentContextChanged(GH_Document document, GH_DocumentContext context)
        {
            if (context == GH_DocumentContext.Close)
            {
                CleanupConduit();
            }
            base.DocumentContextChanged(document, context);
        }

        /// <summary>
        /// 清理 Conduit 资源
        /// </summary>
        private void CleanupConduit()
        {
            if (_conduit != null)
            {
                _conduit.Enabled = false;
                _conduit.Clear();
                _conduit = null;
                _conduitEnabled = false;
            }
        }

        /// <summary>
        /// 探针测量结果
        /// </summary>
        private class ProbeMeasurement
        {
            public int Index { get; set; }
            public Point3d Position { get; set; }
            public Vector3d Velocity { get; set; }
            public double Speed => Velocity.Length;
            public double Pressure { get; set; }
            public bool HasPressure { get; set; }
            public string InterpolationMethod { get; set; }
            public double NearestDistance { get; set; } = double.NaN;
            public int NearbyPointCount { get; set; }

            public override string ToString()
            {
                string result = $"Probe {Index + 1} @ ({Position.X:F2}, {Position.Y:F2}, {Position.Z:F2})\n" +
                               $"  Speed: {Speed:F3} m/s\n" +
                               $"  Vector: ({Velocity.X:F3}, {Velocity.Y:F3}, {Velocity.Z:F3})\n" +
                               $"  Method: {InterpolationMethod}";

                if (HasPressure)
                {
                    result += $"\n  Pressure: {Pressure:F2} Pa";
                }

                return result;
            }
        }

        protected override Bitmap Icon
        {
            get { return IconLoader.Load("DataProbe.png"); }
        }

        public override Guid ComponentGuid
        {
            get { return new Guid("F8A3C5E2-9B7D-4F1A-8C4E-5D3B7A2F9E6C"); }
        }
    }

    /// <summary>
    /// 速度场加速结构（基于空间哈希的最近邻插值）
    /// 与 StreamlineTracer 中的实现一致
    /// </summary>
    internal class VelocityField
    {
        private readonly Dictionary<long, List<int>> _grid;
        private readonly List<Point3d> _pts;
        private readonly List<Vector3d> _vel;
        private readonly double _cellSize;
        private readonly BoundingBox _bounds;

        public VelocityField(List<Point3d> pts, List<Vector3d> vel, double cellSize = 0)
        {
            _pts = pts;
            _vel = vel;
            _bounds = new BoundingBox(pts);

            // 自动计算合适的 cell size
            if (cellSize <= 0)
            {
                double volume = Math.Max(_bounds.Volume, 1.0);
                cellSize = Math.Pow(volume / pts.Count, 1.0 / 3.0) * 2.0;
            }
            _cellSize = Math.Max(cellSize, 0.1);

            // 构建空间哈希
            _grid = new Dictionary<long, List<int>>(pts.Count);
            for (int i = 0; i < pts.Count; i++)
            {
                long h = Hash(pts[i]);
                if (!_grid.TryGetValue(h, out var list))
                {
                    list = new List<int>();
                    _grid[h] = list;
                }
                list.Add(i);
            }
        }

        /// <summary>
        /// 三线性插值获取任意位置的速度（IDW）
        /// </summary>
        public Vector3d Interpolate(Point3d p, double searchRadius = 0.0)
        {
            var nearbyIndices = GetNearbyIndices(p, searchRadius);
            if (nearbyIndices.Count == 0) return Vector3d.Zero;

            // 反距离加权插值（IDW）
            double weightSum = 0.0;
            Vector3d result = Vector3d.Zero;

            foreach (int idx in nearbyIndices)
            {
                double dist = p.DistanceTo(_pts[idx]);
                if (dist < 1e-10) return _vel[idx];

                double w = 1.0 / (dist * dist);
                weightSum += w;
                result += _vel[idx] * w;
            }

            return weightSum > 0 ? result / weightSum : Vector3d.Zero;
        }

        public double GetNearestDistance(Point3d p, double searchRadius = 0.0)
        {
            var nearbyIndices = GetNearbyIndices(p, searchRadius);
            if (nearbyIndices.Count == 0) return double.NaN;

            double nearest = double.MaxValue;
            foreach (int idx in nearbyIndices)
            {
                nearest = Math.Min(nearest, p.DistanceTo(_pts[idx]));
            }

            return nearest == double.MaxValue ? double.NaN : nearest;
        }

        public int GetNearbyCount(Point3d p, double searchRadius = 0.0)
        {
            return GetNearbyIndices(p, searchRadius).Count;
        }

        private List<int> GetNearbyIndices(Point3d p, double searchRadius = 0.0)
        {
            var result = new List<int>();

            int ix = CellIndex(p.X);
            int iy = CellIndex(p.Y);
            int iz = CellIndex(p.Z);
            double effectiveRadius = searchRadius > 0.0 ? searchRadius : _cellSize * 1.5;
            int cellRange = Math.Max(1, (int)Math.Ceiling(effectiveRadius / _cellSize));

            for (int dx = -cellRange; dx <= cellRange; dx++)
                for (int dy = -cellRange; dy <= cellRange; dy++)
                    for (int dz = -cellRange; dz <= cellRange; dz++)
                    {
                        long h = Hash(ix + dx, iy + dy, iz + dz);
                        if (_grid.TryGetValue(h, out var list))
                        {
                            foreach (int idx in list)
                            {
                                if (p.DistanceTo(_pts[idx]) <= effectiveRadius)
                                {
                                    result.Add(idx);
                                }
                            }
                        }
                    }

            return result;
        }

        private long Hash(Point3d p)
        {
            return Hash(
                CellIndex(p.X),
                CellIndex(p.Y),
                CellIndex(p.Z));
        }

        private int CellIndex(double coordinate)
        {
            return (int)Math.Floor(coordinate / _cellSize);
        }

        private long Hash(int ix, int iy, int iz)
        {
            const long P1 = 73856093;
            const long P2 = 19349663;
            const long P3 = 83492791;
            return (ix * P1) ^ (iy * P2) ^ (iz * P3);
        }
    }
}
