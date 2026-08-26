using System;
using System.Drawing;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Special;

namespace GhGenerator
{
    class Program
    {
        static void Main(string[] args)
        {
            string outputPath = args.Length > 0 ? args[0] : @"AIJ_CaseA_Official.gh";
            string postCodePath = args.Length > 1 ? args[1] : @"AIJ_CaseA_Official_PostProcess.py";

            Console.WriteLine("=== AIJ Case A Official .gh Generator ===");
            Console.WriteLine("Output: " + outputPath);

            // Create a new GH document
            var doc = new GH_Document();

            // 1. GhPython PostProcess component
            var ghPythonGuid = new Guid("6d45f1cd-2b6c-4150-9633-7e7edf42f9a1");
            var ghPython = CreateComponent(doc, ghPythonGuid, 1400, 100, "GhPython PostProcess");
            if (ghPython != null && System.IO.File.Exists(postCodePath))
            {
                try {
                    var code = System.IO.File.ReadAllText(postCodePath);
                    // Set the Code property via reflection
                    var prop = ghPython.GetType().GetProperty("Code");
                    if (prop != null) prop.SetValue(ghPython, code);
                } catch (Exception ex) {
                    Console.WriteLine("  WARN: Could not set GhPython code: " + ex.Message);
                }
            }

            // 2. CityLBM components
            CreateComponent(doc, new Guid("C8F3E1D5-6B2A-4E7C-9A8F-2D4B5C7E8F9A"), 500, 100, "Create Scene");
            CreateComponent(doc, new Guid("D4E7F2A8-7C9B-5E8D-0B1A-3E5C6D9F8A2B"), 740, 100, "Add Buildings");
            CreateComponent(doc, new Guid("E8F4A2D1-7B3C-4E8D-9A5F-3D6E7C8B9A1E"), 980, 100, "Grid Generator");
            CreateComponent(doc, new Guid("F9A5B3E2-8C4D-4F7A-9B6E-2D5C7A8B9F1D"), 1220, 100, "Run Simulation");

            // 3. GH Native Box (Center Box)
            CreateComponent(doc, new Guid("722ccc01-0c7f-4030-ad33-c99bda4c90d9"), 100, 100, "Center Box");

            // 4. GH Native Mesh Brep
            CreateComponent(doc, new Guid("0a29d78e-3c9f-47d7-b77a-d47259d27ad6"), 260, 100, "Mesh Brep");

            // 5. Panel
            CreateComponent(doc, new Guid("57DA99BD-ECEB-4743-AEB4-2CFC1B0C32FE"), 1400, 300, "Panel");

            // Wires (simplified - actual wiring needs proper component instance IDs)
            Console.WriteLine("\nWARNING: Wire connections require manual setup in Grasshopper.");
            Console.WriteLine("Components have been placed on the canvas.");
            Console.WriteLine("Please connect them manually:");
            Console.WriteLine("  Box -> Mesh Brep -> AddBuildings.B");
            Console.WriteLine("  CreateScene -> AddBuildings.S");
            Console.WriteLine("  AddBuildings -> GridGenerator -> RunSimulation");
            Console.WriteLine("  RunSimulation -> GhPython PostProcess");
            Console.WriteLine("  GhPython PostProcess -> Panel");

            // Save
            var io = new Grasshopper.Kernel.GH_DocumentIO();
            io.Document = doc;
            bool saved = io.SaveAs(outputPath);

            if (saved)
            {
                var fi = new System.IO.FileInfo(outputPath);
                Console.WriteLine("\nSAVED: " + outputPath);
                Console.WriteLine("SIZE: " + fi.Length + " bytes");
            }
            else
            {
                Console.WriteLine("\nFAILED to save: " + outputPath);
            }
        }

        static IGH_DocumentObject CreateComponent(GH_Document doc, Guid guid, float x, float y, string name)
        {
            try
            {
                var proxy = Grasshopper.Instances.ComponentServer.EmitObjectProxy(guid);
                if (proxy == null)
                {
                    Console.WriteLine("  MISSING: " + name);
                    return null;
                }
                var comp = proxy.CreateInstance();
                comp.Attributes.Pivot = new PointF(x, y);
                doc.AddObject(comp, false);
                Console.WriteLine("  + " + name);
                return comp;
            }
            catch (Exception ex)
            {
                Console.WriteLine("  FAIL: " + name + " - " + ex.Message);
                return null;
            }
        }
    }
}
