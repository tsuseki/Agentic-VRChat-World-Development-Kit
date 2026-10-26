# Lightmap allocation lessons

Which renderers get lightmap texels, how many, and how to prove the allocation before and after a bake.
Distilled from the knowledge notes for this topic; grep .omp/knowledge/notes/ for the full evidence.

## Reception: lightmap, probes or dynamic

- **Before baking, sweep glass, window and glazing renderers to `receiveGI = LightProbes` and leave ContributeGI as it is** — 0.02–0.03 m panes demanded huge atlas area (one 60 m rail panel ~1000 texels of a 2048 atlas) and gutter-bleed lands on the surface players look through.
- **When a small soft or organic piece fails the UV2 audit (pillows, cushions, throws up to about 0.6 m; small sculptures up to about 0.4 m), set ContributeGI + `receiveGI = LightProbes` (a Light Volume material in LV worlds). Re-unwrap failing large furniture instead. Never raise Scale In Lightmap to rescue a fragmented UV2** — auto unwraps cut these pieces into charts of a few texels (one pillow had 94 of its 104 charts under 4 texels; about 800 of 2,379 small renderers), and they bake as torn, faceted dark triangles. Light Volumes are for small props only, and only when their lightmap is broken.
- **Keep tiny pieces (middle bounds under ~0.12 m) and fragmented small trim off the lightmap with ContributeGI kept, and never raise `scaleInLightmap` to clear their overlap warnings** — no pack margin rescues a 2-texel chart, and the blunt raise more than doubled atlas demand.
- **Make flush wall fittings under about 20 cm probe-lit, seat them 0.5 mm off the visual wall, repaint the lightmap footprint of any plate you move or delete, and tint the plate by about 1 / (probe ÷ wall light) stored through `LinearToGammaSpace`** — a switch plate got 4 × 3 texels and baked a half-black smear; a moved plate leaves its baked shadow; probes gave plates up to 2.7× the wall's light.
- **Give pack furniture with no UV2 ContributeGI + `receiveGI = LightProbes` + shadows On per renderer, and move it to the lightmap as soon as it has a clean UV2** — it then casts contact shadows without atlas space instead of reading as a sticker.
- **When objects read as black silhouettes, query `receiveGI` before aiming lights; move anything over ~0.12 m with a clean UV2 to the lightmap, and read `lightmapIndex` only right after a bake** — a Baked light never lights a probe-lit renderer directly, so every extra light and bake changes nothing.
- **Make grass and ground cards receive lightmaps (or sample the ground lightmap at the blade root) wherever baked shadows fall on them** — probe-lit cards carry no shadow detail and stay sunlit inside tree shadows.
- **Animate static decor with a shader vertex offset (phase from vertex colour or a spare UV, not UV2) and pad its bounds** — moving the Transform makes it dynamic and probe-lit, so it stops matching its baked neighbours.

## Groups, atlas share and density

- **Audit chart share (`scaleOffset.x × y`, which grows with `scaleInLightmap²`) before blaming denoise or compression: demote hidden hogs to 0.1, fixed-resolution groups for hero areas, one small shared group for terrain and background, texel padding 8** — one hidden envelope took 68 % of an atlas and a door got ~9 texels; the fix took 17 lightmaps to 7.
- **Give every lightmapped renderer a selector into a few explicit groups (zero ungrouped before each bake) and keep probe-lit renderers selector-free** — a group of only probe-lit members still bakes a full empty atlas, and a blunt "assign all" script wipes hand-made hero, LOD and SSS groups.
- **Put a group selector on every new static object, reading the parent's selector from its renderer, not its wrapper** — an ungrouped object falls into an implicit group that can resolve to 16×16 and bakes flat or black with a valid-looking index.
- **Make one Bakery group per LOD level with `sceneLodLevel` set and unique `id`/`sortingID`** — Bakery silently skips LODGroup renderers whose group has `sceneLodLevel = -1`.
- **Give hero terrain tiles their own group and a mesh copy whose UV2 fills 0–1, and keep anything crossing a tile edge at equal texels per metre on both sides** — the group sets atlas size but UV2 coverage sets density; a tile on its slice of a global unwrap stays ~1.4 texels/m.
- **Check atlas headroom before accepting ~1 texel/m on terrain, and nudge important sites off the tile grid** — at that density contact shadows disappear, and seam fixing cannot stitch separate tile renderers.
- **Weight terrain `scaleInLightmap` by distance from the play route to each chunk's nearest edge** — inside one group the scale is a relative share, so weighting moves texels without adding VRAM.
- **Give each material of a mesh a UV2 share near its surface-area share; flag a submesh with ≥ 10 % of the area and < 5 % of the UV2** — area-weighted unwraps gave tree bark ~3 % of the UV2, so whole limbs sat in ~1 texel and baked a different colour from the trunk.

## UV2 quality

- **Generate importer lightmap UVs with margin method Manual (~6), never Calculate at a low minimum resolution** — Calculate left UV2 fill at 0.10–0.13 (texel extent 25 → 7,939 in one case); Manual 6 gave ~0.4 and garden sofas went from 2.4 to ~25 texels/m.
- **After every bake assert finite `lightmapScaleOffset` on every lightmapped renderer, scan UV2 ranges for the one bad mesh, and always write the UV2 channel on a reused mesh asset** — one mesh with garbage UV2 made the packer fail for its whole group (~900 renderers), and `Mesh.Clear()` keeps a stale UV2.
- **For overlapping-UV warnings on renderers ≥ ~1.3 m, widen the pack margin until the gap is ≥ padding + 1 texels, write it back to `unwrapParameters`, then trim `scaleInLightmap` to the smallest value that holds the gutter** — the margin is in UV space while padding is in texels; trimming took 19.17 to 13.77 Mtexel.
- **Treat overlap warnings from a draft-resolution bake as unproven until final-resolution crops show them** — at draft density nearly every renderer warns, yet the final bake showed no bleeding.
- **Generate ProBuilder UV2 with `EditorMeshUtility.Optimize(pb, true)` and create a `LightingSettings` asset before reading `Lightmapping.lightingSettings`** — `Refresh()` never builds UV2, and the getter throws instead of returning null.

## Sweeps and bindings

- **Before any bulk change to lighting or static flags, snapshot each renderer's `lightmapIndex` and compare expected and actual touch counts** — a predicate written from one diagnosis silently reverted just-fixed renderers while its own metric reported success.
- **Treat clones and renderers placed since the last bake as unbaked, remove the storage row of any renderer moved to probes, rebuild rows from live renderers right after a bake, and never hard-code lightmap ids** — Bakery re-applies bindings from storage at load, clones keep their source's chart, and a new or emptied group renumbers every id after it.
