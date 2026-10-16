// WorldStatsDump.cs: drop into any Unity project under Assets/Editor/, then
// menu Tools > World Stats Dump. Writes <project>/WorldStats_<scene>.json and opens its folder.
// Read-only: it changes nothing in the scene or the project. Counts only active, enabled objects
// in the open scene(s), the way the world ships (EditorOnly-tagged objects are skipped).
// The numbers do not depend on the PC, so they compare directly between worlds.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;
using UnityEngine.Profiling;
using UnityEngine.SceneManagement;

public static class WorldStatsDump
{
    [MenuItem("Tools/World Stats Dump")]
    public static void RunMenu()
    {
        string path = Run();
        EditorUtility.RevealInFinder(path);
        Debug.Log("[WorldStatsDump] wrote " + path);
    }

    // Batch mode: Unity.exe -batchmode -projectPath <p> -executeMethod WorldStatsDump.RunBatch -scene Assets/X.unity -quit
    public static void RunBatch()
    {
        string[] args = Environment.GetCommandLineArgs();
        int i = Array.IndexOf(args, "-scene");
        if (i >= 0 && i + 1 < args.Length)
            UnityEditor.SceneManagement.EditorSceneManager.OpenScene(args[i + 1]);
        Debug.Log("[WorldStatsDump] wrote " + Run());
    }

    static bool Ships(GameObject go)
    {
        for (Transform t = go.transform; t != null; t = t.parent)
            if (t.CompareTag("EditorOnly")) return false;
        return go.activeInHierarchy;
    }

    static IEnumerable<T> Live<T>() where T : Component
    {
        for (int s = 0; s < SceneManager.sceneCount; s++)
        {
            Scene scene = SceneManager.GetSceneAt(s);
            if (!scene.isLoaded) continue;
            foreach (GameObject root in scene.GetRootGameObjects())
                foreach (T c in root.GetComponentsInChildren<T>(true))
                    if (c != null && Ships(c.gameObject)) yield return c;
        }
    }

    static int CountType(string fullName)
    {
        Type t = AppDomain.CurrentDomain.GetAssemblies()
            .Select(a => { try { return a.GetType(fullName, false); } catch { return null; } })
            .FirstOrDefault(x => x != null);
        if (t == null || !typeof(Component).IsAssignableFrom(t)) return -1; // -1 = type not in this project
        int n = 0;
        for (int s = 0; s < SceneManager.sceneCount; s++)
        {
            Scene scene = SceneManager.GetSceneAt(s);
            if (!scene.isLoaded) continue;
            foreach (GameObject root in scene.GetRootGameObjects())
                foreach (Component c in root.GetComponentsInChildren(t, true))
                    if (c != null && Ships(c.gameObject) && (!(c is Behaviour b) || b.enabled)) n++;
        }
        return n;
    }

    static long Bytes(UnityEngine.Object o) => o == null ? 0 : Profiler.GetRuntimeMemorySizeLong(o);
    static double MB(long b) => Math.Round(b / 1048576.0, 1);

    public static string Run()
    {
        var J = new Dictionary<string, object>();
        var scenes = new List<string>();
        for (int s = 0; s < SceneManager.sceneCount; s++) scenes.Add(SceneManager.GetSceneAt(s).path);
        J["scene"] = string.Join(", ", scenes);
        J["unityVersion"] = Application.unityVersion;
        J["dumpedAtUtc"] = DateTime.UtcNow.ToString("s", CultureInfo.InvariantCulture) + "Z";

        // Renderers, meshes, triangles
        var renderers = Live<Renderer>().Where(r => r.enabled).ToList();
        var meshRenderers = renderers.OfType<MeshRenderer>().ToList();
        var skinned = renderers.OfType<SkinnedMeshRenderer>().ToList();
        // Renderers that only appear in LOD1+ of an LODGroup don't render up close; count them apart.
        var lod0 = new HashSet<Renderer>(); var lodFar = new HashSet<Renderer>();
        foreach (var g in Live<LODGroup>().Where(l => l.enabled))
        {
            LOD[] lods = g.GetLODs();
            for (int li = 0; li < lods.Length; li++)
                foreach (var r in lods[li].renderers) if (r != null) (li == 0 ? lod0 : lodFar).Add(r);
        }
        lodFar.ExceptWith(lod0);
        long tris = 0, trisFarLods = 0; var meshes = new HashSet<Mesh>();
        void AddTris(Renderer r, Mesh m)
        {
            if (m == null) return;
            meshes.Add(m);
            long n = 0;
            for (int sm = 0; sm < m.subMeshCount; sm++) n += (long)m.GetIndexCount(sm) / 3;
            if (lodFar.Contains(r)) trisFarLods += n; else tris += n;
        }
        foreach (var mr in meshRenderers) { var mf = mr.GetComponent<MeshFilter>(); AddTris(mr, mf != null ? mf.sharedMesh : null); }
        foreach (var sr in skinned) AddTris(sr, sr.sharedMesh);
        int staticBatched = meshRenderers.Count(r => GameObjectUtility.AreStaticEditorFlagsSet(r.gameObject, StaticEditorFlags.BatchingStatic));
        int lightmapped = meshRenderers.Count(r => r.lightmapIndex >= 0 && r.lightmapIndex < 0xFFFE);
        J["renderers"] = new Dictionary<string, object> {
            {"total", renderers.Count}, {"meshRenderers", meshRenderers.Count}, {"skinnedMeshRenderers", skinned.Count},
            {"particleRenderers", renderers.OfType<ParticleSystemRenderer>().Count()},
            {"staticBatchingFlagged", staticBatched}, {"lightmapped", lightmapped},
            {"trianglesLod0", tris}, {"trianglesFarLodLevels", trisFarLods}, {"uniqueMeshes", meshes.Count},
            {"meshMemoryMB", MB(meshes.Sum(m => Bytes(m)))},
            {"lodGroups", Live<LODGroup>().Count(l => l.enabled)} };

        // Materials, shaders, textures
        var mats = new HashSet<Material>(); int slots = 0;
        foreach (var r in renderers) foreach (var m in r.sharedMaterials) { slots++; if (m != null) mats.Add(m); }
        var shaders = new HashSet<Shader>(mats.Where(m => m.shader != null).Select(m => m.shader));
        var texs = new HashSet<Texture>();
        foreach (var m in mats)
            foreach (string p in m.GetTexturePropertyNames())
            { var t = m.GetTexture(p); if (t != null) texs.Add(t); }
        int big = 0, uncompressed = 0, noMips = 0;
        foreach (var t in texs.OfType<Texture2D>())
        {
            if (Mathf.Max(t.width, t.height) > 2048) big++;
            var f = t.format;
            if (f == TextureFormat.RGBA32 || f == TextureFormat.RGB24 || f == TextureFormat.ARGB32 || f == TextureFormat.RGBAHalf || f == TextureFormat.RGBAFloat) uncompressed++;
            if (t.mipmapCount <= 1 && Mathf.Max(t.width, t.height) > 256) noMips++;
        }
        J["materials"] = new Dictionary<string, object> {
            {"unique", mats.Count}, {"materialSlots", slots}, {"uniqueShaders", shaders.Count},
            {"gpuInstancingEnabled", mats.Count(m => m.enableInstancing)},
            {"topShaders", shaders.Select(s => new { s.name, n = mats.Count(m => m.shader == s) }).OrderByDescending(x => x.n).Take(8).Select(x => x.name + " x" + x.n).ToList()} };
        J["textures"] = new Dictionary<string, object> {
            {"uniqueOnMaterials", texs.Count}, {"memoryMB", MB(texs.Sum(t => Bytes(t)))},
            {"over2048", big}, {"uncompressed", uncompressed}, {"noMipsOver256", noMips} };

        // Lightmaps, probes, lights
        var lms = LightmapSettings.lightmaps ?? new LightmapData[0];
        long lmBytes = 0; var lmSizes = new List<string>();
        foreach (var d in lms)
        {
            foreach (var t in new Texture2D[] { d.lightmapColor, d.lightmapDir, d.shadowMask })
                if (t != null) lmBytes += Bytes(t);
            if (d.lightmapColor != null) lmSizes.Add(d.lightmapColor.width + "x" + d.lightmapColor.height);
        }
        var lights = Live<Light>().Where(l => l.enabled).ToList();
        J["lighting"] = new Dictionary<string, object> {
            {"lightmaps", lms.Length}, {"lightmapSizes", lmSizes.GroupBy(x => x).Select(g => g.Key + " x" + g.Count()).ToList()},
            {"lightmapMemoryMB", MB(lmBytes)},
            {"lightProbes", LightmapSettings.lightProbes != null ? LightmapSettings.lightProbes.count : 0},
            {"reflectionProbes", Live<ReflectionProbe>().Count(p => p.enabled)},
            {"reflectionProbesRealtime", Live<ReflectionProbe>().Count(p => p.enabled && p.mode == UnityEngine.Rendering.ReflectionProbeMode.Realtime)},
            {"lightsRealtime", lights.Count(l => l.lightmapBakeType == LightmapBakeType.Realtime)},
            {"lightsMixed", lights.Count(l => l.lightmapBakeType == LightmapBakeType.Mixed)},
            {"lightsBaked", lights.Count(l => l.lightmapBakeType == LightmapBakeType.Baked)},
            {"realtimeShadowCasters", lights.Count(l => l.lightmapBakeType != LightmapBakeType.Baked && l.shadows != LightShadows.None)},
            {"fog", RenderSettings.fog} };

        // World size
        // Bounds of every mesh renderer, plus the renderers furthest out, since one skybox or far prop stretches them.
        Bounds b = new Bounds(); bool any = false;
        foreach (var r in meshRenderers) { if (!any) { b = r.bounds; any = true; } else b.Encapsulate(r.bounds); }
        var farthest = meshRenderers
            .Select(r => new { r, d = Math.Max(r.bounds.max.magnitude, r.bounds.min.magnitude) })
            .OrderByDescending(x => x.d).Take(5)
            .Select(x => AnimationUtility.CalculateTransformPath(x.r.transform, null) + " @" + Math.Round(x.d) + "m").ToList();
        J["worldBoundsMeters"] = any ? new Dictionary<string, object> {
            {"sizeX", Math.Round(b.size.x, 1)}, {"sizeY", Math.Round(b.size.y, 1)}, {"sizeZ", Math.Round(b.size.z, 1)},
            {"center", b.center.ToString("F1")}, {"farthestFromOrigin", farthest} } : null;

        // Scripts and runtime systems (-1 = component type not in this project)
        var udonByProgram = new Dictionary<string, int>();
        Type udonT = AppDomain.CurrentDomain.GetAssemblies().Select(a => { try { return a.GetType("VRC.Udon.UdonBehaviour", false); } catch { return null; } }).FirstOrDefault(x => x != null);
        int udon = -1;
        if (udonT != null)
        {
            udon = 0;
            var progProp = udonT.GetProperty("programSource");
            var progFld = progProp == null ? udonT.GetField("programSource", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance) : null;
            for (int s = 0; s < SceneManager.sceneCount; s++)
                foreach (GameObject root in SceneManager.GetSceneAt(s).GetRootGameObjects())
                    foreach (Component c in root.GetComponentsInChildren(udonT, true))
                    {
                        if (c == null || !Ships(c.gameObject) || !((Behaviour)c).enabled) continue;
                        udon++;
                        object raw = progProp != null ? progProp.GetValue(c) : progFld != null ? progFld.GetValue(c) : null;
                        var src = raw as UnityEngine.Object;
                        string n = src != null ? src.name : "(none)";
                        udonByProgram[n] = udonByProgram.TryGetValue(n, out int k) ? k + 1 : 1;
                    }
        }
        J["scripts"] = new Dictionary<string, object> {
            {"udonBehaviours", udon},
            {"udonTopPrograms", udonByProgram.OrderByDescending(kv => kv.Value).Take(15).Select(kv => kv.Key + " x" + kv.Value).ToList()},
            {"animators", Live<Animator>().Count(a => a.enabled)},
            {"animatorsWithoutController", Live<Animator>().Count(a => a.enabled && a.runtimeAnimatorController == null)},
            {"particleSystems", Live<ParticleSystem>().Count()},
            {"particleMaxTotal", Live<ParticleSystem>().Sum(p => (long)p.main.maxParticles)},
            {"particleSystemsWithCollision", Live<ParticleSystem>().Count(p => p.collision.enabled)},
            {"audioSources", Live<AudioSource>().Count(a => a.enabled)},
            {"cameras", Live<Camera>().Count(c => c.enabled)},
            {"canvases", Live<Canvas>().Count(c => c.enabled)},
            {"textMeshPro", CountType("TMPro.TextMeshPro") + Math.Max(0, CountType("TMPro.TextMeshProUGUI"))},
            {"vrcMirrors", CountType("VRC.SDK3.Components.VRCMirrorReflection")},
            {"vrcPickups", CountType("VRC.SDK3.Components.VRCPickup")},
            {"vrcStations", CountType("VRC.SDK3.Components.VRCStation")},
            {"vrcVideoPlayersAVPro", CountType("VRC.SDK3.Video.Components.AVPro.VRCAVProVideoPlayer")},
            {"vrcVideoPlayersUnity", CountType("VRC.SDK3.Video.Components.VRCUnityVideoPlayer")},
            {"vrcObjectSyncs", CountType("VRC.SDK3.Components.VRCObjectSync")} };

        // Physics
        var cols = Live<Collider>().Where(c => c.enabled).ToList();
        J["physics"] = new Dictionary<string, object> {
            {"colliders", cols.Count}, {"meshColliders", cols.OfType<MeshCollider>().Count()},
            {"rigidbodies", Live<Rigidbody>().Count()} };

        // Occlusion and camera
        J["occlusion"] = new Dictionary<string, object> {
            {"baked", StaticOcclusionCulling.umbraDataSize > 0}, {"dataKB", StaticOcclusionCulling.umbraDataSize / 1024},
            {"occluderStaticRenderers", meshRenderers.Count(r => GameObjectUtility.AreStaticEditorFlagsSet(r.gameObject, StaticEditorFlags.OccluderStatic))} };
        Component desc = null; Type descT = AppDomain.CurrentDomain.GetAssemblies().Select(a => { try { return a.GetType("VRC.SDK3.Components.VRCSceneDescriptor", false); } catch { return null; } }).FirstOrDefault(x => x != null);
        if (descT != null) desc = (Component)UnityEngine.Object.FindObjectOfType(descT);
        Camera refCam = null;
        if (desc != null) { var f = descT.GetField("ReferenceCamera"); var go = f != null ? f.GetValue(desc) as GameObject : null; if (go != null) refCam = go.GetComponent<Camera>(); }
        J["referenceCamera"] = refCam != null ? new Dictionary<string, object> { {"near", refCam.nearClipPlane}, {"far", refCam.farClipPlane} } : null;
        J["qualityLevel"] = QualitySettings.names[QualitySettings.GetQualityLevel()];

        string json = ToJson(J, 0);
        string safe = string.Join("_", (scenes.Count > 0 ? Path.GetFileNameWithoutExtension(scenes[0]) : "scene").Split(Path.GetInvalidFileNameChars()));
        string outPath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "WorldStats_" + safe + ".json"));
        File.WriteAllText(outPath, json, new UTF8Encoding(false));
        return outPath;
    }

    static string ToJson(object o, int ind)
    {
        string pad = new string(' ', ind * 2), pad2 = new string(' ', (ind + 1) * 2);
        switch (o)
        {
            case null: return "null";
            case string s: return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
            case bool bo: return bo ? "true" : "false";
            case float f: return f.ToString("0.###", CultureInfo.InvariantCulture);
            case double d: return d.ToString("0.###", CultureInfo.InvariantCulture);
            case int or long: return Convert.ToInt64(o).ToString(CultureInfo.InvariantCulture);
            case Dictionary<string, object> dict:
                return "{\n" + string.Join(",\n", dict.Select(kv => pad2 + ToJson(kv.Key, 0) + ": " + ToJson(kv.Value, ind + 1))) + "\n" + pad + "}";
            case System.Collections.IEnumerable list:
                return "[" + string.Join(", ", list.Cast<object>().Select(x => ToJson(x, ind + 1))) + "]";
            default: return ToJson(o.ToString(), ind);
        }
    }
}
#endif
