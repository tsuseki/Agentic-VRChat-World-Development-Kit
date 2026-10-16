# Bakery Light Baking — Code Reference

Complete, copy-pasteable C# editor snippets. All verified on Unity 2022.3 + Bakery.
Everything uses reflection so it works both in `Assets/Editor` scripts and in dynamic
evaluation contexts (Unity MCP `execute_code`, REPL-style tooling) without compile-time
references to Bakery's types.

Shared helper used by several snippets:

```csharp
using System;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityEditor;

static Type FindType(string name)
{
    return AppDomain.CurrentDomain.GetAssemblies()
        .Select(a => a.GetType(name))
        .First(t => t != null);
}
```

---

## Snippet 1 — Read the ACTUAL bake settings (do this first, always)

Bakery's per-scene settings live on the `ftLightmapsStorage` component on the
`!ftraceLightmaps` GameObject. Every serialized field is prefixed `renderSettings*`
(e.g. `renderSettingsGISamples`, `renderSettingsBounces`, `renderSettingsDenoise`,
`renderSettingsTexelsPerUnit`, `renderSettingsMaxAutoResolution`,
`renderSettingsDenoiserType`, `renderSettingsSampleDiv`, `renderSettingsAdjustSamples`,
`renderSettingsHackAOIntensity` / `Samples` / `Radius`). Do not trust the UI — read
what was serialized.

```csharp
using System;
using System.Reflection;
using UnityEngine;
using UnityEditor;

// --- 1. Dump all Bakery per-scene render settings ---
var storageGO = GameObject.Find("!ftraceLightmaps");
if (storageGO == null)
{
    Debug.LogWarning("No !ftraceLightmaps object — Bakery has not stored settings in this scene.");
}
else
{
    var storage = storageGO.GetComponent("ftLightmapsStorage");
    var st = storage.GetType();
    foreach (var f in st.GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
    {
        if (!f.Name.StartsWith("renderSettings")) continue;
        Debug.Log($"{f.Name} = {f.GetValue(storage)}");
    }
    // Spot-check the usual suspects explicitly:
    Debug.Log("GI Samples: " + st.GetField("renderSettingsGISamples").GetValue(storage));
    Debug.Log("Denoise: "    + st.GetField("renderSettingsDenoise").GetValue(storage));
    Debug.Log("MaxAutoRes: " + st.GetField("renderSettingsMaxAutoResolution").GetValue(storage));
}

// --- 2. Lightmap encoding quality (API is INTERNAL in 2022.3 — reflection required) ---
var mi = typeof(PlayerSettings).GetMethod(
    "GetLightmapEncodingQualityForPlatformGroup",
    BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public);
var quality = mi.Invoke(null, new object[] { BuildTargetGroup.Standalone });
Debug.Log("Lightmap Encoding (Standalone): " + quality); // want: High (BC6H)

// --- 3. Enumerate baked lightmaps: format, size, importer compression ---
var lms = LightmapSettings.lightmaps;
for (int i = 0; i < lms.Length; i++)
{
    var tex = lms[i].lightmapColor;
    if (tex == null) { Debug.Log($"Lightmap {i}: <null>"); continue; }
    var path = AssetDatabase.GetAssetPath(tex);
    var importer = AssetImporter.GetAtPath(path) as TextureImporter;
    Debug.Log($"Lightmap {i}: {tex.width}x{tex.height} fmt={tex.format} " +
              $"compression={(importer != null ? importer.textureCompression.ToString() : "n/a")} path={path}");
}
```

Writing a setting (e.g. fix GI samples at 4 → 32):

```csharp
var storage = GameObject.Find("!ftraceLightmaps").GetComponent("ftLightmapsStorage");
storage.GetType().GetField("renderSettingsGISamples").SetValue(storage, 32);
EditorUtility.SetDirty(storage);
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(
    UnityEngine.SceneManagement.SceneManager.GetActiveScene());
```

Compression A/B test (definitive, revert afterwards):

```csharp
var importer = (TextureImporter)AssetImporter.GetAtPath(path);
importer.textureCompression = TextureImporterCompression.Uncompressed;
importer.SaveAndReimport();
```

---

## Snippet 2 — Fire a full Bakery bake from script

`ftRenderLightmap.RenderLightmap()` (the static method) **silently does nothing**.
Go through the editor window instead:

```csharp
var ftType = FindType("ftRenderLightmap");
var window = EditorWindow.GetWindow(ftType);

// Load the scene's serialized settings into the window, then press "Render".
ftType.GetMethod("LoadRenderSettings",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, null);
ftType.GetMethod("RenderButton",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, new object[] { false });
```

Poll for completion:

```csharp
var inProgress = (bool)FindType("ftRenderLightmap")
    .GetField("bakeInProgress", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
    .GetValue(null);
```

Completion also rewrites the atlas files — watch mtime on
`Assets/BakeryLightmaps/*_final.hdr` as a second signal that new data actually landed.

**Unattended launches**: `RenderButton` can stop on a modal dialog (samples warning,
prefab warning) and then the bake just sits there looking like it is working. Set the
statics first — all of them live on `ftRenderLightmap`:

```csharp
void SetStatic(Type t, string name, object v) =>
    t.GetField(name, BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
     ?.SetValue(null, v);

SetStatic(ftType, "verbose", false);          // errors go to the console, not a dialog
SetStatic(ftType, "userCanceled", false);     // clear a previous cancel
SetStatic(ftType, "suppressPopups", true);
SetStatic(ftType, "samplesWarning", false);
SetStatic(ftType, "prefabWarning", false);
```

Also check `bakeInProgress` **before** launching — `RenderButton` has no reentry guard,
and two exports fight over `%TEMP%\frender\heightmaps.bin` (IOException wedge).

---

## Snippet 3 — Selective (subset) bake

**Version warning (source-verified Bakery 1.96): the recipe below is NOT selective in 1.96.**
`RenderButton` explicitly resets `selectedOnly=false` before scheduling its update coroutine
(`ftRenderLightmap.cs`, line 1333). The native "Render Selected Groups" button instead sets
`selectedOnly=true`, `probesOnlyL1=false`, `fullSectorRender=false`, then schedules
`RenderLightmapFunc`/`RenderLightmapUpdate` directly (lines 2372–2385). Follow the installed
version's native path, and prove selectivity by comparing unrelated atlas timestamps/hashes.
Do not report a selected bake merely because the field was set before `RenderButton`.

```csharp
var ftType = FindType("ftRenderLightmap");
var window = EditorWindow.GetWindow(ftType);

// 1. Select the roots you want rebaked.
Selection.objects = new UnityEngine.Object[] {
    GameObject.Find("Interior_Root"),   // your objects here
};

// 2. Set the window's instance field, then render.
ftType.GetField("selectedOnly",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .SetValue(window, true);
ftType.GetMethod("LoadRenderSettings",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, null);
// LoadRenderSettings can reset selectedOnly — set it again after loading:
ftType.GetField("selectedOnly",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .SetValue(window, true);
ftType.GetMethod("RenderButton",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, new object[] { false });
```

Per-area `BakeryLightmapGroup` assets make subset rebakes cheap (each area gets its own
atlas, so rebaking one room does not touch the others). When assigning groups from
script, the `BakeryLightmapGroupSelector` component's field names are:

- `active`
- `lmgroupAsset`  ← NOT `lmgroup`
- `instanceResolutionOverride`
- `instanceResolution`

---

## Snippet 4 — Reflection probes (required after EVERY bake)

If you skip this, glossy surfaces keep a NULL `bakedTexture` and fall back to the
skybox — the classic "blue sheen at night". Prefer Bakery's own probe pass:

```csharp
var ftType = FindType("ftRenderLightmap");
var window = EditorWindow.GetWindow(ftType);
ftType.GetMethod("RenderReflectionProbesButton",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, new object[] { false });   // bool showMsgWindows
```

Alternative (Unity built-in, per probe):

```csharp
UnityEditor.Lightmapping.BakeReflectionProbe(probe, assetPath);
```

Quick audit for stale probes:

```csharp
foreach (var probe in UnityEngine.Object.FindObjectsOfType<ReflectionProbe>())
    Debug.Log($"{probe.name}: bakedTexture={(probe.bakedTexture ? probe.bakedTexture.name : "NULL <-- skybox fallback!")}");
```

---

## Snippet 5 — Light probes: silent failure and verification

`RenderLightProbesButton` **aborts instantly** if scene geometry changed since the last
full bake. Console message:

```
Scene geometry/layout changed since last full bake. Use Render button instead
```

It leaves `bakeInProgress = false`, which looks identical to "finished successfully".
Symptom: every probe returns identical ambient-only SH and dynamic objects render
near-black. Rule: **run the probe pass immediately after a full bake, never standalone
after edits.**

```csharp
var ftType = FindType("ftRenderLightmap");
var window = EditorWindow.GetWindow(ftType);
ftType.GetMethod("RenderLightProbesButton",
    BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
    .Invoke(window, null);
```

Verify the bake actually produced spatially-varying data — sample 2–3 spots in
different rooms; the SH values MUST differ:

```csharp
using UnityEngine.Rendering;

void SampleProbe(Vector3 pos)
{
    LightProbes.GetInterpolatedProbe(pos, null, out SphericalHarmonicsL2 sh);
    // DC (ambient) term per channel — if identical everywhere, the probe bake failed silently.
    Debug.Log($"{pos}: R={sh[0,0]:F4} G={sh[1,0]:F4} B={sh[2,0]:F4}");
}

SampleProbe(new Vector3( 0f, 1.5f,  0f));   // room A
SampleProbe(new Vector3(10f, 1.5f,  0f));   // room B
SampleProbe(new Vector3( 0f, 1.5f, 10f));   // outdoors / third area
```

---

## Snippet 6 — Draft / Final presets (two-stage workflow)

Bakery's own preset type is `ftSettingsAsset`. It carries the same `renderSettings*`
field names as `ftLightmapsStorage`, so a preset is just a field-by-field copy. Assets
created this way also drop straight into the Bakery window's **Presets** field
(Settings Mode = Experimental).

Drop this in `Assets/Editor/`. It uses reflection throughout, so it needs no assembly
reference to Bakery and cannot break the project if Bakery is removed.

```csharp
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public static class BakeryPresets
{
    const string kDir       = "Assets/BakerySettings";
    const string kFinalPath = kDir + "/Bakery_Final.asset";
    const string kDraftPath = kDir + "/Bakery_Draft.asset";

    // DRAFT = FINAL with these overridden. Cost ~ (texels) x (GI samples),
    // and texels scale with texelsPerUnit^2. Bounces stays at the FINAL value
    // on purpose: it changes how bright a sealed room bakes.
    static readonly Dictionary<string, object> kDraftOverrides = new Dictionary<string, object>
    {
        { "renderSettingsGISamples",         16 },
        { "renderSettingsTexelsPerUnit",     5.0f },
        { "renderSettingsMaxAutoResolution", 1024 },
        { "renderSettingsHackAOSamples",     8 },
        { "renderSettingsFixSeams",          false },
    };

    [MenuItem("Bakery/Presets/Apply DRAFT")] static void ApplyDraft() { Apply(kDraftPath, "DRAFT"); }
    [MenuItem("Bakery/Presets/Apply FINAL")] static void ApplyFinal() { Apply(kFinalPath, "FINAL"); }

    // Bootstrap / re-capture: FINAL := whatever is dialled in now, DRAFT := FINAL + overrides.
    [MenuItem("Bakery/Presets/Capture current as FINAL")]
    static void Capture()
    {
        if (!Init() || Playing()) return;
        var storage = GetStorage();
        if (!AssetDatabase.IsValidFolder(kDir)) AssetDatabase.CreateFolder("Assets", "BakerySettings");

        var final = GetOrCreate(kFinalPath);
        CopyFields(storage, final);
        EditorUtility.SetDirty(final);

        var draft = GetOrCreate(kDraftPath);
        CopyFields(storage, draft);
        foreach (var kv in kDraftOverrides) SetField(draft, kv.Key, kv.Value);
        EditorUtility.SetDirty(draft);

        AssetDatabase.SaveAssets();
    }

    static void Apply(string path, string label)
    {
        if (!Init() || Playing() || BakeInProgress()) return;
        var preset  = AssetDatabase.LoadAssetAtPath(path, tAsset);
        var storage = GetStorage();
        if (preset == null || storage == null) { Debug.LogError("[BakeryPresets] missing preset/storage"); return; }

        Undo.RecordObject(storage, "Apply Bakery preset");
        CopyFields(preset, storage);
        SetField(storage, "renderSettingsAsset", null);   // else Bakery greys out its own settings UI
        EditorUtility.SetDirty(storage);
        EditorSceneManager.MarkSceneDirty(((Component)storage).gameObject.scene);

        // Push storage -> window fields AND the ftBuildGraphics statics
        // (texelsPerUnit / maxAutoResolution live there, not on the window).
        var load = tRender.GetMethod("LoadRenderSettings", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        foreach (var w in Resources.FindObjectsOfTypeAll(tRender)) { load.Invoke(w, null); ((EditorWindow)w).Repaint(); }

        Debug.Log("[BakeryPresets] applied " + label);
    }

    // ---- plumbing ----
    static Type tRender, tStorage, tAsset;

    static bool Init()
    {
        tRender  = tRender  ?? FindType("ftRenderLightmap");
        tStorage = tStorage ?? FindType("ftLightmapsStorage");
        tAsset   = tAsset   ?? FindType("ftSettingsAsset");
        if (tRender != null && tStorage != null && tAsset != null) return true;
        Debug.LogError("[BakeryPresets] Bakery types not found");
        return false;
    }

    // Bakery's types are not always reachable by full name from every assembly - scan.
    static Type FindType(string name)
    {
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type[] ts; try { ts = asm.GetTypes(); } catch { continue; }
            foreach (var t in ts) if (t.Name == name) return t;
        }
        return null;
    }

    // The settings live on a scene component, so a play-mode write is discarded on exit.
    static bool Playing()
    {
        if (!EditorApplication.isPlaying) return false;
        Debug.LogError("[BakeryPresets] stop play mode first - the preset would be discarded on exit.");
        return true;
    }

    static bool BakeInProgress()
    {
        var f = tRender.GetField("bakeInProgress", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        if (f == null || !(bool)f.GetValue(null)) return false;
        Debug.LogError("[BakeryPresets] a bake is running");
        return true;
    }

    static UnityEngine.Object GetStorage()
    {
        // static ftLightmapsStorage FindRenderSettingsStorage(GameObject forSceneObject = null)
        var m = tRender.GetMethod("FindRenderSettingsStorage", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
        return m.Invoke(null, new object[] { null }) as UnityEngine.Object;
    }

    static UnityEngine.Object GetOrCreate(string path)
    {
        var a = AssetDatabase.LoadAssetAtPath(path, tAsset);
        if (a == null) { a = ScriptableObject.CreateInstance(tAsset); AssetDatabase.CreateAsset(a, path); }
        return a;
    }

    // ftSettingsAsset and ftLightmapsStorage share every render-setting field name.
    // Scene-only state (lightmap bindings, sector, active preset) has no counterpart
    // on the asset and is skipped automatically.
    static void CopyFields(UnityEngine.Object src, UnityEngine.Object dst)
    {
        foreach (var sf in src.GetType().GetFields(BindingFlags.Public | BindingFlags.Instance))
        {
            if (!sf.Name.StartsWith("renderSettings")) continue;
            if (sf.Name == "renderSettingsAsset" || sf.Name == "renderSettingsSector") continue;
            var df = dst.GetType().GetField(sf.Name, BindingFlags.Public | BindingFlags.Instance);
            if (df != null && df.FieldType.IsAssignableFrom(sf.FieldType)) df.SetValue(dst, sf.GetValue(src));
        }
    }

    static void SetField(UnityEngine.Object target, string name, object value)
    {
        var f = target.GetType().GetField(name, BindingFlags.Public | BindingFlags.Instance);
        if (f == null) return;
        if (value != null && f.FieldType != value.GetType())
            value = Convert.ChangeType(value, f.FieldType, System.Globalization.CultureInfo.InvariantCulture);
        f.SetValue(target, value);
    }
}
```

Verifying a switch actually took (the storage alone is not enough — the atlasing
values are mirrored into `ftBuildGraphics` statics by `LoadRenderSettings`):

```csharp
var g = FindType("ftBuildGraphics");
var flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
Debug.Log("texelsPerUnit="     + g.GetField("texelsPerUnit", flags).GetValue(null) +
          " maxAutoResolution=" + g.GetField("maxAutoResolution", flags).GetValue(null));
```

After the bake, confirm the atlases really came out at draft size:

```csharp
foreach (var lm in LightmapSettings.lightmaps)
    Debug.Log($"{lm.lightmapColor.name} {lm.lightmapColor.width}x{lm.lightmapColor.height}");
```

Sequencing reminders:

- Switching presets invalidates the atlas layout → the next bake must be the full
  **Render**; `selectedOnly` is refused (`sceneNeedsToBeRebuilt`). Do per-area bakes
  *within* a preset, not across a switch.
- Both presets share `renderSettingsOutPath`, so a draft bake replaces the final
  `*_final.hdr` files. Plan on a full final bake afterwards.
- Re-capture FINAL (`Bakery/Presets/Capture current as FINAL`) whenever you tune the
  window, otherwise "apply FINAL" silently rolls your tuning back.

---

## Snippet 7 — Samples Multiplier: a draft knob that keeps per-area bakes working

Bakery's own draft mechanism. Tooltip: *"Multiplies all shadow and GI samples by the
specified factor. Use this to quickly change between draft and final quality."* The UI
slider is inverted (shows `1/N`); internally it is a **divisor**:

```csharp
// ftRenderLightmap.cs
public static int sampleDivisor = 1;
int SampleCount(int samples)
{
    if (samples == 0) return 0;
    return System.Math.Max(samples / sampleDivisor, 1);
}
// applied at write time:  fgi.Write(SampleCount(giSamples));  — and to every light's samples
```

Because it scales *samples only*, it never touches texel density or atlas layout, so it
does **not** set `ftBuildGraphics.sceneNeedsToBeRebuilt` — *Render selected groups* still
works after changing it. That makes it the better inner loop when iterating on one room.

```csharp
var tRender = FindType("ftRenderLightmap");
var stat    = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
tRender.GetField("sampleDivisor", stat).SetValue(null, 8);   // 1/8 samples

// persist it on the scene storage so it survives a domain reload
var storage = tRender.GetMethod("FindRenderSettingsStorage", stat)
                     .Invoke(null, new object[] { null });
storage.GetType().GetField("renderSettingsSampleDiv").SetValue(storage, 8);
EditorUtility.SetDirty((UnityEngine.Object)storage);
```

Reset to `1` before the final bake — like every other render setting it is *not* restored
by a domain reload, so a stale value silently ships a low-sample bake.

Related incremental knobs on the same window (all `renderSettings*` on the storage), worth
using before dropping quality at all:

| Field / UI | Effect |
|---|---|
| *Export Geometry and Maps* (off) | Skips the export stage entirely when geometry is unchanged — the ~40 s that a scripted `forceRebuildGeometry = true` always pays |
| *Update Unmodified Lights* | Re-bakes only lights that did not change |
| *Update Modified Lights and GI* | Re-bakes changed lights + GI, leaving the rest |

The trap is the same for all three: if geometry *did* change, the result is stale and
looks perfectly plausible. Batch geometry edits, then take one full Render.

---

## Debug sequence A — washed-out / flat bake

A shadowless realtime directional light adds on top of lightmaps and penetrates all
geometry. Ceilings face away from it and look fine, which disguises the cause.

1. **Sample the atlas directly** — open `Assets/BakeryLightmaps/*_final.hdr` (or read
   pixels via script). Is the shadow present in the data? If yes, the bake is fine and
   something is adding light at render time.
2. **Check the renderer** — `renderer.lightmapIndex` must be >= 0 and Receive GI set to
   Lightmaps.
3. **White-material swap test** — assign a plain white material to an affected wall:
   - renders flat **BRIGHT** → an additive realtime light is the culprit
   - renders flat **DARK** → the lightmap is missing/not applied

Fix: any helper realtime light must have its `cullingMask` restricted to a dedicated
layer (that scene geometry is not on), or be deleted before judging lighting.

## Debug sequence B — blue sheen / blue tint

Two distinct causes; separate them with one line:

```csharp
RenderSettings.reflectionIntensity = 0f;   // A/B test — remember to restore
```

- Blue **disappears** → reflection probes: NULL `bakedTexture` giving skybox-fallback
  specular. Re-render probes (Snippet 4).
- Blue **persists** → it is baked INTO the lightmap: sky-lit hidden exterior faces
  whose UV charts bleed into interior charts. Fix the geometry/UVs (exclude exterior
  faces from the bake, or give them separate charts with padding) and rebake.

## Debug checklist — chroma blobs (red/green)

1. Read actual settings (Snippet 1) — never diagnose from memory.
2. `renderSettingsGISamples` < 16? → raise to 16, or 32 for dim interiors. This was the
   root cause in the verified case (found at 4; denoiser smeared the chroma noise into
   blobs).
3. Encoding not High Quality (BC6H), or Quest/Android target? → fix encoding, A/B with
   uncompressed importer. Compression artifacts look blocky green/magenta rather than
   soft mottled.
4. Blobs merely look huge? → texel density: `renderSettingsMaxAutoResolution` 1024 with
   large walls at ~20 texels/unit crams everything into one atlas; try 2048.
5. Only some areas blotchy after the global fix? → per-object sample multipliers, not a
   higher global value.

## Misc pitfalls

- `renderSettingsHackAOIntensity` defaults to **0** — Bakery AO is off unless explicitly
  enabled (good starting point: intensity 0.7, radius 0.4) for furniture contact shadows.
- ProBuilder `ToMesh()` invalidates Bakery UV2 — always rebake after mesh edits.
- Scripted scene edits (`SetParent`, rename) do NOT dirty the scene — call
  `EditorSceneManager.MarkSceneDirty(...)` before saving, or a Bakery reload wipes them.
- Play mode requests revert silently when there are compile errors — grep the console
  for `error CS` before assuming your editor script ran.
