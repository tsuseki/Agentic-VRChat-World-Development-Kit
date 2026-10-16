# Mobile materials, textures, lightmaps and probes

Detail for `.omp/skills/vrchat-android-worlds/SKILL.md` §4–§5.
Everything here applies to the iOS build too: iOS uses the Android guidance and limits.

## 1. Shader choice on the Android build

World shaders are not restricted on Android; avatar shaders are.
VRChat still says "use mobile shaders on Android … most shaders will work on Android but usually take
more processing power". **Workspace rule:** lilToon/Standard are the
defaults; a `VRChat/Mobile/*` shader is a shader change, so the Android build uses one only after the
user has said yes (record it in WORLD.md Decisions). Without that yes, keep lilToon/Standard on
Android and win the budget with texture size, transparency and draw calls.

What the SDK's own mobile shaders actually do, read from the SDK 3.10.5 source:

| Shader | Lightmaps | Colour / emission | Other facts | Use it for |
|---|---|---|---|---|
| `VRChat/Mobile/Standard Lite` | Yes (Unity and Bakery MonoSH via *Lightmap Type*); worlds no longer break lightmapping since 3.9.0 | `_Color`, emission map + colour | Metallic(R)/Smoothness(A) map, separate Occlusion(G), normal, detail. **No alpha** (no cutout, no blend). **Vertex colours always multiply albedo.** *Specular Highlights* and *Glossy Reflections* default **off**. No realtime shadows, no extra per-pixel lights (`noforwardadd noshadow`) | The default lightmapped static: walls, floors, furniture, emissive lamp shades |
| `VRChat/Mobile/Lightmapped` | Yes | **None**: albedo × lightmap only, no `_Color`, no emission | Cheapest world shader; VRChat's recommended basic world shader | Large diffuse surfaces with a real texture (plaster, concrete, terrain-like ground) |
| `VRChat/Mobile/Toon Standard` | **No**: every pass has `skip_variants LIGHTMAP_ON` | Ramp, rim, matcap, emission, AudioLink since 3.10.5 | Opaque only. Outline variant is PC-only and falls back | Probe-lit dynamic props in a toon-styled world; never lightmapped statics |
| `VRChat/Mobile/Skybox` | — | — | Cubemap + rotation | Skybox, if the PC sky is a cubemap |
| `VRChat/Mobile/Worlds/Supersampled UI` | — | Unlit | Use with mip maps for crisp text | World-space UI text and panels |
| `VRChat/Mobile/Particles/Additive`, `/Multiply` | — | — | Additive/multiply avoid sorting; still fill-rate cost | Particles |

Every material: tick **Enable GPU Instancing**. Static-batched renderers
are not instanced, so it matters for repeated non-static meshes.

### Mapping PC materials

| PC material | Android material (mobile shaders approved) | Without approval |
|---|---|---|
| Opaque Standard / lilToon, textured | Standard Lite (same albedo, normal, metallic/smoothness); Lightmapped if it is plain diffuse | Keep; strip unused lilToon features |
| Flat-colour material, no texture | Standard Lite (`_Color`). **Not** Lightmapped: it has no colour and renders white | Keep |
| Emissive lamp shade, screen frame, sign | Standard Lite with the same emission colour/intensity | Keep |
| Metal, glass-like, polished wood that relies on reflections | Standard Lite with *Glossy Reflections* and *Specular Highlights* on; probes baked | Keep |
| Glass panes (blend) | Fewer, larger panes; keep a transparent lilToon/Standard material only where the view needs it; otherwise an opaque tinted pane or open frame | Same |
| Cutout foliage, fences, lace, hair cards | Modelled silhouettes or fewer cards; cutout **counts as transparency** on mobile | Same |
| Toon-styled probe-lit props | Toon Standard | Keep |
| Water, custom FX shaders | Profile; replace with a simple scrolling Standard Lite or remove | Profile |
| Video screen | Keep the player's own screen shader; it must not be ContributeGI | Same |

Make the Android materials as copies (`<name>_Mobile.mat`) that reference the **same texture
assets**; the texture's Android override (§2) then applies to both. Never edit the PC material in
place. Switch them per platform with EasyQuestSwitch Renderer entries ([port-workflow.md](port-workflow.md) step 4).

**Vertex colours.** Standard Lite (and Diffuse, Toon Lit, Matcap Lit) multiply albedo by vertex
colour. Imported FBX/GLB meshes with leftover black or random vertex
colours render dark or blotchy. Check `mesh.colors.Length > 0` on every swapped renderer and fix at
the source (re-export without colours) or keep that object on Standard.

## 2. Textures

| Texture | Android/iOS override | Notes |
|---|---|---|
| Albedo, mask, metallic/smoothness | max **1024**, ASTC 6×6 | 512 for small or distant props |
| Normal maps | max 1024 (512 for small props), ASTC 6×6 | Inspect fine bevels; ASTC 5×5/4×4 only where 6×6 visibly breaks |
| UI, text, signage | ASTC 4×4 at the size it is read | Supersampled UI shader |
| Distant scenery, backdrop cards, skybox faces | ASTC 8×8, 512–1024 | Skybox HDRIs are a frequent size surprise |
| Lightmaps | max 1024 per atlas if the size budget needs it | Format follows the lightmap encoding (§3), don't force one |
| Reflection probe cubemaps | 128 (256 for a hero probe) | [INFERENCE: kit performance.md guideline] |

Basis: VRChat's 1K rule of thumb and "Crunch does not help in-memory size"; ASTC 6×6 as the
default and 4×4 for UI/text. The SDK raises a red error until the Android default texture format is ASTC and its Auto Fix sets
`EditorUserBuildSettings.androidBuildSubtarget = ASTC`. A texture whose PC import is
already ≤ 1024 still needs the ASTC override checked, not assumed. Bytes per format:
`vrc-udon-workflow/references/texture-decisions.md`.

The platform names in `TextureImporter.SetPlatformTextureSettings` are `"Android"` and `"iPhone"`.
Script: [port-workflow.md](port-workflow.md) step 6.

## 3. Lightmaps and reflection probes

**One bake serves both platforms.** Lightmaps are textures; the Android import re-encodes and
downsizes them. Never rebake per platform (the scene holds one set of lighting data), and keep the
GI-contributing geometry identical on both builds: an object hidden only on Android leaves its baked
shadow behind.

**Encoding is per platform and our projects ship Android/iOS at Low.** In the open workspace project
(Unity 2022.3.22f1, 2026-10-13) `PlayerSettings` reported lightmap encoding **Android = Low,
iOS = Low, Standalone = High**, and HDR cubemap encoding Android = Low. Low is
dLDR on mobile: values above 2 are clamped and gradients band. Bakery's
fix for Android banding: set Lightmap Encoding to **High Quality**, keep ASTC on, and if it still
bands set the lightmap textures' compression quality to High or None (None costs more video memory)
. On Android ASTC, High stores **ASTC HDR at 3.56 bpp**, the same size as
dLDR/RGBM. Both setters are internal; call them through reflection
([port-workflow.md](port-workflow.md) step 6). Set the HDR cubemap encoding to match so baked
reflection probes don't clip.

**Resolution.** VRChat: "keep your lightmap resolution low. Even with low lightmap resolution,
lighting can look very good". Halving the atlas size on Android with
an importer override quarters its memory with no rebake; check edges for light leaks afterwards,
because chart padding shrinks with the atlas [INFERENCE]. If leaks appear, raise the PC bake's chart
padding and rebake once for both platforms.

**Directional data.** Bakery dominant-direction / MonoSH maps ship as extra textures. Standard Lite
reads MonoSH when its *Lightmap Type* matches the bake; Lightmapped and Toon Standard
ignore directional data. Override the direction maps to half the colour-map size when the budget is
tight [INFERENCE].

**Probes.** Avatars on Android use `VRChat/Mobile` shaders, which don't read VRC Light Volumes
(Toon Standard support is an open request since 2025-05), so in a Light
Volume world Android avatars are lit by the light probes alone [INFERENCE]. Keep the probe set
complete even when Light Volumes carry the PC look. Re-bake reflection probes after every bake as
on PC (hard rule 6); Standard Lite reads them only with *Glossy Reflections* on.
