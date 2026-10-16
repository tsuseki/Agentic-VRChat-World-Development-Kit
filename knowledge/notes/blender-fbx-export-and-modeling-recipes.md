---
title: Headless Blender export flags and modeling recipes for Unity assets
topic: blender-modeling
tags: [Blender, headless, FBX export, bake_space_transform, axis, normals, submesh order, colorspace, cloth, bisect]
summary: Recipes and traps for building Unity assets in headless Blender: FBX export flags, mirrored bakes, material slot order, two-sheet panels, image colorspace round-trips, cloth drapes and cutting an FBX.
---
**Headless build:** all Blender work runs headless (project rule in the `blender-modeler` agent): `blender -b --factory-startup -P script.py` from bash, or the MCP `execute_blender_code_for_cli` tool; never drive the GUI window. Without `--factory-startup`, broken third-party add-ons spam harmless tracebacks; print your own OK marker and grep stdout for it.

**FBX export flags that import into Unity with correct scale/rotation (no -90 deg / x100):**
`apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, object_types={'MESH'}`. Blender front (-Y) maps to Unity -Z. (`FBX_SCALE_NONE` imports at 1/100: see [blender-fbx-export-scale-all-not-scale-none](blender-fbx-export-scale-all-not-scale-none.md).) Curve/text objects are silently skipped: `bpy.ops.object.convert(target='MESH')` first.
- **Mirror trap:** on an extruded text mesh, `bake_space_transform=True` mirrored the geometry (glyphs backwards, winding flipped globally). Adding `flip_normals` only made caps/sides inconsistent. Fix: export with default flags minus `bake_space_transform` (mesh keeps Blender axes: width X, height +Z, front -Y) and stand it up in Unity with `rotation = Euler(-90, 180, 0)`.
- Without `bake_space_transform` (`axis_forward='-Z', axis_up='Y'`), the axis conversion lives in the **child node transforms** (`localRotation ≈ (270,0,0)`), not in the vertices. See [fbx-import-into-unity-traps](fbx-import-into-unity-traps.md).

**Material slot order:** Unity orders FBX submeshes by *first reference*, not by Blender slot index, so faces authored out of slot order import with materials permuted. Before export: `bpy.ops.mesh.sort_elements(type='MATERIAL', elements={'FACE'})`. Diagnose by comparing per-submesh triangle counts with Blender slot face counts.

**Two-sided panels:** `normals_make_consistent(inside=False)` destroys the "two loose open sheets facing opposite ways" idiom: open sheets have no defined outside, so it flips the lower sheet to match the upper (a roof measured 528 m² up-facing, 0 m² down-facing: invisible from inside). Build any panel seen from both sides (roof sheets, gable infill, awnings) as a **closed prism**. Detect across a library by comparing up- vs down-facing triangle area in world space: closed solids sit near 1.00 (the broken roof was 0.36). Open boundary-edge count alone is not the tell.

**`img.pixels` colorspace:** reading `.pixels` converts to scene-linear; assigning and saving encodes back to the image's colorspace, so load-sRGB -> save-sRGB round-trips byte-for-byte. Do **not** hand-encode linear->sRGB before assigning (double gamma: 1.22x too bright on a light texture, 1.93x on a dark one; worst-on-darkest is the signature). Where it IS real: Blender assumes sRGB for every 8-bit file, so rough/metal/alpha `.jpg/.png` maps must get `img.colorspace_settings.name = 'Non-Color'` before reading. `.exr` maps are tagged Linear and unaffected. Always A/B an untouched prop (ratio 1.000) before believing a gamma diagnosis.

**Headless cloth drape (blanket):** `scene.frame_set()` stepping lets cloth fall through colliders; use `bpy.ops.ptcache.bake_all(bake=True)` after setting `point_cache.frame_start/end` (else 250 frames). To stop sliding: collider `collision.cloth_friction = 40`, pin a vertex-group strip (`vertex_group_mass`), temporary floor plane to pool the overhang. Start the cloth ≤ 0.03 m above the surface; pinned verts stay at start height.

**Light tufted cushion (~6k verts instead of 240k):** cube -> edit-subdivide cuts=3 -> Subsurf level 3 (2 for small cushions) applied -> gaussian dip displacement on top verts -> clouds displace 0.008 -> shade smooth. No bevel, no post-dip subsurf.

**Cutting an existing FBX below a Unity floor plane:** compute the cut in Unity as a *fraction of the mesh-local up-axis extent* (`worldToLocal.MultiplyVector(Vector3.up)` gives axis and sign; fraction from renderer world bounds). Blender import/export does not touch mesh-data coords, so apply the fraction to raw `v.co`; `bmesh.ops.bisect_plane` + `holes_fill`, flip caps down, inherit the neighbour `material_index`. Export with default scale flags and verify Unity `mesh.bounds` match. Unity-side gotchas (file scale, slot reorder) are in [fbx-import-into-unity-traps](fbx-import-into-unity-traps.md).
