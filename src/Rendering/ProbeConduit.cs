using System;
using System.Collections.Generic;
using System.Drawing;
using Rhino.Display;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// 数据探针 DisplayConduit
    /// 在 Rhino 视口中实时显示探针点的风速和压力数据
    /// </summary>
    public class ProbeConduit : DisplayConduit
    {
        // ═══════════════════════════════════════════════════════════════
        // 渲染数据（线程安全访问）
        // ═══════════════════════════════════════════════════════════════
        private readonly object _lock = new object();
        private bool _enabled = false;

        // 探针数据
        private List<ProbeData> _probes = new List<ProbeData>();

        // 可视化参数
        private Color _probeColor = Color.Yellow;
        private Color _textColor = Color.White;
        private Color _bgColor = Color.FromArgb(180, 0, 0, 0);
        private float _pointSize = 8.0f;
        private float _lineWidth = 2.0f;

        /// <summary>
        /// 探针数据结构
        /// </summary>
        public class ProbeData
        {
            public Point3d Position { get; set; }
            public Vector3d Velocity { get; set; }
            public double Pressure { get; set; }
            public double Speed => Velocity.Length;
            public bool HasPressure { get; set; }
            public string Label { get; set; }
            
            /// <summary>
            /// 来流风向量（可选，用于方向参考）
            /// </summary>
            public Vector3d WindDirection { get; set; }
            
            /// <summary>
            /// 是否使用风向参考
            /// </summary>
            public bool HasWindDirection => WindDirection.Length > 0.001;
        }

        /// <summary>
        /// 更新探针数据
        /// </summary>
        public void SetProbes(List<ProbeData> probes)
        {
            lock (_lock)
            {
                _probes = probes ?? new List<ProbeData>();
                _enabled = _probes.Count > 0;
            }
        }

        /// <summary>
        /// 更新单个探针数据（用于拖拽时的实时更新）
        /// </summary>
        public void UpdateProbe(int index, ProbeData data)
        {
            lock (_lock)
            {
                if (index >= 0 && index < _probes.Count)
                {
                    _probes[index] = data;
                }
            }
        }

        /// <summary>
        /// 清除渲染数据
        /// </summary>
        public void Clear()
        {
            lock (_lock)
            {
                _probes.Clear();
                _enabled = false;
            }
        }

        // ═══════════════════════════════════════════════════════════════
        // DisplayConduit 渲染回调
        // ═══════════════════════════════════════════════════════════════

        protected override void DrawOverlay(DrawEventArgs e)
        {
            lock (_lock)
            {
                if (!_enabled || _probes.Count == 0) return;

                foreach (var probe in _probes)
                {
                    DrawProbe(e.Display, probe);
                }
            }
        }

        /// <summary>
        /// 绘制单个探针
        /// </summary>
        private void DrawProbe(DisplayPipeline display, ProbeData probe)
        {
            // 将 3D 点投影到屏幕坐标
            if (!display.Viewport.IsVisible(probe.Position))
                return;

            Point2d screenPt2d = display.Viewport.WorldToClient(probe.Position);
            int screenX = (int)screenPt2d.X;
            int screenY = (int)screenPt2d.Y;

            // 绘制探针点（2D 圆点）
            Draw2dCircle(display, screenX, screenY, (int)(_pointSize / 2), _probeColor, 2);

            // 构建显示文本
            string label = string.IsNullOrEmpty(probe.Label) ? $"Probe {_probes.IndexOf(probe) + 1}" : probe.Label;
            string speedText = $"V: {probe.Speed:F2} m/s";
            string vectorText = $"({probe.Velocity.X:F2}, {probe.Velocity.Y:F2}, {probe.Velocity.Z:F2})";
            string pressureText = probe.HasPressure ? $"P: {probe.Pressure:F1} Pa" : "";

            // 文本尺寸
            var font = new Font("Consolas", 10, FontStyle.Bold);
            int lineHeight = font.Height + 2;
            int textWidth = 180;
            int textHeight = probe.HasPressure ? lineHeight * 4 + 10 : lineHeight * 3 + 10;

            // 文本位置（探针点右上方）
            int textX = screenX + 15;
            int textY = screenY - textHeight - 10;

            // 确保文本不超出屏幕边界
            var viewport = display.Viewport;
            if (textX + textWidth > viewport.Size.Width)
                textX = screenX - textWidth - 15;
            if (textY < 0)
                textY = screenY + 20;

            // 绘制背景矩形（使用四条线）
            int bgX = textX - 5;
            int bgY = textY - 5;
            int bgW = textWidth + 10;
            int bgH = textHeight;
            display.Draw2dLine(new System.Drawing.Point(bgX, bgY), new System.Drawing.Point(bgX + bgW, bgY), Color.Gray, 1);
            display.Draw2dLine(new System.Drawing.Point(bgX + bgW, bgY), new System.Drawing.Point(bgX + bgW, bgY + bgH), Color.Gray, 1);
            display.Draw2dLine(new System.Drawing.Point(bgX + bgW, bgY + bgH), new System.Drawing.Point(bgX, bgY + bgH), Color.Gray, 1);
            display.Draw2dLine(new System.Drawing.Point(bgX, bgY + bgH), new System.Drawing.Point(bgX, bgY), Color.Gray, 1);

            // 绘制引线
            display.Draw2dLine(
                new System.Drawing.Point((int)(screenX + _pointSize / 2), screenY),
                new System.Drawing.Point(textX, textY + textHeight / 2),
                _probeColor, 1);

            // 绘制文本
            int currentY = textY;

            // 标签（黄色粗体）
            display.Draw2dText(label, Color.Yellow, new Point2d(textX, currentY), false, font.Height);
            currentY += lineHeight;

            // 速度（青色）
            display.Draw2dText(speedText, Color.Cyan, new Point2d(textX, currentY), false, font.Height);
            currentY += lineHeight;

            // 向量分量（灰色小字）
            var smallFont = new Font("Consolas", 8);
            display.Draw2dText(vectorText, Color.LightGray, new Point2d(textX, currentY), false, smallFont.Height);
            currentY += lineHeight;

            // 压力（绿色）
            if (probe.HasPressure)
            {
                display.Draw2dText(pressureText, Color.Lime, new Point2d(textX, currentY), false, font.Height);
            }

            // 绘制 3D 速度向量（世界空间）
            DrawVelocityVector(display, probe);
        }

        /// <summary>
        /// 绘制 3D 速度向量 - 显示 XYZ 三个分量和合速度
        /// </summary>
        private void DrawVelocityVector(DisplayPipeline display, ProbeData probe)
        {
            if (probe.Speed < 0.001) return;

            // 基础缩放因子
            double baseScale = Math.Min(10.0, 5.0 / Math.Max(probe.Speed, 0.1));
            
            // 绘制 XYZ 三个方向的分量箭头
            DrawComponentArrow(display, probe, probe.Velocity.X, Vector3d.XAxis, Color.Red, baseScale);
            DrawComponentArrow(display, probe, probe.Velocity.Y, Vector3d.YAxis, Color.Green, baseScale);
            DrawComponentArrow(display, probe, probe.Velocity.Z, Vector3d.ZAxis, Color.Blue, baseScale);

            // 绘制合速度向量（主箭头，白色/速度色）
            Vector3d scaledVel = probe.Velocity * baseScale;
            Point3d endPoint = probe.Position + scaledVel;
            Color velColor = GetSpeedColor(probe.Speed);
            
            // 合速度用更粗的线
            display.DrawLine(new Line(probe.Position, endPoint), velColor, (int)_lineWidth);
            DrawArrowHead(display, endPoint, scaledVel, velColor, 1.0);
            
            // 如果有风向参考，绘制风向指示（虚线）
            if (probe.HasWindDirection)
            {
                DrawWindDirectionIndicator(display, probe, baseScale);
            }
        }

        /// <summary>
        /// 绘制速度分量箭头
        /// </summary>
        private void DrawComponentArrow(DisplayPipeline display, ProbeData probe, 
            double componentValue, Vector3d axis, Color color, double baseScale)
        {
            if (Math.Abs(componentValue) < 0.001) return;
            
            // 分量箭头从探针点开始
            Vector3d componentVec = axis * componentValue * baseScale;
            Point3d endPoint = probe.Position + componentVec;
            
            // 使用半透明颜色
            Color semiColor = Color.FromArgb(150, color.R, color.G, color.B);
            
            // 绘制分量线（细线）
            display.DrawLine(new Line(probe.Position, endPoint), semiColor, 1);
            
            // 小箭头头部
            DrawArrowHead(display, endPoint, componentVec, semiColor, 0.5);
        }

        /// <summary>
        /// 绘制风向指示器（虚线圆环）
        /// </summary>
        private void DrawWindDirectionIndicator(DisplayPipeline display, ProbeData probe, double baseScale)
        {
            double radius = baseScale * 2.0;
            int segments = 32;
            
            // 绘制水平圆环（表示风向参考平面）
            for (int i = 0; i < segments; i += 2) // 虚线效果：每隔一个点画
            {
                double a1 = 2 * Math.PI * i / segments;
                double a2 = 2 * Math.PI * (i + 1) / segments;
                
                Point3d p1 = probe.Position + new Vector3d(
                    radius * Math.Cos(a1), 
                    radius * Math.Sin(a1), 
                    0);
                Point3d p2 = probe.Position + new Vector3d(
                    radius * Math.Cos(a2), 
                    radius * Math.Sin(a2), 
                    0);
                
                display.DrawLine(new Line(p1, p2), Color.Gray, 1);
            }
            
            // 绘制风向箭头（黄色）
            Vector3d windDir = probe.WindDirection;
            windDir.Unitize();
            Point3d windEnd = probe.Position + windDir * radius * 1.5;
            display.DrawLine(new Line(probe.Position, windEnd), Color.Yellow, 2);
            DrawArrowHead(display, windEnd, windDir * radius * 1.5, Color.Yellow, 0.7);
        }

        /// <summary>
        /// 绘制 2D 圆（使用线段近似）
        /// </summary>
        private void Draw2dCircle(DisplayPipeline display, int cx, int cy, int r, Color color, int thickness)
        {
            int segments = 16;
            for (int i = 0; i < segments; i++)
            {
                double a1 = 2 * Math.PI * i / segments;
                double a2 = 2 * Math.PI * (i + 1) / segments;
                int x1 = cx + (int)(r * Math.Cos(a1));
                int y1 = cy + (int)(r * Math.Sin(a1));
                int x2 = cx + (int)(r * Math.Cos(a2));
                int y2 = cy + (int)(r * Math.Sin(a2));
                display.Draw2dLine(new System.Drawing.Point(x1, y1), new System.Drawing.Point(x2, y2), color, thickness);
            }
        }

        /// <summary>
        /// 根据速度大小获取颜色（蓝->绿->黄->红）
        /// </summary>
        private Color GetSpeedColor(double speed)
        {
            // 假设速度范围 0-20 m/s
            double t = Math.Min(speed / 20.0, 1.0);

            if (t < 0.33)
            {
                // 蓝 -> 绿
                double localT = t / 0.33;
                return Color.FromArgb(
                    0,
                    (int)(255 * localT),
                    (int)(255 * (1 - localT)));
            }
            else if (t < 0.66)
            {
                // 绿 -> 黄
                double localT = (t - 0.33) / 0.33;
                return Color.FromArgb(
                    (int)(255 * localT),
                    255,
                    0);
            }
            else
            {
                // 黄 -> 红
                double localT = (t - 0.66) / 0.34;
                return Color.FromArgb(
                    255,
                    (int)(255 * (1 - localT)),
                    0);
            }
        }

        /// <summary>
        /// 绘制箭头头部
        /// </summary>
        private void DrawArrowHead(DisplayPipeline display, Point3d tip, Vector3d dir, Color color, double scale = 1.0)
        {
            if (dir.Length < 1e-6) return;

            Vector3d dirUnit = dir;
            dirUnit.Unitize();
            double arrowSize = 0.5 * scale;

            // 找到垂直于 dir 的平面内的两个方向
            Vector3d perp1 = Vector3d.CrossProduct(dirUnit, Vector3d.ZAxis);
            if (perp1.Length < 1e-6) perp1 = Vector3d.CrossProduct(dirUnit, Vector3d.XAxis);
            perp1.Unitize();
            
            Vector3d perp2 = Vector3d.CrossProduct(dirUnit, perp1);
            perp2.Unitize();

            Point3d basePt = tip - dirUnit * arrowSize;
            
            // 绘制箭头（四面锥形）
            double wingSize = arrowSize * 0.4;
            Point3d wing1 = basePt + perp1 * wingSize;
            Point3d wing2 = basePt - perp1 * wingSize;
            Point3d wing3 = basePt + perp2 * wingSize;
            Point3d wing4 = basePt - perp2 * wingSize;

            display.DrawLine(new Line(tip, wing1), color, (int)(2 * scale));
            display.DrawLine(new Line(tip, wing2), color, (int)(2 * scale));
            display.DrawLine(new Line(tip, wing3), color, (int)(2 * scale));
            display.DrawLine(new Line(tip, wing4), color, (int)(2 * scale));
            
            // 绘制底部轮廓
            display.DrawLine(new Line(wing1, wing3), color, 1);
            display.DrawLine(new Line(wing3, wing2), color, 1);
            display.DrawLine(new Line(wing2, wing4), color, 1);
            display.DrawLine(new Line(wing4, wing1), color, 1);
        }
    }
}
