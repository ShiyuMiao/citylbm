using System;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
using GH_IO.Serialization;
using Rhino.Geometry;
using CityLBM.Core;

namespace CityLBM.Utils
{
    /// <summary>
    /// Scene 类的 Grasshopper 数据类型包装
    /// </summary>
    public class GH_Scene : GH_Goo<Scene>
    {
        public GH_Scene()
        {
            Value = new Scene();
        }

        public GH_Scene(Scene scene)
        {
            Value = scene;
        }

        public override IGH_Goo Duplicate()
        {
            return new GH_Scene(Value);
        }

        public override bool IsValid
        {
            get { return Value != null; }
        }

        public override string TypeName
        {
            get { return "CityLBM Scene"; }
        }

        public override string TypeDescription
        {
            get { return "CityLBM城市风场模拟场景"; }
        }

        public override string ToString()
        {
            if (Value == null) return "Null Scene";
            string msg = Value.Validate(out string error) ? "Valid" : "Invalid: " + error;
            string domainMode = Value.UseAbsoluteDomain ? "[绝对域]" :
                               (Value.UseCustomDomain ? "[自定义域]" : "[自动扩展]");
            return $"Scene: {Value.Name} ({msg}) {domainMode}";
        }

        public override bool CastFrom(object source)
        {
            if (source is Scene scene)
            {
                Value = scene;
                return true;
            }
            return false;
        }

        public override bool CastTo<T>(ref T target)
        {
            if (typeof(T).IsAssignableFrom(typeof(Scene)))
            {
                target = (T)(object)Value;
                return true;
            }
            return false;
        }

        public override bool Read(GH_IReader reader)
        {
            try
            {
                string name = reader.GetString("Name");
                double windSpeed = reader.GetDouble("WindSpeed");
                double windDirX = reader.GetDouble("WindDirX");
                double windDirY = reader.GetDouble("WindDirY");
                double windDirZ = reader.GetDouble("WindDirZ");
                double groundHeight = reader.GetDouble("GroundHeight");
                double extRatio = reader.GetDouble("ExtRatio");
                bool useCustom = reader.GetBoolean("UseCustomDomain");
                // 读取绝对域设置（向后兼容：旧文件可能没有此字段）
                bool useAbsolute = false;
                try { useAbsolute = reader.GetBoolean("UseAbsoluteDomain"); } catch { }

                Value = new Scene(name);
                Value.WindSpeed = windSpeed;
                Value.WindDirection = new Vector3d(windDirX, windDirY, windDirZ);
                Value.GroundHeight = groundHeight;
                Value.DomainExtensionRatio = extRatio;

                // 优先处理绝对域（优先级高于偏移量模式）
                if (useAbsolute)
                {
                    try
                    {
                        var absDom = new AbsoluteDomainDefinition
                        {
                            Lx = reader.GetDouble("AbsDomLx"),
                            Ly = reader.GetDouble("AbsDomLy"),
                            Lz = reader.GetDouble("AbsDomLz")
                        };
                        Value.SetAbsoluteDomain(absDom);
                    }
                    catch
                    {
                        // 读取失败则回退到自动扩展
                        Value.ClearCustomDomain();
                    }
                }
                else if (useCustom)
                {
                    var domDef = new DomainDefinition
                    {
                        XMinus = reader.GetDouble("DomXMinus"),
                        XPlus = reader.GetDouble("DomXPlus"),
                        YMinus = reader.GetDouble("DomYMinus"),
                        YPlus = reader.GetDouble("DomYPlus"),
                        Height = reader.GetDouble("DomHeight")
                    };
                    Value.SetCustomDomain(domDef);
                }

                return true;
            }
            catch
            {
                return false;
            }
        }

        public override bool Write(GH_IWriter writer)
        {
            if (Value == null) return false;

            writer.SetString("Name", Value.Name);
            writer.SetDouble("WindSpeed", Value.WindSpeed);
            writer.SetDouble("WindDirX", Value.WindDirection.X);
            writer.SetDouble("WindDirY", Value.WindDirection.Y);
            writer.SetDouble("WindDirZ", Value.WindDirection.Z);
            writer.SetDouble("GroundHeight", Value.GroundHeight);
            writer.SetDouble("ExtRatio", Value.DomainExtensionRatio);
            writer.SetBoolean("UseCustomDomain", Value.UseCustomDomain);
            writer.SetBoolean("UseAbsoluteDomain", Value.UseAbsoluteDomain);

            // 写入偏移量自定义域
            if (Value.UseCustomDomain && Value.CustomDomain.HasValue)
            {
                var dom = Value.CustomDomain.Value;
                writer.SetDouble("DomXMinus", dom.XMinus);
                writer.SetDouble("DomXPlus", dom.XPlus);
                writer.SetDouble("DomYMinus", dom.YMinus);
                writer.SetDouble("DomYPlus", dom.YPlus);
                writer.SetDouble("DomHeight", dom.Height);
            }

            // 写入绝对尺寸域
            if (Value.UseAbsoluteDomain && Value.AbsoluteDomain.HasValue)
            {
                var absDom = Value.AbsoluteDomain.Value;
                writer.SetDouble("AbsDomLx", absDom.Lx);
                writer.SetDouble("AbsDomLy", absDom.Ly);
                writer.SetDouble("AbsDomLz", absDom.Lz);
            }

            return true;
        }
    }
}
