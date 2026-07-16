using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using Grasshopper.Kernel;

namespace CityLBM.LawsonShim
{
    public class LawsonComfortComponent : GH_Component
    {
        private static readonly double[] ComfortThresholds =
        {
            4.0,
            6.0,
            8.0,
            10.0,
        };

        public LawsonComfortComponent()
            : base("Lawson Comfort", "Lawson",
                   "Classify pedestrian wind comfort and safety from wind speed values.",
                   "CityLBM", "3 | Results")
        {
        }

        public override Guid ComponentGuid => new Guid("C4E8F2A1-7B3D-4C5E-9F1A-2D3E4F5A6B7C");

        protected override Bitmap Icon => null;

        protected override void RegisterInputParams(GH_InputParamManager pManager)
        {
            pManager.AddNumberParameter(
                "Wind Speed",
                "V",
                "Wind speed values in m/s. Connect sampled ReadVTK speeds or a list of point speeds.",
                GH_ParamAccess.list);

            pManager.AddIntegerParameter(
                "Mode",
                "M",
                "Assessment mode: 0 = comfort, 1 = safety, 2 = comfort and safety.",
                GH_ParamAccess.item,
                0);

            pManager.AddIntegerParameter(
                "Activity",
                "A",
                "Activity type: 0 = sitting, 1 = standing, 2 = walking, 3 = brisk walking, 4 = general.",
                GH_ParamAccess.item,
                4);

            pManager[1].Optional = true;
            pManager[2].Optional = true;
        }

        protected override void RegisterOutputParams(GH_OutputParamManager pManager)
        {
            pManager.AddIntegerParameter(
                "Category",
                "C",
                "Comfort category index: 0 = A, 1 = B, 2 = C, 3 = D, 4 = E, -1 = not assessed.",
                GH_ParamAccess.list);

            pManager.AddTextParameter(
                "Category Name",
                "CN",
                "Comfort category label: A, B, C, D, or E.",
                GH_ParamAccess.list);

            pManager.AddBooleanParameter(
                "Is Comfortable",
                "OK",
                "True when the wind speed is acceptable for the selected activity.",
                GH_ParamAccess.list);

            pManager.AddTextParameter(
                "Info",
                "I",
                "Summary statistics for the assessment.",
                GH_ParamAccess.item);

            pManager.AddIntegerParameter(
                "Safety Level",
                "S",
                "Safety level: 0 = safe, 1 = unsafe for vulnerable users, 2 = dangerous, -1 = not assessed.",
                GH_ParamAccess.list);
        }

        protected override void SolveInstance(IGH_DataAccess DA)
        {
            var windSpeeds = new List<double>();
            int mode = 0;
            int activity = 4;

            if (!DA.GetDataList(0, windSpeeds))
            {
                return;
            }

            DA.GetData(1, ref mode);
            DA.GetData(2, ref activity);

            if (windSpeeds.Count == 0)
            {
                AddRuntimeMessage(GH_RuntimeMessageLevel.Error, "Wind speed list is empty.");
                return;
            }

            mode = Math.Max(0, Math.Min(2, mode));
            activity = Math.Max(0, Math.Min(4, activity));

            var categories = new List<int>();
            var categoryNames = new List<string>();
            var isComfortable = new List<bool>();
            var safetyLevels = new List<int>();

            if (mode == 0 || mode == 2)
            {
                foreach (double speed in windSpeeds)
                {
                    int category = GetComfortCategory(speed);
                    categories.Add(category);
                    categoryNames.Add(GetCategoryName(category));
                    isComfortable.Add(IsComfortableForActivity(speed, activity));
                }
            }
            else
            {
                categories.AddRange(Enumerable.Repeat(-1, windSpeeds.Count));
                categoryNames.AddRange(Enumerable.Repeat("N/A", windSpeeds.Count));
                isComfortable.AddRange(Enumerable.Repeat(false, windSpeeds.Count));
            }

            if (mode == 1 || mode == 2)
            {
                foreach (double speed in windSpeeds)
                {
                    safetyLevels.Add(GetSafetyLevel(speed));
                }
            }
            else
            {
                safetyLevels.AddRange(Enumerable.Repeat(-1, windSpeeds.Count));
            }

            double maxSpeed = windSpeeds.Max();
            double avgSpeed = windSpeeds.Average();
            int categoryECount = windSpeeds.Count(speed => speed > 10.0);
            double categoryERatio = (double)categoryECount / windSpeeds.Count;

            string info =
                "Lawson comfort assessment\n" +
                $"  Points: {windSpeeds.Count}\n" +
                $"  Max speed: {maxSpeed:F2} m/s\n" +
                $"  Mean speed: {avgSpeed:F2} m/s\n" +
                $"  Category E ratio: {categoryERatio:P1}\n" +
                $"  Activity: {GetActivityName(activity)}";

            DA.SetDataList(0, categories);
            DA.SetDataList(1, categoryNames);
            DA.SetDataList(2, isComfortable);
            DA.SetData(3, info);
            DA.SetDataList(4, safetyLevels);
        }

        private static int GetComfortCategory(double speed)
        {
            if (speed <= 4.0) return 0;
            if (speed <= 6.0) return 1;
            if (speed <= 8.0) return 2;
            if (speed <= 10.0) return 3;
            return 4;
        }

        private static string GetCategoryName(int category)
        {
            switch (category)
            {
                case 0: return "A";
                case 1: return "B";
                case 2: return "C";
                case 3: return "D";
                case 4: return "E";
                default: return "N/A";
            }
        }

        private static bool IsComfortableForActivity(double speed, int activity)
        {
            double threshold = activity == 4 ? 10.0 : ComfortThresholds[activity];
            return speed <= threshold;
        }

        private static int GetSafetyLevel(double speed)
        {
            if (speed <= 15.0) return 0;
            if (speed <= 20.0) return 1;
            return 2;
        }

        private static string GetActivityName(int activity)
        {
            switch (activity)
            {
                case 0: return "Sitting (A)";
                case 1: return "Standing (B)";
                case 2: return "Walking (C)";
                case 3: return "Brisk walking (D)";
                case 4: return "General";
                default: return "Unknown";
            }
        }
    }
}
