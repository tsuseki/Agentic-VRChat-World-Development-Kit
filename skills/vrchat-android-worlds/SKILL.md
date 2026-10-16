---
name: vrchat-android-worlds
description: Android (Meta Quest, Android phones and tablets) and iOS versions of VRChat worlds as a secondary target after the PC version — deciding at intake, the greybox, prop, material and lighting choices that make the port cheap, and the port of a finished PC world in the workspace stack (Unity 2022.3.22f1, Built-in RP, fully baked Bakery/Progressive, lilToon/Standard, UdonSharp) — one project switched per platform, per-platform materials and objects with EasyQuestSwitch, ASTC texture and lightmap-encoding overrides, mobile budgets, PC-only features (post-processing, mirrors, video, transparency), verification in the editor and on device with Build & Test, and upload to the same blueprint ID. Load when a brief asks for Quest, Android, iOS or mobile support, when porting or updating a world's Android build, or when judging whether a PC-world choice will survive mobile.
---

# Android and iOS versions of VRChat worlds

PC is always the primary target: every pipeline stage builds, reviews and ships the PC world first
(`.omp/skills/world-pipeline/SKILL.md`). The Android build is an optional **secondary version of the same
world**, made after D.3 from the same scene. Quest, Android phones and tablets all load the Android
build; iOS loads its own build or, without one, falls back to the Android build.

`[INFERENCE]` = derived, not stated by a source.
Detail: [references/port-workflow.md](references/port-workflow.md) (step-by-step with `execute_code`
snippets) and [references/materials-and-textures.md](references/materials-and-textures.md)
(shader mapping, texture and lightmap settings).

Workspace hard rules apply unchanged on every platform: fully baked lighting (no realtime or Mixed
lights), reflection probes re-baked after every bake, no colliders on small props (big furniture gets
an always-on `SolidCollider`, lie-on furniture a disabled-by-default `LieDownCollider`), one ramp box per stair flight, no `VRCStation` unless asked, requested
pickups at proximity 0.1 and AutoHold No, reviewer SHIP IT before anything counts as done, the
user uploads. lilToon/Standard are the default shaders; `VRChat/Mobile/*` shaders on the Android
build are a shader change the user approves once (recorded in WORLD.md).

## 1. Platform facts

| Fact | Value |
|---|---|
| Who loads the Android build | Meta Quest 2 or newer, PICO 4 or newer, HTC Vive XR Elite, Android 10+ phones and tablets |
| iOS | iPhones/iPads on iOS 17+. A world with an Android build but no iOS build is loaded from the Android build (experimental; works best with Standard Lite content). Guidance and limits for Android apply to iOS |
| No build for a platform | Players on it can't join or enter portals to the world |
| Blueprint ID | Every platform build uploads to the PC world's blueprint ID; the active build target decides which platform an upload is; the Builder can tick several platforms and publish all |
| Size limit | 100 MB compressed; the SDK refuses the upload above 104,857,600 bytes. No uncompressed limit for worlds |
| Shaders | Unrestricted for worlds (avatars: `VRChat/Mobile` only). VRChat still says to stick to mobile shaders where possible |
| Post-processing | Disabled completely on Android |
| Transparency | "Avoid transparency at all costs … alpha cutout counts as transparency" |
| Video | Android plays only HTTPS URLs; the URL resolver now exists on Android |
| Toon Standard | Mobile toon shader usable in worlds (AudioLink since 3.10.5), but it **skips every lightmap variant**: not for lightmapped statics |
| Standard Lite | Lightmaps and Bakery MonoSH supported (lightmapping fixed in 3.9.0); no alpha; vertex colours tint albedo; highlights and glossy reflections off by default |
| Lightmap encoding | Per platform. Our projects ship Android and iOS at **Low** (dLDR: clamps above 2, bands), PC at High |
| Light Volumes | Mobile avatar shaders don't read them (Toon Standard support is an open request), so probes light avatars on Android [INFERENCE] |
| UdonSharp | Recompiled on platform switch since SDK 3.9.0, so `#if UNITY_ANDROID \|\| UNITY_IOS` is safe |
| Shared instances | PC and Android players meet in one instance; synced objects must match on both builds |
| Frame budget | Quest renders at ≥ 72 Hz = 13.8 ms per frame |
| Depth buffer | Assume 24-bit fixed point on mobile; a 0.001 m near clip then z-fights at a few metres (see `.omp/skills/clip-planes/SKILL.md` research §2) [INFERENCE] |

## 2. Decide at intake, design for a cheap port

Intake (A.2) asks once and records in WORLD.md's Brief: `Platform: PC; Android: yes / later / no;
iOS: Android fallback / own build / no`, plus whether the Android build may use `VRChat/Mobile`
shaders (`.omp/skills/world-pipeline/SKILL.md` intake "Platform"). "Later" costs nothing now; "yes" adds the
choices below. Test the Android upload path early: one creator checked the iOS upload at the
greybox stage and planned from the start to avoid special shaders and post-processing so every
platform looks alike.

| Stage | Choice that makes the port cheap |
|---|---|
| A.3 / B.1 | Enclosed rooms, corridors and teleport islands occlude well; long views come from the skybox or backdrop cards (`.omp/skills/clip-planes/SKILL.md` §5), not geometry. Few large glass walls |
| B.2 | Budget the world against §4's Android row, not only the PC one (≈ 250k world tris) |
| C.1 assets | Textures sourced at ≤ 2K so the Android 1K override is a clean halving; one atlas material per object group (keep rooms separate for occlusion); opaque modelled silhouettes instead of cutout foliage, fences and lace; no leftover vertex colours on imported meshes |
| C.1 materials | Keep the mood in lighting and albedo, not post-processing (absent on Android). Flag every transparent or cutout material in the pass plan |
| C.2 | Touch-friendly interactions: big buttons, short labels, no VR-only gesture (phones are touch-only); video URLs HTTPS; diegetic mirrors off by default |
| D.1 | One bake serves both platforms. Same GI geometry on both builds; chart padding generous enough that a half-size Android atlas doesn't leak [INFERENCE] |
| D.3 | PC ships first; the port follows (§3) |

## 3. Port workflow (summary)

Full steps, snippets and checks: [references/port-workflow.md](references/port-workflow.md).

1. **Preconditions.** PC world at D.3 (final-reviewer SHIP IT). One agent owns the editor: the
   platform switch reimports everything and reloads the domain. Checkpoint commit.
2. **Inventory** on the Windows target (read-only snippet): shaders and slot counts, cutout/blend
   slots, vertex-colour meshes, post volumes, mirrors, video URLs, textures > 1K, Udon `Update`
   loops, PC D.2 per-viewpoint draw calls and tris.
3. **Plan** in WORLD.md: material swaps, PC-only objects (never ContributeGI, never synced),
   identical collision on both platforms, Udon `#if`s, budget gaps.
4. **EasyQuestSwitch** (VCC Curated `vrchat.jordo.easyquestswitch` 1.4.0; VRChat recommends it;
   install only with the user's OK) holds per-platform materials, active states, mirror settings
  .
5. **Mobile materials**: `<name>_Mobile.mat` copies on the same textures, swapped per platform
   ([materials-and-textures.md](references/materials-and-textures.md) §1).
6. **Switch to Android** in the SDK Builder; fix the red ASTC error with Auto Fix; read the console.
7. **Textures and encoding**: Android/iPhone overrides (≤ 1024, ASTC 6×6; UI 4×4); lightmap and HDR
   cubemap encoding High for Android and iOS (reflection snippet).
8. **Udon**: near clip 0.01 m on mobile, PC-only effects off, touch path; synced layout identical.
9. **Measure** in the editor against §4; **Build** for the size; VRWorld Toolkit Build Report.
10. **Device test** by the user: Quest/phone through Build & Test over ADB (USB or Wi-Fi), iOS
    through the VRChat Test Protocol on port 9002.
11. **Review**: final-reviewer (FINAL, D.2 visual regression) on Android-target captures beside the
    PC ones; fix its findings on the Android variant.
12. **Back to Windows**, verify the PC build is untouched, then **the user uploads** both platforms
    (and iOS if the account allows) to the same blueprint ID. Later PC updates that touch synced
    objects re-upload Android too.

## 4. Budgets (Android build)

Per player viewpoint, measured as in `perf-optimizer` (same viewpoints as the PC D.2 report). The
PC defaults in `perf-optimizer` "Default budgets" still govern the PC build.

| Metric | Android target | Hard limit / basis |
|---|---|---|
| Compressed world size | ≤ 80 MB, leaving room for updates [INFERENCE] | 100 MB, upload refused |
| World triangles | ≈ 250k for the whole world; visible per viewpoint ≤ 250k | VRChat recommendation, not an upload limit |
| Draw calls (batches) per viewpoint | ≤ 100, aim 50–80 at spawn | [INFERENCE] from Meta: whole frame < 100 (Quest 2) / < 200 (Quest 3); busy social apps 80–200 / 200–300; avatars take the rest |
| Textures | ≤ 1024, most 512; ASTC 6×6, UI 4×4, distant 8×8 | "Avoid large (> 1k) textures"; Crunch doesn't cut memory; ASTC defaults |
| Lightmaps | ≤ 1024 per atlas when the size budget needs it; encoding High | Keep lightmap resolution low |
| Reflection probes | 128 (256 for one hero probe) | [INFERENCE] |
| Frame rate | Smooth at 72 Hz alone at spawn on Quest; never below 45 FPS |— |
| Realtime lights / post-processing | 0 / none in the Android build | Workspace rule; post is disabled on Android |
| Transparent + cutout material slots | As few as the design allows; none on large surfaces |— |
| Mirrors / video players | Off by default / ≤ 1 playing (VRChat: ≤ 2) |— |
| Materials | GPU Instancing on every material |— |

## 5. Gotchas

| Symptom or trap | Cause | Fix |
|---|---|---|
| Banding and hue steps in dark gradients, lamp pools clipped flat on Android | Android lightmap encoding Low (dLDR) in our projects | Encoding High for Android and iOS; if it still bands, lightmap compression quality High or None |
| Toon Standard props look unlit or flat in a baked room | Toon Standard has no lightmap variants | Standard Lite or Lightmapped on lightmapped statics; Toon Standard only on probe-lit dynamic props |
| Lamp shades dark, flat-colour props white | `VRChat/Mobile/Lightmapped` has no emission and no colour | Standard Lite for emissive and untextured materials |
| Standard Lite surfaces dull, no reflections | Highlights and glossy reflections default off | Turn both on for shiny materials; reflection probes baked |
| Dark or blotchy patches after the swap | Standard Lite multiplies albedo by vertex colours | Re-export without vertex colours or keep that object on Standard |
| Yellow "World uses unsupported shader" on Standard, lilToon, even Toon Standard | The SDK checks a short avatar-era list | Advisory only: profile, don't chase to zero |
| Shadow of a missing object on the Android build | A ContributeGI object was hidden on Android only | Hide only non-GI objects; one shared bake |
| "Incompatible version" kicks, objects out of sync between PC and Quest players | Synced objects or fields differ between the builds (`#if` around `[UdonSynced]`, a synced object stripped) | Identical synced layout on both; re-upload both after sync changes |
| Z-fighting or flicker at a few metres on Quest only | Near clip 0.001 m with a 24-bit depth buffer | Near 0.01 m under `#if UNITY_ANDROID \|\| UNITY_IOS`; z-fight gate with `ZDepthFormat.Fixed24` (`.omp/skills/world-pipeline/SKILL.md` z-fight section) |
| Android looks brighter and flatter than PC | Post-processing (tonemapping, grading, bloom) is disabled | Judge Android against the lock, not PC parity; keep mood in lighting and materials |
| Video plays on PC, not on Quest | HTTP URL | HTTPS only on Android |
| Foliage, fences, lace, glass dominate GPU cost | Cutout and blend both cost fill rate on tile GPUs | Modelled silhouettes, fewer layers, fewer panes |
| Disabled PC-only decor still in the upload size | Inactive objects ship in the bundle | Strip from the Android build (EditorOnly via build callback) when size is the goal; never synced or GI objects |
| Avatars lit differently on Android in a Light Volume world | Mobile avatar shaders ignore Light Volumes | Keep a complete light-probe set |
| Agents' edits lost, MCP times out during the port | Platform switch reimports and reloads the domain | One editor owner; save first; wait for `editor_state` idle |
| Build & Test never opens the world | App not launched once, device locked, VRChat still open, other ADB devices, Unity killed scrcpy's ADB server | Follow the troubleshooting in VRChat's "Build and Test for Android Mobile" (https://creators.vrchat.com/platforms/android/build-test-mobile/) |
| Red "iOS is not supported as a build target" | The account has no iOS upload permission | Skip iOS; the Android fallback covers it |
| Phone players can't use the UI | Small world-space buttons, VR-only gestures | Large targets, VRC_UIShape, optional screen-space menu; detect `VRCInputMethod.Touch` |
| Requested pickup behaves differently on Quest | A `PickupPlatformOverride` changed its settings | Overrides must keep proximity 0.1 and AutoHold No |

## 6. Sign-off

The Android version is done when: the §4 table is filled with measured values (or a user-approved
exception in WORLD.md Decisions), the Android build size is read from a real build, the user's
device test passed, final-reviewer returned SHIP IT on the Android captures, the PC build is
verified unchanged after switching back, and WORLD.md records the swaps, budgets and verdict. Then
the user uploads.

Related: `.omp/skills/unity-vrc-world-sdk-3/SKILL.md` (`references/performance.md` Quest/Android section,
`references/upload.md` cross-platform procedure), `.omp/skills/vrchat-world-optimization/SKILL.md`
(attribution, Build Report), `.omp/skills/bakery-light-baking/SKILL.md` (encoding diagnostics),
`.omp/skills/clip-planes/SKILL.md` (depth precision), `.omp/skills/unity-vrc-udon-sharp/SKILL.md`,
`vrc-udon-workflow/references/texture-decisions.md` (bytes per format).

Sources: SOURCES.md (not needed to use this skill).
