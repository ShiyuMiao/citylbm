using System;
using System.Drawing;
using System.Reflection;
using Grasshopper.Kernel;
using CityLBM.Utils;

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

        public override Bitmap Icon
        {
            get { return IconLoader.Load("CityLBM.png"); }
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
                Version version = Assembly.GetExecutingAssembly().GetName().Version;
                return string.Format("{0}.{1}.{2}", version.Major, version.Minor, version.Build);
            }
        }

        public override string AssemblyVersion
        {
            get { return "0.5.0.0"; }
        }
    }
}
