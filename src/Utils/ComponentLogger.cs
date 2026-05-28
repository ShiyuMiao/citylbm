using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Grasshopper.Kernel;

namespace CityLBM.Utils
{
    /// <summary>
    /// 组件日志管理器 - 统一收集和输出组件运行日志
    /// </summary>
    public class ComponentLogger
    {
        private readonly StringBuilder _logBuilder;
        private readonly string _componentName;
        private readonly List<LogEntry> _entries;
        private DateTime _startTime;

        public ComponentLogger(string componentName)
        {
            _componentName = componentName;
            _logBuilder = new StringBuilder();
            _entries = new List<LogEntry>();
            _startTime = DateTime.Now;
            
            Log("INFO", $"=== {_componentName} 开始执行 ===");
        }

        /// <summary>
        /// 记录信息日志
        /// </summary>
        public void Info(string message)
        {
            Log("INFO", message);
        }

        /// <summary>
        /// 记录调试日志
        /// </summary>
        public void Debug(string message)
        {
            Log("DEBUG", message);
        }

        /// <summary>
        /// 记录警告日志
        /// </summary>
        public void Warning(string message)
        {
            Log("WARN", message);
        }

        /// <summary>
        /// 记录错误日志
        /// </summary>
        public void Error(string message)
        {
            Log("ERROR", message);
        }

        /// <summary>
        /// 记录数据摘要
        /// </summary>
        public void DataSummary(string title, Dictionary<string, object> data)
        {
            Log("DATA", $"【{title}】");
            foreach (var kvp in data)
            {
                string valueStr = kvp.Value?.ToString() ?? "null";
                if (kvp.Value is double d)
                    valueStr = $"{d:F4}";
                else if (kvp.Value is float f)
                    valueStr = $"{f:F4}";
                else if (kvp.Value is int[] arr)
                    valueStr = $"[{string.Join(", ", arr)}]";
                else if (kvp.Value is double[] darr)
                    valueStr = $"[{string.Join(", ", darr.Select(x => x.ToString("F2")))}]";
                
                Log("DATA", $"  {kvp.Key}: {valueStr}");
            }
        }

        /// <summary>
        /// 记录几何信息
        /// </summary>
        public void Geometry(string name, Rhino.Geometry.BoundingBox bbox)
        {
            if (!bbox.IsValid)
            {
                Log("GEOM", $"{name}: 无效的边界框");
                return;
            }
            
            Log("GEOM", $"{name} 边界框:");
            Log("GEOM", $"  Min: ({bbox.Min.X:F2}, {bbox.Min.Y:F2}, {bbox.Min.Z:F2})");
            Log("GEOM", $"  Max: ({bbox.Max.X:F2}, {bbox.Max.Y:F2}, {bbox.Max.Z:F2})");
            Log("GEOM", $"  尺寸: ({bbox.Diagonal.X:F2}, {bbox.Diagonal.Y:F2}, {bbox.Diagonal.Z:F2})");
        }

        /// <summary>
        /// 记录几何信息 - Point3d
        /// </summary>
        public void Geometry(string name, Rhino.Geometry.Point3d point)
        {
            Log("GEOM", $"{name}: ({point.X:F4}, {point.Y:F4}, {point.Z:F4})");
        }

        /// <summary>
        /// 记录几何信息 - Vector3d
        /// </summary>
        public void Geometry(string name, Rhino.Geometry.Vector3d vector)
        {
            Log("GEOM", $"{name}: ({vector.X:F4}, {vector.Y:F4}, {vector.Z:F4}), 长度: {vector.Length:F4}");
        }

        /// <summary>
        /// 记录性能计时
        /// </summary>
        public void Timing(string operation, TimeSpan elapsed)
        {
            Log("TIME", $"{operation}: {elapsed.TotalMilliseconds:F1} ms");
        }

        /// <summary>
        /// 记录性能计时（自动计算）
        /// </summary>
        public void Timing(string operation, long milliseconds)
        {
            Log("TIME", $"{operation}: {milliseconds} ms");
        }

        /// <summary>
        /// 记录集合统计
        /// </summary>
        public void Statistics(string name, int count)
        {
            Log("STAT", $"{name}: {count} 项");
        }

        /// <summary>
        /// 记录集合统计（带筛选）
        /// </summary>
        public void Statistics(string name, int total, int filtered)
        {
            Log("STAT", $"{name}: {filtered}/{total} 项 (筛选率: {(100.0 * filtered / total):F1}%)");
        }

        /// <summary>
        /// 记录数值范围
        /// </summary>
        public void Range(string name, double min, double max)
        {
            Log("RANGE", $"{name}: [{min:F4}, {max:F4}] (范围: {max - min:F4})");
        }

        /// <summary>
        /// 记录数值范围（带平均值）
        /// </summary>
        public void Range(string name, double min, double max, double avg)
        {
            Log("RANGE", $"{name}: [{min:F4}, {max:F4}], 平均: {avg:F4}");
        }

        /// <summary>
        /// 记录文件操作
        /// </summary>
        public void FileOperation(string operation, string path, long? size = null)
        {
            string sizeStr = size.HasValue ? $", 大小: {size.Value / 1024.0:F1} KB" : "";
            Log("FILE", $"{operation}: {path}{sizeStr}");
        }

        /// <summary>
        /// 记录配置参数
        /// </summary>
        public void Config(string name, object value)
        {
            Log("CONFIG", $"{name} = {value}");
        }

        /// <summary>
        /// 记录步骤开始
        /// </summary>
        public void StepStart(string stepName)
        {
            Log("STEP", $">>> 开始: {stepName}");
        }

        /// <summary>
        /// 记录步骤完成
        /// </summary>
        public void StepEnd(string stepName)
        {
            Log("STEP", $"<<< 完成: {stepName}");
        }

        /// <summary>
        /// 记录步骤完成（带结果）
        /// </summary>
        public void StepEnd(string stepName, string result)
        {
            Log("STEP", $"<<< 完成: {stepName} - {result}");
        }

        /// <summary>
        /// 记录可视化参数
        /// </summary>
        public void Visualization(string param, object value)
        {
            Log("VIS", $"{param}: {value}");
        }

        /// <summary>
        /// 记录坐标变换
        /// </summary>
        public void Transform(string from, string to, double[] values)
        {
            Log("XFORM", $"{from} -> {to}: [{string.Join(", ", values.Select(v => $"{v:F4}"))}]");
        }

        /// <summary>
        /// 记录坐标变换（单值）
        /// </summary>
        public void Transform(string description, double before, double after)
        {
            Log("XFORM", $"{description}: {before:F4} -> {after:F4}");
        }

        /// <summary>
        /// 添加自定义日志条目
        /// </summary>
        private void Log(string level, string message)
        {
            var entry = new LogEntry
            {
                Timestamp = DateTime.Now,
                Level = level,
                Message = message,
                ElapsedMs = (DateTime.Now - _startTime).TotalMilliseconds
            };
            _entries.Add(entry);
            
            string line = $"[{entry.ElapsedMs,8:F1}ms] [{level,-5}] {message}";
            _logBuilder.AppendLine(line);
        }

        /// <summary>
        /// 获取完整日志字符串
        /// </summary>
        public string GetLog()
        {
            return _logBuilder.ToString();
        }

        /// <summary>
        /// 获取日志条目列表
        /// </summary>
        public List<LogEntry> GetEntries()
        {
            return new List<LogEntry>(_entries);
        }

        /// <summary>
        /// 完成日志记录
        /// </summary>
        public void Finish()
        {
            var elapsed = DateTime.Now - _startTime;
            Log("INFO", $"=== {_componentName} 执行完成 (总耗时: {elapsed.TotalMilliseconds:F1} ms) ===");
        }

        /// <summary>
        /// 将日志输出到 Grasshopper 组件
        /// </summary>
        public void OutputToComponent(GH_Component component, IGH_DataAccess DA, int outputIndex)
        {
            Finish();
            DA.SetData(outputIndex, GetLog());
        }

        /// <summary>
        /// 将日志输出到 Grasshopper 组件（指定参数名）
        /// </summary>
        public void OutputToComponent(GH_Component component, IGH_DataAccess DA, string paramName)
        {
            Finish();
            DA.SetData(paramName, GetLog());
        }
    }

    /// <summary>
    /// 日志条目
    /// </summary>
    public class LogEntry
    {
        public DateTime Timestamp { get; set; }
        public string Level { get; set; }
        public string Message { get; set; }
        public double ElapsedMs { get; set; }
    }
}
