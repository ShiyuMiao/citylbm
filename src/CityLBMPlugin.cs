using System;
using System.Drawing;
using System.Reflection;
using Grasshopper.Kernel;
using CityLBM.Utils;

namespace CityLBM
{
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
            get { return "CityLBM urban wind simulation workflow for Grasshopper and FluidX3D."; }
        }

        public override Guid Id
        {
            get { return new Guid("A47D9F85-5CCF-40D0-A5E9-3F9C8E2B1A7F"); }
        }

        public override string AuthorName
        {
            get { return "Shiyu Miao"; }
        }

        public override string AuthorContact
        {
            get { return "miaoshiyu@mail.dlut.edu.cn"; }
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
            get { return "0.4.0.0"; }
        }
    }
}
