using System.Collections;
using System.Diagnostics;
using System.Globalization;
using System.Threading;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Debug = UnityEngine.Debug;

namespace AWDK.AgentTools.Tests
{
    public class ZFightScanTests
    {
        [SetUp]
        public void SetUp() => TestScene.Fresh();

        [Test]
        public void CoplanarOverlappingQuads_ReportOnePairWithOverlapArea()
        {
            TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero);
            TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(0.5f, 0, 0));

            var report = ZFightScan.RunBlocking();

            StringAssert.EndsWith("PAIRS=1 COMPLETE", report);
            Assert.AreEqual(1, ZFightScan.LastPairs.Count);
            Assert.AreEqual(0.5f, ZFightScan.LastPairs[0].Area, 1e-3f);
        }

        [Test]
        public void QuadOffsetByFiveMillimetres_IsNotAPair()
        {
            TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero);
            TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(0.5f, 0.005f, 0));

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking());
        }

        [Test]
        public void OppositeFacingQuads_OnlyReportedWhenRequested()
        {
            TestScene.MeshObject("Up", TestScene.Quad(1f), Vector3.zero);
            TestScene.MeshObject("Down", TestScene.Quad(1f, faceDown: true), new Vector3(0.25f, 0, 0));

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking());
            StringAssert.EndsWith("PAIRS=1 COMPLETE", ZFightScan.RunBlocking(includeOppositeFacing: true));
            Assert.AreEqual(0.75f, ZFightScan.LastPairs[0].Area, 1e-3f);
        }

        [Test]
        public void OverlapInsideOneRenderer_OnlyReportedWithIncludeSelf()
        {
            TestScene.MeshObject("Self", TestScene.TwoQuads(1f, 0.5f), Vector3.zero);

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking());
            StringAssert.EndsWith("PAIRS=1 COMPLETE", ZFightScan.RunBlocking(includeSelf: true));
            Assert.IsTrue(ZFightScan.LastPairs[0].Self);
            Assert.AreEqual(0.5f, ZFightScan.LastPairs[0].Area, 1e-3f);
        }

        [Test]
        public void AdjacentTrianglesOfOneMesh_AreNotSelfOverlaps()
        {
            TestScene.MeshObject("Grid", TestScene.Grid(20, 4f, false), Vector3.zero);

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking(includeSelf: true));
        }

        [Test]
        public void EdgeToEdgeTiles_AreNotAPair()
        {
            TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero);
            TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(1f, 0, 0));

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking(minOverlapArea: 0f));
        }

        [Test]
        public void FarFromOriginWithTinyTilt_StillFound()
        {
            // Regression: the original plane-bucket key used the plane offset n·p, which for a 0.05° tilt
            // 600 m from the origin differs by ~0.5 m, so the two quads never met in a bucket.
            var p = new Vector3(500f, 20f, 300f);
            TestScene.MeshObject("A", TestScene.Quad(1f), p);
            TestScene.MeshObject("B", TestScene.Quad(1f), p + new Vector3(0.5f, 0, 0), Quaternion.Euler(0.05f, 0, 0));

            StringAssert.EndsWith("PAIRS=1 COMPLETE", ZFightScan.RunBlocking());
            Assert.AreEqual(0.5f, ZFightScan.LastPairs[0].Area, 5e-3f);
        }

        [Test]
        public void TransparentMaterial_IsSkipped()
        {
            var glass = TestScene.Unlit(Color.white);
            glass.renderQueue = 3000;
            TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero);
            TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(0.5f, 0, 0), glass);

            var report = ZFightScan.RunBlocking();
            StringAssert.EndsWith("PAIRS=0 COMPLETE", report);
            StringAssert.Contains("skippedTransparentSubmeshes=1", report);
        }

        [Test]
        public void DifferentLodLevels_AreNotAPair()
        {
            var root = new GameObject("Lod");
            var lod0 = TestScene.MeshObject("LOD0", TestScene.Quad(1f), Vector3.zero, null, root.transform);
            var lod1 = TestScene.MeshObject("LOD1", TestScene.Quad(1f), Vector3.zero, null, root.transform);
            root.AddComponent<LODGroup>().SetLODs(new[]
            {
                new LOD(0.5f, new Renderer[] { lod0.GetComponent<Renderer>() }),
                new LOD(0.1f, new Renderer[] { lod1.GetComponent<Renderer>() }),
            });

            StringAssert.EndsWith("PAIRS=0 COMPLETE", ZFightScan.RunBlocking());
        }

        [Test]
        public void RootPath_LimitsTheScan()
        {
            var area = new GameObject("Area");
            TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero, null, area.transform);
            TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(0.5f, 0, 0), null, area.transform);
            TestScene.MeshObject("C", TestScene.Quad(1f), new Vector3(0, 0, 0.5f));

            StringAssert.EndsWith("PAIRS=1 COMPLETE", ZFightScan.RunBlocking("Area"));
            StringAssert.EndsWith("PAIRS=3 COMPLETE", ZFightScan.RunBlocking());
            StringAssert.StartsWith("ERROR", ZFightScan.RunBlocking("Nope/Missing"));
        }

        [Test]
        public void Report_UsesInvariantCulture()
        {
            var prev = Thread.CurrentThread.CurrentCulture;
            try
            {
                Thread.CurrentThread.CurrentCulture = new CultureInfo("de-DE");
                TestScene.MeshObject("A", TestScene.Quad(1f), Vector3.zero);
                TestScene.MeshObject("B", TestScene.Quad(1f), new Vector3(0.5f, 0, 0));
                var report = ZFightScan.RunBlocking();
                StringAssert.Contains("0.5000 m2", report);
                StringAssert.Contains("planeEps=0.0015", report);
            }
            finally { Thread.CurrentThread.CurrentCulture = prev; }
        }

        /// <summary>
        /// Two coplanar 50 x 50 m grids of 100,352 triangles each (different diagonals), scanned through
        /// Start/Status on EditorApplication.update like an MCP client would.
        /// </summary>
        [UnityTest]
        public IEnumerator LargeCoplanarGrids_CompleteInSlices()
        {
            const int cells = 224;
            TestScene.MeshObject("GridA", TestScene.Grid(cells, 50f, false), Vector3.zero);
            TestScene.MeshObject("GridB", TestScene.Grid(cells, 50f, true), Vector3.zero);

            var sw = Stopwatch.StartNew();
            StringAssert.StartsWith("STARTED", ZFightScan.Start(includeSelf: true));
            string status = ZFightScan.Status();
            int polls = 1;
            while (!status.EndsWith("COMPLETE") && sw.Elapsed.TotalSeconds < 120)
            {
                yield return null;
                status = ZFightScan.Status();
                polls++;
            }
            var job = ZFightScan.LastJob;
            Debug.Log(string.Format(CultureInfo.InvariantCulture,
                "[LargeGrid] tris={0} elapsed={1:0.00}s workMs={2:0} slices={3} maxSliceMs={4:0.0} polls={5}\n{6}",
                2 * cells * cells * 2, sw.Elapsed.TotalSeconds, job.WorkMs, job.Slices, job.MaxSliceMs, polls, status));

            StringAssert.EndsWith("PAIRS=1 COMPLETE", status);
            Assert.AreEqual(2500f, ZFightScan.LastPairs[0].Area, 2500f * 0.005f);
            Assert.Less(job.MaxSliceMs, 2000, "a slice blocked the editor for more than 2 s");
            Assert.Greater(job.Slices, 1, "work was not time-sliced");
            Assert.Less(sw.Elapsed.TotalSeconds, 60, "time budget");
        }
    }
}
