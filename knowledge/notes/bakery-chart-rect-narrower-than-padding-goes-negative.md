---
title: Bakery gives small props 0-3 texel charts and negative scale-offsets when the chart rect is under 2 × padding
topic: lighting-baking
tags: [bakery, lightmapScaleOffset, negative scale offset, scale in lightmap, texel padding, small props, rocks, cm-scale meshes]
summary: Bakery's default atlas packer subtracts 3 texels of padding from each side of every chart rect, so a prop whose rect is under ~6 texels bakes to 0-3 texels or a negative (mirrored) scale-offset; raise Scale In Lightmap per renderer, not the mesh scale, and audit with abs(so).
---

**Symptom.** Small hard props (rocks, stepping stones, kerbs, lanterns, sills; in one scene 34 boulders and 251
stone renderers) read as one flat lightmap value: no sun/shade split, no contact gradient, while trees and walls
beside them bake fine. `lightmapScaleOffset` is tiny (|x| ≈ 0.0005–0.002 on a 4096 atlas) and often **negative**.
A UV2 audit that treats a negative scale-offset as "not baked" falls back to a Scale In Lightmap estimate and shows
healthy numbers for exactly the broken renderers.

**Cause.** With Unwrap UVs off and the default atlas packer, Bakery sizes each chart rect from the world surface area:
`rect texels = texelsPerUnit × sqrt(2 × area × scaleInLightmap)` (the 2 is its un-halved triangle cross products;
non-square UV2 bounds stretch one side). It then shrinks the rect by `texelPaddingForDefaultAtlasPacker` (default 3)
on every side and divides by the UV2 bounds, so the baked chart is `rect − 6` texels across the UV2 bounds. At
3 texels per unit a 1 m rock with Scale In Lightmap 2 gets a rect of about 9 texels and a chart of 3; a 0.5 m stepping
stone at Scale In Lightmap 1 gets 3.6 texels, 3.6 − 6 < 0, so the width goes negative (mirrored UV2, a fraction of a
texel). Unity-generated UV2 also fills only 0.3–0.5 of its bounds, so a "3 texel" chart is ~1 texel per metre.
Mesh scale is not the cause: positions are measured in world space, so a 1 cm FBX scaled ×100 and a 1 m OBJ size
identically. (Centimetre-scale source meshes are still worth importing at metre scale for other reasons.)

**Fix / rule.**
- Do not touch the shared model files. Set Scale In Lightmap on each scene renderer so the chart rect reaches the
  wanted chart plus 6: `scaleNew = scale × ((target + 6) / rectOld)²`, where `rectOld = across + 6` and `across =
  |so.x| × atlasSize × uv2BoundsWidth` (keep the sign: negative `across` still gives `rectOld = across + 6`). Aim for
  ≥ 10 texels across the chart and ≥ ~8 texels per metre of surface for stones; thin foliage patches ≥ 12 across.
- Values of 10–150 are normal for tiny props: the share grows with the square root of the scale, and 390 renderers at
  these sizes added only ~130 k texels (under 1 % of a 4096 atlas).
- Foliage LOD copies that share LOD0's chart (shared-LOD UV) need the scale only on LOD0.
- Audit with `abs(so)`; flag the sign in its own column so negative rows stay visible.

**Verify.** Predict the rect, bake, and compare: the predicted `across` matched the baked one to within a few percent
(10.1 vs 10, 17.7 vs 17.7). A lightmap-only render must show a sun-lit face and a shade face on the same rock, and a
fixed positive control (an unfixed stone) must still read flat. Prove it first in a scratch copy of the scene (a few
hundred stones bake in under half a minute) before the full bake.

**Pitfalls.** Raising Scale In Lightmap does not rescue a fragmented UV2 (see `fragmented-organic-uv2-bakes-faceted-dark-triangles`);
it only fixes charts that are too small after padding. An implicit atlas keeps texel density fixed, so adding stones
only grows the atlas area, not the other charts. A scratch bake may write its lightmaps into the real output folder
whatever the scratch scene's output path says: delete the scratch-named files afterwards.

**Cm-scale FBX meshes (a second cause).** When the mesh is about 1 cm and the instance scale is 60-115, the generated UV2 can have
charts that fill under 0.1 % of the unit square, so the rect model above is not enough (fill ≈ 0 makes any density target
meaningless). Make a metre-scale mesh copy (vertices ×100, instance scale ÷100), regenerate UV2 on the copy, then set Scale In
Lightmap from the rect model with the real UV2 fill. **Prefab instances:** write Scale In Lightmap through `SerializedObject`
(`m_ScaleInLightmap`) plus `PrefabUtility.RecordPrefabInstancePropertyModifications`; a plain property set was reverted when
Bakery reloaded the scene, so the first bake looked unchanged.
