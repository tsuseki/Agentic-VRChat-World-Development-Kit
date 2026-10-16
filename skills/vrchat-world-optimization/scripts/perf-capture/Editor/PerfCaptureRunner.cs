// AWDK perf capture runner: places/removes the test-only tour harness and starts a desktop
// Build & Test. Every entry point is a static method returning plain text, for MCP execute_code:
//   PerfCaptureRunner.Install()                         -> program asset for PerfCaptureTour
//   PerfCaptureRunner.Place(viewpointsJson, "originals") -> AWDK_PerfCapture root + viewpoint children
//   PerfCaptureRunner.StartBuildAndTest()                -> fire-and-forget; poll Status()
//   PerfCaptureRunner.Status()
//   PerfCaptureRunner.Remove()                           -> deletes the harness (always run at the end)
// viewpointsJson: {"viewpoints":[{"name":"garden_west","pos":[x,y,z],"yaw":75.0}, ...]}
// pos = the player's feet. Procedure: references/client-capture.md.

using System;
using System.Linq;
using UdonSharp;
using UdonSharpEditor;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using VRC.SDK3.Editor;

public static class PerfCaptureRunner
{
    public const string RootName = "AWDK_PerfCapture";
    const string ScriptName = "PerfCaptureTour";

    [Serializable] class Vp { public string name; public float[] pos; public float yaw; }
    [Serializable] class VpList { public Vp[] viewpoints; }

    static string _state = "idle";
    static string _error = "";

    public static string Install()
    {
        var script = AssetDatabase.FindAssets(ScriptName + " t:MonoScript")
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<MonoScript>)
            .FirstOrDefault(s => s != null && s.name == ScriptName);
        if (script == null) return "ERROR: PerfCaptureTour.cs not found in the project; copy it in first.";
        if (script.GetClass() == null) return "ERROR: PerfCaptureTour has no compiled class yet (compile errors or compiling). Check the console.";

        var existing = AssetDatabase.FindAssets("t:UdonSharpProgramAsset")
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>)
            .FirstOrDefault(a => a != null && a.sourceCsScript == script);
        if (existing != null) return "OK program asset exists: " + AssetDatabase.GetAssetPath(existing);

        var asset = ScriptableObject.CreateInstance<UdonSharpProgramAsset>();
        asset.sourceCsScript = script;
        string path = System.IO.Path.ChangeExtension(AssetDatabase.GetAssetPath(script), ".asset");
        AssetDatabase.CreateAsset(asset, path);
        AssetDatabase.SaveAssets();
        UdonSharpProgramAsset.CompileAllCsPrograms(true);
        return "OK created " + path + " (compiling U# programs)";
    }

    public static string Place(string viewpointsJson, string runLabel,
        float startDelaySeconds = 30f, float settleSeconds = 6f, float measureSeconds = 20f, int loops = 1)
    {
        var list = JsonUtility.FromJson<VpList>(viewpointsJson);
        if (list?.viewpoints == null || list.viewpoints.Length == 0) return "ERROR: no viewpoints in JSON";
        var tourType = Type.GetType(ScriptName) ??
            AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType(ScriptName)).FirstOrDefault(t => t != null);
        if (tourType == null) return "ERROR: PerfCaptureTour type not compiled";

        Remove();
        var root = new GameObject(RootName);
        var tps = new Transform[list.viewpoints.Length];
        for (int i = 0; i < list.viewpoints.Length; i++)
        {
            var v = list.viewpoints[i];
            if (v.pos == null || v.pos.Length != 3) return "ERROR: viewpoint " + v.name + " needs pos[3]";
            var c = new GameObject(string.IsNullOrEmpty(v.name) ? "vp" + i : v.name).transform;
            c.SetParent(root.transform, false);
            c.position = new Vector3(v.pos[0], v.pos[1], v.pos[2]);
            c.rotation = Quaternion.Euler(0f, v.yaw, 0f);
            tps[i] = c;
        }
        var tour = UdonSharpUndo.AddComponent(root, tourType);
        var so = new SerializedObject(tour);
        var arr = so.FindProperty("viewpoints");
        arr.arraySize = tps.Length;
        for (int i = 0; i < tps.Length; i++) arr.GetArrayElementAtIndex(i).objectReferenceValue = tps[i];
        so.FindProperty("runLabel").stringValue = runLabel;
        so.FindProperty("startDelaySeconds").floatValue = startDelaySeconds;
        so.FindProperty("settleSeconds").floatValue = settleSeconds;
        so.FindProperty("measureSeconds").floatValue = measureSeconds;
        so.FindProperty("loops").intValue = loops;
        so.ApplyModifiedPropertiesWithoutUndo();
        UdonSharpEditorUtility.CopyProxyToUdon(tour);
        EditorSceneManager.MarkSceneDirty(root.scene);
        float tourSeconds = startDelaySeconds + loops * tps.Length * (settleSeconds + measureSeconds + 0.5f);
        return "OK placed " + tps.Length + " viewpoints label=" + runLabel + " tourSeconds~" + tourSeconds.ToString("F0");
    }

    public static string Remove()
    {
        int n = 0;
        foreach (var t in UnityEngine.Object.FindObjectsOfType<Transform>(true))
        {
            if (t != null && t.name == RootName && t.parent == null)
            {
                var scene = t.gameObject.scene;
                UnityEngine.Object.DestroyImmediate(t.gameObject);
                EditorSceneManager.MarkSceneDirty(scene);
                n++;
            }
        }
        return "OK removed " + n;
    }

    public static string StartBuildAndTest()
    {
        if (EditorApplication.isPlaying) return "ERROR: exit play mode first";
        if (_state == "building") return "ERROR: a build is already running";
        SetSdkSetting("NumClients", 1);
        SetSdkSetting("ForceNoVR", true);
        EditorWindow.GetWindow<VRCSdkControlPanel>();
        if (!VRCSdkControlPanel.TryGetBuilder<IVRCSdkWorldBuilderApi>(out var builder))
            return "ERROR: SDK world builder not available (panel not ready or not logged in). Retry in a few seconds.";
        PerfCaptureGuard.AllowTestBuild();
        _state = "building";
        _error = "";
        Run(builder);
        return "OK build started; poll Status() and watch for VRChat.exe";
    }

    static async void Run(IVRCSdkWorldBuilderApi builder)
    {
        try
        {
            await builder.BuildAndTest();
            _state = "launched";
        }
        catch (Exception e)
        {
            _state = "failed";
            _error = e.GetType().Name + ": " + e.Message;
        }
    }

    public static string Status()
    {
        bool harness = UnityEngine.Object.FindObjectsOfType<Transform>(true).Any(t => t.name == RootName && t.parent == null);
        return "STATE=" + _state + (_error.Length > 0 ? " ERROR=" + _error : "") + " harnessInScene=" + harness;
    }

    // VRCSettings lives in a precompiled SDK assembly; set it by reflection so this file compiles
    // against any SDK version that has the property.
    static void SetSdkSetting(string prop, object value)
    {
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type t;
            try { t = asm.GetTypes().FirstOrDefault(x => x.Name == "VRCSettings"); }
            catch (System.Reflection.ReflectionTypeLoadException) { continue; }
            var p = t?.GetProperty(prop, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
            if (p != null && p.CanWrite) { p.SetValue(null, value); return; }
        }
        Debug.LogWarning("[AWDK_PERF] VRCSettings." + prop + " not found; set it in the SDK panel.");
    }
}
