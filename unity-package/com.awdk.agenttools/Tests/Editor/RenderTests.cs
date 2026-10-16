using System.Collections.Generic;
using System.IO;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using Debug = UnityEngine.Debug;

namespace AWDK.AgentTools.Tests
{
    /// <summary>ZFightRender mask math on synthetic ID images (no GPU needed).</summary>
    public class ZFightMaskMathTests
    {
        static Color32[] Ids(params int[] ids)
        {
            var px = new Color32[ids.Length];
            for (int i = 0; i < ids.Length; i++) px[i] = ids[i] == 0 ? new Color32(0, 0, 0, 0) : ZFightRender.IdColor(ids[i] - 1);
            return px;
        }

        [Test]
        public void IdColour_RoundTrips()
        {
            foreach (var i in new[] { 0, 1, 254, 255, 256, 70000, 16777214 })
                Assert.AreEqual(i + 1, ZFightRender.IdOf(ZFightRender.IdColor(i)));
        }

        [Test]
        public void CompareIds_MarksOnlyDifferingRendererPixels()
        {
            //                 0  1  2  3  4  5
            var a = Ids(1, 2, 2, 0, 3, 3);
            var b = Ids(1, 3, 2, 2, 0, 1);   // px1: 2->3 tie, px3/px4: background involved, px5: 3->1 tie
            var c = Ids(1, 3, 1, 0, 3, 3);   // px1 again (already marked), px2: 2->1 tie
            var mask = new bool[6];
            var pairs = new Dictionary<long, int>();

            Assert.AreEqual(2, ZFightRender.CompareIds(a, b, mask, pairs));
            Assert.AreEqual(2, ZFightRender.CompareIds(a, c, mask, pairs));
            CollectionAssert.AreEqual(new[] { false, true, true, false, false, true }, mask);
            Assert.AreEqual(1, pairs[(2L << 32) | 3], "pair 2-3 counted once despite two comparisons");
            Assert.AreEqual(1, pairs[(1L << 32) | 3]);
            Assert.AreEqual(1, pairs[(1L << 32) | 2]);

            var img = ZFightRender.MaskImage(Ids(1, 1, 1, 1, 1, 1), mask);
            Assert.AreEqual(new Color32(255, 0, 255, 255), img[1]);
            Assert.AreEqual(img[0].r, img[0].g);
        }

        [Test]
        public void Tolerance_PcFloatIgnoresNearClip_Fixed24ScalesWithDepthSquared()
        {
            try
            {
                ZFightRender.DepthFormat = ZDepthFormat.Float32ReversedZ;
                ZFightRender.NearClip = 0.001f;
                float floatNear001 = ZFightRender.Tolerance(100f);
                ZFightRender.NearClip = 0.05f;
                Assert.AreEqual(floatNear001, ZFightRender.Tolerance(100f), "float reversed-Z is independent of the near clip");
                Assert.AreEqual(ZFightRender.MinTolerance, ZFightRender.Tolerance(100f), "floor governs at 100 m from the origin");
                // Must cover the separations measured on 2022.3 D3D11 (camera at x = z = 1000: 67 µm at 100 m, 32 µm at 1 m).
                Assert.GreaterOrEqual(ZFightRender.Tolerance(100f, 1000f), 67e-6f);
                Assert.GreaterOrEqual(ZFightRender.Tolerance(1f, 1000f), 32e-6f);
                Assert.Greater(ZFightRender.Tolerance(1f, 5000f), ZFightRender.Tolerance(1f, 1000f), "grows with distance from the origin");

                ZFightRender.DepthFormat = ZDepthFormat.Fixed24;
                ZFightRender.NearClip = 0.01f;
                Assert.AreEqual(2f * 400f / (0.01f * 16777216f), ZFightRender.Tolerance(20f), 1e-7f);
                ZFightRender.NearClip = 0.001f;
                Assert.AreEqual(2f * 400f / (0.001f * 16777216f), ZFightRender.Tolerance(20f), 1e-6f);
            }
            finally { RenderTests.ResetModel(); }
        }
    }

    public class RenderTests
    {
        const string Out = "Temp/AgentToolsTests";
        const string Shot = "[{\"name\":\"top\",\"pos\":[0,3,-3],\"look\":[0,0,0],\"fov\":60,\"w\":480,\"h\":270}]";

        [SetUp]
        public void SetUp()
        {
            TestScene.Fresh();
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                Assert.Ignore("no graphics device (-nographics): render tests need a GPU device");
        }

        [TearDown]
        public void TearDown() => ResetModel();

        internal static void ResetModel()
        {
            ZFightRender.DepthFormat = ZDepthFormat.Float32ReversedZ;
            ZFightRender.NearClip = 0.01f;
        }

        [Test]
        public void PlantedCoplanarPair_IsFlagged_CleanSceneIsNot()
        {
            // Floor + an exactly coplanar decal with a different triangulation, right of and behind the
            // look point, so it lands in the upper-right part of the image.
            TestScene.MeshObject("Floor", TestScene.Quad(6f), Vector3.zero, TestScene.Unlit(Color.red));
            var decal = TestScene.MeshObject("Decal", TestScene.Quad(1.2f), new Vector3(1f, 0, 1f), Quaternion.Euler(0, 37, 0), TestScene.Unlit(Color.green));
            // A panel crossing the floor: only a few pixels on the intersection line may tie.
            TestScene.MeshObject("Crossing", TestScene.Quad(1.5f), new Vector3(-1.2f, 0, 0), Quaternion.Euler(-60, 20, 0), TestScene.Unlit(Color.blue));

            var fight = ZFightRender.RunBlocking(Out, Shot);
            Debug.Log("[ZFightRender planted]\n" + fight);
            StringAssert.EndsWith("COMPLETE", fight);
            var r = ZFightRender.LastResults[0];
            Assert.Greater(r.ZFightPixels, 1000, "planted z-fight not detected:\n" + fight);
            for (int i = 1; i < r.Pairs.Count; i++) Assert.Less(r.Pairs[i].Pixels, 20, "only intersection-line pixels besides the planted pair:\n" + fight);
            CollectionAssert.AreEquivalent(new[] { "Floor", "Decal" }, new[] { r.Pairs[0].PathA, r.Pairs[0].PathB });
            Assert.Greater(r.Box.center.x, r.Width / 2f, "decal is right of centre: " + r.Box);
            Assert.Less(r.Box.center.y, r.Height / 2f, "decal is above centre (y from top): " + r.Box);
            Assert.IsTrue(File.Exists(r.MaskPath));

            // The flagged region lines up with the real render: decal or floor colour at its centre.
            WorldCapture.ShootBlocking(Out, Shot.Replace("\"top\"", "\"top_visual\""));
            var tex = new Texture2D(2, 2);
            tex.LoadImage(File.ReadAllBytes(Path.Combine(Path.GetFullPath(Out), "top_visual.png")));
            var c = tex.GetPixel((int)r.Box.center.x, r.Height - 1 - (int)r.Box.center.y);
            Object.DestroyImmediate(tex);
            Assert.Greater(Mathf.Max(c.r, c.g), 0.8f, "flag box centre is not on the planted pair: " + c);

            decal.transform.position = new Vector3(1f, 0.002f, 1f); // 2 mm above: resolves cleanly
            var clean = ZFightRender.RunBlocking(Out, Shot);
            Debug.Log("[ZFightRender clean]\n" + clean);
            Assert.Less(TestScene.Count(clean, "ZFIGHT_PIXELS"), 20, "false positives on a clean scene:\n" + clean);
        }

        const string FarShot = "[{\"name\":\"far\",\"pos\":[0,12,-16],\"look\":[0,0,0],\"fov\":30,\"w\":480,\"h\":270}]";
        const string NearShot = "[{\"name\":\"near\",\"pos\":[0,2.4,-3.2],\"look\":[0,0,0],\"fov\":60,\"w\":480,\"h\":270}]";
        // ~100 m away (eye depth 100 m at the look point), narrow FOV so the 4 m decal fills the frame.
        const string DistantShot = "[{\"name\":\"distant\",\"pos\":[0,60,-80],\"look\":[0,0,0],\"fov\":4,\"w\":480,\"h\":270}]";

        [Test]
        public void SmallGap_ResolvesOnPcFloat_FightsAt20mOnlyUnderFixed24()
        {
            // 3 mm gap: far above the PC float tolerance (0.05 mm floor at 20 m), below the 24-bit
            // tolerance at 20 m (~4.8 mm) and well above it at 4 m (~0.2 mm).
            TestScene.MeshObject("Floor", TestScene.Quad(12f), Vector3.zero, TestScene.Unlit(Color.red));
            TestScene.MeshObject("Decal", TestScene.Quad(4f), new Vector3(0, 0.003f, 0), Quaternion.Euler(0, 37, 0), TestScene.Unlit(Color.green));

            var pcFar = ZFightRender.RunBlocking(Out, FarShot);
            Debug.Log("[ZFightRender gap, float]\n" + pcFar);
            Assert.AreEqual(0, TestScene.Count(pcFar, "ZFIGHT_PIXELS"), pcFar);

            ZFightRender.DepthFormat = ZDepthFormat.Fixed24;
            var far = ZFightRender.RunBlocking(Out, FarShot);
            var near = ZFightRender.RunBlocking(Out, NearShot);
            Debug.Log("[ZFightRender gap, fixed24]\n" + far + "\n" + near);
            Assert.Greater(TestScene.Count(far, "ZFIGHT_PIXELS"), 500, far);
            Assert.AreEqual(0, TestScene.Count(near, "ZFIGHT_PIXELS"), near);
        }

        [Test]
        public void At100m_CoplanarPairIsFlagged_SubMillimetreGapIsNot()
        {
            // Positive control at distance: an exactly coplanar decal still fights under the PC model.
            TestScene.MeshObject("Floor", TestScene.Quad(12f), Vector3.zero, TestScene.Unlit(Color.red));
            var decal = TestScene.MeshObject("Decal", TestScene.Quad(4f), Vector3.zero, Quaternion.Euler(0, 37, 0), TestScene.Unlit(Color.green));
            var coplanar = ZFightRender.RunBlocking(Out, DistantShot);
            Debug.Log("[ZFightRender 100 m coplanar]\n" + coplanar);
            Assert.Greater(TestScene.Count(coplanar, "ZFIGHT_PIXELS"), 5000, coplanar);

            // 0.5 mm gap: 10x the PC tolerance at 100 m (0.05 mm), so it resolves; the old 24-bit model
            // (near 0.01: ~119 mm at 100 m) would flag it.
            decal.transform.position = new Vector3(0, 0.0005f, 0);
            var gap = ZFightRender.RunBlocking(Out, DistantShot);
            Debug.Log("[ZFightRender 100 m gap]\n" + gap);
            Assert.AreEqual(0, TestScene.Count(gap, "ZFIGHT_PIXELS"), gap);
            ZFightRender.DepthFormat = ZDepthFormat.Fixed24;
            var gap24 = ZFightRender.RunBlocking(Out, DistantShot);
            Assert.Greater(TestScene.Count(gap24, "ZFIGHT_PIXELS"), 5000, gap24);
        }

        [Test]
        public void InactiveLodLevel_IsNotDrawn()
        {
            var root = new GameObject("Lod");
            var lod0 = TestScene.MeshObject("LOD0", TestScene.Quad(2f), Vector3.zero, TestScene.Unlit(Color.red), root.transform);
            var lod1 = TestScene.MeshObject("LOD1", TestScene.Quad(2f), Vector3.zero, Quaternion.Euler(0, 45, 0), TestScene.Unlit(Color.green), root.transform);
            var group = root.AddComponent<LODGroup>();
            group.SetLODs(new[]
            {
                new LOD(0.05f, new Renderer[] { lod0.GetComponent<Renderer>() }),
                new LOD(0.01f, new Renderer[] { lod1.GetComponent<Renderer>() }),
            });
            group.RecalculateBounds();

            var report = ZFightRender.RunBlocking(Out, Shot);
            StringAssert.EndsWith("ZFIGHT_PIXELS=0 COMPLETE", report);
        }

        [Test]
        public void Capture_WritesPngOfRequestedSize()
        {
            TestScene.MeshObject("Floor", TestScene.Quad(4f), Vector3.zero, TestScene.Unlit(Color.red));
            var report = WorldCapture.ShootBlocking(Out, "[{\"name\":\"cap\",\"pos\":[0,3,-3],\"look\":[0,0,0],\"w\":320,\"h\":180}]");
            StringAssert.EndsWith("SHOTS=1 COMPLETE", report);

            var png = Path.Combine(Path.GetFullPath(Out), "cap.png");
            var tex = new Texture2D(2, 2);
            Assert.IsTrue(tex.LoadImage(File.ReadAllBytes(png)));
            Assert.AreEqual(320, tex.width);
            Assert.AreEqual(180, tex.height);
            var centre = tex.GetPixel(160, 90);
            Assert.Greater(centre.r, 0.9f, "floor should be red in the centre: " + centre);
            Assert.Less(centre.g, 0.1f);
            Object.DestroyImmediate(tex);

            int cams = 0;
            foreach (var c in Resources.FindObjectsOfTypeAll<Camera>()) if (c.name == Util.CapCamName && !UnityEditor.EditorUtility.IsPersistent(c)) cams++;
            Assert.AreEqual(1, cams, "exactly one persistent __CapCam__, also after earlier tests opened new scenes");
        }

        [Test]
        public void BadShotsJson_ReturnsError()
        {
            StringAssert.StartsWith("ERROR", WorldCapture.Shoot(Out, "[{\"name\":\"x\",\"pos\":[0,1]}]"));
            StringAssert.StartsWith("ERROR", ZFightRender.Start(Out, ""));
        }
    }
}
