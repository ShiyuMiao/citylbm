using System;
using System.Drawing;
using System.IO;
using System.Reflection;

namespace CityLBM.Utils
{
    /// <summary>
    /// 图标加载工具类
    /// 多策略加载：嵌入资源 → 同目录 Icons 文件夹 → 内嵌 Base64 默认图标
    /// </summary>
    public static class IconLoader
    {
        // 内嵌默认图标的 Base64 编码（24x24 蓝色方块，保证不为 null）
        private const string DefaultIconBase64 =
            "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAhElEQVR4nGNgGAWjYBSMglEwCk" +
            "YBmDmZuY/wMDIyMgBCkAsRixwWwMDAwMDOAEpArGLHBbAwMDAwM4ASkCsYscFsDAwMDAzgBKQKxi" +
            "xwWwMDAwMDOAEpArGLHBbAwMDAwM4ASkCsYscFsDAwMDAzgBKQKxiJmHgAADXhE1CjlPmhAAAAABJ" +
            "RU5ErkJggg==";

        private static readonly string _assemblyDir;

        static IconLoader()
        {
            string location = Assembly.GetExecutingAssembly().Location;
            _assemblyDir = Path.GetDirectoryName(location) ?? "";
        }

        /// <summary>
        /// 加载图标 Bitmap
        /// </summary>
        /// <param name="iconName">图标文件名，如 "CreateScene.png"</param>
        /// <returns>Bitmap 对象，永远不为 null</returns>
        public static Bitmap Load(string iconName)
        {
            try
            {
                // 方式1：从嵌入资源加载
                var assembly = Assembly.GetExecutingAssembly();
                string resourceName = $"CityLBM.src.Resources.Icons.{iconName}";
                using (var stream = assembly.GetManifestResourceStream(resourceName))
                {
                    if (stream != null)
                        return NormalizeIcon(new Bitmap(stream));
                }

                // 方式2：从 gha 同级 Icons/ 目录加载
                string filePath = Path.Combine(_assemblyDir, "Icons", iconName);
                if (File.Exists(filePath))
                    return NormalizeIcon(new Bitmap(filePath));

                // 方式3：检查 gha 上级目录的 Icons/（处理 CityLBM.gha 在子目录的情况）
                string parentDir = Path.GetDirectoryName(_assemblyDir);
                if (!string.IsNullOrEmpty(parentDir))
                {
                    filePath = Path.Combine(parentDir, "Icons", iconName);
                    if (File.Exists(filePath))
                        return NormalizeIcon(new Bitmap(filePath));
                }
            }
            catch
            {
                // 静默失败
            }

            // 回退：返回默认蓝色图标
            return LoadDefaultIcon();
        }

        private static Bitmap NormalizeIcon(Bitmap source)
        {
            if (source.Width == 24 && source.Height == 24)
                return source;

            var scaled = new Bitmap(24, 24);
            using (var g = Graphics.FromImage(scaled))
            {
                g.Clear(Color.Transparent);
                g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic;
                g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.HighQuality;
                g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.HighQuality;
                g.DrawImage(source, new Rectangle(0, 0, 24, 24));
            }
            source.Dispose();
            return scaled;
        }

        private static Bitmap _defaultIcon;
        private static readonly object _defaultLock = new object();

        private static Bitmap LoadDefaultIcon()
        {
            if (_defaultIcon != null) return _defaultIcon;
            lock (_defaultLock)
            {
                if (_defaultIcon != null) return _defaultIcon;
                try
                {
                    byte[] bytes = Convert.FromBase64String(DefaultIconBase64);
                    using (var ms = new MemoryStream(bytes))
                    {
                        _defaultIcon = new Bitmap(ms);
                    }
                }
                catch
                {
                    // 最终回退：创建一个 24x24 蓝色 Bitmap
                    _defaultIcon = new Bitmap(24, 24);
                    using (var g = Graphics.FromImage(_defaultIcon))
                    {
                        g.Clear(Color.FromArgb(26, 111, 196)); // #1a6fc4
                    }
                }
            }
            return _defaultIcon;
        }
    }
}
