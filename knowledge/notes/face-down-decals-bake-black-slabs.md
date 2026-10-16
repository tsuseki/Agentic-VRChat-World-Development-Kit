---
title: Face-down ground decals and wrong-way normals bake black
topic: lighting-baking
tags: [decal, normals, winding, inverted, black lightmap, shadow casting, Bakery, sweep]
summary: A face-down ground quad is invisible from above yet still casts shadow, sealing the surface below into a black baked slab; diagnose by comparing winding normal and shading normal against a ground truth before flipping either.
---
**Symptom:** A hard-edged black rectangle bakes onto a road or floor (e.g. 6 x 27 m across a start/finish line), plus half of a symmetric set of markings. Separately, small closed boxes (plinths, kiosks) bake near-black (lightmap mean 0.031 vs 0.43-0.76 on neighbours).

**Cause:** Flat single-quad markings (painted lines, grid boxes, rugs) authored **facing down** are backface-culled from above, but still have `shadowCastingMode.On` a few cm above the surface, so in the bake they occlude it. **The black thing is the road, not the quad**: disable the quad's Renderer and re-render; if the black persists it is baked into the surface beneath. For closed shells, winding and shading normals that both point inward make the baker see light behind every face.

**Fix / rule:** Compare two normals per ContributeGI mesh, the average **winding** normal (`Cross(p1-p0, p2-p0)` over triangles) and the average **shading** normal:
- Both point down -> authored face-down: reverse the winding AND set shading normals up.
- They disagree -> one is wrong, but disagreement does not say which. Establish ground truth first:
  - **Closed convex shell:** correct faces point away from `mesh.bounds.center`; both winding and shading must score outward (Unity's built-in Cube scores 12/12 on both and is the control).
  - **Flat/open mesh (terrain tile, decal, wall panel):** the bounds-centre test is meaningless; use the known axis (`normal.y > 0` for ground).
  - **Test in world space.** Tiles on a `(270,180,0)` transform from a Z-up import read 30-40% up locally and 100% up in world space; a local test produced a false "inside-out" and four good meshes were wrongly flipped.
- Calibrate the sign on a surface you know faces up; skip meshes whose averaged normals cancel (magnitude < 0.35) or every closed box false-positives.
- Sweep, don't eyeball: one scripted pass over ~1800 ContributeGI meshes found the whole family. One bad quad usually means a symmetric set is bad; check for a correctly authored sibling and match it exactly (winding, normals, `shadowCastingMode`).
- Write corrected geometry to a **new `.asset`**; never mutate a shared source mesh. Call `RecalculateTangents()` afterwards.

**Verify:** Read the lightmap itself: set the `.hdr` importer `isReadable = true`, `GetPixelBilinear` across the renderer's `lightmapScaleOffset` rect (inset ~12% to skip padding), compare the mean against a renderer that looks right, then restore `isReadable`. That reveals shared-mesh patterns ("all 7 users of this mesh are black") that screenshots hide.

Related: [scripted-mesh-builder-winding-check](scripted-mesh-builder-winding-check.md), [generated-mesh-needs-recalculatetangents](generated-mesh-needs-recalculatetangents.md)
