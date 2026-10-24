using System.Text;
using UdonSharp;
using UdonSharpEditor;
using UnityEditor;
using UnityEngine;
using VRC.SDK3.Components;

/// <summary>
/// Wires plush fire screams. Copy to Assets/&lt;World&gt;/Editor/ and the three Udon scripts to Assets/&lt;World&gt;/Udon/.
/// Every step is idempotent and short enough for one MCP execute_code call. Order:
///   CreatePrograms(udonDir) (then wait for the compile) -> ImportClips(audioDir) -> Settings(clip)
///   -> Zone(...) per fire -> WireAll().
/// </summary>
public static class FumoScreamBuilder
{
    const string Root = "FUMO_SCREAM";
    const int WalkthroughLayer = 17; // VRChat built-in: collides with Pickup, never with Player / PlayerLocal

    /// <summary>UdonSharp program assets next to FumoScream.cs, FumoScreamSettings.cs, FumoFireZone.cs.</summary>
    public static string CreatePrograms(string udonDir)
    {
        if (!udonDir.EndsWith("/")) udonDir += "/";
        var sb = new StringBuilder();
        foreach (string n in new[] { "FumoScream", "FumoScreamSettings", "FumoFireZone" })
        {
            string path = udonDir + n + ".asset";
            if (AssetDatabase.LoadAssetAtPath<UdonSharpProgramAsset>(path) != null) { sb.AppendLine(n + " exists"); continue; }
            var src = AssetDatabase.LoadAssetAtPath<MonoScript>(udonDir + n + ".cs");
            if (src == null) { sb.AppendLine(n + " SCRIPT MISSING"); continue; }
            var program = ScriptableObject.CreateInstance<UdonSharpProgramAsset>();
            program.sourceCsScript = src;
            AssetDatabase.CreateAsset(program, path);
            sb.AppendLine(n + " created");
        }
        AssetDatabase.SaveAssets();
        UdonSharp.Compiler.UdonSharpCompilerV1.CompileSync();
        return sb.ToString();
    }

    /// <summary>Scream clips: mono, Vorbis q0.7, compressed in memory, preloaded (short one-shots).</summary>
    public static string ImportClips(string audioDir)
    {
        var sb = new StringBuilder();
        foreach (string g in AssetDatabase.FindAssets("t:AudioClip", new[] { audioDir }))
        {
            string path = AssetDatabase.GUIDToAssetPath(g);
            var imp = AssetImporter.GetAtPath(path) as AudioImporter;
            if (imp == null) continue;
            var s = new AudioImporterSampleSettings
            {
                loadType = AudioClipLoadType.CompressedInMemory,
                compressionFormat = AudioCompressionFormat.Vorbis,
                quality = 0.7f,
                sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate,
                preloadAudioData = true,
            };
            imp.forceToMono = true;
            imp.loadInBackground = false;
            imp.defaultSampleSettings = s;
            imp.SaveAndReimport();
            sb.AppendLine(path + " -> CompressedInMemory Vorbis q70 mono");
        }
        return sb.ToString();
    }

    /// <summary>Root FUMO_SCREAM with the one shared settings object. Swap the scream later by re-running with another clip.</summary>
    public static string Settings(string clipPath, float volume = 1f, float cooldownAfterEnd = 2.5f)
    {
        var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(clipPath);
        if (clip == null) return "ERROR clip not found: " + clipPath;
        var root = RootGo(true);
        var settings = root.GetComponent<FumoScreamSettings>();
        if (settings == null) settings = UdonSharpUndo.AddComponent<FumoScreamSettings>(root);
        settings.scream = clip;
        settings.volume = volume;
        settings.cooldownAfterEnd = cooldownAfterEnd;
        UdonSharpEditorUtility.CopyProxyToUdon(settings);
        SyncMode(settings);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(root.scene);
        return "settings clip=" + clip.name + " " + clip.length.ToString("F2") + "s";
    }

    /// <summary>One trigger box over a fire's flame area (world-space centre and size, axis-aligned).
    /// Keep it inside the flames: it must not reach any plush's resting collider or its Rest_ support.</summary>
    public static string Zone(string name, Vector3 worldCenter, Vector3 size)
    {
        var root = RootGo(true);
        Transform t = root.transform.Find(name);
        GameObject g = t != null ? t.gameObject : new GameObject(name);
        if (t == null) g.transform.SetParent(root.transform, false);
        g.transform.position = worldCenter;
        g.transform.rotation = Quaternion.identity;
        g.transform.localScale = Vector3.one;
        g.layer = WalkthroughLayer;
        GameObjectUtility.SetStaticEditorFlags(g, 0);
        var bc = g.GetComponent<BoxCollider>();
        if (bc == null) bc = g.AddComponent<BoxCollider>();
        bc.isTrigger = true;
        bc.center = Vector3.zero;
        bc.size = size;
        var zone = g.GetComponent<FumoFireZone>();
        if (zone == null) zone = UdonSharpUndo.AddComponent<FumoFireZone>(g);
        SyncMode(zone);
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(g.scene);
        return "zone " + name + " c=" + worldCenter.ToString("F3") + " s=" + size.ToString("F3");
    }

    /// <summary>Every pickup named Fumo_* (active or not): 3D voice + FumoScream. Pickup settings untouched.</summary>
    public static string WireAll()
    {
        var root = RootGo(false);
        var settings = root != null ? root.GetComponent<FumoScreamSettings>() : null;
        if (settings == null) return "ERROR run Settings(clip) first";
        var sb = new StringBuilder();
        int n = 0;
        foreach (var pk in Resources.FindObjectsOfTypeAll<VRCPickup>())
        {
            if (!pk.gameObject.scene.IsValid() || !pk.name.StartsWith("Fumo_")) continue;
            var g = pk.gameObject;

            var src = g.GetComponent<AudioSource>();
            if (src == null) src = g.AddComponent<AudioSource>();
            src.clip = null; // FumoScream assigns settings.scream at play time
            src.playOnAwake = false;
            src.loop = false;
            src.spatialBlend = 1f;
            src.volume = 1f;
            src.dopplerLevel = 0f;
            src.rolloffMode = AudioRolloffMode.Logarithmic;
            src.minDistance = 0.5f;
            src.maxDistance = 8f;
            src.spatialize = false;

            var sp = g.GetComponent<VRCSpatialAudioSource>();
            if (sp == null) sp = g.AddComponent<VRCSpatialAudioSource>();
            sp.EnableSpatialization = true;
            sp.Gain = 0f;
            sp.Near = 0.5f;
            sp.Far = 8f;
            sp.VolumetricRadius = 0f;
            sp.UseAudioSourceVolumeCurve = false;
            EditorUtility.SetDirty(sp);

            var fs = g.GetComponent<FumoScream>();
            if (fs == null) fs = UdonSharpUndo.AddComponent<FumoScream>(g);
            fs.settings = settings;
            fs.voice = src;
            UdonSharpEditorUtility.CopyProxyToUdon(fs);
            SyncMode(fs);

            sb.AppendLine(Path(g.transform) + " active=" + g.activeInHierarchy + " prox=" + pk.proximity + " autoHold=" + pk.AutoHold
                + " objSync=" + (g.GetComponent<VRCObjectSync>() != null) + " layer=" + g.layer);
            n++;
        }
        UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(root.scene);
        return "plushies=" + n + "\n" + sb;
    }

    static GameObject RootGo(bool create)
    {
        foreach (var go in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            if (go.name == Root) return go;
        if (!create) return null;
        var r = new GameObject(Root);
        GameObjectUtility.SetStaticEditorFlags(r, 0);
        return r;
    }

    // UdonSharpUndo.AddComponent leaves the backing UdonBehaviour on Continuous. Programs with sync mode None must be
    // SyncType.None; NoVariableSync programs (FumoScream sends network events, which ClientSim and VRChat refuse on
    // SyncType.None) stay Continuous, which costs no bandwidth without synced fields.
    static void SyncMode(UdonSharpBehaviour proxy)
    {
        var ub = UdonSharpEditorUtility.GetBackingUdonBehaviour(proxy);
        if (ub == null) return;
        var want = ((UdonSharpProgramAsset)ub.programSource).behaviourSyncMode == BehaviourSyncMode.None
            ? VRC.SDKBase.Networking.SyncType.None : VRC.SDKBase.Networking.SyncType.Continuous;
        if (ub.SyncMethod != want)
        {
            ub.SyncMethod = want;
            EditorUtility.SetDirty(ub);
        }
    }

    static string Path(Transform t)
    {
        string p = t.name;
        while (t.parent != null) { t = t.parent; p = t.name + "/" + p; }
        return p;
    }
}
