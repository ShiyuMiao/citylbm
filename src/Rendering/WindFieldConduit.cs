using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Rhino.Display;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// 风场流线 DisplayConduit
    /// 生命周期：由 StreamlineComponent 在 SolveInstance 中创建并 Enable，
    /// 在 RemovedFromDocument / Document 关闭时 Disable，防止内存泄漏。
    /// </summary>
    public class WindFieldConduit : DisplayConduit
    {
        // ═══════════════════════════════════════════════════════════════
        // 渲染数据（线程安全访问）
        // ═══════════════════════════════════════════════════════════════
        private readonly object _lock = new object();
        private List<Polyline> _streamlines = new List<Polyline>();
        private List<Color> _lineColors = new List<Color>();
        private List<double> _lineSpeeds = new List<double>();
        private List<double> _lineLengths = new List<double>();

        // ═══════════════════════════════════════════════════════════════
        // 可视化参数
        // ═══════════════════════════════════════════════════════════════
        public Color ColorLow { get; set; } = Color.Blue;
        public Color ColorHigh { get; set; } = Color.Red;
        public double SpeedMin { get; set; } = 0.0;
        public double SpeedMax { get; set; } = 10.0;
        public double LengthMin { get; set; } = 0.0;
        public double LengthMax { get; set; } = 100.0;
        public float LineWidth { get; set; } = 1.5f;
        public bool ShowArrows { get; set; } = false;
        public float ArrowSize { get; set; } = 5.0f;
        public bool ColorByLength { get; set; } = true; // 默认按长度着色

        /// <summary>
        /// 更新流线数据（在后台线程计算完毕后，在 UI 线程调用）
        /// </summary>
        public void SetStreamlines(List<Polyline> lines, List<double> speeds)
        {
            lock (_lock)
            {
                _streamlines = lines ?? new List<Polyline>();
                _lineSpeeds = speeds ?? new List<double>();
                
                // 计算每条流线的长度
                _lineLengths = _streamlines.Select(pl => pl.Length).ToList();
                
                // 更新长度范围
                if (_lineLengths.Count > 0)
                {
                    LengthMin = _lineLengths.Min();
                    LengthMax = _lineLengths.Max();
                }
                
                // 根据设置选择颜色映射方式
                if (ColorByLength)
                    _lineColors = ComputeColorsByLength(_lineLengths);
                else
                    _lineColors = ComputeColorsBySpeed(_lineSpeeds);
            }
        }

        /// <summary>
        /// 清空渲染数据
        /// </summary>
        public void Clear()
        {
            lock (_lock)
            {
                _streamlines.Clear();
                _lineColors.Clear();
                _lineSpeeds.Clear();
                _lineLengths.Clear();
            }
        }

        /// <summary>
        /// 按流线长度计算颜色映射（短线蓝色 -> 长线红色）
        /// </summary>
        private List<Color> ComputeColorsByLength(List<double> lengths)
        {
            var colors = new List<Color>(lengths.Count);
            if (lengths.Count == 0) return colors;
            
            double minLen = lengths.Min();
            double maxLen = lengths.Max();
            double range = Math.Max(maxLen - minLen, 1e-6);

            foreach (double len in lengths)
            {
                // 短线 (minLen) -> t=0 (蓝色), 长线 (maxLen) -> t=1 (红色)
                double t = (len - minLen) / range;
                t = Math.Max(0.0, Math.Min(1.0, t));
                colors.Add(InterpolateColor(ColorLow, ColorHigh, t));
            }
            return colors;
        }

        /// <summary>
        /// 按风速计算颜色映射（低速蓝色 -> 高速红色）
        /// </summary>
        private List<Color> ComputeColorsBySpeed(List<double> speeds)
        {
            var colors = new List<Color>(speeds.Count);
            double range = Math.Max(SpeedMax - SpeedMin, 1e-6);

            foreach (double speed in speeds)
            {
                double t = (speed - SpeedMin) / range;
                t = Math.Max(0.0, Math.Min(1.0, t));
                colors.Add(InterpolateColor(ColorLow, ColorHigh, t));
            }
            return colors;
        }

        /// <summary>
        /// 线性颜色插值
        /// </summary>
        private static Color InterpolateColor(Color a, Color b, double t)
        {
            return Color.FromArgb(
                (int)(a.R + (b.R - a.R) * t),
                (int)(a.G + (b.G - a.G) * t),
                (int)(a.B + (b.B - a.B) * t));
        }

        // ═══════════════════════════════════════════════════════════════
        // DisplayConduit 渲染回调
        // ═══════════════════════════════════════════════════════════════

        protected override void DrawOverlay(DrawEventArgs e)
        {
            lock (_lock)
            {
                // 绘制流线
                if (_streamlines != null && _streamlines.Count > 0)
                {
                    for (int i = 0; i < _streamlines.Count; i++)
                    {
                        Color c = i < _lineColors.Count ? _lineColors[i] : Color.White;
                        e.Display.DrawPolyline(_streamlines[i], c, (int)LineWidth);

                        // 可选：在流线末端绘制箭头
                        if (ShowArrows && _streamlines[i].Count >= 2)
                        {
                            DrawArrow(e.Display, _streamlines[i], c);
                        }
                    }
                }

                // 绘制颜色图例（Colorbar）
                DrawColorbar(e.Display);
            }
        }

        /// <summary>
        /// 绘制屏幕颜色图例（右下角）
        /// </summary>
        private void DrawColorbar(DisplayPipeline display)
        {
            // 图例位置和尺寸
            int margin = 20;
            int width = 20;
            int height = 150;
            int textWidth = 60;

            // 获取视口尺寸
            var viewport = display.Viewport;
            int screenW = viewport.Size.Width;
            int screenH = viewport.Size.Height;

            // 图例位置：右下角
            int x = screenW - margin - width - textWidth;
            int y = screenH - margin - height;

            // 绘制渐变条（从 ColorLow 到 ColorHigh）
            for (int i = 0; i < height; i++)
            {
                double t = 1.0 - (double)i / (height - 1);  // 从上到下：High -> Low
                Color c = InterpolateColor(ColorLow, ColorHigh, t);
                int lineY = y + i;
                display.Draw2dLine(new System.Drawing.Point(x, lineY), new System.Drawing.Point(x + width, lineY), c, 1);
            }

            // 绘制边框（使用四条线）
            display.Draw2dLine(new System.Drawing.Point(x, y), new System.Drawing.Point(x + width, y), Color.White, 1);
            display.Draw2dLine(new System.Drawing.Point(x + width, y), new System.Drawing.Point(x + width, y + height), Color.White, 1);
            display.Draw2dLine(new System.Drawing.Point(x + width, y + height), new System.Drawing.Point(x, y + height), Color.White, 1);
            display.Draw2dLine(new System.Drawing.Point(x, y + height), new System.Drawing.Point(x, y), Color.White, 1);

            // 绘制文字标签
            var font = new System.Drawing.Font("Arial", 10);
            
            if (ColorByLength)
            {
                // 按长度着色时的图例
                // 最大值（顶部）- 长线红色
                display.Draw2dText($"{LengthMax:F1}", Color.White, new Point2d(x + width + 5, y - 5), false, font.Height);
                
                // 最小值（底部）- 短线蓝色
                display.Draw2dText($"{LengthMin:F1}", Color.White, new Point2d(x + width + 5, y + height - 10), false, font.Height);
                
                // 单位（中间）
                display.Draw2dText("m", Color.Gray, new Point2d(x + width + 5, y + height / 2 - 5), false, font.Height);

                // 标题
                display.Draw2dText("Streamline Length", Color.White, new Point2d(x - 20, y - 20), false, font.Height);
            }
            else
            {
                // 按风速着色时的图例
                // 最大值（顶部）
                display.Draw2dText($"{SpeedMax:F1}", Color.White, new Point2d(x + width + 5, y - 5), false, font.Height);
                
                // 最小值（底部）
                display.Draw2dText($"{SpeedMin:F1}", Color.White, new Point2d(x + width + 5, y + height - 10), false, font.Height);
                
                // 单位（中间）
                display.Draw2dText("m/s", Color.Gray, new Point2d(x + width + 5, y + height / 2 - 5), false, font.Height);

                // 标题
                display.Draw2dText("Wind Speed", Color.White, new Point2d(x, y - 20), false, font.Height);
            }
        }

        /// <summary>
        /// 在流线末端绘制方向箭头
        /// </summary>
        private void DrawArrow(DisplayPipeline display, Polyline line, Color color)
        {
            int n = line.Count;
            if (n < 2) return;

            Point3d end = line[n - 1];
            Point3d prev = line[n - 2];
            Vector3d dir = end - prev;
            double len = dir.Length;
            if (len < 1e-6) return;

            dir.Unitize();
            Vector3d perp = Vector3d.CrossProduct(dir, Vector3d.ZAxis);
            if (perp.Length < 1e-6) perp = Vector3d.CrossProduct(dir, Vector3d.XAxis);
            perp.Unitize();

            double arrowLen = Math.Min(ArrowSize, len * 0.5);
            double arrowWidth = arrowLen * 0.3;

            Point3d basePt = end - dir * arrowLen;
            Point3d left = basePt + perp * arrowWidth;
            Point3d right = basePt - perp * arrowWidth;

            display.DrawLine(new Line(end, left), color, (int)LineWidth);
            display.DrawLine(new Line(end, right), color, (int)LineWidth);
            display.DrawLine(new Line(left, right), color, (int)LineWidth);
        }
    }
}
