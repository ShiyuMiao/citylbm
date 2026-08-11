using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace CityLBM
{
    /// <summary>
    /// Grasshopper assembly metadata for the CityLBM plugin.
    /// </summary>
    public class CityLBMPlugin : GH_AssemblyInfo
    {
        public const string PluginVersion = "0.4.0-rc";
        public const string PluginAssemblyVersion = "0.4.0.0";

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
            get { return "CityLBM urban wind simulation Grasshopper plugin (v0.4.0-rc accuracy-diagnostic line)"; }
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
            get { return PluginVersion; }
        }

        public override string AssemblyVersion
        {
            get { return PluginAssemblyVersion; }
        }
    }
}
