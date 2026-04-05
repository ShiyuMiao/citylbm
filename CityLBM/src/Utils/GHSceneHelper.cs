using System;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;
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
            return $"Scene: {Value.Name} ({msg})";
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
    }
}
