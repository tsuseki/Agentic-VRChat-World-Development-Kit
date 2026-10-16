# Port workflow: PC world → Android (and iOS)

Step detail for `.omp/skills/vrchat-android-worlds/SKILL.md` §3. Stack: Unity 2022.3.22f1, Built-in RP, fully
baked (Bakery or Progressive), lilToon/Standard, UdonSharp, SDK 3.10.x. All editor work goes through the Unity MCP device (hard rule 5);
the snippets are `execute_code` bodies. Snippets that only read are safe at any time; the ones
marked **writes** change assets or settings.

## 0. Preconditions

- The PC version has passed D.3 (final-reviewer SHIP IT, reflection probes current) or is already
  live. The port never changes the PC look: if a fix needs a PC change, it goes back to C/D as a
  normal pass.
- WORLD.md records `Android: yes` and whether `VRChat/Mobile` shaders are approved (intake).
- One agent owns the editor for the whole port. A platform switch reimports every asset and
  reloads the domain; anything else editing the scene at that moment loses work. Save the scene and
  commit a checkpoint first (backgrounded `git add`; never push).

## 1. Inventory (Windows target, read-only)

Count what the port must deal with before touching anything:

```csharp
var shaders = new System.Collections.Generic.Dictionary<string, int>();
int cutout = 0, blend = 0, vcolMeshes = 0, renderers = 0; long tris = 0;
foreach (var r in UnityEngine.Object.FindObjectsOfType<Renderer>(true)) {
    renderers++;
    foreach (var m in r.sharedMaterials) {
        if (!m) continue;
        shaders[m.shader.name] = shaders.TryGetValue(m.shader.name, out var c) ? c + 1 : 1;
        if (m.renderQueue >= 3000) blend++; else if (m.renderQueue >= 2450) cutout++;
    }
    var mf = r.GetComponent<MeshFilter>();
    if (mf && mf.sharedMesh) {
        if (mf.sharedMesh.colors32.Length > 0) vcolMeshes++;
        for (int s = 0; s < mf.sharedMesh.subMeshCount; s++) tris += mf.sharedMesh.GetIndexCount(s) / 3;
    }
}
var sb = new System.Text.StringBuilder();
foreach (var kv in shaders) sb.AppendLine(kv.Value + "  " + kv.Key);
sb.AppendLine($"renderers {renderers}, tris(all, incl. inactive) {tris}, cutout slots {cutout}, blend slots {blend}, meshes with vertex colours {vcolMeshes}");
sb.AppendLine("post volumes: " + UnityEngine.Object.FindObjectsOfType<Component>(true).Count(c => c && c.GetType().Name.StartsWith("PostProcess")));
sb.AppendLine("mirrors: " + UnityEngine.Object.FindObjectsOfType<VRC.SDK3.Components.VRCMirrorReflection>(true).Length);
sb.AppendLine("realtime/mixed lights: " + UnityEngine.Object.FindObjectsOfType<Light>(true).Count(l => l.lightmapBakeType != LightmapBakeType.Baked));
sb.AppendLine("lightmaps: " + LightmapSettings.lightmaps.Length);
return sb.ToString();
```

Verified read-only through `execute_code` (Roslyn) on 2026-10-13. Also list:
textures above 1024 and their Android overrides, HDRI skybox size, audio clip sizes, video players
and their URLs (HTTPS?), particle systems, Udon behaviours with `Update`/`LateUpdate`, and the
per-viewpoint draw calls and visible tris from the PC D.2 report.

## 2. Plan the Android variant

Write a short port plan in WORLD.md before editing:

- **Material swaps** per [materials-and-textures.md](materials-and-textures.md) §1.
- **PC-only objects**: post-processing volume, decorative clutter the budget can't afford, a high-
  detail LOD, extra video screens. An object may differ between platforms only if it is **not**
  ContributeGI (its baked shadow stays in the shared lightmaps) and carries **no synced Udon,
  VRCObjectSync or pickup** (step 7).
- **Collision**: identical on both platforms, so nobody floats or sinks relative to players on the
  other platform. The workspace collider rules hold on both (no colliders on
  small props; always-on `SolidCollider` on big furniture; disabled-by-default `LieDownCollider`;
  one ramp box per stair flight).
- **Udon changes** behind `#if` (step 7).
- **Budget gaps** from §4 of the skill: what must shrink and how.

## 3. Install EasyQuestSwitch (needs the user's OK)

VRChat recommends EasyQuestSwitch for per-platform adjustments. It records
per-platform values on scene components and applies them when the build target changes
. VCC Curated package `vrchat.jordo.easyquestswitch` 1.4.0 (2024-03-25, still the
current curated version on 2026-10-13). Supported types include GameObject (active), Renderer
(materials), Material, MeshFilter (mesh), LODGroup, ReflectionProbe, `VRC_MirrorReflection`
(SDK3), Camera, Transform, colliders, AudioSource, `VRC_SpatialAudioSource` and Bakery lights. The
workspace never installs packages unasked: ask once, install through VCC.

Without it, the fallback is an editor build callback that applies a platform profile before each
SDK build and restores it after (the kit's `PerfCaptureGuard` shows the `IVRCSDKBuildRequestedCallback`
pattern). Prefer EasyQuestSwitch: it is VRChat-recommended and leaves no project code to maintain.

## 4. Mobile materials and objects

1. For each swapped material, duplicate it to `<name>_Mobile.mat` next to the original, set the
   mobile shader, and re-link the same textures. Standard Lite: albedo → `_MainTex`, colour →
   `_Color`, metallic/smoothness → `_MetallicGlossMap` (R/A), AO → `_OcclusionMap` (G), normal →
   `_BumpMap`, emission → `_EmissionMap` + `_EmissionColor`; turn on Glossy Reflections and Specular
   Highlights where the PC material is shiny; set Lightmap Type to MonoSH only if the bake is MonoSH.
   Enable GPU Instancing.
2. In EasyQuestSwitch, add each renderer and set its Android materials; add PC-only GameObjects with
   Android `active = false`; add a diegetic mirror (if any) with a reduced Reflect Layers set and a
   lower Mirror Resolution for Android.
3. Disabled objects still ship in the bundle. When the point is upload size rather than draw cost,
   the object must be removed from the Android build (EditorOnly-tag it only for the Android build
   via the build callback, or move the content to a PC-only asset); never EditorOnly a synced or
   ContributeGI object.

## 5. Switch the build target

SDK Control Panel → Builder → Platforms: untick Windows, tick Android → Switch.
Scripted equivalent (**writes**, long): `EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android)`.
The first switch reimports every asset; later switches are much faster.
The MCP connection drops during the domain reload; wait until `editor_state` reports not compiling
and not updating, then:

- Read the console; resolve any `error CS` (UdonSharp recompiles on platform switch since SDK
  3.9.0).
- Builder validation: fix the red "Default texture format on Android should be set to … ASTC"
  error with its Auto Fix. Yellow "World uses unsupported shader 'X'" lines are
  advisory: the SDK compares against a short list that omits Standard, lilToon and even Toon
  Standard. Profile those materials; don't chase the warning to zero.
- Check that EasyQuestSwitch applied the Android profile (spot-check three renderers).

## 6. Textures, lightmaps, encoding (**writes**)

Run on any target; setting overrides while on Windows only rewrites `.meta` files, and the ASTC
encode happens on the next Android import. Scene-material textures:

```csharp
var seen = new System.Collections.Generic.HashSet<string>(); int changed = 0;
AssetDatabase.StartAssetEditing();
try {
  foreach (var r in UnityEngine.Object.FindObjectsOfType<Renderer>(true))
    foreach (var m in r.sharedMaterials) {
      if (!m) continue;
      foreach (var p in m.GetTexturePropertyNames()) {
        var t = m.GetTexture(p) as Texture2D; if (!t) continue;
        var path = AssetDatabase.GetAssetPath(t);
        if (string.IsNullOrEmpty(path) || !seen.Add(path)) continue;
        var imp = AssetImporter.GetAtPath(path) as TextureImporter; if (imp == null) continue;
        bool ui = imp.textureType == TextureImporterType.Sprite || imp.textureType == TextureImporterType.GUI;
        foreach (var plat in new[] { "Android", "iPhone" }) {
          var s = imp.GetPlatformTextureSettings(plat);
          s.overridden = true;
          s.maxTextureSize = Mathf.Min(imp.maxTextureSize, 1024);
          s.format = ui ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6;
          imp.SetPlatformTextureSettings(s);
        }
        imp.SaveAndReimport(); changed++;
      }
    }
} finally { AssetDatabase.StopAssetEditing(); }
return changed + " textures overridden";
```

Then lower individual small/distant textures to 512 by hand, and handle UI (`Image`/`RawImage`
textures are not on Renderers), skybox and particle textures the same way. Lightmaps: run the same
override on `LightmapSettings.lightmaps[i].lightmapColor` / `.lightmapDir` with
`format = TextureImporterFormat.Automatic` (the encoding decides) and a max size only if the size
budget needs it; check the array is non-empty first (Bakery fills it when the scene loads).

Lightmap and HDR cubemap encoding for Android and iOS (internal setters, so reflection):

```csharp
var bf = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic;
var asm = typeof(PlayerSettings).Assembly;
var lm = asm.GetType("UnityEditor.LightmapEncodingQuality");
var cube = asm.GetType("UnityEditor.HDRCubemapEncodingQuality");
var setLm = typeof(PlayerSettings).GetMethod("SetLightmapEncodingQualityForPlatformGroup", bf);
var setCube = typeof(PlayerSettings).GetMethod("SetHDRCubemapEncodingQualityForPlatformGroup", bf);
foreach (var g in new[] { BuildTargetGroup.Android, BuildTargetGroup.iOS }) {
  setLm.Invoke(null, new object[] { g, System.Enum.Parse(lm, "High") });
  setCube.Invoke(null, new object[] { g, System.Enum.Parse(cube, "High") });
}
AssetDatabase.SaveAssets();
return "lightmap + cubemap encoding: High on Android and iOS";
```

Re-read both with the matching `Get…ForPlatformGroup` methods to confirm. Why High:
[materials-and-textures.md](materials-and-textures.md) §3.

## 7. Udon

- Platform code: `#if UNITY_ANDROID || UNITY_IOS … #endif` in UdonSharp is safe on SDK ≥ 3.9.0,
  which recompiles U# on platform switch.
- **Never** put `[UdonSynced]` fields, synced behaviours or `VRCObjectSync`/pickups inside a platform
  `#if`, and never remove a synced object from one platform. PC and Android players share
  instances, and network compatibility requires matching component types, count and order and
  matching synced-variable types, count and order on every synced object;
  network IDs are the link between the platform versions. One scene for both platforms keeps the IDs identical; if a separate Android scene is
  ever unavoidable, copy IDs with *VRChat SDK → Utilities → Network ID Import and Export Utility*.
- Near clip: a cuddle world's runtime near of 0.001–0.003 m (PC) becomes **0.01 m** on mobile,
  because a 24-bit depth buffer must be assumed there (z-separation 6 mm at 10 m for n = 0.001 vs
  0.6 mm for n = 0.01; `.omp/skills/clip-planes/SKILL.md` research §2.3). 1 cm is still "close enough for head
  pats and cuddles" (`.omp/skills/clip-planes/SKILL.md` §1).
- Phones: VRChat runs on touch-only devices. Use `OnInputMethodChanged(VRCInputMethod)` /
  `InputManager.GetLastUsedInputMethod()` == `VRCInputMethod.Touch` for a touch path, and
  `OnScreenUpdate` for orientation changes. Big buttons, short text,
  nothing that needs a VR gesture.
- Keep idle cost near zero: no per-frame `Update` polling in an idle world; mobile CPUs pay more for
  the same Udon work [INFERENCE].
- Requested pickups keep `proximity = 0.1f` and `AutoHoldMode.No` on every platform; a
  `PickupPlatformOverride` must not change them (`vrc-udon-workflow` module contract).

## 8. Measure in the editor (Android target)

- Per-viewpoint draw calls, SetPass and visible tris with the same `PerfSample` viewpoints as the PC
  D.2 report (`perf-optimizer`); compare with the skill's §4 budgets. Editor play mode does not
  reproduce device performance; it ranks costs and catches regressions.
- **Build** for Android (Builder → Build, or Build & Test without a device) and read the size: the
  SDK refuses an upload above 100 MB compressed; the Editor log's build "statistics"
  give the pre-compression breakdown; VRWorld Toolkit's Build Report
  reads Android build reports and diffs two builds (`vrchat-world-optimization/references/texture-caps.md`).
- Captures for the reviewer: the PC D.2 viewpoints, Android target, play mode, no post-processing.

## 9. Device test (the user's headset or phone)

Agents cannot judge comfort in a headset; the user runs this and reports back.

**Quest / Android (ADB)**:
1. Unity install has Android Build Support (VCC installs it by default).
2. Quest: developer mode through Meta Quest Developer Hub; phone/tablet: Build number ×7, then USB
   debugging. Data-capable USB cable; accept the debugging prompt.
3. Launch VRChat on the device once, then close it; keep the device unlocked.
4. Builder (Android target) → **Build and Test New Build**. Later iterations: press it again.
5. Wi-Fi alternative: `adb pair` / `adb connect` with the `adb.exe` under
   `<Unity>/Data/PlaybackEngines/AndroidPlayer/SDK/platform-tools`, Unity open first.
6. Trouble: unplug other debugging devices; restart USB debugging; Unity kills a running ADB server
   (start scrcpy after Unity); the package name setting is *VRChat → SDK → Android App Package Name*
   (default `com.vrchat.mobile.playstore`). scrcpy mirrors a phone to the desktop.

**iOS (VRChat Test Protocol)**: install iOS Build Support; Builder → iOS; the
console must show `[VTP] Listening on port 9002`; enter the PC's IP (SDK settings → Show Local IP
Address) in iOS Settings → Apps → VRChat → SDK IP Address; allow local-network access on the phone
and the Windows firewall prompt for Unity (delete a blocked "Unity Editor" inbound rule if the prompt
never appears); no VPN; same Wi-Fi. `[VTP] Client connected.` means ready.

What the user checks (≈ 15 min): load time and no crash; smooth at spawn alone (72 Hz on Quest;
VRChat's floor is 45 FPS at spawn); walk every room; lamps lit and no
banding in dark gradients; no flicker or z-fighting at distance; video plays; every toggle, teleport
door and the lie-down toggle; UI readable and tappable on a phone; mirror toggle (if any).

## 10. Review gate

Material swaps and stripped objects are visual changes, so the port passes the stage reviewer like
any D.2 change (hard rule 4): `final-reviewer`, FINAL mode, D.2 visual regression, briefed with the
Android-target captures next to the PC captures of the same viewpoints, the swap list, and "judge
against the lock, not against PC parity: no post-processing exists on Android; the mood must
survive in lighting and materials". NEEDS WORK findings are fixed on the Android variant only.

## 11. Back to Windows, upload

1. Switch back to Windows; confirm EasyQuestSwitch restored the PC materials and objects (spot-check;
   one PC capture diff against the shipped PC capture must be identical).
2. The user uploads. Builder → Platforms: tick Windows and Android (and iOS if the account supports
   it) → Build and Publish builds each target in turn. Same scene, same
   Pipeline Manager, so the same blueprint ID; never detach it. Check the Content Manager shows
   the world with both platforms.
3. iOS: if the Builder shows the red "iOS is not supported as a build target", the account has no
   iOS upload permission; ship without it and rely on the Android fallback.
4. **Every later PC update re-uploads Android too** when it touches anything synced, or players on
   the two builds land in incompatible instances [INFERENCE].
5. Log the Android budgets, swaps and the reviewer verdict in WORLD.md Decisions; commit.
