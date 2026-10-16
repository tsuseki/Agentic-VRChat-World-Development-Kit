---
name: materials-shaders
description: Choosing, setting up and checking materials, textures and shaders in a VRChat Built-in RP world — finding the surface players see, swap-or-tune, shader choice, PBR set conversion, texture import (anisotropy, NPOT, HDRI skyboxes), tiling and per-renderer UV offsets, tint limits, metals and reflection probes, emission keywords, MaterialPropertyBlocks, glass, cutout, fog and text shaders, banding, and same-camera render verification. Load when texturing or restyling a surface, importing textures or PBR sets, tuning a material whose edit "does nothing", or diagnosing a surface that reads wrong (smeared, flat, black, glossy, garish, dead, blurry).
---

# Materials, textures and shaders

Scope: VRChat PC, Unity 2022.3, Built-in RP; values are for Unity Standard unless a row says otherwise.
This skill is the procedure; the linked notes in `.omp/knowledge/notes/` are the evidence and hold the
measured numbers. Open a note when its row applies. Covered elsewhere, not repeated here:

- Texture formats, bytes per pixel, residency, mips on world-space UI, runtime-loaded images:
  `.omp/skills/vrc-udon-workflow/references/texture-decisions.md`.
- Android/iOS shaders (Standard Lite, Lightmapped), ASTC overrides, vertex colours:
  `.omp/skills/vrchat-android-worlds/references/materials-and-textures.md`.
- Emissive fixtures in a bake (light meshes, spill vs fixture glow, SSS): `.omp/skills/bakery-light-baking/SKILL.md`.
- Fog density vs far clip, skybox backdrops, z-fight separation: `.omp/skills/clip-planes/SKILL.md`.

Stages (`.omp/skills/world-pipeline/SKILL.md`): C.1 Build-out applies §1–§2 to shell finish, furniture
swap and dressing; D.1 re-judges metals, glass and emitters after the bake and probe re-bake; D.2
texture-memory changes follow texture-decisions.md and still need §4.

## 1. Decisions in order

1. **Target.** Raycast from a player position to find the renderer and submaterial actually seen;
   blockout boxes often sit hidden behind an imported shell. Count the material's users before editing
   and clone it if not all of them should change.
   [find-the-visible-surface-by-raycast-before-restyling](../../knowledge/notes/find-the-visible-surface-by-raycast-before-restyling.md),
   [recolour-shared-atlas-by-saturation-mask](../../knowledge/notes/recolour-shared-atlas-by-saturation-mask.md)
2. **Swap or tune.** A wrong asset beats every material value: wrong scan pairing, dead-looking
   foliage, a floor pattern on a tread, gloss painted into the albedo, emitters facing into a shade,
   softness baked into an HDRI. Run §2 A first; tune only an asset whose texture is right.
3. **Shader.** Built-in RP only: URP/HDRP and Shader Graph materials import magenta. Use the project's
   default prop shader (`.omp/skills/worldbuilding-assets/SKILL.md`). Write or vendor a custom shader
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
Note links are relative to this file.

### A. Asset choice: swap, don't tune
| Trap | Rule / pass | Note |
|---|---|---|
| Photoscan reads as a smeared swirl while an identical sibling is fine | Check mesh/texture pairing first: albedo name matches the mesh's source asset; scene-wide invariant `meshTextureMismatches == 0` over every material | [check-photoscan-mesh-texture-pairing-first](../../knowledge/notes/check-photoscan-mesh-texture-pairing-first.md) |
| Plant looks dried/dead under every light | Alpha-weighted mean RGB must be G > R; replace R > G assets at every placement | [reject-red-dominant-foliage-textures](../../knowledge/notes/reject-red-dominant-foliage-textures.md) |
| Cloned treads/planks read as wallpaper or chevrons | The pattern must suit the surface (no parquet on a tread); then per-renderer offsets (§2 C) | [cloned-pieces-with-identical-uvs-read-as-a-pattern](../../knowledge/notes/cloned-pieces-with-identical-uvs-read-as-a-pattern.md) |
| Trim reads as wet plastic/chrome even at gloss 0.02 | Highlights are painted into the albedo: swap to a matte material. Replace placeholder primitives with real silhouettes | [trim-gloss-baked-into-albedo-reads-as-plastic](../../knowledge/notes/trim-gloss-baked-into-albedo-reads-as-plastic.md) |
| Lamp reads switched off over a bright pool | Sample the emission map's mean and lit-pixel fraction; dark map or emitters hidden in the dish → swap to a prop proven lit | [lamp-emissive-faces-hidden-reads-switched-off](../../knowledge/notes/lamp-emissive-faces-hidden-reads-switched-off.md) |
| Property sweeps (colour, metallic, name) find no offending pack props | White-tinted shared atlases carry the look: render every user of the atlas and judge by eye | [audit-pack-prop-appearance-by-render](../../knowledge/notes/audit-pack-prop-appearance-by-render.md) |
| HDRI skyline soft, bokeh on lights | No import setting fixes it: real geometry towers for a crisp skyline, HDRI as the far backdrop | [hdri-skybox-import-resolution-and-softness](../../knowledge/notes/hdri-skybox-import-resolution-and-softness.md) |

### B. Import and conversion
| Trap | Rule / pass | Note |
|---|---|---|
| Authored/scripted textures smear at grazing angles | `anisoLevel` ≥ 8, Trilinear, mips on; sweep after every batch; compare with a stock surface before touching UVs | [authored-textures-need-aniso-8-and-trilinear](../../knowledge/notes/authored-textures-need-aniso-8-and-trilinear.md) |
| NPOT art squashed, or imported as RGB24 | `npotScale = ToLarger`; size the quad from the source file's aspect, never `Texture.width/height`; confirm the resolved platform format is compressed | [npot-textures-lose-aspect-and-compression](../../knowledge/notes/npot-textures-lose-aspect-and-compression.md), [size-pictures-from-source-file-not-imported-texture](../../knowledge/notes/size-pictures-from-source-file-not-imported-texture.md) |
| PBR set (e.g. ambientCG) into Standard | Mask = metallic in R, inverted roughness in A; GL normal (Y+), NormalMap type; mask and AO `sRGB` off, mask `alphaSource = FromInput` | [ambientcg-to-standard-material-conversion](../../knowledge/notes/ambientcg-to-standard-material-conversion.md) |
| Polished stone floor turns into a black mirror | With a gloss map bound, `_GlossMapScale` rules: honed stone ≈ 0.35, plaster ≈ 0.45, wood ≈ 0.50 | same note |
| HDRI skybox blurry through big windows | 8K equirect → 2048 cubemap face; preview many via an ffmpeg contact sheet; hide the glass before blaming import | [hdri-skybox-import-resolution-and-softness](../../knowledge/notes/hdri-skybox-import-resolution-and-softness.md) |
| Generated night panorama reads as dusk | Prompt for true night; protect lights by local contrast; stars as ellipses, drawn after upscaling | [night-sky-grading-for-generated-panoramas](../../knowledge/notes/night-sky-grading-for-generated-panoramas.md) |

### C. Mapping and tiling
| Trap | Rule / pass | Note |
|---|---|---|
| Scaled primitives on one material show different texture periods | `_MainTex_ST` per renderer from world bounds via MaterialPropertyBlock; `bounds.size / tiling` constant across the family | [scaled-primitive-texture-period-mpb](../../knowledge/notes/scaled-primitive-texture-period-mpb.md) |
| Clones show the same patch | Random per-renderer `_MainTex_ST` offsets (normal and occlusion follow); assert distinct offsets == renderer count | [cloned-pieces-with-identical-uvs-read-as-a-pattern](../../knowledge/notes/cloned-pieces-with-identical-uvs-read-as-a-pattern.md) |
| Uneven density across floors and walls | One mesh with world-projected UVs (uv = world / repeat) plus UV2; panelled walls fit one repeat to the wall height | [world-projected-uvs-and-fitting-repeats-to-wall-height](../../knowledge/notes/world-projected-uvs-and-fitting-repeats-to-wall-height.md) |
| Matching a neighbour's density | Check whether its density lives in mesh UVs or in `mainTextureScale` before authoring UVs | [uv-density-may-live-in-the-material](../../knowledge/notes/uv-density-may-live-in-the-material.md) |

### D. Maps, scalars and values (Standard)
| Trap | Rule / pass | Note |
|---|---|---|
| Smoothness, metallic or emission edit leaves the frame unchanged | A bound map overrides the scalar (`_MetallicGlossMap`, albedo-alpha smoothness, emission mask) or a stale keyword survived `CopyPropertiesFromMaterial`. Inspect maps and keywords first; zero smoothness also needs both specular paths off (float and keyword each) | [standard-shader-maps-override-scalars](../../knowledge/notes/standard-shader-maps-override-scalars.md) |
| Repurposed pack material keeps its old design or gloss | Clear every map slot and its keyword; list all texture properties, not `mainTexture` | [repurposing-pack-materials-clear-every-map](../../knowledge/notes/repurposing-pack-materials-clear-every-map.md) |
| Grey tint does not fix a garish texture | A multiply cannot desaturate: swap or desaturate the texture; score p95 saturation, not the mean | [color-tint-cannot-desaturate](../../knowledge/notes/color-tint-cannot-desaturate.md) |
| Dark tone erases grain and relief | Dominant `_Color` channel ≥ ~0.25; darkness goes into the albedo; untextured darks need ~⅔ the value of textured ones | [dark-material-tint-erases-texture-detail](../../knowledge/notes/dark-material-tint-erases-texture-detail.md), [trim-gloss-baked-into-albedo-reads-as-plastic](../../knowledge/notes/trim-gloss-baked-into-albedo-reads-as-plastic.md) |
| One class in a shared atlas needs a new colour | HSV saturation-mask remap of the atlas; sample the file, not an unbaked render | [recolour-shared-atlas-by-saturation-mask](../../knowledge/notes/recolour-shared-atlas-by-saturation-mask.md) |
| Metal renders as a flat slab before the bake | Until the bake: albedo ~0.40, metallic ~0.55, smoothness ~0.45, or contrasting parts; revisit after | [metallic-materials-cannot-be-judged-before-a-bake](../../knowledge/notes/metallic-materials-cannot-be-judged-before-a-bake.md) |
| Metal black in a sealed dark room; dark prop black against a bright window | Ask what the reflection probe sees: dark room → metallic ~0.3, warm albedo, smoothness ~0.6; bright probe → metallic is the fix. Change albedo and metallic one at a time | [metallic-depends-on-what-the-reflection-probe-sees](../../knowledge/notes/metallic-depends-on-what-the-reflection-probe-sees.md) |
| New prop reads cold/blue beside an identical baked one | `lightmapIndex == -1`: bake it, don't re-tint | [unbaked-props-read-blue](../../knowledge/notes/unbaked-props-read-blue.md) |
| Big near-white surface makes a sealed room bake blown | Lower the albedo of the big bright surface, not the lights | [white-albedo-ceilings-make-sealed-rooms-bake-hot](../../knowledge/notes/white-albedo-ceilings-make-sealed-rooms-bake-hot.md) |

### E. Emission, property blocks, colour maths
| Trap | Rule / pass | Note |
|---|---|---|
| Property-block emission applies, reads back, never renders | `_EMISSION` enabled on the asset and `globalIlluminationFlags = None` (Standard's GUI turns the keyword off under `EmissiveIsBlack`); `BakedEmissive` only for bake emitters; an emission map attenuates | [emission-keyword-off-ignores-property-block](../../knowledge/notes/emission-keyword-off-ignores-property-block.md) |
| A "fixtures off" bake still glows | The bake reads material-asset emission, never property blocks: edit the assets, restore afterwards | [bakery-bakes-material-emission-not-property-blocks](../../knowledge/notes/bakery-bakes-material-emission-not-property-blocks.md) |
| Two passes or a multi-material renderer get the wrong result | `SetPropertyBlock` replaces the whole block and covers every submesh; one block carries all passes' properties, or use the `submeshIndex` overload | [setpropertyblock-replaces-not-merges](../../knowledge/notes/setpropertyblock-replaces-not-merges.md) |
| Restore with `SetPropertyBlock(null)` | That clears blocks other systems own: test `HasPropertyBlock()` in the base state, restore a captured block | [dont-clobber-existing-material-property-blocks](../../knowledge/notes/dont-clobber-existing-material-property-blocks.md), [removing-a-renderer-from-a-toggle-list-leaks-state](../../knowledge/notes/removing-a-renderer-from-a-toggle-list-leaks-state.md) |
| Brightness fit overshoots or undershoots | `SetColor` applies sRGB → linear: pick the regime by the 0.04045 knee; albedo may exceed 1; a solve returning its own ceiling failed | [setcolor-gamma-conversion-breaks-linear-fits](../../knowledge/notes/setcolor-gamma-conversion-breaks-linear-fits.md) |
| Diagnostic shader (e.g. magenta `Unlit/Color`) shipped | A `.mat` stores its shader as GUID/fileID: sweep `shader.name` through the AssetDatabase; restore from the commit before keying; reimport with `ForceUpdate` | [mat-files-reference-shaders-by-guid](../../knowledge/notes/mat-files-reference-shaders-by-guid.md) |

### F. Special shaders and surfaces
| Trap | Rule / pass | Note |
|---|---|---|
| World behind glass blurry, glass has no reflections | Mochie Glass: `_Roughness = 0` on see-through panes; read the glass material before the world outside | [mochie-glass-roughness-enables-screen-blur](../../knowledge/notes/mochie-glass-roughness-enables-screen-blur.md) |
| Glass panes lightmapped | `receiveGI = LightProbes` before baking | [glass-should-be-probe-lit-not-lightmapped](../../knowledge/notes/glass-should-be-probe-lit-not-lightmapped.md) |
| Cutout foliage burns white in front of a bright sky | Drop the `alphatest:_Cutoff` pragma, `clip()` explicitly; test identical quads against a wall and against the sky | [alphatest-pragma-blends-cutout-against-background](../../knowledge/notes/alphatest-pragma-blends-cutout-against-background.md) |
| Fog wall at the screen edge; mirrors unfogged | Radial ExpSq fog from the shader's own uniforms, applied unconditionally, one formula in every fogging shader, re-synced with scene fog | [fog-must-be-radial-and-shader-driven-for-mirrors](../../knowledge/notes/fog-must-be-radial-and-shader-driven-for-mirrors.md) |
| World-space TextMesh shows through walls | Copy `GUI/Text Shader` with `ZTest LEqual`; clear the label's static flags | [textmesh-default-font-material-draws-through-walls](../../knowledge/notes/textmesh-default-font-material-draws-through-walls.md) |
| Contour bands on big dark surfaces | 8-bit quantization, not the bake: count distinct values in 8-bit vs float renders; static multiplicative screen-space dither (~0.06) on a head-locked quad that also carries any dimmer | [dark-gradient-banding-is-8bit-quantization](../../knowledge/notes/dark-gradient-banding-is-8bit-quantization.md) |
| Distant building windows flat and dead | Built-in RP interior-mapping shader, emissive interior term; never for rooms players can reach | [interior-mapping-fake-rooms-behind-windows](../../knowledge/notes/interior-mapping-fake-rooms-behind-windows.md) |
| First-pass emissive flames cartoonish | Small (45–145 mm), deep orange, glow card sunk out of sight, dark burner | [gas-fire-pit-emissive-flame-dimensions](../../knowledge/notes/gas-fire-pit-emissive-flame-dimensions.md) |

## 3. Diagnose in this order

For "looks wrong" or "my edit does nothing", cheapest exonerating check first:

1. Is the edited renderer the visible one? Raycast (§1.1).
2. Did the frame change at all? A zero-pixel diff means the edit missed: wrong map, keyword, block
   owner, submesh or material copy.
   [unchanged-metric-means-wrong-target](../../knowledge/notes/unchanged-metric-means-wrong-target.md)
3. Lighting state: `lightmapIndex`, a leftover realtime helper light, what the reflection probe captured.
   [realtime-preview-lights-wash-out-baked-scenes](../../knowledge/notes/realtime-preview-lights-wash-out-baked-scenes.md),
   [reflection-probes-need-reflectionprobestatic-flag](../../knowledge/notes/reflection-probes-need-reflectionprobestatic-flag.md)
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
- Numbers locate defects; renders prove fixes. Quote a zero-defect result with its positive control,
  and try an ad-hoc metric on a known-good sibling first.
  [metrics-that-cannot-see-their-defect](../../knowledge/notes/metrics-that-cannot-see-their-defect.md),
  [zero-defect-result-needs-positive-control](../../knowledge/notes/zero-defect-result-needs-positive-control.md),
  [validate-ad-hoc-metrics-on-a-known-good-sibling](../../knowledge/notes/validate-ad-hoc-metrics-on-a-known-good-sibling.md)
- Read-only sweeps after a batch: no diagnostic shaders by `shader.name`; import settings (aniso,
  Trilinear, mips, compressed; `WorldAudit.Run` flags uncompressed scene textures); mesh/texture
  pairing; metallic > 0.6 with low albedo; `HasPropertyBlock()` owners; `_EMISSION` and GI flags on
  every emitter.
- Then the stage reviewer with the before/after pairs and the §2 rows applied: `dressing-reviewer`
  in C.1, `final-reviewer` in D.1/D.2.
- A new trap becomes a note per `.omp/knowledge/README.md`, and a row here.
