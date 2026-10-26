# Reception and density

How each renderer class receives light, how many texels it gets, and how the atlas is split.
Modes: **L** lightmapped, **P** probe/Light-Volume-lit but still casting, **D** dynamic (see SKILL.md §1).

## 1. Reception per class

### Defaults and how a world changes them

- **Nothing that never moves is probe-lit, except the classes below** (user rule; the lighting
  standard lives in the bakery-light-baking skill). Each P row is a named exception, not a shortcut.
- **Light Volumes light small props only:** about ≤ 0.4 m bounds, plus loose soft decor. Furniture,
  fixture bodies, lamps, rugs, large plants and pots and statues stay L on their original material.
- A world overrides a row in its `WORLD.md` Decisions log with the user's words, e.g. "LV threshold
  0.6 m in this world" or "no Light Volumes: small decor lightmapped with Blender UV2".

### Class table

| Class | Mode | Settings | Why / traps |
|---|---|---|---|
| Shell: walls, floors, ceilings, stairs, built-ins | L | hero group per area; Scale In Lightmap 1 (2 on hero surfaces near seats) | the surfaces players read light from; equal density across a visible join |
| Hidden exterior envelope, wall backs, roof undersides nobody sees | L at Scale In Lightmap 0.1, or 0, or `ShadowsOnly` | 0 = occluder only: still renders, still casts, gets no chart and needs probes; `ShadowsOnly` for geometry that must not render | one hidden envelope took 68 % of an atlas and starved a door to ~9 texels |
| Large furniture > ~0.4 m (sofas, beds, tables, cabinets, wardrobes, lamp bodies, rugs, big plants and pots, statues, toilets, tubs, vanities) | L | valid UV2 passing the audit; Scale In Lightmap so the main face's short side ≥ 8 texels (cushion-heavy sofas 3–4, toilets up to 16) | fragmented auto UV2 on these gets re-unwrapped (uv2-quality.md §2); probes are not the fix for a big piece |
| Bedding that is part of a bed mesh | L with the bed | re-unwrap the bed: one bed had 7,600 of 8,254 UV2 triangles degenerate | loose throws and pillows on it are the next row |
| Soft or organic small pieces: pillows, cushions, throws, folded linen (≤ ~0.6 m), small sculptures and figurines (≤ ~0.4 m) | L if the UV2 passes the audit; P if it fails (expected for auto-unwrapped soft pieces) | P: `ContributeGI` on, `receiveGI = LightProbes`, `BlendProbes`, LV-aware material copy in LV worlds, no group selector, storage row removed | they keep their contact shadow in the bake. One pillow had 104 charts, 94 of them under 4 texels. The user's rule: small props go to light volumes only when their lightmap is broken |
| Small hard decor ≤ ~0.4 m: bottles, taps, levers, soap, fruit, souvenirs, books on shelves, small towels | L if the UV2 passes and the short side reaches 8 texels; else P (LV in LV worlds) | as above | thin hose and holder charts of ~37 texels baked striped. The user's 2026-10-22 rule: small props with complicated UVs go to light volumes |
| Tiny parts (middle bounds < ~0.12 m) | P | as above | no margin or scale rescues a 1–2 texel chart |
| Flush wall fittings < ~20 cm | P, seated 0.5 mm proud | probe-lit plates can read 0.6–2.7× the wall; tint by measurement | a lightmapped switch plate got 4 × 3 texels; a removed one leaves its baked shadow |
| Glass, glazing, transparent panes, shower screens | P | `receiveGI = LightProbes` only; leave `ContributeGI` as the world has it; `ReflectionProbeStatic` off | 0.02–0.03 m panes: a 60 m rail panel claimed ~1000 texels of a 2048 atlas; edge charts sit a hair from face charts and gutter-bleed onto what players look through. 129 panes moved freed ~32,000 m² of atlas demand |
| Hero trees (cutout leaf cards + bark) | L | hand-built Lightmap UV in the FBX (lowpoly-tree-generation skill), bark weighted well above leaves, leaf shader tagged `RenderType = TransparentCutout` | area-weighted unwraps give bark ~3 % of the UV2, so limbs bake one flat colour unlike the trunk |
| Scatter plants, shrubs, small potted plants | P | no selector | scatter and LOD props on probes took one 2,626-renderer scene to 3 atlases |
| Grass and ground cards | L, or a shader that samples the ground lightmap at the blade root | — | probe-lit cards stay sunlit inside baked tree shadows |
| `BakeryLightMesh` emitters | never L | no selector, no storage row; `lightmapIndex -1` is correct | Bakery hard-skips them; split a small emitter child from a lightmapped body |
| Emissive glow strips, LED nosings | as their emitter design; id −1 rows are expected | — | count them as "unbound by design" in checks |
| SSS shades and translucent fabric | L | own `computeSSS` group, closed volume with thickness, shadows On, Scale In Lightmap ~6, emission ~0 | SSS is per group and needs a casting volume |
| Pickups, Udon-moved objects, doors that swing, animated parts | D | `BlendProbes`, probe coverage where they go; LV material in LV worlds | nothing that moves gets a baked shadow; a never-moving one can get a ShadowsOnly proxy |
| Ambient-motion decor (curtains, hanging lanterns) | L | sway by vertex offset in the shader, phase from vertex colour or a spare UV (not UV2), padded bounds | moving the Transform makes it D and it stops matching its neighbours |
| Mirrors, video and runtime screens | not `ContributeGI`, not L | — | a screen bakes its placeholder as a coloured area light; a mirror loops Progressive forever |
| Far scenery, skyline, backdrop cards | L in one small shared group at 1–5 texels/m, or P; outside the probe hull probe usage Off | — | never let far content share a hero group |
| Terrain tiles | L, every tile in a group | hero tiles: own group **and** a mesh copy with UV2 stretched to fill 0–1 | ungrouped terrain tiles each grab an atlas (12 tiles made 11 of 17 maps); a tile on its 1/10 slice of a global unwrap stays ~1.4 texels/m |
| LOD levels | L per level, or P | Bakery: one group per LOD level with `sceneLodLevel` set; discount LOD1/LOD2 scale (~0.35 / 0.2) or share LOD0's chart (`BakerySharedLODUV`); GLIM: hand-authored LODs bake LOD0 only | Bakery silently skips LOD renderers whose group has `sceneLodLevel = -1`; LOD1 is what players see beyond ~3 m on many props |
| Merged / combined meshes | bake the originals | merged result reuses each source's UV2 and scale-offset; a mesh baked merged needs a fresh unwrap and its own scale | a defect that appears only merged means the merge broke UV2 or scale-offset |
| Pack furniture with no UV2 | P until UV2 exists, then L | `ContributeGI` + `LightProbes` + shadows On | casts contact shadows without atlas space |

## 2. Density targets

Effective texels per metre on the renderer (formula in §3). Base resolution 20 texels/unit is the
usual final preset; Scale In Lightmap and group resolution move each class to its target.

| Surface class | Target texels/m | Notes |
|---|---|---|
| Hero interior shell near seats and beds | 20–40 | 20 is not proof of starvation; measure and render first |
| Other interior shell, corridors | 12–25 | |
| Furniture players sit or lie on | 30–60 | garden sofas went from 2.4 (black pillows) to 24.5–27.8 at Scale In Lightmap 4 |
| Small lightmapped decor (no-LV worlds) | ≥ 8 texels across the short side | usually 60–160 texels/m; a static plush at Scale In Lightmap 8 got ~56² texels |
| Tree bark | thinnest visible limb ≥ 2 texels around, trunk ≥ 8 | set in the tree's UV, Scale In Lightmap 1 |
| Exterior play area, garden ground | 10–30 | ~4 texels/m average (p10 1.6) read as blurry shadows |
| Ground where contact shadows matter | ≥ 10 | at ~1 texel/m nothing casts a readable ground shadow |
| Background terrain, far facades | 1–5 | equal density on both sides of any boundary players see |
| Hidden backs | Scale In Lightmap 0.1 or 0 | |

## 3. Maths

```
metresPerUV  = sqrt(worldArea / uv2Area)                 // world area includes lossyScale
T_pre        = lightmapResolution × scaleInLightmap × metresPerUV    // texels per UV unit, estimate
T_post       = atlasSize × sqrt(so.x × so.y)              // so = lightmapScaleOffset after the bake
texelsPerM   = T / metresPerUV
triTexels²   = uv2TriArea × T²
chartTexels  = sqrt(chartUv2Area) × T
chartShare   = so.x × so.y                                // fraction of the atlas the renderer's 0–1 rect covers
usedTexels   = uv2Area × so.x × so.y × atlasW × atlasH
gapTexels    = minGapBetweenChartsInUV × T
```

- Share grows with `scaleInLightmap²`, so trimming a hog from 2 to 1 frees three quarters of its rect.
- `uv2Area` is the UV2 fill. Importer UV2 at fill 0.10 wastes 90 % of the rect; Manual margin
  ~0.4 (uv2-quality.md §1).
- Pre-bake values are estimates. A fixed-resolution Bakery group that is overfull scales everyone
  down, so the post-bake value is the truth.
- Smallest scale that still holds a gutter: `needed = (padding + 2) / (res × metresPerUV × minGapUV)`,
  clamped to [1, current]. One scene went from 19.17 to 13.77 Mtexel this way with the worst gutter
  still 5 texels.
- A UV-space share gain is not a texel gain when total fill changes: normalise by
  √(fill_after / fill_before).

## 4. Groups, padding and memory

- **Few explicit groups.**
  - Every L renderer has a `BakeryLightmapGroupSelector` on itself or an ancestor's renderer.
  - `autoAtlas = false`; count ungrouped renderers before every bake and expect 0.
  - An ungrouped static object falls into an implicit group that can resolve to 16×16. It then bakes
    flat or black with a valid-looking index; the tell is scale-offset `(1,1,0,0)`.
- **Hero areas:** a fixed-resolution group per area (2048 typical, 4096 for a large garden). Check
  headroom before piling more area into it; a fixed group just thins everyone.
- **Background:** terrain, far scenery and the exterior shell go into one small shared fixed group
  (512–1024).
- **Probe-lit renderers carry no selector.** A group whose members are all probe-lit still bakes and
  binds a full empty atlas.
- **Selectors live on rebuild-stable roots.** A builder that destroys and recreates its root deletes
  them. A blunt "assign all" script wipes hand-made hero, LOD and SSS groups unless it rebuilds those
  refinements last.
- **Padding:** Bakery texel padding (project settings; default packer 3, xatlas 1) at 8 for hero
  groups. Unity/Progressive `lightmapPadding` in texels. ProBuilder's pack margin is in UV space, so
  measure gaps in texels.
- **Memory:** BC6H stores 1 byte per texel: a 2048² map ≈ 4 MiB, 4096² ≈ 16 MiB (+⅓ with mips).
  Directional maps add more. Count the expected atlases before baking. One scene went from 17 maps to
  7 by fixing hogs and grouping terrain. Ask before adding a 4096 map for one area.
- **GLIM:** one lightmap for the scene unless you add GLIM group selectors. It computes Scale In
  Lightmap differently, so re-measure density after switching lightmappers.
