using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using AWDK.AgentTools.TestFakes;

namespace AWDK.AgentTools.Tests
{
    public class WorldAuditTests
    {
        [SetUp]
        public void SetUp() => TestScene.Fresh();

        [Test]
        public void CleanScene_HasNoIssues()
        {
            var light = new GameObject("Sun").AddComponent<Light>();
            light.type = LightType.Directional;
            light.lightmapBakeType = LightmapBakeType.Baked;
            new GameObject("Floor").AddComponent<BoxCollider>();

            var report = WorldAudit.Run();
            StringAssert.EndsWith("ISSUES=0", report, report);
        }

        [Test]
        public void FindsPlantedRealtimeLightAndCapCam()
        {
            var rt = new GameObject("Lamp").AddComponent<Light>();
            rt.lightmapBakeType = LightmapBakeType.Realtime;
            var mixed = new GameObject("Sun").AddComponent<Light>();
            mixed.lightmapBakeType = LightmapBakeType.Mixed;
            var baked = new GameObject("Fill").AddComponent<Light>();
            baked.lightmapBakeType = LightmapBakeType.Baked;
            new GameObject("__CapCam__").AddComponent<Camera>();

            var report = WorldAudit.Run();
            Assert.AreEqual(2, TestScene.Section(report, "REALTIME_OR_MIXED_LIGHTS"), report);
            StringAssert.Contains("Lamp type=", report);
            StringAssert.Contains("Sun type=", report);
            StringAssert.DoesNotContain("Fill type=", report);
            Assert.AreEqual(1, TestScene.Section(report, "LEFTOVER_OBJECTS"), report);
            StringAssert.Contains("  __CapCam__", report);
            StringAssert.EndsWith("ISSUES=3", report);
        }

        [Test]
        public void DontSaveHelper_IsNotCountedAsLeftover()
        {
            new GameObject("__Temp__") { hideFlags = HideFlags.DontSave };
            var report = WorldAudit.Run();
            Assert.AreEqual(0, TestScene.Section(report, "LEFTOVER_OBJECTS"), report);
            StringAssert.Contains("more are DontSave", report);
        }

        [Test]
        public void FindsStationsAndMisconfiguredPickups_ByTypeName()
        {
            new GameObject("Chair").AddComponent<VRCStation>();
            new GameObject("BadPickup").AddComponent<VRCPickup>();
            var good = new GameObject("GoodPickup").AddComponent<VRCPickup>();
            good.proximity = 0.1f;
            good.AutoHold = VRCPickup.AutoHoldMode.No;

            var report = WorldAudit.Run();
            Assert.AreEqual(1, TestScene.Section(report, "STATIONS"), report);
            Assert.AreEqual(1, TestScene.Section(report, "PICKUPS"), report);
            StringAssert.Contains("BadPickup proximity=2 AutoHold=AutoDetect", report);
        }

        [Test]
        public void FlagsPropColliders_ButNotPickupsOrTriggers()
        {
            var props = new GameObject("Props").transform;
            var chair = new GameObject("Chair");
            chair.transform.SetParent(props);
            chair.AddComponent<BoxCollider>();
            var ball = new GameObject("Ball");
            ball.transform.SetParent(props);
            ball.AddComponent<SphereCollider>();
            var p = ball.AddComponent<VRCPickup>();
            p.proximity = 0.1f;
            p.AutoHold = VRCPickup.AutoHoldMode.No;
            var zone = new GameObject("Zone");
            zone.transform.SetParent(props);
            zone.AddComponent<BoxCollider>().isTrigger = true;
            new GameObject("Wall").AddComponent<BoxCollider>();

            var report = WorldAudit.Run();
            Assert.AreEqual(1, TestScene.Section(report, "PROP_COLLIDERS"), report);
            StringAssert.Contains("Props/Chair [BoxCollider] under 'Props'", report);
        }

        static GameObject LieDown(Transform bed)
        {
            var go = new GameObject(WorldAudit.LieDownName);
            go.transform.SetParent(bed);
            return go;
        }

        [Test]
        public void LieDownCollider_AllowedOnlyWhenOffBoxCollider()
        {
            var props = new GameObject("Props").transform;
            var chair = new GameObject("Chair");
            chair.transform.SetParent(props);
            chair.AddComponent<BoxCollider>(); // positive control: still flagged

            var bed = new GameObject("Bed").transform;
            bed.SetParent(props);
            LieDown(bed).AddComponent<BoxCollider>().enabled = false; // allowed
            var couch = new GameObject("Couch").transform;
            couch.SetParent(props);
            var inactive = LieDown(couch);
            inactive.AddComponent<BoxCollider>();
            inactive.SetActive(false); // allowed

            var report = WorldAudit.Run();
            Assert.AreEqual(1, TestScene.Section(report, "PROP_COLLIDERS"), report);
            StringAssert.Contains("Props/Chair [BoxCollider]", report);
            Assert.AreEqual(2, TestScene.Section(report, "LIE_DOWN_COLLIDERS"), report);
            StringAssert.Contains("lie-down colliders: 2, all off by default", report);
        }

        [Test]
        public void LieDownCollider_FlaggedWhenEnabledOrNotBox()
        {
            var props = new GameObject("Props").transform;
            var bed = new GameObject("Bed").transform;
            bed.SetParent(props);
            LieDown(bed).AddComponent<BoxCollider>(); // enabled + active
            var platform = new GameObject("CuddlePlatform").transform;
            platform.SetParent(props);
            var mesh = LieDown(platform);
            mesh.AddComponent<MeshCollider>().enabled = false;

            var report = WorldAudit.Run();
            Assert.AreEqual(2, TestScene.Section(report, "PROP_COLLIDERS"), report);
            StringAssert.Contains("Props/Bed/LieDownCollider [BoxCollider] under 'Props' (LieDownCollider must be off by default)", report);
            StringAssert.Contains("Props/CuddlePlatform/LieDownCollider [MeshCollider] under 'Props' (LieDownCollider must be a BoxCollider)", report);
            Assert.AreEqual(0, TestScene.Section(report, "LIE_DOWN_COLLIDERS"), report);
        }

        static GameObject Solid(Transform piece)
        {
            var go = new GameObject(WorldAudit.SolidName);
            go.transform.SetParent(piece);
            return go;
        }

        [Test]
        public void SolidCollider_AllowedWhenOnBoxCollider_FlaggedOtherwise()
        {
            var props = new GameObject("Furniture").transform;
            var chair = new GameObject("Chair");
            chair.transform.SetParent(props);
            chair.AddComponent<BoxCollider>(); // positive control: plain prop collider still flagged

            var table = new GameObject("DiningTable").transform;
            table.SetParent(props);
            Solid(table).AddComponent<BoxCollider>(); // allowed
            var cabinet = new GameObject("Cabinet").transform;
            cabinet.SetParent(props);
            Solid(cabinet).AddComponent<BoxCollider>().enabled = false; // off: pickups would fall through
            var counter = new GameObject("Counter").transform;
            counter.SetParent(props);
            Solid(counter).AddComponent<BoxCollider>().isTrigger = true;

            var report = WorldAudit.Run();
            Assert.AreEqual(3, TestScene.Section(report, "PROP_COLLIDERS"), report);
            StringAssert.Contains("Furniture/Chair [BoxCollider]", report);
            StringAssert.Contains("Furniture/Cabinet/SolidCollider [BoxCollider] under 'Furniture' (SolidCollider must be on)", report);
            StringAssert.Contains("Furniture/Counter/SolidCollider [BoxCollider] under 'Furniture' (SolidCollider must not be a trigger)", report);
            Assert.AreEqual(1, TestScene.Section(report, "SOLID_FURNITURE_COLLIDERS"), report);
        }

        [Test]
        public void FlagsMeshColliderOnFloorLikeSurface_NotOnWall()
        {
            var slab = TestScene.MeshObject("Slab", TestScene.Quad(3f), Vector3.zero);
            slab.AddComponent<MeshCollider>().sharedMesh = slab.GetComponent<MeshFilter>().sharedMesh;
            var wall = TestScene.MeshObject("Panel", TestScene.Quad(3f), Vector3.zero, Quaternion.Euler(90, 0, 0));
            wall.AddComponent<MeshCollider>().sharedMesh = wall.GetComponent<MeshFilter>().sharedMesh;

            var report = WorldAudit.Run();
            Assert.AreEqual(1, TestScene.Section(report, "WALKABLE_MESHCOLLIDERS"), report);
            StringAssert.Contains("Slab (9 m2", report);
        }

        [Test]
        public void FlagsStaticRendererWithoutUv2_AndUncompressedTexture()
        {
            var tex = new Texture2D(256, 256, TextureFormat.RGBA32, false) { name = "RawTex" };
            var mat = new Material(Shader.Find("Unlit/Texture"));
            mat.mainTexture = tex;
            var go = TestScene.MeshObject("StaticNoUv2", TestScene.Quad(1f), Vector3.zero, mat);
            GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.ContributeGI);
            go.GetComponent<MeshRenderer>().receiveGI = ReceiveGI.Lightmaps;

            var withUv2 = TestScene.Quad(1f);
            withUv2.uv2 = new[] { Vector2.zero, Vector2.up, Vector2.one, Vector2.right };
            var ok = TestScene.MeshObject("StaticWithUv2", withUv2, new Vector3(5, 0, 0));
            GameObjectUtility.SetStaticEditorFlags(ok, StaticEditorFlags.ContributeGI);

            var report = WorldAudit.Run();
            Assert.AreEqual(1, TestScene.Section(report, "STATIC_MISSING_UV2"), report);
            StringAssert.Contains("StaticNoUv2 mesh=", report);
            Assert.AreEqual(1, TestScene.Section(report, "UNCOMPRESSED_TEXTURES"), report);
            StringAssert.Contains("RawTex <not an asset> 256x256", report);
        }

        [Test]
        public void RootPath_LimitsTheAudit()
        {
            var a = new GameObject("AreaA");
            new GameObject("Lamp").AddComponent<Light>().transform.SetParent(a.transform);
            new GameObject("Other").AddComponent<Light>();

            Assert.AreEqual(1, TestScene.Section(WorldAudit.Run("AreaA"), "REALTIME_OR_MIXED_LIGHTS"));
            StringAssert.StartsWith("ERROR", WorldAudit.Run("Missing"));
        }
    }
}
