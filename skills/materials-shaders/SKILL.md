---
name: materials-shaders
description: Choosing, setting up and checking materials, textures and shaders in a VRChat Built-in RP world — finding the surface players see, swap-or-tune, shader choice, PBR set conversion, texture import (anisotropy, NPOT, HDRI skyboxes), tiling and per-renderer UV offsets, tint limits, metals and reflection probes, emission keywords, MaterialPropertyBlocks, glass, cutout, fog and text shaders, banding, and same-camera render verification. Load when texturing or restyling a surface, importing textures or PBR sets, tuning a material whose edit "does nothing", or diagnosing a surface that reads wrong (smeared, flat, black, glossy, garish, dead, blurry).
---

# Materials, textures and shaders

Scope: VRChat PC, Unity 2022.3, Built-in RP; values are for Unity Standard unless a row says otherwise.
Covered elsewhere, not repeated here:

- Texture formats, bytes per pixel, residency, mips on world-space UI, runtime-loaded images:
  `.omp/skills/vrc-udon-workflow/references/texture-decisions.md`.
- Android/iOS shaders (Standard Lite, Lightmapped), ASTC overrides, vertex colours:
  `.omp/skills/vrchat-android-worlds/references/materials-and-textures.md`.
- Emissive fixtures in a bake (light meshes, spill vs fixture glow, SSS): `.omp/skills/bakery-light-baking/SKILL.md`.
- Fog density vs far clip, skybox backdrops, z-fight separation: `.omp/skills/clip-planes/SKILL.md`.

Stages (`.omp/skills/world-pipeline/SKILL.md`): C.1 Build-out applies §1–§2 to shell finish, placed
furniture and dressing; D.1 re-judges metals, glass and emitters after the bake and probe re-bake; D.2
texture-memory changes follow texture-decisions.md and still need §4.

## 1. Decisions in order

1. **Target.** Raycast from a player position and read the hit renderer and submaterial; blockout
   boxes often sit hidden behind an imported shell whose shared submaterials (Floor / Wall / Ceil)
   are what players see. Count the material's users before editing and clone it if not all of them
   should change.
2. **Swap or tune.** A wrong asset beats every material value: wrong scan pairing, dead-looking
   foliage, a floor pattern on a tread, gloss painted into the albedo, emitters facing into a shade,
   softness baked into an HDRI. Run §2 A first; tune only an asset whose texture is right.
3. **Shader.** Built-in RP only: URP/HDRP and Shader Graph materials import magenta. Use the project's
   default prop shader (`.omp/skills/worldbuilding-assets/SKILL.md`). Anything not lightmapped
   (dynamic props, pickups, small props whose UV2 fails the audit) is lit by VRC Light Volumes and
   needs an LV-compatible shader: `Light Volume Samples/Light Volume PBR` through a `<name>_LV.mat`
   copy, or lilToon/Poiyomi for stylised assets; a Standard-shader dynamic prop is a finding
   (`.omp/skills/lightmap-allocation/SKILL.md` §1). Write or vendor a custom shader
   only for a need the default can't meet: fog that survives mirrors, fake interiors behind distant
   windows, depth-tested world text, cutout without framebuffer blend, a dither against banding (§2 F).
4. **Texture set and import.** Convert PBR sets offline into the shader's channel packing, then set
   import per §2 B before judging anything at a grazing angle. Size and format: texture-decisions.md.
5. **Mapping.** Decide where texel density lives (mesh UVs, world-projected, or material tiling) and
   keep it uniform across a surface family. Break clone repetition per renderer with a property
   block, not with material copies.
6. **Value and colour.** Put tone into the albedo texture; `_Color` only trims. Before touching
   metallic, decide whether the surface is carried by diffuse (bounce-lit) or by reflection (facing a
   bright source).
7. **Runtime state.** If Udon or a toggle changes the look through MaterialPropertyBlocks, plan block
   ownership, submeshes and keywords now (§2 E). A bake sees only the material assets.
8. **Verify** per §4, then the stage reviewer.

## 2. Trap checklist

The builder checks every row that applies to the pass; the reviewer can verify each "Rule / pass".

### A. Asset choice: swap, don't tune
| Trap | Rule / pass |
|---|---|
| Photoscan reads as a smeared swirl while an identical sibling is fine | Another scan's texture on this mesh; texture metrics all read normal. Check pairing first: raycast the bad pixels, albedo name matches the mesh's source asset; scene-wide invariant `meshTextureMismatches == 0` over every material |
| Plant looks dried/dead under every light | Alpha-weighted mean RGB (blit to a small RT, read back) must be G > R; replace R > G assets at every placement |
| Cloned treads/planks read as wallpaper or chevrons | The pattern must suit the surface (no herringbone parquet on a tread; use straight grain); then per-renderer offsets (§2 C) |
| Trim reads as wet plastic/chrome even at gloss 0.02 | Highlights are painted into the albedo: swap to a matte material. Highlights left at gloss 0.02 may be diffuse hotspots from nearby lights. Replace placeholder primitives with real silhouettes |
| Lamp reads switched off over a bright pool | Sample the emission map's mean and lit-pixel fraction (switched-off-by-design ≈ 3% lit vs ≈ 48% for a lit sibling). Dark map, or emitters facing into an opaque dish → swap to a prop proven lit; raising `_EmissionColor` only brightens the pool. Judge from standing eye height |
| Property sweeps (colour, metallic, name) find no offending pack props | Pack materials are white-tinted over a shared atlas that carries the look: render every user of the atlas and judge by eye |
| HDRI skyline soft, bokeh on lights | Shallow depth of field in the photo; no import setting fixes it: real geometry towers (emissive window grids) for a crisp skyline, HDRI as the far backdrop |

### B. Import and conversion
| Trap | Rule / pass |
|---|---|
| Authored/scripted textures smear at grazing angles | They import at aniso 1 / Bilinear. Set `anisoLevel` ≥ 8, Trilinear, mips on; sweep after every batch; compare with a stock surface before touching UVs |
| NPOT art squashed, or imported as RGB24 | Default `ToNearest` rounds each axis separately (aspect changes); NPOT + mips or `None` blocks BC compression. Use `npotScale = ToLarger`; size the quad from the source file's pixel aspect, never `Texture.width/height`; confirm the resolved platform format is compressed |
| PBR set (e.g. ambientCG) into Standard | `_MetallicGlossMap` = metallic in R, inverted roughness (255 − v) in A; GL normal (Y+), NormalMap type; mask and AO `sRGB` off, mask `alphaSource = FromInput` or the smoothness is discarded. Prefer a set whose own albedo mean sits near the target; a strong `_Color` correction erases its pattern |
| Polished stone floor turns into a black mirror | With a gloss map bound, `_GlossMapScale` (not `_Glossiness`) rules: honed stone ≈ 0.35, plaster ≈ 0.45, wood ≈ 0.50 |
| HDRI skybox blurry through big windows | A visible skybox stays at full resolution and is never reduced or lossy-compressed (user 2026-10-26: it is a big part of the world); only a fully enclosed world with no sky visible may reduce it. Imported as a cubemap, an 8192×4096 equirect keeps its full detail at 2048 per face (one 90° face); 1024 halves it. Preview many via an ffmpeg contact sheet; hide the glass before blaming import |
| Generated night panorama reads as dusk | Prompt for "deep night, moonless, no twilight", drop orange-cloud wording; darken the sky but protect lights by local contrast, not raw luminance; draw stars as ellipses widened by 1/cos(elevation), after any upscale, with an HDR boost to survive BC6H |

### C. Mapping and tiling
| Trap | Rule / pass |
|---|---|
| Scaled primitives on one material show different texture periods | Set `_MainTex_ST` per renderer from world bounds (`bounds.size / period`) via MaterialPropertyBlock; `bounds.size / tiling` constant across the family; check at a grazing angle |
| Clones show the same patch | Random per-renderer `_MainTex_ST` offsets via property block (Standard routes normal and occlusion through it; UV2 unaffected); assert distinct offsets == renderer count |
| Uneven density across floors and walls | One mesh with world-projected UVs (uv = world / repeat, material tiling 1,1) plus UV2; panelled walls fit one repeat to the wall height (`scale.y = 1/height`-style, `offset.y = −minY/height`) |
| Matching a neighbour's density | Check whether its density lives in mesh UVs or in `mainTextureScale` (ProBuilder carries 1 UV unit per metre) before authoring UVs |

### D. Maps, scalars and values (Standard)
| Trap | Rule / pass |
|---|---|
| Smoothness, metallic or emission edit leaves the frame unchanged | A bound map overrides the scalar: `_MetallicGlossMap` (A = smoothness, R = metalness), albedo-alpha smoothness, an `_EmissionMap` mask black over the UVs; or a stale `_METALLICGLOSSMAP` / `_SPECGLOSSMAP` keyword survived `CopyPropertiesFromMaterial`. Inspect maps and keywords first. Zero shine also needs `_SpecularHighlights 0` + `_SPECULARHIGHLIGHTS_OFF` and `_GlossyReflections 0` + `_GLOSSYREFLECTIONS_OFF` |
| Repurposed pack material keeps its old design or gloss | Atlas roughness/normal maps carry the old artwork. Clear `_SpecGlossMap`, `_MetallicGlossMap`, `_BumpMap`, `_OcclusionMap`, `_Detail*` and their keywords; list all texture properties, not `mainTexture` |
| Grey tint does not fix a garish texture | `_Color` multiplies all channels equally, so it cannot desaturate: swap the texture or desaturate it into a new asset; score p95 saturation, not the mean |
| Dark tone erases grain and relief | Dominant `_Color` channel ≥ ~0.25; darkness goes into the albedo; untextured darks need ~⅔ the value of textured ones |
| One class in a shared atlas needs a new colour | HSV saturation mask, remap the masked mean to the target albedo's mean; sample the file, not an unbaked render |
| Metal renders as a flat slab before the bake | Unbaked, metals have nothing to reflect. Until the bake: albedo ~0.40, metallic ~0.55, smoothness ~0.45, or contrasting parts; revisit after |
| Baked scene: metal black in a sealed dark room; dark prop black against a bright window | Once baked, metals take all brightness from the reflection probe: dark room → metallic ~0.3, saturated warm albedo, smoothness ~0.6; bright probe → metallic is the fix. Diffuse ≈ albedo × (1 − metallic): change albedo and metallic one at a time |
| New prop reads cold/blue beside an identical baked one | `lightmapIndex == -1` (added after the bake, skybox ambient): bake it, don't re-tint |
| Big near-white surface makes a sealed room bake blown | Bounce gain ≈ 1/(1 − albedo): lower the albedo of the big bright surface, not the lights |

### E. Emission, property blocks, colour maths
| Trap | Rule / pass |
|---|---|
| Property-block emission applies, reads back, never renders | `_EMISSION` enabled on the asset and `globalIlluminationFlags = None` (Standard's GUI turns the keyword off again under `EmissiveIsBlack`); `BakedEmissive` only for bake emitters; an emission map attenuates, so calibrate on the render |
| A "fixtures off" bake still glows | The bake reads material-asset emission, never property blocks: edit the assets, restore afterwards |
| Two passes or a multi-material renderer get the wrong result | `SetPropertyBlock` replaces the whole block and covers every submesh; one block carries all passes' properties, or use the `submeshIndex` overload. A wrong-direction result is the tell |
| Restore with `SetPropertyBlock(null)` | That clears blocks other systems own (e.g. pen colours): test `HasPropertyBlock()` in the base state, restore a captured block. Dropping a renderer from a toggle list leaves its ON block behind |
| Brightness fit overshoots or undershoots | In Linear space `SetColor` applies sRGB → linear: L ∝ k^2.2 above the 0.04045 knee, linear below; `GetVector` reads back linear. Albedo may exceed 1; a solve returning its own ceiling failed |
| Diagnostic shader (e.g. magenta `Unlit/Color`) shipped | A `.mat` stores its shader as GUID/fileID, so grepping for the name finds nothing: sweep `shader.name` through the AssetDatabase; restore from the commit before keying; reimport with `ImportAssetOptions.ForceUpdate` |

### F. Special shaders and surfaces
| Trap | Rule / pass |
|---|---|
| World behind glass blurry, glass has no reflections | Mochie Glass: any `_Roughness` > 0 enables a blurred grab pass and a blurrier reflection mip. `_Roughness = 0` on see-through panes; frost via a roughness map only where wanted; read the glass material before the world outside |
| Glass panes lightmapped | `receiveGI = LightProbes` before baking |
| Cutout foliage burns white in front of a bright sky | The surface-shader `alphatest:_Cutoff` pragma leaves a framebuffer blend. Drop it, declare `_Cutoff`, `clip(c.a - _Cutoff)`, `o.Alpha = 1`; test identical quads against a wall and against the sky |
| Cutout leaves shimmer in VR at MSAA 4x | MSAA alone does nothing for clip; A2C alone ~8 %. Alpha to coverage plus, ramped in only past mip 1 (`saturate(lod − 1)` from `ddx/ddy(uv)`), a +0.35 mip bias via `tex2Dgrad` and a −0.05 A2C cutoff drop: ~45–70 % less flicker at 6–40 m, coverage and near leaves unchanged. Larger values clump or overfill sprays. Measure on a 0.25 px/frame yaw against a 4× supersampled reference |
| Fog wall at the screen edge; mirrors unfogged | Built-in fog is view-space, and VRChat mirrors render without Unity fog state. Radial ExpSq fog from the shader's own uniforms, applied unconditionally, one formula in every fogging shader, re-synced with scene fog |
| World-space TextMesh shows through walls | `GUI/Text Shader` is `ZTest Always`: copy it with `ZTest LEqual`, bind the font atlas; clear the label's static flags |
| Contour bands on big dark surfaces | 8-bit quantization, not the bake: count distinct values in 8-bit vs float renders of one camera. Fix with a static multiplicative, one-sided screen-space dither (~0.06, interleaved-gradient noise) on a head-locked quad that also carries any dimmer |
| Distant building windows flat and dead | Built-in RP interior-mapping shader (per-pixel ray vs room planes on a grid), emissive interior term; never for rooms players can reach |
| First-pass emissive flames cartoonish | Gas fire pit: ~30 blades 45–145 mm tall, emission ≈ (1.85, 0.52, 0.09) deep orange, glow card sunk ~65 mm below the stones, dark burner body |

## 3. Diagnose in this order

For "looks wrong" or "my edit does nothing", cheapest exonerating check first:

1. Is the edited renderer the visible one? Raycast (§1.1).
2. Did the frame change at all? A zero-pixel diff means the edit missed: wrong map, keyword, block
   owner, submesh or material copy.
3. Lighting state: `lightmapIndex`, a leftover realtime helper light (it flattens every lightmapped
   surface), what the reflection probe captured (only `ReflectionProbeStatic` renderers are in it).
4. The asset: pairing, albedo statistics, pattern, emission map (§2 A).
5. Import settings against a stock surface that looks right (§2 B).
6. Maps and keywords, then scalars (§2 D).
7. UVs and geometry last.

## 4. Verify

- **Same camera, before and after.** Capture with the kit's `WorldCapture.Shoot` and an identical
  shots JSON (`.omp/docs/unity-tools.md`). Poses: standing eye height from where players stand, a
  grazing angle along each changed floor or wall, and the far side of the room. Never judge from the
  Inspector, a swatch or top-down.
- Judge albedo and hue once under neutral light, then under the scene's own lighting. Delete helper
  lights and every `__*__` object before judging lighting or committing.
- Metals, glass and emitters: judge again after the bake and the reflection-probe re-bake.
- Numbers locate defects; renders prove fixes. Quote a zero-defect result with its positive control
  (same poses and threshold against a known-failing state), and try an ad-hoc metric on a known-good
  sibling first: if it condemns that too, the metric is wrong.
- Read-only sweeps after a batch: no diagnostic shaders by `shader.name`; import settings (aniso,
  Trilinear, mips, compressed; `WorldAudit.Run` flags uncompressed scene textures); mesh/texture
  pairing; metallic > 0.6 with low albedo; `HasPropertyBlock()` owners; `_EMISSION` and GI flags on
  every emitter.
- Then the stage reviewer with the before/after pairs and the §2 rows applied: `dressing-reviewer`
  in C.1, `final-reviewer` in D.1/D.2.
- A new trap becomes a knowledge note per `.omp/knowledge/README.md`, and a row here.
