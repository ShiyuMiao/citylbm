using System;
using System.Collections.Generic;
using System.Drawing;
using Rhino.Display;
using Rhino.Geometry;

namespace CityLBM.Rendering
{
    /// <summary>
    /// 计算域预览 DisplayConduit
    /// 在 Rhino 视口中绘制 AIJ 规范计算域、边界标注和半透明材质区分
    /// </summary>
    public class DomainPreviewerConduit : DisplayConduit
    {
        // ═══════════════════════════════════════════════════════════════
        // 渲染数据（线程安全访问）
        // ═══════════════════════════════════════════════════════════════
        private readonly object _lock = new object();
        private bool _enabled = false;

        // 计算域几何
        private BoundingBox _domainBox = BoundingBox.Unset;
        private List<Line> _domainEdges = new List<Line>();
        private Mesh _inletMesh;
        private Mesh _outletMesh;
        private Mesh _wallMesh;

        // 风场参数（用于确定入口/出口）
        private double _windDirectionDegrees = 0.0;

        // 可视化参数
        private Color _inletColor = Color.FromArgb(100, 0, 150, 255);    // 半透明蓝
        private Color _outletColor = Color.FromArgb(100, 255, 100, 0);   // 半透明橙
        private Color _wallColor = Color.FromArgb(80, 150, 150, 150);    // 半透明灰
        private Color _edgeColor = Color.White;

        /// <summary>
        /// 更新计算域数据
        /// </summary>
        public void SetDomain(BoundingBox domainBox, double windDirectionDegrees)
        {
            lock (_lock)
            {
                _domainBox = domainBox;
                _windDirectionDegrees = windDirectionDegrees;
                _enabled = domainBox.IsValid;

                if (_enabled)
                {
                    BuildDomainGeometry();
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
                _enabled = false;
                _domainBox = BoundingBox.Unset;
                _domainEdges.Clear();
                _inletMesh = null;
                _outletMesh = null;
                _wallMesh = null;
            }
        }

        // ═══════════════════════════════════════════════════════════════
        // 构建计算域几何
        // ═══════════════════════════════════════════════════════════════

        private void BuildDomainGeometry()
        {
            _domainEdges.Clear();

            // 计算域的8个角点
            Point3d[] corners = _domainBox.GetCorners();

            // 底面边 (0-1, 1-2, 2-3, 3-0)
            _domainEdges.Add(new Line(corners[0], corners[1]));
            _domainEdges.Add(new Line(corners[1], corners[2]));
            _domainEdges.Add(new Line(corners[2], corners[3]));
            _domainEdges.Add(new Line(corners[3], corners[0]));

            // 顶面边 (4-5, 5-6, 6-7, 7-4)
            _domainEdges.Add(new Line(corners[4], corners[5]));
            _domainEdges.Add(new Line(corners[5], corners[6]));
            _domainEdges.Add(new Line(corners[6], corners[7]));
            _domainEdges.Add(new Line(corners[7], corners[4]));

            // 垂直边 (0-4, 1-5, 2-6, 3-7)
            _domainEdges.Add(new Line(corners[0], corners[4]));
            _domainEdges.Add(new Line(corners[1], corners[5]));
            _domainEdges.Add(new Line(corners[2], corners[6]));
            _domainEdges.Add(new Line(corners[3], corners[7]));

            // 确定入口/出口面（基于风向）
            DetermineBoundaryFaces(corners);
        }

        /// <summary>
        /// 根据风向确定入口、出口和壁面面
        /// </summary>
        private void DetermineBoundaryFaces(Point3d[] corners)
        {
            // 风向转换为向量（0=北风，从北来）
            double angleRad = _windDirectionDegrees * Math.PI / 180.0;
            Vector3d windDir = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);

            // 计算六个面的中心点法向
            // X- 面 (左): corners[0,3,7,4]
            // X+ 面 (右): corners[1,2,6,5]
            // Y- 面 (前): corners[0,1,5,4]
            // Y+ 面 (后): corners[3,2,6,7]
            // Z- 面 (底): corners[0,1,2,3]
            // Z+ 面 (顶): corners[4,5,6,7]

            var faces = new List<(Mesh mesh, Vector3d normal, string name, BoundaryType type)>();

            // X- 面
            var xNegMesh = CreateQuadMesh(corners[0], corners[3], corners[7], corners[4]);
            faces.Add((xNegMesh, new Vector3d(-1, 0, 0), "X-", BoundaryType.Wall));

            // X+ 面
            var xPosMesh = CreateQuadMesh(corners[1], corners[2], corners[6], corners[5]);
            faces.Add((xPosMesh, new Vector3d(1, 0, 0), "X+", BoundaryType.Wall));

            // Y- 面
            var yNegMesh = CreateQuadMesh(corners[0], corners[1], corners[5], corners[4]);
            faces.Add((yNegMesh, new Vector3d(0, -1, 0), "Y-", BoundaryType.Wall));

            // Y+ 面
            var yPosMesh = CreateQuadMesh(corners[3], corners[2], corners[6], corners[7]);
            faces.Add((yPosMesh, new Vector3d(0, 1, 0), "Y+", BoundaryType.Wall));

            // Z- 面 (地面)
            var zNegMesh = CreateQuadMesh(corners[0], corners[1], corners[2], corners[3]);
            faces.Add((zNegMesh, new Vector3d(0, 0, -1), "Ground", BoundaryType.Wall));

            // Z+ 面 (顶部)
            var zPosMesh = CreateQuadMesh(corners[4], corners[5], corners[6], corners[7]);
            faces.Add((zPosMesh, new Vector3d(0, 0, 1), "Top", BoundaryType.Wall));

            // 根据风向确定入口（上游）和出口（下游）
            // 入口 = 与来风方向相反的面（风从该面进入）
            // 出口 = 与来风方向相同的面（风从该面流出）

            double maxInletDot = -1;
            double maxOutletDot = -1;
            int inletIndex = -1;
            int outletIndex = -1;

            for (int i = 0; i < faces.Count; i++)
            {
                double dot = faces[i].normal * windDir;

                // 入口：法向与风向相反（点积最小/最负）
                if (dot < maxInletDot)
                {
                    maxInletDot = dot;
                    inletIndex = i;
                }

                // 出口：法向与风向相同（点积最大/最正）
                if (dot > maxOutletDot)
                {
                    maxOutletDot = dot;
                    outletIndex = i;
                }
            }

            // 构建入口、出口、壁面网格
            _inletMesh = new Mesh();
            _outletMesh = new Mesh();
            _wallMesh = new Mesh();

            for (int i = 0; i < faces.Count; i++)
            {
                if (i == inletIndex)
                {
                    _inletMesh.Append(faces[i].mesh);
                }
                else if (i == outletIndex)
                {
                    _outletMesh.Append(faces[i].mesh);
                }
                else
                {
                    _wallMesh.Append(faces[i].mesh);
                }
            }

            // 设置顶点颜色
            if (_inletMesh != null && _inletMesh.Vertices.Count > 0)
            {
                _inletMesh.VertexColors.CreateMonotoneMesh(_inletColor);
            }
            if (_outletMesh != null && _outletMesh.Vertices.Count > 0)
            {
                _outletMesh.VertexColors.CreateMonotoneMesh(_outletColor);
            }
            if (_wallMesh != null && _wallMesh.Vertices.Count > 0)
            {
                _wallMesh.VertexColors.CreateMonotoneMesh(_wallColor);
            }
        }

        private Mesh CreateQuadMesh(Point3d p0, Point3d p1, Point3d p2, Point3d p3)
        {
            var mesh = new Mesh();
            mesh.Vertices.Add(p0);
            mesh.Vertices.Add(p1);
            mesh.Vertices.Add(p2);
            mesh.Vertices.Add(p3);
            mesh.Faces.AddFace(0, 1, 2, 3);
            mesh.Normals.ComputeNormals();
            return mesh;
        }

        // ═══════════════════════════════════════════════════════════════
        // DisplayConduit 渲染回调
        // ═══════════════════════════════════════════════════════════════

        protected override void DrawOverlay(DrawEventArgs e)
        {
            lock (_lock)
            {
                if (!_enabled || !_domainBox.IsValid) return;

                // 绘制半透明面
                DrawShadedFaces(e.Display);

                // 绘制边框线
                DrawEdges(e.Display);

                // 绘制边界标注
                DrawBoundaryLabels(e.Display);

                // 绘制尺寸标注
                DrawDimensionLabels(e.Display);
            }
        }

        /// <summary>
        /// 绘制半透明面
        /// </summary>
        private void DrawShadedFaces(DisplayPipeline display)
        {
            // 使用 DrawMeshFalseColors 绘制半透明面
            if (_inletMesh != null && _inletMesh.Faces.Count > 0)
            {
                display.DrawMeshFalseColors(_inletMesh);
            }
            if (_outletMesh != null && _outletMesh.Faces.Count > 0)
            {
                display.DrawMeshFalseColors(_outletMesh);
            }
            if (_wallMesh != null && _wallMesh.Faces.Count > 0)
            {
                display.DrawMeshFalseColors(_wallMesh);
            }
        }

        /// <summary>
        /// 绘制边框线
        /// </summary>
        private void DrawEdges(DisplayPipeline display)
        {
            foreach (var edge in _domainEdges)
            {
                display.DrawLine(edge, _edgeColor, 2);
            }
        }

        /// <summary>
        /// 绘制边界条件标注
        /// </summary>
        private void DrawBoundaryLabels(DisplayPipeline display)
        {
            Point3d[] corners = _domainBox.GetCorners();

            // 计算各面中心
            Point3d centerXNeg = (corners[0] + corners[3] + corners[7] + corners[4]) / 4.0;
            Point3d centerXPos = (corners[1] + corners[2] + corners[6] + corners[5]) / 4.0;
            Point3d centerYNeg = (corners[0] + corners[1] + corners[5] + corners[4]) / 4.0;
            Point3d centerYPos = (corners[3] + corners[2] + corners[6] + corners[7]) / 4.0;
            Point3d centerZNeg = (corners[0] + corners[1] + corners[2] + corners[3]) / 4.0;
            Point3d centerZPos = (corners[4] + corners[5] + corners[6] + corners[7]) / 4.0;

            // 风向向量
            double angleRad = _windDirectionDegrees * Math.PI / 180.0;
            Vector3d windDir = new Vector3d(
                Math.Sin(angleRad),
                -Math.Cos(angleRad),
                0);

            // 确定各面类型
            DrawFaceLabel(display, centerXNeg, new Vector3d(-1, 0, 0), windDir, "X-");
            DrawFaceLabel(display, centerXPos, new Vector3d(1, 0, 0), windDir, "X+");
            DrawFaceLabel(display, centerYNeg, new Vector3d(0, -1, 0), windDir, "Y-");
            DrawFaceLabel(display, centerYPos, new Vector3d(0, 1, 0), windDir, "Y+");
            DrawFaceLabel(display, centerZNeg, new Vector3d(0, 0, -1), windDir, "Ground");
            DrawFaceLabel(display, centerZPos, new Vector3d(0, 0, 1), windDir, "Top");
        }

        /// <summary>
        /// 绘制单个面的标签
        /// </summary>
        private void DrawFaceLabel(DisplayPipeline display, Point3d center, Vector3d normal,
            Vector3d windDir, string faceName)
        {
            double dot = normal * windDir;
            string label;
            Color color;

            if (dot < -0.7) // 入口
            {
                label = "Inlet\n(Velocity)";
                color = Color.Cyan;
            }
            else if (dot > 0.7) // 出口
            {
                label = "Outlet\n(Pressure=0)";
                color = Color.Orange;
            }
            else if (faceName == "Ground")
            {
                label = "Ground\n(No-Slip)";
                color = Color.Gray;
            }
            else if (faceName == "Top")
            {
                label = "Top\n(Slip)";
                color = Color.LightGray;
            }
            else // 侧壁
            {
                label = "Side\n(Slip)";
                color = Color.LightGray;
            }

            // 创建文字平面（面向相机）
            var plane = new Plane(center + normal * 0.5, normal);
            display.Draw3dText(label, color, plane, 1.0, "Arial");
        }

        /// <summary>
        /// 绘制尺寸标注
        /// </summary>
        private void DrawDimensionLabels(DisplayPipeline display)
        {
            Point3d[] corners = _domainBox.GetCorners();

            double lx = _domainBox.Max.X - _domainBox.Min.X;
            double ly = _domainBox.Max.Y - _domainBox.Min.Y;
            double lz = _domainBox.Max.Z - _domainBox.Min.Z;

            // X 尺寸（底面前边）
            Point3d xLabelPos = (corners[0] + corners[1]) / 2.0 - new Vector3d(0, 0, lz * 0.05);
            var xPlane = new Plane(xLabelPos, -Vector3d.YAxis);
            display.Draw3dText($"Lx={lx:F1}m", Color.White, xPlane, 1.0, "Arial");

            // Y 尺寸（底面左侧）
            Point3d yLabelPos = (corners[0] + corners[3]) / 2.0 - new Vector3d(0, 0, lz * 0.05);
            var yPlane = new Plane(yLabelPos, Vector3d.XAxis);
            display.Draw3dText($"Ly={ly:F1}m", Color.White, yPlane, 1.0, "Arial");

            // Z 尺寸（左前垂直边）
            Point3d zLabelPos = (corners[0] + corners[4]) / 2.0 + new Vector3d(lx * 0.05, 0, 0);
            var zPlane = new Plane(zLabelPos, Vector3d.XAxis);
            display.Draw3dText($"Lz={lz:F1}m", Color.White, zPlane, 1.0, "Arial");
        }

        private enum BoundaryType
        {
            Inlet,
            Outlet,
            Wall
        }
    }
}
