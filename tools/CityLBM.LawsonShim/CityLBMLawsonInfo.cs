using System;
using System.Drawing;
using Grasshopper.Kernel;

namespace CityLBM.LawsonShim
{
    public class CityLBMLawsonInfo : GH_AssemblyInfo
    {
        public override string Name => "CityLBM.Lawson";

        public override Bitmap Icon => null;

        public override string Description => "Lawson comfort component for CityLBM v0.2.0.";

        public override Guid Id => new Guid("9F5E2D0E-195E-4A3C-86C3-8D2D5B0E0200");

        public override string AuthorName => "Shiyu Miao";

        public override string AuthorContact => "https://github.com/ShiyuMiao/citylbm";

        public override string Version => "0.2.0";

        public override string AssemblyVersion => "0.2.0.0";
    }
}
