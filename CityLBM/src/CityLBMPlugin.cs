using System;
using System.Drawing;
using System.Reflection;
using Grasshopper.Kernel;

namespace CityLBM
{
    /// <summary>
    /// CityLBM 插件主类
    /// 负责插件的加载和初始化
    /// </summary>
    public class CityLBMPlugin : GH_AssemblyInfo
    {
        public override string Name
        {
            get { return "CityLBM"; }
        }

        public override Bitmap? Icon
        {
            get { return null; }
        }

        public override string Description
        {
            get { return "CityLBM城市风场模拟Grasshopper插件"; }
        }

        public override Guid Id
        {
            get { return new Guid("A47D9F85-5CCF-40D0-A5E9-3F9C8E2B1A7F"); }
        }

        public override string AuthorName
        {
            get { return "CityLBM Development Team"; }
        }

        public override string AuthorContact
        {
            get { return "support@citylbm.local"; }
        }

        public override string Version
        {
            get
            {
                Assembly? asm = Assembly.GetExecutingAssembly();
                if (asm != null)
                {
                    Version? ver = asm.GetName().Version;
                    if (ver != null)
                    {
                        return string.Format("{0}.{1}.{2}", ver.Major, ver.Minor, ver.Build);
                    }
                }
                return "0.1.0";
            }
        }

        public override string AssemblyVersion
        {
            get { return "0.1.0.0"; }
        }
    }
}
