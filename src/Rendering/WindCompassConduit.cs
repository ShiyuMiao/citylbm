using System;
using System.Drawing;
using Rhino.Display;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// 风向指南针 DisplayConduit - 视角联动版
    /// 方位指示器随 Rhino 视角旋转而联动
    /// </summary>
    public class WindCompassConduit : DisplayConduit
    {
        private readonly object _lock = new object();
        private bool _enabled = false;

        // 风场参数
        private double _windDirectionDegrees = 0.0;
        private double _windSpeed = 5.0;
        private Point3d _origin = Point3d.Origin;
        private double _compassRadius = 20.0;

        // 风廓线参数
        private WindProfileType _windProfile = WindProfileType.Uniform;
        private double _referenceHeight = 10.0;
        private double _roughnessLength = 0.3;
        private double _alpha = 0.22;
        private double _vonKarman = 0.41;
        private bool _showProfile = false;

        // 计算域边界
        private BoundingBox _domainBounds = BoundingBox.Unset;

        public void SetWindData(
            double directionDegrees,
            double windSpeed,
            Point3d origin,
            double compassRadius = 20.0)
        {
            lock (_lock)
            {
                _windDirectionDegrees = directionDegrees;
                _windSpeed = windSpeed;
                _origin = origin;
                _compassRadius = compassRadius;
                _enabled = true;
            }
        }

        public void SetWindProfile(
            WindProfileType profile,
            double referenceHeight,
            double roughnessLength,
            double alpha,
            double vonKarman = 0.41)
        {
            lock (_lock)
            {
                _windProfile = profile;
                _referenceHeight = referenceHeight;
                _roughnessLength = roughnessLength;
                _alpha = alpha;
                _vonKarman = vonKarman;
                _showProfile = (profile != WindProfileType.Uniform);
            }
        }

        public void SetDomainBounds(BoundingBox bounds)
        {
            lock (_lock)
            {
                _domainBounds = bounds;
            }
        }

        public void Clear()
        {
            lock (_lock)
            {
                _enabled = false;
            }
        }

        /// <summary>
        /// 绘制屏幕空间覆盖层（在 DrawOverlay 中调用）
        /// </summary>
        protected override void DrawOverlay(DrawEventArgs e)
        {
            lock (_lock)
            {
                if (!_enabled) return;

                // 绘制屏幕空间指南针（左上角，随视角联动）
                DrawScreenCompass(e.Display);

                // 绘制世界空间风方向箭头
                DrawWindArrow(e.Display);

                // 绘制风剖面曲线
                if (_showProfile && _domainBounds.IsValid)
                {
                    DrawWindProfileCurve(e.Display);
                }
            }
        }

        /// <summary>
        /// 绘制屏幕空间 2D 指南针 - 随视角联动
        /// 根据当前视口的 Camera 方向调整 N/E/S/W 的显示位置
        /// </summary>
        private void DrawScreenCompass(DisplayPipeline display)
        {
            var viewport = display.Viewport;
            int screenW = viewport.Size.Width;
            int screenH = viewport.Size.Height;

            // 指南针位置：左上角
            int margin = 30;
            int centerX = margin + 60;
            int centerY = margin + 60;
            int radius = 50;

            // 获取视口的世界坐标系到屏幕坐标系的变换
            // 用于计算 N/E/S/W 在屏幕上的相对位置
            var camera = viewport.CameraDirection;
            camera.Z = 0; // 投影到 XY 平面
            if (camera.Length < 0.001)
            {
                // 顶视图，使用默认方向
                camera = new Vector3d(0, -1, 0);
            }
            camera.Unitize();

            // 计算屏幕上的"北"方向
            // 世界坐标：北 = -Y 方向
            Vector3d worldNorth = new Vector3d(0, -1, 0);
            
            // 计算北方向在屏幕上的投影
            // 使用视口的变换矩阵
            var xform = viewport.GetTransform(Rhino.DocObjects.CoordinateSystem.World, 
                                              Rhino.DocObjects.CoordinateSystem.Screen);
            
            // 计算北方向在屏幕上的偏移
            Point3d northWorld = new Point3d(0, -1, 0);
            Point3d originWorld = new Point3d(0, 0, 0);
            
            // 如果视口是透视或平行投影，计算北方向的屏幕角度
            double northAngle = ComputeNorthAngleOnScreen(viewport);

            // 绘制指南针圆环
            Draw2dCircle(display, centerX, centerY, radius, Color.White, 2);

            // 绘制 N/E/S/W 标记 - 随视角旋转
            var font = new Font("Arial", 12, FontStyle.Bold);
            int labelOffset = radius + 15;

            // 根据视角计算 N/E/S/W 的屏幕位置
            DrawDirectionLabel(display, "N", centerX, centerY, labelOffset, northAngle, font, Color.Red);
            DrawDirectionLabel(display, "E", centerX, centerY, labelOffset, northAngle + Math.PI / 2, font, Color.White);
            DrawDirectionLabel(display, "S", centerX, centerY, labelOffset, northAngle + Math.PI, font, Color.White);
            DrawDirectionLabel(display, "W", centerX, centerY, labelOffset, northAngle + Math.PI * 1.5, font, Color.White);

            // 绘制来风方向箭头（相对于北方向）
            // 风向角度：0=北风（从北来，箭头指向北）
            double windAngleRad = (_windDirectionDegrees - 90) * Math.PI / 180.0; // 转换为标准角度
            double arrowAngle = northAngle + windAngleRad;

            int arrowLen = radius - 10;
            int arrowX = centerX + (int)(arrowLen * Math.Cos(arrowAngle));
            int arrowY = centerY + (int)(arrowLen * Math.Sin(arrowAngle));

            // 绘制粗箭头线
            display.Draw2dLine(
                new System.Drawing.Point(centerX, centerY),
                new System.Drawing.Point(arrowX, arrowY),
                Color.Cyan, 4);

            // 绘制箭头头部
            double headAngle1 = arrowAngle + Math.PI * 0.8;
            double headAngle2 = arrowAngle - Math.PI * 0.8;
            int headLen = 15;

            int head1X = arrowX + (int)(headLen * Math.Cos(headAngle1));
            int head1Y = arrowY + (int)(headLen * Math.Sin(headAngle1));
            int head2X = arrowX + (int)(headLen * Math.Cos(headAngle2));
            int head2Y = arrowY + (int)(headLen * Math.Sin(headAngle2));

            display.Draw2dLine(new System.Drawing.Point(arrowX, arrowY), new System.Drawing.Point(head1X, head1Y), Color.Cyan, 3);
            display.Draw2dLine(new System.Drawing.Point(arrowX, arrowY), new System.Drawing.Point(head2X, head2Y), Color.Cyan, 3);

            // 绘制风速文字
            var infoFont = new Font("Arial", 10);
            string dirText = GetDirectionText(_windDirectionDegrees);
            display.Draw2dText(
                $"{_windSpeed:F1} m/s",
                Color.Yellow,
                new Point2d(centerX - 25, centerY + radius + 20),
                false, infoFont.Height);
            display.Draw2dText(
                $"{dirText} ({_windDirectionDegrees:F0}°)",
                Color.White,
                new Point2d(centerX - 35, centerY + radius + 35),
                false, infoFont.Height);
        }

        /// <summary>
        /// 计算北方向在屏幕上的角度
        /// </summary>
        private double ComputeNorthAngleOnScreen(RhinoViewport viewport)
        {
            // 获取视口的 X 和 Y 轴在世界坐标系中的方向
            var cameraX = viewport.CameraX;
            var cameraY = viewport.CameraY;

            // 世界北方向 (-Y)
            Vector3d worldNorth = new Vector3d(0, -1, 0);

            // 计算北方向在屏幕上的投影
            // 屏幕 X 方向 = cameraX，屏幕 Y 方向 = cameraY（向下为正）
            double screenX = Vector3d.Multiply(worldNorth, cameraX);
            double screenY = Vector3d.Multiply(worldNorth, cameraY);

            // 计算角度（从正X轴逆时针）
            double angle = Math.Atan2(screenY, screenX);
            
            // 调整：屏幕Y向下为正，需要翻转
            // 同时确保北在正确的位置
            return angle;
        }

        /// <summary>
        /// 绘制方向标签
        /// </summary>
        private void DrawDirectionLabel(DisplayPipeline display, string text, 
            int cx, int cy, int offset, double angle, Font font, Color color)
        {
            int x = cx + (int)(offset * Math.Cos(angle));
            int y = cy + (int)(offset * Math.Sin(angle));
            
            // 估算文字大小（不使用 TextRenderer）
            int textWidth = text.Length * font.Height / 2;
            int textHeight = font.Height;
            x -= textWidth / 2;
            y -= textHeight / 2;
            
            display.Draw2dText(text, color, new Point2d(x, y), false, font.Height);
        }

        /// <summary>
        /// 绘制世界空间风方向箭头
        /// </summary>
        private void DrawWindArrow(DisplayPipeline display)
        {
            double angleRad = _windDirectionDegrees * Math.PI / 180.0;
            Vector3d windDir = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);

            double arrowLength = _compassRadius * 1.5;
            Point3d arrowEnd = _origin + windDir * arrowLength;

            display.DrawLine(new Line(_origin, arrowEnd), Color.Cyan, 4);
            DrawArrowHead(display, arrowEnd, windDir, _compassRadius * 0.3, Color.Cyan);

            var plane = new Plane(arrowEnd + windDir * _compassRadius * 0.2, Vector3d.ZAxis);
            display.Draw3dText(
                $"Wind: {_windSpeed:F1} m/s",
                Color.Yellow,
                plane,
                _compassRadius * 0.15,
                "Arial");
        }

        /// <summary>
        /// 在入口边界位置绘制风剖面示意曲线
        /// </summary>
        private void DrawWindProfileCurve(DisplayPipeline display)
        {
            Point3d inletCenter = GetInletCenter();
            if (!inletCenter.IsValid) return;

            double angleRad = _windDirectionDegrees * Math.PI / 180.0;
            Vector3d inletNormal = new Vector3d(
                -Math.Sin(angleRad),
                Math.Cos(angleRad),
                0);

            Point3d curveOrigin = inletCenter + inletNormal * (_compassRadius * 0.2);

            var profilePoints = new System.Collections.Generic.List<Point3d>();
            int numPoints = 20;
            double maxHeight = _domainBounds.Max.Z - _domainBounds.Min.Z;
            double maxSpeed = 0;

            for (int i = 0; i <= numPoints; i++)
            {
                double z = (i / (double)numPoints) * maxHeight;
                double speed = ComputeWindSpeedAtHeight(z);
                if (speed > maxSpeed) maxSpeed = speed;

                profilePoints.Add(new Point3d(
                    curveOrigin.X + inletNormal.Y * speed * (_compassRadius / Math.Max(_windSpeed, 1.0)),
                    curveOrigin.Y - inletNormal.X * speed * (_compassRadius / Math.Max(_windSpeed, 1.0)),
                    _domainBounds.Min.Z + z));
            }

            if (profilePoints.Count >= 2)
            {
                var polyline = new Polyline(profilePoints);
                display.DrawPolyline(polyline, Color.Lime, 2);

                display.DrawLine(
                    new Line(
                        new Point3d(curveOrigin.X, curveOrigin.Y, _domainBounds.Min.Z),
                        new Point3d(curveOrigin.X, curveOrigin.Y, _domainBounds.Max.Z)),
                    Color.Gray, 1);

                double refZ = _domainBounds.Min.Z + _referenceHeight;
                double refSpeed = ComputeWindSpeedAtHeight(_referenceHeight);
                double scale = _compassRadius / Math.Max(_windSpeed, 1.0);
                Point3d refPoint = new Point3d(
                    curveOrigin.X + inletNormal.Y * refSpeed * scale,
                    curveOrigin.Y - inletNormal.X * refSpeed * scale,
                    refZ);

                display.DrawPoint(refPoint, PointStyle.RoundActivePoint, 8, Color.Red);

                var textPlane = new Plane(refPoint + new Vector3d(0, 0, 2), Vector3d.ZAxis);
                display.Draw3dText(
                    $"Zref={_referenceHeight:F1}m, Uref={_windSpeed:F1}m/s",
                    Color.Red,
                    textPlane,
                    _compassRadius * 0.08,
                    "Arial");
            }
        }

        private double ComputeWindSpeedAtHeight(double height)
        {
            if (height <= 0) return 0;

            switch (_windProfile)
            {
                case WindProfileType.PowerLaw:
                    return _windSpeed * Math.Pow(height / Math.Max(_referenceHeight, 0.1), _alpha);

                case WindProfileType.Logarithmic:
                    double z0 = Math.Max(_roughnessLength, 1e-6);
                    double kappa = Math.Max(_vonKarman, 0.1);
                    double zRef = Math.Max(_referenceHeight, 0.1);
                    double uStar = _windSpeed * kappa / Math.Log(zRef / z0);
                    return (uStar / kappa) * Math.Log(height / z0);

                case WindProfileType.Uniform:
                default:
                    return _windSpeed;
            }
        }

        private Point3d GetInletCenter()
        {
            if (!_domainBounds.IsValid) return Point3d.Unset;

            double angleRad = _windDirectionDegrees * Math.PI / 180.0;

            Point3d domainCenter = new Point3d(
                (_domainBounds.Min.X + _domainBounds.Max.X) / 2.0,
                (_domainBounds.Min.Y + _domainBounds.Max.Y) / 2.0,
                (_domainBounds.Min.Z + _domainBounds.Max.Z) / 2.0);

            Vector3d windDir = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);

            if (Math.Abs(windDir.X) > Math.Abs(windDir.Y))
            {
                return new Point3d(
                    windDir.X > 0 ? _domainBounds.Min.X : _domainBounds.Max.X,
                    domainCenter.Y,
                    domainCenter.Z);
            }
            else
            {
                return new Point3d(
                    domainCenter.X,
                    windDir.Y > 0 ? _domainBounds.Min.Y : _domainBounds.Max.Y,
                    domainCenter.Z);
            }
        }

        private void DrawArrowHead(DisplayPipeline display, Point3d tip, Vector3d dir, double size, Color color)
        {
            dir.Unitize();
            Vector3d perp = Vector3d.CrossProduct(dir, Vector3d.ZAxis);
            if (perp.Length < 1e-6) perp = Vector3d.CrossProduct(dir, Vector3d.XAxis);
            perp.Unitize();

            Point3d basePt = tip - dir * size;
            Point3d left = basePt + perp * size * 0.4;
            Point3d right = basePt - perp * size * 0.4;

            display.DrawLine(new Line(tip, left), color, 3);
            display.DrawLine(new Line(tip, right), color, 3);
            display.DrawLine(new Line(left, right), color, 2);
        }

        private void Draw2dCircle(DisplayPipeline display, int cx, int cy, int r, Color color, int thickness)
        {
            int segments = 32;
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

        private string GetDirectionText(double degrees)
        {
            string[] directions = { "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW" };
            int index = (int)((degrees + 11.25) / 22.5) % 16;
            return directions[index];
        }
    }

    public enum WindProfileType
    {
        Uniform = 0,
        PowerLaw = 1,
        Logarithmic = 2
    }
}
